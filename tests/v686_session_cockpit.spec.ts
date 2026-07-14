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
  expect(r.ws).toEqual(['session', 'tools', 'forge', 'funi', 'fsets']);
  expect(r.dataCount).toBe(11);   // the data group is untouched (v641 nav is settled)
});

test('cockpit renders 4 cards + live KPIs + freshness chips on the seeded profile', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2500);
  await page.evaluate(() => (window as any).switchTab('session'));
  await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const rwT = Object.keys(w.RUNEWORD_TIP || {}).length;
    return {
      active: document.getElementById('tab-session')!.classList.contains('active'),
      cards: document.querySelectorAll('#tab-session .sc-card').length,
      kpiText: document.getElementById('sc-kpis')!.textContent || '',
      rwT,
      chips: document.querySelectorAll('#sc-fresh .sc-chip').length,
      tz: document.getElementById('sc-tz-body')!.textContent || '',
      forge: document.getElementById('sc-forge-body')!.textContent || '',
      grailRows: document.querySelectorAll('#sc-grail-body .sc-row').length,
    };
  });
  expect(r.active).toBe(true);
  expect(r.cards).toBe(4);
  expect(r.kpiText).toContain('Chronicle');
  expect(r.kpiText).toContain('Grail');
  expect(r.chips).toBe(4);
  expect(r.tz).toMatch(/online site|live on bull/);          // file:// = graceful note, no fetch error
  expect(r.grailRows).toBeGreaterThan(0);
  // seeded Chronicle is FULL → the forge card must say sealed, not lie about "no tasks"
  const made = await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length);
  if (made >= r.rwT) expect(r.forge).toMatch(/sealed/i);
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
      runesNever: /never scanned/.test(chips.find(c => c.includes('Runes')) || ''),
    };
  });
  expect(r.stamped).toBe(true);
  expect(r.railOk && r.railDot).toBe(true);
  expect(r.gemChipOk).toBe(true);
  expect(r.runesNever).toBe(true);   // untouched kinds stay honest
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
