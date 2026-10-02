# -*- coding: utf-8 -*-
"""REG-1737 (#86 gap item 1) — A PADLOCK ASKS WHAT THE ACT ASKS.

The 09-29 gap audit, driven: with no heart census, `self_arming.report()` said 16 of 18 locks OPEN or HARDENED,
the heart drew `reel.route` with an open padlock - and `may("reel.route")` refused every reel ("the heart has
never run here"). report() scored the proof ledger alone; may() also asks the heart and the upstream chain.
Re-measured 10-02 on the signin tree with the heart refusing: open 16, may() True for 0.

  · DRIVEN: every report row carries `permitted` + `permittedWhy`, equal to may() for that lock, with the heart
    refusing AND with it watching - one function (`_verdict`) answers both.
  · DRIVEN: the surface asks the heart once per TTL (it rides the status poll; the gate digest costs 0.2-0.6 s);
    an act still asks fresh every time.
  · DRIVEN: control_app's trim (the sixth field it would have swallowed) carries permitted to the heart and chips.
  · DRIVEN in node: the ONE helper every padlock is drawn from - open only when the evidence tier is OPEN or
    HARDENED and the lock may act. It also ends a sibling: the vault/prune chip tested `state === 'open'`, so a
    HARDENED lock was drawn SHUT and labelled LOCKED.
  · COMPILER: every padlock site asks that helper.
RED_PROOF below. [[the-unjoined-end]] [[unknown-stays-unknown]] [[copy-drift]]
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_arming as SA  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
NEVER_RAN = (False, "UNKNOWN: the heart has never run here - there is no census on this PC")
WATCHED = (True, "instruments watched: planted for this law")


def _reset_memo():
    SA._HEART_SHOWN["at"] = None
    SA._HEART_SHOWN["v"] = None


class EveryRowCarriesTheActsOwnVerdict(unittest.TestCase):

    def setUp(self):
        _reset_memo()
        self.addCleanup(_reset_memo)

    def _rows_and_may(self, heart):
        with mock.patch.object(SA, "_heart_says_watched", lambda: heart):
            _reset_memo()
            rep = SA.report()
            may = {r["lock"]: SA.may(r["lock"]) for r in rep["locks"]}
        return rep, may

    def test_with_no_census_an_earned_lock_is_not_permitted_and_says_why(self):
        rep, may = self._rows_and_may(NEVER_RAN)
        earned = [r for r in rep["locks"] if r.get("state") in (SA.OPEN, SA.HARDENED)]
        self.assertTrue(earned, "PREMISE: no lock has earned OPEN/HARDENED in the tracked ledger - "
                                "this law could not tell the evidence tier from the permission")
        for r in rep["locks"]:
            self.assertIn("permitted", r, "%s: the report row carries no permission" % r["lock"])
            self.assertEqual(r["permitted"], may[r["lock"]][0],
                             "%s: the report says permitted=%r, the act's may() says %r"
                             % (r["lock"], r["permitted"], may[r["lock"]]))
        for r in earned:
            self.assertIs(r["permitted"], False, "%s: drawn open while the heart has never run" % r["lock"])
            self.assertIn("never run", r["permittedWhy"], r)
        self.assertEqual(rep["permitted"], 0)
        self.assertIs(rep["heartOk"], False)

    def test_a_held_row_says_what_holds_it(self):
        rep, _may = self._rows_and_may(NEVER_RAN)
        earned = [r for r in rep["locks"] if r.get("state") in (SA.OPEN, SA.HARDENED)]
        self.assertTrue(earned, "PREMISE: nothing earned")
        self.assertEqual({r["heldBy"] for r in earned}, {"heart"}, [(r["lock"], r["heldBy"]) for r in earned])
        stale = (False, "the instruments' %s - the gates changed since the last prove" % SA._HEART_STALE_PHRASE)
        rep, may = self._rows_and_may(stale)
        for r in rep["locks"]:
            self.assertEqual(r["permitted"], may[r["lock"]][0], r["lock"])
        held = {r["lock"]: r["heldBy"] for r in rep["locks"]
                if r.get("state") in (SA.OPEN, SA.HARDENED) and not r["permitted"]}
        destructive = {k for k, v in list(SA.LOCKS.items()) + list(SA.ROUTES.items()) if v.get("destructive")}
        self.assertTrue(held, "PREMISE: a stale prover held no earned lock")
        self.assertTrue(set(held) <= destructive, "a stale prover held an ordinary lock: %r" % held)
        self.assertEqual(set(held.values()), {"stale"}, held)

    def test_premise_with_the_heart_watching_the_two_still_agree(self):
        rep, may = self._rows_and_may(WATCHED)
        for r in rep["locks"]:
            self.assertEqual(r["permitted"], may[r["lock"]][0], r["lock"])
        self.assertTrue(rep["permitted"] > 0, "PREMISE: nothing is permitted even with the heart watching")


class TheSurfaceReusesTheHeartAndTheActNever(unittest.TestCase):

    def setUp(self):
        _reset_memo()
        self.addCleanup(_reset_memo)

    def test_two_reports_ask_once_and_two_acts_ask_twice(self):
        calls = []

        def heart():
            calls.append(1)
            return WATCHED
        with mock.patch.object(SA, "_heart_says_watched", heart):
            SA.report()
            SA.report()
            self.assertEqual(len(calls), 1, "the status poll paid the heart's digest on every report")
            SA.may("reel.route")
            SA.may("reel.route")
        self.assertEqual(len(calls), 3, "an act reused a remembered heart answer")

    def test_a_remembered_answer_expires(self):
        with mock.patch.object(SA, "_heart_says_watched", lambda: WATCHED):
            SA._heart_for_report(_now=1000.0)
        with mock.patch.object(SA, "_heart_says_watched", lambda: NEVER_RAN):
            self.assertEqual(SA._heart_for_report(_now=1000.0 + SA._HEART_SHOWN_TTL_S + 1), NEVER_RAN)

    def test_a_heart_that_raises_fails_closed(self):
        def boom():
            raise OSError("census unreadable")
        with mock.patch.object(SA, "_heart_says_watched", boom):
            ok, why = SA._heart_for_report(_now=5.0)
        self.assertIs(ok, False)
        self.assertIn("UNKNOWN", why)


class TheTrimCarriesIt(unittest.TestCase):

    def setUp(self):
        _reset_memo()
        self.addCleanup(_reset_memo)

    def test_the_status_poll_and_the_heart_see_the_permission(self):
        import control_app as ca
        with mock.patch.object(SA, "_heart_says_watched", lambda: NEVER_RAN):
            st = ca._self_arming_state()
        self.assertTrue(st.get("locks"), "PREMISE: the lock state carried no locks: %r" % (st,))
        for l in st["locks"]:
            self.assertIs(l.get("permitted"), False, "%s: the trim dropped the permission: %r" % (l.get("lock"), l))
            self.assertTrue(l.get("permittedWhy"), l)
            self.assertTrue(l.get("heldBy"), "%s: the trim dropped what holds it: %r" % (l.get("lock"), l))
        self.assertEqual(st.get("permitted"), 0)
        self.assertIn("never run", st.get("heartWhy") or "")


def _node():
    return shutil.which("node") or shutil.which("nodejs")


def _helper_source():
    src = io.open(UI, encoding="utf-8", errors="replace").read()
    i = src.find("window._lockOpen = function(l){")
    assert i >= 0, "window._lockOpen is gone from control_ui.html"
    end = src.find("\n};", i)
    assert end > i, "window._lockOpen has no closing brace where one is expected"
    return src[i:end + 3]


@unittest.skipUnless(_node(), "node is not installed - the shipped helper cannot be driven")
class TheOneHelperEveryPadlockAsks(unittest.TestCase):

    def _open(self, rows):
        prog = ("var window = {};\n" + _helper_source() + "\n"
                "console.log(JSON.stringify(" + json.dumps(rows) + ".map(function(l){ return window._lockOpen(l); })));\n")
        p = subprocess.run([_node(), "-"], input=prog, capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise AssertionError("node could not run the shipped helper: %s" % (p.stderr or "")[:300])
        return json.loads(p.stdout.strip().split("\n")[-1])

    def test_open_needs_the_evidence_and_the_permission(self):
        got = self._open([{"state": "HARDENED", "permitted": False}, {"state": "OPEN", "permitted": False}])
        self.assertEqual(got, [False, False], "an earned lock that may not act was drawn OPEN")

    def test_a_hardened_lock_that_may_act_is_open(self):
        self.assertEqual(self._open([{"state": "HARDENED", "permitted": True}, {"state": "HARDENED"}]), [True, True],
                         "a HARDENED lock was drawn shut")

    def test_premise_the_evidence_still_decides_when_it_is_short(self):
        self.assertEqual(self._open([{"state": "LOCKED", "permitted": True}, {"state": "UNPROVEN"}, None]),
                         [False, False, False])


class EveryPadlockSiteAsksTheHelper(unittest.TestCase):

    def test_no_padlock_decides_open_from_state_alone(self):
        src = io.open(UI, encoding="utf-8", errors="replace").read()
        calls = [m.start() for m in re.finditer(r"window\._lockMark\(", src)]
        self.assertEqual(len(calls), 2, "PREMISE: the padlock call sites moved (%d)" % len(calls))
        for i in calls:
            arg = src[i + len("window._lockMark("):].split(",", 1)[0].strip()
            self.assertIn(arg, ("_isOpen", "window._lockOpen(L)"),
                          "a padlock decides open by itself: _lockMark(%s, ...)" % arg)
        self.assertIn("var _isOpen = !!l && window._lockOpen(l);", src, "the chip's open-ness is not the helper's")
        self.assertIn("      var open = window._lockOpen(L);\n", src, "the river map's padlock is not the helper's")

    def test_the_helper_asks_the_permission_even_where_node_is_missing(self):
        # REG-1736's lesson, applied before it can recur: the node class above is skipped on a PC with no node,
        # and a red-proof whose only catching case is skipped reads BLIND there. This reads the helper's own
        # return statement, bounded by the helper, on every PC.
        body = _helper_source()
        ret = [ln.strip() for ln in body.split("\n") if ln.strip().startswith("return (")]
        self.assertEqual(len(ret), 1, "PREMISE: the helper's verdict line moved: %r" % ret)
        self.assertIn("l.permitted !== false", ret[0], "the helper opens on the evidence tier alone: %s" % ret[0])


RED_PROOF = [
    {"why": "REG-1737 - report() scores the ledger alone again: an earned lock reads permitted with no census",
     "file": "self_arming.py",
     "find": "        ok, why = _verdict(lock, spec, rows, heart[0], heart[1])\n",
     "replace": "        ok, why = score(lock, rows).get(\"state\") in (OPEN, HARDENED), \"\"\n",
     "matches": 1},
    {"why": "REG-1737 - the surface asks the heart on every report again (the digest on every status poll)",
     "file": "self_arming.py",
     "find": "    if v is not None and at is not None and 0 <= now - at < _HEART_SHOWN_TTL_S:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1737 - a held lock no longer says what holds it (the fan prints an earned lock's sentence)",
     "file": "self_arming.py",
     "find": "        return k if k in (\"stale\", \"blind\") else \"heart\"\n",
     "replace": "        return \"evidence\"\n",
     "matches": 1},
    {"why": "REG-1737 - the trim swallows the permission again",
     "file": "control_app.py",
     "find": "                   \"permitted\": l.get(\"permitted\"), \"permittedWhy\": l.get(\"permittedWhy\"),\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1737 - a padlock opens on the evidence tier alone again",
     "file": "control_ui.html",
     "find": "  return (s === 'OPEN' || s === 'HARDENED') && l.permitted !== false;\n",
     "replace": "  return (s === 'OPEN' || s === 'HARDENED');\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
