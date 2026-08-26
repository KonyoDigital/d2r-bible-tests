import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v596 — FORGE→VAULT CONSUME SYNC (Konyo: "after i click created on forge it needs to automatically
// get taken out of the vault.. not showing again and again the same socketed base"). Marking a word
// ✓ created consumes the owned base the Forge planned it on (the base BECAME the runeword); un-marking
// gives it back (d2r_rwBaseUsed remembers). Pinned scenario: Insight the only unmade word, one owned
// 4os Colossus Voulge with the Insight runes ready — the exact make-now card he ticks.

test('✓ created consumes the planned base from the vault; un-mark restores it', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    // NOTE: rwMade deliberately NOT set here — addInitScript re-runs on reload and would stomp the
    // pinned Chronicle written below (the v578.1 lesson).
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  /* v2134 — WAIT FOR THE BOARD, NOT FOR A DURATION. This spec used two flat 1500ms waits and a
     500ms one. Routine I runs SIX shards in parallel on one runner, so a fixed wait that is ample
     on a quiet machine is a coin-flip on a loaded one — and #162 is exactly that: `preTaskHasBase`
     false twice on CI while the same fixture passes 5/5 locally at these very timings.

     ⚠ WAITING ON THE ASSERTION WOULD MAKE IT VACUOUS. What is waited for here is the PRECONDITION —
     the board's own API being present, and the socket-base entry `_ensureSocketBaseEntry` writes.
     Whether forgeScan then PLANS Insight on that base is the claim, and it is still asserted cold.
     [[feedback-blind-fixture-green-gate]] */
  await page.goto(URL);
  await page.waitForFunction(() => {
    const w = window as any;
    return typeof w.forgeScan === 'function'
        && typeof w.rwToggleMade === 'function'
        && typeof w._ensureSocketBaseEntry === 'function'
        && w.RUNEWORD_TIP && Object.keys(w.RUNEWORD_TIP).length > 50;
  }, null, { timeout: 20000 });
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (n !== 'Insight') made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload();
  await page.waitForFunction(() => {
    const w = window as any;
    return typeof w.forgeScan === 'function' && typeof w._ensureSocketBaseEntry === 'function'
        && w.RUNEWORD_TIP && Object.keys(w.RUNEWORD_TIP).length > 50;
  }, null, { timeout: 20000 });
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const r = await page.evaluate(async () => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    /* the registration is the PRECONDITION: _ownedBases() only yields labels that are in the
       in-memory owned set AND carry cat:'Socketed bases' in EXTRA_ITEMS. Wait for that fact rather
       than for 500ms — but NOT for the plan itself, which is what this spec is here to test. */
    for (let i = 0; i < 100; i++) {
      const e = w.EXTRA_ITEMS && w.EXTRA_ITEMS['Colossus Voulge (4os)'];
      if (e && e.cat === 'Socketed bases') break;
      await new Promise((res) => setTimeout(res, 50));
    }
    const ownedList = () => JSON.parse(localStorage.getItem('d2r_owned') || '[]');
    const preTask = [...w.forgeScan().now].find((t: any) => t.rw === 'Insight');
    const ownedBefore = ownedList().includes('Colossus Voulge (4os)');
    w.rwToggleMade('Insight');                                       // ✓ created (the Forge button path)
    const ownedAfter = ownedList().includes('Colossus Voulge (4os)');
    const used = JSON.parse(localStorage.getItem('d2r_rwBaseUsed') || '{}');
    const madeNow = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
    w.rwToggleMade('Insight');                                       // ↺ un-mark → base comes back
    const ownedRestored = ownedList().includes('Colossus Voulge (4os)');
    const usedAfter = JSON.parse(localStorage.getItem('d2r_rwBaseUsed') || '{}');
    return { preTaskHasBase: !!(preTask && preTask.base), ownedBefore, ownedAfter, madeNow,
             usedEntry: used['Insight'] || null, ownedRestored, usedCleared: !usedAfter['Insight'] };
  });
  expect(r.preTaskHasBase).toBe(true);         // the Forge genuinely planned Insight on the owned Voulge
  expect(r.ownedBefore).toBe(true);
  expect(r.madeNow).toBe(true);                // the word got marked created
  expect(r.ownedAfter).toBe(false);            // …and the base LEFT the vault automatically
  expect(r.usedEntry).toEqual({ l: 'Colossus Voulge (4os)', copy: false });
  expect(r.ownedRestored).toBe(true);          // un-mark gives the base back
  expect(r.usedCleared).toBe(true);
});
