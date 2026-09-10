#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A LANE THAT SITS DARK MUST SAY SO — and nothing in this console could say it.

⚠⚠ THE STATE THIS GATE EXISTS FOR, in `shelf_driver`'s own words: *"a lane with work owed and a
heartbeat that has stopped is the state `vaultAutoread` sat in for weeks with `reads: 0,
lastTs: null` and nothing said so."* Heart 2.0 asks whether the GATES can still go red;
`lane_liveness` asks whether a THREAD is still ticking. Neither joins "there is work owed" to "this
lane has done a unit of work", and a lamp that cannot report the dark is not a lamp.

⚠ MEASURED 2026-09-10 on his tree, and the invisibility was structural, not accidental. `beat()`
wrote `owedByLane`, which is built by COUNTING owed reels — so a lane owing zero was ABSENT from the
record entirely. His stored beat read `{"vault": 18}`. The chronicle lane exists, has a store, has a
watchdog on the roster, and appeared nowhere at all. Absent and healthy looked identical.

⚠⚠ AND THE READINGS COME OFF DISK, NEVER OUT OF PROCESS MEMORY — #60's lesson one level up. A
process-local counter reports a RESTART as "this lane has never swept", which is a completely
different accusation from the truth. Every law below drives the census over a store on disk.

⚠ NO FOOTAGE, NO LIVE STORE, NO LIVE PLAN. Every law here injects `work_` and `beats`, or points a
fixture module's store at a `tempfile` directory. Nothing in this file can read his shelf and
nothing in it can write into his `tv/`. [[feedback-fixtures-never-touch-live-data]]
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import shelf_driver as SD  # noqa: E402

OWNER = "shelf_driver_supervision_fixture_owner"


def _plan_says(owed=(), releasable=(), on_disk=None):
    """The shape `work()` returns, with nothing computed. -> dict

    ⚠ THIS IS NOT A SECOND PREDICATE, IT IS THE FIRST ONE'S OUTPUT HELD STILL. The census is given
    an answer and asked what it concludes; it is never asked to work out who owes what. A fixture
    that recomputed the work-list would be the exact defect the module is named after.
    """
    return {"ok": True, "why": "",
            "owed": [dict(r) for r in owed],
            "held": [],
            "releasable": list(releasable),
            "onDisk": on_disk}


