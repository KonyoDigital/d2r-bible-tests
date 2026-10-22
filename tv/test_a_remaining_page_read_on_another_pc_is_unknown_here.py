# -*- coding: utf-8 -*-
"""#165 (REG-2472) - A REMAINING PAGE READ ON ANOTHER PC IS UNKNOWN HERE, NOT EVIDENCE ABOUT THIS BOARD.

counter_ledger read every page in tv/remaining/ - a TRACKED dir that ships to every PC - with no provenance, and its
judges (contradicted, arithmetic, denied, owned_by_subtraction, audit) fed the chronicle calibration and the write-path
veto, where `denied` WITHHOLDS set rows. The one page there is Konyo's 2026-08-21 Remaining filter, read by eye off a
reel only his Mac ever held. Dean's eagle, 02:44: "Your board has 130 set pieces ticked. The last Remaining page (62 days
old) still listed 19 as missing..." - his board judged by another player's page.

THE RULE, decided at read time. A shipped page counts for THIS PC's judgement only when its reel is this PC's: the reel
dir is under this PC's footage root (TV_HIST or tv/frames/hist), or this PC's sweep memory (TV_CHRON_SWEPT) or reel
tombstones (reel_retention._tombstone_path) name it - every store resolved at call time. A store that cannot be read,
with no positive answer, is UNKNOWN - never "another PC's", never "this PC's"; a page with no reel cannot be attributed.
A TV_REMAINING_DIR world is that world's own. A page filmed on THIS PC goes to the per-PC gitignored dir
(tv/remaining_here/, TV_REMAINING_HERE) and needs no provenance. Every judge says WHY it has no page.
The base -> piece mapping (sets_base_index, bible.html's _SET_BASE_INDEX) is GAME DATA and still reads the shipped page
on every PC, through counter_ledger.reference() - never the per-PC loader.

Never his live stores: footage root, sweep memory, tombstones and the per-PC dir all live in this law's own scratch.
The reel is DERIVED from the tracked page, never pinned. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import counter_ledger as CL  # noqa: E402
import sets_base_index as SBI  # noqa: E402
import chronicle_resolve as _res  # noqa: E402

GIT = shutil.which("git")
#: the seams this law sets, held and restored per case
_ENV = ("TV_HIST", "TV_CHRON_SWEPT", "TV_REMAINING_DIR", "TV_REMAINING_HERE")
#: the shipped page this law is about - named so a change to it re-proves the law (heart2 keys PROOF_NEEDS)
PROOF_NEEDS = ["remaining/sets_2026-08-21.json"]


def _write(p, blob):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8") as fh:
        if isinstance(blob, str):
            fh.write(blob)
        else:
            json.dump(blob, fh)


class _Pcs(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="remaining-pc-")
        self.addCleanup(shutil.rmtree, self.d, True)
        held = {k: os.environ.pop(k, None) for k in _ENV}

        def _restore():
            for k in _ENV:
                os.environ.pop(k, None)
            for k, v in held.items():
                if v is not None:
                    os.environ[k] = v
        self.addCleanup(_restore)
        self.hist = os.path.join(self.d, "hist")
        os.makedirs(self.hist)
        os.environ["TV_HIST"] = self.hist
        self.swept = os.path.join(self.d, "chronicle_swept.json")
        os.environ["TV_CHRON_SWEPT"] = self.swept
        self.here_dir = os.path.join(self.d, "remaining_here")
        os.environ["TV_REMAINING_HERE"] = self.here_dir
        self.page = CL.reference("sets")
        self.assertIsNotNone(self.page, "PREMISE: tv/remaining ships no page, so nothing here is about it")
        self.reel = self.page.get("reel")
        self.assertTrue(self.reel, "PREMISE: the shipped page names no reel")

    def tombstones(self):
        import reel_retention as _rr
        return _rr._tombstone_path()

    def pc_a(self):
        """THIS PC swept the page's reel - the Mac's shape: footage released, the sweep memory remembers it."""
        _write(self.swept, {self.reel: {"ts": 1, "classified": 1, "pages": 1}})

    def pc_b(self):
        """THIS PC never held the page's reel: its sweep memory names only its own."""
        _write(self.swept, {"reel_s_1000000000000_1": {"ts": 1, "classified": 1, "pages": 1}})

    def old_sighting(self):
        """A sighting older than the page, so a page this PC owns denies it."""
        ms = CL._reading_ms(self.page)
        self.assertIsNotNone(ms, "PREMISE: the shipped page carries no usable time")
        return [{"frame": "f_%d.jpg" % (ms - 60000)}]


