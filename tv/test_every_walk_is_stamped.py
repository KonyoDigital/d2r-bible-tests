#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🖨🔖 A READ THAT LEFT NO STAMP IS A READ NOBODY CAN PROVE HAPPENED.

Konyo, 2026-09-10, on the reels sitting in THE SHELF: *"make sure it gets processed through the
printer ... and gets stamped and verified that it was so it can go on the river flow to get
tombstoned after properly getting filtered and extracted"*.

⚠⚠ THE DEFECT, AND IT IS v2202'S OWN, IN THE BRANCH v2202 DID NOT TOUCH.

The sweep writer has three exits:

    did_read = classified > 0 or pages > 0
    1.  not did_read and not walked   -> write nothing          (nobody looked: correct)
    2.  not did_read                  -> write looked=True      (v2202 fixed this one)
    3.  did_read                      -> write NO `looked` key  (the reader worked, and said so nowhere)

`_chron_reel_owes_a_read` reads a missing `looked` as "nobody ever looked", so every reel that WAS
read and banked no page re-owes a read for ever. That is precisely the deadlock v2202 was written
to break, one branch over.

MEASURED on his 41 reels before the fix:

    _chron_owed_count()            41    every reel on disk owes a read
    records carrying `looked`       2    v2203, v2397
    records with NO `looked` key   36    agentVers v1868 .. v2350, written up to 09-08

Not legacy: v2314, v2319 and v2350 all post-date v2203 and still omit it. And downstream,
`reel_retention` reads their `pages: 0` as *"sealed with 0 pages — this reader found nothing"* and
keeps them for ever — an UNSTAMPED read wearing an unread reel's clothes.

[[unknown-stays-unknown]] [[the-unjoined-end]] [[copy-drift]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_safe  # noqa: E402  — this file prints 🖨 🔖 ⚠ ★
console_safe.enable()

import control_app as C  # noqa: E402


RED_PROOF = [
    {
        "why": "removing the stamp from the branch that DID read: the reel is walked, its runs are "
               "classified, and the record says nothing about having been looked at — so it owes a "
               "read for ever and can never reach the tombstone",
        "file": "control_app.py",
        "find": '''            _row.update(_look_stamp(
                st["reel"],
                "walked and read: %d run(s) classified, %d page(s) banked"
                % (st.get("classified") or 0, st.get("pages") or 0)))''',
        "replace": '            pass',
        "matches": 1,
    },
    {
        "why": "un-stamping the MEASURED-ZERO branch instead — v2202's own fix, removed. A reel "
               "the walk opened and found nothing in goes back to being re-read for ever",
        "file": "control_app.py",
        "find": '''                _row.update(_look_stamp(
                    st["reel"], "read and found no chronicle page — measured zero, not unread"))''',
        "replace": "                pass",
        "matches": 1,
    },
]


def _sweep_writer_src():
    """The function that writes chronicle_swept records, sliced by its own line span.

    Anchored at both ends, never a fixed-size window. [[source-reading-guard]]

    (Note) ONE PASS, DELIBERATELY. The first cut called ast.get_source_segment() on EVERY
    FunctionDef in a 30,000-line file; that helper re-splits the whole source on each call, so this
    law hung for minutes and had to be killed twice by PID. Find the marker LINE, then the smallest
    function whose span contains it. A law slow enough to be killed is a law that never runs.
    [[feedback-suspect-the-instrument]]
    """
    src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
    lines = src.splitlines()
    mark = None
    for i, l in enumerate(lines, start=1):
        if "_chron_swept_save(swept)" in l:
            mark = i
            break
    if mark is None:
        return ""
    best = None
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.FunctionDef):
            continue
        end_ln = getattr(n, "end_lineno", None)
        if end_ln is None or not (n.lineno <= mark <= end_ln):
            continue
        if best is None or (end_ln - n.lineno) < (best[1] - best[0]):
            best = (n.lineno, end_ln)
    if not best:
        return ""
    return "\n".join(lines[best[0] - 1:best[1]])


