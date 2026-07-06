import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v588 — PREMIUM TRADE BASES (Konyo): market-wanted bases (Archon Plate/Staff, Bone Visage, Monarch,
// the 4os-Flail-for-HotO class…) are worth ≥ an Ist as clean drops — the loot filter must NEVER shrink
// them off, regardless of the Chronicle (all words made) or bases already owned. Ordinary bases keep
// the v535/v536.2 auto-shrink. Superior premium drops are never gamble-only-hidden.

test('a 100%-forged Chronicle still keeps every premium trade base in the filter', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_ladderMode', 'nonladder'); });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload(); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const eb = w._endgameFilterBases();
    const CODE = JSON.parse(document.getElementById('lf-base-codes')!.textContent!.trim());
    const premium: string[] = w._premiumTradeBases || [];
    return {
      premiumCount: premium.length,
      missing: premium.filter((nm: string) => eb.names.indexOf(nm) < 0),
      gambleHidden: premium.filter((nm: string) => eb.gambleOnlyCodes.indexOf(CODE[nm]) >= 0),
      names: eb.names,
    };
  });
  expect(r.premiumCount).toBeGreaterThanOrEqual(15);
  expect(r.missing).toEqual([]);        // every premium base survives a complete Chronicle
  expect(r.gambleHidden).toEqual([]);   // superior premium drops never hidden as gamble-only
  // with EVERYTHING forged nothing else remains: the filter = exactly the premium floor
  expect(r.names.length).toBe(r.premiumCount);
});

test('owning a socket-correct premium base does NOT drop it (v536.2 shrink skips the floor)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Monarch (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Tal: 1, Thul: 1, Ort: 1, Amn: 1 }));
    // NOTE: rwMade deliberately NOT set here — addInitScript re-runs on reload (the v578.1 lesson).
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  // Spirit (Tal+Thul+Ort+Amn, 4os Monarch) is the ONLY unmade word; the owned 4os Monarch covers it,
  // so the v536.2 shrink would have dropped Monarch — the premium floor must keep it.
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (n !== 'Spirit') made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload(); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Monarch (4os)');
    const s = w.forgeScan();
    const spirit = [...(s.now || []), ...(s.pipeline || [])].find((t: any) => t.rw === 'Spirit');
    return { spiritHasBase: !!(spirit && spirit.base), names: w._endgameFilterBases().names };
  });
  expect(r.spiritHasBase).toBe(true);        // the Forge plans Spirit on the owned Monarch…
  expect(r.names).toContain('Monarch');      // …but the premium floor keeps Monarch in the filter anyway
});
