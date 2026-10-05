# -*- coding: utf-8 -*-
"""Sessions leaves Vault on the first press.

The shell is its own stacking context, and the board iframe is a later sibling
promoted above that context. A header z-index that only competes inside the
shell never meets the iframe, so the first press lands on the board. While a
room is open the shell stops being that context.

The same press is taken on pointerdown. The click that follows that press on
the same button must not open a second room. A click that arrives alone — the
keyboard, and the render gate — still leaves.
"""
import io
import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
UI = os.path.join(HERE, "control_ui.html")

# The live declaration. A comment that quotes this sentence must not satisfy the law.
LAYER = "body.shell-open .shell { z-index: auto; }"
START = "var _headTabPtr = null, _headTabPtrTs = 0;"
END = "/* v1596 — SESSIONS IS THE HOMEPAGE."


def _page():
    with io.open(UI, encoding="utf-8", errors="replace") as f:
        return f.read()


def _layer_live(src):
    """The layer rule, once, as CSS, outside a comment. -> (bool, str)"""
    n = src.count(LAYER)
    if n != 1:
        return False, "the layer rule occurs %d times" % n
    i = src.find(LAYER)
    a = src.rfind("<style>", 0, i)
    b = src.find("</style>", i)
    if a < 0 or b < 0:
        return False, "the layer rule is not inside a style block"
    block = src[a:b]
    j = block.find(LAYER)
    opened = block.rfind("/*", 0, j)
    if opened >= 0 and block.rfind("*/", 0, j) < opened:
        return False, "the layer rule sits inside a comment"
    return True, "ok"


def _handler(src):
    """The press handler and the two listeners, as source. -> str|None"""
    if src.count(START) != 1 or src.count(END) != 1:
        return None
    i = src.find(START)
    j = src.find(END, i)
    if j < 0:
        return None
    return src[i:j]


def _ask(src):
    """Run the shipped handler in node. -> dict|None, and the node error if it failed."""
    body = _handler(src)
    if body is None:
        return None, "the press handler is not in the page"
    js = (
        "function boot(){\n"
        "  var calls = [];\n"
        "  function showSessions(){ calls.push('session'); }\n"
        "  function shellHome(){ calls.push('tvd'); }\n"
        "  function shellOpen(tab){ calls.push(String(tab)); }\n"
        "  var _shellTab = 'vault';\n"
        "  var document = { body: { removeAttribute: function(){} },\n"
        "    getElementById: function(){ return { blur: function(){} }; } };\n"
        "  var window = { TH: { open: false }, thClose: function(){ calls.push('theatre'); } };\n"
        "  var _ht = { ls: {}, addEventListener: function(t, fn){\n"
        "    (this.ls[t] = this.ls[t] || []).push(fn); } };\n"
        + body +
        "  function button(tab){\n"
        "    var b = { dataset: { tab: tab } };\n"
        "    b.closest = function(sel){ return sel === '.ht' ? b : null; };\n"
        "    return b;\n"
        "  }\n"
        "  function fire(type, b, ts){\n"
        "    var e = { type: type, target: b, timeStamp: ts,\n"
        "      preventDefault: function(){}, stopPropagation: function(){} };\n"
        "    (_ht.ls[type] || []).forEach(function(fn){ fn(e); });\n"
        "  }\n"
        "  return { calls: calls, fire: fire, button: button, bound: Object.keys(_ht.ls).sort() };\n"
        "}\n"
        "var out = {};\n"
        "var h = boot();\n"
        "var s = h.button('session');\n"
        "h.fire('pointerdown', s, 1000);\n"
        "h.fire('click', s, 1200);\n"
        "out.pressThenClick = h.calls.slice();\n"
        "out.bound = h.bound;\n"
        "h = boot();\n"
        "h.fire('click', h.button('session'), 1000);\n"
        "out.bareClick = h.calls.slice();\n"
        "h = boot();\n"
        "h.fire('click', h.button('session'), 1000);\n"
        "h.fire('click', h.button('vault'), 1010);\n"
        "out.rapidDifferent = h.calls.slice();\n"
        "h = boot();\n"
        "s = h.button('session');\n"
        "h.fire('pointerdown', s, 1000);\n"
        "h.fire('click', s, 1100);\n"
        "h.fire('click', s, 2000);\n"
        "out.laterClick = h.calls.slice();\n"
        "console.log(JSON.stringify(out));\n"
    )
    try:
        r = subprocess.run(["node", "-"], input=js, capture_output=True, text=True, timeout=60)
    except Exception as e:
        return None, "node did not run: %s" % e
    if r.returncode != 0:
        return None, (r.stderr or r.stdout or "node failed")[-800:]
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), ""
    except Exception as e:
        return None, "node answered %r (%s)" % (r.stdout[-400:], e)


class SessionsLeavesTheVaultOnTheFirstPress(unittest.TestCase):

    def test_a_quoted_rule_inside_a_comment_is_not_the_rule(self):
        """The checker itself. A comment that contains the declaration must read as absent."""
        fake = "<style>\n/* " + LAYER + " */\n.shell { z-index: 1; }\n</style>"
        ok, why = _layer_live(fake)
        self.assertFalse(ok, why)

    def test_the_open_shell_is_not_its_own_layer(self):
        """While a room is up, the header at 960 and the iframe at 940 share one context."""
        ok, why = _layer_live(_page())
        self.assertTrue(ok, why)

    def test_one_press_leaves_once_and_a_bare_click_still_leaves(self):
        """pointerdown plus its click is one leave. A click with no press ahead of it still leaves.
        Two clicks on two tabs in the same instant both leave. A later click on the same tab leaves again."""
        got, err = _ask(_page())
        self.assertIsNotNone(got, err)
        self.assertEqual(["click", "pointerdown"], got["bound"],
                         "the header must hear the press and the click: %r" % got["bound"])
        self.assertEqual(["session"], got["pressThenClick"],
                         "one press left %d times: %r" % (len(got["pressThenClick"]), got["pressThenClick"]))
        self.assertEqual(["session"], got["bareClick"],
                         "a click with no pointerdown did not leave: %r" % got["bareClick"])
        self.assertEqual(["session", "vault"], got["rapidDifferent"],
                         "two tabs pressed together did not both leave: %r" % got["rapidDifferent"])
        self.assertEqual(["session", "session"], got["laterClick"],
                         "a click after the press had finished did not leave: %r" % got["laterClick"])


RED_PROOF = [
    {
        "why": "the open shell must stop being its own layer; putting the header back at z-index 1 "
               "inside that layer lets the iframe paint over Sessions",
        "file": "control_ui.html",
        "find": "body.shell-open .shell { z-index: auto; }\n",
        "replace": "body.shell-open .shell { z-index: 1; }\n",
        "matches": 1,
    },
    {
        "why": "one press must leave once; deleting the return makes the click that follows the "
               "same press open the room a second time",
        "file": "control_ui.html",
        "find": "    if (e.type === 'click' && b === _headTabPtr && ((e.timeStamp || 0) - _headTabPtrTs) < 700) {\n"
                "      e.preventDefault();\n"
                "      e.stopPropagation();\n"
                "      return;\n"
                "    }\n",
        "replace": "    if (e.type === 'click' && b === _headTabPtr && ((e.timeStamp || 0) - _headTabPtrTs) < 700) {\n"
                   "      e.preventDefault();\n"
                   "      e.stopPropagation();\n"
                   "    }\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
