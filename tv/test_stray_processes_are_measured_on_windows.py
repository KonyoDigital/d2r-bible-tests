# -*- coding: utf-8 -*-
"""#171 (REG-2482) - STRAY PROCESSES ARE MEASURED ON WINDOWS, BY THE KERNEL'S OWN COUNTERS.

MEASURED on Dean's PC 2026-10-22: 'stray processes' UNKNOWN for 45 days - "`ps` could not be asked for a CPU sample".
There is no ps on Windows, so the runaway watch (the 28-hour core-burner class) was blind on every Windows PC. The
Windows sweep asks the same question the same way: two CUMULATIVE CPU-time samples, the second from the previous call,
busy only on what a process burned BETWEEN them, and old by the creation time child_guard's birth reader reads.

Driven with fixture samples on any PC:
  * busy and old -> a suspect (and young, idle, reused-pid and born-after-the-first-sample processes are not);
  * his game and Windows' own images are excused - but never a Windows host running THIS tree's code;
  * one sample -> UNMEASURED, never a verdict;
  * an unreadable sampler -> UNMEASURED, never "nothing busy" - and the last good sample is kept;
  * an idle machine -> OK, and the sentence names what was scanned and by what.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[i-own-everything-i-start]]
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import health_engine as HE  # noqa: E402
import my_orphans as MO  # noqa: E402

T0, T1 = 100000.0, 100600.0          # two eagle ticks, ten minutes apart
OURS_PS = ("C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File %s\\capture_win.ps1" % HERE)


def _p(cpu_s, exe="python.exe", ppid="1"):
    return {"cpuS": cpu_s, "ppid": ppid, "exe": exe}


class _Sweep(unittest.TestCase):

    def setUp(self):
        self.samples, self.clock = [], [T0]
        self.births = {}
        self.cmds = {}
        seams = {
            "_platform": lambda: "win32",
            "_now": lambda: self.clock[0],
            "_win_cpu_sample": lambda: self.samples.pop(0) if self.samples else None,
            "_win_birth": lambda pid: self.births.get(str(pid)),
            "_win_command": lambda pid: self.cmds.get(str(pid)),
            "holds_his_port": lambda pid: (0, "holds no port of his (fixture)"),
            "_registered_pids": lambda: set(),
        }
        for name, val in seams.items():
            p = mock.patch.object(MO, name, val)
            p.start()
            self.addCleanup(p.stop)
        saved_last, saved_scan = dict(MO._LAST_WIN), dict(MO._SCAN)
        MO._LAST_WIN.update(at=0.0, cpu={})
        MO._SCAN.update(n=None, how=None, at=None, portsSay=None)
        self.addCleanup(lambda: (MO._LAST_WIN.clear(), MO._LAST_WIN.update(saved_last),
                                 MO._SCAN.clear(), MO._SCAN.update(saved_scan)))

    def _two(self, first, second):
        """the first eagle tick at T0, the second at T1 -> what the second one judged"""
        self.samples[:] = [first, second]
        self.clock[0] = T0
        MO.suspects()
        self.clock[0] = T1
        return MO.suspects()


class BusyAndOldIsASuspect(_Sweep):

    def test_only_what_burned_a_core_between_the_samples_and_is_old_is_named(self):
        old = T0 - 3600
        first = {"4242": _p(100.0), "77": _p(50.0), "99": _p(10.0), "55": _p(500.0), "88": _p(1.0),
                 "1111": _p(10.0, "D2R.exe"), "2222": _p(10.0, "svchost.exe"), "3333": _p(10.0, "powershell.exe"),
                 "4444": _p(10.0, "powershell.exe")}
        second = {"4242": _p(400.0),        # 300 s over 600 s: 50% of a core, sustained - and 70 min old
                  "77": _p(51.0),           # idle
                  "99": _p(310.0),          # busy, but born at the first sample: 10 min old
                  "55": _p(20.0),           # LESS cpu than before: the pid names another process now
                  "88": _p(301.0),          # busy, but born AFTER the first sample: that reading was another's
                  "1111": _p(310.0, "D2R.exe"), "2222": _p(310.0, "svchost.exe"),
                  "3333": _p(310.0, "powershell.exe"), "4444": _p(310.0, "powershell.exe"),
                  "6000": _p(900.0)}        # 6000 is younger than the first sample
        self.births.update({"4242": old, "77": old, "99": T0, "55": old, "88": T0 + 300, "1111": old, "2222": old,
                            "3333": old, "4444": old, "6000": T0 + 100})
        self.cmds.update({"4242": "python.exe -c \"while 1: pass\"",
                          "99": "python.exe young.py",
                          "1111": "C:\\Program Files (x86)\\Diablo II Resurrected\\D2R.exe",
                          "2222": "C:\\Windows\\System32\\svchost.exe -k netsvcs",
                          "3333": OURS_PS,
                          "4444": ("\"C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\" -Command "
                                   "\"Get-ChildItem C:\\ -Recurse\"")})
        rows = self._two(first, second)
        by = dict((r["pid"], r) for r in rows)
        print("   suspects: %s" % ", ".join("%s %.0f%% %.0f min" % (r["pid"], r["cpu"], r["minutes"]) for r in rows))
        self.assertEqual(sorted(by), ["3333", "4242", "4444"], "the wrong processes were named: %r" % rows)
        self.assertIsNone(by["4444"]["ours"], "an inline shell runaway is nobody's to name - and never the OS's")
        self.assertEqual(by["4242"]["cpu"], 50.0, "the load is not the CPU burned between the two samples")
        self.assertEqual(by["4242"]["samples"], 2)
        self.assertAlmostEqual(by["4242"]["minutes"], 70.0, places=1)
        self.assertIs(by["3333"]["ours"], True,
                      "a shell running THIS tree's code was not attributed to us")
        # the next tick, through the row he reads: still burning, so the row is never OK
        self.samples[:] = [dict(second, **{"4242": _p(700.0), "3333": _p(610.0, "powershell.exe")})]
        self.clock[0] = T1 + 600
        st = HE.check_orphans()
        print("   the row: %s - %s" % (st["state"], st["line"][:120]))
        self.assertEqual(st["state"], HE.WARN, "a busy, old process of ours was not actionable: %r" % st)

    def test_his_game_and_its_stream_are_never_suspects(self):
        self.births.update({"9": T0 - 7200, "1111": T0 - 7200})
        self.cmds.update({"1111": "C:\\Games\\Diablo II Resurrected\\D2R.exe"})
        rows = self._two({"9": _p(10.0, "Boosteroid.exe"), "1111": _p(10.0, "D2R.exe")},
                         {"9": _p(400.0, "Boosteroid.exe"), "1111": _p(400.0, "D2R.exe")})
        self.assertEqual(rows, [], "his game, or the client streaming it, was named a runaway: %r" % rows)


class AnUnmeasuredSweepIsNeverClean(_Sweep):

    def test_one_sample_is_unmeasured_not_a_verdict(self):
        self.samples[:] = [{"4242": _p(100.0)}]
        rows = MO.suspects()
        self.assertEqual([r.get("pid") for r in rows], [None], rows)
        self.assertIn("only ONE cpu sample", rows[0]["why"])
        self.samples[:] = [{"4242": _p(100.0)}]
        st = HE.check_orphans()
        self.assertEqual(st["state"], HE.UNKNOWN, st)

    def test_an_unreadable_sampler_is_never_nothing_busy(self):
        for broken in (None, {}):
            MO._LAST_WIN.update(at=T0 - 600, cpu={"4242": _p(1.0)})
            self.samples[:] = []                                     # the seam answers None
            if broken == {}:
                self.samples[:] = [{}]
            rows = MO.suspects()
            self.assertEqual([r.get("pid") for r in rows], [None], "a failed sample was judged: %r" % rows)
            self.assertIn("UNMEASURED", rows[0]["why"])
            self.assertEqual(MO._LAST_WIN["cpu"], {"4242": _p(1.0)},
                             "a failed sample replaced the last good one - the next read would judge against nothing")
            self.samples[:] = [] if broken is None else [{}]
            st = HE.check_orphans()
            print("   unreadable (%r): %s - %s" % (broken, st["state"], st["line"][:100]))
            self.assertEqual(st["state"], HE.UNKNOWN, st)
            self.assertNotIn("nothing busy", st["line"])


class AnIdleMachineSaysWhatItScanned(_Sweep):

    def test_ok_names_the_instrument_and_the_count(self):
        self.births.update({"10": T0 - 9000, "11": T0 - 9000})
        self.samples[:] = [{"10": _p(5.0), "11": _p(7.0)}, {"10": _p(6.0), "11": _p(7.5)}]
        self.clock[0] = T0
        MO.suspects()
        self.clock[0] = T1
        st = HE.check_orphans()
        print("   idle: %s" % st["line"])
        self.assertEqual(st["state"], HE.OK, st)
        self.assertIn("2 process(es) scanned by the Windows kernel", st["line"])
        self.assertIn("His ports cannot be read on this PC", st["line"],
                      "the OK claims a port check that cannot run on Windows")


RED_PROOF = [
    {
        "why": "REG-2482 - a sampler failure on Windows reads as a clean machine: 'nothing busy' over a sweep that "
               "measured nothing",
        "file": "my_orphans.py",
        "find": "        return [_unmeasured_win(cur)]\n",
        "replace": "        return []\n",
        "matches": 1,
    },
    {
        "why": "REG-2482 - one sample is judged: nothing has a second reading, so every Windows tick says 'clean'",
        "file": "my_orphans.py",
        "find": "    if not prev or gap < 1.0:\n        return [{\"pid\": None, \"ours\": None,\n"
                "                 \"why\": (\"only ONE cpu sample is available%s - a CPU time",
        "replace": "    if False:\n        return [{\"pid\": None, \"ours\": None,\n"
                   "                 \"why\": (\"only ONE cpu sample is available%s - a CPU time",
        "matches": 1,
    },
    {
        "why": "REG-2482 - age is not asked on Windows: a busy ten-minute-old build is named a runaway",
        "file": "my_orphans.py",
        "find": "        if mins < old_min:\n            continue\n",
        "replace": "        if False:\n            continue\n",
        "matches": 1,
    },
    {
        "why": "REG-2482 - a shell under System32 is excused as the OS: a powershell runaway - this tree's capture, or "
               "an inline -Command loop of mine - goes unseen",
        "file": "my_orphans.py",
        "find": "    if first.rsplit(\"\\\\\", 1)[-1] in WIN_SCRIPT_HOSTS:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-2482 - the OK sentence stops naming its instrument: a Windows 'nothing busy' no longer says what "
               "it scanned",
        "file": "health_engine.py",
        "find": "        _how = (_scan or {}).get(\"how\") or \"an instrument that did not say which\"\n",
        "replace": "        _how = \"an instrument\"\n",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
