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


class TheIntersectionRuleHadABlindSpot(unittest.TestCase):
    """★★ RANKED FIRST BY A COLD READ OF THE SHIPPED v2655 BYTES, and reproduced before believing.

    `on_every` is the INTERSECTION of keys across all rows, so **a field absent from even ONE row
    is never considered for deadness again**. Measured: 200 rows carrying `a=None` report
    `dead=['a']`; make one row lack the key and it reports `dead=[]`.

    ⚠⚠ AND IT IS LIVE ON HIS STORE. `prunedWhy` was added in v2646, so it sits on **18 of 8,595
    rows** and can never be judged — which also made the declared-null entry written for it inert.
    A store that GAINS fields over time is exactly the shape the rule cannot see, and this store
    gains fields.

    ⚠ THE ORIGINAL RULE IS KEPT, because its reason is sound: presence on EVERY row is the evidence
    that a field is meant to be there. What is added is the class it was blind to, reported
    SEPARATELY — "never fills a field it always writes" and "never fills a field it recently
    started writing" are different facts, and only the first is the typo-with-a-comma case.
    """

    def test_a_field_on_every_row_is_still_DEAD(self):
        """⚠ THE BASELINE. The rule this file is about must not be weakened by the addition."""
        r = DF.dead_fields([{"a": None, "b": 1} for _ in range(200)])
        self.assertEqual(r["dead"], ["a"])

    def test_ONE_missing_key_no_longer_hides_it(self):
        rows = [{"a": None, "b": 1} for _ in range(200)]
        rows[0] = {"b": 1}
        r = DF.dead_fields(rows)
        self.assertEqual(r["dead"], [], "the intersection rule's meaning changed")
        self.assertIn("a", r["unfilledWherePresent"],
                      "a column absent from one row of 200 is invisible again")

    def test_it_is_reported_SEPARATELY_and_not_folded_into_dead(self):
        """⚠ Folding them would make a young field block a push the way a dead one does."""
        rows = [{"a": None, "b": 1} for _ in range(200)]
        rows[0] = {"b": 1}
        r = DF.dead_fields(rows)
        self.assertEqual(r["state"], "OK",
                         "a field the intersection cannot judge now blocks like a dead one")
        self.assertIn("intersection rule cannot judge", r["why"])

    def test_a_field_on_TOO_FEW_rows_is_not_judged_at_all(self):
        """⚠ Under the floor it is a young field, and a zero over rows that cannot disagree
        measures the sample. [[unknown-stays-unknown]]"""
        rows = [{"b": 1} for _ in range(200)] + [{"b": 1, "c": None} for _ in range(5)]
        r = DF.dead_fields(rows)
        self.assertNotIn("c", r["unfilledWherePresent"])
        self.assertNotIn("c", r["dead"])

    def test_a_DECLARED_field_is_excused_in_the_new_class_too(self):
        """⚠ Otherwise the declaration works for one rule and not the other, which is the
        copy-drift shape inside one function."""
        rows = [{"a": None, "b": 1} for _ in range(200)]
        rows[0] = {"b": 1}
        r = DF.dead_fields(rows, declared_null={"a": "deliberately never filled, for a reason"})
        self.assertEqual(r["unfilledWherePresent"], [])
        self.assertIn("a", r["declaredNull"])


class AVerdictOverAMinorityIsNotAVerdict(unittest.TestCase):
    """★★ ALSO FROM THE COLD READ: *"8500 lines that are not objects, 40 valid dict rows at the end
    — returns DEAD_FIELDS plus skipped: 8500. The gate will still block based on the 40 rows."*

    ⚠ The count was ALREADY returned, and the comment beside the JSONL reader claims that counting
    is what stops the denominator being silently shrunk. Nothing READ the count, so the claim was
    larger than the code. **Counting only helps if something acts on the count.**
    """

    def test_a_MINORITY_of_readable_rows_yields_UNKNOWN(self):
        r = DF.dead_fields([{"x": 1, "dead": None} for _ in range(40)] + [None] * 8500)
        self.assertEqual(r["state"], "UNKNOWN",
                         "a verdict was drawn from 40 rows of an 8,540-row file")
        self.assertIn("MINORITY", r["why"])

    def test_a_FEW_bad_lines_do_NOT_silence_it(self):
        """⚠⚠ THE BASELINE, and it is the half that matters. A rule that goes UNKNOWN on any
        corruption is a detector that never reports anything — trading a false green for silence."""
        r = DF.dead_fields([{"x": 1, "dead": None} for _ in range(200)] + [None] * 5)
        self.assertEqual(r["state"], "DEAD_FIELDS")
        self.assertEqual(r["dead"], ["dead"])

    def test_the_UNKNOWN_carries_both_counts_so_it_can_be_checked(self):
        r = DF.dead_fields([{"x": 1} for _ in range(40)] + [None] * 8500)
        self.assertEqual(r["judged"], 40)
        self.assertEqual(r["skipped"], 8500)


