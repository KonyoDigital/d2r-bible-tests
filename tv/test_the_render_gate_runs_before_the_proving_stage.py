# -*- coding: utf-8 -*-
"""#42 P5 — hooks/pre-push RUNS THE RENDER GATE BEFORE THE PROVING STAGE, AT TOP LEVEL, AND LOST NO STAGE DOING IT.

MEASURED 2026-09-29 on the v3523 push: every cheap stage green by 0m09s, the changed laws proved (~83 min), both python
suites green - and then the render gate REFUSED at 94m53s (and again at ~98m on the retry) on a shelf proof that passed
alone minutes later. Twice the whole proving stage was paid to learn what a five-minute render would have said first.
Over 2026-09-26..28 the render gate refused 3 of 9 pushes: it is the stage most likely to refuse, so it runs right after
the cheap stages, before anything long. With the same clocks a render refusal now lands at ~5 min, not ~95.

THIS LAW READS THE HOOK'S OWN STAGE ORDER, not a string count: the shell walker the anchors law already owns (`_walk`,
`_code`, column-0 grammar) gives every `gate_run` call and the prove call a line and a nesting depth, and the order is
judged from those. It also pins that the move removed nothing: every stage the hook ran before P5 still runs, with the
bound it had, and `bash -n` still accepts the file. And it pins the second thing the move bought: the render block sits
at TOP LEVEL, no longer inside the `tv/ python touched` lane where a push changing only tv/render_coverage.json or art/
never rendered at all.

THE SECOND EYE ON P5 (2026-09-29): the very log P5 cites was refused by console-demos at 113m13s, 26 s after the render
gate passed - a 25-second stage paid for behind 96 minutes of proofs; it refused 2 of 13 pushes over 2026-09-27..29. So
both console-demos call sites (his console, and the console the gate starts when :17772 is silent) now run right after
the render gate and before the proving stage, byte for byte, at top level - the same move, the same hole closed (inside
the lane, a push changing only tv/control_ui.html or tv/demo_console.mjs - the files its own trigger names - never ran
the demos). [[regression-guard]] [[the-unjoined-end]] RED_PROOF below.
"""
import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
# ONE shell walker for the hook, owned by the anchors law - never a second copy of the column-0 grammar. [[copy-drift]]
from test_every_push_checks_every_proof_anchor import _walk, _code, _call_block  # noqa: E402

HOOK = os.path.join(ROOT, "hooks", "pre-push")
PROVE = 'tv/heart2.py" --prove $_gates'

#: every stage the hook ran before P5, with its bound in seconds - "keep every existing stage and its bound". A
#: DELIBERATE change to a bound updates this map in the same commit and says why; a silent one is refused here.
STAGES = {"version-stamp": 30, "second-eye": 30, "blueprint": 60, "heart": 60, "red-proof anchors": 120,
          "review-lite": 120, "visual-lock": 120, "boss-portraits": 120, "test_agent": 600, "test_control": 1500,
          "test_tz_art": 120, "test_chronicle_retro": 120, "test_chronicle_seal": 120, "render": 353,
          "crest-loudness": 180, "console-demos": 180, "smoke": 900}
_GATE_RUN = re.compile(r'gate_run\s+"([^"]+)"\s+"(?:[^"\\]|\\.)*"\s+(\d+)\s+--')


def _lines():
    with io.open(HOOK, encoding="utf-8") as fh:
        return fh.read().split("\n")


def _stages(lines):
    """Every gate_run call and the prove call, in file order. -> [(label, bound | None, line, depth)]"""
    out = []
    for i, l in enumerate(lines):
        code = _code(l)
        if not code.strip():
            continue
        m = _GATE_RUN.search(_call_block(lines, i)) if "gate_run" in code and "gate_run()" not in code else None
        if m and not code.lstrip().startswith("#"):
            out.append((m.group(1), int(m.group(2)), i, _walk(lines, i)[0]))
        elif PROVE in code:
            out.append(("heart2 --prove --push", None, i, _walk(lines, i)[0]))
    return out


