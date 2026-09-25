# -*- coding: utf-8 -*-
"""#240 — EACH CONSOLE SHOWS ITS OWN COUNTS; A SYNCED LEDGER IS NEVER CALLED "NEVER SYNCED".

Konyo, 2026-09-25, from his ALT: *"when i look at dean it shows me his sets/and uniques and runerword. but
when i look at grokbot or KONYO from my ALT PC on my windows i dont see the numbers anywahere for the
others.. its like as if im the same person on all three different users??"*

MEASURED on the ALT's own /api/fleet: the rows ARE individual - Konyo 134/312/99, GrokBot 128/309/99, the
ALT 2/4/0, Dean 132/0/98, and /api/fleet_compare answers each one separately. What hid them: every v3504
tally carried measured=False, "runewords, sets, uniques were never synced", beside a ledgerVerdict whose
three ledgers all said SYNCED, and the card prints "- never synced" in place of a number when measured is
False. Dean's older build seals no `measured`, so his were the only numbers left.

TWO DEFECTS: grail_tally asked the authority while the tally still held its starting ok:False (so every
verdict read ok:False), and the seal read that `ok` as "is it a count" and named every ledger whose
provenance was not "EARNED" - a word ledger_authority has never said. The v3389 law was written in that
word too, so it was green on fiction.

  · DRIVEN (the real classify -> seal chain, his live shapes): a SYNCED console is a count on every ledger.
  · DRIVEN: one never-synced store does not blank its neighbours - the ALT's 2 and 4 stay counts.
  · DRIVEN: an empty board is still refused (the v3389 baseline).
  · DRIVEN (node, the real relay shaper): `measuredBy` crosses; a non-boolean arrives as null.
  · DRIVEN (node, the card's own reader): each bar reads its own ledger; the row bit only for an old peer.
  · DRIVEN: the doctor row goes red on a real count hidden as never synced, and green once fixed.
  · JOINED: grail_tally no longer classifies before the seal.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import control_app as CA  # noqa: E402
import console_doctor as CD  # noqa: E402

NODE = shutil.which("node")
LEDGERS = ("sets", "uniques", "runewords")


def _tally(s, u, r, seed=False):
    """The shape grail_tally builds, BEFORE the seal: ok still False, exactly as in production."""
    return {"ok": False, "why": None, "sets": {"have": s, "total": 135},
            "uniques": {"have": u, "total": 403}, "runewords": {"have": r, "total": 99},
            "onOwnerSeed": seed}


def _sealed(s, u, r, seed=False):
    return CA._seal_tally_verdict(_tally(s, u, r, seed), "carried no counts", world=None)


def _src(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def _node(js):
    r = subprocess.run([NODE, "-e", js], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not run the shipped code - UNKNOWN, not passing: %s" % r.stderr[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheSealAnswersPerLedger(unittest.TestCase):

    def test_his_synced_console_is_a_count_on_every_ledger(self):
        out = _sealed(134, 312, 99)
        self.assertEqual(out.get("measuredBy"), {"sets": True, "uniques": True, "runewords": True},
                         "a SYNCED console's ledgers were not called counts: %r" % (out.get("measuredWhy"),))
        self.assertIs(out["measured"], True, "his 134/312/99 would print as '- never synced' again")
        self.assertIs(out["ledgerVerdict"].get("ok"), True,
                      "the authority was asked before `ok` was sealed - every verdict reads ok:False")

    def test_one_never_synced_store_does_not_blank_its_neighbours(self):
        out = _sealed(2, 4, 0)
        self.assertEqual(out["measuredBy"], {"sets": True, "uniques": True, "runewords": False})
        self.assertIsNone(out["measured"], "a mixed row claimed one answer for all three ledgers")
        self.assertIn("runewords", out["measuredWhy"])
        self.assertNotIn("sets", out["measuredWhy"].split("never synced")[0].split(":")[-1])

    def test_an_empty_board_is_still_refused(self):
        out = _sealed(0, 0, 0)
        self.assertIs(out["measured"], False, "the v3389 baseline regressed: an empty store reads as a count")
        self.assertEqual(set(out["measuredBy"].values()), {False})

    def test_grail_tally_does_not_classify_before_the_seal(self):
        names = CA.grail_tally.__code__.co_names
        self.assertNotIn("classify_row", names, "grail_tally asks the authority before `ok` is decided again")
        self.assertEqual(_src("tv/control_app.py").count(
            'return _seal_tally_verdict(out, "the board answered but carried no counts", world=_world)'), 1)


@unittest.skipIf(NODE is None, "node is absent - these laws are UNMEASURED, not passing")
class TheRelayAndTheCardCarryIt(unittest.TestCase):

    def _shape(self, tally):
        src = _src("functions/api/console.js")
        i = src.index("    tally: (function (t) {")
        j = src.index("    })(body.tally),", i)
        fn = "(" + src[i + len("    tally: "):j + len("    })")] + ")"
        return _node("var shape = %s;\nconsole.log(JSON.stringify(shape(%s)));" % (fn, json.dumps(tally)))

    def test_measuredBy_crosses_the_relay(self):
        t = {"ok": True, "at": 1, "sets": {"have": 2, "total": 135}, "uniques": {"have": 4, "total": 403},
             "runewords": {"have": 0, "total": 99}, "measured": None,
             "measuredBy": {"sets": True, "uniques": True, "runewords": False, "stranger": True}}
        out = self._shape(t)
        self.assertEqual(out.get("measuredBy"), {"sets": True, "uniques": True, "runewords": False},
                         "the relay dropped or widened measuredBy - the seventh joint")

    def test_a_non_boolean_arrives_as_unknown(self):
        t = {"ok": True, "at": 1, "sets": {"have": 2, "total": 135}, "measuredBy": {"sets": "yes"}}
        self.assertEqual(self._shape(t).get("measuredBy"), {"sets": None})

    def _meas(self, t, lab):
        ui = _src("tv/control_ui.html")
        a = ui.index("        var _measOf = function (lab) {")
        b = ui.index("        };\n", a) + len("        };\n")
        return _node("var t = %s;\n%s\nconsole.log(JSON.stringify(_measOf(%s)));"
                     % (json.dumps(t), ui[a:b], json.dumps(lab)))

    def test_each_bar_reads_its_own_ledger(self):
        t = {"measured": None, "measuredBy": {"sets": True, "runewords": False}}
        self.assertIs(self._meas(t, "sets"), True)
        self.assertIs(self._meas(t, "runewords"), False)
        self.assertIsNone(self._meas(t, "uniques"), "a ledger with no answer was guessed")

    def test_an_old_peer_falls_back_to_the_row_bit(self):
        self.assertIs(self._meas({"measured": False}, "sets"), False)

    def test_an_old_seal_is_read_through_its_own_provenance(self):
        """MEASURED on GrokBot's glass after 3cd6bb26: Konyo and the ALT, still on the old seal, read "—"
        although their tallies carry numbers. Their ledgerVerdict rows say SYNCED; that wins over the row bit."""
        old = {"measured": False, "ledgerVerdict": {"ok": False, "ledgers": [
            {"ledger": "sets", "provenance": "SYNCED"}, {"ledger": "runewords", "provenance": "UNSYNCED"}]}}
        self.assertIs(self._meas(old, "sets"), True, "an old peer's synced count is still hidden as never synced")
        self.assertIs(self._meas(old, "runewords"), False)
        self.assertIs(self._meas(old, "uniques"), False, "no provenance row: the row bit stays the fallback")


class TheDoctorSeesAHiddenCount(unittest.TestCase):

    def _run(self, tally):
        row = {"machine": "m1", "nickname": "Peer", "tally": tally}
        keep = CA._FLEET_PRESENCE_CACHE.get("d")
        CA._FLEET_PRESENCE_CACHE["d"] = {"online": [row], "offline": []}
        try:
            return CD._check_a_tally_agrees_with_its_own_ledger_verdict()
        finally:
            CA._FLEET_PRESENCE_CACHE["d"] = keep

    def _verdict(self):
        return {"ok": False, "ledgers": [{"ledger": k, "provenance": "SYNCED"} for k in LEDGERS]}

    def test_a_real_count_hidden_as_never_synced_is_missing(self):
        """The shape every v3504 console published on 2026-09-25."""
        t = {"sets": {"have": 128}, "uniques": {"have": 309}, "runewords": {"have": 99},
             "measured": False, "ledgerVerdict": self._verdict()}
        st, why = self._run(t)
        self.assertEqual(st, CD.MISSING, "the doctor stayed quiet over hidden counts: %s" % why)
        self.assertIn("hidden as never synced", why)

    def test_the_fixed_shape_agrees(self):
        t = {"sets": {"have": 128}, "uniques": {"have": 309}, "runewords": {"have": 99},
             "measured": True, "measuredBy": {k: True for k in LEDGERS}, "ledgerVerdict": self._verdict()}
        st, why = self._run(t)
        self.assertEqual(st, CD.OK, why)

    def test_a_never_synced_zero_read_as_progress_is_still_missing(self):
        v = {"ok": True, "ledgers": [{"ledger": "sets", "provenance": "UNSYNCED"}]}
        st, why = self._run({"sets": {"have": 0}, "ledgerVerdict": v})
        self.assertEqual(st, CD.MISSING, why)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#240 - an old peer's broken row bit wins again; Konyo and the ALT read '-' on every other console",
        "file": "tv/control_ui.html",
        "find": "              if (pv === 'SYNCED' || pv === 'SEEDED' || pv === 'MANUAL') return true;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#240 - a SYNCED ledger is called never synced again; his 134/312/99 print as '- never synced'",
        "file": "tv/control_app.py",
        "find": '_PROVENANCE_MEASURED = {"SYNCED": True, ',
        "replace": '_PROVENANCE_MEASURED = {"SYNCED": False, ',
        "matches": 1,
    },
    {
        "why": "#240 - the seal no longer asks the authority itself, so grail_tally's rows carry no verdict",
        "file": "tv/control_app.py",
        "find": "    if world is not _NO_WORLD:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#240 - the relay drops the per-ledger answer: the seventh joint of the fleet tally",
        "file": "functions/api/console.js",
        "find": "                        if (k in m) o[k] = (typeof m[k] === 'boolean') ? m[k] : null;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#240 - the card reads the row bit for every bar again; one never-synced store blanks all three",
        "file": "tv/control_ui.html",
        "find": "          if (by && typeof by === 'object') return (typeof by[lab] === 'boolean') ? by[lab] : null;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#240 - the doctor is blind to a real count hidden as never synced, as it was on 2026-09-25",
        "file": "tv/console_doctor.py",
        "find": "            elif want is True and said is False:\n",
        "replace": "            elif False:\n",
        "matches": 1,
    },
]
