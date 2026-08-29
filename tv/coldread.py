#!/usr/bin/env python3
"""RENDER A SHIPPED VERSION THE WAY HE ACTUALLY SEES IT, for the cold second-eye pass.

The push gate refuses to ship version N+1 until version N has been looked at by a different model
family. That look is only worth the gate protecting it if the pixels are the REAL pixels — and
mine were not. Two flaws, both measured on 2026-08-29:

  ⚠ RELATIVE ASSETS 404 WHEN YOU RENDER FROM SOMEWHERE ELSE. I extracted the shipped bible.html
    with `git show` into a scratch directory and rendered it there. Every `src="art/…"` in the
    page resolves against the DOCUMENT'S directory, so the whole art corpus vanished. Measured:
    50 broken images from the scratch copy against 5 from the repo, and the second eye duly
    reported a broken image in the Vault header that does not exist on his screen. I nearly
    "fixed" a file that was never missing. The document must live at the REPO ROOT so its
    relative paths mean what they mean in production. [[feedback-suspect-the-instrument]]

  ⚠ A TAB SWITCH IS A 0.28s FADE, AND 1.6s WAS NOT ENOUGH IN PRACTICE. A capture taken too early
    handed the eye a half-painted Vault: mean luminance 12.2 against 30.0 for the same panel
    settled, and 1.5% of pixels above the dark floor against 19.2%. It reads as a styling
    regression and is a stopwatch. This waits for the panel to reach full opacity and then
    measures that it did.

  ⚠ AND IT REFUSES RATHER THAN HANDING OVER A BAD FRAME. A black capture, a panel still
    transparent, or a broken-image count above the baseline all stop the run. A cold read is
    evidence; evidence taken through a broken instrument is worse than none, because the ledger
    records it as a look that happened. [[unknown-stays-unknown]]
"""
import base64
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console_safe import enable                                       # noqa: E402
import render_check as rc                                             # noqa: E402

enable(sys.stdout)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ⚠ AT THE REPO ROOT ON PURPOSE — that is the whole point. Gitignored so it can never be committed.
STAGE = os.path.join(ROOT, ".coldread.tmp.html")
SHOTS = ("main", "vault", "tools")
BROKEN_CEILING = 12          # the real page measures 5, all of them inert placeholders


