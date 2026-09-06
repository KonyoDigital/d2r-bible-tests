# -*- coding: utf-8 -*-
"""v2708 — THE CONSOLE REPORTED THREE VERSIONS AND ALL THREE READ THE WORKING TREE.

His console EXECS this working tree — every save is a deploy. So the page in front of him can be
bytes that were never pushed, and for over an hour of the session this file was written in, it
was: `/api/status` answered `ver=v2706` while `origin/main` shipped v2705, silently.

Nothing could have told him. The status payload carried:

    ver        the app's own stamp          <- working tree
    bibleVer   bible.html's D2R_BUILD       <- working tree
    agentVer   the agent stamp              <- working tree
    shipVer    the WINDOWS ship record      <- None on his Mac, always

Three numbers that agree with each other and can all be wrong together. That is mutual agreement
mistaken for corroboration — three readings of ONE source is n=1, not n=3, which is the same
inflation [[build-the-heart-and-census-everywhere]] warns about for confluence.

He described the symptom himself while closing an unrelated row: *"something like unsyncs and it
needs a restart or something to fetch it"*. [[stale-render]] [[execs-the-working-tree]]

=== WHAT THIS FILE PINS, AND WHY EACH LAW EXISTS ===

1. `liveVer` must not be read from the working tree. If it were, it would agree with `bibleVer`
   by construction and the divergence it exists to expose could never appear.
2. It must carry the AGE OF THE REF. `origin/main` is a LOCAL ref and can be stale — the
   pre-push hook records that in its own words, "not the local origin/main ref (which is stale,
   and is simply absent in a clone whose remote is not named 'origin' — that skipped the gate
   entirely)". A confidently wrong "live version" is WORSE than none: it would say the page
   matches production when it does not. [[stale-reading]]
3. An unaskable question answers None, never a guess. No git, no remote ref, an unparseable ship
   file — every one of those is nobody-looked, which is a different fact from a version that
   genuinely matches. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

SRC = os.path.join(HERE, "control_app.py")


def _decomment(src):
    """-> src with docstrings and hash comments removed, so PROSE cannot trip a CODE check."""
    src = re.sub(r'"' + r'""(?:.|\n)*?"' + r'""', " ", src)
    src = re.sub(r"'" + r"''(?:.|\n)*?'" + r"''", " ", src)
    return re.sub(r"(?m)#.*$", " ", src)


def _fn_src(name):
    """The named function's source, bound at both ends by its own indentation.

    Not a fixed window: a window past the region reads as absent and would grade a truncated
    body, which is [[source-window-shortcut]].
    """
    s = io.open(SRC, encoding="utf-8").read()
    i = s.find("def %s(" % name)
    if i < 0:
        raise AssertionError(
            "GUARD CANNOT GRADE: `def %s(` is not in control_app.py. It was renamed or removed — "
            "fix this test before trusting any verdict it prints." % name
        )
    j = s.find("\ndef ", i + 1)
    return s[i:j if j > 0 else len(s)]


class LiveVersionIsNotTheWorkingTree(unittest.TestCase):

    def setUp(self):
        self.raw = _fn_src("_published_ver")
        # ⚠⚠ JUDGE THE CODE, NOT THE PROSE — and this guard tripped on its OWN docstring the
        # first time it ran. That docstring explains that `git show origin/main:bible.html` is
        # 6 MB and must NOT be used; the substring check then found that filename in the very
        # sentence forbidding it and reported the function as reading the working tree. This is
        # [[source-reading-guard]] verbatim — "the comment that trips the guard is usually the
        # one describing the fix" — and it fired within a minute of the guard existing.
        self.fn = _decomment(self.raw)

    def test_it_does_not_read_the_working_tree(self):
        """The whole point. A working-tree read would agree with bibleVer by construction."""
        for bad in ("bible.html", "WINDOWS_SHIP.json\"", "open(os.path.join(REPO"):
            self.assertNotIn(
                bad, self.fn.replace("origin/main:tv/WINDOWS_SHIP.json", ""),
                "_published_ver reads %r from the working tree. Then `liveVer` agrees with "
                "`bibleVer` by construction and the divergence this field exists to expose can "
                "never appear — a gate that cannot fail." % bad
            )

    def test_it_asks_the_REMOTE_ref(self):
        self.assertIn("origin/main:", self.fn,
                      "_published_ver does not ask origin/main, so it is not reporting what "
                      "shipped")

    def test_it_carries_the_age_of_the_ref(self):
        """A stale ref must read as stale, not as a confident answer."""
        self.assertIn("age", self.fn,
                      "the age of the ref is not reported. origin/main is a LOCAL ref and can be "
                      "stale; a confidently wrong live version is worse than none, because it "
                      "says the page matches production when it does not")
        self.assertRegex(
            self.fn.replace("\n", " "), r"git.{0,40}log.{0,60}origin/main",
            "the age is not taken from the REF itself. Timing the read instead of the thing is "
            "the stale-reading defect exactly: it would report a fresh read of a month-old ref"
        )

    def test_unaskable_answers_None_not_a_guess(self):
        self.assertRegex(
            self.fn.replace("\n", " "), r"except Exception:\s*ver, age = None, None",
            "an exception path does not resolve to None. No git, no remote ref, an unparseable "
            "ship file — each is nobody-looked, which is a different fact from a version that "
            "matches, and collapsing them is a lie with no author"
        )

    def test_the_status_payload_carries_both(self):
        s = io.open(SRC, encoding="utf-8").read()
        for k in ('"liveVer"', '"liveVerAge"'):
            self.assertIn(k, s, "%s is not in the status payload, so nothing on his screen can "
                                "show the divergence" % k)

    def test_it_is_cached_so_the_console_does_not_fork_git_per_poll(self):
        """The console polls status; an uncached subprocess per poll is the 172s-answered-every-12s
        shape that once saturated his machine. [[poll-slower-than-its-interval]]"""
        # ⚠ NOT `assertIn("_LIVE_VER_CACHE")` — that was the first cut and it was VACUOUS.
        # Deleting the early return leaves `_LIVE_VER_CACHE.update(...)` behind, so the name is
        # still there while git forks on every poll. Proven: that sabotage stayed GREEN. The law
        # is the EARLY RETURN, so this pins the return, not the mention.
        self.assertRegex(
            self.fn.replace("\n", " "),
            r"if now - _LIVE_VER_CACHE\[.t.\] <.{0,12}:\s*return",
            "_published_ver has no early return on a warm cache, so it forks git on EVERY call. "
            "The status endpoint is polled, and an unbounded subprocess per poll is the "
            "172s-answered-every-12s shape that once saturated his machine"
        )

    def test_it_really_answers_on_this_repo(self):
        """Anti-vacuity: the laws above are all source-shaped, so at least one must EXECUTE."""
        import control_app as ca
        ver, age = ca._published_ver()
        if ver is None:
            self.skipTest("no origin/main ref on this venue — the function correctly answered "
                          "None rather than guessing, which is the behaviour test_unaskable pins")
        self.assertRegex(str(ver), r"^v\d+", "liveVer is not a version string: %r" % (ver,))
        self.assertIsNotNone(age, "a version was returned with no ref age beside it")
        self.assertGreaterEqual(age, 0, "the ref age is negative: %r" % (age,))


if __name__ == "__main__":
    unittest.main(verbosity=2)
