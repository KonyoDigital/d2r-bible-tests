# -*- coding: utf-8 -*-
"""#151 - A LOW DISK IS A SIGN UNDER THE ONLINE LIGHT, NOT A NUMBER SOMEONE HAS TO GO LOOKING FOR.

His words, 2026-10-21: "this cant happen in general... it was a mistake that it was this low" and "a more cool and
designed style for the memory/gigabytes running low, like a warning sign under the online area". That day his Mac sat at
4.0 GB free - under the 8 GB ON AIR floor and under the room heart2's proof lanes need - and the only words saying so
were inside the retention panel and a prove log the push cuts to 24 lines.

The console now publishes diskSign on every status call: free GB read NOW (decimal GB); amber under ON_AIR_FLOOR_GB;
red under the room the proof lanes need, derived from heart2's own constants (UNKNOWN, never red on a guess, when they
cannot be read); what holds the space measured by its own lane (bounded walks, never while he plays or the machine is
busy, "at least" when a walk runs out of time); and the one action that frees room, on amber and red only. The console
paints it under the ONLINE light on every poll. Fixtures only: a temp folder, stubbed free space. RED_PROOF below.
[[unknown-stays-unknown]] [[stale-reading]] [[heart-first]]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
from cb_node_harness import NODE  # noqa: E402
import control_app as ca  # noqa: E402
import heart2 as h2  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")
CA = os.path.join(HERE, "control_app.py")


def _read(p):
    with open(p, encoding="utf-8") as fh:
        return fh.read()


class TheLevelIsMeasuredNeverGuessed(unittest.TestCase):

    def test_red_amber_ok_and_unknown(self):
        L = ca.disk_sign_level
        self.assertEqual(L(30.0, 8.0, 5.97), "ok")
        self.assertEqual(L(7.0, 8.0, 5.97), "amber")
        self.assertEqual(L(4.0, 8.0, 5.97), "red")
        self.assertEqual(L(None, 8.0, 5.97), "unknown", "a free space nobody read is not ok")
        self.assertEqual(L(True, 8.0, 5.97), "unknown")

    def test_an_unknown_lane_floor_is_never_red_on_a_guess(self):
        self.assertEqual(ca.disk_sign_level(3.0, 8.0, None), "amber")

    def test_the_red_floor_comes_from_heart2s_own_constants(self):
        with mock.patch.object(h2, "PROVE_WORKERS", 2):
            want = round((h2.LANE_DISK_FLOOR_MB + h2.LANE_DISK_MB * 2) * 1048576 / 1e9, 2)
            self.assertEqual(ca._disk_sign_floor_gb(), want, "the red floor is typed, not derived")


class WhatHoldsTheSpaceIsMeasuredBounded(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="disksign_")
        self.addCleanup(shutil.rmtree, self.d, True)
        for i, n in enumerate((100, 2000, 30)):
            sub = os.path.join(self.d, "s%d" % i)
            os.makedirs(sub)
            with open(os.path.join(sub, "f.bin"), "wb") as fh:
                fh.write(b"x" * n)

    def test_a_walk_counts_every_byte_and_says_when_it_ran_out_of_time(self):
        self.assertEqual(ca._disk_walk(self.d, 30), (2130, True))
        self.assertEqual(ca._disk_walk(os.path.join(self.d, "absent"), 30), (0, True))
        ticks = iter([0.0] + [10.0] * 50)
        b, done = ca._disk_walk(self.d, 1.0, _now=lambda: next(ticks))
        self.assertFalse(done, "a walk past its budget called its partial count a total")

    def test_biggest_first_each_with_its_action(self):
        rows = ca._disk_sign_measure([("small", os.path.join(self.d, "s2"), "a"), ("big", os.path.join(self.d, "s1"), "b")],
                                     budget_s=30)
        self.assertEqual([r["name"] for r in rows], ["big", "small"])
        self.assertEqual(rows[0]["action"], "b")

    def test_the_lane_never_walks_while_he_plays_or_the_machine_is_busy(self):
        saved = dict(ca._DISK_SIGN)
        self.addCleanup(lambda: (ca._DISK_SIGN.clear(), ca._DISK_SIGN.update(saved)))
        cand = [("x", self.d, "act")]
        w0 = ca._DISK_SIGN.get("worked") or 0
        ca._disk_sign_once(now_ms=1, playing=True, busy_pct=0, candidates=cand)
        self.assertEqual(ca._DISK_SIGN.get("worked") or 0, w0, "it walked the disk while he played")
        self.assertIn("playing", ca._DISK_SIGN["say"])
        ca._disk_sign_once(now_ms=2, playing=False, busy_pct=95.0, candidates=cand)
        self.assertEqual(ca._DISK_SIGN.get("worked") or 0, w0, "it walked the disk on a busy machine")
        r = ca._disk_sign_once(now_ms=3, playing=False, busy_pct=5.0, candidates=cand)
        self.assertEqual((r["worked"], r["owed"], r["measuredAt"]), (w0 + 1, 0, 3))


class TheSignIsPublishedAndPainted(unittest.TestCase):

    def setUp(self):
        saved = dict(ca._DISK_SIGN)
        self.addCleanup(lambda: (ca._DISK_SIGN.clear(), ca._DISK_SIGN.update(saved)))
        ca._DISK_SIGN.update(consumers=[{"name": "his reels", "gb": 5.8, "atLeast": False, "action": "the reel prune"}],
                             measuredAt=1000)

    def test_amber_names_the_action_and_ok_does_not(self):
        a = ca.disk_sign_payload(_free=lambda: 7.0e9)
        self.assertEqual((a["freeGb"], a["level"], a["action"]), (7.0, "amber", "the reel prune"))
        o = ca.disk_sign_payload(_free=lambda: 30.0e9)
        self.assertEqual((o["level"], o["action"]), ("ok", None), "an ok disk was told how to free room")

    def test_an_unreadable_disk_is_unknown_and_says_why(self):
        def boom():
            raise OSError("no such volume")
        u = ca.disk_sign_payload(_free=boom)
        self.assertEqual((u["freeGb"], u["level"]), (None, "unknown"))
        self.assertIn("could not be read", u["why"])

    def test_the_status_carries_it_and_the_roster_runs_its_lane(self):
        s = _read(CA)
        self.assertEqual(s.count('        "diskSign": _t("diskSign", disk_sign_payload),'), 1, "the status does not carry the sign")
        self.assertEqual(s.count('        ("tvd-disk-sign", _disk_sign_loop),\n'), 1, "the lane is not in the roster")
        self.assertIn('"tvd-river-warm", "tvd-disk-sign")', s, "a harness console would walk his Grok folder")

    def test_the_console_paints_it_under_the_online_light_on_every_poll(self):
        u = _read(UI)
        self.assertEqual(u.count('<div class="disk-sign" id="disk-sign" data-level="unknown" role="status">'), 1)
        self.assertLess(u.index('<span id="bug-txt">OFF AIR</span>'), u.index('id="disk-sign"'),
                        "the sign is not under the ONLINE light")
        self.assertEqual(u.count("window._diskSignPaint(st.diskSign); } catch(e){}   // #151"), 1,
                         "the status painter never paints the sign")


@unittest.skipIf(NODE is None, "node is not on this machine - UNMEASURED here, not passing")
class TheConsolesWords(unittest.TestCase):

    def words(self, d):
        u = _read(UI)
        head = "  window._diskSignWords = function(d, now){\n"
        self.assertEqual(u.count(head), 1)
        i = u.index(head)
        fn = u[i:u.index("\n  };\n", i) + 5]
        js = "var window = {};\n" + fn + "\nprocess.stdout.write(JSON.stringify(window._diskSignWords(%s, 1000 + 7 * 60000)));" % json.dumps(d)
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise AssertionError("the console's words would not run in node: %s" % r.stderr[-500:])
        return json.loads(r.stdout)

    def test_each_level_reads_as_itself(self):
        base = {"lowGb": 8.0, "criticalGb": 5.97, "consumers": None, "lane": {"say": "not measured yet"}}
        self.assertEqual(self.words(dict(base, level="ok", freeGb=22.1))["text"], "22.1 GB free")
        self.assertEqual(self.words(dict(base, level="amber", freeGb=7.0))["text"], "⚠ 7.0 GB · low")
        self.assertEqual(self.words(dict(base, level="red", freeGb=4.0))["text"], "⛔ 4.0 GB · proofs slow")
        u = self.words(dict(base, level="unknown", freeGb=None, why="free space could not be read (OSError)"))
        self.assertEqual(u["text"], "disk UNKNOWN", "an unread disk was given a number")
        self.assertIn("could not be read", u["title"])
        self.assertEqual(self.words(None)["text"], "disk —")

    def test_the_hover_names_the_floors_the_consumers_with_their_age_and_the_action(self):
        w = self.words({"level": "amber", "freeGb": 7.0, "lowGb": 8.0, "criticalGb": 5.97, "measuredAt": 1000,
                        "consumers": [{"name": "his reels", "gb": 5.8, "atLeast": True}], "action": "the reel prune"})
        for want in ("amber under 8 GB", "red under 6.0 GB", "measured 7 min ago", "his reels at least 5.80 GB",
                     "to free room: the reel prune"):
            self.assertIn(want, w["title"], w["title"])


RED_PROOF = [
    {"why": "#151 - a disk under the ON AIR floor reads as ok",
     "file": "tv/control_app.py",
     "find": "    if free_gb < low_gb:\n        return \"amber\"\n",
     "replace": "",
     "matches": 1},
    {"why": "#151 - an UNKNOWN proof-lane floor paints red on a guess",
     "file": "tv/control_app.py",
     "find": "    if isinstance(critical_gb, (int, float)) and not isinstance(critical_gb, bool) and free_gb < critical_gb:\n",
     "replace": "    if free_gb < (critical_gb or 99):\n",
     "matches": 1},
    {"why": "#151 - the red floor is a typed number, not heart2's own",
     "file": "tv/control_app.py",
     "find": "        return round(mib * 1048576 / 1e9, 2)\n",
     "replace": "        return 5.6\n",
     "matches": 1},
    {"why": "#151 - an unread free space reads as ok",
     "file": "tv/control_app.py",
     "find": "    if not isinstance(free_gb, (int, float)) or isinstance(free_gb, bool):\n        return \"unknown\"\n",
     "replace": "    if not isinstance(free_gb, (int, float)) or isinstance(free_gb, bool):\n        return \"ok\"\n",
     "matches": 1},
    {"why": "#151 - a walk past its budget calls its partial count the total",
     "file": "tv/control_app.py",
     "find": "            if _now() > t_end:\n                return total, False\n",
     "replace": "",
     "matches": 1},
    {"why": "#151 - the lane walks his disk while he plays",
     "file": "tv/control_app.py",
     "find": "    if _play:\n        _DISK_SIGN.update(lastTs=now, say=\"he is playing",
     "replace": "    if False:\n        _DISK_SIGN.update(lastTs=now, say=\"he is playing",
     "matches": 1},
    {"why": "#151 - the consumers are not ordered biggest first",
     "file": "tv/control_app.py",
     "find": "    rows.sort(key=lambda r: -(r[\"bytes\"] if isinstance(r[\"bytes\"], int) else -1))",
     "replace": "    pass",
     "matches": 1},
    {"why": "#151 - an ok disk is told how to free room",
     "file": "tv/control_app.py",
     "find": "            \"action\": ((top or {}).get(\"action\") if lvl in (\"red\", \"amber\") else None),\n",
     "replace": "            \"action\": ((top or {}).get(\"action\")),\n",
     "matches": 1},
    {"why": "#151 - an unread disk is painted as a number",
     "file": "tv/control_ui.html",
     "find": "    var text = !num ? 'disk UNKNOWN' :",
     "replace": "    var text = !num ? '0.0 GB free' :",
     "matches": 1, "needs": "node"},
    {"why": "#151 - the status painter never paints the sign",
     "file": "tv/control_ui.html",
     "find": "    try { if (typeof window._diskSignPaint === 'function') window._diskSignPaint(st.diskSign); } catch(e){}   // #151\n",
     "replace": "",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
