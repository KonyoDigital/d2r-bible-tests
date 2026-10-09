# -*- coding: utf-8 -*-
"""REG-1752 (#160) - A RENDER FIXTURE WAITS FOR THE PAGE'S OWN FIRST ANSWER BEFORE IT IS ADOPTED.

The `pop-asks` render target adopts a fixture question into the board's needs-you state and then measures the 📥 pop.
The board asks /api/status once at load (and every 120s), and that answer REPLACES the needs-you state wholesale. On
two pushes of 10-03 the load-time answer landed AFTER the adopt, inside the 4s warmup, and repainted the pop without
the fixture card - '#inbox-pop .ibx-ny-ask matched NOTHING' at 375 (then at 375 and 901) - while the SAME tree
rendered 1/1 at every width run alone. Each refusal cost a push (~3-5 min) and taught a re-run.

The activate now refuses until #ibx-needsyou (static markup) has left its pre-answer text, 'waiting-on-you: UNKNOWN'.
This law runs the target's REAL activate expression in node against a minimal page and holds:
  * before the page's own answer (pre-answer text, or nothing painted yet) the fixture is NOT adopted;
  * after any answer - clear, unreachable, unmeasured, rows - it is adopted and the card measures;
  * the refusal names its reason (activateWhy).
RED_PROOF below. [[regression-guard]] [[the-unjoined-end]] [[stale-reading]]
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

NODE = shutil.which("node")

# a page with just enough DOM for the activate: the needs-you host, the pop, a card that exists once adopted
HARNESS = r"""
const vm = require('vm');
let adopted = 0;
const btn = { getBoundingClientRect: () => ({ width: 40, height: 12, right: 40, top: 0 }), contains: () => true };
const card = { getBoundingClientRect: () => ({ width: 200, height: 40, right: 200, top: 0 }),
               querySelectorAll: () => [btn, btn, btn] };
const pop = { classList: { contains: () => true }, textContent: '',
              querySelector: (s) => (adopted && s === '.ibx-ny-ask') ? card : null };
const host = { textContent: inp.ny };
const document = { getElementById: (id) => id === 'ibx-needsyou' ? host : (id === 'inbox-pop' ? pop : null),
                   elementFromPoint: () => btn };
const window = { _eagleNYAdopt: () => { adopted++; }, inboxPopTog: () => {} };
const ctx = { window, document, Math, String };
const res = vm.runInNewContext(inp.src, ctx);
const why = inp.why ? vm.runInNewContext(inp.why, ctx) : '';
process.stdout.write(JSON.stringify({ res: !!res, adopted, why: String(why || '') }));
"""

PRE = u"\U0001F985 waiting-on-you: UNKNOWN"
AFTER = {
    "clear": u"\U0001F985 waiting-on-you: none — the watchdog has nothing for you",
    "unreachable": u"\U0001F985 waiting-on-you: UNKNOWN — the console did not answer (fetch failed). "
                   u"Not zero: nobody could look.",
    "unmeasured": u"\U0001F985 waiting-on-you: the watchdog has not looked yet this boot — UNKNOWN, not zero",
    "rows": u"\U0001F985 WAITING ON YOU — 1 shadow gate",
}


@unittest.skipUnless(NODE, "node is not on PATH here - the activate cannot be executed, so this is UNKNOWN, not clean")
class TheFixtureWaitsForThePage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import render_check
        cls.spec = render_check.TARGETS["pop-asks"]

    def run_activate(self, ny_text, with_why=False):
        payload = {"src": self.spec["activate"], "ny": ny_text,
                   "why": self.spec.get("activateWhy") if with_why else ""}
        # the PROGRAM travels on stdin (test_no_law_hands_node_its_program_on_argv - Linux caps one argv string at
        # 128 KB), with the payload inlined as a JSON literal at its head
        program = "const inp = %s;\n%s" % (json.dumps(payload), HARNESS)
        r = subprocess.run([NODE, "-"], input=program, capture_output=True,
                           text=True, encoding="utf-8", timeout=60)
        self.assertEqual(r.returncode, 0, "the harness itself failed: %s" % r.stderr[-400:])
        return json.loads(r.stdout)

    def test_baseline_an_answered_page_adopts_and_measures(self):
        # PREMISE: the harness can reach a TRUE activate at all - otherwise every refusal below is vacuous
        out = self.run_activate(AFTER["clear"])
        self.assertEqual((out["res"], out["adopted"]), (True, 1))

    def test_before_the_page_answers_the_fixture_is_not_adopted(self):
        out = self.run_activate(PRE)
        self.assertEqual((out["res"], out["adopted"]), (False, 0),
                         "the fixture was adopted before the page's own /api/status answer - that answer "
                         "will land after it and erase the card the target measures")

    def test_before_anything_is_painted_the_fixture_is_not_adopted(self):
        out = self.run_activate("")
        self.assertEqual((out["res"], out["adopted"]), (False, 0))

    def test_every_answer_kind_lets_it_adopt(self):
        for kind, text in sorted(AFTER.items()):
            out = self.run_activate(text)
            self.assertEqual((out["res"], out["adopted"]), (True, 1), kind)

    def test_the_refusal_names_its_reason(self):
        out = self.run_activate(PRE, with_why=True)
        self.assertIn("first /api/status answer", out["why"])



# REG-2140 (the v3635 second eye) - theatre-head's activateWhy dereferenced the header and caption that its activate guards, so
# a missing node made the refusal a script error instead of a reason. Runs the REAL activateWhy in node over a theatre that is
# open with a reel loaded and is missing each node in turn: it must RETURN a reason that names the missing part.
THEATRE_WHY = r"""
const vm = require('vm');
const cap = inp.cap === null ? null : { textContent: inp.cap };
const tl = inp.tl ? { getBoundingClientRect: () => ({ bottom: 80 }) } : null;
const document = { querySelector: (s) => s === '#theatre .th-topline' ? tl : null,
                   getElementById: (id) => id === 'th-caption' ? cap : null,
                   createRange: () => ({ selectNodeContents: (n) => { if (!n) throw new TypeError('no node'); },
                                         getBoundingClientRect: () => ({ top: 120 }) }) };
