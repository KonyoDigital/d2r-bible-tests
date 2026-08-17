// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v351 — maxroll/DarkHumility trade-value tier lists (505 uniques/sets + 280 magic items) embedded:
// a filterable "Trade Values" Tools card + a value-tier badge on owned items in the Registered panel.

const URL = 'file://' + process.cwd() + '/bible.html';

test('trade values: data, card render, owned-item badge, suffix-aware lookup', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Windforce', 'Axe of Fechmar', 'Annihilus']));
    // v681 — mule-assign so the v677 ledger/vault cleanse keeps these physical grail uniques in owned
    // (unassigned grail-seed names are stripped from d2r_owned on boot). The badge still exercises _itemValue.
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Windforce': 'uni-weap', 'Axe of Fechmar': 'uni-weap', 'Annihilus': 'uni-small' }));
  });
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const w = window as any;
    w.switchTab('tools');
    w.renderItemValues('unique');
    const rowsU = document.querySelectorAll('#iv-list .iv-row').length;
    w.renderItemValues('magic');
    const rowsM = document.querySelectorAll('#iv-list .iv-row').length;
    w.renderItemValues('unique'); w._ivSetTier('trash');
    const trashOnly = Array.from(document.querySelectorAll('#iv-list .iv-row .vrg-val')).every((b) => /trash/i.test(b.className));
    // owned-item badge in the Registered panel
    w._ivSetTier('all');
    const regBadge = (() => {
      const rows = Array.from(document.querySelectorAll('#vault-registered .vrg-row'));
      const wf = rows.find((x) => (x.getAttribute('data-vault-item') || '') === 'Axe of Fechmar');
      return wf?.querySelector('.vrg-val')?.textContent || '';
    })();
    return {
      uniques: (w.D2_VAL_UNIQUE || []).length, magic: (w.D2_VAL_MAGIC || []).length,
      ivFechmar: w._itemValue('Axe of Fechmar'), ivShako: w._itemValue('Harlequin Crest (Shako)'),
      rowsU, rowsM, trashOnly, regBadge,
    };
  });
  expect(errs).toEqual([]);
  expect(r.uniques).toBe(505);
  expect(r.magic).toBe(280);
  expect(r.ivFechmar).toBe('trash');
  expect(r.ivShako).toBe('high');         // suffix-stripped lookup ("(Shako)")
  expect(r.rowsU).toBeGreaterThan(400);
  expect(r.rowsM).toBeGreaterThan(100);
  expect(r.trashOnly).toBe(true);          // tier filter works
  expect(r.regBadge.toLowerCase()).toContain('trash');  // owned item badged
});
