# -*- coding: utf-8 -*-
"""A7 — a witness that watches writes happen, because two static walks both measured themselves.

    a filename-adjacency grep        0 writers, all four stores
    an AST walk resolving constants  0 writers, all four stores

Neither follows a path bound in a helper and threaded through arguments (v2507). This is the
runtime half — and it nearly became the THIRD zero:

⚠⚠ ITS OWN DEMO CAUGHT IT BLIND. Patching only `builtins.open` missed `io.open`, which this
codebase uses everywhere, so a module whose entire job is counting writers reported ZERO for a
store it had just watched being written.

⚠ AND IT NAMED A MODULE THAT DOES NOT EXIST. `os.path.abspath("<stdin>")` is inside the tree, so an
interactive frame passed the "is it ours" test, and a blind `[:-3]` reported the writer as `<std`.
A witness naming a module that does not exist is worse than one naming nobody — the first is
believed.
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import write_witness as WW   # noqa: E402


class ItSeesTheWritesItClaimsToWatch(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ww_")
        self.probe = os.path.join(HERE, "_ww_test_probe.py")
        io.open(self.probe, "w", encoding="utf-8").write(
            "import io, os\n"
            "def write(p):\n"
            "    with io.open(p, 'w', encoding='utf-8') as fh:\n"
            "        fh.write('{}')\n"
            "def atomic(p):\n"
            "    t = p + '.tmp'\n"
            "    with io.open(t, 'w', encoding='utf-8') as fh:\n"
            "        fh.write('{}')\n"
            "    os.replace(t, p)\n")
        import importlib
        self.mod = importlib.import_module("_ww_test_probe")
        importlib.reload(self.mod)

    def tearDown(self):
        for f in (self.probe, self.probe + "c"):
            try:
                os.unlink(f)
            except Exception:
                pass

    def _store(self, name):
        return os.path.join(self.tmp, name)

    def test_it_sees_an_io_open_write(self):
        """⚠ THE DEFECT ITS OWN DEMO CAUGHT: patching builtins.open alone misses io.open."""
        with WW.watching() as w:
            self.mod.write(self._store("vault_swept.json"))
        self.assertEqual(
            w.writers("vault_swept.json"), ["_ww_test_probe"],
            "the witness did not see an io.open write. A module whose job is counting writers "
            "reporting zero for a write it watched is the third instrument in this task to "
            "measure itself.")

    def test_it_sees_the_ATOMIC_write_that_never_opens_the_store(self):
        """⚠ These stores are written to `<name>.tmp` and MOVED into place. A witness watching
        only `open` would see the tmp file and never the store — reporting zero writers for a
        store written on every sweep, which is exactly the shape of the two static failures."""
        with WW.watching() as w:
            self.mod.atomic(self._store("retro_triage.json"))
        self.assertEqual(
            w.writers("retro_triage.json"), ["_ww_test_probe"],
            "an atomic write (tmp + os.replace) was not witnessed, so every store written that "
            "way would report no writers at all")

    def test_a_READ_is_not_a_write(self):
        p = self._store("vault_accum.json")
        io.open(p, "w", encoding="utf-8").write("{}")
        with WW.watching() as w:
            with io.open(p, encoding="utf-8") as fh:
                fh.read()
        self.assertEqual(w.writers("vault_accum.json"), [],
                         "a READ was counted as a write, which would make every reader look like "
                         "a second implementation")

    def test_a_frame_that_is_not_a_real_file_is_never_named(self):
        """⚠ abspath('<stdin>') is INSIDE the tree, so the 'is it ours' test passed and a blind
        [:-3] reported the writer as `<std`. A witness naming a module that does not exist is
        worse than one naming nobody."""
        with WW.watching() as w:
            exec(compile("import io\nwith io.open(P,'w',encoding='utf-8') as f: f.write('{}')",
                         "<stdin>", "exec"),
                 {"P": self._store("reel_tombstones.json")})
        names = w.writers("reel_tombstones.json")
        # ⚠ MY FIRST VERSION OF THIS ASSERTED [] AND WAS WRONG. The witness skips the `<stdin>`
        # frame and blames the module that RAN the exec — which is the responsible one, and the
        # answer A7 wants. The law is not "nobody"; it is that every name printed must be a
        # module someone can open.
        self.assertTrue(names, "the exec'd write was attributed to nobody at all")
        for n in names:
            self.assertNotIn("<", n, "a non-file frame was named as a module: %r" % n)
            self.assertTrue(
                os.path.isfile(os.path.join(HERE, n + ".py")),
                "the witness named %r, which is not a module on disk. A witness naming a module "
                "that does not exist is worse than one naming nobody — the first is believed." % n)

    def test_an_UNWATCHED_store_is_None_not_zero(self):
        with WW.watching() as w:
            self.mod.write(self._store("something_else.json"))
        self.assertIsNone(
            w.writers("something_else.json"),
            "an unwatched store reported a writer list. None means NOT ASKED; an empty list means "
            "watched and saw nothing, and those are different facts.")

    def test_it_restores_open_and_replace(self):
        import builtins
        before = (builtins.open, io.open, os.replace)
        with WW.watching():
            pass
        self.assertEqual((builtins.open, io.open, os.replace), before,
                         "the witness left its patches installed — it observes, and a tool that "
                         "stays wrapped around every write in the process is not observation")

    def test_it_never_redirects_or_blocks_a_write(self):
        """It watches the one door with no undo. It must not be able to move it."""
        p = self._store("chron_evidence.json")
        with WW.watching():
            self.mod.write(p)
        self.assertTrue(os.path.isfile(p), "the write did not reach disk while being watched")
        self.assertEqual(io.open(p, encoding="utf-8").read(), "{}",
                         "the witness altered what was written")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
