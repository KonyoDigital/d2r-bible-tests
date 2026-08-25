import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2124 — #134. FILING AN ITEM MUST NOT CHANGE WHERE THE RULES SAY IT BELONGS.
//
// Konyo asked to simulate inside the vault manager, and the manager contradicted itself: it filed
// Shako to SOCKETED and then, on the same page, VAULT INTEGRITY reported
// "filed in SOCKETED — belongs in UNI-ARMOR · 1 auto-fixable" — a misroute finding against a
// filing the system had just made.
//
// Both doors call the SAME classifier, so this was never two rules. It was ONE rule answering
// differently before and after the item was filed: suggestMule's white-base branch is gated on
// EXTRA_ITEMS[name], and _tvExtraRemember writes the name straight into EXTRA_ITEMS, so
// registering an item removed it from the branch that had just routed it.
//
// MEASURED on the live board before the fix, before -> after registering the same name:
//     Shako / Monarch / Archon Plate            bases -> uni-armor
//     Phase Blade / Colossus Blade / Hydra Bow   bases -> uni-weap
// FIVE OF SEVEN moved.
//
// ⚠ THIS IS THE HALF A SOURCE GREP CANNOT PROVE. TestV2124 in tv/test_control.py pins the SHAPE of
// the fix; only a browser can call suggestMule twice and watch the answer move. Both are needed:
// the grep would stay green on a refactor that reintroduced the order-dependence by another route.

const NAMES = ['Shako', 'Monarch', 'Archon Plate', 'Phase Blade', 'Colossus Blade', 'Hydra Bow'];

test('a name routes to the same locker before and after it is filed', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).suggestMule === 'function');

  const rows = await page.evaluate((names: string[]) => {
    const w = window as any;
    const out: any[] = [];
    for (const n of names) {
      const ask = () => { try { const r = w.suggestMule(n); return (r && r.id) || '?'; }
                          catch (e) { return 'ERR'; } };
      const before = ask();
      // exactly what tvVaultRegister does to this classifier's inputs
      try {
        w._tvExtraRemember && w._tvExtraRemember(n, {
          rarity: 'basic', base: n, cat: 'TV-vaulted', val: 'tv', src: 'spec',
        });
      } catch (e) { /* the assertion below reports it */ }
      out.push({ name: n, before, after: ask() });
    }
    return out;
  }, NAMES);

  const moved = rows.filter(r => r.before !== r.after);
  expect(moved, 'filing these names moved them to a different locker, so the assembler files with '
    + 'one answer and the integrity auditor flags its own filing: '
    + JSON.stringify(moved)).toEqual([]);

  // AND THE READINGS MUST BE REAL. If suggestMule started throwing, every row would read
  // ERR === ERR and this spec would pass while measuring nothing.
  const useless = rows.filter(r => r.before === 'ERR' || r.before === '?');
  expect(useless, 'the classifier returned no usable answer for these, so the comparison above is '
    + 'vacuous: ' + JSON.stringify(useless)).toEqual([]);
});

test('the assembler and the auditor agree on the item Konyo reported', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).tvVaultRegister === 'function');

  const r = await page.evaluate(() => {
    const w = window as any;
    const reg = w.tvVaultRegister('Shako');
    let assign: any = {};
    try { assign = JSON.parse(w.LSR.getItem('d2r_muleAssign') || '{}') || {}; } catch (e) {}
    const sg = w.suggestMule('Shako');
    return {
      filedTo: assign['Shako'] || (reg && reg.mule) || null,
      rulesSay: sg && sg.id,
      // the auditor's own misroute predicate (bible.html, renderVaultAudit)
      auditWouldFlag: !!(sg && sg.id !== '__keep' && sg.id !== '__throwout'
                         && sg.id !== (assign['Shako'] || (reg && reg.mule))),
    };
  });

  expect(r.rulesSay, 'the classifier gave no answer for the reported item').toBeTruthy();
  expect(r.filedTo, 'the register filed it somewhere the rules do not name')
    .toBe(r.rulesSay);
  expect(r.auditWouldFlag,
    'VAULT INTEGRITY still flags the locker the assembler just chose — the two doors disagree, '
    + 'which is exactly what he reported').toBe(false);
});
