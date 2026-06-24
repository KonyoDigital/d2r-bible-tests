import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v418 — (1) runewords read WITH their base type resolve, (2) ethereal name matches a slot-suffixed grail
// item, (3) a set piece stored with its "(slot)" disambiguator still resolves its art.
test('runeword+base resolves to the runeword', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const f = w._rwResolve;
    return {
      spiritMonarch: f('Spirit Monarch')||'∅',
      cohDusk: f('Chains of Honor Dusk Shroud')||'∅',
      quoted: f("Crystal Sword 'Spirit'")||'∅',
      cleanStill: f('Spirit')||'∅',
      sockSuffix: f('Spirit (4os)')||'∅',
      notRW: f('Spirit Caller')||'∅',         // 'Caller' isn't a base → must NOT false-match
      randomRare: f('Dread Spiral Ring')||'∅',
    };
  });
  expect(r.spiritMonarch).toBe('Spirit');
  expect(r.cohDusk).toBe('Chains of Honor');
  expect(r.quoted).toBe('Spirit');
  expect(r.cleanStill).toBe('Spirit');
  expect(r.sockSuffix).toBe('Spirit');
  expect(r.notRW).toBe('∅');
  expect(r.randomRare).toBe('∅');
});
test('ethereal name normalization bridges a slot suffix', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const en = w._etherNorm;
    return {
      // AI reports the bare tooltip name "Gull"; the grail item carries the slot disambiguator "(dagger)".
      bridged: en('Gull (dagger)') === en('Gull'),
      stillBase: en('Stormshield (4os)') === en('Stormshield'),
      distinct: en('Gull') !== en('Bul-Kathos'),
    };
  });
  expect(r.bridged).toBe(true);
  expect(r.stillBase).toBe(true);
  expect(r.distinct).toBe(true);
});
test('slot-suffixed set piece resolves its base art', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window;
    const html = w.artOr ? w.artOr("Sander's Riprap (heavy boots)", '·', 'sm') : '';
    const m = html.match(/src="([^"]+)"/);
    return { src: m ? m[1] : '(failed/no img)' };
  });
  expect(r.src).toContain('boots');   // NOT a charm/gem sprite
});