def _stage(ref):
    """Write the version's bible.html to the repo root so `art/…` resolves as it does live."""
    r = subprocess.run(["git", "show", "%s:bible.html" % ref], cwd=ROOT,
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0 or not r.stdout:
        return None
    with open(STAGE, "w", encoding="utf-8") as fh:
        fh.write(r.stdout)
    return STAGE


def _shoot(tab, w, h, out_dir, tag, region=None, suffix=""):
    """Capture one tab at one width. `region` is a CSS selector to photograph on its own.

    ⚠ v2268 — WITHOUT `region` THIS HARNESS ONLY EVER SAW THE FIRST SCREEN, and four consecutive
    cold reads were "clean" about a page whose defect sat two screens below the fold. Measured on
    the vault tab: the routing ledger's first row is at y=2114 (1440x1000) and y=2719 (901x900), on
    pages 2611 and 3208 tall. A whole column of item names was truncated to as little as THREE
    PIXELS and no read could have seen it. [[gate-blind-to-unexercised-input]]

    Four things had to be true before a frame of a deep region was worth handing to anyone, and
    each one was learned by getting a wrong picture first:

      1. THE PAGE DOES NOT SCROLL under setDeviceMetricsOverride. scrollIntoView, window.scrollTo,
         documentElement.scrollTop and body.scrollTop all leave scrollY at 0 and the rect unmoved,
         even after forcing html{overflow:auto} — the emulated viewport lays the whole document out
         at once. So this is a capture problem, not a scrolling one.
      2. MEASURE AND CAPTURE IN ONE LAYOUT. Measuring in a 1000px viewport and then capturing with
         captureBeyondViewport reflows the page and the crop lands ~2000px off. Grow the viewport
         FIRST, then measure.
      3. OPEN WHAT IS CLOSED — and a `.collapsed` class is not the only way to be closed. The
         routing ledger lives inside a <details> that ships shut, and a child of a closed <details>
         reports its FULL height from getBoundingClientRect while nothing paints. That rect is a lie
         about visibility, and it produced a crop of a heading over blank space which I then read as
         "the panel is collapsed" and nearly retracted a correct diagnosis over.
      4. REFUSE IF THE REGION IS EMPTY. A picture of a card with no rows in it, labelled with the
         card's name, is exactly the false evidence this whole lane exists to prevent — the eye read
         four item names off one and called them complete. [[feedback-suspect-the-instrument]]"""
    t = rc._Tab("file://" + STAGE)
    try:
        t.send("Page.enable")
        t.send("Runtime.enable")
        t.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
               deviceScaleFactor=1, mobile=False)
        time.sleep(4.0)
        t.ev("(function(){document.documentElement.style.scrollBehavior='auto';"
             "try{window.switchTab&&window.switchTab(%s)}catch(e){}return 1})()" % json.dumps(tab))
        # WAIT FOR THE FADE TO FINISH, then say so — never assume a fixed sleep was enough
        # ⚠ WAIT FOR THE PAGE TO FINISH BOOTING FIRST. bible.html is ~6 MB; under load a switch
        # fired too early is undone by late initialisation, and the panel restarts its fade. That
        # produced a refusal reading opacity '0.01' held across the whole budget on a page that
        # measures perfectly when asked on its own. The refusal was right to fire and the cause was
        # the harness rushing it. [[feedback-suspect-the-instrument]]
        for _ in range(20):
            if t.ev("(function(){return document.readyState})()") == "complete":
                break
            time.sleep(0.5)
        # ⚠ PROVE THE TAB IS THE ONE WE ASKED FOR, BEFORE TIMING ITS FADE. The refusal kept
        # reporting opacity '0.01' for the whole budget — which is not a fade IN sampled early, it
        # is a panel fading OUT. The page restores its last-used tab from localStorage on boot, so
        # on a profile that has been driven around (mine, after a night of repros) the restore and
        # this switch fight each other and the requested panel is on its way out.
        # Waiting on opacity alone could never see that; it just timed a losing race.
        for _ in range(20):
            active = t.ev("(function(){var a=document.querySelector('button.tab.active[data-tab]');"
                          "return a?a.dataset.tab:''})()")
            if active == tab:
                break
            t.ev("(function(){try{window.switchTab&&window.switchTab(%s)}catch(e){}return 1})()"
                 % json.dumps(tab))
            time.sleep(0.5)
        else:
            return None, "tab %r never became the active tab — the page kept restoring %r" % (tab, active)
        settled, waited, saw, stable = False, 0.0, "never sampled", 0
        while waited < 20.0:
            time.sleep(0.5)
            waited += 0.5
            op = t.ev("(function(){var p=document.getElementById('tab-%s');"
                      "if(!p) return 'no-panel';"
                      "return String(getComputedStyle(p).opacity)})()" % tab)
            saw = repr(op)
            # ⚠ SAY WHAT YOU SAW. The first cut compared to "1" and, when it refused, reported only
            # "never reached full opacity" — which reads as a page defect. It was not: a direct
            # measurement showed every panel at opacity 1 on both versions. A refusal that cannot
            # name its observation is indistinguishable from the fault it claims to have found.
            # 'no-panel' is a PASS: not every tab id is `tab-<name>`, and a tab with no panel of
            # that id has no fade to wait for. [[unknown-stays-unknown]]
            # ⚠ TWO CONSECUTIVE READS. One sample of "1" can land in a gap between a re-render
            # and the fade it restarts, which is how a half-painted panel got captured before.
            if op in ("1", "no-panel", 1):
                stable += 1
                if stable >= 2:
                    settled = True
                    break
            else:
                stable = 0
                # re-assert the tab: a late re-render can drop it back, and asking again is free
                t.ev("(function(){try{window.switchTab&&window.switchTab(%s)}catch(e){}return 1})()"
                     % json.dumps(tab))
        if not settled:
            return None, ("tab %r never reached full opacity in %.0fs — last saw %s"
                          % (tab, waited, saw))
        crop_box = None
        if region:
            opened = t.ev("""(function(){var e=document.querySelector(%s);
                if(!e) return 'absent';
                var n=0;
                for(var p=e;p&&p!==document.body;p=p.parentElement){
                  if(p.tagName==='DETAILS' && !p.open){ p.open=true; n++; }
                  if(p.classList && p.classList.contains('collapsed')){
                    if(p.id && typeof window.toggleCardCollapse==='function'){
                      try{ window.toggleCardCollapse(p.id); }catch(err){ p.classList.remove('collapsed'); }
                    } else { p.classList.remove('collapsed'); }
                    n++; }}
                return String(n);})()""" % json.dumps(region))
            if opened == "absent":
                return None, "%s: %r is not on this page, so there is nothing to look at" % (tab, region)
            time.sleep(1.2)
            page_h = t.ev("(function(){return String(Math.min(12000,"
                          "document.documentElement.scrollHeight))})()")
            try:
                t.send("Emulation.setDeviceMetricsOverride", width=w, height=int(page_h),
                       deviceScaleFactor=1, mobile=False)
            except (TypeError, ValueError):
                return None, "%s: could not grow the viewport to reach %r" % (tab, region)
            time.sleep(1.2)
            meas = t.ev("""(function(){var e=document.querySelector(%s);
                if(!e) return 'absent';
                var r=e.getBoundingClientRect();
                return [Math.round(r.left),Math.round(r.top+(window.scrollY||0)),
                        Math.round(r.width),Math.round(r.height),
                        e.querySelectorAll('.vrg-row,tr,li').length].join(',');})()""" % json.dumps(region))
            try:
                bx, by, bw, bh, rows_n = [int(v) for v in str(meas).split(",")]
            except (TypeError, ValueError):
                return None, "%s: could not locate %r after the viewport grew" % (tab, region)
            if rows_n < 1:
                return None, ("%s: %r rendered NO rows, so the frame would show an empty card and "
                              "prove nothing. A skip is not a pass." % (tab, region))
            if bw < 40 or bh < 40:
                return None, ("%s: %r measures %dx%d — too small to be the surface it names"
                              % (tab, region, bw, bh))
            crop_box = (bx, by, bw, bh, rows_n)
        png = base64.b64decode(t.send("Page.captureScreenshot", format="png",
                                      captureBeyondViewport=False)["data"])
        if rc._looks_black(png):
            return None, "the %s capture came back black — a refusal, not a screenshot" % tab
        if crop_box:
            bx, by, bw, bh, rows_n = crop_box
            try:
                from PIL import Image
                import io as _io
                im = Image.open(_io.BytesIO(png))
                pad = 12
                cut = im.crop((max(0, bx - pad), max(0, by - pad),
                               min(im.width, bx + bw + pad), min(im.height, by + bh + pad)))
                if cut.width < 40 or cut.height < 40:
                    return None, ("%s: the crop of %r came out %dx%d — the region is not inside the "
                                  "captured page" % (tab, region, cut.width, cut.height))
                buf = _io.BytesIO(); cut.save(buf, format="PNG"); png = buf.getvalue()
            except ImportError:
                return None, ("%s: Pillow is missing, so a below-the-fold region cannot be cut out. "
                              "A skip is not a pass." % tab)
            if rc._looks_black(png):
                return None, "the %s %r crop came back black — a refusal" % (tab, region)
        broken = t.ev("""(function(){var n=0;document.querySelectorAll('img').forEach(function(i){
            if(i.complete&&i.naturalWidth===0) n++;});return n})()""")
        if isinstance(broken, int) and broken > BROKEN_CEILING:
            return None, ("%d broken images on %s — above the %d the real page carries. The "
                          "document is not resolving its relative art; do not show this to "
                          "anyone." % (broken, tab, BROKEN_CEILING))
        p = os.path.join(out_dir, "%s_%s%s_%d.png" % (tag, tab, suffix, w))
        with open(p, "wb") as fh:
            fh.write(png)
        return p, ("%s%s @%dx%d · settled in %.1fs · %s broken img%s"
                   % (tab, suffix, w, h, waited, broken,
                      (" · %d rows in %s" % (crop_box[4], region)) if crop_box else ""))
    finally:
        t.close()


