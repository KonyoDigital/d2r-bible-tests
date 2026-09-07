# -*- coding: utf-8 -*-
"""v2762 — FOUR GRAIL ITEMS HAD NO PICTURE BECAUSE ONE FILE SPELLS THEM TWO WAYS.

MEASURED: `tv/unique_roster.json` holds four names with a CURLY apostrophe (U+2019) —
Atma’s Scarab, Saracen’s Chance, Seraph’s Hymn, The Cat’s Eye — while `bible.html` spells the same
four with a STRAIGHT one (U+0027) in `ITEM_VALUE` and in `D2IO_ART`. Same item, two spellings, in
ONE file. `artUrl()` matched exactly, so all four missed art that EXISTS under the other spelling.
The page's own prose already names them: "9 of 398 uniques did not resolve to 'unique'. FOUR of
them were this: Atma’s Scarab · Seraph’s Hymn · The Cat’s Eye · Saracen’s Chance".

Verified against the REAL resolver (D2IO_ART + _artTier + artUrl executed out of the shipped page):
    "Atma’s Scarab"    -> art/mr_atmasscarab.png
    "Saracen’s Chance" -> art/mr_saracenschance.png
    "Seraph’s Hymn"    -> art/mr_seraphshymn.png
    "The Cat’s Eye"    -> art/mr_thecatseye.png

=== WHY THE FOLD IS IN THE RESOLVER AND NOT THE ROSTER ===
`unique_roster.json` and `set_roster.json` SHARE one `sourceHash`. Changing those bytes invalidates
every machine's fleet mask until it republishes — `fleet_mask.decode()` refuses a mask whose
fingerprint does not match. A picture is not worth making the whole fleet undecodable, so the
cheap end is the lookup. [[copy-drift]]
⚠ AND IT IS A FALLBACK, NEVER A REWRITE: the caller's name is untouched, so nothing downstream
starts seeing a spelling it did not ask for.

=== ⚠⚠ THE ALIAS I ALMOST SHIPPED, AND WHY IT IS GONE ===
The task note said "The Scourge" missed because its art was "keyed as the bare Scourge
(hd_flail.png)", so I wrote a one-off alias {'The Scourge': 'Scourge'}. MEASURED against the real
table before shipping: NEITHER "Scourge" NOR "The Scourge" is an art key at all. The strings that
look like keys are a BASE CODE ("Scourge":"7fl", out of the lf-base-codes JSON) and a DESCRIPTION
("+200% ED · damage to demons"). The alias pointed at nothing — plumbing with no tap.

`Flail` -> art/base_flail.png DOES exist, so a base-type fallback was available. It is REFUSED:
`_itemArtPath`'s own rule is "NO ART FOR THIS ITEM -> NO PICTURE. Not a placeholder, not a fallback
glyph, not a guess." A stock flail under his grail item is exactly that guess.
[[unknown-stays-unknown]] [[plumbing-with-no-tap]]
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

CURLY = ["Atma’s Scarab", "Saracen’s Chance", "Seraph’s Hymn", "The Cat’s Eye"]


def _resolve(names):
    """Run the SHIPPED resolver in node and return {name: url|None}. -> dict|None (None = no node)

    ⚠ THE REAL FUNCTIONS, NOT A PYTHON RE-IMPLEMENTATION. A second copy of the matching rule would
    pass while the page still failed — the defect this file exists for was a MISMATCH between two
    spellings, and only the real lookup can prove it is gone.
    """
    i = BIBLE.find("const D2IO_ART = {")
    j = BIBLE.find("window.artUrl = artUrl;")
    if i < 0 or j < 0 or j < i:
        return None
    # ⚠ THE REGION ENDS WITH `window.D2IO_ART = D2IO_ART;` AND NODE HAS NO `window`. Without this
    # stub the probe exits 1 with "ReferenceError: window is not defined", `_resolve` returns None,
    # and THREE laws below skip — reporting nothing while looking like they ran. Measured: 3 of 7
    # skipped on the first cut. A skip is not a pass. [[feedback-blind-fixture-green-gate]]
    js = ("var window = {}; var globalThis = globalThis || {};\n" + BIBLE[i:j]
          + "\nconst _q=" + json.dumps(names) + ";"
          "\nconst out={};for(const n of _q){out[n]=artUrl(n)||null;}"
          "\nconsole.log(JSON.stringify(out));")
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "art_resolve_probe.js")
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


class TheArtResolverFoldsTheApostrophe(unittest.TestCase):

    def test_the_resolver_region_is_still_findable(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertIn("const D2IO_ART = {", BIBLE, "the art table moved or was renamed")
        self.assertIn("function artUrl(name){", BIBLE, "artUrl moved or was renamed")

    def test_the_roster_and_the_page_STILL_disagree(self):
        """⚠ THE FIXTURE ASSUMPTION, PINNED. If the two spellings are ever unified at the source,
        this fold becomes dead code and should be deleted rather than left as furniture — but that
        is a DIFFERENT change, and it must not happen silently."""
        ro = json.load(io.open(os.path.join(HERE, "unique_roster.json"), encoding="utf-8"))
        curly = [n for n in (ro.get("names") or []) if "’" in n]
        self.assertEqual(4, len(curly),
                         "the roster no longer holds exactly the four curly names this fold "
                         "exists for — it holds %d: %r" % (len(curly), curly))

    # ── ⚠⚠ THE LAW, AGAINST THE REAL RESOLVER ────────────────────────────────────────────────
    def test_all_four_curly_names_RESOLVE_to_art(self):
        got = _resolve(CURLY)
        if got is None:
            self.skipTest("node unavailable, so the shipped resolver could not be run — a skip is "
                          "NOT a pass and nothing here has been established")
        for n in CURLY:
            self.assertTrue(got.get(n),
                            "%r still resolves to NO art. The page spells it straight and the "
                            "roster spells it curly, so an exact match misses art that exists."
                            % n)

    def test_the_fold_did_not_break_a_straight_name(self):
        """The other direction: a name that already worked must keep working."""
        probe = ["Atma's Wail", "Stealskull", "Gull"]
        got = _resolve(probe)
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        for n in probe:
            self.assertTrue(got.get(n), "%r stopped resolving after the fold" % n)

    # ── ⚠ THE REFUSAL, PINNED SO IT IS NOT 'HELPFULLY' UNDONE ───────────────────────────────
    def test_The_Scourge_is_left_WITHOUT_art(self):
        """★ It has none, and the repo's rule is to show nothing rather than guess. A future pass
        that maps it to `Flail` would be showing a stock flail under his grail item."""
        got = _resolve(["The Scourge"])
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertIsNone(got.get("The Scourge"),
                          "The Scourge resolved to %r. Neither 'Scourge' nor 'The Scourge' is an "
                          "art key — if this now resolves, something mapped it to a BASE TYPE, "
                          "which _itemArtPath explicitly refuses: 'not a placeholder, not a "
                          "fallback glyph, not a guess'." % got.get("The Scourge"))

    def test_no_base_type_alias_was_smuggled_in(self):
        i = BIBLE.find("function artUrl(name){")
        j = BIBLE.find("window._artTier", i)
        blk = BIBLE[i:j]
        self.assertNotIn("'Scourge'", blk,
                         "a Scourge alias is back in artUrl. It points at a key that does not "
                         "exist, and the base-type art it would reach is a guess.")
        self.assertIn("u2019", blk.replace("\\u2019", "u2019"),
                      "the apostrophe fold is gone from artUrl")

    def test_it_is_a_FALLBACK_not_a_rewrite(self):
        """The caller's name must be untouched — nothing downstream should start seeing a spelling
        it did not ask for."""
        i = BIBLE.find("function artUrl(name){")
        j = BIBLE.find("window._artTier", i)
        blk = BIBLE[i:j]
        self.assertNotIn("name =", blk.replace("name ==", ""),
                         "artUrl reassigns its own `name` parameter, so the folded spelling can "
                         "escape into the caller")


if __name__ == "__main__":
    unittest.main(verbosity=2)
