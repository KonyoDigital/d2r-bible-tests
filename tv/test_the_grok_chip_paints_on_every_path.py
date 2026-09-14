# -*- coding: utf-8 -*-
"""THE GROK CHIP MUST PAINT WHEN CLAUDE IS UNMEASURED, AND A CEILING OF 0 MUST NOT LOOK UNMEASURED.

⚠⚠ THE SECOND EYE'S TWO HIGHS ON THE SHIPPED v3099 DIFF, BOTH VERIFIED IN THE FILE BEFORE A LINE
WAS CHANGED. v3099 fixed the PRODUCER — `_meter_lanes` now runs on every return of `_meter_state`,
so `/api/meter` carries `lanes.grok` even on a machine where Claude has never written its ledger.
The consumer was still shut:

    bible.html:52817   if (!known){
    bible.html:52822     return j;          <- bails here
    bible.html:52848   var gl = (j.lanes && j.lanes.grok)   <- the grok paint, never reached

So on exactly the machine v3099 exists for — Grok as primary, Grok as shadow, a fresh checkout,
CI — the payload arrived and the chip was never drawn. **The same unjoined end, one layer down.**
[[the-unjoined-end]] [[plumbing-with-no-tap]]

And the second: `"hourlyMax": _ghm or None` turned a ceiling of **0** into `None`, while the
renderer's `paint()` treats any falsey max as nothing-to-divide-by and writes the same `–` it
writes for an unmeasured lane:

    if (used === null || used === undefined || !max){ ... v.textContent = '-'; return; }

A ceiling of 0 is the circuit that refuses EVERY read — `_budget_ok` returns False outright — and
it is a MEASURED configuration, not an absent value. Off, unknown and switched-off-at-the-budget
are three different facts and two of them were sharing pixels. [[zero-needs-a-denominator]]

⚠ AND A THIRD, WHICH IS MINE AND WHICH NOBODY REPORTED: the early call works ONLY because
`paintGrok` is a hoisted `function` DECLARATION. It is called inside the `!known` branch and
defined below it. Rewrite it as `const paintGrok = () => {}` — the modern habit, and a change any
reviewer would wave through — and the early call throws a TDZ ReferenceError, killing the chip on
the very path this exists to fix, silently, inside a `try`. Pinned here so the shape cannot drift.
"""
import io
import os
import re
import sys
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import control_app as CA          # noqa: E402


def _block(src, opener):
    """The source of the {...} block that `opener` opens, by BRACE MATCHING.

    ⚠ A BRACE WALK, NOT A FIXED WINDOW. `src[i:i+N]` past the end of the region reads as ABSENT,
    which is how a guard comes to describe a guess instead of a file. [[source-window-shortcut]]
    """
    i = src.index(opener)
    j = src.index("{", i)
    depth, k = 0, j
    while k < len(src):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return src[j:k + 1], j, k
        k += 1
    raise AssertionError("unbalanced braces after %r" % opener)



def _executable_js(text):
    """JS with comments removed. -> str

    ⚠⚠ WITHOUT THIS, THE COMMENT EXPLAINING THE FIX SATISFIES THE ASSERTION ABOUT THE FIX. The
    red-proof that replaces `var circuit = (gl.capWindow === 'circuit')` with `var circuit = false`
    came back **BLIND**: the guard asked `assertIn("capWindow === 'circuit'", body)` and matched the
    `/* ... */` note directly above, which quotes the expression by name. The law was reading prose
    and calling it code. [[source-reading-guard]] [[measured-true-read-wrong]]
    """
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        else:
            out.append(text[i]); i += 1
    return "".join(out)


