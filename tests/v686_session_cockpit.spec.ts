import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v686 — ⚡ SESSION COCKPIT (Grok's v44 concept rebuilt native): one-screen session plan.
// Guards: the workshop nav gains the session tab WITHOUT moving existing tabs; the cockpit
// renders its 4 cards from the LIVE truths (rwMade seed / funiScan wall / MF dock); the
// session-target pin + stash freshness both persist through window.LSR (account-forked,
// d2r_chroniclePin + d2r_stashMeta in _LP_FORKED); intake fns are wrapped as OBSERVERS only
// (the locked intake pipeline itself untouched); progress snapshots are schema v2 with FLAT
// data (v1-compatible restore). TZ card fails soft on file://.

test('workshop nav: ⚡ session added first, existing tabs untouched', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const ws = Array.from(document.querySelectorAll('.tabs-workshop .tab')).map(b => b.getAttribute('data-tab'));
    return { ws, dataCount: document.querySelectorAll('.tabs-data .tab').length };
  });
  expect(r.ws).toEqual(['session', 'tools', 'forge', 'funi', 'fsets', 'tvd']);   // v710.4 — +📺 TV·D
  expect(r.dataCount).toBe(11);   // the data group is untouched (v641 nav is settled)
});

test('cockpit renders 4 cards + live KPIs + freshness chips on the seeded profile', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2500);
  await page.evaluate(() => (window as any).switchTab('session'));
  await page.waitForTimeout(1800);
  // v688 recalibration — the cockpit became Grok's ⚔️ Task Force layout: mission brief (the ONE
  // computed order) + ops queue + TZ/intel/log cards. Same truths, new surfaces.
  const r = await page.evaluate(() => {
    return {
      active: document.getElementById('tab-session')!.classList.contains('active'),
      cards: document.querySelectorAll('#tab-session .sc-card').length,
      kpiText: document.getElementById('sc-kpis')!.textContent || '',
      chips: document.querySelectorAll('#sc-fresh .sc-chip').length,
      tz: document.getElementById('sc-tz-body')!.textContent || '',
      mission: document.getElementById('sc-mission-body')!.textContent || '',
      opsRows: document.querySelectorAll('#sc-ops-body .sc-ops-row, #sc-ops-body .sc-row').length,
      logBody: document.getElementById('sc-log-body')!.textContent || '',
    };
  });
  expect(r.active).toBe(true);
  expect(r.cards).toBe(6);                                    // ops · tz · intel · log · 📺 TV DIABLO (v710) · ⚔️ DAILY TASK FORCE (v907)
  expect(r.kpiText).toContain('Chronicle');
  expect(r.kpiText).toContain('Grail');
  // v691 (🏓 R1) — 2+ stale stashes collapse into ONE intel-gate chip ('N of 4 stashes unscanned');
  // per-stash chips return as intel freshens. Fresh profile ⇒ the single gate.
  expect(r.chips).toBeGreaterThanOrEqual(1);
  expect(r.tz).toMatch(/online site|live on bull|tracker/);   // file:// = graceful note, no fetch error
  expect(r.mission.length).toBeGreaterThan(10);               // the general always issues an order (auto or standby)
  expect(r.opsRows).toBeGreaterThan(0);                       // fresh profile: stale-intel blockers guarantee ops
  expect(r.logBody.length).toBeGreaterThan(0);                // log renders (events or the empty-state line)
});

test('session-target pin: LSR-persisted, dock chip, account-forked, clearable', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._sessionPinSet('Windforce');
    const dock = document.getElementById('dock-pin')!;
    const set = {
      ls: w.LSR.getItem('d2r_chroniclePin'),
      dockTxt: dock.textContent || '',
      forked: w._LP_FORKED.has('d2r_chroniclePin') && w._LP_FORKED.has('d2r_stashMeta'),
    };
    w._sessionPinClear();
    return { ...set, afterClear: w.LSR.getItem('d2r_chroniclePin'), emptyCls: dock.classList.contains('empty') };
  });
  expect(r.ls).toBe('Windforce');
  expect(r.dockTxt).toContain('Windforce');
  expect(r.forked).toBe(true);
  expect(r.afterClear).toBeFalsy();
  expect(r.emptyCls).toBe(true);
});

test('ladder pin lands on L· and never touches MAIN\'s pin', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_chroniclePin', 'MainTarget');
    localStorage.setItem('d2r_activeProfile', 'ladder');
  });
  await page.goto(URL); await page.waitForTimeout(2500);
  const r = await page.evaluate(() => {
    (window as any)._sessionPinSet('LadderTarget');
    return {
      profile: (window as any).D2R_PROFILE,
      lKey: localStorage.getItem('L·d2r_chroniclePin'),
      bare: localStorage.getItem('d2r_chroniclePin'),
    };
  });
  expect(r.profile).toBe('ladder');
  expect(r.lKey).toBe('LadderTarget');
  expect(r.bare).toBe('MainTarget');
});

test('stash freshness: touch stamps via LSR and paints the Tools rail + session chips', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._stashTouch('gems');
    w.renderSessionCockpit();
    const meta = JSON.parse(w.LSR.getItem('d2r_stashMeta') || '{}');
    const rail = document.querySelector('.tqu-btn.tqu-gem')!;
    const chips = Array.from(document.querySelectorAll('#sc-fresh .sc-chip')).map(c => c.className + '|' + c.textContent);
    const gemChip = chips.find(c => c.includes('Gems')) || '';
    return {
      stamped: typeof meta.gems === 'number',
      railOk: rail.classList.contains('sc-ok'),
      railDot: !!rail.querySelector('.sc-dot'),
      gemChipOk: /sc-ok/.test(gemChip) && /ago/.test(gemChip),
      // v691 (🏓 R1) — the 3 untouched stashes collapse into the intel-gate summary chip
      staleGate: /stashes unscanned/.test(chips.join('|')),
    };
  });
  expect(r.stamped).toBe(true);
  expect(r.railOk && r.railDot).toBe(true);
  expect(r.gemChipOk).toBe(true);
  expect(r.staleGate).toBe(true);   // untouched kinds stay honest — one gate says so
});

test('intake fns wrapped as observers; snapshot is schema v2 with flat v1-compatible data', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    // @ts-ignore — persist/_progressSnapshot are script-globals, not window props
    persist();
    // @ts-ignore
    const snap = JSON.parse(_progressSnapshot());
    return {
      wraps: ['runeIntake', 'gemIntake', 'materialIntake', 'vaultIntake'].every(n => typeof w[n] === 'function' && w[n].__v686 === true),
      version: snap.version,
      meta: snap.meta,
      dataFlat: Object.keys(snap.data).every((k: string) => typeof snap.data[k] === 'string'),
      hasOwned: 'd2r_owned' in snap.data,
      noForeignNs: Object.keys(snap.data).every((k: string) => k.indexOf('L·') !== 0 && k.indexOf('W·') !== 0),
    };
  });
  expect(r.wraps).toBe(true);
  expect(r.version).toBe(2);
  expect(r.meta.schemaVersion).toBe(2);
  expect(r.meta.profile).toBe('main');
  expect(r.meta.machine).toBe('mac');
  expect(r.dataFlat && r.hasOwned && r.noForeignNs).toBe(true);
});
