# -*- coding: utf-8 -*-
"""Every push checks EVERY red-proof anchor — not only the laws whose test file changed.

⚠⚠ WHAT IT COST BEFORE THIS EXISTED, all in one day (2026-09-24), REG-1163:
    v3455  read_names_lane.py edited  -> test_the_lane_asks_the_item_not_the_frame[2] matched 0
    v3456  test_control.py re-indented -> test_remeasure_population[0] matched 0
    v3462  handoff.py gained timeout=  -> test_a_failed_read_never_reaches_a_zero_claim[0] matched 0
    v3464  second_eye_ledger.py edited -> test_partial_look_is_not_agreement[3] matched 0 (caught by hand)
The hook re-proves a law only when its TEST file is in the push. A red-proof lives in one test file
and anchors on a line in ANOTHER file, so an ordinary fix to that line never names the proof — and
the proof silently changes nothing while the law reads as proven. The census case
(test_every_declared_red_proof_is_well_formed) knew all four; it simply never ran at push time.

⚠ ITS REACH, STATED: this catches an anchor that matches NOTHING (INVALID). It does not catch a proof
that still matches and no longer turns the law red (BLIND) — only a full `heart2 --prove` sees that.

⚠ A PRESENCE-LAW IS NOT A REACHABILITY-LAW. The gate must run on EVERY push, so this pins that the
call sits at TOP LEVEL of the hook, not inside the `if [ -n "$_chg_live" ]` changed-tests block
where it would run only when a test file changed — the exact blind spot it exists to close.
"""
import io
import os
import sys
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()       # these print non-ASCII; a cp1255 console must not crash while REPORTING
except Exception:
    pass
HOOK = os.path.join(os.path.dirname(HERE), "hooks", "pre-push")
CALL = 'if ! gate_run "red-proof anchors"'


INVOCATION = ('test_the_heart_can_see_its_own_instruments.py" '
              'TestHeartSeesItsInstruments.test_every_declared_red_proof_is_well_formed')


def _code(line):
    """The line with its shell COMMENT removed — quote-aware. v3471: a `#` starts a comment only
    outside quotes and at the start of a word; `split("#")` cut `echo "#"` in half (eye on v3469)."""
    q, out = None, []
    for i, ch in enumerate(line):
        if q:
            if ch == q and (q == "'" or line[i - 1] != "\\"):
                q = None
        elif ch in ("'", '"'):
            q = ch
        elif ch == "#" and (i == 0 or line[i - 1].isspace()):
            break
        out.append(ch)
    return "".join(out).rstrip()


