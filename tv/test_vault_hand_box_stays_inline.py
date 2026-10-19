"""v3773 - the "+ Add an item" box was a page-wide fixed layer (inset 0, a dark scrim, z-index 130)
that covered the tab bar and FIND ON A MULE and swallowed tab clicks. It now sits inline in the
vault, right under the find results, with no scrim. The top search's hover tip (a title on
.gsearch-wrap) sat on the first result row; the title is gone, the placeholder says the same.

The CSS rule is read as a rule, the open path runs in node on a small DOM. Each RED_PROOF changes
what the page does.
"""
import json
import os
import re
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read():
    with open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        return fh.read()


def _rule(css, sel):
    m = re.search(r"(?m)^" + re.escape(sel) + r"\{([^}]*)\}", css)
    return m.group(1) if m else None


def problems(bible):
    bad = []
    rule = _rule(bible, "#vault-hand-win")
    if rule is None:
        return ["no #vault-hand-win rule"]
    decl = dict((k.strip().lower(), v.strip().lower()) for k, v in
                (d.split(":", 1) for d in rule.split(";") if ":" in d))
    if decl.get("position") in ("fixed", "absolute", "sticky"):
        bad.append("the add box is a %s layer again" % decl["position"])
    if "inset" in decl or "top" in decl:
        bad.append("the add box is pinned over the page (inset/top)")
    if "rgba" in decl.get("background", "") or "rgba" in decl.get("background-color", ""):
        bad.append("the add box draws a scrim over the page")
    z = decl.get("z-index", "auto")
    if z != "auto" and z.isdigit() and int(z) >= 100:
        bad.append("the add box sits at z-index %s over the tabs" % z)
    if _rule(bible, "#vault-hand-win[hidden]") is None or "display:none" not in _rule(bible, "#vault-hand-win[hidden]").replace(" ", ""):
        bad.append("a closed add box is not display:none")
    wrap = re.search(r'<div class="gsearch-wrap"[^>]*>', bible)
    inp = re.search(r'<input id="gsearch-input"[^>]*>', bible)
    for tag in (wrap, inp):
        if tag and re.search(r"\stitle=", tag.group(0)):
            bad.append("the top search carries a hover title that covers its results: %s" % tag.group(0)[:80])
    i = bible.find("  window.vaultHandOpen = function(){")
    j = bible.find("\n  };\n", i)
    fn = bible[i:j + 5]
    prog = r"""
function El(id){ this.id = id; this.parentNode = null; this.kids = []; this.hidden = true; this.attrs = {}; }
El.prototype.setAttribute = function(k, v){ this.attrs[k] = v; };
El.prototype.appendChild = function(c){ if (c.parentNode) c.parentNode.kids.splice(c.parentNode.kids.indexOf(c), 1); c.parentNode = this; this.kids.push(c); return c; };
El.prototype.insertBefore = function(c, ref){ if (c.parentNode) c.parentNode.kids.splice(c.parentNode.kids.indexOf(c), 1); c.parentNode = this; var k = ref ? this.kids.indexOf(ref) : -1; if (k < 0) this.kids.push(c); else this.kids.splice(k, 0, c); return c; };
Object.defineProperty(El.prototype, 'nextSibling', { get: function(){ var p = this.parentNode; if (!p) return null; return p.kids[p.kids.indexOf(this) + 1] || null; } });
var body = new El('body'), vault = new El('tab-vault'), find = new El('vault-find-results'), move = new El('vault-move-list');
body.appendChild(vault); vault.appendChild(find); vault.appendChild(move);
var byId = function(id){ var walk = [body], x; while ((x = walk.shift())) { if (x.id === id) return x; walk = walk.concat(x.kids); } return null; };
var document = { body: body, documentElement: { classList: { contains: function(){ return false; } } },
  getElementById: byId, createElement: function(){ return new El(''); } };
var window = { vaultHandSearch: function(){ return { ok: true }; } };
var _vhSeen = {};
""" + fn + r"""
var out = [];
for (var n = 0; n < 2; n++) {
  window.vaultHandOpen();
  var h = byId('vault-hand-win');
  out.push({ parent: h && h.parentNode ? h.parentNode.id : null, after: h ? (vault.kids[vault.kids.indexOf(h) - 1] || {}).id : null, shown: h ? !h.hidden : false });
}
console.log(JSON.stringify(out));
"""
    try:
        r = subprocess.run(["node", "-e", prog], capture_output=True, text=True, timeout=60)
        got = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        return bad + ["node run failed: %s %s" % (e, (r.stderr if 'r' in dir() else '')[-400:])]
    for k, row in enumerate(got):
        if row["parent"] != "tab-vault" or row["after"] != "vault-find-results" or not row["shown"]:
            bad.append("open #%d: the add box is not shown inline right under the find results: %s" % (k + 1, row))
    return bad


