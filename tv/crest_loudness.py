#!/usr/bin/env python3
"""THE INSTALL CREST IS NEVER THE LOUDEST THING ON THE BOARD.

v2294. The crest says WHICH MACHINE this is. It is not news, it is not an alert, and it must never
out-shout what he is supposed to do next — his own ruling about the hunt was that it should be
optimised "as priority as first visual render".

Measured, not asserted: every element above the fold is ranked by the SHARE of its pixels that are
saturated. Density is the right property and it took three tries to get there — ranking by
mean-chroma x sqrt(area), and then by saturated-pixel COUNT, both simply elected the page's largest
containers. A 20x20 pill that is 92% saturated pops out of a dark page; a 1.2Mpx grid that is 1%
saturated does not. [[feedback-suspect-the-instrument]]

⚠ A CDP probe is a GUEST world (navigator.webdriver + file:), which boots with seeds suppressed, so
this claims ownership first — otherwise it measures an empty state he never sees.
[[cdp-probe-reads-a-guest-world]]

⚠ NO CHROME IS **UNKNOWN**, NEVER A PASS. Exit 2 says nobody looked. [[unknown-stays-unknown]]
"""
import base64, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable                                      # noqa: E402
enable(sys.stdout)   # this file reports in 🔴/🟢/⚪; a non-UTF-8 console must not crash the VERDICT
ROOT = os.path.dirname(HERE)

URL = "file://" + os.path.join(ROOT, "bible.html")
W, H = 1440, 1000
CREST = ("#bs-glyph", ".bs-glyph", ".bd-sigil", "#bs-name")


def _rank(tab, img):
    rects = json.loads(tab.ev("""(function(){
      var out=[], all=document.querySelectorAll('body *');
      for (var i=0;i<all.length;i++){
        var e=all[i], r=e.getBoundingClientRect();
        if (r.top>%d || r.bottom<0 || r.width<12 || r.height<8) continue;
        var cs=getComputedStyle(e);
        if (cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0) continue;
        var _c=e.getAttribute('class')||'';   // .className on an SVG node is an object, not a string
        out.push({sel:(e.id?('#'+e.id):(_c?('.'+_c.trim().split(/\\s+/)[0]):('<'+e.tagName.toLowerCase()+'>'))),
                  x:Math.round(r.left),y:Math.round(r.top),
                  w:Math.round(r.width),h:Math.round(r.height)});
      }
      return JSON.stringify(out);
    })()""" % H) or "[]")
    iw, ih = img.size
    scored = []
    for r in rects:
        x0, y0 = max(0, r["x"]), max(0, r["y"])
        x1, y1 = min(iw, r["x"] + r["w"]), min(ih, r["y"] + r["h"])
        if x1 <= x0 or y1 <= y0:
            continue
        px = list(img.crop((x0, y0, x1, y1)).getdata())
        if not px:
            continue
        hot = sum(1 for p in px if (max(p) - min(p)) >= 60 and max(p) >= 120)
        scored.append((hot / float(len(px)), r["sel"]))
    scored.sort(key=lambda z: -z[0])
    return scored


