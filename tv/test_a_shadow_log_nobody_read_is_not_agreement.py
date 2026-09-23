# -*- coding: utf-8 -*-
"""A SHADOW LOG NOBODY READS IS NOT AGREEMENT — board #188.

`tv/g5_grok_eyes.py::g5_shadow_log()` has written `claude_names` / `grok_names` / `claude_scene` /
`grok_scene` since 2026-08-23. Those four keys occur at exactly FOUR lines tree-wide and ALL FOUR
ARE WRITES — the file had never been opened for read. Measured by hand on his live store the day
this gate was written (6,082 rows, 2026-08-23 23:06:14 -> 2026-09-14 18:05:20): of the 1,596 rows
where BOTH lanes answered, 1,079 (67.6%) carried different NAME lists and 968 (60.7%) a different
SCENE — while `tv/g5_grok_eyes.state` read {"on": true, "mode": "primary"}.

**The promotion to primary rested on evidence nobody had ever looked at.** `tv/g5_shadow_reducer.py`
is the read side. This gate is what stops the reader from lying.

The five ways a reader like this goes quietly wrong, each with a law below:

  1. IT PICKS A WINNER. The moment a reducer says which lane was right, the 67.6% stops being a
     finding about the instruments and becomes a scoreboard. LAW_SYMMETRY drives the reducer twice
     — once with the lanes swapped — and pins that agree/disagree are IDENTICAL while the one-sided
     counts trade places. A reducer that prefers a lane cannot pass that.
  2. IT COUNTS SILENCE AS DISSENT. 4,486 of his 6,082 rows have grok silent. Folding those into the
     denominator would have turned 67.6% into a number about lane availability. LAW_BUCKETS pins
     one-sided and neither into their own buckets and out of the agreement denominator.
  3. IT PUBLISHES A BARE PERCENT. LAW_EVERY_FIGURE walks the whole report and fails any figure that
     does not carry n, d, pct AND its window together. [[zero-needs-a-denominator]]
  4. IT REPORTS 0.0% FOR NOTHING-MEASURED. LAW_ZERO_DENOM pins pct=None when d=0.
     [[unknown-stays-unknown]]
  5. IT READS HIS LIVE STORE. tv/g5_shadow.jsonl is gitignored and per-machine; a gate that reads
     it is green here and red on origin for reasons that are not the code. LAW_NO_IO proves through
     the COMPILER that reduce_rows and every helper it calls name no file primitive at all, so a
     test can only ever hand it fixtures. [[feedback-fixtures-never-touch-live-data]]

And one join law, because a reader wired to keys the writer does not write is the same defect in
the other direction: LAW_JOIN parses tv/g5_grok_eyes.py with `ast` (never imports it — importing
touches his per-machine state and budget files) and pins that every key the reducer reads is a key
`g5_shadow_log` actually writes, and that the reducer's default path is the writer's `_SHADOW_LOG`.
[[the-unjoined-end]]

⚠ EVERY LAW HERE DRIVES THE REDUCER AND READS ITS VERDICT. Not one asserts arithmetic about what
the reducer ought to compute. [[a-law-about-a-row-must-drive-the-row]]
"""
from __future__ import annotations

import ast
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import g5_shadow_reducer as R   # noqa: E402

WRITER = os.path.join(HERE, "g5_grok_eyes.py")

