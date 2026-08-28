#!/usr/bin/env python3
"""LOOK AT THE PIXELS — the render loop, coded so it does not depend on me remembering it.

Konyo, after the third time he had to tell me something did not render: "make sure its coded as a
loop full set complete so going forward you can visually check and i dont need to keep telling you
after you say its fixed something doesnt render :)"

He is right, and the reason is not laziness — it is that every failure mode here LOOKS LIKE A PASS
unless the harness refuses. Every rule below is a mistake made in this repo, most of them today:

  ⚠ A ZERO-SIZE ELEMENT CANNOT BE CLIPPED, so "0 clipped" on a hidden panel is a FALSE GREEN.
    Measured 2026-08-28: a vault probe reported {widths:["0"], clipped:0} because the tab was never
    activated. Every card was 0x0 and the harness called it clean. Zero-size is now a REFUSAL.

  ⚠ A BLACK CAPTURE IS A REFUSAL, NOT A SCREENSHOT. Same morning: a clip of a real, populated card
    came back solid black (deviceScaleFactor/clip mismatch — chrome-cdp-mac lists two ways this
    happens). A black PNG is indistinguishable from an empty panel, so the harness measures the
    image and refuses rather than handing over a plausible rectangle.

  ⚠ LOG THE TEXT BESIDE THE CAPTURE. It is the only thing that separates "the panel is empty" from
    "my crop is wrong", and it has settled two wrong diagnoses.

  ⚠ INERT ELEMENTS ARE NOT UNREACHABLE ONES. A rect-based sweep that ignores opacity:0 /
    pointer-events:none reported 27 dead links that all worked, and later a whole "unclickable
    column" that was a closed nav panel. Reachability skips inert nodes before it complains.

  ⚠ RENDER NARROW AND BREAKPOINT-ADJACENT. A grid died at 901px — one pixel above its rule — while
    every check at 900 and 1600 stayed green for a month.

  ⚠ AND A SKIP IS NOT A PASS. No Chrome, no browser, no target found: the verdict is UNKNOWN and it
    exits non-zero. A gate that quietly does nothing is the defect this whole file is a reaction to.

Usage:
    python3 tv/render_check.py                 # every registered target
    python3 tv/render_check.py vault inbox     # just these
    python3 tv/render_check.py --list
Shots land in tv/.render_shots/ (gitignored) so a human can look at what the harness judged.
"""

