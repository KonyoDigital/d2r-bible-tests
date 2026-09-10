# -*- coding: utf-8 -*-
"""v2781 — THE PANEL PRINTED "read once" OVER A ROW THAT SAYS "only 0 independent witnesses".

The inbox row already carries the measurement. His eight pending rows, read out of his own board:

    Ars Tor'Baalos      only 1 independent witness (cross-reel)  — needs 2
    Chromatic Ire       only 1 independent witness (cross-frame) — needs 2
    Gheed's Wager       only 0 independent witnesses (none)      — needs 2
    Latent Bone Break   only 1 independent witness (cross-frame) — needs 2
    ... four more, all cross-frame, all 1

What the panel printed over every one of them:

    "a real chronicle item you do not have — read once, and one sighting is not two,
     so it needs your eye"

A fixed sentence. FALSE for Gheed's Wager, which has zero. And it throws away WHICH KIND of
witness was found — cross-reel vs cross-frame — which is the entire question of whether a second
sighting would be independent at all.

=== ⚠⚠ THE ENGINE'S OWN COMMENT PREDICTED THIS, ONE SURFACE OVER ===
`d2rInboxEngine` says, in as many words:

    "`code` stays null by default ON PURPOSE. Callers read `code || why`, so a default code would
     override the specific `why` of every branch that does not set one."

`roster-unconfirmed` is not a default — it is a real code — and it outranked `triageWhy` all the
same, in a caller three thousand lines from where that rule was written down. The rule was right
and the shape it warned about arrived anyway, wearing a non-default code.
[[unknown-stays-unknown]] [[label-outlived-referent]]

=== WHAT IS PINNED ===
The measured sentence wins where a row has one; the generic sentence is the FALLBACK for a row
nothing measured — never the other way round. The decision is SLICED FROM bible.html AND RUN IN
NODE, never grepped, because the thing under test is which of two strings a conditional picks.
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
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")

try:
    from console_safe import enable
    enable()
except Exception:
    pass

SRC = io.open(BIBLE, encoding="utf-8").read()


def _decision_block():
    """The three lines that choose between the measured why and the generic code. -> str"""
    # ⚠ ANCHOR ON THE STABLE PREFIX, NOT THE WHOLE LINE. The first cut anchored on the exact text
    # `String(x.triageWhy || x.gateWhy || '')` — which is one of the things a sabotage DELETES. The
    # slice then returned None and all six laws died in 0.010s instead of one failing in 0.2s: a
    # green-looking red that blames the fix for a broken instrument. The duration was the tell.
    # [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
    i = SRC.find("var _meas = String(")
    if i < 0:
        return None
    j = SRC.find("\n", SRC.find("var _raw =", i))
    return SRC[i:j] if j > i else None


HARNESS = """
const x = %(row)s;
const _live = %(live)s;
%(block)s
console.log(JSON.stringify({ raw: _raw }));
"""


def _run(row, live):
    blk = _decision_block()
    assert blk, "could not slice the why-decision out of bible.html"
    js = HARNESS % {"row": json.dumps(row), "live": json.dumps(live), "block": blk}
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, "t.js")
        io.open(p, "w", encoding="utf-8").write(js)
        out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=30)
        return json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
    finally:
        shutil.rmtree(d, True)


# His real rows, shape-for-shape, with the names kept because they are ROSTER items rather than
# anything personal — the roster ships in this repo already.
HIS = [
    {"name": "Ars Tor'Baalos", "triageWhy": "only 1 independent witness (cross-reel) — needs 2"},
    {"name": "Gheed's Wager", "triageWhy": "only 0 independent witnesses (none) — needs 2"},
    {"name": "Ormus' Robes", "triageWhy": "only 1 independent witness (cross-frame) — needs 2"},
]
UNCONFIRMED = {"code": "roster-unconfirmed", "verdict": "find"}


@unittest.skipIf(shutil.which("node") is None, "node is absent — UNMEASURED, not passing")
class ThePanelPrintsWhatTheRowMeasured(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_measured_row_prints_ITS_OWN_count(self):
        """★★ Every one of his pending rows carries a real count and a real witness KIND. The
        panel must print that, not a sentence written before the row existed."""
        for row in HIS:
            r = _run(row, UNCONFIRMED)
            self.assertEqual(r["raw"], row["triageWhy"],
                             "the panel discarded the row's own measurement for %r and fell back "
                             "to the generic code" % row["name"])

    def test_the_ZERO_row_no_longer_reads_as_ONE(self):
        """★★ THE ONE THAT IS FLATLY FALSE ON HIS SCREEN. Gheed's Wager has ZERO independent
        witnesses; the panel said "read once". A count that is wrong by one is still a number he
        would act on. [[zero-needs-a-denominator]]"""
        r = _run(HIS[1], UNCONFIRMED)
        self.assertIn("0 independent witnesses", r["raw"],
                      "a row with zero witnesses still reads as read-once")
        self.assertNotIn("read once", r["raw"])

    def test_the_witness_KIND_survives(self):
        """⚠ cross-reel and cross-frame are not the same evidence: two frames of one reel is a
        weaker claim than two reels. Collapsing them to "one sighting" loses the distinction that
        decides whether a second witness would be independent."""
        self.assertIn("cross-reel", _run(HIS[0], UNCONFIRMED)["raw"])
        self.assertIn("cross-frame", _run(HIS[2], UNCONFIRMED)["raw"])

    # ── ⛔ THE FALLBACKS, so this is a re-ordering and not a deletion ────────────────────────
    def test_an_UNMEASURED_row_still_gets_the_generic_code(self):
        """⛔ THE HALF THAT KEEPS IT HONEST. A row nothing measured must still say something, and
        that something is the code — which the humaniser then turns into the generic sentence. The
        fix REORDERS two sources; it must not delete one. [[unknown-stays-unknown]]"""
        r = _run({"name": "Something Unswept"}, UNCONFIRMED)
        self.assertEqual(r["raw"], "roster-unconfirmed",
                         "a row with no measurement lost its reason entirely")

    def test_a_NON_roster_code_still_outranks_the_row(self):
        """⛔ THE SCOPE. Only `roster-unconfirmed` defers to the measurement. A code like
        `misread-of:` or `reads-as-two:` is a statement about the NAME, not about the evidence
        count, and it must keep winning — those branches carry information `triageWhy` does not
        have. Widening the deferral to every code would silence them."""
        r = _run({"name": "Battlecage", "triageWhy": "only 1 independent witness (cross-reel)"},
                 {"code": "misread-of:Rattlecage", "verdict": "misread-open"})
        self.assertEqual(r["raw"], "misread-of:Rattlecage",
                         "a misread verdict was overridden by a witness count, so the panel now "
                         "explains the evidence for a name it believes was misread")

    def test_gateWhy_is_accepted_when_triageWhy_is_absent(self):
        """⚠ 108 of his 396 logged rows carry `gateWhy` and 28 carry `triageWhy`; the two sweeps
        do not agree on the key. Reading only one of them would have left most rows unmeasured.
        [[copy-drift]]"""
        r = _run({"name": "Razor's Edge",
                  "gateWhy": "only 0 independent witnesses (none) — needs 2"}, UNCONFIRMED)
        self.assertIn("0 independent witnesses", r["raw"])



RED_PROOF = [
    {
        'why': 'This is the whole fix in one expression: `roster-unconfirmed` is the ONLY code that defers to the row\'s own measurement, so `_raw` prints `only 0 independent witnesses (none) - needs 2` instead of the generic sentence. Kill the condition and `_raw` collapses to `(_code || _meas)` = the pre-fix behaviour, which is exactly the defect on his screen: the panel prints "read once" over Gheed\'s Wager, which has ZERO. The anchor is the live declaration inside the three lines the gate slices out of bible.html and runs in node - not a comment, not a message string, and not a shared constant read by both sides of an agreement (the bare string `roster-unconfirmed` occurs 4x in bible.html, but this composite anchor is unique at 1). Both slice anchors `var _meas = String(` and `var _raw =` survive the edit, so the instrument still parses instead of dying in 0.010s with all six laws blaming the fix for a broken slicer.  MEASURED: untampered Ran 6 tests in 0.215s -- OK. 0 skips: node present at /usr/local/bin/node, so the skipIf g; tampered (all 1) Ran 6 tests in 0.147s -- FAILED (failures=4): test_a_measured_row_prints_ITS_OWN_count, te; reddened law ThePanelPrintsWhatTheRowMeasured.test_a_measured_row_prints_ITS_OWN_co; ALONE python3 -m unittest test_the_panel_prints_what_the_row_measured.ThePanelPrintsWhatTheRowMeasured.test_a_measur.',
        'file': 'bible.html',
        'find': '/^roster-unconfirmed/.test(_code) && _meas',
        'replace': 'false && _meas',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
