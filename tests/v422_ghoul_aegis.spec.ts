import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v422 — Ghoul Aegis (RotW unique Codex) enriched: golden card + uni-armor routing + AI vocab + verified stats.
test('Ghoul Aegis is a routable, carded, vocab off-grail unique', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    const e = w.EXTRA_ITEMS && w.EXTRA_ITEMS['Ghoul Aegis'];
    const vocab = (w.ITEMS||[]).map((i:any)=>i.n).concat(Object.keys(w.EXTRA_ITEMS||{}));
    return {
      exists: !!e,
      rarity: e && e.rarity,
      base: e && e.base,
      mule: w.suggestMule ? (w.suggestMule('Ghoul Aegis')||{}).id : null,
      carded: w._arttipResolve ? !!(w._arttipResolve('Ghoul Aegis')||{}).rich : null,
      inVocab: vocab.includes('Ghoul Aegis'),
      hasSigil: !!(e && (e.stats||[]).some((s:string)=>/Sigil: Rancor/.test(s))),
    };
  });
  expect(r.exists).toBe(true);
  expect(r.rarity).toBe('unique');
  expect(r.base).toBe('Codex');
  expect(r.mule).toBe('uni-armor');
  expect(r.carded).toBe(true);
  expect(r.inVocab).toBe(true);
  expect(r.hasSigil).toBe(true);
});
