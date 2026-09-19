# -*- coding: utf-8 -*-
"""v3374 (#28/#121) — A TALLY CANNOT BE ASKED *WHICH*, AND HIS RULING NEEDED THE NAMES.

His #28 ruling: *"WIDEN THE LAW so panel-sourced names auto-bank (the 96)"*. The heart row reported
the 96 faithfully for versions. Nothing could act on it, because `_named_sessions()` classified
EVERY NAME as panel/floor/chronicle and then kept only the COUNTS:

    for _nm in names:
        ...
        cur["panel"] += 1        # his, in hand — stashing or pre-stash
        cur["floor"] += 1
        cur["chronicle"] += 1

The verdict was computed per name and dropped at the aggregation, so "96" could be reported and
never addressed — a widening has nothing to widen ONTO while the population is a number.
[[heart-first]] §6 — persist what you KNEW, not a summary of it.

⚠ THIS LANE WAS ALREADY BITTEN BY THE COARSER VERSION. v3043's own comment in that function:
"`cur['panel'] += len(names)` WAS THE WHOLE DEFECT. One frame carries stash and inventory together
... 11 names that can NEVER be a holding were counted as panel." It was fixed from per-FRAME to
per-NAME — and still only the tally survived.

=== WHAT THE LIST SHOWED THE MOMENT IT EXISTED, AND IT RESIZED THE RULING ===
96 sightings are 26 DISTINCT names. Against his own rosters (uniques 398 · runewords 105 · set
pieces 135 · set names 34), exactly 10 resolve:
    SET      Laying of Hands · Credendum · Dark Adherent · Rite of Passage · Telling of Beads
    SET NAME The Disciple      <- a set's NAME, not an item; arguably 9 bankable, not 10
    UNIQUE   War Traveler · Dwarf Star · Magefist · Hellfire Torch
The other 86 sightings are Horadric Cube x31, Tome of Town Portal x18, Tome of Identify x18,
potions, charms, and bare bases. Taken literally, "auto-bank the 96" writes 31 Horadric Cubes into
his ownership records.

⚠ A LIST OF PAIRS, NOT A DICT. One session can read the same name twice — the Horadric Cube is
seen 31 times — and a dict keyed by name would fold sightings into one, quietly disagreeing with
the count it sits beside. [[one-to-one-store-for-a-one-to-many-fact]]

⛔ NOTHING HERE WRITES TO HIS OWNERSHIP RECORDS. This persists a verdict the function already
reached. Banking stays gated on witnesses, the door still re-gates every row, and his fences hold:
39 rares manual, floor sightings never become cells.
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

import extract_gap as EG  # noqa: E402

COUNTERS = ("panel", "floor", "chronicle", "equipped", "contradicted", "unplaced")


def _fn_source():
    with io.open(os.path.join(HERE, "extract_gap.py"), encoding="utf-8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_named_sessions":
            return ast.get_source_segment(src, node) or ""
    return ""


class TestATallyCannotBeAskedWhich(unittest.TestCase):

    def test_every_branch_that_counts_also_records_which(self):
        """⚠ THE LOAD-BEARING CASE, AND IT IS VENUE-INDEPENDENT.

        Parsed, not grepped: a comment mentioning `cur["panel"]` must not satisfy it, and a string
        constant is not a subscript. [[source-reading-guard]] §1

        Counts every `cur[<counter>] += 1` and every `cur["placed"].append(...)` in the function.
        A counter incremented without a matching record is a verdict computed and thrown away —
        the exact defect this version exists to remove.
        """
        src = _fn_source()
        self.assertTrue(src, "_named_sessions could not be located — the law cannot reach its "
                             "subject, which is a failure of the law, not a pass")
        tree = ast.parse("if 1:\n" + "\n".join("    " + l for l in src.split("\n")))
        incs = appends = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Subscript):
                sl = node.target.slice
                key = getattr(sl, "value", None)
                if isinstance(key, str) and key in COUNTERS:
                    incs += 1
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "append"
                    and isinstance(node.func.value, ast.Subscript)):
                k = getattr(node.func.value.slice, "value", None)
                if k == "placed":
                    appends += 1
        self.assertGreater(incs, 0, "no counter increments found — the parse missed the subject")
        self.assertEqual(
            appends, incs,
            "%d counter increment(s) but only %d placed-record(s): a name is being classified and "
            "its verdict discarded, so the population stays a number nobody can act on"
            % (incs, appends))

    def test_the_record_is_a_list_so_a_repeat_is_not_folded(self):
        """The Horadric Cube is seen 31 times. A dict keyed by name would report it once."""
        src = _fn_source()
        self.assertIn('cur.setdefault("placed", [])', src,
                      "`placed` must be seeded as a LIST; a dict folds repeat sightings and would "
                      "then disagree with the count beside it")

    def test_the_existing_counts_are_untouched(self):
        """Callers ask for .get('panel') and must keep getting it — this version is additive."""
        src = _fn_source()
        for k in COUNTERS:
            self.assertIn('cur["%s"]' % k, src, "counter %r vanished; callers read these" % k)

    def test_the_list_reconciles_with_every_count_on_his_journal(self):
        """Behavioural, and it SKIPS HONESTLY off his machine rather than passing vacuously."""
        named, _why = EG._named_sessions()
        if not named:
            self.skipTest("no journal ring on this venue — reconciliation UNMEASURED here, not "
                          "clean; the structural case above is what CI enforces")
        mism = []
        for sid, v in named.items():
            placed = v.get("placed")
            self.assertIsInstance(placed, list, "%s carries no placed list" % sid)
            for k in COUNTERS:
                got = sum(1 for _n, t in placed if t == k)
                if got != int(v.get(k) or 0):
                    mism.append((sid, k, int(v.get(k) or 0), got))
        self.assertEqual(mism, [], "the list and the counts disagree: %s" % mism[:4])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a counter incremented without recording WHICH name leaves the population a number nobody can act on",
        "file": "tv/extract_gap.py",
        "find": '                            cur["panel"] += 1          # his, in hand — stashing or pre-stash\n                            cur["placed"].append((_nm, "panel"))',
        "replace": '                            cur["panel"] += 1          # his, in hand — stashing or pre-stash',
        "matches": 1,
    },
    {
        "why": "a dict keyed by name folds 31 Horadric Cube sightings into one and then disagrees with the count beside it",
        "find": '                    cur.setdefault("placed", [])',
        "file": "tv/extract_gap.py",
        "replace": '                    cur.setdefault("placed", {})',
        "matches": 1,
    },
]
