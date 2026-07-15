import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v588 → v667.2 → v690.1 DOCTRINE HISTORY (this spec tracks the CURRENT one):
//   v588: premium trade bases never shrink off the filter (unconditional floor).
//   v667.2 (Konyo: 'not every single item though'): the floor rides in FULL only below 50% forged;
//          from 50% premium obeys the same engine gates as every base.
//   v690.1 (Konyo: 'once im through the runeword chronicle …it hardens… no base.. its pointless'):
//          a COMPLETE Chronicle shows NO bases at all — word-driven shows shrink to zero, premium
//          included. The list itself lives on for the early stage + SI intel.

test('a 100%-forged Chronicle HARDENS the filter: no bases at all, premium included (v690.1)', async ({ page }) => {
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
    return { premiumCount: (w._premiumTradeBases || []).length, names: eb.names, sock: eb.sockCodes, plain: eb.plainCodes };
  });
  expect(r.premiumCount).toBeGreaterThanOrEqual(15);   // the curated list itself lives on (early stage + SI)
  expect(r.names).toEqual([]);                          // …but a sealed Chronicle shows NOTHING
  expect(r.sock).toEqual([]);
  expect(r.plain).toEqual([]);
});

test('early stage (<50%): the premium floor rides in full (v667.2)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_ladderMode', 'nonladder');
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const eb = w._endgameFilterBases();
    const premium: string[] = w._premiumTradeBases || [];
    return { missing: premium.filter((nm: string) => eb.names.indexOf(nm) < 0) };
  });
  expect(r.missing).toEqual([]);   // fresh chronicle = every premium base lights up as trade capital
});

test('late stage: owned socket-correct premium leaves the CURATED list but its socketed drops stay engine-true', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Monarch (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Tal: 1, Thul: 1, Ort: 1, Amn: 1 }));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  // Spirit is the ONLY unmade word (98/99 = late stage): the owned 4os Monarch covers it, so the
  // v536.2 shrink correctly drops Monarch from the curated farm list (v667.2 ended the late floor) —
  // but the v662.1 engine-true socketed universe still shows socketed shield drops while Spirit lives.
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
    const CODE = JSON.parse(document.getElementById('lf-base-codes')!.textContent!.trim());
    const spirit = [...(s.now || []), ...(s.pipeline || [])].find((t: any) => t.rw === 'Spirit');
    const eb = w._endgameFilterBases();
    return { spiritHasBase: !!(spirit && spirit.base), names: eb.names, sockHasMonarch: eb.sockCodes.indexOf(CODE['Monarch']) >= 0 };
  });
  expect(r.spiritHasBase).toBe(true);            // the Forge plans Spirit on the owned Monarch
  expect(r.names).not.toContain('Monarch');      // curated farm intel correctly drops it (owned + late stage)
  expect(r.sockHasMonarch).toBe(true);           // a socketed Monarch on the ground still shows (engine-true honesty)
});
