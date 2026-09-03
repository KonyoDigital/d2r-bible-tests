"""v2476 — nothing in this repo may be copied in a way that can fill his disk.

⚠ THE FAILURE, MEASURED. On 2026-09-03 three review agents each ran

    cp -R /Users/konyo/d2r_bible_tests/tv /tmp/skep_<n>/tv

because my own workflow prompt told them to "work on COPIES under /tmp if you need to sabotage
something". `tv/` holds the reel JPEG store (5.8 GB) and, at the time, a Chrome profile the render
gate never cleaned (1.4 GB). Three copies wrote **20.5 GB in four minutes** onto a volume with
about 9 GB free.

It hit ENOSPC — and then every Bash call in the session, mine and every agent's, failed BEFORE IT
RAN, because the tool could not create its own output file. Nobody could run `df` to see what had
happened, or `rm` to undo it. A full disk is not a slow disk; it is a machine with no shell.

Two fixes, both guarded here:
  · tv/render_check.py uses a TEMPORARY Chrome profile, removed with the browser in a `finally`.
    It was persistent, inside .render_shots, and had reached 1,413 MB beside 63 MB of the PNGs the
    directory exists for.
  · tv/safe_copy.py is the only sanctioned way to copy this tree to scratch. It excludes the heavy
    directories, refuses above a size ceiling, and refuses any copy that would leave the volume
    under a free-space floor.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

import safe_copy as SC  # noqa: E402


def _code_only(path):
    """A file's CODE, with every comment and string literal blanked out.

    Line numbers survive (blanked, not deleted) so a failure still points at the real line.
    """
    import tokenize
    lines = io.open(path, encoding="utf-8").read().split("\n")
    keep = [[" "] * len(l) for l in lines]
    with io.open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            (srow, scol), (erow, _ec) = tok.start, tok.end
            if srow != erow:
                continue
            for i, ch in enumerate(tok.string):
                if scol + i < len(keep[srow - 1]):
                    keep[srow - 1][scol + i] = ch
    return "\n".join("".join(r) for r in keep)


class TheHeavyDirectoriesAreNeverCopied(unittest.TestCase):

    def setUp(self):
        self.src = tempfile.mkdtemp(prefix="sc-src-")
        self.dst = os.path.join(tempfile.mkdtemp(prefix="sc-dst-"), "copy")
        # a miniature of the real tree: source beside footage
        os.makedirs(os.path.join(self.src, "frames"))
        os.makedirs(os.path.join(self.src, ".render_shots", "chrome-profile"))
        os.makedirs(os.path.join(self.src, "sub"))
        io.open(os.path.join(self.src, "real.py"), "w").write("x = 1\n")
        io.open(os.path.join(self.src, "sub", "also.py"), "w").write("y = 2\n")
        io.open(os.path.join(self.src, "frames", "big.jpg"), "w").write("J" * 200000)
        io.open(os.path.join(self.src, ".render_shots", "chrome-profile", "c"), "w").write("C" * 200000)

    def tearDown(self):
        for p in (self.src, os.path.dirname(self.dst)):
            shutil.rmtree(p, ignore_errors=True)

    def test_the_reel_store_is_excluded(self):
        """The 5.8 GB that caused it. If this ever passes through, the machine dies again."""
        rc = SC.copy(self.src, self.dst, say=lambda m: None)
        self.assertEqual(rc, 0, "the copy refused a tiny fixture")
        self.assertFalse(os.path.exists(os.path.join(self.dst, "frames")),
                         "frames/ was copied — that is his footage and it is gigabytes")

    def test_the_render_profile_is_excluded(self):
        SC.copy(self.src, self.dst, say=lambda m: None)
        self.assertFalse(os.path.exists(os.path.join(self.dst, ".render_shots")),
                         ".render_shots was copied — it held a 1.4 GB Chrome profile")

    def test_the_source_it_is_FOR_is_still_copied(self):
        """An exclusion list that excludes the point is not a fix. [[unknown-stays-unknown]]"""
        SC.copy(self.src, self.dst, say=lambda m: None)
        self.assertTrue(os.path.exists(os.path.join(self.dst, "real.py")),
                        "the source file a sabotage test needs was not copied")
        self.assertTrue(os.path.exists(os.path.join(self.dst, "sub", "also.py")),
                        "nested source was not copied")

    def test_plan_reports_what_it_skips(self):
        """A silent exclusion is how someone concludes the copy is complete."""
        files, total, skipped = SC.plan(self.src)
        self.assertIn("frames", skipped)
        self.assertIn(".render_shots", skipped)
        self.assertLess(total, 100000, "the plan counted the heavy files it claims to skip")

    def test_the_heavy_list_names_the_reel_store_and_the_shots(self):
        """Pin the two that actually caused it, not the whole list — the rest may evolve."""
        for name in ("frames", ".render_shots"):
            self.assertIn(name, SC.HEAVY,
                          "%r is no longer excluded; copying tv/ would carry it again" % name)


class ItRefusesRatherThanFillingTheDisk(unittest.TestCase):

    def setUp(self):
        self.src = tempfile.mkdtemp(prefix="sc-src2-")
        self.dst = os.path.join(tempfile.mkdtemp(prefix="sc-dst2-"), "copy")
        io.open(os.path.join(self.src, "a.py"), "w").write("z = 3\n")
        self.said = []

    def tearDown(self):
        for p in (self.src, os.path.dirname(self.dst)):
            shutil.rmtree(p, ignore_errors=True)

    def test_it_refuses_when_the_copy_would_leave_too_little_free(self):
        """The floor is the point: at zero bytes nothing runs, not even the cleanup."""
        real = SC.KEEP_FREE_MB
        try:
            SC.KEEP_FREE_MB = 10 ** 9      # pretend the volume is tiny
            rc = SC.copy(self.src, self.dst, say=self.said.append)
        finally:
            SC.KEEP_FREE_MB = real
        self.assertEqual(rc, 1, "it copied even though that would leave the volume under the floor")
        self.assertFalse(os.path.exists(self.dst), "a refused copy still wrote to the destination")
        self.assertTrue(any("REFUSED" in m for m in self.said))

    def test_it_refuses_above_the_size_ceiling(self):
        real = SC.MAX_MB
        try:
            SC.MAX_MB = 0
            rc = SC.copy(self.src, self.dst, say=self.said.append)
        finally:
            SC.MAX_MB = real
        self.assertEqual(rc, 1, "it copied past its own ceiling")
        self.assertFalse(os.path.exists(self.dst))

    def test_it_refuses_a_destination_inside_the_repo(self):
        """Otherwise the next walk copies the copy."""
        rc = SC.copy(self.src, os.path.join(SC.REPO, "scratch_x"), say=self.said.append)
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(os.path.join(SC.REPO, "scratch_x")))

    def test_it_refuses_to_overwrite_an_existing_destination(self):
        os.makedirs(self.dst)
        rc = SC.copy(self.src, self.dst, say=self.said.append)
        self.assertEqual(rc, 2, "it wrote into a directory that already existed")


class TheRenderProfileIsTemporary(unittest.TestCase):

    def test_the_profile_is_not_a_persistent_directory_in_the_repo(self):
        """It reached 1,413 MB there, beside 63 MB of the PNGs that directory is for.

        ⚠ READ BY AST, NOT BY TEXT, AND BOTH TEXT ATTEMPTS FAILED FOR OPPOSITE REASONS.
        Searching raw source went red with the fix correctly in place, because render_check's own
        comment SAYS `os.path.join(SHOTS, "chrome-profile")` while explaining what it stopped
        doing. Stripping comments fixed that and broke the other half: the stripper blanks STRING
        LITERALS too, so `tempfile.mkdtemp(prefix="render_check-profile-")` became
        `tempfile.mkdtemp(prefix=)` and the positive assertion could not find it either.
        A question about what a name is ASSIGNED is a question about structure, so ask the
        structure. [[source-reading-guard]]
        """
        import ast

        tree = ast.parse(io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read())
        assigns = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == "_CHROME_PROFILE":
                        assigns.append(node.value)
        self.assertTrue(assigns, "_CHROME_PROFILE is never assigned — has the profile moved?")

        made_temp = False
        for v in assigns:
            if isinstance(v, ast.Call):
                f = v.func
                name = getattr(f, "attr", None) or getattr(f, "id", None)
                mod = getattr(getattr(f, "value", None), "id", None)
                if name == "mkdtemp" and (mod in (None, "tempfile")):
                    made_temp = True
                if name == "join" and any(
                        isinstance(a, ast.Name) and a.id == "SHOTS" for a in v.args):
                    self.fail("the render gate assigns _CHROME_PROFILE from os.path.join(SHOTS, "
                              "...) again — a persistent profile inside .render_shots. Chrome "
                              "fills it every run and nothing empties it; it reached 1.4 GB and "
                              "ENOSPC'd his Mac.")
        self.assertTrue(
            made_temp,
            "_CHROME_PROFILE is no longer created with tempfile.mkdtemp, so the profile is not "
            "temporary and nothing guarantees it is ever removed.")

    def test_the_teardown_removes_it_even_when_the_kill_fails(self):
        """On the happy path only is how it survived every crash and grew for months."""
        import inspect

        import render_check as R
        src = inspect.getsource(R._chrome_down)
        self.assertIn("finally:", src,
                      "the profile is removed outside a finally, so any raise leaks it")
        self.assertIn("rmtree", src, "the teardown no longer removes the profile")
        # and it must only ever remove something it made
        self.assertIn("render_check-profile-", src,
                      "the teardown does not check the directory is one this file created — a "
                      "cleanup that does not verify its target is how a cleanup deletes the wrong "
                      "thing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
