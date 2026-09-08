# -*- coding: utf-8 -*-
"""v2778 — ISOLATING THE PORT IS NOT ISOLATING THE WORLD, AND render_check DID NOT KNOW IT.

`test_button_matrix.py:58` has carried this scar since v1867, in as many words:

    "This harness was careful about the one thing that had bitten before — it takes a private free
     port, passes --no-open, and terminates only the pid it started — and then handed that private
     control app his REAL environment… A port is one door; the frames, the journal, the sweep
     memory and the sweep lock are four more."

`render_check.py` did all three careful things and then did the same thing wrong: its spawn passed
`TV_CONTROL_PORT / TV_PORT / TV_STUB / TV_PARENT_PID` and **no world vars at all**. With no
`TV_HIST`, `_fixture_root_for_state()` and `_log_root()` both fall back to `HERE`, so every
"isolated" state path resolved to his live `tv/`.

=== MEASURED, 2026-09-08 ===
Fingerprinted all 69 state files in `tv/` by SHA, ran the render gate, fingerprinted again. Changed:
`.board_identity.json`, `.chronicle_routes_cache.json`, `.fixture_reels_cache.json`,
`.tvd_beacon.json`.

⚠ THAT RUN WAS CONFOUNDED — his live console writes those same files, and attributing them to the
harness is exactly the mistake made earlier the same night. So the proof below is STRUCTURAL, not a
before/after diff: does the path MOVE when TV_HIST says "this is not his world", and stay put when
it does not? That question has no second writer in it.

=== THE ACTUAL DEFECT, AND IT IS OLDER THAN render_check ===
`tv_diablo._fixture_root` states the rule in its own docstring: **"v1869 — one rule, four files."**
Three files were added AFTER that ship and never got it:
    .board_identity.json       control_app.py       (arrived v2147)
    .fixture_reels_cache.json  frame_authority.py
    .chronicle_routes_cache.json chronicle_routes.py
`.tvd_beacon.json` was already correct — it goes through `_log_root()`.

=== ⛔ WHY THE FIX IS A SNAPSHOT AND NOT AN EMPTY SANDBOX ===
These targets exist to photograph HIS surfaces. `advanced-fleet` refuses unless the fleet list is
FILLED; an empty world renders "nobody has checked in", and a target photographing an empty page is
green about nothing. So the small state is copied in and the writes land in the copy.
⛔ FRAMES ARE NEVER COPIED — `tv/frames/hist` is 5.6 GB, and copying `tv/` is the ENOSPC incident
this repo has already paid for once.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass


def _paths_under(tv_hist):
    """Re-import the three modules with TV_HIST set (or cleared) and report where they write.

    ⚠ Fresh subprocess, not importlib.reload: these are module-level constants evaluated once at
    import, and a reload inside this process would leave the REAL console's paths repointed for
    every later test in the file. Isolation tested by polluting the tester is not isolation.
    """
    import json
    import subprocess
    code = (
        "import sys,os,json; sys.path.insert(0,%r)\n"
        "import control_app as CA, chronicle_routes as CR, frame_authority as FA, inspect\n"
        "print(json.dumps({'board': CA._BOARD_ID_PATH, 'routes': CR._CACHE_PATH,\n"
        "                  'reels_src': ('_tvd._fixture_root(HERE)' in inspect.getsource(FA))}))\n"
        % HERE)
    env = dict(os.environ)
    env.pop("TV_HIST", None)
    if tv_hist:
        env["TV_HIST"] = tv_hist
    out = subprocess.check_output([sys.executable, "-c", code], env=env, cwd=HERE,
                                  stderr=subprocess.DEVNULL, timeout=120)
    return json.loads(out.decode("utf-8").strip().splitlines()[-1])


class TheHarnessIsolatesTheWorld(unittest.TestCase):

    # ── ⚠⚠ THE RULE, BOTH DIRECTIONS ────────────────────────────────────────────────────────
    def test_a_fixture_world_takes_the_state_with_it(self):
        """★★ v1869's rule applied to the three files that missed it. If TV_HIST says this is not
        his world, none of these may be written into his tree."""
        # ⚠ realpath BOTH SIDES. On macOS mkdtemp returns /var/folders/… while the child resolves
        # it to /private/var/folders/… — /var is a symlink. The first cut of this law failed on a
        # CORRECT result and I nearly went looking in control_app. Suspect the fixture first.
        # [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
        sand = os.path.realpath(tempfile.mkdtemp(prefix="isolaw-"))
        hist = os.path.join(sand, "frames", "hist")
        os.makedirs(hist, exist_ok=True)
        p = _paths_under(hist)
        p = dict(p, board=os.path.realpath(p["board"]), routes=os.path.realpath(p["routes"]))
        for key in ("board", "routes"):
            self.assertFalse(p[key].startswith(HERE + os.sep),
                             "%s still writes into his real tv/ when TV_HIST names a fixture "
                             "world: %s" % (key, p[key]))
            self.assertTrue(p[key].startswith(sand),
                            "%s did not follow TV_HIST into the fixture world: %s" % (key, p[key]))
        self.assertTrue(p["reels_src"],
                        "frame_authority still builds .fixture_reels_cache.json from a bare HERE")

    def test_HIS_world_is_unchanged_when_nothing_says_otherwise(self):
        """⛔ THE OTHER HALF, AND THE ONE THAT MATTERS TO HIM. A console started normally must keep
        writing exactly where it always did — an isolation fix that quietly repoints his live
        console's own record would be far worse than the leak it closes."""
        p = _paths_under(None)
        for key in ("board", "routes"):
            self.assertTrue(p[key].startswith(HERE + os.sep),
                            "his real console no longer writes %s into his own tv/: %s"
                            % (key, p[key]))

    # ── ⚠ THE HARNESS MUST ACTUALLY SET IT ──────────────────────────────────────────────────
    def test_render_checks_spawn_carries_the_world(self):
        """★ [[plumbing-with-no-tap]] — the rule above is inert unless the harness declares a
        world. Parsed off the function, not grepped at file scope, because these var names appear
        in prose elsewhere in the file."""
        import ast
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_serve_console"), None)
        self.assertIsNotNone(fn, "_serve_console is gone")
        body = ast.get_source_segment(src, fn) or ""
        code = "\n".join(l for l in body.split("\n") if not l.strip().startswith("#"))
        for var in ("TV_HIST", "TV_SESSIONS", "TV_CHRON_EVIDENCE", "TV_SWEEP_LOCK",
                    "TV_FRAMES_DIR"):
            self.assertIn(var, code,
                          "the private console is spawned without %s, so that part of his world "
                          "is still shared with the harness" % var)

    def test_the_snapshot_can_never_become_a_bulk_copy(self):
        """⛔⛔ THE ENOSPC GUARD. tv/frames/hist is 5.6 GB. Three agents once copied tv/ to /tmp —
        20.5 GB in four minutes — and every Bash call in that session then failed before it ran,
        because the harness could not create its own output file. The copy list is NAMED, never
        globbed, and carries a byte ceiling."""
        import ast
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_serve_console"), None)
        body = ast.get_source_segment(src, fn) or ""
        code = "\n".join(l for l in body.split("\n") if not l.strip().startswith("#"))
        self.assertNotIn("copytree", code, "the snapshot uses copytree — that is how tv/ gets copied")
        self.assertNotIn("glob", code, "the copy list is globbed; a big file added beside the small "
                                       "ones would be swept in silently")
        self.assertIn("1024", code, "the snapshot carries no byte ceiling")
        for banned in ("frames/hist", "HIST_DIR"):
            self.assertNotIn(banned, code,
                             "the snapshot names %r — frames must never be copied" % banned)

    # ── ⚠ THE FIXTURE ───────────────────────────────────────────────────────────────────────
    def test_the_shared_rule_still_exists_to_be_followed(self):
        """⚠ All three fixes route through `tv_diablo._fixture_root`. If that helper is renamed or
        loses its TV_HIST behaviour, all three silently fall back to HERE and this file's other
        laws would still pass on the FALLBACK path."""
        import tv_diablo as tvd
        self.assertTrue(callable(getattr(tvd, "_fixture_root", None)),
                        "tv_diablo._fixture_root is gone — the shared rule has no implementation "
                        "and every caller falls back to his real tree")
        sand = tempfile.mkdtemp(prefix="isorule-")
        hist = os.path.join(sand, "frames", "hist")
        os.makedirs(hist, exist_ok=True)
        old = os.environ.get("TV_HIST")
        os.environ["TV_HIST"] = hist
        try:
            got = tvd._fixture_root(HERE)
        finally:
            if old is None:
                os.environ.pop("TV_HIST", None)
            else:
                os.environ["TV_HIST"] = old
        self.assertNotEqual(got, HERE,
                            "_fixture_root ignores TV_HIST, so the rule it documents does nothing")

    # ── ⚠⚠ v2780 — THE CENSUS, WHICH IS THE ONLY LAW HERE THAT CATCHES THE *NEXT* ONE ────────
    def test_NO_module_level_path_still_resolves_to_the_LIVE_dir(self):
        """★★★ v2778 SANDBOXED THE WORLD AND EIGHT PATHS WALKED STRAIGHT PAST IT.

        v2778 handed the render child TV_HIST plus seven TV_* file vars and called the world
        isolated. A cross-family review of that change asked the one question that mattered — *name
        every way the child can still reach and WRITE a live file* — and the answer, measured by
        spawning a child under v2778's own env and enumerating every module-level constant, was
        **EIGHT**:

            CAPTURE_DOORS_PATH · IDENTITY_PATH · VIEW_REQUEST_PATH · _CHRON_HUNT_MEM_PATH
            _CHRON_SWEPT_PATH · _DISK_HISTORY · _SHADOW_WATCH_PATH · _UI_FAULTS

        A render gate appended to his real `ui_faults.jsonl`. Two of the eight name files that
        v2778 COPIES INTO the sandbox — copied, then read from the live path anyway, which is
        plumbing built on both ends and never joined.

        ⚠⚠ THIS LAW IS A CENSUS, NOT A LIST. It does not name the eight; it spawns a child in a
        fixture world and asserts that NOTHING lands under the live directory. A law that named
        them would have been green the day a ninth appeared — and a ninth is exactly how this
        defect arrived, one careless `os.path.join(HERE, ...)` at a time, for 911 versions after
        v1867 first wrote the rule down. [[the-unjoined-end]] [[regression-guard]]

        ⚠ IT MUST BE A FRESH INTERPRETER. These are module-level constants frozen at import, so
        setting TV_HIST inside this process proves nothing about a child that imported earlier —
        and the child is what the render harness actually spawns."""
        sand = tempfile.mkdtemp(prefix="census-")
        try:
            hist = os.path.join(sand, "frames", "hist")
            os.makedirs(hist, exist_ok=True)
            env = dict(os.environ, TV_STUB="1", TV_HIST=hist,
                       TV_FRAMES_DIR=os.path.join(sand, "frames"))
            code = (
                "import sys, os; sys.path.insert(0, %r)\n"
                "import control_app as CA\n"
                "HERE = %r\n"
                "bad = []\n"
                "for k in dir(CA):\n"
                "    if not k.isupper() and not k.startswith('_'): continue\n"
                "    try: v = getattr(CA, k)\n"
                "    except Exception: continue\n"
                "    if isinstance(v, str) and v.startswith(HERE + os.sep) and "
                "v.endswith(('.json', '.jsonl', '.lock')):\n"
                "        bad.append(k + ' -> ' + os.path.relpath(v, HERE))\n"
                "print('BAD:' + '|'.join(sorted(bad)))\n" % (HERE, HERE))
            out = subprocess.check_output([sys.executable, "-c", code], env=env,
                                          stderr=subprocess.STDOUT, timeout=180)
            line = [l for l in out.decode("utf-8", "replace").splitlines()
                    if l.startswith("BAD:")]
            self.assertTrue(line, "the census child never reported — it is UNMEASURED, not clean")
            bad = [b for b in line[-1][4:].split("|") if b]
            self.assertEqual(bad, [],
                             "%d module-level path(s) still resolve into the LIVE directory while "
                             "TV_HIST names a fixture world, so a render or a test writes through "
                             "them into his real data: %s" % (len(bad), ", ".join(bad)))
        finally:
            shutil.rmtree(sand, True)

    def test_the_same_paths_STILL_point_at_his_real_files_normally(self):
        """⛔ THE OTHER HALF, and the one that makes the fix above safe rather than merely tidy.
        `_fixture_root_for_state()` returns HERE unless TV_HIST is set, and his console never sets
        it. If that ever stopped being true, his live console would silently start writing its
        identity, its fault journal and its sweep memory somewhere else — a far worse bug than the
        one being fixed."""
        import control_app as CA
        for name in ("_UI_FAULTS", "CAPTURE_DOORS_PATH", "IDENTITY_PATH", "VIEW_REQUEST_PATH",
                     "_CHRON_HUNT_MEM_PATH", "_CHRON_SWEPT_PATH", "_DISK_HISTORY",
                     "_SHADOW_WATCH_PATH"):
            v = getattr(CA, name, None)
            self.assertTrue(v, "%s is gone — re-point this law rather than let it pass on nothing"
                            % name)
            self.assertTrue(str(v).startswith(HERE + os.sep),
                            "%s no longer resolves to his live directory in ordinary use (%s) — "
                            "his console would write its state somewhere he cannot find it"
                            % (name, v))

    def test_the_size_ceiling_SKIPS_one_file_and_does_not_ABANDON_the_rest(self):
        """★ THE SECOND FINDING FROM THE SAME REVIEW. The ceiling used `break`, so ONE oversized
        file abandoned every remaining name — and a name absent from the sandbox falls back to the
        LIVE file. The guard against a bulk copy would have caused the exact leak the sandbox
        exists to prevent. It must `continue`, and it must SAY what it skipped, because a silent
        skip is indistinguishable from a file that was never there.
        [[unknown-stays-unknown]] [[zero-needs-a-denominator]]"""
        src = io.open(os.path.join(HERE, "render_check.py"), encoding="utf-8").read()
        i = src.find("if _bytes + _sz > 64 * 1024 * 1024")
        self.assertGreater(i, 0, "the size ceiling is gone")
        after = src[i:i + 400]
        # ⚠ code only — the comment above this line explains the `break` that was wrong, so a
        # substring search over the region would read the explanation as the defect.
        after = "\n".join(l for l in after.split("\n") if not l.strip().startswith("#"))
        self.assertNotIn("break", after,
                         "the ceiling ABANDONS the remaining files again, so one oversized store "
                         "un-isolates every store after it")
        self.assertIn("continue", after, "the ceiling no longer skips just the oversized file")
        self.assertIn("_skipped", after, "a skipped file is silent again")

    # ── ⚠⚠ v2783 — A REQUEST FOR ISOLATION MUST NOT DEGRADE TO "NO ISOLATION" ────────────────
    def test_a_BROKEN_resolver_does_not_fall_back_to_his_LIVE_dir(self):
        """★★★ FROM THE CROSS-FAMILY REVIEW OF v2780, which asked the one question I had not:
        under what conditions does the except arm fire *while TV_HIST is set*?

        `_fixture_root_for_state()` was `try: return _tvd._fixture_root(HERE) / except Exception:
        return HERE`. Any failure inside the resolver — an import error, a renamed symbol, a
        runtime error — silently returned the LIVE directory to a caller that had explicitly asked
        for a fixture world. Eight module-level paths then bind to his real data with nothing
        raised and nothing logged. The guard against writing into his world would itself have been
        the thing that wrote into it.

        ⛔ The asymmetry is the whole point: if isolation was requested and cannot be resolved, the
        raw TV_HIST value is the one thing the caller actually said. Falling back to HERE is not a
        degraded answer, it is the wrong one. [[unknown-stays-unknown]]

        ⚠ The resolver is broken by sabotaging `import tv_diablo` INSIDE a fresh child, because
        these constants bind at import."""
        sand = tempfile.mkdtemp(prefix="broken-resolver-")
        try:
            hist = os.path.join(sand, "frames", "hist")
            os.makedirs(hist, exist_ok=True)
            env = dict(os.environ, TV_STUB="1", TV_HIST=hist)
            code = (
                "import sys, os, builtins; sys.path.insert(0, %r)\n"
                "_real = builtins.__import__\n"
                "def _boom(name, *a, **k):\n"
                "    if name == 'tv_diablo': raise RuntimeError('resolver is broken')\n"
                "    return _real(name, *a, **k)\n"
                "builtins.__import__ = _boom\n"
                "import control_app as CA\n"
                "print('ROOT:' + str(CA._fixture_root_for_state()))\n" % (HERE,))
            out = subprocess.check_output([sys.executable, "-c", code], env=env,
                                          stderr=subprocess.STDOUT, timeout=180)
            line = [l for l in out.decode("utf-8", "replace").splitlines()
                    if l.startswith("ROOT:")]
            self.assertTrue(line, "the child never reported — UNMEASURED, not clean")
            root = line[-1][5:]
            self.assertFalse(root.startswith(HERE),
                             "a broken resolver fell back to his LIVE directory (%s) while TV_HIST "
                             "asked for a fixture world, so every state path binds to his real "
                             "data with nothing raised" % root)
        finally:
            shutil.rmtree(sand, True)

    def test_a_broken_resolver_with_NO_request_still_gives_him_HERE(self):
        """⛔ THE OTHER HALF. With nobody asking for a fixture world, a broken resolver must still
        answer HERE — his console depends on it, and a fix that made it answer anything else would
        move his live state somewhere he cannot find it."""
        env = dict(os.environ, TV_STUB="1")
        env.pop("TV_HIST", None)
        code = (
            "import sys, os, builtins; sys.path.insert(0, %r)\n"
            "_real = builtins.__import__\n"
            "def _boom(name, *a, **k):\n"
            "    if name == 'tv_diablo': raise RuntimeError('resolver is broken')\n"
            "    return _real(name, *a, **k)\n"
            "builtins.__import__ = _boom\n"
            "import control_app as CA\n"
            "print('ROOT:' + str(CA._fixture_root_for_state()))\n" % (HERE,))
        out = subprocess.check_output([sys.executable, "-c", code], env=env,
                                      stderr=subprocess.STDOUT, timeout=180)
        line = [l for l in out.decode("utf-8", "replace").splitlines() if l.startswith("ROOT:")]
        self.assertTrue(line, "the child never reported — UNMEASURED, not clean")
        self.assertEqual(line[-1][5:], HERE,
                         "with nothing asking for a fixture world, his own console no longer "
                         "resolves its state to the live directory")


if __name__ == "__main__":
    unittest.main(verbosity=2)
