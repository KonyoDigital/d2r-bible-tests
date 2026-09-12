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
import shutil
import tempfile
import atexit
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
# ⚠ v2406 — THE FIFTH ENTRY IS THE ONLY ONE HE ACTUALLY HAS, AND IT WAS THE ONE MISSING.
# Every height above is TALLER THAN HIS WINDOW. control_app.py opens the console at 1120x660
# (v1464, a deliberate default that fits a 672-logical work area — a runtime clamp was tried and
# shipped a window 174px off-screen, so the height is not up for negotiation), which leaves a
# ~628px viewport. This gate rendered 1120 at height 900 and called it covered.
#
# So when the live beat reported `taskforce top=1050 H=502` and `forge top=1599 H=181` against a
# 628px viewport, the gate had nothing to say — at 900px tall those panels are simply further down
# a page that has room for them. THE DEFECT COULD NOT APPEAR IN THE VIEWPORT BEING TESTED. That is
# the same shape as the `.shell` bare-1fr scar and the claim-bar spec that asserted geometry on a
# page where the claim bar can never exist: a green produced by a fixture the bug cannot inhabit.
# [[feedback-blind-fixture-green-gate]] [[gate-blind-to-unexercised-input]]
#
# 628 is not a breakpoint-adjacent guess. It is the number on his screen.
WIDTHS = ((1440, 1000), (1120, 900), (901, 900), (375, 800), (1120, 628))

# ── v2406 — CAN HE FIND IT, not just does it render once you get there ──────────────────────────
#
# Every measurement in this file happens AFTER `scrollIntoView({block:'center'})`, and it has to:
# an unscrolled target captures as a plausible black rectangle rather than an error. But that means
# the gate has only ever been able to answer ONE question — *does this render correctly once you
# reach it* — while silently implying the other: *can he reach it at all*.
#
# The contradiction that exposed it, 2026-09-01: this gate reported `taskforce 1120x628 painted 3/3
# clipped 0 off 0 covered 0` while the LIVE console's own beat, in the same minute, reported
# `taskforce BELOW-FOLD top=1050 vh=628`. Both were correct. The gate had scrolled to it first.
# Two instruments disagreeing IS the finding. [[feedback-contradiction-is-the-finding]]
#
# ⚠ AND BELOW-FOLD IS NOT AUTOMATICALLY A DEFECT. A long page he can scroll is a page working. The
# defect is the `.util-strip` shape: content placed where NOTHING CAN SCROLL TO IT — four buttons
# at x=1165 on a 901px viewport with scrollWidth still 901, clipped rather than scrolled off, and
# unreachable for three ships. So this reports three distinct states and fails on exactly one.
_REACH = """(function(sel){
  var e=document.querySelector(sel); if(!e) return null;
  /* measure the LOAD position: undo this loop's own previous scrollIntoView, and every inner
     scroller too, or we measure a leftover from the last viewport in WIDTHS. */
  try{ window.scrollTo(0,0); }catch(_){}
  var sc=null, p=e.parentElement;
  while(p && p!==document.body){
    var st=getComputedStyle(p);
    if(/(auto|scroll)/.test(st.overflowY) && p.scrollHeight > p.clientHeight+1){
      p.scrollTop=0; if(!sc) sc=p; }
    p=p.parentElement; }
  var r=e.getBoundingClientRect(), vh=innerHeight||0, vw=innerWidth||0;
  if(r.width<1 && r.height<1) return {state:'ZERO-SIZE', top:0, h:0, vh:vh, max:0};
  var on = r.top<vh && r.bottom>0 && r.left<vw && r.right>0;
  var box = sc || document.scrollingElement || document.documentElement;
  var max = Math.max(0, box.scrollHeight - box.clientHeight);
  var state='ON-SCREEN';
  if(!on){
    /* how far must we travel to bring its TOP edge into the viewport */
    var need = r.top - vh + Math.min(r.height, vh);
    state = (max > 0 && max >= need - 2) ? 'BELOW-FOLD' : 'UNREACHABLE';
  }
  return {state:state, top:Math.round(r.top), h:Math.round(r.height), vh:vh,
          max:Math.round(max), scroller: sc ? (sc.id||sc.className||'inner') : 'page'};
})"""

#: what counts as "the browser went away" rather than "this file has a bug". Narrow ON PURPOSE —
#: see the handler in main(). websocket may be absent, so this is built defensively.
def _transport_errors():
    # ⚠ THREE SWINGS, AND THE FILE WAS LEFT ARGUING WITH ITSELF AFTER THE THIRD.
    #   v2412  except Exception              — anything at all was "the browser went away"
    #   v2416  (ConnectionError, OSError)    — still swallows FileNotFoundError, PermissionError,
    #                                          a full disk. The same defect with a smaller net.
    #   v2418  (ConnectionError, TimeoutError) — too narrow: on his 3.9.6 `socket.timeout` is NOT
    #                                          TimeoutError, and URLError is not ConnectionError.
    # A cold review then found the paragraph explaining why URLError must NOT be here still sitting
    # directly above the list that had just added it — "not documentation drift, an unresolved
    # argument left in the source". It is resolved here rather than layered over.
    #
    # THE RULE, stated once: a member must mean THE BROWSER DID NOT ANSWER.
    #   ConnectionError  reset / aborted / broken pipe            — yes
    #   socket.timeout   named, because 3.9 does not alias it     — yes
    #   TimeoutError     the 3.10+ spelling, harmless to include  — yes
    #   URLError         no answer from /json/new                 — yes
    #   HTTPError        the server ANSWERED, with a status       — NO, and it subclasses URLError,
    #                    so it rides in unless excluded. A 500 may be Chrome dying, but a 404 is
    #                    this file asking for the wrong path — that is a harness bug wearing a
    #                    transport coat, and v2418's message called it "unambiguously transport"
    #                    without pinning it either way.
    # Anything not on that list is a bug in this file and is reported as one. [[label-outlived-referent]]
    # ⚠ AND THEN I SWUNG TOO FAR THE OTHER WAY. Dropping OSError removed the over-broad catch and
    # took two GENUINE transport cases with it. Measured on his Python 3.9.6:
    #
    #     socket.timeout is TimeoutError            -> False   (that alias arrived in 3.10)
    #     socket.timeout subclass of TimeoutError   -> False
    #     urllib.error.URLError subclass of OSError -> True, of ConnectionError -> False
    #
    # So a read that times out on the CDP socket, and a URLError from Chrome's own /json/new
    # endpoint — both unambiguously "the browser went away" — were being reported as bugs in this
    # file. A cold review caught it on the very next ship.
    #
    # The lesson is not "OSError was right after all": it is that a transport family must be a LIST
    # OF THE THINGS THAT ARE TRANSPORT, not a base class chosen for how much it happens to cover.
    # Naming them means the next surprise is a missing NAME, which is visible, rather than a
    # silently swallowed sibling. [[unknown-stays-unknown]]
    import socket as _sock
    import urllib.error as _uerr
    errs = [ConnectionError, TimeoutError, _sock.timeout, _uerr.URLError]
    try:
        import websocket as _ws
        errs.append(getattr(_ws, "WebSocketException", None))
        errs.append(getattr(_ws._exceptions, "WebSocketConnectionClosedException", None))
    except Exception:
        pass
    return tuple(e for e in errs if isinstance(e, type) and issubclass(e, BaseException))


_TRANSPORT_ERRORS = _transport_errors()


def _transport_exclusions():
    """Types that LOOK like transport by inheritance but are not. -> tuple

    ⚠ A MODULE CONSTANT, NOT SOMETHING SMUGGLED IN VIA globals() FROM INSIDE A FUNCTION. The first
    cut set this with `globals()["_TRANSPORT_EXCLUDE"] = ...` inside _transport_errors(), which
    works only because that function happens to be called at import — and a repo guard caught it
    (`render_check.py: '_TRANSPORT_EXCLUDE' in main()`). A name that main() depends on must be
    visible where a reader looks for it, not created as a side effect of an unrelated call.

    HTTPError subclasses URLError, so admitting URLError admits it unless it is excluded FIRST.
    URLError means the browser did not answer; HTTPError means it ANSWERED, with a status — and a
    404 is this file asking for the wrong path.
    """
    try:
        import urllib.error as _ue
        return (_ue.HTTPError,)
    except Exception:
        return ()


_TRANSPORT_EXCLUDE = _transport_exclusions()

def _find_chrome():
    """The browser binary ON THIS MACHINE. -> path (may not exist; callers check)

    ⚠⚠ v2659 — THIS WAS A HARDCODED macOS PATH, AND IT MADE A CI CHANGE COMPLETELY INERT.
    `CHROME` was `/Applications/Google Chrome.app/...`, so `_chrome_up()` asks `os.path.exists` of
    a path that CANNOT exist on a Linux runner. The same day, `tv-tests.yml` gained a Chromium
    install and cache specifically so `overlap_ratchet` could stop skipping on CI — and the very
    first run with a browser still printed `⚪ UNKNOWN — headless chrome would not start` in
    **0.1s**, because nothing ever looked where Playwright had put it. CI minutes spent installing
    a browser no reader could see. [[the-unjoined-end]] — built at both ends, never joined, and I
    closed the task claiming it was fixed.
    ⚠ THE 0.1s WAS THE TELL. A real launch attempt cannot fail that fast.

    Resolution order, per the same rule `grok-second-eye` §2 records for a second-eye binary —
    env override, then the known install locations, never one hardcoded guess:
      1. `TV_CHROME`      — an explicit override always wins
      2. his Mac's Google Chrome
      3. Playwright's cached chromium (`~/.cache/ms-playwright/chromium-*/…`), which is what CI has
      4. the usual Linux names on PATH
    """
    import glob as _g
    import shutil as _sh
    env = os.environ.get("TV_CHROME")
    if env:
        return env
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(mac):
        return mac
    # Playwright keeps a versioned directory; take the newest so a cache carrying two does not
    # pin the older one for ever.
    roots = sorted(_g.glob(os.path.expanduser("~/.cache/ms-playwright/chromium*/chrome-linux/chrome")))
    if roots:
        return roots[-1]
    for name in ("google-chrome", "chromium-browser", "chromium", "chrome"):
        p = _sh.which(name)
        if p:
            return p
    return mac          # unchanged behaviour when nothing is found: a path that will not exist


CHROME = _find_chrome()

# A target says: how to set the board up, what to click, and what element IS the thing.
def _shelf_activate():
    """Open the THEATRE, then force THE SHELF open, and refuse until the river has RENDERED.

    ⚠⚠ THE RIVER STRIP HAD NO PIXEL COVERAGE AT ALL until this target. v2773 fixed its heading at
    375px — three anonymous flex items each wrapping in its own column, the FIFO qualifier crushed
    into a 61px column three lines tall — and the only thing guarding that fix was a unit test
    reading computed style. A surface nobody photographs is a surface whose next regression is
    found by Konyo. [[visual-regression-detector]]

    ⚠⚠ `thShelf(true)` IS CALLED EXACTLY ONCE, VIA A SENTINEL — NOT GUARDED ON `ov.hidden`, AND
    THIS COST A ROUND. The obvious guard is "call it while the overlay is still hidden", and it is
    WRONG: the shelf unhides ASYNCHRONOUSLY, so the overlay is still hidden on the next poll, so it
    is called again, so the load restarts — once per second, for the full 12s window, and the
    target dies with "could not be ACTIVATED" while the page is perfectly healthy. MEASURED: with
    the hidden-guard it never activated; with the sentinel it does. `_adv_activate` carries a note
    about exactly this shape and I reproduced it anyway.

    `thOpen()` may stay guarded on `theatre-open` because thOpen sets that class SYNCHRONOUSLY —
    the guard is true on the very next statement. A guard is only safe when the thing it tests is
    set before the poll can come round again.

    ⚠ AND IT REFUSES UNTIL A LANE EXISTS, not merely until the overlay is visible. The lanes are
    filled by an async load; the overlay unhides FIRST. Photographing it in between would give a
    permanently green target measuring an empty box — the exact false green `require_filled` was
    written for on #fleet-list.

    ⚠ `thOpen()` already routes Sessions -> TV·D itself (v1627), so this does not repeat that.
    """
    return """(function(){
        try {
          /* ⚠⚠ v2795 — THIS WAS A ONE-SHOT AND THE ONE SHOT MISSED. It clicked exactly once,
             guarded by `window.__shelfAsked`, on the harness's FIRST poll. MEASURED via this
             target's own activateWhy:
                 view=none · _toTVD=function · asked=FIRED · btnVisible=yes
                 · theatre=SHUT(display:none) · th-shelfov=present but HIDDEN
             The button existed and was visible, the click fired, and the theatre never opened —
             and `#btn-shelf`'s handler records a `shelf-door-refused` fault when it refuses, of
             which there were NONE from these runs. So the handler did not refuse; it never ran.
             The click landed before its onclick was bound, and the sentinel guaranteed no second
             attempt for the remaining 12s of polling.
             ⛔ A ONE-SHOT THAT MISSES IS A PERMANENT REFUSAL WEARING A SLOW ONE'S CLOTHES, and
             the two must not look alike — this target refused for 12.1s reporting only "could not
             be ACTIVATED", which is the shape note 5 above warns costs a round every time.
             ⚠ RETRY, BUT ONLY WHILE IT IS SHUT — that is what keeps it idempotent, the property
             heart-fan's opener documents as mandatory ("the harness re-runs this every 0.4s, so it
             must never toggle"). Once the theatre is open the click STOPS, so a repeat can never
             toggle the door back closed. Counted, so a reader can tell one missed click from a
             door that refuses every time. */
          var _th0 = document.getElementById('theatre');
          var _shut = !_th0 || getComputedStyle(_th0).display === 'none';
          if (_shut && (window.__shelfTries || 0) < 25) {
            window.__shelfTries = (window.__shelfTries || 0) + 1;
            /* ⚠⚠ v2785 — LEAVE THE GAMEPLAY HOME FIRST, exactly as `_adv_activate` does, and for
               the same reason. `#btn-shelf` sits in the RAIL beside `#sig-adv`, and v2775 made
               `.signal` / `#sig-adv` `display:none` under `body[data-view="sessions"]` — which is
               the console's HOMEPAGE, the view a freshly served console lands in. So the door was
               in a hidden region on every run. `window._toTVD()` is the published route out and
               is the one `_adv_activate` already uses; not calling it is why this target refused
               three times for three different-looking reasons. [[copy-drift]] */
            /* ⚠ THE GUARD READ `data-view` AND A FRESHLY SERVED CONSOLE HAS NONE — measured
               `view=none`, so this whole call was skipped on exactly the load it exists for. The
               attribute is a statement about WHICH view is active, not about whether leaving one
               is possible; `_toTVD()` is safe to call regardless and is what `_adv_activate`
               does unconditionally. [[feedback-threshold-above-the-ceiling]] */
            try { if (window._toTVD) window._toTVD(); } catch(e){}
            /* ⚠⚠ v2785 — #th-shelf IS THE WRONG DOOR, AND IT COST THIS TARGET A ROUND.
               `#th-shelf` is the button INSIDE the theatre bar, and `#th-shelfov` lives inside
               `#theatre`, which is display:none while the theatre is shut — so clicking it opened
               an overlay inside a collapsed box and the target refused for its whole 12s window.
               `#btn-shelf` is the door a person actually uses: its handler awaits `thOpen()`
               FIRST and only then `thShelf(true)`, and v2446 wrote it exactly because the shelf
               was "swallowed" without that ordering. Neither `thOpen` nor `thShelf` is on
               `window`, so clicking the real control is the only way in. */
            var b = document.getElementById('btn-shelf')
                 || document.getElementById('th-shelf');
            if (b && b.click) b.click();
          }
        } catch(e){}
        var ov = document.getElementById('th-shelfov');
        if (!ov || ov.hidden) return false;
        /* ⚠⚠ PROVE IT FROM THE RECT, NOT THE FLAG — this file's own v2666 scar, verbatim:
           "`hidden === false` IS NOT 'HE CAN SEE IT', AND THAT IS THE HOLE HE FELL IN ... the
           overlay reported height 0 with the full refusal text inside it", because #th-shelfov
           lives inside #theatre and that is display:none while the theatre is shut. A target that
           trusted the flag would photograph a zero-height box and call the surface covered. */
        var _r = ov.getBoundingClientRect();
        if (!(_r.width > 0 && _r.height > 0)) return false;
        /* ⚠⚠ v2785 — THE LANES ARE ONE OF FOUR THINGS THE RIVER CAN SAY, AND THE FIRST CUT OF THIS
           TARGET WOULD ONLY EVER ACCEPT THE HAPPY ONE. `_shLanesRender` renders `.shr-head` +
           `.shr-lane` when the ask succeeds, and a `.shr-bad` sentence in the three other cases:
           the console was asked and did not answer (UNKNOWN, not an empty river), the river
           refused with a reason, or it reported no lanes at all.

           Requiring `.shr-lane` meant a console whose river ask fails could never be photographed
           — the target would refuse for its full 12s window and report "could not be ACTIVATED"
           while the page was perfectly healthy and RENDERING THE VERY SENTENCE a reader needs to
           see. Those three refusal surfaces have never been photographed either, and they are the
           ones that appear when something is wrong, which is when pixels matter most.

           So: EITHER the lanes OR a rendered refusal counts as painted, and `__shelfSaw` records
           WHICH — a green run that photographed a refusal must not read as a green river.
           Only the loading placeholder is still refused, because that one really is "not yet".
           [[unknown-stays-unknown]] [[zero-needs-a-denominator]] */
        var lanes = ov.querySelector('.shr-lane') && ov.querySelector('.shr-head');
        var bad = ov.querySelector('.shr-bad');
        if (!lanes && !bad) return false;
        try { window.__shelfSaw = lanes ? 'lanes' : 'refusal'; } catch(e){}
        return true;
      })()"""


