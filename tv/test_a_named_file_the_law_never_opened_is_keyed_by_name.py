# -*- coding: utf-8 -*-
"""REG-2640 (#42 P3-fine) — A NAMED FILE THE LAW NEVER OPENED IS KEYED BY ITS NAME, NOT ITS BYTES; ONE IT READ RE-PROVES.

MEASURED 2026-10-24 on v3796 r6 (8 lines of CSS in control_ui.html): the P3 key moved for 5,012 of 6,327 proofs and
only 856 were reusable, so the Mac pre-prove re-proved from nothing. 3,474 of the moved proofs carried control_ui.html
only because a module in their import closure SPELLS its name; the law never opens it. heart2 now traces every
push-time law run (an audit hook installed by a sitecustomize on PYTHONPATH) and banks a PROVEN under a v2 key that
keys such a never-opened, never-stat'd named data file by name only. Every byte a run DID read is still keyed.

The cases: an edit to a file the law never touches IS reused (the point); an edit to one it opens, stats, or reaches
through a child the trace cannot see is NOT (soundness); the off switch and the v1 compatibility hold.

EVERYTHING HERE IS A FIXTURE: the throwaway repo copy of test_a_proven_verdict_is_reused_only_on_identical_bytes, with
one more file (tv/page.css) that a helper module NAMES and the law may or may not read. Nothing of his is read.
[[regression-guard]] [[unknown-stays-unknown]]
RED_PROOF below.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import heart2 as H  # noqa: E402
import test_a_proven_verdict_is_reused_only_on_identical_bytes as P3  # noqa: E402  one fixture, never re-derived

#: what the law does with tv/page.css, spliced into the fixture law right after it knows where it is
_READS = {
    "never": "",
    "opens": "with open(os.path.join(here, 'page' + '.css')) as _fh: _fh.read()\n",
    "stats": "os.path.getsize(os.path.join(here, 'page' + '.css'))\n",
    "shell": "import subprocess; subprocess.run(['cat', os.path.join(here, 'page' + '.css')], capture_output=True)\n",
    "imports": "sys.path.insert(0, here); import named_mod\n",
    "direct": ("os.posix_spawn(sys.executable, [sys.executable, '-S', '-c', 'open(%r).read()' % "
               "os.path.join(here, 'page' + '.css')], dict(os.environ)); os.wait()\n"),
    "forkexec": ("import multiprocessing as _mp\n"
                 "if __name__ == '__main__':\n"
                 "    _mp.set_start_method('spawn'); _q = _mp.Process(target=print); _q.start(); _q.join()\n"),
    "pure": "import subprocess; subprocess.run(['true'])\n",
    "python": ("import subprocess; subprocess.run([sys.executable, '-c', 'open(%r).read()' % "
               "os.path.join(here, 'page' + '.css')])\n"),
    # -W takes a value, so a reader of the flags stops there and never sees the -S: the child is counted as traced,
    # says no hello, and only the hello count can tell
    "hidden": ("import subprocess; subprocess.run([sys.executable, '-W', 'ignore', '-S', '-c', 'open(%r).read()' % "
               "os.path.join(here, 'page' + '.css')])\n"),
}


def _law(how):
    head, sep, rest = P3._LAW.partition("here = os.path.dirname(os.path.abspath(__file__))\n")
    assert sep, "the P3 fixture law moved"
    return head + sep + _READS[how] + rest


class _Case(P3._Case):

    def setUp(self):
        super(_Case, self).setUp()
        self.tree.files["tv/helper_p3.py"] = "SALT = 1\nSTYLE = 'page.css'   # named, so it is in the static key\n"
        self.tree.files["tv/page.css"] = ".a { color: red }\n"
        # a module the helper only NAMES (as run_gates names every law): no AST import, so not in the closure
        self.tree.files["tv/helper_p3.py"] += "OTHER = 'named_mod.py'\n"
        self.tree.files["tv/named_mod.py"] = "X = 1\n"
        self._tracked = H._tracked_files
        H._tracked_files = lambda repo=None: None        # the fixture is not in git: every named file counts

    def tearDown(self):
        H._tracked_files = self._tracked
        H._TRACES.clear()
        super(_Case, self).tearDown()

    def law(self, how):
        self.tree.files["tv/" + P3._FILE] = _law(how)

    def cold_then_edit(self, how, env=None):
        self.law(how)
        H._TRACES.clear()
        results, per, stopped, runs, said = self.push(env=env)
        self.assertEqual((results, stopped), ({P3._GATE: H.PROVEN}, []), "\n".join(said))
        self.tree.files["tv/page.css"] = ".a { color: blue }   /* a one-line CSS edit */\n"
        H._TRACES.clear()                                 # the next push is another process
        return self.push(env=env)


class ANamedFileTheLawNeverOpenedIsKeyedByName(_Case):

    def test_an_edit_to_a_named_file_the_law_never_opened_reuses_the_proven(self):
        """★ THE POINT: page.css is in the key by name (a helper spells it), the law never opens it, and a CSS edit to
        it re-proves nothing - while the entry says which input it keyed by name"""
        results, per, stopped, runs, said = self.cold_then_edit("never")
        self.assertReused(runs, results, said, "an edit to a file no run of the law opened")
        unread = [e.get("unread") for e in self.entries().values()]
        self.assertEqual(unread, [["tv/named_mod.py", "tv/page.css"]], "the banked entry does not name what it keyed by name: %s" % unread)

    def test_an_edit_to_a_file_the_law_opened_is_proved_again(self):
        """★ SOUNDNESS: the law reads page.css - its bytes are an input, and the edit re-proves"""
        results, per, stopped, runs, said = self.cold_then_edit("opens")
        self.assertRan(runs, said, "an edit to a file the law opened")

    def test_an_edit_to_a_file_the_law_only_stats_is_proved_again(self):
        """★ os.path.getsize reads a size without an open: a stat is a read"""
        results, per, stopped, runs, said = self.cold_then_edit("stats")
        self.assertRan(runs, said, "an edit to a file the law stat'd")

    def test_a_child_the_trace_cannot_see_drops_nothing(self):
        """★ `cat` reads page.css in a process no hook is in: nothing is dropped, the edit re-proves"""
        results, per, stopped, runs, said = self.cold_then_edit("shell")
        self.assertRan(runs, said, "an edit read through an untraced child")

    def test_a_python_child_is_traced_too(self):
        """★ a python child inherits the hook: its open counts, the edit re-proves"""
        results, per, stopped, runs, said = self.cold_then_edit("python")
        self.assertRan(runs, said, "an edit read by a traced python child")

    def test_a_python_child_that_never_says_hello_drops_nothing(self):
        """★ a python child started with -S never loads the hook; the flags reader misses it (-W takes a value), so
        only the hello count stands between it and a stale PROVEN"""
        results, per, stopped, runs, said = self.cold_then_edit("hidden")
        self.assertRan(runs, said, "an edit read by a python child that was never traced")

    def test_an_edit_to_a_named_module_nothing_imported_reuses_the_proven(self):
        """★ the third input of v3796 r6: a law .py run_gates only names. Not imported, not opened: keyed by name"""
        self.law("never")
        H._TRACES.clear()
        r0 = self.push()
        self.assertEqual(r0[0], {P3._GATE: H.PROVEN}, "\n".join(r0[4]))
        self.tree.files["tv/named_mod.py"] = "X = 2   # another law's 47 new lines\n"
        H._TRACES.clear()
        results, per, stopped, runs, said = self.push()
        self.assertReused(runs, results, said, "an edit to a module the law never imported")

    def test_an_edit_to_a_named_module_the_law_imports_at_run_time_is_proved_again(self):
        """★ SOUNDNESS: a module the AST walk cannot see imported (sys.path + import) is read through the hook"""
        self.law("imports")
        H._TRACES.clear()
        r0 = self.push()
        self.assertEqual(r0[0], {P3._GATE: H.PROVEN}, "\n".join(r0[4]))
        self.tree.files["tv/named_mod.py"] = "X = 2\n"
        H._TRACES.clear()
        results, per, stopped, runs, said = self.push()
        self.assertRan(runs, said, "an edit to a module imported at run time")

    def test_the_static_closure_is_never_dropped(self):
        """a module the law imports by AST (helper_p3) stays a byte input even with an empty trace"""
        self.law("never")
        sandbox, root = self.tree.make()
        try:
            keep = H._keep_for(sandbox, P3._FILE, P3._proof())
            self.assertIn("tv/helper_p3.py", keep, keep)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_a_python_child_spawned_directly_is_counted(self):
        """★ os.posix_spawn without subprocess: the child is counted, says no hello (-S), and nothing is dropped"""
        results, per, stopped, runs, said = self.cold_then_edit("direct")
        self.assertRan(runs, said, "an edit read by a directly spawned python child")

    def test_a_multiprocessing_child_is_traced(self):
        """a multiprocessing spawn child (fork_exec, no Popen event) inherits the hook and says hello: still complete"""
        results, per, stopped, runs, said = self.cold_then_edit("forkexec")
        self.assertReused(runs, results, said, "a law that started a multiprocessing child that read nothing")

    def test_a_pure_tool_child_still_lets_an_unread_file_go(self):
        """`true` opens no file of the tree: the trace stays complete and the unread file is still keyed by name"""
        results, per, stopped, runs, said = self.cold_then_edit("pure")
        self.assertReused(runs, results, said, "a law that only ran `true`")

    def test_the_off_switch_keeps_every_byte_in_the_key(self):
        """HEART2_TRACE=0: no trace, nothing dropped - the edit re-proves, as before REG-2640"""
        results, per, stopped, runs, said = self.cold_then_edit("never", env={"HEART2_TRACE": "0"})
        self.assertRan(runs, said, "HEART2_TRACE=0")

    def test_a_proof_with_nothing_to_drop_keeps_its_v1_key(self):
        """compatible: the key every bank on every machine already holds is unchanged when nothing is unread"""
        self.law("opens")
        self.tree.files["tv/helper_p3.py"] = self.tree.files["tv/helper_p3.py"].replace("OTHER = 'named_mod.py'\n", "")
        self.push()
        ent = self.entries()
        self.assertEqual(len(ent), 1)
        self.assertNotIn("unread", list(ent.values())[0])
        sandbox, root = self.tree.make()
        try:
            c = H._VerdictCache(path=self.cache_path, say=lambda *a: None)
            k_lookup = c.key_for(sandbox, P3._GATE, P3._FILE, P3._proof())[0]
            k_v1 = c.key_for(sandbox, P3._GATE, P3._FILE, P3._proof(), unread=[])[0]
            self.assertEqual(k_lookup, k_v1)
            self.assertIn(k_v1, ent, "the v1 key is not the key it was banked under")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_target_the_needs_and_the_prover_are_never_dropped(self):
        """the tampered target, every PROOF_NEEDS file and the prover are keyed by bytes, traced or not"""
        sandbox, root = self.tree.make()
        try:
            keep = H._keep_for(sandbox, P3._FILE, P3._proof())
            self.assertTrue({"tv/subject.txt", "tv/heart2.py", "tv/law_widths.py"} <= keep, keep)
            with H._TRACE_LOCK:
                H._TRACES[P3._FILE] = {"names": set(), "ok": True, "runs": 1}
            got = H._trace_unread(P3._FILE, ["tv/subject.txt", "tv/heart2.py", "tv/page.css", "tv/x.py"], keep)
            self.assertEqual(got, ["tv/page.css", "tv/x.py"], "a kept input was dropped, or a named one kept: %s" % got)
            with H._TRACE_LOCK:
                H._TRACES[P3._FILE]["ok"] = False
            self.assertEqual(H._trace_unread(P3._FILE, ["tv/page.css"], keep), [], "an incomplete trace dropped")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_the_trace_leaves_the_law_its_own_sys_path_and_sitecustomize(self):
        """the hook's directory leaves sys.path before the law's first line, and a sitecustomize it shadows still runs"""
        d = tempfile.mkdtemp(prefix="h2trace-fx.")
        try:
            other = os.path.join(d, "other")
            os.makedirs(other)
            with io.open(os.path.join(other, "sitecustomize.py"), "w", encoding="utf-8") as fh:
                fh.write("import builtins\nbuiltins.H2_OTHER_SITE = True\n")
            site = H._trace_site()
            log = os.path.join(d, "log")
            env = dict(os.environ, PYTHONPATH=site + os.pathsep + other, HEART2_TRACE_LOG=log, HEART2_TRACE_SITE=site)
            import subprocess
            r = subprocess.run([sys.executable, "-c", "import sys, builtins; print(%r in sys.path, "
                                "getattr(builtins, 'H2_OTHER_SITE', False))" % site], env=env,
                               capture_output=True, text=True, timeout=60)
            self.assertEqual(r.stdout.split(), ["False", "True"], r.stdout + r.stderr)
            seen, ok = H._trace_read(log, os.getpid())
            self.assertTrue(ok, "a plain python run was not a complete trace")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a_killed_provers_trace_dir_is_swept_and_a_live_ones_is_kept(self):
        """the trace dir of a prover SIGKILL ended (no atexit ran) leaves on the next run; a live prover's stays"""
        base = tempfile.mkdtemp(prefix="h2sweep-fx.")
        try:
            import subprocess
            dead = subprocess.Popen([sys.executable, "-c", "pass"]); dead.wait()
            for pid in (dead.pid, os.getpid(), os.getppid()):
                os.makedirs(os.path.join(base, "heart2-trace-%d-x" % pid, "sub"))
            gone = H._trace_sweep(base)
            self.assertEqual(gone, ["heart2-trace-%d-x" % dead.pid])
            self.assertEqual(sorted(_fx_tmp.list_own(base)), sorted("heart2-trace-%d-x" % p for p in (os.getpid(), os.getppid())))
        finally:
            shutil.rmtree(base, ignore_errors=True)


