import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2205 (#48) — A SET PIECE IN d2r_owned WAS DELETED ON EVERY SINGLE LOAD.
//
// Found while verifying an unrelated vault undo, and PRE-EXISTING — nothing shipped that day caused
// it. Measured with every migration stamped so none could interfere:
//     wrote   ["Laying of Hands (bramble mitts)", "Waterwalk", "Nagelring"]
//     reload  ["Waterwalk", "Nagelring"]
//
// "Laying of Hands (bramble mitts)" is one of the FIVE items his 14:39 ledger snapshot records as
// genuinely his. It was being quietly removed every time he opened the board.
//
// WHY NO CLAUSE SAW IT:
//     _norm("Laying of Hands (bramble mitts)") = "laying of hands bramble mitts"
//     _norm("Laying of Hands")                 = "laying of hands"        <- do not match
//     ITEM_REGISTRY holds the BARE name only
//     _ROSTER_NORM is the 398 UNIQUES and excludes set pieces BY CONSTRUCTION
// So the filter had no clause for a set piece at all — while tvVaultRegister deliberately writes
// them there (findSetPiece -> owned.add(name)). The vault puts them in; the prune took them out.
//
// ⚠ THIS IS THE THIRD TIME THIS LINE HAS EATEN REAL ITEMS. v2082 fixed sixteen names by asking the
// ROSTER instead of ITEM_REGISTRY ("two catalogues, one question, opposite answers"); v2128 added
// his own mule filings. Each fix closed one catalogue and left the next. The rule is not "add
// another list" — it is ASK THE RESOLVER THE REST OF THE APP TRUSTS, which for set pieces is
// findSetPiece, the exact function the vault uses to decide the same thing.

const HIS_FIVE = ['Waterwalk', "Cow King's Leathers (set)", 'Nagelring', 'Raven Frost',
                  'Laying of Hands (bramble mitts)'];

async function ready(page: any) {
  await page.waitForFunction(
    () => typeof (window as any).LSR !== 'undefined'
       && typeof (window as any).findSetPiece === 'function', null, { timeout: 120000 });
}

/** Stamp every migration so this spec measures the PRUNE and nothing else. */
async function quiesce(page: any, owned: string[]) {
  await page.evaluate((own: string[]) => {
    const w = window as any;
    w.LSR.setItem('d2r_vaultBackfill_v2200', '{"x":1}');
    w.LSR.setItem('d2r_vaultBackfillUndo_v2203', '{"x":1}');
    w.LSR.setItem('d2r_vaultBackfillUndo_v2205', '{"x":1}');
    w.LSR.setItem('d2r_tvExtraItems', '{}');
    w.LSR.setItem('d2r_muleAssign', '{}');      // so _maKeep cannot be what saves it
    w.LSR.setItem('d2r_owned', JSON.stringify(own));
  }, owned);
}

test('a set piece he owns is still there after a reload', async ({ page }) => {
  await page.goto(URL);
  await ready(page);
  await quiesce(page, HIS_FIVE);

  await page.goto(URL);
  await ready(page);
  await page.waitForTimeout(1200);

  const own = await page.evaluate(() =>
    JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]') as string[]);

  for (const n of HIS_FIVE) {
    expect(own, `"${n}" was deleted by the load-time prune. It is one of the five items his own `
      + `ledger snapshot records as genuinely his, and it was disappearing on EVERY page load. `
      + `d2r_muleAssign is emptied by this fixture on purpose, so nothing but the set-piece clause `
      + `can be what keeps it.`).toContain(n);
  }
});

test('the fixture is not vacuous — the prune really does still delete a bogus name',
  async ({ page }) => {
    // ⚠ Without this, the test above passes on a build where the prune was simply disabled, and a
    // prune that keeps EVERYTHING is a different defect wearing this fix's name.
    await page.goto(URL);
    await ready(page);
    await quiesce(page, ['Waterwalk', 'Zzzz Not A Real Item At All']);

    await page.goto(URL);
    await ready(page);
    await page.waitForTimeout(1200);

    const own = await page.evaluate(() =>
      JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]') as string[]);
    expect(own, 'the real item was dropped').toContain('Waterwalk');
    expect(own, 'a name no catalogue and no resolver recognises SURVIVED the prune — the prune is '
      + 'no longer pruning, so the test above proves nothing')
      .not.toContain('Zzzz Not A Real Item At All');
  });

test('findSetPiece is what decides it, not another hand-written list', async ({ page }) => {
  // the rule v2082 reached for and this fix repeats: ask the resolver the app already trusts, so
  // the vault's idea of "is this a set piece" and the prune's can never drift apart
  await page.goto(URL);
  await ready(page);
  const m = await page.evaluate(() => {
    const w = window as any;
    return {
      resolves: !!w.findSetPiece('Laying of Hands (bramble mitts)'),
      normDiffers: w._norm ? w._norm('Laying of Hands (bramble mitts)') !== w._norm('Laying of Hands')
                           : null,
      registryLacksSuffixed: !w.ITEM_REGISTRY['Laying of Hands (bramble mitts)'],
    };
  });
  expect(m.resolves, 'findSetPiece no longer recognises the suffixed piece name, so the prune '
    + 'clause that depends on it is inert and the item starts vanishing again').toBe(true);
  expect(m.registryLacksSuffixed, 'ITEM_REGISTRY now holds the suffixed name, which means this '
    + 'test is no longer exercising the gap it was written for').toBe(true);
});
