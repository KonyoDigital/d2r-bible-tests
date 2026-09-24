# -*- coding: utf-8 -*-
"""#197 — A REUSED FILE NAME IS NOT ONE PICTURE, AND THE TWO EYES MUST HAVE SEEN THE SAME ONE.

Raised by the cross-family eye on the SHIPPED v3451 bytes. The shadow log stored only
`os.path.basename(image)`, and the reducer grouped its per-FRAME figures by that name. For a history
frame that is fine — `f_<epoch-ms>.jpg` is written once. For `read.jpg` it is not: tv_diablo.py
writes FRAMES/read.jpg at five sites and rewrites it on every read. MEASURED on his store:

    both-answered rows 1,596 · distinct names 165 · name shapes f_N.jpg 161 · read_N_N.jpg 3 · read.jpg 1
    read.jpg alone: 131 rows, published as ONE "mixed" frame — a frame disagreeing with itself —
    when it is 131 different pictures written to one path

And the same fact hides a worse one. The shadow read runs in a THREAD started after Claude's read
returns, so by the time Grok opens `read.jpg` the capture loop may already have written the next
frame over it. The two lanes may not have been shown the same picture at all, and nothing recorded
whether they were.

So the WRITER now stores what identifies the picture: `picture` (a content hash taken by the caller
right after Claude's read, before the thread starts) and `picture_after` (taken after Grok's read).
The reducer keys frames by that identity, falls back to the name only where the name IS an identity,
and places everything else in NO frame — counted out loud, never guessed into one. The doctor row
says how many reads that is. [[heart-first]] [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd       # noqa: E402
import g5_grok_eyes as G          # noqa: E402
import g5_shadow_reducer as R     # noqa: E402

TV_DIABLO = os.path.join(HERE, "tv_diablo.py")


def _row(ts, image, agree, **extra):
    r = {"ts": "2026-01-01 00:00:%02d" % ts, "image": image,
         "claude_names": ["Shako"], "grok_names": ["Shako"] if agree else ["Occulus"],
         "claude_scene": "stash", "grok_scene": "stash"}
    r.update(extra)
    return r


def _names(rows):
    return R.reduce_rows(rows)["fields"]["names"]


class AReusedNameIsNotOnePicture(unittest.TestCase):

    def test_the_premise_the_fixture_names_are_the_two_shapes_his_store_has(self):
        """If the frame-name rule stopped matching his real history names, every case below would
        be judging a rule nobody applies. [[a-probe-licenses-only-what-it-tested]]"""
        self.assertIsNotNone(R.frame_key(_row(1, "f_1788192823779.jpg", True)),
                             "a real history-frame name is no longer read as a frame")
        self.assertIsNone(R.frame_key(_row(1, "read.jpg", True)),
                          "the scratch name read.jpg is being read as a frame")
        self.assertIsNone(R.frame_key(_row(1, "read_0_21.jpg", True)),
                          "a per-reader scratch name is being read as a frame")

    def test_a_scratch_name_is_placed_in_no_frame_and_counted(self):
        """The measured defect: read.jpg giving both verdicts was ONE mixed frame."""
        rows = [_row(i, "read.jpg", i % 2 == 0) for i in range(6)]
        n = _names(rows)
        self.assertEqual(n["frames_mixed"]["n"], 0,
                         "read.jpg was published as a frame changing its mind — it is six pictures")
        self.assertEqual(n["frames_both"], 0)
        self.assertEqual(n["frames_unattributed_rows"], 6,
                         "the rows no frame could hold were dropped instead of counted")
        self.assertEqual(n["frames_unattributed_names"], [{"name": "read.jpg", "rows": 6}])
        self.assertEqual(n["both"], 6, "the ROW figures must still count every both-answered read")

    def test_BASELINE_a_real_frame_that_changes_its_mind_is_still_mixed(self):
        """⚠ The fix must not hide the real finding: one history frame, two verdicts, IS mixed."""
        rows = [_row(i, "f_1788192823779.jpg", i % 2 == 0) for i in range(4)]
        n = _names(rows)
        self.assertEqual((n["frames_both"], n["frames_mixed"]["n"]), (1, 1),
                         "a history frame read both ways is no longer reported as mixed")
        self.assertEqual(n["frames_unattributed_rows"], 0)

    def test_a_picture_identity_separates_what_one_name_hid(self):
        rows = [_row(1, "read.jpg", True, picture="aaaa", picture_after="aaaa"),
                _row(2, "read.jpg", True, picture="aaaa", picture_after="aaaa"),
                _row(3, "read.jpg", False, picture="bbbb", picture_after="bbbb")]
        n = _names(rows)
        self.assertEqual(n["frames_both"], 2, "two pictures under one name are still one frame")
        self.assertEqual((n["frames_agree"]["n"], n["frames_disagree"]["n"],
                          n["frames_mixed"]["n"]), (1, 1, 0))
        self.assertEqual(n["frames_unattributed_rows"], 0)

    def test_a_picture_that_changed_between_the_two_reads_is_not_a_comparison(self):
        rows = [_row(1, "f_1788192823779.jpg", False, picture="aaaa", picture_after="bbbb"),
                _row(2, "f_1788192823779.jpg", True, picture="aaaa", picture_after="aaaa")]
        n = _names(rows)
        self.assertEqual(n["rows_picture_moved"]["n"], 1,
                         "a row whose two lanes saw two pictures was not counted as such")
        self.assertEqual(n["rows_picture_moved"]["d"], 2)
        self.assertEqual((n["frames_both"], n["frames_agree"]["n"], n["frames_mixed"]["n"]),
                         (1, 1, 0),
                         "the two-picture row was folded into a frame — it made that frame read "
                         "MIXED when the lanes never disagreed about one picture")
        self.assertEqual(n["frames_unattributed_rows"], 1)

    def test_no_identity_anywhere_is_UNKNOWN_not_zero_moved(self):
        n = _names([_row(1, "f_1788192823779.jpg", True)])
        self.assertIsNone(n["rows_picture_moved"],
                          "no row carries both identities, and the report claimed a measured %r"
                          % (n["rows_picture_moved"],))

    def test_the_caveat_is_derived_from_what_the_rows_carry(self):
        legacy = R.reduce_rows([_row(1, "read.jpg", True), _row(2, "f_1788192823779.jpg", True)])
        self.assertTrue(any("no picture identity" in c for c in legacy["caveats"]),
                        "legacy rows carry no identity and the report did not say so: %r"
                        % legacy["caveats"])
        self.assertTrue(any("read.jpg" in c for c in legacy["caveats"]),
                        "the caveat does not name the scratch name it left out")
        full = R.reduce_rows([_row(1, "read.jpg", True, picture="a", picture_after="a")])
        self.assertFalse(any("no picture identity" in c for c in full["caveats"]),
                         "the caveat is hardcoded — it survived rows that carry an identity")


    def test_a_known_picture_with_an_UNKNOWN_after_is_never_guessed_into_a_frame(self):
        """v3483 — the eye on v3479, finding [3]."""
        rows = [_row(1, "f_1788192823779.jpg", True, picture="aaaa", picture_after="aaaa"),
                _row(2, "f_1788192823779.jpg", False, picture="aaaa", picture_after=None)]
        n = _names(rows)
        self.assertEqual((n["frames_both"], n["frames_agree"]["n"], n["frames_mixed"]["n"]),
                         (1, 1, 0),
                         "the row whose shown picture is unknown was keyed by the before-picture and "
                         "made a frame read MIXED")
        self.assertEqual(n["frames_unattributed_why"], {R.WHY_UNKNOWN: 1})

    def test_each_reason_is_counted_apart_and_the_caveat_counts_only_scratch(self):
        """v3483 — the eye on v3479, finding [2]: three populations under one number."""
        rows = [_row(1, "read.jpg", True),
                _row(2, "f_1788192823779.jpg", False, picture="aaaa", picture_after="bbbb"),
                _row(3, "f_1788192823780.jpg", False, picture="cccc")]
        rep = R.reduce_rows(rows)
        n = rep["fields"]["names"]
        self.assertEqual(n["frames_unattributed_why"],
                         {R.WHY_SCRATCH: 1, R.WHY_CHANGED: 1, R.WHY_UNKNOWN: 1})
        self.assertEqual(n["frames_unattributed_names"], [{"name": "read.jpg", "rows": 1}],
                         "the by-name list must hold only the rows placed out BECAUSE of their name")
        cav = [c for c in rep["caveats"] if "no picture identity" in c]
        self.assertTrue(cav and "1 row(s) under reused scratch names" in cav[0],
                        "the caveat printed a different population's count: %r" % cav)

class TheWriterStoresThePicture(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="reused_name_law.")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.log = os.path.join(self.tmp, "shadow.jsonl")
        self.img = os.path.join(self.tmp, "read.jpg")
        _real = G._SHADOW_LOG
        G._SHADOW_LOG = self.log          # never his store [[feedback-fixtures-never-touch-live-data]]
        self.addCleanup(setattr, G, "_SHADOW_LOG", _real)

    def _write(self, data):
        with io.open(self.img, "wb") as fh:
            fh.write(data)

    def _rows(self):
        with io.open(self.log, encoding="utf-8") as fh:
            return [json.loads(ln) for ln in fh if ln.strip()]

    def test_a_snapshot_survives_the_capture_loop_rewriting_the_original(self):
        """⚠⚠ v3483 — the eye on v3479, finding [0]: the two hashes bracketed a WINDOW, not the
        picture Grok read. Driven: snapshot, then rewrite the ORIGINAL exactly as the capture loop
        rewrites read.jpg mid-read — the row must still name ONE picture, because Grok was shown
        the private copy."""
        self._write(b"the picture claude read")
        snap, pic = G.snapshot_picture(self.img)
        self.addCleanup(lambda: os.path.exists(snap or "") and os.remove(snap))
        self.assertTrue(snap and pic, "the snapshot could not be made of a readable file")
        self.assertNotEqual(os.path.abspath(snap), os.path.abspath(self.img))
        self.assertEqual(pic, G.picture_id(snap), "the id is not the snapshot's own bytes")
        self._write(b"the NEXT frame, written over read.jpg while grok was reading")
        G.g5_shadow_log({"names": ["Shako"]}, {"names": ["Occulus"]}, self.img, picture=pic,
                        shown=snap)
        r = self._rows()[0]
        self.assertEqual(r["image"], "read.jpg", "the row lost the name of the picture it is about")
        self.assertEqual(r["picture"], r["picture_after"],
                         "the original was rewritten and the row claims the eyes saw two pictures — "
                         "the snapshot was not what grok was shown")
        self.assertEqual(R.frame_key(r), ("picture", pic))

    def test_a_snapshot_that_CHANGED_is_counted_as_moved(self):
        """The one way the pair can still differ: the shown file itself changed. Counted, never
        folded into a frame."""
        self._write(b"picture one")
        snap, pic = G.snapshot_picture(self.img)
        self.addCleanup(lambda: os.path.exists(snap or "") and os.remove(snap))
        with io.open(snap, "wb") as fh:
            fh.write(b"something else entirely")
        G.g5_shadow_log({"names": ["Shako"]}, {"names": ["Occulus"]}, self.img, picture=pic,
                        shown=snap)
        rows = self._rows()
        self.assertNotEqual(rows[0]["picture"], rows[0]["picture_after"])
        n = R.reduce_rows(rows)["fields"]["names"]
        self.assertEqual(n["rows_picture_moved"]["n"], 1)
        self.assertEqual(n["frames_unattributed_why"], {R.WHY_CHANGED: 1})

    def test_no_snapshot_means_what_grok_saw_is_UNKNOWN(self):
        """⚠ v3483 — without a snapshot there is NO after-id: re-hashing the live file at log time
        measured a window, not what grok saw."""
        self._write(b"the only picture")
        G.g5_shadow_log({"names": ["Shako"]}, {"names": ["Shako"]}, self.img,
                        picture=G.picture_id(self.img))
        r = self._rows()[0]
        self.assertIsNone(r["picture_after"], "an after-id was made up without a snapshot")
        self.assertEqual(R.frame_key_why(r), (None, R.WHY_UNKNOWN))

    def test_an_unreadable_picture_is_None_never_a_match(self):
        self.assertIsNone(G.picture_id(os.path.join(self.tmp, "absent.jpg")))

    def test_the_reducer_reads_only_keys_the_writer_writes(self):
        """A join law: the reducer keys on picture/picture_after, so the writer must write both.
        Read from the writer's record literal with ast, never by importing. [[the-unjoined-end]]"""
        with io.open(os.path.join(HERE, "g5_grok_eyes.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "g5_shadow_log"), None)
        self.assertIsNotNone(fn, "g5_shadow_log() is gone from the writer")
        keys = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict) and any(
                    isinstance(t, ast.Name) and t.id == "rec" for t in node.targets):
                keys |= {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
        self.assertIn("image", keys, "premise: the writer's record literal was not found")
        for k in ("picture", "picture_after"):
            self.assertIn(k, keys, "the reducer keys on %r and the writer does not write it" % k)


class BothCallersNameThePictureBeforeTheThread(unittest.TestCase):
    """⚠ The hash has to be taken BEFORE the shadow thread starts. Taken inside the thread it races
    the next write to the scratch file — the very race it exists to record."""

    def _jobs(self):
        with io.open(TV_DIABLO, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        def _logs(n):
            return [c for c in ast.walk(n) if isinstance(c, ast.Call)
                    and getattr(c.func, "attr", "") == "g5_shadow_log"]

        # the INNERMOST defs that call the writer — the thread bodies, not the read functions
        # that enclose them
        jobs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and _logs(node):
                inner = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n is not node]
                if not any(_logs(i) for i in inner):
                    jobs.append((node, _logs(node)))
        return jobs

    def test_every_caller_hands_over_a_picture_taken_outside_the_thread(self):
        jobs = self._jobs()
        self.assertEqual(len(jobs), 2,
                         "expected the two shadow jobs (warm + one-shot); found %d — the callers "
                         "moved and this law is judging nothing" % len(jobs))
        for fn, calls in jobs:
            for c in calls:
                kw = {k.arg: k.value for k in c.keywords}
                self.assertIn("picture", kw, "%s calls g5_shadow_log without a picture" % fn.name)
                self.assertTrue(isinstance(kw["picture"], ast.Name),
                                "%s passes a computed picture — it must be the one taken before "
                                "the thread" % fn.name)
                bound = [a.arg for a in fn.args.args]
                self.assertIn(kw["picture"].id, bound,
                              "%s's picture is not bound as a default argument, so it is read "
                              "when the thread RUNS rather than when it was started" % fn.name)
            hashed_inside = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
                             and getattr(c.func, "attr", "") in ("picture_id", "snapshot_picture")]
            self.assertEqual(hashed_inside, [],
                             "%s hashes or snapshots the picture INSIDE the thread — after the race"
                             % fn.name)

    def test_every_caller_shows_grok_the_SNAPSHOT(self):
        """⚠⚠ v3483 — the eye on v3479, finding [0]: Grok was handed the LIVE path and opened it
        whenever it liked. The shadow read must be handed the snapshot, and the log must be told
        which file Grok was shown."""
        jobs = self._jobs()
        self.assertEqual(len(jobs), 2, "the two shadow jobs moved — this law is judging nothing")
        for fn, calls in jobs:
            bound = [a.arg for a in fn.args.args]
            for c in calls:
                kw = {k.arg: k.value for k in c.keywords}
                self.assertIn("shown", kw, "%s never tells the log which file Grok was shown" % fn.name)
                self.assertTrue(isinstance(kw["shown"], ast.Name) and kw["shown"].id in bound,
                                "%s: `shown` is not the snapshot bound when the thread started"
                                % fn.name)
                shown = kw["shown"].id
            reads = [c for c in ast.walk(fn) if isinstance(c, ast.Call)
                     and getattr(c.func, "attr", "") == "g5_vision_read"]
            self.assertEqual(len(reads), 1, "%s: expected one shadow read" % fn.name)
            arg = reads[0].args[0] if reads[0].args else None
            self.assertIsInstance(arg, ast.Name, "%s reads a computed path" % fn.name)
            src_of = [n.value for n in ast.walk(fn) if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == arg.id for t in n.targets)]
            self.assertTrue(src_of and isinstance(src_of[0], ast.BoolOp)
                            and isinstance(src_of[0].values[0], ast.Name)
                            and src_of[0].values[0].id == shown,
                            "%s hands Grok %r, which is not the snapshot first — the live path "
                            "again" % (fn.name, arg.id))


    def test_a_thread_that_never_starts_still_removes_its_snapshot(self):
        """v3486 — the eye on the shipped v3483: the snapshot is made BEFORE the thread, the only unlink
        is the thread's own `finally`, and a failed start() was swallowed by the outer except — one
        full frame left in the temp dir per failed start. Every start must sit in a try whose handler
        removes the snapshot."""
        with io.open(TV_DIABLO, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        starts = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            for st in node.body:
                for c in ast.walk(st):
                    if (isinstance(c, ast.Call) and getattr(c.func, "attr", "") == "start"
                            and isinstance(c.func.value, ast.Call)
                            and any(k.arg == "target" and isinstance(k.value, ast.Name)
                                    and k.value.id.startswith("_g5_shadow_job")
                                    for k in c.func.value.keywords)):
                        removes = any(getattr(x.func, "attr", "") == "remove"
                                      for h in node.handlers for x in ast.walk(h)
                                      if isinstance(x, ast.Call))
                        starts.append((c.func.value.keywords[0].value.id, removes))
        names = sorted(set(n for n, _r in starts))
        self.assertEqual(names, ["_g5_shadow_job", "_g5_shadow_job2"],
                         "expected both shadow-thread starts inside a try; found %r" % (starts,))
        for n in names:
            self.assertTrue(any(r for m, r in starts if m == n),
                            "%s's start() is caught by a handler that never removes the snapshot" % n)

class TheDoctorSaysWhatNoFrameHolds(unittest.TestCase):

    def _drive(self, unattributed, why):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 3600))
        row = {"id": "g5-shadow-divergence", "state": "measured", "mode": "shadow",
               "label": "G5 two-eye divergence", "detail": "stub",
               "report": {"fields": {"names": {
                   "disagree": {"n": 1, "d": 4, "last_ts": ts},
                   "frames_disagree": {"n": 1, "d": 3, "last_ts": ts},
                   "frames_unattributed_rows": unattributed,
                   "frames_unattributed_why": why}}},
               "store": {"exists": True}}
        real = R.divergence_row
        R.divergence_row = lambda *a, **k: row
        try:
            return dict(cd.CHECKS)["two eyes compared"]()
        finally:
            R.divergence_row = real

    def test_the_row_names_the_reads_no_frame_holds_BY_REASON(self):
        """v3483 — the eye on v3479, finding [2]: the whole unplaced total was printed as "reused
        scratch names". Each reason is its own count."""
        st, say = self._drive(134, {R.WHY_SCRATCH: 131, R.WHY_CHANGED: 2, R.WHY_UNKNOWN: 1})
        self.assertIn("134 read(s) are attributed to no frame", say, say)
        for part in ("131: " + R.WHY_SCRATCH, "2: " + R.WHY_CHANGED, "1: " + R.WHY_UNKNOWN):
            self.assertIn(part, say, "the doctor folded a reason away: %s" % say)

    def test_BASELINE_nothing_unattributed_adds_nothing(self):
        st, say = self._drive(0, {})
        self.assertNotIn("attributed to no frame", say,
                         "a warning that fires when nothing is wrong is an off switch: %s" % say)