def _adv_activate(el_id, require_filled=False):
    """Open the ⚙ ADVANCED drawer and scroll `el_id` to the top of the rail scroller.

    ⚠ RECTS, NOT offsetParent. `.rail` is declared with grid-area/flex/overflow and NO `position`,
    so it is static and is therefore never an offsetParent — an offset walk sails straight past the
    scroller it just found and lands on a document-relative number. That cost v2107 and v2113 a
    round each in the app itself; the harness must not repeat it. getBoundingClientRect is
    viewport-relative for both boxes, so their difference is the exact delta whatever is positioned.

    `require_filled` additionally refuses while #fleet-list still shows the copy that means "nobody
    has asked the route yet" — a section can be laid out perfectly and carry nothing. That is the
    whole defect this target exists for, so photographing it green would be the false green.

    ⚠⚠ v2773 — IT MUST LEAVE THE GAMEPLAY HOME FIRST, AND THAT IS A RETARGET, NOT A RELAXATION.
    The drawer moved: `.signal` and `#sig-adv` are now `display: none` under `data-view="sessions"`
    and under `body.shell-open`, because the engine room belongs on TV·D beside the AI readers.
    And Sessions is the console's HOMEPAGE (v1596, his own ruling — `showSessions()` fires on
    DOMContentLoaded), so a freshly served console lands in the one view that no longer owns this
    drawer. MEASURED: activate returned false and all three targets failed with "the panel could
    not be ACTIVATED after 12.1-12.3s", plus three COVERAGE refusals — 11 green / 8 red against
    15 green / 0 red on the previous shape of the file.

    That is [[regression-guard]] GATE_MOVES_WITH_PRODUCT to the letter: *a ship that moves a
    surface owns the gates that describe it*, and its first named way to get the retarget wrong is
    "retarget to a room that has not rendered — the retarget itself would have looked like the
    defect. OPEN THE ROOM THAT OWNS THE THING." So this opens TV·D. It does NOT touch the
    assertions: same element, same 5 widths, same `require_filled` refusal on #fleet-list. Relaxing
    those is that document's failure mode #2 and it is not what this is.

    ⚠ GUARDED ON `data-view` BEING PRESENT, because this expression is POLLED for ~12s. An
    unguarded `_toTVD()` would re-run `shellHome()` on every poll and reset the scroll this
    function performs three lines below — a fix that fights itself once per tick.
    """
    return """(function(){
        try { if (document.body.getAttribute('data-view') && window._toTVD) window._toTVD(); } catch(e){}
        var d = document.getElementById('sig-adv');
        if (!d) return false;
        if (!d.open) d.open = true;
        var el = document.getElementById('%s');
        if (!el) return false;
        %s
        var sc = el.parentElement;
        while (sc && sc !== document.body) {
            var ov = getComputedStyle(sc).overflowY;
            if ((ov === 'auto' || ov === 'scroll') && sc.scrollHeight > sc.clientHeight + 4) break;
            sc = sc.parentElement;
        }
        if (sc && sc !== document.body) {
            var delta = el.getBoundingClientRect().top - sc.getBoundingClientRect().top;
            sc.scrollTop = Math.max(0, sc.scrollTop + delta - 6);
        }
        /* prove it from the RECT, never from the call returning - the harness's own scar */
        var r = el.getBoundingClientRect();
        return !!(r.width > 2 && r.height > 2); })()""" % (
        el_id,
        ("if (/advanced to check the fleet/i.test(el.textContent || '')) return false;"
         if require_filled else ""))


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
    # ⚠ v2440 — A `locks` TARGET WAS WRITTEN AND WITHDRAWN, AND SAYING SO IS THE POINT.
    # The vault lock chip (#lock-vault, added v2438) has NO TARGET here, so it is UNMEASURED — and
    # in a green run unmeasured reads exactly like clean. That is a real gap, named rather than
    # hidden. What was tried and why it was pulled:
    #
    #   · the chip IS correct, measured directly over CDP at 1120x628:
    #       171.0 x 19.6 · data-state="unproven" · text "locked untested" · every ancestor visible
    #   · but the target could not be made to ACTIVATE reliably, and a gate that always refuses is
    #     furniture in the same way one that always passes is. Shipping it would have trained us to
    #     skim its refusal, and then the real one goes with it.
    #
    # TWO THINGS IT FOUND BEFORE IT WAS PULLED, both kept:
    #   1. the chips shipped `hidden` and only appeared after a status poll — so before the first
    #      poll, or if none ever lands, the lock was INVISIBLE. An absent badge reads as NO LOCK,
    #      which is the one direction it must never fail in. They now ship data-state="locked".
    #   2. AN ACTIVATE IS POLLED, SO IT MUST BE IDEMPOTENT. check() re-runs it every 0.4s for 12s;
    #      an unconditional tab click TOGGLES, so each poll undid the last and the answer came down
    #      to parity. Any future target here must check before it acts.
    #
    # ⚠⚠⚠ v2785 — A `shelf` TARGET WAS WRITTEN AND WITHDRAWN, AND SAYING SO IS THE POINT.
    # Task #30 is real and stays open: THE RIVER STRIP HAS NO PIXEL COVERAGE. v2773 fixed its
    # heading at 375px — three anonymous flex items each wrapping into its own column, the FIFO
    # qualifier crushed into a 61px column three lines tall — and the only thing guarding that fix
    # is a unit test reading computed style. A surface nobody photographs is a surface whose next
    # regression is found by Konyo. That gap is NAMED here rather than hidden, exactly as the
    # `locks` target above is. [[visual-regression-detector]] [[unknown-stays-unknown]]
    #
    # WHY IT WAS PULLED — the last refusal, which is a fact about the SURFACE and not the target:
    #
    #     🔴 shelf  the page never settled in 25s — readyState/size kept moving
    #
    # Opening the shelf keeps the document assembling past the settle bound. That is the same
    # shape as task #15 ("THE SHELF builds ~72,700 DOM elements in one open and stops the whole
    # window painting"); v2760 narrowed the build to what is shown, and it still churns enough
    # that `settled` never latches. A target that always refuses is furniture in the same way one
    # that always passes is — ship it and we learn to skim its refusal, and then the real one goes
    # with it. Konyo's call, 2026-09-08: *"withdraw the target if it refuses again"*.
    #
    # ⚠ FIVE THINGS IT FOUND BEFORE IT WAS PULLED, ALL KEPT AND ALL REAL:
    #   1. `spec["seed"]` RAISED rather than skipped, so adding any target with nothing to seed
    #      printed `🔴 the GATE ITSELF raised (KeyError: 'seed')` and lost the surface. Now
    #      `spec.get("seed")`. That one is shipped and is a fix to the harness for every future
    #      target, not just this one.
    #   2. `serve: True` is what separates a CONSOLE target from a bible.html one. Without it the
    #      shelf was being driven against the public page, where `#th-shelfov`, `#btn-shelf`,
    #      `_toTVD` and even `data-view` simply do not exist. Four rounds of my inference chased
    #      symptoms on the wrong document. [[copy-drift]]
    #   3. `#btn-shelf` is the door, NOT `#th-shelf`: the latter lives inside the theatre bar and
    #      `#th-shelfov` is inside `#theatre`, which is display:none while shut. v2446 wrote
    #      `#btn-shelf` precisely because the shelf was "swallowed" without `await thOpen()` first.
    #   4. PROVE IT FROM THE RECT, NOT THE FLAG — v2666's scar, which applies here verbatim:
    #      "`hidden === false` IS NOT 'HE CAN SEE IT' ... the overlay reported height 0 with the
    #      full refusal text inside it".
    #   5. `activateWhy` IS NOT OPTIONAL FOR A NEW TARGET. Four refusals in a row each said only
    #      "could not be ACTIVATED"; I inferred a cause, fixed something genuinely broken, and got
    #      the same sentence back. The first run WITH `activateWhy` printed
    #      `view=null · _toTVD=undefined · btnShelf=NO · ov=ABSENT` and settled it instantly. A
    #      refusal that cannot name its own cause costs a round every time.
    #      [[zero-needs-a-denominator]] [[feedback-verify-not-proxy]]
    #
    # ⚠ THE NOTE ABOVE IS ANSWERED, v2795 — AND THE ANSWER WAS PRECEDENT, NOT NEW MACHINERY.
    # It said re-registering `_shelf_activate()` needs "a `settle_shape` that tolerates a growing
    # document, or a shelf that stops building", and warned against simply widening the bound.
    # Neither was required. MEASURED across this file's targets: every one of the NINE live-console
    # surfaces — console, state-panel, heart, heart-fan, locks, advanced, advanced-shadow,
    # advanced-fleet, console-tabs — already declares `settles: False` with a `warmup`, because
    # "a live console never stops moving". Proving stillness is the wrong question on this page and
    # the file already knows it.
    # ⛔ AND `settles: False` IS NOT A WEAKER TEST HERE, because the arrival proof lives in
    # `activate` and is stricter than a settle: it refuses until #th-shelfov is unhidden AND has a
    # non-zero RECT (v2666's scar — the overlay reports height 0 inside a shut #theatre while
    # holding its full text) AND the river has actually painted, accepting `.shr-bad` so a console
    # whose river ask FAILS is still photographed rather than being unreachable. That is the exact
    # shape the settle comment itself endorses: "a target that measures a document rather than a
    # widget states its own arrival test in `activate`, which runs separately and CAN fail".
    # ⚠⚠ `_shelf_activate()` STAYS UNREGISTERED — AND THE BLOCKER IS NOW MEASURED, NOT GUESSED.
    # The old note here said it needed "a `settle_shape` that tolerates a growing document, or a
    # shelf that stops building". That was not it. v2795 built the target, ran it, and the numbers
    # say something else entirely:
    #     the DOOR is fine now      clicks=2 · theatre=open · th-shelfov=present+shown · rect=1044x906
    #     the ROUTE is fast          /api/river 0.18s over HTTP; reel_router.route() 0.2s over 40 reels
    #     the machine is fine        load 3.92 on 10 cores
    #     and yet                    shr-wait=YES · says: "reading the river…" past a 12.3s poll
    # So the strip is never ASKED. `_shRiverLoad`'s caller sits behind the shelf's card render, and
    # `_shSort()` returns early when there is no `.sh-grid` — in the harness's sandbox world the
    # grid the river branch depends on is not there to reach. A target that cannot be satisfied by
    # the fixture is [[feedback-blind-fixture-green-gate]]: registering it would ship a permanently
    # red gate, and widening its bound would ship a permanently UNKNOWN one. Both are furniture.
    # ⇒ WHAT REGISTERING IT NEEDS: a seeded shelf in the sandbox (sessions.jsonl is already in
    #   render_check's copy list, so the reels exist — what is missing is the grid actually being
    #   built for them), or the empty-world path resolving the strip instead of leaving it
    #   "reading". The staged target block is kept verbatim in the v2795 notes so the next attempt
    #   starts from the working door rather than rebuilding it.
    # ⚠ THE WORK THAT DID LAND IS IN `_shelf_activate` ABOVE AND IS NOT REVERTED: the one-shot
    #   click became a bounded retry (a one-shot that misses is a permanent refusal wearing a slow
    #   one's clothes), the `_toTVD()` route-out no longer hides behind a `data-view` attribute a
    #   freshly served console does not have, and the whole chain is now instrumented so the next
    #   refusal names its own cause instead of costing a round.
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
        # RAW on purpose: this block holds JS regexes (`/FULL|needs \d+ mules/` below). Unraw, `\d`
        # is an invalid Python escape — silent on 3.9 here, a VISIBLE SyntaxWarning on CI's 3.12.
        # That warning went to stderr, and run_gates derived a gate's skip reason from
        # stdout+stderr, so the warning's source echo DISPLACED crest_loudness's declared
        # "no Chrome" line and turned a declared skip into an undeclared one. Cost: test_control
        # red on CI, green here, for four ships.
        "activate": r"""(function(){
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
    # ⚠⚠⚠ THE PAGE ITSELF, AND IT IS HERE BECAUSE EVERY OTHER TARGET IS A NAMED SUBTREE.
    # Measured 2026-09-05: all eleven selectors below name specific nodes — `console` is
    # `#btn-mini, #btn-miniauto`, so its `painted 1/1 · clipped 0 · off 0 · covered 0` was a
    # statement about ONE BUTTON and was never a claim about the page. A cold second-eye read of
    # the 375px screenshot found `ON AIR`/`MINI` stacked with text cut off, the AI reads bar
    # rendering "appea / here", and "Failed to fetch" sliced mid-word — every one confirmed by
    # eye, and every one OUTSIDE all eleven selectors and therefore structurally invisible to this
    # harness. A gate reporting clean on a page with visible clipping is [[regression-guard]]'s
    # SAMPLE ≠ VERDICT landing on the visual gate itself. [[visual-regression-detector]]
    #
    # ⚠ `body > *`, NOT `body *`. The probe expands each matched node to `[e] + e.querySelectorAll('*')`,
    # so matching every element would walk every subtree once per ancestor — O(n²) on an 11,806-node
    # document. Matching the top-level containers covers exactly the same nodes ONCE.
    #
    # ⚠⚠ AND IT REUSES `_PROBE` RATHER THAN ASKING ITS OWN QUESTION, which is the whole reason to
    # trust the number. A hand-rolled page sweep written for this finding counted 14 cut elements
    # at every width and was NOT published, because it honoured none of the recovery paths this
    # probe already knows: the scroller exclusion (v2381 — ink one flick away is not destroyed),
    # `title` recovery (v2432 — the full string is reachable), `inert()` (opacity-0 controls),
    # and the fixed-position escape with its transform/filter/contain re-anchoring (v2381 — 31
    # false reds from one missing rule). A second implementation of a measurement is a second
    # thing to be wrong. [[copy-drift]] [[feedback-suspect-the-instrument]]
    "page": {
        # ⚠⚠ SERVED, NOT `file://`, AND MY FIRST CUT COPIED `console`'S ORIGIN TOO. Over file://
        # every root-absolute `/art/...` src resolves to `file:///art/...`, cannot load, and each
        # tag runs its own onerror — several of which REMOVE the element. Measured: the harness
        # reported `imgs 12/12 broken` at every width, which is a fact about the ORIGIN and not
        # about his console; served, the same page carries 2,399 images of which 4 are broken.
        # `broken` is a REFUSAL field, so the file:// origin alone would have turned this target
        # permanently red on twelve images that are fine. Six other console targets already serve
        # for exactly this reason. [[borrowed-surface]] [[feedback-suspect-the-instrument]]
        "serve": True,
        "why": "THE WHOLE CONSOLE PAGE — every other target is a named subtree, so nothing here "
               "has ever measured the parts between them",
        "seed": """(function(){ return 1; })()""",
        # ⚠⚠ THE PAGE IS ARRIVED, NOT ACTIVATED — AND ARRIVAL IS PROVEN FROM A RECT. My first cut
        # returned `body.children.length > 2`, and `test_control`'s
        # `test_activation_is_proven_from_the_RECT_not_from_the_call_returning` took it RED for
        # exactly the right reason: *"target 'page' calls a painter and trusts it. A painter that
        # runs and paints nothing must not read the same as an open panel."* A document can have
        # eight children and lay out none of them — measured on this very page, 6 of its 9
        # top-level children are zero-size (six closed modals, the sixth added by v3016) — so a
        # COUNT cannot tell a
        # rendered console from a collapsed one, which is the false green a whole-page target
        # would multiply across the document.
        # So: the body must have real area, and at least two top-level children must have real
        # rects of their own. Two, not one, because a single painted node is also what a page that
        # rendered only its shell looks like.
        "activate": """(function(){
            var b = document.body; if (!b) return false;
            var br = b.getBoundingClientRect();
            if (br.width < 2 || br.height < 2) return false;
            var painted = 0;
            var kids = [].slice.call(b.children);
            for (var i = 0; i < kids.length; i++){
                var r = kids[i].getBoundingClientRect();
                if (r.width > 2 && r.height > 2) painted++;
            }
            return painted >= 2; })()""",
        # ⚠ TAGS THAT NEVER RENDER ARE EXCLUDED, HIDDEN OVERLAYS ARE NOT. `script` and `style` are
        # zero-size by definition and counting them as a collapse is noise; the five `display:none`
        # modals (`#th-dossier-ov`, `#th-compare-ov`, `#th-heatmap-ov`, `#forensics-ov`,
        # `#ch-modal`) are LEFT IN on purpose, because "this overlay is closed" and "this overlay
        # collapsed" are the same measurement from outside and the probe should say so rather than
        # have me decide for it. Measured at 1440: 11 children -> 3 painted, 2 script, 1 style,
        # 5 hidden modals.
        "sel": "body > *:not(script):not(style):not(template):not(noscript)",
        # ⚠⚠ IT MUST SETTLE, AND MY FIRST CUT SET THIS TO False BY COPYING `console`. That target
        # skips the settle because its two named buttons re-time their own labels. The PAGE target
        # measures the whole document, and `_settle`'s own docstring says exactly why skipping it
        # is fatal here: *"a partial page reports zero clipping, zero overflow and zero covers,
        # which is the exact false green this file exists to refuse."*
        # MEASURED, and the gap is not small. Unsettled, the run reported `clipped 3` at 375 and
        # `imgs 12/12 broken`. Driving the SAME probe against a loaded page: `clipped 54` at 375,
        # `clipped 5` at 901, and `imgs 2399` of which only **4** are broken. So the unsettled run
        # under-counted the clipping seventeen-fold AND turned "the images have not loaded yet"
        # into "every image is broken". Copying a flag without asking whether its reason applies
        # is how a new instrument inherits an old one's exemption. [[feedback-suspect-the-instrument]]
        # ⚠⚠⚠ THE BACKLOG THIS TARGET FOUND ON ITS FIRST RUN, DECLARED SO IT CANNOT HIDE AND
        # CANNOT BLOCK. Measured 2026-09-05 on the SERVED console, all five widths:
        #
        #     1440x1000   clipped  1     |  broken: NOT RATCHETED, see below
        #     1120x900    clipped  1     |
        #     1120x628    clipped  1     |
        #      901x900    clipped  5     |
        #      375x800    clipped 54     |
        #
        # Every one is PRE-EXISTING and none was visible to any target before this one, because
        # all eleven others measure named subtrees. A cold second-eye read of the 375 screenshot
        # named several of them independently ("appea / here", "Failed to fetch" sliced mid-word,
        # ON AIR and MINI stacked with text cut off) and I confirmed those by looking.
        # ⚠ THIS IS A FLOOR, NOT AN EXEMPTION. Every count above is printed in full on every run;
        # the target refuses the moment one RISES, and reports loudly when one FALLS so the floor
        # gets lowered rather than quietly excusing work someone already did. Fixing the 54 is its
        # own task with its own pixels and its own second eye — it is not something to be smuggled
        # into whatever else is shipping. [[regression-guard]] [[unknown-stays-unknown]]
        # ⚠ v2677 — RE-BLESSED AGAINST A WORLD THAT IS NOW PINNED, AND THE RISE IS NAMED, NOT HIDDEN.
        # 901x900 5 -> 6 and 375x800 54 -> 55. That is a RISE, which this target refuses on purpose,
        # so it is justified here rather than quietly absorbed:
        #
        #   · The old numbers were measured with a NO-OP seed — `(function(){ return 1; })()` — so
        #     this target rendered whatever the browser profile happened to hold. Measured: the same
        #     unchanged tree reports 5 in one world and 6 in another. A floor over an undefined world
        #     is not a floor; it is whatever was in localStorage the day it was written.
        #   · The seed above now pins the owner world, and the result is STABLE: two consecutive
        #     runs both report 6 / 55.
        #   · BISECTED BEFORE RE-BLESSING: `git checkout 0c5e65ea -- bible.html tv/control_ui.html`
        #     and re-rendered — the SHIPPED surfaces report the same 6 / 55. The rise is not the
        #     work being shipped alongside it.
        #   · The extra elements are NAMED so nothing hides behind the number: at 901
        #     `tf-t :: Chronicle Uniques — 403 left` and `tf-chron-note :: — 403 left to hunt`, at 375
        #     `home-dash :: 📖 full bible →`. All are `.sc-tf-t`-class rows carrying
        #     `text-overflow: ellipsis` — they are DESIGNED to cut, and how many render depends on
        #     world state, which is exactly what pinning the seed fixes.
        #
        # ⚠ This does NOT excuse the backlog. 55 elements are still cut at 375 and fixing them is
        # still its own task with its own pixels and its own second eye.
        # [[regression-guard]] [[feedback-blind-fixture-green-gate]] [[unknown-stays-unknown]]
        # ⚠⚠ v3019 — `zero` 5 -> 6: A SIXTH CLOSED MODAL EXISTS. The floor of 5 was never an
        # arbitrary tolerance — the note above states exactly what it counts: "5 of its 8 top-level
        # children are zero-size (five closed modals)". v3016 added a sixth, `#th-tomb-ov`, the
        # Released panel's overlay, and it is byte-for-byte the same shape as the three it sits
        # beside (`th-dossier-ov`, `th-compare-ov`, `th-heatmap-ov`): an empty div carrying `hidden`
        # until its opener fills it.
        #
        # MEASURED, so the raise is not taken on trust: empty hidden overlay divs number 3 at
        # origin/main and 4 in this tree, and the page target reported "6 of 9 node(s) are
        # ZERO-SIZE ... DECLARED FLOOR IS 5, this is 1 MORE". One node, one modal, accounted for.
        #
        # ⚠ RAISED BY HAND RATHER THAN BY `--bless`, deliberately. --bless refused this very run —
        # "this run did not report every target, and a partial run must never write a LOWER floor" —
        # because `page` was the red target, so blessing could not run until the thing it would fix
        # was already fixed. Raising the one value the measurement names keeps every OTHER floor
        # exactly where it is; a blanket bless would also have moved five coverage floors in the
        # same commit and buried this one-node change among them. [[regression-guard]]
        "known": {
            "1440x1000": {"clipped": 1, "broken": None, "zero": 6},
            "1120x900":  {"clipped": 1, "broken": None, "zero": 6},
            "1120x628":  {"clipped": 1, "broken": None, "zero": 6},
            "901x900":   {"clipped": 6, "broken": None, "zero": 6},
            "375x800":   {"clipped": 55, "broken": None, "zero": 6},
        },
        "settles": True,
        # ⚠ THE SHAPE PREDICATE, not the byte-length one. This page carries a live clock and
        # re-timed "last seen" strings, so `innerHTML.length` never repeats and the target sat
        # UNKNOWN for the whole 25s budget on every run. Layout depends on how many elements exist
        # and whether images have resolved; it does not depend on what second it is.
        "settle_shape": True,
    },
    "console": {
        "page": os.path.join("tv", "control_ui.html"),
        "why": "the CONSOLE's own action row — the buttons he actually reaches for",
        # ⚠ v2677 — THIS SEED WAS A NO-OP, AND THAT MADE THE FLOOR BELOW WORLD-DEPENDENT.
        # `(function(){ return 1; })()` establishes NOTHING, so this target rendered whatever
        # the browser profile happened to be holding. Measured: the same tree reports
        # `clipped 5` in one world and `clipped 6` in another, so the gate passed or blocked a
        # push according to leftover localStorage rather than the page. Every other target that
        # needs the owner world seeds it explicitly; this one — the only one that measures the
        # WHOLE page — did not. A floor is only a floor if the world under it is fixed.
        # [[regression-guard]] [[feedback-blind-fixture-green-gate]]
        "seed": """(function(){ localStorage.setItem('d2r_ownerClaim','*'); return 1; })()""",
        "activate": """(function(){
            /* v2856 — WAS btn-miniauto, REMOVED BY HIS RULING (REG-823). This target is "the
               buttons he actually reaches for", and anchoring it on a button that no longer
               exists made the whole surface UNMEASURED — which the coverage ratchet refused
               rather than passing quietly, exactly as it should. */
            var b = document.getElementById('btn-on');
            if (!b) return false;
            // it must not be inside a COLLAPSED details — that is how it hid for three rounds
            for (var q = b.parentElement; q; q = q.parentElement){
                if (q.tagName === 'DETAILS' && !q.open) return false;
            }
            var r = b.getBoundingClientRect();
            return !!(r.width > 2 && r.height > 2); })()""",
        "sel": "#btn-on, #btn-mini",
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
    # ══ v2428 — THE ADVANCED DRAWER, ON PIXELS. Konyo, 2026-09-02: "the Advanced setting i
    # suddenly cant see the advanced grok eyes and the fleet. it slike hidden.. make sure this is
    # watchdogs control too.. visually pixel wise and backend". The backend half is
    # tv/live_panel_gate.py reading uiBeat.advFill; this is the pixel half, and it needs BOTH
    # because they fail differently: the beat can say a drawer filled while it renders as a black
    # column, and this can photograph a drawer that is laid out perfectly and carries placeholder
    # copy. Neither instrument is the other's proof.
    #
    # ⚠ IT MUST BE SERVED. Under file:// the fleet is a fetch to /api/fleet that cannot resolve, so
    # the drawer renders its "unreachable" branch and a target would refuse on every run — the
    # exact mistake the note above says a `tvd` target already made and got deleted for.
    # ══ v2539 — ♥ THE HEART, ON PIXELS. Konyo, 2026-09-04: "connect it to the heart of the
    # console that way we would have caught it". A reading joined to the heart payload and never
    # photographed is half a join: `deadFields` can be perfect in /api/heart and render as nothing
    # at all, which is exactly how a section comes to exist only in the backend. This panel has had
    # sections added to it for twenty versions with no target watching any of them.
    #
    # ⚠ IT MUST BE SERVED. _heartOpen() fetches /api/heart; under file:// that cannot resolve and
    # the panel paints its unreachable branch, so a file:// target would refuse on every run — the
    # mistake the `tvd` target already made and got deleted for, recorded above.
    "heart-fan": {
        # #53 — the solver's own record, written by `_hrtFanFit` onto the overlay. `reverted` is
        # the whole question: false means it found a placement and KEPT it; true means it found one
        # and put everything back, which is the all-or-nothing revert the task names.
        "report": ("(function(){ var o=document.querySelector('#heart-ov'); if(!o) return null;"
                   " var a=o.getAttribute('data-fanfit'); if(!a) return null;"
                   " try { return JSON.parse(a); } catch(e) { return {unparsed:String(a).slice(0,200)}; } })()"),
        # ⚠⚠ v2925 — THE FAN'S OWN CAVEAT, DECLARED WHERE THE FAN IS DECLARED.
        # MEASURED 2026-09-11: `_hrtFanFit` has exactly ONE call site in control_ui.html (the
        # heart-open path), and the page's ONLY resize listener calls `_shellSizePane()` and
        # nothing else. So `data-fanfit` is written ONCE, at open, and is never recomputed when
        # the window changes size — which means `readAt` names the width this harness READ at,
        # and the width the fan SOLVED at is genuinely unknown. Say so, rather than let a
        # per-width key imply a per-width verdict. [[stale-reading]] [[unknown-stays-unknown]]
        "reportNote": {
            "solvedAt": "UNKNOWN — the fan solves once on open and never re-solves on resize, "
                        "so this reading is from whatever width the heart was opened at, not "
                        "from the one named in readAt",
        },
        "serve": True,
        "why": "♥ THE HEART'S LOCK FAN — the half of the panel nothing was photographing. The "
               "`heart` target's selector is `.hrt-h, .hrt-row`, which is TWO of the panel's "
               "fourteen text classes, so the radial lock fan was never in any shot. That is why "
               "[[heartov2]] survived three fixes: overlap_ratchet can see the fan and is "
               "baselined at 2 (green forever, and it cannot run on CI at all), the render gate "
               "never photographed it, and the second eye is shown the render gate's pixels — "
               "four instruments, not one able to raise it. Asked cold about overlaps on a heart "
               "shot, a different model family answered that the labels are ABSENT FROM THE "
               "FRAME. They were",
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            /* the SAME opener overlap_ratchet drives, so the two instruments finally agree on
               what they are looking at: PANELS uses `#heart-chip`.click(). Idempotent on purpose —
               the harness re-runs this every 0.4s, so it must never toggle. */
            var ov = document.getElementById('heart-ov');
            if (!ov) return false;
            if (ov.hidden || getComputedStyle(ov).display === 'none') {
                var c = document.getElementById('heart-chip');
                if (!c) return false;
                c.click();
                return false;
            }
            /* CONTENT, not just a rect: the fan is what this target exists for, so refuse until
               the fan's own classes are actually present. An open panel with no fan would
               photograph as a clean pass and measure nothing. */
            /* ⚠ PROVEN FROM THE RECT, NOT FROM A COUNT. A gate already in this repo caught the
               first cut of this target for exactly that:
               test_activation_is_proven_from_the_RECT_not_from_the_call_returning. Counting
               elements proves they EXIST; it does not prove they were laid out, and this very
               target measured two `.hrt-w` nodes that exist at ZERO SIZE. An activate that
               returns true on a collapsed panel photographs a blank and reports a clean pass —
               which is the empty-box defect the whole file is built against. So: the overlay must
               have a box, AND enough fan nodes must have a box of their own. */
            var r = ov.getBoundingClientRect();
            if (!(r.width > 2 && r.height > 2)) return false;
            var fan = [].slice.call(ov.querySelectorAll('.hrt-k, .hrt-w, .hrt-s, .hrt-chain, .hrt-grp'));
            var laid = 0;
            for (var i = 0; i < fan.length; i++) {
                var fr = fan[i].getBoundingClientRect();
                if (fr.width > 1 && fr.height > 1) laid++;
            }
            return laid >= 6; })()""",
        # The classes the `heart` target does NOT cover. Deliberately NOT a replacement: `heart`
        # photographs the chronicle routes, a different surface with its own value, and its text
        # begins "The chronicle routes - 3 - source -> generator -> roster -> freshness ->".
        "sel": "#heart-ov .hrt-k, #heart-ov .hrt-w, #heart-ov .hrt-s, #heart-ov .hrt-note, "
               "#heart-ov .hrt-chain, #heart-ov .hrt-grp, #heart-ov .hrt-legend, "
               "#heart-ov .hrt-sec, #heart-ov .hrt-head, #heart-ov .hrt-win, "
               # ⚠⚠ THE FAN ITSELF, AND IT WAS MISSING FROM THE FIRST CUT OF THIS TARGET.
               # I built this target to photograph the lock fan and then chose its classes by
               # WIDENING from the old target's two — twelve of the fourteen `hrt-*` names — and
               # the fan was not in that vocabulary at all. Picking more of the wrong list is not
               # picking the right one.
               # The answer was in this target's OWN first run: its 375px clip warning named the
               # element, `hrt-svgwrap :: miniauto.run — INCOMPLETE —`. It appeared there because
               # `clipped` walks [e] + e.querySelectorAll('*'), so a DESCENDANT is clip-scanned
               # even when it is not in `sel` — two populations in one target, the same split that
               # produced the wrong denominator in REG-668.
               "#heart-ov .hrt-svgwrap",
        "settles": False,
        "warmup": 10.0,
        # ⚠ DECLARED PER WIDTH, AND NAMED SO IT IS NOT A BLANK CHEQUE. Two `.hrt-w` nodes carry
        # no text at all, so they have no box — measured identically at all five widths, which is
        # structural rather than a race, and the probe now NAMES them ("hrt-w :: " with nothing
        # after the separator) instead of leaving a reader to bisect the selector. They are empty
        # CONTAINERS, not a collapse: nothing is clipped or covered (0/1613 scanned, 0/260).
        # The floor is 2 and the gate refuses the moment a THIRD collapses — which is the case
        # that would actually mean something.
        "known": {
            "1440x1000": {"zero": 2},
            "1120x900":  {"zero": 2},
            "1120x628":  {"zero": 2},
            "901x900":   {"zero": 2},
            # ⚠⚠ 375 CARRIES ONE CLIPPED ELEMENT, AND IT IS DEBT, NOT A PASS.
            # The FIRST run of this target found it: `hrt-svgwrap :: miniauto.run — INCOMPLETE —`
            # has text cut off inside it at 375px. Nothing was watching this surface, which is the
            # whole reason the target exists, and it found something in its first minute.
            # It is declared so the gate can go green on the KNOWN state and refuse a SECOND —
            # but a declared floor is how [[heartov2]] sat on his screen through three fixes
            # ("baseline 2 now 2, held" forever), so this one is filed as an open row rather than
            # absorbed here. Lower it the moment the clip is fixed; never raise it.
            # ⚠ 2, NOT 1 — AND I SHIPPED THIS RED BECAUSE I DID NOT RE-READ THE VERDICT.
            # Adding `.hrt-svgwrap` to `sel` made the wrapper a MATCHED element, which widened the
            # clip scan from 1613 nodes to 1853, and a SECOND clipped label appeared. Both are the
            # same text — `hrt-svgwrap :: miniauto.run — INCOMPLETE —`, each failing its own
            # self-check. After that edit I checked `painted` and ran the coverage test, and never
            # looked at the target's own verdict. [[exit-status-of-the-block]]: run the check AND
            # READ IT, in the same breath.
            # ⚠ IT SHIPPED BECAUSE THE RENDER GATE DID NOT RUN. That push touched only .py files,
            # so pre-push skipped render entirely — meaning a change to render_check.py, THE
            # GATE'S OWN DEFINITION, does not re-run the gate. Filed separately; it is not fixed
            # by this line.
            # Still DEBT, not a pass — lower it when the label stops overflowing, never raise it.
            "375x800":   {"zero": 2, "clipped": 2},
        },
    },
    "heart-stored": {
        "serve": True,
        # ⚠ SAME VENUE DECLARATIONS AS ITS SIBLINGS, AND MY FIRST CUT OMITTED BOTH. This panel
        # ANIMATES — the chip beats and the fan draws — so a settle-by-size check can never
        # converge: the target refused with "the page never settled in 25s, readyState/size kept
        # moving" and never reached activation at all. `heart` and `heart-fan` both carry
        # settles=False + warmup=10.0 for exactly that reason. Copying a target's mechanics without
        # its venue facts is how a harness measures its own impatience.
        "settles": False,
        "warmup": 10.0,
        "why": ("♥ THE STORED HALF OF THE HEART — the census row, IN FRAME. `heart-fan` reports "
                "275/277 painted and the instruments section is in NEITHER of its shots, because "
                "the panel SCROLLS and that section renders below the fan. A paint count measures "
                "DOM rects; it does not prove a thing is in the picture, and this panel has already "
                "taught that once: the lock fan survived three fixes while every instrument called "
                "it clean. So this target scrolls the section into view and refuses until its own "
                "row is inside the viewport, which is the only form of the question a screenshot "
                "can answer. It exists because the stored half is the one that can go stale — "
                "heart2 writes tv/.heart2.json and nothing but a human running --ratchet refreshes "
                "it, so its age and its PARTIAL flag are exactly what a reader must be able to see"),
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            /* IDEMPOTENT — the harness re-runs this every 0.4s, so it must never toggle. */
            var ov = document.getElementById('heart-ov');
            if (!ov) return false;
            if (ov.hidden || getComputedStyle(ov).display === 'none') {
                var c = document.getElementById('heart-chip');
                if (!c) return false;
                c.click();
                return false;
            }
            /* ⚠⚠ v2896 — BY THE ID `sel` NAMES, NOT BY HEADING COPY. Raised by the cross-family
               eye on v2892: this walked `.hrt-sec` headings for /instruments still go red/i while
               `sel` selects `#hrt-instruments` — and that id was added IN THE SAME COMMIT because
               a previous selector photographed the wrong section. Activate was never pointed at
               it. Reword the heading and `want` stays null forever: the target refuses with "the
               panel could not be ACTIVATED" about a node that is present, correct, and exactly
               where `sel` expects it. An activate and a sel that name different subjects are two
               targets wearing one name. [[label-outlived-referent]] [[the-unjoined-end]] */
            var want = ov.querySelector('#hrt-instruments') ||
                       document.getElementById('hrt-instruments');
            if (!want) return false;
            /* ⚠ PROVEN FROM THE RECT, IN THE VIEWPORT — not from scrollIntoView returning.
               Scrolling can be refused (a hidden or zero-height scroller) and the call still
               returns, so the only honest test is where the rect actually LANDED. */
            want.scrollIntoView({block: 'center'});
            var r = want.getBoundingClientRect();
            if (!(r.width > 0 && r.height > 0)) return false;
            /* ⚠ AGAINST THE SCROLLPORT THAT ACTUALLY CLIPS IT. The same eye: `.fx-body` is
               `overflow-y: auto` while the window is `overflow: hidden`, so a section can
               intersect the WINDOW while sitting above the overlay's own scrollport — in frame by
               this test, out of frame in the shot. Measure against the nearest scrolling ancestor
               when there is one, and fall back to the window when there is not. */
            var sc = want.closest('.fx-body') || ov;
            var box = (sc && sc.getBoundingClientRect) ? sc.getBoundingClientRect() : null;
            var top = box ? Math.max(0, box.top) : 0;
            var bot = box ? Math.min(window.innerHeight || 0, box.bottom) : (window.innerHeight || 0);
            if (!(bot > top)) { top = 0; bot = window.innerHeight || 0; }
            return (r.top < bot && r.bottom > top);
        })()""",
        # ⚠ v2905 (#68) — THE NEW ELEMENTS ARE IN THE SELECTOR, NOT JUST IN THE MARKUP. This
        # repo has now lost a surface three times by adding one and leaving it out of `sel`:
        # an unphotographed element reads exactly like a clean one, and losing it would be
        # invisible in a green run. `.hrt-hn` is the census figures under the question,
        # `.hrt-nw` are the welds that stop a figure ending a line without its noun, and
        # `.hrt-w > i` are the source labels that say WHICH gates the 285 counts.
        "sel": ("#hrt-instruments .hrt-k, #hrt-instruments .hrt-s, #hrt-instruments .hrt-w, "
                "#hrt-instruments .hrt-hn, #hrt-instruments .hrt-nw, "
                "#hrt-instruments .hrt-w > i"),
    },
    "heart": {
        "serve": True,
        "why": "♥ THE HEART — the panel that says which vessels are alive, which valves are open, "
               "which promises a lane can still break, and (v2539) which recorded fields have "
               "NEVER once been filled. Every one of those is a reading somebody acts on, and "
               "until now not one of them was photographed",
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            /* ⚠ CLICK THE CHIP, DO NOT CALL _heartOpen() BY NAME. It is exported on window here,
               but the state-panel target's own note records a first cut that called closure-local
               functions and got `undefined` while the panel was perfectly openable. Drive it the
               way he does. */
            var ov = document.getElementById('heart-ov');
            if (!ov) return false;
            /* ⚠⚠ CLICK ONLY WHILE IT IS SHUT, AND THE FIRST CUT DID NOT. The harness polls this
               expression every 0.4s for 12s; _heartOpen() paints a "taking the census…"
               placeholder, then fetches /api/heart (measured 4.5s) and replaces the panel. A cut
               that clicked unconditionally re-opened it on the very next poll after it finished,
               wiping the populated panel back to the placeholder — so the activate could NEVER
               observe the state it was waiting for, and refused for 12s on a panel that came up
               correctly every time. The instrument was the defect, not the surface. */
            if (ov.hidden) {
                var c = document.getElementById('heart-chip');
                if (!c) return false;
                c.click();
                return false;                 /* let the poll come back once the fetch lands */
            }
            /* PROVE IT FROM THE RECT AND FROM THE CONTENT. An overlay with a frame and no
               sections is the empty-box defect an author cannot see, and it would photograph as a
               clean pass. */
            var r = ov.getBoundingClientRect();
            var secs = ov.querySelectorAll('.hrt-h').length;
            return !!(r.width > 2 && r.height > 2 && secs >= 4
                      && getComputedStyle(ov).display !== 'none'); })()""",
        "sel": "#heart-ov .hrt-h, #heart-ov .hrt-row",
        "settles": False,
        "warmup": 10.0,     # /api/heart re-derives the census and the proof ledger on every open
    },

    # ══ v2568 — THE LOCK CHIPS, ON PIXELS. The last item on TASKS.md's "STILL OWED BY ME" list:
    # *"the new vault lock chip has no target at all. Unmeasured reads identical to clean in a
    # green run."* His ask was explicit — *"i want a visual lock on whats locked in the console
    # resembling the BACKEND coding lock for wilson score"* — and the markup declares FOUR chips:
    # lock-vault-tab, lock-vault, lock-miniauto, lock-prune.
    #
    # ⚠⚠ AND THIS SURFACE HAS ALREADY LOST ONE, SILENTLY. v2443 moved the mini-auto padlock inside
    # `<b id="miniauto-lbl">`, which `_miniLbl` rewrites with `textContent` on EVERY POLL — so the
    # stamp existed for a fraction of a second at load and was then destroyed for ever. On his
    # console it was simply ABSENT, on the one surface whose whole purpose is making the lock
    # known. A probe had counted THREE where the markup declares four and that was read past; a
    # cold cross-family look at real pixels is what named it.
    #
    # ⚠ IT MUST BE SERVED, and that is the entire point: under file:// the chips sit in the static
    # markup and all four are trivially present. The defect only exists once the polls run.
    "locks": {
        "serve": True,
        "why": "the THREE lock chips — vault tab, vault accumulator and the prune. A "
               "chip with NO state renders as `locked`, never as absent, because a missing badge "
               "reads as an OPEN lock and that is the one direction this must never fail in. This "
               "target exists because one of them was destroyed on every poll and nothing saw it",
        "seed": """(function(){ return 1; })()""",
        "activate": """(function(){
            /* ⚠⚠ THE FIRST TWO VERSIONS OF THIS TARGET REFUSED, AND BOTH TIMES IT WAS THIS
               INSTRUMENT AND NOT HIS CONSOLE. Measured cold over CDP on a served console:

                   lock-vault-tab  19x14  state=unproven  blockers=NONE
                   lock-vault       0x0   state=unproven  blockers=hd-vault[display:none]
                   lock-miniauto   21x16  state=open      blockers=NONE
                   lock-prune      19x14  state=open      blockers=NONE

               All FOUR chips exist and all four carry a real state. `lock-vault` measures 0x0
               because its SECTION is display:none — a badge on a pane that is not the open one,
               which is the disclosure working. Demanding that all four paint at once measured
               WHICH PANE STARTS ACTIVE, a thing this target was never asked about and one that
               would refuse the moment a default changed. [[feedback-suspect-the-instrument]]

               So the contract is split, because two different questions were wearing one rect:

                 · DESTRUCTION and STATELESSNESS are asked of ALL FOUR here, in the DOM. That is
                   the v2443 defect — the mini-auto padlock was moved inside a <b> that _miniLbl
                   rewrites with textContent every poll, so it existed for a fraction of a second
                   at load and was then destroyed for ever. A count catches that; a rect cannot,
                   because a destroyed node has no rect to be wrong.
                 · COLLAPSE is asked only of the chips actually on screen, marked below so `sel`
                   names them without hard-coding an id that rots when the panes are rearranged.

               A chip with NO state is the dangerous direction and is refused here: the UI paints
               a missing badge as `locked`, so an absent state reads as a LOCK THAT IS OPEN.
               [[unknown-stays-unknown]] */
            var all = document.querySelectorAll('.lockchip');
            /* v2856 — WAS 4. mini-auto's chip went with MINI(AUTOMATIC), REG-823. Measured after
               the removal: lock-vault, lock-vault-tab, lock-prune. The guard still does its job —
               it catches a chip DESTROYED by a poll, the v2443 defect this target exists for;
               only the denominator moved. [[zero-needs-a-denominator]] */
            if (all.length < 3) return false;          /* one was destroyed by a poll */
            var onscreen = 0;
            for (var i = 0; i < all.length; i++){
                var e = all[i];
                if (!(e.getAttribute('data-state') || '').trim()) return false;
                for (var n = e.parentNode; n && n.nodeType === 1; n = n.parentNode){
                    if (n.tagName === 'DETAILS' && !n.open) n.open = true;
                }
                var hidden = false;
                for (var m = e.parentNode; m && m.nodeType === 1; m = m.parentNode){
                    var cs = getComputedStyle(m);
                    if (cs.display === 'none' || cs.visibility === 'hidden'){ hidden = true; break; }
                }
                if (hidden) continue;
                var r = e.getBoundingClientRect();
                if (!(r.width > 2 && r.height > 2)) return false;   /* visible AND collapsed */
                e.classList.add('lockchip-onscreen');
                onscreen++;
            }
            return onscreen > 0; })()""",
        # v2569 — WHICH of the three conditions refused. Same walk as `activate`, reporting
        # instead of deciding, so the two cannot drift into disagreeing about the same DOM.
        "activateWhy": """(function(){
            var all = document.querySelectorAll('.lockchip');
            if (all.length < 3) {
                var seen = [].slice.call(all).map(function(e){ return e.id || '?'; });
                return 'DESTROYED: the markup declares 3 lock chips and only ' + all.length
                     + ' survive in the DOM. Survivors: ' + (seen.join(', ') || 'none')
                     + ' — whichever declared chip is absent from that list is the one a poll ate. '
                     + 'This is the v2443 defect: a poll rewrote a label with textContent and took '
                     + 'the padlock inside it with it.';
            }
            var stateless = [], collapsed = [], onscreen = 0;
            for (var i = 0; i < all.length; i++){
                var e = all[i];
                if (!(e.getAttribute('data-state') || '').trim()) { stateless.push(e.id || '?'); continue; }
                var hidden = false;
                for (var m = e.parentNode; m && m.nodeType === 1; m = m.parentNode){
                    var cs = getComputedStyle(m);
                    if (cs.display === 'none' || cs.visibility === 'hidden'){ hidden = true; break; }
                }
                if (hidden) continue;
                onscreen++;
                var r = e.getBoundingClientRect();
                if (!(r.width > 2 && r.height > 2))
                    collapsed.push((e.id || '?') + ' ' + Math.round(r.width) + 'x' + Math.round(r.height));
            }
            if (stateless.length)
                return 'STATELESS: ' + stateless.join(', ')
                     + (stateless.length === 1 ? ' carries' : ' carry') + ' no data-state. The UI '
                     + 'paints a missing badge as `locked`, so an absent state reads as a LOCK '
                     + 'THAT IS OPEN.';
            if (collapsed.length)
                return 'COLLAPSED: ' + collapsed.join(', ') + ' are on a VISIBLE pane and still '
                     + 'measure 0x0 — present in the DOM, invisible to him.';
            if (!onscreen)
                return 'NONE ON SCREEN: all 4 chips exist but every one sits on a hidden pane, so '
                     + 'there was nothing to photograph. That is not a defect in the chips.';
            return 'all four chips are present, stated and painted — if this refused, the '
                 + 'instrument disagrees with itself and the instrument is the suspect.'; })()""",
        "sel": ".lockchip-onscreen",   # stamped by activate: the chips actually on screen
        "settles": False,
        "warmup": 12.0,     # long enough for the label poll that once destroyed one of them
    },

    "advanced": {
        "serve": True,
        "why": "the ⚙ ADVANCED drawer — the EYES switch, the shadow reader and THE FLEET. It sits "
               "1,026px deep in a 430px rail, so it is off-screen until scrolled, and for 238 "
               "versions its fleet held placeholder copy because _fleetRefresh did not exist when "
               "the inline ontoggle fired during parse",
        "seed": """(function(){ try { localStorage.setItem('d2r_advOpen','1'); } catch(e){} return 1; })()""",
        "activate": _adv_activate("g5-eyes-card"),
        "sel": "#g5-eyes-card",
        "settles": False,   # the fleet re-times its "last seen" strings; it never fully stills
        "warmup": 10.0,     # /api/fleet must answer before there is anything to photograph
    },

    # ⚠ THREE TARGETS AND NOT ONE, AND THE REASON IS A FALSE POSITIVE THIS HARNESS PRODUCED ON ITS
    # FIRST RUN. The first cut listed all three sections in one `sel` and scrolled the DRAWER to the
    # top of the rail. The drawer is 1,026px tall inside a 430px scroller, so #shadow-adv landed at
    # y=534..670 — entirely below the rail's visible box (bottom 533) — and the cover probe sampled
    # a point inside that rect which lands over the ticker band at 544..582. It reported
    # "ticker over shadow-adv".
    #
    # MEASURED, and it refutes the label: rail bottom 533, ticker top 544, railOverflowsTicker
    # FALSE. Nothing covers anything. getBoundingClientRect returns the LAYOUT rect and knows
    # nothing about an ancestor's overflow clip, so an element scrolled out of its own scroller
    # still reports a rect sitting wherever the layout put it. The instrument was right that
    # something was wrong with the reading and wrong about what. [[feedback-suspect-the-instrument]]
    #
    # A section can only be judged when it is actually inside its scroller, so each gets its own
    # target and its own scroll. Cheaper than teaching the harness about clipped ancestors, and it
    # covers the two sections he named by name - "the advanced grok eyes and the fleet".
    "advanced-shadow": {
        "serve": True,
        "why": "the ADVANCED drawer's SHADOW READER — what watches while he plays",
        "seed": """(function(){ try { localStorage.setItem('d2r_advOpen','1'); } catch(e){} return 1; })()""",
        "activate": _adv_activate("shadow-adv"),
        "sel": "#shadow-adv",
        "settles": False,
        "warmup": 10.0,
    },

    "advanced-fleet": {
        "serve": True,
        "why": "THE FLEET inside the ADVANCED drawer — the section that held placeholder copy for "
               "238 versions because _fleetRefresh was undefined when the inline ontoggle fired",
        "seed": """(function(){ try { localStorage.setItem('d2r_advOpen','1'); } catch(e){} return 1; })()""",
        "activate": _adv_activate("fleet-list", require_filled=True),
        "sel": "#fleet-list",
        "settles": False,
        "warmup": 10.0,
    },
    # ── v2843 (#55) — THE STATE THE CARD WAS ACTUALLY IN WHEN HE PHOTOGRAPHED IT ────────────
    # `advanced-fleet` above serves the real console, so it can only ever photograph a REACHABLE
    # fleet — and every regression this task fixed lives on the UNREACHABLE path. A surface the
    # harness cannot reach is a surface that regresses unseen, which is how the raw `_ssl.c:1112`
    # string sat on his card in the first place. [[gate-blind-to-unexercised-input]]
    #
    # ⚠ THE STUB IS THE POINT, AND ITS LIMIT IS NAMED. This target intercepts /api/fleet and
    # answers with a failure payload carrying a lastGood roster, because the live site will not go
    # down on request. It therefore proves the MARKUP AND LAYOUT of the degraded render — never
    # that the server actually produces that payload. That second half is a different question and
    # is guarded by test_the_fleet_lane_reaches_the_heart Law 5, which parses the handler.
    # [[feedback-blind-fixture-green-gate]] [[the-unjoined-end]]
    "advanced-fleet-down": {
        "serve": True,
        "why": "THE FLEET WHEN IT CANNOT BE REACHED — the state in his 2026-09-09 11:07 "
               "screenshot, where the card printed a raw <urlopen error _ssl.c:1112> while the "
               "console was holding a three-machine roster it never showed. Photographs the "
               "degraded path: humanised cause, hairline rule, and the remembered roster as "
               "dimmed chips. The payload is stubbed, so this proves the RENDER, not the wire",
        # ⚠⚠ CLEAR, STUB, THEN RE-ASK — AND THE FIRST CUT DID ONLY THE MIDDLE ONE, WHICH IS WHY
        # IT WENT GREEN PHOTOGRAPHING THE WRONG STATE. The harness loads the page and waits for it
        # to settle BEFORE running the seed, so `_fleetRefresh` has already fetched and painted the
        # REACHABLE card by the time this runs; installing a stub at that point changes nothing,
        # and `require_filled` then saw the stale healthy fill and passed instantly. Measured: the
        # target reported 🟢 with text `konyo-3 · v2843 · unpublished` — the success path, under a
        # name that says "when it cannot be reached". A fixture that cannot reach its own subject
        # is worse than no target: it occupies the slot and reports coverage.
        # [[feedback-blind-fixture-green-gate]] [[sabotage-is-usually-the-wrong-one]]
        "seed": """(function(){
            try { localStorage.setItem('d2r_advOpen','1'); } catch(e){}
            var _f = window.fetch;
            window.fetch = function(u, o){
              if (String(u).indexOf('/api/fleet') === 0) {
                return Promise.resolve(new Response(JSON.stringify({
                  ok: false, online: [], offline: [],
                  error: "<urlopen error _ssl.c:1112: The handshake operation timed out>",
                  lastGood: { online: [{machine:'Dean', ver:'v2745'}, {machine:'Konyo', ver:'v2745'}],
                              offline: [{machine:'Wife PC', ver:'v2101'}] },
                  lastGoodAgeS: 412
                }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
              }
              return _f.apply(this, arguments);
            };
            var _b = document.getElementById('fleet-list');
            if (_b) _b.innerHTML = '';
            if (window._fleetRefresh) { try { window._fleetRefresh(); } catch(e){} }
            return 1;
          })()""",
        # ⚠ AND THE GATE IS THE DEGRADED MARKUP ITSELF, NOT "is the box full". `require_filled`
        # cannot tell the healthy card from the unreachable one — both fill the box. This refuses
        # until `.fleet-dead` exists, so the target can only ever pass on the state it is named for.
        "activate": ("(function(){ var _b = (%s); if (!_b) return false; "
                     "return !!document.querySelector('#fleet-list .fleet-dead') "
                     "&& document.querySelectorAll('#fleet-list .fleet-stale-m').length === 3; })()"
                     % _adv_activate("fleet-list")),
        "sel": "#fleet-list, .fleet-dead, .fleet-was, .fleet-stale-m",
        "settles": False,
        "warmup": 10.0,
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
    # ══ v2664 — THE SEVEN CONSOLE TABS NOBODY EVER RENDERED ═══════════════════════════════════
    # MEASURED before this existed: control_ui.html carries EIGHT header tabs and exactly ONE
    # target loaded the console — `console` — whose activate is a READINESS PREDICATE about
    # #btn-miniauto, not a navigation. Seven of eight rendered at no width, so a layout regression
    # behind any of them shipped unseen. [[visual-regression-detector]]
    #
    # ⚠ ONE TARGET, NOT EIGHT, AND THAT IS A COST DECISION. `_serve_console()` is NOT memoised:
    # every "serve": True target boots its own control_app and waits for /api/status. Seven already
    # do. One target walking all eight tabs costs one boot and catches the same class.
    #
    # ⚠⚠ PROVEN FROM THE DESTINATION, NEVER THE BUTTON — that is v2125's scar, recorded in
    # control_ui.html itself: the banner lit its tab and scrolled to an element that was
    # display:none at height 0, "it scrolled to a hidden element and nothing moved".
    # `_shellLight()` stamps body.dataset.shellTab whether or not the board moved, so the STAMP
    # alone is not evidence. This reads the board's OWN `.tab.active` through the iframe and
    # requires the two to agree.
    #
    # ⚠ tvd IS ASSERTED TO DO THE OPPOSITE, and that is the design rather than an exemption —
    # control_ui.html:16139: `if (b.dataset.tab === 'tvd'){ …; shellHome(); return; }  // TV·D =
    # the cockpit home`. It stamps the route and deliberately leaves the board alone. I reproduced
    # that three times with settle time and was one commit from filing it as the v2125 defect.
    # So tvd must stamp itself AND leave the board where it was; a tvd that started routing fails.
    #
    # ⚠ THE SELECTOR IS THE LABEL SPAN, AND MY FIRST TWO CHOICES WERE BOTH WRONG. `#head-tabs .ht`
    # measures the buttons, whose verdict is dominated by their <img class="ht-i"> icons — that run
    # came back "imgs 5/8 broken" and RED while the pixels showed all eight icons rendering and
    # every file served 200. `#tvd-eng` is an <iframe>, whose text lives in another document, so it
    # reported "painted but carries NO TEXT". `.ht-lbl` was added for this: text-bearing, image
    # free, and one per tab.
    #
    # ⚠ FILE:// CANNOT DO THIS, WHICH IS WHY "serve" IS SET. The board arrives in an <iframe
    # id="tvd-eng" src="/board?app=1&engine=1&v=boot#session"> — an absolute server path. From the
    # filesystem it resolves to file:///board, never loads, and _shellRoute() returns false at
    # `if (!w || !w.document)`. Served, the iframe is same-origin and readable.
    "console-tabs": {
        "serve": True,
        "path": "",
        "warmup": 12.0,
        "settles": False,
        "why": ("Six tabs in the console header ROUTE THE BOARD and must PAINT what they route "
                "to, proven from the board's own active tab and the destination pane's rect "
                "rather than from the header lighting up. TWO are console-native and must do "
                "the opposite: session (the flagship hunt hub) and TV·D (the cockpit home) "
                "stamp themselves, leave the board where it was, and leave that room painted."),
        "seed": """(function(){ return 1; })()""",
        "sel": "#head-tabs .ht-lbl",
        "activate": r"""(function(){
            /* ⚠⚠ SIX ROUTE, TWO ARE CONSOLE-NATIVE — and I had session in the wrong group,
               which the rect check exposed. control_ui.html dispatches TWO tabs to console views
               that deliberately leave the board alone:
                   :16178  if (b.dataset.tab === 'session'){ showSessions(); return; }
                           // v1376 — Sessions = console-native flagship hunt hub
                   :16139  if (b.dataset.tab === 'tvd'){ …; shellHome(); return; }
                           // TV·D = the cockpit home
               showSessions() calls _shellDemotePane() and _shellRestoreConsole() and sets
               data-view="sessions" — it is a CONSOLE surface, not a board room.
               ⚠ MEASURED, because the first run looked like a defect twice over. Clicked FIRST,
               session reported active=session with a 0x3755 pane — only because the board BOOTS on
               session (src=…#session), so the click changed nothing. Clicked 4th and 8th it
               reported display:none with active still on the PREVIOUS tab. Both readings were the
               design, not a bug: the board never leaves the room it was in. */
            var ROUTING = ["forge","crafts","funi","fsets","tools","vault"];
            var CONSOLE_NATIVE = ["session","tvd"];
            var f = document.getElementById('tvd-eng');
            if (!f) return false;
            var d; try { d = f.contentWindow && f.contentWindow.document; } catch (e) { return false; }
            if (!d) return false;
            function active(){
                try { var a = d.querySelector('.tab.active');
                      return a ? a.getAttribute('data-tab') : null; } catch (e) { return null; }
            }
            /* the board must have BOOTED, or every comparison below runs against null and passes
               by accident on an empty iframe. UNKNOWN is not a pass. */
            if (!active()) return false;
            /* ⚠⚠ PROVE IT FROM THE RECT — the repo's law, and my first cut broke it.
               test_activation_is_proven_from_the_RECT_not_from_the_call_returning requires every
               activate to measure a real box, and it caught this one: reading `.tab.active` proves
               the board ROUTED and NOT that the destination PAINTED. v2125's defect was exactly a
               tab lighting up while its destination sat at display:none, height 0 — so
               `.tab.active === t` over a hidden pane would have passed. The pane is `#tab-<name>`
               (bible.html:27990: `_tabEl = $("tab-"+name)`), read inside the board's own document. */
            function paneRect(t){
                try { var el = d.getElementById('tab-' + t); if (!el) return null;
                      return el.getBoundingClientRect(); } catch (e) { return null; }
            }
            for (var i = 0; i < ROUTING.length; i++){
                var t = ROUTING[i];
                var b = document.querySelector('#head-tabs .ht[data-tab="' + t + '"]');
                if (!b) return false;
                b.click();
                if (document.body.dataset.shellTab !== t) return false;   /* the stamp */
                if (active() !== t) return false;                          /* the destination moved */
                var pr = paneRect(t);                                      /* AND it is really there */
                if (!pr || pr.width <= 2 || pr.height <= 2) return false;
            }
            /* ⚠⚠ THE CONSOLE-NATIVE PAIR DEMOTES THE BOARD — and my first cut asserted the
               OPPOSITE, requiring the room they left to stay painted. Measured: clicking session
               with the board on vault took tab-vault from 1384x122 to 0x122. That is not a bug, it
               is `showSessions()` calling _shellDemotePane() and _shellRestoreConsole() — collapsing
               the board pane IS what returning to a console view means. I asserted that a cockpit
               view must not blank the board, when blanking the board is its whole job.
               THE REAL LAW IS A BEFORE/AFTER, so it cannot pass on a pane that was already flat:
               promote a real board room first, prove it is painted, THEN prove the console-native
               tab stamps itself, leaves `active` alone, and DEMOTES that pane. */
            for (var j = 0; j < CONSOLE_NATIVE.length; j++){
                var ct = CONSOLE_NATIVE[j];
                /* re-promote a known board room, so the demotion below is a measured CHANGE */
                var anchor = document.querySelector('#head-tabs .ht[data-tab="vault"]');
                if (!anchor) return false;
                anchor.click();
                if (active() !== "vault") return false;
                var before = paneRect("vault");
                if (!before || before.width <= 2 || before.height <= 2) return false;
                var cb = document.querySelector('#head-tabs .ht[data-tab="' + ct + '"]');
                if (!cb) return false;
                cb.click();
                if (document.body.dataset.shellTab !== ct) return false;   /* it stamps itself */
                if (active() !== "vault") return false;                    /* board did NOT move */
                var after = paneRect("vault");
                if (!after || after.width > 2) return false;               /* and it DEMOTED the pane */
            }
            return true; })""" + """()""",
    },

    # ══ v2805 — 🌊 THE RIVER STRIP, ON PIXELS AT LAST. The surface he reads before deleting
    # footage, and nothing had ever photographed it.
    #
    # ⚠⚠ IT REFUSED TWICE FIRST, AND BOTH REFUSALS WERE THE HARNESS BEING RIGHT. "The panel could
    # not be ACTIVATED after 12.2s" at load 1.89 and 1.95 — not contention. Two guesses at the
    # cause were wrong; four CDP evaluations against a private console settled it, and the answer
    # was a LAYOUT fact hiding behind a scripting symptom:
    #
    #     window.thShelf   'function'     the opener was reachable after v2804 exported it
    #     thShelf(true)    -> hidden=false  it DID open the overlay
    #     .shr-lane        4              the river DID render its DOM
    #     every rect       0x0            and occupied no pixels whatsoever
    #
    #     #sh-lanes    0x0  display=block  hidden=false
    #     #th-shelfov  0x0  display=block  hidden=false   <- opened correctly
    #     #theatre     0x0  display=none   hidden=TRUE    <- THE COLLAPSE
    #     div.shell    1440x900
    #
    # THE SHELF LIVES INSIDE THE THEATRE, and the theatre is closed on a fresh console. So the
    # harness could open the panel and photograph nothing, and `thOpen` — the theatre's own opener
    # — was unexported for exactly the same reason `thShelf` was. Fixing one and not the other
    # fixes half a chain. Both exported in v2805; measured ACTIVATE TRUE at 1440, 901 and 375.
    "shelf-cards": {
        # ⚠⚠ `settles`, NOT A FIXED WARMUP — AND I LEARNED THIS THE WAY THE FILE ALREADY RECORDS.
        # Copied `warmup: 14.0` from river-strip, which watches ~21 nodes. This grid builds 533
        # CARDS. Measured twice on the SAME HEAD: 🟢 533/533 at all five widths on a quiet machine,
        # then 🔴 with "every one of 533 node(s) is ZERO-SIZE" at 901x900 and two widths that never
        # matched at all — while the second eye held the load average at 4.68. Same tree, opposite
        # verdicts, so it is the room and not the code. That is v2404's scar verbatim ("A FIXED
        # SLEEP HERE BLOCKED A LEGITIMATE PUSH ... the SAME tree rendered all six targets green
        # minutes later on a quiet machine"), and a flaky target is worse than no target because it
        # teaches people to re-run until green. [[ab-against-head-before-blaming-the-room]]
        # ⚠⚠ WARMUP, NOT `settles` — AND I SWAPPED THE WRONG WAY ONCE ALREADY. A fixed 14s went
        # flaky under load, so I moved to `settles: True`; the bless then refused with "the page
        # never settled in 25s — readyState/size kept moving". That is not load, it is this panel:
        # the shelf fills ASYNCHRONOUSLY from four directions (_shLanesLoad, _shStoryRender,
        # _shHighlights, the timeline), so the document is never quiet and a global settle can
        # never be satisfied here. `river-strip` watches the SAME overlay on a fixed warmup and is
        # green in every run — so the mechanism was proven on this panel and I left it for the one
        # thing it cannot do. Back to a warmup, with real headroom for a 530-card grid instead of
        # the 14s copied from a target that watches ~21 nodes.
        # ⚠⚠ 14s, AND THE CEILING IS THE GATE'S BUDGET, NOT THIS TARGET'S COMFORT. hooks/pre-push
        # runs `render_check.py` with NO arguments under a 300s kill (`gate_run "render" ... 300`),
        # so the WHOLE 18-target pass must finish inside it. Measured: a full pass takes ~4-5 min,
        # already at the edge — and at warmup 24 this one target spends 24s x 5 widths = 120s of
        # pure sleeping, 40% of the entire budget. The push died at target 17 of 18 with
        # "⏱ render HUNG — killed after 300s", and that was my doing: v2984 passed this step fine.
        # 14s is the value that rendered 533/533 green at all five widths on a quiet machine; the
        # earlier flakiness at 14 was the second eye holding the load at 4.68, which is a room
        # problem I now fix by not running the eye during a push rather than by paying 10 extra
        # seconds five times over. [[ab-against-head-before-blaming-the-room]]
        "serve": True, "path": "", "warmup": 14.0, "settles": False,
        "why": "\U0001f4da THE SHELF'S REEL CARDS \u2014 the things the panel is NAMED after, and "
               "nothing has ever photographed them. Every existing shelf target aims at the "
               "analytics: `river-strip` watches #sh-lanes, and the grid itself had no selector in "
               "any target. That is precisely how #58 survived \u2014 at his real 1120x660 the "
               "overlay is trapped in a ~449px stage with 549px of furniture above the first card, "
               "so the panel showed 0 of 530 cards while every instrument called the shelf green. "
               "A target that watches the chrome and not the content cannot see an empty room. "
               "\u26a0 IT MEASURES THE ON-AIR SHELF, i.e. the WORST case. _shLiveRender hides "
               "#sh-live unless `__lastStatus.__on` is true, and the harness's status stub sets "
               "it, so the 'Recording now' card is painted and counts toward the furniture above "
               "the first card. His console off-air (measured `mode: off`) shows LESS. Keeping the "
               "worst case is deliberate \u2014 a shelf that only works when he is not recording "
               "is still broken \u2014 but any y reported here is an UPPER BOUND on what he sees, "
               "never his everyday state.",
        "seed": """(function(){ return 1; })()""",
        # ⚠⚠ BOUNDED TO THE FIRST THREE CARDS, AND THAT IS THE WHOLE QUESTION. The first cut
        # selected every card in the grid — 533 nodes, 1438 text leaves — to answer "is a card on
        # screen when the panel opens", which the FIRST card answers on its own. Measuring 533
        # made the target flaky under load rather than more truthful: same HEAD, 🟢 at five widths
        # on a quiet machine and 🔴 "every one of 533 node(s) is ZERO-SIZE" while the second eye
        # held the load at 4.68. A gate that depends on how busy the Mac is teaches people to
        # re-run until green, which is worse than not having it.
        # ⚠ It still measures the REAL grid in the REAL panel — only the count is bounded.
        # ⚠ THE BOUNDED SELECTOR WAS WRONG AND MATCHED NOTHING. `.sh-grid > *:nth-child(-n+3)`
        # takes the first three CHILDREN of the grid — and since v2987 those are the lane banner
        # and station headers, which are siblings of the cards, not their parents. It went red at
        # all five widths for "never matched", which is the honest answer to a selector that
        # describes nothing. Back to the whole grid: the count is what made it slow, never what
        # made it wrong, and the warmup above is what pays for the count.
        "sel": "#th-shelfov .sh-grid .shc-hero, #th-shelfov .sh-grid .shc-sess, "
               "#th-shelfov .sh-grid .shc-area",
        # ⚠ ONLY THE TWO CLASSES THAT DECLARE AN ELLIPSIS. Both set `white-space:nowrap;
        # overflow:hidden; text-overflow:ellipsis` in control_ui.html (.shc-area at :2106-2107,
        # .shc-headfind at its own rule), so the cut is DESIGNED and he can SEE it. Anything else
        # on this card that clips is a real defect and must still turn this target red — a blanket
        # allowance here would buy a green by making the target stop looking.
        "truncation_ok": {
            "shc-area": "the run's area line — `white-space:nowrap; overflow:hidden; "
                        "text-overflow:ellipsis` at control_ui.html:2106-2107. A long D2R area "
                        "name ('Catacombs Level 3 · The Crypt') cannot fit a 244px card column, "
                        "and it is cut with a visible ellipsis, not hard-clipped",
            "shc-headfind": "the run's top find, same nowrap+ellipsis rule on its own class. The "
                            "full name is one click away on the card, and the ellipsis makes the "
                            "cut visible rather than silent",
        },
        "activate": r"""(function(){
            /* ⚠ IDEMPOTENT. The harness re-runs this every 0.4s, so it must never toggle:
               thShelf(force) with an explicit true always SHOWS, thShelf() alone flips. */
            var ov = document.getElementById('th-shelfov');
            if (!ov) return false;
            /* ⚠⚠ THE THEATRE FIRST, OR THE PANEL OPENS INTO A ZERO-SIZED PARENT. Measured over
               CDP: with #theatre hidden, every lane rect is 0x0 while the DOM is perfectly
               correct — 4 lanes, no wait node, real content. A rect check alone would then
               report "painted 0 of 4" and a bare existence check would have passed. */
            var th = document.getElementById('theatre');
            if (th && th.hidden) {
                try { (window.thOpen || thOpen)(); } catch (e) { return false; }
            }
            if (th && th.hidden) return false;
            if (ov.hidden) {
                try { (window.thShelf || thShelf)(true); } catch (e) { return false; }
            }
            if (ov.hidden) return false;
            var el = document.getElementById('sh-lanes');
            if (!el) return false;
            /* ask again ONLY while it is still waiting — that is what keeps this idempotent,
               since the wait node disappears the moment the strip renders */
            if (el.querySelector('.shr-wait')) {
                try { (window._shLanesLoad || function(){})(); } catch (e) {}
                return false;                 /* not ready, and NOT a pass */
            }
            /* ⚠⚠ PROVE IT FROM THE RECT, never from the fetch resolving —
               test_activation_is_proven_from_the_RECT_not_from_the_call_returning. A river that
               could not be read paints ONE `.shr-wait.shr-bad` line with a perfectly good box, so
               a bare rect check on #sh-lanes would photograph the failure and call it a river. */
            var lanes = el.querySelectorAll('.shr-lane');
            if (lanes.length < 2) return false;
            var painted = 0;
            for (var i = 0; i < lanes.length; i++) {
                var r = lanes[i].getBoundingClientRect();
                if (r.width > 8 && r.height > 4) painted++;
            }
            return painted === lanes.length;
        })()""",
    },
    "river-strip": {
        "serve": True,
        "path": "",
        "warmup": 14.0,
        "settles": False,
        "why": ("🌊 THE RIVER — the lanes painted into #sh-lanes from /api/river, and the surface "
                "he reads before deleting footage. A failed ask paints `.shr-wait.shr-bad` in the "
                "same box, so an empty river and an unreachable one occupy identical pixels; and "
                "`_shLanesRender` has rendered nothing at all while every piece looked right, when "
                "its name collided with `_shRiverLoad` and the later declaration silently won."),
        "seed": """(function(){ return 1; })()""",
        # ⚠⚠ v2822 (#36) — `.shr-life` AND `.shr-cl` ADDED, BECAUSE A SELECTOR LIST IS A
        # COVERAGE DECISION AND MINE SILENTLY EXCLUDED THE NEW ELEMENTS. The run right after the
        # closure figures shipped reported `clipped 0/28` and its extracted text did not contain
        # them at all — a green render over a surface the harness was not looking at. The pixels
        # showed `+7 closed out` running THROUGH the TOMBSTONE card's right border at 901px while
        # the harness called the target clean. A target that measures three of five classes is a
        # gate blind to what changed. [[gate-blind-to-unexercised-input]] [[the-unjoined-end]]
        # ⚠⚠ v2903 — `.shr-stlab` ADDED, AND THIS IS THE THIRD TIME THIS TARGET HAS TAUGHT THE
        # SAME LESSON. The note above already says it about `.shr-life`/`.shr-cl`: a selector list
        # is a COVERAGE DECISION, and a new element left out of it is unphotographed — losing it
        # would be invisible and the target would still report clean. I added the STATIONS caption
        # and the very next render extracted text with no "stations" in it. Caught by reading the
        # text, not by the verdict, which was green. [[gate-blind-to-unexercised-input]]
        "sel": ("#sh-lanes .shr-lbl, #sh-lanes .shr-n, #sh-lanes .shr-st, "
                "#sh-lanes .shr-life, #sh-lanes .shr-cl, #sh-lanes .shr-stlab"),
        "activate": r"""(function(){
            /* ⚠ IDEMPOTENT. The harness re-runs this every 0.4s, so it must never toggle:
               thShelf(force) with an explicit true always SHOWS, thShelf() alone flips. */
            var ov = document.getElementById('th-shelfov');
            if (!ov) return false;
            /* ⚠⚠ THE THEATRE FIRST, OR THE PANEL OPENS INTO A ZERO-SIZED PARENT. Measured over
               CDP: with #theatre hidden, every lane rect is 0x0 while the DOM is perfectly
               correct — 4 lanes, no wait node, real content. A rect check alone would then
               report "painted 0 of 4" and a bare existence check would have passed. */
            var th = document.getElementById('theatre');
            if (th && th.hidden) {
                try { (window.thOpen || thOpen)(); } catch (e) { return false; }
            }
            if (th && th.hidden) return false;
            if (ov.hidden) {
                try { (window.thShelf || thShelf)(true); } catch (e) { return false; }
            }
            if (ov.hidden) return false;
            var el = document.getElementById('sh-lanes');
            if (!el) return false;
            /* ask again ONLY while it is still waiting — that is what keeps this idempotent,
               since the wait node disappears the moment the strip renders */
            if (el.querySelector('.shr-wait')) {
                try { (window._shLanesLoad || function(){})(); } catch (e) {}
                return false;                 /* not ready, and NOT a pass */
            }
            /* ⚠⚠ PROVE IT FROM THE RECT, never from the fetch resolving —
               test_activation_is_proven_from_the_RECT_not_from_the_call_returning. A river that
               could not be read paints ONE `.shr-wait.shr-bad` line with a perfectly good box, so
               a bare rect check on #sh-lanes would photograph the failure and call it a river. */
            var lanes = el.querySelectorAll('.shr-lane');
            if (lanes.length < 2) return false;
            var painted = 0;
            for (var i = 0; i < lanes.length; i++) {
                var r = lanes[i].getBoundingClientRect();
                if (r.width > 8 && r.height > 4) painted++;
            }
            return painted === lanes.length;
        })()""",
    },
}


