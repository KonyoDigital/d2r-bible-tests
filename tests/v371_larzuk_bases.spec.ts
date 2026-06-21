import { test, expect } from '@playwright/test';

// v371 — 0-socket base calibration ("track elite, ignore junk"). A hovered elite/magic/eth base with
// ZERO sockets is a LARZUK CANDIDATE: backend (intake.js) emits "Larzuk <slot> Base", which the front-end
// registers to the SOCKETED locker with base-type art + a rich card. Junk 0-socket whites stay ignored.

const URL = 'file://' + process.cwd() + '/bible.html';
const LARZUK = ['Larzuk Helm Base', 'Larzuk Body Armor Base', 'Larzuk Shield Base', 'Larzuk 1H Weapon Base', 'Larzuk 2H Weapon Base'];

test('Larzuk-candidate bases: in EXTRA_ITEMS + vocab, base art, route to SOCKETED, rich card', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1300);
  const r = await page.evaluate((names) => {
    const w = window as any;
    const vocab = Object.keys(w.EXTRA_ITEMS || {});
    return names.map((n: string) => ({
      n,
      inExtra: !!(w.EXTRA_ITEMS && w.EXTRA_ITEMS[n]),
      hasArt: !!(w.artUrl && w.artUrl(n)),
      mule: w.suggestMule ? (w.suggestMule(n) || {}).id : '?',
      rich: w._arttipResolve ? w._arttipResolve(n).rich : false,
      inVocab: vocab.includes(n),
    }));
  }, LARZUK);
  expect(errs).toEqual([]);
  for (const e of r) {
    expect(e.inExtra).toBe(true);     // registered concept
    expect(e.hasArt).toBe(true);      // base-type sprite (no bare glyph)
    expect(e.mule).toBe('bases');     // → SOCKETED locker
    expect(e.rich).toBe(true);        // rich hover card
    expect(e.inVocab).toBe(true);     // backend can emit it & client matches it
  }
});
