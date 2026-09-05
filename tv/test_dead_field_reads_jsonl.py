#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE DETECTOR BUILT FOR THIS CLASS NEVER LOOKED HERE, AND COULD NOT HAVE READ IT IF IT HAD.

⚠⚠ WHAT HAPPENED. `histBytes` was null in **8,588 of 8,588 rows** of his disk series — present on
every row, filled on none — while `reels`, `eligibleMb` and `freeGb` beside it were populated on
all 8,588. `dead_field.py` exists for precisely that shape (*"a field that never once carried a
value is not a field, it is a typo with a comma after it"*) and reported **zero rows**, because its
`WATCHED` list held ONE store and never looked at this one.

⚠⚠ AND ADDING IT ALONE WOULD NOT HAVE WORKED. `_rows_of` read every store with
`json.loads(<the whole file>)`. `disk_history.jsonl` is JSONL — one object per line — so the parse
raises and the store comes back UNKNOWN. **It could have sat in the registry, appeared covered, and
said nothing** — a false green wearing a registry entry, which is worse than not being watched at
all. So the reader learned the format and the store was added in the same change.

MEASURED, driven on his real series:

    before the v2654 fix   ->  DEAD_FIELDS   dead=['histBytes']   judged=8589
    with ONE filled row    ->  OK            dead=[]

So it would have caught this, and it **self-clears** once the writer is fixed rather than nagging
about history for ever.

⚠ I FIRST CLAIMED THE OPPOSITE AND WAS WRONG. My own objection was that adding the store would
report the 8,588 old nulls as a live defect for ever. That is a misread of the rule: `dead_fields`
asks whether a column is filled on **NO** row, not whether it has nulls. Measured before believing
my own objection — which is the only reason the store got added at all.

⚠ IT REPORTS AND REFUSES NOTHING, exactly as before. Nothing here fails a build or blocks a button.

⚠ NOTHING HERE WRITES TO HIS STORES. Every fixture is a temp file; his series is read count-only.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import dead_field as DF  # noqa: E402


class TheReaderUnderstandsJSONL(unittest.TestCase):
    """★ Driven, not read. A reader that cannot parse a store makes WATCHING it meaningless."""

    def _write(self, name, text):
        """-> a path RELATIVE to the module, which is the only kind `_path_of` accepts.

        ⚠⚠ MY FIRST CUT HANDED IT ABSOLUTE TEMP PATHS AND ALL SEVEN CASES FAILED — correctly.
        REG-542 refuses an absolute literal because it would read a file outside this tree and
        report ITS rows as the store's. The module was right and the fixture was wrong, which is
        the usual way round: a sabotage that goes green is nearly always the sabotage's fault, and
        so is one that goes red for the wrong reason. Fixtures live under a `.scratch-` directory
        inside the tree, the same convention the store census already skips.
        [[sabotage-is-usually-the-wrong-one]]
        """
        d = tempfile.mkdtemp(prefix=".scratch-dfjsonl-", dir=HERE)
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, name)
        io.open(p, "w", encoding="utf-8").write(text)
        return os.path.relpath(p, HERE)

    def test_a_jsonl_store_yields_its_rows(self):
        p = self._write("s.jsonl", "\n".join(
            json.dumps({"at": i, "x": i, "dead": None}) for i in range(5)))
        rows, why = DF._rows_of(p, None)
        self.assertIsNotNone(rows, "a jsonl store read as UNKNOWN: %s" % why)
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["x"], 0)

    def test_blank_lines_are_not_rows(self):
        p = self._write("s.jsonl", '{"a":1}\n\n\n{"a":2}\n')
        rows, _ = DF._rows_of(p, None)
        self.assertEqual(len(rows), 2)

    def test_an_UNPARSEABLE_line_is_COUNTED_not_silently_dropped(self):
        """⚠ Silently shrinking the denominator is how the row floor stops meaning anything."""
        p = self._write("s.jsonl", '{"a":1}\n{not json\n{"a":2}\n')
        rows, why = DF._rows_of(p, None)
        self.assertEqual(len(rows), 2)
        self.assertIn("unparseable", why or "",
                      "a corrupt line vanished with nothing said about it")

    def test_a_file_where_NOTHING_parses_is_UNKNOWN_not_an_empty_store(self):
        """[[unknown-stays-unknown]] — an empty store licenses 'nothing is dead'."""
        p = self._write("s.jsonl", "not json\nalso not json\n")
        rows, why = DF._rows_of(p, None)
        self.assertIsNone(rows, "an unreadable store read as EMPTY, which is a clean bill")
        self.assertIn("none parsed", why or "")

    def test_a_jsonl_of_NON_OBJECTS_is_not_mistaken_for_rows(self):
        p = self._write("s.jsonl", "[1,2]\n3\n")
        rows, why = DF._rows_of(p, None)
        self.assertIsNone(rows, "a list-of-scalars file was read as rows")

    def test_the_PLAIN_JSON_path_is_UNCHANGED(self):
        """⚠⚠ THE BASELINE. The existing store must still read exactly as before — trading one
        blindness for another is not a fix."""
        p = self._write("s.json", json.dumps({"reels": [{"a": 1}, {"a": 2}]}))
        rows, why = DF._rows_of(p, "reels")
        self.assertIsNotNone(rows, "the json path broke: %s" % why)
        self.assertEqual(len(rows), 2)

    def test_a_json_file_holding_no_list_at_the_key_still_REFUSES(self):
        p = self._write("s.json", json.dumps({"reels": {"not": "a list"}}))
        rows, why = DF._rows_of(p, "reels")
        self.assertIsNone(rows)
        self.assertIn("holds no list", why or "")


