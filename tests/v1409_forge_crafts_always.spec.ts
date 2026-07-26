import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1409 — crafts must NEVER vanish from the Forge when the runeword chronicle is sealed
// (or when no Perfect gem is tallied). User: "where are my crafts? create them all".

test('sealed chronicle still shows all 4 craft types + ✓ crafted buttons', async ({ page }) => {
  await page.addInitScript(() => {
    // mark every runeword made → sealed chronicle (the path that used to early-return before crafts)
    const tipKeys = Object.keys((window as any).RUNEWORD_TIP || {});
    // RUNEWORD_TIP may not exist yet in init; seed a huge made map after load instead
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_gemStash', JSON.stringify({}));
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
  });
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    try {
      // seal every word in the catalog
      const tip = w.RUNEWORD_TIP || {};
      const made: any = {};
      Object.keys(tip).forEach((n) => { made[n] = '2026-07-26'; });
      try { (w.LSR || localStorage).setItem('d2r_rwMade', JSON.stringify(made)); } catch (e) {}
      if (w.rwMade) Object.keys(tip).forEach((n) => { w.rwMade[n] = '2026-07-26'; });
    } catch (e) {}
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    // force crafts filter
    try { w.forgeSetFilter && w.forgeSetFilter('crafts'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const acc = document.querySelectorAll('#tab-forge .f-craftacc');
    const rows = document.querySelectorAll('#tab-forge .f-craftrow');
    const madeBtns = document.querySelectorAll('#tab-forge .f-craft-made');
    const names = Array.from(document.querySelectorAll('#tab-forge .f-craftacc-name')).map((el) => el.textContent || '');
    const pill = document.querySelector('#tab-forge .forge-tab.ft-craft .ft-ct');
    const scan = (typeof w.forgeScan === 'function') ? w.forgeScan() : null;
    return {
      accN: acc.length,
      rowN: rows.length,
      madeN: madeBtns.length,
      names,
      pill: pill ? pill.textContent : '',
      craftTypes: (scan && scan.craftTypes) ? scan.craftTypes.map((t: any) => t.craft) : [],
      sealedBanner: !!document.querySelector('#tab-forge .forge-sealed'),
    };
  });
  // all 4 craft types always present
  expect(r.accN).toBeGreaterThanOrEqual(4);
  expect(r.names.join(' ')).toMatch(/Caster/i);
  expect(r.names.join(' ')).toMatch(/Blood/i);
  expect(r.names.join(' ')).toMatch(/Safety/i);
  expect(r.names.join(' ')).toMatch(/Hit Power/i);
  // 4 types × 9 slots = 36 recipe rows when expanded
  expect(r.rowN).toBeGreaterThanOrEqual(36);
  expect(r.madeN).toBeGreaterThanOrEqual(36);
  expect(r.pill).toBe('4');
  expect(r.craftTypes.length).toBe(4);
});

test('craft one-step tasks when gem ready but rune missing', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_gemStash', JSON.stringify({ 'Perfect Amethyst': 2 }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({})); // no Ral etc.
  });
  await page.goto(URL);
  await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    const s = w.forgeScan();
    return {
      ready: (s.crafts || []).length,
      one: (s.craftOnestep || []).length,
      sample: (s.craftOnestep || []).slice(0, 3),
    };
  });
  expect(r.ready).toBe(0);
  expect(r.one).toBeGreaterThan(0);
  expect(r.sample[0].missKind).toBe('rune');
});