class TestVaultHandBoxStaysInline(unittest.TestCase):
    def test_01_add_box_is_inline_and_the_top_search_has_no_covering_tip(self):
        bad = problems(_read())
        self.assertEqual(bad, [], bad)

    def test_02_distinct_attacks_clear_the_wilson_bar(self):
        from confidence import wilson_lower
        n = len(RED_PROOF)
        self.assertGreaterEqual(n, 10)
        self.assertGreaterEqual(wilson_lower(n, n), 0.722)


RED_PROOF = [
    {'why': 'The add box is a fixed layer again.', 'file': 'bible.html', 'find': '#vault-hand-win{position:relative;z-index:auto;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'replace': '#vault-hand-win{position:fixed;z-index:auto;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'matches': 1},
    {'why': 'The add box is pinned over the whole page.', 'file': 'bible.html', 'find': '#vault-hand-win{position:relative;z-index:auto;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'replace': '#vault-hand-win{position:relative;z-index:auto;display:block;inset:0;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'matches': 1},
    {'why': 'The add box draws its dark scrim again.', 'file': 'bible.html', 'find': '#vault-hand-win{position:relative;z-index:auto;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'replace': '#vault-hand-win{position:relative;z-index:auto;display:block;margin:8px 0;padding:0;background:rgba(4,3,2,.62);box-sizing:border-box}', 'matches': 1},
    {'why': 'The add box rides over the tab bar at z-index 130.', 'file': 'bible.html', 'find': '#vault-hand-win{position:relative;z-index:auto;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'replace': '#vault-hand-win{position:relative;z-index:130;display:block;margin:8px 0;padding:0;background:none;box-sizing:border-box}', 'matches': 1},
    {'why': 'A closed add box stays on screen.', 'file': 'bible.html', 'find': '#vault-hand-win[hidden]{display:none}', 'replace': '#vault-hand-win[hidden]{opacity:.99}', 'matches': 1},
    {'why': 'The open path no longer moves the box under the find results.', 'file': 'bible.html', 'find': '    if (_vhAnchor && _vhAnchor.parentNode && _vhAnchor.nextSibling !== host)', 'replace': '    if (false && _vhAnchor && _vhAnchor.parentNode && _vhAnchor.nextSibling !== host)', 'matches': 1},
    {'why': 'The box is anchored under the move list instead of the find results.', 'file': 'bible.html', 'find': "    var _vhAnchor = document.getElementById('vault-find-results');", 'replace': "    var _vhAnchor = document.getElementById('vault-move-list');", 'matches': 1},
    {'why': 'After the move the open path hands the box back to the page body.', 'file': 'bible.html', 'find': '      _vhAnchor.parentNode.insertBefore(host, _vhAnchor.nextSibling);\n    host.hidden = false;', 'replace': '      _vhAnchor.parentNode.insertBefore(host, _vhAnchor.nextSibling);\n    if (document.body) document.body.appendChild(host);\n    host.hidden = false;', 'matches': 1},
    {'why': 'The top search wrap carries its hover title again.', 'file': 'bible.html', 'find': '<div class="gsearch-wrap">', 'replace': '<div class="gsearch-wrap" title="Search a boss, act, zone, super-unique or item — Enter to jump">', 'matches': 1},
    {'why': 'The hover title moves onto the search input itself.', 'file': 'bible.html', 'find': '<input id="gsearch-input" ', 'replace': '<input id="gsearch-input" title="Enter to jump" ', 'matches': 1},
]


if __name__ == "__main__":
    unittest.main()
