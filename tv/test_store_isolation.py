"""v1965 — EVERY GRAIL STORE IS ISOLATED PER WORLD, OR IT IS LISTED HERE ON PURPOSE.

bible.html gives a non-owner browser its own world: keys in _WP_FORKED get an `I·<id8>·` prefix
(and `IL·` on ladder), so a guest's grail never lands in the owner's keys. Keys in neither fork set
stay BARE in every world — deliberately, so that "a bare key exists" can never be read as ownership.

THE DEFECT THIS PINS. That set was correct for every store that existed when it was written, and was
never extended to the ones added since. Measured 2026-08-22: 29 of the 41 stores written through LSR
are in a fork set, and SEVEN grail-ish stores are not — including `d2r_chronicleInboxLog`, the
Routing Ledger, which on a guest world writes into the key the owner reads.

WHY THIS TEST ALLOWS THEM RATHER THAN FAILING. Adding keys to _WP_FORKED is not free: it orphans
whatever a guest world already wrote under the bare name, and this repo has migration machinery
precisely because that cost is real. Changing the namespacing is Konyo's call. What is NOT his call
is whether the next store added repeats the pattern silently — so the seven are listed here by name,
and an EIGHTH fails this test.

⚠ ITS OWN REACH, STATED. This reads `LSR.setItem('d2r_…')` string literals. A store written through
a variable is invisible to it, so the count is a floor, not a census. That is why the assertion is
"no NEW unisolated store", not "every store is isolated". [[source-reading-guard]]
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402

# v1965 — this suite prints the `I·<id8>·` prefix and em-dashes in its failure messages. On a
# non-UTF-8 console (his Windows cousin) that crashes WHILE REPORTING, so a clean tree would exit
# non-zero for a reason that has nothing to do with the code. Caught by test_control's own
# encoding-safety gate the first time this file ran in the suite.
_console_safe_enable()

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")

# The seven that were already unisolated when this guard was written. Each is grail-ish and each
# predates the guard; listing them makes the gap visible instead of forgotten.
KNOWN_UNISOLATED = {
    "d2r_chronAdopted",
    "d2r_chronicleInbox",
    "d2r_chronicleInboxLog",   # the Routing Ledger — the "visual backend"
    "d2r_gameFound",           # the game's First Found date + dropper
    "d2r_setRepairAt",
    "d2r_setRepairKept",
    "d2r_setRepairRemoved",
}

GRAILISH = re.compile(r"grail|found|set|rw|chron|repair|vault|mule|stash", re.I)


def _read():
    with open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _fork_sets(src):
    lp = re.search(r"window\._LP_FORKED\s*=\s*new Set\(\[(.*?)\]\)", src, re.S)
    wp = re.search(r"window\._WP_FORKED\s*=\s*new Set\((.*?)\);", src, re.S)
    names = set()
    for blob in (lp.group(1) if lp else "", wp.group(1) if wp else ""):
        names |= {a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", blob)}
    return names


def _written(src):
    return (set(re.findall(r"LSR\.setItem\(\s*'(d2r_[A-Za-z0-9_]+)'", src))
            | set(re.findall(r'LSR\.setItem\(\s*"(d2r_[A-Za-z0-9_]+)"', src)))


class TestGrailStoresAreIsolatedPerWorld(unittest.TestCase):
    def setUp(self):
        if not os.path.isfile(BIBLE):
            self.skipTest("bible.html is not on this machine")
        self.src = _read()

    def test_the_fork_sets_still_parse(self):
        """If either Set stops parsing, every assertion below silently measures nothing."""
        names = _fork_sets(self.src)
        self.assertGreater(len(names), 40, "fork sets did not parse — this guard would measure air")
        self.assertIn("d2r_foundLog", names, "_WP_FORKED lost the found ledger")
        self.assertIn("d2r_setPieces", names, "_WP_FORKED lost the set store")

    def test_no_NEW_grail_store_escapes_isolation(self):
        """An eighth unisolated grail store is a regression; the seven below are a recorded decision."""
        forked = _fork_sets(self.src)
        written = _written(self.src)
        self.assertGreater(len(written), 25, "the setItem scan found too little — check its reach")
        unisolated = {k for k in written if k not in forked and GRAILISH.search(k)}
        new = unisolated - KNOWN_UNISOLATED
        self.assertEqual(
            new, set(),
            "a NEW grail store is not isolated per world: %s — add it to _WP_FORKED, or to "
            "KNOWN_UNISOLATED with the reason" % sorted(new))

    def test_the_known_gap_has_not_quietly_widened_or_closed(self):
        """If one of the seven gets isolated, this list must shrink — a stale allowlist hides the next."""
        forked = _fork_sets(self.src)
        now_isolated = sorted(k for k in KNOWN_UNISOLATED if k in forked)
        self.assertEqual(
            now_isolated, [],
            "these are isolated now and must be removed from KNOWN_UNISOLATED: %s" % now_isolated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