import base64
import io
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# ⚠ THIS SCRIPT'S WHOLE OUTPUT IS GLYPHS (🟢 🔴 ⚠). On a non-UTF-8 console it would crash WHILE
# REPORTING — a render gate that dies mid-verdict is indistinguishable from one that found nothing,
# which is the exact false-green this file exists to refuse. Guarded by
# test_every_cli_that_prints_non_ascii_is_encoding_safe, which caught this file on its first run.
import console_safe  # noqa: F401  — imported for the side effect

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHOTS = os.path.join(HERE, ".render_shots")
PORT = int(os.environ.get("TV_RENDER_PORT", "9224"))     # never 9222 (his Chrome) or 9223 (TV)
WIDTHS = ((1440, 1000), (1120, 900), (901, 900), (375, 800))

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# A target says: how to set the board up, what to click, and what element IS the thing.
TARGETS = {
    "vault": {
        "why": "the vault shelf — his lockers, the gauge, the FULL state",
        "seed": """(function(){
            localStorage.setItem('d2r_ownerClaim','*');
            ['Windforce','Doombringer','The Grandfather','Breath of the Dying','Stormlash',
             'Bonehew','Steeldriver','Earth Shifter','Lightsabre','Tomb Reaver','Eaglehorn',
             'Widowmaker','Buriza-Do Kyanon','Gimmershred','Lacerator','Warshrike','Hellrack',
             'Silver-Edged Axe'].forEach(function(n){
                try{ window.tvVaultRegister(n); window.vaultAssign(n,'uni-weap'); }catch(e){} });
            ['Nagelring','Raven Frost','Manald Heal'].forEach(function(n){
                try{ window.tvVaultRegister(n); window.vaultAssign(n,'uni-small'); }catch(e){} });
            return 1; })()""",
        "activate": """(function(){
            var el=[].slice.call(document.querySelectorAll('.tab,[data-tab]')).filter(function(x){
              return /vault/i.test((x.getAttribute&&x.getAttribute('data-tab'))||x.textContent||'');})[0];
            if(el) el.click();
            try{ window.renderVault && window.renderVault(); }catch(e){}
            /* PROVE IT FROM THE RECT. `!!el` only said a tab element existed and was clicked —
               it would have returned true over a shelf that painted nothing, which is exactly
               how the inbox target read three 0x0 nodes as clean. A painter that ran is not a
               panel that is up. */
            var s=document.querySelector('[data-vault-mule]');
            if(!s) return false;
            var r=s.getBoundingClientRect();
            return !!(r.width>0 && r.height>0 && getComputedStyle(s).display!=='none'); })()""",
        "sel": "[data-vault-mule]",
        # ⚠ TRUNCATION THAT IS DESIGN, NOT DAMAGE — each entry needs a REASON, exactly like
        # test_reachability's ALLOWED. On its first run this harness reported 9 clipped elements
        # in the vault and every one was a name label inside a 28px D2 grid tile, where the tile
        # is identified by its ART and its tooltip and the label is deliberately cut. A gate that
        # calls a designed truncation a defect becomes furniture, which is the exact failure it
        # exists to prevent. Anything NOT on this list is still a refusal.
        "truncation_ok": {
            "vm-cell-name": "the name label inside a 10x10-grid tile — the cell is 28px by design, "
                            "the item is read from its art and its tooltip, and the full name is "
                            "in the title attribute",
        },
    },
    "taskforce": {
        "why": "the Task Force card — the mission line, the date, the DAILY PICK tag",
        "seed": """(function(){ localStorage.setItem('d2r_ownerClaim','*'); return 1; })()""",
        "activate": """(function(){
            var t=[].slice.call(document.querySelectorAll('.tab[data-tab]')).filter(function(x){
              return x.getAttribute('data-tab')==='session';})[0];
            if(t) t.click();
            var s=document.getElementById('sc-taskforce');
            if(!s) return false;
            var r=s.getBoundingClientRect();
            return !!(r.width>0 && r.height>0); })()""",
        "sel": "#sc-taskforce .sc-tf-row, #sc-taskforce > .sc-card-h",
        "truncation_ok": {
            "sc-tf-t": "the one-line mission summary, `text-overflow:ellipsis` at bible.html:8444 — "
                       "it is a headline for a card whose full text is one tap away, and it is cut "
                       "with an ellipsis rather than hard-clipped, so the cut is visible to him",
        },
    },
    "vault-full": {
        "why": "a locker packed until it is FULL — the v2216 state the other targets never reach",
        # ⚠ THIS TARGET EXISTS BECAUSE A COLD CROSS-FAMILY READ FOUND NOTHING TO READ. Asked with no
        # hint whether anything on the vault reported a capacity or a fullness, a different model
        # family answered CANNOT TELL — and it was right: the "vault" target seeds 18 weapons across
        # eleven lockers, so no locker ever fills, no gauge ever goes hot, and the entire v2216
        # subject (FULL is not 100%; fifteen 2x4 weapons sit at 120 of 140 cells) was never once on
        # screen for the gate to look at. Real data, right gate, still blind.
        # [[gate-blind-to-unexercised-input]] [[feedback-blind-fixture-green-gate]]
        "seed": """(function(){
            localStorage.setItem('d2r_ownerClaim','*');
            var W=['Windforce','Doombringer','The Grandfather','Breath of the Dying','Stormlash',
                   'Bonehew','Steeldriver','Earth Shifter','Lightsabre','Tomb Reaver','Eaglehorn',
                   'Widowmaker','Buriza-Do Kyanon','Gimmershred','Lacerator','Warshrike','Hellrack',
                   'Silver-Edged Axe','Astreon\\u2019s Iron Ward','Bloodtree Stump','Boneslayer Blade',
                   'Brainhew','Cranebeak','Death Cleaver','Demonlimb','Djinn Slayer','Doomslinger',
                   'Ethereal Edge','Executioner\\u2019s Justice','Fleshripper'];
            W.forEach(function(n){
              try{ window.tvVaultRegister(n); window.vaultAssign(n,'uni-weap'); }catch(e){} });
            return 1; })()""",
        "activate": """(function(){
            var t=[].slice.call(document.querySelectorAll('.tab[data-tab]')).filter(function(x){
              return /vault/i.test(x.getAttribute('data-tab')||'');})[0];
            if(t) t.click();
            try{ window.renderVault && window.renderVault(); }catch(e){}
            /* PROVE THE STATE, NOT JUST THE ELEMENT. A target that renders eleven cheerful
               half-empty lockers would pass every geometry check while measuring the exact
               opposite of what it exists for — which is how v2216 went unlooked-at for ten
               versions. So: at least one gauge must actually be HOT (full, or spilled onto a
               second mule), or this target refuses and says so. */
            var hot=[].slice.call(document.querySelectorAll('.vm-gauge')).filter(function(g){
              var f=g.querySelector('.vm-gauge-fill');
              var t=g.getAttribute('title')||'';
              return (f && /vg-hot/.test(f.className)) || /FULL|needs \d+ mules/.test(t);
            });
            if(!hot.length) return false;
            var r=hot[0].getBoundingClientRect();
            return !!(r.width>0 && r.height>0); })()""",
        "sel": ".vm-gauge, [data-vault-mule]",
        "truncation_ok": {
            "vm-cell-name": "the name label inside a 10x10-grid tile — the cell is 28px by design, "
                            "the item is read from its art and its tooltip, and the full name is "
                            "in the title attribute",
        },
    },
    "inbox": {
        "why": "the chronicle inbox — the rows he answers",
        "seed": """(function(){
            localStorage.setItem('d2r_ownerClaim','*');
            localStorage.setItem('d2r_chronicleInbox', JSON.stringify([
              {name:'Shadow Dancer', tier:'grail', gateHeld:true, proposedAt:1,
               gateWhy:'only 1 independent witness'},
              {name:"Razor's Edge", tier:'grail', gateHeld:true, proposedAt:2,
               gateWhy:'only 1 independent witness'}]));
            return 1; })()""",
        # ⚠ THE PAINTER IS `renderInboxFab`, AND IT IS THE ONLY ONE. The first cut of this target
        # called `renderInboxBadge` and `renderInbox` — both real functions, neither of which
        # touches the sticky. The harness then measured three nodes at 0x0 and would have called
        # the inbox clean at every width had zero-size not been a refusal. `renderInboxFab` is
        # what builds the string and hands the SAME string to both the pop-up and the sticky
        # (bible.html v1793); the sticky only takes `.has` from that call, and `.inbox-sticky`
        # without `.has` is `display:none`. So: open Sessions, paint, then PROVE it is on screen.
        "activate": """(function(){
            var t=[].slice.call(document.querySelectorAll('.tab[data-tab]')).filter(function(x){
              return x.getAttribute('data-tab')==='session';})[0];
            if(t) t.click();
            try{ window.renderInboxFab && window.renderInboxFab(); }catch(e){}
            var s=document.getElementById('inbox-sticky');
            if(!s) return false;
            /* ACTIVATION IS PROVEN, NEVER ASSUMED — a painter that ran and painted nothing
               must not read the same as a panel that is up. */
            var r=s.getBoundingClientRect();
            return !!(s.classList.contains('has') && r.width>0 && r.height>0
                      && getComputedStyle(s).display!=='none'); })()""",
        # The FAB is hidden on Sessions BY DESIGN (`body:has(#tab-session.active) .inbox-fab.has
        # {display:none}`, bible.html:8087) — asking for it here would refuse on a rule the page
        # is keeping correctly. On Sessions the sticky IS the inbox.
        "sel": "#inbox-sticky .ibp-row, #inbox-sticky .ibp-h",
    },
}