const TH = { open: true, beats: [1] };
const ctx = { window: { TH }, document, Math, String, TH };
let why = '', threw = '';
try { why = vm.runInNewContext(inp.why, ctx); } catch (e) { threw = String(e); }
process.stdout.write(JSON.stringify({ why: String(why || ''), threw }));
"""


@unittest.skipUnless(NODE, "node is not on PATH here - the refusal cannot be executed, so this is UNKNOWN, not clean")
class TheTheatreRefusalNamesWhatIsMissing(unittest.TestCase):

    def why(self, tl, cap):
        import render_check
        payload = {"why": render_check.TARGETS["theatre-head"]["activateWhy"], "tl": tl, "cap": cap}
        r = subprocess.run([NODE, "-"], input="const inp = %s;\n%s" % (json.dumps(payload), THEATRE_WHY),
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(r.returncode, 0, "the harness itself failed: %s" % r.stderr[-400:])
        return json.loads(r.stdout)

    def test_baseline_a_whole_theatre_names_the_overlap(self):
        out = self.why(True, "a caption")
        self.assertEqual(out["threw"], "", out)
        self.assertIn("paints over the header", out["why"])

    def test_a_missing_header_or_caption_is_named_not_thrown(self):
        for tl, cap, says in ((False, "a caption", "no header row"), (True, None, "no caption"),
                              (True, "   ", "caption is empty")):
            out = self.why(tl, cap)
            self.assertEqual(out["threw"], "", "the refusal THREW instead of naming %r: %r" % (says, out))
            self.assertIn(says, out["why"], out)


RED_PROOF = [
    {"why": "REG-2140 - theatre-head's refusal dereferences a missing caption and throws",
     "file": "render_check.py",
     "find": "            if (!cap) return 'the theatre has no caption (#th-caption)';\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1752 - the wait removed: the fixture is adopted before the page's own answer and gets erased",
     "file": "render_check.py",
     "find": "            if (!_nyT || /waiting-on-you: UNKNOWN$/.test(_nyT)) return false;\n",
     "replace": "            if (false) return false;\n",
     "matches": 1},
    {"why": "REG-1752 - the wait only checks for an empty host: the painted pre-answer UNKNOWN still adopts",
     "file": "render_check.py",
     "find": "            if (!_nyT || /waiting-on-you: UNKNOWN$/.test(_nyT)) return false;\n",
     "replace": "            if (!_nyT) return false;\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
