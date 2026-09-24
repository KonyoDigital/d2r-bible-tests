# -*- coding: utf-8 -*-
"""#229 — FREE SPACE IS MEASURED ON EVERY OS.

The per-machine roadmap (architecture survey wf_deba71ab-474) named it: river.py measured free disk with
`os.statvfs`, which does not exist on Windows, so the river's disk joint read UNKNOWN on every Windows
console. The same call sat in safe_copy (whose 4 GB floor could then never be proven, so a Windows copy
could not pass its own guard) and space_warden. All three use `shutil.disk_usage` now.

  · DRIVEN: with os.statvfs REMOVED (the Windows condition), all three still return a number.
  · AST: no production tv/*.py calls os.statvfs.
RED_PROOF below.
"""
import ast
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import river  # noqa: E402
import safe_copy  # noqa: E402
import space_warden  # noqa: E402


class WithoutStatvfs(unittest.TestCase):
    """The Windows condition. ⚠ os.statvfs cannot simply be DELETED on this Mac: shutil.disk_usage is
    built on it on POSIX, so the first cut of this case broke the replacement too and read as a failure
    of the fix. Here os.statvfs RAISES as on Windows, and shutil.disk_usage answers a known 7 GB - so
    each module must report exactly that, which it can only do through disk_usage."""

    def setUp(self):
        import collections
        import shutil
        self.shutil = shutil
        self._du, self._sv = shutil.disk_usage, getattr(os, "statvfs", None)
        usage = collections.namedtuple("usage", "total used free")(100 << 30, 50 << 30, 7 << 30)
        shutil.disk_usage = lambda p: usage

        def _no_statvfs(*a, **k):
            raise AttributeError("module 'os' has no attribute 'statvfs'")
        os.statvfs = _no_statvfs
        self._hist = river._hist_dir
        self.d = tempfile.mkdtemp(prefix="free-space-")
        river._hist_dir = lambda: self.d

    def tearDown(self):
        self.shutil.disk_usage = self._du
        if self._sv is not None:
            os.statvfs = self._sv
        river._hist_dir = self._hist
        os.rmdir(self.d)

    def test_the_river_disk_joint_is_a_number(self):
        j = river.j_disk()
        self.assertEqual(j.get("crossed"), 7.0, "the disk joint did not measure through disk_usage: %r" % j)

    def test_safe_copy_can_still_prove_its_floor(self):
        self.assertEqual(safe_copy._free_mb(os.path.join(self.d, "not", "yet", "made")), 7 * 1024,
                         "safe_copy cannot measure free space without statvfs")

    def test_space_warden_reads_the_disk(self):
        self.assertEqual(space_warden._free_gb(), 7.0)


class NothingCallsStatvfs(unittest.TestCase):

    def test_no_production_module_calls_os_statvfs(self):
        hits = []
        for fn in sorted(os.listdir(HERE)):
            if not fn.endswith(".py") or fn.startswith("test_"):
                continue
            try:
                tree = ast.parse(io.open(os.path.join(HERE, fn), encoding="utf-8").read())
            except SyntaxError:
                continue
            for n in ast.walk(tree):
                if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "statvfs"
                        and getattr(n.func.value, "id", "") == "os"):
                    hits.append("%s:%d" % (fn, n.lineno))
        self.assertEqual(hits, [], "os.statvfs does not exist on Windows: %s" % hits)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#229 - the river measures free disk with os.statvfs again: UNKNOWN on every Windows console",
        "file": "river.py",
        "find": "        free_gb = _sh.disk_usage(h).free / (1024.0 ** 3)\n",
        "replace": "        st = os.statvfs(h)\n        free_gb = (st.f_bavail * st.f_frsize) / (1024.0 ** 3)\n",
        "matches": 1,
    },
    {
        "why": "#229 - safe_copy measures free space with os.statvfs again: its floor cannot be proven on Windows",
        "file": "safe_copy.py",
        "find": "            return shutil.disk_usage(p).free // (1024 * 1024)\n",
        "replace": "            st = os.statvfs(p)\n            return (st.f_bavail * st.f_frsize) // (1024 * 1024)\n",
        "matches": 1,
    },
]
