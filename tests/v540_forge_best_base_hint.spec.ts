import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v540 — Konyo: "it's not endgame gear for the user, just for merc." When you make a runeword on a 2H base you
// OWN, that's a MERCENARY weapon — but the ideal PLAYER version is a 1H base. The Make-now card now surfaces the
// best/ideal base per runeword (it was in the data — t.bestStr/t.bestMeta — just not rendered on owned-base cards),
// so the merc-vs-player distinction is spelled out and the endgame isn't framed as "only merc gear".

test('a merc-owned Make-now card shows the "best base" (ideal 1H player) hint', async ({ page }) => {
  await page.addInitScript(() => {
    // v576 gated BotD-on-Grim-Scythe (endgame word needs an elite/ideal base). The merc-own hint case now
    // uses the CHEAP v501 classic: Honor in an owned 5os Zweihander (2H sword → merc-own rescue).
    localStorage.setItem('d2r_owned', JSON.stringify(['Zweihander (5os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 1, El: 1, Ith: 1, Tir: 1, Sol: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Zweihander (5os)');
    w.switchTab('forge'); w.forgeSetFilter('now'); w.renderForge();
    const f = document.getElementById('tab-forge')!;
    const card = [...f.querySelectorAll('.forge-sec-now .f-card.f-now')].find((c) => /Honor/.test(c.textContent || ''));
    const txt = card ? (card.textContent || '').replace(/\s+/g, ' ') : '';
    return {
      hasCard: !!card,
      isMerc: /mercenary/i.test(txt),
      hasBestBase: /best base/i.test(txt),
      namesPlayerBase: /Scourge|Ettin Axe|Phase Blade|Berserker Axe|War Spike/.test(txt),   // 5os word → 5os-max 1H ideals
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
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
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
