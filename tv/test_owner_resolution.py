# -*- coding: utf-8 -*-
"""v2698 — WHO OWNS THIS BOARD IS THE MOST CONSEQUENTIAL BOOLEAN IN THE FILE.

`window._D2R_OWNER` decides whether a browser is Konyo's board or somebody else's. Everything
downstream hangs off it: `_isCousinShell = !_D2R_OWNER`, which gates `_seedsBelongHere`, which
decides whether 245 seeded uniques appear in a stranger's chronicle. When it was wrong, Dean's
board showed 243/403 of another man's finds. That is the defect this file exists to prevent
coming back.

⚠ IT HAS NOW BROKEN IN BOTH DIRECTIONS, WHICH IS WHY THE TEST IS A TABLE AND NOT AN ASSERTION.

    too generous — a claimed browser inherited the owner's chronicle          (the Dean defect)
    too strict   — an automated file:// world could not stop being the owner, so the claim bar
                   never rendered, btn.onclick was never assigned, and the ONE spec about the
                   stranger path died on `b.onclick is not a function`

v2694 fixed the first by making an automated file:// world resolve as OWNER, so the seed specs
stopped being refused. That was correct and it caused the second: the claim bar is gated on
`if (claimed || window._D2R_OWNER) return`. Two fixes breaking each other, the second landing on
the seat of the first. v2698 added a `d2r_testGuest` opt-out read ONLY inside the automated
branch — narrow enough that a real person cannot reach it (a real browser has
navigator.webdriver false) and short-lived enough that a claim overrides it (the claim checks
return before it).

=== WHY THIS RUNS THE REAL FRAGMENT AND NOT A COPY OF THE RULE ===
The function is extracted from bible.html and EXECUTED in a VM sandbox with every global under
this test's control. It is not re-implemented in Python. A second implementation of a rule is
how you get a confident number and no truth — chronicle_resolve.py says exactly that about this
same family of logic, and this test would be worthless if it graded a paraphrase.

⚠ THE HARNESS LIED FIRST, AND THAT IS RECORDED ON PURPOSE. The first version of this proof set
`global.navigator = {webdriver: true}` in plain node. Modern node ships a BUILT-IN `navigator`
whose `webdriver` is undefined, and the assignment does not take — so the automated branch never
fired and the run reported a FAILURE that was entirely the instrument's. Measured:
`typeof navigator === 'object'`, `navigator.webdriver === undefined`. Hence vm.createContext,
where the sandbox is the only global there is. [[feedback-suspect-the-instrument]]
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")

# (label, ownerClaim, navigator.webdriver, location.protocol, d2r_testGuest, expected owner)
CASES = [
    ("a real person, file://, unclaimed",            None,      None, "file:", None, False),
    ("a real person, http, unclaimed",               None,      None, "http:", None, False),
    ("PLAYWRIGHT unclaimed - the seed specs need this", None,    True, "file:", None, True),
    ("PLAYWRIGHT + testGuest - the stranger path",    None,      True, "file:", "1", False),
    ("PLAYWRIGHT claimed as THIS install",            "INST123", True, "file:", "1", True),
    ("PLAYWRIGHT claimed with the wildcard",          "*",       True, "file:", "1", True),
    ("claimed by ANOTHER install",                    "OTHER99", True, "file:", None, False),
    ("a real person with a stray testGuest key",      None,      None, "file:", "1", False),
    ("webdriver true but SERVED over http",           None,      True, "http:", None, False),
]


def _fragment():
    """The real `window._D2R_OWNER = (function(){...})();` lifted out of bible.html.

    Both ends are bound — the opening paren is matched to its own close — because a fixed-size
    window past the region reads as absent and would grade a truncated function.
    """
    s = io.open(BIBLE, encoding="utf-8").read()
    i = s.find("window._D2R_OWNER =")
    if i < 0:
        raise AssertionError(
            "GUARD CANNOT GRADE: `window._D2R_OWNER =` is not in bible.html. It was renamed or "
            "removed — fix this test before trusting any verdict it prints."
        )
    depth = 0
    for j in range(s.index("(", i), len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return s[i:s.index(";", j) + 1]
    raise AssertionError("GUARD CANNOT GRADE: the _D2R_OWNER IIFE is never closed")


def _run_cases(frag):
    js = """
const vm = require('vm');
const FRAG = %s, CASES = %s, out = [];
for (const c of CASES) {
  const store = {};
  if (c[1] !== null) store['d2r_ownerClaim'] = c[1];
  if (c[4] !== null) store['d2r_testGuest']  = c[4];
  const sandbox = {
    window: { localStorage: { getItem: k => (k in store ? store[k] : null) },
              _D2R_INSTALL: 'INST123' },
    navigator: { webdriver: c[2] },
    location:  { protocol: c[3] },
  };
  vm.createContext(sandbox);
  vm.runInContext(FRAG, sandbox);
  out.push({ label: c[0], got: sandbox.window._D2R_OWNER, want: c[5] });
}
console.log(JSON.stringify(out));
""" % (json.dumps(frag), json.dumps([[c[0], c[1], c[2], c[3], c[4], c[5]] for c in CASES]))
    r = subprocess.run([_node(), "-e", js], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("node refused the fragment: %s" % (r.stderr or "")[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


def _node():
    for exe in ("node", "/usr/local/bin/node", "/opt/homebrew/bin/node"):
        try:
            if subprocess.run([exe, "-v"], capture_output=True).returncode == 0:
                return exe
        except Exception:
            continue
    raise unittest.SkipTest("node is not available to execute the fragment")


class OwnerResolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = _run_cases(_fragment())

    def test_every_case_resolves_as_ruled(self):
        wrong = [r for r in self.rows if r["got"] != r["want"]]
        self.assertEqual(
            len(self.rows), len(CASES),
            "the harness returned %d rows for %d cases -- it is not grading what it claims"
            % (len(self.rows), len(CASES))
        )
        self.assertEqual(
            wrong, [],
            "ownership resolved wrongly in %d of %d cases: %s"
            % (len(wrong), len(self.rows),
               " | ".join("%s -> %s (want %s)" % (r["label"], r["got"], r["want"]) for r in wrong))
        )

    def test_a_real_person_is_never_the_owner_by_accident(self):
        """The half that protects Dean. No key a user can set may make them the owner."""
        for r in self.rows:
            if "real person" in r["label"]:
                self.assertIs(r["got"], False,
                              "%s resolved as OWNER -- a stranger would inherit the seeded "
                              "chronicle, which is the Dean defect exactly" % r["label"])

    def test_the_automated_world_can_still_be_both(self):
        """Both directions must remain reachable, or one path becomes untestable forever."""
        by = {r["label"]: r["got"] for r in self.rows}
        self.assertIs(by["PLAYWRIGHT unclaimed - the seed specs need this"], True,
                      "the automated world stopped being the owner -- every seed spec will be "
                      "refused, which is what v2694 was for")
        self.assertIs(by["PLAYWRIGHT + testGuest - the stranger path"], False,
                      "the automated world can no longer play the stranger -- the claim bar "
                      "never renders, btn.onclick is never assigned, and the stranger spec "
                      "dies on `b.onclick is not a function`")

    def test_a_claim_outranks_the_test_flag(self):
        """Otherwise a spec could clear the store, claim, and still not be the owner after."""
        by = {r["label"]: r["got"] for r in self.rows}
        self.assertIs(by["PLAYWRIGHT claimed as THIS install"], True)
        self.assertIs(by["PLAYWRIGHT claimed with the wildcard"], True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
