# -*- coding: utf-8 -*-
"""A JOURNAL ROW THAT IS THE ONLY TRACE OF WHAT A REEL FOUND MAY NEVER BE RELEASED.

Konyo approved the river's deletion with one string attached, 2026-09-14: *"i agree delete.. just
make sure before it was tallied and extracted properly"*. This is that sentence as a rule instead
of a check somebody did once.

⚠⚠ MEASURED ON HIS LIVE JOURNAL BEFORE THE RULE EXISTED. Of 447 rows the planner would have
released:

    245  still carried payload (finds, tallies, intakes, named, chron, registered, topFind)
    207  of those had their reel recorded in the sweep memory — the READ survives the row
     38  appeared in NO bank at all, several carrying `finds` and `topFind`

Those 38 are the whole point. The film is already gone for every one of them; the row is what is
left, and nothing else names the reel. Deleting it is not tidying, it is forgetting.

⚠ THE FILM GATE ALREADY ENFORCES HIS RULE ON THE OTHER SIDE, and this is the same sentence one
step downstream. `reel_retention` refuses to tombstone on `zero-pages` — *"that is 'this reader
found nothing', not 'done'"* — and on `panels-never-banked`, whose comment quotes him directly:
*"all of the reels get extracted with information thats needed"* BEFORE the tombstone. The journal
row is what survives the film, so it needs the same question asked of it. [[join-gate-heart]]

⚠ AND UNKNOWN HOLDS. A bank that could not be read is not an empty bank. On a path that deletes,
"I could not tell" and "there is nothing there" must never collapse into the same branch.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]
"""
import os
import sys
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import journal_retention as JR      # noqa: E402


def _row(sid, t0, **kw):
    r = {"sessionId": sid, "t0": t0, "footageState": JR.EXTRACTED, "footageWhy": "read and sealed"}
    r.update(kw)
    return r


