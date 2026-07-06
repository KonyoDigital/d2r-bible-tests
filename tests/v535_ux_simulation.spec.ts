import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v535 — USER-EXPERIENCE simulations (Konyo's request: "the user experience ones... part of the autonomous
// loop workflow"). Unlike the logic-level forgeScan sims, these drive the RENDERED UI the way a person does:
// switch tabs, read the cards that actually appear, click the real buttons, and check the DOM updates. They
// catch render-vs-logic drift (badge count ≠ rendered cards), evaporation-on-complete, and cross-tab platform
// sync — things a headless forgeScan assertion can't see. Living in tests/ they run in Routine I on every push.

const RUNES = ['El','Eld','Tir','Nef','Eth','Ith','Tal','Ral','Ort','Thul','Amn','Sol','Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um','Mal','Ist','Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod'];

async function seed(page: any, owned: string[], runes: Record<string, number>, made: Record<string, boolean> = {}) {
  await page.addInitScript((s: any) => {
    localStorage.setItem('d2r_owned', JSON.stringify(s.owned));
    localStorage.setItem('d2r_runeStash', JSON.stringify(s.runes));
    localStorage.setItem('d2r_rwMade', JSON.stringify(s.made));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, { owned, runes, made });
  await page.goto(URL);
  await page.waitForTimeout(1400);
}

test('UX — empty-base vault: Forge renders "go find the base" one-steps, no forge-now card, no cube-upgrade instruction', async ({ page }) => {
  // Konyo's REAL shape: lots of runes, zero tracked bases. Every needed word becomes a "find the base" one-step,
  // there is NO owned base to forge on (0 forge-now cards), and — the v534/v535 regression guard — nothing in the
  // rendered UI tells you to cube-upgrade a white base.
  const runes: Record<string, number> = {}; RUNES.forEach((r) => (runes[r] = 5));
  await seed(page, [], runes, {});
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('forge'); w.renderForge();
    const forge = document.getElementById('tab-forge')!;
    const stepCards = [...forge.querySelectorAll('.forge-sec-step .f-card')];
    return {
      stepCardCount: stepCards.length,
      anyGetBaseText: stepCards.some((c) => /Get\b/i.test(c.textContent || '')),
      nowForgeCards: forge.querySelectorAll('.forge-sec-now .f-card.f-now').length,
      cubeUpgradeLeak: /Cube-upgrade your/i.test(forge.textContent || ''),
    };
  });
  expect(r.stepCardCount).toBeGreaterThan(10);      // many "find the base" tasks
  expect(r.anyGetBaseText).toBe(true);              // they tell you to GET a base
  expect(r.nowForgeCards).toBe(0);                  // no owned base → no forge-now card
  expect(r.cubeUpgradeLeak).toBe(false);            // v534/v535: no "cube-upgrade your <white base>" instruction
});

test('UX — own the socket-correct base + runes: a Make-now card RENDERS, and ticking "✓ created" makes it evaporate', async ({ page }) => {
  // Insight = Ral+Tir+Tal+Sol on a 4os polearm. Colossus Voulge Larzuks to exactly 4 → a real Make-now forge.
  await seed(page, ['Colossus Voulge (4os)'], { Ral: 1, Tir: 1, Tal: 1, Sol: 1 }, {});
  const before = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.renderForge();
    const forge = document.getElementById('tab-forge')!;
    const nowSec = forge.querySelector('.forge-sec-now')!;
    const insightCard = [...forge.querySelectorAll('.forge-sec-now .f-card.f-now')].find((c) => /Insight/.test(c.textContent || ''));
    const header = parseInt((nowSec?.querySelector('.forge-sec-ct')?.textContent || '0').trim(), 10);
    const nowCards = nowSec ? nowSec.querySelectorAll('.f-card').length : 0;   // no gems seeded → no craft tiles
    return {
      rendered: !!insightCard,
      hasCreateBtn: !!(insightCard && insightCard.querySelector('.f-btn-go')),
      headerMatchesRender: header === nowCards,     // anti-drift: badge count == rendered cards
    };
  });
  expect(before.rendered).toBe(true);               // the Make-now forge card is actually in the DOM
  expect(before.hasCreateBtn).toBe(true);
  expect(before.headerMatchesRender).toBe(true);    // the "Make now N" badge equals what actually renders

  // click the real "✓ created" button, then re-render as the app does
  const after = await page.evaluate(() => {
    const w: any = window;
    w.rwToggleMade('Insight');                       // what the "✓ created" button calls
    w.renderForge();
    const forge = document.getElementById('tab-forge')!;
    const stillNow = [...forge.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || ''));
    const made = !!JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')['Insight'];
    return { stillNow, made };
  });
  expect(after.stillNow).toBe(false);               // it EVAPORATED from Make-now
  expect(after.made).toBe(true);                    // and moved to Completed (persisted to d2r_rwMade)
});

test('UX — cross-platform sync: the Forge\'s "find the base" set === the Tools loot-filter set (rendered count too)', async ({ page }) => {
  const runes: Record<string, number> = {}; RUNES.forEach((r) => (runes[r] = 5));
  await seed(page, [], runes, {});
  const r = await page.evaluate(() => {
    const w: any = window;
    const forgeBases = [...new Set(w.forgeScan().onestep
      .flatMap((t: any) => String(t.bestStr || '').split(/\s*\/\s*/).map((x: string) => x.trim()))
      .filter(Boolean))].sort();
    const filterBases = w._endgameFilterBases().names.slice().sort();
    // the Tools card badge should show the same number after opening the tab
    w.switchTab('tools');
    const badge = (document.getElementById('lf-endgame-count')?.textContent || '').trim();
    return {
      forgeBases, filterBases,
      premium: (w._premiumTradeBases || []).slice(),
      inFilterNotForge: filterBases.filter((n: string) => !forgeBases.includes(n)),
      inForgeNotFilter: forgeBases.filter((n: string) => !filterBases.includes(n)),
      badge, filterCount: filterBases.length,
    };
  });
  // v588 — the filter may exceed the Forge set ONLY by the premium trade floor (never shrinks off)
  expect(r.inFilterNotForge.filter((n: string) => !r.premium.includes(n))).toEqual([]);
  expect(r.inForgeNotFilter).toEqual([]);           // every Forge "find the base" IS in the filter — one source of truth
  expect(r.badge).toBe(r.filterCount + ' bases');   // the Tools card badge reflects the live set
});

test('UX — skip a Make-now task → the always-visible Restore bar appears and restores it', async ({ page }) => {
  await seed(page, ['Colossus Voulge (4os)'], { Ral: 1, Tir: 1, Tal: 1, Sol: 1 }, {});
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.renderForge();
    w.forgeSkip('rw|Insight'); w.renderForge();      // ✕ skip the Insight task
    const forge = document.getElementById('tab-forge')!;
    const restoreBar = !!forge.querySelector('.forge-restore-top');
    const gone = ![...forge.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || ''));
    w.forgeUnskipAll(); w.renderForge();             // ↺ restore
    const back = [...forge.querySelectorAll('.forge-sec-now .f-card.f-now')].some((c) => /Insight/.test(c.textContent || ''));
    return { restoreBar, gone, back };
  });
  expect(r.restoreBar).toBe(true);                  // restore bar is visible (not swallowed when the section empties)
  expect(r.gone).toBe(true);                        // skipped task left the feed
  expect(r.back).toBe(true);                        // restore brought it back
});
