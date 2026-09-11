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
        # ⚠⚠ v2924 — THIS USED TO BE `assertIn("fanfit", _src())`, AND THE EYE CAUGHT IT.
        # After v2923 the file's OWN COMMENTS contain "fanfit", so that check matched my prose
        # about the code rather than the code. Someone could keep
        #     "report": "(function(){ return {ok:true}; })()"
        # and delete `getAttribute('data-fanfit')` entirely: the key is still present, the comments
        # still say fanfit, the law stays green, and the attribute is once again written for a
        # reader that does not read it — the exact defect this file's docstring names.
        # The law is now about the EXPRESSION, read out of TARGETS, not about the file's text.
        # [[source-reading-guard]] [[measured-true-read-wrong]]
        rep = None
        for kk, vv in zip(fan.keys, fan.values):
            if isinstance(kk, ast.Constant) and kk.value == "report":
                rep = ast.literal_eval(vv)
        self.assertIsInstance(rep, str, "heart-fan's report is not a string expression: %r" % (rep,))
        self.assertIn("data-fanfit", rep,
                      "heart-fan declares a report that never reads data-fanfit, so the attribute "
                      "is written for a reader that does not read it: %r" % rep[:160])
        self.assertIn("getAttribute", rep,
                      "the report does not actually READ the attribute off the element: %r"
                      % rep[:160])

    def test_check_READS_a_declared_report(self):
        """A spec key nothing consults is a spec key that does not exist."""
        body = ast.get_source_segment(_src(), _fn("check"))
        self.assertIn('spec.get("report")', body,
                      "check() never asks whether the target declared a report")
        self.assertIn('setdefault("report"', body,
                      "check() never records the report it just evaluated")
        # ⚠ v2924 — AND IT MUST BE KEYED BY WIDTH. A single `out["report"]` was the v2923 shape,
        # measured once at Chrome's launch size and therefore about no photographed viewport.
        self.assertIn('out.setdefault("report", {})["%dx%d" % (w, h)]', body,
                      "the report is not keyed by width, so it cannot say which viewport it "
                      "describes — the defect the eye caught in v2923")

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
        # ⚠⚠ v2924 — PARSED, NOT SEARCHED FOR THE NEXT LINE. My first cut found the block by
        # `tail.index("\n        for w, h in WIDTHS:")` — i.e. by assuming what followed it. When
        # v2924 moved the report INSIDE that loop the search raised ValueError and the law errored
        # rather than judging: a law that breaks when its subject MOVES was reading position, not
        # structure. The AST knows where an `if` body starts and ends. [[source-reading-guard]]
        node = _fn("check")
        block_node = None
        for sub in ast.walk(node):
            if isinstance(sub, ast.If):
                t = ast.dump(sub.test)
                if "report" in t and "spec" in t:
                    block_node = sub
        self.assertIsNotNone(block_node,
                             "no `if spec.get(\"report\")` block in check() — this law did not "
                             "reach its subject, so its silence is not evidence")
        block = "\n".join(ast.dump(st) for st in block_node.body)
        self.assertNotIn("'ok'", block,
                         "the report block assigns out[\"ok\"] — a diagnostic that can fail a run "
                         "is a second gate wearing a diagnostic's clothes:\n%s" % block[:400])
        self.assertNotIn("refusals", block,
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
        "why": "collecting without printing is the REG-920 shape. The anchor spans the WHOLE loop: an earlier cut took only the _say() lines and left the enclosing `for` with an empty body, so the tamper was a SyntaxError rather than a law.",
        "file": "render_check.py",
        "find": "            for _wk in sorted(r[\"report\"]):\n                _say(\"     \u24d8 report %-9s %s\"\n                     % (_wk, json.dumps(r[\"report\"][_wk], sort_keys=True)[:340]))\n",
        "replace": "            pass\n",
        "matches": 1,
    },
    {
        "why": "letting a null report be stored as null makes 'the expression answered nothing' identical to 'this target declared no report'.",
        "file": "render_check.py",
        "find": "                    _rep = {\"unread\": \"the report expression returned null\"}",
        "replace": "                    _rep = None",
        "matches": 1,
    },
    {
        "why": "collapsing the per-width readings back into ONE key is the v2923 defect the eye caught: a single reading, taken at a viewport this harness never photographs, presented as the answer for all five.",
        "file": "render_check.py",
        "find": "                out.setdefault(\"report\", {})[\"%dx%d\" % (w, h)] = _rep",
        "replace": "                out[\"report\"] = _rep",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
