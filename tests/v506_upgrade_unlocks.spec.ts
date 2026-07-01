import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v534 — CORRECTION of the old v506 "upgrade" tests. Game-file cubemain.txt proves white / normal / superior
// bases CANNOT be cube-upgraded to a higher tier (only unique/rare/set can). So there is NO "base upgrade"
// task. A low-tier white base whose max sockets can't reach an endgame word does NOT produce an upgrade — the
// word surfaces as a "🛒 get the right base" one-step naming the elite base to find. These lock that in.

test('a Normal white base produces NO upgrade task; _upgradeChainFor is a null stub', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Bone Helm (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Bone Helm (Larzuk base)');
    const s = w.forgeScan();
    return {
      upgrades: s.upgrades.length,
      chain: (typeof w._upgradeChainFor === 'function') ? w._upgradeChainFor('Bone Helm', 3, false) : 'no fn',
    };
  });
  expect(r.upgrades).toBe(0);     // no upgrade bucket exists anymore
  expect(r.chain).toBeNull();     // white bases can't be cube-upgraded
});

test('an endgame word needing a higher-socket ELITE base → "get the right base" one-step (Delirium → elite helm)', async ({ page }) => {
  // Delirium = Lem+Ist+Io (3 socket helm). A Bone Helm maxes at 2 sockets → can't hold it; you must FIND the
  // elite (Bone Visage, 3os max). With the runes in hand and no base owned, that's a sub:'base' one-step.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Lem: 1, Ist: 1, Io: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    const s = w.forgeScan();
    const t = s.onestep.find((x: any) => x.rw === 'Delirium');
    return { found: !!t, sub: t && t.sub, bestStr: t && t.bestStr };
  });
  expect(r.found).toBe(true);
  expect(r.sub).toBe('base');                       // "go get the base" — not an upgrade
  expect(/Bone Visage|Spired Helm|Corona|Demonhead|Conqueror Crown/.test(r.bestStr || '')).toBe(true); // names an elite helm to find
});

test('owning the ELITE base + runes → a real Make-now / Pipeline task (endgame still works)', async ({ page }) => {
  // The endgame path is unchanged: own the socket-correct elite base + runes → forge it.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));   // Insight base, exact 4os
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    const s = w.forgeScan();
    return { madeNow: s.now.some((t: any) => t.rw === 'Insight' && !t.deferred) };
  });
  expect(r.madeNow).toBe(true);   // endgame forge task intact
});
