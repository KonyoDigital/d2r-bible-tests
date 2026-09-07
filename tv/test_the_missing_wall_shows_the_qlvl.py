# -*- coding: utf-8 -*-
"""v2765 — THE MISSING WALL PRINTS THE QLVL, AND REFUSES TO PRINT ONE IT DOES NOT HAVE.

Konyo: *"for MISSING when it collapses open i want the q1-87 levels of the item in white same color
based but for sets.. because sets i see they dont have it... some items here in uniques are missing
the q level of there rarity. so for sets and uniques fix the rest."*

=== ⚠⚠ `qlvl: 0` IS A SENTINEL, NOT A LEVEL ===
MEASURED across all 5,925 item rows in `bible.html`, counted DISTINCT by name:

    high     126 of 127 carry a real qlvl        set        14 of 148
    grail     78 of  91                          special     0 of 4
    common    93 of 175                          uber        1 of 2

So a 0 means "this table never recorded one". Rendering it would put a confident **q0** under 134
set pieces and 96 uniques — a fabricated figure in the longest list on the page, which is exactly
where nobody would catch it. Absent renders NOTHING. [[zero-needs-a-denominator]]

=== ⚠⚠ AND THE 14 SET ROWS THAT DO CARRY ONE ARE NOT PIECES ===
They are set-level AGGREGATES — "Trang-Oul set (any piece)", "Immortal King set (any)", "Aldur's
Watchtower (any)". Hanging one on a piece is the trap v2299 named two comments up in the same file
("not a set-level average standing in for a piece"), and it is easy to fall into because
`_etaHours` legitimately DOES take a set aggregate as its fallback source. The qlvl reader takes no
fallback at all. Proven on real pixels: `_qlvlOf("Trang-Oul's Wing (shield)")` -> null while
`_qlvlOf("Trang-Oul set (any piece)")` -> 65.

=== ⚠ HALF OF WHAT HE ASKED FOR IS A DATA GAP, NOT A RENDER GAP ===
He said *"sets is missing the q level"* and wanted it fixed for sets too. **134 of the 148 set
entries have no qlvl anywhere in this page** — the per-piece rows carry `"tc":0,"qlvl":0`, and the
set structure holds art and dates but no level field. Nothing was found to render, and 134 values
were NOT written in from memory to make the wall look complete. That needs the game's own SetItems
table, which is a sourcing job. `test_the_set_piece_gap_is_still_real` pins the gap so that the day
the data arrives, this file goes RED and says so instead of the fix sitting unnoticed.

MEASURED ON REAL PIXELS after the change: the F-Uniques wall renders 392 missing rows and **296**
carry a q-chip, computed colour `rgb(255, 255, 255)`. The sets wall renders 135 rows and 1 chip,
which is the honest picture of the data underneath.
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()

#: every item row the page ships, as (name, tc, qlvl, tier)
ROWS = re.findall(r'"n":"([^"]{2,60})","tc":(\d+),"qlvl":(\d+),"tier":"([a-z]+)"', BIBLE)


def _best():
    """name -> (max qlvl seen, tier). Rows repeat per drop source."""
    best, tier = {}, {}
    for n, _tc, q, t in ROWS:
        best[n] = max(best.get(n, 0), int(q))
        tier[n] = t
    return best, tier


def _run_real_reader(names):
    """Run the SHIPPED _etaIdx + _qlvlOf in node against the SHIPPED rows. -> dict|None

    ⚠ THE REAL FUNCTION, NOT A PYTHON RE-IMPLEMENTATION. A second copy of the sentinel rule would
    pass while the page still printed q0. The item source is stubbed — that is the seam — but the
    logic under test is the file's own bytes.

    ⚠ `window._regKey` IS DELIBERATELY LEFT UNDEFINED so the reader takes its documented fallback
    (`String(name).toLowerCase()`). That is a real branch of the real function, and stubbing a fake
    _regKey would test a key rule this file does not own.
    """
    a = BIBLE.find("  var _etaIdxCache = null;")
    b = BIBLE.find("  window._qlvlOf = _qlvlOf;")
    if a < 0 or b < 0 or b < a:
        return None
    slice_ = BIBLE[a:b + len("  window._qlvlOf = _qlvlOf;")]
    items = [{"n": n, "qlvl": int(q), "tier": t} for n, _tc, q, t in ROWS]
    js = ("var window = {};\n"
          "window._allDropItems = function(){ return " + json.dumps(items) + "; };\n"
          + slice_ + "\n"
          "const _q = " + json.dumps(names) + ";\n"
          "const out = {}; for (const n of _q) out[n] = window._qlvlOf(n);\n"
          "console.log(JSON.stringify(out));")
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "qlvl_probe.js")
    io.open(p, "w", encoding="utf-8").write(js)
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True, timeout=90)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads((r.stdout or "").strip().split("\n")[-1])
    except Exception:
        return None


class TheMissingWallShowsTheQlvl(unittest.TestCase):

    # ── the guard can find its subject ───────────────────────────────────────────────────────
    def test_the_reader_is_still_here(self):
        self.assertIn("function _qlvlOf(name){", BIBLE, "the qlvl reader moved or was renamed")
        self.assertIn("window._qlvlOf = _qlvlOf;", BIBLE, "the reader is no longer exported")
        self.assertTrue(ROWS, "no item rows parsed out of the page — this file graded nothing")

    # ── ⚠⚠ THE LAWS, AGAINST THE REAL READER ────────────────────────────────────────────────
    def test_a_real_unique_gets_its_real_level(self):
        got = _run_real_reader(["Atma's Wail", "Stealskull", "Nagelring"])
        if got is None:
            self.skipTest("node unavailable, so the shipped reader could not be run — a skip is "
                          "NOT a pass and nothing here has been established")
        self.assertEqual(51, got.get("Atma's Wail"))
        self.assertEqual(35, got.get("Stealskull"))
        self.assertEqual(7, got.get("Nagelring"))

    def test_the_zero_sentinel_renders_NOTHING(self):
        """★ 0 is 'never recorded', and q0 under 230 rows would be a fabricated number in the one
        place nobody would check."""
        got = _run_real_reader(["Annihilus", "Key of Hate", "Death's Guard (belt)",
                                "Arctic Binding (belt)"])
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        for n, v in got.items():
            self.assertIsNone(v, "%r resolved to %r. Its table row carries qlvl 0, which means no "
                                 "level was ever recorded — printing it states a fact the data "
                                 "does not hold" % (n, v))

    def test_a_SET_AGGREGATE_never_leaks_onto_a_PIECE(self):
        """★★ THE TRAP, AND IT IS THE ONE THIS FILE EXISTS FOR. `_etaHours` takes a set aggregate as
        its fallback source ON PURPOSE — a piece with no clock of its own borrows the set's. Doing
        the same for a LEVEL would print the set's gate under every piece of it. v2299 refused this
        two comments up in the same file; the qlvl reader takes no fallback at all."""
        got = _run_real_reader(["Trang-Oul's Wing (shield)", "Trang-Oul set (any piece)",
                                "Immortal King's Soul Cage (armor)", "Immortal King set (any)"])
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertIsNone(got.get("Trang-Oul's Wing (shield)"),
                          "a set PIECE picked up %r — the aggregate's level standing in for the "
                          "piece's, which is the substitution v2299 refused"
                          % got.get("Trang-Oul's Wing (shield)"))
        self.assertIsNone(got.get("Immortal King's Soul Cage (armor)"))
        self.assertEqual(65, got.get("Trang-Oul set (any piece)"),
                         "the aggregate itself lost its own level, so this law is now passing "
                         "because NOTHING resolves — an instrument failure, not a clean result")

    # ── ⚠ THE FIXTURE ASSUMPTION, PINNED ────────────────────────────────────────────────────
    def test_the_set_piece_gap_is_still_real(self):
        """⚠⚠ HALF HIS ASK IS BLOCKED ON DATA THIS PAGE DOES NOT HAVE, and that must not become
        invisible. The day set-piece levels are sourced, this goes RED — which is the signal to
        render them, not a failure."""
        best, tier = _best()
        sets = [(n, q) for n, q in best.items() if tier[n] == "set"]
        withq = [(n, q) for n, q in sets if q > 0]
        self.assertTrue(sets, "no set rows parsed — this law graded nothing")
        # ⚠ THE DISCRIMINATOR IS THE ROSTER, NOT A NAME PATTERN. My first cut asked whether the
        # name "looked like" an aggregate (`(any)`, `(set)`, the word set) and went red on
        # "Sigon's Complete Steel" — which IS the Sigon set's own name and simply does not contain
        # any of those tokens. A shape-guess about names is not a test; `set_roster.json` holds the
        # 135 real piece names and settles it. [[feedback-suspect-the-instrument]]
        roster = json.load(io.open(os.path.join(HERE, "set_roster.json"), encoding="utf-8"))
        pieces = roster.get("pieces") or []
        self.assertEqual(135, len(pieces),
                         "the set roster no longer holds 135 pieces (%d) — this law's authority "
                         "moved and it must be re-pointed before its green means anything"
                         % len(pieces))
        bare = set(p.split(" (")[0] for p in pieces) | set(pieces)
        for n, q in withq:
            self.assertNotIn(n, bare,
                             "%r is a set PIECE and it now carries a real qlvl (%d). Per-piece "
                             "levels have arrived — render them; the sets wall is currently blank "
                             "for 134 pieces only because nothing was there to show." % (n, q))
        self.assertLessEqual(len(withq), 20,
                             "%d set entries now carry a qlvl, up from the 14 known aggregates. "
                             "Per-piece data may have landed; the sets wall should stop being blank."
                             % len(withq))

    def test_the_unique_coverage_has_not_collapsed(self):
        """A zero needs a denominator, and so does a fix. If a data change drops unique coverage,
        the wall goes quiet and nothing else would say so."""
        best, tier = _best()
        hi = [(n, q) for n, q in best.items() if tier[n] == "high"]
        self.assertGreaterEqual(sum(1 for _n, q in hi if q > 0), 120,
                                "the 'high' tier lost its levels — the wall he asked to fill is "
                                "emptying out and only this law would notice")

    # ── ⚠ BOTH WALLS CARRY IT, AND THE RENDERER GUARDS ──────────────────────────────────────
    def test_both_walls_pass_the_level_through(self):
        """⚠ Built and not called is this repo's most repeated defect. Two walls feed one renderer;
        a level added to one only would look shipped and be half absent. [[the-unjoined-end]]"""
        # ⚠⚠ v2769 — CORRECTED, AND THE CORRECTION IS THE POINT. This first required the UNIQUES
        # wall to carry `q:` too. The post-ship review found — and the live board CONFIRMED at 220
        # of 220 rows — that it then printed the level TWICE: "Gull q4 q4". That wall's `badge` is
        # ALREADY the qlvl (`badge:(x.qlvl>0?'q'+x.qlvl:'')`), so uniques never needed a chip and
        # v2765 added a duplicate rather than a fix.
        # The uniques that show nothing are the 96 whose qlvl is 0 in the data, and sets have none
        # at all — BOTH are the data gap in task #20. The renderer was never this wall's problem.
        self.assertNotIn("q:_qlvlOf(x.n)", BIBLE,
                         "the UNIQUES wall carries a q chip again — its badge is already the "
                         "qlvl, so every row with a real level prints it twice")
        i = BIBLE.find("badge:(x.qlvl")
        self.assertGreater(i, 0,
                           "the uniques wall's badge no longer carries the qlvl — if that moved, "
                           "the chip may now be the right home and this law must be re-pointed "
                           "deliberately rather than left green")
        # ⚠⚠ v2771 — HIS CLARIFICATION, with a screenshot: "for the sets it says in white the type
        # base item it is — it needs to be switched to the q level INSTEAD of the base item in
        # white". So the level goes IN the badge, REPLACING the slot, not beside it. v2765 had it
        # as a separate chip, which would have put two white tokens on one row.
        self.assertIn("badge:(_sq?('q'+_sq):_sl)", BIBLE,
                      "the SETS wall's white badge no longer carries the q-level. He asked for the "
                      "level IN that slot, replacing the base type — not added next to it")
        self.assertNotIn("q:_qlvlOf(pp.name)", BIBLE,
                         "the sets wall carries a SECOND q token beside the badge, so a row with a "
                         "known level would print it twice — the defect the uniques wall already "
                         "had")
        # ⚠ AND IT FALLS BACK, which is why the wall is not blank today. 134 of 148 set entries
        # have no level, so `_sq` is null and the slot still shows. Dropping to an empty badge
        # would trade a true fact for a blank while waiting on data (task #20).
        self.assertIn("_sq?", BIBLE, "the badge no longer falls back to the base type, so 134 set "
                                     "rows would render an empty white space")

    def test_the_renderer_emits_nothing_when_there_is_no_level(self):
        """`e.q ? ... : ''` — a truthiness guard, so both null AND a 0 that ever slipped through
        render as absence rather than as `q0`."""
        i = BIBLE.find("entries.forEach(function(e){ H.push('<span class=\"gf-piece gf-miss\"")
        self.assertGreater(i, 0, "the shared missing-row renderer moved")
        blk = BIBLE[i:BIBLE.find("\n", i)]
        self.assertIn("e.q?", blk, "the level is rendered unconditionally, so an absent one prints")
        self.assertIn("gp-q", blk, "the level chip is gone from the renderer")

    def test_the_chip_is_white_as_he_asked(self):
        i = BIBLE.find(".gp-q{")
        self.assertGreater(i, 0, "the .gp-q style is gone")
        blk = BIBLE[i:BIBLE.find("}", i)]
        self.assertIn("color:#fff", blk, "he asked for the level in white and it is not white")


if __name__ == "__main__":
    unittest.main(verbosity=2)
