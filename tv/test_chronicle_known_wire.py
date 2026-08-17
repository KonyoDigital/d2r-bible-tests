"""v1695 — THE RETRO SWEEP IS HANDED THE FRAMES THE LIVE AGENT ALREADY IDENTIFIED.

`sweep_hist(known_chronicle=)` shipped in v1689 and NOTHING EVER PASSED IT. Both halves were built
and never joined: the live lane journals a `chronicle/visit` row naming the frames it saw, and the
sweep will admit a named frame regardless of what the cheap classifier makes of it — but the call
site omitted the argument, so every retro sweep re-derived from scratch what the live agent already
knew, and paid the classifier for the privilege of disagreeing with it.

WHY THIS HAD A DEADLINE. `tv/chronicle_swept.json` did not exist when this was found — no sweep had
ever completed on this machine. The first one writes every reel it touches into that file, and
`skip_reels` then hides those reels from every future sweep. A first sweep that selects nothing does
not merely waste a run, it SEALS the footage, and undoing that costs a `force` re-read of everything.

WHAT THIS GUARD HOLDS, measured rather than asserted: with a classifier that recognises nothing —
the exact predicted failure — a reel holding eight Chronicle frames yields ZERO page reads without
the wire and EIGHT with it. That 0 -> 8 is the whole feature; if this test ever goes quiet, the wire
came loose again and the sweep silently went back to reading nothing.

Hermetic: builds its own reel in a temp dir, stubs both lanes, reaches no model and writes nothing
outside tempfile. It deliberately does NOT import control_app (13k lines, module-level side
effects); the function under test is sliced out of the source by ast, so this guard can never be
the thing that mutates his console.
"""
import ast
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# this suite's own docstrings print non-ASCII (— and ⚠). On his Windows console that crashes while
# REPORTING, so a clean tree would exit non-zero. See tv/console_safe.py.
try:
    from console_safe import enable as _enable_console
    _enable_console()
except Exception:                                   # pragma: no cover
    pass

import chronicle_retro as cr  # noqa: E402

try:
    from PIL import Image as _PILImage
except Exception:                                   # pragma: no cover
    _PILImage = None


def _slice(name):
    """The named top-level function, lifted out of control_app.py source. See module docstring for
    why this is a slice and not an import."""
    src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == name), None)
    assert fn is not None, "%s not found in control_app.py" % name
    return ast.get_source_segment(src, fn), tree


class KnownChronicleContract(unittest.TestCase):
    """The map handed to the sweep is the shape the sweep already accepts."""

    def _build(self, visits, raise_it=False):
        fn_src, _ = _slice("_chron_known_from_journal")
        ns = {}

        def chronicle_visits(limit=500):
            if raise_it:
                raise RuntimeError("journal unreadable")
            return {"visits": visits}

        ns["chronicle_visits"] = chronicle_visits
        exec(fn_src, ns)
        return ns["_chron_known_from_journal"]()

    def test_flat_map_across_visits(self):
        self.assertEqual(
            self._build([{"ledger": "uniques", "frames": ["a", "b"]},
                         {"ledger": "sets", "frames": ["c"]}]),
            {"a": "uniques", "b": "uniques", "c": "sets"})

    def test_unread_ledger_never_overwrites_a_real_one(self):
        # order must not decide the answer: "" is the absence of knowledge, not a competing claim
        self.assertEqual(self._build([{"ledger": "", "frames": ["x"]},
                                      {"ledger": "uniques", "frames": ["x"]}]), {"x": "uniques"})
        self.assertEqual(self._build([{"ledger": "uniques", "frames": ["x"]},
                                      {"ledger": "", "frames": ["x"]}]), {"x": "uniques"})

    def test_tab_unknown_is_still_a_mark(self):
        # "this IS a Chronicle frame, tab unknown" is a real state the selector handles, and is
        # deliberately NOT the same as the frame being absent.
        self.assertEqual(self._build([{"ledger": "", "frames": ["y"]}]), {"y": ""})

    def test_broken_journal_degrades_and_never_raises(self):
        # these marks make the sweep cheaper and better; nothing downstream may depend on them.
        self.assertEqual(self._build([], raise_it=True), {})

    def test_empty_frames_are_skipped(self):
        self.assertEqual(self._build([{"ledger": "uniques", "frames": ["", None, "z"]}]),
                         {"z": "uniques"})


class CallSiteActuallyPassesIt(unittest.TestCase):
    """The entire defect was a missing keyword argument, so that is what gets asserted."""

    def test_sweep_hist_is_called_with_known_chronicle(self):
        _, tree = _slice("_chron_known_from_journal")
        sweep = next(n for n in ast.walk(tree)
                     if isinstance(n, ast.FunctionDef) and n.name == "_chron_sweep_run")
        calls = [n for n in ast.walk(sweep)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "sweep_hist"]
        self.assertEqual(len(calls), 1, "expected exactly one sweep_hist call")
        self.assertIn("known_chronicle", {k.arg for k in calls[0].keywords},
                      "the sweep is back to re-deriving what the live agent already knew")


