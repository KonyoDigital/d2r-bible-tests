import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v592 — SOCKETED-ONLY for common bases (Konyo: "its a pain in the ass to do these larzuk quests..
// rather just farm for it" — a plain white War Spike on the ground is useless to him). The plain-white
// show rule ("Show Base Items") lights up ONLY the premium trade floor; every other wanted base shows
// eth/socketed only (rule 3), and its PLAIN drops are explicitly hidden (rule 1) so the mod's
// default-show can't leak them. Split checked against a pinned 1-word Chronicle: Insight unmade →
// Colossus Voulge is a wanted NON-premium base; Bone Visage is premium.

test('plain whites: premium-only show; common wanted bases eth/socketed-only with plain drops hidden', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_ladderMode', 'nonladder'); });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window;
    const made: any = {}; Object.keys(w.RUNEWORD_TIP || {}).forEach((n) => { if (n !== 'Insight') made[n] = 'x'; });
    localStorage.setItem('d2r_rwMade', JSON.stringify(made));
    localStorage.setItem('d2r_rwProfile', 'fresh');
  });
  await page.reload(); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const CODE = JSON.parse(document.getElementById('lf-base-codes')!.textContent!.trim());
    const eb = w._endgameFilterBases();
    const out = JSON.parse(w.buildEndgameFilter().text);
    const rule = (n: string) => out.rules.find((x: any) => x.name === n);
    const cv = CODE['Colossus Voulge'], bv = CODE['Bone Visage'];
    return {
      cvWanted: eb.codes.includes(cv), cvPlain: eb.plainCodes.includes(cv),
      bvPlain: eb.plainCodes.includes(bv),
      plainEqualsPremiumCount: eb.plainCodes.length === (w._premiumTradeBases || []).length,
      showBase: rule('Show Base Items').equipmentItemCode,
      showEth: rule('3. Show ETH and Socket bases').equipmentItemCode,
      hidePlain: rule('1. Hide Trash Gear').equipmentItemCode,
      hideEth: rule('Hide ETH Sockets').equipmentItemCode,
      cvCode: cv, bvCode: bv,
    };
  });
  expect(r.cvWanted).toBe(true);                       // Insight still needs a Voulge…
  expect(r.cvPlain).toBe(false);                       // …but NOT as a plain white
  expect(r.bvPlain).toBe(true);                        // premium floor keeps plain Bone Visage
  expect(r.plainEqualsPremiumCount).toBe(true);        // plain set === the premium floor, nothing else
  expect(r.showBase).toContain(r.bvCode);              // plain-white rule = premium only
  expect(r.showBase).not.toContain(r.cvCode);
  expect(r.showEth).toContain(r.cvCode);               // eth/socketed Voulge still lights up
  expect(r.showEth).toContain(r.bvCode);
  expect(r.hidePlain).toContain(r.cvCode);             // plain Voulge explicitly hidden (no default-show leak)
  expect(r.hidePlain).not.toContain(r.bvCode);         // plain Bone Visage NOT hidden
  expect(r.hideEth).not.toContain(r.cvCode);           // the eth/socketed hide never swallows a wanted base
  expect(r.hideEth).not.toContain(r.bvCode);
});
