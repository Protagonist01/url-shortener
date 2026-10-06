"""Verify the HS256 repair against this revision's actual fresh audit report."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "output/dependency-audit"
    report = json.loads((output / ("baseline-" + sys.platform + ".json")).read_text())
    metadata = json.loads((output / ("metadata-" + sys.platform + ".json")).read_text())
    expected_hash = hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest()
    if metadata["requirements_sha256"] != expected_hash or metadata["scanner_version"] != "2.10.1":
        raise RuntimeError("Audit does not match these requirements/tool")
    dependencies = report.get("dependencies", [])
    if not dependencies or any("skip_reason" in item for item in dependencies):
        raise RuntimeError("Audit coverage is incomplete")
    by_name = {item["name"].lower().replace("_", "-"): item for item in dependencies}
    if any(name in by_name for name in ("python-jose", "ecdsa")):
        raise RuntimeError("Target JOSE/ECDSA chain still exists in clean app resolution")
    pyjwt = by_name.get("pyjwt")
    if not pyjwt or pyjwt["version"] != "2.15.1" or pyjwt.get("vulns"):
        raise RuntimeError("Required PyJWT pin missing or has known findings")
    print("Verified current resolved app requirements: no JOSE/ECDSA; PyJWT2.15.1 has no recorded findings.")
    print("Other findings remain visible; this is not full security approval.")


if __name__ == "__main__":
    main()
