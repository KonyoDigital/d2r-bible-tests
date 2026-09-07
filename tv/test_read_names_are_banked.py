# -*- coding: utf-8 -*-
"""v2751 — 119 ITEM NAMES WERE READ FROM HIS FOOTAGE AND NONE OF THEM ARE BANKED.

Konyo, 2026-09-07: *"the routing and funnel and main pipeline should still go through it regardless
of the paid reads.. i want it filtered and then stamped unified logic"*. Following that instruction
instead of the paid-read question is what found this.

MEASURED across all 40 reels — printer.stream() joined to reel_router.route():
    PRINTER  11 reels  64 names read, and the session carries NO SEAL AT ALL
    JOIN      4 reels  55 names read, sealed — and the seal does not carry them
    CAPTURE / EMPTY / STATION           0 names
The printer says it per reel, eleven times: *"23 item name(s) were read, but this session has no
seal at all, so the extraction contract was never even asked about it."*

⚠⚠ THE READING ALREADY HAPPENED. The names are in the JOURNAL RING right now, retrievable by
session id — Andariel's Visage, Atma's Wail, Bartuc's Cut-Throat, Arm of King Leoric, Blade of Ali
Baba, Sandstorm Trek, Tearhaunch. The pipeline is stalled AFTER the read, so no money is owed here.
That matters because the whole evening had been spent on the paid-read question: whether a re-read
would help (it would not, PROMPT_VER is unchanged), whether the vault lane could (its work list
never fires), whether to change that (a known-wrong move, caught twice). All true, all beside the
point.

⚠ HIS FILTER DECIDES WHICH NAMES COUNT, so the row reports PANEL separately. extract_gap's taxonomy
— written from his own words, *"if its a FLOOR ITEM with no stash/inventory open then obviously it
cant be in the same exact route"* — splits 472 corpus names PANEL 110 / FLOOR 208 / CHRONICLE 154,
77% filtered. A floor name has no cell to name, so it is a sighting and not a holding. One number
over both would overstate the work owed. [[unknown-stays-unknown]]

⛔ THE ROW REPORTS AND NEVER WRITES, and this file pins that. Banking means landing in
vault_accum/vault_seen, which is gated on witnesses deliberately and feeds a deleter with no
un-delete. Making the stall visible is the whole job here.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402


def _verdict(rows, stations, panel=110):
    """Force the row's verdict without touching his shelf."""
    import printer as P, reel_router as RR, extract_gap as EG
    rp, rr, ns = P.stream, RR.route, EG._named_sessions
    P.stream = lambda *a, **k: {"rows": rows}
    RR.route = lambda *a, **k: {"ok": True, "reels": stations}
    EG._named_sessions = lambda *a, **k: ({"s": {"panel": panel}}, "")
    try:
        return dict(D.CHECKS)["names banked"]()
    finally:
        P.stream, RR.route, EG._named_sessions = rp, rr, ns


def _row(reel, names, sealed):
    return {"reel": reel, "stations": {"extract": {"names": names, "sealed": sealed}}}


