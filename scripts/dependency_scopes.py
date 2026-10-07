"""Named install scopes and hashes of their complete local manifest inputs."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCOPES = {"runtime": "requirements.txt", "test": "requirements-ci.txt",
          "operations": "requirements-ops.txt"}


def manifest_hashes(scope, root=ROOT):
    root = root.resolve()
    hashes = {}
    active = set()

    def visit(path):
        path = path.resolve()
        name = path.relative_to(root).as_posix()
        if path in active:
            raise ValueError("Cyclic requirement include")
        if name in hashes:
            return
        active.add(path)
        contents = path.read_bytes()
        hashes[name] = hashlib.sha256(contents).hexdigest()
        for raw in contents.decode("utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if line.startswith("-r ") or line.startswith("--requirement "):
                visit(path.parent / line.split(maxsplit=1)[1])
        active.remove(path)

    visit(root / SCOPES[scope])
    return dict(sorted(hashes.items()))


def suffix(scope, platform):
    # Retain the original runtime evidence names for existing consumers.
    return platform if scope == "runtime" else scope + "-" + platform
