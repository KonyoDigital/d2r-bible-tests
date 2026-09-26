#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3411 — TWO SEATS MUST NOT RENDER THE SAME LABEL, AND THE RULE HAS ONLY ONE MEANING.

His finding, carried since v3385: *"two grokbot account si see in fleet"*. Ambiguity must be
measured on the RENDERED LABEL, not on the nickname.

⚠⚠ THE FALSE OK IS REPRODUCED ON THE SHIPPED HELPER, NOT ARGUED. Running control_ui's own
`_fleetName` over a 5-row roster:
    nick='GrokBot' mach='vm-1'     -> 'GrokBot · vm-1'
    nick='GrokBot' mach='vm-1'     -> 'GrokBot · vm-1'   <- IDENTICAL
    nick=''        mach=''         -> '?'
    nick=''        mach=''         -> '?'                <- IDENTICAL
    nick='Konyo'   mach='konyo-3'  -> 'Konyo'
Two colliding labels. The OLD row counted shared non-empty NICKNAMES, found 'GrokBot', confirmed
control_ui carries the disambiguator, and answered OK — while both rows drew the same string. The
'?' pair it never looked at at all, because empty nicknames were skipped by construction.

⚠ NOT HYPOTHETICAL: his two GrokBot seats already share a nickname AND an install id; only
`machine` differs (grok-bot-vm-346371813 vs cursor). One rename and they are indistinguishable.

⚠⚠ AND THE FIX SHIPS A SECOND COPY OF A RULE THAT LIVES IN JAVASCRIPT, which is [[copy-drift]] by
construction. So the copies are PINNED TOGETHER here: `test_the_python_twin_agrees_with_the_SHIPPED_js`
extracts `_fleetName` from control_ui.html, runs it in node over a 9-roster table, and asserts
`console_doctor.fleet_label` agrees on every row of every roster. Without that join this file is
two rules wearing one name.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as CD  # noqa: E402

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

# The awkward ones on purpose: padded nickname, shared nick with one machine empty, two blanks,
# a solo row with no machine, and an EMPTY roster.
ROSTERS = [
    [{"nickname": "GrokBot", "machine": "vm-1"}, {"nickname": "GrokBot", "machine": "vm-1"}],
    [{"nickname": "GrokBot", "machine": "grok-bot-vm-346371813"},
     {"nickname": "GrokBot", "machine": "cursor"}],
    [{"nickname": "", "machine": ""}, {"nickname": "", "machine": ""}],
    [{"nickname": "  Dean  ", "machine": "LAPTOP-QNFL860M"}, {"nickname": "Dean", "machine": "other"}],
    [{"nickname": "Konyo", "machine": "konyo-3"}, {"nickname": "Dean", "machine": "laptop"}],
    [{"nickname": "Solo", "machine": ""}],
    [{"nickname": "Twin", "machine": ""}, {"nickname": "Twin", "machine": ""}],
    [{"nickname": "Twin", "machine": "a"}, {"nickname": "Twin", "machine": ""}],
    [],
]


def _node():
    return shutil.which("node") or shutil.which("nodejs")


