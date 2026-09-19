# -*- coding: utf-8 -*-
"""v3365 (#24) — THE RECORDER KEEPS ITS OWN EVIDENCE, AND IT KEEPS IT *BEFORE* IT DESTROYS IT.

#24 has sat unactionable across 27 events because every row it produced says the same unusable
sentence: "the stage was open for 12s and had nothing on it". That records THAT nothing was there.
It never records WHAT was there — and that single fact is the only thing separating the two live
candidates: a stage that never painted, versus a stage that painted where nobody looked.

MEASURED 2026-09-19 on his real tv/ui_faults.jsonl:
    rows                                    200
    rows carrying a `before` snapshot         8   (4%)
    ui_fault_record call sites                11
    call sites that pass `before`              1

⚠⚠ AND IT WAS A THREE-LINK CHAIN WITH THE MIDDLE AND FAR END BOTH CUT:
    ui_fault_record(..., before=None)  ->  STORES it, since CF-4, whose own comment reads
                                           "the reload destroys the only evidence"
    the /api/ui_fault route            ->  called it with (kind, why, where) and DROPPED before
    the JS self-heal                   ->  closed the stage FIRST, then reported
So the storage end has been built and waiting, while neither end that could fill it did.
[[the-unjoined-end]] — third instance of this exact shape in one day.

=== THE ORDER IS THE WHOLE FIX, AND IT IS WHY THIS FILE EXISTS ===
`document.body.classList.remove('theatre-open')` and `th.hidden = true` destroy the measurement.
A snapshot taken AFTER them is not a smaller snapshot — it is a snapshot OF THE DESTRUCTION, and it
would look completely correct in review: same fields, same shape, same code, all zeroes forever. A
law that only checked "is `before` sent" would pass over that. So the order is pinned by position.

⚠ THE MEASUREMENT MUST NEVER BREAK THE SELF-HEAL. It is wrapped, and a failure records
`{measureFailed: ...}` rather than throwing — a stuck black stage that cannot close itself is a
worse bug than the one being fixed. [[unknown-stays-unknown]]
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = os.path.join(HERE, "control_ui.html")
APP = os.path.join(HERE, "control_app.py")


def _ui():
    return io.open(UI, encoding="utf-8").read()


def _app_code():
    src = io.open(APP, encoding="utf-8").read()
    return "\n".join(l.split("#", 1)[0] for l in src.split("\n"))


class TheRouteStopsDroppingIt(unittest.TestCase):

    def test_the_route_forwards_the_snapshot(self):
        code = _app_code()
        self.assertIn(
            'before=(body or {}).get("before")', code,
            "/api/ui_fault calls ui_fault_record without forwarding `before`. The recorder has "
            "accepted and stored it since CF-4; dropping it at the door means the far end can "
            "send evidence and the row will still be blank.")

    def test_the_recorder_still_stores_a_dict_and_refuses_junk(self):
        import control_app as CA
        p = os.path.join(tempfile.mkdtemp(), "faults.jsonl")
        CA.ui_fault_record("t", why="w", where="x", path=p, before={"cards": 0, "scrollH": 900})
        CA.ui_fault_record("t", why="w", where="x", path=p, before="not a dict")
        rows = []
        for ln in io.open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln.startswith("{"):
                rows.append(json.loads(ln))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].get("before", {}).get("scrollH"), 900,
                         "a dict snapshot was not stored")
        self.assertIsNone(rows[1].get("before"),
                          "a non-dict was stored as a snapshot — a string cannot answer 'how many "
                          "cards were there', so accepting one manufactures unusable evidence")


class TheMeasurementHappensBeforeTheDestruction(unittest.TestCase):
    """⚠⚠ THE CASE. Everything else can be right and this still be worthless."""

    def test_the_snapshot_is_taken_BEFORE_the_stage_is_closed(self):
        ui = _ui()
        # ⚠ BOUND THE BLOCK FIRST. Searching for the destructive lines FROM the measurement can
        # only ever find ones that come after it, so it could not see a hide inserted ABOVE —
        # which is exactly the sabotage. Bound the self-heal block, then compare inside it.
        start = ui.find("if (window._thEmptyFor >= 4)")
        self.assertGreater(start, -1, "the self-heal block is gone")
        end = ui.find("}, 3000);", start)
        self.assertGreater(end, start, "could not bound the self-heal block; refusing to judge a "
                                       "slice whose far end is a guess")
        blk = ui[start:end]
        i_measure = blk.find("var _before = null;")
        i_hide = blk.find("th.hidden = true;")
        i_class = blk.find("document.body.classList.remove('theatre-open');")
        self.assertGreater(i_measure, -1,
                           "the pre-close snapshot is gone from the self-heal entirely")
        self.assertGreater(i_hide, -1, "the self-heal no longer hides the stage")
        self.assertGreater(
            i_hide, i_measure,
            "`th.hidden = true` runs BEFORE the snapshot (hide at %d, measure at %d within the "
            "block). The measurement would then describe the DESTRUCTION rather than the fault — "
            "all zeroes, forever, and it would look entirely correct in review."
            % (i_hide, i_measure))
        self.assertGreater(
            i_class, i_measure,
            "the theatre-open class is removed before the snapshot, so the layout being measured "
            "is already the closed one")

    def test_it_measures_the_things_that_DISCRIMINATE(self):
        """A snapshot that cannot separate the two candidates is decoration.

        ⚠⚠ THIS CASE WENT BLIND ON ITS FIRST PROOF, AT MATCH COUNT 1 — so the law was weak, not
        the sabotage. It did `assertIn("cards", seg)`, and the sabotage renamed the key to
        `cardsOmitted:` — which still CONTAINS "cards". The needle was a substring of the broken
        form, which is the trap [[source-reading-guard]] §4c names verbatim. It now compares
        PARSED KEYS as a set, so a rename is a different key rather than a longer one.

        ⚠ And the window is bounded by the object literal's own braces rather than by a byte
        count; a fixed slice here would drift the first time anyone adds a field. §3
        """
        import re
        ui = _ui()
        i = ui.find("_before = {")
        self.assertGreater(i, -1, "the snapshot object literal is gone")
        j = ui.find("};", i)
        self.assertGreater(j, i, "could not bound the snapshot literal; refusing to judge a slice "
                                 "whose far end is a guess")
        seg = ui[i:j]
        # ⚠ KEYS ANCHOR TO `{` OR `,`, NOT TO LINE START. The first cut used `(?m)^\s*(\w+)\s*:`
        # and missed every SECOND key on a line — `clientH`, `thH`, `scrollY`, `loaded` — so the
        # case went red against correct code. `[{,]` also excludes the `:` of a ternary, which a
        # bare `(\w+)\s*:` would have swallowed as a key called `length`.
        keys = set(re.findall(r"[{,]\s*(\w+)\s*:", seg))
        for k in ("cards", "scrollH", "clientH", "innerH", "sessions"):
            self.assertIn(
                k, keys,
                "the snapshot does not record %r — it records %s. cards>0 with scrollH>>clientH "
                "is 'painted off-screen'; cards==0 is 'never painted'. Without both, the row "
                "still cannot tell the two apart, which is the entire reason #24 stalled."
                % (k, sorted(keys)))

    def test_a_failed_measurement_never_blocks_the_self_heal(self):
        ui = _ui()
        i = ui.find("var _before = null;")
        seg = ui[i:i + 1400]
        self.assertIn("measureFailed", seg,
                      "a measurement failure is not recorded as UNKNOWN — it either throws or "
                      "vanishes, and a throw here leaves his stage stuck black")
        self.assertIn("catch", seg,
                      "the snapshot is not wrapped; an exception would stop the stage closing "
                      "itself, which is worse than the fault being fixed")

    def test_the_payload_actually_carries_it(self):
        ui = _ui()
        i = ui.find("kind:'theatre-stuck-black'")
        self.assertGreater(i, -1, "the self-heal no longer reports at all")
        seg = ui[i:i + 800]
        self.assertIn("before: _before", seg,
                      "the snapshot is measured and never sent — computed, held, dropped before "
                      "the wire. [[the-unjoined-end]]")


class HisRealLedgerOnlyGetsBetter(unittest.TestCase):

    def test_the_share_of_rows_with_evidence_may_only_RISE(self):
        """A ratchet, not a bar: 8 of 200 today. It must never fall."""
        p = os.path.join(os.path.dirname(HERE), "tv", "ui_faults.jsonl")
        p = p if os.path.exists(p) else os.path.join(HERE, "ui_faults.jsonl")
        if not os.path.exists(p):
            self.skipTest("no fault ledger on this machine")
        rows = []
        for ln in io.open(p, encoding="utf-8"):
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
        if len(rows) < 20:
            self.skipTest("only %d rows; too few to ratchet" % len(rows))
        have = [r for r in rows if isinstance(r.get("before"), dict)]
        # ⚠ THE DENOMINATOR TRAVELS. 8/200 measured the day this shipped.
        self.assertGreaterEqual(
            len(have), 8,
            "rows carrying evidence fell to %d of %d (was 8 of 200 when this law was written). "
            "Evidence already banked cannot un-happen, so a fall means a writer stopped passing "
            "it. [[zero-needs-a-denominator]]" % (len(have), len(rows)))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping before at the route puts every console-reported fault back to blank",
        "file": "tv/control_app.py",
        "find": '                                   before=(body or {}).get("before"))',
        "replace": "                                   )",
        "matches": 1,
    },
    {
        # ⚠ THIS SABOTAGE MUST ACTUALLY MOVE THE ORDER, NOT EDIT A COMMENT. The first cut replaced
        # the line with itself plus `/* moved */`, which changes no behaviour at all - an INERT
        # sabotage, and the case would have read BLIND while being perfectly sound.
        # [[regression-guard]] 5a
        "why": "hiding the stage BEFORE the snapshot makes the measurement describe the destruction",
        "file": "tv/control_ui.html",
        "find": "          var _before = null;",
        "replace": "          th.hidden = true;\n          var _before = null;",
        "matches": 1,
    },
    {
        "why": "not sending it leaves the snapshot computed, held and dropped before the wire",
        "file": "tv/control_ui.html",
        "find": "                before: _before,\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a snapshot that omits the card count cannot separate never-painted from off-screen",
        "file": "tv/control_ui.html",
        "find": "              cards: _cards ? _cards.length : null,",
        "replace": "              cardsOmitted: true,",
        "matches": 1,
    },
]
