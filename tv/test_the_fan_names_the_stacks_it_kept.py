# -*- coding: utf-8 -*-
"""#53 — THE PARTIAL SOLVE MUST NAME THE STACKS IT ACTUALLY KEPT.

v2848 made the revert INCREMENTAL: withdraw the most-displaced stack, re-measure, stop as soon as
the arrangement is no longer worse. That was the right fix for "an all-or-nothing revert throws
good solutions away", and it landed with a defect one field over.

`applied` is dense over the stacks that MOVED. `kept` and `dropped` hold indices into `stacks`.
Two index spaces — and the partial path filtered one of them by the other's values:

    var landed = applied.filter(function (m, mi) { return dropped.indexOf(mi) < 0; });

MEASURED 2026-09-11, by running the real `_hrtFanFit` over a stub DOM (below). A fan with a
non-moving stack sorted first, one stack withdrawn and one kept:

    moves REPORTED   : [{"x":100,"dx":0,"dy":15}]      <- WITHDRAWN, carries no transform
    transforms ON DOM: [{"name":"LC","x":500,...}]     <- KEPT, and named nowhere

Exactly inverted. `keptStacks: 1` was right the whole time, and that is what hid it: a correct
count standing beside a wrong name is the defect he has caught here more than any other, and no
instrument was asking. [[label-outlived-referent]] [[unknown-stays-unknown]]

⚠ THIS LAW EXECUTES THE FUNCTION, IT DOES NOT READ IT. Four source-reading laws already guard
`_hrtFanFit`'s inputs and its report plumbing; none of them could see this, because the code
LOOKED right — the mistake is only visible in what it returns. [[regression-guard]]
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

_START = "  function _hrtFanFit(root) {"
_END = "\n  }\n"


def _fn(case):
    """The WHOLE function, by anchors at both ends — never a fixed window.
    [[source-window-shortcut]] Every inner block closes at 4+ spaces, so the first `\\n  }\\n`
    after the header is this function's own close. If that stops being true the extract will not
    parse and node says so, loudly, rather than this law quietly measuring a fragment."""
    i = UI.find(_START)
    case.assertGreater(i, 0, "anchor %r is gone — this law has lost its target" % _START)
    j = UI.find(_END, i + len(_START))
    case.assertGreater(j, i, "closing anchor not found — the extract would be truncated")
    return UI[i:j + len(_END)]


# ── a stub DOM just rich enough for the solver: rects, a REAL hit test, transforms ─────────────
_STUB = r"""
'use strict';
class El {
  constructor(o) {
    this.attrs = Object.assign({}, o.attrs || {});
    this.textContent = o.text === undefined ? '' : o.text;
    this.children = [];
    this.base = o.rect || null;
    this.name = o.name;
    this.w = o.w;
  }
  _off() {
    const t = this.attrs.transform;
    if (!t) return [0, 0];
    const m = /translate\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\)/.exec(t);
    return m ? [parseFloat(m[1]), parseFloat(m[2])] : [0, 0];
  }
  getClientRects() {
    if (!this.base) return [];
    const [dx, dy] = this._off(), b = this.base;
    return [{ left: b.l + dx, right: b.r + dx, top: b.t + dy, bottom: b.b + dy,
              width: b.r - b.l, height: b.b - b.t }];
  }
  getBoundingClientRect() {
    const rs = this.getClientRects();
    return rs.length ? rs[0] : { left: 0, right: 0, top: 0, bottom: 0, width: 0, height: 0 };
  }
  getAttribute(n) { return n in this.attrs ? this.attrs[n] : null; }
  setAttribute(n, v) { this.attrs[n] = String(v); }
  removeAttribute(n) { delete this.attrs[n]; }
  contains(o) { return o === this; }
  getComputedTextLength() { return this.w === undefined ? (this.base.r - this.base.l) : this.w; }
}
let ALL = [];
global.innerWidth = 2000; global.innerHeight = 2000;
global.getComputedStyle = () => ({ visibility: 'visible', display: 'block', opacity: '1' });
global.document = {
  elementFromPoint(x, y) {
    let top = null;
    for (const e of ALL) for (const r of e.getClientRects())
      if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) { top = e; break; }
    return top;                                  // last in DOM order == topmost
  }
};
function build(spec) {
  ALL = spec.map(s => new El(s));
  const SVG = {
    getBoundingClientRect: () => ({ left: 0, top: 0, right: 960, bottom: 400,
                                    width: 960, height: 400 }),
    querySelectorAll: sel => (sel === 'text.hrt-fan'
      ? ALL.filter(e => /(^|\s)hrt-fan(\s|$)/.test(e.attrs.class || '')) : [])
  };
  return { querySelector: sel => (sel === 'svg.hrt' ? SVG : null),
           querySelectorAll: sel => (sel === '*' ? ALL.slice(0) : []) };
}
const F = (name, x, l, r, t, b, w) =>
  ({ name, attrs: { class: 'hrt-fan', x: String(x), y: String(t) },
     text: name, rect: { l, r, t, b }, w });