RED_PROOF = [
    {
        "why": "REG-2640 - a direct os.posix_spawn python child is never counted, so its missing hello goes unseen",
        "file": "heart2.py",
        "find": "                emit(\"P\" if py else \"U\", ev + \" \" + what)\n",
        "replace": "                emit(\"p\", ev + \" \" + what)\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - the static import closure is dropped like a merely named file",
        "file": "heart2.py",
        "find": "    keep |= {rel(p) for p in closure}\n",
        "replace": "    keep |= set()\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - every named data file is keyed by name, read or not: a CSS edit the law reads reuses a PROVEN",
        "file": "heart2.py",
        "find": "    return sorted(r for r in rels if r not in keep\n                  and r.rsplit(\"/\", 1)[-1] not in names)\n",
        "replace": "    return sorted(r for r in rels if r not in keep)\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - a stat is not a read: a law that asks a file's size is reused over a new size",
        "file": "heart2.py",
        "find": "    for n in (\"stat\", \"lstat\", \"access\", \"readlink\"):\n",
        "replace": "    for n in ():\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - a child no hook is in (cat, git, node) still lets files go",
        "file": "heart2.py",
        "find": "                elif tag:\n                    untraced = True\n",
        "replace": "                elif tag:\n                    pass\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - a counted python child that never said hello is taken as traced",
        "file": "heart2.py",
        "find": "    return seen, bool(root and not untraced and len(hellos) >= py)\n",
        "replace": "    return seen, bool(root and not untraced)\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - an incomplete trace still drops what it did not see",
        "file": "heart2.py",
        "find": "        if not t or not t[\"ok\"] or t[\"runs\"] < 1:\n",
        "replace": "        if not t or t[\"runs\"] < 1:\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - a python child does not inherit the hook's reads (its opens are lost)",
        "file": "heart2.py",
        "find": "        elif ev == \"open\":\n            names(\"R\", args[0] if args else None)\n",
        "replace": "        elif ev == \"open\" and _o.getppid() != int(_o.environ.get(\"H2_NOPE\", \"0\")) and _s.argv[0] != \"-c\":\n            names(\"R\", args[0] if args else None)\n",
        "matches": 1,
    },
    {
        "why": "REG-2640 - the unread file is hashed by bytes again: the CSS edit re-proves (the fix undone)",
        "file": "heart2.py",
        "find": "            if rel in unread:                         # REG-2640 - no traced run opened it: its name, never its bytes\n",
        "replace": "            if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
