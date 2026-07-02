import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v551 — HD-art nav icons: shiny in-game sprites replace the flat emoji on BOTH the main tabs and the compass
// navigator. Centralised TAB_ICON map, per-icon emoji fallback if the art 404s (nav never breaks).

test('main tabs render HD-art icons for mapped tabs (runes → Ber rune, tools → cube, forge → hammer)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const pick = (tab: string) => {
      const el = document.querySelector(`.tabs .tab[data-tab="${tab}"] img.tab-hdico`) as HTMLImageElement | null;
      return el ? el.getAttribute('src') : null;
    };
    return { runes: pick('runes'), tools: pick('tools'), forge: pick('forge'), label: (document.querySelector('.tabs .tab[data-tab="runes"] .tab-lbl')?.textContent || '') };
  });
  expect(r.runes).toMatch(/hd_ber_rune/);
  expect(r.tools).toMatch(/horadric_cube/);
  expect(r.forge).toMatch(/warhammer/);
  expect(r.label).toBe('runes');   // label preserved next to the icon
});

test('every mapped tab gets an HD icon; each carries an emoji fallback', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const imgs = [...document.querySelectorAll('.tabs .tab img.tab-hdico')] as HTMLImageElement[];
    return { count: imgs.length, allHaveEmoji: imgs.every((i) => !!i.getAttribute('data-emoji')), allHaveOnerror: imgs.every((i) => !!i.getAttribute('onerror')) };
  });
  expect(r.count).toBe(13);            // all 13 nav tabs mapped
  expect(r.allHaveEmoji).toBe(true);
  expect(r.allHaveOnerror).toBe(true);
});

test('the compass navigator chips use the same HD icons', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    if (typeof w.buildNavWidget === 'function') w.buildNavWidget();
    const chipImgs = [...document.querySelectorAll('#nav-widget .nav-chip img.nav-ic')] as HTMLImageElement[];
    const runeChip = document.querySelector('#nav-widget .nav-chip[data-nav="runes"] img.nav-ic') as HTMLImageElement | null;
    return { chipCount: chipImgs.length, runeSrc: runeChip ? runeChip.getAttribute('src') : null };
  });
  expect(r.chipCount).toBeGreaterThanOrEqual(13);
  expect(r.runeSrc).toMatch(/hd_ber_rune/);
});

test('the tab click handler still works after the icon rewrite (switchTab fires)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    (document.querySelector('.tabs .tab[data-tab="tools"]') as HTMLElement)?.click();
    const tools = document.getElementById('tab-tools');
    return tools ? getComputedStyle(tools).display !== 'none' : false;
  });
  expect(r).toBe(true);
});
