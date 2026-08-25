// demo_console.mjs — STANDALONE scripted DEMONSTRATION journeys vs the LIVE TV·D console.
// NOT a Playwright test-runner spec. Run:  node tv/demo_console.mjs   (from repo root).
// Drives http://127.0.0.1:17772/ with a fresh headless chromium (own browser — never
// touches Konyo's tab, never the repo suite). Each journey prints one ✅/❌ line; the
// process exits non-zero if any journey fails. Target runtime < 60s.
//
// The 7 journeys mirror the console's real architecture (control_ui.html):
//   header tabs #head-tabs .ht[data-tab] → shellOpen() adds body.shell-open and routes the
//   same-origin engine iframe #tvd-eng (its .tab.active gains the matching data-tab);
//   the 📺 TV·D tab calls shellHome() back to the .stage. Tally chip .hd-chip.tly-btn opens
//   #tly-ov with .tly-tab filters. Three eyes = #eye-live/#eye-second/#eye-kai + status spans.
//   The 📚 shelf (#btn-shelf → thOpen+thShelf) renders one .sh-card per /api/sessions run,
//   each sealed reel carrying a .sh-verdict line (🛡/🚨/🧠/📸).

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch (e) {
  // fallback: resolve via CommonJS require if the bare ESM import ever fails
  const { createRequire } = await import('node:module');
  const require = createRequire(import.meta.url);
  ({ chromium } = require('playwright'));
}

// v1679 — the port is overridable so a layout probe can run against a THROWAWAY console
// (TV_CONTROL_PORT=17999 control_app.py --no-open) instead of the one Konyo has open. Default
// unchanged; nothing that does not set the variable behaves differently.
const URL = `http://127.0.0.1:${process.env.TV_CONTROL_PORT || 17772}/`;
const PANE_TABS = ['forge', 'crafts', 'funi', 'fsets', 'tools', 'vault'];  // v1377 — 'session' removed: Sessions is now console-native (data-view=sessions), no longer opens a bible pane
// v2092 — 'vault' added. The console got a Vault tab between Tools and TV·D this ship, and this
// list is what J1 SHELL MATRIX actually walks — so without it the new tab would have shipped
// with the matrix reporting a confident green about the four tabs it already knew.
// A gate is blind to what its fixture never exercises. [[gate-blind-to-unexercised-input]]

const results = [];
function record(name, ok, detail) {
  results.push({ name, ok, detail });
  const mark = ok ? '✅' : '❌';
  console.log(`${mark} ${name}${detail ? ' — ' + detail : ''}`);
}

// ── browser-side helpers (stringified into evaluate/waitForFunction) ──────────────
// The engine iframe is same-origin, so page context can read its contentDocument directly.
async function activeBoardTab(page) {
  return page.evaluate(() => {
    const f = document.getElementById('tvd-eng');
    const d = f && f.contentDocument;
    const a = d && d.querySelector('.tab.active');
    return a ? (a.dataset.tab || null) : null;
  });
}
function shellOpen(page) {
  return page.evaluate(() => document.body.classList.contains('shell-open'));
}
function headRect(page) {
  return page.evaluate(() => {
    const r = document.getElementById('head-tabs').getBoundingClientRect();
    return { top: r.top, left: r.left };
  });
}
async function goHome(page) {
  if (await shellOpen(page)) {
    await page.click('#head-tabs .ht[data-tab="tvd"]');
    await page.waitForFunction(() => !document.body.classList.contains('shell-open'), null, { timeout: 8000 });
  }
}

// Warm up: give the engine iframe a chance to boot bible JS so the first pane route is snappy
// (best-effort — shellOpen() retries switchTab for ~4s anyway, so this is never fatal).
async function warmEngine(page) {
  /* v2112 — WAIT FOR WHAT J1 ACTUALLY ASSERTS, AND SAY SO IF IT NEVER ARRIVES.
     This waited only for `switchTab` to be a function, then swallowed its own timeout with
     "the click retry loop will cover it". On a COLD console — a gate run seconds after a
     relaunch — switchTab exists while the board's tab markup does not, so J1 clicked six
     panes and timed out waiting for `.tab.active` to follow. The run reported
     `j1_shellMatrix — page.waitForFunction: Timeout 12000ms exceeded`, which names the
     symptom and hides the cause; the same journey then passed twice in a row at 5.7s
     against a warm console.
     Silence is not evidence: a warm-up that gives up quietly turns a boot race into a
     mystery failure in an unrelated journey. [[feedback-silence-is-not-evidence]] */
  try {
    await page.waitForFunction(() => {
      const f = document.getElementById('tvd-eng');
      const w = f && f.contentWindow;
      if (!w || typeof w.switchTab !== 'function') return false;
      const d = f.contentDocument;
      // the tab strip is what every pane journey steers by — an engine with no tabs is not warm
      return !!(d && d.querySelector('.tab.active'));
    }, null, { timeout: 25000 });
  } catch (_) {
    console.log('⚠ BOOT — the board engine did not finish loading in 25s. The pane journeys '
      + 'below steer by its tab strip, so treat any J1/J2 failure as THIS, not as a routing bug.');
  }
}

