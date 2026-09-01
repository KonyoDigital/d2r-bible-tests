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
    # ══ v2379 — THE CONSOLE ITSELF, WHICH THIS GATE HAD NEVER LOOKED AT ═══════════════════════
    # Konyo: "skills loaded? how come you didnt use our visual harness gate? you should have
    # caught this already 3 times back.." He is right, and the reason is measurable rather than
    # forgetful: every target here rendered bible.html, and every control he has gone looking for
    # — MINI, MINI(AUTOMATIC), the farm gate, the lamps — lives in tv/control_ui.html. Five
    # targets, zero coverage of that file. The gate could not have caught it.
    #
    # This target asserts the CONTROLS HE REACHES FOR ARE ON SCREEN AND NOT BURIED. It is not a
    # prettiness check: `sel` names the action row, so a control that gets moved back inside a
    # collapsed <details> stops being painted here and the gate says so.
    "console": {
        "page": os.path.join("tv", "control_ui.html"),
        "why": "the CONSOLE's own action row — the buttons he actually reaches for",
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            var b = document.getElementById('btn-miniauto');
            if (!b) return false;
            // it must not be inside a COLLAPSED details — that is how it hid for three rounds
            for (var q = b.parentElement; q; q = q.parentElement){
                if (q.tagName === 'DETAILS' && !q.open) return false;
            }
            var r = b.getBoundingClientRect();
            return !!(r.width > 2 && r.height > 2); })()""",
        "sel": "#btn-mini, #btn-miniauto",
        "settles": False,   # a live console never stops moving; see the note at the settle call
    },
    "state-panel": {
        "serve": True,
        "why": "THE STATE OF THIS CONSOLE — the ⟳ CHECK NOW control, the four sections, and the "
               "DISK row that must carry its own age. This panel is fed entirely by /api/status, so "
               "file:// could never render it: until v2401 it had NO gate coverage at all, and v2400 "
               "shipped a change to it verified only by a by-hand CDP run",
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            /* ⚠ CLICK THE ELEMENT, DO NOT CALL THE FUNCTION. A first cut called thShelf() and
               _verXrefOpen() by name; both live inside a closure and are `undefined` on window, so
               the activate returned false while the panel was perfectly openable. Measured on a
               served console 2026-09-01. Drive the UI the way he does. */
            var f = document.getElementById('foot-ver');
            if (!f) return false;
            f.click();
            var ov = document.getElementById('ver-xref');
            if (!ov || ov.hidden) return false;
            /* PROVE IT FROM THE RECT — a painter that ran and painted nothing must never read the
               same as a panel that is up. And require the SECTIONS, because an overlay with a
               frame and no content is the empty-box defect an author cannot see. */
            var r = ov.getBoundingClientRect();
            var secs = ov.querySelectorAll('.vx-h').length;
            return !!(r.width > 2 && r.height > 2 && secs >= 4
                      && getComputedStyle(ov).display !== 'none'); })()""",
        "sel": "#ver-xref .vx-row, #ver-xref .vx-h",
        "settles": False,
        "warmup": 10.0,     # it has to fetch /api/status before there is a panel to open
    },

    # ⚠ WHY THE CONSOLE'S DATA-DRIVEN SURFACES ARE NOT TARGETS HERE, AND IT IS A GAP, NOT A CHOICE.
    # This harness loads `file://` (see _Tab below). That is right for bible.html, which builds
    # itself out of localStorage — every target above seeds a store and the page renders. It cannot
    # work for the console's own panels: THE SHELF, the pipeline board, THE FLEET and the stat strip
    # are all filled from /api/sessions and /api/status, so under file:// they render "Loading
    # runs…" and nothing else. A target for them would refuse on EVERY run, and a gate that can
    # only ever be red is switched off inside a week — the same defect as one that is green forever.
    #
    # MEASURED 2026-09-01 while adding targets for gh #207: a `tvd` target was written, ran, and
    # correctly refused with "the panel could not be ACTIVATED". The refusal was the harness working;
    # the target was the mistake.
    #
    # So those surfaces are covered by driving a PRIVATE console over http on an ephemeral port
    # (never :17772) with CDP, which is what verified task 143 on real pixels. Closing this gap
    # properly means teaching this harness an optional http origin per target — filed, not faked.
    # A surface with no target is UNMEASURED, and unmeasured must never read as clean.
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