# ── THE FIXTURE ───────────────────────────────────────────────────────────────────────────────
# Ten synthetic rows, one per shape the reducer must tell apart. Every timestamp is 2026-01-01 and
# every name is a fixture, so nothing here can be mistaken for his footage and nothing reaches the
# live store. [[feedback-fixtures-never-touch-live-data]] [[a-gate-may-not-pin-his-footage]]
ROWS = [
    # 0  AGREE, both non-empty (case-insensitive, order-insensitive), same scene
    {"ts": "2026-01-01 00:00:01", "claude_names": ["Shako"], "grok_names": ["shako"],
     "claude_scene": "stash", "grok_scene": "stash"},
    # 1  AGREE, BOTH EMPTY — the cheapest possible agreement; must be reported separately
    {"ts": "2026-01-01 00:00:02", "claude_names": [], "grok_names": [],
     "claude_scene": "gameplay", "grok_scene": "gameplay"},
    # 2  DISAGREE, disjoint, and the scenes differ too
    {"ts": "2026-01-01 00:00:03", "claude_names": ["Windforce"], "grok_names": ["Titan's Revenge"],
     "claude_scene": "gameplay", "grok_scene": "stash"},
    # 3  DISAGREE, claude empty / grok saw — the dominant shape in his real store (914 of 1,079)
    {"ts": "2026-01-01 00:00:04", "claude_names": [], "grok_names": ["Horadric Cube"],
     "claude_scene": "gameplay", "grok_scene": "stash"},
    # 4  DISAGREE, partial overlap
    {"ts": "2026-01-01 00:00:05", "claude_names": ["Shako", "Occulus"], "grok_names": ["Shako"],
     "claude_scene": "stash", "grok_scene": "stash"},
    # 5  ONE-SIDED CLAUDE — grok silent on both fields. NOT a disagreement.
    {"ts": "2026-01-01 00:00:06", "claude_names": ["Grandfather"], "grok_names": None,
     "claude_scene": "loot", "grok_scene": None},
    # 6  ONE-SIDED GROK — claude silent on both fields. NOT a disagreement.
    {"ts": "2026-01-01 00:00:07", "claude_names": None, "grok_names": ["Tome of Identify"],
     "claude_scene": None, "grok_scene": "stash"},
    # 7  NEITHER — not evidence at all
    {"ts": "2026-01-01 00:00:08", "claude_names": None, "grok_names": None,
     "claude_scene": None, "grok_scene": None},
    # 8  MIXED PER FIELD: names agree, but a BLANK scene is not an answer -> scene is one-sided grok
    {"ts": "2026-01-01 00:00:09", "claude_names": ["Ist"], "grok_names": ["Ist"],
     "claude_scene": "", "grok_scene": "stash"},
    # 9  DISAGREE, grok empty / claude saw — the mirror of row 3
    {"ts": "2026-01-01 00:00:10", "claude_names": ["Vex"], "grok_names": [],
     "claude_scene": "stash", "grok_scene": "stash"},
]

FIRST_TS, LAST_TS = "2026-01-01 00:00:01", "2026-01-01 00:00:10"


def _swap(rows):
    """The same rows with the two lanes exchanged. Used to prove the reducer has no favourite."""
    out = []
    for r in rows:
        q = dict(r)
        for f in ("names", "scene"):
            q["claude_" + f], q["grok_" + f] = r.get("grok_" + f), r.get("claude_" + f)
        out.append(q)
    return out


def _figures(obj, path="report"):
    """Every figure in the report tree, as (path, figure)."""
    found = []
    if isinstance(obj, dict):
        if "pct" in obj and "n" in obj:
            found.append((path, obj))
        for k, v in obj.items():
            found += _figures(v, "%s.%s" % (path, k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            found += _figures(v, "%s[%d]" % (path, i))
    return found


def _writer_dict_keys(path=WRITER):
    """The literal keys g5_shadow_log() writes, read with ast — never by importing, never by grep.

    Importing g5_grok_eyes touches his per-machine state/budget files; grepping would match the
    same words inside a comment. [[feedback-comments-vs-code]] [[source-reading-guard]]
    """
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "g5_shadow_log"), None)
    if fn is None:
        return None
    keys = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.add(k.value)
    return keys


def _writer_log_basename(path=WRITER):
    """The filename in `_SHADOW_LOG = os.path.join(HERE, "...")`, read with ast."""
    with io.open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_SHADOW_LOG"
                                                for t in node.targets):
            for a in ast.walk(node.value):
                if isinstance(a, ast.Constant) and isinstance(a.value, str) and "." in a.value:
                    return a.value
    return None


