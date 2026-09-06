# -*- coding: utf-8 -*-
"""THE GATE ON THE END-ROUTE PREDICATE — and every law here has been seen RED.

`tv/end_routes.py` claims to have REVERSE-ENGINEERED the end route from the 410 reels that already
reached it. That is a claim about his footage, and a claim about footage that no longer exists is
exactly the kind that rots quietly. So this gate does two different jobs:

  1. it pins the LAWS of the predicate against fixtures that are REAL ROWS from his stores, copied
     verbatim, so the gate runs on a CI runner that has never seen a reel; and
  2. it re-derives the predicate from the tombstone ledger when the ledger IS present, so a door
     edited tomorrow stops explaining the journeys it was read off and this goes red.

⚠⚠ THE FIXTURES RUN IN BOTH DIRECTIONS, DELIBERATELY. A predicate proved only on reels that
qualified is a predicate never tested in the direction that matters — the refusing one. Every door
below has at least one fixture that OPENS it and one that REFUSES it, and
`test_the_fixtures_exercise_both_directions` counts them, because a gate whose fixtures all fall on
one side is measuring nothing. [[gate-blind-to-unexercised-input]] [[feedback-blind-fixture-green-gate]]

⚠ NO FIXTURE TOUCHES A LIVE STORE. Every case passes `hist_dir=<tmp>` explicitly — no env var, no
module attribute — and `test_the_fixture_really_redirects` asserts all four resolved paths land
under the tmp dir. Setting up an isolation and never checking it took is the conftest incident.
[[feedback-fixtures-never-touch-live-data]]

=== THE SABOTAGE PASS — 16 of 16 LAWS PROVED RED, 2026-09-06 ========================

Every `test_LAW_*` below was made to fail before it was trusted. Each mutation was applied to a
COPY of the module in a scratch dir (the live files were verified byte-identical afterwards) and
each printed its MATCH COUNT, because a sabotage that matches nothing is a fake green and this repo
has been fooled by that four times in one day. [[sabotage-is-usually-the-wrong-one]]

    16 of 16 RED · bad anchors 0 · vacuous laws 0

Two of those laws were red BEFORE any sabotage, on the first run, and both were real defects in
`end_routes.py` rather than in the tests:
  · a fixture that omitted `reel_tombstones.json` silently read his LIVE 410-row ledger, so the
    "an absent ledger is UNKNOWN" law was grading data it could not control — REG-570's class,
    reproduced inside a module about REG-570;
  · a QUALIFIED reel still published the REFUSING door's gaps as `missing`, describing a reel that
    had reached the end route as stuck — and the module's own docstring already said otherwise.

A third was caught by a reach assertion rather than by a sabotage: `test_no_fixture_id_names_a_live
_reel` scanned `end_routes.py` instead of its own source and found ZERO ids in a file that defines
four. That is why every source-reading law here asserts on its own reach first.

The `test_SABOTAGE_*` methods below are the ones cheap enough to run EVERY time — they mutate
fixture data rather than source — so the expensive proof is not the only proof.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import end_routes as ER  # noqa: E402

SRC_PATH = os.path.join(HERE, "end_routes.py")
TEST_PATH = os.path.abspath(__file__)
SRC = io.open(SRC_PATH, encoding="utf-8").read()
TREE = ast.parse(SRC)


# ══ THE FIXTURES — REAL ROWS, WITH SYNTHESISED IDS ════════════════════════════════════════════
#
# Every VALUE below is verbatim from his stores, read 2026-09-06. Every ID is synthetic, stamped
# 15000000xxxxx — July 2017, before the recorder existed, so no reel can ever carry one.
#
# ⚠⚠ AND THE ID RULE IS NOT COSMETIC — THIS FILE MINTED THE DEFECT IT DESCRIBES, ONCE. The first
# cut used the real ids as literals. `frame_authority.test_referenced_reels` scans `tv/*.py` for
# `reel_s_\d{10,16}_\d+`, and a match makes `reel_retention.plan()` hold that reel with the reason
# *"the TEST SUITE opens this reel by name"*. Measured immediately after writing it: the live reel
# behind F_HELD flipped from `zero-pages` to `test-fixture`, and the ladder's tally moved
# `test-fixture 8 -> 9` / `zero-pages 27 -> 26` with nothing about his footage having changed.
# That is v2071 exactly: the hold errs toward KEEPING so nothing was endangered, but the REASON was
# false, and a wrong reason is how a real hold later gets dismissed as noise. These tests read no
# footage — only JSON store rows in a tmp dir — so there is nothing here to protect.
#
# `_executable_only` strips COMMENTS AND DOCSTRINGS and keeps string literals, so the real ids are
# recorded HERE, in prose, where the scanner cannot see them and a human can:
#
#     F_STRUCTURAL_WORKED  is  reel_ s_1785083099664_77787   (tombstoned, gone)
#     F_SEMANTIC_WORKED    is  reel_ s_1787520892804_95400   (tombstoned, gone)
#     F_HELD               is  reel_ s_1788189355803_72106   (LIVE on his shelf — the reason above)
#
# `test_no_fixture_id_names_a_live_reel` enforces it, and is proved red in the sabotage pass.

#: WORKED, STRUCTURAL DOOR. 175.7 MB, deleted 2026-09-01. Never read (pages 0), never vault-sealed,
#: and released anyway because a FULL structural pass found no panel on any of its 126 frames.
#: 396 of the 410 left exactly like this.
F_STRUCTURAL_WORKED = "reel_s_1500000077787_1"

#: WORKED, SEMANTIC DOOR. 1,779.8 MB, deleted 2026-09-01. The structural door REFUSED it — 135
#: panel frames — and it left anyway on 16 chronicle pages and a vault seal carrying 7 rows. This
#: single reel is why the predicate is a DISJUNCTION: an AND would have kept it forever.
F_SEMANTIC_WORKED = "reel_s_1500000095400_1"

#: STUCK TODAY. 123 unread stash panels, 0 pages, no vault seal. The shape 26 of his 40 are in.
F_HELD = "reel_s_1500000072106_1"

#: STUCK TODAY, AND THE OPPOSITE FAILURE: nothing has ever surveyed it. Its verdict must be
#: UNKNOWN-flavoured, never a confident refusal.
F_NEVER_SURVEYED = "reel_s_1500000000000_1"

#: The 2017 floor. A stamp at or above this is synthetic by construction — the recorder did not
#: exist, so no footage can carry one. Named once; `test_no_fixture_id_names_a_live_reel` uses it.
SYNTHETIC_BEFORE_MS = 1500000000000
SYNTHETIC_CEILING_MS = 1600000000000        # Sep 2020, still years before the first reel

RETRO = {
    F_STRUCTURAL_WORKED: {"panels": 0, "frames": 126, "kinds": {}, "ts": 1788224607573,
                          "full": True},
    F_SEMANTIC_WORKED: {"panels": 135, "frames": 1270, "kinds": {"panel": 135},
                        "ts": 1788224593710, "full": True},
    F_HELD: {"panels": 123, "frames": 154, "kinds": {"stash": 123}, "ts": 1788267085686,
             "full": True},
}
CHRON = {
    F_STRUCTURAL_WORKED: {"ts": 1787800843779, "classified": 1, "pages": 0,
                          "promptVer": "p1839", "agentVer": "v2184"},
    F_SEMANTIC_WORKED: {"ts": 1787537117488, "classified": 1217, "pages": 16,
                        "promptVer": "p1839", "agentVer": "v2037"},
    F_HELD: {"ts": 1788227399688, "classified": 5, "pages": 0, "promptVer": "p1839",
             "agentVer": "v2372"},
}
#: ⚠ KEYED BARE, exactly as his vault_swept.json is. `lookup_either_way` is what reconciles the two
#: key forms, and a fixture that quietly used the prefixed form everywhere would never exercise it.
VAULT = {
    F_SEMANTIC_WORKED[len("reel_"):]: {"ts": 1787532331034, "rows": 7, "promptVer": "vp2017",
                                       "agentVer": "v2037"},
}
LEDGER = {"reels": [
    {"reel": F_STRUCTURAL_WORKED, "session": F_STRUCTURAL_WORKED[len("reel_"):],
     "mb": 175.7, "pages": 0,
     "why": "read (0 pages) and sealed by BOTH lanes — it has given up its information",
     "deletedTs": 1788224948449, "frames": 127, "focus": None, "startedTs": None},
    {"reel": F_SEMANTIC_WORKED, "session": F_SEMANTIC_WORKED[len("reel_"):],
     "mb": 1779.8, "pages": 16,
     "why": "read (16 pages) and sealed by BOTH lanes — it has given up its information",
     "deletedTs": 1788262484839, "frames": 1271, "focus": None, "startedTs": None},
], "updatedTs": 1788262484840}


def _fixture_dir(retro=None, chron=None, vault=None, ledger=None, omit=()):
    d = tempfile.mkdtemp(prefix="end_routes_fix_")
    for nm, blob in (("retro_triage.json", RETRO if retro is None else retro),
                     ("chronicle_swept.json", CHRON if chron is None else chron),
                     ("vault_swept.json", VAULT if vault is None else vault),
                     ("reel_tombstones.json", LEDGER if ledger is None else ledger)):
        if nm in omit:
            continue
        with io.open(os.path.join(d, nm), "w", encoding="utf-8") as fh:
            json.dump(blob, fh)
    return d


def _fn(name):
    """The AST node of one top-level function. -> ast.FunctionDef or None."""
    for n in TREE.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


class EndRoutePredicate(unittest.TestCase):

    def setUp(self):
        self._dirs = []

    def tearDown(self):
        for d in self._dirs:
            shutil.rmtree(d, ignore_errors=True)

    def _fix(self, **kw):
        d = _fixture_dir(**kw)
        self._dirs.append(d)
        return d

    # ── ⚠ A LAW THAT CANNOT FIND ITS SUBJECT PASSES HAVING EXAMINED NOTHING ────────────────────

    def test_the_guard_can_find_its_subject_AT_ALL(self):
        self.assertIsNotNone(_fn("structural_door"), "structural_door is gone or renamed")
        self.assertIsNotNone(_fn("semantic_door"), "semantic_door is gone or renamed")
        self.assertIsNotNone(_fn("verdict"), "verdict is gone or renamed")
        self.assertIsNotNone(_fn("derived_from"), "derived_from is gone or renamed")
        self.assertEqual(("structural", "semantic"), tuple(ER.DOORS),
                         "the doors this gate was written against are not the doors the module "
                         "declares — every law below would be grading a different predicate")

    def test_the_fixture_really_redirects(self):
        """⚠ THE ISOLATION IS ASSERTED, NOT ASSUMED. `_store_paths` falls back to HERE for any file
        the fixture does not supply — which is the DELETER's real behaviour and correct — so a
        fixture missing one store would silently grade against his live one."""
        d = self._fix()
        paths = ER.sources(hist_dir=d)["paths"]
        self.assertEqual(4, len(paths))
        for nm, p in paths.items():
            self.assertTrue(os.path.realpath(p).startswith(os.path.realpath(d)),
                            "%s resolved to %s — OUTSIDE the fixture. A gate reading his live "
                            "store is grading data it cannot control." % (nm, p))

    def test_no_fixture_id_names_a_live_reel(self):
        """⚠⚠ v2071's DEFECT, WHICH THIS FILE COMMITTED AND THEN CLOSED. A reel id written into a
        test as a LITERAL is picked up by `frame_authority.test_referenced_reels` (it scans
        `tv/*.py` for `reel_s_\\d{10,16}_\\d+` after stripping comments and docstrings) and
        `reel_retention.plan()` then holds that reel as *"the TEST SUITE opens this reel by name"*.
        These tests read no footage, so any such hold carries a FALSE REASON.

        ⚠ IT CHECKS THE SCANNED TEXT, NOT MY OWN CONSTANTS — a future fixture added inline would
        escape a law that only walked F_*. And it runs BOTH ways: every id must be 2017-stamped,
        AND (when his shelf is readable) none may be on disk. On a runner with no shelf the second
        half reports what it could not reach rather than passing silently.
        [[source-reading-guard]] [[regression-guard]]"""
        import re
        import frame_authority as FA
        # ⚠ THIS FILE'S OWN SOURCE, NOT end_routes.py's. The first cut passed `SRC` — the module
        # under test — and the scan returned ZERO ids from a file that plainly defines four. It was
        # caught only by the reach assertion two lines down, which is the entire reason that
        # assertion exists: a law pointed at the wrong subject passes having examined nothing.
        # [[source-reading-guard]]
        own = io.open(TEST_PATH, encoding="utf-8").read()
        scanned = FA._executable_only(own, TEST_PATH)
        ids = sorted(set(re.findall(r"reel_s_\d{10,16}_\d+", scanned)))
        self.assertGreaterEqual(len(ids), 4,
                                "the scan found %d id(s) in a file that plainly defines four "
                                "fixtures — the LAW is broken, not the fixtures: %r"
                                % (len(ids), ids))
        for rid in ids:
            stamp = int(rid.split("_")[2])
            self.assertTrue(SYNTHETIC_BEFORE_MS <= stamp < SYNTHETIC_CEILING_MS,
                            "%s carries a REAL epoch stamp. A literal reel id in this file makes "
                            "reel_retention hold that reel as a test fixture, with a reason that "
                            "is false — these tests read no footage. Use a 2017 stamp and name the "
                            "real reel in a comment, where the scanner cannot see it." % rid)
        hist = os.path.join(HERE, "frames", "hist")
        try:
            on_disk = set(d for d in os.listdir(hist) if d.startswith("reel_"))
        except OSError as e:
            sys.stderr.write("\n  [end_routes] shelf unreadable (%s) — the on-disk half of this "
                             "law examined NOTHING; the stamp half above still ran\n"
                             % str(e)[:60])
            return
        clash = sorted(set(ids) & on_disk)
        self.assertEqual([], clash,
                         "fixture id(s) %r name reels that are ON HIS SHELF right now — they will "
                         "be held as test fixtures for a reason that is not true" % clash)

    def test_the_fixtures_exercise_both_directions(self):
        """⚠ A DOOR WITH NO REFUSING FIXTURE IS UNTESTED IN THE ONLY DIRECTION THAT PROTECTS
        FOOTAGE. Counted, and printed, so 'both directions' is a number rather than a belief."""
        d = self._fix()
        src = ER.sources(hist_dir=d)
        tally = {"structural": {True: 0, False: 0, None: 0},
                 "semantic": {True: 0, False: 0, None: 0}}
        for r in (F_STRUCTURAL_WORKED, F_SEMANTIC_WORKED, F_HELD, F_NEVER_SURVEYED):
            tally["structural"][ER.structural_door(r, src)[0]] += 1
            tally["semantic"][ER.semantic_door(r, src)[0]] += 1
        for door in ER.DOORS:
            self.assertGreaterEqual(tally[door][True], 1,
                                    "%s: no fixture OPENS this door — %r" % (door, tally[door]))
            self.assertGreaterEqual(tally[door][False], 1,
                                    "%s: no fixture REFUSES this door, so the clause that holds "
                                    "footage is unexercised — %r" % (door, tally[door]))
        self.assertGreaterEqual(tally["structural"][None], 1,
                                "no fixture leaves a door UNASKED, so the unknown path is "
                                "unexercised — %r" % (tally["structural"],))

    # ── ⚠⚠ THE LAWS ───────────────────────────────────────────────────────────────────────────

    def test_LAW_the_structural_door_alone_qualifies_a_reel(self):
        """396 of the 410 left this way: never read, never sealed, and PROVEN to hold no panel."""
        d = self._fix()
        v = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
        self.assertEqual("QUALIFIED", v["say"], v["why"])
        self.assertEqual("structural", v["door"])
        self.assertEqual(0, v["evidence"]["structural"]["panels"])
        self.assertEqual(0, v["evidence"]["semantic"]["pages"],
                         "this reel was NEVER READ — if the fixture says otherwise the law below "
                         "is not proving what it claims")
        self.assertIs(False, v["evidence"]["semantic"]["vaultSealed"])

    def test_LAW_the_semantic_door_alone_qualifies_a_reel(self):
        """The other 13. 135 panel frames — the structural door REFUSES it — and it left anyway."""
        d = self._fix()
        v = ER.verdict(F_SEMANTIC_WORKED, hist_dir=d)
        self.assertEqual("QUALIFIED", v["say"], v["why"])
        self.assertEqual("semantic", v["door"])
        self.assertEqual(135, v["evidence"]["structural"]["panels"],
                         "the structural door must genuinely refuse this reel, or the "
                         "disjunction is not what is being proved")
        # ⚠ NOTHING IS MISSING FOR A REEL THAT QUALIFIED — but the refusing door's finding is not
        # thrown away either. The first cut published it as `missing` and described a reel that had
        # reached the end route as stuck.
        self.assertEqual([], v["missing"])
        self.assertTrue([g for g in v["doorGaps"] if g["door"] == "structural"],
                        "the refusing door's finding was discarded rather than kept as context")

    def test_LAW_the_predicate_is_a_DISJUNCTION_not_a_conjunction(self):
        """⚠⚠ THE ONE THAT COST SOMETHING. 392 of the 396 structural releases have NO vault seal,
        so requiring both doors would have refused 96% of every end-route journey that has ever
        happened — the collapse v2312 attempted on the reel/frame doors and withdrew at v2314.
        Proved by two real reels, each of which satisfies exactly ONE door."""
        d = self._fix()
        a = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
        b = ER.verdict(F_SEMANTIC_WORKED, hist_dir=d)
        self.assertEqual(["structural"], a["openedDoors"])
        self.assertEqual(["semantic"], b["openedDoors"])
        self.assertEqual("QUALIFIED", a["say"])
        self.assertEqual("QUALIFIED", b["say"])
        self.assertEqual(set(), set(a["openedDoors"]) & set(b["openedDoors"]),
                         "the two reels the disjunction rests on satisfy the SAME door, so this "
                         "test could pass under a conjunction")

    def test_LAW_a_PARTIAL_survey_never_qualifies(self):
        """A sampled pass that missed the only stash frame reads identically to an empty reel, and
        this is the clause that stands between that and footage with no un-delete."""
        retro = json.loads(json.dumps(RETRO))
        retro[F_STRUCTURAL_WORKED]["full"] = False
        d = self._fix(retro=retro)
        v = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
        self.assertNotEqual("QUALIFIED", v["say"],
                            "a SAMPLED survey opened the end route — %s" % v["why"])
        self.assertIn("a FULL structural pass", [g["what"] for g in v["missing"]])

    def test_LAW_zero_is_measured_and_None_is_nobody_looked(self):
        """⚠ THE COLLAPSE THIS REPO REFUSES. `panels: 0` released 396 reels; a reel nobody surveyed
        must never borrow that verdict."""
        d = self._fix()
        seen = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
        never = ER.verdict(F_NEVER_SURVEYED, hist_dir=d)
        self.assertEqual(0, seen["evidence"]["structural"]["panels"])
        self.assertIsNone(never["evidence"]["structural"]["panels"],
                          "a reel nobody surveyed reports a panel COUNT — 0 and 'nobody looked' "
                          "have been collapsed")
        self.assertNotEqual("QUALIFIED", never["say"], never["why"])
        self.assertIn("structural", never["unaskedDoors"],
                      "the unasked door is not named, so a refusal reads as settled")
        gaps = {g["what"]: g for g in never["missing"]}
        self.assertIn("a structural survey", gaps)
        self.assertIsNone(gaps["a structural survey"]["measured"])
        self.assertIs(False, gaps["a structural survey"]["looked"])

    def test_LAW_an_unreadable_store_is_UNKNOWN_not_a_refusal(self):
        """'I could not read the ledger' and 'there is nothing there' are opposite facts, and only
        one of them is safe to act on."""
        d = self._fix()
        for nm in ("retro_triage.json", "chronicle_swept.json"):
            with io.open(os.path.join(d, nm), "w", encoding="utf-8") as fh:
                fh.write("{ this will not parse")
        v = ER.verdict(F_HELD, hist_dir=d)
        self.assertEqual("UNKNOWN", v["say"], v["why"])
        self.assertIsNone(v["missing"],
                          "an UNKNOWN verdict published a `missing` list, which reads as a "
                          "measured refusal")
        self.assertEqual([], v["askedDoors"])

    def test_LAW_a_HELD_reel_names_the_number_that_is_missing(self):
        """⚠ THE VALUABLE HALF. 'not eligible' is what every surface says today; this must say
        WHAT and HOW MANY."""
        d = self._fix()
        v = ER.verdict(F_HELD, hist_dir=d)
        self.assertEqual("HELD", v["say"], v["why"])
        gaps = {g["what"]: g for g in v["missing"]}
        self.assertIn("panels read", gaps)
        self.assertEqual(123, gaps["panels read"]["measured"])
        self.assertEqual(0, gaps["panels read"]["needed"])
        self.assertIn("chronicle pages", gaps)
        self.assertEqual(0, gaps["chronicle pages"]["measured"])
        self.assertEqual(1, gaps["chronicle pages"]["needed"])
        self.assertIn("stash 123", gaps["panels read"]["why"],
                      "the gap does not say WHAT KIND of panel is unread, so nobody can route it")
        for g in v["missing"]:
            self.assertIs(g["looked"], g["measured"] is not None,
                          "`looked` and `measured` disagree on %r" % (g["what"],))

    def test_LAW_a_HELD_verdict_never_hides_an_unasked_door(self):
        d = self._fix()
        v = ER.verdict(F_NEVER_SURVEYED, hist_dir=d)
        self.assertNotEqual("QUALIFIED", v["say"])
        self.assertTrue(v["unaskedDoors"])
        self.assertIn("NEVER ASKED", v["why"],
                      "a reel refused on one door while the other was never asked reads as a "
                      "settled refusal — %s" % v["why"])

    def test_LAW_the_page_floor_is_the_DELETERs_not_a_copy(self):
        """⚠ A SECOND COPY OF MIN_PAGES WOULD BE FREE TO DRIFT FROM THE DOOR IT DESCRIBES. AST, not
        a substring scan: a module-level `MIN_PAGES = 1` is the defect, and a comment mentioning it
        is not. [[copy-drift]] [[source-reading-guard]]"""
        import reel_retention as RR
        d = self._fix()
        self.assertEqual(RR.MIN_PAGES, ER.sources(hist_dir=d)["minPages"],
                         "the page floor does not come from reel_retention")
        for node in ast.walk(TREE):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "MIN_PAGES":
                        self.fail("end_routes.py assigns its own MIN_PAGES at line %d — a copy of "
                                  "the deleter's constant" % node.lineno)

    # ── ⚠⚠ THE SELF-REFUTING LAW — the predicate must still explain the reels it came from ─────

    def test_LAW_the_derivation_still_explains_the_ledger_it_was_read_off(self):
        d = self._fix()
        got = ER.derived_from(hist_dir=d)
        self.assertTrue(got["ok"], got.get("why"))
        self.assertEqual(2, got["rows"])
        self.assertEqual({"structural": 1, "semantic": 1}, got["byDoor"],
                         "the two reels the predicate was derived from are no longer explained by "
                         "the doors it declares — %s" % got["why"])
        self.assertGreaterEqual(got["coverage"], ER.DERIVED_COVERAGE_FLOOR)

    def test_LAW_an_absent_ledger_is_UNKNOWN_never_zero(self):
        """⚠ `rows: 0` would read as 'no reel has ever reached the end route' on a runner that
        simply has no ledger. That is the exact rot `_tombstone_census` exists to prevent, one
        module over. [[zero-needs-a-denominator]]"""
        d = self._fix(omit=("reel_tombstones.json",))
        got = ER.derived_from(hist_dir=d)
        self.assertFalse(got["ok"])
        self.assertIsNone(got["rows"], "an absent ledger reported a COUNT")
        self.assertIn("UNKNOWN", got["why"])

    def test_LAW_the_label_contradiction_is_COUNTED_not_narrated(self):
        """Every tombstone says 'sealed by BOTH lanes'. On his real ledger 395 of 410 have no vault
        seal in any store. A number a reader has to regex off English is a number nothing can join
        to."""
        d = self._fix()
        got = ER.derived_from(hist_dir=d)
        self.assertEqual(1, got["labelContradictions"],
                         "the structural-door fixture claims 'sealed by BOTH lanes' and has no "
                         "vault seal; the count did not see it")

    # ── ⚠ SOURCE-TEXT LAWS, ASKED OF THE AST — a grep would pass over an `if False:` branch ────

    def test_LAW_the_module_cannot_WRITE_delete_or_arm_anything(self):
        """⚠⚠ THE ONE THAT MATTERS MOST. The prune is disarmed by his standing ruling and this
        module exists to REPORT. Asked of the parse tree, so a writer hidden behind a constant-false
        branch, an alias, or a string this gate never greps for is still seen."""
        banned_calls = {"rmtree", "remove", "unlink", "replace", "rename", "rmdir", "truncate",
                        "apply_plan", "system", "Popen", "run", "call", "check_output"}
        found = []
        for node in ast.walk(TREE):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name)
                                                                else "")
            if nm in banned_calls:
                found.append("%s at line %d" % (nm, node.lineno))
            if nm == "open":
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if mode is not None and any(c in str(mode) for c in "wax+"):
                    found.append("open(mode=%r) at line %d" % (mode, node.lineno))
            if nm in ("dump",) and isinstance(fn, ast.Attribute) and len(node.args) > 1:
                found.append("json.dump to a file at line %d" % node.lineno)
        self.assertEqual([], found,
                         "end_routes.py can write, delete or execute: %s. It is a READER." % found)

    def test_LAW_both_doors_are_REACHED_by_the_verdict(self):
        """⚠ A door defined and never called is a predicate with one clause wearing two names. AST,
        because the call could be behind a constant-false branch and a grep would not care."""
        v = _fn("verdict")
        called, unreachable = set(), []
        for node in ast.walk(v):
            if isinstance(node, ast.Name) and node.id in ("structural_door", "semantic_door"):
                called.add(node.id)
        self.assertEqual({"structural_door", "semantic_door"}, called,
                         "verdict() does not reference both doors — it references %r" % (called,))
        for node in ast.walk(TREE):
            if isinstance(node, ast.If) and isinstance(node.test, ast.Constant) \
                    and not node.test.value:
                unreachable.append(node.lineno)
        self.assertEqual([], unreachable,
                         "constant-false branch(es) at %r — a law passing over one has examined "
                         "nothing" % unreachable)

    # ══ THE SABOTAGES — every law above, proved RED ═══════════════════════════════════════════
    #
    # ⚠ A GREEN SABOTAGE IS USUALLY THE SABOTAGE'S FAULT, so each one asserts on the value it
    # changed as well as on the verdict: a mutation that matched nothing cannot pass for a law
    # that held. [[sabotage-is-usually-the-wrong-one]]

    def test_SABOTAGE_a_conjunction_would_refuse_396_of_the_410(self):
        """Strip the structural reel's page count to what an AND would demand and it stays out;
        this is the measured consequence, not a hypothetical."""
        d = self._fix()
        src = ER.sources(hist_dir=d)
        opened_alone = 0
        for r in (F_STRUCTURAL_WORKED, F_SEMANTIC_WORKED):
            s = ER.structural_door(r, src)[0]
            m = ER.semantic_door(r, src)[0]
            self.assertNotEqual((True, True), (s, m),
                               "%s satisfies BOTH doors, so it cannot demonstrate the "
                               "disjunction" % r)
            opened_alone += 1 if (s is True) != (m is True) else 0
        self.assertEqual(2, opened_alone,
                         "the two reels do not each open exactly one door — the disjunction law "
                         "is proving nothing")

    def test_SABOTAGE_deleting_a_ledger_row_moves_the_derivation(self):
        led = {"reels": [LEDGER["reels"][0]], "updatedTs": 1}
        d = self._fix(ledger=led)
        got = ER.derived_from(hist_dir=d)
        self.assertEqual(1, got["rows"], "the ledger sabotage matched nothing")
        self.assertEqual({"structural": 1}, got["byDoor"])

    def test_SABOTAGE_an_unexplainable_row_drops_the_coverage_below_the_floor(self):
        """The refutation condition, run as a test: a reel in the ledger that NO door explains.
        This is exactly `reel_s_222_2` on his real tree — a test fixture that reached the permanent
        deletion record — and the predicate must not silently absorb it."""
        led = {"reels": list(LEDGER["reels"]) + [
            {"reel": "reel_s_222_2", "session": "s_222_2", "mb": 9.5, "pages": 31,
             "why": "read and sealed by BOTH lanes", "deletedTs": 1787604588927,
             "frames": 4, "focus": "chronicle-sets", "startedTs": None}], "updatedTs": 1}
        d = self._fix(ledger=led)
        got = ER.derived_from(hist_dir=d)
        self.assertEqual(3, got["rows"], "the sabotage row did not reach the derivation")
        self.assertEqual(1, len(got["unexplained"]))
        self.assertEqual("reel_s_222_2", got["unexplained"][0]["reel"])
        self.assertLess(got["coverage"], ER.DERIVED_COVERAGE_FLOOR,
                        "an unexplained row left coverage above the floor, so the self-refuting "
                        "law cannot fire — coverage %r" % got["coverage"])

    def test_SABOTAGE_a_panel_appearing_flips_QUALIFIED_to_HELD(self):
        retro = json.loads(json.dumps(RETRO))
        retro[F_STRUCTURAL_WORKED]["panels"] = 1
        d = self._fix(retro=retro)
        v = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
        self.assertEqual("HELD", v["say"], v["why"])
        self.assertEqual(1, {g["what"]: g["measured"]
                             for g in v["missing"]}.get("panels read"),
                         "the panel sabotage did not reach the gap list")

    def test_SABOTAGE_a_non_integer_panel_count_HOLDS_rather_than_qualifying(self):
        """REG-573's class, one store over: `panels: true` is a bool, and bool is a subclass of int.
        A count that is not a whole number is an UNREADABLE survey, not a small one."""
        for bad in (True, "many", [1, 2], 1.5):
            retro = json.loads(json.dumps(RETRO))
            retro[F_STRUCTURAL_WORKED]["panels"] = bad
            d = self._fix(retro=retro)
            v = ER.verdict(F_STRUCTURAL_WORKED, hist_dir=d)
            self.assertNotEqual("QUALIFIED", v["say"],
                               "panels=%r opened the end route — %s" % (bad, v["why"]))
            self.assertIn("a whole-number panel count", [g["what"] for g in v["missing"]],
                          "panels=%r did not raise the unreadable-count gap" % (bad,))

    def test_SABOTAGE_the_vault_key_form_is_reconciled_not_guessed(self):
        """His vault_swept.json keys BARE and his chronicle_swept.json keys PREFIXED. If the
        lookup stopped reconciling them, the semantic reel loses its seal and falls out."""
        _bare = F_SEMANTIC_WORKED[len("reel_"):]
        vault = {"reel_" + _bare: VAULT[_bare]}
        d = self._fix(vault=vault)
        v = ER.verdict(F_SEMANTIC_WORKED, hist_dir=d)
        self.assertIs(True, v["evidence"]["semantic"]["vaultSealed"],
                      "the prefixed key form was not found — %s" % v["why"])
        d2 = self._fix(vault={})
        v2 = ER.verdict(F_SEMANTIC_WORKED, hist_dir=d2)
        self.assertIs(False, v2["evidence"]["semantic"]["vaultSealed"],
                      "an EMPTY vault store still reported a seal — the sabotage matched nothing")
        self.assertEqual("HELD", v2["say"],
                         "the semantic door opened without its vault clause — %s" % v2["why"])

    def test_SABOTAGE_a_writer_added_to_the_module_would_be_caught(self):
        """⚠ PROVE THE WRITER LAW GOES RED, on a synthetic tree, without touching the real file.
        A law that has only ever seen its own subject clean is a law nobody has tested."""
        bad = ast.parse("import json\n"
                        "def f(p):\n"
                        "    if False:\n"
                        "        with open(p, 'w') as fh:\n"
                        "            json.dump({}, fh)\n")
        hits = []
        for node in ast.walk(bad):
            if isinstance(node, ast.Call):
                fn = node.func
                nm = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name)
                                                                    else "")
                if nm == "open" and len(node.args) > 1 and isinstance(node.args[1], ast.Constant) \
                        and "w" in str(node.args[1].value):
                    hits.append(node.lineno)
                if nm == "dump" and len(node.args) > 1:
                    hits.append(node.lineno)
        self.assertEqual(2, len(hits),
                         "the writer scan found %d call(s) in a tree that plainly contains two — "
                         "the LAW is broken, not the module" % len(hits))
        falsey = [n.lineno for n in ast.walk(bad)
                  if isinstance(n, ast.If) and isinstance(n.test, ast.Constant) and not n.test.value]
        self.assertEqual(1, len(falsey),
                         "the constant-false detector missed an `if False:` — a grep-shaped law "
                         "would have passed over this whole branch")


# ══ HIS REAL TREE — this class MEASURES rather than skipping ═══════════════════════════════════

class OnHisRealShelf(unittest.TestCase):
    """⚠⚠ A SKIP IS NOT A PASS. CI has no reels and no ledger, so these cannot assert on his
    numbers — but they must not vanish either. Each one reports what it could and could not reach,
    and fails only on a CONTRADICTION, never on absence. [[regression-guard]]"""

    def test_the_real_ledger_if_present_is_still_explained(self):
        src = ER.sources()
        if src.get("ledgerState") != "ok":
            self.assertIsNone(ER.derived_from(src=src)["rows"],
                              "no ledger here, and the derivation reported a COUNT anyway")
            return
        got = ER.derived_from(src=src)
        sys.stderr.write("\n  [end_routes] real ledger: %d row(s) %r coverage=%.4f "
                         "labelContradictions=%d\n"
                         % (got["rows"], got["byDoor"], got["coverage"] or 0,
                            got["labelContradictions"]))
        self.assertGreaterEqual(got["coverage"], ER.DERIVED_COVERAGE_FLOOR,
                                "the predicate no longer explains the reels it was derived from "
                                "— %s" % got["why"])
        self.assertGreater(got["byDoor"].get("structural", 0),
                           got["byDoor"].get("semantic", 0),
                           "the STRUCTURAL door is no longer the majority route. That was the "
                           "whole finding (396 vs 13); if it has flipped, the predicate was "
                           "re-derived from a different ledger and this gate is stale.")

    def test_a_reel_is_never_both_QUALIFIED_and_dead_ended(self):
        """The contradiction check that costs nothing and needs no shelf."""
        src = ER.sources()
        for r in sorted((src.get("structural") or {}))[:60]:
            v = ER.verdict(r, src=src)
            self.assertFalse(v["say"] == "QUALIFIED" and v["missing"],
                             "%s is QUALIFIED and still lists something missing: %r"
                             % (r, v["missing"]))
            self.assertFalse(v["say"] == "HELD" and not v["missing"],
                             "%s is HELD and names nothing missing — 'not eligible' with no "
                             "reason is what this module exists to replace" % r)


if __name__ == "__main__":
    unittest.main(verbosity=2)
