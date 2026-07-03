import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v553 — fixes from the deep Tools/Forge audit:
//  A) AI Item Checker now scores Increased Attack Speed (was unscored → tossed good gloves/weapons) + a premium
//     affix (skills/IAS/FCR/all-res) never auto-tosses.
//  B) Ladder-only runewords no longer leak into the Loot filter / Smart-Insights farm-priority & rune-radar
//     when the user is in the default non-ladder mode.
//  C) Loot filter shows NO bases (empty codes) when nothing needs farming — instead of the ~50 template codes.
//  D) Forge no longer drops an owned caster STAFF for staff-legal words (Insight / Heart of the Oak).

test('A — AI Item Checker scores IAS: a 20% IAS rare gloves is a KEEP, and IAS appears in the breakdown', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const keep = w._aicVerdict({ q: 'rare', base: 'Heavy Gloves', mods: ['20% Increased Attack Speed', '+30 to Life', 'All Resistances +20'] });
    const iasAlone = w._aicVerdict({ q: 'rare', base: 'Chain Gloves', mods: ['20% Increased Attack Speed'] });
    return { keepTier: keep.tier, iasScored: iasAlone.breakdown.some((b: any) => /Attack Speed/.test(b.label)), iasScore: iasAlone.score };
  });
  expect(r.keepTier).toBe('keep');           // IAS(4)+life(5)+allres(6) = 15 → keep (was a toss before — the real bug)
  expect(r.iasScored).toBe(true);            // IAS is now a valued affix (was entirely unscored)
  expect(r.iasScore).toBeGreaterThan(0);     // …and contributes to the score
});

test('A — a lone +2 class-skills caster amulet is NOT tossed (premium-affix floor)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => (window as any)._aicVerdict({ q: 'magic', base: 'Amulet', mods: ['+2 to Sorceress Skill Levels'] }).tier);
  expect(r).not.toBe('toss');
});

test('B — ladder-only runewords are blocked off-ladder and excluded from Smart-Insights unmade list', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_ladderMode', 'nonladder'); localStorage.setItem('d2r_rwMade', '{}'); localStorage.setItem('d2r_owned', '[]'); });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    // find a genuinely ladder-only word to assert on
    const ladderWord = Object.keys((window as any).RUNEWORD_TIP || {}).find((n) => w._rwIsLadderOnly && w._rwIsLadderOnly(n));
    const unmade = w._smartUnmadeNeedingBase();
    const gating = w._smartRuneGating();   // must not report shortfall driven only by ladder words
    return {
      fn: typeof w._rwLadderBlocked,
      ladderWord,
      blocked: ladderWord ? w._rwLadderBlocked(ladderWord) : null,
      unmadeHasLadder: ladderWord ? unmade.includes(ladderWord) : false,
      gatingOk: Array.isArray(gating),
    };
  });
  expect(r.fn).toBe('function');
  expect(r.ladderWord).toBeTruthy();
  expect(r.blocked).toBe(true);              // ladder-only word is blocked in non-ladder mode
  expect(r.unmadeHasLadder).toBe(false);     // …so it's not in the farm/loot unmade list
});

test('B — a ladder-only word IS surfaced when ladder mode is on', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_ladderMode', 'ladder'); localStorage.setItem('d2r_rwMade', '{}'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const ladderWord = Object.keys((window as any).RUNEWORD_TIP || {}).find((n) => w._rwIsLadderOnly && w._rwIsLadderOnly(n));
    return { ladderWord, blocked: ladderWord ? w._rwLadderBlocked(ladderWord) : null };
  });
  expect(r.blocked).toBe(false);   // in ladder mode it's makeable → not blocked
});

test('C — loot filter shows NO base codes when nothing needs farming', async ({ page }) => {
  await page.addInitScript(() => {
    // mark ALL runewords made → nothing to farm
    // (done post-load below since RUNEWORD_TIP isn't available in init script)
  });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys((window as any).RUNEWORD_TIP || {}).forEach((n) => (made[n] = 'x'));
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    const f = w.buildEndgameFilter();
    const parsed = JSON.parse(f.text);
    const baseRule = parsed.rules.find((x: any) => x.name === 'Show Base Items');
    return { baseCount: f.baseCount, ruleCodes: baseRule ? baseRule.equipmentItemCode.length : -1 };
  });
  expect(r.baseCount).toBe(0);
  expect(r.ruleCodes).toBe(0);   // the base-show rule is emptied, not left at the ~50 template codes
});