_CHROME_PROC = None          # set ONLY when this process spawned it — see _chrome_down


def _chrome_down():
    """Kill the scratch Chrome THIS process started. Never one it merely found.

    ⚠ v2369 — THIS IS WHERE HIS MAC GOT HOT, TWICE. `_chrome_up` did a bare `subprocess.Popen`
    and returned; nothing kept the handle, so when the python exited the browser was reparented
    to init and ran forever. Measured on 2026-09-01: FOUR orphaned headless Chromes, one alive
    for **1 day 11 hours**, another 15h47m, each holding a throwaway /var/folders profile. He
    told me his machine was hot and it was mine. `console_doctor` records the same class before:
    eight chrome-headless-shell processes found one morning.

    ⚠ IT MUST ONLY KILL WHAT IT SPAWNED. `_chrome_up` returns True early when something is
    already listening on the port, and that something may not be ours — killing a browser we
    merely found is how a gate takes down the thing it was measuring. `_CHROME_PROC` is set on
    the spawn path alone, so a found-not-started Chrome is left exactly where it was.

    By PID, through the handle we hold. Never by name: `pkill -f` cannot tell his Chrome from a
    scratch one. [[process-port-discipline]]
    """
    global _CHROME_PROC
    p, _CHROME_PROC = _CHROME_PROC, None
    if p is None:
        return False
    try:
        if p.poll() is None:
            p.kill()
        try:
            p.wait(timeout=5)
        except Exception:
            # a child that outlived its kill deadline is reaped off-thread rather than left
            # <defunct> — the same mistake REG-432 fixed elsewhere in this tree
            import threading
            threading.Thread(target=(lambda pr: pr.wait()), args=(p,), daemon=True).start()
        return True
    except Exception:
        return False


try:
    import atexit as _atexit
    _atexit.register(_chrome_down)          # backstop only: a KILLED parent never runs atexit,
