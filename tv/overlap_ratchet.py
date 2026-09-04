#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TEXT SITTING ON TEXT — the class the render gate cannot see.

⚠⚠ WHY THIS EXISTS. `render_check` measures whether an element is CLIPPED, OFF-SCREEN or COVERED.
None of those catches two labels drawn on top of each other: both are fully on screen, neither is
clipped, and the pixels are a mess. Measured 2026-09-04 at 375x800 — a width the render gate
already renders and reports as *"no clipping"*:

    375x800    50 text leaves    24 overlapping pairs
    1120x900   53 text leaves     2 overlapping pairs

A cold cross-family look at the same PNG found it unprompted — *"'AI READS · LIVE' overlaps the
partial text 'appea here'… ':17772' and ':17771' colliding with 'MILLENIUM', 'heart', and
'AGENT'"* — and the gate had just called that width green. **He must not be the detector, and
today neither was the gate.** [[visual-regression-detector]]

⚠⚠ IT IS A RATCHET, NOT A PASS/FAIL, AND THAT IS DELIBERATE. There are 24 overlaps at 375px today.
A check that failed on all of them would be red from birth, and a gate that is red on arrival gets
switched off or re-baselined without being read — which is precisely how the swallow ratchet one
file over came to be cleared by `--write-baseline` instead of by fixing anything. So: the debt is
RECORDED per target per width, a RISE fails, and a FALL fails too until it is blessed deliberately.
An exact-match baseline has no slack for a new overlap to hide in.

⚠ 2 OVERLAPS AT 1120 ARE IN THE BASELINE AND ARE NOT ASSUMED HARMLESS. Nobody has read them yet.
They are debt, recorded as debt, and the ratchet stops them growing — calling them "fine" would be
a verdict nobody earned. [[unknown-stays-unknown]]

    python3 tv/overlap_ratchet.py              # measure and print
    python3 tv/overlap_ratchet.py --check      # grade against the baseline (the gate)
    python3 tv/overlap_ratchet.py --write-baseline
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

REPO = os.path.dirname(HERE)
BASELINE = os.path.join(REPO, "baseline", "overlap_baseline.json")

#: the widths this asks about. The narrow one is the point — layout dies at breakpoints, and
#: [[workflow-topology]]'s render rule says include 375.
WIDTHS = ((375, 800), (901, 900), (1120, 900), (1440, 1000))

#: minimum overlap in BOTH axes before two boxes count as colliding. A 1-2px kiss is antialiasing
#: and letter-spacing, not two labels on top of each other; measured, 3px removes those without
#: hiding any of the 24 real ones at 375.
MIN_OVERLAP_PX = 3

_JS = """(() => {
  const leaves = [...document.querySelectorAll('*')].filter(e => {
    const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    return e.children.length === 0 && (e.textContent || '').trim()
           && r.width > 4 && r.height > 4
           && cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0'
           && r.top < innerHeight && r.bottom > 0;
  });
  const pairs = [];
  for (let i = 0; i < leaves.length; i++) {
    for (let j = i + 1; j < leaves.length; j++) {
      const a = leaves[i].getBoundingClientRect(), b = leaves[j].getBoundingClientRect();
      const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (ox > __MIN__ && oy > __MIN__) {
        pairs.push({a: (leaves[i].textContent || '').trim().slice(0, 26),
                    b: (leaves[j].textContent || '').trim().slice(0, 26),
                    ox: Math.round(ox), oy: Math.round(oy)});
      }
    }
  }
  return {leaves: leaves.length, count: pairs.length, sample: pairs.slice(0, 8)};
})()"""


def measure(page=None, widths=WIDTHS):
    """-> ({("%dx%d" % w): {...}}, why). `why` non-empty means NOTHING was established."""
    import time
    try:
        import render_check as RC
    except Exception as e:
        return None, "render_check would not import (%s)" % str(e)[:70]
    if not RC._chrome_up():
        return None, "headless chrome would not start, so no width was measured"
    url = "file://" + (page or os.path.join(HERE, "control_ui.html"))
    out = {}
    try:
        tab = RC._Tab(url)
    except Exception as e:
        return None, "could not open the page (%s)" % str(e)[:70]
    for w, h in widths:
        try:
            tab.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
                     deviceScaleFactor=1, mobile=False)
            # ⚠ RELOAD AT EACH WIDTH. Measuring four widths in sequence on one tab grades 1440 on
            # a layout that has just been squeezed to 375 and back: scroll position persists,
            # anything that collapsed stays collapsed, and a resize reflow is not a first paint.
            # Each width is now graded as a user opening AT that width sees it.
            #
            # ⚠⚠ AND THE HONEST FOOTNOTE, because the tempting version of this comment is wrong:
            # THIS CHANGED NOTHING. Measured both ways — 2 / 3 / 24 / 3, identical, and identical
            # across three consecutive sequenced runs before that. I added the reload suspecting
            # the sequenced numbers were an artifact and they were not. It stays because grading a
            # first paint is the right thing to measure, NOT because it fixed a defect, and
            # writing it up as a fix would have put a discovery in the log that never happened.
            # [[feedback-suspect-the-instrument]]
            tab.send("Page.navigate", url=url)
            time.sleep(2.5)
            r = tab.send("Runtime.evaluate",
                         expression=_JS.replace("__MIN__", str(MIN_OVERLAP_PX)),
                         returnByValue=True)
            v = (r.get("result") or {}).get("value")
            if not isinstance(v, dict):
                return None, "the page returned no measurement at %dx%d" % (w, h)
            out["%dx%d" % (w, h)] = v
        except Exception as e:
            # ⚠ ONE WIDTH THAT COULD NOT BE ASKED MAKES THE WHOLE RUN UNKNOWN. A partial run
            # graded against a full baseline would read every unmeasured width as zero.
            return None, "%dx%d could not be measured (%s)" % (w, h, str(e)[:60])
    return out, ""


