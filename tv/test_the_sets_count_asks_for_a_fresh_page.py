# -*- coding: utf-8 -*-
"""#228 — THE SETS COUNT ASKS HIM FOR A FRESH PAGE; IT DOES NOT ACCUSE HIM.

HIS SCREENSHOT, 2026-09-24 11:13: the chronicle-sweep panel drew "the board and the game do not add
up" and "the not-found readings here cannot be dated" as LOUD cards that read as if he had done
something wrong. Measured on his live result the same day: the "16 rows the game says you do not
have" came from a Remaining page filmed 2026-08-21 (the card said 24.5 days old; it was 34), the
game's own bar on 3 recent frames agreed with his board, and the next-action promised "the two wrong
rows" for a finding of 16. The one line that was his - film a new Remaining page - is a WAITING ON
YOU question now.

  · DRIVEN (doctor): the new check reads the saved sweep, says MISSING in his words with the page's
    age counted from the PAGE (readAt), not from the stored ageDays; OK and absent never ask him.
  · DRIVEN (asks): attach_asks gives exactly one well-formed question, keyed to that page.
  · DRIVEN (UI, node): the REAL _chronWarnStrip renders the card calm (unk) and folded, with the
    real count, the page's true age and the pointer to WAITING ON YOU; "two wrong rows" is gone.
RED_PROOF below.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as cd  # noqa: E402
import control_app as ca  # noqa: E402

NAMES = ["Aldur's Deception (armor)", "Death's Guard (belt)", "Death's Hand (gloves)",
         "Griswold's Honor (shield)", "Griswold's Redemption (scepter)", "Horazon's Dominion (armor)",
         "Horazon's Secrets (grimoire)", "Immortal King's Soul Cage (armor)", "Laying of Hands (bramble mitts)",
         "Natalya's Mark (claws)", "Sazabi's Ghost Liberator (balrog skin)", "Taebaek's Glory (ward)",
         "Tal Rasha's Adjudication (amulet)", "Tal Rasha's Guardianship (armor)",
         "Tancred's Hobnails (light plated boots)", "Telling of Beads (amulet)"]


def _iso_days_ago(d):
    t = datetime.fromtimestamp(time.time() - d * 86400.0, tz=timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _his_calibration_at(read_ts, stored_age=24.46):
    cal = _his_calibration(stored_age=stored_age)
    t = datetime.fromtimestamp(read_ts, tz=timezone.utc)
    cal["exact"]["reading"]["readAt"] = t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return cal


def _his_calibration(page_days_ago=34.0, stored_age=24.46, ok=False):
    """His live shape, 2026-09-24: 132 found, 19 missing, roster 135, surplus 16, all 16 named."""
    reading = {"readAt": _iso_days_ago(page_days_ago), "ageDays": stored_age, "source": "sets.json"}
    return {"ok": ok, "say": ("⚠ 132 found + 19 missing = 151, which is 16 MORE than the 135-piece roster. "
                             "⚠ THE TWO INSTRUMENTS DISAGREE"),
            "exact": {"boardFound": 132, "gameMissing": 19, "rosterTotal": 135,
                      "surplus": 16 if not ok else 0, "impliedFound": 116, "ok": ok, "reading": reading,
                      "named": [] if ok else [{"name": n, "boardDate": None, "undated": True} for n in NAMES],
                      "say": "arithmetic"},
            "bar": {"ok": True, "frames": 3, "gameFill": 1.0, "boardPct": 0.9778}}


class _SavedSweep(unittest.TestCase):

    def setUp(self):
        self._path = ca._CHRON_RESULT_PATH
        self.tmp = tempfile.mkdtemp(prefix="remaining-page-")
        ca._CHRON_RESULT_PATH = os.path.join(self.tmp, "chron_last_result.json")

    def tearDown(self):
        ca._CHRON_RESULT_PATH = self._path
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _save(self, cal):
        with io.open(ca._CHRON_RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump({"savedTs": 1, "result": {"calibration": cal}, "proposal": {}}, f)

    def _row(self):
        state, why = cd._check_a_fresh_remaining_page_would_settle_the_sets_count()
        return cd.attach_asks([{"check": "a fresh remaining page", "state": state, "why": why}])[0]


class TheDoctorAsksInHisWords(_SavedSweep):

    def test_his_live_shape_is_missing_in_his_words(self):
        self._save(_his_calibration())
        row = self._row()
        self.assertEqual(row["state"], cd.MISSING)
        for want in ("132 set pieces ticked", "still listed 19 as missing", "16 of your ticked rows",
                     "agrees with your board", "A new Remaining page settles it"):
            self.assertIn(want, row["why"], "the doctor's sentence lost %r: %r" % (want, row["why"]))

    def test_the_page_age_is_counted_from_the_page_not_the_sweep(self):
        self._save(_his_calibration(page_days_ago=34.0, stored_age=24.46))
        why = self._row()["why"]
        self.assertIn("34 days old", why, "the age came from the stored sweep, not the page: %r" % why)
        self.assertNotIn("24 days", why)

    def test_it_asks_exactly_one_well_formed_question_keyed_to_the_page(self):
        cal = _his_calibration()
        self._save(cal)
        asks = self._row()["asks"]
        self.assertEqual(len(asks), 1, "the sets count is out and asks him nothing")
        self.assertEqual(cd.ask_problems(asks[0]), [])
        self.assertEqual(asks[0]["kind"], "do")
        self.assertEqual(asks[0]["fp"], "remaining-page:%s" % cal["exact"]["reading"]["readAt"])
        self.assertEqual([a["key"] for a in asks[0]["answers"]], ["filmed", "week", "skip"])
        self.assertIn("16 set rows", asks[0]["q"])
        self.assertEqual(cd.owner_of("a fresh remaining page"), "you")

    def test_an_agreeing_page_asks_nothing(self):
        self._save(_his_calibration(ok=True))
        row = self._row()
        self.assertEqual(row["state"], cd.OK)
        self.assertEqual(row["asks"], [])

    def test_a_sweep_that_never_ran_is_unknown_and_asks_nothing(self):
        row = self._row()                          # no file written
        self.assertEqual(row["state"], cd.UNKNOWN)
        self.assertEqual(row["asks"], [], "a question built on a comparison nobody took")

    def test_missing_counts_are_unknown_and_ask_nothing(self):
        """the second eye on v3498: this printed 'Your board has None set pieces' and still asked"""
        cal = _his_calibration()
        del cal["exact"]["boardFound"]
        self._save(cal)
        row = self._row()
        self.assertEqual(row["state"], cd.UNKNOWN)
        self.assertNotIn("None", row["why"])
        self.assertEqual(row["asks"], [])

    def test_a_wrong_shaped_file_is_unknown_never_a_traceback(self):
        for shape in ({"result": ["not", "a", "dict"]}, {"result": {"calibration": "a string"}},
                      {"result": {"calibration": {"ok": False, "exact": ["x"]}}},
                      {"result": {"calibration": dict(_his_calibration(), exact=dict(_his_calibration()["exact"], named=7))}}):
            with io.open(ca._CHRON_RESULT_PATH, "w", encoding="utf-8") as f:
                json.dump(shape, f)
            state, why = cd._check_a_fresh_remaining_page_would_settle_the_sets_count()   # must not raise
            self.assertIn(state, (cd.UNKNOWN, cd.MISSING), "shape %r read %r" % (shape, state))

    def test_the_doctor_rounds_a_half_day_the_way_the_card_does(self):
        """the second eye on v3498: Python round() is half-even, Math.round is half-up - 4.5 days read
        '4 days' in the doctor and '5 days' on the card"""
        fixed = 1790000000.0
        real = cd.time.time
        cd.time.time = lambda: fixed
        try:
            self._save(_his_calibration_at(fixed - 4.5 * 86400))
            why = cd._check_a_fresh_remaining_page_would_settle_the_sets_count()[1]
        finally:
            cd.time.time = real
        self.assertIn("5 days old", why)

    def test_it_is_declared_in_every_registry_and_runs_every_tick(self):
        self.assertIn("a fresh remaining page", {n for n, _ in cd.CHECKS})
        self.assertIn("a fresh remaining page", cd.WATCHES)
        # an UNMEASURED (skipped periodic) row carries no question, so a periodic asking row would
        # leave his card on 5 of every 6 ticks
        self.assertNotIn("a fresh remaining page", cd.PERIODIC)


UI = os.path.join(HERE, "control_ui.html")


def _strip_source():
    with io.open(UI, encoding="utf-8") as f:
        src = f.read()
    i = src.index("  function _cwPageAgeDays(rd) {")
    j = src.index("  function _chronNames(", i)
    return src[i:j]


def _render_at(res, now_ms):
    return _render(res, now_ms=now_ms)


def _render(res, now_ms=None):
    js = """
    function escC(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]); }); }
    var _cwOpen = {};
    %s
    %s
    console.log(JSON.stringify(_chronWarnStrip(%s)));
    """ % (("Date.now = function(){ return %d; };" % now_ms) if now_ms else "", _strip_source(), json.dumps(res))
    r = subprocess.run([shutil.which("node"), "-"], input=js, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("node could not evaluate the strip - UNKNOWN, not passing: %s" % r.stderr[:600])
    return json.loads(r.stdout.strip())


def _card(html, rank):
    m = re.search(r'<div class="chron-warn ([^"]*)" data-rank="%s"[^>]*>(.*?)</div>' % re.escape(rank), html)
    return (m.group(1).split(), m.group(2)) if m else (None, None)


@unittest.skipIf(shutil.which("node") is None, "node is absent - this law is UNMEASURED, not passing")
class TheCardIsCalmInformation(unittest.TestCase):

    def setUp(self):
        cal = _his_calibration(page_days_ago=34.0, stored_age=24.46)
        self.html = _render({
            "calibration": cal,
            "denial": {"denied": [{"name": "Shako"}], "reading": cal["exact"]["reading"]},
            "notFoundDatable": {"ok": False, "say": "19 of 394 not-found reading(s) carry NO reel"},
        })

    def test_premise_the_card_renders(self):
        cls, body = _card(self.html, "1")
        self.assertIsNotNone(cls, "premise: rank 1 did not render at all: %r" % self.html[:400])

    def test_it_is_calm_and_folded_never_red(self):
        cls, body = _card(self.html, "1")
        self.assertIn("unk", cls)
        self.assertIn("settled", cls, "the card that is not his to fix renders LOUD again")
        self.assertNotIn("bad", cls, "the sets-count card is RED again")

    def test_it_says_what_it_means_with_the_real_count_and_the_true_age(self):
        cls, body = _card(self.html, "1")
        self.assertIn("your board is ahead of the last Remaining page", body)
        self.assertIn("34 days old", body)
        self.assertNotIn("24 days", body)
        self.assertIn("16 of your ticked rows", body)
        self.assertIn("WAITING ON YOU", body, "the card no longer says where the one action went")
        self.assertNotIn("two wrong rows", self.html, "a count that outlived its referent is back")

    def test_opened_it_shows_the_measurement_not_the_alarm(self):
        # grok-4.7 on the OPENED card: the reader's raw sentence brought the accusation back one click in
        cls, body = _card(self.html, "1")
        self.assertIn("measured: board 132 found", body)
        self.assertIn("Tancred", body, "the rows the page still called missing are no longer named")
        self.assertNotIn("THE TWO INSTRUMENTS DISAGREE", body, "the alarm is back inside the calm card")

    def test_the_card_points_to_a_question_only_when_one_is_asked(self):
        """the second eye on v3498: the card pointed at WAITING ON YOU on any calibration.ok false, the
        doctor asks only when exact.ok is false with both counts - a pointer to a question that is not there"""
        cal = _his_calibration()
        cal["exact"] = {}
        cls, body = _card(_render({"calibration": cal}), "1")
        self.assertNotIn("WAITING ON YOU", body)

    def test_the_card_rounds_a_half_day_the_way_the_doctor_does(self):
        fixed_ms = 1790000000000
        cal = _his_calibration_at(fixed_ms / 1000.0 - 4.5 * 86400)
        cls, body = _card(_render_at({"calibration": cal}, fixed_ms), "1")
        self.assertIn("5 days old", body)

    def test_the_undatable_card_folds_too(self):
        cls, body = _card(self.html, "1.5")
        self.assertIsNotNone(cls, "premise: rank 1.5 did not render")
        self.assertIn("settled", cls)

    def test_the_denial_age_is_counted_from_the_page(self):
        cls, body = _card(self.html, "0")
        self.assertIsNotNone(cls, "premise: rank 0 did not render")
        self.assertRegex(body, r"its page is 3[34]\.\d days old")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the second eye on v3498 - the doctor rounds half-even again: a 4.5-day page is '4 days' here and '5 days' on the card",
        "file": "console_doctor.py",
        "find": "(\"from today\" if age < 1 else \"%d days old\" % int(age + 0.5))\n",
        "replace": "(\"from today\" if age < 1 else \"%d days old\" % round(age))\n",
        "matches": 1,
    },
    {
        "why": "the second eye on v3498 - missing counts print 'None' and still ask him",
        "file": "console_doctor.py",
        "find": "    if ex.get(\"boardFound\") is None or ex.get(\"gameMissing\") is None:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "the second eye on v3498 - the card points at a WAITING ON YOU question the doctor never asked",
        "file": "control_ui.html",
        "find": "        (cEx.ok === false && cEx.boardFound != null && cEx.gameMissing != null)\n",
        "replace": "        (true)\n",
        "matches": 1,
    },
    {
        "why": "#228 - the opened calm card prints the reader's raw alarm again (grok-4.7: the accusation, one click in)",
        "file": "control_ui.html",
        "find": "      var cMeas = (cEx.boardFound != null && cEx.gameMissing != null && cEx.rosterTotal != null)\n",
        "replace": "      var cMeas = (false)\n",
        "matches": 1,
    },
    {
        "why": "#228 - the sets-count card renders LOUD again, as if he had done something wrong",
        "file": "control_ui.html",
        "find": "          : 'nothing is held back and nothing here is yours to fix.', false);\n",
        "replace": "          : 'nothing is held back and nothing here is yours to fix.');\n",
        "matches": 1,
    },
    {
        "why": "#228 - the card's page age comes from the stored sweep again (24.5 days about a 34-day-old page)",
        "file": "control_ui.html",
        "find": "    var t = rd.readAt ? Date.parse(rd.readAt) : NaN;\n",
        "replace": "    var t = NaN;\n",
        "matches": 1,
    },
    {
        "why": "#228 - the one line that was his is no longer asked in WAITING ON YOU",
        "file": "console_doctor.py",
        "find": "    \"a fresh remaining page\": _ask_remaining_page,\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#228 - the doctor counts the page's age from the stored sweep again",
        "file": "console_doctor.py",
        "find": "    ra = rd.get(\"readAt\")\n",
        "replace": "    ra = None\n",
        "matches": 1,
    },
]