class TestTheGrokChipPaintsOnEveryPath(unittest.TestCase):

    def setUp(self):
        with io.open(os.path.join(REPO, "bible.html"), encoding="utf-8") as fh:
            self.src = fh.read()

    # ── 1. the chip is painted on the CLAUDE-UNMEASURED path ──────────────────────────────────
    def test_the_grok_chip_is_painted_when_claude_is_unmeasured(self):
        body, _a, end = _block(self.src, "if (!known){")
        # ⚠⚠ `paintGrok();` WITH THE SEMICOLON, AND THE EYE HAD TO TELL ME. The first cut counted
        # `paintGrok()` — and `function paintGrok(){` CONTAINS that substring, so the declaration
        # itself satisfied the count. Deleting the real later call left n_after at 1 and the
        # assertion named for exactly that failure stayed GREEN. A counter that cannot reach zero
        # is not a counter. [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]
        n_in = body.count("paintGrok();")
        after = self.src[end:]
        n_after = after.count("paintGrok();")
        print("   paintGrok() inside the !known block: %d · after it: %d" % (n_in, n_after))
        self.assertGreaterEqual(
            n_in, 1,
            "the `if (!known)` branch returns without painting the grok chip, so on a machine "
            "where CLAUDE has never read — the exact case v3099 exists for — /api/meter carries "
            "lanes.grok and the panel draws nothing")
        self.assertGreaterEqual(
            n_after, 1,
            "the grok chip is painted ONLY on the unmeasured path — the normal path lost it")

    # ── 2. and it only works because the declaration HOISTS ───────────────────────────────────
    def test_paintgrok_is_a_hoisted_declaration(self):
        decls = re.findall(r"function\s+paintGrok\s*\(", self.src)
        lex = re.findall(r"(?:const|let|var)\s+paintGrok\s*=", self.src)
        print("   `function paintGrok(` declarations: %d · lexical `paintGrok =`: %d"
              % (len(decls), len(lex)))
        self.assertEqual(
            len(decls), 1,
            "paintGrok must be exactly one hoisted FUNCTION DECLARATION — it is CALLED above the "
            "line it is DEFINED on, and only a declaration is legal there")
        self.assertEqual(
            len(lex), 0,
            "paintGrok is bound with const/let/var: the call inside the `if (!known)` branch runs "
            "BEFORE the binding is initialised and throws a TDZ ReferenceError — inside a try, so "
            "the chip just silently never appears on the one path this was written for")

    # ── 3. the circuit is drawn as a circuit, not as an absence ───────────────────────────────
    def test_a_zero_ceiling_is_not_drawn_like_an_unmeasured_one(self):
        body = _executable_js(_block(self.src, "function paintGrok()")[0])
        self.assertIn("capWindow === 'circuit'", body,
                      "the renderer does not distinguish a ceiling of 0 from an unmeasured lane, "
                      "so `paint()` writes the same '-' for both")
        # and it must actually WRITE something different, not merely test for it
        self.assertTrue(re.search(r"textContent\s*=\s*\(gl\.(hour|day)", body),
                        "the circuit branch tests for the state and paints nothing different")
        print("   circuit branch present in paintGrok, and it writes its own text")

    # ── 4. the server publishes the REAL ceiling, so 0 can reach the screen at all ────────────
    def test_a_zero_ceiling_is_published_as_zero(self):
        import g5_grok_eyes as G5
        h0, d0 = G5._HOURLY_MAX, G5._DAILY_MAX
        try:
            G5._HOURLY_MAX, G5._DAILY_MAX = 0, 200
            lane = (CA._meter_lanes({"hour": 1, "day": 1, "hourlyMax": 4000,
                                     "dailyMax": 20000, "armed": True}) or {}).get("grok") or {}
            print("   with G5._HOURLY_MAX=0 -> hourlyMax=%r atCap=%r capWindow=%r"
                  % (lane.get("hourlyMax"), lane.get("atCap"), lane.get("capWindow")))
            self.assertEqual(lane.get("hourlyMax"), 0,
                             "a ceiling of 0 is published as %r — `or None` erased the difference "
                             "between a configured zero and an unmeasured value, and the bar "
                             "cannot draw what the payload does not carry"
                             % (lane.get("hourlyMax"),))
            self.assertTrue(lane.get("atCap"))
            self.assertEqual(lane.get("capWindow"), "circuit")
        finally:
            G5._HOURLY_MAX, G5._DAILY_MAX = h0, d0


    # ── 5. THE RUNTIME, not the source text — the real function in a real engine ───────────────
    def test_the_real_function_paints_the_real_text(self):
        """⚠⚠ THE SECOND EYE'S SHARPEST POINT ON v3100, AND IT WAS RIGHT: *"a gate joined to its
        source text and unjoined from the runtime it claims to protect. All four tests in this
        file can pass on a page whose meter never executes."* They could — v3100 shipped a bare
        `} catch(e){}` that made the browser refuse the WHOLE script, and every source assertion
        here stayed green through it.

        So this one EXTRACTS `paint` and `paintGrok` from bible.html and RUNS them in node against
        a stub DOM, asserting the text a person would actually read. A SyntaxError anywhere in
        either function fails here, and so does a wrong denominator.
        [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]
        """
        import json as _json
        import shutil
        import subprocess
        import tempfile

        node = shutil.which("node")
        if not node:
            # ⚠ A SKIP IS NOT A PASS, and it says so out loud rather than going quietly green.
            self.skipTest("node is not installed — the RUNTIME half of this law is UNMEASURED")

        paint_body, _pa, _pb = _block(self.src, "function paint(barId, fillId, vId, used, max)")
        grok_body, _ga, _gb = _block(self.src, "function paintGrok()")
        harness = """
        var els = {};
        function el(id){
          /* ⚠ getBoundingClientRect IS NOT OPTIONAL — the real `paint` calls it, and paintGrok's
             own `catch(e){}` SWALLOWED the TypeError, so the day bar silently never rendered and
             the harness looked like a bad selector. That swallow is also why no source-text
             assertion can ever see a runtime fault in this function. */
          if (!els[id]) els[id] = {id:id, textContent:'', hidden:false, style:{},
                                   classList:{toggle:function(){}, add:function(){},
                                              remove:function(){}, contains:function(){return false;}},
                                   getBoundingClientRect:function(){
                                     return {width:120,height:8,top:0,left:0,right:120,bottom:8};},
                                   setAttribute:function(){}, appendChild:function(){}};
          return els[id];
        }
        var document = { getElementById: el };
        var j = JSON.parse(process.argv[2]);
        function paint(barId, fillId, vId, used, max)%s
        function paintGrok()%s
        paintGrok();
        console.log(JSON.stringify({
          hour: els['sm-v-gh'].textContent, day: els['sm-v-gd'].textContent,
          key:  els['sm-grok-k'].textContent, hidden: els['sm-grok'].hidden}));
        """ % (paint_body, grok_body)

        d = tempfile.mkdtemp(prefix="grokchip-")
        self.addCleanup(shutil.rmtree, d, True)
        script = os.path.join(d, "h.js")
        with io.open(script, "w", encoding="utf-8") as fh:
            fh.write(harness)

        def run(lane):
            out = subprocess.check_output(
                [node, script, _json.dumps({"lanes": {"grok": lane}})],
                stderr=subprocess.STDOUT, timeout=60)
            return _json.loads(out.decode("utf-8").strip().splitlines()[-1])

        base = {"label": "Grok", "on": True, "atCap": False, "capWindow": None, "capText": "",
                "hour": 70, "day": 1035, "hourlyMax": 4000, "dailyMax": 20000, "why": ""}

        got = run(dict(base))
        print("   running lane          -> %r / %r  key=%r" % (got["hour"], got["day"], got["key"]))
        # ⚠ THE REAL `paint` COMPACTS THE CEILING — "4k"/"20k", by v2027, so the cap fits the
        # column beside the bar. Asserted against what it actually renders, not what I assumed.
        self.assertEqual(got["hour"], "70/4k")
        self.assertEqual(got["day"], "1035/20k")
        self.assertEqual(got["key"], "grok")

        # ⚠ THE CELL THE EYE FOUND: only the DAY is a circuit. The hour must keep its own
        # denominator — the first cut overwrote both bars and printed `70/0` for a 4000 ceiling.
        day0 = run(dict(base, dailyMax=0, atCap=True, capWindow="circuit"))
        print("   daily ceiling 0       -> %r / %r  key=%r"
              % (day0["hour"], day0["day"], day0["key"]))
        self.assertEqual(day0["day"], "1035/0",
                         "the window that IS the circuit must say so")
        self.assertEqual(day0["key"], "grok \u00b7 CEILING 0",
                         "the key must NAME the circuit — it read %r" % day0["key"])
        self.assertEqual(day0["hour"], "70/4k",
                         "the HOUR has a 4000 ceiling and is not the circuit — it read %r"
                         % day0["hour"])

        hr0 = run(dict(base, hourlyMax=0, atCap=True, capWindow="circuit"))
        print("   hourly ceiling 0      -> %r / %r" % (hr0["hour"], hr0["day"]))
        self.assertEqual(hr0["key"], "grok \u00b7 CEILING 0",
                         "the key must NAME the circuit — it read %r" % hr0["key"])
        self.assertEqual(hr0["hour"], "70/0")
        self.assertEqual(hr0["day"], "1035/20k",
                         "the DAY has a 20000 ceiling and is not the circuit — it read %r"
                         % hr0["day"])

        # and a lane that could not be read stays UNKNOWN on screen, not zero
        unk = run(dict(base, hour=None, day=None, hourlyMax=None, dailyMax=None,
                       on=None, atCap=None))
        print("   unreadable lane       -> %r / %r" % (unk["hour"], unk["day"]))
        self.assertEqual(unk["hour"], "\u2013")
        self.assertEqual(unk["day"], "\u2013")

    # ── 6. and the chip is hidden when there is no grok lane at all ────────────────────────────
    def test_no_grok_lane_hides_the_chip(self):
        import json as _json
        import shutil
        import subprocess
        import tempfile
        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed — the RUNTIME half of this law is UNMEASURED")
        paint_body, _a, _b = _block(self.src, "function paint(barId, fillId, vId, used, max)")
        grok_body, _c, _d = _block(self.src, "function paintGrok()")
        harness = """
        var els = {};
        function el(id){
          /* ⚠ getBoundingClientRect IS NOT OPTIONAL — the real `paint` calls it, and paintGrok's
             own `catch(e){}` SWALLOWED the TypeError, so the day bar silently never rendered and
             the harness looked like a bad selector. That swallow is also why no source-text
             assertion can ever see a runtime fault in this function. */
          if (!els[id]) els[id] = {id:id, textContent:'', hidden:false, style:{},
                                   classList:{toggle:function(){}, add:function(){},
                                              remove:function(){}, contains:function(){return false;}},
                                   getBoundingClientRect:function(){
                                     return {width:120,height:8,top:0,left:0,right:120,bottom:8};},
                                   setAttribute:function(){}, appendChild:function(){}};
          return els[id];
        }
        var document = { getElementById: el };
        var j = JSON.parse(process.argv[2]);
        function paint(barId, fillId, vId, used, max)%s
        function paintGrok()%s
        paintGrok();
        console.log(JSON.stringify({hidden: els['sm-grok'].hidden}));
        """ % (paint_body, grok_body)
        d = tempfile.mkdtemp(prefix="grokchip2-")
        self.addCleanup(shutil.rmtree, d, True)
        s = os.path.join(d, "h.js")
        with io.open(s, "w", encoding="utf-8") as fh:
            fh.write(harness)
        out = subprocess.check_output([node, s, _json.dumps({"lanes": {}})],
                                      stderr=subprocess.STDOUT, timeout=60)
        got = _json.loads(out.decode("utf-8").strip().splitlines()[-1])
        print("   no grok lane -> chip hidden: %r" % got["hidden"])
        self.assertTrue(got["hidden"], "with no grok lane the chip must be hidden, not blank")


    # ── 7. THE JOIN: the REAL producer's payload into the REAL renderer ───────────────────────
    def test_the_real_payload_reaches_the_real_renderer(self):
        """⚠⚠ THE SECOND EYE'S FINDING ON v3102, AND IT NAMED THE GAP EXACTLY: *"the two new
        runtime tests are each joined to their own half and unjoined from each other."* They were.
        `test_a_zero_ceiling_is_published_as_zero` asked `_meter_lanes` for a circuit and never
        checked that the OTHER window's ceiling survived; the node test built its lane BY HAND. So
        a producer that smeared the circuit across both maxes would pass the publisher test, pass
        the renderer test on its synthetic payload, and paint the healthy window as `/0` on his
        screen — the v3102 bug, at the other end of the wire. [[the-unjoined-end]]

        This one takes what `_meter_lanes` ACTUALLY returns and feeds it to the extracted renderer.
        """
        import json as _json
        import shutil
        import subprocess
        import tempfile
        import g5_grok_eyes as G5

        node = shutil.which("node")
        if not node:
            self.skipTest("node is not installed — the RUNTIME half of this law is UNMEASURED")

        h0, d0, c0 = G5._HOURLY_MAX, G5._DAILY_MAX, G5._budget_counts
        try:
            # a DAILY circuit with a healthy hourly ceiling — the exact cell that was mispainted
            G5._HOURLY_MAX, G5._DAILY_MAX = 4000, 0
            G5._budget_counts = lambda: (70, 1035)
            lane = (CA._meter_lanes({"hour": 1, "day": 1, "hourlyMax": 4000,
                                     "dailyMax": 20000, "armed": True}) or {}).get("grok") or {}
        finally:
            G5._HOURLY_MAX, G5._DAILY_MAX, G5._budget_counts = h0, d0, c0

        print("   producer said: hourlyMax=%r dailyMax=%r capWindow=%r"
              % (lane.get("hourlyMax"), lane.get("dailyMax"), lane.get("capWindow")))
        self.assertEqual(lane.get("hourlyMax"), 4000,
                         "the producer smeared the circuit onto the HEALTHY window — hourlyMax "
                         "came back %r with _HOURLY_MAX=4000" % (lane.get("hourlyMax"),))
        self.assertEqual(lane.get("dailyMax"), 0)

        paint_body, _a, _b = _block(self.src, "function paint(barId, fillId, vId, used, max)")
        grok_body, _c, _d = _block(self.src, "function paintGrok()")
        harness = """
        var els = {};
        function el(id){
          if (!els[id]) els[id] = {id:id, textContent:'', hidden:false, style:{},
                                   classList:{toggle:function(){}, add:function(){},
                                              remove:function(){}, contains:function(){return false;}},
                                   getBoundingClientRect:function(){
                                     return {width:120,height:8,top:0,left:0,right:120,bottom:8};},
                                   setAttribute:function(){}, appendChild:function(){}};
          return els[id];
        }
        var document = { getElementById: el };
        var j = JSON.parse(process.argv[2]);
        function paint(barId, fillId, vId, used, max)%s
        function paintGrok()%s
        paintGrok();
        console.log(JSON.stringify({hour: els['sm-v-gh'].textContent,
                                    day: els['sm-v-gd'].textContent,
                                    key: els['sm-grok-k'].textContent}));
        """ % (paint_body, grok_body)
        d = tempfile.mkdtemp(prefix="grokjoin-")
        self.addCleanup(shutil.rmtree, d, True)
        s = os.path.join(d, "h.js")
        with io.open(s, "w", encoding="utf-8") as fh:
            fh.write(harness)
        out = subprocess.check_output([node, s, _json.dumps({"lanes": {"grok": lane}})],
                                      stderr=subprocess.STDOUT, timeout=60)
        got = _json.loads(out.decode("utf-8").strip().splitlines()[-1])
        print("   renderer drew: %r / %r  key=%r" % (got["hour"], got["day"], got["key"]))
        self.assertEqual(got["day"], "1035/0", "the DAY is the circuit and must say so")
        self.assertEqual(got["hour"], "70/4k",
                         "the HOUR has a 4000 ceiling and is NOT the circuit — it drew %r"
                         % got["hour"])