def _say(msg):
    print(msg, flush=True)


_CHROME_PROC = None          # set ONLY when this process spawned it — see _chrome_down
_CHROME_PROFILE = None       # the temp profile this process made, removed with the browser


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
    finally:
        # ⚠ IN `finally`, AND AFTER THE KILL. A profile removed while Chrome still holds it comes
        # straight back; one removed only on the happy path survives every crash, which is exactly
        # how it reached 1.4 GB. Failing to remove it is never fatal to the gate's verdict — the
        # verdict is about the page, not about housekeeping — so this swallows its own errors and
        # says nothing rather than turning a full disk into a red render.
        global _CHROME_PROFILE
        _prof, _CHROME_PROFILE = _CHROME_PROFILE, None
        if _prof and os.path.isdir(_prof) and "render_check-profile-" in os.path.basename(_prof):
            try:
                shutil.rmtree(_prof, ignore_errors=True)
            except Exception:
                pass


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
    # ⚠⚠ A TEMPORARY PROFILE, NOT A PERSISTENT ONE — IT REACHED 1.4 GB AND ENOSPC'D HIS MAC.
    # This used to be `os.path.join(SHOTS, "chrome-profile")`, which Chrome fills with caches,
    # code cache and service-worker storage on every run and nothing ever emptied. Measured on
    # 2026-09-03: 1,413 MB of profile beside 63 MB of the PNGs this directory exists for. The gate
    # written to refuse a false green had become the largest disposable object in the tree, and
    # copying `tv/` — which review agents were told to do — carried it three times over.
    # A fresh profile per run also removes a whole class of "it passed because of state left by
    # the last run" that this file has no other defence against. [[process-port-discipline]]
    global _CHROME_PROFILE
    _CHROME_PROFILE = tempfile.mkdtemp(prefix="render_check-profile-")
    prof = _CHROME_PROFILE
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
  var clipScanned=0;
  var okTrunc=0, clippedWhat=[], coveredWhat=[], zeroWhat=[];
  var unreachable=0, unreachableWhat=[];
  nodes.forEach(function(e){
    var r=e.getBoundingClientRect();
    if (r.width<1 || r.height<1) {
      /* ⚠ v2708 — NAME IT. This counted zero-size nodes and could not say WHICH, so the warning
         read "2 of 260 node(s) are ZERO-SIZE" and the only way to find them was to bisect the
         selector. This file already learned that lesson once, for `covered`: "IT COULD NOT NAME
         WHAT IT FLAGGED. `e.id` is empty for most elements, so the refusal read `tab-content
         active over ` with nothing after `over`". Same fix, same reason — a refusal that cannot
         name its subject sends the reader hunting instead of looking. */
      zero++;
      if (zeroWhat.length < 5) zeroWhat.push(
        /* ⚠⚠ v2892 — A CLASS IS NOT A LOCATION. This named the class and the text, and for an
           EMPTY node the text is '' — so the refusal read "hrt-w :: ; hrt-w :: " and said nothing
           about WHERE. MEASURED on the heart panel: 2 of 243 nodes zero-size, both .hrt-w, and
           NINE call sites in control_ui.html can emit an empty one, so source reading could not
           narrow it. That is the complaint v2708 fixed for `covered` — "a refusal that cannot name
           its subject sends the reader hunting instead of looking" — and it was only half fixed:
           the class was named, the PLACE was not. Walk up for the nearest heading, which is what a
           human would use to find it. */
        (function(){
          var where = '', p = e.parentElement, hops = 0;
          while (p && hops++ < 6) {
            var h = p.querySelector && p.querySelector('.hrt-h, .fx-head, h1, h2, h3');
            if (h && (h.textContent||'').trim()) { where = (h.textContent||'').trim().slice(0,44); break; }
            p = p.parentElement;
          }
          /* ⚠ AND NAME THE ROW. The section heading was not enough: the heart panel builds rows as
             <span class="hrt-k">LABEL</span><span class="hrt-s">STATE</span><span class="hrt-w">WHY</span>,
             so an empty .hrt-w is only findable by the LABEL beside it. Reading source could not
             narrow 9 candidate call sites; the row's own key answers it in one line. */
          var row = e.parentElement, key = '';
          if (row) {
            var k = row.querySelector && row.querySelector('.hrt-k');
            if (k) key = (k.textContent||'').trim().slice(0,32);
          }
          var t = (e.textContent||'').trim();
          return (String(e.className||'') || e.tagName)
               + (key ? ' [row: ' + key + ']' : '')
               + (where ? ' under "' + where + '"' : ' (no titled ancestor within 6 hops)')
               + ' :: ' + (t ? t.slice(0,24) : 'EMPTY TEXT');
        })());
      return;
    }
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
    /* ⚠ v2701 — COUNT WHAT THE CLIP SCAN ACTUALLY LOOKS AT. `clipped` is incremented over THIS
       list -- the element plus every descendant -- while `found` counts the target's own matched
       elements. v2697 gave all four counts `/found` in one sweep, which was right for painted,
       off and covered (all three walk `nodes`) and WRONG for this one: the page target printed
       `clipped 54/8`, asserting a subset relationship that does not exist. A denominator that is
       merely present is not the fix; the fix is the RIGHT denominator, and a wrong one is worse
       than none because it reads as a ratio. */
    clipScanned += _clipNodes.length;
    _clipNodes.forEach(function(c){
      var cls = String(c.className||'');
      var allowed = OK_TRUNC.some(function(k){ return cls.indexOf(k) >= 0; });
      function flag(why){
        if (allowed) { okTrunc++; return; }
        clipped++;
        if (clippedWhat.length < 5) clippedWhat.push(
          (cls||c.tagName) + ' :: ' + (c.textContent||'').trim().slice(0,28) + ' [' + why + ']');
      }
      /* ⚠ v2432 — A TITLE CARRYING THE WHOLE STRING IS A RECOVERY PATH, exactly as a scrollable
         ancestor is. The note above already draws this line for scrollers: "content outside a
         scroller is one scroll away, not destroyed". A `title` is the same fact by a different
         route, and this file's own subject proved it — v1753 measured the Theatre sub-label at
         562px inside a 208px box, found that shortening could not fix it, and concluded "a title
         is the honest answer". Until now the harness could not tell that answer from a raw cut, so
         the only way to stop it complaining was OK_TRUNC — a hand-maintained allowlist BY CLASS
         NAME, which goes stale silently and says nothing about whether the text is recoverable.
         Measured on the TV·D tab at 1120x628: 18 truncated elements, of which 13 were `.rcpt-t`
         ticker lines with NO title (fixed in v2432), 2 already carried one, and 3 sat inside a
         scrollable `.chron-list`. After the fix every one has a way back — which is what #207's
         "Nothing ellipsised" can actually mean, since some strings genuinely cannot fit.
         ⚠ THE TITLE MUST CONTAIN THE FULL TEXT. A title that merely exists, or that paraphrases,
         recovers nothing — that would be the allowlist again wearing an attribute. */
      function _recoverable(node, full){
        if (!full) return false;
        var t = node.getAttribute && node.getAttribute('title');
        if (!t && node.closest) { var a = node.closest('[title]'); t = a && a.getAttribute('title'); }
        return !!(t && String(t).indexOf(full) >= 0);
      }
      /* the original question: this box hides its own overflowing content */
      /* ⚠⚠ v2719 — THIS BRANCH AND THE ANCESTOR BRANCH BELOW ANSWERED THE SAME QUESTION TWO
         DIFFERENT WAYS, and the disagreement produced a false red that then became a declared
         floor. The ancestor walk excludes a scrollable box on purpose, and states why:
         "content outside a scroller is one scroll away, not destroyed". This branch excluded
         nothing — any `overflow` that was not `visible` counted, INCLUDING `auto` and `scroll`.

         MEASURED: `#heart-ov .hrt-svgwrap` is `overflow-x: auto` (control_ui.html:5306) wrapping
         an SVG pinned at `min-width: 640px` inside a panel that is ~352px at a 375 viewport. It
         is DESIGNED to scroll there. The gate reported it as clipped, `heart-fan` took a declared
         floor of `{"clipped": 2}` at 375, and the row was filed as a page defect. It is not one —
         it is this instrument disagreeing with itself.

         ⚠ AND THE 2 WAS ONE CONDITION COUNTED TWICE. `.hrt-win` and `.hrt-svgwrap` are BOTH in
         heart-fan's `sel`, and `.hrt-svgwrap` is a descendant of `.hrt-win`; the scan walks
         `[e].concat(e.querySelectorAll('*'))` per matched `e` with no cross-`e` dedupe, so the
         same physical node self-flagged once as itself and once inside its parent's walk.
         [[feedback-suspect-the-instrument]] [[zero-needs-a-denominator]]

         ⚠ HIDDEN/CLIP STILL COUNT. A box that hides its overflow destroys it — that is the real
         defect this branch exists for and it is untouched. Only the SCROLLABLE case is excused,
         by the same rule and the same sentence the ancestor walk already uses. */
      var _sx = getComputedStyle(c);
      var _scrollsSelf = (_sx.overflowX === 'auto' || _sx.overflowX === 'scroll');
      if (c.scrollWidth > c.clientWidth+1 && _sx.overflow!=='visible'
          && !_scrollsSelf && c.clientWidth>0) {
        if (_recoverable(c, (c.textContent||'').trim())) { okTrunc++; return; }
        flag('self'); return; }
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
      /* ⚠ AND AN ELEMENT SCROLLED OUT OF ITS OWN SCROLLER IS NOT COVERED — IT IS ONE SCROLL AWAY.
         Such an element still reports a layout rect, so the sampled point lands on whatever is
         painted there and the ancestor gets recorded as "covering" it. Measured: shortening the
         inbox panel so its action row clears the dock pushed the remaining rows below the panel's
         own fold, and they began reporting as covered by `tab-content` at 1120x628. Tuning the
         panel height only moved the failure between two messages, which is how you know the
         instrument was the thing that could not tell them apart.
         This does NOT weaken the real check: a control under fixed furniture is caught by the
         control-reachability rule below, which has no fixed/sticky exception on purpose. */
      var scrolledOut=false;
      for (var sc=e.parentElement; sc && sc!==document.body; sc=sc.parentElement){
        var scs=getComputedStyle(sc);
        if (!/auto|scroll/.test(scs.overflowY) && !/auto|scroll/.test(scs.overflowX)) continue;
        if (sc.scrollHeight <= sc.clientHeight + 2 && sc.scrollWidth <= sc.clientWidth + 2) continue;
        /* ⚠ THE SAMPLED POINT, NOT THE WHOLE RECT. The first cut exempted an element only when
           its ENTIRE rect lay outside the scroller, and the real case is a row STRADDLING the
           fold: its rect overlaps the visible box while its centre — the point actually probed —
           lands past the clip, so the ancestor answers and it reads as covered. Measured: with
           the whole-rect test the inbox still refused, naming `.ibp-row`. The question this
           clause asks is "was the point I sampled even visible", so it must be asked about the
           point. */
        var sr=sc.getBoundingClientRect();
        var px=r.left+r.width/2, py=r.top+r.height/2;
        if (py <= sr.top || py >= sr.bottom || px <= sr.left || px >= sr.right) { scrolledOut=true; }
        break;
      }
      if (!scrolledOut && top && !e.contains(top) && top!==e && !inert(top)) {
        var fixed=false;
        for (var q=top; q && q!==document.body; q=q.parentElement){
          var pos=getComputedStyle(q).position;
          if (pos==='fixed' || pos==='sticky') { fixed=true; break; }
        }
        if (!fixed) {
          covered++;
          if (coveredWhat.length < 3) coveredWhat.push(
            /* ⚠ IT COULD NOT NAME WHAT IT FLAGGED. `e.id` is empty for most elements, so the
               refusal read "tab-content active over " with nothing after "over" — a refusal that
               cannot say what it is about sends the reader nowhere. Fall through id -> class ->
               tag -> a snippet of its own text, so there is always something to look for. */
            (top.className||top.tagName) + ' over ' +
            (e.getAttribute('data-vault-mule') || e.id ||
             (typeof e.className==='string' && e.className ? '.'+e.className.trim().split(/\s+/)[0] : '') ||
             e.tagName + ' "' + String(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,24) + '"'));
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
  var _de = document.documentElement;
  var _hscroll = Math.max(0, _de.scrollWidth - _de.clientWidth);
  return JSON.stringify({found:nodes.length, painted:rects.length, zero:zero, zeroWhat:zeroWhat, off:off, hscroll:_hscroll,
    clipped:clipped, clipScanned:clipScanned, clippedWhat:clippedWhat, okTrunc:okTrunc,
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


def _settled(tab, budget=25.0, shape=False):
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
    # ⚠⚠ WHAT "STILL" MEANS DEPENDS ON WHAT IS BEING MEASURED, and one predicate for both was
    # wrong. `innerHTML.length` is right for a target whose content is being assembled, and it can
    # NEVER go still on a page carrying a live clock and re-timed "last seen" strings — measured
    # 2026-09-05: the whole-page target sat UNKNOWN for the full 25s budget every run. A target
    # that is permanently UNKNOWN is furniture in exactly the way a permanently-red one is.
    # A LAYOUT probe depends on the element count and on images having resolved, not on whether a
    # clock ticked. `shape=True` asks that question instead. Both still require readyState
    # complete and a rendered tab row, so neither can pass on a half-built document.
    _expr = ("(function(){return document.readyState+'|'"
             "+document.body.innerHTML.length+'|'"
             "+document.querySelectorAll('.tab[data-tab]').length;})()") if not shape else (
             "(function(){var i=document.images,d=0;"
             "for(var k=0;k<i.length;k++){if(i[k].complete)d++;}"
             "return document.readyState+'|'"
             "+document.querySelectorAll('*').length+'/'+i.length+'/'+d+'|'"
             "+document.querySelectorAll('.tab[data-tab]').length;})()")
    t0, last = time.time(), None
    while time.time() - t0 < budget:
        raw = tab.ev(_expr) or ""
        parts = raw.split("|")
        # ⚠⚠ THE THIRD CONDITION IS A PAGE-SPECIFIC LIVENESS PROXY, NOT A GENERAL ONE. A rendered
        # `.tab[data-tab]` row proves `bible.html` has painted — and `control_ui.html` has no tab
        # row at all, so it is ZERO there for ever and the whole-page target could never settle no
        # matter how still it went. Measured 2026-09-05: its shape reached `11814/2399/46` at t=4s
        # and repeated unchanged for the remaining 20s of the budget, while the settle kept
        # answering "never settled" on a count that page does not have.
        # The shape branch drops it: a target that measures a document rather than a widget states
        # its own arrival test in `activate`, which runs separately and CAN fail. Requiring a proxy
        # a page cannot satisfy is not strictness, it is a permanent UNKNOWN — furniture in exactly
        # the way a permanently-red gate is. [[feedback-suspect-the-instrument]]
        _arrived = parts[0] == "complete" and (shape or int(parts[2] or 0) > 0)
        if len(parts) == 3 and _arrived:
            if last == parts[1]:
                return None
            last = parts[1]
        time.sleep(0.6)
    return ("the page never settled in %.0fs — readyState/size kept moving, so anything measured "
            "would be about a document still assembling, and a half-built page reports zero of "
            "everything" % budget)


class _Verdict(list):
    """The refusals, with the report riding alongside on `.notes`.

    ⚠ A plain list keeps every caller and every assertion working; the attribute is what stops the
    block-or-allow decision being a string sniff.
    """
    notes = ()


def verdict(key, m, sel, known=None):
    """Turn ONE width's measurements into refusals. Pure — no browser, no files, no clock.

    This is a separate function ONLY so the suite can prove the refusals BEHAVIOURALLY instead of
    grepping this file for the strings. `source-reading-guard`: a guard that greps source fails on
    its own reach, and every refusal below is a sentence that also appears in a comment explaining
    it. Feed it a dict, read what comes back.

    Returns [] when the width is clean. Order matters: the first three RETURN, because a surface
    that is absent, zero-size or empty makes every later number meaningless — and a meaningless
    number that reads as 0 is the false green this whole file exists to refuse.

    ⚠⚠ THE LIST HOLDS REFUSALS ONLY; ANYTHING THAT MUST BE SEEN BUT DECIDES NOTHING RIDES ON
    `.notes`. My first cut of the declared-floor work put both kinds in one list and had the CALLER
    sniff for a `ⓘ` inside the message to tell them apart — so a gate's block-or-allow decision
    depended on detecting a character in prose, which is the same class of fragility as a guard
    that greps its own comments. Found reviewing my own pushed bytes. The split is structural now:
    a caller that treats the return as "the refusals" is simply right, and `.notes` is there for
    printing. It is a `list` subclass, so every existing caller and every existing assertion —
    `== []`, `len(...)`, iteration — keeps working unchanged. [[source-reading-guard]]
    """
    _notes = []

    def _tag(refusals, notes=()):
        v = _Verdict(refusals)
        v.notes = list(notes)
        return v
    if not m.get("found"):
        return _tag(["%s: selector %r matched NOTHING" % (key, sel)])
    if not m.get("painted"):
        return _tag(["%s: every one of %d node(s) is ZERO-SIZE. A zero-size element cannot be "
                     "clipped or covered, so any 'nothing wrong' below it is a false green."
                     % (key, m.get("zero") or 0)])
    # ⚠ v2225 — AND A PARTIAL COLLAPSE IS THE SAME DEFECT, SMALLER. This refused only when EVERY
    # node measured 0x0, so 17 of 18 lockers collapsing returned [] and the gate exited 0 green on
    # a shelf that had lost almost everything. "Some of it painted" is not the question the gate
    # was asked. The whole-collapse case keeps its own sentence above because it is the one that
    # also invalidates every number below it.
    _zero = int(m.get("zero") or 0)
    # ⚠⚠ A DECLARED ZERO FLOOR, for the one target where zero-size is DESIGN rather than collapse.
    # The `page` target selects `body > *`, and five of the console's eight top-level children are
    # CLOSED MODALS carrying `display:none` — measured: #th-dossier-ov, #th-compare-ov,
    # #th-heatmap-ov, #forensics-ov, #ch-modal. They are deliberately left IN the selector, because
    # "this overlay is closed" and "this overlay collapsed" are the same measurement from outside
    # and the probe should say so rather than have me decide for it. But refusing on them makes the
    # target permanently red, and the refusal above is right for every OTHER target — 17 of 18
    # lockers collapsing is exactly the defect it was written for.
    # So the count is declared per width, printed in full, and refuses when a SIXTH node collapses.
    # ⚠ It never excuses a WHOLE collapse: that branch is above this one and returns first.
    _zfloor = int(((known or {}).get("zero") or 0))
    if _zero > _zfloor:
        return _tag(["%s: %d of %d node(s) are ZERO-SIZE while %d painted%s. A partial collapse reports "
                "zero clipping for the missing ones, so the clean numbers beside it are about the "
                "survivors only.%s" % (key, _zero, m.get("found", 0), m.get("painted", 0),
                                     (" — DECLARED FLOOR IS %d, this is %d MORE"
                                      % (_zfloor, _zero - _zfloor)) if _zfloor else "",
                                     # v2708 — say WHICH. Bisecting a selector to find two
                                     # collapsed nodes is work the probe can simply do.
                                     ("  ::  " + " ; ".join(m.get("zeroWhat") or []))
                                     if m.get("zeroWhat") else "")])
    if _zfloor and _zero < _zfloor:
        return _tag([], ["%s: ⓘ %d of %d node(s) are zero-size against a declared floor of %d, so "
                         "%d now paint that did not. Lower the floor so it cannot excuse a real "
                         "collapse later."
                         % (key, _zero, m.get("found", 0), _zfloor, _zfloor - _zero)])
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
            # ⚠⚠ A DECLARED FLOOR, AND IT EXISTS BECAUSE A NEW INSTRUMENT FOUND OLD DEFECTS.
            # The `page` target measures the whole document for the first time and immediately
            # reports 54 clipped elements at 375px — real, pre-existing, and nothing to do with
            # whatever is being pushed. `render_check` is wired into hooks/pre-push and a red
            # target sets `_px_fail=1` and `exit 1`, so with no floor this would BLOCK EVERY
            # VISUAL PUSH on a backlog it did not create. That is how a gate becomes the thing
            # people switch off — this file's own words: "a gate that cries wolf is how a real one
            # stops being read".
            # So the count is DECLARED, printed in full every run, and refuses only when it RISES.
            # It is the same instrument as `render_coverage.json` (a floor that may improve and
            # may not silently worsen) and the same shape as `KNOWN_MISSES`: pin the LAW, not the
            # number. ⚠ A DROP is reported too — a stale floor is a label that outlived its
            # referent, and it must not quietly excuse more than it was written for.
            # ⚠⚠ A FIELD DECLARED `None` IS REPORTED AND NEVER JUDGED, and `broken` on a
            # whole-page target is the case that forced it. Measured across two runs of the SAME
            # tree minutes apart: 11 broken, then 4. The settle stills when the document's shape
            # stops moving, and at that moment only 46 of 2,399 images are `complete` — the rest
            # are lazy or offscreen and never start. `broken` counts `complete && naturalWidth==0`,
            # so it only ever sees whichever subset happened to load, and WHICH subset varies run
            # to run. Ratcheting that would pin NOISE and hand a red gate a random trigger; and a
            # floor set high enough to absorb the swing would be an exemption wearing a number.
            # So it is printed every run and decides nothing, with the reason on the line.
            # [[unknown-stays-unknown]] [[feedback-suspect-the-instrument]]
            _declared = (known or {}).get(field, 0)
            if field in (known or {}) and _declared is None:
                _notes.append("%s: ⓘ %d element(s) %s — REPORTED, NOT JUDGED: this count moves "
                           "between runs of the same tree because only a fraction of images are "
                           "`complete` when the document's shape stills, so it measures the load "
                           "race and not the page.%s"
                           % (key, m[field], msg, (" — " + "; ".join(what)) if what else ""))
                continue
            _floor = int(_declared or 0)
            if m[field] > _floor:
                out.append("%s: %d element(s) %s%s%s"
                           % (key, m[field], msg,
                              (" — DECLARED FLOOR IS %d, this is %d MORE"
                               % (_floor, m[field] - _floor)) if _floor else "",
                              (" — " + "; ".join(what)) if what else ""))
            elif m[field] < _floor:
                _notes.append("%s: ⓘ %d element(s) %s — the declared floor is %d, so %d were FIXED. "
                           "Lower the floor in TARGETS so it cannot excuse them again."
                           % (key, m[field], msg, _floor, _floor - m[field]))
    # ⚠⚠ THE DOCUMENT MUST NOT SCROLL SIDEWAYS, and until v2712 nothing in this repo said so.
    # Measured 2026-09-06: no gate anywhere asserted it at any width, while BUGS.md had carried
    # "the dash overflows horizontally at 375" as NAMED-NOT-FIXED since v2608. A defect that is
    # known, written down and unwatched is the [[heartov2]] shape — the fixes were never the
    # problem, nobody was looking.
    #
    # PIXELS, NOT ELEMENTS, which is why this does not ride the loop above: that loop prints
    # "%d element(s) ..." and saying "9 element(s) scroll sideways" would be a false sentence
    # attached to a true number. [[label-outlived-referent]]
    #
    # A declared floor here is a LAST resort. The intent is to fix the overrun and declare 0, so a
    # regression is refused; a floor written to match today's measurement is an exemption wearing
    # a number. A DROP is reported so a stale floor cannot quietly excuse more than it was
    # written for.
    _hs = m.get("hscroll")
    if _hs is not None:
        _hs_decl = (known or {}).get("hscroll", 0)
        if "hscroll" in (known or {}) and _hs_decl is None:
            _notes.append("%s: \u24d8 the document scrolls sideways by %dpx — REPORTED, NOT JUDGED"
                          % (key, _hs))
        else:
            _hs_floor = int(_hs_decl or 0)
            if _hs > _hs_floor:
                out.append(
                    "%s: the DOCUMENT SCROLLS SIDEWAYS by %dpx%s. Content past the right edge is "
                    "reachable only by scrolling horizontally, which on a page laid out to fit is "
                    "not a feature — it is the tell that some child cannot shrink into its box."
                    % (key, _hs,
                       (" — DECLARED FLOOR IS %dpx, this is %dpx MORE" % (_hs_floor, _hs - _hs_floor))
                       if _hs_floor else ""))
            elif _hs < _hs_floor:
                _notes.append(
                    "%s: \u24d8 the document scrolls sideways by %dpx against a declared floor of "
                    "%dpx, so %dpx were FIXED. Lower the floor in TARGETS so it cannot excuse them "
                    "again." % (key, _hs, _hs_floor, _hs_floor - _hs))
    return _tag(out, _notes)


def _selector_ready(tab, sel, budget=20.0, spec=None, token=None, reprepare=None):
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
    # ⚠ BEFORE ACCUSING THE PAGE, ASK WHETHER IT IS STILL THE PAGE WE PREPARED.
    if token and callable(reprepare):
        try:
            _same = tab.ev("window.__rcPrepared === %s" % json.dumps(token))
        except Exception:
            _same = True                      # cannot ask -> do not invent a navigation
        if not _same:
            print("   \u21bb the page NAVIGATED after it was prepared (the seed marker is gone) — "
                  "re-preparing and measuring again rather than reporting a red about a world "
                  "this harness never built", flush=True)
            if reprepare():
                _t2 = time.time()
                while time.time() - _t2 < budget:
                    try:
                        if tab.ev(js % json.dumps(sel)):
                            return None
                    except Exception:
                        pass
                    time.sleep(0.4)
                return ("%r never matched a painted element in %.0fs, and again after the page was "
                        "re-prepared following a navigation — so this is the surface, not the "
                        "harness" % (sel, budget))
            return ("%r could not be measured: the page navigated after preparation and the "
                    "harness could not re-prepare it. UNKNOWN, not absent." % (sel,))
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
    # v2433 — TELL THE CHILD WHO ITS PARENT IS, so it can outlive nothing. `proc.terminate()`
    # below only runs when THIS process finishes normally; a killed or timed-out run leaves the
    # console orphaned with PPID 1 and every one of its lanes still turning. Measured on his Mac:
    # three of them, one 15 hours old, load 5.42 -> 3.08 when they were killed. The Chrome child
    # already learned this at v2369 ("THIS IS WHERE HIS MAC GOT HOT, TWICE"); the console child
    # had not. See _orphan_exit_loop in control_app.py. [[feedback-generalize-fixes]]
    # ⚠⚠ v2778 — ISOLATING THE PORT IS NOT ISOLATING THE WORLD, AND THIS FILE DID NOT KNOW IT.
    # `test_button_matrix.py:58` carries that scar in as many words from v1867: *"A port is one
    # door; the frames, the journal, the sweep memory and the sweep lock are four more."* It closes
    # it with nine env vars. THIS harness took the private port, passed --no-open, reaped its own
    # pid — and then handed the child HIS REAL ENVIRONMENT. With no TV_HIST,
    # `_fixture_root_for_state()` and `_log_root()` both fall back to HERE, so every "isolated"
    # path resolved to his live tv/. The same defect, re-shipped in a file that had not read it.
    #
    # ⚠ AND FULL ISOLATION WOULD BREAK THE GATE, which is why the fix is a SNAPSHOT and not an
    # empty sandbox. These targets exist to photograph HIS surfaces: `advanced-fleet` refuses
    # unless the fleet list is FILLED, and an empty world renders "nobody has checked in" — a
    # target that photographs an empty page is green about nothing. So the small state is COPIED
    # in (reads work, and they read what he actually has) and every write lands in the copy.
    #
    # ⛔ FRAMES ARE NEVER COPIED. tv/frames/hist is 5.6 GB. Copying tv/ is the ENOSPC incident this
    # repo already paid for — three agents put 20.5 GB in /tmp in four minutes and every Bash call
    # in the session then failed before it ran. TV_HIST points at an EMPTY temp dir: no rendered
    # target needs a frame, and if one ever does it must say so rather than inherit 5.6 GB.
    _sand = tempfile.mkdtemp(prefix="rc-world-")
    atexit.register(shutil.rmtree, _sand, True)
    _hist = os.path.join(_sand, "frames", "hist")
    os.makedirs(_hist, exist_ok=True)
    # ⚠ NAMED, NOT GLOBBED. A glob would quietly widen the day someone adds a big file beside these,
    # and the size ceiling below is the second guard rather than the only one.
    _COPY = ("sessions.jsonl", "chron_evidence.json", "chron_last_result.json",
             "chronicle_swept.json", "chron_reads.json", "vault_accum.json",
             "vault_last_result.json", "vault_swept.json", "shadow_ledger.json",
             "chron_hunt_memory.json", "chron_autoread.json")
    _copied, _skipped, _bytes = [], [], 0
    for _n in _COPY:
        _src = os.path.join(HERE, _n)
        if not os.path.isfile(_src):
            continue
        _sz = os.path.getsize(_src)
        # ⚠ v2780 — THIS WAS `break`, AND THE CEILING IS NOT A BUDGET, IT IS A SAFETY STOP. A
        # cross-family review found it: `break` abandons every REMAINING name the moment ONE file
        # is oversized, and a name that is absent from the sandbox falls back to the LIVE file. So
        # one large chronicle ledger would have quietly un-isolated the six stores after it — the
        # ceiling protecting against a bulk copy would have caused the exact leak the sandbox
        # exists to prevent. `continue` skips only the oversized file. [[zero-needs-a-denominator]]
        if _bytes + _sz > 64 * 1024 * 1024:      # ⛔ ceiling: this may never become a bulk copy
            _skipped.append(_n)
            continue
        # ⚠ TWO DESTINATIONS, because the child resolves these two ways: five are pointed at by an
        # explicit TV_* var set below (sandbox root), and the rest resolve through
        # `_fixture_root_for_state()`, which is TV_HIST. Copying to only one left the others reading
        # an EMPTY store while their copy sat unused beside it. [[plumbing-with-no-tap]]
        shutil.copy2(_src, os.path.join(_sand, _n))
        shutil.copy2(_src, os.path.join(_hist, _n))
        _copied.append(_n); _bytes += _sz
    # ⚠ [[unknown-stays-unknown]] — a silent skip is indistinguishable from a file that was never
    # there. If the ceiling ever bites, the run must say so rather than render a half-live world.
    if _skipped:
        print("   ⚠ render sandbox SKIPPED %d file(s) over the 64 MB ceiling: %s — the child will "
              "read the LIVE copy of these" % (len(_skipped), ", ".join(_skipped)), flush=True)
    # ⚠⚠ v2822 (#36) — A SYNTHETIC CLOSURE LEDGER, BECAUSE OTHERWISE THIS TARGET IS BLIND TO THE
    # ONE BRANCH IT NOW EXISTS TO PHOTOGRAPH. The river strip draws a second figure — "+N closed
    # out" on the TOMBSTONE lane — sourced from `reel_tombstones.json`, which resolves through
    # TV_HIST and is therefore ABSENT in this deliberately empty world. So the first render after
    # the feature shipped painted "0 closed out · 41 lifetimes", correctly for the fixture and
    # uselessly for the gate: a surface photographed only in the state where the new element does
    # not appear. [[gate-blind-to-unexercised-input]] [[feedback-blind-fixture-green-gate]]
    #
    # ⚠ SYNTHETIC AND NOT COPIED. His real ledger holds 428 rows and 127 KB of session ids; copying
    # it would make these pixels depend on one machine's history and render nothing at all on CI,
    # where the file does not exist. Seven obviously-fake rows exercise the same branch everywhere.
    # ⚠ It is written into the SANDBOX only — `_tombstone_path()` resolves through TV_HIST, and
    # the sandbox is removed at exit. Nothing here can reach his tree.
    # [[feedback-fixtures-never-touch-live-data]]
    io.open(os.path.join(_hist, "reel_tombstones.json"), "w", encoding="utf-8").write(
        json.dumps({"updatedTs": 1700000000000, "reels": [
            {"reel": "reel_fixture_%d" % i, "session": "fixture_%d" % i, "mb": 1.5,
             "pages": 0, "frames": 8, "focus": None, "startedTs": 1700000000000 + i,
             "deletedTs": 1700000100000 + i,
             "why": "render fixture — not a real closure"} for i in range(7)]}))
    env = dict(os.environ, TV_CONTROL_PORT=str(port), TV_PORT=str(port + 1), TV_STUB="1",
               TV_PARENT_PID=str(os.getpid()),
               TV_HIST=_hist,
               TV_FRAMES_DIR=os.path.join(_sand, "frames"),
               TV_SESSIONS=os.path.join(_sand, "sessions.jsonl"),
               TV_CHRON_EVIDENCE=os.path.join(_sand, "chron_evidence.json"),
               TV_CHRON_RESULT=os.path.join(_sand, "chron_last_result.json"),
               TV_CHRON_SWEPT=os.path.join(_sand, "chronicle_swept.json"),
               TV_CHRON_READS=os.path.join(_sand, "chron_reads.json"),
               TV_SWEEP_LOCK=os.path.join(_sand, ".sweep.lock"))
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


# ⚠ v2925 — generous ON PURPOSE. The point is not to fit a line, it is to never drop a field
# without saying so; see the printer below for the 83 chars this number exists to stop losing.
_REPORT_LINE_CAP = 1200


def _report_line(payload):
    """The ⓘ line's payload text — truncated only OUT LOUD. -> str

    ⚠⚠ v2925 — THIS IS A FUNCTION SO A LAW CAN EXERCISE IT INSTEAD OF READING IT.
    The defect it exists to stop was a bare `[:340]` inside the printer: unreachable from any
    test, so the only way to assert anything about it was to match its source text, and a law
    that matches source text goes green the moment somebody rewrites the same bug differently.
    [[source-reading-guard]] [[feedback-blind-fixture-green-gate]]
    """
    _s = json.dumps(payload, sort_keys=True)
    if len(_s) <= _REPORT_LINE_CAP:
        return _s
    return "%s… +%d more char(s) NOT SHOWN — full value in .render_verdict.json" % (
        _s[:_REPORT_LINE_CAP], len(_s) - _REPORT_LINE_CAP)


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
            why = _settled(tab, shape=bool(spec.get("settle_shape")))
        if why:
            out["ok"] = False
            out["refusals"].append(why)
            return out
        # ⚠ v2785 — `spec["seed"]` RAISED AND TOOK THE WHOLE TARGET WITH IT. Adding a target
        # that has nothing to seed produced `🔴 shelf  the GATE ITSELF raised (KeyError: 'seed')`,
        # which the harness correctly labelled a bug in itself rather than in the page — and then
        # still lost the surface. Not every surface needs seeding; a missing seed is a shape, not a
        # fault. [[unknown-stays-unknown]]
        # ⚠⚠ v2851 (#56) — STAMP THE PAGE WE PREPARED, SO WE CAN TELL IF WE ARE JUDGING IT.
        # MEASURED: a failing `river-strip` run reported `window.__thSeed` UNDEFINED and a viewport
        # of 1440x1213 — the DEFAULT size, none of the five this target sets — on a page whose
        # shelf overlay was OPEN. Both elements start `hidden` in the markup, so that is not a
        # fresh load; it is a page `activate` reached and the SEED never did. The harness had
        # navigated (or the console relaunched under it) and then measured a page it never set up,
        # reporting "the surface never painted" about a world it had not built.
        # A red from an unprepared page is not a finding about the page. [[unknown-stays-unknown]]
        _rc_token = "rc%d" % int(time.time() * 1000)
        if spec.get("seed"):
            tab.ev(spec["seed"])
        tab.ev("window.__rcPrepared = %s;" % json.dumps(_rc_token))
        # ⚠ v2404 — A FIXED SLEEP HERE BLOCKED A LEGITIMATE PUSH. This was `time.sleep(0.6)`, and
        # on the v2403 pre-push the `inbox` target refused with "the panel could not be ACTIVATED"
        # while the SAME tree rendered all six targets green minutes later on a quiet machine.
        # Nothing was wrong with the page; 0.6s is simply not enough while the suites are still
        # unwinding, and a gate that fails under load teaches him to re-run it until it agrees —
        # which is how a gate stops being evidence.
        #
        # v2330 already learned this for the SELECTOR wait and left its sibling in place two lines
        # up. Fixing the site that happened to fail and not the class is the whole of
        # [[feedback-generalize-fixes]] — so this one polls the target's OWN activate expression
        # until it answers true or the budget runs out, and the refusal below then means the panel
        # really did not come up rather than that the machine was busy.
        act, _t0 = False, time.time()
        _deadline = _t0 + 12.0
        while time.time() < _deadline:
            act = tab.ev(spec["activate"])
            if act:
                break
            time.sleep(0.4)
        if not act:
            out["ok"] = False
            # ⚠⚠ v2569 — A REFUSAL THAT COULD NOT NAME ITS OWN REASON, found reviewing the v2568
            # bytes. Every activate failure produced this ONE fixed sentence, whatever caused it.
            # For a target whose activate tests several distinct things that is not a detail: the
            # `locks` activate refuses on THREE different defects — a chip destroyed by a poll, a
            # chip carrying no state, and a visible chip collapsed to 0x0 — and all three printed
            # the same words. Measured on myself: the first two versions of that target refused,
            # the message could not tell me which condition had fired, and finding out took a
            # separate hand-written CDP probe. A gate that says "something is wrong" and cannot say
            # WHAT sends the reader hunting, which is how a red gate starts getting re-run instead
            # of read. [[unknown-stays-unknown]]
            #
            # So a target MAY declare `activateWhy`: an expression evaluated only on failure, whose
            # string is appended. It is OPTIONAL and it never decides anything — the refusal stands
            # either way — so a target without one behaves exactly as before.
            _why = ""
            if spec.get("activateWhy"):
                try:
                    _v = tab.ev(spec["activateWhy"])
                    # ⚠ AND A DIAGNOSTIC THAT LIES IS WORSE THAN NONE. Anything that is not a
                    # non-empty string is reported as an absent reason rather than coerced into
                    # one — `None` must not print as "None", and a raised exception must not be
                    # mistaken for a diagnosis of the surface.
                    if isinstance(_v, str) and _v.strip():
                        _why = " — " + _v.strip()[:300]
                    else:
                        _why = " — (this target declares activateWhy and it returned no reason)"
                except Exception as _e:
                    _why = " — (activateWhy itself failed: %s)" % str(_e)[:80]
            # ⚠⚠ v2692 — SAY HOW LONG IT WAITED, AND NAME LOAD AS A CANDIDATE. This refusal used to
            # state only that the panel did not open, while its SIBLING — _selector_ready, twenty
            # lines down — already says the honest version: "either the surface is genuinely absent,
            # or this machine was too loaded to build it, and the difference is exactly what this
            # bound exists to state rather than guess". Same ambiguity, one sentence short.
            # MEASURED COST OF THAT SILENCE, on me, 2026-09-06: the `heart` target refused, I read
            # it as a surface defect, widened this very target's warmup 10s -> 24s on a number taken
            # while a game held 3.4 cores, reverted that, then blamed the wrong subsystem — before a
            # profile found the real cause (/api/heart 19.5s cold, two in-process-only caches).
            # An elapsed number and a named alternative would have pointed at it in one line.
            # ⚠ It still refuses. Naming load as a POSSIBILITY is not excusing it — the panel really
            # was not measured, and unmeasured must never read as clean.
            out["refusals"].append("the panel could not be ACTIVATED after %.1fs of polling — "
                                   "everything measured after this would be about a hidden pane, "
                                   "and a hidden pane reports zero clipping. Either the panel is "
                                   "genuinely broken, or this machine was too loaded to build it "
                                   "in that window (check the load before changing the surface, "
                                   "and the surface before changing this bound)"
                                   % (time.time() - _t0) + _why)
            return out
        # v2330 — was `time.sleep(1.4)`. See _selector_ready: a fixed sleep here is the same
        # defect _settled() was written to remove, and under load it measured empty panels.
        # ⚠ v2851 (#56) — the closure that puts the page back the way it was prepared. Used ONLY
        # when the seed marker is gone (a navigation), never on a plain slow paint.
        def _reprepare(_w=None, _h=None):
            try:
                if _w:
                    tab.send("Emulation.setDeviceMetricsOverride", width=_w, height=_h,
                             deviceScaleFactor=1, mobile=False)
                if spec.get("seed"):
                    tab.ev(spec["seed"])
                tab.ev("window.__rcPrepared = %s;" % json.dumps(_rc_token))
                _d2 = time.time() + 12.0
                while time.time() < _d2:
                    if tab.ev(spec["activate"]):
                        return True
                    time.sleep(0.4)
            except Exception:
                return False
            return False
        why = _selector_ready(tab, spec["sel"], spec=spec, token=_rc_token,
                              reprepare=_reprepare)
        if why:
            out["ok"] = False
            out["refusals"].append(why)
            return out
        # ⚠⚠ v2925 (#53) — THE READING IS TAKEN EVEN AT A WIDTH THAT REFUSED.
        # v2924 put this AFTER `if why_w: … continue`, so a width whose TARGET SELECTOR failed to
        # settle produced no fanfit reading at all. MEASURED by parse on 2026-09-11: the `why_w`
        # continue was at line 2677 and the tap at 2689 — the tap was unreachable for exactly the
        # widths that struggle. And the widths that struggle are the narrow ones: 375x800 is where
        # REG-928 says the collisions are worst, so the ONE width the instrument exists to speak
        # for is the one that silently dropped out, leaving a refusal and no diagnostic.
        # The reading does not depend on the refusal: `data-fanfit` lives on `#heart-ov`, not on
        # `.hrt-k` / `.hrt-svgwrap`, so it is readable whether or not the target selector painted.
        # ⚠ It still NEVER decides ok/not-ok — the refusal above already did that, and a diagnostic
        # that can change a verdict is a second gate in disguise. [[plumbing-with-no-tap]]
        def _take_report(w, h):
                # ⚠⚠ v2924 (#53) — PER WIDTH, BECAUSE THE FAN'S WHOLE PROBLEM IS WIDTH.
                # v2923 evaluated this ONCE, before this loop, and the cross-family eye caught it: at
                # that moment the viewport is Chrome's launch size (`--window-size=1440,1300`), which is
                # NOT one of the five WIDTHS this harness photographs. So the printed `reverted: false`
                # was a reading from a viewport no shot was ever taken at — and the labels collide at
                # particular widths, which is the entire reason #53 exists. A verdict measured at a size
                # nobody photographs cannot speak for 375x800, where the collisions have been worst.
                # ⚠ AND IT STAMPS THE VIEWPORT IT MEASURED. The v2923 expression carried no
                # innerWidth/innerHeight, so the log could not say which size produced the answer — a
                # number with no denominator, in the instrument added to answer a question.
                # [[zero-needs-a-denominator]] [[stale-reading]] [[feedback-blind-fixture-green-gate]]
                if spec.get("report"):
                    try:
                        _rep = tab.ev(spec["report"])
                    except Exception as _exc:
                        _rep = {"error": type(_exc).__name__}
                    if _rep is None:
                        _rep = {"unread": "the report expression returned null"}
                    if isinstance(_rep, dict):
                        _rep = dict(_rep)
                        # ⚠⚠ `readAt`, NOT `atWidth` — AND THE DIFFERENCE IS THE FINDING.
                        # MEASURED 2026-09-11: `_hrtFanFit` has exactly ONE caller (control_ui.html, the
                        # heart-open path after /api/heart lands), and the page's only resize listener
                        # calls `_shellSizePane()` and nothing else. So `data-fanfit` is written ONCE, at
                        # open, and is NEVER recomputed when the window changes size.
                        # My first cut of this stamped `atWidth`, which ASSERTED a width it had not
                        # measured: the same stale attribute read five times wearing five different
                        # labels. That is worse than v2923's unlabelled reading, because a wrong
                        # denominator invites arithmetic a missing one does not.
                        # ⚠ AND THIS IS ITSELF THE LIKELIEST #53: a fan solved once at open is stale at
                        # every other width, which is exactly "the labels collide at some widths". The
                        # diagnostic must not FIX that by re-solving here — `_hrtFanFit` MUTATES the DOM,
                        # so calling it would change the layout being photographed.
                        # [[stale-reading]] [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
                        _rep["readAt"] = "%dx%d" % (w, h)
                        # ⚠⚠ v2925 — THE CAVEAT BELONGS TO THE TARGET, NOT TO THE TAP.
                        # v2924 hardcoded the fan's `solvedAt` essay right here, inside a tap whose own
                        # comments call it a GENERAL expression that ANY target may declare. So every
                        # other shape this tap produces — `{"error": …}`, `{"unread": …}`,
                        # `{"unparsed": …}`, and any second target's reading — was stamped with a
                        # sentence about a fan solve it has nothing to do with. The cross-family eye
                        # caught it as a caller/callee contract disagreement; it is dormant only
                        # because heart-fan is the single declarer TODAY, which is the same "dormant
                        # until it is not" shape as [[label-outlived-referent]].
                        # An error/unread/unparsed shape is NOT a reading, so it is never annotated.
                        if not ("error" in _rep or "unread" in _rep or "unparsed" in _rep):
                            for _nk, _nv in (spec.get("reportNote") or {}).items():
                                _rep[_nk] = _nv
                    out.setdefault("report", {})["%dx%d" % (w, h)] = _rep

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
            why_w = _selector_ready(tab, spec["sel"], budget=12.0, spec=spec,
                                    token=_rc_token,
                                    reprepare=(lambda _w=w, _h=h: _reprepare(_w, _h)))
            if why_w:
                out["ok"] = False
                out["refusals"].append("%dx%d: %s" % (w, h, why_w))
                _take_report(w, h)      # ⚠ v2925 — the fan's attribute does not need the selector
                continue
            _take_report(w, h)
            # ⚠ MEASURE REACHABILITY BEFORE SCROLLING TO IT — see _REACH. After the
            # scrollIntoView below, every target is on screen by construction.
            reach = tab.ev("%s(%s)" % (_REACH, json.dumps(spec["sel"])))
            if isinstance(reach, dict):
                out.setdefault("reach", {})["%dx%d" % (w, h)] = reach
                if reach.get("state") == "UNREACHABLE":
                    out["ok"] = False
                    out["refusals"].append(
                        "%dx%d: the panel is at y=%s in a %spx viewport and the %s scroller only "
                        "travels %spx — it is not scrolled off, it is UNREACHABLE. Nothing he can "
                        "do with a mouse brings it on screen."
                        % (w, h, reach.get("top"), reach.get("vh"), reach.get("scroller"),
                           reach.get("max")))
            tab.ev("(function(){var e=document.querySelector(%s); if(e) "
                   "e.scrollIntoView({block:'center'}); return 1;})()" % json.dumps(spec["sel"]))
            time.sleep(0.35)
            raw = tab.ev(_PROBE % (json.dumps(spec["sel"]),
                                   json.dumps(sorted(spec.get("truncation_ok") or {}))))
            m = json.loads(raw) if raw else {"found": 0}
            key = "%dx%d" % (w, h)
            out["widths"][key] = m

            # ⚠⚠ A REPORT IS NOT A REFUSAL, and conflating them is how a declared floor turns
            # into a permanently-red gate anyway. `verdict` returns two kinds of line now: real
            # refusals, and ⓘ lines that state something the reader must SEE but that decides
            # nothing — a count within its declared floor, a count that has IMPROVED and wants the
            # floor lowered, and a count that moves between runs and therefore cannot be judged.
            # Both go into `refusals` so nothing is hidden from the printout; only the first kind
            # sets ok:False. ⚠ The marker is the leading ⓘ, which `verdict` alone writes.
            # ⚠ THE LIST IS THE REFUSALS; `.notes` is what must be SEEN but decides nothing.
            # My first cut had this line sniff for a `ⓘ` inside the message to tell them apart —
            # a gate's block-or-allow decision resting on detecting a character in prose. Found
            # reviewing my own pushed bytes; the split is structural now. [[source-reading-guard]]
            hurt = verdict(key, m, spec["sel"], (spec.get("known") or {}).get(key))
            out["refusals"].extend(list(hurt) + list(getattr(hurt, "notes", ())))
            if hurt:
                out["ok"] = False
            # the first three refusals mean every later number is meaningless — do not shoot it
            if not m.get("found") or not m.get("painted"):
                continue

            if shots:
                os.makedirs(SHOTS, exist_ok=True)
                d = tab.send("Page.captureScreenshot", format="png", captureBeyondViewport=False)
                png = base64.b64decode(d.get("data") or "")
                # ⚠ v2407 — THE NAME MUST CARRY THE HEIGHT, OR TWO VIEWPORTS FIGHT OVER ONE FILE.
                # This was "%s_%d.png" % (name, w) — width only — which was unambiguous for as
                # long as every entry in WIDTHS had a distinct width. v2406 added his real window
                # (1120, 628) beside the existing (1120, 900), and both promptly wrote
                # `state-panel_1120.png`: whichever ran last silently won, and the surviving PNG
                # could not say which viewport it showed. A screenshot that cannot name its own
                # viewport is useless for the visual pass it exists to serve, and the loss is
                # SILENT — the run still reports both sizes as rendered.
                # Found immediately, by looking at the file listing rather than at the green line.
                p = os.path.join(SHOTS, "%s_%dx%d.png" % (name, w, h))
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


# ══ THE COVERAGE RATCHET ══════════════════════════════════════════════════════════════════════
# Every other refusal in this file is about ONE reading being wrong. This one is about the SET of
# readings getting smaller, which no single reading can see. `console` went 3/3 to 2/2 when a
# control was hidden, and the run stayed green because two clean measurements are two clean
# measurements — the missing third left no trace anywhere.
#
# Shape, deliberately the same as tv/swallow_census.py's RANK-1 ratchet so there is one idea here
# and not two, but INVERTED: that one counts a defect and may only fall; this one counts COVERAGE
# and may only rise. A drop is a refusal naming the target, the width and both numbers.
#
# ⚠ IT RECORDS `found`, NOT `painted`. `painted` is a verdict about the nodes and moves for honest
# reasons — a legitimately hidden node paints zero. `found` is how many nodes the selector matched,
# which is the question "is this surface still here at all". Ratcheting a verdict would fail every
# time a panel is correctly empty; ratcheting the census fails when a surface goes missing.
#
# ⚠ AND IT IS BLESSED ONLY FROM A CLEAN RUN. A run where the browser went away mid-render must
# never be allowed to write a lower floor — that is how "the machine was busy once" becomes the new
# normal and the coverage quietly halves. `--bless` refuses unless every target reported.
COVERAGE = os.path.join(HERE, "render_coverage.json")


def _coverage_floor():
    """-> {target: {width: n}}. Absent file is UNKNOWN, not zero. [[unknown-stays-unknown]]"""
    try:
        with io.open(COVERAGE, encoding="utf-8") as fh:
            d = json.load(fh)
        return d.get("floor") or {}
    except Exception:
        return None


def _coverage_of(results):
    """-> {target: {width: found}} from this run's per-width measurements."""
    out = {}
    for name, r in results.items():
        w = {}
        for key, m in (r.get("widths") or {}).items():
            try:
                w[str(key)] = int(m.get("found") or 0)
            except Exception:
                # ⚠ A WIDTH THAT COULD NOT BE PARSED IS NOT A WIDTH THAT FOUND NOTHING. This
                # recorded 0, and this map is what --bless writes as the coverage FLOOR — so an
                # unparseable reading would silently lower the ratchet, which is the one direction
                # a ratchet must never move on its own. Omit it instead: a width that is absent
                # from the map is UNKNOWN, and the floor keeps whatever it already held.
                # [[unknown-stays-unknown]] [[regression-guard]]
                continue
        if w:
            out[name] = w
    return out


def _coverage_check(results, say, scope=None, out=None):
    """Refuse when a target measures FEWER nodes than its floor. -> n_refusals

    ⚠⚠ #72 — A SUBSET RUN USED TO SKIP THIS ENTIRELY, so `render_check.py heart-stored`
    could lose a node and still exit 0. The old reason was true of the SET and false of the
    MEMBERS: a subset cannot tell a deliberate filter from a vanished surface for the targets it
    did NOT run, and has exactly as much evidence as a full run about the ones it DID.
    `scope` is the set of target names THIS RUN ASKED FOR. Inside it, a drop is judged exactly as
    on a full run. Outside it, the floor entry is NOT CHECKED — reported as unmeasured, never as
    clean and never as a drop. `scope=None` means "everything", which is the old behaviour.

    ⚠ AND A FLOOR IS A CEILING ON WHAT THIS GATE CAN SEE. heart-stored's floor said 9 at every
    width while a clean run photographed 15, so six watched nodes could vanish inside the ratchet's
    own slack and the run would still be >= 9 and still be green. A ratchet exists precisely so
    that "a surface this gate used to watch has gone" cannot read as clean, and inside its slack it
    cannot fire at all. So every gap is now named per target, per width, with the number of nodes
    of blindness it buys. [[zero-needs-a-denominator]] [[stale-reading]]

    `out`, when a dict, collects the machine-readable report: stale / staleNodes / notChecked,
    which main() writes into .render_verdict.json so the fact outlives the scrollback.
    """
    floor = _coverage_floor()
    now = _coverage_of(results)
    rep = out if isinstance(out, dict) else {}
    # 0 is a measurement, absent is nobody looked — floorKnown keeps those apart for the reader
    # of the verdict record. [[unknown-stays-unknown]]
    rep.setdefault("floorKnown", floor is not None)
    rep.setdefault("stale", [])
    rep.setdefault("staleNodes", 0)
    rep.setdefault("notChecked", [])
    if floor is None:
        say("⚪ coverage ratchet UNKNOWN — %s has never been written, so this run cannot tell "
            "whether coverage shrank. Run --bless on a clean run to set the floor."
            % os.path.relpath(COVERAGE, REPO))
        return 0
    if scope is None:
        scope = set(floor) | set(now)          # a FULL run: nothing is out of scope
    scope = set(scope)
    bad = 0
    for name in sorted(floor):
        if name not in scope:
            # ⚠ NOT ASKED FOR IS UNKNOWN, NOT CLEAN — and it is not a drop either. This run has
            # no evidence about it in either direction, so it says so and judges what it ran.
            # [[unknown-stays-unknown]]
            if name not in TARGETS:
                # … but a floor naming a target this file no longer DEFINES needs no browser to
                # judge. That is a lost surface, readable from the registry alone, and a subset
                # run is often the only run anybody executes.
                say("🔴 coverage %-8s the floor names this target and TARGETS no longer "
                    "defines it. A surface that stopped being registered is UNMEASURED for ever, "
                    "and unmeasured must never read as clean." % name)
                bad += 1
            else:
                rep["notChecked"].append(name)
            continue
        if name not in now:
            say("🔴 coverage %-8s the target did not report at all this run, and its floor says it "
                "should measure %d width(s). A surface that stops being checked is UNMEASURED, and "
                "unmeasured must never read as clean."
                % (name, len(floor[name])))
            bad += 1
            continue
        for key in sorted(floor[name]):
            was, is_ = floor[name][key], now[name].get(key)
            if is_ is None:
                say("🔴 coverage %-8s %s is no longer measured at all (floor %d)."
                    % (name, key, was))
                bad += 1
            elif is_ < was:
                say("🔴 coverage %-8s %s measured %d node(s), was %d. Something this gate used to "
                    "watch is gone. If that is intended, say so and re-bless; if it is not, this "
                    "is the defect — and it would otherwise have been %d clean readings in a green "
                    "run." % (name, key, is_, was, is_))
                bad += 1
    # ⚠⚠ #72 — A FLOOR THAT HAS NOT KEPT UP IS SLACK THE RATCHET CANNOT SEE THROUGH, and
    # this used to be one ⓘ line, capped at six rows, worded as an invitation. MEASURED:
    # heart-stored floor 9 at all five widths against a selector that now photographs 15, so six
    # of its nodes could disappear and the run would still be green. The gap is now named per
    # target and per width, with the blindness it buys, and NOTHING is truncated silently — a
    # truncated list of blind spots is itself a blind spot. [[zero-needs-a-denominator]]
    #
    # ⚠ IT IS LOUD, NOT A REFUSAL, ON PURPOSE. Raising a floor needs a FULL clean run and a
    # --bless, which needs a browser; refusing every push until someone finds one would make this
    # the gate that is only ever red, and a gate that is only ever red is switched off inside a
    # week — the same defect as one that is green for ever. The fact is RECORDED instead, in
    # .render_verdict.json, so the heart supervises it rather than the scrollback.
    # [[join-gate-heart]]
    grew = [(n, k, now[n][k], floor[n][k]) for n in floor for k in floor[n]
            if n in scope and now.get(n, {}).get(k, 0) > floor[n][k]]
    # ⚠ THE RECORD IS BUILT FROM THE WHOLE LIST, NOT FROM THE PRINTED LOOP. If the printout is
    # ever capped again, the recorded fact must not be capped with it.
    rep["stale"] = [[n, k, was, is_] for n, k, is_, was in sorted(grew)]
    rep["staleNodes"] = rep.get("staleNodes", 0) + sum(is_ - was for _n, _k, is_, was in grew)
    for n, k, is_, was in sorted(grew):
        say("     🟠 coverage %-8s %s STALE: floor %d, measured %d, STALE by %d — this "
            "ratchet cannot fire until %d of the %d nodes it photographs are gone. It grew "
            "%d -> %d; --bless on a FULL clean run to raise the floor."
            % (n, k, was, is_, is_ - was, is_ - was + 1, is_, was, is_))
    if rep["stale"]:
        say("     🟠 %d stale floor(s), %d node(s) of slack in total — this gate would "
            "stay GREEN while that many watched nodes vanished. "
            "python3 tv/render_check.py --bless"
            % (len(rep["stale"]), rep["staleNodes"]))
    if rep["notChecked"]:
        say("     ⚪ coverage NOT CHECKED for %d of %d floored target(s): %s. They were not "
            "asked for this run, so their coverage is UNKNOWN — not clean, and no subset run "
            "may ever raise a floor. [[unknown-stays-unknown]]"
            % (len(rep["notChecked"]), len(floor), ", ".join(sorted(rep["notChecked"]))))
    return bad


def _coverage_bless(results, complete, say):
    """Write the floor. Refuses unless the run covered every target. -> exit code"""
    if not complete:
        say("🔴 refusing to bless: this run did not report every target, and a partial run must "
             "never write a LOWER floor. That is how one busy afternoon becomes the new normal.")
        return 2
    # ⚠⚠ REG-568 — THE RATCHET DID NOT RATCHET. This file's own `_why` says *"It may only RISE"*
    # and the merge was a plain `dict.update()`, which OVERWRITES with whatever the run measured —
    # including a LOWER number. Reproduced: a floor of 65 and a run measuring 12 wrote **12**. So
    # `--bless` after a real coverage loss silently adopted the loss as the new normal, which is
    # precisely the sentence above it promising that cannot happen. TASKS.md has named this as
    # still-owed since the `console` target went 3/3 -> 2/2 and was re-baselined with nobody
    # noticing. A floor that can be lowered by the thing it is measuring is not a floor.
    #
    # ⚠ AND LOWERING IS SOMETIMES RIGHT — a target deliberately narrowed, a surface intentionally
    # removed. So it is not forbidden, it is REFUSED SILENTLY NO LONGER: the floor holds, and the
    # bless says out loud which numbers it declined to lower and what to do about it.
    now = _coverage_of(results)
    old = _coverage_floor() or {}
    merged, held = {}, []
    for name in set(list(now) + list(old)):
        merged[name] = dict(old.get(name) or {})
        for k, v in (now.get(name) or {}).items():
            was = merged[name].get(k)
            if isinstance(was, int) and isinstance(v, int) and v < was:
                held.append((name, k, was, v))
                continue                      # the floor may only RISE
            merged[name][k] = v
    with io.open(COVERAGE, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "_why": "COVERAGE RATCHET — how many nodes each target measured on a clean run. It may "
                    "only RISE. A drop means a surface this gate used to watch has gone, which in a "
                    "green run reads exactly like clean. Regenerate with: "
                    "python3 tv/render_check.py --bless",
            "floor": merged}, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    say("blessed %d target(s) into %s" % (len(merged), os.path.relpath(COVERAGE, REPO)))
    for name, k, was, v in sorted(held):
        say("   \u26a0 HELD %s %s at %d — this run measured %d, and a floor may only RISE. If that "
            "loss is deliberate, lower it by hand and say why in the commit; if it is not, a "
            "surface this gate used to watch has gone." % (name, k, was, v))
    if held:
        say("   \u26a0\u26a0 %d floor(s) were NOT lowered. In a green run a silent drop reads "
            "exactly like clean, which is how the `console` target went 3/3 -> 2/2 unnoticed."
            % len(held))
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

    bad, unknown = 0, 0
    results = {}          # per-target, for the coverage ratchet after the loop
    for name, spec in sorted(targets.items()):
        # ⚠ v2412 — A DROPPED CDP SOCKET IS UNKNOWN, NOT A CRASH AND NOT A DEFECT. On 2026-09-02 a
        # push was blocked by a bare WebSocketConnectionClosedException propagating out of this
        # loop: Chrome went away mid-run and the gate DIED MID-VERDICT rather than reporting one.
        # This file's own opening note calls that out — "a render gate that dies mid-verdict is
        # indistinguishable from one that found nothing, which is the exact false-green this file
        # exists to refuse" — and the transport was the one path not covered by it.
        #
        # The pre-push was right to block: a gate that produced no verdict must never read as a
        # pass. But BLOCKED with a traceback and BLOCKED with "the browser went away" send a person
        # to two completely different places, and only one of them is true. Exit 2, the same code
        # as "no Chrome at all", because it is the same fact arriving later.
        #
        # ⚠ AND IT IS NOT RETRIED HERE ON PURPOSE. A gate you re-run until it agrees has stopped
        # being evidence. If Chrome dies repeatedly that is a finding about the machine or about
        # this harness, and it should be looked at rather than papered over with an attempt count.
        try:
            r = check(name, spec)
        except _TRANSPORT_EXCLUDE as _e:
            # ⚠ HTTPError SUBCLASSES URLError, so it must be caught BEFORE the transport clause or
            # it rides in on it. The server answered — with a status — which is not "the browser
            # went away", and a 404 is this file asking for the wrong path.
            _say("🔴 %-8s the GATE ITSELF raised (%s: %s) — Chrome ANSWERED with a status, so this "
                 "is a bad request from render_check, not a disconnect."
                 % (name, type(_e).__name__, str(_e)[:80]))
            bad += 1
            continue
        except _TRANSPORT_ERRORS as _e:
            _say("⚪ %-8s UNKNOWN — the browser connection was lost mid-render (%s: %s)."
                 % (name, type(_e).__name__, str(_e)[:90]))
            _say("   NOTHING WAS ESTABLISHED about this surface. A skip is not a pass, so this "
                 "still exits non-zero — but it is not a layout defect and the PNGs will not show "
                 "one.")
            bad += 1
            unknown += 1
            continue
        except Exception as _e:
            # ⚠ A HARNESS BUG IS NOT A TRANSPORT FAILURE, AND THE FIRST CUT CALLED EVERY RAISE ONE.
            # This was a bare `except Exception` printing "the browser connection was lost" — so a
            # JSONDecodeError, a KeyError in a target spec, a TypeError in the probe path would all
            # have sent someone to look at Chrome for a bug in this file. A cold review caught it.
            # Neither can hide a layout defect (check() returns dicts for every rendering failure),
            # but pointing at the wrong component costs an hour. [[label-outlived-referent]]
            _say("🔴 %-8s the GATE ITSELF raised (%s: %s) — this is a bug in render_check, not in "
                 "the page and not in the browser." % (name, type(_e).__name__, str(_e)[:90]))
            bad += 1
            continue
        icon = "🟢" if r["ok"] else "🔴"
        _say("%s %-8s %s" % (icon, name, r["why"]))
        # ⚠ v2923 (#53) — AND IT IS PRINTED, not merely collected. Recording a target's own verdict
        # into a dict nobody prints is the same defect as the attribute nobody read: one grave
        # instead of another. This never changes ok/not-ok — it is a diagnostic, and a diagnostic
        # that can fail a run is a second gate in disguise. [[plumbing-with-no-tap]]
        if r.get("report"):
            # ⚠ one line per width. Collapsing five readings into one would re-create exactly the
            # defect v2924 fixed: an answer with no denominator.
            for _wk in sorted(r["report"]):
                _s = _report_line(r["report"][_wk])
                # ⚠⚠ v2925 — A SILENT `[:340]` ATE THE HALF OF THE PAIR THAT ANSWERS #53.
                # MEASURED 2026-09-11 against the gate's own .render_verdict.json: heart-fan
                # serialises to 423 chars, so 83 were dropped — and the 83 were exactly
                # `"to": {"adjacent": 0, "collisions": 0, "displacement": 65.6}`, the collisions
                # AFTER the solve. The line kept `from` (before) and dropped `to` (after), so the
                # one human-facing surface printed HALF A COMPARISON and looked complete. The
                # cross-family eye caught it on v2924, in the instrument built to answer #53.
                # A cut that does not SAY it cut is [[zero-needs-a-denominator]] wearing a slice:
                # nothing distinguishes a short payload from a truncated one.
                _say("     ⓘ report %-9s %s" % (_wk, _s))
        for key in sorted(r["widths"]):
            m = r["widths"][key]
            # ⚠ v2697 — EVERY COUNT CARRIES ITS DENOMINATOR, because three of these used to read as
            # statements about the PAGE when they are statements about the TRACKED SET. A second
            # eye, cold on the pixels, said the floating ROUTINES bar was sitting on top of the
            # GRAIL-DUPES and WIP locker text; this line said `covered 0` for the same surface at
            # the same width. Both were right. The bar really does cover those cards, and none of
            # the 11 elements this target tracks is one of them.
            #
            # `covered 0` invites exactly the wrong reading — "nothing on this page is covered" —
            # when the honest sentence is "none of the 11 I watch". That is [[zero-needs-a-
            # denominator]] in the instrument that is supposed to catch it: a 0 with no
            # denominator is UNKNOWN wearing green. `painted` always had its /found and was never
            # once misread; the other three did not, and one of them hid a real overlap.
            # ⚠ v2701 — AND EACH COUNT GETS ITS **OWN** DENOMINATOR, not a shared one.
            # v2697 gave all four `/found` in one sweep. Three of them were right: painted, off
            # and covered are all incremented inside `nodes.forEach`, so `found` IS their
            # population. `clipped` is not — it is incremented over `_clipNodes`, which is each
            # matched element PLUS every descendant, so the page target printed `clipped 54/8`.
            # That is a worse failure than the bare `0` it replaced: a bare number is silent
            # about its population, while `54/8` actively asserts a subset relationship that
            # does not exist, and invites the reader to compute a ratio from it.
            # The lesson is not "add denominators", it is "a number and its denominator have to
            # be counted over the SAME set" — which is the thing that has to be checked per
            # counter, one at a time, rather than applied in a sweep. [[zero-needs-a-denominator]]
            _fnd = m.get("found", 0)
            _scan = m.get("clipScanned")
            # ⚠⚠ v2704 — `if _scan` WAS A TRUTHINESS TEST, AND clipScanned CAN LEGITIMATELY BE 0.
            # clipScanned is incremented AFTER the `zero++; return` early-out, so a target whose
            # matched nodes are all zero-size reports a real, measured 0 — and `if _scan` sent it
            # down the same branch as a probe that never reported the key at all, printing
            # "(of an unreported scan)" over a scan that WAS reported. Measured-zero collapsed
            # into nobody-looked, in the commit whose entire subject was denominator honesty.
            # The test is `is not None`. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
            _clip = ("%s/%s" % (m.get("clipped", 0), _scan) if _scan is not None
                     else "%s (of an unreported scan)" % m.get("clipped", 0))
            _say("     %-9s painted %s/%s · clipped %s · off %s/%s · covered %s/%s · "
                 "imgs %s/%s broken"
                 % (key, m.get("painted", 0), _fnd, _clip,
                    m.get("off", 0), _fnd, m.get("covered", 0), _fnd,
                    m.get("broken", 0), m.get("imgs", 0)))
            rc = (r.get("reach") or {}).get(key)
            if rc and rc.get("state") != "ON-SCREEN":
                # BELOW-FOLD is REPORTED, not failed — a long page he can scroll is a page working.
                # But it must be SAID, because "painted 3/3 clipped 0" reads as "he can see it".
                _say("               ⓘ %s at load: y=%s in a %spx viewport (%s scroller travels "
                     "%spx) — reachable by scrolling, not visible on arrival"
                     % (rc["state"], rc.get("top"), rc.get("vh"), rc.get("scroller"), rc.get("max"))
                     if rc["state"] == "BELOW-FOLD" else
                     "               ⓘ %s at load: y=%s in a %spx viewport"
                     % (rc["state"], rc.get("top"), rc.get("vh")))
            if m.get("text"):
                _say("               text: %s" % m["text"][:96])
        for why in r["refusals"]:
            _say("     ⚠ %s" % why)
        results[name] = r
        if not r["ok"]:
            bad += 1
    _say("")

    # THE SET OF READINGS, not any one of them. Everything above judges a surface; this judges
    # whether the same surfaces are still being looked at. Only meaningful over the FULL target
    # set — a `--target vault` run legitimately reports one target and must not read as a drop.
    _full = (len(targets) == len(TARGETS))
    if "--bless" in argv:
        return _coverage_bless(results, _full and not bad and not unknown, _say)
    # ⚠⚠ COVERAGE REFUSALS GET THEIR OWN COUNTER — `bad += _coverage_check(...)` mixed them into
    # the RENDER-FAILURE count and three things broke at once. `clean = len(targets) - bad` went
    # NEGATIVE (measured: Chrome dies, 9 targets each counted once as a lost socket and again as
    # "did not report", bad=18, clean=-9), and because that also made `unknown != bad` BOTH v2412
    # branches that exist to say "nothing was established" were skipped — so a dead browser
    # printed "🔴 9 target(s) did not render cleanly — LOOK AT THE PNGs above" for PNGs that were
    # never written. A count of one kind of thing must not absorb a different kind.
    # ⚠⚠ #72 — THE RATCHET USED TO BE SKIPPED ENTIRELY ON A SUBSET RUN. `elif` meant a
    # `render_check.py heart-stored` run could lose a node and exit 0 with one ⓘ line about it.
    # The scope is handed in instead, so the ratchet judges what was actually rendered and stays
    # silent — explicitly UNKNOWN — about the rest.
    #
    # ⚠ AND A SUBSET STILL MAY NOT RAISE ANYTHING. --bless returns above, behind its own
    # `complete` gate: a partial run blessing coverage it never fully measured would be this
    # same lie one layer down.
    cov_missing = 0
    _cov = {}
    cov_missing = _coverage_check(results, _say, scope=set(targets), out=_cov)
    if not _full:
        _say("     ⓘ this run asked for %d of %d target(s); the ratchet judged those %d and "
             "says nothing about the rest, which are UNKNOWN rather than clean."
             % (len(targets), len(TARGETS), len(targets)))

    # ⚠⚠ v2859 — THE RENDER VERDICT WAS NOT DURABLE ANYWHERE, so the heart could not read it.
    # Konyo asked whether 100% on HEART 2.0 is also a VISUAL pass. It is not, and the reason it
    # could not even be MEASURED is here: this harness wrote PNGs and a coverage FLOOR, and nothing
    # else. Which surfaces actually reported on the last run existed only in the push log and the
    # terminal. `.render_shots` is gitignored and holds 425 files mixing today's 16 targets with
    # ad-hoc shots going back to v2262, so it cannot answer "did `locks` report this run?" either.
    # A verdict nobody records is a verdict nobody can supervise. [[the-unjoined-end]]
    try:
        _v = {"_why": "which render targets REPORTED on the last run. heart2 reads this to say how "
                      "much of the heart is pixels rather than code. A target missing from "
                      "`targets` was not measured — which is UNKNOWN, not clean.",
              "ranAt": int(time.time() * 1000),
              "full": bool(_full),
              "totalTargets": len(TARGETS),
              "reported": sorted(results.keys()),
              "coverageMissing": int(cov_missing),
              # #72 — the ratchet's OWN blind spot, recorded so it outlives the terminal. A
              # stale floor is slack this gate cannot see through; 0 here is a measured zero,
              # and the key being absent means an older render_check wrote this file — which
              # is UNKNOWN, not clean. [[join-gate-heart]] [[unknown-stays-unknown]]
              # ⚠ the skeptic caught this written and never read. Absent here means an
              # older render_check wrote the file; False means there is no floor at all;
              # True means a floor exists and 0 in the fields below is MEASURED.
              "coverageFloorKnown": bool(_cov.get("floorKnown")),
              # ⚠ v2924 — RECORDED, not only printed. A diagnostic that lives in scrollback
              # is the grave REG-920 named. Keyed by target, then by width.
              "reports": {_n: _r["report"] for _n, _r in results.items() if _r.get("report")},
              "coverageStale": list(_cov.get("stale") or []),
              "coverageStaleNodes": int(_cov.get("staleNodes") or 0),
              "coverageNotChecked": list(_cov.get("notChecked") or []),
              "renderFailures": int(bad)}
        with io.open(os.path.join(HERE, ".render_verdict.json"), "w", encoding="utf-8") as _fh:
            _fh.write(json.dumps(_v, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    except Exception as _e:                     # a bookkeeping failure must never fail the gate
        _say("     \u26a0 could not write .render_verdict.json (%s) — the heart will read this run "
             "as UNMEASURED rather than clean." % type(_e).__name__)
    _say("shots: %s" % os.path.relpath(SHOTS, REPO))
    if cov_missing:
        _say("🔴 %d surface(s) the ratchet expected were never reported — a COVERAGE refusal, "
             "counted apart from the %d render failure(s) above because it is a different fact."
             % (cov_missing, bad))
    if bad:
        # ⚠ v2412 — AN UNMEASURED SURFACE IS NOT A DIRTY ONE, AND SENDING HIM TO PNGs THAT SHOW
        # NOTHING IS ITS OWN SMALL LIE. This line said "did not render cleanly — LOOK AT THE PNGs"
        # for every non-zero outcome, including a lost CDP socket where no PNG was ever written.
        # Same defect class as the three console rows in CF-10: a state that is neither health nor
        # fault, reported as fault, which teaches the reader to discount the row.
        # ⚠ AND THIS IGNORED THE GREENS. `unknown == bad` says "nothing was established" even when
        # five targets rendered cleanly and one socket dropped — fail-closed, and dishonest about
        # the five. Only claim nothing was established when nothing was.
        clean = len(targets) - bad
        if unknown and unknown == bad and not clean:
            _say("⚪ %d target(s) UNKNOWN — the browser went away mid-render, so nothing was "
                 "established. NOT a layout defect, and the PNGs will not show one. Still "
                 "non-zero: a skip is not a pass." % unknown)
            return 2
        if unknown and unknown == bad:
            _say("⚪ %d target(s) UNKNOWN (browser lost) — but %d DID render cleanly, so this is "
                 "not 'nothing was established'. Non-zero because the unknown ones were never "
                 "looked at." % (unknown, clean))
            return 2
        if unknown:
            _say("🔴 %d target(s) did not render cleanly — LOOK AT THE PNGs above. ⚪ %d further "
                 "target(s) were UNKNOWN (browser lost), which is neither clean nor dirty. "
                 "%d rendered clean." % (bad - unknown, unknown, clean))
            return 1
        _say("🔴 %d target(s) did not render cleanly — LOOK AT THE PNGs above." % bad)
        return 1
    if cov_missing:
        # every target that RAN rendered clean; the SET is what shrank
        _say("   (every target that ran rendered cleanly — it is the set of surfaces that shrank.)")
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
