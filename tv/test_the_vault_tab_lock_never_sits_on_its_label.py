# -*- coding: utf-8 -*-
"""#107 — THE VAULT TAB'S LOCK NEVER SITS ON ITS OWN LABEL, AND NOTHING CUTS IT OFF.

MEASURED 2026-09-30 with the real tab icons served (the icons are what make the tab tight): the 🔒 stamp on the Vault
tab (out of flow since v2443, top:1px right:3px) sat 6-10px on the "Vault" label's ink at 900, 960, 1000, 1120, 1280,
1400 and 1600 - "Vaul" with a padlock on the t, on every width he uses. It was never red because the render gate's
console-tabs target samples label points with elementFromPoint, and the stamp is pointer-events:none: the instrument
could not see the one thing covering the label.

The fix lifts the stamp onto the tab's top edge (a badge, still out of flow, still costing the strip nothing), and the
brand above it clips only sideways (overflow-x: clip), because a y-clip cut the badge to a sliver wherever the tabs
wrap - and an invisible lock is the direction v2443 says this must never fail in.

The law RENDERS the shipped header in headless Chrome at seven widths, over a scratch localhost server so the tab
icons load exactly as they do on his console, and measures geometry, never paint order:
  1. the stamp's box never intersects the label's ink (a Range over the label's text),
  2. no ancestor that clips an axis cuts the stamp on that axis,
  3. the stamp is there at all (a lock that is gone passes 1 and 2 by vanishing).
[[visual-regression-detector]] [[feedback-suspect-the-instrument]] RED_PROOF below.
"""
import json
import os
import socket
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


# ⚠ BEFORE the import: render_check reads its Chrome port once. Never 9222/9223 (his).
_LAW_PORT = os.environ.get("TV_LAW_PORT", "").strip()
os.environ["TV_RENDER_PORT"] = _LAW_PORT if _LAW_PORT.isdigit() and _LAW_PORT not in ("9222", "9223") else str(_free_port())
import render_check as RC  # noqa: E402

WIDTHS = (1600, 1400, 1280, 1120, 1000, 960, 900)

RED_PROOF = [
    {
        "why": "#107 - the stamp goes back inside the tab at top:1px: the padlock sits on the Vault label again",
        "file": "control_ui.html",
        "find": "    position: absolute; top: -10px; right: 3px;\n",
        "replace": "    position: absolute; top: 1px; right: 3px;\n",
        "matches": 1,
    },
    {
        "why": "#107 - the brand clips the y axis again: wherever the tabs wrap, the lifted badge is cut to a sliver",
        "file": "control_ui.html",
        "find": "    .topbar .brand { flex: 1 1 auto; min-width: 0; overflow-x: clip; overflow-y: visible; }",
        "replace": "    .topbar .brand { flex: 1 1 auto; min-width: 0; overflow: hidden; }",
        "matches": 1,
    },
]

MEASURE = r"""(function(){ try {
  var b = document.querySelector('#head-tabs .ht[data-tab="vault"]');
  if (!b) return JSON.stringify({err: 'no vault tab'});
  var l = b.querySelector('.ht-lbl'), c = b.querySelector('.lc-tab');
  if (!l || !c) return JSON.stringify({err: 'no label or no stamp'});
  var rg = document.createRange(); rg.selectNodeContents(l); var ri = rg.getBoundingClientRect(), rc = c.getBoundingClientRect();
  var ox = Math.min(ri.right, rc.right) - Math.max(ri.left, rc.left), oy = Math.min(ri.bottom, rc.bottom) - Math.max(ri.top, rc.top);
  var cut = [];
  for (var a = c.parentElement; a && a !== document.documentElement; a = a.parentElement) {
    var cs = getComputedStyle(a), ra = a.getBoundingClientRect();
    if (cs.overflowY !== 'visible' && (rc.top < ra.top - 0.5 || rc.bottom > ra.bottom + 0.5))
      cut.push('y by ' + (a.id ? '#' + a.id : a.className || a.tagName));
    if (cs.overflowX !== 'visible' && (rc.left < ra.left - 0.5 || rc.right > ra.right + 0.5))
      cut.push('x by ' + (a.id ? '#' + a.id : a.className || a.tagName));
  }
  var st = getComputedStyle(c);
  return JSON.stringify({on: (ox > 0.5 && oy > 0.5) ? Math.round(Math.min(ox, oy) * 10) / 10 : 0, cut: cut,
                         shown: rc.width > 4 && rc.height > 4 && st.display !== 'none' && st.visibility !== 'hidden' && +st.opacity > 0,
                         icon: !!b.querySelector('img.ht-i'), text: l.textContent});
} catch (e) { return JSON.stringify({err: String(e)}); } })()"""

_CACHE = {}


def _render():
    if "r" in _CACHE:
        return _CACHE["r"]
    port = _free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=REPO,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {}
    try:
        if not RC._chrome_up():
            raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d" % (RC.CHROME, RC.PORT))
        try:
            t = RC._Tab("about:blank")
            t.send("Page.enable")
            t.send("Runtime.enable")
            for w in WIDTHS:
                t.send("Emulation.setDeviceMetricsOverride", width=w, height=900, deviceScaleFactor=1, mobile=False)
                t.send("Page.navigate", url="http://127.0.0.1:%d/tv/control_ui.html" % port)
                for _ in range(120):
                    time.sleep(0.25)
                    try:
                        if t.ev("document.readyState==='complete' && !!document.querySelector('#head-tabs .lc-tab')") is True:
                            break
                    except Exception:
                        pass
                else:
                    raise AssertionError("the console header never painted at %d - UNKNOWN, not passing" % w)
                time.sleep(1.2)          # the icons land and the strip settles
                res[w] = json.loads(t.ev(MEASURE))
            try:
                t.close()
            except Exception:
                pass
        finally:
            RC._chrome_down()
    finally:
        srv.kill()
        srv.wait(10)
    _CACHE["r"] = res
    return res


@unittest.skipUnless(os.path.exists(RC.CHROME or ""), "no Chrome on this machine - the header was not rendered (declared skip 77)")
class TheVaultTabLockNeverSitsOnItsLabel(unittest.TestCase):

    def test_the_header_was_really_rendered_with_its_icons(self):
        r = _render()
        for w in WIDTHS:
            self.assertNotIn("err", r[w], "%d: %r" % (w, r[w]))
            self.assertEqual(r[w]["text"], "Vault", "%d: the label is not the Vault tab's" % w)
        self.assertTrue(any(r[w]["icon"] for w in WIDTHS if w > 1100),
                        "no tab icon loaded at any wide width - the strip was measured looser than on his console")

    def test_the_stamp_is_never_on_the_label(self):
        r = _render()
        on = ["%d: %spx" % (w, r[w]["on"]) for w in WIDTHS if r[w].get("on")]
        self.assertEqual(on, [], "the vault tab's lock sits on its own label: " + ", ".join(on))

    def test_nothing_cuts_the_stamp_off_and_it_is_there(self):
        r = _render()
        cut = ["%d: %s" % (w, "; ".join(r[w]["cut"])) for w in WIDTHS if r[w].get("cut")]
        self.assertEqual(cut, [], "an ancestor clips the vault tab's lock: " + " | ".join(cut))
        gone = [w for w in WIDTHS if not r[w].get("shown")]
        self.assertEqual(gone, [], "the lock is not shown at %s - an invisible lock reads as no lock" % gone)


if __name__ == "__main__":
    unittest.main(verbosity=2)
