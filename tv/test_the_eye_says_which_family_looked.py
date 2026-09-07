# -*- coding: utf-8 -*-
"""v2766 — A DARK EYE AND AN ABSENT ONE LOOKED IDENTICAL ON THE FLEET.

MEASURED before the change, off the live beacon:

    Konyo  eye={"live": false, "ageMs": 0}
    Dean   eye={"live": false, "ageMs": 63824123}

and the card rendered the glyph ONLY when `live` was true, so three different machines drew the
same nothing:

    · no second model family is INSTALLED there   (Dean — correct and expected)
    · one is installed and IDLE                   (Konyo, lane toggled off)
    · one is installed, on, and FAILING

Absence, rest and failure are not the same fact. [[zero-needs-a-denominator]]

=== ⚠ WHAT THIS IS *NOT* ===
The task that produced this file was first written as "make the eye provider-neutral", and that was
WRONG — it already is, and the correction is kept here because writing it before measuring is the
error worth remembering:

    chronicle_hunt.py   lane = (page or {}).get("lane") or "claude"   <- Claude IS the default
    chronicle_hunt.py   ZERO grok references anywhere in the reader
    control_app.py      "GROK EYES (G5) — REMOVABLE. OFF by default." + a removal checklist

Konyo's ruling — *"grok doesnt exist for dean.. it all needs to be claude based.. default as if
shadow is off toggled off"* — was ALREADY the built behaviour. Nothing was rebuilt. The only real
gap was that none of it reached the WIRE, so the card could not say which of the three states a
dark dot meant.

=== ⚠⚠ AVAILABILITY IS NOT A SECOND EYE, AND THIS FILE GUARDS THAT ===
A machine reporting a second family has a lane that COULD look. It has not looked. Only
`second_eye_ledger` records a look, and it refuses same-family ones on purpose so a model cannot
certify its own work. If a Claude run on Dean's box ever banked as a "second eye", the ledger would
report a filled seat that is empty — worse than no ledger at all.

    CHECK      any model, anywhere, including Claude on Dean's box. Bankable as a check.
    SECOND EYE a DIFFERENT family from the author. Where none exists the honest state is an
               EMPTY SEAT, said out loud.

[[grok-second-eye]] [[feedback-silence-is-not-evidence]] [[workflow-third-eye-provider-neutral]]
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import control_app as CA  # noqa: E402

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
APP = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _render(cases):
    """Run the SHIPPED _fleetEye in node. -> dict|None

    ⚠ THE REAL BUILDER, not a re-description of it. `escC` is stubbed because it belongs to the
    console's own escaping rules, which this file does not own and must not restate.
    """
    i = UI.find("      var _fleetEye = function(e){")
    j = UI.find("      window._fleetEye = _fleetEye;", i)
    if i < 0 or j < 0:
        return None
    js = ("var window = {};\n"
          "var escC = function(s){ return String(s === undefined ? '' : s)"
          ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\"/g,'&quot;'); };\n"
          + UI[i:j] + "\n"
          "const cases = " + json.dumps(cases) + ";\n"
          "const out = {}; for (const k in cases) out[k] = _fleetEye(cases[k]);\n"
          "console.log(JSON.stringify(out));")
    p = os.path.join(os.environ.get("TMPDIR", "/tmp"), "fleet_eye_probe.js")
    io.open(p, "w", encoding="utf-8").write(js)
    try:
        r = subprocess.run(["node", p], capture_output=True, text=True, timeout=90)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads((r.stdout or "").strip().split("\n")[-1])
    except Exception:
        return None


class TheEyeSaysWhichFamilyLooked(unittest.TestCase):

    # ── ⚠⚠ THE WIRE ─────────────────────────────────────────────────────────────────────────
    def test_the_wire_carries_the_provider_and_the_family(self):
        e = CA._eye_for_wire()
        if e is None:
            self.skipTest("the eye pulse did not run here, so there is no payload to grade — "
                          "a skip is NOT a pass")
        self.assertEqual("claude", e.get("provider"),
                         "the wire does not say WHO read, so a consumer has to assume it")
        self.assertEqual("anthropic", e.get("family"))
        self.assertIn("second", e, "the wire says nothing about a second family, which is the "
                                   "whole gap: absence, rest and failure stay indistinguishable")

    def test_the_second_lane_state_is_one_of_the_four(self):
        st = CA._second_eye_lane_state()
        self.assertIn(st.get("state"), ("absent", "off", "on", "unknown"))
        if st["state"] in ("absent", "unknown"):
            self.assertTrue(st.get("why"),
                            "the lane is %r and nothing says why — an unexplained absence reads "
                            "as a fault when on most machines it is simply correct" % st["state"])

    def test_an_UNREACHABLE_lane_is_UNKNOWN_and_never_absent(self):
        """★ THE DISTINCTION THAT MATTERS MOST. "not installed" is a MEASUREMENT; "I could not ask"
        is not. Collapsing the second into the first would tell Konyo a cousin has no second family
        when the truth is nobody looked. [[unknown-stays-unknown]]"""
        src = APP[APP.find("def _second_eye_lane_state():"):]
        src = src[:src.find("\ndef ", 1)]
        self.assertIn("except ImportError:", src,
                      "the lane does not separate 'not installed' from 'could not be asked'")
        self.assertIn('state="absent"', src)
        i = src.find("except Exception as exc:")
        self.assertGreater(i, 0, "a non-import failure is not handled at all")
        self.assertNotIn('state="absent"', src[i:i + 400],
                         "a lane that RAISED is being reported as absent — a failed probe "
                         "rendering as a measured 'none'")

    def test_the_none_contract_is_UNTOUCHED(self):
        """⚠ `_eye_for_wire()` returns None when the pulse did not run, and an existing law
        (test_control) pins that. Adding fields must not turn UNKNOWN into a payload."""
        i = APP.find("def _eye_for_wire():")
        blk = APP[i:APP.find("\ndef ", i + 1)]
        self.assertIn("return None", blk,
                      "the pulse-did-not-run case stopped returning None, so an unmeasured eye "
                      "now ships a payload and reads as measured")

    def test_it_does_NOT_keep_its_own_family_table(self):
        """★ `second_eye_ledger.family_of` is the authority that ENFORCES the cross-family rule. A
        second table here would be free to drift from it, and the wire would then name a family the
        ledger does not recognise. [[copy-drift]]"""
        i = APP.find("def _second_eye_lane_state():")
        blk = APP[i:APP.find("\ndef _eye_for_wire", i)]
        self.assertIn("second_eye_ledger", blk, "the lane state does not consult the family authority")
        # ⚠ FORBID THE FAMILY LITERAL, NOT A TABLE SHAPE. My first cut asserted `"xai":` was absent
        # — a family name in KEY position — and a sabotage writing `{"grok": "xai"}` sailed straight
        # through it, because there the family is the VALUE. A guard aimed at one spelling of a
        # defect measures that spelling and nothing else. No family name may be written here at
        # all; the ledger is the only place they are allowed to live.
        for fam in ('"xai"', "'xai'", '"anthropic"', "'anthropic'", '"openai"', "'openai'"):
            self.assertNotIn(fam, blk,
                             "the family name %s is hardcoded beside the ledger that enforces the "
                             "cross-family rule. Two tables drift, and then the wire names a "
                             "family the ledger does not recognise." % fam)

    # ── ⚠⚠ THE CARD ─────────────────────────────────────────────────────────────────────────
    def test_the_four_states_render_DIFFERENTLY(self):
        got = _render({
            "absent": {"live": False, "ageMs": 63824123, "provider": "claude",
                       "second": {"state": "absent", "provider": "grok",
                                  "why": "the CLI is not installed"}},
            "off": {"live": False, "ageMs": 0, "provider": "claude",
                    "second": {"state": "off", "provider": "grok"}},
            "on": {"live": True, "ageMs": 1200, "provider": "claude",
                   "second": {"state": "on", "provider": "grok"}},
            "unknown": {"live": False, "ageMs": 5000, "provider": "claude",
                        "second": {"state": "unknown", "why": "raised TimeoutError"}},
        })
        if got is None:
            self.skipTest("node unavailable, so the shipped builder could not be run — a skip is "
                          "NOT a pass")
        self.assertIn("no second model family on this machine", got["absent"])
        self.assertIn("the CLI is not installed", got["absent"],
                      "the absence does not say WHY, so a correct machine looks broken")
        self.assertIn("toggled off", got["off"])
        self.assertIn("second lane ON", got["on"])
        self.assertIn("UNKNOWN", got["unknown"],
                      "a lane nobody could ask renders as a settled state")
        self.assertNotEqual(got["absent"], got["off"],
                            "an ABSENT second family and an IDLE one render identically — the "
                            "exact defect this file exists for")
        self.assertIn("fleet-eye-dark", got["absent"])
        self.assertIn("fleet-eye-live", got["on"])

    def test_no_pulse_renders_NOTHING_rather_than_a_dot(self):
        got = _render({"none": None})
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertEqual("", got["none"],
                         "an omitted eye field drew a chip anyway, so UNKNOWN is being rendered "
                         "as a measured state")

    def test_availability_is_never_worded_as_a_LOOK(self):
        """★★ THE SAFETY LAW. A lane that COULD look has not looked. If this chip ever reads as a
        completed second eye, the empty seat starts reporting as filled — worse than no ledger."""
        i = UI.find("      var _fleetEye = function(e){")
        blk = UI[i:UI.find("      window._fleetEye = _fleetEye;", i)]
        for banned in ("verified", "second eye", "reviewed", "confirmed", "checked by"):
            self.assertNotIn(banned, blk.lower(),
                             "the fleet eye chip says %r. Availability is not a look, and only "
                             "second_eye_ledger records one." % banned)

    def test_the_builder_and_its_caller_share_a_SCRIPT_BLOCK(self):
        """⚠ control_ui.html has more than one <script>, and a call across them is a DEAD RENDER —
        five times in this file's history. This is cheap to assert and impossible to eyeball."""
        blocks = [(m.start(), UI.index("</script>", m.start()))
                  for m in re.finditer(r"<script[^>]*>", UI)]

        def blk_of(pos):
            for n, (a, b) in enumerate(blocks):
                if a <= pos <= b:
                    return n
            return None
        d = UI.find("var _fleetEye = function(e){")
        c = UI.find("+ _fleetEye(m.eye)")
        self.assertGreater(d, 0, "the builder is gone")
        self.assertGreater(c, 0, "the fleet row no longer calls the builder")
        self.assertIsNotNone(blk_of(d), "the builder is not inside any <script>")
        self.assertEqual(blk_of(d), blk_of(c),
                         "the builder and its caller are in DIFFERENT script blocks — the chip "
                         "would silently render nothing")
        self.assertLess(d, c, "the builder is defined after its caller")


if __name__ == "__main__":
    unittest.main(verbosity=2)
