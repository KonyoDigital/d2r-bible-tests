#!/usr/bin/env python3
"""EVERY CONTROL HAS A NAME — asked of the live DOM, because the source cannot answer it.

Why this exists as a separate instrument from the guards in test_control.py:

  ⚠ A STATIC GUARD ACCEPTED A PLACEHOLDER AND STAYED GREEN OVER 21 FIELDS. A placeholder IS exposed
    as a fallback accessible name, so the source-level test was not wrong — it was asking a weaker
    question than a person asks. This probe asks it the way he meets it: the placeholder DISAPPEARS
    the moment you type, so tabbing back into a half-filled box leaves nothing at all.

  ⚠ THE ATTRIBUTES LIVE INSIDE JS STRING CONCATENATION. `aria-label="one more copy of '+esc(n)+'"`
    can mis-escape and land as literal text while every source grep still passes. Only the rendered
    DOM proves the name REACHED anything. [[the-unjoined-end]]

  ⚠ AND A SKIP IS NOT A PASS. No Chrome, no tab, no controls found: the verdict is UNKNOWN and this
    exits non-zero saying so, rather than printing a green line nobody earned.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console_safe import enable                                      # noqa: E402
import render_check as rc                                            # noqa: E402

enable(sys.stdout)   # this file reports in 🟢/⚪/⚠; a non-UTF-8 console must not crash the REPORT

PROBE = r"""
(function(){
  function name(el){
    var a = el.getAttribute('aria-label'); if (a && a.trim()) return a.trim();
    var ti = el.getAttribute('title');     if (ti && ti.trim()) return ti.trim();
    if (el.getAttribute('aria-hidden') === 'true') return '(hidden from assistive tech)';
    var lb = el.id && document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
    if (lb && (lb.innerText||'').trim()) return (lb.innerText||'').trim();
    var t = (el.innerText || el.textContent || '').trim();
    if (/[A-Za-z0-9]/.test(t)) return t.slice(0, 40);
    return null;                          // ⚠ placeholder deliberately NOT consulted
  }
  var out = {nameless: [], named: 0, weak: [], ghosted: []};
  var els = document.querySelectorAll('button, select, input:not([type=hidden])');
  for (var i = 0; i < els.length; i++){
    var el = els[i], cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') continue;
    var ty = (el.getAttribute('type') || '').toLowerCase();
    if (el.tagName === 'INPUT' && ['checkbox','radio','range','file'].indexOf(ty) >= 0) continue;
    var n = name(el), r = el.getBoundingClientRect();
    var who = el.tagName + (el.id ? '#' + el.id : '.' + String(el.className||'').slice(0,26))
            + ' [' + Math.round(r.width) + 'x' + Math.round(r.height) + ']';
    // ⚠ A VISIBLE THING MARKED aria-hidden IS WORSE THAN A NAMELESS ONE, and it hides itself from
    // this very probe. v2246 did exactly that to the profile crest: I called it decorative, marked
    // it aria-hidden, and the probe then skipped it and reported a clean page. Refuse the skip.
    if (el.getAttribute('aria-hidden') === 'true' && r.width > 0 && r.height > 0){
      out.ghosted.push(who + ' -> ' + JSON.stringify((el.innerText||'').trim().slice(0,30)));
    }
    if (n === null){
      out.nameless.push(who + (el.getAttribute('placeholder') ? ' (placeholder only)' : ''));
    } else {
      out.named++;
      if (n.length < 3) out.weak.push(who + ' -> ' + JSON.stringify(n));
    }
  }
  out.total = els.length;
  return JSON.stringify(out);
})()
"""

# ⚠ EVERY TAB, READ OFF THE PAGE — not a list I typed. My first cut named six tabs that mostly do
# not exist ("uniques", "sets", "sessions") and called `window.showTab`, which is not the function;
# the switcher is `switchTab`. Nothing errored. The probe printed six identical rows — 606/593/0/5
# six times — and read as six-tab coverage while measuring ONE tab six times.
# [[feedback-blind-fixture-green-gate]]
TABS = None                                       # discovered from the DOM at run time

DISCOVER = ("Array.from(document.querySelectorAll('button.tab[data-tab]'))"
            ".map(function(b){return b.dataset.tab}).join(',')")
ACTIVE = ("(function(){var a=document.querySelector('button.tab.active[data-tab]');"
          "return a?a.dataset.tab:''})()")


def main():
    if not rc._chrome_up():
        print("⚪ UNKNOWN — no Chrome on :%d. A skip is not a pass." % rc.PORT)
        return 2
    page = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bible.html")
    tab = rc._Tab("file://" + page)
    try:
        tab.send("Page.enable")
        tab.send("Runtime.enable")
        time.sleep(3.0)
        found = (tab.ev(DISCOVER) or "").split(",")
        tabs = [t for t in found if t]
        if len(tabs) < 5:
            print("⚪ UNKNOWN — found %d tabs on the page; the switcher moved." % len(tabs))
            return 2
        worst, seen_any, weak_all = [], 0, []
        for t in tabs:
            tab.ev("(function(){try{window.switchTab&&window.switchTab(%s);}catch(e){}return 1})()"
                   % json.dumps(t))
            time.sleep(0.9)
            # ⚠ PROVE THE SWITCH. Without this the probe measures one tab N times and says N.
            now = tab.ev(ACTIVE)
            if now != t:
                print("⚪ UNKNOWN — asked for tab %r, the page is showing %r." % (t, now))
                return 2
            raw = tab.ev(PROBE)
            if not raw:
                print("⚪ UNKNOWN — the probe returned nothing on tab %r" % t)
                return 2
            r = json.loads(raw)
            seen_any += r["named"]
            weak_all.extend((t, w) for w in r["weak"])
            for g in r.get("ghosted", []):
                worst.append((t, "GHOSTED (visible but aria-hidden) " + g))
            print("  %-11s %4d controls · named %4d · nameless %d · weak %d · ghosted %d"
                  % (t, r["total"], r["named"], len(r["nameless"]), len(r["weak"]),
                     len(r.get("ghosted", []))))
            for w in r["nameless"]:
                worst.append((t, w))
        if not seen_any:
            print("⚪ UNKNOWN — no named control was seen at all; the page did not boot.")
            return 2
        if worst:
            print("\n🔴 %d control(s) reach the screen without reaching a person:" % len(worst))
            for t, w in worst[:20]:
                print("     %-10s %s" % (t, w))
            return 1
        if weak_all:
            seen = set()
            print("\n⚠ %d name(s) under 3 characters — real, but they may not tell him much:"
                  % len(weak_all))
            for t, w in weak_all:
                if w not in seen:
                    seen.add(w)
                    print("     %-10s %s" % (t, w))
        print("\n🟢 every visible control across %d tabs carries a name that survives typing."
              % len(tabs))
        return 0
    finally:
        tab.close()


if __name__ == "__main__":
    sys.exit(main())