def _say(msg):
    print(msg, flush=True)


def _chrome_up():
    """A scratch Chrome on 9224+, per chrome-cdp-mac. Returns True when CDP answers."""
    import urllib.request
    try:
        urllib.request.urlopen("http://127.0.0.1:%d/json/version" % PORT, timeout=2).read()
        return True
    except Exception:
        pass
    if not os.path.exists(CHROME):
        return False
    prof = os.path.join(SHOTS, "chrome-profile")
    os.makedirs(prof, exist_ok=True)
    subprocess.Popen(
        [CHROME, "--headless=new", "--remote-debugging-port=%d" % PORT,
         "--user-data-dir=" + prof, "--no-first-run", "--no-default-browser-check",
         "--disable-gpu", "--window-size=1440,1300",
         # ⚠ WITHOUT THIS the WebSocket upgrade is refused 403 and nothing suggests a launch flag
         "--remote-allow-origins=*", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        time.sleep(0.5)
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/json/version" % PORT, timeout=2).read()
            return True
        except Exception:
            continue
    return False


class _Tab(object):
    def __init__(self, url):
        import urllib.request
        import websocket
        req = urllib.request.Request("http://127.0.0.1:%d/json/new?%s" % (PORT, url), method="PUT")
        info = json.load(urllib.request.urlopen(req))
        self.id = info["id"]
        self.ws = websocket.create_connection(info["webSocketDebuggerUrl"],
                                              origin="http://127.0.0.1:%d" % PORT)
        self.n = 0

    def send(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            r = json.loads(self.ws.recv())
            # ⚠ a native dialog blocks the renderer AND every Runtime.evaluate with it; the socket
            # just goes quiet, which reads exactly like a crashed tab
            if r.get("method") == "Page.javascriptDialogOpening":
                self.n += 1
                self.ws.send(json.dumps({"id": self.n, "method": "Page.handleJavaScriptDialog",
                                         "params": {"accept": False}}))
                continue
            if r.get("id") == self.n:
                return r.get("result", {})

    def ev(self, expr):
        return self.send("Runtime.evaluate", expression=expr, returnByValue=True,
                         awaitPromise=True).get("result", {}).get("value")

    def close(self):
        import urllib.request
        try:
            self.ws.close()
        except Exception:
            pass
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/json/close/%s" % (PORT, self.id), timeout=3)
        except Exception:
            pass


# the measurement, run inside the page. It answers about the TARGET and about the chrome over it.
_PROBE = r"""(function(sel, OK_TRUNC){
  var nodes = [].slice.call(document.querySelectorAll(sel));
  if (!nodes.length) return JSON.stringify({found:0});
  function inert(e){
    for (var n=e; n && n!==document.body; n=n.parentElement){
      var cs=getComputedStyle(n);
      if (cs.visibility==='hidden' || cs.display==='none' || parseFloat(cs.opacity)===0
          || cs.pointerEvents==='none') return true;
    }
    return false;
  }
  var rects=[], zero=0, off=0, clipped=0, covered=0, broken=0, imgs=0;
  var okTrunc=0, clippedWhat=[], coveredWhat=[];
  nodes.forEach(function(e){
    var r=e.getBoundingClientRect();
    if (r.width<1 || r.height<1) { zero++; return; }
    rects.push({w:Math.round(r.width), h:Math.round(r.height),
                x:Math.round(r.left), y:Math.round(r.top)});
    if (r.left < -1 || r.right > innerWidth+1) off++;
    [].slice.call(e.querySelectorAll('*')).forEach(function(c){
      if (c.scrollWidth > c.clientWidth+1 && getComputedStyle(c).overflow!=='visible'
          && c.clientWidth>0) {
        var cls = String(c.className||'');
        var allowed = OK_TRUNC.some(function(k){ return cls.indexOf(k) >= 0; });
        if (allowed) { okTrunc++; } else {
          clipped++;
          if (clippedWhat.length < 5) clippedWhat.push(
            (cls||c.tagName) + ' :: ' + (c.textContent||'').trim().slice(0,28));
        }
      }
    });
    [].slice.call(e.querySelectorAll('img')).forEach(function(i){
      imgs++; if (i.complete && i.naturalWidth===0) broken++;
    });
    if (!inert(e)) {
      /* ⚠ SAMPLE THE MIDDLE, NOT THE TOP EDGE, and never count PAGE CHROME as a cover. The first
         cut scrolled each card to centre and then probed 12px below its top — which lands under
         the sticky header on a scrolled page. It reported "1 covered" at every width on a vault
         that a separate probe found completely unobstructed. A sticky header over scrolled content
         is the page working; an overlay sitting on a control he needs is the defect. Only the
         second is worth his attention, and telling them apart is what stops this becoming noise.
         [[visual-regression-detector]] */
      var top=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
      if (top && !e.contains(top) && top!==e && !inert(top)) {
        var fixed=false;
        for (var q=top; q && q!==document.body; q=q.parentElement){
          var pos=getComputedStyle(q).position;
          if (pos==='fixed' || pos==='sticky') { fixed=true; break; }
        }
        if (!fixed) {
          covered++;
          if (coveredWhat.length < 3) coveredWhat.push(
            (top.className||top.tagName) + ' over ' + (e.getAttribute('data-vault-mule')||e.id||''));
        }
      }
    }
  });
  var txt = nodes.map(function(e){return (e.textContent||'');}).join(' ')
                 .replace(/\s+/g,' ').trim();
  var widths = {}; rects.forEach(function(r){ widths[r.w]=1; });
  return JSON.stringify({found:nodes.length, painted:rects.length, zero:zero, off:off,
    clipped:clipped, clippedWhat:clippedWhat, okTrunc:okTrunc,
    covered:covered, coveredWhat:coveredWhat,
    imgs:imgs, broken:broken,
    widths:Object.keys(widths).length, text:txt.slice(0,160), textLen:txt.length,
    rects:rects.slice(0,3)});
})(%s, %s)"""


def _looks_black(png_bytes, w=None, h=None):
    """Is this capture effectively blank? -> bool

    ⚠⚠ v2225 — THE BYTE THRESHOLD COULD NOT FIRE WHERE IT MATTERED. This was
    `len(png_bytes) < 3000`, and a MEASURED solid-black PNG is 4279 bytes at 1440x1000 and 3011 at
    1120x900 — both above it. So the one refusal that exists to catch "a plausible-looking empty
    image" was dead at the two widest viewports, which are exactly where his console lives. No
    sabotage in --prove covered it either, so it had never been seen fire.

    A flat image compresses in proportion to its AREA, so the floor has to scale with the area, and
    better still: look at the pixels when we can. PIL is already a dependency of vault_corpus.
    """
    n = len(png_bytes or b"")
    if not n:
        return True
    try:
        from PIL import Image
        import io as _io
        im = Image.open(_io.BytesIO(png_bytes)).convert("L")
        px = list(im.getdata())
        if not px:
            return True
        lo = sum(1 for v in px if v < 12) / float(len(px))
        rng = max(px) - min(px)
        # near-uniform and dark, or near-uniform at all: nothing was painted
        return lo > 0.995 or rng < 6
    except Exception:
        # no PIL: fall back to a floor that SCALES, since a flat PNG grows with its area
        area = (w or 1440) * (h or 1000)
        return n < max(1200, area // 240)


def _settled(tab, budget=25.0):
    """Wait until the document is COMPLETE and its size has stopped moving. Returns why, or None.

    ⚠ A FIXED SLEEP IS NOT A LOAD WAIT, and under load it silently measures a half-built page.
    This harness used `time.sleep(2.5)` and, while a 1383-test suite was saturating the CPU, read
    bible.html at **878,210 bytes of body when the finished page is 8,918,364** — one tenth. Every
    getElementById returned null. I read that as "the inbox was REMOVED from the DOM by the refresh
    I just shipped" and came within one step of publishing it as a defect.

    That is founding rule 4 — suspect the instrument first — and THE COUNT IS THE TELL: a tenth of
    a page is not a subtle discrepancy, and I should have looked at the number before the theory.

    So: readyState complete, then the body must measure the SAME SIZE TWICE in a row. A page still
    assembling grows between samples. If it never settles inside the budget the caller REFUSES with
    UNKNOWN rather than measuring — because a partial page reports zero clipping, zero overflow and
    zero covers, which is the exact false green this file exists to refuse.
    """
    t0, last = time.time(), None
    while time.time() - t0 < budget:
        raw = tab.ev("(function(){return document.readyState+'|'"
                     "+document.body.innerHTML.length+'|'"
                     "+document.querySelectorAll('.tab[data-tab]').length;})()") or ""
        parts = raw.split("|")
        if len(parts) == 3 and parts[0] == "complete" and int(parts[2] or 0) > 0:
            if last == parts[1]:
                return None
            last = parts[1]
        time.sleep(0.6)
    return ("the page never settled in %.0fs — readyState/size kept moving, so anything measured "
            "would be about a document still assembling, and a half-built page reports zero of "
            "everything" % budget)


def verdict(key, m, sel):
    """Turn ONE width's measurements into refusals. Pure — no browser, no files, no clock.

    This is a separate function ONLY so the suite can prove the refusals BEHAVIOURALLY instead of
    grepping this file for the strings. `source-reading-guard`: a guard that greps source fails on
    its own reach, and every refusal below is a sentence that also appears in a comment explaining
    it. Feed it a dict, read what comes back.

    Returns [] when the width is clean. Order matters: the first three RETURN, because a surface
    that is absent, zero-size or empty makes every later number meaningless — and a meaningless
    number that reads as 0 is the false green this whole file exists to refuse.
    """
    if not m.get("found"):
        return ["%s: selector %r matched NOTHING" % (key, sel)]
    if not m.get("painted"):
        return ["%s: every one of %d node(s) is ZERO-SIZE. A zero-size element cannot be "
                "clipped or covered, so any 'nothing wrong' below it is a false green."
                % (key, m.get("zero") or 0)]
    # ⚠ v2225 — AND A PARTIAL COLLAPSE IS THE SAME DEFECT, SMALLER. This refused only when EVERY
    # node measured 0x0, so 17 of 18 lockers collapsing returned [] and the gate exited 0 green on
    # a shelf that had lost almost everything. "Some of it painted" is not the question the gate
    # was asked. The whole-collapse case keeps its own sentence above because it is the one that
    # also invalidates every number below it.
    _zero = int(m.get("zero") or 0)
    if _zero:
        return ["%s: %d of %d node(s) are ZERO-SIZE while %d painted. A partial collapse reports "
                "zero clipping for the missing ones, so the clean numbers beside it are about the "
                "survivors only." % (key, _zero, m.get("found", 0), m.get("painted", 0))]
    out = []
    if not m.get("textLen"):
        out.append("%s: the panel painted but carries NO TEXT — that is an empty box, not a "
                   "rendered one" % key)
    for field, msg in (("off", "sit outside the viewport and cannot be reached"),
                       ("clipped", "have text cut off inside them"),
                       ("covered", "are covered by something on top"),
                       ("broken", "are images that failed to load")):
        if m.get(field):
            what = m.get(field + "What") or []
            out.append("%s: %d element(s) %s%s"
                       % (key, m[field], msg, (" — " + "; ".join(what)) if what else ""))
    return out


def check(name, spec, shots=True):
    """Render one target at every width and judge it. -> dict"""
    out = {"target": name, "why": spec["why"], "widths": {}, "ok": True, "refusals": []}
    tab = _Tab("file://" + os.path.join(REPO, "bible.html"))
    try:
        tab.send("Page.enable")
        tab.send("Runtime.enable")
        why = _settled(tab)
        if why:
            out["ok"] = False
            out["refusals"].append(why)
            return out
        tab.ev(spec["seed"])
        time.sleep(0.6)
        act = tab.ev(spec["activate"])
        if not act:
            out["ok"] = False
            out["refusals"].append("the panel could not be ACTIVATED — everything measured after "
                                   "this would be about a hidden pane, and a hidden pane reports "
                                   "zero clipping")
            return out
        time.sleep(1.4)
        for w, h in WIDTHS:
            tab.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
                     deviceScaleFactor=1, mobile=False)
            time.sleep(0.6)
            tab.ev("(function(){var e=document.querySelector(%s); if(e) "
                   "e.scrollIntoView({block:'center'}); return 1;})()" % json.dumps(spec["sel"]))
            time.sleep(0.6)
            raw = tab.ev(_PROBE % (json.dumps(spec["sel"]),
                                   json.dumps(sorted(spec.get("truncation_ok") or {}))))
            m = json.loads(raw) if raw else {"found": 0}
            key = "%dx%d" % (w, h)
            out["widths"][key] = m

            hurt = verdict(key, m, spec["sel"])
            if hurt:
                out["ok"] = False
                out["refusals"].extend(hurt)
            # the first three refusals mean every later number is meaningless — do not shoot it
            if not m.get("found") or not m.get("painted"):
                continue

            if shots:
                os.makedirs(SHOTS, exist_ok=True)
                d = tab.send("Page.captureScreenshot", format="png", captureBeyondViewport=False)
                png = base64.b64decode(d.get("data") or "")
                p = os.path.join(SHOTS, "%s_%d.png" % (name, w))
                with open(p, "wb") as fh:
                    fh.write(png)
                m["shot"] = os.path.relpath(p, REPO)
                if _looks_black(png, w, h):
                    out["ok"] = False
                    out["refusals"].append(
                        "%s: the capture is effectively BLANK (%d bytes). A black rectangle is "
                        "what a bad clip produces and it reads exactly like an empty panel — "
                        "refusing rather than handing over a plausible image." % (key, len(png)))
    finally:
        tab.close()
    return out


# ─────────────────────────────────────────────────────────────────────────────
# --prove — MAKE IT GO RED FOR ITS OWN REASON
#
# Founding rule 2: a gate that has never been seen red is measuring nothing, and this harness
# has already produced two false GREENS and two false REDS in one day. The false greens were
# the dangerous ones — three inbox nodes at 0x0 read as "clean", because a hidden pane clips
# nothing. The false reds were the ones that would have made it furniture — nine 28px grid
# labels called clipped, and page chrome called a cover at every width.
#
# So each sabotage below names the SPECIFIC field it must move. A sabotage that turns the run
# red for the WRONG reason proves nothing at all, and would be counted here as a pass.
# ─────────────────────────────────────────────────────────────────────────────
SABOTAGE = [
    ("clipped", "squeeze a real name label so its text overflows its own box",
     """(function(){var e=document.querySelector('.vm-pill,[data-vault-mule] .vm-nm,'
        + '[data-vault-mule] b, [data-vault-mule] span');
        if(!e) return 'NO ELEMENT TO SABOTAGE';
        e.textContent='A NAME FAR TOO LONG TO EVER FIT INSIDE THIS BOX AT ANY WIDTH WHATSOEVER';
        e.style.width='30px'; e.style.overflow='hidden'; e.style.whiteSpace='nowrap';
        e.style.display='block'; return 1;})()"""),
    ("covered", "drop an opaque panel over the middle of the shelf",
     """(function(){var t=document.querySelector('[data-vault-mule]');
        if(!t) return 'NO ELEMENT TO SABOTAGE';
        var r=t.getBoundingClientRect(), d=document.createElement('div');
        d.style.cssText='position:absolute;z-index:99999;background:#900;'
          + 'left:'+(r.left+window.scrollX)+'px;top:'+(r.top+window.scrollY)+'px;'
          + 'width:'+r.width+'px;height:'+r.height+'px';
        document.body.appendChild(d); return 1;})()"""),
    ("painted", "collapse the shelf to nothing — the ZERO-SIZE case that read as clean",
     """(function(){var n=document.querySelectorAll('[data-vault-mule]');
        if(!n.length) return 'NO ELEMENT TO SABOTAGE';
        [].forEach.call(n,function(e){ e.style.height='0px'; e.style.width='0px';
          e.style.overflow='hidden'; e.style.padding='0'; e.style.border='0'; });
        return 1;})()"""),
]


def prove():
    """Sabotage the vault three ways and require the harness to name each one."""
    spec = TARGETS["vault"]
    _say("PROVING THE HARNESS — three sabotages, each must move ITS OWN field.")
    _say("")
    base = check("vault", dict(spec), shots=False)
    if not base["ok"]:
        _say("🔴 the CLEAN baseline is already red — fix that first; a sabotage that changes")
        _say("   nothing proves nothing, and a baseline that is already red changes nothing.")
        return 2
    _say("   baseline: clean at %d widths" % len(base["widths"]))

    bad = 0
    for field, what, js in SABOTAGE:
        hurt = dict(spec)
        hurt["activate"] = "(function(){var a=%s; var b=%s; return a&&b;})()" % (
            spec["activate"], js)
        # the truncation allowlist must NOT excuse a sabotage — it names one class by reason
        r = check("vault", hurt, shots=False)
        moved = any((r["widths"][k].get(field, 0) or 0) > (base["widths"].get(k, {}).get(field, 0) or 0)
                    for k in r["widths"]) if field != "painted" else                 any(r["widths"][k].get("painted", 0) < base["widths"].get(k, {}).get("painted", 0)
                    for k in r["widths"])
        if moved and not r["ok"]:
            _say("   🟢 %-8s caught — %s" % (field, what))
        else:
            bad += 1
            _say("   🔴 %-8s NOT CAUGHT — %s" % (field, what))
            _say("      ok=%s  fields=%s" % (r["ok"], {k: r["widths"][k].get(field)
                                                       for k in sorted(r["widths"])}))
            for why in r["refusals"][:2]:
                _say("      it said instead: %s" % why)
    _say("")
    if bad:
        _say("🔴 %d sabotage(s) went unnoticed — this harness may not be trusted as a gate." % bad)
        return 1
    _say("🟢 every sabotage was caught, each on its own field. The gate has been seen RED.")
    return 0


def main(argv):
    want = [a for a in argv if not a.startswith("-")]
    if "--list" in argv:
        for k, v in sorted(TARGETS.items()):
            print("  %-10s %s" % (k, v["why"]))
        return 0
    try:
        import websocket  # noqa: F401
    except Exception:
        _say("⚪ UNKNOWN — the websocket client is not installed, so nothing was rendered.")
        _say("   A skip is not a pass. pip3 install websocket-client")
        return 2
    if not _chrome_up():
        _say("⚪ UNKNOWN — no headless Chrome on :%d, so NOTHING WAS LOOKED AT." % PORT)
        _say("   A skip is not a pass; this exits non-zero on purpose.")
        return 2

    if "--prove" in argv:
        return prove()

    targets = {k: v for k, v in TARGETS.items() if not want or k in want}
    if not targets:
        _say("no such target: %s (try --list)" % ", ".join(want))
        return 2

    bad = 0
    for name, spec in sorted(targets.items()):
        r = check(name, spec)
        icon = "🟢" if r["ok"] else "🔴"
        _say("%s %-8s %s" % (icon, name, r["why"]))
        for key in sorted(r["widths"]):
            m = r["widths"][key]
            _say("     %-9s painted %s/%s · clipped %s · off %s · covered %s · imgs %s/%s broken"
                 % (key, m.get("painted", 0), m.get("found", 0), m.get("clipped", 0),
                    m.get("off", 0), m.get("covered", 0), m.get("broken", 0), m.get("imgs", 0)))
            if m.get("text"):
                _say("               text: %s" % m["text"][:96])
        for why in r["refusals"]:
            _say("     ⚠ %s" % why)
        if not r["ok"]:
            bad += 1
    _say("")
    _say("shots: %s" % os.path.relpath(SHOTS, REPO))
    if bad:
        _say("🔴 %d target(s) did not render cleanly — LOOK AT THE PNGs above." % bad)
        return 1
    _say("🟢 every target rendered, at every width, with text and no clipping.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
