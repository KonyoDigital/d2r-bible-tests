// v462 — manual socket-count FIX on the Socketed Review: the AI sometimes misreads a faint "Socketed (N)" as a
// 0-socket Larzuk base (Konyo's Superior Champion Axe). vaultFixSockets RENAMES the registered entry in place to
// the correct count, preserving the Superior prefix / eth flag / mule, with no leftover duplicate.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v462 fix socket count', () => {
  test.beforeEach(async ({ page }) => {
    // v681 — Chronicle sealed 99/99 (owner seed) makes every socketed base route to __throwout (no unmade
    // word left to host). Pin a fresh profile so unmade words exist and the corrected label derives a real
    // 'bases' home — the mechanism this file actually exercises (rename + assignment carry/derive).
    await page.addInitScript(() => { localStorage.setItem('d2r_rwProfile', 'fresh'); });
    await page.goto(URL);
    await page.waitForFunction(() => (window as any).vaultFixSockets && (window as any)._ensureSocketBaseEntry);
    await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
    await page.waitForTimeout(1200);
  });

  test('a misread Larzuk base is renamed to the real socket count (no duplicate)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Superior Champion Axe (Larzuk base)');
      eval('owned').add('Superior Champion Axe (Larzuk base)');
      w.renderVault();
      w.vaultFixSockets('Superior Champion Axe (Larzuk base)', 5);
      const ownedArr = Array.from(eval('owned')) as string[];
      return {
        hasNew: ownedArr.includes('Superior Champion Axe (5os)'),
        hasOld: ownedArr.includes('Superior Champion Axe (Larzuk base)'),
        sockets: (w.EXTRA_ITEMS['Superior Champion Axe (5os)'] || {}).sockets,
      };
    });
    expect(r.hasNew).toBe(true);
    expect(r.hasOld).toBe(false);   // no leftover duplicate
    expect(r.sockets).toBe(5);
  });

  test('the eth flag carries over to the corrected label', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Thresher (Larzuk base)');
      eval('owned').add('Thresher (Larzuk base)');
      w.etherealItems.add('Thresher (Larzuk base)');
      w.vaultFixSockets('Thresher (Larzuk base)', 4);
      return { ethNew: w._isEthereal('Thresher (4os)'), ethOldStill: w.etherealItems.has('Thresher (Larzuk base)') };
    });
    expect(r.ethNew).toBe(true);
    expect(r.ethOldStill).toBe(false);
  });

  test('the corrected label keeps the mule and the witness it had, and mints none (#246)', async ({ page }) => {
    /* #246 review — A SOCKET COUNT FIX IS NOT A SIGHTING. Before #246 an unfiled label was DERIVED onto a mule by
       the router alone; #246's first cut kept that by minting {by:'hand', where:'the socket count fix'} for it —
       a hand that never happened, which the tile, the doctor and the render prune then all believed. The rename
       carries the filing it had: his hand's row travels with the new label, and a label that was never filed
       stays unfiled (in the dock) with no witness row. */
    const r = await page.evaluate(() => {
      const w = window as any;
      const g = (k: string) => { try { return JSON.parse(w.LSR.getItem(k) || 'null'); } catch (e) { return null; } };
      w._ensureSocketBaseEntry('Champion Axe (Larzuk base)');
      eval('owned').add('Champion Axe (Larzuk base)');
      w.vaultAssign('Champion Axe (Larzuk base)', 'bases');         // his hand files it
      w.vaultFixSockets('Champion Axe (Larzuk base)', 5);
      w._ensureSocketBaseEntry('Thresher (Larzuk base)');
      eval('owned').add('Thresher (Larzuk base)');                    // registered, never filed, no witness
      w.vaultFixSockets('Thresher (Larzuk base)', 4);
      // assign isn't eval-exposed; read it through the board's own store accessor (saveA writes d2r_muleAssign)
      const assign = g('d2r_muleAssign') || {};
      const prov = g('d2r_vaultProv') || {};
      return { mule: assign['Champion Axe (5os)'], oldGone: assign['Champion Axe (Larzuk base)'] === undefined,
               src: (prov['Champion Axe (5os)'] || {}).source, where: (prov['Champion Axe (5os)'] || {}).where,
               unfiled: assign['Thresher (4os)'] === undefined, noRow: !prov['Thresher (4os)'] };
    });
    expect(r.mule).toBe('bases');   // the locker he chose is carried to the corrected label
    expect(r.oldGone).toBe(true);   // stale assignment cleared
    expect(r.src, 'the renamed label lost the witness row it had').toBe('hand');
    expect(r.where).toBe('the vault manager');
    expect(r.unfiled, 'a socket-count fix filed a label that never had a witness').toBe(true);
    expect(r.noRow, 'a socket-count fix minted a witness row').toBe(true);
  });

  test('the fix buttons + base tier render on the Socketed Review card', async ({ page }) => {
    const html = await page.evaluate(() => {
      const w = window as any;
      w._ensureSocketBaseEntry('Champion Axe (Larzuk base)');   // Champion Axe = Exceptional tier
      eval('owned').add('Champion Axe (Larzuk base)');
      w.renderVault();
      return (document.getElementById('vault-socketed') || {}).innerHTML || '';
    });
    expect(html).toContain('wrong count? set the real sockets');
    expect(html).toContain('vaultFixSockets');
    expect(html).toMatch(/Exceptional|Elite|Normal/);   // v463 — base tier shown on the card
  });
});
