# -*- coding: utf-8 -*-
"""SPLITTING A RUN ON THE TOOLTIP MAY ONLY EVER ADD PAGES — IT MAY NOT REMOVE THE LAST ONE.

v2396 splits a still run on the TOOLTIP so a hover-by-hover pass stops collapsing into a single
page, and it says of itself that it "splits on evidence and leaves the rest alone". It did not.
MIN_RUN_FRAMES is a STILLNESS floor calibrated on UNSPLIT runs; applied to the fragments, it can
discard every candidate a reel had.

MEASURED 2026-09-13 on reel_s_1788099999528_42457 — 4 frames, 1 run, 1 candidate before the split;
2 runs and ZERO candidates after it, both fragments under the 3-frame floor. Nothing was ever
offered to the reader. A forced re-sweep reported reelsDone=1/1 with pagesRead=0, classify called
0 times and reader 0 times, while the free structural gate opened all 4 frames as `shared` and the
survey counted 4 panels. A short reel with a hover in it was permanently unreadable, and it sealed
rows=0 — which then held it in the river forever. [[feedback-threshold-above-the-ceiling]]

⚠ THE FALLBACK IS NOT "IGNORE THE FLOOR". It restores the grouping that existed BEFORE the split,
floor and all. A reel with no candidates either way still reads nothing, which is correct.
"""
import io
import json
import os
import shutil
import tempfile
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


