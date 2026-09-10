#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A STORE MUST BE ABLE TO NAME WHAT PRODUCED IT — AND MUST NEVER INVENT A NAME IT DOES NOT HAVE.

⚠⚠ THE CENSUS, MEASURED 2026-09-10 ON THIS TREE, not inherited from a brief:

    python3 tv/verdict_provenance.py --census-only -v
    44 stores · ANSWERS 6 · PARTIAL 4 · SILENT 16 · REFERENCE 17 · UNKNOWN 1

`verdict_provenance.py` counts 43 when it ratchets, because it excludes its own baseline file from
its own census. Both numbers are right about different questions, and "37 of 43 cannot say what
produced them" is 43 minus the 6 that ANSWER — arithmetically true and three classes wide. The
ACTIONABLE half is SILENT 16 (a dated verdict with no producer) plus PARTIAL 4 (names the lane,
never the version). The REFERENCE 16 are rosters with no clock, which the census's own doctrine
excuses, and the 1 UNKNOWN is `known_frames.json`, a JSON ARRAY with nowhere to put a block.

⚠ EVERY TEST HERE POINTS ITS STORE AT A `tempfile` DIRECTORY. Nothing in this file can write into
his live `tv/`, so it measures the same thing on his Mac and on a CI runner.
[[feedback-fixtures-never-touch-live-data]]

⚠ IT DOES NOT IMPORT `control_app`. This law is about the mechanism, not the console, and pulling
the console in to test a 300-line module would make the fixture the biggest thing in the room.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import provenance as PV                                  # noqa: E402


