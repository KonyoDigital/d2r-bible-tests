import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v662 — COUSIN loot filter (the cousin's bug: "socketed items are not being shown! something is
// hiding them deliberately" — correct: the Hide-ETH-Sockets rule, by Chronicle-shrink design, and
// the shared-chronicle seed floors Konyo's 88 words on ANY browser so the cousin can't generate an
// honest filter himself). buildEndgameFilter({fresh:true}) = the CousinFull profile:
//   - fresh grail: every word lights its bases (77 vs Konyo's ~27)
//   - SOCKETS = SHOW, PERIOD: every eth/socketed hide rule is stripped, so NO rule can swallow a
//     socketed/eth drop (unmatched → the mod default-shows it)
// Konyo's own KonyoEndgame<N> build must stay byte-identical.

test('CousinFull: fresh grail, zero socketed/eth hide rules, ASCII names; KonyoEndgame untouched', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2500);
  const r = await page.evaluate(() => {
    const w: any = window;
    if (!w._lfEngineReady()) return { notReady: true };
    const mine = JSON.parse(w.buildEndgameFilter().text);
    const cuz = JSON.parse(w.buildEndgameFilter({ fresh: true }).text);
    const sockHides = (f: any) => f.rules.filter((x: any) => x.ruleType === 'hide' && x.filterEtherealSocketed === true).length;
    const show3 = (f: any) => (f.rules.find((x: any) => x.name === '3. Show ETH and Socket bases') || {}).equipmentItemCode || [];
    return {
      notReady: false,
      mineName: mine.name, mineSockHides: sockHides(mine), mineShow3: show3(mine).length, mineRules: mine.rules.length,
      cuzName: cuz.name, cuzSockHides: sockHides(cuz), cuzShow3: show3(cuz).length, cuzRules: cuz.rules.length,
      cuzAscii: cuz.rules.every((x: any) => /^[\x20-\x7e]*$/.test(x.name)),   // non-ASCII rule names get silently dropped by the mod importer
      cuzHasUniques: cuz.rules.some((x: any) => x.name === '2. Show Uniques and Sets' && x.enabled),
      cuzTrashHideIntact: cuz.rules.some((x: any) => x.name === '1. Hide Trash Gear' && x.filterEtherealSocketed === false),
    };
  });
  expect(r.notReady).toBe(false);
  expect(r.mineName).toMatch(/^KonyoEndgame\d+$/);
  expect(r.mineSockHides).toBe(4);                    // Konyo's build keeps all four eth/socket hides
  expect(r.cuzName).toBe('CousinFull');
  expect(r.cuzSockHides).toBe(0);                     // ★ NO rule can hide a socketed/eth item
  expect(r.cuzShow3).toBeGreaterThan(r.mineShow3);    // fresh grail lights far more bases
  expect(r.cuzRules).toBe(r.mineRules - 4);           // exactly the four socketed hides removed
  expect(r.cuzAscii).toBe(true);
  expect(r.cuzHasUniques).toBe(true);
  expect(r.cuzTrashHideIntact).toBe(true);            // plain trash still hidden (flag=false ignores socketed)
});
