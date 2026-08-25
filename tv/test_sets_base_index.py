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
        self.assertEqual(pairs["Scissors Suwayyah"], ["Natalya's Mark (claws)"],
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
        # v1938 — the boot call now passes {auto:true} so the one-shot suppressor can stop the
        # WHOLE repair on a spec's later-load boot while a hand-run repair still works. Matched on
        # the call HEAD, not the exact argument text, so adding an option does not read as "nothing
        # runs it". [[source-reading-guard]]
        self.assertIn("window._chRepairLedgers({", s,
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
        # v1946 — THE INVARIANT IS UNCHANGED; THE MECHANISM IS STRONGER. v1942 replaced
        # `doneThisReading` with d2r_setRepairKept, because the old gate INFERRED his intent from
        # elapsed time ("the repair already ran, so anything still ticked must be his doing") and
        # that inference was false on his own board: REG-300 had undone the effect while the stamp
        # survived, so the repair believed itself done and froze F·Sets at 117. A recorded ruling
        # cannot go stale the way an inference can. The claim this test defends — a piece he ticks
        # back is never stripped again — is now stronger, so it is pinned on the new mechanism.
        self.assertIn("d2r_setRepairAt", s, "the per-reading receipt is gone — nothing records "
                                            "which reading the repair acted on")
        self.assertIn("d2r_setRepairKept", s,
                      "nothing records his deliberate re-ticks, so the repair would strip them "
                      "again on every load — the exact data-loss trap this test exists for")
        self.assertIn("!_repairKept[n]", s,
                      "the missing-list branch must honour a piece he has ticked back")
        # ...and the not-a-set-piece branch must NOT be gated: "this is a unique" never goes stale
        i_uni = s.index("it was routed into the set ledger by mistake")
        # v1937 added `&& !_repairSuppressed` to this line; the pin below caught the change, which
        # is the guard working. Anchored on the stable prefix so the next legitimate condition does
        # not read as a regression.
        i_gate = s.index("if (missing[n] && !_repairKept[n]")
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
        import re
        s = self._src()
        # v2119 — PIN THE LAW, NOT THE MEMBER LIST. This asserted the literal three-tab spelling and
        # went red the moment v2094 legitimately joined #tab-crafts to the same family: the rule was
        # never gone, the grep just could not reach past its own wording. What matters is that each
        # sibling is still IN the shared rule, not how many siblings there are.
        # [[source-reading-guard]] [[feedback-state-the-bar-not-the-routes]]
        m = re.search(r":is\(([^)]*)\)\s*\.fp-fill\{", s)
        self.assertIsNotNone(m, "the sibling rule is gone — removing inline colours now leaves them "
                                "unstyled, which is worse than the drift")
        members = [t.strip() for t in m.group(1).split(",")]
        # v2121 (#127) — AND #tab-crafts. The replacement for the 3-tab literal pin kept the
        # pre-v2094 trio as its required set, so the fourth sibling could drop straight back out
        # and stay green — the very un-unify the original was watching for. Every member of the
        # family is required; what is NOT required is the count, which is what made the old pin
        # brittle.
        for sib in ("#tab-forge", "#tab-crafts", "#tab-funi", "#tab-fsets"):
            self.assertIn(sib, members,
                          "%s dropped out of the shared .fp-fill rule — that sibling is now "
                          "unstyled and free to drift" % sib)


class TestV2119ASetPiecesSlotAgreesWithItsBase(unittest.TestCase):
    """The swap that produced this guard: the roster bound `Natalya's Mark` to (boots) and
    `Natalya's Soul` to (claws) while the set catalogue said Mark -> "Scissors Suwayyah" (a CLAW)
    and Soul -> "Mesh Boots". Konyo saw it as art: "claws is boots image.. and the boots is a claw
    image? its completely oppisite". Nothing compared the two, so a piece could name one item and
    wear another's slot indefinitely — and the slot is what the base index, the art lane and his
    own ledger all key on. [[feedback-generalize-fixes]]

    ⚠ The arbiter is `setMembers[].slot`, NOT ITEM_CODEX. My first cut of this guard asked the
    codex, which knows only 3 of the 295 piece strings, and its own floor caught it judging two."""

    # slot word -> words that must appear in the base for it to be consistent. Deliberately
    # literal: a slot this table cannot judge is SKIPPED, never guessed. [[unknown-stays-unknown]]
    SLOT_WORDS = {
        "claws":  ("suwayyah", "katar", "talons", "blade", "scissors", "claw", "hand"),
        "boots":  ("boots", "greaves", "treads", "shoes"),
        "helm":   ("helm", "cap", "crown", "mask", "casque", "coif", "diadem", "circlet",
                   "visage", "armet", "shako", "horns", "skull", "sallet", "basinet",
                   "guise", "corona", "guard", "tiara", "spirit"),
        "armor":  ("mail", "plate", "armor", "hauberk", "cuirass", "jerkin", "skin", "shroud",
                   "wyrmhide", "husk", "fleece", "field", "breast", "cape", "robe", "vest",
                   "shell", "scarab", "hide", "pelt"),
        "belt":   ("belt", "sash", "girdle", "vambraces"),
        "gloves": ("gloves", "gauntlets", "bracers", "mitts", "vambraces"),
        "amulet": ("amulet",),
        "ring":   ("ring",),
        "shield": ("shield", "rondache", "targe", "aegis", "ward", "scutum", "defender",
                   "pavise", "kite", "buckler", "tower", "spiked", "heater", "luna",
                   "trophy", "head", "skull", "preserver", "idol", "bone"),
    }

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_no_piece_wears_another_items_slot(self):
        import re
        s = self._src()

        # name -> base, straight out of the set catalogue the board renders from
        bases = dict(re.findall(r'\{"name":"([^"]+)","slot":"([^"]+)"', s))
        # MEASURED, not aspirational: exactly 56 setMembers rows carry a "slot" today, and 55 of
        # the piece strings resolve against them. A floor above the ceiling is an absent floor.
        # [[feedback-threshold-above-the-ceiling]]
        self.assertGreaterEqual(len(bases), 50,
                                "only %d setMembers rows carry a base — this guard has lost its "
                                "arbiter and would pass by knowing nothing" % len(bases))

        # STRIP THE PROSE FIRST. bible.html's comments QUOTE the very swap this guard exists to
        # catch ("Natalya's Soul (claws) is a Scissors Suwayyah…"), so a raw scan reports the
        # paragraph explaining the bug as the bug. Bounded so a stray `/*` cannot eat the file —
        # an unbounded strip once removed 16.9% of it. [[feedback-comments-vs-code]]
        code = re.sub(r"/\*.{0,4000}?\*/", " ", s, flags=re.S)
        code = re.sub(r"(?m)^\s*//.*$", "", code)
        # AND NOT THE RENAME MIGRATION'S OWN MAP. v2119's _ALIAS exists precisely to name the OLD
        # spelling so a stranded tick can be moved; scanning it reports the cure as the disease.
        code = re.sub(r"var _ALIAS = \{.{0,600}?\};", " ", code, flags=re.S)
        self.assertGreater(len(code), len(s) * 0.6, "the comment strip ate the document")
        pieces = set(re.findall(r'"([^"]+?) \(([a-z ]+)\)"', code))
        self.assertTrue(pieces, "no set-piece strings found — this guard has lost its subject")

        judged, bad = 0, []
        for name, slot in pieces:
            base = bases.get(name)
            words = self.SLOT_WORDS.get(slot)
            if not base or not words:
                continue                      # unknown name or unjudgeable slot -> SKIP, never guess
            judged += 1
            if not any(w in base.lower() for w in words):
                bad.append('%s (%s) -> base "%s"' % (name, slot, base))

        # A SKIP IS NOT A PASS. Without this the table could drift to judging nothing and read
        # exactly like "everything agrees" — which is how the swap survived.
        # [[feedback-blind-fixture-green-gate]]
        self.assertGreaterEqual(judged, 20,
                                "only %d piece(s) could be judged — the guard has gone blind, which "
                                "reads identical to 'everything agrees'" % judged)
        self.assertEqual(bad, [],
                         "a set piece names one item and wears another's slot; the base index, the "
                         "art lane and his ledger all key on that slot: %s" % bad)


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
        # v1953 — ANCHOR ON THE MAP, AND BOUND BY ITS REAL END.
        # Two ways this guard broke its own reach at once:
        #   · v1949 hoisted the table out of renderInbox to window._CH_PILL_MAP so the new routing
        #     ledger could share one vocabulary, and `s.index("var PILL = {")` then raised
        #     ValueError — the guard ERRORED rather than failing, which reads as a broken test
        #     rather than a broken join, and CI reported it on two ships before I looked;
        #   · the 1400-character window was already a guess, and v1948/v1951/v1952 added five more
        #     statuses. A byte count that happens to fit today silently stops covering the tail —
        #     the same defect the vault-quote guard had, fixed there by bounding on the real end.
        i = s.find("window._CH_PILL_MAP = {")
        if i < 0:
            i = s.index("var PILL = {")          # pre-v1949 shape, kept so this reads either
        end = s.index("};", i)
        pills = set(re.findall(r"'([a-z\-]+)':\s*\[", s[i:end]))
        self.assertGreater(len(pills), 5,
                           "the pill map scan found almost nothing (%d) — suspect the instrument "
                           "before the code" % len(pills))
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

    def test_the_demo_gate_never_skips_for_a_missing_console(self):
        """v2121 (#132) — THE LAW GOT STRONGER, SO THE PIN MOVED WITH IT.

        This asserted the string "CONSOLE DEMOS SKIPPED", and v2119 deleted that branch: at
        Konyo's instruction ("you can relaunch and verify you DONT NEED TO WAIT FOR ME TO DO IT
        ... i want it locked as a workflow too") a silent port now STARTS a headless console and
        runs the demos, and failing to start is a FAILURE rather than a skip. So the old pin went
        red on the fix — the same shape as #80. Pin what must be TRUE, not the sentence that used
        to be printed. [[feedback-state-the-bar-not-the-routes]]"""
        h = self._hook()
        self.assertNotIn("CONSOLE DEMOS SKIPPED", h,
                         "the app-down SKIP is back — a UI change can ship unverified again")
        self.assertIn("control_app.py --no-open", h,
                      "the gate no longer starts its own console when :17772 is silent")
        self.assertIn("_demo_rc=1", h,
                      "failing to start a console must be a FAILURE, not a quiet pass")
        self.assertIn("console demos not run", h,
                      "the file-unchanged branch must still say it skipped — that is the branch "
                      "that hid seven versions of a red gate")

    def test_the_gate_stops_only_the_console_it_started(self):
        """The safety half, and it is not optional: :17772 is his LIVE window. The gate may only
        ever start one when the port is already silent, and may only ever stop the pid it started
        — never by name. `pkill -f` cannot tell his console from the gate's and has cost him a
        live window before. [[process-port-discipline]]"""
        import re
        h = self._hook()
        # ⚠ STRIP THE SHELL COMMENTS. The first cut of this assertion fired on the hook's own
        # sentence explaining that it must never use `pkill -f` — the rule forbidding the thing,
        # read as the thing. Eighth time in one night that prose has stood in for code in a check
        # of mine. [[feedback-comments-vs-code]] [[source-reading-guard]]
        code = re.sub(r"(?m)^\s*#.*$", "", h)
        self.assertGreater(len(code.strip()), 800, "the comment strip ate the hook")
        self.assertNotIn("pkill", code,
                         "the hook kills by NAME somewhere — that reaches his live console")
        self.assertIn('kill "$_own_console"', h,
                      "the gate does not stop the console it started, by pid")
        self.assertIn("_own_console=$(cat", h,
                      "the gate does not record WHICH pid it started, so it cannot stop just that one")

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


class TestAKeeperCanNameItsPhotograph(unittest.TestCase):
    """Konyo, on a small charm in his MAGIC locker: "it wrongly muled a random charm.. i dont think
    i even own this.. from what picture is this here?"

    He could not check, and neither could the board. A `magicFinds` row carried {q, base, mods} and
    the checker verdict — and NO frame, reel or session. The card said "Stats read from your
    screenshot" while the data could not say WHICH screenshot: a claim with no receipt.

    ⚠ AND THE RECEIPT WAS ALREADY IN SCOPE. Thirty-seven lines above the writer, the same function
    builds `prop` for kaiChroniclePropose carrying frameId, sessionId and firstSeenTs from `meta` —
    uses them for the chronicle and drops them for the vault. The tally lane (runes/gems/materials)
    has keyed its durable ledger on sid|frameId|name since v889; keepers went through a different
    door and lost it. [[the-unjoined-end]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_the_writer_records_the_frame_and_session(self):
        s = self._src()
        i = s.index("magicFinds[nm] = { q: q || 'magic', base: base, mods: mods,")
        seg = s[i:i + 400]
        for k in ("frameId:", "sessionId:", "at:"):
            self.assertIn(k, seg, "the keeper row drops %s — the receipt is in scope and unused" % k)

    def test_a_row_with_no_frame_SAYS_SO_instead_of_repeating_the_claim(self):
        """An item whose source cannot be produced is exactly the one he is right to distrust."""
        s = self._src()
        self.assertIn("no source frame for this", s)
        self.assertIn("Untick it if you do not own it", s)

    def test_the_UPLOAD_lane_records_the_filename_it_already_had(self):
        """v1934 fixed the aic-judge writer and NAMED this one as still blind. It was not.

        `fname` — the uploaded screenshot's filename — is in scope at the writer, and
        `_vPutShot(fname, …)` has stashed the FULL-RES image in IndexedDB under that same key since
        v365, for click-to-enlarge. So this lane can not only name its source, it can SHOW it. The
        receipt existed, was already keyed, and the row dropped it anyway. [[the-unjoined-end]]"""
        s = self._src()
        i = s.index("magicFinds[nm] = { q: f.q || 'magic'")
        seg = s[i:i + 300]
        self.assertIn("shotFile: fname", seg,
                      "the upload lane still drops the filename it already has in scope")
        self.assertIn("the full-res shot is stored", s,
                      "the card does not offer the shot it can actually produce")

    def test_all_three_provenance_states_are_distinguishable(self):
        """frame · filename · nothing. Collapsing any two of these is how a claim outlives its
        evidence."""
        s = self._src()
        for phrase in ("· frame ", "the full-res shot is stored", "no source frame for this"):
            self.assertIn(phrase, s, "missing the %r branch" % phrase)

    def test_the_provenance_branch_uses_an_escaper_that_EXISTS(self):
        """⚠ It first used `esc`, which is not in that scope — and ONLY the with-provenance branch
        reaches that line, so it threw ReferenceError on exactly the case the feature adds. Testing
        both branches is the only reason it was caught."""
        s = self._src()
        i = s.index("'Stats read from your screenshot \u00b7 frame '".replace("\u00b7", "·"))
        seg = s[i - 200:i + 160]
        self.assertIn("_d2artEsc(", seg)
        self.assertNotIn("+ esc(", seg)


class TestTheRepairJoinedTheOneShotConvention(unittest.TestCase):
    """My v1925 repair mutated another spec's fixture, and CI is what caught it.

    tests/_oneshots.ts derives every boot-apply guard OUT OF bible.html by the pattern
    `d2r_v<version><Thing>Applied`, so a spec that seeds a ledger can boot as a LATER load. It
    exists because a hand-listed version went stale and reported "the app MUTATED his ledger" about
    a correct apply.

    `d2r_setRepairAt` does not match that pattern, so the suppressor could not see it: the repair
    quietly removed two rows from v1692's seeded 110 and the spec read 108 of its own fixture. The
    pre-push smoke subset does not run that spec; **Routine I did**.

    Two keys, two questions, and conflating them is why this took a CI round-trip:
        d2r_setRepairAt                    WHICH READING did this act on (staleness)
        d2r_v1925RemainingRepairApplied    is a SPEC booting a later load (suppression)

    ⚠ Suppression covers the game-Remaining apply only. The unique-in-the-set-store branch is NOT
    suppressed, because "this is a unique" is a structural invariant, not a one-shot decision, and
    it does not go stale. Measured: his board removes 3, a suppressed spec removes 1.
    [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]
    """

    def _src(self):
        with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
            return fh.read()

    def test_the_flag_matches_the_pattern_the_suppressor_derives(self):
        import re
        s = self._src()
        flags = set(re.findall(r"d2r_v\d{3,4}[A-Za-z]*Applied", s))
        self.assertIn("d2r_v1925RemainingRepairApplied", flags,
                      "the repair's guard does not match d2r_v<version><Thing>Applied, so "
                      "tests/_oneshots.ts cannot see it and it will mutate seeded fixtures")

    def test_only_the_expiring_branch_is_suppressed(self):
        """A structural invariant must not be switched off by a test convenience."""
        s = self._src()
        # v1946 — same re-point: the suppression flag still guards the same branch, beside the
        # recorded ruling that replaced the inferred one.
        self.assertIn("if (missing[n] && !_repairKept[n] && !_repairSuppressed)", s)
        i_uni = s.index("it was routed into the set ledger by mistake")
        i_supp = s.index("!_repairSuppressed")
        self.assertLess(i_uni, i_supp,
                        "the unique branch must run before, and independently of, the suppressible "
                        "one — a unique in the set store is wrong on every load")


if __name__ == "__main__":
    unittest.main(verbosity=2)