const P = (name, l, r, t, b) => ({ name, attrs: { class: 'vessel' }, text: name,
                                   rect: { l, r, t, b } });
"""

# Z sorts FIRST and never moves, so `stacks` index and `applied` index genuinely diverge — that
# divergence IS the defect, and a fixture where they coincide cannot see it.
# V and W are vessel labels hidden UNDER LA: in no instrument's view until LA moves, which is how
# the geometric model and the pixel ratchet come to disagree at all.
_SPEC_PARTIAL = """
const root = build([
  F('Z',  50,  40,  90, 200, 216, 50),
  P('V',      100, 200, 100, 116),
  P('W',      160, 260, 100, 116),
  F('LA', 100, 100, 300, 100, 116, 200),
  P('CH',     195, 205, 100, 116),
  F('LB', 260, 260, 460, 100, 116, 200),
  F('LC', 500, 500, 660, 100, 108, 160),
  F('LD', 520, 520, 680, 100, 108, 160),
]);
"""

# the same world with the second pair removed: the ONLY stack that moves is also the one that must
# be withdrawn, so every stack ends up back where it started — the reverted path.
_SPEC_REVERTED = """
const root = build([
  F('Z',  50,  40,  90, 200, 216, 50),
  P('V',      100, 200, 100, 116),
  P('W',      160, 260, 100, 116),
  F('LA', 100, 100, 300, 100, 116, 200),
  P('CH',     195, 205, 100, 116),
  F('LB', 260, 260, 460, 100, 116, 200),
]);
"""

_TAIL = """
const ff = _hrtFanFit(root);
const onDom = ALL.filter(e => e.attrs.transform)
                 .map(e => ({ x: +e.getAttribute('x'), tf: e.attrs.transform }));