def _js_labels(roster):
    """Run the SHIPPED _fleetName over one roster in node. -> [label] or None when node is absent."""
    m = re.search(r"var _fleetName = function \(m, rows\) \{.*?\n  \};", UI, re.S)
    if not m:
        return "NO_RULE"
    src = m.group(0)
    prog = ("%s\nconst rows = %s;\nconsole.log(JSON.stringify(rows.map(function(r){"
            "return _fleetName(r, rows);})));\n" % (src, json.dumps(roster)))
    p = subprocess.run([_node(), "-"], input=prog, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise AssertionError("node could not run the shipped rule: %s" % (p.stderr or "")[:200])
    return json.loads(p.stdout.strip())


class TestThePythonTwinAgreesWithTheShippedJs(unittest.TestCase):
    """⚠ THE JOIN. Without it, this file is two rules wearing one name. [[copy-drift]]"""

    def test_the_python_twin_agrees_with_the_SHIPPED_js(self):
        self.assertIn("var _fleetName = function (m, rows) {", UI,
                      "control_ui no longer carries _fleetName, so the label rule this row "
                      "measures is not the one his screen uses")
        if not _node():
            self.skipTest("no node on this machine — the JS side cannot be executed, so "
                          "agreement is UNKNOWN rather than proven")
        agree = differ = 0
        for i, roster in enumerate(ROSTERS):
            js = _js_labels(roster)
            self.assertNotEqual(js, "NO_RULE", "the _fleetName rule could not be extracted")
            py = [CD.fleet_label(r, roster) for r in roster]
            if js == py:
                agree += 1
            else:
                differ += 1
                self.fail("roster %d: the shipped JS renders %r and the python twin says %r — "
                          "two rules wearing one name" % (i, js, py))
        print("rosters: %d  AGREE: %d  DIFFER: %d" % (len(ROSTERS), agree, differ))


class TestTwoSeatsCannotRenderTheSameLabel(unittest.TestCase):

    def _collisions(self, roster):
        seen = {}
        for r in roster:
            seen.setdefault(CD.fleet_label(r, roster), []).append(r)
        return sorted(k for k, v in seen.items() if len(v) > 1)

    def test_a_shared_nickname_AND_machine_is_a_collision(self):
        """The case the old row answered OK on."""
        self.assertEqual(self._collisions(ROSTERS[0]), ["GrokBot · vm-1"],
                         "two seats rendering the identical string were not reported")

    def test_two_BLANK_rows_collide_on_the_question_mark(self):
        """⚠ The old row skipped empty nicknames by construction and never looked at these."""
        self.assertEqual(self._collisions(ROSTERS[2]), ["?"],
                         "two unnamed seats both render '?' and that was invisible")

    def test_two_shared_nicknames_with_NO_machine_collide(self):
        self.assertEqual(self._collisions(ROSTERS[6]), ["Twin"],
                         "the disambiguator needs a machine; without one the rows are identical")

    def test_BASELINE_his_REAL_pair_is_NOT_flagged(self):
        """⚠ vm-346371813 vs cursor. A fix that called everything ambiguous would pass every
        case above and be useless — this is what stops it."""
        self.assertEqual(self._collisions(ROSTERS[1]), [],
                         "his two GrokBot seats ARE distinguishable (the machine differs) and "
                         "were wrongly reported as ambiguous")

    def test_BASELINE_distinct_names_are_NOT_flagged(self):
        self.assertEqual(self._collisions(ROSTERS[4]), [])

    def test_BASELINE_a_solo_row_is_never_ambiguous(self):
        self.assertEqual(self._collisions(ROSTERS[5]), [])

    def test_an_EMPTY_roster_is_not_a_collision(self):
        self.assertEqual(self._collisions(ROSTERS[8]), [])

    def test_a_padded_nickname_is_the_SAME_nickname(self):
        """'  Dean  ' and 'Dean' are one name with one rendering, so they collide."""
        self.assertEqual(self._collisions(ROSTERS[3]), [],
                         "these two carry DIFFERENT machines, so the rule disambiguates them")
        labels = [CD.fleet_label(r, ROSTERS[3]) for r in ROSTERS[3]]
        self.assertEqual(labels, ["Dean · LAPTOP-QNFL860M", "Dean · other"],
                         "whitespace was not trimmed the way the shipped rule trims it")

    def _drive_row(self, roster):
        """Run the REAL heart row over a stubbed roster. -> (state, why).

        ⚠⚠ ADDED AFTER heart2 CALLED THIS GATE BLIND. Every case above measures `fleet_label`
        directly and never touches the row, so flipping the row's own verdict from MISSING to OK
        — the exact false OK this version exists to kill — changed nothing and the sabotage
        `stayed GREEN through its own defeat (1 match)`. The match count was 1, so the sabotage
        was sound and the LAW was weak. A law about what a ROW REPORTS has to drive the row.
        [[regression-guard]] §5a
        """
        import control_app as _ca
        keep = getattr(_ca, "_FLEET_PRESENCE_CACHE", None)
        _ca._FLEET_PRESENCE_CACHE = {"d": {"online": list(roster), "offline": []}}
        try:
            return CD._check_a_fleet_row_identifies_its_machine()
        finally:
            if keep is None:
                try:
                    del _ca._FLEET_PRESENCE_CACHE
                except Exception:
                    pass
            else:
                _ca._FLEET_PRESENCE_CACHE = keep

    def test_THE_ROW_answers_MISSING_when_two_seats_render_the_same_label(self):
        st, why = self._drive_row(ROSTERS[0])
        self.assertEqual(st, CD.MISSING,
                         "the row answered %r on a roster where two seats draw the identical "
                         "string — that is the false OK this version exists to kill" % st)
        self.assertIn("INDISTINGUISHABLE", why)
        self.assertIn("GrokBot", why, "the refusal must NAME the pair, not just count it")

    def test_THE_ROW_answers_MISSING_on_two_blank_rows(self):
        st, why = self._drive_row(ROSTERS[2])
        self.assertEqual(st, CD.MISSING,
                         "two unnamed seats both render '?' and the row called it %r" % st)

    def test_BASELINE_THE_ROW_answers_OK_on_his_REAL_pair(self):
        """⚠ Without this a row hardwired to MISSING would pass both cases above."""
        st, why = self._drive_row(ROSTERS[1])
        self.assertEqual(st, CD.OK,
                         "his two GrokBot seats differ by machine and ARE distinguishable; the "
                         "row answered %r — a guard that accuses everything is silenced" % st)

    def test_the_row_itself_reports_MISSING_on_a_colliding_roster(self):
        """The row must SAY it, not just compute it."""
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        i = src.find("def _check_a_fleet_row_identifies_its_machine(")
        self.assertGreater(i, -1)
        blk = src[i:src.find("\ndef ", i + 1)]
        self.assertIn("fleet_label(r, rows)", blk,
                      "the row no longer measures the RENDERED label")
        self.assertIn("INDISTINGUISHABLE", blk,
                      "a colliding roster must be reported as indistinguishable ON HIS SCREEN, "
                      "not as a nickname statistic")


RED_PROOF = [
    {
        "why": "v3411 — THE FALSE OK, RESTORED. Answering OK on a colliding roster is exactly the "
               "old behaviour: it found the disambiguator in control_ui and called the pair fine "
               "while both rows drew 'GrokBot · vm-1'. The row must report what his SCREEN shows, "
               "not what the source is capable of.",
        "file": "console_doctor.py",
        "find": '    return MISSING, ("%d rendered label(s) are drawn by more than one seat',
        "replace": '    return OK, ("%d rendered label(s) are drawn by more than one seat',
        "matches": 1,
    },
    {
        "why": "v3411 — EMPTY NICKNAMES SKIPPED, which is how the old row never saw the '?' pair. "
               "Giving each unnamed row a unique label hides two seats that draw the identical "
               "string on his screen.",
        "file": "console_doctor.py",
        "find": '    if not nick:\n        return mach or "?"',
        "replace": '    if not nick:\n        return mach or ("?%d" % id(m))',
        "matches": 1,
    },
    {
        "why": "v3411 — THE DISAMBIGUATOR DROPPED. Returning the bare nickname makes his REAL "
               "pair (vm-346371813 vs cursor) collide, so the BASELINE case reds — which is what "
               "proves these cases can tell a genuine collision from a distinguishable one, "
               "rather than calling everything ambiguous.",
        "file": "console_doctor.py",
        "find": '    return (nick + " \\u00b7 " + mach) if (seen > 1 and mach) else nick',
        "replace": '    return nick',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
