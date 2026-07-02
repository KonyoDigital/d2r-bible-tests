import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v547 — the Socketed & Larzuk Review / throw-out card (shared _baseRWLine) now words the base's hand-class
// (1H player / 2H merc / caster) + endgame tier IN SYNC with the Forge, using the same window._baseHandClass /
// _baseTier engines. Konyo: "even in throwout should be telling me two handed / end game gear like it is in forge."

test('_baseHandClass is exposed and agrees with the Forge for known bases', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      fn: typeof w._baseHandClass,
      championAxe: w._baseHandClass('Champion Axe'),   // 2H axe → 2H (→ merc)
      grimScythe: w._baseHandClass('Grim Scythe'),     // polearm/scythe → merc
      phaseBlade: w._baseHandClass('Phase Blade'),     // pure 1H → 1H
    };
  });
  expect(r.fn).toBe('function');
  expect(['2H', 'merc']).toContain(r.championAxe);
  expect(r.grimScythe).toBe('merc');
  expect(r.phaseBlade).toBe('1H');
});

test('a 2H base (Champion Axe) review line says 2-handed → mercenary weapon', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const html = await page.evaluate(() => (window as any)._baseRWLine('Champion Axe', 5));
  expect(html).toMatch(/2-handed/);
  expect(html).toMatch(/mercenary/i);
});

test('a 1H base (Phase Blade) review line says 1-handed → your (player) weapon', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const html = await page.evaluate(() => (window as any)._baseRWLine('Phase Blade', 6));
  expect(html).toMatch(/1-handed/);
  expect(html).toMatch(/player/i);
  expect(html).not.toMatch(/mercenary/i);
});

test('an elite base review line flags it as an endgame base', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    return { tier: w._baseTier('Phase Blade'), html: w._baseRWLine('Phase Blade', 6) };
  });
  expect(r.tier).toBe('elite');
  expect(r.html).toMatch(/endgame<\/b> base/);
});

test('a shield base (gear) shows no bogus hand note but still flags endgame', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const html = await page.evaluate(() => (window as any)._baseRWLine('Sacred Rondache', 4));
  // shields are not 1H/2H — must not claim a mercenary/player hand
  expect(html).not.toMatch(/mercenary weapon|player.*weapon/i);
  // Sacred Rondache is elite → endgame flagged
  expect(html).toMatch(/endgame<\/b> base/);
});