class APcThatHeldTheReelJudgesWithItsPage(_Pcs):
    def test_its_own_sweep_memory_makes_the_page_its_own(self):
        self.pc_a()
        r = CL.load("sets")
        self.assertIsNotNone(r, CL.provenance("sets")["why"])
        self.assertEqual(r["reel"], self.reel)
        name = self.page["names"][0]
        c = CL.contradicted([name])
        self.assertIs(c["ok"], False)
        self.assertEqual([h["name"] for h in c["contradicted"]], [CL._folder()(name)])
        roster = len(_res.load_set_roster() or {})
        self.assertIs(CL.arithmetic(roster - self.page["count"], roster)["ok"], True)
        dn = CL.denied({name: self.old_sighting()})
        self.assertEqual([x["name"] for x in dn["denied"]], [CL._folder()(name)],
                         "the page this PC owns no longer vetoes a row it denies")

    def test_its_footage_tree_makes_the_page_its_own(self):
        self.pc_b()
        os.makedirs(os.path.join(self.hist, self.reel))
        self.assertIsNotNone(CL.load("sets"), CL.provenance("sets")["why"])

    def test_its_tombstones_make_the_page_its_own(self):
        self.pc_b()
        _write(self.tombstones(), {"reels": [{"reel": self.reel, "session": self.reel[len("reel_"):]}]})
        self.assertIsNotNone(CL.load("sets"), CL.provenance("sets")["why"])

    def test_a_positive_answer_beats_an_unreadable_store(self):
        _write(self.swept, "{ not json")
        os.makedirs(os.path.join(self.hist, self.reel))
        self.assertIsNotNone(CL.load("sets"), CL.provenance("sets")["why"])


class APcThatNeverHeldTheReelHasNoPage(_Pcs):
    def test_load_is_none_and_every_judge_says_why(self):
        self.pc_b()
        self.assertIsNone(CL.load("sets"), "PC-B was handed another install's Remaining page")
        pv = CL.provenance("sets")
        self.assertEqual(pv["state"], "elsewhere", pv["why"])
        name = self.page["names"][0]
        c = CL.contradicted([name])
        self.assertIsNone(c["ok"])
        self.assertIsNone(c["reading"])
        a = CL.arithmetic(130, 135)
        self.assertIsNone(a["ok"])
        owned, meta = CL.owned_by_subtraction(_res.load_set_roster() or {})
        self.assertIsNone(owned)
        for say in (c["say"], a["say"], meta["why"], CL.audit({})["say"]):
            self.assertIn("never held", say, "a judge with no page for this PC did not say why: %r" % say)
            self.assertIn("UNKNOWN here", say)

    def test_the_veto_withholds_nothing(self):
        self.pc_b()
        dn = CL.denied({self.page["names"][0]: self.old_sighting()})
        self.assertIsNone(dn["ok"])
        self.assertEqual(dn["denied"], [], "another install's page withheld a row from this PC's board")
        self.assertIn("never held", dn["say"])

    def test_an_absent_store_everywhere_is_still_another_installs_page(self):
        """A fresh PC: no footage, no sweep memory, no tombstones. Absent is an honest empty, not UNKNOWN."""
        self.assertIsNone(CL.load("sets"))
        self.assertEqual(CL.provenance("sets")["state"], "elsewhere")