class TestARowThatIsTheOnlyTraceIsNeverReleased(unittest.TestCase):

    def setUp(self):
        self._real = JR._banked_reels
        self.addCleanup(lambda: setattr(JR, "_banked_reels", self._real))
        # ⚠ enough dated rows that the "newest 8" hold cannot be what is doing the work
        self.filler = [_row("s_filler_%03d" % i, 1_800_000_000_000 + i) for i in range(12)]

    def _plan(self, extra, banked):
        JR._banked_reels = lambda: banked
        return JR.plan(self.filler + extra, hist_dir=os.path.join(HERE, "no-such-frames"))

    def test_a_banked_payload_row_is_released(self):
        row = _row("s_banked_1", 1_700_000_000_000, finds=[{"name": "x"}], named=3)
        p = self._plan([row], ({"s_banked_1": 3}, None))
        rel = {r["sessionId"] for r in p["release"]}
        print("   banked payload row released: %s" % ("s_banked_1" in rel))
        self.assertIn("s_banked_1", rel,
                      "a row whose reel yielded PAGES has a surviving trace and "
                      "may go — holding it would make the river undrainable")

    def test_an_unbanked_payload_row_is_held(self):
        row = _row("s_orphan_1", 1_700_000_000_001, finds=[{"name": "x"}], topFind="Shako")
        p = self._plan([row], ({"someone_else": 2}, None))
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   unbanked payload row released: %s" % ("s_orphan_1" in rel))
        self.assertNotIn("s_orphan_1", rel,
                         "a row carrying finds whose reel NO bank names is the only trace of what "
                         "that reel found, and it was released")
        self.assertIn("s_orphan_1", held)
        self.assertIn("only trace", held["s_orphan_1"])

    def test_a_row_swept_for_zero_pages_is_held(self):
        """⚠⚠ THE HOLE THE SECOND EYE FOUND IN v3105, AND THE FILE SETTLES IT. A sweep record is
        `{ts, classified, pages, promptVer, agentVer}` — there are no finds, no topFind, no names
        in chronicle_swept.json at all. Key presence proves the reel was LOOKED AT and says nothing
        about whether what it found was written down. MEASURED on his tree: 395 of 422 records
        carry `pages: 0`, and of the 207 payload rows the old rule released, only 12 had
        `pages >= 1`. `pages >= 1` is reel_retention's own bar, not one invented here."""
        row = _row("s_looked_1", 1_700_000_000_004, finds=[{"name": "Shako"}], topFind="Shako")
        p = self._plan([row], ({"s_looked_1": 0}, None))
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   swept-for-0-pages row released: %s" % ("s_looked_1" in rel))
        self.assertNotIn("s_looked_1", rel,
                         "a row whose reel was swept for ZERO pages was released — the sweep "
                         "proves a read ATTEMPT, never a durable copy, and this row held the only "
                         "register of a Shako")
        self.assertIn("0 PAGES", held["s_looked_1"])

    def test_the_bank_reader_detects_an_unreadable_store(self):
        """⚠ `_chron_swept_mem()` CAN NEVER RETURN None — `_json_store_load` marks the path in
        `control_app._UNREADABLE` and returns `{}`. So the UNKNOWN branch was reachable only if the
        call RAISED, and a corrupt bank quietly became an EMPTY one, which on a delete path is the
        difference between holding and releasing."""
        import ast
        import io as _io
        with _io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_banked_reels"), None)
        # ⚠ BOTH SPELLINGS. It is reached as `getattr(_ca, "_UNREADABLE", ())` — a defensive read
        # so an older control_app cannot raise — so the name is a STRING CONSTANT, not an
        # Attribute. A walk that only collects `.attr` reports it absent from code that uses it.
        names = {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
        # ⚠⚠ AND THE DOCSTRING IS EXCLUDED, because it MENTIONS `_UNREADABLE` by name. Leaving it
        # in makes the assertion satisfiable by PROSE — the exact trap that made a v3102 red-proof
        # come back BLIND, where a comment quoting an expression satisfied the check about it.
        # [[source-reading-guard]] [[measured-true-read-wrong]]
        _doc = fn.body[0] if fn.body else None
        _doc = _doc.value if (isinstance(_doc, ast.Expr)
                              and isinstance(getattr(_doc, "value", None), ast.Constant)) else None
        names |= {n.value for n in ast.walk(fn)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str) and n is not _doc}
        print("   _banked_reels consults: %s"
              % sorted(n for n in names if "UNREAD" in n.upper() or "swept" in n))
        self.assertIn("_UNREADABLE", names,
                      "_banked_reels never consults control_app._UNREADABLE, so a corrupt "
                      "chronicle_swept.json reads as an empty one instead of as UNKNOWN")

    def test_a_row_with_no_payload_still_goes(self):
        """The rule may not become 'nothing is ever deletable'."""
        row = _row("s_empty_1", 1_700_000_000_002)
        p = self._plan([row], ({}, None))
        rel = {r["sessionId"] for r in p["release"]}
        print("   empty row released: %s" % ("s_empty_1" in rel))
        self.assertIn("s_empty_1", rel,
                      "a row carrying nothing at all is not the only trace of anything; refusing "
                      "it would make the rule a blanket refusal wearing a reason")

    def test_an_unreadable_bank_holds_everything_with_payload(self):
        row = _row("s_unknown_1", 1_700_000_000_003, tallies={"a": 1})
        p = self._plan([row], (None, "the sweep memory could not be read (IOError)"))
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   with an UNREADABLE bank, payload row released: %s" % ("s_unknown_1" in rel))
        self.assertNotIn("s_unknown_1", rel,
                         "a bank that could not be read was treated as an EMPTY bank — 'I could "
                         "not tell' and 'there is nothing there' are different facts and only one "
                         "of them permits a delete")
        self.assertIn("UNKNOWN", held["s_unknown_1"])

    def test_the_bank_reader_delegates_rather_than_rederiving_the_path(self):
        """⚠ control_app's own v2139.1 scar names this file: a third reader joined
        chronicle_swept.json from HERE and bypassed TV_CHRON_SWEPT, _CHRON_SWEPT_PATH and TV_HIST,
        so two fixtures that patched the path still got the LIVE memory. [[copy-drift]]"""
        import ast
        import io as _io
        with _io.open(os.path.join(HERE, "journal_retention.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_banked_reels"), None)
        self.assertIsNotNone(fn, "_banked_reels is gone")
        calls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "_chron_swept_mem"]
        joins = [n for n in ast.walk(fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "join"]
        print("   _banked_reels: %d delegate call(s) · %d path join(s)" % (len(calls), len(joins)))
        self.assertEqual(len(calls), 1,
                         "_banked_reels must ask control_app._chron_swept_mem() exactly once")
        self.assertEqual(len(joins), 0,
                         "_banked_reels joins a path itself — that is the v2139.1 defect verbatim, "
                         "and it makes every fixture that patches the path read LIVE data")


RED_PROOF = [
    {
        "why": "a row carrying finds whose reel NO bank names is released again — the 38 rows on "
               "his live journal that are the only trace of what they found",
        "file": "journal_retention.py",
        "find": "            elif _carries_payload(s) and sid not in banked:",
        "replace": "            elif False:",
        "matches": 1,
    },
    {
        "why": "'looked at' goes back to counting as 'banked', so a row whose reel was swept for "
               "ZERO pages is released — 195 of his rows, several holding the only register of a "
               "real find",
        "file": "journal_retention.py",
        "find": "            elif _carries_payload(s) and int(banked.get(sid) or 0) < 1:",
        "replace": "            elif False:",
        "matches": 1,
    },
    {
        "why": "an unreadable bank is treated as an EMPTY bank, so 'I could not tell' silently "
               "becomes 'there is nothing there' on a path that deletes",
        "file": "journal_retention.py",
        "find": "            elif _carries_payload(s) and banked is None:",
        "replace": "            elif False:",
        "matches": 1,
    },
    {
        "why": "the payload check stops seeing anything, so every row looks empty and both holds "
               "evaporate at once",
        "file": "journal_retention.py",
        "find": '    return sorted(k for k in _PAYLOAD_FIELDS if s.get(k))',
        "replace": '    return []',
        "matches": 1,
    },
    {
        "why": "_banked_reels re-derives the sweep path instead of delegating — control_app's "
               "v2139.1 scar verbatim, which made fixtures read LIVE data",
        "file": "journal_retention.py",
        "find": "        mem = _ca._chron_swept_mem()",
        "replace": "        mem = json.load(io.open(os.path.join(HERE, 'chronicle_swept.json')))",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
