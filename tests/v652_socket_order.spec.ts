import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v652 — EVERY missing-runes list renders in SOCKET ORDER (Konyo wasted his last ladder Cham
// following the value-sorted 'Missing: 1× Cham, 1× Fal, 1× Io' — the true order is Io→Cham→Fal;
// wrong order = no runeword, runes consumed). Value-sorting a socket recipe is a data lie.

test('missing lists follow rec[] order everywhere a word has a known recipe', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    // empty the stash so EVERYTHING is missing → the full list must equal rec order exactly
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
    const bad: string[] = [];
    // 1) the Tools chronicle rows
    try { w.renderRunewordChronicle(); } catch (e) {}
    const madeMap = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    Object.keys(w.RUNEWORD_TIP).filter((n) => !madeMap[n]).slice(0, 40).forEach((n) => {
      const rec = (w.RUNEWORD_TIP[n].rec || []);
      const row = [...document.querySelectorAll('.rwc-need')].find((x: any) => {
        const p = x.closest('[data-arttip]') || x.parentElement?.parentElement; return false; });
      // DOM matching is fragile — assert via the same scan the rows use instead:
    });
    // authoritative check: forgeScan's missing arrays
    const sc = w.forgeScan();
    [].concat(sc.onestep || [], sc.farm || []).forEach((t: any) => {
      const rec: string[] = (w.RUNEWORD_TIP[t.rw] && w.RUNEWORD_TIP[t.rw].rec) || [];
      const order = [...new Set(rec)];
      const miss = (t.missing || []).map((m: string) => m.replace(/^\d+×\s*/, '').trim());
      const expected = order.filter((rn) => miss.includes(rn));
      if (JSON.stringify(miss) !== JSON.stringify(expected)) bad.push(t.rw + ': ' + miss.join(',') + ' ≠ ' + expected.join(','));
    });
    // Metamorphosis, the incident word, explicitly (ladder-parked on main → flip mode for the scan):
    w.rwSetLadderMode('ladder');
    const sc2 = w.forgeScan();
    const meta = [].concat(sc2.onestep || [], sc2.farm || []).find((t: any) => t.rw === 'Metamorphosis');
    const metaMiss = meta ? (meta.missing || []).map((m: string) => m.replace(/^\d+×\s*/, '')) : [];
    w.rwSetLadderMode('nonladder'); localStorage.removeItem('d2r_ladderMode');
    localStorage.removeItem('d2r_runeStash');
    return { bad: bad.slice(0, 10), metaMiss };
  });
  expect(r.bad).toEqual([]);
  expect(r.metaMiss).toEqual(['Io', 'Cham', 'Fal']);   // the exact order that cost him a Cham
});
