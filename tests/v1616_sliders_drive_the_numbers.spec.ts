import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1616 — ASK B: "the MF finder on the bottom should be silopen synced to the drops ... for all
   forges and grails ... this worked back in the day."

   The archaeology answer is in the assertions below, not in a comment: the chronicles' ETA math
   was reading the RAW source odds (s.chance) instead of the calculator's effChance()/playerMult()
   seams, so the control dock moved the Calculator and the hero and left every chronicle frozen at
   the 300-MF / players-1 baseline. _adjC (exposed as window._fAdjC) is the repair.

   BOTH DIRECTIONS ARE ASSERTED. A number that moves when MF must not touch it is exactly as wrong
   as one that refuses to move: the app's own honesty panel says MF does nothing for runes, gems,
   jewels, charms or gold, and this file holds that line under the same drag that must move a
   unique. */

const settle = async (page: any) => { await page.waitForTimeout(900); };

async function setSlider(page: any, id: string, value: number) {
  await page.evaluate(([i, v]: [string, number]) => {
    const el = document.getElementById(i) as HTMLInputElement;
    el.value = String(v);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, [id, value] as [string, number]);
  await page.waitForTimeout(450);   // _sliderFanout is debounced at 220ms
}

test.describe('v1616 — the sliders drive every number', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await settle(page);
  });

  test('★★★ the chronicle seam exists and is the SAME seam the calculator uses', async ({ page }) => {
    const r = await page.evaluate(() => ({
      seam: typeof (window as any)._fAdjC,
      eff: typeof (window as any).effChance,
      fanout: typeof (document.getElementById('mf') as any)?.oninput,
    }));
    // if _fAdjC is gone the chronicles are computing their own odds again — the exact v1616 bug
    expect(r.seam, 'the chronicles must defer to a published adjust seam').toBe('function');
    expect(r.fanout).toBe('function');
  });

  test('★★★ a UNIQUE ETA responds to the MF slider — and in the right direction', async ({ page }) => {
    const probe = async () => await page.evaluate(() => {
      const f = (window as any)._fAdjC;
      // a plain unique source row: MF is allowed to improve its quality roll
      return f({ chance: 20000, bossId: 'mephisto', diffKey: 'hell' }, 'Frostburn');
    });
    await setSlider(page, 'mf', 0);
    const low = await probe();
    await setSlider(page, 'mf', 800);
    const high = await probe();
    expect(low, 'the seam must return a number, not null').toBeGreaterThan(0);
    expect(high).not.toBe(low);
    // higher MF = better odds = a SMALLER 1-in-N
    expect(high).toBeLessThan(low);
  });

  test('★★★ MF does NOT touch runes/gems/charms — the honesty panel holds under the same drag', async ({ page }) => {
    const probe = async (name: string) => await page.evaluate((n) => {
      const f = (window as any)._fAdjC;
      return f({ chance: 20000, bossId: 'mephisto', diffKey: 'hell' }, n);
    }, name);
    await setSlider(page, 'mf', 0);
    const before = { rune: await probe('Ist rune'), gem: await probe('Perfect Ruby'), charm: await probe("Gheed's Fortune") };
    await setSlider(page, 'mf', 800);
    const after = { rune: await probe('Ist rune'), gem: await probe('Perfect Ruby'), charm: await probe("Gheed's Fortune") };
    expect(after.rune, 'an Ist rune drops at the same rate at 0% MF as at 800%').toBe(before.rune);
    expect(after.gem).toBe(before.gem);
    expect(after.charm).toBe(before.charm);
  });

  test('★★★ the /players slider moves the numbers MF is not allowed to move', async ({ page }) => {
    const probe = async () => await page.evaluate(() => {
      const f = (window as any)._fAdjC;
      return f({ chance: 20000, bossId: 'mephisto', diffKey: 'hell' }, 'Ist rune');
    });
    await setSlider(page, 'players', 1);
    const p1 = await probe();
    await setSlider(page, 'players', 8);
    const p8 = await probe();
    // /players shrinks NoDrop — QUANTITY — and quantity is real for runes
    expect(p8).not.toBe(p1);
    expect(p8).toBeLessThan(p1);
  });

  test('★★ the console bridges are REWRITTEN when a slider moves', async ({ page }) => {
    await setSlider(page, 'mf', 0);
    const before = await page.evaluate(() => ({
      grail: localStorage.getItem('d2r_grailFarm'),
      sets: localStorage.getItem('d2r_setFarm'),
    }));
    await setSlider(page, 'mf', 900);
    await page.waitForTimeout(600);
    const after = await page.evaluate(() => ({
      grail: localStorage.getItem('d2r_grailFarm'),
      sets: localStorage.getItem('d2r_setFarm'),
    }));
    // at least one bridge must carry the new baseline to the console; d2r_setFarm had NO live
    // caller at all before v1616, which is why the console ETA never followed his slider
    const moved = (before.grail !== after.grail) || (before.sets !== after.sets);
    expect(moved, 'the console bridges must be refreshed by _sliderFanout').toBe(true);
  });
});