RED_PROOF = [
    {
        "why": "keying a scratch name as a frame restores #197: read.jpg is one MIXED frame again",
        "file": "g5_shadow_reducer.py",
        "find": "    if _FRAME_NAME_RX.match(name):\n        return (\"frame\", name), None\n    return None, WHY_SCRATCH",
        "replace": "    return (\"frame\", name), None",
        "matches": 1,
    },
    {
        "why": "dropping the moved-picture check folds a two-picture row into a frame, which then "
               "reads MIXED about a disagreement the lanes never had about one picture",
        "file": "g5_shadow_reducer.py",
        "find": "        return (((\"picture\", str(pic)), None) if pic == after else (None, WHY_CHANGED))",
        "replace": "        return ((\"picture\", str(pic)), None)",
        "matches": 1,
    },
    {
        "why": "a moved count with no identity to move reads as MEASURED-AND-ZERO when nobody "
               "looked",
        "file": "g5_shadow_reducer.py",
        "find": "(figure(_moved, _pair_known, bf, bl) if _pair_known else None)",
        "replace": "figure(_moved, _pair_known, bf, bl)",
        "matches": 1,
    },
    {
        "why": "recording the caller's hash as the after-hash makes every picture look unmoved, "
               "so the race the field exists for can never be seen",
        "file": "g5_grok_eyes.py",
        "find": "            \"picture_after\": _after,",
        "replace": "            \"picture_after\": picture,",
        "matches": 1,
    },
    {
        "why": "a caller that stops handing over the picture leaves every new row UNKNOWN again",
        "file": "tv_diablo.py",
        "find": "                            _G5.g5_shadow_log(_c, _gr, _orig, picture=_pic, shown=_snap)",
        "replace": "                            _G5.g5_shadow_log(_c, _gr, _orig)",
        "matches": 1,
    },
    {
        "why": "a doctor sentence that drops the unattributed reads prints a frame fraction as if "
               "it covered every read",
        "file": "console_doctor.py",
        "find": "    _unattr = names.get(\"frames_unattributed_rows\")\n    if _unattr:",
        "replace": "    _unattr = 0\n    if _unattr:",
        "matches": 1,
    },
    {
        "why": "v3483 - a known picture with an UNKNOWN shown-picture guessed into the before-picture's frame again (the eye on v3479, finding [3])",
        "file": "g5_shadow_reducer.py",
        "find": "    if pic:\n        return None, WHY_UNKNOWN",
        "replace": "    if pic:\n        return (\"picture\", str(pic)), None",
        "matches": 1
    },
    {
        "why": "v3483 - grok handed the LIVE path again instead of the snapshot, so the two eyes can be shown different bytes (the eye on v3479, finding [0])",
        "file": "tv_diablo.py",
        "find": "                        _p = _snap or _orig",
        "replace": "                        _p = _orig",
        "matches": 1
    },
    {
        "why": "v3486 - a failed thread start leaves the snapshot in the temp dir again: the handler no longer removes it (the eye on the shipped v3483)",
        "file": "tv_diablo.py",
        "find": "                    try:\n                        threading.Thread(target=_g5_shadow_job, daemon=True).start()\n                    except Exception:\n                        if _snap:\n                            try:\n                                os.remove(_snap)",
        "replace": "                    try:\n                        threading.Thread(target=_g5_shadow_job, daemon=True).start()\n                    except Exception:\n                        if _snap:\n                            try:\n                                pass",
        "matches": 1
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