console.log(JSON.stringify({ ff: ff, onDom: onDom }));
"""


def _run(case, spec):
    """Execute the REAL function over the stub. -> (report, transforms actually on the DOM)"""
    d = tempfile.mkdtemp(prefix="fanfit_")
    try:
        p = os.path.join(d, "run.js")
        with io.open(p, "w", encoding="utf-8") as fh:
            fh.write(_STUB + _fn(case) + spec + _TAIL)
        r = subprocess.run([shutil.which("node"), p], capture_output=True, text=True, timeout=90)
        case.assertEqual(0, r.returncode,
                         "node could not run the extracted solver — this law measured NOTHING, "
                         "which is not the same as passing:\n%s" % r.stderr[:1500])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        return out["ff"], out["onDom"]
    finally:
        shutil.rmtree(d, ignore_errors=True)


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — UNMEASURED, not passing")
class TheReportNamesWhatIsOnThePage(unittest.TestCase):

    def test_the_fixture_still_reaches_the_partial_branch(self):
        """A fixture that stopped exercising the branch would let every law below pass vacuously.
        [[feedback-blind-fixture-green-gate]] — the fixture is the usual culprit."""
        ff, _ = _run(self, _SPEC_PARTIAL)
        self.assertTrue(ff.get("ok"), "the solver refused the fixture outright: %r" % (ff,))
        self.assertIs(True, ff.get("partial"),
                      "this fixture no longer drives the solver into the PARTIAL branch "
                      "(partial=%r, keptStacks=%r, droppedStacks=%r, reverted=%r). Every "
                      "assertion below is then about a path that did not run."
                      % (ff.get("partial"), ff.get("keptStacks"),
                         ff.get("droppedStacks"), ff.get("reverted")))
        self.assertGreater(ff.get("droppedStacks") or 0, 0, "nothing was withdrawn")
        self.assertGreater(ff.get("keptStacks") or 0, 0, "nothing was kept")

    def test_this_fixture_can_tell_the_two_implementations_apart(self):
        """★ THE SECOND EYE'S FINDING on v2962, sharpened after its first form proved too weak.

        The old filter `dropped.indexOf(mi) < 0` compares a POSITION in `applied` against values
        that are indices into `stacks`. It is only WRONG when a hole sits in front of a dropped
        stack — here Z (si=0) never moves, so the withdrawn stack is attempted[0] carrying si=1.

        Asserting merely that some si differs from its position is NOT enough: with Z removed the
        gap at B still produces a difference while the two filters could still agree. So this law
        RUNS BOTH IMPLEMENTATIONS over the fixture's own output and demands they DISAGREE. If they
        ever agree, the red-proof that restores the old filter would stay GREEN and this whole file
        would be measuring nothing — the production bug hid for exactly that reason.
        [[feedback-blind-fixture-green-gate]] [[sabotage-is-usually-the-wrong-one]]"""
        ff, _ = _run(self, _SPEC_PARTIAL)
        att = ff.get("attempted") or []
        kept = ff.get("moves") or []
        self.assertTrue(att, "nothing was attempted, so there is nothing to tell apart")
        kept_si = {m.get("si") for m in kept}
        dropped_si = {m.get("si") for m in att} - kept_si
        self.assertTrue(dropped_si,
                        "no stack was withdrawn, so the partial path did not run and neither "
                        "implementation is exercised")
        # what the CORRECT filter yields — by stack index
        correct = [m for m in att if m.get("si") in kept_si]
        # what the OLD, defective filter yielded — position tested against stack indices
        old = [m for i, m in enumerate(att) if i not in dropped_si]
        self.assertNotEqual([m.get("si") for m in correct], [m.get("si") for m in old],
                            "the correct filter and the OLD positional one give the SAME answer "
                            "on this fixture, so it cannot tell them apart. RED_PROOF[0] would "
                            "stay green and every law here would be blind. "
                            "attempted=%r kept=%r dropped=%r"
                            % ([m.get("si") for m in att], sorted(kept_si), sorted(dropped_si)))

    def test_moves_names_exactly_the_stacks_that_kept_a_transform(self):
        """The measured inversion: the withdrawn stack reported as landed, the kept one unnamed."""
        ff, on_dom = _run(self, _SPEC_PARTIAL)
        # ⚠ EYE FINDING on v2962: `moves` carries ONE row per STACK, while the harness reads
        # one row per ELEMENT — _hrtFanFit stamps a stack's transform onto every label in it. The
        # sibling verdict law already measured "3 stacks kept · DOM: 5 of 20 labels transformed".
        # These two lists being the same length here is a property of THIS fixture, not a
        # contract, so compare the stacks both sides name. [[label-outlived-referent]]
        reported = sorted({m["x"] for m in (ff.get("moves") or [])})
        on_page = sorted({t["x"] for t in on_dom})
        self.assertEqual(on_page, reported,
                         "`moves` does not name the stacks that actually carry a transform.\n"
                         "  reported by moves : %s\n"
                         "  on the DOM        : %s\n"
                         "A reader of this report — the CDP probe, and the render harness through "
                         "data-fanfit — is told a stack moved that is back where it started, and "
                         "told nothing about the one that did move."
                         % (reported, on_page))

    def test_keptStacks_and_moves_are_the_same_count(self):
        """Two fields answering one question must not disagree inside one payload."""
        ff, _ = _run(self, _SPEC_PARTIAL)
        self.assertEqual(ff.get("keptStacks"), len(ff.get("moves") or []),
                         "keptStacks=%r but moves carries %d entr(y/ies) — the count and the "
                         "names come from different arithmetic, so one of them is wrong and the "
                         "payload cannot say which"
                         % (ff.get("keptStacks"), len(ff.get("moves") or [])))

    def test_the_attempt_survives_the_withdrawal(self):
        """Withdrawing a stack must not erase the record that it was tried."""
        ff, _ = _run(self, _SPEC_PARTIAL)
        self.assertEqual(len(ff.get("attempted") or []),
                         (ff.get("keptStacks") or 0) + (ff.get("droppedStacks") or 0),
                         "`attempted` does not cover kept + dropped, so the solve's own record of "
                         "what it tried is incomplete and #53's question — did it revert, or find "
                         "nothing? — goes back to being unanswerable")


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — UNMEASURED, not passing")
class AFullRevertClaimsNoMoves(unittest.TestCase):
    """`moves` meant something different on each return: what LANDED on two of them, what was
    ATTEMPTED on the reverted one — which published `moves: N` beside `keptStacks: 0` in the same
    DOM record. One field, one meaning. [[label-outlived-referent]]"""

    def test_the_fixture_still_reaches_the_reverted_branch(self):
        ff, _ = _run(self, _SPEC_REVERTED)
        self.assertTrue(ff.get("ok"), "the solver refused the fixture outright: %r" % (ff,))
        self.assertIs(True, ff.get("reverted"),
                      "this fixture no longer drives the solver into the REVERTED branch "
                      "(reverted=%r, partial=%r, keptStacks=%r)"
                      % (ff.get("reverted"), ff.get("partial"), ff.get("keptStacks")))

    def test_a_full_revert_reports_no_moves_and_leaves_no_transform(self):
        ff, on_dom = _run(self, _SPEC_REVERTED)
        self.assertEqual([], on_dom,
                         "the revert claims nothing landed, but transforms are still on the "
                         "page: %r" % (on_dom,))
        self.assertEqual([], ff.get("moves") or [],
                         "a full revert reports moves=%r beside keptStacks=%r — the payload says "
                         "both 'nothing landed' and 'here is what landed'"
                         % (ff.get("moves"), ff.get("keptStacks")))
        self.assertEqual(0, ff.get("keptStacks"))

    def test_a_full_revert_still_says_what_it_tried(self):
        """`moves: []` must not be bought by throwing the attempt away — that would trade one
        unanswerable question for another. [[unknown-stays-unknown]]"""
        ff, _ = _run(self, _SPEC_REVERTED)
        self.assertGreater(len(ff.get("attempted") or []), 0,
                           "the reverted path reports no attempt at all, so 'it found nothing' "
                           "and 'it found something and put it back' read identically again — "
                           "the exact ambiguity #53 was opened to remove")
        self.assertIsNotNone(ff.get("wouldHaveBeen"),
                             "the reverted path drops wouldHaveBeen")


RED_PROOF = [
    {
        "why": "restoring the positional filter reproduces the measured inversion — the withdrawn "
               "stack named as landed, the kept one named nowhere — while keptStacks stays right",
        "file": "control_ui.html",
        "find": "var landed = applied.filter(function (m) { return kept.indexOf(m.si) >= 0; });",
        "replace": "var landed = applied.filter(function (m, mi) { return dropped.indexOf(mi) < 0; });",
        "matches": 1,
    },
    {
        "why": "dropping `si` from the applied entries leaves the partial filter nothing to match, "
               "so every kept stack falls out and moves goes empty against keptStacks > 0",
        "file": "control_ui.html",
        "find": "applied.push({ si: t, x: st.x,",
        "replace": "applied.push({ x: st.x,",
        "matches": 1,
    },
    {
        "why": "putting `applied` back under `moves` on the reverted path republishes 'here is "
               "what landed' beside keptStacks: 0 in the same payload",
        "file": "control_ui.html",
        "find": "moves: [], attempted: applied,",
        "replace": "moves: applied, attempted: applied,",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # ⚠⚠ EYE FINDING on v2962 — THREE PARTIES DISAGREED ABOUT "node absent", AND THE GREEN ONE WON.
    # The gate declares skip_ok=() ("this gate may never skip") and its own why says "node absent
    # => SKIP, which is UNMEASURED and not a pass". But a class-level @skipIf makes unittest print
    # `OK (skipped=7)` and exit 0, and run_gates maps 0 to PASS. MEASURED with node off PATH:
    # EXIT=0, seven laws skipped, gate GREEN — the skip-counted-as-pass class, on a gate whose
    # whole job is to execute JS.
    # 77 is run_gates' SKIP_EXIT: every other non-zero code is a FAIL, and with skip_ok=() a
    # DECLARED skip is refused rather than waved through. The decorators stay for other runners.
    # [[regression-guard]] [[feedback-blind-fixture-green-gate]]
    if shutil.which("node") is None:
        sys.stderr.write("node is absent — this gate executes the solver and can measure NOTHING "
                         "without it. UNMEASURED, declared as a skip (77), never a pass.\n")
        raise SystemExit(77)
    unittest.main(verbosity=2)
