# -*- coding: utf-8 -*-
"""REG-2464 (#171) — THE RUNAWAY WATCH READS THIS PROCESS'S CPU ON EVERY OS, WINDOWS INCLUDED.

Measured by the agent on Dean's PC (Windows): the console's runaway record read `cpu: null` on every tick.
control_app._cpu_seconds() read only resource.getrusage, and `resource` does not exist on Windows - so the CPU half of
the runaway watch (REG-699: "late AND burning") was blind there, and a console spinning a core while refusing status
reads could only ever read "late but idle". It now falls back to time.process_time(), this process's user+system CPU on
every OS (GetProcessTimes on Windows); POSIX still asks getrusage first.

THE LAW: with `resource` unimportable - the way Windows has none - _cpu_seconds() returns a float that RISES across a
busy loop, and the watch's own fraction is a number, never None. With `resource` present it is a float too.
RED_PROOF below. [[unknown-stays-unknown]]
"""
import os
import sys
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as CA  # noqa: E402


def _burn(seconds=0.3):
    """Spend about `seconds` of CPU on this thread."""
    end = time.process_time() + seconds
    n = 0
    while time.process_time() < end:
        n += sum(range(200))
    return n


class TheCpuIsReadOnEveryOS(unittest.TestCase):

    def test_without_resource_the_cpu_still_reads_and_rises(self):
        with mock.patch.dict(sys.modules, {"resource": None}):    # `import resource` raises, as on Windows
            with self.assertRaises(ImportError):
                import resource  # noqa: F401
            a = CA._cpu_seconds()
            _burn()
            b = CA._cpu_seconds()
        self.assertIsInstance(a, float, "with no `resource` module the CPU reads %r - the watch is blind" % (a,))
        self.assertIsInstance(b, float)
        self.assertGreater(b, a, "a busy loop burned no CPU by this reading (%r -> %r)" % (a, b))

    def test_the_watch_gets_a_fraction_not_none(self):
        with mock.patch.dict(sys.modules, {"resource": None}):
            t0, c0 = time.monotonic(), CA._cpu_seconds()
            _burn(0.2)
            t1, c1 = time.monotonic(), CA._cpu_seconds()
        self.assertIsNotNone(c0)
        frac = (c1 - c0) / (t1 - t0)
        self.assertGreater(frac, 0.0, "the runaway watch would read a busy thread as idle")

    @unittest.skipUnless(os.name == "posix", "getrusage exists only on POSIX - nothing to compare there")
    def test_with_resource_it_still_reads(self):
        self.assertIsInstance(CA._cpu_seconds(), float)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2464 - the fallback is gone: with no `resource` module (every Windows PC) the CPU reads None and "
               "the runaway watch's CPU half is blind",
        "file": "control_app.py",
        "find": "        return float(time.process_time())      # REG-2464 - every OS, Windows included\n",
        "replace": "        return None\n",
        "matches": 1,
    },
]