class TheStampNamesItsWriter(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="prov-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _p(self, name="store.json"):
        return os.path.join(self.tmp, name)

    # ── 1. ADDITIVE: what exists must keep working ───────────────────────────────────────────
    def test_a_store_written_before_this_module_still_loads(self):
        """The sixteen SILENT stores must not become sixteen outages."""
        p = self._p()
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"reads": 3, "retired": {"r": 1}}))
        body, prov = PV.load_json(p)
        self.assertEqual(body, {"reads": 3, "retired": {"r": 1}},
                         "an unstamped store did not load unchanged — provenance was supposed to "
                         "be additive, and this makes every existing store a migration")
        self.assertFalse(prov.known,
                         "a store with no %s block reported KNOWN provenance" % PV.PROV_KEY)

    def test_the_block_never_reaches_a_readers_key_loop(self):
        """`payload()` returns exactly what the reader always saw.

        ⚠ The half of "additive" that is easy to forget. `chronicle_swept.json` is keyed by reel
        id; a `_prov` entry left among those keys invents a 402nd reel.
        """
        before = {"reel_a": 1, "reel_b": 2}
        doc = PV.stamp(before, by="test")
        self.assertEqual(sorted(PV.payload(doc)), ["reel_a", "reel_b"])
        self.assertEqual(len(PV.payload(doc)), len(before),
                         "the block leaked into the payload a reader iterates")

    # ── 2. ABSENT IS UNKNOWN, NEVER A NAME ───────────────────────────────────────────────────
    def test_absent_provenance_is_unknown_and_carries_no_name(self):
        """The requirement stated as a measurement, not a promise.

        ⚠ Three separate assertions because there are three ways to fail it: claiming to know,
        carrying a name-shaped string, and printing a sentence that READS like an attribution.
        """
        prov = PV.read({"reads": 3})
        self.assertFalse(prov.known, "a store with no block reported that it knows its producer")
        self.assertIsNone(prov.by,
                          "the UNKNOWN answer carried a writer name (%r) — absent provenance was "
                          "turned into an attribution, which is the exact defect this module "
                          "exists to refuse" % (prov.by,))
        said = prov.describe().lower()
        self.assertIn("unknown", said)
        for word in ("by unknown", "by nobody", "by someone", "unknown writer"):
            self.assertNotIn(word, said,
                             "the UNKNOWN sentence reads as an attribution: %r" % prov.describe())

    def test_a_placeholder_writer_is_refused(self):
        for bad in ("unknown", "UNKNOWN", "", "  ", "n/a", "none", "?"):
            with self.assertRaises(PV.CannotStamp,
                                   msg="by=%r was accepted as a writer name" % bad):
                PV.stamp({"a": 1}, by=bad)

    def test_a_malformed_block_is_its_own_answer(self):
        """A broken writer must not hide inside the legitimate backlog."""
        absent = PV.read({"a": 1})
        broken = PV.read({PV.PROV_KEY: "written by me", "a": 1})
        noname = PV.read({PV.PROV_KEY: {"ver": "v2904", "at": 1789000000000}, "a": 1})
        for prov in (broken, noname):
            self.assertFalse(prov.known)
            self.assertIsNone(prov.by)
        self.assertNotEqual(absent.why, broken.why,
                            "a malformed block and an absent one gave the identical reason, so a "
                            "writer emitting garbage looks like a store nobody has got to yet")

    # ── 3. A VERSION THAT CANNOT BE ESTABLISHED SAYS SO ──────────────────────────────────────
    def test_an_unestablished_version_is_partial_not_answers(self):
        doc = PV.stamp({"a": 1}, by="test", ver=None)
        blk = doc[PV.PROV_KEY]
        self.assertNotIn("ver", blk,
                         "the block carries a `ver` key with nothing behind it (%r) — a key-presence "
                         "check anywhere downstream would read that as a version"
                         % (blk.get("ver"),))
        self.assertIn("verUnknown", blk, "nothing in the block says WHY there is no version")
        self.assertEqual(PV.classify(doc), "PARTIAL",
                         "a block naming WHO but not WHAT VERSION graded as ANSWERS")
        self.assertEqual(PV.classify(PV.stamp({"a": 1}, by="test", ver="v2904")), "ANSWERS")

    def test_a_placeholder_version_is_refused(self):
        with self.assertRaises(PV.CannotStamp):
            PV.stamp({"a": 1}, by="test", ver="unknown")

    def test_classify_says_nothing_about_a_row_it_did_not_write(self):
        """`None` means "fall through" — the census patch can never make a store worse."""
        self.assertIsNone(PV.classify({"agentVer": "v1", "ts": 1}))
        self.assertIsNone(PV.classify({}))

    # ── 4. THE STAMP RIDES THE SAME os.replace ───────────────────────────────────────────────
    def test_save_json_performs_exactly_one_replace(self):
        p, seen = self._p(), []
        _real = os.replace

        def _counting(a, b, *rest, **kw):
            seen.append(b)
            return _real(a, b, *rest, **kw)

        os.replace = _counting
        try:
            PV.save_json(p, {"a": 1}, by="test", ver="v2904")
        finally:
            os.replace = _real
        self.assertEqual(len(seen), 1,
                         "the store was replaced %d time(s). More than one means there is an "
                         "instant where the file is live and unattributed — the window this "
                         "module exists to close" % len(seen))

    def test_a_concurrent_reader_never_sees_the_store_without_its_block(self):
        """v2712's measurement, aimed at provenance instead of at torn bytes.

        ⚠⚠ THE DENOMINATOR IS ASSERTED, NOT JUST THE ZERO. A reader thread that never ran also
        reports "0 unstamped reads", and that zero is UNKNOWN rather than clean. So the count of
        reads that actually parsed is printed and floored. [[zero-needs-a-denominator]]
        """
        p, stop = self._p(), []
        reads, parsed, unstamped = [0], [0], []

        def _reader():
            while not stop:
                reads[0] += 1
                try:
                    with io.open(p, encoding="utf-8") as fh:
                        blob = json.load(fh)
                except Exception:
                    continue          # absent or mid-flight — a TORN read, not a provenance gap
                parsed[0] += 1
                if PV.PROV_KEY not in blob:
                    unstamped.append(dict(blob))

        t = threading.Thread(target=_reader)
        t.daemon = True
        t.start()
        try:
            for i in range(200):
                PV.save_json(p, {"n": i, "pad": "x" * 4000}, by="test", ver="v2904")
        finally:
            stop.append(1)
            t.join(timeout=10)

        print("\n    concurrent reader: %d reads, %d parsed, %d parsed-but-unstamped"
              % (reads[0], parsed[0], len(unstamped)))
        self.assertGreater(parsed[0], 20,
                           "only %d read(s) ever parsed — the reader barely ran, so a zero here "
                           "would be UNKNOWN and not clean" % parsed[0])
        self.assertEqual(unstamped, [],
                         "%d read(s) saw a complete, parseable store with NO %s block. The stamp "
                         "is not riding the same replace as the content"
                         % (len(unstamped), PV.PROV_KEY))

    # ── 5. THE SHAPES IT REFUSES ─────────────────────────────────────────────────────────────
    def test_a_list_shaped_store_is_refused_by_name(self):
        """`known_frames.json` — the 1 UNKNOWN in the census, and it stays UNKNOWN."""
        with self.assertRaises(PV.CannotStamp) as cm:
            PV.stamp([1, 2, 3], by="test")
        said = str(cm.exception).lower()
        self.assertIn("array", said,
                      "a JSON array was refused for the wrong reason: %r. Wrapping it in an object "
                      "would be a migration disguised as a stamp" % str(cm.exception))

    def test_epoch_seconds_are_refused(self):
        """A 1000x unit error still parses as a valid time, and dates every row to 1970."""
        with self.assertRaises(PV.CannotStamp):
            PV.stamp({"a": 1}, by="test", ver="v2904", at=1789067205)
        self.assertEqual(PV.stamp({"a": 1}, by="test", ver="v2904",
                                  at=1789067205463)[PV.PROV_KEY]["at"], 1789067205463)

    # ── 6. THE STAMP ITSELF ──────────────────────────────────────────────────────────────────
    def test_stamping_does_not_mutate_the_callers_payload(self):
        before = {"a": 1}
        PV.stamp(before, by="test", ver="v2904")
        self.assertEqual(before, {"a": 1},
                         "stamp() mutated the dict it was handed — a writer that saves the same "
                         "payload twice would carry the first save's timestamp forever")

    def test_the_block_is_the_first_key(self):
        """Not cosmetic: `verdict_provenance._sample_row` samples `list(blob)[:25]`.

        A block that lands as a wide store's fortieth key is one the census never looks at, and
        the join would be silently dead on exactly the biggest stores. [[the-unjoined-end]]
        """
        wide = dict(("k%03d" % i, i) for i in range(60))
        doc = PV.stamp(wide, by="test", ver="v2904")
        self.assertEqual(list(doc)[0], PV.PROV_KEY,
                         "the block is key #%d of %d — outside the census's 25-key sample window"
                         % (list(doc).index(PV.PROV_KEY) + 1, len(doc)))

    def test_re_stamping_replaces_rather_than_accumulates(self):
        once = PV.stamp({"a": 1}, by="first", ver="v1")
        twice = PV.stamp(once, by="second", ver="v2")
        self.assertEqual(PV.read(twice).by, "second")
        self.assertEqual(list(twice).count(PV.PROV_KEY), 1)

    def test_append_jsonl_stamps_before_it_writes(self):
        p = self._p("rows.jsonl")
        PV.append_jsonl(p, {"n": 1}, by="test", ver="v2904")
        PV.append_jsonl(p, {"n": 2}, by="test", ver="v2904")
        with io.open(p, encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertTrue(PV.read(r).known, "a jsonl row landed without its block")
        self.assertTrue(PV.read_file(p).known)

    def test_read_file_separates_absent_from_unparseable(self):
        missing = PV.read_file(self._p("nope.json"))
        bad = self._p("bad.json")
        with io.open(bad, "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self.assertFalse(missing.known)
        self.assertFalse(PV.read_file(bad).known)
        self.assertNotEqual(missing.why, PV.read_file(bad).why,
                            "a missing store and a corrupt one gave the same reason")


class TheJoinToTheCensus(unittest.TestCase):
    """Does stamping a store actually move it in `verdict_provenance.py`?

    ⚠⚠ THIS IS THE HALF THAT IS USUALLY SKIPPED. A mechanism can be perfect and joined to nothing:
    two halves built correctly that never meet. [[the-unjoined-end]] [[plumbing-with-no-tap]]
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="prov-census-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _grade(self, name):
        import verdict_provenance as VP
        rep = VP.census(self.tmp)
        for r in rep["rows"]:
            if r["store"] == name:
                return r["state"]
        return None

    def test_a_stamped_json_store_reads_as_ANSWERS_in_the_census(self):
        p = os.path.join(self.tmp, "made_up_store.json")
        PV.save_json(p, {"verdict": "EMPTY", "ts": 1789000000000}, by="retro_triage", ver="v2904")
        self.assertEqual(self._grade("made_up_store.json"), "ANSWERS",
                         "a store stamped by this module still cannot say what produced it as far "
                         "as the census is concerned — the mechanism and the measurement do not "
                         "meet")

    def test_a_stamped_store_with_no_version_reads_as_PARTIAL(self):
        p = os.path.join(self.tmp, "no_version.json")
        PV.save_json(p, {"verdict": "EMPTY", "ts": 1789000000000}, by="retro_triage", ver=None)
        self.assertEqual(self._grade("no_version.json"), "PARTIAL",
                         "a block naming the writer but no version graded as something other than "
                         "PARTIAL — the two answers were collapsed into one")

    def test_classify_is_the_definition_and_does_not_depend_on_the_stores_shape(self):
        """⚠⚠ THE JSONL HALF OF THE JOIN IS NOT LANDED, AND THIS SAYS SO OUT LOUD.

        `classify()` grades a stamped row the same whether it came from a `.json` object or a
        `.jsonl` line, because the block is identical. The CENSUS does not, today: `_sample_row`
        merges an object store's sub-dicts (so the block's inner `ver` is seen, which is why the
        two tests above pass WITHOUT any change to `verdict_provenance.py`) and does no merging at
        all for `.jsonl`, where it reads the last line's top-level keys and sees only `_prov`.

        So the object half of the join works BY ACCIDENT and the jsonl half does not work at all.
        This test pins the part that is under this module's control — one definition, shape
        independent — and PRINTS the census's current grade for both rather than asserting it, so
        applying the three-line `_verdict` patch does not turn this law red. [[copy-drift]]
        """
        row = PV.stamp({"n": 1}, by="ui_faults", ver="v2904")
        self.assertEqual(PV.classify(row), "ANSWERS")

        pj = os.path.join(self.tmp, "shape_a.json")
        pl = os.path.join(self.tmp, "shape_b.jsonl")
        PV.save_json(pj, {"n": 1, "at": 1789000000000}, by="ui_faults", ver="v2904")
        PV.append_jsonl(pl, {"n": 1, "at": 1789000000000}, by="ui_faults", ver="v2904")
        with io.open(pj, encoding="utf-8") as fh:
            obj_row = json.load(fh)
        with io.open(pl, encoding="utf-8") as fh:
            line_row = json.loads([l for l in fh if l.strip()][-1])
        print("\n    census today, unpatched:  shape_a.json -> %s   shape_b.jsonl -> %s"
              % (self._grade("shape_a.json"), self._grade("shape_b.jsonl")))
        print("    classify() (this module): shape_a.json -> %s   shape_b.jsonl -> %s"
              % (PV.classify(obj_row), PV.classify(line_row)))
        self.assertEqual(PV.classify(obj_row), PV.classify(line_row),
                         "one definition of a provenance block graded two shapes differently")


class TheRedProofsAreWellFormed(unittest.TestCase):
    """⚠ SHAPE ONLY, AND DELIBERATELY NOT MATCH COUNTS.

    A test asserting `provenance.py.count(find) == matches` would go RED under EVERY tamper — so
    every red-proof would be reported PROVEN by this one meta-test, whether or not its own sabotage
    changed any behaviour. That is a green that lies with the sign flipped, and it would make the
    whole block worthless. The counts are verified out of band and printed in the hand-back.
    [[sabotage-is-usually-the-wrong-one]] [[regression-guard]]
    """

    def test_every_declaration_is_complete(self):
        self.assertTrue(RED_PROOF, "no red-proof declared at all")
        for i, pr in enumerate(RED_PROOF):
            for k in ("why", "file", "find", "replace", "matches"):
                self.assertIn(k, pr, "RED_PROOF[%d] is missing %r" % (i, k))
            self.assertNotEqual(pr["find"], pr["replace"],
                                "RED_PROOF[%d] tampers nothing" % i)
            self.assertGreaterEqual(int(pr["matches"]), 1)
            self.assertGreater(len(pr["why"]), 40,
                               "RED_PROOF[%d]'s why is too short to say what breaks" % i)


RED_PROOF = [
    {
        'why': "THE UNKNOWN PATH GOES RED — the requirement stated as a defect. A store with no "
               "block would report a KNOWN producer called \"unknown\", so a file nobody can "
               "attribute renders identically to one written by a module of that name. This is "
               "the exact shape of the defect this repo keeps shipping: a word standing where a "
               "measurement belongs. Caught by "
               "test_absent_provenance_is_unknown_and_carries_no_name.",
        'file': 'provenance.py',
        'find': '        return _unknown(UNKNOWN_WHY_ABSENT)',
        'replace': '        return Prov(True, by="unknown", why=UNKNOWN_WHY_ABSENT)',
        'matches': 1,
    },
    {
        'why': "accepting a placeholder as a writer name: by=\"unknown\" is then a legal stamp, "
               "and the store ANSWERS the census with a word that answers nothing. Absent "
               "provenance must be refused at the writer, not laundered into a name. Caught by "
               "test_a_placeholder_writer_is_refused.",
        'file': 'provenance.py',
        'find': '    if b.lower() in _PLACEHOLDERS:',
        'replace': '    if False:',
        'matches': 1,
    },
    {
        'why': "writing the content FIRST and stamping in a second replace — the store is live and "
               "unattributed for the width of one write, and every test that reads the settled "
               "file passes. This is v2712's torn-read window with provenance as the thing that "
               "goes missing. Caught by test_save_json_performs_exactly_one_replace and by "
               "test_a_concurrent_reader_never_sees_the_store_without_its_block.",
        'file': 'provenance.py',
        'find': "    doc = stamp(obj, by, ver=ver, at=at, extra=extra)\n"
                "    _atomic_write(path, json.dumps(doc, indent=indent, sort_keys=sort_keys, ensure_ascii=False))",
        'replace': "    _atomic_write(path, json.dumps(obj, indent=indent, sort_keys=sort_keys, ensure_ascii=False))\n"
                   "    doc = stamp(obj, by, ver=ver, at=at, extra=extra)\n"
                   "    _atomic_write(path, json.dumps(doc, indent=indent, sort_keys=sort_keys, ensure_ascii=False))",
        'matches': 1,
    },
    {
        'why': "recording `ver: null` instead of `verUnknown: <why>`. The key is then PRESENT with "
               "nothing behind it, so any downstream key-presence check reads it as a version and "
               "the store's grade climbs from PARTIAL to ANSWERS on a null. Caught by "
               "test_an_unestablished_version_is_partial_not_answers.",
        'file': 'provenance.py',
        'find': '        block["verUnknown"] = vwhy or "the version could not be established"',
        'replace': '        block["ver"] = None',
        'matches': 1,
    },
    {
        'why': "letting the block leak into payload(): every reader that iterates a store's keys "
               "gains a phantom entry — on chronicle_swept.json, keyed by reel id, that is a 402nd "
               "reel that does not exist. Additive has to mean invisible to existing readers, not "
               "merely parseable. Caught by test_the_block_never_reaches_a_readers_key_loop.",
        'file': 'provenance.py',
        'find': '    return dict((k, v) for k, v in obj.items() if k != PROV_KEY)',
        'replace': '    return dict(obj)',
        'matches': 1,
    },
    {
        'why': "appending the block LAST instead of first. JSON key order is insertion order and "
               "verdict_provenance._sample_row samples list(blob)[:25], so on any store wider than "
               "25 keys the block lands outside the sample window and the census never sees it — "
               "the mechanism works, the measurement cannot see it, and nothing anywhere fails. "
               "Caught by test_the_block_is_the_first_key.",
        'file': 'provenance.py',
        'find': '    out = {PROV_KEY: block}\n'
                '    for k, val in payload.items():\n'
                '        if k == PROV_KEY:\n'
                '            continue          # re-stamping REPLACES; a store carries one producer, the last one\n'
                '        out[k] = val\n'
                '    return out',
        'replace': '    out = {}\n'
                   '    for k, val in payload.items():\n'
                   '        if k == PROV_KEY:\n'
                   '            continue          # re-stamping REPLACES; a store carries one producer, the last one\n'
                   '        out[k] = val\n'
                   '    out[PROV_KEY] = block\n'
                   '    return out',
        'matches': 1,
    },
    {
        'why': "accepting epoch SECONDS as `at`. It parses, it is a plausible integer, and it "
               "dates every stamped row to January 1970 — a 1000x unit collision this tree has "
               "already been bitten by once. Caught by test_epoch_seconds_are_refused.",
        'file': 'provenance.py',
        'find': '    if at < _MS_FLOOR:',
        'replace': '    if False:',
        'matches': 1,
    },
    {
        'why': "silently accepting a JSON ARRAY store. known_frames.json is the census's single "
               "UNKNOWN precisely because it has no key to hang a block on; wrapping it would "
               "change the shape its readers parse — a migration disguised as a stamp. Caught by "
               "test_a_list_shaped_store_is_refused_by_name, which asserts the refusal names the "
               "array shape rather than failing for some other reason.",
        'file': 'provenance.py',
        'find': '    if isinstance(payload, list):',
        'replace': '    if isinstance(payload, tuple):',
        'matches': 1,
    },
    {
        'why': "grading every block ANSWERS regardless of whether it carries a version. PARTIAL "
               "and ANSWERS are different answers — \"names the writer\" and \"names the build\" — "
               "and collapsing them is the same mistake the census itself carved a comment about. "
               "A store that can name only its lane would then read as fully attributable. Caught "
               "by test_an_unestablished_version_is_partial_not_answers and by "
               "test_a_stamped_store_with_no_version_reads_as_PARTIAL.",
        'file': 'provenance.py',
        'find': '    return "ANSWERS" if p.ver else "PARTIAL"',
        'replace': '    return "ANSWERS"',
        'matches': 1,
    },
    {
        'why': "letting stamp() mutate the dict it was handed. A writer that builds a payload once "
               "and saves it on every tick then carries the FIRST save's timestamp forever, so the "
               "store's `at` stops meaning \"when this was written\" while still looking like a "
               "live clock — a label that outlived its referent. Caught by "
               "test_stamping_does_not_mutate_the_callers_payload.",
        'file': 'provenance.py',
        'find': '    out = {PROV_KEY: block}\n',
        'replace': '    payload[PROV_KEY] = block\n    out = payload\n',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
