"""A SURFACE BUILT FOR THIS HARNESS THAT THIS HARNESS NEVER READ.

⚠⚠ MEASURED 2026-09-11 (#53). `control_ui.html` writes the fan solver's entire record onto the
heart overlay as `data-fanfit`, and says who it is for in as many words:

    "`window._hrtFanLast` is for a CDP probe; the `data-fanfit` attribute is for the render
     harness, which photographs the DOM and cannot reach a JS global."

`render_check.py` contained **ZERO** occurrences of `fanfit`. The attribute was written for a reader
that did not exist. So #53's central question — did the solver find no improving move, or find one
and put it back? — stayed one manual probe away on every render this gate has ever done, while the
answer sat in the DOM being photographed.

Once the tap existed, one run answered it:

    ⓘ report {"reverted": false, "ok": true, "passes": 2, "moves": 4, "before": 1, "after": 0,
              "from": {"collisions": 2, "adjacent": 2, "displacement": 0},
              "to":   {"collisions": 0, "adjacent": 0, "displacement": 65.6}}

`reverted: false` — the all-or-nothing revert did not fire. ⚠ That is the FIXTURE world; his console
carries different labels at different widths, so his own answer stays UNKNOWN until a render of his
console prints one. What changed is that it now would. [[plumbing-with-no-tap]] [[the-unjoined-end]]

⚠ A REPORT IS A DIAGNOSTIC AND MAY NEVER DECIDE. One that could fail a run would be a second gate
wearing a diagnostic's clothes, and the next person to add a `report` would be adding a gate without
knowing it. [[regression-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RC = os.path.join(HERE, "render_check.py")

if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _src():
    return io.open(RC, encoding="utf-8").read()


def _fn(name):
    """The AST node for a top-level function. PARSED, never grepped — this file is mostly
    comments by volume, and a text search cannot tell code from prose about code.
    [[source-reading-guard]]"""
    for n in ast.walk(ast.parse(_src())):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    raise AssertionError("%s() is gone from render_check.py — this gate did not reach its "
                         "subject, so its silence is not evidence" % name)


def _targets():
    for n in ast.walk(ast.parse(_src())):
        if isinstance(n, ast.Assign) and any(getattr(x, "id", "") == "TARGETS" for x in n.targets):
            return n.value
    raise AssertionError("TARGETS is gone from render_check.py")


class ATargetCanHandBackItsOwnVerdict(unittest.TestCase):

    def test_the_fan_target_DECLARES_a_report_that_reads_the_attribute(self):
        """THE HEADLINE. The attribute existed for this harness and this harness did not read it."""
        node = _targets()
        fan = None
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "heart-fan":
                fan = v
        self.assertIsNotNone(fan, "the heart-fan target is gone — re-derive this law")
        keys = [kk.value for kk in fan.keys if isinstance(kk, ast.Constant)]
        self.assertIn("report", keys,
                      "heart-fan declares no `report`, so data-fanfit goes on being written for a "
                      "reader that does not exist: %s" % keys)
        self.assertIn("fanfit", _src(),
                      "render_check no longer mentions fanfit at all — the tap is gone")

    def test_check_READS_a_declared_report(self):
        """A spec key nothing consults is a spec key that does not exist."""
        body = ast.get_source_segment(_src(), _fn("check"))
        self.assertIn('spec.get("report")', body,
                      "check() never asks whether the target declared a report")
        self.assertIn('out["report"]', body,
                      "check() never records the report it just evaluated")

    def test_the_report_is_PRINTED_and_not_merely_COLLECTED(self):
        """⚠ Recording a verdict into a dict nobody prints is one grave instead of another — the
        REG-920 shape, where the heart carried a number no surface showed."""
        src = _src()
        self.assertIn('ⓘ report', src,
                      "nothing prints the report, so it is collected and unread — exactly the "
                      "defect this tap exists to end")

    def test_a_report_NEVER_decides_ok_or_not_ok(self):
        """⚠ THE LOAD-BEARING RESTRAINT. A diagnostic that can fail a run is a second gate in
        disguise. Parsed: no assignment to out["ok"] may appear inside the report block."""
        body = ast.get_source_segment(_src(), _fn("check"))
        i = body.index('if spec.get("report"):')
        # the block ends at the next line with the same indentation that is not part of it
        tail = body[i:]
        end = tail.index("\n        for w, h in WIDTHS:")
        block = tail[:end]
        self.assertNotIn('out["ok"]', block,
                         "the report block assigns out[\"ok\"] — a diagnostic that can fail a run "
                         "is a second gate wearing a diagnostic's clothes:\n%s" % block[:400])
        self.assertNotIn('refusals', block,
                         "the report block appends a refusal, which fails the run: %s" % block[:400])

    def test_a_report_that_RAISES_is_recorded_and_never_swallowed(self):
        """A throw and a decline must not look alike — the same distinction v2827 had to add to
        `_hrtFanFit`'s own caller. [[unknown-stays-unknown]]"""
        body = ast.get_source_segment(_src(), _fn("check"))
        i = body.index('if spec.get("report"):')
        block = body[i:i + 900]
        self.assertIn("except Exception", block, "the report evaluation has no error path")
        self.assertIn('"error"', block,
                      "a raising report is swallowed rather than recorded: %s" % block[:400])

    def test_a_NULL_report_is_UNREAD_and_not_silence(self):
        """⚠ An expression that answered nothing is not a target that declared nothing. Collapsing
        those two is how a missing surface reads as a clean one. [[unknown-stays-unknown]]"""
        body = ast.get_source_segment(_src(), _fn("check"))
        self.assertIn("unread", body,
                      "a report returning null is stored as null, which is indistinguishable from "
                      "a target that never declared one")


RED_PROOF = [
    {
        "why": "removing the read puts render_check back to ZERO occurrences of the attribute the UI writes for it \u2014 the measured state of #53, where the answer sat in the DOM and nothing collected it.",
        "file": "render_check.py",
        "find": "        if spec.get(\"report\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "collecting without printing is the REG-920 shape: the value is recorded and no surface shows it, so the fact moves from one grave to another.",
        "file": "render_check.py",
        "find": "            _say(\"     \u24d8 report %s\" % json.dumps(r[\"report\"], sort_keys=True)[:400])",
        "replace": "            pass",
        "matches": 1,
    },
    {
        "why": "letting a null report be stored as null makes 'the expression answered nothing' identical to 'this target declared no report'. The anchor spans the WHOLE two-line expression: an earlier cut took only the first line and orphaned its continuation, so heart2 refused it as a SyntaxError rather than a law.",
        "file": "render_check.py",
        "find": "            out[\"report\"] = _rep if _rep is not None else {\"unread\": \"the report expression \"\n                                                           \"returned null\"}",
        "replace": "            out[\"report\"] = _rep",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
