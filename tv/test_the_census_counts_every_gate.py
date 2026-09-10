"""⚠⚠ THE CENSUS MUST COUNT EVERY REGISTERED GATE, OR ITS DENOMINATOR IS A GUESS.

Heart 2.0 asks "can my own gates still go red?". It answers with `proved / total`. That answer is
only worth anything if `total` is every gate the suite actually runs.

MEASURED 2026-09-10: `run_gates.GATES` held **279** gates and the heart reported **278**. The
missing one was `visual-lock`, whose file is `visual_lock_invariant.py` in the REPO ROOT rather
than in `tv/` — `gate_files()` looked only in `tv/`, failed to find it, and dropped it with no line
saying so. "0 blind of 278" therefore read as *every gate is accounted for* while one had never
been asked. The disagreement between the two counts WAS the finding.

These laws hold the heart to its own premise: the instruments must watch themselves.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]] [[feedback-contradiction-is-the-finding]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ This file prints non-ASCII in its assertion messages and is an entry point, so on a non-UTF-8
# console (Windows stdout is cp1255 here) it would crash WHILE REPORTING and a clean tree would
# exit non-zero. Sibling gates are exempt only because they import control_app, which enables this
# downstream; this one imports heart2/run_gates, so it must enable it itself.
try:
    from console_safe import enable
    enable()
except Exception:
    pass

import heart2 as H       # noqa: E402
import run_gates as G    # noqa: E402


class TheCensusCountsEveryGate(unittest.TestCase):

    def test_the_hearts_scope_is_every_registered_gate(self):
        """★ THE DEFECT ITSELF. One name in GATES that the heart never asks about is one guard
        whose ability to go red is UNKNOWN — and the census would not say so."""
        registered = set(g.name for g in G.GATES)
        seen = set(n for n, _fn in H.gate_files())
        missing = sorted(registered - seen)
        self.assertEqual([], missing,
                         "%d registered gate(s) are outside the heart's census, so `total` is "
                         "smaller than the suite and every percentage under it is measured against "
                         "the wrong denominator: %r" % (len(missing), missing))

    def test_the_heart_invents_no_gate_of_its_own(self):
        """The other direction: a name in the census that nothing runs would inflate `total`."""
        registered = set(g.name for g in G.GATES)
        extra = sorted(set(n for n, _fn in H.gate_files()) - registered)
        self.assertEqual([], extra,
                         "the census counts gate(s) the suite does not run: %r" % extra)

    def test_a_gate_outside_tv_is_addressed_so_every_consumer_resolves_it(self):
        """⚠ THE FIX MUST NOT BE COSMETIC. Counting a root-file gate while handing consumers a
        name they cannot open would trade a silent omission for a silent UNPROVABLE."""
        for name, fn in H.gate_files():
            p = os.path.join(HERE, fn)
            self.assertTrue(os.path.isfile(p),
                            "gate %r is in the census as %r, which does not resolve to a file "
                            "from tv/ — red_proofs_in() and _run_gate() both join it that way"
                            % (name, fn))

    def test_a_root_file_gate_is_placed_in_the_sandbox(self):
        """A gate whose file never reaches the sandbox can only ever report UNPROVABLE."""
        src = H._read_text(os.path.join(HERE, "heart2.py")) or ""
        roots = [fn for _n, fn in H.gate_files() if fn.startswith("..")]
        for fn in roots:
            base = os.path.basename(fn)
            self.assertIn(base, src,
                          "%r is counted from the repo root but make_sandbox never places it "
                          "there, so it can never be proven" % base)


RED_PROOF = [
    {
        'why': 'restoring the tv/-only lookup drops the one gate whose file lives in the repo root, and the census silently counts 278 of 279 again — the exact defect',
        'file': 'heart2.py',
        'find': '                elif os.path.exists(os.path.join(REPO, base)):',
        'replace': '                elif False:',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