def main():
    try:
        import render_check as rc
        from PIL import Image
    except Exception as e:
        print("⚪ UNKNOWN — cannot load the harness: %s" % str(e)[:90])
        return 2
    if not rc._chrome_up():
        print("⚪ UNKNOWN — no Chrome on :%d. A skip is not a pass." % rc.PORT)
        return 2
    t = rc._Tab(URL)
    try:
        t.send("Emulation.setDeviceMetricsOverride", width=W, height=H,
               deviceScaleFactor=1, mobile=False)
        t.ev("try{localStorage.setItem('d2r_ownerClaim','*')}catch(e){}")
        # ⚠ v2426 — THE RELOAD WAS FIRE-AND-FORGET, AND v2424's MESSAGE CLAIMED OTHERWISE.
        # Swapping an inline poll for `_selector_ready` fixed the HIDDEN-NODE predicate and did
        # nothing about the reload: `.bd-sigil` is true on BOTH sides of it, so any wait can be
        # satisfied by the document the reload was meant to replace. A cold read put it plainly —
        # "replacing the poll does not replace a load wait" — and I had said it did.
        #
        # Other CDP callers in this tree (render_check.check, coldread, a11y_check) enable page
        # events and wait for the load. This one did not. Waiting for a NEW document id is the
        # cheapest honest join: the old page cannot satisfy it.
        # ⚠ v2428 — AND `Page.enable` DOES NOT MAKE THIS A LOAD WAIT. A cold review: `_Tab.send`
        # reads until its OWN command id and discards everything else, so `frameNavigated` and
        # `loadEventFired` are generated and thrown away. Nobody in this tree waits on CDP page
        # events. v2426's message said page events were enabled "so nothing can wait on it"
        # otherwise — implying they are what waits. They are not. The JS clock check below is the
        # whole wait, and it should be described as such.
        #
        # The enable is kept ONLY because it makes _Tab's javascriptDialogOpening handler live,
        # which is worth having and is a different benefit entirely.
        try:
            t.send("Page.enable")
        except Exception:
            pass
        # ⚠ SEPARATE try, BECAUSE SHARING ONE DISABLED THE ONLY CHECK. Previously the enable and
        # this sample sat in one block: an enable failure set `_before = None` and silently skipped
        # the new-document test entirely. One failure must not disarm an unrelated guard.
        try:
            _before = float(t.ev("String(performance.now())"))
        except Exception:
            _before = None
        t.send("Page.reload")
        # performance.now() restarts at ~0 on a real navigation, so a value BELOW the pre-reload
        # reading is evidence THIS is a new document. It is a proxy and it is named as one.
        _fresh = None
        if _before is not None:
            _dl = time.time() + 20.0
            _err = 0
            while time.time() < _dl:
                try:
                    if float(t.ev("String(performance.now())")) < _before:
                        _fresh = True
                        break
                except Exception:
                    _err += 1
                time.sleep(0.1)
            else:
                _fresh = False
            # ⚠ A SILENT CDP DEATH USED TO LOOK LIKE A PATIENT WAIT. Every tick swallowed its
            # exception, so twenty seconds of a dead connection ended in the same "timed out" state
            # as a page that simply had not navigated — and then proceeded to score it.
            if _err and _fresh is not True:
                print("⚪ UNKNOWN — the page never reported a new document and the probe raised %d "
                      "time(s); this gate measured nothing." % _err)
                return 2
        if _fresh is False:
            # ⚠ AND PROCEEDING ANYWAY WAS THE DEFECT. The budget expiring means the capture would
            # be of the document the reload was meant to replace — which is precisely the thing
            # this wait exists to prevent. Refusing is the only honest end. [[unknown-stays-unknown]]
            print("⚪ UNKNOWN — no new document within 20s of the reload, so a capture here would "
                  "be the page the reload was meant to replace. This gate measured nothing.")
            return 2
        why = rc._selector_ready(t, ".bd-sigil")
        if why:
            # ⚠ DO NOT QUOTE THE HELPER'S `why` VERBATIM HERE. It ends "...after the panel was
            # activated", which is true for render_check's targets and FALSE for this gate — it
            # activates nothing. Quoting it imports a cause this path does not have, which is a
            # miss painted as a fact. Say what THIS gate knows. [[label-outlived-referent]]
            print("⚪ UNKNOWN — no PAINTED .bd-sigil within the wait, so this gate measured "
                  "nothing. That is a page that did not paint the crest, not a quiet crest. "
                  "(probe detail: %s)" % str(why).split(" after ")[0])
            return 2
        # ⚠ _settled's ANSWER WAS THROWN AWAY. `check()` in render_check REFUSES on it; here the
        # page could fail to settle and be screenshotted anyway — a half-built page, scored.
        _unsettled = rc._settled(t)
        if _unsettled:
            print("⚪ UNKNOWN — the page never settled (%s), so this gate measured a page still "
                  "assembling." % str(_unsettled)[:90])
            return 2
        data = t.send("Page.captureScreenshot", format="png",
                      captureBeyondViewport=False).get("data")
        p = os.path.join(HERE, ".render_shots", "crest_loudness.png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(base64.b64decode(data))
        img = Image.open(p).convert("RGB")
        scored = _rank(t, img)
        if not scored:
            print("⚪ UNKNOWN — nothing above the fold could be measured")
            return 2
        print("── loudest above the fold, by saturated-pixel share ──")
        for d, sel in scored[:6]:
            print("   %5.1f%%  %s" % (100 * d, sel))
        top = scored[0][1]
        rank = next((i for i, (_, s) in enumerate(scored) if s in CREST), None)
        if top in CREST:
            print()
            print("🔴 THE INSTALL CREST IS THE LOUDEST THING ON THE BOARD (%s at %.1f%%)."
                  % (top, 100 * scored[0][0]))
            print("   It says which machine this is. It must never out-shout the hunt.")
            return 1
        where = ("#%d" % (rank + 1)) if rank is not None else "not in the ranking"
        print()
        print("🟢 the crest is %s, behind %s — identity is quiet, and its hue is untouched."
              % (where, scored[0][1]))
        return 0
    finally:
        t.close()


if __name__ == "__main__":
    sys.exit(main())
