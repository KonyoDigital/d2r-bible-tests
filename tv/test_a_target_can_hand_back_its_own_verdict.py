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
# ⚠ v2925 — the MODULE, not the path. `RC` above is a filename used by _src(); two of the laws
# below must EXERCISE the code rather than read it, and that needs the real import.
import render_check as RCM  # noqa: E402
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
        those two is how a missing surface reads as a clean one. [[unknown-stays-unknown]]

        ⚠⚠ v2925 — THIS LAW WAS BLIND AND THE DRILL CAUGHT IT. It was `assertIn("unread", body)`
        over check()'s whole source. v2925 added a guard `"unread" in _rep` and a COMMENT saying
        "an error/unread/unparsed shape is NOT a reading" — so the word survived in two places the
        tamper does not touch, and deleting the REAL assignment left the law green. A law that
        reads prose goes green the moment prose mentions the thing.
        [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]"""
        fn = _fn("check")
        nulls = [n for n in ast.walk(fn)
                 if isinstance(n, ast.If)
                 and isinstance(n.test, ast.Compare)
                 and isinstance(n.test.ops[0], ast.Is)
                 and isinstance(n.test.comparators[0], ast.Constant)
                 and n.test.comparators[0].value is None]
        self.assertEqual(1, len(nulls),
                         "the null branch is gone — a report that answered nothing now falls "
                         "through as if the target had declared nothing (found %d)" % len(nulls))
        keys = set()
        for asn in ast.walk(nulls[0]):
            if isinstance(asn, ast.Assign) and isinstance(asn.value, ast.Dict):
                keys |= {k.value for k in asn.value.keys if isinstance(k, ast.Constant)}
        self.assertIn("unread", keys,
                      "the null branch assigns %r — a report returning null is stored as a shape "
                      "indistinguishable from a target that never declared one" % (sorted(keys),))

    # ── v2925, from the cross-family eye on v2924 ───────────────────────────────────────────────
    def test_the_printed_line_never_drops_a_field_in_SILENCE(self):
        """⚠⚠ THE MEASURED DEFECT. v2924 printed the payload through a bare `[:340]`. MEASURED on
        the gate's own .render_verdict.json: heart-fan serialises to 423 chars, so 83 were cut —
        and the 83 were exactly `"to": {...}`, the collisions AFTER the solve. The line kept the
        BEFORE half of the pair, dropped the AFTER half, and looked complete either way.

        This law EXERCISES the rule rather than reading it: a payload of the real shape must keep
        every top-level key, and a payload past the cap must SAY how much it dropped.
        [[zero-needs-a-denominator]] [[regression-guard]]"""
        real = {"from": {"collisions": 2}, "to": {"adjacent": 0, "collisions": 0,
                "displacement": 65.6}, "reverted": False, "readAt": "375x800",
                "solvedAt": "UNKNOWN — " + "x" * 160, "why": "", "moves": 4, "passes": 2}
        line = RCM._report_line(real)
        for k in real:
            self.assertIn('"%s"' % k, line,
                          "the printed line drops %r — a truncation that does not announce "
                          "itself is indistinguishable from a short payload" % k)
        over = RCM._report_line({"k": "v" * (RCM._REPORT_LINE_CAP + 500)})
        self.assertIn("NOT SHOWN", over, "past the cap the line cuts without saying it cut")
        self.assertRegex(over, r"\+\d+ more char\(s\)",
                         "the cut does not state HOW MANY characters went missing")

    def test_a_width_that_REFUSED_still_hands_back_its_reading(self):
        """⚠⚠ v2924 put the tap AFTER `if why_w: … continue`, so the widths that struggle — the
        narrow ones, where REG-928 says the collisions are worst — were the exact widths that
        produced no reading. The attribute lives on `#heart-ov` and does not depend on the
        target's selector, so a refusal is not a reason to skip it.

        STRUCTURAL, not prose: walk to the `If` that appends a refusal and ends in `continue`,
        and require a call to the tap inside THAT body. [[the-unjoined-end]]"""
        fn = _fn("check")
        guilty = []
        for node in ast.walk(fn):
            if not isinstance(node, ast.If):
                continue
            body = node.body
            if not any(isinstance(x, ast.Continue) for x in body):
                continue
            dumped = ast.dump(node)
            if "refusals" not in dumped:
                continue
            calls = [c for c in ast.walk(node)
                     if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "_take_report"]
            if not calls:
                guilty.append(node.lineno)
        self.assertEqual([], guilty,
                         "a width refuses and `continue`s at line(s) %s without taking its "
                         "report — the reading does not need the selector that failed" % guilty)

    def test_the_CAVEAT_belongs_to_the_target_and_not_to_the_tap(self):
        """⚠ v2924 hardcoded the fan's `solvedAt` essay inside a tap its own comments call GENERAL.
        Every `{"error": …}` and `{"unread": …}` shape, and any second target's reading, was
        stamped with a sentence about a fan solve. Dormant only because heart-fan is the single
        declarer today. The tap may stamp ONLY what the spec declared, and only onto a reading."""
        fn = _fn("check")
        loops = [n for n in ast.walk(fn)
                 if isinstance(n, ast.For) and "reportNote" in ast.dump(n)]
        self.assertEqual(1, len(loops),
                         "the tap does not stamp the SPEC's own note (found %d such loops)"
                         % len(loops))
        guards = [n for n in ast.walk(fn)
                  if isinstance(n, ast.If) and loops[0] in n.body]
        self.assertTrue(guards, "the spec's note is stamped onto EVERY shape, errors included")
        g = ast.dump(guards[0])
        for shape in ("error", "unread", "unparsed"):
            self.assertIn(shape, g,
                          "%r is annotated as though it were a reading — it is a failure to "
                          "read, and the two must not look alike" % shape)
        # and the tap must not have re-grown a hardcoded essay of its own
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
               and isinstance(node.value.value, str) and len(node.value.value) > 60:
                tgt = ast.dump(node.targets[0])
                self.assertNotIn("_rep", tgt,
                                 "the tap assigns a %d-char literal into the reading again — "
                                 "that is the v2924 defect regrown"
                                 % len(node.value.value))
        self.assertIn("reportNote", RCM.TARGETS["heart-fan"],
                      "heart-fan no longer declares the caveat that explains its own readAt")


RED_PROOF = [
    {
        "why": "removing the read puts render_check back to ZERO occurrences of the attribute the UI writes for it \u2014 the measured state of #53, where the answer sat in the DOM and nothing collected it.",
        "file": "render_check.py",
        "find": "        if spec.get(\"report\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "collecting without printing is the REG-920 shape. v2925 moved the truncation out of this loop into _report_line(), so the v2924 anchor matched ZERO and would have proved INVALID rather than red \u2014 caught by re-counting every anchor after the edit, which is the only reason it is not a silent hole.",
        "file": "render_check.py",
        "find": "                _say(\"     \u24d8 report %-9s %s\" % (_wk, _s))\n",
        "replace": "                pass\n",
        "matches": 1,
    },
    {
        "why": "a null reading collapsed into silence is [[unknown-stays-unknown]]: a target that answered nothing looks exactly like a target that declared nothing.",
        "file": "render_check.py",
        "find": "                    _rep = {\"unread\": \"the report expression returned null\"}\n",
        "replace": "                    _rep = {}\n",
        "matches": 1,
    },
    {
        "why": "one reading for the whole run is the v2923 defect: an answer taken at Chrome's launch size, which is not one of the five widths this harness photographs.",
        "file": "render_check.py",
        "find": "                out.setdefault(\"report\", {})[\"%dx%d\" % (w, h)] = _rep",
        "replace": "                out.setdefault(\"report\", {})[\"all\"] = _rep",
        "matches": 1,
    },
    {
        "why": "v2925/A \u2014 RESTORES THE MEASURED DEFECT EXACTLY. The bare [:340] is what the cross-family eye caught on v2924: the heart-fan payload is 423 chars, so 83 were dropped, and the 83 were `\"to\": {...}` \u2014 the collisions AFTER the solve. The law must go red because the AFTER half of the pair vanishes from the printed line and nothing says it did.",
        "file": "render_check.py",
        "find": "    _s = json.dumps(payload, sort_keys=True)\n    if len(_s) <= _REPORT_LINE_CAP:\n        return _s\n",
        "replace": "    _s = json.dumps(payload, sort_keys=True)[:340]\n    if True:\n        return _s\n",
        "matches": 1,
    },
    {
        "why": "v2925/B \u2014 puts the tap back behind the refusal, so a width whose selector failed to settle hands back NO reading. The widths that struggle are the narrow ones, and 375x800 is where REG-928 says the collisions are worst: the one width the instrument exists for is the one that drops out.",
        "file": "render_check.py",
        "find": "                _take_report(w, h)      # \u26a0 v2925 \u2014 the fan's attribute does not need the selector\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v2925/C \u2014 re-grows the hardcoded essay inside a tap its own comments call GENERAL, stamping a sentence about a fan solve onto every {error}/{unread} shape and onto any second target's reading.",
        "file": "render_check.py",
        "find": '                        if not ("error" in _rep or "unread" in _rep or "unparsed" in _rep):\n                            for _nk, _nv in (spec.get("reportNote") or {}).items():\n                                _rep[_nk] = _nv\n',
        "replace": '                        _rep["solvedAt"] = "UNKNOWN — the fan solves once on open and never re-solves on resize, so this reading is from whatever width the heart was opened at"\n',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
