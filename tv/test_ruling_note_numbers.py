"""v2484 — a NOTE that quotes a measured number must still be telling the truth.

⚠⚠ THE FAILURE, MEASURED. The v2192 ruling comment in bible.html carries a small table of
measurements supporting Konyo's "the chronicle counts 99 runewords". One row read:

    RUNEWORD_TIP           97   what the chronicle KPI divides by today

That was never true. The KPI it names returns `total: Object.keys(_tip).length` — UNFILTERED — so
it has always divided by 99. The 97 is the NUMERATOR: `made` is
`Object.keys(rm).filter(n => _tip[n]).length`, the 97 of his 99 made runewords that appear in the
map, which is literally the next line of the same table. The row named the wrong side of the
fraction.

The damage was not the digit. The sentence after it concluded the KPI "would say 97/97" (it says
97/99), and then ACCUSED the neighbouring `(99/99)` comment of being "a label that outlived its
referent: the map drifted to 97 and the sentence did not move". The map never drifted —
RUNEWORD_TIP held 99 keys at the commit that authored the note, at v2104, and at HEAD. The stale
number was in the accusing note, pointing at a comment that was right.

Nothing on any screen was ever wrong, and his ruling is untouched: RUNEWORD_CHRONICLE_TOTAL = 99
is his call and happens to equal the derived catalogue size. The defect lived in the REASONING
RECORD, where nothing was checking it — a note is the one place a wrong number can sit for months
because no test reads prose.

This reads it. [[label-outlived-referent]] [[inherited-claim-is-not-evidence]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _src():
    return io.open(BIBLE, encoding="utf-8").read()


def _balanced(s, start, open_ch, close_ch):
    """Span of a balanced bracket run, skipping string literals. -> str"""
    i = s.index(open_ch, start)
    depth = 0
    instr = None
    j = i
    while j < len(s):
        c = s[j]
        if instr:
            if c == "\\":
                j += 2
                continue
            if c == instr:
                instr = None
        elif c in "\"'":
            instr = c
        elif c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return s[i:j + 1]
        j += 1
    raise AssertionError("unbalanced %s from %d" % (open_ch, start))


def _runeword_tip_keys(s):
    """Top-level key count of const RUNEWORD_TIP, string-aware. -> int"""
    i = s.index("const RUNEWORD_TIP")
    blk = _balanced(s, i, "{", "}")
    depth = 0
    instr = None
    keys = 0
    for idx, c in enumerate(blk):
        if instr:
            if c == "\\":
                continue
            if c == instr:
                instr = None
        elif c in "\"'":
            instr = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ":" and depth == 1:
            keys += 1
    return keys


def _runewords_rows(s):
    """Row count of const RUNEWORDS (entries are keyed n:"Name"). -> int"""
    m = re.search(r"const\s+RUNEWORDS\s*=\s*\[", s)
    blk = _balanced(s, m.start(), "[", "]")
    return len(re.findall(r"\bn\s*:\s*\"[^\"]+\"", blk))


class ANoteMayNotQuoteANumberThatIsNotTrue(unittest.TestCase):

    def setUp(self):
        self.s = _src()

    def test_RUNEWORD_TIP_as_quoted_in_prose_matches_the_object(self):
        """Every `RUNEWORD_TIP <n>` written in a comment must equal the real key count."""
        real = _runeword_tip_keys(self.s)
        quoted = [(m.start(), int(m.group(1)))
                  for m in re.finditer(r"RUNEWORD_TIP\s{2,}(\d+)", self.s)]
        self.assertTrue(
            quoted,
            "no comment quotes a RUNEWORD_TIP count any more — if that table was removed this "
            "guard has lost its subject and should be retired deliberately, not left passing")
        for pos, n in quoted:
            line = self.s.count("\n", 0, pos) + 1
            self.assertEqual(
                n, real,
                "bible.html:%d says RUNEWORD_TIP is %d; the object has %d top-level keys. A note "
                "is the one place a wrong number sits for months, because nothing reads prose — "
                "and this exact row once said 97, which was the NUMERATOR of the KPI it was "
                "describing." % (line, n, real))

    def test_the_KPI_denominator_really_is_unfiltered(self):
        """The note's claim rests on WHICH expression the KPI divides by."""
        m = re.search(r"total:\s*_tip\s*\?\s*Object\.keys\(_tip\)\.length\s*:\s*0", self.s)
        self.assertTrue(
            m,
            "the chronicle KPI no longer returns `total: Object.keys(_tip).length`. Every note "
            "in this file that says what it 'divides by' was written against that expression, so "
            "if it changed, those notes are now describing something that does not exist.")
        # and it must NOT have quietly grown a filter, which is what would make 97 correct
        seg = self.s[m.start():m.start() + 160]
        self.assertNotIn(
            "filter", seg,
            "the KPI's TOTAL now filters. That changes the denominator every surrounding comment "
            "describes, and it is the one change that would retroactively make the old '97' right")

    def test_the_farm_roster_count_as_quoted_matches(self):
        real = _runewords_rows(self.s)
        for m in re.finditer(r"window\.RUNEWORDS\s{2,}(\d+)", self.s):
            n = int(m.group(1))
            line = self.s.count("\n", 0, m.start()) + 1
            self.assertEqual(
                n, real,
                "bible.html:%d says window.RUNEWORDS is %d; it has %d rows" % (line, n, real))

    def test_the_ruling_itself_is_untouched(self):
        """⚠ His call, dated. This guard exists to protect the record AROUND it, never to move it.

        If this ever fails, someone changed what the chronicle counts. That is Konyo's decision
        and nobody else's — the failure is the point, not a bug in the test.
        """
        m = re.search(r"var\s+RUNEWORD_CHRONICLE_TOTAL\s*=\s*(\d+)\s*;", self.s)
        self.assertTrue(m, "RUNEWORD_CHRONICLE_TOTAL is gone")
        self.assertEqual(
            int(m.group(1)), 99,
            "RUNEWORD_CHRONICLE_TOTAL is no longer 99. That is his ruling of 2026-08-27 — 'i have "
            "99 runewords' — and it may only change because he says so.")


RED_PROOF = [
    {
        'why': 'The gate\'s second law pins the ONE expression the whole v2192/v2484 ruling note reasons about: the chronicle KPI\'s denominator must stay `total: _tip ? Object.keys(_tip).length : 0` — UNFILTERED — because that is what makes the note\'s "it has always divided by 99" true and the neighbouring `(99/99)` label correct. Swapping the denominator to the made-map (`Object.keys(rm).length`) is exactly the 97-vs-99 confusion the note was corrected for: the KPI would start dividing by the NUMERATOR\'s basis, every surrounding comment would be describing an expression that no longer exists, and the old wrong "97" would retroactively look right. It is live code on bible.html:41420, not a comment, not a mention inside a message string, and not a constant the test reads from both sides (the test hardcodes its own expected shape), so only one side of the comparison moves.  MEASURED: untampered GREEN — `python3 tv/test_ruling_note_numbers.py` -> Ran 4 tests, OK (0.057s), ex; tampered (all 1) RED — same command -> Ran 4 tests, FAILED (failures=1); the single failure is te; reddened law test_ruling_note_numbers.ANoteMayNotQuoteANumberThatIsNotTrue.test_the; ALONE FAILS ALONE — fresh process: `python3 -m unittest test_ruling_note_numbers.ANoteMayNotQuoteANumberTh.',
        'file': 'bible.html',
        'find': 'total: _tip ? Object.keys(_tip).length : 0',
        'replace': 'total: _tip ? Object.keys(rm).length : 0',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
