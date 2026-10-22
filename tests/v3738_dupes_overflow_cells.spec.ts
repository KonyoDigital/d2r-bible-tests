import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — duplicate copies sit next to the original on the same
// mule. GRAIL-DUPES draws no spare cells. A 7-copy shared Grief and a 2-copy Raven Frost both
// contribute 0 overflow. The dupes locker, holding nothing, is an empty locker.
//
// V0 spec refresh (#175 / #176) — HIS 2026-10-22 RULING (verbatim): "so for grief and certain runewords that
// are rare and as hard core as it like last wish too they should be in war gear like 2-3 copies". That retires
// the 10-18 "every copy beside the original on the shared locker" rule FOR WAR GEAR and keeps it for everything
// else, so the two cases are held apart:
//   1. 10-18, a NON-war item. The Stone of Jordan x7 filed to the shared stash: every copy stays on the shared
//      locker (7 cells — a 1x1 ring keeps every copy under his 10-20 cap, bible.html _vaultWarCap0), the
//      GRAIL-DUPES locker draws no spare cells (_vaultDupesCells / _vaultSharedOverflowCells return 0, "v3767
//      no spare cells"), and holding nothing it reads "empty locker" and is dimmed. Grief and Raven Frost left
//      this case: both are on the WAR_GEAR list, and which war items keep every copy is exactly what the
//      10-22 ruling reopened (the exact list is still his to confirm, #175).
//   2. 10-22, war gear. Grief x7 filed to the shared stash keeps 2-3 copies there — on the shelf's shared card
//      AND in the shared stash window, which must agree.
//      ⚠ RED ON THE MERGED V1 TREE, AND THAT IS THE FINDING, NOT A SPEC BUG. Measured: the shelf card draws 4
//      (the 10-20 footprint cap: an un-sized Grief is the 1x2 guess → "small gear" → 4) and the shared stash
//      window draws all 7 (_sharedPack → _sharedCappedCopies, "v3767 draw every copy" — no war cap at all).
//      Two surfaces of one stash disagree, and neither keeps the 2-3 he ruled. It stays red until it is built.
//      The premises it shares (war gear, filed to shared) are asserted again in case 3, which runs green, so a
//      broken premise shows there, never only inside this red.
//
// Review of r3c (V1 round 3): case 2 pins the cap. It never says where the copies ABOVE the cap go, and that is the
// open detail #175 names. A cap of 3 that also capped the window and sent the rest nowhere passed it. Measured: the
// card and the window both draw 3, and no cell or line holds the other 4. V1's rule is that nothing is silently lost.
// So two cases now account for every Grief copy, wherever a cap sends it. Each counts the cells EVERY locker card
// draws for the name: a regular cell (`.vm-cell[data-vault-item]`) or a spare trade-stock cell (`.vmc-spare`).
//   3. A mule named WAR1 is made through the real Add-mule door: its prompt is answered "WAR1", and a mule named
//      WAR<n> is a WAR mule (_vaultWarRole `/^war\s*(\d*)$/i`). Then the cells summed over every card equal the 7 he
//      owns: the cap sends copies over it "to the WAR mules (WAR1, WAR2 ... in order)" (bible.html, above
//      _WAR_SMALL_CAP), and _shelfCopyCount draws them on the WAR card (`_vaultWarOverOn`). GREEN on the merged tree:
//      4 shared + 3 on WAR1. A cap that drops the copies over it draws fewer: 3 in all, measured both with the WAR
//      card's draw removed and with the over-cap copies cut out of the plan.
//   4. With no WAR mule, the shared stash window draws what the shelf card draws (one stash, one count). The cards
//      draw every copy, OR the MOVE TASKS line "No room: … — make a mule named WAR1 (then WAR2…) for: <b>Grief</b>"
//      names it (_vaultMoveHtml, `.vmv-warfull`). That is the L1 rule's own promise (Elad 2026-10-20): "with no WAR
//      mule they keep no cell and the 'make a mule named WAR1' line says so".
//      ⚠ RED ON THE MERGED V1 TREE, AND IT IS REAL. It does not depend on the 10-22 cap. The 10-20 cap is applied
//      on the card and nowhere else:
//      - The window packs every copy: _sharedCappedCopies is `return _sharedCopyCount(n); /* v3767 draw every copy */`.
//      - For a copy count with no sighting, the line names nothing. _vaultMoveCollect builds no row for such a copy
//        (`if (!stored && !hasSight && !_vaultMisfiled(r.name)) return;`), so nothing packs the war stash, and
//        window._vaultWarFull (set only by _vaultMovePackHome) stays empty.
//      Measured: card 4, window 7, line "". A planner re-pick makes exactly that state: vaultPlannerFile's "already
//      filed" branch does `copies[nm] = prevN + 1` and writes no move row. Green once the window follows the cap and
//      an unsighted over-cap count reaches the line. Measured with a scratch patch doing both: card 4, window 4,
//      Grief named. With a cap of 3 as well: card 3, window 3, named.