@unittest.skipIf(_PILImage is None, "Pillow absent — the sweep cannot group frames without it")
class MarksChangeWhatTheSweepSelects(unittest.TestCase):
    """THE RED/GREEN. Without marks the sweep reads nothing; with them it reads the marked frames.

    ⚠ THE FIRST VERSION OF THIS FIXTURE WROTE 0-BYTE .jpg FILES and reported GREEN=0, which reads as
    "the wire does not work" when the wire provably did (his real reel gave 0 -> 8 through the same
    code path). live_probe() at chronicle_retro:467 discards a run that is blank all the way through
    BEFORE the kind is ever consulted — "a blank capture cannot be a Chronicle" — so the marks were
    honoured and then thrown away one line later. The frames must be decodable and visibly non-blank,
    and they must differ from each other, or _distinct() collapses a scrolled page to one read.
    """

    def _reel(self, tmp, n=12, base=1786385773403):
        reel = os.path.join(tmp, "reel_s_test_0001")
        os.makedirs(reel)
        names = []
        for i in range(n):
            nm = "f_%d.jpg" % (base + i * 1000)   # 1fps, matching the real reel's cadence
            im = _PILImage.new("RGB", (48, 48))
            px = im.load()
            for y in range(48):
                for x in range(48):
                    # `i` in every channel: non-blank, and each frame unmistakably its own page
                    px[x, y] = ((x * 5 + i * 20) % 256, (y * 7 + i * 13) % 256,
                                ((x + y) * 3 + i * 31) % 256)
            im.save(os.path.join(reel, nm), "JPEG", quality=90)
            names.append(nm)
        return reel, names

    def test_blind_classifier_reads_nothing_without_marks_and_the_marked_frames_with_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            reel, names = self._reel(tmp)
            marked = {n: "uniques" for n in names[3:11]}   # eight frames, as in his real journal

            pages = []

            def classify_blind(_p):
                return None      # recognises nothing — the predicted first-sweep failure

            def read_page(p, k):
                pages.append((os.path.basename(str(p)), k))
                return {}        # a page read finding no names; no model is reached

            cr.read_reel(reel, classify_blind, read_page, known_chronicle=None)
            red = len(pages)

            pages.clear()
            cr.read_reel(reel, classify_blind, read_page, known_chronicle=marked)
            green = len(pages)

            self.assertEqual(red, 0,
                             "a blind classifier should select nothing — if this is non-zero the "
                             "fixture stopped reproducing the failure and the GREEN below is hollow")
            self.assertGreater(green, 0,
                               "marked frames must be admitted despite the classifier refusing")
            self.assertGreater(green, red, "the wire is what made the difference")


class AgainstHisRealFootage(unittest.TestCase):
    """Skipped anywhere his session data is absent — CI has neither journal nor reels."""

    def test_real_journal_and_reel(self):
        journal = os.path.join(HERE, "sessions.jsonl")
        reel = os.path.join(HERE, "frames", "hist", "reel_s_1786385768689_67392")
        if not (os.path.isfile(journal) and os.path.isdir(reel)):
            self.skipTest("his session footage is not on this machine")

        rows = [json.loads(l) for l in open(journal, encoding="utf-8") if l.strip()]
        visits = [{"ledger": r.get("ledger") or "", "frames": r.get("frames") or []}
                  for r in reversed(rows)
                  if r.get("lane") == "chronicle" and r.get("kind") == "visit"]
        fn_src, _ = _slice("_chron_known_from_journal")
        ns = {"chronicle_visits": lambda limit=500: {"visits": visits}}
        exec(fn_src, ns)
        known = ns["_chron_known_from_journal"]()
        self.assertTrue(known, "his journal holds chronicle/visit rows; the map came back empty")

        pages = []

        def read_page(p, k):
            pages.append(os.path.basename(str(p)))
            return {}

        cr.read_reel(reel, lambda _p: None, read_page, known_chronicle=None)
        self.assertEqual(len(pages), 0)
        pages.clear()
        cr.read_reel(reel, lambda _p: None, read_page, known_chronicle=known)

        # 2026-08-17 — SCOPE THE EXPECTATION TO THE REEL BEING READ.
        # `known` is built from EVERY chronicle visit in his journal, across every session; this
        # reads ONE reel. The assertion compared the two directly, so it held only while his journal
        # happened to contain visits from that one session — and the moment he recorded another
        # Chronicle visit it went 8 != 12, red on footage that had not changed. A test standing on
        # live, growing data has to say which slice of it it is judging.
        #
        # ASK THE MODULE, DO NOT RE-DERIVE THE JOIN. A mark is a deep-lane frameId, "a different
        # capture of the same moment", so _resolve_known binds it to the nearest frame within
        # JOURNAL_MATCH_MS — NOT by equal timestamps. A first attempt here matched "<idx>_<ts>"
        # against "f_<ts>.jpg" and found ZERO overlap while read_reel was happily binding eight,
        # because the two captures are milliseconds apart, never identical. Re-implementing that
        # rule in the test would have been a second copy of it to drift.
        with open(os.path.join(reel, "index.json"), encoding="utf-8") as fh:
            reel_frames = json.load(fh).get("frames") or []
        mine = cr._resolve_known(reel_frames, cr._known_chronicle_map(known))
        self.assertTrue(mine, "no mark in his journal binds to a frame in this reel")
        self.assertEqual(len(pages), len(mine),
                         "every frame the live agent marked IN THIS REEL should be read back")


if __name__ == "__main__":
    unittest.main(verbosity=2)