class ADeliberateNullIsNotADeadField(unittest.TestCase):
    """★★ A DATED FALSE RED, DEFUSED BEFORE THE DATE ARRIVED.

    `disk_history.prunedMb` is null ON PURPOSE — the prune is OFF, so nobody measured a freed
    figure, and `0` would claim a measurement nobody took. Today its column is filled by 8,270 rows
    written before 2026-09-02, so it reads fine. **The store's own 14-day trim removes the last of
    those on 2026-09-16**, after which the column is filled on NO row and this detector reads
    DEAD_FIELDS — on a healthy tree, on a gate in the PRE-PUSH set, where a push publishes the live
    site. Found by an adversarial review of the shipped bytes, 11.6 days before it would have fired.

    **"Deliberately not measured" and "a typo with a comma after it" are different facts**, and a
    detector that cannot tell them apart is one somebody eventually switches off.

    ⚠ A DECLARATION IS NOT AN EXEMPTION. It must carry a reason, it does not cover any other field,
    and it is checked in BOTH directions — a field declared null that has started carrying a value
    is reported STALE rather than silently honoured.
    """

    DN = {"prunedMb": "the prune is OFF, so nobody measured a freed figure",
          "prunedWhy": "only written when a claim is REFUSED"}

    def _rows(self, n=200, **over):
        base = {"at": 0, "freeGb": 40.0, "reels": 40, "histBytes": 5728790118,
                "prunedMb": None, "prunedWhy": None}
        return [dict(base, at=i, **over) for i in range(n)]

    def test_WITHOUT_a_declaration_it_reads_DEAD(self):
        """★ The fuse, lit. This is the state his store enters on 2026-09-16."""
        r = DF.dead_fields(self._rows())
        self.assertEqual(r["state"], "DEAD_FIELDS")
        self.assertIn("prunedMb", r["dead"])

    def test_WITH_the_declaration_it_reads_OK_and_says_so(self):
        r = DF.dead_fields(self._rows(), declared_null=self.DN)
        self.assertEqual(r["state"], "OK", "a deliberately-null field still reads as a defect")
        self.assertEqual(r["dead"], [])
        self.assertIn("prunedMb", r["declaredNull"],
                      "it is excused silently rather than reported — a silent exemption is how a "
                      "real defect later hides behind a declaration")
        self.assertIn("declared null on purpose", r["why"])

    def test_a_declaration_does_NOT_cover_any_other_field(self):
        """⚠⚠ THE BASELINE. If declaring one field quieted the rest, this would be an off switch."""
        r = DF.dead_fields(self._rows(somethingElse=None), declared_null=self.DN)
        self.assertEqual(r["state"], "DEAD_FIELDS")
        self.assertIn("somethingElse", r["dead"])

    def test_a_STALE_declaration_is_reported(self):
        """A field declared null that HAS started carrying a value — the declaration outlived its
        referent and must say so rather than become a permanent exemption."""
        rows = self._rows()[:-40] + self._rows(n=40, prunedMb=12.5)
        r = DF.dead_fields(rows, declared_null=self.DN)
        self.assertIn("prunedMb", r["staleDeclarations"])
        self.assertIn("STALE", r["why"])

    def test_staleness_asks_about_the_WRITER_not_the_ARCHIVE(self):
        """⚠⚠ MY FIRST CUT ASKED IT OF EVERY ROW AND GOT THE WRONG ANSWER on his real store: 8,270
        rows written before 2026-09-02 carry a hardcoded `0` that v2154's retraction established
        was 'a fact about the CALLER', never a measurement. Judging the declaration against those
        made it read STALE for a writer that had not filled the field in three days. The
        declaration describes CURRENT behaviour. [[stale-reading]]"""
        rows = self._rows(n=40, prunedMb=0) + self._rows(n=200)
        r = DF.dead_fields(rows, declared_null=self.DN)
        self.assertEqual(r["staleDeclarations"], [],
                         "an old archive of values makes a current declaration read stale")

    def test_the_registry_entry_carries_the_declaration_and_a_REASON(self):
        entry = [w for w in DF.WATCHED if w[0] == "disk_history"][0]
        self.assertGreater(len(entry), 3, "the disk store declares nothing, so it re-arms the fuse")
        for field, why in entry[3].items():
            self.assertGreater(len(why or ""), 25,
                               "%s is declared null with no reason worth the name — an "
                               "unexplained exemption is how a real defect gets silenced" % field)

    def test_a_THREE_tuple_entry_still_works(self):
        """⚠ Additive only. reel_tombstones has no declaration and must keep its exact meaning."""
        entry = [w for w in DF.WATCHED if w[0] == "reel_tombstones"][0]
        self.assertEqual(len(entry), 3)
        r = DF.state()
        got = [s for s in (r.get("stores") or []) if s.get("store") == "reel_tombstones"]
        self.assertTrue(got, "the undeclared store vanished from the reading")
        self.assertIn("startedTs", got[0].get("dead") or [],
                      "the store this module was built for stopped reporting its own dead field")


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
