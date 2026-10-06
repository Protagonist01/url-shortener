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


def stop_owned_process(process):
    """Terminate only descendants of the Popen handle from this audit."""
    import psutil
    if process.poll() is not None:
        return
    parent = psutil.Process(process.pid)
    descendants = parent.children(recursive=True)
    for child in descendants:
        try:
            child.terminate()
        except psutil.NoSuchProcess:
            pass
    process.terminate()
    _, remaining = psutil.wait_procs(descendants + [parent], timeout=5)
    for child in remaining:
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    process.wait(timeout=5)


def main():
    requirements = ROOT / "requirements.txt"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT / ("baseline-" + sys.platform + ".json")
    metadata_path = OUTPUT / ("metadata-" + sys.platform + ".json")
    # Avoid confusing an earlier report with the current failed attempt.
    report_path.unlink(missing_ok=True)
    metadata_path.unlink(missing_ok=True)
    (OUTPUT / ("failure-" + sys.platform + ".json")).unlink(missing_ok=True)
    if version("pip-audit") != SCANNER_VERSION:
        raise RuntimeError("Use the isolated pinned requirements-audit.txt environment")
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("PIP_")}
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1")
    command = [sys.executable, "-m", "pip_audit", "--requirement", str(requirements),
               "--index-url", "https://pypi.org/simple", "--strict", "--timeout", "15",
               "--format", "json", "--desc", "off", "--progress-spinner", "off",
               "--output", str(report_path)]
    log_path = OUTPUT / ("scanner-" + sys.platform + ".log")
    with TemporaryDirectory(prefix="resolver-", dir=OUTPUT) as directory:
        Path(directory).resolve().relative_to(OUTPUT.resolve())
        env.update({key: directory for key in ("TMPDIR", "TEMP", "TMP")})
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(command, env=env, cwd=directory,
                                       stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                scanner_exit = process.wait(timeout=300)
            finally:
                stop_owned_process(process)
    if scanner_exit not in (0, 1) or not report_path.exists():
        raise RuntimeError("Audit failed; inspect the ignored scanner log, not a security pass")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    dependencies = report.get("dependencies", [])
    if not dependencies or any("skip_reason" in dependency for dependency in dependencies):
        raise RuntimeError("Empty or skipped dependency coverage; audit is incomplete")
    vulnerable = [dependency for dependency in dependencies if dependency.get("vulns")]
    findings = sum(len(dependency["vulns"]) for dependency in vulnerable)
    unique_ids = sum(len({finding["id"] for finding in dependency["vulns"]})
                     for dependency in vulnerable)
    if (scanner_exit == 0) != (findings == 0):
        raise RuntimeError("Scanner exit/report disagree; inspect evidence")
    metadata = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "requirements_sha256": hashlib.sha256(requirements.read_bytes()).hexdigest(),
        "python": platform.python_version(), "platform": platform.platform(),
        "scanner": "pip-audit", "scanner_version": SCANNER_VERSION,
        "service": "PyPI Python Packaging Advisory Database",
        "dependency_count": len(dependencies), "vulnerable_packages": len(vulnerable),
        "advisory_records": findings, "scanner_exit": scanner_exit,
        "unique_package_advisory_ids": unique_ids,
        "result": "known_vulnerabilities" if findings else "no_known_findings_in_scanned_set",
        "limitations": "OS-specific resolver; no exploitability, unpublished prototype, frontend or full-security proof",
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    for dependency in vulnerable:
        print(dependency["name"], dependency["version"],
              [(v["id"], v.get("fix_versions", [])) for v in dependency["vulns"]])
    return scanner_exit


if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as error:
        print("Dependency audit incomplete:", type(error).__name__, file=sys.stderr)
        OUTPUT.mkdir(parents=True, exist_ok=True)
        (OUTPUT / ("failure-" + sys.platform + ".json")).write_text(
            json.dumps({"result": "incomplete", "error_type": type(error).__name__,
                        "recorded_at": datetime.now(timezone.utc).isoformat()}, indent=2) + "\n")
        exit_code = 2  # Operational failure, not the known-findings code1.
    sys.exit(exit_code)
