# -*- coding: utf-8 -*-
"""A7 — a store's declaration must describe the code, and the registry must not count itself.

⚠⚠ THIS FILE EXISTS BECAUSE THE REGISTRY CAUGHT ITSELF ON ITS FIRST RUN. `store_owners` names every
store — that IS the declaration — so it appeared as an undeclared toucher of all four. Excluding it
is honest ONLY while it never actually opens one, and that is asserted here rather than promised in
a comment. This console has produced the counts-itself defect before: a deriver that counted itself
as a watcher.

⚠ AND THE REGISTRY DOES NOT PROVE SINGLE-WRITER. Two static attempts to measure writers returned
ZERO for all four stores — a filename-adjacency grep, then an AST walk resolving path constants —
because paths are bound in helpers and threaded through arguments. Both zeros measured the
instrument. The registry checks COUPLING, which is checkable, and says so.
[[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import store_owners as SO   # noqa: E402


class TheDeclarationMustDescribeTheCode(unittest.TestCase):

    def test_every_module_touching_a_store_is_declared(self):
        r = SO.audit()
        self.assertTrue(r["rows"], "BASELINE: no store audited, so this law is vacuous")
        bad = [(x["store"], x["undeclared"]) for x in r["rows"] if x["undeclared"]]
        self.assertFalse(
            bad,
            "%d store(s) are touched by a module nothing declares: %s. A second implementation "
            "should have to be argued in, not appear." % (len(bad), bad))

    def test_a_declared_reader_that_no_longer_touches_it_is_reported(self):
        stale = [(x["store"], x["stale"]) for x in SO.audit()["rows"] if x["stale"]]
        self.assertFalse(
            stale,
            "%d stale allowance(s): %s. A list that has stopped describing the code is how the "
            "next undeclared module slips in under a name nobody re-checked." % (len(stale), stale))

    def test_the_declared_owner_actually_mentions_its_store(self):
        for row in SO.audit()["rows"]:
            self.assertTrue(
                row["ownerMentionsIt"],
                "%r is declared owner of %s and never mentions it. A declaration naming a module "
                "that has never heard of the file is worse than no declaration."
                % (row["owner"], row["store"]))

    def test_every_reader_carries_a_REASON_not_just_a_name(self):
        """"It appears in the file" is not a reason. The list earns its keep by making someone
        say out loud why another module needs this store."""
        for store, spec in SO.STORES.items():
            for mod, why in spec["readers"].items():
                self.assertTrue(
                    len(str(why or "").strip()) > 15,
                    "%s is allowed to touch %s with no real reason given (%r)" % (mod, store, why))

    def test_the_registry_does_not_read_or_write_any_store_it_names(self):
        """⚠ THE EXCLUSION IS ONLY HONEST WHILE THIS IS TRUE.

        `store_owners` skips itself when counting, because naming a store IS its job. The moment it
        opens one, that exclusion hides a real coupling — so the exclusion is paid for here.
        """
        src = io.open(os.path.join(HERE, "store_owners.py"), encoding="utf-8").read()
        body = src.split('"""', 2)[-1]
        for store in SO.STORES:
            for verb in ("io.open(", "open(", "json.load", "json.dump"):
                pat = re.compile(re.escape(verb) + r"[^\n]{0,80}" + re.escape(store))
                self.assertIsNone(
                    pat.search(body),
                    "store_owners appears to %s the store %s it merely declares. It excludes "
                    "itself from the coupling count, so that would hide a real coupling."
                    % (verb.rstrip("("), store))

    def test_the_registry_is_excluded_but_nothing_else_is(self):
        """⚠ BASELINE: the exclusion must be narrow, or it becomes a place to hide modules."""
        mods = SO._modules()
        self.assertNotIn("store_owners", mods, "the registry counts itself again")
        for expected in ("control_app", "frame_authority", "reel_retention"):
            self.assertIn(expected, mods,
                          "%r vanished from the module graph — the exclusion has widened beyond "
                          "the registry itself" % expected)

    def test_it_reports_and_never_fails_a_build(self):
        """[[the standing constraint]] — nothing here may block a button or a push."""
        src = io.open(os.path.join(HERE, "store_owners.py"), encoding="utf-8").read()
        self.assertNotIn("sys.exit(1)", src)
        self.assertNotIn("raise SystemExit(1)", src)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