_HEREDOC = re.compile(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?")


def _heredoc_tag(code):
    """A heredoc opener OUTSIDE quotes, or None. v3471: `echo "a << note"` is not an opener."""
    q, i = None, 0
    while i < len(code):
        ch = code[i]
        if code.startswith("$(", i):
            # ⚠ bash starts a FRESH quoting context inside $( ... ), even inside double quotes, so
            # `x="$(python3 - <<'PYGATE' ...)"` IS a real heredoc. The first v3471 cut read it as text
            # inside quotes, skipped nothing, and the hook stopped balancing — its own check caught it.
            q = None
            i += 2
            continue
        if q:
            if ch == q:
                q = None
        elif ch in ("'", '"'):
            q = ch
        elif code.startswith("<<", i) and not code.startswith("<<<", i):
            m = _HEREDOC.match(code, i)
            return m.group(1) if m else None
        i += 1
    return None


def _walk(lines, stop=None):
    """-> (depth at `stop` (or at EOF), unterminated heredoc tag or None). COLUMN-0 grammar.

    ⚠ SIX CUTS, EACH WRONG FOR A NAMED REASON. v3469's three (a python heredoc at column 0, Perl in a
    multi-line `perl -e` string, continued `if ... \\` conditions) and the cross-family eye's three on
    v3469 (a `<<` inside quotes froze the counter; `{ }` bodies at column 0 were not counted; a `#`
    inside quotes was read as a comment). The walk now reports its own blindness: a heredoc that never
    terminates, or a file that does not balance to depth 0, is the counter failing — said loudly."""
    depth, tag = 0, None
    for n, l in enumerate(lines):
        if stop is not None and n >= stop:
            break
        if tag is not None:
            if l.strip() == tag:
                tag = None
            continue
        code = _code(l)
        t = _heredoc_tag(code)
        if t:
            tag = t
        if (re.match(r"^(if|for|while|until|case)\b", code)
                and not re.search(r"\b(fi|done|esac)$", code)):
            depth += 1
        elif re.match(r"^(fi|done|esac)\b", code):
            depth -= 1
        elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(\)\s*\{$", code) or code in ("{", "("):
            depth += 1                                   # a function body or group at column 0
        elif code in ("}", ")"):
            depth -= 1
    return depth, tag


def _call_block(lines, i):
    """The call line and its `\\` continuations, comments stripped. -> str"""
    out, k = [], i
    while k < len(lines):
        out.append(_code(lines[k]))
        if not lines[k].rstrip().endswith("\\"):
            break
        k += 1
    return " ".join(x.rstrip("\\ ") for x in out)


class EveryPushChecksEveryProofAnchor(unittest.TestCase):

    def _lines(self):
        return io.open(HOOK, encoding="utf-8").read().split("\n")

    def test_the_hook_EXECUTES_the_anchor_census(self):
        lines = self._lines()
        hits = [i for i, l in enumerate(lines) if l.startswith(CALL)]
        self.assertEqual(len(hits), 1, "the hook does not run the red-proof anchor census exactly once "
                                       "at top level (found %d)" % len(hits))
        block = _call_block(lines, hits[0])
        # v3471 — what RUNS is what follows `--`; the first quoted argument is only the reproduce
        # hint, and a comment beside a different script named the census too (eye on v3469).
        self.assertIn(" -- ", block, "the call has no `--` argv to execute: %r" % block)
        runs = block.split(" -- ", 1)[1]
        self.assertIn(INVOCATION, runs, "the census is NAMED but not EXECUTED by this call: %r" % runs)

    def test_the_parser_reads_shell_the_way_bash_does(self):
        """v3471 — the eye on v3469 named each of these; each is now DRIVEN, not argued."""
        self.assertEqual(_code('echo "#" here'), 'echo "#" here', "a # inside quotes was read as a comment")
        self.assertEqual(_code("x=1 # note"), "x=1", "a real trailing comment survived")
        self.assertIsNone(_heredoc_tag('echo "a << note"'), "a << inside quotes was read as a heredoc")
        self.assertEqual(_heredoc_tag('x="$(python3 - <<\'PYGATE\' 2>/dev/null)"'), "PYGATE",
                         "a heredoc inside $( ) was missed — bash opens a fresh quote context there")
        self.assertEqual(_walk(["f() {", "  if x; then", "  fi", "}"])[0], 0)
        self.assertEqual(_walk(["f() {", "if ! gate_run \"x\" y -- z; then"], stop=1)[0], 1,
                         "a call inside a column-0 function body read as top level")

    def test_the_counter_can_see_the_whole_hook(self):
        """The instrument proves it is not blind before its verdict is believed."""
        depth, tag = _walk(self._lines())
        self.assertIsNone(tag, "a heredoc opened with %r never terminates — the counter skipped the "
                               "rest of the hook" % tag)
        self.assertEqual(depth, 0, "the hook does not balance to depth 0 (%d): the counter misread "
                                   "its structure somewhere" % depth)

    def test_it_runs_on_every_push_not_only_when_a_test_changed(self):
        lines = self._lines()
        call = [k for k, l in enumerate(lines) if l.startswith(CALL)]
        self.assertTrue(call, "no top-level call to measure")
        inner = [k for k, l in enumerate(lines) if 'tv/heart2.py" --prove $_gates' in l]
        self.assertTrue(inner, "the changed-law prove call is gone, so the baseline cannot be taken")
        self.assertGreaterEqual(_walk(lines, inner[0])[0], 1,
                                "BASELINE: the prove call INSIDE the changed-tests block read as top "
                                "level, so this counter cannot tell nested from not")
        self.assertEqual(_walk(lines, call[0])[0], 0,
                         "the anchor census sits inside a block, so some pushes skip it")

if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the census call removed: an anchor that matches nothing ships as a proven law again",
        "file": "hooks/pre-push",
        "find": "if ! gate_run \"red-proof anchors\"",
        "replace": "if false && ! gate_run \"red-proof anchors - disabled\"",
        "matches": 1,
    },
    {
        "why": "the census moved INSIDE a block — some pushes skip it, the blind spot it closes",
        "file": "hooks/pre-push",
        "find": "if ! gate_run \"red-proof anchors\"",
        "replace": "if [ -n \"${_chg_live:-}\" ]; then\nif ! gate_run \"red-proof anchors\"",
        "matches": 1,
    },
    {
        "why": "v3471 — the census only NAMED in a comment beside a different script (eye on v3469)",
        "file": "hooks/pre-push",
        "find": "     python3 \"$REPO/tv/test_the_heart_can_see_its_own_instruments.py\" TestHeartSeesItsInstruments.test_every_declared_red_proof_is_well_formed; then\n",
        "replace": "     python3 \"$REPO/tv/review_lite.py\"; then  # test_the_heart_can_see_its_own_instruments.py\" TestHeartSeesItsInstruments.test_every_declared_red_proof_is_well_formed\n",
        "matches": 1,
    },
    {
        "why": "v3471 — a heredoc that never terminates blinds the counter to the rest of the hook",
        "file": "hooks/pre-push",
        "find": "if ! gate_run \"red-proof anchors\"",
        "replace": "cat <<NEVER_TERMINATED\nif ! gate_run \"red-proof anchors\"",
        "matches": 1,
    },
]
