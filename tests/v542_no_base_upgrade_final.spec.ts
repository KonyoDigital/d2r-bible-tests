import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v542 — the "cube-up a white base to a higher tier" fiction is ripped out ENTIRELY (Konyo: "rip this out of
// the universe completely"). No _upgradeChainFor, no forgeScan.upgrades bucket, no "Cube-upgrade" render text,
// and the Item Checker only offers a tier-upgrade note for RARE items (magic/crafted can't upgrade — game-file
// cubemain.txt: unique/rare/set only). These lock every piece of the removal.

test('forgeScan has NO upgrades bucket and _upgradeChainFor does not exist', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const s = w.forgeScan();
    return { hasBucket: ('upgrades' in s), fnType: typeof w._upgradeChainFor };
  });
  expect(r.hasBucket).toBe(false);
  expect(r.fnType).toBe('undefined');
});

test('the rendered Forge never contains "Cube-upgrade" (any owned base, any bucket)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Crystal Sword (Larzuk base)', 'Bone Helm (Larzuk base)', 'Grim Scythe (6os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Vex: 1, Hel: 1, El: 1, Eld: 1, Zod: 1, Eth: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    ['Crystal Sword (Larzuk base)', 'Bone Helm (Larzuk base)', 'Grim Scythe (6os)'].forEach((o) => { try { w._ensureSocketBaseEntry(o); } catch (e) {} });
    w.switchTab('forge');
    let txt = '';
    ['all', 'now', 'pipeline', 'onestep'].forEach((f) => { w.forgeSetFilter(f); w.renderForge(); txt += (document.getElementById('tab-forge')!.textContent || ''); });
    return { hasCubeUpgrade: /Cube-upgrade|cube.upgrade your|Base upgrades/i.test(txt) };
  });
  expect(r.hasCubeUpgrade).toBe(false);
});

test('Item Checker: cube tier-upgrade note shows for RARE only — never magic or crafted', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    const mods = ['+2 to All Skills', '20% Faster Cast Rate', '+30 to Life'];
    const ctxOf = (q: string) => {
      const v = w._aicVerdict({ q, base: 'Crystal Sword', mods });   // Crystal Sword = normal tier
      return (v.ctx || []).join(' | ');
    };
    return {
      rare: /cube-up|tier/i.test(ctxOf('rare')),
      magic: /cube-up/i.test(ctxOf('magic')),
      crafted: /cube-up/i.test(ctxOf('crafted')),
    };
  });
  expect(r.rare).toBe(true);      // rare CAN cube-up (keeps affixes)
  expect(r.magic).toBe(false);    // magic can't — no note
  expect(r.crafted).toBe(false);  // crafted can't — no note
});
