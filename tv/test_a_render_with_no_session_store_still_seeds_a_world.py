# -*- coding: utf-8 -*-
"""A RENDER WITH NO SESSION STORE STILL GETS A WORLD TO PHOTOGRAPH.

sessions.jsonl is gitignored. A checkout that has none — this VM, a fresh clone, a worktree whose
main checkout also has none — used to boot the render sandbox against an empty journal. The film
seed then wrote stills for 0 of 0 runs. Measured there: shelf-cards had no .sh-grid, theatre-head
said the theatre never opened, and river-strip read 0 of 4 lanes straight after a rebuild, because
thShelf does not paint until TH.sessions is nonempty. Those three refusals are an empty fixture.

_seed_empty_world_journal writes FILM_RUNS synthetic runs into the sandbox it is handed, and only
when that sandbox has no journal. _seed_film then attaches the stills the shelf counts. A journal
already present is left byte for byte, so his world is never replaced by the fixture.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import render_check as rc  # noqa: E402
import replay  # noqa: E402
import reel_retention as rr  # noqa: E402


class ARenderWithNoSessionStoreStillSeedsAWorld(unittest.TestCase):

    def test_an_empty_sandbox_gets_filmed_runs_and_an_existing_journal_is_kept(self):
        sand = tempfile.mkdtemp(prefix="rc-empty-world-")
        self.addCleanup(shutil.rmtree, sand, True)
        hist = os.path.join(sand, "frames", "hist")
        os.makedirs(hist)
        n = rc._seed_empty_world_journal(sand)
        self.assertEqual(n, rc.FILM_RUNS, "an empty sandbox was not given %d runs" % rc.FILM_RUNS)
        path = os.path.join(sand, "sessions.jsonl")
        with open(path, encoding="utf-8") as fh:
            rows = [json.loads(ln) for ln in fh if ln.strip()]
        ids = []
        for row in rows:
            self.assertEqual(row.get("area"), "Rogue Encampment")
            self.assertNotIn("fixture", row)
            self.assertRegex(row.get("sessionId") or "", r"^s_\d{10,16}_\d+$")
            if row["sessionId"] not in ids:
                ids.append(row["sessionId"])
        self.assertEqual(len(ids), rc.FILM_RUNS)
        order = rr.recent_order(["reel_" + sid for sid in ids])
        self.assertEqual(len(order), len(ids),
                         "the river cannot order these runs, so riverKept will hide every card")
        kept = [name[len("reel_"):] for name in order[-min(16, len(order)):]]
        self.assertEqual(len(kept), min(16, len(ids)))
        self.assertEqual(len(rows), rc.FILM_RUNS * 3, "each run needs three rows so it is not a ghost")
        groups = replay.split_sessions(rows)
        self.assertEqual(len(groups), rc.FILM_RUNS)
        filmed, total = rc._seed_film(sand, hist)
        self.assertEqual((filmed, total), (rc.FILM_RUNS, rc.FILM_RUNS))
        reels = [d for d in os.listdir(hist) if d.startswith("reel_")]
        self.assertEqual(len(reels), rc.FILM_RUNS)

        kept = tempfile.mkdtemp(prefix="rc-kept-world-")
        self.addCleanup(shutil.rmtree, kept, True)
        prior = os.path.join(kept, "sessions.jsonl")
        with open(prior, "w", encoding="utf-8") as fh:
            fh.write('{"sessionId":"s_his"}\n')
        with open(prior, "rb") as fh:
            before = fh.read()
        self.assertEqual(rc._seed_empty_world_journal(kept), 0)
        with open(prior, "rb") as fh:
            self.assertEqual(fh.read(), before, "an existing journal was replaced")

        with open(rc.__file__.replace(".pyc", ".py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("_nj = _seed_empty_world_journal(_sand)\n"), 1,
                         "the sandbox no longer asks for a journal when it has none")

    def test_the_live_tree_is_not_where_the_synthetic_journal_is_written(self):
        live = os.path.join(HERE, "sessions.jsonl")
        existed = os.path.isfile(live)
        before = os.path.getsize(live) if existed else None
        sand = tempfile.mkdtemp(prefix="rc-empty-world-")
        self.addCleanup(shutil.rmtree, sand, True)
        rc._seed_empty_world_journal(sand)
        self.assertTrue(os.path.isfile(os.path.join(sand, "sessions.jsonl")))
        self.assertEqual(os.path.isfile(live), existed)
        if existed:
            self.assertEqual(os.path.getsize(live), before)


RED_PROOF = [
    {
        "why": "the synthetic journal is no longer written, so an empty checkout films 0 runs and the three shelf targets photograph nothing",
        "file": "tv/render_check.py",
        "find": "    with io.open(path, \"w\", encoding=\"utf-8\") as fh:\n"
                "        fh.write(\"\\n\".join(lines) + \"\\n\")\n"
                "    return runs\n",
        "replace": "    return 0\n",
        "matches": 1,
    },
    {
        "why": "the sandbox stops calling the seeder, so a missing journal stays missing",
        "file": "tv/render_check.py",
        "find": "        _nj = _seed_empty_world_journal(_sand)\n",
        "replace": "        _nj = 0\n",
        "matches": 1,
    },
    {
        "why": "an existing journal is overwritten, so his world is replaced by the fixture",
        "file": "tv/render_check.py",
        "find": "    if os.path.isfile(path) or runs < 1:\n        return 0\n",
        "replace": "    if runs < 1:\n        return 0\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