class AStoreThatWillNotReadIsUnknown(_Pcs):
    def test_an_unreadable_sweep_memory_is_unknown_not_another_pcs(self):
        _write(self.swept, "{ not json")
        self.assertIsNone(CL.load("sets"))
        pv = CL.provenance("sets")
        self.assertEqual(pv["state"], "unknown", pv["why"])
        self.assertIn("UNKNOWN", pv["why"])
        self.assertNotIn("never held", pv["why"], "an unreadable store was read as 'this PC never held it'")
        self.assertIn("UNKNOWN", CL.contradicted([self.page["names"][0]])["say"])

    def test_an_unreadable_tombstone_ledger_is_unknown(self):
        self.pc_b()
        _write(self.tombstones(), "[[[")
        self.assertEqual(CL.provenance("sets")["state"], "unknown")

    def test_a_page_with_no_reel_cannot_be_attributed(self):
        for reel in (None, "", "   ", "../" + str(self.reel)):
            held, why = CL._held_here(reel)
            self.assertIsNone(held, "a page with reel %r was attributed: %s" % (reel, why))


class OtherWorldsAndThisPcsOwnPages(_Pcs):
    def test_a_page_filmed_here_needs_no_provenance(self):
        self.pc_b()
        later = {"ledger": "sets", "reel": "reel_s_1999999999999_7", "readAt": "2099-01-01T00:00:00Z",
                 "rows": [{"piece": self.page["names"][0]}]}
        _write(os.path.join(self.here_dir, "sets_here.json"), later)
        r = CL.load("sets")
        self.assertIsNotNone(r, "a page this PC filmed itself was not used")
        self.assertEqual(r["reel"], later["reel"])

    def test_a_fixture_world_is_its_own(self):
        world = os.path.join(self.d, "world")
        _write(os.path.join(world, "sets_w.json"),
               {"ledger": "sets", "reel": "reel_s_1999999999999_8", "readAt": "2026-08-21T10:19:13.811000Z",
                "rows": [{"piece": self.page["names"][0]}]})
        os.environ["TV_REMAINING_DIR"] = world
        self.pc_b()
        r = CL.load("sets")
        self.assertIsNotNone(r, "a TV_REMAINING_DIR world's own page was provenance-checked")
        self.assertEqual(r["reel"], "reel_s_1999999999999_8")

    def test_the_base_index_is_game_data_and_identical_on_both_pcs(self):
        self.pc_a()
        a = SBI.build()
        self.pc_b()
        b = SBI.build()
        self.assertIsNotNone(a)
        self.assertIsNotNone(b, "sets_base_index lost the base -> piece mapping on a PC that never held the reel")
        self.assertEqual(a, b)
        self.assertEqual(b["reel"], self.reel)


@unittest.skipIf(GIT is None, "git is absent - this case is UNMEASURED, not passing")
class GitIgnoresThePerPcPages(unittest.TestCase):
    def test_the_per_pc_dir_is_ignored_and_the_shipped_one_is_not(self):
        # a linked-worktree push exports GIT_DIR into the hook; this case's throwaway repo must never see it
        _gitenv = {k: os.environ.pop(k) for k in list(os.environ) if k.startswith("GIT_")}
        self.addCleanup(os.environ.update, _gitenv)
        env = dict((k, v) for k, v in os.environ.items() if not k.startswith("GIT_"))
        d = tempfile.mkdtemp(prefix="remaining-ignore-")
        self.addCleanup(shutil.rmtree, d, True)
        subprocess.run([GIT, "init", "-q", d], check=True, env=env)
        os.makedirs(os.path.join(d, "tv"))
        for rel in (".gitignore", os.path.join("tv", ".gitignore")):
            if os.path.isfile(os.path.join(ROOT, rel)):
                shutil.copyfile(os.path.join(ROOT, rel), os.path.join(d, rel))

        def ignored(rel):
            return subprocess.run([GIT, "check-ignore", "-q", "--no-index", rel], cwd=d, env=env).returncode == 0
        self.assertTrue(ignored("tv/remaining_here/sets_2026-10-22.json"),
                        "a page one PC filmed is one `git add -A` away from judging every PC's board")
        self.assertFalse(ignored("tv/remaining/sets_2026-10-22.json"), "the SHIPPED pages must stay trackable")


