"""Enforce targeted JWT, framework/parser and test-tool repairs in fresh scopes."""
import hashlib
import json
from pathlib import Path
import sys
import subprocess

from scripts.dependency_scopes import SCOPES, manifest_hashes, suffix

ROOT = Path(__file__).resolve().parents[1]


def read_scope(scope):
    output = ROOT / "output/dependency-audit"
    tag = suffix(scope, sys.platform)
    report = json.loads((output / ("baseline-" + tag + ".json")).read_text())
    metadata = json.loads((output / ("metadata-" + tag + ".json")).read_text())
    expected_hash = hashlib.sha256((ROOT / SCOPES[scope]).read_bytes()).hexdigest()
    if (metadata["requirements_sha256"] != expected_hash
            or metadata["scanner_version"] != "2.10.1"
            or metadata.get("scope") != scope
            or metadata.get("requirements_files_sha256") != manifest_hashes(scope, root=ROOT)
            or metadata.get("source_head") != subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()):
        raise RuntimeError("Audit does not match these requirements/tool")
    dependencies = report.get("dependencies", [])
    if not dependencies or any("skip_reason" in item for item in dependencies):
        raise RuntimeError("Audit coverage is incomplete")
    by_name = {item["name"].lower().replace("_", "-"): item for item in dependencies}
    return by_name


def require_pin(dependencies, name, pin):
    item = dependencies.get(name)
    if not item or item["version"] != pin or item.get("vulns"):
        raise RuntimeError("Required clean targeted pin missing or has findings: " + name)


def main():
    by_name = read_scope("runtime")
    if any(name in by_name for name in ("python-jose", "ecdsa")):
        raise RuntimeError("Target JOSE/ECDSA chain still exists in clean app resolution")
    require_pin(by_name, "pyjwt", "2.15.1")
    forbidden = {"pytest", "pytest-asyncio", "flower", "psutil", "pip-audit"}
    if forbidden.intersection(by_name):
        raise RuntimeError("Non-runtime tooling entered the production resolution")
    tests = read_scope("test")
    require_pin(tests, "pytest", "9.1.1")
    require_pin(tests, "pytest-asyncio", "1.4.0")
    if "flower" in tests or "pip-audit" in tests:
        raise RuntimeError("Monitoring/scanner tooling entered ordinary CI tests")
    operations = read_scope("operations")
    if any(name in operations for name in ("pytest", "pytest-asyncio", "psutil", "pip-audit")):
        raise RuntimeError("Test/scanner tooling entered operations")
    if operations.get("flower", {}).get("version") != "2.0.1":
        raise RuntimeError("Operations Flower pin missing")
    for dependencies in (by_name, tests, operations):
        for name, pin in (("fastapi", "0.141.1"), ("starlette", "1.7.0"),
                          ("python-multipart", "0.0.32"),
                          ("prometheus-fastapi-instrumentator", "8.1.0")):
            require_pin(dependencies, name, pin)
        if "opentelemetry-api" in dependencies:
            raise RuntimeError("Unreviewed telemetry dependency entered the scoped stack")
    print("Verified current resolved app requirements: no JOSE/ECDSA; PyJWT2.15.1 has no recorded findings.")
    print("Other findings remain visible; this is not full security approval.")
    print("Verified runtime/test/operations manifests; fixed pytest and plugin have no recorded findings.")
    print("Verified compatible framework/parser pins without known findings in all three scopes.")


if __name__ == "__main__":
    main()
