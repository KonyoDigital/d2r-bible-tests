#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-1879 (#86 gap audit 33) — A DELETER HE SWITCHED OFF WAS CALLED A DRAIN THAT HAD STOPPED.

The retention drain took `on` from `_PRUNE_SAFE_TO_RUN`, a module constant that is True on every machine. The
deleter's real arming is two halves: that constant, and his TV_AUTO_PRUNE switch, which retention_may_act reads
before it lets a pass delete anything. So with TV_AUTO_PRUNE=off and releasable reels carried through three passes,
the drain said STOPPED, "the drain has STOPPED — 3 releasable reel(s) carried through 3 consecutive passes", with
on:true. drain_state's own DORMANT branch, "disarmed BY DESIGN — a decision, not a stall", was unreachable from the
console. shelf_driver's deleter lane read the same constant through `armedFrom`, so its DORMANT was unreachable too.

Now one function answers whether the deleter is armed: control_app.deleter_armed() = the constant AND his switch.
retention_may_act asks the switch through the same parse, the drain's `on` is deleter_armed(), and the lane's
armedFrom names deleter_armed, so all three say the same thing. A switch he set to off is DORMANT with his words.
A misspelt switch also holds, and says so. Unset and on stay armed, which is his ruling ("automatically prune its not
a question.. needs to be defaulted in"). Nothing here deletes or touches his tree: the drain's inputs are handed in.
[[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import os
import sys
import unittest
from unittest import mock

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402
import reel_retention as rr  # noqa: E402
import river_stamp as rvs  # noqa: E402
import shelf_driver as SD  # noqa: E402

OWED_THREE_PASSES = [{"owed": 3}, {"owed": 3}, {"owed": 3}]


def _drain(switch, stop_why=None):
    """The console's drain over three passes that each carried 3 releasable reels, with TV_AUTO_PRUNE=`switch`
    (None = unset). Every input is handed in. -> dict"""
    env = {k: v for k, v in os.environ.items() if k != "TV_AUTO_PRUNE"}
    if switch is not None:
        env["TV_AUTO_PRUNE"] = switch
    with mock.patch.dict(os.environ, env, clear=True), \
            mock.patch.object(ca, "_disk_history_tail", lambda n: list(OWED_THREE_PASSES)), \
            mock.patch.object(SD, "lane_beat", lambda *a, **k: {"works": 0, "lastWorkAt": None}), \
            mock.patch.object(rvs, "last_stamps_read", lambda *a, **k: {"last": {}, "why": None, "unparsed": 0}), \
            mock.patch.object(rr, "blocked_upstream",
                              lambda *a, **k: {"n": 0, "complete": True, "why": "nothing waits upstream"}):
        return ca._retention_drain(stop_why=stop_why, plan={"kept": [], "candidates": []})


def _env(switch):
    env = {k: v for k, v in os.environ.items() if k != "TV_AUTO_PRUNE"}
    if switch is not None:
        env["TV_AUTO_PRUNE"] = switch
    return mock.patch.dict(os.environ, env, clear=True)


class ASwitchedOffDeleterIsDormantNotStopped(unittest.TestCase):

    def test_the_premise_three_carried_passes_with_the_deleter_armed_is_stopped(self):
        """The other direction first: armed and carrying the same reels for three passes IS a stall."""
        d = _drain(None)
        self.assertEqual(d.get("state"), rr.DRAIN_STOPPED, d)
        self.assertIs(d.get("on"), True, d)

    def test_his_switch_set_to_off_is_dormant_and_says_his_words(self):
        with _env("off"):
            ok, why = ca.retention_may_act()
        self.assertFalse(ok, "the premise: TV_AUTO_PRUNE=off must refuse the deleter")
        d = _drain("off", stop_why=why)
        self.assertEqual(d.get("state"), rr.DRAIN_DORMANT,
                         "TV_AUTO_PRUNE=off with 3 releasable reels read %r: %r - a switch he set is a decision, "
                         "never a stall" % (d.get("state"), d.get("why")))
        self.assertIs(d.get("on"), False, "the drain published on=%r over a deleter he switched off" % d.get("on"))

    def test_a_misspelt_switch_holds_and_is_not_a_stall(self):
        d = _drain("offf")
        self.assertEqual(d.get("state"), rr.DRAIN_DORMANT, d)
        self.assertIs(d.get("on"), False)

    def test_on_and_unset_stay_armed(self):
        for sw in (None, "on", "1"):
            with _env(sw):
                armed, why = ca.deleter_armed()
            self.assertIs(armed, True, "TV_AUTO_PRUNE=%r disarmed the deleter: %r" % (sw, why))

    def test_one_parse_answers_the_drain_the_act_and_the_lane(self):
        """retention_may_act, deleter_armed and the lane census must refuse on the same switch values."""
        for sw in ("off", "0", "false", "offf", "​0"):
            with _env(sw):
                act_ok, act_why = ca.retention_may_act()
                armed, armed_why = ca.deleter_armed()
                lane_armed, lane_why = SD._armed(SD.LANES["deleter"], allow_import=True)
            self.assertFalse(act_ok, sw)
            self.assertIs(armed, False, "TV_AUTO_PRUNE=%r: the act refuses and deleter_armed says armed" % sw)
            self.assertIs(lane_armed, False,
                          "TV_AUTO_PRUNE=%r: the act refuses and the deleter lane census says armed (%r)"
                          % (sw, lane_why))
            self.assertEqual(armed_why, act_why, "two sentences for one switch: %r vs %r" % (armed_why, act_why))
            self.assertTrue(lane_why, "a disarmed lane must say why it is not acting")

    def test_a_dormant_lane_says_the_switch_not_a_generic_line(self):
        decl = dict(SD.LANES["deleter"])
        with _env("off"):
            armed, why = SD._armed(decl, allow_import=True)
        self.assertIs(armed, False)
        self.assertIn("TV_AUTO_PRUNE", why, "the lane's reason does not name his switch: %r" % why)


RED_PROOF = [
    {
        "why": "REG-1879 - the drain takes `on` from the constant alone again, so a deleter he switched off reads STOPPED",
        "file": "control_app.py",
        "find": "        return _rr_dr.drain_state(_rows, beat=_beat, on=_drain_on,\n",
        "replace": "        return _rr_dr.drain_state(_rows, beat=_beat, on=bool(_PRUNE_SAFE_TO_RUN),\n",
        "matches": 1,
    },
    {
        "why": "REG-1879 - deleter_armed stops asking his switch, so the drain and the lane call it armed while the act refuses",
        "file": "control_app.py",
        "find": "    _sw_ok, _sw_why = _auto_prune_switch()\n    if not _sw_ok:\n        return False, _sw_why\n    return True, \"\"\n",
        "replace": "    return True, \"\"\n",
        "matches": 1,
    },
    {
        "why": "REG-1879 - the deleter lane reads the constant again, so its DORMANT is unreachable",
        "file": "shelf_driver.py",
        "find": "        \"armedFrom\": (\"control_app\", \"deleter_armed\"),\n",
        "replace": "        \"armedFrom\": (\"control_app\", \"_PRUNE_SAFE_TO_RUN\"),\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
