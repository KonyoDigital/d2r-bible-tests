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


def _shoot(tab, w, h, out_dir, tag):
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
        png = base64.b64decode(t.send("Page.captureScreenshot", format="png",
                                      captureBeyondViewport=False)["data"])
        if rc._looks_black(png):
            return None, "the %s capture came back black — a refusal, not a screenshot" % tab
        broken = t.ev("""(function(){var n=0;document.querySelectorAll('img').forEach(function(i){
            if(i.complete&&i.naturalWidth===0) n++;});return n})()""")
        if isinstance(broken, int) and broken > BROKEN_CEILING:
            return None, ("%d broken images on %s — above the %d the real page carries. The "
                          "document is not resolving its relative art; do not show this to "
                          "anyone." % (broken, tab, BROKEN_CEILING))
        p = os.path.join(out_dir, "%s_%s_%d.png" % (tag, tab, w))
        with open(p, "wb") as fh:
            fh.write(png)
        return p, "%s @%dx%d · settled in %.1fs · %s broken img" % (tab, w, h, waited, broken)
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
        for tab, w, h in (("main", 1440, 1000), ("vault", 901, 900), ("tools", 1440, 1000),
                          ("main", 375, 800)):
            p, why = _shoot(tab, w, h, out_dir, tag)
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
