import { test, expect } from '@playwright/test';

// REG-2257 (#76 phase 1, slice 1) — THE ONE-RECORD MODEL FAITHFULLY REPRODUCES THE VAULT HEADER.
// window._vaultRecords builds one record per physical copy from the already-forked name-homed stores
// (owned/copies/assign — so it inherits Ladder/Main fork for free; derived in-memory, no new store, no
// data write). window._vaultRecordsHeader counts records per location-kind. The LIVE header (#vault-pop)
// derives "filed to mules" by SUBTRACTION (pool - loose - carried). On consistent data the two
// INDEPENDENT paths must agree EXACTLY — that parity is the foundation phase 2 flips the source onto.
// Also pins the keepInv fix: a KEEP_IN_INVENTORY charm (Anni/Torch/Gheed's) with no resolvable mule is
// drawn with MAIN, so it is 'keepInv', NEVER an 'orphan' (the-unjoined-end: never mislabel a kept item).
//
// Verified via CDP first (bible.html is 76k lines; Playwright does NOT run on his Mac — test-venue):
//   consistent -> rh {owned:5, copies:6, filed:4, loose:1, orphans:0}; #vault-pop reads
//     "5 owned · 4 filed to mules · 1 still loose"  (records == render, byte-for-byte).
//   Annihilus -> dead mule -> byKind.keepInv:1, orphans:[]  (the fix; pre-fix it read 'orphan').
// RED-FIRST (observed on bible.html via the CDP smoke): without the keepInv branch Annihilus reads
//   'orphan' and test 2 fails; drop the 'loose' branch and records.loose != #vault-pop loose, failing
//   test 1's parity. A guard seen red for its own reason. [[regression-guard]]

const SOJ   = 'The Stone of Jordan';   // grail unique — seeded with 2 copies
const RAVEN = 'Raven Frost';           // grail unique
const RW    = 'Enigma';                // runeword (findRuneword)
const SET   = "Natalya's Totem";       // set piece (findSetPiece)
const LOOSE = 'Nagelring';             // grail unique, left unassigned -> loose
const ANNI  = 'Annihilus';             // KEEP_IN_INVENTORY charm

async function seedLoad(page: any, owned: string[], copies: any, assign: any) {
  await page.addInitScript(({ owned, copies, assign }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
    } catch (e) {}
  }, { owned, copies, assign });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    typeof (window as any)._vaultRecordsHeader === 'function'
    && typeof (window as any).ownedPool === 'function');
}

test('records header byte-matches the live vault header on consistent data (REG-2257, #76)', async ({ page }) => {
  await seedLoad(page,
    [SOJ, RAVEN, RW, SET, LOOSE],
    { [SOJ]: 2 },
    { [SOJ]: 'uni-small', [RAVEN]: 'uni-small', [RW]: 'runewords', [SET]: 'sets-rest' });

  const r = await page.evaluate(() => {
    try { if ((window as any).renderVault) (window as any).renderVault(); } catch (e) {}
    const rh = (window as any)._vaultRecordsHeader();
    const pop = document.getElementById('vault-pop');
    const txt = pop ? (pop.textContent || '').replace(/\s+/g, ' ') : '';
    const num = (re: RegExp) => { const m = txt.match(re); return m ? +m[1] : -1; };
    return { rh, popOwned: num(/(\d+) owned/), popFiled: num(/(\d+) filed to mules/), popLoose: num(/(\d+) still loose/), txt };
  });

  // the records model reproduces the header (CDP-verified fixture)
  expect(r.rh.orphans).toBe(0);
  expect(r.rh.owned).toBe(5);
  expect(r.rh.copies).toBe(6);        // SoJ counted twice — copies = total records
  expect(r.rh.filed).toBe(4);
  expect(r.rh.loose).toBe(1);
  // THE PARITY: records-COUNT (independent path) == render-SUBTRACTION (what he actually sees on screen)
  expect(r.rh.owned, r.txt).toBe(r.popOwned);
  expect(r.rh.filed, r.txt).toBe(r.popFiled);
  expect(r.rh.loose, r.txt).toBe(r.popLoose);
});

test('a kept charm with no resolvable mule is keepInv, never an orphan (REG-2257, #76)', async ({ page }) => {
  // Annihilus homed to a mule that does not resolve -> the page prunes the dead assign -> Annihilus is
  // unassigned. It is KEEP_IN_INVENTORY (drawn with MAIN), so records must call it 'keepInv', not 'orphan'.
  await seedLoad(page,
    [SOJ, ANNI, RW, SET, LOOSE],
    {},
    { [SOJ]: 'uni-small', [ANNI]: 'dead-mule-zzz', [RW]: 'runewords', [SET]: 'sets-rest' });

  const r = await page.evaluate(() => {
    try { if ((window as any).renderVault) (window as any).renderVault(); } catch (e) {}
    const rec = (window as any)._vaultRecords();
    const rh = (window as any)._vaultRecordsHeader();
    return { orphans: rec.orphans.map((o: any) => o.name), keepInv: (rec.byKind.keepInv || 0), rhOrphans: rh.orphans };
  });

  expect(r.orphans).not.toContain(ANNI);          // the false positive is fixed
  expect(r.rhOrphans).toBe(0);
  expect(r.keepInv).toBeGreaterThanOrEqual(1);
});