RED_PROOF = [
    {
        "why": "the grok chip stops being painted when Claude is unmeasured — the producer fix in "
               "v3099 reaches /api/meter and the panel still draws nothing, on exactly the "
               "machines where grok is the lane doing the reading",
        "file": "../bible.html",
        "find": "      paintGrok();          /* ⚠ v3100 — CLAUDE unmeasured says NOTHING about the GROK lane */\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the NORMAL path loses its paint — the chip draws only when Claude is unmeasured, "
               "which is the inverse of the bug and just as wrong. This is the proof the first "
               "cut could not go red on, because `function paintGrok(){` contains the substring "
               "it was counting",
        "file": "../bible.html",
        "find": "    paintGrok();\n    return j;",
        "replace": "    return j;",
        "matches": 1,
    },
    {
        "why": "paintGrok becomes a lexical binding, so the call inside the `if (!known)` branch "
               "hits the temporal dead zone and throws — inside a try, so the chip silently never "
               "appears on the path this exists to fix",
        "file": "../bible.html",
        "find": "    function paintGrok(){",
        "replace": "    const paintGrok = function(){",
        "matches": 1,
    },
    {
        "why": "a ceiling of 0 goes back to being published as None, so the circuit that refuses "
               "every read is drawn with the same '-' as a lane nobody has measured",
        "file": "control_app.py",
        "find": '            "hour": _gh, "day": _gd, "hourlyMax": _ghm, "dailyMax": _gdm,',
        "replace": '            "hour": _gh, "day": _gd, "hourlyMax": _ghm or None, "dailyMax": _gdm or None,',
        "matches": 1,
    },
    {
        "why": "the circuit overwrite goes back to being per-LANE instead of per-WINDOW, so with a "
               "4000 hourly ceiling and a 0 daily one the HOUR bar prints `70/0` — a denominator "
               "that is not the hour's, on the window that is not the circuit",
        "file": "../bible.html",
        "find": "        if (gl.hourlyMax === 0){",
        "replace": "        if (circuit){",
        "matches": 1,
    },
    {
        "why": "the renderer stops naming the circuit, so a 0 ceiling is drawn exactly like an "
               "unmeasured lane again",
        "file": "../bible.html",
        "find": "        var circuit = (gl.capWindow === 'circuit');",
        "replace": "        var circuit = false;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
