# -*- coding: utf-8 -*-
"""#223 / #227 item 2 — A MACHINE THAT DIED RESTARTING IS ASKED ABOUT; A MACHINE SWITCHED OFF IS NOT.

His rule for the mailbox: "it should only really be waiting on me if its something i need to do". A peer
that died mid-restart (the ALT, #225, into v3419) needs a person at it; a peer he switched off does not.
MEASURED on his roster 2026-09-24: relaunch.armed is True on EVERY console, so "armed" cannot be the
signal - the last beacon holding a newer build on disk than it runs, with the restart allowed, is.

  · DRIVEN over his real roster shapes: Dean (v3404 on v3404, off) and Wife PC (no diskVer, off) ask
    NOTHING - OK. A peer last heard running v3419 with v3420 on disk and may=True -> MISSING and ONE
    well-formed ask whose identity carries the build (a new stall is a new question).
  · DRIVEN: a restart that was HELD (may False) is not a stall; this machine's own row is never asked
    about; no roster is UNMEASURED, never OK.
  · JOINED: the row is in CHECKS, WATCHES and ASKS, and attach_asks puts the question on the row.
RED_PROOF below.
"""
import calendar
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402

NAME = "no machine went quiet mid-restart"
NOW = calendar.timegm(time.strptime("2026-09-24T21:00:00", "%Y-%m-%dT%H:%M:%S"))   # UTC, as the row reads t


def _row(machine, nick, ver, disk, t, may=True):
    return {"machine": machine, "nickname": nick, "ver": ver, "diskVer": disk, "t": t,
            "relaunch": ({"armed": True, "may": may, "why": "nothing in flight"} if may is not None else None)}


HIS = {"me": "konyo-3",
       "online": [_row("konyo-3", "Konyo", "v3499", "v3499", "2026-09-24T20:19:15.133Z")],
       "offline": [_row("dean-1", "Dean", "v3404", "v3404", "2026-09-20T23:17:06.336Z"),
                   dict(_row("wife-1", "Wife PC", "v2101", None, "2026-09-01T18:24:45.281Z"), relaunch=None)]}


def _with(*extra):
    r = {"me": HIS["me"], "online": list(HIS["online"]), "offline": list(HIS["offline"]) + list(extra)}
    return r


class AMachineThatDiedRestartingIsAskedAbout(unittest.TestCase):

    def test_his_real_roster_asks_nothing(self):
        r = cd._mid_restart_peers(HIS, now=NOW)
        self.assertEqual(r["state"], cd.OK, r)
        self.assertEqual(r["quiet"], [], "a machine he switched off became a question")

    def test_a_stalled_restart_is_missing_and_asked(self):
        r = cd._mid_restart_peers(_with(_row("alt-1", "Konyo ALT TEST", "v3419", "v3420",
                                             "2026-09-24T18:00:00.000Z")), now=NOW)
        self.assertEqual(r["state"], cd.MISSING)
        self.assertEqual([q["nickname"] for q in r["quiet"]], ["Konyo ALT TEST"])
        self.assertEqual(r["quiet"][0]["ageS"], 3 * 3600)
        self.assertIn("into v3420", r["why"])

    def test_a_held_restart_is_not_a_stall(self):
        r = cd._mid_restart_peers(_with(_row("alt-1", "ALT", "v3419", "v3420", "2026-09-24T18:00:00Z", may=False)),
                                  now=NOW)
        self.assertEqual(r["quiet"], [], "a restart that was WAITING (may False) is not a machine that died")

    def test_this_machine_is_never_asked_about(self):
        mine = dict(_row("konyo-3", "Konyo", "v3499", "v3500", "2026-09-24T18:00:00Z"))
        r = cd._mid_restart_peers({"me": "konyo-3", "online": [], "offline": [mine]}, now=NOW)
        self.assertEqual(r["quiet"], [])

    def test_no_roster_is_unmeasured(self):
        self.assertEqual(cd._mid_restart_peers("not a roster", now=NOW)["state"], cd.UNMEASURED,
                         "no roster must read as UNMEASURED, never OK")
        self.assertEqual(cd._mid_restart_peers({"me": "konyo-3", "online": [], "offline": []}, now=NOW)["state"],
                         cd.UNMEASURED, "nothing offline is an absent question, not a clean answer")

    def test_the_ask_is_well_formed_and_carries_the_build(self):
        stalled = _with(_row("alt-1", "Konyo ALT TEST", "v3419", "v3420", "2026-09-24T18:00:00Z"))
        real = cd._mid_restart_peers
        cd._mid_restart_peers = lambda roster=None, now=None: real(stalled, now=NOW)
        try:
            state, why = cd._check_no_machine_went_quiet_mid_restart()
            asks = cd._ask_mid_restart({"check": NAME, "state": state, "why": why})
            rows = cd.attach_asks([{"check": NAME, "state": state, "why": why}])
        finally:
            cd._mid_restart_peers = real
        self.assertEqual(len(asks), 1)
        self.assertEqual(cd.ask_problems(asks[0]), [], "the ask is malformed: %r" % asks[0])
        self.assertEqual(asks[0]["fp"], "mid-restart:alt-1:v3420")
        self.assertIn("Is it on?", asks[0]["q"])
        self.assertTrue(rows[0].get("asks"), "attach_asks did not put the question on the row")

    def test_the_row_is_joined_everywhere_it_must_be(self):
        self.assertIn(NAME, [c[0] for c in cd.CHECKS])
        self.assertIn(NAME, cd.WATCHES)
        self.assertIs(cd.ASKS.get(NAME), cd._ask_mid_restart)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#223 - every machine that is simply OFF becomes 'is it on?' again (his wife's PC is not an errand)",
        "file": "console_doctor.py",
        "find": "        if not (ver and disk and disk != ver and rl.get(\"may\") is True):\n",
        "replace": "        if not (ver and rl.get(\"may\") is not False):\n",
        "matches": 1,
    },
    {
        "why": "#223 - the ask is unregistered: a machine that died restarting reads as switched off again",
        "file": "console_doctor.py",
        "find": "    \"no machine went quiet mid-restart\": _ask_mid_restart,\n",
        "replace": "",
        "matches": 1,
    },
]
