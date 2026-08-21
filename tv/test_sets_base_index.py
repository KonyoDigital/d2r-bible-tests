#!/usr/bin/env python3
"""BASE -> SET PIECE: the index, and the copy of it embedded in the board.

Konyo asked for the sets side of something uniques already had — expanding a base name the
Chronicle prints back to what he still has to find. `_chUniquesOnBase` does it for uniques from
ITEM_CODEX; **ITEM_CODEX carries a base for only 14 of the 135 set pieces**, so there was nothing
to copy and the mapping had to come from the Remaining page he recorded.

That creates a second copy of one fact — the source JSON and the block embedded in bible.html — and
a copy that nothing compares is a copy that drifts. These tests are the comparison. [[copy-drift]]
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import sets_base_index as sbi  # noqa: E402
import chronicle_resolve as _res  # noqa: E402


def _embedded():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        s = fh.read()
    m = re.search(r"window\._SET_BASE_INDEX = (\{.*?\});\n", s, re.S)
    return json.loads(m.group(1)) if m else None


class TestTheIndexItself(unittest.TestCase):
    def test_it_is_read_data_not_derived_from_the_slot_suffix(self):
        """The rule I first believed — 'the suffix IS the base' — is true for some rows and false
        for others, and a rule that is quietly right half the time is worse than no rule."""
        b = sbi.build()
        self.assertIsNotNone(b, "no Remaining page on file")
        pairs = {v["base"]: v["pieces"] for v in b["index"].values()}
        # rows where the suffix genuinely IS the base
        self.assertIn("Ward", pairs)
        self.assertTrue(any(p.endswith("(ward)") for p in pairs["Ward"]))
        # ...and rows where it is a CATEGORY, which a suffix rule would have mis-resolved
        self.assertIn("Scissors Suwayyah", pairs)
        self.assertEqual(pairs["Scissors Suwayyah"], ["Natalya's Soul (claws)"],
                         "the suffix here is 'claws', a category — not the base")
        self.assertEqual(pairs["Occult Codex"], ["Horazon's Secrets (grimoire)"])
        self.assertEqual(pairs["Sacred Armor"], ["Immortal King's Soul Cage (armor)"])

    def test_one_base_may_carry_more_than_one_piece(self):
        b = sbi.build()
        pairs = {v["base"]: v["pieces"] for v in b["index"].values()}
        self.assertEqual(len(pairs.get("Amulet") or []), 2,
                         "two set pieces share the Amulet base; collapsing them to one would "
                         "silently drop a piece he still has to find")

    def test_every_indexed_piece_is_a_real_roster_piece(self):
        b = sbi.build()
        roster = _res.load_set_roster()
        bad = []
        for v in b["index"].values():
            for p in v["pieces"]:
                if _res.canonical(p, roster) is None:
                    bad.append(p)
        self.assertEqual(bad, [], "an indexed piece that is not on the roster would expand a base "
                                  "into a name that does not exist")

    def test_coverage_is_stated_rather_than_assumed(self):
        c = sbi.coverage()
        self.assertTrue(c["ok"])
        self.assertEqual(c["rosterTotal"], 135)
        self.assertLess(c["pieces"], c["rosterTotal"],
                        "this index covers only what is missing; if it ever claims the whole "
                        "roster, something has confused 'missing' with 'all'")
        self.assertIn("do not have", c["say"])

    def test_with_no_reading_it_refuses_rather_than_returning_an_empty_index(self):
        """An empty index and 'never read' are opposite facts. [[unknown-stays-unknown]]"""
        old = os.environ.get("TV_REMAINING_DIR")
        import tempfile
        os.environ["TV_REMAINING_DIR"] = tempfile.mkdtemp(prefix="nobase-")
        try:
            self.assertIsNone(sbi.build())
            self.assertIsNone(sbi.coverage()["ok"])
        finally:
            if old is None:
                os.environ.pop("TV_REMAINING_DIR", None)
            else:
                os.environ["TV_REMAINING_DIR"] = old


class TestTheBoardsCopyHasNotDrifted(unittest.TestCase):
    def test_the_embedded_block_exists_and_parses(self):
        e = _embedded()
        self.assertIsNotNone(e, "window._SET_BASE_INDEX is missing from bible.html — the board "
                                "cannot expand a set base without it")
        self.assertTrue(e.get("index"))

    def test_it_matches_the_source_exactly(self):
        e, b = _embedded(), sbi.build()
        self.assertEqual(e["index"], b["index"],
                         "the board's copy has drifted from tv/remaining — regenerate it")
        self.assertEqual(e.get("readAt"), b.get("readAt"),
                         "the embedded stamp must be the reading's own, or the board reports an "
                         "age that belongs to a different page")

    def test_the_board_carries_the_stamp_so_the_age_is_answerable(self):
        e = _embedded()
        self.assertTrue(e.get("readAt"), "an index with no date cannot be aged, and an age that "
                                         "cannot be established is UNKNOWN")
        self.assertTrue(e.get("reel"))

    def test_the_resolver_and_its_wiring_are_both_present(self):
        """Two halves each built right and never joined is the failure mode that costs most here."""
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            s = fh.read()
        self.assertIn("window._chSetPiecesOnBase = function", s, "the resolver is missing")
        self.assertIn("window._chSetPiecesOnBase(canon)", s,
                      "the resolver exists but d2rInboxEngine never calls it — a base would still "
                      "resolve to nothing, which is the whole defect [[the-unjoined-end]]")
        # TWO call sites, and the second is the one measurement found. The base branch only fires
        # when d2rResolveItem calls the string a base, and its catalogue does not hold the plain
        # slot words: live in a browser, "Ward" and "Occult Codex" resolved while **"Amulet" came
        # back not-in-game** — a name the game printed on his own Remaining page for two pieces he
        # is still hunting. Declaring an item the game itself listed to be "not an item in this
        # game" is the most confident possible way to be wrong.
        self.assertIn("window._chSetPiecesOnBase(canon || raw)", s,
                      "the not-in-game fallthrough must consult the index too, or a generic base "
                      "like Amulet is reported as not an item in this game")
        self.assertLess(s.index("window._chSetPiecesOnBase(canon || raw)"),
                        s.index("out.verdict = 'not-in-game'; out.action = 'reader';"),
                        "the fallback must run BEFORE the not-in-game verdict, or it can never "
                        "change it")


class TestTheSentenceNamesWhatItLists(unittest.TestCase):
    """A right list under a word naming half of it.

    "Ward" carries BOTH a unique he is missing (Spirit Ward) and a set piece (Taebaek's Glory). The
    first cut printed both names under "for a unique you have NOT found", which is how he ends up
    hunting one and not the other. Measured live in a browser before and after.
    [[label-outlived-referent]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_all_three_sentences_exist(self):
        s = self._src()
        for phrase in ("for a unique AND a set piece you have NOT found",
                       "for a SET PIECE you have NOT found",
                       "for a unique you have NOT found"):
            self.assertIn(phrase, s, "missing branch: %s" % phrase)

    def test_the_both_case_is_tested_before_the_single_cases(self):
        """An `if sets` that runs before `if uniques and sets` can never reach the both-branch."""
        # ⚠ The first version of THIS assertion grepped `? (sp.missing.length` — a spelling the
        # code does not use (it is `: (sp.missing.length`) — and errored instead of failing. Same
        # class as the guard it is guarding. Anchor on both real occurrences instead.
        s = self._src()
        both = s.index("u.missing.length && sp.missing.length")
        only = s.index("(sp.missing.length", both + 10)
        self.assertLess(both, only,
                        "the both-case must be tested first or it is unreachable, and every mixed "
                        "base silently reports as one catalogue")
        self.assertLess(only - both, 400,
                        "the two branches drifted apart; this check anchors on proximity and would "
                        "otherwise be measuring an unrelated occurrence [[source-reading-guard]]")


class TestTheLedgerRepair(unittest.TestCase):
    """His F·Sets read 118/135 while the game read 116. Asking the live board settled it: 119
    stored, and three rows that do not belong — a UNIQUE (Blood Crescent, already in his Holy
    Grail) plus two pieces the game's own Remaining page lists as missing. 119 - 3 = 116.
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_the_repair_and_its_boot_call_both_exist(self):
        s = self._src()
        self.assertIn("window._chRepairLedgers = function", s)
        self.assertIn("window._chRepairLedgers()", s,
                      "the repair exists but nothing runs it [[the-unjoined-end]]")
        self.assertIn("window._SET_MISSING", s)

    def test_it_refuses_to_judge_against_an_empty_catalogue(self):
        """Judging a ledger against a roster that has not loaded would delete every row in it."""
        s = self._src()
        self.assertIn("the set catalogue is not loaded yet", s)

    def test_the_missing_list_branch_fires_ONCE_PER_READING(self):
        """⚠ THE DATA-LOSS TRAP. _SET_MISSING is a photograph of one moment. Without the key, the
        day he finds Natalya's Soul and ticks it, the next load strips it again — forever, while
        the repair looks like it is working. Proven in a browser: after a re-tick, run 2 removes 0.
        [[stale-reading]]"""
        s = self._src()
        self.assertIn("d2r_setRepairAt", s, "no per-reading key — the repair would re-fire forever")
        self.assertIn("!doneThisReading", s,
                      "the missing-list branch must be gated on the reading key")
        # ...and the not-a-set-piece branch must NOT be gated: "this is a unique" never goes stale
        i_uni = s.index("it was routed into the set ledger by mistake")
        i_gate = s.index("if (missing[n] && !doneThisReading)")
        self.assertLess(i_uni, i_gate,
                        "the unique branch must run before, and independently of, the expiring one")

    def test_it_never_removes_a_row_that_is_in_BOTH_ledgers(self):
        """⚠ THE RULE THAT WOULD HAVE DELETED 116 REAL FINDS. He asked for a guard against an item
        being in both chronicles, and the obvious reading of that is catastrophic here:
        toggleSetPiece writes every set piece into d2r_foundLog ON PURPOSE (v644), so all 116 of
        his real pieces are in both by design."""
        s = self._src()
        # assertNotIn on a 5.6MB string dumps the WHOLE FILE into the failure message — 11MB of
        # output for a one-line defect, which is a failure nobody can read. Boolean + a short say.
        self.assertFalse("counted in BOTH your Holy Grail and your set ledger" in s,
                         "the both-ledgers rule is back in bible.html. It deletes every legitimate "
                         "set piece: toggleSetPiece writes each one into d2r_foundLog on purpose "
                         "(v644), so all 116 of his real pieces are in both by design.")
        self.assertIn("IN BOTH LEDGERS\" IS NORMAL".replace('\"', '"'), s.replace('“', '"'),
                      "the reason must stay recorded, or someone re-adds the rule")

    def test_the_write_guard_stops_a_unique_entering_the_set_store(self):
        s = self._src()
        self.assertIn("A UNIQUE MUST NEVER ENTER THE SET STORE", s)
        i_guard = s.index("_isPiece = _cat.exact.has(piece)")
        i_add = s.index("if (_isPiece) setPieces.add(piece);")
        self.assertLess(i_guard, i_add, "the guard must be computed before the add")

    def test_the_meter_floors_so_it_matches_the_game(self):
        """116/135 = 85.93%. Rounded prints 86; the game prints 85, and he compares them directly."""
        s = self._src()
        self.assertIn("var pct=total?Math.floor(found/total*100):0;", s)
        self.assertNotIn("var pct=total?Math.round(found/total*100):0;", s)


class TestTheChroniclesShareOneStyle(unittest.TestCase):
    """Konyo: "make sure its a unified CSS between the individual chronicles related."

    The stylesheet already unifies them — `:is(#tab-forge,#tab-funi,#tab-fsets) .fp-fill` gives all
    three siblings ONE gradient — and F·Uniques used it by passing no colour. F·Sets passed
    '#4ade80,#86efac' inline, and **inline beats the stylesheet**, so the one tab opted itself out
    of the rule written to keep them the same. Measured side by side before the fix:

        uniques  rgb(95,201,122) -> rgb(143,230,160)
        sets     rgb(74,222,128) -> rgb(134,239,172)

    v775 had already spotted the sibling drift and unified the TITLE colour, noting in its own
    comment "was #4ade80 on Sets" — and left the FILL behind. Half a class is how it comes back.
    [[d2r-css-last-rule-wins]] [[feedback-generalize-fixes]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_no_meter_call_passes_an_inline_colour(self):
        import re
        s = self._src()
        calls = [m for m in re.findall(r"_meter\(([^;]{0,120})", s) if not m.startswith("found,")]
        self.assertTrue(calls, "no _meter calls found — this guard has lost its subject")
        bad = [c for c in calls if re.search(r"'#[0-9a-fA-F]{3,8}", c)]
        self.assertEqual(bad, [],
                         "a chronicle meter passes an inline gradient, which overrides the shared "
                         ":is(#tab-forge,#tab-funi,#tab-fsets) .fp-fill rule and un-unifies the "
                         "siblings: %s" % bad)

    def test_the_shared_sibling_rule_still_exists(self):
        """The guard above is only meaningful while there IS a shared rule to inherit."""
        s = self._src()
        self.assertIn(":is(#tab-forge,#tab-funi,#tab-fsets) .fp-fill", s,
                      "the sibling rule is gone — removing inline colours now leaves them unstyled, "
                      "which is worse than the drift")


class TestEveryLedgerStatusHasAPill(unittest.TestCase):
    """v1925 started writing `removed` and `refused` into the Activity Ledger and never told the
    PILL map, so both rendered as bare dim text beside a green "✓ ticked" — a row that CHANGED his
    grail reading quieter than one that merely confirmed it. Found on the rendered panel.

    This pins the join: any status the code writes must have a pill to render it.
    [[the-unjoined-end]]"""

    def test_written_statuses_all_have_pills(self):
        import re
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            s = fh.read()
        i = s.index("var PILL = {")
        pills = set(re.findall(r"'([a-z\-]+)':\s*\[", s[i:i + 1400]))
        # ⚠ SCOPE IT TO THE LEDGER'S OWN WRITER. A bare `status: '...'` grep pulled in farm, hunt,
        # idle, now, pipe and queued — other subsystems entirely, none of which this panel renders.
        # A guard that reaches past its subject reports six defects that are not there, and six
        # false positives is how a guard stops being read. [[source-reading-guard]]
        written = set()
        for m in re.finditer(r"kaiChronicleRecord\(\{", s):
            seg = s[m.start():m.start() + 700]
            written |= set(re.findall(r"status:\s*'([a-z\-]+)'", seg))
        self.assertTrue(written, "no kaiChronicleRecord call sites found — this guard has lost its "
                                 "subject and would pass on an empty set")
        missing = sorted(w for w in written if w not in pills)
        self.assertEqual(missing, [],
                         "these statuses are written into the ledger but have no pill, so they "
                         "render as bare text: %s" % missing)


class TestEverySweepPayloadKeyIsRead(unittest.TestCase):
    """A key computed, attached to a payload, and read by nothing.

    Found by sweeping the chronicle sweep RESULT payload against both UI files with comments
    stripped: seven keys no UI had ever read. Two mattered and are now rendered —

        newlyDated        (v1846) the finds whose IN-GAME date is newer than the last sweep, which
                          is exactly what he asked for when he said the stamp must be when he found
                          it in game and NOT when the reader registered it. Computed for eighty
                          versions, shown nowhere.
        contestedExpired  (v1923, mine) names dropped from the contested count because the newest
                          look says found.

    ⚠ contestedExpired shipped in the SAME COMMIT that fixed calibration, contested and denial for
    this exact defect. Fixing three instances of a class and shipping a fourth is how a class
    survives being fixed. [[plumbing-with-no-tap]] [[feedback-generalize-fixes]]

    ⚠ The first sweep was UNSCOPED and returned 153 keys — subprocess kwargs, HTTP headers,
    platform strings. A finding too large to act on is noise. Scoped to the result payload it
    returned 7. [[sweep-dont-ask]]
    """

    KEYS = ("calibration", "contested", "denial", "notFoundDatable", "newlyDated",
            "contestedExpired")

    def test_each_payload_key_the_panel_depends_on_is_actually_read(self):
        import re
        def strip(src):
            src = re.sub(r"/\*.{0,4000}?\*/", " ", src, flags=re.S)
            return re.sub(r"(?m)^\s*//.*$", " ", src)
        with io.open(os.path.join(ROOT, "tv", "control_ui.html"), encoding="utf-8") as fh:
            ui = strip(fh.read())
        unread = [k for k in self.KEYS
                  if not re.search(r"[.\[]['\"]?%s" % re.escape(k), ui)]
        self.assertEqual(unread, [],
                         "these are written into the sweep payload and no UI reads them, so they "
                         "read as protection from the code side and carry nothing: %s" % unread)

    def test_the_dropped_diagnostic_key_is_not_back_in_the_payload(self):
        """contestedResolved is per-name internals that drive no decision. If it returns, it must
        return with a consumer."""
        import re
        with io.open(os.path.join(ROOT, "tv", "control_app.py"), encoding="utf-8") as fh:
            ca = fh.read()
        with io.open(os.path.join(ROOT, "tv", "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        in_payload = '"contestedResolved": prop.get' in ca
        read = bool(re.search(r"[.\[]['\"]?contestedResolved", ui))
        self.assertFalse(in_payload and not read,
                         "contestedResolved is back on the payload with nothing reading it")


class TestNoGateSkipsSilently(unittest.TestCase):
    """A skip that whispers is a gate that is not there.

    The console-demo gate fires only on a tv/control_ui.html diff with the app up. v1930 was the
    first push in a while to satisfy both and it caught J9 failing — which bisection showed had
    ALSO been failing on v1924 through v1929, every one of which pushed clean because none touched
    that file. Seven versions, a real red gate, and nothing said a word.

    The trigger stays narrow on purpose (never block on an environment the push did not break).
    What must not return is the SILENT skip. [[feedback-blind-fixture-green-gate]]
    """

    def _hook(self):
        p = os.path.join(ROOT, "hooks", "pre-push")
        if not os.path.isfile(p):
            self.skipTest("hooks/pre-push is not on this machine")
        with io.open(p, encoding="utf-8") as fh:
            return fh.read()

    def test_the_demo_gate_announces_every_skip(self):
        h = self._hook()
        self.assertIn("CONSOLE DEMOS SKIPPED", h,
                      "the app-down branch must SAY it skipped")
        self.assertIn("console demos not run", h,
                      "the file-unchanged branch must say it skipped too — that is the branch that "
                      "hid seven versions of a red gate")

    def test_the_skip_says_how_long_it_has_been_skipping(self):
        """A count he can watch grow beats a line he stops seeing."""
        h = self._hook()
        self.assertIn("commit(s) since it last was", h)
        self.assertIn("_since=", h)

    def test_the_skip_says_how_to_run_it_by_hand(self):
        h = self._hook()
        self.assertIn("node tv/demo_console.mjs", h)


class TestTheUniquesLedgerIsAuditedNotEdited(unittest.TestCase):
    """The symmetric audit of d2r_foundLog, and the decision NOT to act on it.

    Five rows matched neither roster. MEASURED, not guessed:

        Atma's Scarab / Saracen's Chance   the roster spells these with a CURLY apostrophe.
                                           Both _norm implementations fold ‘’ʼ to ', so they
                                           resolve correctly and are NOT debris.
        Naglring                           a misread of Nagelring — and Nagelring is ALSO in his
                                           foundLog, so this is a duplicate, not a lost find.
        Athena's Wrath (set piece)         same: the real name is also present.
        Cow King's Leathers (set)          a SET NAME in the uniques ledger.

    His 267/403 is RIGHT and none of this changes it. The uniques write path is already guarded —
    it writes only when the name resolves — so these are historical rows, not an open leak.

    They are REPORTED and NOT REMOVED. Deleting grail rows that cost him nothing, to tidy a number
    that is already correct, is an unasked-for edit to his history. [[sweep-dont-ask]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_debris_is_collected(self):
        s = self._src()
        self.assertIn("out.debris", s, "the audit is missing")
        self.assertIn("REPORT (never remove) DEBRIS", s)

    def test_debris_is_never_added_to_the_removal_list(self):
        """The one line that keeps this an audit instead of an edit."""
        s = self._src()
        i = s.index("out.debris = Object.keys(fl2)")
        seg = s[i:i + 500]
        self.assertNotIn("out.removed.push", seg,
                         "debris must never reach the removal list — that would delete grail rows "
                         "he never asked to lose")

    def test_the_apostrophe_rows_are_not_treated_as_debris(self):
        """Both normalisers fold ‘’ʼ to ', so a curly-apostrophe roster name resolves. If this
        breaks, four real uniques start reading as debris."""
        s = self._src()
        self.assertIn("replace(/[‘’ʼ]/g, \"'\")", s,
                      "the grail normaliser no longer folds curly apostrophes — Atma’s Scarab, "
                      "Saracen’s Chance, Seraph’s Hymn and The Cat’s Eye would stop resolving")


if __name__ == "__main__":
    unittest.main(verbosity=2)