async function seed(page: any, owned: string[], copies: Record<string, number>, assign: Record<string, string>) {
  await page.addInitScript(({ owned, copies, assign }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
    } catch (e) {}
  }, { owned, copies, assign });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).renderVault === 'function'
    && typeof (window as any)._vaultSharedOverflowCells === 'function');
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
        filed: W._vaultFiledOn(nm),
        per,
        drawn: Object.keys(per).reduce((s, k) => s + per[k], 0),
        named: listShown && lineNames.indexOf(nm) >= 0,
      };
    });
    const line = lines.map((l: any) => (l.textContent || '').replace(/\s+/g, ' ').trim()).join(' | ');
    return { wars, line, out };
  }, { names, withWar1 });
}

test('the DUPES locker draws no spare cells; copies stay on the shared mule (Elad 2026-10-18)', async ({ page }) => {
  const NAME = 'The Stone of Jordan';
  await seed(page, [NAME], { [NAME]: 7 }, { [NAME]: 'shared' });
  const r = await page.evaluate((nm: string) => {
    const W = window as any;
    const logic = {
      war: W.vaultWarGearRole ? W.vaultWarGearRole(nm) : 'n/a',
      overflow: W._vaultSharedOverflowCells(nm),
      names: W._vaultSharedOverflowNames(),
      sharedCells: W._shelfDrawNames([nm], 'shared').length,
    };
    W.VAULT_PROVEN = { [nm]: true };   // so the ⚖ proof chip renders
    W.renderVault();
    const dupes = document.querySelector('[data-vault-mule="dupes"]');
    const spareCells = dupes ? dupes.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    const nameCells = dupes
      ? Array.from(dupes.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf(nm) >= 0).length
      : -1;
    // REG-2226 follow-up: a dupes locker with ONLY overflow (nothing filed to it) is NOT empty
    const saysEmpty = dupes ? /empty locker/i.test(dupes.textContent || '') : true;
    const isDimmed = dupes ? dupes.classList.contains('vm-empty') : true;
    return { logic, spareCells, nameCells, dupesPresent: !!dupes, saysEmpty, isDimmed };
  }, NAME);

  expect(r.logic.war, 'PREMISE: a non-war item, so the 10-18 rule still governs it').toBeNull();
  expect(r.logic.sharedCells).toBe(7);
  expect(r.dupesPresent).toBe(true);
  expect(r.logic.overflow).toBe(0);
  expect(r.logic.names).not.toContain(NAME);
  expect(r.spareCells).toBe(0);
  expect(r.nameCells).toBe(0);
  expect(r.saysEmpty).toBe(true);
  expect(r.isDimmed).toBe(true);
});