// ── the six journeys ──────────────────────────────────────────────────────────────
async function j1_shellMatrix(page) {
  const name = 'J1 SHELL MATRIX';
  await goHome(page);
  for (const tab of PANE_TABS) {
    await page.click(`#head-tabs .ht[data-tab="${tab}"]`);
    try {
      await page.waitForFunction((t) => {
        if (!document.body.classList.contains('shell-open')) return false;
        const f = document.getElementById('tvd-eng');
        const d = f && f.contentDocument;
        const a = d && d.querySelector('.tab.active');
        return !!(a && a.dataset.tab === t);
        /* v2112 — 30s, not 12s. This gate runs INSIDE hooks/pre-push, immediately after the
           full tv suite and alongside the Playwright smoke, so the machine is loaded and the
           board is promoting a 5.9MB document into an iframe. Measured: 8/9 at ~17s during the
           gate, 9/9 five times in a row at ~6s standalone, with no product difference between
           them. The budget was the failure, and a per-pane budget that only holds on an idle
           machine is a race the gate loses at exactly the moment it matters. */
      }, tab, { timeout: 30000 });
    } catch (e) {
      /* v2112 — NAME THE PANE. This threw `page.waitForFunction: Timeout 12000ms exceeded`,
         which says a wait expired and nothing about WHICH of six panes, what the board was
         showing instead, or whether the shell had even opened — so the same message covers a
         routing bug, a cold engine and a click that missed. Report the state at the moment it
         gave up. [[feedback-verify-not-proxy]] */
      const st = await page.evaluate(() => {
        const f = document.getElementById('tvd-eng');
        let d = null; try { d = f && f.contentDocument; } catch (_) {}
        const a = d && d.querySelector('.tab.active');
        return {
          shell: document.body.classList.contains('shell-open'),
          doc: !!d,
          active: a ? a.dataset.tab : null,
          tabs: d ? d.querySelectorAll('.tabs .tab').length : -1,
        };
      }).catch(() => null);
      /* v2112 — AND ASK WHETHER THE ROUTE ITSELF STILL WORKS. "the pane did not activate"
         covers two opposite causes: the click never reached the router, or the router ran and
         the board refused. Calling switchTab directly separates them — if the board moves when
         asked in-process, the defect is upstream of the board, and if it does not, it is the
         board. Suspect the instrument before the subject. [[feedback-suspect-the-instrument]] */
      const probe = await page.evaluate((t) => {
        const f = document.getElementById('tvd-eng');
        const w = f && f.contentWindow;
        const out = { hasSwitch: !!(w && typeof w.switchTab === 'function'), threw: null, after: null };
        if (!out.hasSwitch) return out;
        try { w.switchTab(t); } catch (e) { out.threw = String((e && e.message) || e); }
        try {
          const a = f.contentDocument.querySelector('.tab.active');
          out.after = a ? a.dataset.tab : null;
        } catch (e) { out.after = '(unreadable)'; }
        return out;
      }, tab).catch(() => null);
      throw new Error(`pane "${tab}" never activated — shell-open=${st && st.shell}, `
        + `board doc=${st && st.doc}, board shows="${st && st.active}", `
        + `board tab count=${st && st.tabs} · direct switchTab: exists=${probe && probe.hasSwitch}`
        + `, threw=${probe && probe.threw}, board then showed="${probe && probe.after}"`);
    }
  }
  // then TV·D → shell closes and the stage is visible
  await page.click('#head-tabs .ht[data-tab="tvd"]');
  await page.waitForFunction(() => {
    if (document.body.classList.contains('shell-open')) return false;
    const s = document.getElementById('stage');
    return !!(s && s.getClientRects().length);
  }, null, { timeout: 8000 });
  record(name, true, `${PANE_TABS.length} panes routed [${PANE_TABS.join(', ')}] + tvd→stage`);
}

async function j2_alignment(page) {
  const name = 'J2 ALIGNMENT INVARIANT';
  await goHome(page);
  const home1 = await headRect(page);
  await page.click('#head-tabs .ht[data-tab="forge"]');
  await page.waitForFunction(() => document.body.classList.contains('shell-open'), null, { timeout: 8000 });
  // let the fixed-topbar layout settle a paint
  await page.waitForFunction(() => true);
  const pane = await headRect(page);
  await goHome(page);
  const home2 = await headRect(page);
  const dTop1 = Math.abs(pane.top - home1.top), dLeft1 = Math.abs(pane.left - home1.left);
  const dTop2 = Math.abs(home2.top - home1.top), dLeft2 = Math.abs(home2.left - home1.left);
  const TOL = 0.5;
  const ok = dTop1 <= TOL && dLeft1 <= TOL && dTop2 <= TOL && dLeft2 <= TOL;
  const detail = `home↔pane Δ(top ${dTop1.toFixed(2)}, left ${dLeft1.toFixed(2)}) · home↔home Δ(top ${dTop2.toFixed(2)}, left ${dLeft2.toFixed(2)})`;
  if (!ok) throw new Error(detail);
  record(name, true, detail);
}

async function j3_tally(page) {
  const name = 'J3 TALLY ENGINE';
  await goHome(page);
  // v1380.5 — TALLIES lives in the off-air RECORD zone; if a prior journey left ON AIR,
  // home-dash is hidden and the chip never appears. End the session first.
  const st = await page.evaluate(() => document.body.getAttribute('data-state'));
  if (st === 'on' || st === 'sim' || st === 'stopping') {
    try {
      await page.click('#btn-on');
      await page.waitForFunction(
        () => document.body.getAttribute('data-state') === 'off',
        null,
        { timeout: 20000 }
      );
    } catch (_) { /* best-effort; selector wait below is the real gate */ }
  }
  // also leave Theatre if open (stage exclusivity)
  await page.evaluate(() => {
    try { if (window.TH && TH.open && typeof thClose === 'function') thClose(); } catch (e) {}
  });
  await page.waitForSelector('.hd-chip.tly-btn', { timeout: 12000 });
  await page.click('.hd-chip.tly-btn');
  await page.waitForFunction(() => {
    const ov = document.getElementById('tly-ov');
    if (!ov || ov.hidden) return false;
    return getComputedStyle(ov).display !== 'none';
  }, null, { timeout: 8000 });
  // filter tabs render from /api/tallies (works even with zero shots — counts show · 0)
  await page.waitForSelector('#tly-tabs .tly-tab', { timeout: 8000 });
  await page.locator('#tly-tabs .tly-tab', { hasText: 'RUNES' }).click();
  await page.waitForFunction(() => {
    const on = document.querySelector('#tly-tabs .tly-tab.on');
    return !!(on && /RUNES/.test(on.textContent || ''));
  }, null, { timeout: 5000 });
  const wasShellOpen = await shellOpen(page);
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => {
    const ov = document.getElementById('tly-ov');
    return !ov || ov.hidden;
  }, null, { timeout: 5000 });
  const nowShellOpen = await shellOpen(page);
  // Esc that closed the overlay must not have leaked a shell toggle (opened from home).
  if (!wasShellOpen && nowShellOpen) throw new Error('Esc closing the tally overlay leaked into shell-open');
  record(name, true, 'chip→overlay, 🪨 RUNES active moved, Esc closed clean (no shell side-effect)');
}

