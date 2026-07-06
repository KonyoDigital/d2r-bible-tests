import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v591 — SUPER POTIONS VISIBLE (Konyo: "super healing and super mana potions are shown to be seen..
// but technically i cant see them — something is hiding them!"). Root cause: the template's
// "8. Show Potions" rule (hp5 Super Healing / mp5 Super Mana / rvl Full Rejuv) shipped DISABLED, and
// hp5/mp5 ALSO sat on the "1. Hide Trash Gear" itemCode list — double-hidden. Fix: rule 8 enabled and
// the three codes stripped from every hide rule, so potions show under BOTH first-match and last-match
// rule semantics. The sweep assertion locks the general invariant: nothing an ENABLED show rule lists
// by itemCode may sit in an enabled hide rule's itemCode list (the gem overlap was the one legacy
// exception — now the only sanctioned overlaps are NONE).

test('super/rejuv potions: show rule enabled, codes absent from every hide list (built output)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const out = JSON.parse(w.buildEndgameFilter().text);
    const pot = out.rules.find((x: any) => x.name === '8. Show Potions');
    const hides = out.rules.filter((x: any) => x.ruleType === 'hide' && x.enabled);
    const hiddenPotions = hides.flatMap((x: any) => (x.itemCode || []).filter((c: string) => ['hp5', 'mp5', 'rvl'].includes(c)));
    return { potEnabled: !!(pot && pot.enabled), potCodes: (pot && pot.itemCode) || [], hiddenPotions };
  });
  expect(r.potEnabled).toBe(true);                       // the show rule actually fires
  expect(r.potCodes.sort()).toEqual(['hp5', 'mp5', 'rvl']);
  expect(r.hiddenPotions).toEqual([]);                   // no hide rule re-hides them (works under first-match too)
});

test('sync sweep: no enabled show rule itemCode is also on an enabled hide rule itemCode list', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const out = JSON.parse(w.buildEndgameFilter().text);
    const hideCodes = new Set<string>();
    out.rules.filter((x: any) => x.ruleType === 'hide' && x.enabled).forEach((x: any) => (x.itemCode || []).forEach((c: string) => hideCodes.add(c)));
    const clashes: string[] = [];
    out.rules.filter((x: any) => x.ruleType === 'show' && x.enabled).forEach((x: any) =>
      (x.itemCode || []).forEach((c: string) => { if (hideCodes.has(c)) clashes.push(x.name + ':' + c); }));
    return { clashes };
  });
  // known legacy exception: rule 1 still lists the 21 gem codes that rule 5 shows — gems demonstrably
  // render in-game (show wins in this mod), so they're tolerated; anything NEW must not clash.
  const unexpected = r.clashes.filter((c: string) => !c.startsWith('5. Show Gems:'));
  expect(unexpected).toEqual([]);
});

// v591.1 — BOOT-RACE GUARD: on a slow load the runeword engine (RUNEWORD_TIP / forgeScan /
// _forgeMetaBase, defined far below the filter card's block) lands SECONDS after the card is clickable.
// Copy must refuse (not export a degenerate premium-only "KonyoEndgame0") until the engine is ready.
test('copy refuses while the runeword engine is still loading (boot-race guard)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const readyBefore = w._lfEngineReady();
    const saved = w.forgeScan;
    delete w.forgeScan;                          // simulate the not-yet-parsed tail of the file
    const readyDuringBoot = w._lfEngineReady();
    w.copyLootFilter('endgame');
    const status = (document.getElementById('lf-endgame-status')?.textContent || '');
    w.forgeScan = saved;                         // restore
    const readyAfter = w._lfEngineReady();
    return { readyBefore, readyDuringBoot, status, readyAfter };
  });
  expect(r.readyBefore).toBe(true);
  expect(r.readyDuringBoot).toBe(false);
  expect(r.status).toContain('still loading');   // refused with a clear message, nothing copied
  expect(r.readyAfter).toBe(true);
});