test('war gear keeps 2-3 copies in the war stash, on the shelf card and in the stash window alike (his 2026-10-22 ruling)', async ({ page }) => {
  const NAME = 'Grief';
  await seed(page, [NAME], { [NAME]: 7 }, { [NAME]: 'shared' });
  const r = await page.evaluate((nm: string) => {
    const W = window as any;
    const shelf = W._shelfDrawNames([nm], 'shared').length;
    try { if (typeof W.switchTab === 'function') W.switchTab('tools'); } catch (e) {}
    const tab = W._sharedTabOf(nm).tab;
    W.openMuleCard('shared');
    W._sharedSetPage(tab);
    const windowCells = Array.from(document.querySelectorAll('#vault-detail .vd-item'))
      .filter((el: any) => (el.getAttribute('title') || '').indexOf(nm) === 0).length;
    return { copies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm], war: W.vaultWarGearRole(nm),
             filed: W._vaultFiledOn(nm), shelf, windowCells };
  }, NAME);
  expect(r.copies).toBe(7);
  expect(r.war, 'PREMISE: Grief is war gear').toBeTruthy();
  expect(r.filed, 'PREMISE: Grief is filed to the war (shared) stash').toBe('shared');
  // soft, so one run names every surface that is off the ruling (measured today: shelf 4, window 7)
  expect.soft(r.shelf, 'the shelf card keeps 2-3 Grief copies in war gear').toBeGreaterThanOrEqual(2);
  expect.soft(r.shelf, 'the shelf card keeps 2-3 Grief copies in war gear, not the 10-20 cap of 4').toBeLessThanOrEqual(3);
  expect.soft(r.windowCells, 'the shared stash window draws what the shelf card draws — one stash, one count').toBe(r.shelf);
});

test('war gear: with a WAR1 mule every Grief copy is drawn on some locker card, so a cap drops none (V1: nothing silently lost)', async ({ page }) => {
  const NAME = 'Grief', COPIES = 7;
  await seed(page, [NAME], { [NAME]: COPIES }, { [NAME]: 'shared' });
  const r = await whereEveryCopyIs(page, [NAME], true);
  const a = r.out[NAME];
  expect(r.wars, 'PREMISE: the Add-mule door made one WAR mule, WAR1').toEqual(['WAR1']);
  expect(a.war, 'PREMISE: Grief is war gear').toBeTruthy();
  expect(a.filed, 'PREMISE: Grief is filed to the war (shared) stash').toBe('shared');
  expect(a.per.shared || 0, `PREMISE: the war stash card leaves Grief copies over its cap (cells ${JSON.stringify(a.per)}), or this case proves nothing`).toBeLessThan(COPIES);
  expect(a.drawn, `every one of the ${COPIES} Grief copies is drawn on some locker card, wherever the cap sends it (cells ${JSON.stringify(a.per)})`).toBe(COPIES);
});

test('war gear with no WAR mule: the stash window draws what the shelf card draws, and the "No room … WAR1" line names every copy the card leaves out (L1, Elad 2026-10-20)', async ({ page }) => {
  const NAME = 'Grief', COPIES = 7;
  await seed(page, [NAME], { [NAME]: COPIES }, { [NAME]: 'shared' });
  const r = await whereEveryCopyIs(page, [NAME], false);
  const a = r.out[NAME];
  const windowCells = await page.evaluate((nm: string) => {
    const W = window as any;
    const tab = W._sharedTabOf(nm).tab;
    W.openMuleCard('shared');
    W._sharedSetPage(tab);
    return Array.from(document.querySelectorAll('#vault-detail .vd-item'))
      .filter((el: any) => (el.getAttribute('title') || '').indexOf(nm) === 0).length;
  }, NAME);
  expect(r.wars, 'PREMISE: no WAR mule').toEqual([]);
  expect(a.drawn, `no locker card draws more cells than he owns copies (cells ${JSON.stringify(a.per)})`).toBeLessThanOrEqual(COPIES);
  // soft, so one run names both halves (measured on the merged tree: card 4, window 7, line "")
  expect.soft(windowCells, 'the shared stash window draws what the shelf card draws: one stash, one count').toBe(a.per.shared || 0);
  expect.soft(a.drawn === COPIES || a.named,
    `the locker cards draw ${a.drawn} of ${COPIES} Grief copies and no "No room" line names it, so ${COPIES - a.drawn} ${COPIES - a.drawn === 1 ? 'has' : 'have'} no cell and no word (cells ${JSON.stringify(a.per)}, line "${r.line}")`).toBe(true);
});
