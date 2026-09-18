# -*- coding: utf-8 -*-
"""v3321 — A LOCK STATE IS ASKED, NEVER ASSERTED IN PROSE.

`self_arming` exists so a lock OPENS ITSELF once its witness has survived enough distinct attacks,
"and never by anyone editing a file". That is the design, and it works. It also guarantees that
every comment stating a lock's state will eventually be false, because the state moves and the
comment cannot.

MEASURED 2026-09-18. Three production sites said, in present tense:

    control_app.py   "⛔ IT SHIPS LOCKED AND THAT IS THE POINT. `may()` returns False today"
    self_arming.py   "this ships LOCKED: `may()` returns False today"
    the law's own    "`may(\"console.pixel_rescue\")` returns False today"

while the lock had opened:

    may("console.pixel_rescue") -> True
    32 of 32 DISTINCT ATTACKS refused · wilson 0.893 >= 0.839 · kinds 2.50 >= 1.80

⚠ IT MATTERS MORE THAN AN ORDINARY STALE COMMENT, because of WHICH lock it is. That block's own
docstring says a wrong verdict here "does not lose footage, it REPLACES THE WINDOW HE IS LOOKING
AT". A reader asking whether the console may replace his window reads "ships locked" and stops
reading. That is exactly what happened on 2026-09-18, to me, and it was caught only by calling
may() instead of believing the sentence above it. [[measured-true-read-wrong]]

THIS IS A CORROBORATOR, NOT A WORD BAN. A claim is allowed to say a lock is shut — while it is
shut. The law fails only when prose and `may()` DISAGREE, so it goes red on the day the lock moves
and stays quiet otherwise. Banning the words outright would forbid explaining the mechanism at all.
[[heart-first]] §1 — two genuinely independent sides: one is English, one is the live lock.

⚠ REACH, STATED RATHER THAN IMPLIED:
  · it reads COMMENTS AND DOCSTRINGS only — the code itself is judged by the lock, not by this law
  · `run_gates.py` why= strings are NOT scanned. They are SHIP NOTES: dated records of what was
    true at that version, and "it shipped locked" remains true of the ship forever. A law that
    reds on an accurate historical record is a law someone deletes. [[regression-guard]] §4
  · test files are NOT scanned except this one's siblings-by-name, so a law may still quote a
    claim it is testing
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_arming as SA  # noqa: E402

#: Prose that claims the lock is SHUT. Deliberately narrow: it must be a claim about a return or a
#: ship state, not any sentence containing the word "locked".
CLOSED_CLAIM = re.compile(r"returns\s+False|may\(\)\s+is\s+False|ships?\s+LOCKED", re.I)

#: Prose that claims the lock is OPEN.
OPEN_CLAIM = re.compile(r"returns\s+True|may\(\)\s+is\s+True|is\s+OPEN\b", re.I)

#: Sentence boundaries. A claim binds to a lock only inside the same sentence.
_SENTENCES = re.compile(r'(?<=[.!?])\s+')

#: Ship notes, not present-tense claims. See REACH above.
SKIP_FILES = {"run_gates.py"}


def _prose_blocks(path):
    """Every contiguous comment block and every docstring, as (line, text)."""
    with io.open(path, encoding="utf-8") as fh:
        src = fh.read()
    out = []
    # contiguous `#` blocks
    cur, start = [], None
    for i, line in enumerate(src.split("\n"), 1):
        s = line.strip()
        if s.startswith("#"):
            if start is None:
                start = i
            cur.append(s.lstrip("#").strip())
        else:
            if cur:
                out.append((start, " ".join(cur)))
            cur, start = [], None
    if cur:
        out.append((start, " ".join(cur)))
    # docstrings
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc:
                out.append((getattr(node, "lineno", 1), " ".join(doc.split())))
    return out


def _production_modules():
    for name in sorted(os.listdir(HERE)):
        if not name.endswith(".py") or name.startswith("test_") or name in SKIP_FILES:
            continue
        yield name


class TestALockStateIsAskedNotAsserted(unittest.TestCase):

    def test_no_comment_contradicts_the_live_lock(self):
        """THE LAW. Prose and may() are two independent sides; they must not disagree."""
        locks = sorted(SA.LOCKS)
        self.assertTrue(
            locks, "self_arming declares no locks at all, so this law scanned nothing and a PASS "
                   "is UNMEASURED. [[zero-needs-a-denominator]]")

        live = {}
        for lk in locks:
            try:
                live[lk] = bool(SA.may(lk)[0])
            except Exception as exc:                      # a lock that cannot be asked is UNKNOWN
                live[lk] = None
                self.fail("may(%r) raised %s — a lock nobody can ask is worse than a stale "
                          "comment, because nothing can ever correct the prose."
                          % (lk, type(exc).__name__))

        scanned, mentions, bad = 0, 0, []
        for name in _production_modules():
            path = os.path.join(HERE, name)
            scanned += 1
            for line, text in _prose_blocks(path):
                # ⚠ SENTENCE SCOPE, NOT BLOCK SCOPE — AND THE FIRST RUN OF THIS LAW PROVED
                # WHY. A contiguous comment block in control_app runs ~40 lines: it names
                # console.pixel_rescue in one paragraph and says "`ui_rescue_due` returns False"
                # in another, about a DIFFERENT function entirely. Judged per block, that reads as
                # a lock-state claim and the law accused correct code. A claim belongs to the lock
                # only when it shares a SENTENCE with it. [[source-reading-guard]] §3
                for lk in locks:
                    if lk not in text:
                        continue
                    near = [s for s in _SENTENCES.split(text) if lk in s]
                    if not near:
                        continue
                    mentions += 1
                    says_shut = any(CLOSED_CLAIM.search(s) for s in near)
                    says_open = any(OPEN_CLAIM.search(s) for s in near)
                    if says_shut and live[lk]:
                        bad.append("%s:%d claims %s is SHUT, but may() is True" % (name, line, lk))
                    if says_open and not live[lk]:
                        bad.append("%s:%d claims %s is OPEN, but may() is False" % (name, line, lk))

        self.assertGreater(
            scanned, 10,
            "only %d production module(s) were scanned — this law measured almost nothing."
            % scanned)
        self.assertGreater(
            mentions, 0,
            "no comment in %d production module(s) mentions any of the %d declared lock(s), so "
            "this law cannot fail for the reason it exists and its PASS is UNMEASURED. If the "
            "prose genuinely stopped naming locks, retire the law rather than leave a green that "
            "means nothing. [[zero-needs-a-denominator]]" % (scanned, len(locks)))

        self.assertEqual(
            bad, [],
            "%d comment(s) state a lock state that disagrees with the live lock:\n  %s\n"
            "self_arming opens a lock WITHOUT anyone editing a file, so a comment restating the "
            "state is guaranteed to go stale. Say what the lock is FOR and let may() say where it "
            "is. MEASURED 2026-09-18: three sites read 'ships LOCKED / may() returns False today' "
            "while console.pixel_rescue had opened on 32 of 32 refused attacks — about the one "
            "mechanism that REPLACES THE WINDOW HE IS LOOKING AT."
            % (len(bad), "\n  ".join(bad)))

    def test_the_detector_can_actually_see_a_claim(self):
        """A detector that matches nothing would make the law above vacuously green."""
        self.assertTrue(CLOSED_CLAIM.search("`may()` returns False today"))
        self.assertTrue(CLOSED_CLAIM.search("this ships LOCKED: nothing changes"))
        self.assertTrue(OPEN_CLAIM.search("may() returns True now"))
        # and it must NOT fire on ordinary prose about locks
        self.assertFalse(CLOSED_CLAIM.search(
            "the lock is the strictest on the board and a wrong verdict replaces his window"))
        self.assertFalse(OPEN_CLAIM.search(
            "it opens itself only once the witness has survived three families of attack"))

    def test_the_prose_sites_still_explain_the_mechanism(self):
        """⚠ THE OTHER DIRECTION. Deleting the explanation would also make the law green."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(
            "console.pixel_rescue", src,
            "control_app no longer names the pixel-rescue lock anywhere. The cheapest way to pass "
            "the law above is to delete every sentence about the lock, which costs the next reader "
            "the whole explanation. The comment must be CORRECTED, not removed.")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "restoring the stale present-tense claim in the rescue loop, while the lock is open",
        "file": "tv/control_app.py",
        "find": "                # ⛔ IT SHIPPED LOCKED, AND THE LOCK HAS SINCE OPENED ITSELF",
        "replace": "                # ⛔ IT SHIPS LOCKED. may() returns False today, for console.pixel_rescue",
        "matches": 1,
    },
    {
        "why": "restoring the same claim in self_arming, where the lock is declared",
        "file": "tv/self_arming.py",
        "find": "    # ⛔ THE BAR IS THE STRICTEST ONE ON THE BOARD",
        "replace": "    # ⛔ console.pixel_rescue ships LOCKED. THE BAR IS THE STRICTEST ONE ON THE BOARD",
        "matches": 1,
    },
]