async function j4_escDiscipline(page) {
  const name = 'J4 ESC DISCIPLINE';
  await goHome(page);
  // open a pane
  await page.click('#head-tabs .ht[data-tab="forge"]');
  await page.waitForFunction(() => document.body.classList.contains('shell-open'), null, { timeout: 8000 });
  // Escape with no overlays up → back home (stage visible)
  await page.keyboard.press('Escape');
  await page.waitForFunction(() => {
    if (document.body.classList.contains('shell-open')) return false;
    const s = document.getElementById('stage');
    return !!(s && s.getClientRects().length);
  }, null, { timeout: 8000 });
  // reopen a pane (best-effort; no forced board overlays / game data)
  await page.click('#head-tabs .ht[data-tab="forge"]');
  await page.waitForFunction(() => document.body.classList.contains('shell-open'), null, { timeout: 8000 });
  await goHome(page); // leave clean
  record(name, true, 'Escape (no overlay) returned home; pane reopened cleanly');
}

async function j5_threeEyes(page) {
  const name = 'J5 THREE EYES';
  const r = await page.evaluate(() => {
    const ids = ['eye-live', 'eye-second', 'eye-kai'];
    const eyes = ids.map((id) => !!document.getElementById(id));
    const status = ids.map((id) => {
      const s = document.getElementById(id + '-s');
      return s ? (s.textContent || '').trim() : '';
    });
    const det = document.querySelector('details.sig-adv');
    return {
      eyes, status,
      detailsExists: !!det,
      detailsClosed: det ? det.open === false : null,
    };
  });
  if (!r.eyes.every(Boolean)) throw new Error(`missing eye element(s): ${JSON.stringify(r.eyes)}`);
  if (!r.status.every((t) => t.length > 0)) throw new Error(`empty eye status text: ${JSON.stringify(r.status)}`);
  if (!r.detailsExists) throw new Error('⚙ advanced <details> missing');
  if (!r.detailsClosed) throw new Error('⚙ advanced <details> is open (should default closed)');
  record(name, true, `3 eyes present, status=[${r.status.join(' | ')}], ⚙ advanced closed`);
}

async function j6_signalPanel(page) {
  const name = 'J6 SIGNAL PANEL';
  const r = await page.evaluate(() => {
    const panel = document.querySelector('.signal');
    const panelText = panel ? (panel.textContent || '') : '';
    const rows = panel ? Array.from(panel.querySelectorAll('.row')) : [];
    // case-sensitive: 'BRIDGE' must not appear as a signal ROW label anymore
    const bridgeRow = rows.some((el) => (el.textContent || '').indexOf('BRIDGE') !== -1);
    return {
      hasPanel: !!panel,
      hasSignal: panelText.indexOf('Signal') !== -1,
      hasWatching: panelText.indexOf('Watching') !== -1,
      bridgeRow,
    };
  });
  if (!r.hasPanel) throw new Error('.signal panel missing');
  if (!r.hasSignal) throw new Error("humanized 'Signal' label not found in panel");
  if (!r.hasWatching) throw new Error("humanized 'Watching' label not found in panel");
  if (r.bridgeRow) throw new Error("'BRIDGE' still present as a signal row label");
  record(name, true, "'Signal' + 'Watching' present, no 'BRIDGE' row label");
}

