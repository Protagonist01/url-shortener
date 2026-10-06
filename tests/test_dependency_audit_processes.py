"""A real audit process tree is stopped while a separate owned sentinel survives."""
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
import unittest

import psutil

from scripts.audit_dependencies import stop_owned_process


class ProcessCleanupTest(unittest.TestCase):
    def test_cleanup_stops_descendant_and_preserves_other_process(self):
        with TemporaryDirectory(prefix="audit-tree-test-") as directory:
            pid_file = Path(directory) / "child.json"
            code = """
import json, pathlib, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid': child.pid}))
time.sleep(30)
"""
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            parent = subprocess.Popen([sys.executable, "-c", code, str(pid_file)], creationflags=flags)
            sentinel = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"], creationflags=flags)
            child = None
            try:
                deadline = time.monotonic() + 10
                while not pid_file.exists():
                    if parent.poll() is not None or time.monotonic() > deadline:
                        self.fail("Owned fixture did not create a real descendant")
                    time.sleep(0.05)
                child = psutil.Process(json.loads(pid_file.read_text())["pid"])
                child_creation = child.create_time()
                stop_owned_process(parent)
                self.assertIsNotNone(parent.poll())
                self.assertTrue(not child.is_running() or child.status() == psutil.STATUS_ZOMBIE)
                self.assertIsNone(sentinel.poll(), "Cleanup touched a separate process")
            finally:
                stop_owned_process(parent)
                sentinel.terminate()
                sentinel.wait(timeout=5)
                # Never clean a PID that has been reused for another process.
                if child is not None and child.is_running() and child.create_time() == child_creation:
                    child.kill()


if __name__ == "__main__":
    unittest.main()
