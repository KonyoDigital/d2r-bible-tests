# -*- coding: utf-8 -*-
"""THE VAULT'S SAVE MAY ONLY COPY, AND A PARTIAL SAVE IS NOT A SAVE.

Konyo, 2026-09-13: *"its fine i want it zeroed and able to be brought back based on like last recent
save ledger wise... by day and timestamp ... but vault is separate and it can be restored or wiped
clean with a safeguarded button that asks twice"*.

The wipe he is asking for is the most destructive act in this console — six stores, gone on a click.
The ONLY thing that makes it safe to build is a save that is already proven to work, so this file
pins the save and pins it hard.

⚠⚠ THE MODULE MAY NOT CONTAIN A DELETE, BY CONSTRUCTION AND NOT BY SETTING. `hover_drive` earns its
safety the same way — it never BUILDS a mouse-down event, so no flag or future caller can make it
click. Here: no `remove`, no `unlink`, no `rmtree`, no `open(..., "w")` over a store. A backup module
that can also destroy is one bug away from being the thing it was built to protect against, and the
wipe will live somewhere else, behind his twice-asking button.

⚠ A PARTIAL SAVE IS THE DANGEROUS SHAPE, not a failed one. A save that copies five of six stores and
says nothing restores as a complete-looking vault that is silently short — and it would be restored
at exactly the moment nobody can check, right after a wipe. So every file is read back at its source
size and ANY mismatch fails the WHOLE save rather than keeping a good-looking subset.
[[zero-needs-a-denominator]]

⚠ THE STORES ARE NAMED, NEVER GLOBBED. A `vault*.json` glob would sweep in whatever a future feature
happens to call vault-something, and a backup whose contents drift is one nobody can reason about
restoring. Each name here has a declared owner in store_owners.py.

⚠ AND THE RETENTION IS REUSED, NOT RE-DERIVED. 48h rolling + one keeper per UTC day for 90 days is
`_ledger_backup_prune`'s policy, sized in v3009 (#81) from his real 2026-09-08 loss — noticed three
days late, with the oldest backup then on disk 69 HOURS too young to answer "which save predates
this". Two numbers invented here instead would be a second policy free to disagree with the first.
[[copy-drift]]
"""
import ast
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = "vault_backup.py"

# every call that could remove or truncate something of his
DESTRUCTIVE = {"remove", "unlink", "rmtree", "rmdir", "truncate", "move", "replace"}


class TestTheVaultSaveCanOnlyCopy(unittest.TestCase):

    def _tree(self):
        with io.open(os.path.join(HERE, MODULE), encoding="utf-8") as fh:
            return ast.parse(fh.read())

    def test_it_cannot_delete_anything(self):
        """PARSED. A grep would be satisfied by the word appearing in a comment saying it must not."""
        found = []
        for node in ast.walk(self._tree()):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name in DESTRUCTIVE:
                found.append((name, node.lineno))
        self.assertEqual(found, [],
                         "vault_backup calls %s — this module may only COPY. The wipe is a separate, "
                         "twice-asking act; a backup that can also destroy is one bug away from "
                         "being the thing it protects against" % found)
        print("no destructive call in %s (checked %d name(s))" % (MODULE, len(DESTRUCTIVE)))

    def test_it_never_opens_a_store_for_writing(self):
        for node in ast.walk(self._tree()):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
            if name != "open":
                continue
            for a in list(node.args[1:]) + [k.value for k in node.keywords if k.arg == "mode"]:
                mode = getattr(a, "value", None)
                if isinstance(mode, str) and ("w" in mode or "a" in mode or "+" in mode):
                    self.fail("vault_backup opens something in %r at line %d — it may only read "
                              "his stores and write COPIES" % (mode, node.lineno))
        print("no store is opened for writing")

    def test_the_stores_are_named_not_globbed(self):
        import vault_backup as VB
        self.assertIsInstance(VB.STORES, tuple, "STORES must be a fixed tuple, not a computed list")
        self.assertGreaterEqual(len(VB.STORES), 5, "the store list shrank — was six")
        for n in VB.STORES:
            self.assertNotIn("*", n, "%r is a glob; a backup whose contents drift cannot be "
                                     "reasoned about when restoring" % n)
            self.assertTrue(n.endswith(".json"), "%r is not a json store" % n)
        print("STORES: %d named files, no globs" % len(VB.STORES))

    def test_a_short_copy_fails_the_whole_save(self):
        """The dangerous shape is a save that looks complete and is short."""
        src = io.open(os.path.join(HERE, MODULE), encoding="utf-8").read()
        i = src.find("def save(")
        j = src.find("\ndef ", i + 5)
        body = "\n".join(l.split("#", 1)[0] for l in src[i:j].splitlines())
        self.assertIn("getsize", body,
                      "save() no longer reads the copy back — an unverified backup is a promise, "
                      "and this one exists so a wipe can be undone")
        self.assertIn("return None", body,
                      "save() has no refusal path; a partial copy would be kept")
        print("save() verifies each copy and refuses the whole save on a mismatch")

    def test_plan_prune_writes_nothing(self):
        src = io.open(os.path.join(HERE, MODULE), encoding="utf-8").read()
        i = src.find("def plan_prune(")
        j = src.find("\ndef ", i + 5)
        body = src[i:j]
        for bad in ("shutil.", "os.remove", "os.rmdir", ".write("):
            self.assertNotIn(bad, body, "plan_prune touches the disk via %r — it must only plan" % bad)
        import vault_backup as VB
        p = VB.plan_prune()
        self.assertTrue(p.get("ok"))
        self.assertIn("NOTHING was written", p.get("say", ""))
        print("plan_prune: %s" % p["say"])

    def test_the_retention_policy_is_the_ledgers_own(self):
        """48h + 90d came from his real loss. A second policy free to drift is not wanted."""
        import vault_backup as VB
        self.assertEqual(VB.KEEP_RECENT_H, 48,
                         "the rolling window moved off _ledger_backup_prune's measured 48h")
        self.assertEqual(VB.KEEP_DAILY_DAYS, 90,
                         "the daily-keeper horizon moved off the measured 90 days")
        print("retention: %dh rolling · %d-day keepers — the ledger's own numbers"
              % (VB.KEEP_RECENT_H, VB.KEEP_DAILY_DAYS))


RED_PROOF = [
    {
        "why": "the save stops reading its copies back, so a short or truncated store is kept and "
               "restores later as a complete-looking vault that is silently missing rows — at the "
               "one moment nobody can check, right after a wipe",
        "file": "vault_backup.py",
        "find": "            back = os.path.getsize(dst)",
        "replace": "            back = size",
        "matches": 1,
    },
    {
        "why": "the named store list becomes a glob, so the backup's contents drift with whatever "
               "a future feature calls vault-something and nobody can reason about a restore",
        "file": "vault_backup.py",
        "find": '    "vault_accum.json",          # what the vault sweep accumulated per reel   (vault_retro)',
        "replace": '    "vault_*.json",',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
