# -*- coding: utf-8 -*-
"""#154.19 (REG-2735, GrokBot's vault sweep) - A LOCKER AND A SHARED-STASH TAB TAKE THE KEYBOARD.

A locker's plate (div.vm-plate) opened its ID card on a click only - no tabindex, no role - and the shared stash's five
page tabs were divs with an onclick, so neither could be reached from the keyboard (the mule tabs beside them were
already real tab buttons). The plate is focusable now, a button to a reader, and Enter or Space on the PLATE itself
clicks it, so the page's own click handler opens the card exactly as a mouse does; a key that lands inside it is left
alone. The shared stash's tabs are the mule tabs' shape: button type=button role=tab with aria-selected, in a tablist.

Driven on the whole page in node (vault_page_node: every inline script, a fresh empty world, no network): the vault is
rendered, the plate's own keydown is run, and the shared stash card is opened. RED_PROOF below. Same defect as #148.5
(REG-2734, the move rows).
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import vault_page_node as VPN  # noqa: E402

BODY = r"""
(function(){
var W = window;
try { W.renderVault(); } catch (e) { OUT.renderErr = String(e && e.message || e); }
H.flush(60, 3);
var all = '';
H.ELS.forEach(function(el){ if (el && typeof el.innerHTML === 'string' && el.innerHTML.indexOf('vm-plate') >= 0) all += el.innerHTML; });
var m = /<div class="vm-plate"([^>]*)>/.exec(all);
OUT.plateFound = !!m;
var attrs = m ? m[1] : '';
function attr(n){
  var r = new RegExp(' ' + n + '="([^"]*)"').exec(attrs);
  return r ? r[1].replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&') : null;
}
OUT.tabindex = attr('tabindex'); OUT.role = attr('role');
var kd = attr('onkeydown'), clicks = 0, PLATE = { click: function(){ clicks++; } };
function fire(key, target){
  var prevented = false;
  if (kd) new Function('event', kd).call(PLATE, { key: key, target: target, preventDefault: function(){ prevented = true; } });
  return prevented;
}
OUT.enter = fire('Enter', PLATE); OUT.space = fire(' ', PLATE); OUT.child = fire('Enter', { id: 'inner' }); OUT.tab = fire('Tab', PLATE);
OUT.clicks = clicks;
try { W.openMuleCard('shared'); } catch (e) { OUT.sharedErr = String(e && e.message || e); }
H.flush(60, 3);
var sh = '';
H.ELS.forEach(function(el){
  if (el && typeof el.innerHTML === 'string' && el.innerHTML.indexOf('SHARED STASH') >= 0 && el.innerHTML.indexOf('vd-tab') >= 0) sh = el.innerHTML;
});
var tabs = sh.match(/<[a-z]+ [^>]*class="vd-tab(?: [^"]*)?"[^>]*>/g) || [];   /* the tab, never its vd-tabs row */
OUT.sharedTabs = tabs.map(function(t){
  return /^<([a-z]+)/.exec(t)[1] + (/ type="button"/.test(t) ? ':button' : '') + (/ role="tab"/.test(t) ? ':tab' : '')
    + (/ aria-selected="(true|false)"/.test(t) ? ':sel' : '');
});
OUT.tablist = / role="tablist" aria-label="shared stash pages"/.test(sh);
/* REG-2747 - a page switch made from a focused tab hands the focus to the newly selected tab; one made with no tab
   focused (a mouse) moves no focus. The DOM stand-ins record who asked for focus. */
var focused = [];
var realQS = document.querySelector, realAE = Object.getOwnPropertyDescriptor(document, 'activeElement');
document.querySelector = function(sel){
  if (String(sel).indexOf('.vd-tab[aria-selected="true"]') === 0) return { focus: function(){ focused.push('selected-tab'); } };
  return realQS.call(document, sel);
};
Object.defineProperty(document, 'activeElement', { configurable: true, get: function(){ return { classList: { contains: function(c){ return c === 'vd-tab'; } } }; } });
try { W._sharedSetPage(1); } catch (e) { OUT.setErr = String(e && e.message || e); }
OUT.focusFromKey = focused.slice();
focused.length = 0;
Object.defineProperty(document, 'activeElement', { configurable: true, get: function(){ return null; } });
try { W._sharedSetPage(2); } catch (e) { OUT.setErr2 = String(e && e.message || e); }
OUT.focusFromMouse = focused.slice();
document.querySelector = realQS;
if (realAE) Object.defineProperty(document, 'activeElement', realAE); else delete document.activeElement;
/* REG-2767 - the tablist roves with the arrow keys (GrokBot's v3824 nit): the page each key asks for, from page 2, 0, 4 */
OUT.tabKeyWired = / role="tablist" aria-label="shared stash pages" onkeydown="window._sharedTabKey\(event\)"/.test(sh);
var realSet = W._sharedSetPage, asked = [];
function rove(from, k){ realSet(from); var pd = false; W._sharedSetPage = function(i){ asked.push(i); };
  var r = W._sharedTabKey({ key: k, preventDefault: function(){ pd = true; } }); W._sharedSetPage = realSet; return [r, pd]; }
OUT.rove = [rove(2, 'ArrowRight'), rove(2, 'ArrowLeft'), rove(2, 'Home'), rove(2, 'End'), rove(0, 'ArrowLeft'),
            rove(4, 'ArrowRight'), rove(2, 'a')];
OUT.roveAsked = asked;
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class ALockerAndASharedTabTakeTheKeyboard(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, prelude="localStorage.setItem('d2r_ownerClaim', '*');", timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])
        self.assertTrue(self.o.get("plateFound"), "PREMISE: no locker plate was drawn: %r" % self.o)

    def test_a_locker_plate_is_focusable_and_opens_on_enter_or_space(self):
        o = self.o
        self.assertEqual((o.get("tabindex"), o.get("role")), ("0", "button"), "a locker cannot take the keyboard: %r" % o)
        self.assertEqual(o.get("clicks"), 2, "Enter/Space on the plate did not click it, or a key inside it did: %r" % o)
        self.assertEqual((o.get("enter"), o.get("space"), o.get("child"), o.get("tab")), (True, True, False, False), o)

    def test_the_shared_stash_tabs_are_tab_buttons(self):
        o = self.o
        self.assertEqual(len(o.get("sharedTabs") or []), 5, "PREMISE: the shared stash card drew no page tabs: %r" % o)
        self.assertEqual(set(o["sharedTabs"]), {"button:button:tab:sel"},
                         "a shared stash tab is not a keyboard-reachable tab button: %r" % o["sharedTabs"])
        self.assertTrue(o.get("tablist"), "the shared stash tabs sit in no tablist")

    def test_a_keyboard_page_switch_keeps_the_focus_on_the_tabs(self):
        """REG-2747 (GrokBot's v3821 pass) - after Enter on a tab the card re-rendered and focus fell to <body>."""
        o = self.o
        self.assertFalse(o.get("setErr") or o.get("setErr2"), o)
        self.assertEqual(o.get("focusFromKey"), ["selected-tab"], "a keyboard page switch dropped the focus: %r" % o)
        self.assertEqual(o.get("focusFromMouse"), [], "a mouse page switch moved the focus: %r" % o)

    def test_the_tablist_roves_with_the_arrow_keys(self):
        """REG-2767 (GrokBot's v3824 pass) - ArrowRight did not move between the shared stash's page tabs."""
        o = self.o
        self.assertTrue(o.get("tabKeyWired"), "the shared stash tablist does not hand its keys to _sharedTabKey")
        self.assertEqual(o.get("roveAsked"), [3, 1, 0, 4, 4, 0],
                         "Right/Left/Home/End from pages 2, 0 and 4 did not ask for 3, 1, 0, 4 and wrap: %r" % o.get("roveAsked"))
        self.assertEqual([r[0] for r in o.get("rove") or []], [True] * 6 + [False], "a letter key was taken, or an arrow was not")
        self.assertTrue(all(r[1] for r in (o.get("rove") or [])[:6]), "an arrow key also scrolled the page (no preventDefault)")


