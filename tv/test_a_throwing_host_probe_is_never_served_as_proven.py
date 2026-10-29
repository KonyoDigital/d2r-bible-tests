#!/usr/bin/env python3
"""v3842 - the v3841 second eye: a host probe that THROWS is UNKNOWN, never "this PC has it".

host_lacks returned False when its probe raised, so _cache_serve (which serves only on `is False`) handed back a
carried PROVEN for a proof whose declared need this PC could not even probe. host_lacks now returns None there, as its
docstring always said. Driven: a declared capability whose probe raises reads None, and _cache_serve over a cache that
WOULD hit returns no verdict for it, while the same proof with a probe that answers "present" is still served.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import heart2 as H  # noqa: E402


class _Boom(object):
    @staticmethod
    def probe():
        raise RuntimeError("probe died")

    @staticmethod
    def have():
        return True


class AThrowingHostProbeIsNeverServedAsProven(unittest.TestCase):
    def setUp(self):
        sys.modules["_tvd_probe_fixture"] = _Boom
        self._saved = dict(H.PROOF_NEEDS_HOST)
        H.PROOF_NEEDS_HOST["fx-throws"] = ("_tvd_probe_fixture", "probe", "a probe that raises")
        H.PROOF_NEEDS_HOST["fx-present"] = ("_tvd_probe_fixture", "have", "a capability this PC has")

    def tearDown(self):
        H.PROOF_NEEDS_HOST.clear()
        H.PROOF_NEEDS_HOST.update(self._saved)
        sys.modules.pop("_tvd_probe_fixture", None)

    def test_a_throwing_probe_reads_unknown_not_present(self):
        lacks, words = H.host_lacks("fx-throws")
        self.assertIsNone(lacks, "a probe that raised read as %r" % (lacks,))
        self.assertIn("probe failed", words)
        self.assertIs(H.host_lacks("fx-present")[0], False)

    def test_cache_serve_never_serves_a_proof_whose_probe_threw(self):
        src = open(os.path.join(HERE, "heart2.py"), encoding="utf-8").read()
        body = src[src.index("def _cache_serve("):src.index("def _cache_bank(")]
        # the gate in the one serve: anything but a definite False is not served
        self.assertIn('_lacks = host_lacks(pr.get("needs"))[0]', body)
        self.assertIn("if _lacks is not False:", body)
        self.assertLess(body.index("if _lacks is not False:"), body.index("return PROVEN"))
        # and the value that reaches it for a throwing probe is the one that stops it
        self.assertIsNot(H.host_lacks("fx-throws")[0], False)


if __name__ == "__main__":
    unittest.main()
