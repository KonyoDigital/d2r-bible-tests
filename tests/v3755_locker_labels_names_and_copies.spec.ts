import { test, expect } from '@playwright/test';

// #76 (v3755) — THE LOCKER HEADER COUNTS DISTINCT NAMES (= the shelf card), NOT PHYSICAL COPIES, AND SHOWS
// COPIES AS A SEPARATELY-LABELLED FIGURE. GrokBot read Konyo's live board (v3753): the shelf card shows
// "SETS-REST 30" (distinct names) while the opened locker's headline showed "Items 49" (capped physical
// copies) — the SAME number labelled "Items" on both surfaces, reading as a card-vs-locker contradiction
// when 30 = distinct names and 49 = physical copies. openMuleCard's _physN (_muleLoad.phys) was labelled
// "Items" at every headline/row; it now shows the distinct-name count (names.length === the card badge,
// _muleNamesFor is the card's own list) as "items", with _physN surfaced as its own "copies" figure.
// Pure RELABEL — no store write, no records dependency (names.length / _physN already in scope @openMuleCard).
// RED before v3755: the locker header shows the physical-copy count (4), not the name count (2), and never
// says "copies". The LAW is header === distinct names AND copies shown separately — pinned, never the literal
// number. [[regression-guard]] [[the-unjoined-end]]

const SOJ = 'The Stone of Jordan';   // grail unique — seeded with 3 copies
const RAVEN = 'Raven Frost';          // grail unique — 1 copy

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
    typeof (window as any).openMuleCard === 'function'
    && typeof (window as any)._muleNamesFor === 'function');
}

test('the locker header counts distinct names (= the card), not physical copies, and shows copies separately (#76 v3755)', async ({ page }) => {
  // two distinct names on uni-small, one owning 3 copies -> distinct names = 2, physical copies = 4
  await seedLoad(page, [SOJ, RAVEN], { [SOJ]: 3 }, { [SOJ]: 'uni-small', [RAVEN]: 'uni-small' });

  const r = await page.evaluate(() => {
    const w = window as any;
    try { if (w.renderVault) w.renderVault(); } catch (e) {}
    w.openMuleCard('uni-small');
    const box = document.getElementById('vault-detail');
    const lvl = box ? box.querySelector('.mp-lvl .mp-box-v') : null;
    const headerNum = lvl ? parseInt((lvl.textContent || '').trim(), 10) : -1;
    const names = (w._muleNamesFor('uni-small') || []).length;      // === the shelf card badge, by construction
    const txt = box ? (box.textContent || '') : '';
    return { headerNum, names, hasCopies: /\bcopies\b/i.test(txt) };
  });

  // the seed makes names (2) and physical copies (4) genuinely differ, so the law can fail
  expect(r.names).toBe(2);
  // the locker header shows the DISTINCT-NAME count (what the shelf card shows), not the inflated physical count
  expect(r.headerNum).toBe(r.names);      // RED before v3755: header showed physical copies (4) != names (2)
  // and the physical copy count is still shown, labelled "copies"
  expect(r.hasCopies).toBe(true);         // RED before v3755: the locker never said "copies"
});
