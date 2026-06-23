import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v414 — runeword ID card renders (regression: esc undefined broke every runeword card incl. Chronicle click).
test('runeword ID card renders + Chronicle click opens it', async ({ page }) => {
  const errs:string[]=[]; page.on('pageerror',e=>errs.push(String(e)));
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w:any = window;
    let detailLen = 0, detailErr = '';
    try { detailLen = String(w.runewordDetailHtml('Hand of Justice')||'').length; } catch(e:any){ detailErr = String(e).slice(0,100); }
    // simulate the Chronicle row click → openDrop
    try { w.renderRunewordChronicle && w.renderRunewordChronicle(); } catch(e){}
    const row = document.querySelector('.rwc-row') as HTMLElement|null;
    const img = row ? row.querySelector('.d2art-wrap, .rwc-glyph') as HTMLElement|null : null;
    if (img) img.click();
    const panel = document.getElementById('item-detail');
    const hasCard = !!(panel && panel.querySelector('.runeword-card'));
    const hasWarn = !!(panel && /SUPERIOR|NORMAL \(white\)/i.test(panel.innerHTML||''));
    return { detailLen, detailErr, hasCard, hasWarn };
  });
  expect(r.detailErr).toBe('');               // runewordDetailHtml no longer throws
  expect(r.detailLen).toBeGreaterThan(200);   // card HTML generated
  expect(r.hasCard).toBe(true);               // Chronicle click surfaces the card
  expect(r.hasWarn).toBe(true);               // base-requirement warning present
  expect(errs).toEqual([]);
});