def _baseline():
    try:
        with io.open(BASELINE, encoding="utf-8") as fh:
            return json.load(fh) or {}, ""
    except FileNotFoundError:
        return None, "no baseline at %s — this gate is UNCONFIGURED, not clean" % BASELINE
    except Exception as e:
        return None, "the baseline would not parse (%s) — refusing to grade against it" % e


def write_baseline():
    got, why = measure()
    if got is None:
        print("🔴 %s" % why)
        return 1
    os.makedirs(os.path.dirname(BASELINE), exist_ok=True)
    with io.open(BASELINE, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "_why": "TEXT-ON-TEXT overlaps per width. A rise FAILS; a fall also fails until it is "
                    "blessed here deliberately, so there is no slack for a new overlap to hide "
                    "in. These are DEBT, not a clean bill: nobody has read them.",
            "counts": {k: v["count"] for k, v in sorted(got.items())}}, indent=2, sort_keys=True))
        fh.write("\n")
    print("wrote %s" % BASELINE)
    for k, v in sorted(got.items()):
        print("   %-10s %d overlap(s) across %d text leaf/leaves" % (k, v["count"], v["leaves"]))
    return 0


def check():
    was, why = _baseline()
    if was is None:
        print("🔴 %s" % why)
        print("   run:  python3 tv/overlap_ratchet.py --write-baseline")
        return 1
    got, mwhy = measure()
    if got is None:
        # ⚠ UNKNOWN IS NOT A PASS. Nothing was measured, so nothing may be reported clean.
        print("⚪ UNKNOWN — %s. Nothing was established, which is not the same as no overlaps."
              % mwhy)
        return 1
    old = was.get("counts") or {}
    print("text-on-text overlap ratchet")
    bad = []
    for k in sorted(set(list(old) + list(got))):
        now = (got.get(k) or {}).get("count")
        then = old.get(k)
        if now is None:
            bad.append("%s was in the baseline and was NOT measured" % k)
            continue
        if not isinstance(then, int):
            bad.append("%s has no recorded baseline (%r) — MALFORMED, not a count of zero"
                       % (k, then))
            continue
        flag = "" if now == then else ("  🔴 ROSE +%d" % (now - then) if now > then
                                       else "  🟡 fell -%d" % (then - now))
        print("   %-10s baseline %-3d now %-3d%s" % (k, then, now, flag))
        if now != then:
            bad.append("%s: %d -> %d" % (k, then, now))
            for pr in (got.get(k) or {}).get("sample") or []:
                print("        %r over %r  (%dx%d px)" % (pr["a"], pr["b"], pr["ox"], pr["oy"]))
    if bad:
        print()
        print("🔴 the overlap count moved: %s" % "; ".join(bad))
        print("   A RISE is new text drawn on top of other text — no clipping check can see it.")
        print("   A FALL is good and still fails, so the win is recorded rather than absorbed:")
        print("       python3 tv/overlap_ratchet.py --write-baseline")
        return 1
    print("✅ held.")
    return 0


def main(argv):
    if "--write-baseline" in argv:
        return write_baseline()
    if "--check" in argv:
        return check()
    got, why = measure()
    if got is None:
        print("⚪ UNKNOWN — %s" % why)
        return 1
    print("\nTEXT-ON-TEXT OVERLAPS — the class a clipping check cannot see\n")
    for k, v in sorted(got.items()):
        print("  %-10s %3d overlap(s)   across %d text leaf/leaves" % (k, v["count"], v["leaves"]))
        for pr in (v.get("sample") or [])[:3]:
            print("       %r over %r  (%dx%d px)" % (pr["a"], pr["b"], pr["ox"], pr["oy"]))
    print()
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