class TheDiskStoreIsWATCHED(unittest.TestCase):

    def test_it_is_in_the_registry(self):
        names = [w[0] for w in DF.WATCHED]
        self.assertIn("disk_history", names,
                      "the store whose figure he acts on is not watched, which is how histBytes "
                      "stayed dead for 8,588 rows")

    def test_it_asks_the_OWNER_for_the_path(self):
        """⚠ REG-540's lesson: a hardcoded path watches a file the writes never reach."""
        entry = [w for w in DF.WATCHED if w[0] == "disk_history"][0]
        self.assertIsInstance(entry[1], tuple,
                              "the path is a literal, so it can drift from where the writer sends "
                              "its rows")
        self.assertEqual(entry[1][0], "control_app")

    def test_the_reel_tombstones_entry_is_UNTOUCHED(self):
        """⚠ Additive only. The store this module was built for keeps its exact entry."""
        entry = [w for w in DF.WATCHED if w[0] == "reel_tombstones"][0]
        self.assertEqual(entry[1], ("reel_retention", "_tombstone_path"))
        self.assertEqual(entry[2], "reels")


class ItWouldHaveCaughtItAndItSelfClears(unittest.TestCase):
    """★★ The claim this whole change rests on, driven rather than asserted."""

    def _rows(self, n=200, filled=0):
        rows = [{"at": i, "freeGb": 40.0, "reels": 40, "histBytes": None} for i in range(n)]
        for i in range(filled):
            rows[-(i + 1)]["histBytes"] = 5728790118
        return rows

    def test_a_column_filled_on_NO_row_reads_DEAD(self):
        r = DF.dead_fields(self._rows())
        self.assertEqual(r["state"], "DEAD_FIELDS")
        self.assertIn("histBytes", r["dead"])

    def test_ONE_filled_row_clears_it(self):
        """★ Why adding the store does not nag about history. My own objection said the opposite
        and was refuted by this measurement."""
        r = DF.dead_fields(self._rows(filled=1))
        self.assertEqual(r["state"], "OK")
        self.assertEqual(r["dead"], [])

    def test_a_young_store_is_UNKNOWN_and_not_clean(self):
        """⚠ A zero over rows that cannot disagree measures the sample."""
        r = DF.dead_fields(self._rows(n=5))
        self.assertEqual(r["state"], "UNKNOWN")

    def test_his_live_series_is_reachable_now(self):
        """Read-only. If this ever says UNKNOWN, the store is watched and saying nothing."""
        p = os.path.join(HERE, "disk_history.jsonl")
        if not os.path.exists(p):
            self.skipTest("no live disk history on this tree — not a pass")
        rows, why = DF._rows_of(("control_app", "_disk_history_path"), None)
        self.assertIsNotNone(rows, "the watched store cannot be read: %s" % why)
        self.assertGreater(len(rows), 100,
                           "only %d rows reached the detector" % len(rows or []))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