RED_PROOF = [
    {"why": "REG-2767 - the shared stash tablist ignores the arrow keys again",
     "file": "bible.html",
     "find": " onkeydown=\"window._sharedTabKey(event)\">' + tabs + '</div>'",
     "replace": ">' + tabs + '</div>'",
     "matches": 1, "needs": "node"},
    {"why": "REG-2767 - the arrow keys stop at the ends instead of wrapping",
     "file": "bible.html",
     "find": "(_sharedPage + (k === 'ArrowRight' ? 1 : n - 1)) % n;",
     "replace": "Math.max(0, Math.min(n - 1, _sharedPage + (k === 'ArrowRight' ? 1 : -1)));",
     "matches": 1, "needs": "node"},
    {"why": "REG-2747 - a keyboard page switch on the shared stash drops the focus to the page again",
     "file": "bible.html",
     "find": "    if (_fromKey) { try { var _sel = document.querySelector('.vd-tab[aria-selected=\"true\"]'); if (_sel) _sel.focus(); } catch (eF2) {} }\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2747 - every page switch steals the focus, a mouse click included",
     "file": "bible.html",
     "find": "    if (_fromKey) { try {",
     "replace": "    if (true) { try {",
     "matches": 1, "needs": "node"},
    {"why": "#154.19 (REG-2735) - a locker plate takes no keyboard focus again",
     "file": "bible.html",
     "find": "        + '<div class=\"vm-plate\" tabindex=\"0\" role=\"button\" onkeydown=",
     "replace": "        + '<div class=\"vm-plate\" onkeydown=",
     "matches": 1, "needs": "node"},
    {"why": "#154.19 (REG-2735) - Enter/Space on a focused locker plate does nothing",
     "file": "bible.html",
     "find": "&&event.target===this){event.preventDefault();this.click();}",
     "replace": "&&false){event.preventDefault();this.click();}",
     "matches": 1, "needs": "node"},
    {"why": "#154.19 (REG-2735) - a key inside the plate also clicks it",
     "file": "bible.html",
     "find": "&&event.target===this){event.preventDefault();this.click();}",
     "replace": "){event.preventDefault();this.click();}",
     "matches": 1, "needs": "node"},
    {"why": "#154.19 (REG-2735) - the shared stash's page tabs are divs with an onclick again",
     "file": "bible.html",
     "find": "return '<button type=\"button\" class=\"vd-tab' + (i === _sharedPage ? ' vt-on' : '') + '\" role=\"tab\" aria-selected=\"' + (i === _sharedPage) + '\" onclick=\"window._sharedSetPage(' + i + ')\">Page ' + (i + 1) + (p.length ? ' <b>' + p.length + '</b>' : '') + '</button>';",
     "replace": "return '<div class=\"vd-tab' + (i === _sharedPage ? ' vt-on' : '') + '\" onclick=\"window._sharedSetPage(' + i + ')\">Page ' + (i + 1) + '</div>';",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
