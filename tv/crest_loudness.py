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
        t.send("Page.reload")
        # ⚠ v2424 — CALL THE HELPER THAT ALREADY EXISTS, THIRD TIME OF ASKING THIS SESSION.
        # v2422 replaced a fixed sleep(3.0) with an inline poll, which was the right idea aimed at
        # the WRONG PREDICATE. A cold review: "_selector_ready already polls, already uses 20s,
        # already swallows evaluate failures, already has FakeTab tests. It also requires a PAINTED
        # rect. This loop only asks 'is the node in the document?'"
        #
        # Two consequences, both real:
        #   · the static button carries `hidden` and still satisfies "is it in the document", so the
        #     loop could return on a node the gate is not there to measure — the LIVE crest is the
        #     one paint() un-hides (204x32).
        #   · the node is true on BOTH SIDES of the reload, so the poll could observe the PREVIOUS
        #     page and call it ready.
        #
        # ⚠ AND IT IS THE THIRD WEAKER COPY I HAVE WRITTEN TONIGHT — after _is_primary_console and
        # _decision_path. The helper built for this exact flake sits in the module this file already
        # imports. [[the-unjoined-end]] [[copy-drift]]
        why = rc._selector_ready(t, ".bd-sigil")
        if why:
            print("⚪ UNKNOWN — %s. This gate measured nothing: a page that did not paint the "
                  "crest, not a quiet crest." % why)
            return 2
        rc._settled(t)
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
