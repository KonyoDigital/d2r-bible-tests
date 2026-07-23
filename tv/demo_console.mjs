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
    console.log('DEMOS: 0/8 ✅');
    await browser.close();
    process.exitCode = 1;
    return;
  }

  const journeys = [j1_shellMatrix, j2_alignment, j3_tally, j4_escDiscipline, j5_threeEyes, j6_signalPanel, j7_shelfStory, j8_sessionsFlagship];
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
  console.log(`DEMOS: ${pass}/8 ✅  (${secs}s)`);
  process.exitCode = pass === 8 ? 0 : 1;
}

main().catch((e) => {
  console.log(`❌ FATAL — ${e && e.stack ? e.stack : e}`);
  process.exitCode = 1;
});
