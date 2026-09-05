import { test, expect } from '@playwright/test';
import path from 'path';

/* v2692 — THE HARDCODED SEEDS BELONG TO A NAMED LEDGER, AND THIS GUARDS BOTH DIRECTIONS.
 *
 * Konyo, from his cousin Dean's board: "the uniques for his uniques tab is rendering 243/403 which
 * is wrong its my old seeded chronicle that he harnessed as a default... he doent have a way to
 * reset his uniques from 243/403 to 0/403 so he can finally sync his chronicle via MINI focused/ON
 * AIR." Then: "it should be registerd accordingly to ledger/profile and ledger name."
 *
 * THE DEFECT WAS ONE BROKEN PREDICATE BEHIND FOUR DOORS. Every seed asked `_isCousinShell`, which is
 * only `!_D2R_OWNER` — so pressing "claim this browser" flipped it false and the board began
 * inheriting Konyo's data. Measured then, on a claimed browser after ONE find: foundLog 13 keys
 * (his 1 + 12 from the v1692/v1693 ruling migrations), d2r_rwMade 99, d2r_rwVerify 2, Uniques
 * 243/403.
 *
 * ⚠⚠ THIS FILE ASSERTS BOTH DIRECTIONS ON PURPOSE, because each alone is satisfiable by a fix that
 * ruins the other. "A stranger inherits nothing" is satisfiable by never seeding anyone — which
 * would silently subtract Konyo's own 356 finds, the exact damage v2680 did and v2685 reverted.
 * "His board keeps its floor" is satisfiable by seeding everyone, which is the bug. Only the PAIR
 * is the law. [[d2r-ladder-doctrine]] (a display rule must never change a count)
 */
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function readWorld(page: any) {
  return page.evaluate(() => {
    const n = (k: string) => {
      try {
        const v = JSON.parse(localStorage.getItem(k) || 'null');
        if (v === null) return -1;
        return Array.isArray(v) ? v.length : (typeof v === 'object' ? Object.keys(v).length : -2);
      } catch (e) { return -3; }
    };
    const w: any = window;
    const scan = w.funiScan();
    return {
      ledger: String(w._D2R_LEDGER ?? ''),
      seedsBelongHere: !!w._seedsBelongHere,
      found: scan.found,
      total: scan.found + (scan.missing || []).length,
      foundLog: n('d2r_foundLog'),
      rwMade: n('d2r_rwMade'),
      rwVerify: n('d2r_rwVerify'),
      ledgerName: String(localStorage.getItem('d2r_ledgerName') || ''),
    };
  });
}

test('a stranger who CLAIMS the browser inherits nothing — not the chronicle, not the runewords', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(2500);
  await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  await page.reload();
  await page.waitForTimeout(2500);

  /* Claim it the way a person does — the button, not a hand-written key. */
  const claimed = await page.evaluate(() => {
    const b: any = document.getElementById('claim-btn');
    if (!b) return false;
    b.onclick();
    return true;
  });
  expect(claimed, 'no claim button — this test could not exercise the path it is about').toBe(true);

  /* A claim must NAME the ledger immediately. Without this the unnamed-store heuristic re-adopts
     the seed ledger at the owner's very first find, re-creating the defect one find later. */
  const named = await page.evaluate(() => String(localStorage.getItem('d2r_ledgerName') || ''));
  expect(named, 'a claim left the ledger unnamed — it will adopt the seed ledger at the first find')
    .not.toBe('');

  /* Now he finds ONE item, which is what used to trigger the ruling migrations. */
  await page.evaluate(() => {
    try { localStorage.setItem('d2r_foundLog', JSON.stringify({ Shaftstop: 'Jun 1, 2026 · 00:00' })); } catch (e) {}
  });
  await page.reload();
  await page.waitForTimeout(2800);

  const w = await readWorld(page);
  expect(w.total, 'the chronicle universe did not build — this test measured NOTHING').toBeGreaterThan(300);
  expect(w.seedsBelongHere, 'a stranger board is being treated as the seed ledger').toBe(false);
  expect(w.foundLog,
    'his cousin found ONE item and the board added more — the v1692/v1693 ruling migrations are '
    + 'seeding another man\'s finds').toBe(1);
  expect(w.found, 'the Uniques tab is counting finds that are not his').toBe(1);
  expect(w.rwMade, 'the runeword seed landed on a stranger board').toBe(0);
  expect(w.rwVerify, 'the verify verdicts landed on a stranger board').toBe(0);
});

test("HIS OWN board still gets its floor — the half a naive fix breaks", async ({ page }) => {
  /* An install predating the ledger name is UNNAMED and already carries a chronicle. That is the
     board these seeds were written for, and it must keep them. A fix that zeroes everyone would
     pass the test above and silently delete his chronicle. */
  await page.goto(URL);
  await page.waitForTimeout(2500);
  await page.evaluate(() => {
    try {
      localStorage.clear();
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_foundLog', JSON.stringify({
        Shaftstop: 'Jun 1, 2026 · 00:00', 'Gore Rider': 'Jun 1, 2026 · 00:00',
      }));
    } catch (e) {}
  });
  await page.reload();
  await page.waitForTimeout(2800);

  const w = await readWorld(page);
  expect(w.total, 'the chronicle universe did not build — this test measured NOTHING').toBeGreaterThan(300);
  expect(w.ledgerName, 'this scenario is only meaningful while the store is UNNAMED').toBe('');
  expect(w.ledger,
    'an unnamed board that already carries a chronicle must resolve to the seed ledger — otherwise '
    + 'every install predating v2692 silently loses its finds').toBe('KonyoEndgame');
  expect(w.seedsBelongHere, 'his own board stopped being the seed ledger').toBe(true);
  expect(w.foundLog,
    'the chronicle floor did not restore his finds — a roster change must never subtract from what '
    + 'he has found').toBeGreaterThan(200);
  expect(w.rwMade, 'his made runewords were not restored').toBeGreaterThan(50);
});