class ReadNamesAreBanked(unittest.TestCase):

    def test_the_row_is_REGISTERED(self):
        self.assertIn("names banked", dict(D.CHECKS),
                      "the names-banked row is not registered, so it never runs")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_names_read_with_NO_SEAL_are_reported(self):
        st, say = _verdict([_row("r1", 23, False), _row("r2", 6, False)],
                           [{"reel": "r1", "station": "PRINTER"}, {"reel": "r2", "station": "PRINTER"}])
        self.assertEqual(D.MISSING, st, "names read with no seal were graded as fine")
        self.assertIn("29 item name(s)", say)
        self.assertIn("NO SEAL", say)

    def test_a_seal_that_does_not_CARRY_the_names_is_counted_separately(self):
        """⚠ TWO DIFFERENT FAULTS. 'no seal at all' is a lane that never ran; 'sealed but the seal
        does not carry them' is a code problem. Collapsing them hides which work is owed."""
        st, say = _verdict([_row("r1", 10, False), _row("r2", 40, True)],
                           [{"reel": "r1", "station": "PRINTER"}, {"reel": "r2", "station": "JOIN"}])
        self.assertEqual(D.MISSING, st)
        self.assertIn("10 sit in sessions with NO SEAL", say)
        self.assertIn("40 are under a seal that does not carry them", say)

    def test_it_says_NO_PAID_READ_IS_OWED(self):
        """⚠ THE SENTENCE THAT REDIRECTS THE WORK. Without it a reader sees unbanked names and
        reaches for the paid lane — which is what the whole evening did before this was measured."""
        _, say = _verdict([_row("r1", 5, False)], [{"reel": "r1", "station": "PRINTER"}])
        self.assertIn("no paid read is owed", say)
        self.assertIn("journal ring", say)

    def test_the_PANEL_split_is_reported_not_collapsed(self):
        """His filter: a floor name has no cell to name. Reporting one total over PANEL and FLOOR
        would overstate what can become a holding."""
        _, say = _verdict([_row("r1", 5, False)], [{"reel": "r1", "station": "PRINTER"}], panel=110)
        self.assertIn("110", say, "the PANEL count is no longer reported")
        self.assertIn("container OPEN", say)

    def test_everything_banked_is_OK(self):
        """The other direction — a row that can only be red measures nothing."""
        st, _ = _verdict([_row("r1", 12, True)], [{"reel": "r1", "station": "ROUTED"}])
        self.assertEqual(D.OK, st, "a fully-banked shelf was still graded as stuck")

    def test_reels_with_NO_names_are_not_counted(self):
        """A reel the reader yielded nothing from owes no banking; counting it would inflate the
        figure with reels that have nothing to bank."""
        st, _ = _verdict([_row("r1", 0, False), _row("r2", None, False)],
                         [{"reel": "r1", "station": "CAPTURE"}, {"reel": "r2", "station": "EMPTY"}])
        self.assertEqual(D.OK, st, "reels with no names at all were counted as unbanked work")

    # ── UNKNOWN never collapses into OK ───────────────────────────────────────────────────────
    def test_an_unreadable_router_is_UNKNOWN(self):
        import reel_router as RR
        real = RR.route
        RR.route = lambda *a, **k: {"ok": False, "why": "simulated"}
        try:
            st, _ = dict(D.CHECKS)["names banked"]()
            self.assertEqual(D.UNKNOWN, st, "an unreadable router produced a measurement")
        finally:
            RR.route = real

    # ── ⛔ IT MUST NEVER WRITE ─────────────────────────────────────────────────────────────────
    def test_the_row_writes_nothing(self):
        """Banking lands in vault_accum/vault_seen, which is witness-gated on purpose and feeds a
        deleter with no un-delete. This row makes the stall visible; it must not bank anything."""
        # ⚠ STRIP THE DOCSTRING, NOT JUST THE COMMENTS. The row's own docstring EXPLAINS that
        # banking lands in vault_accum/vault_seen, so a text law looking for those names matches its
        # own prose and fails a row that writes nothing. Fifth time tonight a guard has been fooled
        # by the text it is written beside. [[measured-true-read-wrong]] [[source-reading-guard]]
        import ast as _ast
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        fn = [n for n in _ast.walk(_ast.parse(src))
              if isinstance(n, _ast.FunctionDef) and n.name == "_check_read_names_are_actually_banked"]
        self.assertTrue(fn, "the names-banked row is gone or renamed")
        body = _ast.get_source_segment(src, fn[0]) or ""
        doc = _ast.get_docstring(fn[0], clean=False)
        if doc:
            body = body.replace(doc, "")
        body = "\n".join(l.split("#")[0] for l in body.split("\n"))
        for bad in ("open(", "setItem", "vault_accum", "vault_seen", "json.dump", ".write("):
            self.assertNotIn(bad, body,
                             "the names-banked row appears to WRITE (%r). It reports; the witnessed "
                             "machinery banks." % bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
