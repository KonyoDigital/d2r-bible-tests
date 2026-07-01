import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v540 — Konyo: "it's not endgame gear for the user, just for merc." When you make a runeword on a 2H base you
// OWN, that's a MERCENARY weapon — but the ideal PLAYER version is a 1H base. The Make-now card now surfaces the
// best/ideal base per runeword (it was in the data — t.bestStr/t.bestMeta — just not rendered on owned-base cards),
// so the merc-vs-player distinction is spelled out and the endgame isn't framed as "only merc gear".

test('a merc-owned Make-now card shows the "best base" (ideal 1H player) hint', async ({ page }) => {
  await page.addInitScript(() => {
    // Grim Scythe (6os, 2H polearm → merc) + Breath of the Dying runes (Vex+Hel+El+Eld+Zod+Eth)
    localStorage.setItem('d2r_owned', JSON.stringify(['Grim Scythe (6os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Vex: 1, Hel: 1, El: 1, Eld: 1, Zod: 1, Eth: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Grim Scythe (6os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    const card = [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].find((c) => /Breath of the Dying/.test(c.textContent || ''));
    const txt = card ? (card.textContent || '').replace(/\s+/g, ' ') : '';
    return {
      hasCard: !!card,
      isMerc: /mercenary/i.test(txt),
      hasBestBase: /best base/i.test(txt),
      namesPlayerBase: /Phase Blade|War Spike|Berserker Axe/.test(txt),
      says1HPlayer: /1H player|ideal is a .*player/i.test(txt),
    };
  });
  expect(r.hasCard).toBe(true);
  expect(r.isMerc).toBe(true);          // still correctly a merc weapon (you own the 2H base)
  expect(r.hasBestBase).toBe(true);     // …but the card now names the best/ideal base
  expect(r.namesPlayerBase).toBe(true); // …a 1H player weapon
  expect(r.says1HPlayer).toBe(true);    // …spelled out as the player version
});

test('when you own the IDEAL base, no redundant best-base hint is shown', async ({ page }) => {
  // Insight on a socket-correct Colossus Voulge is itself the meta base → don't nag with a "best base" line.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    const card = [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].find((c) => /Insight/.test(c.textContent || ''));
    return { hasCard: !!card, hasBestBase: card ? /best base/i.test(card.textContent || '') : false };
  });
  expect(r.hasCard).toBe(true);
  // Colossus Voulge IS the Insight meta base → no redundant hint
  expect(r.hasBestBase).toBe(false);
});
