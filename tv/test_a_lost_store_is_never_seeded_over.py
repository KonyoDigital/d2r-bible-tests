# -*- coding: utf-8 -*-
"""v2988 — A STORE THAT LOST ITS CONTENTS MUST NOT BE PAPERED OVER WITH SEEDS.

HIS RULING, 2026-09-12: *"for vault the items should not be seeded like the chronicles are.. it
should be able to be saved. or it gets auto saved daily in a ledger just incase if needed to
restore."* And, on the risk this law exists to bound: *"make sure though like when i login to the
console it doesnt start fresh with 0 items everytime... it starts with how i recently left it. as
long as nothing reset it.. or i deleted or did something to it"*.

THE DEFECT, at bible.html ~20718-20745. The detector was already GOOD — it tells a store that
STARTED empty (a new install) from one that BECAME empty, using bare keys no new install has ever
written (`d2r_pieceAlias_v2` / `d2r_chronSyncMerged_v1` / `d2r_installIdCache`). It recorded the
event to `d2r_storeEmptied`, WITH the restore command, and warned the console.
⚠ AND THEN THE SEED FLOOR RAN ANYWAY. Its own comment: "the seed floor below is about to refill it
from the built-in seeds. Anything you had that is in no seed will NOT come back on its own."
Detected-then-overwritten is WORSE than undetected: once the seeds land the store looks FULL, so
the hole is invisible. Measured consequence — 17 uniques and 3 set pieces gone, and the emptying
(`d2r_storeEmptied.at` = 2026-09-08 06:28 UTC) was not noticed for days.

⚠⚠ THE 20 ARE NOT RECOVERABLE, which is why this is a law and not a note. The ledger backups are
excellent — 60 snapshots, every ~5 minutes, 76 d2r_* stores each, with restore_ledger.py — but the
OLDEST is 2026-09-11 03:33 UTC, sixty-nine hours AFTER the loss. A backup that begins after the
incident is not a backup of the incident.

★ WHAT THIS LAW PINS, and the second clause is as important as the first:
  1. the seed floor does NOT run when the store BECAME empty (`_emptiedLoss`);
  2. it DOES still run for a genuine fresh install — otherwise the fix would trade a silent data
     loss for a silently broken first-run, and his "it doesnt start fresh with 0 items everytime"
     is exactly that fear. `_emptiedLoss` can only be true when `_hadRun` is true, and `_hadRun`
     reads keys a new install has never written, so the two cases cannot be confused.
  3. the flag is RAISED where the loss is detected — a clause guarding a variable nobody sets is
     the same as no clause at all. [[plumbing-with-no-tap]]
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

BIBLE = io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8").read()

#: the live seed-floor condition, anchored at BOTH ends
_COND = re.compile(r"if \(!_rwFreshFlag && ([^)]*?) && window\.D2R_PROFILE !== 'ladder'")


class ALostStoreIsNeverSeededOver(unittest.TestCase):

    def test_the_seed_floor_is_still_findable(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertTrue(_COND.search(BIBLE),
                        "the seed-floor condition moved or was rewritten — this law has no subject")

    def test_the_floor_refuses_a_store_that_became_empty(self):
        m = _COND.search(BIBLE)
        self.assertIn("!_emptiedLoss", m.group(1),
                      "the seed floor no longer consults _emptiedLoss, so a store that LOST its "
                      "contents is refilled from built-in seeds and then looks full — the exact "
                      "shape in which 17 uniques and 3 set pieces went missing")

    def test_the_first_loss_timestamp_is_never_overwritten(self):
        """⚠⚠ FOUND BY THE CROSS-FAMILY EYE ON v2988 — on the fix itself, hours after it shipped.

        `at: Date.now()` was written on EVERY boot that found the store still empty, so the
        recorded moment of the loss walked forward with each restart. That field is the whole
        point of the record: it is what says WHICH BACKUP PREDATES THE LOSS. On his own data that
        question decided everything — emptied 2026-09-08 06:28 UTC, oldest backup 2026-09-11
        03:33, sixty-nine hours later, which is why 17 uniques and 3 set pieces are unrecoverable.
        A drifting timestamp would have made even that answer unknowable. [[stale-reading]]
        """
        # ⚠⚠ THIS CLAUSE WAS BLIND ON ITS FIRST DRILL. It asserted that `var _firstAt` EXISTS and
        # that `_prevEv` appears nearby — and the tamper `var _firstAt = Date.now(); var _unused =
        # (_prevEv && ...` satisfies BOTH while destroying the behaviour. A presence check cannot
        # see a value. So it runs the shipped block instead. [[source-reading-guard]]
        a = BIBLE.find("        var _prevEv = null;")
        b = BIBLE.find("? _prevEv.at : Date.now();")
        if a < 0 or b < a:
            self.fail("the first-timestamp block moved or was renamed — this law lost its subject")
        block = BIBLE[a:b + len("? _prevEv.at : Date.now();")]
        js = ("var STORE = %s;\n"
              "var LS = { getItem: function(k){ return STORE[k] === undefined ? null : STORE[k]; } };\n"
              "%s\nconsole.log(JSON.stringify({first: _firstAt}));"
              % (json.dumps({"d2r_storeEmptied": json.dumps({"at": 1000, "boots": 3})}), block))
        d = tempfile.mkdtemp(prefix="firstat_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertEqual(r.returncode, 0, "the shipped block would not execute: %s" % r.stderr[:220])
        got = json.loads(r.stdout.strip().splitlines()[-1])["first"]
        self.assertEqual(
            got, 1000,
            "the FIRST loss timestamp was not preserved — got %r, expected the stored 1000. Every "
            "boot would overwrite the moment of the loss, and the record would stop being able to "
            "name which backup predates it." % got)

    def test_the_warning_does_not_still_say_it_is_seeding(self):
        """⚠ MY OWN STALE SENTENCE, ONE VERSION OLD. v2988 made the floor REFUSE to run over a
        loss, and the warning still announced 'seeding over it'. A message describing behaviour
        the code no longer has is the defect named most often in this repo.
        [[label-outlived-referent]]"""
        i = BIBLE.find("STORE CAME UP EMPTY")
        self.assertGreater(i, 0, "the emptied-store warning is gone")
        line = BIBLE[i:BIBLE.find("\n", i)]
        self.assertNotIn("— seeding over it", line,
                         "the console still tells him the store is being seeded over, which "
                         "v2988 made false: %r" % line[:120])

    def test_the_doctor_does_not_still_say_the_store_was_refilled(self):
        """⚠⚠ THE READER, NOT THE WRITER — and I fixed only the writer in v2990.

        The cross-family eye on v2988 named this precisely: the floor's contract changed and the
        surfaces describing it did not. `console_doctor` still told him the store "was refilled
        from the built-in seeds" while v2988 had made the floor REFUSE to run — so the board would
        show 0 and the doctor would report a plausible 383/117. Its words: "the operator is
        pointed at 17 items missing from a full-looking store when the actual state is an
        obviously empty board." [[label-outlived-referent]] [[the-unjoined-end]]

        ⚠ SCOPED TO THE LIVE SENTENCE, NOT THE FILE. The comment above it QUOTES the old wording on
        purpose, and a file-wide search would be satisfied by that quote — the same way an earlier
        law in this session went red on its own prose. Read the return, not the module.
        [[source-reading-guard]]
        """
        doc = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        i = doc.find("THE BOARD'S STORE CAME UP EMPTY")
        self.assertGreater(i, 0, "the emptied-store verdict is gone from the doctor")
        sentence = doc[i:i + 500]
        self.assertNotIn("was refilled from the built-in seeds", sentence,
                         "the doctor still tells him the store was refilled from seeds, which "
                         "v2988 made false — he would be handed the old diagnosis for a board "
                         "that is visibly empty")
        self.assertIn("REFUSING", sentence,
                      "the doctor no longer says the floor REFUSED, so 'empty' and 'seeded over' "
                      "read the same on the one surface that is supposed to tell them apart")

    def test_the_transport_carries_every_field_the_doctor_reads(self):
        """⚠⚠ I BUILT A READER FOR FIELDS THE TRANSPORT DROPPED. v2990 added
        {at, seenAgainAt, boots, recoveredAt}; v2991's doctor reads `boots`; and
        `control_app.board_ownership` copied storeEmptied through a WHITELIST of two keys, so
        `boots` was in localStorage, in every ledger backup, and absent from the ONE api the doctor
        feeds from. Its "still empty N boots later" could never print. The eye named the join:
        "the two readers of the same key do not share a shape." [[plumbing-with-no-tap]]

        ⚠ It stays a whitelist on purpose — `restore` is a COMMAND STRING and the console must
        never carry a command up out of board storage. Widened by name, never made a passthrough.
        """
        ca = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = ca.find("storeEmptied={at:")
        self.assertGreater(i, 0, "the board_ownership copy of storeEmptied is gone")
        seg = ca[i:i + 420]
        for field in ("boots", "seenAgainAt", "recoveredAt"):
            self.assertIn(field + ":", seg,
                          "board_ownership drops %r, so any doctor line reading it is dead on "
                          "arrival" % field)
        self.assertNotIn("restore:", seg,
                         "the command string `restore` is being carried up from board storage — "
                         "the console must never do that")

    def test_a_recovered_store_stops_reading_as_missing(self):
        """⚠ THE RECORD HAD NO EXIT. The advertised restore (`restore_ledger.py --apply`, a
        merge-max chronicleApply) puts the NAMES back and never removes `d2r_storeEmptied`, so the
        doctor reported MISSING for ever — including after a successful recovery. A permanent alarm
        is one he learns to ignore, which is worse than no alarm. Found by the cross-family eye.
        ⚠ And the record is NOT deleted: it is the evidence of what happened and when, which is the
        very thing v2990 exists to protect. `recoveredAt` is stamped beside it."""
        doc = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        i = doc.find("def _check_the_board_store_did_not_come_up_empty")
        j = doc.find("\ndef ", i + 10)
        body = doc[i:j]
        self.assertIn('ev.get("recoveredAt")', body,
                      "the doctor never looks for a recovery, so a restored store keeps reporting "
                      "MISSING for ever")
        self.assertIn("has contents again since", body,
                      "there is no OK verdict for a store that recovered — the row can only ever "
                      "say MISSING once it has fired")
        self.assertNotIn("removeItem('d2r_storeEmptied')", BIBLE,
                         "the emptied record is being DELETED on recovery — that erases the one "
                         "field that says which backup predates the loss")

    def test_the_flag_is_raised_where_the_loss_is_detected(self):
        """⚠ v3004 — THIS LAW WAS A FIXED-SIZE WINDOW AND IT BROKE ON AN INNOCENT EDIT. It read
        `i-600 : i+900` around the detector prose, and the v3004 episode-history block pushed
        `_emptiedLoss = true` past +900 — so a CORRECT tree failed the law. My own carved scar
        (`src[i:i+N]` past the region reads as ABSENT), shipped inside a gate. Anchored at both
        ends now: the detection REGION runs from the prose to the console.warn that closes it.
        [[source-window-shortcut]]"""
        i = BIBLE.find("the found ledger was EMPTY on a load that had already")
        self.assertGreater(i, 0, "the emptied-store detector is gone")
        j = BIBLE.find("STORE CAME UP EMPTY", i)
        self.assertGreater(j, i, "the detector's closing console.warn is gone — the region "
                                 "cannot be bounded, which is a failure, not a smaller window")
        near = BIBLE[max(0, i - 600):j]
        self.assertIn("_emptiedLoss = true", near,
                      "nothing SETS _emptiedLoss at the detection site, so the clause guards a "
                      "variable that is never raised — a guard with no tap")

    # ── the round trip: fresh install seeds, lost store does not ──────────────────────────────
    def _floor_runs(self, was_empty, had_run):
        """Execute the SHIPPED condition in node. -> bool | None"""
        m = _COND.search(BIBLE)
        if not m:
            return None
        cond = m.group(0)[len("if ("):]
        js = """
        var _rwFreshFlag = false;
        var _emptiedLoss = %s;
        var window = { D2R_PROFILE: 'main', _isCousinShell: false, _D2R_LEDGER: 'L' };
        var _GRAIL_SEED_LEDGER = 'L';
        var ran = false;
        if (%s && window._D2R_LEDGER === _GRAIL_SEED_LEDGER) { ran = true; }
        console.log(JSON.stringify({ran: ran}));
        """ % ("true" if (was_empty and had_run) else "false", cond)
        d = tempfile.mkdtemp(prefix="seed_law_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            return None
        if r.returncode != 0:
            return {"__err": (r.stderr or "")[:300]}
        return json.loads(r.stdout.strip().splitlines()[-1]).get("ran")

    def test_a_FRESH_INSTALL_still_gets_its_seeds(self):
        """⚠ HIS FEAR, PINNED. 'it doesnt start fresh with 0 items everytime' — a fix that stopped
        seeding a NEW install would trade a silent loss for a silently empty first run."""
        got = self._floor_runs(was_empty=True, had_run=False)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertTrue(got, "a genuine fresh install no longer receives the seed floor")

    def test_a_LOST_STORE_is_left_alone(self):
        got = self._floor_runs(was_empty=True, had_run=True)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertFalse(got, "the seed floor still runs over a store that BECAME empty")

    def test_a_NORMAL_LOGIN_is_untouched(self):
        """His store today: foundLog 432, setPieces 129 — _wasEmpty is False, so nothing changes."""
        got = self._floor_runs(was_empty=False, had_run=True)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertTrue(got, "an ordinary login stopped reaching the floor, which is a different "
                             "defect from the one this law was written for")


class ASecondLossKeepsItsOwnTimestamp(unittest.TestCase):
    """⚠⚠ v3004 — A SECOND LOSS MUST NOT WEAR THE FIRST LOSS'S TIMESTAMP. Found by the
    cross-family eye on v2993: `_firstAt` inherited `_prevEv.at` UNCONDITIONALLY, so after
    empty-at-T1 -> restore -> reload stamps recoveredAt at T2 -> empty again at T3, the record
    read {at: T1, no recoveredAt} — and "which backup predates the loss" pointed at T1, when the
    backups that predate THIS loss are the ones between T2 and T3. The exact field v2990 exists
    to protect, aimed at the wrong episode. EXECUTES the shipped block; prose cannot prove an
    order. [[feedback-blind-fixture-green-gate]]"""

    def _run(self, prev, now=9000):
        a = BIBLE.find("        var _prevEv = null;")
        b = BIBLE.find("try { console.warn('[ledger] STORE CAME UP EMPTY", a)
        if a < 0 or b < a:
            self.fail("the episode block moved — this law is grading nothing, which is not a pass")
        js = ("function run(prev, NOW){\n"
              "  var stored = null;\n"
              "  var LS = { getItem: function(){ return prev ? JSON.stringify(prev) : null; },\n"
              "             setItem: function(k, v){ stored = JSON.parse(v); } };\n"
              "  var Date = { now: function(){ return NOW; } };\n"
              "  var _emptiedLoss = false;\n"
              + BIBLE[a:b] +
              "\n  return stored;\n}\n"
              "console.log(JSON.stringify(run(%s, %d)));" % (json.dumps(prev), now))
        d = tempfile.mkdtemp(prefix="episode_")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        try:
            r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        except Exception:
            self.fail("node is REQUIRED by this law and is not on PATH — with it absent the law "
                      "does not run, and a law that does not run is not a pass")
        if r.returncode != 0:
            self.fail("the shipped episode block would not execute: %s" % (r.stderr or "")[:300])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_an_open_episode_still_keeps_the_first_at(self):
        """v2990's protection, untouched: while the SAME loss is still open, `at` must not walk."""
        got = self._run({"at": 1000, "boots": 3})
        self.assertEqual(got["at"], 1000)
        self.assertEqual(got["boots"], 4)

    def test_a_closed_episode_starts_a_new_one(self):
        got = self._run({"at": 1000, "boots": 3, "recoveredAt": 2000})
        self.assertEqual(got["at"], 9000,
                         "the previous loss was CLOSED at T2; this empty is a NEW loss and its "
                         "`at` must be now, or the backup question points at the wrong episode")
        self.assertEqual(got["boots"], 1, "boots is a fact about ONE loss, not a lifetime tally")

    def test_the_closed_episode_survives_as_history(self):
        got = self._run({"at": 1000, "boots": 3, "recoveredAt": 2000})
        prev = got.get("prevEpisode") or {}
        self.assertEqual((prev.get("at"), prev.get("recoveredAt")), (1000, 2000),
                         "recovering twice must never erase the first loss's record — evidence "
                         "is superseded, not deleted")