async function j7_shelfStory(page) {
  const name = 'J7 SHELF STORY';
  await goHome(page);
  const shellBefore = await shellOpen(page); // home → false
  // 📚 The Shelf console button: thOpen() (loads TH.sessions from /api/sessions) then thShelf(true)
  await page.click('#btn-shelf');
  // the shelf overlay #th-shelfov renders one .sh-card per recorded session
  await page.waitForFunction(() => {
    const ov = document.getElementById('th-shelfov');
    if (!ov || ov.hidden) return false;
    return ov.querySelectorAll('.sh-card').length > 0;
  }, null, { timeout: 15000 });
  const r = await page.evaluate(() => {
    const glyphs = ['🛡', '🚨', '🧠', '📸']; // seal-verdict markers
    const cards = document.querySelectorAll('#th-shelfov .sh-card');
    const verdicts = Array.from(document.querySelectorAll('#th-shelfov .sh-verdict'));
    // any rendered verdict line must carry at least one verdict glyph; zero-verdict
    // (unsealed) cards simply have no .sh-verdict span and are tolerated.
    const bad = verdicts.find((v) => {
      const t = v.textContent || '';
      return !glyphs.some((g) => t.indexOf(g) !== -1);
    });
    return {
      cards: cards.length,
      verdicts: verdicts.length,
      bad: bad ? (bad.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null,
    };
  });
  if (r.cards < 1) throw new Error('shelf rendered zero .sh-card');
  if (r.bad) throw new Error(`.sh-verdict missing a 🛡/🚨/🧠/📸 glyph: "${r.bad}"`);
  // close cleanly: the shelf toggle (#th-shelf, in the uncovered bottom strip) hides the
  // overlay, then #th-close folds the theatre → console returns to its prior (home) state.
  await page.click('#th-shelf');
  await page.waitForFunction(() => {
    const ov = document.getElementById('th-shelfov');
    return !ov || ov.hidden;
  }, null, { timeout: 5000 });
  await page.click('#th-close');
  await page.waitForFunction(() => {
    const th = document.getElementById('theatre');
    if (!th || !th.hidden) return false;
    if (document.body.classList.contains('shell-open')) return false;
    const s = document.getElementById('stage');
    return !!(s && s.getClientRects().length);
  }, null, { timeout: 6000 });
  const shellAfter = await shellOpen(page);
  if (shellBefore !== shellAfter) throw new Error('shelf journey left the shell state changed');
  record(name, true, `${r.cards} .sh-card, ${r.verdicts} verdict line(s) all glyph-tagged, closed → home`);
}

// v1378 — J8: the console-native Sessions flagship. 'session' nav sets data-view=sessions and
// shows the hunt hub as the console home (NO bible pane / shell-open); TV·D restores the cockpit.
async function j8_sessionsFlagship(page) {
  const name = 'J8 SESSIONS FLAGSHIP';
  await goHome(page);
  await page.click('#head-tabs .ht[data-tab="session"]');
  await page.waitForFunction(() => {
    if (document.body.classList.contains('shell-open')) return false;          // console-native, not a bible pane
    if (document.body.getAttribute('data-view') !== 'sessions') return false;
    const hunt = document.querySelector('.zone-hunt'), stage = document.getElementById('stage');
    return hunt && getComputedStyle(hunt).display !== 'none' && (!stage || getComputedStyle(stage).display === 'none');
  }, null, { timeout: 8000 });
  await page.click('#head-tabs .ht[data-tab="tvd"]');
  await page.waitForFunction(() => {
    if (document.body.getAttribute('data-view') === 'sessions') return false;
    const s = document.getElementById('stage');
    return !!(s && s.getClientRects().length);
  }, null, { timeout: 8000 });
  record(name, true, 'session→data-view=sessions (hunt shown, stage hidden, no shell) · tvd→cockpit');
}


// v1578 — J9: the TERROR ZONE flagship. Three things had to become true at once and each one was
// invisible on its own: the art has to come from the GAME (not the diablo2.io act pictures that
// covered 13 of 67 zones), a three-zone rotation must not render a chip called "and <Zone>", and a
// weak zone must LOOK weak. The route is stubbed with a rotation chosen to exercise all three:
// a dense prime, a boss-prime that density alone would have greyed, and two thin Act 1 zones.
async function j9_terrorZoneFlagship(page) {
  const name = 'J9 TERROR ZONE FLAGSHIP';
  await page.route('**/api/tz', (r) => r.fulfill({
    status: 200, contentType: 'application/json',
    /* v1641 — THE ROTATION NOW CONTAINS THE CASE KONYO SCREENSHOTTED, WHICH IT NEVER DID.
       The defect is a card carrying an optional `why` subtitle standing taller than one without,
       so LIVE NOW and UP NEXT stop lining up. The old stub could not produce it across the two
       slots: every slot had a why-bearing zone in it (Travincal · The Pit), so both grids grew by
       the same line and the mismatch cancelled out. A gate whose fixture cannot express the bug
       passes for the same reason an empty list passes every assertion about its members.
       LIVE NOW now carries BOTH kinds of why — a TZ_NOTABLE boss line (Travincal · "the Council")
       and a TZ_HINT adjacency line (Ancient's Way · "next door to the Ancient Tunnels") — beside
       two zones with no why at all. UP NEXT carries NONE: Cold Plains (520) and Outer Cloister
       (600) are both in TZ_INFO, both thin, and in neither TZ_NOTABLE nor TZ_HINT. So the two
       slots are asymmetric exactly as he photographed them, and `whyNow`/`whyNext` below assert
       that asymmetry is still there — deleting the why zone to make the gate green now FAILS. */
    body: JSON.stringify({ current: "Stony Tomb, Travincal, Ancient's Way, and Blood Moor",
                           next: 'Cold Plains and Outer Cloister', ts: Date.now() }) }));
  await goHome(page);
  await page.click('#head-tabs .ht[data-tab="session"]');
  await page.evaluate(() => { const b = document.getElementById('tz-refresh'); if (b) b.click(); });
  await page.waitForFunction(() => document.querySelectorAll('#tz-body .tzz').length >= 5,
                             null, { timeout: 9000 });
  const out = await page.evaluate(() => [...document.querySelectorAll('#tz-body .tzz')].map((z) => ({
    n: (z.querySelector('b') || {}).textContent || '',
    t: [...z.classList].find((c) => ['tzz-prime', 'tzz-good', 'tzz-thin'].includes(c)) || '',
    art: ((z.querySelector('.tzz-art') || {}).style || {}).backgroundImage || '',
    grey: getComputedStyle(z).filter })));
  const by = (n) => out.find((o) => o.n === n);
  const fail = [];
  // v1580 — PLACEMENT, pinned. Konyo asked twice for this panel at the top of Sessions. v1573
  // answered with `order:-1`, which only sorts a card WITHIN its own zone — and the card was in
  // Ⅲ THE RECORD, so it was hoisted to the top of the BOTTOM zone and rendered at y=613 under
  // three empty placeholders. The CSS said yes and the page said no, and nothing caught it.
  const place = await page.evaluate(() => {
    const el = document.getElementById('hd-tz');
    if (!el) return { missing: true };
    const zone = el.closest('section.zone');
    const ban = zone && zone.querySelector('.zone-banner');
    /* v1641 — MEASURE BOTH SLOTS. Konyo's complaint is "this needs to be symmetric and aligned
       to the other acts at LIVE. you see how its off" — a comparison BETWEEN LIVE NOW and UP
       NEXT. This measured only `.tz-zones-hero`, i.e. LIVE NOW alone, so the one relationship he
       was pointing at was the one thing never looked at. Inside a single grid the v1640 rule
       (`grid-auto-rows:1fr`) really does equalise the rows even though the container is
       auto-height — per CSS Grid §12.7.1 an indefinite container sizes every 1fr track to the
       largest track's max-content — which is why the old one-slot measurement stayed green while
       the panel was visibly uneven. What 1fr can never do is reach ACROSS two sibling grids. */
    const boxes = (sel) => [...document.querySelectorAll(sel)].map((c) => {
      const r = c.getBoundingClientRect();
      return { n: ((c.querySelector('b') || {}).textContent || '').trim(),
               w: Math.round(r.width), h: Math.round(r.height), y: Math.round(r.y),
               /* v1641 — the .tzz-why ELEMENT is now always emitted (it reserves its line even
                  when empty, which is the fix), so its PRESENCE means nothing. A card carries a
                  why only if that line has TEXT — the proxy and the thing are different here. */
               why: !!((c.querySelector('.tzz-why') || {}).textContent || '').trim() };
    });
    const cards = boxes('#tz-body .tz-zones-hero .tzz');
    const nextCards = boxes('#tz-body .tz-slot.next .tzz');
    const all = cards.concat(nextCards);
    const hs = all.map((c) => c.h);
    return {
      /* the fixture guard: if the rotation under test stops containing a why-bearing card beside
         a why-less one, this gate is measuring nothing and must say so rather than pass. */
      whyNow: cards.filter((c) => c.why).length,
      whyNext: nextCards.filter((c) => c.why).length,
      slotSpread: hs.length ? Math.max(...hs) - Math.min(...hs) : 0,
      allBoxes: all.map((c) => (c.why ? '★' : '·') + c.n + ' ' + c.w + 'x' + c.h + '@y' + c.y),
      numeral: ban ? (ban.querySelector('.zb-no') || {}).textContent : null,
      /* v1930 — "FIRST CARD" MEANS FIRST CARD, NOT FIRST CHILD. This asserted
         `zone.children[1] === el`, which silently assumed nothing would ever sit between the zone
         banner and the flagship. v1914 put `#chron-waiting` there — a one-line notice that appears
         only when a sweep is waiting on him, and which he asked for on the tab he lives on. The
         flagship is still the first CARD; it is no longer the second CHILD.
         Measured: children are [zone-banner, chron-waiting, hd-tz, hd-taskforce].
         Compare against the cards, so a notice line cannot fail a layout gate. */
      firstCard: zone
        ? [...zone.children].filter((c) => c.classList.contains('hd-col'))[0] === el
        : false,
      bannerAbove: ban ? ban.getBoundingClientRect().y < el.getBoundingClientRect().y : false,
      fullWidth: Math.round(el.getBoundingClientRect().width)
                 >= Math.round(el.parentElement.getBoundingClientRect().width) - 24,
      equalW: new Set(all.map((c) => c.w)).size === 1,
      equalH: new Set(all.map((c) => c.h)).size === 1,
      /* v1639 — ONE ROW WAS A PROXY, AND IT BECAME A FALSE ONE. This asserted every zone card
         shared a single y, which was right while the hero held all four zones across a ~1400px
         card. v1637/v1639 split the card into LIVE NOW + UP NEXT slots of ~682px each, and four
         cards in one 682px row is exactly what produced the defect Konyo screenshotted: tiles at
         157.75px with THIRTEEN clipped text nodes, zone names rendered at 0px wide ("T a." /
         "O u."). So the honest invariant is not "one row" — it is EVEN rows and NOTHING CLIPPED.
         rowsEven keeps the alignment guarantee (cards sharing a y must share a width and height,
         and there are at most two rows); clipped is the property that actually matters and was
         never asserted at all, which is how the crammed row passed this gate for two versions. */
      /* v1640 — THE SECOND ATTEMPT AT THIS WAS ALSO A LAYOUT ASSUMPTION. `oneRow` was wrong once
         the card split into two slots; the replacement capped rows at TWO, and that failed on a
         perfectly even stack — measured ["484x139@y456","484x139@y604","484x139@y752"], three
         IDENTICAL cards in a 484px slot that fits one column. How many rows the zones land in is
         the browser's business and changes with the slot width and the size of the rotation. What
         must hold is that the cards agree with each other and nothing is clipped. So: every row's
         cards share a width and a height — no cap on the number of rows. */
      rowsEven: (() => {
        const rows = new Map()
        for (const c of all) { if (!rows.has(c.y)) rows.set(c.y, []); rows.get(c.y).push(c) }
        for (const row of rows.values()) {
          if (new Set(row.map((c) => c.w)).size !== 1) return false
          if (new Set(row.map((c) => c.h)).size !== 1) return false
        }
        return true
      })(),
      cardBoxes: all.map((c) => c.w + 'x' + c.h + '@y' + c.y),
      /* ══ v1679 · THE ROWS INSIDE THE CARD, WHICH NOTHING HERE HAS EVER MEASURED ═══════════════
         Konyo: "tz tracker i want aligned the sections/acts within it they are like not syymetric".
         Every assertion above is about the CARD — its width, its height, its y. All of them were
         GREEN on the rotation he screenshotted, because the cards really were even; what was
         crooked was the type INSIDE them. The zone name wraps to two lines for "Worldstone Keep"
         and one for "Black Marsh", so ACT sat 28px lower in UP NEXT than in LIVE NOW, and the
         density line's optional `→ 96 terrorized` moved it another 14px between UP NEXT's own two
         rows. Measured before the v1679 fix at 1920px: three distinct offset sets — ACT at +40,
         +68 and +83 from the card top on five cards in one panel.
         So this measures each line's offset FROM ITS OWN CARD and demands one answer across every
         card in BOTH slots. Offsets are fractional (grid tracks land on half pixels), so the
         invariant is a 1px spread, not equality — rounding each side separately manufactured a
         1px "failure" on a panel that was in fact aligned to 0.01px. */
      rowSpread: (() => {
        const rows = ['.tzz-art', '.tzz-txt i', '.tzz-why', '.tzz-den'];
        const cards = [...document.querySelectorAll('#tz-body .tz-slot .tzz')];
        const out = {};
        for (const sel of rows) {
          const offs = cards.map((c) => {
            const e = c.querySelector(sel);
            return e ? e.getBoundingClientRect().y - c.getBoundingClientRect().y : null;
          }).filter((v) => v !== null);
          out[sel] = offs.length ? +(Math.max(...offs) - Math.min(...offs)).toFixed(2) : null;
        }
        return out;
      })(),
      clipped: [...document.querySelectorAll('#tz-body .tz-slot .tzz *')]
        .filter((n) => n.childElementCount === 0 && (n.textContent || '').trim())
        .filter((n) => n.scrollWidth > n.clientWidth + 1)
        .map((n) => ((n.textContent || '').trim().slice(0, 24) + ' @' + Math.round(n.getBoundingClientRect().width) + 'px')),
      // v1588 — the prose legend was REMOVED on purpose; the treatment carries the verdict now.
      // v1801 — and the LOCK was removed on purpose too. Dropping the meaningless level term from
      // both tzTiers takes thin from 15 zones to 40, so Konyo chose greyed-and-cancelled but still
      // clickable: a lock over most of the map punishes him for a ranking instead of reporting it.
      // What this now checks is the pair that can go wrong — the verdict must survive undimmed AND
      // the card must route. Checking only one half is how a card ends up bright and clickable, or
      // grey and dead.
      thinGrey: [...document.querySelectorAll('#tz-body .tzz-thin')]
        .every((c) => parseFloat(getComputedStyle(c).opacity) <= 0.35
                   && getComputedStyle(c).filter.includes('grayscale')),
      /* ⚠ v1930 — THIS ASSERTED A DECISION HE HAS SINCE REVERSED, FOR THE THIRD TIME.
         v1588 made a thin zone inert. v1801 undid it: dropping the meaningless level term took
         thin from 15 zones to 40, and "a lock over most of the map stops informing him of a
         ranking and starts overruling him with one". v1915 reversed it again, in his own words:
         "the mouse cursor for TZ ZONES that arent worth farming at all i want a CANCELLED sign on
         it so i know i cant click them. only the TZ ZONES worth farming should be clickable and
         routable."
         So a thin card must now be INERT and SAY SO: role=button for the screen reader, explicitly
         aria-disabled, no click handler, cursor:not-allowed. The old assertion is not a bug that
         appeared — it is a recorded expectation that his instruction superseded, and updating it is
         the honest move rather than reverting a feature he asked for twice.
         The pair that can still go wrong is unchanged in spirit: the verdict must survive undimmed
         AND the card must be honestly inert. Checking one half is how a card ends up bright and
         dead, or grey and secretly clickable. */
      thinRoutes: [...document.querySelectorAll('#tz-body .tzz-thin')]
        .every((c) => c.getAttribute('role') === 'button'
                   && c.getAttribute('aria-disabled') === 'true'
                   && !c.hasAttribute('onclick')
                   && getComputedStyle(c).cursor === 'not-allowed'),
      thinSeen: document.querySelectorAll('#tz-body .tzz-thin').length,
      routes: [...document.querySelectorAll('#tz-body .tzz-prime, #tz-body .tzz-good')]
        .every((c) => c.getAttribute('role') === 'button'),
    };
  });
  if (place.missing) fail.push('the TZ panel is gone from Sessions');
  else {
    if (place.numeral !== 'Ⅰ') fail.push(`the rotation is filed under ${place.numeral}, not Ⅰ THE HUNT`);
    if (!place.firstCard) fail.push('it is not the first card in its zone');
    if (!place.bannerAbove) fail.push('the card jumped above its own zone banner');
    if (!place.fullWidth) fail.push('it is not stretched left to right');
    /* v1640 — A GATE THAT SAYS "not evenly placed" AND NOTHING ELSE COSTS A DEBUG CYCLE EVERY
       TIME IT FIRES. Carry the geometry it just measured. */
    if (!place.equalW || !place.equalH || !place.rowsEven) {
      fail.push('the zone cards are not evenly placed (spread ' + place.slotSpread + 'px) — '
                + JSON.stringify(place.allBoxes || []));
    }
    /* v1641 — NON-VACUITY, ASSERTED. The height invariant above is only worth anything while the
       rotation actually contains a card with a `why` subtitle standing beside cards without one;
       with a uniform fixture it is true for free. So the fixture itself is now under test: LIVE
       NOW must render at least one .tzz-why and UP NEXT must render none. Making this gate green
       by deleting the why zone is the one cheat this assertion exists to refuse. */
    if (!place.whyNow) {
      fail.push('FIXTURE IS BLIND — no LIVE NOW card carries a `why` subtitle, so the equal-height '
                + 'assertion above cannot fail; restore a why-bearing zone to the stub rotation');
    }
    if (place.whyNext) {
      fail.push(`FIXTURE IS BLIND — ${place.whyNext} UP NEXT card(s) carry a \`why\` subtitle, so both `
                + 'slots grow by the same line and a cross-slot mismatch cannot show');
    }
    // v1639 — the assertion that would have caught the crammed row on day one, instead of two
    // versions later from a screenshot. A label the user cannot read is a broken card, whatever
    // its geometry says.
    if (place.clipped && place.clipped.length) {
      fail.push(`${place.clipped.length} clipped label(s) in the zone cards: ${place.clipped.slice(0, 4).join(' · ')}`);
    }
    // the stub rotation deliberately contains a thin zone, so seeing none means the tiering
    // stopped working rather than that this window happened to be all good
    if (!place.thinSeen) fail.push('no thin zone rendered — the tiering is not running');
    if (!place.thinGrey) fail.push('a thin zone is not greyed out — the verdict stopped being visible');
    if (!place.thinRoutes) fail.push('a thin zone is not honestly inert — it must be role=button, aria-disabled, no onclick, cursor:not-allowed (v1915, his words)');
    if (!place.routes) fail.push('a zone worth running does not route anywhere');
  }
  if (out.some((o) => /^and /i.test(o.n))) fail.push('a chip is labelled "and <Zone>" — the Oxford-comma split is back');
  if (!out.every((o) => o.art.includes('/art/tz_'))) fail.push('a zone has no game-extracted face');
  if ((by('Travincal') || {}).t !== 'tzz-prime') fail.push('Travincal (density 325, the Council) was not PRIME');
  if ((by('Blood Moor') || {}).t !== 'tzz-thin') fail.push('Blood Moor was not greyed');
  if (!((by('Blood Moor') || {}).grey || '').includes('grayscale')) fail.push('the THIN treatment is not visually distinct');
  if ((by('Stony Tomb') || {}).t !== 'tzz-prime') fail.push('Stony Tomb (density 2200) was not PRIME');

  /* ══ v1679 · A SECOND ROTATION, BECAUSE THE ONE ABOVE CANNOT FAIL THIS ═══════════════════════
     Konyo: "tz tracker i want aligned the sections/acts within it they are like not syymetric" —
     the lines INSIDE the cards, not the cards. Every assertion above is about card geometry and
     all of them were green on the panel he photographed.

     I wrote the offset check against the fixture above first and it passed with the fix REMOVED —
     measured, not assumed: 484x139 cards, spread 0px, gate green, defect fully present on his
     screen. None of Stony Tomb / Travincal / Ancient's Way / Blood Moor / Cold Plains / Outer
     Cloister wraps its name at 484px and all six carry the same density shape, so the fixture is
     blind to this the same way the pre-v1641 one was blind to the `why` line. That is the exact
     failure mode the two FIXTURE IS BLIND guards above exist to name, so the answer is a fixture
     that CAN express it, not a softer assertion.

     HIS ROTATION, verbatim from the 01:34 screenshot. It carries both triggers at once:
       · "Worldstone Keep" wraps to two lines where "Black Marsh" does not — and the two slots are
         sibling grids, so `grid-auto-rows:1fr` cannot equalise across them (:2664).
       · "Worldstone Chamber" has density but no alvl, so it renders no `→ 96 terrorized` verdict
         row while its neighbours do.
     Before v1679 this produced ACT at +40 / +68 / +83 from the card top on five cards in one
     panel; after, one offset for every line on every card in both slots.
     Kept as a SEPARATE pass rather than by editing the rotation above, because that one is
     load-bearing for the tier, art, oxford-comma and why/no-why assertions. */
  await page.unroute('**/api/tz');
  await page.route('**/api/tz', (r) => r.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ current: 'Black Marsh and The Hole',
                           next: 'Worldstone Keep, Throne of Destruction, and Worldstone Chamber',
                           ts: Date.now() }) }));
  /* v1682 — WIDEN THE WINDOW, OR THE SQUEEZE CANNOT HAPPEN. The suite runs at 1470px, where the
     TZ slot fits ONE 484px column and every zone name has room to spare. The mid-word break needs
     the TWO-column layout: at 1920px the slot is 682px, `.tz-zones` auto-fit puts two ~325px cards
     side by side, and the name column drops to 134px against a 139px "Worldstone". I wrote this
     assertion at 1470 first and it passed with the fix REMOVED — measured, not assumed. A wider
     window is the fixture, exactly as the second rotation is. Restored below so nothing after this
     inherits it. */
  await page.setViewportSize({ width: 1920, height: 1200 });
  await page.evaluate(() => { const b = document.getElementById('tz-refresh'); if (b) b.click(); });
  await page.waitForFunction(() => [...document.querySelectorAll('#tz-body .tzz b')]
    .some((b) => /Worldstone/.test(b.textContent)), null, { timeout: 9000 }).catch(() => {});
  const rows = await page.evaluate(() => {
    const cards = [...document.querySelectorAll('#tz-body .tz-slot .tzz')];
    /* offset FROM ITS OWN CARD, subtracted before rounding: grid tracks land on half pixels, and
       rounding each side separately manufactures a 1px "failure" on a panel aligned to 0.01px. */
    const spread = (sel) => {
      const offs = cards.map((c) => {
        const e = c.querySelector(sel);
        return e ? e.getBoundingClientRect().y - c.getBoundingClientRect().y : null;
      }).filter((v) => v !== null);
      return offs.length ? +(Math.max(...offs) - Math.min(...offs)).toFixed(2) : null;
    };
    /* v1682 — NO NAME MAY BE FORCED TO BREAK INSIDE A WORD. `.tzz-top` is a flex row shared with
       the PRIME/GOOD badge, and `.tzz-top b { min-width: 0 }` licensed the name to shrink below
       its own longest word — measured at 1920px, a 134px box against a 139px "Worldstone", which
       rendered "Worldston / e Keep" on three of five cards. Compared against the CANVAS-measured
       width of the longest word in the name's own computed font, so this asks whether a break is
       FORCED rather than trying to read the rendered line boxes. */
    const midWord = cards.map((c) => {
      const nm = c.querySelector('.tzz-top b');
      if (!nm) return null;
      const cs = getComputedStyle(nm);
      const ctx = document.createElement('canvas').getContext('2d');
      ctx.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
      const words = (nm.textContent || '').trim().split(/\s+/);
      const need = Math.max(...words.map((w) => ctx.measureText(w).width));
      return nm.getBoundingClientRect().width + 1 < need
        ? (nm.textContent || '').trim() + ' (' + Math.round(nm.getBoundingClientRect().width)
          + 'px box vs ' + Math.ceil(need) + 'px word)' : null;
    }).filter(Boolean);
    return { n: cards.length, midWord,
             wrapped: cards.some((c) => { const b = c.querySelector('.tzz-top b');
               return b && b.getBoundingClientRect().height > parseFloat(getComputedStyle(b).lineHeight) * 1.5; }),
             noVerdict: cards.some((c) => !c.querySelector('.tzz-terr')),
             art: spread('.tzz-art'), act: spread('.tzz-txt i'),
             why: spread('.tzz-why'), den: spread('.tzz-den') };
  });
  if (rows.n < 5) fail.push(`the second rotation rendered ${rows.n} zone cards, expected 5`);
  if (rows.midWord && rows.midWord.length) {
    fail.push('a zone name is squeezed narrower than its own longest word, so it breaks mid-word — '
              + rows.midWord.join(' · '));
  }
  /* NON-VACUITY, same discipline as whyNow/whyNext: this fixture is only worth running while it
     still contains a wrapped name AND a card with no verdict row. Lose either and it goes blind. */
  if (!rows.wrapped) fail.push('FIXTURE IS BLIND — no zone name wraps to two lines, so a cross-slot '
                               + 'name-height mismatch cannot show; restore a long-named zone');
  if (!rows.noVerdict) fail.push('FIXTURE IS BLIND — every card carries a `→ 96 terrorized` verdict, '
                                 + 'so a missing-verdict height mismatch cannot show');
  {
    const crooked = ['art', 'act', 'why', 'den'].filter((k) => rows[k] !== null && rows[k] > 1);
    if (crooked.length) {
      fail.push('the lines inside the zone cards do not line up across the two slots — '
                + crooked.map((k) => k + ' varies by ' + rows[k] + 'px').join(', '));
    }
  }
  await page.unroute('**/api/tz');
  await page.setViewportSize({ width: 1470, height: 920 });   // v1682 — hand the suite back its window
  record(name, fail.length === 0,
         fail.length ? fail.join(' · ')
                     : `${out.length} zones · all faces game-extracted · PRIME/THIN separated (Travincal kept by boss override)`
                       + ` · cards level across BOTH slots, spread ${place.slotSpread}px `
                       + `(${place.whyNow} why live / ${place.whyNext} up next): ${JSON.stringify(place.allBoxes)}`);
}

