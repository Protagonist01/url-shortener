"""Resolve public application requirements and record actual advisory evidence."""
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "dependency-audit"
SCANNER_VERSION = "2.10.1"


def main():
    if version("pip-audit") != SCANNER_VERSION:
        raise RuntimeError("Use the isolated pinned requirements-audit.txt environment")
    requirements = ROOT / "requirements.txt"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT / ("baseline-" + sys.platform + ".json")
    metadata_path = OUTPUT / ("metadata-" + sys.platform + ".json")
    # Avoid confusing an earlier report with the current failed attempt.
    report_path.unlink(missing_ok=True)
    metadata_path.unlink(missing_ok=True)
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("PIP_")}
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1")
    command = [sys.executable, "-m", "pip_audit", "--requirement", str(requirements),
               "--index-url", "https://pypi.org/simple", "--strict", "--timeout", "15",
               "--format", "json", "--desc", "off", "--progress-spinner", "off",
               "--output", str(report_path)]
    with TemporaryDirectory(prefix="resolver-", dir=OUTPUT) as directory:
        result = subprocess.run(command, env=env, cwd=directory, timeout=300,
                                capture_output=True, text=True)
    (OUTPUT / ("scanner-" + sys.platform + ".log")).write_text(
        result.stdout + result.stderr, encoding="utf-8")
    if result.returncode not in (0, 1) or not report_path.exists():
        raise RuntimeError("Audit failed; inspect the ignored scanner log, not a security pass")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dependencies = report.get("dependencies", [])
    if not dependencies or any("skip_reason" in dependency for dependency in dependencies):
        raise RuntimeError("Empty or skipped dependency coverage; audit is incomplete")
    vulnerable = [dependency for dependency in dependencies if dependency.get("vulns")]
    findings = sum(len(dependency["vulns"]) for dependency in vulnerable)
    if (result.returncode == 0) != (findings == 0):
        raise RuntimeError("Scanner exit/report disagree; inspect evidence")
    metadata = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
        "python": platform.python_version(), "platform": platform.platform(),
        "scanner": "pip-audit", "scanner_version": SCANNER_VERSION,
        "service": "PyPI Python Packaging Advisory Database",
        "dependency_count": len(dependencies), "vulnerable_packages": len(vulnerable),
        "advisory_records": findings, "scanner_exit": result.returncode,
        "result": "known_vulnerabilities" if findings else "no_known_findings_in_scanned_set",
        "limitations": "OS-specific resolver; no exploitability, unpublished prototype, frontend or full-security proof",
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    for dependency in vulnerable:
        print(dependency["name"], dependency["version"],
              [(v["id"], v.get("fix_versions", [])) for v in dependency["vulns"]])
    return result.returncode


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as error:
        print("Dependency audit incomplete:", type(error).__name__, file=sys.stderr)
        exit_code = 2  # Operational failure, not the known-findings code1.
    sys.exit(exit_code)