def main(argv):
    ref = argv[1] if len(argv) > 1 else "origin/main"
    out_dir = argv[2] if len(argv) > 2 else os.path.join(ROOT, "tv", ".render_shots")
    os.makedirs(out_dir, exist_ok=True)
    if not rc._chrome_up():
        print("⚪ UNKNOWN — no Chrome on :%d. A skip is not a pass." % rc.PORT)
        return 2
    if not _stage(ref):
        print("⚪ UNKNOWN — could not read bible.html at %r" % ref)
        return 2
    try:
        # ⚠ READ THE WHOLE FILE. console_doctor._tree_version already paid for this: a first cut
        # read 400KB and returned None because D2R_BUILD sits ~1.1MB into a 5.8MB file. I capped
        # at 2MB and still got "unknown", so the stamp has moved again — a bound chosen once is a
        # bound that goes stale. There is no reason to bound it at all.
        with open(STAGE, encoding="utf-8") as fh:
            head = fh.read()
        import re
        m = re.search(r"D2R_BUILD\s*=\s*\{\s*id:'(v\d+)'", head)
        tag = m.group(1) if m else "unknown"
        print("staged %s as %s (at the repo root, so art/ resolves)" % (ref, tag))
        made, failed = [], []
        # (tab, width, height, region-selector, filename suffix)
        for tab, w, h, region, sfx in (
                ("main",  1440, 1000, None, ""),
                ("vault",  901,  900, None, ""),
                ("tools", 1440, 1000, None, ""),
                ("main",   375,  800, None, ""),
                # v2268 — the surfaces BELOW THE FOLD, which no cold read could reach until now
                ("vault", 1440, 1000, ".vrg-cols", "-ledger"),
                ("vault",  901,  900, ".vrg-cols", "-ledger")):
            p, why = _shoot(tab, w, h, out_dir, tag, region, sfx)
            print(("  ✓ " if p else "  ✗ ") + why)
            (made if p else failed).append(p or why)
        if failed:
            print("\n🔴 %d capture(s) refused — nothing here is fit to hand to a second eye."
                  % len(failed))
            return 1
        print("\n🟢 %d captures of %s, each settled and asset-complete:" % (len(made), tag))
        for p in made:
            print("     " + p)
        return 0
    finally:
        try:
            os.remove(STAGE)
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
