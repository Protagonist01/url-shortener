"""Exercise the actual installed pytest UNIX temporary-root boundary."""
import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from unittest.mock import patch

from _pytest.tmpdir import TempPathFactory

ROOT = Path(__file__).resolve().parents[1]


def factory():
    return TempPathFactory(given_basetemp=None, retention_count=0,
                           retention_policy="none", trace=lambda *args: None,
                           _ispytest=True)


def verify(expect_vulnerable=False):
    if os.name != "posix":
        raise RuntimeError("UNIX boundary proof requires a POSIX runner")
    cases = []
    with TemporaryDirectory(prefix="pytest-boundary-") as directory:
        owned = Path(directory).resolve()
        with (
            patch.dict(os.environ, {"PYTEST_DEBUG_TEMPROOT": str(owned)}),
            patch("_pytest.tmpdir.get_user", return_value="boundary-fixture"),
        ):
            root = owned / "pytest-of-boundary-fixture"
            base = factory().getbasetemp()
            assert base.is_dir() and base.parent == root
            assert stat.S_IMODE(root.stat().st_mode) == 0o700
            cases.append("ordinary private temporary root")
            # All links/targets belong to this temporary fixture. No shared /tmp
            # user directory or another user's filesystem is modified.
            for chain in (False, True):
                root.rename(owned / ("previous-" + str(chain)))
                victim = owned / ("victim-" + str(chain))
                victim.mkdir()
                victim.chmod(0o755)
                sentinel = victim / "sentinel"
                sentinel.write_bytes(b"owned-fixture")
                target = victim
                if chain:
                    target = owned / "intermediate"
                    target.symlink_to(victim, target_is_directory=True)
                root.symlink_to(target, target_is_directory=True)
                before = (stat.S_IMODE(victim.stat().st_mode), sorted(p.name for p in victim.iterdir()))
                rejected = False
                try:
                    factory().getbasetemp()
                except OSError as error:
                    if "symbolic link" not in str(error):
                        raise
                    rejected = True
                assert sentinel.read_bytes() == b"owned-fixture"
                if expect_vulnerable:
                    assert not rejected, "Historical dependency no longer reproduces"
                    assert any(p.name.startswith("pytest-") for p in victim.iterdir())
                else:
                    assert rejected, "Installed pytest accepted a symlink root"
                    after = (stat.S_IMODE(victim.stat().st_mode), sorted(p.name for p in victim.iterdir()))
                    assert before == after, "Rejected root changed its target"
                cases.append("chained symlink" if chain else "direct symlink")
                root.unlink()
                root.mkdir(mode=0o700)
    result = {"pytest": version("pytest"), "platform": os.name,
              "expected_vulnerable": expect_vulnerable, "cases": cases,
              "result": "reproduced" if expect_vulnerable else "rejected_with_legitimate_control"}
    output = ROOT / "output/test-dependency"
    output.mkdir(parents=True, exist_ok=True)
    name = "boundary-before.json" if expect_vulnerable else "boundary-after.json"
    (output / name).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect-vulnerable", action="store_true")
    verify(parser.parse_args().expect_vulnerable)