class EveryWalkIsStamped(unittest.TestCase):

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_a_reel_that_was_READ_stops_owing_a_read(self):
        """★★ The whole point, behaviourally: branch 3's record must satisfy the owes-a-read rule.

        This is the shape the reader writes after walking a reel and banking no page. Before the
        fix it carried no `looked` key and this returned True for ever."""
        rid = "reel_s_9999999999999_00001"
        mem = {rid: {"ts": 1, "classified": 7, "pages": 0, "looked": True,
                     "framesAtLook": 10 ** 9,          # far more film than any dir holds
                     "why": "walked and read: 7 run(s) classified, 0 page(s) banked",
                     "promptVer": getattr(C, "_tv", None) and getattr(C._tv, "PROMPT_VER", "p?")}}
        self.assertFalse(
            C._chron_reel_owes_a_read(rid, mem),
            "a reel that WAS walked and read still owes a read, so it can never be retired and "
            "never reaches the tombstone — the v2202 deadlock, one branch over")

    def test_an_UNSTAMPED_record_still_owes_a_read(self):
        """★★ The other half, and it must stay true: no stamp is UNKNOWN, and UNKNOWN buys the
        read rather than suppressing it. A fix that made everything stop owing would be worse than
        the defect. [[unknown-stays-unknown]]"""
        rid = "reel_s_9999999999999_00002"
        mem = {rid: {"ts": 1, "classified": 7, "pages": 0}}
        self.assertTrue(
            C._chron_reel_owes_a_read(rid, mem),
            "a record with no `looked` key was treated as a proven look — an unread reel would be "
            "retired on the strength of a record that never says anyone read it")

    # ── the writer itself ───────────────────────────────────────────────────────────────────
    def test_EVERY_record_the_sweep_writes_carries_the_stamp(self):
        """★★ Parsed, not grepped: every dict assigned into `swept[...]` must end up with a
        `looked` key, whether inline or merged in."""
        seg = _sweep_writer_src()
        self.assertTrue(seg, "the sweep writer could not be located in control_app.py by AST")
        tree = ast.parse(seg)
        writes = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Subscript) and getattr(t.value, "id", "") == "swept"
                          for t in n.targets)]
        self.assertTrue(writes, "no `swept[...] = ...` assignment found — this law is vacuous")
        stamps = seg.count("_look_stamp(")
        self.assertGreaterEqual(
            stamps, len(writes) + 1,
            "%d record(s) are written into `swept` but the stamp is applied only %d time(s) "
            "(one definition + one call per record expected). A branch that walked and did not "
            "stamp re-owes its reel for ever." % (len(writes), stamps - 1))

    def test_the_stamp_has_exactly_ONE_definition(self):
        """★ Two copies of the stamp is how the two branches drifted apart in the first place."""
        seg = _sweep_writer_src()
        defs = [n for n in ast.walk(ast.parse(seg))
                if isinstance(n, ast.FunctionDef) and n.name == "_look_stamp"]
        self.assertEqual(1, len(defs),
                         "_look_stamp is defined %d times inside the sweep writer" % len(defs))

    def test_the_stamp_carries_the_EVIDENCE_a_re_read_would_need(self):
        """★ `looked` alone would retire a reel that has since grown. The frame count is what makes
        a re-read worth paying for, and v2202's rule keys on exactly that."""
        seg = _sweep_writer_src()
        d = [n for n in ast.walk(ast.parse(seg))
             if isinstance(n, ast.FunctionDef) and n.name == "_look_stamp"]
        self.assertEqual(1, len(d))
        body = ast.get_source_segment(seg, d[0]) or ""
        for k in ("looked", "framesAtLook", "dirMtimeAtLook", "why"):
            self.assertIn('"%s"' % k, body,
                          "the stamp omits %r, so a reel that GROWS after the look cannot be told "
                          "from one that did not" % k)


if __name__ == "__main__":
    unittest.main(verbosity=2)
