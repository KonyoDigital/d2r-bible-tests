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
        p = self._plan([row], ({"s_banked_1"}, None))
        rel = {r["sessionId"] for r in p["release"]}
        print("   banked payload row released: %s" % ("s_banked_1" in rel))
        self.assertIn("s_banked_1", rel,
                      "a row whose reel IS recorded in the sweep memory has a surviving trace and "
                      "may go — holding it would make the river undrainable")

    def test_an_unbanked_payload_row_is_held(self):
        row = _row("s_orphan_1", 1_700_000_000_001, finds=[{"name": "x"}], topFind="Shako")
        p = self._plan([row], ({"someone_else"}, None))
        rel = {r["sessionId"] for r in p["release"]}
        held = {r["sessionId"]: r["why"] for r in p["keep"]}
        print("   unbanked payload row released: %s" % ("s_orphan_1" in rel))
        self.assertNotIn("s_orphan_1", rel,
                         "a row carrying finds whose reel NO bank names is the only trace of what "
                         "that reel found, and it was released")
        self.assertIn("s_orphan_1", held)
        self.assertIn("only trace", held["s_orphan_1"])

    def test_a_row_with_no_payload_still_goes(self):
        """The rule may not become 'nothing is ever deletable'."""
        row = _row("s_empty_1", 1_700_000_000_002)
        p = self._plan([row], (set(), None))
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
        "find": "        mem = _ca._chron_swept_mem() or {}",
        "replace": "        mem = json.load(io.open(os.path.join(HERE, 'chronicle_swept.json'))) or {}",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
