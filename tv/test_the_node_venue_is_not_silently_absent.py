# -*- coding: utf-8 -*-
"""A VENUE THAT CANNOT RUN THE DRIVES MUST SAY SO ONCE, LOUDLY.

FOUND BY THE CODEX EYE on v3170 (cross-family review, openai/gpt-5.6-terra), and it is right:

    "the new gate can pass without executing its assertion. drive() converts missing Node (or a
     timeout) into skipTest, and unittest counts a skip as not-a-failure."

⚠ THE PATTERN IS THE HOUSE STYLE, NOT A NEW MISTAKE. `skipTest("node unavailable - a skip is NOT
a pass")` appears at 26 sites across 9 law files — the message itself already knows the hazard.
The skip is deliberate: a developer without node should still be able to run the python laws.

★ BUT 26 QUIET SKIPS IS NOT A REPORT. If node ever vanishes from a venue, every law that DRIVES
shipped JavaScript in a real engine stops asserting at once, and the suite still prints OK. That
is the exact shape of [[regression-guard]]'s green-that-lies: SAMPLE != VERDICT, SKIP != PASS.
And [[feedback-blind-fixture-green-gate]] names the HOST MACHINE as one of the usual culprits.

So instead of rewriting 26 call sites into failures, ONE law fails: the venue is asserted once,
by name, with the number of laws that would have gone silent. One loud failure that names the
cause beats twenty-six quiet skips that name nothing.

⚠ IT FAILS EVERYWHERE, NOT ONLY IN CI. A venue that cannot execute the shipped JavaScript is
worth knowing about on a laptop too — that is where a false green is most likely to be believed.
The remedy is one line and it is in the message.
"""
import glob
import io
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable
    enable()
except Exception:
    pass

MARK = "node unavailable"


def _laws_that_need_node():
    """Every law file that would go quiet without node. -> sorted [basename]"""
    out = []
    for p in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        try:
            with io.open(p, encoding="utf-8") as fh:
                src = fh.read()
        except Exception:
            continue
        if MARK in src and os.path.basename(p) != os.path.basename(__file__):
            out.append(os.path.basename(p))
    return out


class TheNodeVenueIsNotSilentlyAbsent(unittest.TestCase):

    def test_node_is_present_or_this_venue_cannot_prove_the_shipped_javascript(self):
        laws = _laws_that_need_node()
        self.assertTrue(laws, "nothing drives node any more - this guard is now pointless and "
                              "should be deleted rather than left as decoration")
        where = shutil.which("node")
        self.assertIsNotNone(
            where,
            "node is NOT on this venue, so %d law file(s) would skip instead of assert and the "
            "suite would still print OK: %s. Every one of them drives SHIPPED JavaScript in a "
            "real engine - without node, nothing proves the page behaves at all. "
            "Remedy: install node (CI already does, via actions/setup-node). "
            "A skip is not a pass." % (len(laws), ", ".join(laws[:6])))

    def test_the_node_on_this_venue_actually_runs(self):
        """PRESENT IS NOT WORKING. A node on PATH that cannot execute is the same false green,
        wearing a passing `which`. [[the-unjoined-end]]"""
        if shutil.which("node") is None:
            self.skipTest("no node — the law above is the one that reports that")
        try:
            r = subprocess.run(["node", "-e", "process.stdout.write('ok')"],
                               capture_output=True, text=True, timeout=30)
        except Exception as exc:
            self.fail("node is on PATH but would not run (%s)" % type(exc).__name__)
        self.assertEqual(r.returncode, 0, "node exited %s: %s" % (r.returncode, (r.stderr or "")[:200]))
        self.assertEqual((r.stdout or "").strip(), "ok",
                         "node ran but did not produce its own output — the drives would read "
                         "an empty result as a page defect")


if __name__ == "__main__":
    unittest.main(verbosity=2)