class TheDoctorSeesTheStoreRefillWithoutAReload(unittest.TestCase):
    """⚠⚠ v3004 — HE RAN THE EXACT COMMAND THE MISSING ROW PRINTS AND THE ROW KEPT SAYING MISSING.
    `--apply` writes names into the ALREADY-LOADED board; `recoveredAt` stamps only at board load.
    The evidence was in _board_read()'s own `counts` the whole time and the doctor never looked."""

    def _verdict(self, ev, counts):
        import console_doctor as cd
        real = cd._board_read
        cd._board_read = lambda: {"ok": True, "boardLoaded": True,
                                  "storeEmptied": ev, "counts": counts}
        try:
            return cd._check_the_board_store_did_not_come_up_empty()
        finally:
            cd._board_read = real

    def test_an_open_event_with_measured_contents_is_not_missing(self):
        st, why = self._verdict({"at": 1000, "boots": 2}, {"foundLog": 440, "setPieces": 129})
        self.assertEqual(st, "ok",
                         "the store measurably holds 440 names; telling him to run --apply again "
                         "is the permanent alarm this row keeps almost becoming — got %s" % st)
        self.assertIn("440", why, "and the verdict must carry the number it rests on")

    def test_zero_counts_stay_missing(self):
        st, _w = self._verdict({"at": 1000, "boots": 2}, {"foundLog": 0, "setPieces": 0})
        self.assertEqual(st, "missing", "measured-zero is the fault, not recovery")

    def test_absent_counts_never_read_as_contents(self):
        """Only a MEASURED count exits. 'Could not count' must never become 'has contents'.
        [[unknown-stays-unknown]]"""
        st, _w = self._verdict({"at": 1000, "boots": 2}, None)
        self.assertEqual(st, "missing")


