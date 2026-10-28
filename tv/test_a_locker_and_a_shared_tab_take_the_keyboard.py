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


RED_PROOF = [
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
     "find": "return '<button type=\"button\" class=\"vd-tab' + (i === _sharedPage ? ' vt-on' : '') + '\" role=\"tab\" aria-selected=\"' + (i === _sharedPage) + '\" onclick=\"window._sharedSetPage(' + i + ')\">' + p.icon + ' ' + p.label + '</button>';",
     "replace": "return '<div class=\"vd-tab' + (i === _sharedPage ? ' vt-on' : '') + '\" onclick=\"window._sharedSetPage(' + i + ')\">' + p.icon + ' ' + p.label + '</div>';",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
