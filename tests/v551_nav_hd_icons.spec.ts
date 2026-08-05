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
    /* v1683 — the WORKSHOP six moved to the console's own chrome icons (art/ui_tab_*.png); the
       LORE/data tabs keep their in-game sprites. So this now checks BOTH families rather than
       three tabs that happened to be handy. */
    const WORKSHOP = ['session', 'tools', 'forge', 'funi', 'fsets', 'tvd'];
    return { runes: pick('runes'),
             workshop: WORKSHOP.map((t) => [t, pick(t)]),
             label: (document.querySelector('.tabs .tab[data-tab="runes"] .tab-lbl')?.textContent || '') };
  });
  expect(r.runes).toMatch(/hd_ber_rune/);   // a LORE tab still wears its in-game sprite
  /* Each workshop tab renders the SAME file the console header strip renders. Before v1683 these
     were a specific unique's portrait — funi was crownofages_graphic.png and fsets was
     talrashasguardianship_graphic.png — so one tab showed a gold ring in the app and the Crown of
     Ages on the website. Chrome does not wear an item's identity (v1677, v1678). */
  for (const [tab, src] of r.workshop as [string, string | null][]) {
    expect(src, `the ${tab} tab renders no icon at all`).not.toBeNull();
    expect(src, `the ${tab} tab is not on the console's chrome art`).toMatch(new RegExp(`ui_tab_${
      { session: 'session', tools: 'tools', forge: 'forge', funi: 'funi', fsets: 'fsets', tvd: 'tvd' }[tab]}\\.png`));
  }
  expect(r.label).toBe('runes');   // label preserved next to the icon
});

test('every mapped tab gets an HD icon; each carries an emoji fallback', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const imgs = [...document.querySelectorAll('.tabs .tab img.tab-hdico')] as HTMLImageElement[];
    /* v1683 — COUNT AGAINST THE MAP, NOT A LITERAL. This read `toBe(15)` and went red the moment
       session + tvd joined TAB_ICON — a number that has to be hand-edited every time the nav grows
       is a tripwire on the wrong thing. What it exists to catch is an icon that silently stopped
       rendering, so it now compares against the tabs the map actually claims. */
    const map = (window as any).TAB_ICON || {};
    const claimed = [...document.querySelectorAll('.tabs .tab')]
      .filter((t) => map[(t as HTMLElement).dataset.tab || '']).length;
    return { count: imgs.length, claimed,
             allHaveEmoji: imgs.every((i) => !!i.getAttribute('data-emoji')),
             allHaveOnerror: imgs.every((i) => !!i.getAttribute('onerror')) };
  });
  expect(r.claimed, 'TAB_ICON claims no tabs at all — the map is gone').toBeGreaterThanOrEqual(15);
  expect(r.count, `${r.claimed} tabs are mapped but only ${r.count} rendered an icon`).toBe(r.claimed);
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
