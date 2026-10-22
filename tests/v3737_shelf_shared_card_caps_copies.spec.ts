import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — the shelf draws every physical copy, on the shared
// locker and on a category mule. A 7-copy Grief is 7 cells on both.
//
// V0 spec refresh (#175 / #176) — HIS 2026-10-22 RULING (verbatim): "so for grief and certain runewords that
// are rare and as hard core as it like last wish too they should be in war gear like 2-3 copies". For Grief
// and the rare endgame runewords like Last Wish it REPLACES the 10-18 "every copy" rule; for everything else
// the 10-18 rule stands. So the spec now holds the two cases apart:
//   1. 10-18, a NON-war item. The Stone of Jordan — shared by high trade value, in no war-gear or merc list —
//      owned x7 draws 7 cells on the shared locker and 7 on its slot mule. On the shared card that is also his
//      2026-10-20 L1 cap: a 1x1 ring keeps every copy (bible.html _vaultWarCap0:
//      `if (area === 1 && /\b(ring|amulet)\b/i.test(base)) return Infinity;`). Measured 7 / 7 on the merged V1 tree.
//   2. 10-22, war gear. Grief x7 and Last Wish x5 keep 2-3 copies in the war-gear stash (the shared card). The
//      exact runeword list and 2-vs-3 are still his to confirm (#175), so the case asserts the ruled RANGE.
//      ⚠ RED ON THE MERGED V1 TREE, AND THAT IS THE FINDING, NOT A SPEC BUG: _shelfCopyCount still applies the
//      10-20 footprint cap. Neither runeword has an established footprint, so each is drawn at the 1x2 guess,
//      reads as "small gear" and keeps _WAR_SMALL_CAP = 4 (measured: 4 and 4). His ruling is not implemented
//      yet; this case stays red until it is.

async function seed(page: any, owned: string[], copies: Record<string, number>) {
  await page.addInitScript(({ owned, copies }: { owned: string[]; copies: Record<string, number> }) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
    } catch (e) {}
  }, { owned, copies });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any)._shelfDrawNames === 'function'
    && typeof (window as any).vaultWarGearRole === 'function');
}

test('the shelf draws every copy on the shared locker and on a mule (Elad 2026-10-18)', async ({ page }) => {
  const NAME = 'The Stone of Jordan';
  await seed(page, [NAME], { [NAME]: 7 });
  const r = await page.evaluate((nm: string) => {
    const w = window as any;
    return {
      seededCopies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm],
      route: (w.suggestMule(nm) || {}).id,
      war: w.vaultWarGearRole(nm),
      sharedCells: w._shelfDrawNames([nm], 'shared').length,
      muleCells: w._shelfDrawNames([nm], 'uni-small').length,
    };
  }, NAME);
  expect(r.seededCopies).toBe(7);
  expect(r.route, 'PREMISE: the rules keep this non-war item in the shared stash').toBe('shared');
  expect(r.war, 'PREMISE: it is in no war-gear list, so the 10-18 rule still governs it').toBeNull();
  expect(r.sharedCells).toBe(7);
  expect(r.muleCells).toBe(7);
});

test('war gear keeps 2-3 copies in the war stash (his 2026-10-22 ruling: Grief, Last Wish)', async ({ page }) => {
  const COPIES: Record<string, number> = { 'Grief': 7, 'Last Wish': 5 };
  await seed(page, Object.keys(COPIES), COPIES);
  const r = await page.evaluate((names: string[]) => {
    const w = window as any;
    const out: Record<string, any> = {};
    names.forEach((nm) => {
      out[nm] = {
        copies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm],
        war: w.vaultWarGearRole(nm),
        route: (w.suggestMule(nm) || {}).id,
        warStashCells: w._shelfDrawNames([nm], 'shared').length,
      };
    });
    return out;
  }, Object.keys(COPIES));
  for (const nm of Object.keys(COPIES)) {
    expect(r[nm].copies, `${nm}: the seeded copy count`).toBe(COPIES[nm]);
    expect(r[nm].war, `PREMISE: ${nm} is war gear`).toBeTruthy();
    expect(r[nm].route, `PREMISE: ${nm} lives in the war (shared) stash`).toBe('shared');
    // soft, so one run names every runeword that is off the ruling (measured today: Grief 4, Last Wish 4)
    expect.soft(r[nm].warStashCells, `${nm}: his 10-22 ruling keeps 2-3 copies in war gear`).toBeGreaterThanOrEqual(2);
    expect.soft(r[nm].warStashCells, `${nm}: his 10-22 ruling keeps 2-3 copies in war gear, not every copy and not the 10-20 cap of 4`).toBeLessThanOrEqual(3);
  }
});
