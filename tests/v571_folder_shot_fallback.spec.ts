import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v571 — "no shot needs to be PHOTOS of the item screenshot like the file itself, rendering HD 1920×1080"
// (Konyo). When a review card's journal thumb was pruned (v359/v365 history) the card now keeps the FILENAME
// and hydrates the ORIGINAL screenshot straight from the linked folder (object URL, native resolution):
//   shotOf keeps ff without th → placeholder with data-ffsrc → _vHydrateShots swaps in the real file →
//   _shotLightbox falls back IndexedDB → folder file → thumb.

const PNG_1PX = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

test('a thumbless journal read renders a folder placeholder, and _vHydrateShots swaps in the real file', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(async (png: string) => {
    const w: any = window;
    // seed: one throw-out read whose session has the FILENAME but its thumb was pruned
    localStorage.setItem('d2r_unknownReads', JSON.stringify(['Devil Star (3os low base)']));
    localStorage.setItem('d2r_intakeLog', JSON.stringify([{
      ts: 1783200000000, u: 'Konyo',
      items: [], pf: [{ f: '21.57.20', ff: 'Screenshot 2026-07-04 at 21.57.20.png', nw: [], mf: [], own: [],
                        unr: ['Devil Star (3os low base)'], e: false }],   // NO th — pruned
    }]));
    location.reload();
    return 'seeded ' + png.length;
  }, PNG_1PX);
  await page.waitForTimeout(1800);
  const out = await page.evaluate(async (png: string) => {
    const w: any = window;
    // stub the folder source BEFORE rendering — the renderer hydrates immediately (headless has no real folder)
    w._vShotFromFolder = async () => png;
    w.switchTab('tools'); w.renderVault && w.renderVault();
    await new Promise((res) => setTimeout(res, 400));
    const el = document.getElementById('vault-throwout')!;
    const placeholderOrImg = !!el.querySelector('.to-noshot[data-ffsrc], img.to-shot[data-shot*="21.57.20"]');
    const img = el.querySelector('img.to-shot[data-shot*="21.57.20"]') as HTMLImageElement | null;
    return {
      fns: { fromFolder: typeof w._vShotFromFolder, hydrate: typeof w._vHydrateShots },
      placeholderOrImg,
      hydrated: !!img && img.src === png,
      clickable: !!img && typeof img.onclick === 'function',
    };
  }, PNG_1PX);
  expect(out.fns.hydrate).toBe('function');
  expect(out.placeholderOrImg).toBe(true);   // the card knows its file even without a thumb
  expect(out.hydrated).toBe(true);           // the original file rendered into the card
  expect(out.clickable).toBe(true);          // click → full-size lightbox
});

test('the lightbox falls back IndexedDB → linked-folder file → thumb', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(async (png: string) => {
    const w: any = window;
    w._vGetShot = async () => null;                 // nothing stored
    w._vShotFromFolder = async () => png;           // but the file exists in the folder
    w._shotLightbox('Screenshot X.png', 'data:image/gif;base64,thumb');
    await new Promise((res) => setTimeout(res, 200));
    const im = document.querySelector('#_shotlb img') as HTMLImageElement | null;
    const src = im ? im.src : 'none';
    const lb = document.getElementById('_shotlb'); if (lb) lb.remove();
    return src;
  }, PNG_1PX);
  expect(r).toBe(PNG_1PX);                    // folder file wins over the tiny thumb
});
