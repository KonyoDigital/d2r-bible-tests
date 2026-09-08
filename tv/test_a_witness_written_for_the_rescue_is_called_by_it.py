#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2807 — A WITNESS WRITTEN FOR THE RESCUE THAT THE RESCUE NEVER ASKED.

`paint_witness` exposes three functions whose docstrings name the rescue as their caller. Measured
across the whole tree, production callers (excluding tests, the module itself, and its CLI):

    blank_strikes              1     joined at v2627 — asks the pixels when nothing else will
    rescue_worked              1     joined at v2601 — did the cure actually cure?
    contradicts_a_blank_beat   0     ← written, tested, gated, and called by NOBODY

The missing one is the one its own docstring calls **"THE VALUABLE DIRECTION, and the one his
rescue needs most … True here should HOLD a rescue."**

★ WHY THAT DIRECTION COSTS MORE THAN THE OTHER. Everything the rescue reasons from is published BY
the page — `blankStrikes`, `elsHigh`, `frozenBeats` all come from JavaScript running inside the
window whose health is in question. A page can be wrong about itself both ways, and this repo has
measured one of them: a window drawing 185 BLANK frames while reporting `painting: true`. The
OTHER direction is worse, because it is the one that ACTS — a beat claiming blank while the
compositor is painting means reloading a working window under his hands and losing whatever he was
looking at. The reload is not free; it is the harm.

⚠ AND UNKNOWN MUST NEVER HOLD A RESCUE. `contradicts_a_blank_beat` returns False when the capture
could not be taken, so an absent witness cannot veto a rescue the beat genuinely called for. This
law pins that direction too: a call site that treated "could not look" as "do not rescue" would
turn a broken camera into a permanently disabled self-heal.
[[the-unjoined-end]] [[feedback-silence-is-not-evidence]]

THE LAW IS THE GENERAL SHAPE. It does not name one function. Every public entry point in
paint_witness whose docstring says the rescue should use it must have a caller outside the tests —
because this is the THIRD time a witness in this tree was built, proven, and joined to nothing.
"""
import os
import ast
import io
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

WITNESS = os.path.join(HERE, "paint_witness.py")
#: files that are production, not tests and not the witness itself
PRODUCTION = ("control_app.py", "console_doctor.py", "stage_witness.py",
              "region_witness.py", "self_arming.py", "tv_diablo.py")

#: the phrases a witness docstring uses to say "the rescue should call this"
_FOR_THE_RESCUE = re.compile(r"rescue", re.I)


def _src(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def rescue_facing():
    """Public paint_witness functions whose own docstring names the rescue. -> {name: doc}"""
    out = {}
    for n in ast.parse(_src(WITNESS)).body:
        if not isinstance(n, ast.FunctionDef) or n.name.startswith("_") or n.name == "main":
            continue
        doc = ast.get_docstring(n) or ""
        if _FOR_THE_RESCUE.search(doc):
            out[n.name] = doc
    return out


def production_calls(name):
    """-> [(file, line)] every call to `name` in production code."""
    hits = []
    for f in PRODUCTION:
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        src = _src(p)
        for m in re.finditer(r"\b\w*\.%s\s*\(" % re.escape(name), src):
            hits.append((f, src[:m.start()].count("\n") + 1))
    return hits


class TestAWitnessWrittenForTheRescueIsCalledByIt(unittest.TestCase):

    def test_the_scan_found_rescue_facing_functions(self):
        """THE INSTRUMENT FIRST. An empty set would make every assertion below pass over nothing —
        which is exactly how a witness stays unjoined while a law says it is fine."""
        rf = rescue_facing()
        self.assertTrue(rf, "no rescue-facing function was found in paint_witness — the scan is "
                            "broken, and a broken scan reports a clean bill of health")
        self.assertIn("contradicts_a_blank_beat", rf,
                      "the function whose docstring calls itself 'the one his rescue needs most' "
                      "is not being recognised as rescue-facing")
        print("\n   rescue-facing: %s" % sorted(rf))

    def test_every_rescue_facing_witness_has_a_production_caller(self):
        unjoined = []
        for name in sorted(rescue_facing()):
            calls = production_calls(name)
            print("   %-28s %d production caller(s)%s"
                  % (name, len(calls), ("  " + str(calls[:2])) if calls else ""))
            if not calls:
                unjoined.append(name)
        self.assertEqual(
            unjoined, [],
            "these are written FOR the rescue and the rescue never calls them: %s\n"
            "Built, tested, gated, and joined to nothing — the defect this repo has paid for "
            "three times with this one module." % ", ".join(unjoined))

    def test_an_unreadable_witness_never_holds_a_rescue(self):
        """A broken camera must not become a permanently disabled self-heal. The witness returns
        False on UNKNOWN; this pins that the CALL SITE does not invert it."""
        import paint_witness as PW
        ok, why = PW.contradicts_a_blank_beat(-1)          # a pid that cannot be captured
        self.assertFalse(ok, "an unreadable window was reported as CONTRADICTING the beat, which "
                             "would veto every rescue whenever the camera is broken")
        self.assertTrue(str(why).strip(), "the refusal carries no reason")

    def test_the_hold_is_a_continue_not_a_reload(self):
        """A hold must SKIP the reload, not fall through into it — the whole point is that the
        window is fine and must be left alone."""
        src = _src(os.path.join(HERE, "control_app.py"))
        i = src.find("contradicts_a_blank_beat")
        self.assertGreater(i, 0, "the rescue no longer asks the pixels before reloading")
        seg = src[i:src.find("ui_pre_rescue_snapshot()", i)]
        self.assertIn("continue", seg,
                      "the pixel hold does not skip the reload — it records a disagreement and "
                      "then reloads his working window anyway")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
# Un-joining the call returns the witness to what it was for its whole life: written, tested,
# gated, and asked by nobody.
RED_PROOF = [{
    "why": "removing the call leaves contradicts_a_blank_beat with zero production callers again",
    "file": "control_app.py",
    "find": "                _refutes, _rwhy = _pw_hold.contradicts_a_blank_beat(os.getpid())",
    "replace": "                _refutes, _rwhy = False, \"the pixels were not asked\"",
    "matches": 1,
}]


if __name__ == "__main__":
    unittest.main(verbosity=2)