class TheLaneCensusCanReportTheDark(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shelf-lane-census-")
        self.store = os.path.join(self.tmp, "lane_store.json")
        mod = types.ModuleType(OWNER)
        mod.STORE = self.store
        mod.ARMED = True
        sys.modules[OWNER] = mod
        self.owner = mod
        self._hist = os.environ.get("TV_HIST")

    def tearDown(self):
        # ⚠ PUT EVERYTHING BACK. REG-865: one law's fixture leaking into the next is how a suite
        # starts grading a world nobody built.
        sys.modules.pop(OWNER, None)
        if self._hist is None:
            os.environ.pop("TV_HIST", None)
        else:
            os.environ["TV_HIST"] = self._hist
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── fixture helpers ──────────────────────────────────────────────────────────────────────
    def _decl(self, **kw):
        d = {"what": "a fixture lane", "owedFrom": "tags", "owner": OWNER, "store": "STORE",
             "worksKey": "reads", "worksAs": "int", "lastKey": "lastTs", "lastWhy": "",
             "boundS": None, "armedFrom": None}
        d.update(kw)
        return d

    def _write_store(self, doc):
        with io.open(self.store, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)

    def _census(self, decl, work_, beat=None):
        """One declared lane named 'probe', driven over a given plan answer."""
        lanes = {"probe": decl}
        beats = {"probe": beat if beat is not None else SD.lane_beat("probe", decl)}
        saved = dict(SD.LANES)
        SD.LANES.clear()
        SD.LANES.update(lanes)
        try:
            return SD.lane_census(work_=work_, beats=beats)
        finally:
            SD.LANES.clear()
            SD.LANES.update(saved)

    def _row(self, *a, **kw):
        c = self._census(*a, **kw)
        self.assertEqual(len(c["rows"]), 1, "the census did not return one row per declared lane")
        return c["rows"][0]

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # THE ONE THIS WHOLE TASK IS FOR
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_a_lane_with_work_owed_and_no_unit_of_work_is_DARK(self):
        """⚠⚠ THE STATE `vaultAutoread` SAT IN FOR WEEKS. Work is owed, the lane's own durable
        store says it has completed nothing, and the verdict must be RED with no threshold
        involved — `owed > 0 and works == 0` is two measurements and a conjunction, not a number
        somebody guessed. A supervision layer that cannot produce this word has built a lamp that
        cannot report the dark."""
        # no store on disk at all: a genuine, measured "never worked"
        self.assertFalse(os.path.exists(self.store))
        row = self._row(self._decl(),
                        _plan_says(owed=[{"reel": "reel_s_1_1", "lane": "probe",
                                          "tag": "vault-owes"}], on_disk=9))
        self.assertEqual(row["state"], SD.DARK,
                         "a lane with 1 reel owed and 0 units of work ever completed reported %r. "
                         "That is the vault lane's own months-long failure rendering as health."
                         % row["state"])
        self.assertEqual(row["works"], 0, "the fixture did not actually produce a never-worked "
                                          "lane, so this law proves nothing")
        self.assertIn("0 units", row["why"],
                      "the DARK verdict does not say WHAT is dark about it: %r" % row["why"][:120])

    def test_a_lane_with_work_owed_that_HAS_worked_is_not_dark(self):
        """The other side of the same law — a green sabotage is usually the sabotage's fault, and
        a DARK that fires on everything is worth exactly as little as one that never fires."""
        self._write_store({"reads": 4, "lastTs": 1789000000000})
        row = self._row(self._decl(),
                        _plan_says(owed=[{"reel": "reel_s_1_1", "lane": "probe",
                                          "tag": "vault-owes"}], on_disk=9))
        self.assertNotEqual(row["state"], SD.DARK,
                            "a lane that has completed 4 units of work was reported DARK")

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # UNKNOWN IS A FIRST-CLASS ANSWER, IN EVERY COLUMN
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_a_plan_that_could_not_be_read_is_UNKNOWN_on_every_lane(self):
        """⚠ "CANNOT ASK" AND "NOTHING OWED" ARE OPPOSITE FACTS, and the shorter table is the
        worse lie: a failed plan must not shorten the census either, or a lane that owes an
        unmeasurable amount of work simply stops being on screen."""
        row = self._row(self._decl(),
                        {"ok": False, "why": "retention could not plan (OSError)",
                         "owed": None, "held": None, "releasable": None})
        self.assertEqual(row["state"], SD.UNKNOWN,
                         "a shelf nobody could read reported %r — an unmeasured work-list wearing "
                         "a calmer word" % row["state"])
        self.assertIsNone(row["owed"], "an unmeasurable work-list came back as a number")
        self.assertIn("could not plan", row["why"],
                      "the UNKNOWN carries no reason, which is UNKNOWN with the reason removed")

    def test_a_zero_owed_with_no_denominator_is_UNKNOWN_not_IDLE(self):
        """⚠ 0 of nothing counted is not a measurement of an empty work-list, it is an absent
        measurement. [[zero-needs-a-denominator]]"""
        self._write_store({"reads": 4, "lastTs": 1789000000000})
        row = self._row(self._decl(), _plan_says(owed=[], on_disk=None))
        self.assertEqual(row["state"], SD.UNKNOWN,
                         "0 owed out of an UNKNOWN number of reels reported %r. A clean-looking "
                         "zero with nothing to divide by is the shape this repo has shipped four "
                         "times in one session." % row["state"])

    def test_a_lane_nobody_could_ask_is_UNKNOWN_and_never_DARK(self):
        """⚠⚠ THE TWO REDS ARE DIFFERENT ACCUSATIONS. "this lane has stopped working" sends him
        to fix a lane; "nobody could read this lane's record" sends him to fix a reader. Collapsing
        the second into the first is how a supervision layer starts crying wolf."""
        row = self._row(self._decl(owner="a_module_that_is_not_loaded_anywhere"),
                        _plan_says(owed=[{"reel": "reel_s_1_1", "lane": "probe",
                                          "tag": "vault-owes"}], on_disk=9))
        self.assertEqual(row["state"], SD.UNKNOWN,
                         "a lane whose owner could not be reached reported %r" % row["state"])
        self.assertFalse(row["resolved"], "the fixture resolved an owner that does not exist")

    def test_an_unreadable_store_is_UNKNOWN_and_not_a_missing_field(self):
        """⚠ THE THIRD OUTCOME, and it must name the RIGHT failure. A store that exists and will
        not parse is not a store with a field missing — reported as the latter it sends a reader to
        add a key to a writer that is working fine, while the real fault (a torn or corrupt file)
        goes untouched. And `durable` must stay UNKNOWN: a durability nobody could measure must
        never render as 'this lane is not durable'."""
        with io.open(self.store, "w", encoding="utf-8") as fh:
            fh.write("{ this is not json")
        b = SD.lane_beat("probe", self._decl())
        self.assertIsNone(b["storeReadable"], "a corrupt store did not read as UNKNOWN")
        self.assertIsNone(b["works"], "a corrupt store produced a unit count")
        self.assertIn("could NOT be read", b["why"],
                      "an unreadable store was reported as something else entirely: %r"
                      % b["why"][:140])
        self.assertIsNone(b["durable"],
                          "durability nobody could measure came back as a verdict (%r) — an "
                          "unmeasured store is not a store known to be fragile" % b["durable"])

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # IS THE HEARTBEAT DURABLE — MEASURED, NEVER DECLARED
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_durability_is_measured_from_the_store_and_needs_BOTH_halves(self):
        """⚠⚠ THE CHRONICLE LANE'S REAL SHAPE, AND IT ALREADY FOOLED THE FIRST CUT OF THIS FILE.
        `chron_autoread.json` persists {done, reels, retired, skipped} — a durable unit COUNT and no
        clock reading anywhere, while the in-memory `lastTs` holds a VISIT id rather than a time.
        Reported as one `durable: True` that is a right measurement under a word that had stopped
        being true of the whole heartbeat. [[label-outlived-referent]]"""
        self._write_store({"reads": 7})            # a count, and no clock
        b = SD.lane_beat("probe", self._decl())
        self.assertIs(b["durableWorks"], True, "the durable unit count was not seen")
        self.assertIs(b["durableLast"], False, "a clock reading was found in a store with none")
        self.assertIs(b["durable"], False,
                      "a heartbeat whose count survives a restart and whose TIME does not was "
                      "reported fully durable. After a restart 'when did this lane last work' is "
                      "UNKNOWN, which is exactly what #60 was about.")
        self.assertIn("clock", b["durableWhy"],
                      "the partial durability carries no explanation: %r" % b["durableWhy"][:120])

    def test_a_store_with_both_halves_is_durable(self):
        """The vault lane's real shape after #60 — the sabotage's own control."""
        self._write_store({"reads": 7, "lastTs": 1789000000000})
        b = SD.lane_beat("probe", self._decl())
        self.assertIs(b["durable"], True, "a store carrying both halves was not called durable")

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # STALENESS: DECIDABLE, OR SAID TO BE UNDECIDABLE
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_a_working_lane_with_no_declared_bound_is_UNTIMED_not_FLOWING(self):
        """⚠ A TICK PERIOD IS NOT A WORK PERIOD. The vault loop wakes every few seconds and a paid
        sweep takes minutes, so grading work against the loop's sleep would report every healthy
        lane stalled. No lane declares a measured work period today — and a lane whose staleness
        cannot be decided must say so rather than being handed the green word by default.
        [[unknown-stays-unknown]] [[feedback-threshold-above-the-ceiling]]"""
        self._write_store({"reads": 4, "lastTs": 1_000_000_000_000})
        row = self._row(self._decl(boundS=None),
                        _plan_says(owed=[{"reel": "r", "lane": "probe", "tag": "vault-owes"}],
                                   on_disk=9))
        self.assertEqual(row["state"], SD.UNTIMED,
                         "a lane with work owed, a real last-worked time and NO declared work "
                         "period reported %r. Nothing measured says that is on time."
                         % row["state"])

    def test_a_bounded_lane_past_its_own_bound_is_STALLED(self):
        """STALLED must be a state something can actually reach, or the bound machinery is
        plumbing with no tap. [[plumbing-with-no-tap]]"""
        self._write_store({"reads": 4, "lastTs": 1_000_000_000_000})
        row = self._row(self._decl(boundS=60),
                        _plan_says(owed=[{"reel": "r", "lane": "probe", "tag": "vault-owes"}],
                                   on_disk=9))
        self.assertEqual(row["state"], SD.STALLED,
                         "a lane that last worked in 2001 against a 60s period reported %r"
                         % row["state"])

    def test_a_bounded_lane_inside_its_own_bound_is_FLOWING(self):
        """And the green must be reachable too, or STALLED is just an unconditional red."""
        import time as _t
        self._write_store({"reads": 4, "lastTs": int(_t.time() * 1000)})
        row = self._row(self._decl(boundS=600),
                        _plan_says(owed=[{"reel": "r", "lane": "probe", "tag": "vault-owes"}],
                                   on_disk=9))
        self.assertEqual(row["state"], SD.FLOWING,
                         "a lane that worked just now against a 600s period reported %r"
                         % row["state"])

    def test_a_disarmed_lane_with_work_owed_is_DORMANT_and_says_why(self):
        """⚠ A KNOWN REASON IS NOT AN UNKNOWN, and it is not a fault either. `_PRUNE_SAFE_TO_RUN`
        is Konyo's to arm; reporting a deliberately disarmed deleter as DARK is an alarm about a
        decision, which is how a supervision layer teaches him to ignore it. Copied straight from
        `lane_liveness.DORMANT`, including its refusal to accept a reasonless dormancy."""
        self.owner.ARMED = False
        row = self._row(self._decl(armedFrom=(OWNER, "ARMED"),
                                   dormantWhy="the prune is armed by Konyo and is not armed"),
                        _plan_says(owed=[{"reel": "r", "lane": "probe", "tag": "vault-owes"}],
                                   on_disk=9))
        self.assertEqual(row["state"], SD.DORMANT,
                         "a lane that is deliberately not acting reported %r" % row["state"])
        self.assertIn("armed by Konyo", row["why"],
                      "a DORMANT with no reason is UNKNOWN wearing a calmer word: %r"
                      % row["why"][:120])

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # EVERY LANE DECLARED — THE GATE CENSUS'S OWN DISCIPLINE
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_a_lane_owing_nothing_still_gets_a_row(self):
        """⚠⚠ THE MEASURED GAP. `owedByLane` is built by counting owed reels, so a lane owing zero
        is absent from it — his stored beat read `{"vault": 18}` and the chronicle lane, which
        exists and has a watchdog, appeared nowhere. Absent and healthy must never look the same."""
        self._write_store({"reads": 4, "lastTs": 1789000000000})
        row = self._row(self._decl(), _plan_says(owed=[], on_disk=12))
        self.assertEqual(row["state"], SD.IDLE,
                         "a lane with nothing owed reported %r" % row["state"])
        self.assertIn("12", row["why"],
                      "the IDLE verdict carries no denominator: %r. 'Nothing owed' out of an "
                      "unstated total is not a measurement." % row["why"][:120])

    def test_a_lane_the_tag_map_names_and_nobody_declared_is_reported(self):
        """⚠ A HAND-KEPT SET ROTS. Add a tag pointing at an undeclared lane and its reels are
        counted into the owed total while appearing on no row — work that belongs to nobody.
        `lane_census.supervisor_set_is_current` exists for this exact reason one level down."""
        ok, why = SD.declared_covers_the_map(owed_by={"some-tag": "a-lane-nobody-declared"},
                                             lanes=SD.LANES)
        self.assertFalse(ok, "a lane named by the tag map and declared nowhere passed unnoticed")
        self.assertIn("a-lane-nobody-declared", why,
                      "the finding does not NAME the undeclared lane: %r" % why[:140])

    def test_the_real_tag_map_is_fully_declared(self):
        """And the shipped pair must agree today, or the law above is about a hypothetical."""
        ok, why = SD.declared_covers_the_map()
        self.assertTrue(ok, why)

    def test_every_background_loop_is_either_a_shelf_lane_or_named_as_not_one(self):
        """⚠⚠ A PARTIAL CENSUS THAT DOES NOT SAY SO IS A FULL ONE THAT LIES. His console starts 12
        background loops; three own a work-list on the shelf and nine do not, and the nine are
        named in `NOT_SHELF_LANES` with the reason. Add a thirteenth loop and this goes red, which
        forces the decision — supervised here, or written down as out of scope — instead of letting
        a new lane join the console invisible to both.

        ⚠ AND THE EXCLUSION LIST ITSELF IS FALSIFIABLE: a name that no longer appears on the roster
        is a stale note whose warning has been silently absent ever since. Same rot
        `lane_census.supervisor_set_is_current` had to be taught to catch. [[label-outlived-referent]]

        ⚠ REGEX ON A DELIBERATELY NARROW BLOCK, and a block it cannot find FAILS rather than
        skipping — a skip is not a pass. [[source-reading-guard]] [[regression-guard]]"""
        import re
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        block = re.search(r"\n    roster = \[(.*?)\n    \]", src, re.S)
        self.assertIsNotNone(block, "the background-watcher roster could not be located in "
                                    "control_app.py — its shape changed, so this law is measuring "
                                    "nothing and must not report green")
        names = [n for n, _fn in re.findall(r'\("([a-z0-9-]+)",\s*([A-Za-z_]\w*)\)', block.group(1))]
        self.assertGreaterEqual(len(names), 10,
                                "only %d roster entries parsed — the reader, not the roster"
                                % len(names))
        stale = sorted(set(SD.NOT_SHELF_LANES) - set(names))
        self.assertEqual([], stale,
                         "NOT_SHELF_LANES names %r, which no longer appear on the roster. A "
                         "declaration that stopped matching stops warning, silently." % stale)
        unaccounted = sorted(set(names) - set(SD.NOT_SHELF_LANES))
        self.assertEqual(
            len(unaccounted), len(SD.LANES),
            "%d background loop(s) are neither declared shelf lanes nor listed as out of scope: "
            "%r. %d lane(s) are declared. A loop in neither list runs unwatched by this census and "
            "unexplained by it, which is the exact silence it was written to end."
            % (len(unaccounted), unaccounted, len(SD.LANES)))

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # NO SECOND PREDICATE — THE RULE THE MODULE IS NAMED AFTER
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_one_beat_asks_the_work_list_exactly_once(self):
        """⚠⚠ THE DEFECT THIS MODULE EXISTS TO AVOID, IN ITS CHEAPEST FORM. Every serious defect
        found on 2026-09-10 was two authorities answering one question. A census that builds its own
        retention plan is a SECOND read of a moving shelf inside a single beat: the two can
        disagree, and the disagreement is invisible because both came from the same function.
        Driven behaviourally, because a source law cannot see a call added through an alias."""
        calls = []

        def _counted(hist=None):
            calls.append(hist)
            return _plan_says(owed=[], releasable=[], on_disk=3)

        saved = SD.work
        SD.work = _counted
        try:
            SD.beat(hist=None, write=False)
        finally:
            SD.work = saved
        self.assertEqual(len(calls), 1,
                         "one beat asked the work-list %d times. Two reads of a moving shelf in "
                         "one beat can disagree, and nothing downstream could tell which number it "
                         "was looking at." % len(calls))

    def test_the_census_never_builds_its_own_work_list(self):
        """The injected half of the same rule: given an answer, the census must not go and get
        another one."""
        def _explode(hist=None):
            raise AssertionError("lane_census built its own work-list instead of using the one it "
                                 "was handed — that is a second predicate")

        saved = SD.work
        SD.work = _explode
        try:
            c = SD.lane_census(work_=_plan_says(owed=[], on_disk=3), beats={})
        finally:
            SD.work = saved
        self.assertTrue(c["ok"])

    def test_only_one_place_in_this_module_asks_retention(self):
        """⚠ PARSED, NOT GREPPED — a docstring in this file quotes `plan(` several times and prose
        is not code. [[source-reading-guard]]"""
        with io.open(os.path.join(HERE, "shelf_driver.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        asks = [n for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "plan"]
        self.assertEqual(len(asks), 1,
                         "%d call sites in shelf_driver.py ask reel_retention for a plan. There "
                         "must be exactly one, or 'is there work owed' has two authorities inside "
                         "the module written to have none." % len(asks))

    # ═════════════════════════════════════════════════════════════════════════════════════════
    # THE BEAT ITSELF
    # ═════════════════════════════════════════════════════════════════════════════════════════
    def test_the_beat_path_honours_a_fixture_world(self):
        """⚠⚠ IT WAS A MODULE CONSTANT, SO A GATE WROTE INTO HIS LIVE tv/. `BEAT` was computed at
        import from HERE, and `beat()` writes on every call — the same shape control_app fixed in
        `_shadow_watch_path` (v2423): an env honoured only at import is a redirect that silently
        does not take. [[feedback-fixtures-never-touch-live-data]]"""
        os.environ["TV_HIST"] = self.tmp
        p = SD._beat_path()
        self.assertIsNotNone(p, "the beat path could not be resolved inside a fixture world")
        self.assertIn(os.path.realpath(self.tmp), os.path.realpath(p),
                      "the driver's heartbeat resolved to %r while TV_HIST pointed at a fixture — "
                      "a gate run would overwrite the record his console reads" % p)

    def test_the_beat_writer_is_atomic(self):
        """⚠ PARSED, NOT GREPPED. `open(p, "w")` TRUNCATES BEFORE IT WRITES, so a crash mid-beat
        leaves an empty file that reads back as a census nobody could build. This repo has already
        emptied a 6 MB bible.html exactly that way.
        [[open-for-write-truncates-first]] [[bible-writes-must-be-atomic]]"""
        with io.open(os.path.join(HERE, "shelf_driver.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "beat"), None)
        self.assertIsNotNone(fn, "beat() is gone — nothing records that the driver looked")
        repl = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "replace"]
        self.assertTrue(repl,
                        "beat() does not os.replace — it writes the destination directly, so a "
                        "reader can see a half-written beat and a crash mid-write leaves an empty "
                        "one that looks like a census that found nothing")

    def test_the_beat_carries_every_declared_lane(self):
        """The join, end to end: what `beat()` persists must be the census, not a count of the
        lanes that happened to owe something. [[the-unjoined-end]]"""
        saved = SD.work
        SD.work = lambda hist=None: _plan_says(owed=[], releasable=[], on_disk=3)
        try:
            b = SD.beat(hist=None, write=False)
        finally:
            SD.work = saved
        self.assertIsNotNone(b.get("lanes"), "the beat carries no lane census at all")
        self.assertEqual(sorted(r["lane"] for r in b["lanes"]), sorted(SD.LANES),
                         "the beat named %r while %r lanes are declared — a lane owing nothing "
                         "fell out of the record, which is the gap this whole gate is about"
                         % (sorted(r["lane"] for r in b["lanes"]), sorted(SD.LANES)))


RED_PROOF = [
    {
        'why': 'THE ONE THIS TASK IS NAMED AFTER — disarming the DARK verdict. Work owed and zero units of work ever completed then falls through to UNTIMED, so the state the vault lane sat in for weeks with reads 0 / lastTs null renders as "staleness cannot be decided" instead of RED. Reddens test_a_lane_with_work_owed_and_no_unit_of_work_is_DARK.',
        'file': 'shelf_driver.py',
        'find': '    if not row.get("works"):',
        'replace': '    if False and not row.get("works"):',
        'matches': 1,
    },
    {
        'why': 'collapsing an UNMEASURABLE work-list into "nothing owed of 0 reels" — a retention plan that could not be built then reports every lane IDLE, which is a confident zero produced by a failed read. Reddens test_a_plan_that_could_not_be_read_is_UNKNOWN_on_every_lane.',
        'file': 'shelf_driver.py',
        'find': '        owed_all, owed_why = None, str(w.get("why") or "the shelf could not be read")\n        on_disk = None',
        'replace': '        owed_all, owed_why = [], ""\n        on_disk = 0',
        'matches': 1,
    },
    {
        'why': 'letting a 0 with no denominator read as IDLE. "0 owed of an UNKNOWN number of reels" then becomes a clean bill, which is the shape this repo shipped four times in one session. Reddens test_a_zero_owed_with_no_denominator_is_UNKNOWN_not_IDLE.',
        'file': 'shelf_driver.py',
        'find': '    if owed == 0 and on_disk is None:',
        'replace': '    if False and on_disk is None:',
        'matches': 1,
    },
    {
        'why': 'collapsing "nobody could ask this lane" into DARK. The two reds are different accusations — one sends him to fix a lane, the other to fix a reader — and an UNKNOWN dressed as a stall is how a supervision layer starts crying wolf. Reddens test_a_lane_nobody_could_ask_is_UNKNOWN_and_never_DARK.',
        'file': 'shelf_driver.py',
        'find': '    if not row.get("resolved") or row.get("works") is None:',
        'replace': '    if False:',
        'matches': 1,
    },
    {
        'why': 'reading an UNPARSEABLE store as a store with a field missing. The reason then names the wrong fault (add a key to a healthy writer) while the torn file goes untouched, and `durable` drops from UNKNOWN to a False verdict nobody measured. Reddens test_an_unreadable_store_is_UNKNOWN_and_not_a_missing_field.',
        'file': 'shelf_driver.py',
        'find': '    if readable is None:\n        out["why"] = ("this lane\'s store exists and could NOT be read',
        'replace': '    if False:\n        out["why"] = ("this lane\'s store exists and could NOT be read',
        'matches': 1,
    },
    {
        'why': 'declaring durability instead of measuring it. A heartbeat whose unit count survives a restart and whose clock reading does not is then reported fully durable — the chronicle lane\'s exact shape, and #60 one level up. Reddens test_durability_is_measured_from_the_store_and_needs_BOTH_halves.',
        'file': 'shelf_driver.py',
        'find': '    out["durable"] = bool(out["durableWorks"] and out["durableLast"])',
        'replace': '    out["durable"] = True',
        'matches': 1,
    },
    {
        'why': 'handing the green word to a lane whose staleness nobody can decide. With no lane declaring a WORK period, every working lane would read FLOWING on the strength of a bound that does not exist. Reddens test_a_working_lane_with_no_declared_bound_is_UNTIMED_not_FLOWING.',
        'file': 'shelf_driver.py',
        'find': '        return UNTIMED, ("%d reel(s) owed; this lane last worked %s ago and declares no WORK "',
        'replace': '        return FLOWING, ("%d reel(s) owed; this lane last worked %s ago and declares no WORK "',
        'matches': 1,
    },
    {
        'why': 'pinning the driver\'s heartbeat back to HERE, so TV_HIST cannot redirect it and a gate run overwrites the record his console reads. The v2423 shape: an env honoured only at import is a redirect that silently does not take. Reddens test_the_beat_path_honours_a_fixture_world.',
        'file': 'shelf_driver.py',
        'find': '        return os.path.join(_tvd._fixture_root(HERE), ".shelf_driver.json")',
        'replace': '        return os.path.join(HERE, ".shelf_driver.json")',
        'matches': 1,
    },
    {
        'why': 'writing the beat with a bare open(w), which truncates the destination BEFORE writing — a crash or a full disk mid-beat then leaves an empty file that reads back as a census that found nothing. Reddens test_the_beat_writer_is_atomic.',
        'file': 'shelf_driver.py',
        'find': '            tmp = dest + ".tmp"\n            with io.open(tmp, "w", encoding="utf-8") as fh:\n                json.dump(out, fh, indent=1)\n            os.replace(tmp, dest)',
        'replace': '            with io.open(dest, "w", encoding="utf-8") as fh:\n                json.dump(out, fh, indent=1)',
        'matches': 1,
    },
    {
        'why': 'dropping a loop from the out-of-scope list, which is how the scope note goes stale: a background loop then belongs to neither list — not supervised by this census and not explained by it — and nothing says so. Reddens test_every_background_loop_is_either_a_shelf_lane_or_named_as_not_one.',
        'file': 'shelf_driver.py',
        'find': '                   "tvd-ledger-backup", "tvd-space-warden", "tvd-version-drift",',
        'replace': '                   "tvd-space-warden", "tvd-version-drift",',
        'matches': 1,
    },
    {
        'why': 'making one beat build TWO retention plans — the second predicate this module was written to refuse, in its cheapest form. Two reads of a moving shelf inside a single beat can disagree, and nothing downstream could tell which number it was looking at. Reddens test_one_beat_asks_the_work_list_exactly_once.',
        'file': 'shelf_driver.py',
        'find': '        cen = lane_census(hist, work_=w)',
        'replace': '        cen = lane_census(hist)',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