class TheRenderGateRunsBeforeTheProvingStage(unittest.TestCase):

    def test_bash_accepts_the_hook(self):
        import posix_shell as _PS   # REG-1642 - a real POSIX bash; on a Windows PC `bash` is the WSL launcher
        _bash = _PS.bash()
        if _bash is None:
            self.skipTest("no real POSIX bash on this PC - the hook's syntax is UNMEASURED, not passing")
        r = subprocess.run([_bash, "-n", HOOK], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
        self.assertEqual(r.returncode, 0, "bash -n refuses the hook:\n%s" % r.stdout.decode("utf-8", "replace")[-600:])

    def test_the_walker_sees_the_whole_hook(self):
        """the instrument first: a walker that cannot balance the file cannot place a stage in it"""
        depth, tag = _walk(_lines())
        self.assertIsNone(tag, "a heredoc opened with %r never terminates" % tag)
        self.assertEqual(depth, 0, "the hook does not balance to depth 0 (%d)" % depth)

    def test_render_runs_before_the_proving_stage_and_at_top_level(self):
        """★ the render gate's line precedes the heart2 --prove call, and the render block is at depth 0 - the trigger
        alone decides whether it runs, not the tv/ python lane it used to sit inside"""
        st = _stages(_lines())
        render = [s for s in st if s[0] == "render"]
        prove = [s for s in st if s[0] == "heart2 --prove --push"]
        self.assertEqual(len(render), 1, "PREMISE: the hook runs the render gate %d times: %s" % (len(render), st))
        self.assertEqual(len(prove), 1, "PREMISE: the hook runs heart2 --prove %d times: %s" % (len(prove), st))
        self.assertLess(render[0][2], prove[0][2],
                        "the render gate (line %d) runs AFTER the proving stage (line %d): a render refusal costs the "
                        "whole proving stage again, as it did twice on v3523" % (render[0][2] + 1, prove[0][2] + 1))
        # the call itself sits inside `if [ "$_px_touched" = "1" ]` (one level), whose trigger is at top level
        lines = _lines()
        trig = [i for i, l in enumerate(lines) if _code(l) == "_px_touched=0"]
        self.assertEqual(len(trig), 1, "PREMISE: the render trigger `_px_touched=0` is not exactly once in the hook")
        self.assertEqual(_walk(lines, trig[0])[0], 0,
                         "the render block sits inside another block (depth %d): a push that changes only "
                         "tv/render_coverage.json or art/ - no tv/*.py - would never render" % _walk(lines, trig[0])[0])
        self.assertGreaterEqual(prove[0][3], 1, "BASELINE: the prove call inside the changed-tests block read as top "
                                                "level, so this walker cannot tell nested from not")

    def test_the_console_demos_run_after_render_and_before_the_proving_stage(self):
        """★ (second eye on P5) EVERY console-demos call site precedes the prove call and follows the render gate, and
        the demos' trigger `_demo_touched=0` sits at depth 0 - the trigger alone decides, not the tv/ python lane"""
        st = _stages(_lines())
        demos = [s for s in st if s[0] == "console-demos"]
        prove = [s for s in st if s[0] == "heart2 --prove --push"]
        render = [s for s in st if s[0] == "render"]
        self.assertEqual(len(prove), 1, "PREMISE: the hook runs heart2 --prove %d times: %s" % (len(prove), st))
        self.assertEqual(len(render), 1, "PREMISE: the hook runs the render gate %d times" % len(render))
        self.assertGreaterEqual(len(demos), 2, "PREMISE: the console demos lost a call site: %s" % demos)
        late = [s for s in demos if s[2] > prove[0][2]]
        self.assertEqual(late, [], "console-demos site(s) at line(s) %s run AFTER the proving stage (line %d): a demo "
                                   "refusal costs the whole proving stage again, as it did on v3523 push #3 at 113m13s"
                         % ([s[2] + 1 for s in late], prove[0][2] + 1))
        self.assertLess(render[0][2], min(s[2] for s in demos),
                        "the demos run before the render gate: the picture is looked at first, then the journeys")
        lines = _lines()
        trig = [i for i, l in enumerate(lines) if _code(l).strip() == "_demo_touched=0"]
        self.assertEqual(len(trig), 1, "PREMISE: the demos trigger `_demo_touched=0` is not exactly once in the hook")
        self.assertEqual(_walk(lines, trig[0])[0], 0,
                         "the console-demos block sits inside another block (depth %d): a push changing only "
                         "tv/control_ui.html or tv/demo_console.mjs - the files its own trigger names - would never "
                         "run the demos" % _walk(lines, trig[0])[0])

    def test_the_cheap_stages_still_come_first(self):
        """render runs AFTER the cheap stages (version-stamp, second-eye, blueprint, heart) - it does not jump them"""
        st = _stages(_lines())
        at = dict((s[0], s[2]) for s in st if s[0] in ("version-stamp", "second-eye", "blueprint", "heart", "render"))
        for cheap in ("version-stamp", "second-eye", "blueprint", "heart"):
            self.assertIn(cheap, at, "PREMISE: the cheap stage %s is gone" % cheap)
            self.assertLess(at[cheap], at["render"], "%s runs after the render gate" % cheap)

    def test_every_stage_and_its_bound_survived_the_move(self):
        """★ the move removed no stage and weakened none: every label the hook ran before P5 is still run through
        gate_run with the bound it had"""
        st = _stages(_lines())
        got = {}
        for label, bound, _i, _d in st:
            if bound is not None:
                got.setdefault(label, set()).add(bound)
        missing = sorted(set(STAGES) - set(got))
        self.assertEqual(missing, [], "stage(s) no longer run through gate_run: %s" % missing)
        wrong = sorted("%s: %s (was %d)" % (k, sorted(got[k]), STAGES[k]) for k in STAGES if got[k] != {STAGES[k]})
        self.assertEqual(wrong, [], "a stage's bound moved silently - a deliberate change updates STAGES in the same "
                                    "commit and says why: %s" % wrong)
        self.assertGreaterEqual(len([s for s in st if s[0] == "console-demos"]), 2,
                                "the console demos lost one of their two call sites (his console / a gate console)")

    def test_the_stage_reader_reads_calls_not_prose(self):
        """the reader ignores a gate_run named in a comment and reads the bound from the call"""
        lines = ['# if ! gate_run "ghost" "x" 999 -- python3 x.py; then',
                 'if ! gate_run "real" "python3 tv/x.py" 42 -- \\',
                 '     python3 "$REPO/tv/x.py"; then',
                 '  exit 1', 'fi', 'if python3 "$REPO/tv/heart2.py" --prove $_gates --push > "$l" 2>&1; then', 'fi']
        self.assertEqual([(s[0], s[1], s[3]) for s in _stages(lines)],
                         [("real", 42, 0), ("heart2 --prove --push", None, 0)])


RED_PROOF = [
    {
        "why": "the render gate is gone from the hook: no stage looks at the page, and the order case has no render",
        "file": "hooks/pre-push",
        "find": '    gate_run "render" "python3 tv/render_check.py" 353 -- python3 "$REPO/tv/render_check.py" || _px_fail=1\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the render bound weakened tenfold in the move (353 -> 3530): a hung render blocks a push for an hour",
        "file": "hooks/pre-push",
        "find": '    gate_run "render" "python3 tv/render_check.py" 353 -- python3 "$REPO/tv/render_check.py" || _px_fail=1\n',
        "replace": '    gate_run "render" "python3 tv/render_check.py" 3530 -- python3 "$REPO/tv/render_check.py" || _px_fail=1\n',
        "matches": 1,
    },
    {
        "why": "the render block is pushed back inside a lane: some pushes never render (and the file no longer balances)",
        "file": "hooks/pre-push",
        "find": "_px_touched=0\n",
        "replace": 'if [ -n "${_chg_live:-}" ]; then\n_px_touched=0\n',
        "matches": 1,
    },
    {
        "why": "a stage the move must keep (crest-loudness) is dropped",
        "file": "hooks/pre-push",
        "find": '    gate_run "crest-loudness" "python3 tv/crest_loudness.py" 180 -- python3 "$REPO/tv/crest_loudness.py" || _px_fail=1\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the hook no longer parses (an unmatched fi after its last line)",
        "file": "hooks/pre-push",
        "find": '  echo "          if CI is down, publish by hand: bash deploy.sh"\nfi\n\nexit 0\n',
        "replace": '  echo "          if CI is down, publish by hand: bash deploy.sh"\nfi\nfi\n\nexit 0\n',
        "matches": 1,
    },
    {
        "why": "a console-demos site is put back AFTER the proving stage (at the very end): a demo refusal again costs "
               "the whole proving stage, and the order case must see it",
        "file": "hooks/pre-push",
        "find": '  echo "          if CI is down, publish by hand: bash deploy.sh"\nfi\n\nexit 0\n',
        "replace": '  echo "          if CI is down, publish by hand: bash deploy.sh"\nfi\ngate_run "console-demos" '
                   '"node tv/demo_console.mjs" 180 -- node "$REPO/tv/demo_console.mjs" || true\n\nexit 0\n',
        "matches": 1,
    },
    {
        # the walker is this law's instrument (imported from the anchors law), so its two halves are pinned here:
        # with either one undone the hook no longer balances, and the whole-hook case says so
        "why": "the walker's seventh cut undone (a quoted -c program's column-0 `if` counts again): the demos block "
               "now sits ahead of every later stage, so each reads one level too deep and the hook does not balance",
        "file": "test_every_push_checks_every_proof_anchor.py",
        "find": '    return ("" if started_inside else "".join(out).rstrip()), q, stack\n',
        "replace": '    return "".join(out).rstrip(), q, stack\n',
        "matches": 1,
    },
    {
        "why": "the array opener is not counted: the lone `)` closing SMOKE_SPECS=( reads as a group close and the "
               "hook ends at depth -1",
        "file": "test_every_push_checks_every_proof_anchor.py",
        "find": '              or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=\\($", code)):\n',
        "replace": '              or False):\n',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
