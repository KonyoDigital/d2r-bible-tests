import { test, expect } from '@playwright/test';

// v353 — base reverse-index: a white/grey base's hover-card lists every runeword it enables (+ the
// socket count to chase), so "keep for Spirit/Insight…" vs "vendor" is obvious. Built from the
// bible's own RUNEWORD_TIP base categories (no new data), surfaced on the throw-out base tip.

const URL = 'file://' + process.cwd() + '/bible.html';

test('base → runewords classifier + throw-out base tip line', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const w = window as any;
    const names = (a: any[]) => a.map((x) => x.n);
    const archon = names(w._baseRunewords('Archon Plate'));
    const monarch = names(w._baseRunewords('Monarch'));
    const crystal = names(w._baseRunewords('Crystal Sword'));
    // the throw-out base tip should now include the runeword line
    const tip = w._arttipResolve ? '' : '';
    let tipHas = false;
    try { tipHas = /Keep for runewords/.test((function(){
      // simulate a socketed base in unknownReads to render the tip
      try { eval('unknownReads').add('Monarch (4os low base)'); } catch(e){}
      const vr = w._arttipResolve('Monarch (4os low base)');
      return vr && vr.desc || '';
    })()); } catch(e){}
    return { archon, monarch, crystal, tipHas };
  });
  expect(errs).toEqual([]);
  expect(r.archon).toContain('Enigma');         // body armor
  expect(r.archon).toContain('Chains of Honor');
  expect(r.monarch).toContain('Spirit');         // shield
  expect(r.monarch).not.toContain('Exile');      // Exile is paladin AURIC-shield only (a Monarch can't host it)
  expect(r.crystal).toContain('Spirit');         // sword
  expect(r.tipHas).toBe(true);                   // surfaced on the base hover card
});