class TheseAttacksMeetTheBar(unittest.TestCase):
    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": "#165 - provenance bypassed: a PC that never held the reel is judged by another install's page",
     "file": "counter_ledger.py",
     "find": "            held, why = _held_here(p.get(\"reel\"))  # PROVENANCE\n",
     "replace": "            held, why = True, \"bypassed\"  # PROVENANCE\n", "matches": 1},
    {"why": "#165 - an unreadable store is read as 'this PC never held it' instead of UNKNOWN",
     "file": "counter_ledger.py",
     "find": "    if unread:  # UNREAD-IS-UNKNOWN\n", "replace": "    if False:  # UNREAD-IS-UNKNOWN\n", "matches": 1},
    {"why": "#165 - sets_base_index switched to the per-PC loader: the base index vanishes on a PC without the reel",
     "file": "sets_base_index.py",
     "find": "    r = _cl.reference(ledger)  # REFERENCE-PAGE\n", "replace": "    r = _cl.load(ledger)  # REFERENCE-PAGE\n",
     "matches": 1},
    {"why": "#165 - the per-PC page dir's ignore line is gone: one PC's page ships to every PC again",
     "file": ".gitignore",
     "find": "/remaining_here/\n", "replace": "", "matches": 1},
    {"why": "#165 - a page with no reel is attributed to this PC",
     "file": "counter_ledger.py",
     "find": "    if not ids:  # NO-REEL\n        return None,", "replace": "    if not ids:  # NO-REEL\n        return True,",
     "matches": 1},
    {"why": "#165 - this PC's footage tree is no longer asked",
     "file": "counter_ledger.py",
     "find": "        if got is True:  # FOOTAGE-ARM\n", "replace": "        if False:  # FOOTAGE-ARM\n", "matches": 1},
    {"why": "#165 - this PC's sweep memory is no longer asked",
     "file": "counter_ledger.py",
     "find": "        if any(i in blob for i in ids):  # SWEPT-ARM\n", "replace": "        if False:  # SWEPT-ARM\n",
     "matches": 1},
    {"why": "#165 - this PC's reel tombstones are no longer asked",
     "file": "counter_ledger.py",
     "find": "            if any(_names_of(x) & set(ids) for x in rows):  # TOMBSTONE-ARM\n",
     "replace": "            if False:  # TOMBSTONE-ARM\n", "matches": 1},
    {"why": "#165 - a TV_REMAINING_DIR world is provenance-checked against stores it does not own",
     "file": "counter_ledger.py",
     "find": "    if os.environ.get(\"TV_REMAINING_DIR\"):  # WORLD-OWN\n", "replace": "    if False:  # WORLD-OWN\n",
     "matches": 1},
    {"why": "#165 - a page this PC filmed itself is not used",
     "file": "counter_ledger.py",
     "find": "            p[\"origin\"] = \"here\"  # PER-PC-DIR\n", "replace": "            p[\"origin\"] = \"elsewhere\"  # PER-PC-DIR\n",
     "matches": 1},
    {"why": "#165 - a judge with no page for this PC no longer says why",
     "file": "counter_ledger.py",
     "find": "    if pv[\"state\"] in (\"elsewhere\", \"unknown\"):  # SAY-WHY\n", "replace": "    if False:  # SAY-WHY\n",
     "matches": 1},
    {"why": "#165 - every judge reads the shipped page whoever filmed it (the leak, at its widest)",
     "file": "counter_ledger.py",
     "find": "    r = reading or load(ledger)\n", "replace": "    r = reading or reference(ledger)\n", "matches": 5},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