class ShadowLogReadSide(unittest.TestCase):

    # ── PREMISE — a case that cannot run must never read like a case that ran and was fine ──
    def test_00_premise(self):
        """[[a-probe-licenses-only-what-it-tested]] — prove the subject before asserting on it."""
        self.assertTrue(os.path.isfile(R.__file__.replace(".pyc", ".py")),
                        "the reducer under test is not on disk: %r" % R.__file__)
        self.assertEqual(os.path.basename(R.__file__).split(".")[0], "g5_shadow_reducer")
        self.assertTrue(callable(R.reduce_rows) and callable(R.divergence_row))
        self.assertTrue(os.path.isfile(WRITER), "the WRITER %s is tracked and must exist" % WRITER)
        rep = R.reduce_rows(ROWS)
        self.assertEqual(rep["rows_total"], len(ROWS))
        # NON-VACUOUS: the fixture must actually populate every bucket, or the laws below could all
        # pass over a reducer that returns zeros. [[matches-once-can-still-prove-nothing]]
        n = rep["fields"]["names"]
        for k in ("both", "one_sided_claude", "one_sided_grok", "neither"):
            self.assertGreater(n[k], 0, "fixture never exercises bucket %r — the gate would be "
                                        "vacuous" % k)
        self.assertGreater(n["disagree"]["n"], 0)
        self.assertGreater(n["agree"]["n"], 0)

    # ── LAW_BUCKETS ─────────────────────────────────────────────────────────────────────────
    def test_01_names_buckets(self):
        """Agree / disagree / one-sided / neither, each counted where it belongs."""
        f = R.reduce_rows(ROWS)["fields"]["names"]
        self.assertEqual(f["both"], 7, "rows where both lanes produced a names list: %r" % f)
        self.assertEqual(f["one_sided_claude"], 1, "claude spoke, grok silent")
        self.assertEqual(f["one_sided_grok"], 1, "grok spoke, claude silent")
        self.assertEqual(f["neither"], 1, "neither lane answered — not evidence")
        self.assertEqual(f["agree"]["n"], 3)
        self.assertEqual(f["disagree"]["n"], 4)
        self.assertEqual(f["agree"]["d"], 7, "the denominator is the BOTH rows and only those")
        self.assertEqual(f["disagree"]["d"], 7)
        self.assertEqual(f["shapes"], {"equal_both_empty": 1, "equal_nonempty": 2,
                                       "claude_empty_grok_saw": 1, "grok_empty_claude_saw": 1,
                                       "overlap_partial": 1, "disjoint_both_nonempty": 1})
        # The free agreement is subtractable: two empty lists matching is not two eyes agreeing.
        self.assertEqual(f["agree_excluding_both_empty"]["n"], 2)
        self.assertEqual(f["agree_excluding_both_empty"]["d"], 6)

    def test_02_scene_buckets(self):
        """A BLANK scene is not an answer, so row 8 is one-sided, not a disagreement."""
        f = R.reduce_rows(ROWS)["fields"]["scene"]
        self.assertEqual(f["both"], 6, "%r" % f)
        self.assertEqual(f["one_sided_claude"], 1)
        self.assertEqual(f["one_sided_grok"], 2, "row 8's blank claude_scene is silence, not 'stash'")
        self.assertEqual(f["neither"], 1)
        self.assertEqual(f["agree"]["n"], 4)
        self.assertEqual(f["disagree"]["n"], 2)
        self.assertEqual([(e["claude_scene"], e["grok_scene"], e["rows"])
                          for e in f["top_divergences"]], [("gameplay", "stash", 2)])

    def test_03_one_sided_and_silent_stay_out_of_the_denominator(self):
        """The bug this exists to stop: folding 4,486 silent rows into a 67.6%."""
        f = R.reduce_rows(ROWS)["fields"]["names"]
        self.assertEqual(f["both"] + f["one_sided_claude"] + f["one_sided_grok"] + f["neither"],
                         len(ROWS), "the four buckets must partition the input exactly")
        self.assertEqual(f["agree"]["d"] + f["one_sided_claude"] + f["one_sided_grok"]
                         + f["neither"], len(ROWS))
        self.assertNotIn(len(ROWS), (f["agree"]["d"], f["disagree"]["d"]),
                         "the denominator is not the row count")

    # ── LAW_SYMMETRY — no lane preference, proven by driving it twice ───────────────────────
    def test_04_the_reducer_has_no_favourite_lane(self):
        a = R.reduce_rows(ROWS)
        b = R.reduce_rows(_swap(ROWS))
        for fld in ("names", "scene"):
            fa, fb = a["fields"][fld], b["fields"][fld]
            self.assertEqual(fa["both"], fb["both"], fld)
            self.assertEqual(fa["agree"]["n"], fb["agree"]["n"],
                             "%s: swapping the lanes changed the agreement count — the reducer "
                             "prefers a lane" % fld)
            self.assertEqual(fa["disagree"]["n"], fb["disagree"]["n"], fld)
            self.assertEqual(fa["one_sided_claude"], fb["one_sided_grok"],
                             "%s: one-sided counts must TRADE PLACES under a swap" % fld)
            self.assertEqual(fa["one_sided_grok"], fb["one_sided_claude"], fld)
        na, nb = a["fields"]["names"], b["fields"]["names"]
        self.assertEqual([e["name"] for e in na["top_divergences"]["claude_only"]],
                         [e["name"] for e in nb["top_divergences"]["grok_only"]],
                         "the two testimonies must trade places, not be re-ranked")
        self.assertEqual([e["name"] for e in na["top_divergences"]["grok_only"]],
                         [e["name"] for e in nb["top_divergences"]["claude_only"]])
        self.assertEqual(na["shapes"]["claude_empty_grok_saw"],
                         nb["shapes"]["grok_empty_claude_saw"])

    def test_05_both_testimonies_are_published(self):
        """Neither list is 'the errors'. Both directions must carry rows."""
        d = R.reduce_rows(ROWS)["fields"]["names"]["top_divergences"]
        self.assertTrue(d["claude_only"], "the claude-only testimony was dropped")
        self.assertTrue(d["grok_only"], "the grok-only testimony was dropped")
        self.assertEqual(sorted(e["name"] for e in d["claude_only"]),
                         ["occulus", "vex", "windforce"])
        self.assertEqual(sorted(e["name"] for e in d["grok_only"]),
                         ["horadric cube", "titan's revenge"])

    # ── LAW_EVERY_FIGURE — a number never travels without its denominator and its window ────
    def test_06_every_figure_carries_its_denominator_and_window(self):
        rep = R.reduce_rows(ROWS)
        figs = _figures(rep)
        self.assertGreater(len(figs), 8, "no figures found — the walker missed the tree")
        for path, f in figs:
            for k in ("n", "d", "pct", "first_ts", "last_ts"):
                self.assertIn(k, f, "%s publishes a number without %r: %r" % (path, k, f))
            if f["d"]:
                self.assertIsNotNone(f["pct"], "%s: %r" % (path, f))
                self.assertIsNotNone(f["first_ts"],
                                     "%s carries a percent with no window: %r" % (path, f))
                self.assertIsNotNone(f["last_ts"], "%s: %r" % (path, f))
            else:
                self.assertIsNone(f["pct"], "%s: a rate over nothing is unknown, not 0.0: %r"
                                  % (path, f))
        # and the formatter must never print a bare percent
        self.assertNotIn("%", R.fmt_figure(R.figure(0, 0)),
                         "a figure with no denominator must not be printed as a percent")
        self.assertIn("/", R.fmt_figure(R.figure(3, 7, FIRST_TS, LAST_TS)))
        self.assertIn(FIRST_TS, R.fmt_figure(R.figure(3, 7, FIRST_TS, LAST_TS)))

    def test_07_a_window_is_the_rows_dates_not_the_run_time(self):
        rep = R.reduce_rows(ROWS)
        self.assertEqual(rep["window"], {"first_ts": FIRST_TS, "last_ts": LAST_TS})
        self.assertEqual(rep["fields"]["names"]["agree"]["first_ts"], FIRST_TS)
        self.assertEqual(rep["fields"]["names"]["agree"]["last_ts"], LAST_TS)
        self.assertEqual(rep["fields"]["scene"]["window"]["first_ts"], FIRST_TS)

    def test_08_nothing_measured_is_unknown_not_zero(self):
        """[[zero-needs-a-denominator]] — the one-sided-only store."""
        only = [r for r in ROWS if r.get("grok_names") is None]
        rep = R.reduce_rows(only)
        f = rep["fields"]["names"]
        self.assertEqual(f["both"], 0)
        self.assertIsNone(f["agree"]["pct"], "0 of 0 must be unknown: %r" % f["agree"])
        self.assertIsNone(f["disagree"]["pct"], "%r" % f["disagree"])
        empty = R.reduce_rows([])
        self.assertIsNone(empty["fields"]["names"]["agree"]["pct"])
        self.assertTrue(any("evidence" in c for c in empty["caveats"]),
                        "an empty store must say it is not evidence: %r" % empty["caveats"])

    # ── LAW_CAVEAT — derived from the record, not typed into it ─────────────────────────────
    def test_09_the_caveat_is_derived_from_the_keys_present(self):
        """A lane's [] cannot be told from a failed read — but only while the keys are missing."""
        rep = R.reduce_rows(ROWS)
        self.assertTrue(any("cannot be told apart" in c for c in rep["caveats"]),
                        "the record carries no conf/mode/error and the report did not say so: %r"
                        % rep["caveats"])
        richer = [dict(r, claude_conf=0.8, grok_conf=0.7) for r in ROWS]
        rep2 = R.reduce_rows(richer)
        self.assertFalse(any("cannot be told apart" in c for c in rep2["caveats"]),
                         "the caveat is hardcoded — it survived rows that disambiguate: %r"
                         % rep2["caveats"])

    # ── LAW_NO_IO — proven through the compiler, not by hoping ──────────────────────────────
    def test_10_the_reducer_touches_no_file(self):
        """A gate can only hand it fixtures if it cannot open anything. [[the-unjoined-end]]"""
        names = set()
        for fn in (R.reduce_rows, R._names_field, R._scene_field, R._bucket, R._window, R.figure,
                   R.names_key, R.scene_key, R.answered_names, R.answered_scene):
            names |= set(fn.__code__.co_names)
        for banned in ("open", "load_rows", "DEFAULT_LOG", "DEFAULT_STATE", "read_mode"):
            self.assertNotIn(banned, names,
                             "reduce_rows reaches %r — it can read his live store, and a gate "
                             "driving it would be reading gitignored per-machine data" % banned)
        self.assertIn("figure", set(R._names_field.__code__.co_names),
                      "premise: the walker is looking at the real helpers")

    # ── LAW_JOIN — the reader's keys are the writer's keys ──────────────────────────────────
    def test_11_the_reader_is_wired_to_the_keys_the_writer_writes(self):
        keys = _writer_dict_keys()
        self.assertIsNotNone(keys, "g5_shadow_log() not found in %s — the writer moved" % WRITER)
        self.assertGreater(len(keys), 4, "premise: the writer's record was not parsed (%r)" % keys)
        for lane in R.LANES:
            for field in ("names", "scene"):
                k = "%s_%s" % (lane, field)
                self.assertIn(k, keys,
                              "the reducer reads %r and g5_shadow_log() does not write it — "
                              "half a wire reads exactly like a whole one" % k)
        self.assertEqual(os.path.basename(R.DEFAULT_LOG), _writer_log_basename(),
                         "the reader's default store is not the file the writer appends to")

    # ── LAW_ROW — the doctor-callable row, driven ───────────────────────────────────────────
    def test_12_the_row_reports_and_never_judges(self):
        d = tempfile.mkdtemp(prefix="g5_shadow_")
        missing = os.path.join(d, "nope.jsonl")
        row = R.divergence_row(log_path=missing, state_path=os.path.join(d, "nope.state"))
        self.assertEqual(row["state"], "unread",
                         "a store that is gitignored and absent is NORMAL on CI — a row that "
                         "cries wolf here gets silenced: %r" % row)
        self.assertEqual(row["mode"], "unknown", "an unreadable state file is never 'off': %r" % row)
        self.assertIsNone(row["report"])

        # a store with rows but no row where both lanes answered
        p1 = os.path.join(d, "one_sided.jsonl")
        with io.open(p1, "w", encoding="utf-8") as fh:
            for r in ROWS:
                if r.get("grok_names") is None:
                    fh.write(json.dumps(r) + "\n")
        row1 = R.divergence_row(log_path=p1, state_path=os.path.join(d, "nope.state"))
        self.assertEqual(row1["state"], "no-evidence",
                         "silence is not agreement: %r" % row1["detail"])

        # a store with real two-lane rows, and a state file declaring primary
        p2 = os.path.join(d, "full.jsonl")
        with io.open(p2, "w", encoding="utf-8") as fh:
            for r in ROWS:
                fh.write(json.dumps(r) + "\n")
            fh.write("{ this line is not json\n")
        sp = os.path.join(d, "s.state")
        with io.open(sp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"on": True, "mode": "primary"}))
        row2 = R.divergence_row(log_path=p2, state_path=sp)
        self.assertEqual(row2["state"], "measured")
        self.assertEqual(row2["mode"], "primary",
                         "the promotion rests on these figures and the row must name it")
        self.assertEqual(row2["store"]["unparsable"], 1,
                         "a half-corrupt store must count what it could not read: %r"
                         % row2["store"])
        self.assertEqual(row2["report"]["fields"]["names"]["both"], 7)
        self.assertIn("4/7", row2["detail"], "the row must carry n/d, not a bare rate: %r"
                      % row2["detail"])

    def test_13_the_report_renders_and_names_both_lanes(self):
        txt = R.format_report(R.reduce_rows(ROWS, source="fixture"), mode="primary")
        self.assertIn("claude_only", txt)
        self.assertIn("grok_only", txt)
        self.assertIn("3/7", txt)
        self.assertIn(FIRST_TS, txt)
        self.assertNotIn("g5_shadow.jsonl", txt, "the report must not name his live store when "
                                                 "it was handed a fixture")
        txt.encode("ascii", "strict")   # cp1255 console safety: the report itself stays ASCII


if __name__ == "__main__":
    unittest.main(verbosity=2)
