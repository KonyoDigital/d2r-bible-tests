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
//      yet; this case stays red until it is. Its red means only that: the premises it shares (war gear, routed
//      shared) are asserted again in case 3, which runs green, so a broken premise shows there.
//
// Review of r3c (V1 round 3) — a cap alone never says where the copies ABOVE it go, and that is the open detail #175
// names. A cap of 3 that sent the rest nowhere (no cell, no line) passed case 2. V1's rule is that nothing is silently
// lost, so two cases now account for every copy, WHEREVER the cap sends it. Each counts the cells EVERY locker card
// draws for the name (a regular cell, `.vm-cell[data-vault-item]`, or a spare trade-stock cell, `.vmc-spare`), so
// the destination is left to his ruling:
//   3. With a WAR1 mule (made through the real Add-mule door, its prompt answered "WAR1"; a mule named WAR<n> is a
//      WAR mule, _vaultWarRole `/^war\s*(\d*)$/i`), the cells summed over every card equal the copies he owns. The
//      cap's own comment (bible.html, above _WAR_SMALL_CAP) says copies over the cap "go to the WAR mules (WAR1,
//      WAR2 ... in order) with their own rows", and _shelfCopyCount draws them on the WAR card (`_vaultWarOverOn`).
//      GREEN on the merged tree: Grief 4 shared + 3 on WAR1, Last Wish 4 + 1. A cap that drops the copies over it
//      draws fewer cells. Measured: red with the WAR card's draw removed, and red with the over-cap copies cut out of
//      the plan.
//   4. With no WAR mule, the cards draw every copy, OR the MOVE TASKS line "No room: … — make a mule named WAR1 (then
//      WAR2…) for: <b>name</b>" names the item (_vaultMoveHtml, `.vmv-warfull`). That is the L1 rule's own promise
//      (Elad 2026-10-20): "with no WAR mule they keep no cell and the 'make a mule named WAR1' line says so".
//      ⚠ RED ON THE MERGED V1 TREE, AND IT IS REAL. It does not depend on the 10-22 cap. For a copy count with no
//      sighting, the line names nothing, because _vaultMoveCollect builds no row for such a copy
//      (`if (!stored && !hasSight && !_vaultMisfiled(r.name)) return;`). So nothing packs the war stash, and
//      window._vaultWarFull, which only _vaultMovePackHome sets, stays empty. Measured: cards 4 and 4, line "". The
//      planner re-pick makes exactly that state: vaultPlannerFile's "already filed" branch does
//      `copies[nm] = prevN + 1` and writes no move row. Today only the stash window still draws all 7 Grief (v3738
//      case 4), and a cap that also caps the window, the obvious next step, leaves 4 of 7 Grief drawn nowhere and
//      named in no line (the reviewer's sb9, measured: cards 3, line ""). Green once the window follows the cap and
//      an unsighted over-cap count reaches the line (a scratch patch doing both, measured: cards 4, Grief and Last
//      Wish named; and with a cap of 3 as well: cards 3, named).

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

/* Cases 3 and 4: where every copy of each name is after one paint. `per` holds the cells each locker card draws for it,
   keyed by locker id. `named` says whether the MOVE TASKS "No room … WAR1" line names it. With withWar1, a mule named
   WAR1 is made first, through the Add-mule door. */