// ── runner ──────────────────────────────────────────────────────────────────────
async function main() {
  const t0 = Date.now();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1470, height: 920 } });
  const page = await context.newPage();

  try {
    const resp = await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 20000 });
    if (!resp || !resp.ok()) throw new Error(`console did not load OK (status ${resp && resp.status()}) — is it running?`);
    await page.waitForSelector('#head-tabs .ht', { timeout: 15000 });
    await warmEngine(page);
  } catch (e) {
    console.log(`❌ BOOT — ${e.message}`);
    console.log('DEMOS: 0/9 ✅');
    await browser.close();
    process.exitCode = 1;
    return;
  }

  const journeys = [j1_shellMatrix, j2_alignment, j3_tally, j4_escDiscipline, j5_threeEyes, j6_signalPanel, j7_shelfStory, j8_sessionsFlagship, j9_terrorZoneFlagship];
  for (const j of journeys) {
    try {
      await j(page);
    } catch (e) {
      // name is derivable from the first record miss; print explicit failure line
      record(j.name || 'journey', false, (e && e.message) ? e.message.split('\n')[0] : String(e));
    }
  }

  await browser.close();
  const pass = results.filter((r) => r.ok).length;
  const secs = ((Date.now() - t0) / 1000).toFixed(1);
  console.log(`DEMOS: ${pass}/9 ✅  (${secs}s)`);
  /* v2112 — AND THE FAILURES AGAIN, AFTER THE SUMMARY. hooks/pre-push shows only the TAIL of
     this output, so a failure printed at the top — where it happens — is cut off, and the gate
     reports "DEMOS: 8/9" with no way to tell WHICH journey or why. I chased one of these three
     times reading a truncated log. The line costs nothing when everything passes. */
  const failed = results.filter((r) => !r.ok);
  if (failed.length) {
    console.log('── what failed (repeated here because the gate only shows the tail) ──');
    for (const r of failed) console.log(`   ❌ ${r.name} — ${r.detail || '(no detail)'}`);
  }
  process.exitCode = pass === 9 ? 0 : 1;
}

main().catch((e) => {
  console.log(`❌ FATAL — ${e && e.stack ? e.stack : e}`);
  process.exitCode = 1;
});
