# -*- coding: utf-8 -*-
"""THE DOCTOR WORKED PERFECTLY AND ITS WHOLE COLUMN READ UNKNOWN, BECAUSE NOBODY HAD SAID WHAT IT
WATCHES IN THE WORDS THE TABLE USES.

organ_matrix measured it without flinching: *"doctor names 59 thing(s), and NONE of them resolves
to any of the 58 surfaces — it is naming a different KIND of thing (concerns, not code objects)."*
A check is called "shelf lanes reading"; a surface is called "shelf-cards". Those two never meet,
so a quarter of the table was unanswerable about an organ that was doing its job.

⚠⚠ IT CANNOT BE DERIVED, AND THAT WAS MEASURED BEFORE IT WAS AUTHORED. A first attempt parsed each
check's body for unambiguous surface-shaped tokens — dotted, hyphenated, `/api/` and `#id` forms.
On a 12-check sample, 4 reached anything at all, and what they reached was `control_app.py`,
`status`, `per-lane`, `REG-415`. Not one registry surface. The relationship is simply not present
in the code, so no parser can find it and the deriver was thrown away rather than shipped as noise.

So `WATCHES` states it, and this law is what keeps a stated thing honest:

  · EVERY check must appear. Silence is not "covers nothing" — a check added next week with no
    declaration would otherwise inherit an empty list and read ABSENT, which is a claim nobody
    made. That is the whole failure mode of a hand-maintained map.
  · A check that truly watches no registry surface declares an EMPTY tuple, deliberately, and
    reads ABSENT. Under-claiming is the intended bias: organ_matrix's own rule is that a table
    reporting coverage it cannot demonstrate is worse than the empty one he was shown.
  · A declared name that is NOT in the registry fails here. A typo would otherwise sit in the map
    forever, matching nothing, looking exactly like considered coverage.

[[unknown-stays-unknown]] [[the-unjoined-end]] [[regression-guard]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as CD      # noqa: E402
import organ_matrix as OM        # noqa: E402


class TestTheDoctorSaysWhatItWatches(unittest.TestCase):

    def setUp(self):
        self.checks = [n for n, _ in CD.CHECKS]
        self.assertGreater(len(self.checks), 40,
                           "only %d checks parsed out of console_doctor — the reader stopped "
                           "matching the file, so everything below is UNKNOWN not clean"
                           % len(self.checks))
        self.registry = set(OM.surfaces())
        self.assertGreater(len(self.registry), 40,
                           "only %d surfaces in the registry — same problem, other end"
                           % len(self.registry))

    def test_every_check_declares_what_it_watches(self):
        """THE LAW. A missing key is the failure, not an empty one."""
        missing = sorted(set(self.checks) - set(CD.WATCHES))
        self.assertEqual(
            missing, [],
            "%d check(s) do not say what they watch: %s. A check with no declaration reads "
            "ABSENT in the organ table — a claim nobody made. Declare an EMPTY tuple if it "
            "genuinely covers no registry surface." % (len(missing), missing))

    def test_the_map_names_no_check_that_does_not_exist(self):
        """The other direction: a renamed check leaves its old declaration behind, still looking
        like coverage of something."""
        ghosts = sorted(set(CD.WATCHES) - set(self.checks))
        self.assertEqual(ghosts, [],
                         "WATCHES declares %d check(s) that no longer exist: %s" % (len(ghosts), ghosts))

    def test_every_declared_surface_is_a_real_surface(self):
        """A typo here matches nothing and reads as considered coverage — the exact shape of a
        green that lies."""
        declared = {s for v in CD.WATCHES.values() for s in v}
        bogus = sorted(declared - self.registry)
        self.assertEqual(
            bogus, [],
            "%d declared surface(s) are not in the registry: %s. They can never match, so they "
            "would sit here forever looking like coverage." % (len(bogus), bogus))

    def test_the_report_actually_publishes_the_declaration(self):
        """Declaring it and not publishing it is the unjoined end this exists to close."""
        rows = (CD.report() or {}).get("rows") or []
        self.assertTrue(rows, "console_doctor.report() returned no rows")
        self.assertTrue(all("surfaces" in r for r in rows),
                        "report() rows do not carry `surfaces`, so the declaration reaches no "
                        "reader and the organ table cannot use it")
        named = {s for r in rows for s in (r.get("surfaces") or [])}
        self.assertTrue(
            named & self.registry,
            "report() publishes surfaces but NONE of them is in the registry — the join is "
            "cosmetic and the doctor's column is still UNKNOWN everywhere")


RED_PROOF = [
    {
        "why": "removes one check's declaration, which is the failure this law exists for: a check "
               "with no entry reads ABSENT in the organ table, a claim nobody made",
        "file": "console_doctor.py",
        "find": '    "locked lanes":                ("locks",),\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "puts a surface in the map that does not exist in the registry — it can never "
               "match, so it sits there forever looking like considered coverage",
        "file": "console_doctor.py",
        "find": '    "his gear":                    ("vault",),',
        "replace": '    "his gear":                    ("vault", "no-such-surface"),',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