async function whereEveryCopyIs(page: any, names: string[], withWar1: boolean) {
  return page.evaluate(({ names, withWar1 }: { names: string[]; withWar1: boolean }) => {
    const W = window as any;
    try { if (typeof W.switchTab === 'function') W.switchTab('tools'); } catch (e) {}
    if (withWar1) { W.prompt = () => 'WAR1'; W.vaultAddMule(); }
    W.renderVault();
    const wars: string[] = (typeof W._vaultWarMules === 'function' ? W._vaultWarMules() : []).map((m: any) => m.name);
    const host = document.getElementById('vault-move-list');
    const lines = host ? Array.from(host.querySelectorAll('.vmv-warfull')) : [];
    const lineNames: string[] = [];
    lines.forEach((l: any) => Array.from(l.querySelectorAll('b')).forEach((b: any) => lineNames.push((b.textContent || '').trim())));
    const listShown = !!host && !host.hidden && !host.closest('[hidden]');
    const out: Record<string, any> = {};
    names.forEach((nm) => {
      const per: Record<string, number> = {};
      document.querySelectorAll('.vault-mule[data-vault-mule]').forEach((card: any) => {
        const n = Array.from(card.querySelectorAll('.vm-cell')).filter((c: any) => c.getAttribute('data-vault-item') === nm
          || (c.classList.contains('vmc-spare') && c.getAttribute('data-arttip') === nm)).length;
        const id = card.getAttribute('data-vault-mule');
        if (n) per[id] = (per[id] || 0) + n;
      });
      out[nm] = {
        war: W.vaultWarGearRole(nm),
        route: (W.suggestMule(nm) || {}).id,
        per,
        drawn: Object.keys(per).reduce((s, k) => s + per[k], 0),
        named: listShown && lineNames.indexOf(nm) >= 0,
      };
    });
    const line = lines.map((l: any) => (l.textContent || '').replace(/\s+/g, ' ').trim()).join(' | ');
    return { wars, line, out };
  }, { names, withWar1 });
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

test('war gear: with a WAR1 mule every Grief and Last Wish copy is drawn on some locker card, so a cap drops none (V1: nothing silently lost)', async ({ page }) => {
  const COPIES: Record<string, number> = { 'Grief': 7, 'Last Wish': 5 };
  await seed(page, Object.keys(COPIES), COPIES);
  const r = await whereEveryCopyIs(page, Object.keys(COPIES), true);
  expect(r.wars, 'PREMISE: the Add-mule door made one WAR mule, WAR1').toEqual(['WAR1']);
  for (const nm of Object.keys(COPIES)) {
    const a = r.out[nm];
    expect(a.war, `PREMISE: ${nm} is war gear`).toBeTruthy();
    expect(a.route, `PREMISE: ${nm} lives in the war (shared) stash`).toBe('shared');
    expect(a.per.shared || 0, `PREMISE: the war stash card leaves ${nm} copies over its cap (cells ${JSON.stringify(a.per)}), or this case proves nothing`).toBeLessThan(COPIES[nm]);
    expect(a.drawn, `${nm}: every one of the ${COPIES[nm]} copies is drawn on some locker card, wherever the cap sends it (cells ${JSON.stringify(a.per)})`).toBe(COPIES[nm]);
  }
});

test('war gear with no WAR mule: every copy the war stash card leaves out is named in the MOVE TASKS "No room … WAR1" line (L1, Elad 2026-10-20)', async ({ page }) => {
  const COPIES: Record<string, number> = { 'Grief': 7, 'Last Wish': 5 };
  await seed(page, Object.keys(COPIES), COPIES);
  const r = await whereEveryCopyIs(page, Object.keys(COPIES), false);
  expect(r.wars, 'PREMISE: no WAR mule').toEqual([]);
  for (const nm of Object.keys(COPIES)) {
    const a = r.out[nm];
    expect(a.drawn, `${nm}: no locker card draws more cells than he owns copies (cells ${JSON.stringify(a.per)})`).toBeLessThanOrEqual(COPIES[nm]);
    // soft, so one run names every runeword that is short (measured on the merged tree: Grief 4 of 7, Last Wish 4 of 5, line "")
    expect.soft(a.drawn === COPIES[nm] || a.named,
      `${nm}: the locker cards draw ${a.drawn} of ${COPIES[nm]} copies and no "No room" line names it, so ${COPIES[nm] - a.drawn} ${COPIES[nm] - a.drawn === 1 ? 'has' : 'have'} no cell and no word (cells ${JSON.stringify(a.per)}, line "${r.line}")`).toBe(true);
  }
});