RED_PROOF = [
    {
        "why": "dropping the recoveredAt clause lets a CLOSED episode donate its timestamp to a "
               "brand-new loss, and the backup question points at the wrong episode again",
        "file": "bible.html",
        "find": "                            && !_prevEv.recoveredAt);",
        "replace": "                            && true);",
        "matches": 1,
    },
    {
        "why": "disabling the counts exit returns the doctor to MISSING-until-reload: he runs the "
               "exact command the row prints and the row keeps printing it",
        "file": "console_doctor.py",
        "find": "    if ((isinstance(_fl, (int, float)) and _fl > 0)",
        "replace": "    if False and ((isinstance(_fl, (int, float)) and _fl > 0)",
        "matches": 1,
    },
    {
        "why": "dropping the clause restores the exact behaviour that destroyed 17 uniques and 3 "
               "set pieces — the floor seeding over a store that lost its contents",
        "file": "bible.html",
        "find": "if (!_rwFreshFlag && !_emptiedLoss && window.D2R_PROFILE !== 'ladder'",
        "replace": "if (!_rwFreshFlag && window.D2R_PROFILE !== 'ladder'",
        "matches": 1,
    },
    {
        "why": "narrowing the transport back to two keys makes the doctor's boots line dead on "
               "arrival — the field exists everywhere except the api it is read from",
        "file": "control_app.py",
        "find": "\"boots:(typeof _se.boots==='number'?_se.boots:null),\"",
        "replace": "\"\"",
        "matches": 1,
    },
    {
        "why": "removing the recovery verdict makes a restored store report MISSING for ever, and "
               "a permanent alarm is one he learns to ignore",
        "file": "console_doctor.py",
        "find": '    _rec = ev.get("recoveredAt") if isinstance(ev, dict) else None',
        "replace": "    _rec = None",
        "matches": 1,
    },
    {
        "why": "putting the old sentence back into the doctor hands him the pre-v2988 diagnosis "
               "for a board that is visibly empty",
        "file": "console_doctor.py",
        "find": "                     \"EMPTY rather than being papered over with defaults: an empty store you can \"",
        "replace": "                     \"and was refilled from the built-in seeds. \"",
        "matches": 1,
    },
    {
        "why": "going back to an unconditional Date.now() makes the loss timestamp walk forward on "
               "every boot, so the record can no longer name which backup predates the loss",
        "file": "bible.html",
        "find": "        var _firstAt = _sameEpisode ? _prevEv.at : Date.now();",
        "replace": "        var _firstAt = Date.now();",
        "matches": 1,
    },
    {
        "why": "leaving the clause but never raising the flag is a guard with no tap: it reads "
               "correct and can never fire",
        "file": "bible.html",
        "find": "        _emptiedLoss = true;   // v2988 — the seed floor MUST NOT run over this",
        "replace": "        /* not raised */",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