class TestTheTooltipSplitMayOnlyAddPages(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="tipsplit.")
        self.reel = os.path.join(self.d, "reel_s_1700000000001_00002")
        os.makedirs(self.reel)
        self.names = []
        for i in range(4):
            n = "f_170000000%04d.jpg" % i
            with io.open(os.path.join(self.reel, n), "wb") as fh:
                fh.write(b"\xff\xd8\xff\xe0stub")
            self.names.append(n)
        # ⚠ THE KEY IS "f", NOT "name". still_runs reads frames[i]["f"]; a fixture using "name"
        # produces ZERO runs and every assertion here passes or fails for the wrong reason. Cost
        # three wrong diagnoses before the docstring settled it. [[feedback-blind-fixture-green-gate]]
        idx = {"sessionId": "s_1700000000001_00002",
               "frames": [{"f": n, "ts": 1700000000000 + i * 1000}
                          for i, n in enumerate(self.names)]}
        with io.open(os.path.join(self.reel, "index.json"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps(idx))

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def _sweep(self, tooltips):
        """Run the real sweep with a tooltip oracle we control. -> (reader_calls, sessionsRead)"""
        import vault_retro as VR
        import tooltip_find as TF
        calls = {"reader": 0}

        def classify(p, *a, **k):
            return "stash"                     # a SURFACE name, not a tab name

        def reader(p, surface):
            calls["reader"] += 1
            return {"items": []}

        import chronicle_retro as CR
        old_locate = TF.locate
        old_probe = CR.live_probe
        old_memo = dict(getattr(VR, "_TOOLTIP_MEMO", {}))
        try:
            # ⚠ RETURN THE SHAPE PRODUCTION UNWRAPS: `tooltip_find.locate` answers
            # (rect|None, why), and `_tip_of` takes `r[0] if isinstance(r, tuple) else r`. Stubbed
            # as a BARE bbox, that unwrapping stored `left` — an int — and this fixture only split
            # because every `left` happened to differ. A vertical hover (same left, new top) would
            # not have split at all, so the fixture was not modelling production.
            TF.locate = lambda p, *a, **k: (tooltips.get(os.path.basename(p)), "stub")
            # ⚠ live_probe rejects a BLANK capture, and these fixture frames are 8-byte stubs. It
            # is a different law with its own gate; stubbing it keeps this one about candidate
            # runs. The alternative — real frames — would make the gate unrunnable on CI, which
            # has no reels at all. [[feedback-blind-fixture-green-gate]]
            CR.live_probe = lambda names, path_of: ((names[0] if names else None), [])
            if hasattr(VR, "_TOOLTIP_MEMO"):
                VR._TOOLTIP_MEMO.clear()
            prop = VR.sweep([self.reel],
                            sig=lambda p: 1.0,          # identical AND truthy: 0.0 reads as unreadable
                            classify=classify, reader=reader,
                            panel_gate=lambda p: "shared", prior_seen=[])
            return calls["reader"], list(prop.get("sessionsRead") or [])
        finally:
            TF.locate = old_locate
            CR.live_probe = old_probe
            if hasattr(VR, "_TOOLTIP_MEMO"):
                VR._TOOLTIP_MEMO.clear()
                VR._TOOLTIP_MEMO.update(old_memo)

    def test_a_split_that_would_zero_the_candidates_falls_back(self):
        """Four identical frames, tooltips moving every frame — the split fragments them all."""
        tips = {n: (10 + i * 40, 20 + i * 40, 30, 30) for i, n in enumerate(self.names)}
        reads, sessions = self._sweep(tips)
        print("tooltip moving every frame -> reader calls=%d sessionsRead=%s" % (reads, sessions))
        self.assertGreater(reads, 0,
                           "the split fragmented a readable 4-frame reel into sub-floor runs and "
                           "offered the reader NOTHING — that reel can never bank a row, and the "
                           "river then holds it forever")
        self.assertTrue(sessions, "a reel that was read must report its session")

    def test_a_reel_with_no_tooltips_is_untouched(self):
        reads, _ = self._sweep({})
        print("no tooltips -> reader calls=%d" % reads)
        self.assertGreater(reads, 0, "the control case v2396 cites must keep reading")

    def test_the_split_never_yields_FEWER_candidates_than_no_split(self):
        """The case the cross-family second eye found on the SHIPPED v3075 diff.

        v3075 fell back only `if not cands`, so the law was named "may only ever add pages" while
        the code restored solely at ZERO. REPRODUCED before it was believed: two held screens of 4
        frames, a hover moving inside the FIRST screen only, gives runs [4, 4] -> 2 candidates
        without the split and [2, 2, 4] -> 1 candidate with it. Candidates fell 2 -> 1 without
        ever reaching zero, so the guard never fired and a whole held screen was never read.
        [[review-after-ship]]

        Pure — it calls the grouping functions directly, so it needs no reel, no files and no
        model, and it cannot go blind when his own footage stops exercising the shape.
        """
        import chronicle_retro as CR
        import vault_retro as VR
        fr = [{"f": "f_%d.jpg" % i, "ts": 1700000000000 + i * 1000} for i in range(8)]
        one, two = [0.0] * 16, [200.0] * 16
        sig = {("f_%d.jpg" % i): (one if i < 4 else two) for i in range(8)}
        tips = {"f_0.jpg": (10, 10, 30, 30), "f_1.jpg": (10, 10, 30, 30),
                "f_2.jpg": (90, 90, 30, 30), "f_3.jpg": (90, 90, 30, 30)}
        unsplit = CR.candidate_runs(CR.still_runs(fr, lambda n: sig[n]),
                                    min_frames=VR.MIN_RUN_FRAMES)
        split = CR.candidate_runs(
            CR.still_runs(fr, lambda n: sig[n], tooltip_of=lambda n: tips.get(n)),
            min_frames=VR.MIN_RUN_FRAMES)
        print("unsplit cands=%d · split cands=%d (the shape that loses a look)"
              % (len(unsplit), len(split)))
        self.assertGreater(len(unsplit), len(split),
                           "this fixture no longer reproduces the shape it was built for, so the "
                           "assertion below would pass for the wrong reason")
        code = _between(io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read(),
                        "runs = _cr.still_runs(frames, sig_of, tooltip_of=_tip_of)",
                        "read_this_reel = False")
        bare = "\n".join(ln.split("#", 1)[0] for ln in code.splitlines())
        self.assertNotIn("if not cands:", bare,
                         "falling back only at ZERO lets the split drop a reel from 2 candidates "
                         "to 1 and never fire — which is losing a page, not adding one")
        self.assertIn("len(_unsplit) > len(cands)", bare,
                      "the grouping must be chosen by COUNT so it can never decrease")

    def test_the_fallback_restores_the_floor_rather_than_removing_it(self):
        src = io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read()
        region = _between(src, "runs = _cr.still_runs(frames, sig_of, tooltip_of=_tip_of)",
                          "read_this_reel = False")
        # ⚠⚠ PIN THE FALLBACK'S OWN FLOOR, BY PARSE. The first cut asserted the text
        # `min_frames=MIN_RUN_FRAMES` appeared anywhere in this region — but the region STARTS at
        # the split's own `candidate_runs(...)` call, which already contains it. Changing only the
        # fallback to `min_frames=1` left the assertion green, and neither runtime fixture could
        # catch it either: with the floor dropped, the split's 1-frame fragments BECOME candidates,
        # the fallback is never entered, and `assertGreater(reads, 0)` still passes. A guard that
        # cannot see the thing it names is not a guard. [[source-reading-guard]]
        import ast as _ast
        with io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8") as _fh:
            _tree = _ast.parse(_fh.read())
        _found = []
        for _n in _ast.walk(_tree):
            if (isinstance(_n, _ast.Assign) and len(_n.targets) == 1
                    and getattr(_n.targets[0], "id", None) == "_unsplit"
                    and isinstance(_n.value, _ast.Call)):
                _found.append(_n.value)
        print("fallback `_unsplit = candidate_runs(...)` sites: %d" % len(_found))
        self.assertEqual(len(_found), 1,
                         "expected exactly one fallback grouping; found %d" % len(_found))
        _kw = {k.arg: k.value for k in _found[0].keywords if k.arg}
        self.assertIn("min_frames", _kw,
                      "the fallback calls candidate_runs with no floor at all — the split's "
                      "sub-floor fragments would become candidates and it would never fire")
        self.assertEqual(getattr(_kw["min_frames"], "id", None), "MIN_RUN_FRAMES",
                         "the fallback must re-apply the SAME floor by name, not a literal that "
                         "can drift away from it")


RED_PROOF = [
    {
        "why": "the split may shrink the candidate set again — at zero a short reel with a hover "
               "in it offers the reader nothing and is held in the river for ever "
               "(reel_s_1788099999528_42457), and above zero a held screen silently goes unread "
               "when candidates fall 2 -> 1",
        "file": "vault_retro.py",
        "find": "        if len(_unsplit) > len(cands):",
        "replace": "        if False:",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
