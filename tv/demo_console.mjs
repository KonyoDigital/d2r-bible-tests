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

const URL = 'http://127.0.0.1:17772/';
const PANE_TABS = ['forge', 'funi', 'fsets', 'tools'];  // v1377 — 'session' removed: Sessions is now console-native (data-view=sessions), no longer opens a bible pane

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
  try {
    await page.waitForFunction(() => {
      const f = document.getElementById('tvd-eng');
      const w = f && f.contentWindow;
      return !!(w && typeof w.switchTab === 'function');
    }, null, { timeout: 15000 });
  } catch (_) { /* the click retry loop will cover it */ }
}

// ── the six journeys ──────────────────────────────────────────────────────────────
async function j1_shellMatrix(page) {
  const name = 'J1 SHELL MATRIX';
  await goHome(page);
  for (const tab of PANE_TABS) {
    await page.click(`#head-tabs .ht[data-tab="${tab}"]`);
    await page.waitForFunction((t) => {
      if (!document.body.classList.contains('shell-open')) return false;
      const f = document.getElementById('tvd-eng');
      const d = f && f.contentDocument;
      const a = d && d.querySelector('.tab.active');
      return !!(a && a.dataset.tab === t);
    }, tab, { timeout: 12000 });
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
      firstCard: zone ? zone.children[1] === el : false,
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
      clipped: [...document.querySelectorAll('#tz-body .tz-slot .tzz *')]
        .filter((n) => n.childElementCount === 0 && (n.textContent || '').trim())
        .filter((n) => n.scrollWidth > n.clientWidth + 1)
        .map((n) => ((n.textContent || '').trim().slice(0, 24) + ' @' + Math.round(n.getBoundingClientRect().width) + 'px')),
      // v1588 — the prose legend was REMOVED on purpose; the treatment carries the verdict now.
      locked: [...document.querySelectorAll('#tz-body .tzz-thin')]
        .every((c) => c.classList.contains('tzz-locked') && c.getAttribute('role') !== 'button'),
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
    if (!place.locked) fail.push('a thin zone is not locked (still a button, or no padlock class)');
    if (!place.routes) fail.push('a zone worth running does not route anywhere');
  }
  if (out.some((o) => /^and /i.test(o.n))) fail.push('a chip is labelled "and <Zone>" — the Oxford-comma split is back');
  if (!out.every((o) => o.art.includes('/art/tz_'))) fail.push('a zone has no game-extracted face');
  if ((by('Travincal') || {}).t !== 'tzz-prime') fail.push('Travincal (density 325, the Council) was not PRIME');
  if ((by('Blood Moor') || {}).t !== 'tzz-thin') fail.push('Blood Moor was not greyed');
  if (!((by('Blood Moor') || {}).grey || '').includes('grayscale')) fail.push('the THIN treatment is not visually distinct');
  if ((by('Stony Tomb') || {}).t !== 'tzz-prime') fail.push('Stony Tomb (density 2200) was not PRIME');
  await page.unroute('**/api/tz');
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
  process.exitCode = pass === 9 ? 0 : 1;
}

main().catch((e) => {
  console.log(`❌ FATAL — ${e && e.stack ? e.stack : e}`);
  process.exitCode = 1;
});