except Exception:                           # which is why the caller also tears down explicitly
    pass


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
    global _CHROME_PROC
    _CHROME_PROC = subprocess.Popen(
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
  var unreachable=0, unreachableWhat=[];
  nodes.forEach(function(e){
    var r=e.getBoundingClientRect();
    if (r.width<1 || r.height<1) { zero++; return; }
    rects.push({w:Math.round(r.width), h:Math.round(r.height),
                x:Math.round(r.left), y:Math.round(r.top)});
    if (r.left < -1 || r.right > innerWidth+1) off++;
    /* ⚠ v2381 — THIS CHECK HAD TWO HOLES AND A SLICED LETTER WENT THROUGH BOTH. The console's
       MINI card printed "MINI \u00b7 AUTC" at 901px — the O cut off by the card's own
       overflow:hidden — and this probe scored `clipped 0` on the same render.

         hole 1: it asks each element whether ITS OWN box hides overflow. The overflowing node
                 was a <b> with white-space:nowrap and overflow:VISIBLE; the box doing the
                 cutting was its BUTTON ancestor. Nobody asked the pair.
         hole 2: it walks `e.querySelectorAll('*')` — descendants only — so the target element
                 itself was never tested at all.

       Both are closed by asking a geometry question instead of a style question: does this
       node's ink stick out of the nearest ancestor that actually CLIPS on that axis. A
       scrollable ancestor (auto/scroll) is excluded on purpose — content outside a scroller is
       one scroll away, not destroyed — which is the same distinction the reachability probe
       below already draws. [[visual-regression-detector]] [[feedback-suspect-the-instrument]] */
    var _clipNodes = [e].concat([].slice.call(e.querySelectorAll('*')));
    _clipNodes.forEach(function(c){
      var cls = String(c.className||'');
      var allowed = OK_TRUNC.some(function(k){ return cls.indexOf(k) >= 0; });
      function flag(why){
        if (allowed) { okTrunc++; return; }
        clipped++;
        if (clippedWhat.length < 5) clippedWhat.push(
          (cls||c.tagName) + ' :: ' + (c.textContent||'').trim().slice(0,28) + ' [' + why + ']');
      }
      /* the original question: this box hides its own overflowing content */
      if (c.scrollWidth > c.clientWidth+1 && getComputedStyle(c).overflow!=='visible'
          && c.clientWidth>0) { flag('self'); return; }
      /* the question it was missing: this box's INK leaves an ancestor that clips */
      var txt = (c.textContent||'').trim();
      if (!txt) return;
      if (c.children.length) return;          /* leaf text only — a wrapper repeats its child */
      /* ⚠ AND IT MUST NOT REPORT INK NOBODY CAN SEE. The first cut of this branch flagged 23
         elements on the vault shelf at every width — every one a `.vm-unassign` ✕ sitting at
         opacity:0 until the mule card is hovered. Measured: opacity 0, and every offset INSIDE
         its parent. A control that is not painted cannot have text visibly cut off, and 23
         identical hits at four widths is the shape of a probe that has started reporting the
         page's own design back at it. inert() is the same test the covered/reachable checks
         already use; this branch simply was not asking it. [[regression-guard]] */
      if (inert(c)) return;
      var cr = c.getBoundingClientRect();
      if (cr.width<1 || cr.height<1) return;
      /* ⚠ A FIXED ELEMENT IS NOT CLIPPED BY AN ORDINARY OVERFLOW ANCESTOR, AND THIS PROBE DID
         NOT KNOW THAT. Measured 2026-09-01 on the state panel: 31 elements reported "cut by rail"
         at 1440, 1120 and 901 — every one of them inside `.fleet-xref`, which is
         `position:fixed; inset:0`, a full-viewport overlay. `.rail` above it carries
         `overflow-x:hidden`, so the ancestor walk compared the overlay's ink against a box that
         does not contain it. The 1440 PNG shows the panel rendering completely and cut nowhere.
         31 false reds from one missing rule — and a false RED is how a gate becomes furniture,
         which is the same end as a false green by a different road.
         The escape is not absolute: transform / filter / perspective / will-change on an ancestor
         re-establish a containing block, and then the clip is real again. So track it rather than
         assuming either way. [[regression-guard]] [[feedback-suspect-the-instrument]] */
      var escaped = (getComputedStyle(c).position === 'fixed');
      for (var q=c.parentElement; q && q!==document.body; q=q.parentElement){
        var qs=getComputedStyle(q);
        if (qs.position === 'fixed') { escaped = true; }
        else if (escaped) {
          var reAnchors = (qs.transform && qs.transform !== 'none')
                       || (qs.filter && qs.filter !== 'none')
                       || (qs.perspective && qs.perspective !== 'none')
                       || (qs.contain && /paint|layout|strict|content/.test(qs.contain))
                       || (qs.willChange && /transform|filter|perspective/.test(qs.willChange));
          if (!reAnchors) continue;   /* it cannot clip what it does not contain */
          escaped = false;            /* this one DOES contain it — clipping is real again */
        }
        /* ⚠ AND INK BELOW A SCROLL FOLD IS NOT INK THAT IS CUT OFF. Measured on the state
           panel at 375: 11 elements reported "cut by fxr-win", including the ⟳ CHECK NOW button.
           The panel is a scroller — .fx-body is overflow-y:auto with scrollHeight 1331 against
           clientHeight 698 — so all eleven are one flick away, and the 375 PNG shows the panel
           rendering correctly and stacking. A gate that calls a scrollable panel clipped will be
           red on every long panel forever, which is how an instrument becomes furniture.
           So: if the walk passes a REAL scroller on the way up, the ink is reachable and this is
           not the defect we are hunting. A scroller is not merely `auto` — it must actually
           overflow, or an `auto` that never scrolls would silently excuse a genuine clip. */
        var scrollsY = (qs.overflowY==='auto' || qs.overflowY==='scroll') && q.scrollHeight > q.clientHeight + 1;
        var scrollsX = (qs.overflowX==='auto' || qs.overflowX==='scroll') && q.scrollWidth > q.clientWidth + 1;
        if (scrollsY || scrollsX) return;
        var hidesX = (qs.overflowX==='hidden' || qs.overflowX==='clip');
        var hidesY = (qs.overflowY==='hidden' || qs.overflowY==='clip');
        if (!hidesX && !hidesY) continue;
        var qr=q.getBoundingClientRect();
        if (qr.width<2 || qr.height<2) continue;
        if ((hidesX && (cr.right > qr.right+1 || cr.left < qr.left-1)) ||
            (hidesY && (cr.bottom > qr.bottom+1 || cr.top < qr.top-1))) {
          flag('cut by ' + (String(q.className||q.tagName)).slice(0,18));
          return;
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
      /* ⚠ v2316 — AND THE EXCLUSION ABOVE IS EXACTLY HOW A DEAD BUTTON SHIPS. The rule "a
         fixed/sticky cover is page chrome" is right for ORDINARY CONTENT and wrong for a CONTROL:
         the comment above says so in its own words ("an overlay sitting on a control he needs is
         the defect") while the code separates by POSITION rather than by what is underneath.
         .control-dock is position:fixed, so a dock lying across a button was excluded by
         construction. MEASURED on bible.html at 375px: `tick it -> Chronicle + Vault` and
         `ignore` inside #inbox-sticky both hit-test to DIV.dock-inner — unclickable at first
         paint — and every render gate passed. A different model family found it cold, from the
         pixels, which is the whole argument for that seat.
         So: a CONTROL is checked separately and a fixed cover does NOT excuse it.
         [[visual-regression-detector]] [[gate-blind-to-unexercised-input]] */
      [].slice.call(e.querySelectorAll(
          'button, a[href], input, select, textarea, [role=button], [onclick]')).forEach(function(c){
        if (inert(c)) return;
        var cr=c.getBoundingClientRect();
        if (cr.width<2 || cr.height<2) return;
        var cx=cr.left+cr.width/2, cy=cr.top+cr.height/2;
        if (cx<0 || cy<0 || cx>innerWidth || cy>innerHeight) return;   /* off-screen is a different fact */
        /* ⚠ v2337 — AND NEITHER IS A CONTROL ITS OWN PANEL HAS SCROLLED OUT OF VIEW. getBounding
           ClientRect ignores an ancestor's overflow clip, so a row below a scrolling panel's fold
           reports viewport coordinates where it is NOT painted, and elementFromPoint there answers
           with whatever the page has at that spot — reported as "a control he cannot click".
           MEASURED at 375x800: #inbox-sticky box 242..573 (maxHeight 331, scrollHeight 465) and
           three buttons reporting y=674, i.e. 101px past a clip that hides them. They are one
           scroll away, not dead.
           ⚠ THIS MUST NOT BECOME A BLANKET EXCUSE. My first attempt walked up looking for ANY
           scrollable ancestor and returned "reachable" — but the page itself scrolls, so it
           answered that for every control on every page and switched the whole check off. The
           sabotage caught it: removing the panel's bound left the gate GREEN on the very defect it
           exists to catch. This version asks a narrower question — is the control INSIDE the box
           of each clipping ancestor — so a control that really is painted under the dock still
           fails. [[feedback-suspect-the-instrument]] [[regression-guard]] */
        var clipped=false;
        for (var q=c.parentElement; q && q!==document.body && !clipped; q=q.parentElement){
          var qs=getComputedStyle(q);
          if (qs.overflowY==='visible' && qs.overflowX==='visible') continue;
          var qr=q.getBoundingClientRect();
          if (qr.width<2 || qr.height<2) continue;
          if (cy < qr.top-1 || cy > qr.bottom+1 || cx < qr.left-1 || cx > qr.right+1) clipped=true;
        }
        if (clipped) return;
        var hit=document.elementFromPoint(cx, cy);
        if (!hit) return;
        if (hit===c || c.contains(hit) || hit.contains(c)) return;     /* the control answers for itself */
        /* ⚠ AND SCROLLING MUST NOT BE ABLE TO SEPARATE THEM, or this becomes exactly the noise the
           comment above warns about. The first cut of this check counted ANY covered control and
           reported 9 in the vault at 1440 — every one a cell that scrollIntoView had parked under
           the sticky HEADER, which is the page working. A control the user can scroll out from
           under is not unreachable; it is merely somewhere else right now.
           The defect is the pair that move TOGETHER: a control pinned in a fixed/sticky container
           and a fixed/sticky thing lying on it. Neither scrolls away from the other, so the button
           is dead wherever he goes. That is the inbox case exactly — #inbox-sticky is sticky,
           .control-dock is fixed. [[visual-regression-detector]] */
        function pinned(n){
          for (var q=n; q && q!==document.body; q=q.parentElement){
            var pp=getComputedStyle(q).position;
            if (pp==='fixed' || pp==='sticky') return true;
          }
          return false;
        }
        if (!(pinned(c) && pinned(hit))) return;
        unreachable++;
        if (unreachableWhat.length < 4) unreachableWhat.push(
          (String(c.className||c.tagName)) + ' :: "' + (c.textContent||'').trim().slice(0,26)
          + '" is under ' + String(hit.className||hit.tagName));
      });
    }
  });
  var txt = nodes.map(function(e){return (e.textContent||'');}).join(' ')
                 .replace(/\s+/g,' ').trim();
  var widths = {}; rects.forEach(function(r){ widths[r.w]=1; });
  return JSON.stringify({found:nodes.length, painted:rects.length, zero:zero, off:off,
    clipped:clipped, clippedWhat:clippedWhat, okTrunc:okTrunc,
    covered:covered, coveredWhat:coveredWhat,
    unreachable:unreachable, unreachableWhat:unreachableWhat,
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
                       # ⚠ v2316 — A CONTROL HE CANNOT PRESS IS THE LOUDEST DEFECT THIS FILE CAN
                       # FIND, and until now it was the one class excluded by construction: the
                       # `covered` probe skips any cover with a fixed/sticky ancestor, and the
                       # bottom dock is position:fixed. Measured at 375px on bible.html, `tick it
                       # -> Chronicle + Vault` and `ignore` both hit-tested to DIV.dock-inner and
                       # every gate stayed green. Reported cold by a different model family off
                       # the pixels, then reproduced by hit test. [[visual-regression-detector]]
                       ("unreachable", "are CONTROLS he cannot click — something else answers the "
                                       "hit test at their centre"),
                       ("broken", "are images that failed to load")):
        if m.get(field):
            what = m.get(field + "What") or []
            out.append("%s: %d element(s) %s%s"
                       % (key, m[field], msg, (" — " + "; ".join(what)) if what else ""))
    return out


def _selector_ready(tab, sel, budget=20.0):
    """Wait until the TARGET'S OWN selector matches something painted. Returns why, or None.

    ⚠ v2330 — _settled() ABOVE IS A GLOBAL SETTLE, AND THAT IS NOT THE SAME QUESTION.
    It waits for readyState complete and the body to stop growing, which its own docstring
    correctly calls the difference between measuring a page and measuring a page still
    assembling. But several targets here are filled by data that arrives AFTER the body has
    stopped moving — the Task Force rows and the vault mules among them — so the document can be
    perfectly settled while the panel this run is about is still empty.

    What followed the activation was `time.sleep(1.4)`, i.e. the exact fixed sleep _settled was
    written to replace, one step further down the same function.

    MEASURED, 2026-08-31. Eight consecutive runs on an idle machine: 8 green. Four runs with one
    extra console process alive: 1 green, 3 RED — and every failure was
    `selector ... matched NOTHING`, never a layout fault:

        901x900   selector '.vm-gauge, [data-vault-mule]' matched NOTHING
        1440x1000 selector '#sc-taskforce .sc-tf-row, #sc-taskforce > .sc-card-h' matched NOTHING

    So the gate was not a coin flip. It was deterministic given a condition nobody was measuring,
    which is worse, because "run it again" made it green and taught us to do that.
    [[feedback-blind-fixture-green-gate]] [[feedback-suspect-the-instrument]]

    ⚠ AND IT STILL FAILS HONESTLY. A selector that never matches inside the budget is reported as
    exactly that — never appeared, not "not yet" — so a genuinely absent panel is still caught.
    The bound is what separates the two facts; without one they are the same observation.
    """
    t0 = time.time()
    js = ("(function(){try{var n=document.querySelectorAll(%s);if(!n.length)return 0;"
          "for(var i=0;i<n.length;i++){var r=n[i].getBoundingClientRect();"
          "if(r.width>1&&r.height>1)return 1;}return 0;}catch(e){return 0}})()")
    while time.time() - t0 < budget:
        try:
            if tab.ev(js % json.dumps(sel)):
                return None
        except Exception:
            pass
        time.sleep(0.4)
    return ("%r never matched a painted element in %.0fs after the panel was activated — either "
            "the surface is genuinely absent, or this machine was too loaded to build it, and "
            "the difference is exactly what this bound exists to state rather than guess"
            % (sel, budget))


def _serve_console():
    """Boot a PRIVATE control_app on an ephemeral port and return (origin, proc).

    ⚠ WHY THIS EXISTS. This harness loaded `file://` and nothing else, which is right for
    bible.html — it assembles itself out of localStorage, so a target seeds a store and the page
    renders. It is IMPOSSIBLE for the console's own panels: THE SHELF, the pipeline board, THE
    FLEET and the BEST RUN / STREAK strip are filled from /api/sessions and /api/status, so under
    file:// they render "Loading runs…" and nothing else.

    That is not a small hole. Every one of the nine defects Konyo reported on 2026-09-01 lives on
    one of those surfaces, and NOT ONE was found by a gate — because a surface with no target is
    unmeasured, and unmeasured reads identically to clean in a green run. gh #208.

    ⚠ NEVER :17772. The port is taken from the kernel, and the process this starts is the ONLY one
    it ever kills — by the pid it holds, never by name. [[process-port-discipline]]
    """
    import socket
    import subprocess
    import urllib.request
    s_ = socket.socket()
    s_.bind(("127.0.0.1", 0))
    port = s_.getsockname()[1]
    s_.close()
    if port == 17772:                      # cannot happen from an ephemeral bind; refuse anyway
        raise RuntimeError("refusing to serve on :17772 — that is his live console")
    env = dict(os.environ, TV_CONTROL_PORT=str(port), TV_PORT=str(port + 1), TV_STUB="1")
    proc = subprocess.Popen([sys.executable, os.path.join(HERE, "control_app.py"), "--no-open"],
                            cwd=HERE, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    origin = "http://127.0.0.1:%d/" % port
    for _ in range(60):
        time.sleep(0.5)
        try:
            urllib.request.urlopen(origin + "api/status", timeout=2).read(1)
            return origin, proc
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("the private console exited before it answered")
    try:
        proc.terminate()
    except Exception:
        pass
    raise RuntimeError("a private console did not answer on :%d in 30s — UNKNOWN, not a pass" % port)


def check(name, spec, shots=True):
    """Render one target at every width and judge it. -> dict"""
    out = {"target": name, "why": spec["why"], "widths": {}, "ok": True, "refusals": []}
    # ⚠ v2379 — A TARGET MAY NAME ITS OWN PAGE. Every target until now was hard-wired to
    # bible.html, so tv/control_ui.html — HIS CONSOLE, where every button we argue about lives —
    # had ZERO coverage from this gate. Measured: 5 targets, 0 mentions of control_ui. That is
    # why "the button is missing / buried / half-built" reached him THREE times: the instrument
    # that exists to catch it was never pointed at the file. [[visual-regression-detector]]
    # ⚠ v2401 — A TARGET MAY ASK TO BE SERVED, because file:// cannot render a panel whose
    # content arrives from the server. `serve: True` boots a private console on an ephemeral port
    # (never :17772) and points the tab at it. Opt-in per target: for bible.html, file:// is the
    # honest environment and an http origin would only add a dependency. gh #208
    _console = None
    if spec.get("serve"):
        try:
            _origin, _console = _serve_console()
        except Exception as e:
            out["ok"] = False
            out["refusals"].append("could not serve a private console for this target: %s. That is "
                                   "UNKNOWN, not a pass." % str(e)[:160])
            return out
        _url = _origin + (spec.get("path") or "")
    else:
        _url = "file://" + os.path.join(REPO, spec.get("page") or "bible.html")
    tab = _Tab(_url)
    try:
        tab.send("Page.enable")
        tab.send("Runtime.enable")
        # ⚠ v2379 — A LIVE CONSOLE NEVER SETTLES, AND THAT IS NOT A FAULT TO REPORT. Its clock
        # ticks every second and its CSS animations are infinite, so readyState/size never stop
        # moving — the exact reason Playwright's screenshot hangs on it (chrome-cdp-mac). A
        # target may declare `settles: False`; it then waits a fixed beat instead. It must be
        # OPT-IN per target, because for an ordinary page 'never settled' IS the finding.
        if spec.get("settles") is False:
            # ⚠ v2401 — 1.6s IS ENOUGH FOR A FILE, NOT FOR A SERVER. A served console must fetch
            # /api/status and build its panels from the answer; at 1.6s the elements EXIST and are
            # empty, so `activate` returns false and the target refuses for a reason that is about
            # the clock rather than the page. Measured: the state panel refused at 1.6s and opened
            # 1440x913 with all four sections at 9s. `warmup` makes the wait a stated property of
            # the target instead of a number that happened to work. [[stale-reading]]
            time.sleep(float(spec.get("warmup") or 1.6))
            why = None
        else:
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
        # v2330 — was `time.sleep(1.4)`. See _selector_ready: a fixed sleep here is the same
        # defect _settled() was written to remove, and under load it measured empty panels.
        why = _selector_ready(tab, spec["sel"])
        if why:
            out["ok"] = False
            out["refusals"].append(why)
            return out
        for w, h in WIDTHS:
            tab.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
                     deviceScaleFactor=1, mobile=False)
            # ⚠ v2331 — AND AGAIN AFTER EVERY RESIZE, which the first cut of this fix missed.
            # v2330 waited for the selector once, after activation, and the gate still blocked a
            # push with "matched NOTHING" — this time at ALL FOUR widths, and WITHOUT the new
            # refusal message, which is what pinned it: the wait had passed, so the panel existed
            # and then went away. A resize re-renders these panels, and the loop answered that
            # with a fixed 0.6s exactly as the activation step used to.
            #
            # One fixed sleep replaced, its sibling two lines below left in place. That is the
            # same defect surviving in the same function, which is the whole of
            # [[feedback-generalize-fixes]]: fix the CLASS, not the site that happened to fail.
            why_w = _selector_ready(tab, spec["sel"], budget=12.0)
            if why_w:
                out["ok"] = False
                out["refusals"].append("%dx%d: %s" % (w, h, why_w))
                continue
            tab.ev("(function(){var e=document.querySelector(%s); if(e) "
                   "e.scrollIntoView({block:'center'}); return 1;})()" % json.dumps(spec["sel"]))
            time.sleep(0.35)
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
        if _console is not None:
            # the pid THIS function started, and only that one. [[process-port-discipline]]
            try:
                _console.terminate()
                _console.wait(timeout=8)
            except Exception:
                try:
                    _console.kill()
                except Exception:
                    pass
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
    # ⚠ TEAR IT DOWN HERE TOO, NOT ONLY IN atexit. The gate is routinely run under a hard time
    # bound (`perl -e 'alarm N; exec @ARGV'` — `timeout` is not installed on this Mac), and a
    # process killed by a signal never runs its atexit handlers. That is precisely how four
    # headless Chromes survived, one of them for a day and a half.
    try:
        sys.exit(main(sys.argv[1:]))
    finally:
        _chrome_down()
