import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2081 — TWO DEFECTS HE SAW AND NO CHECK DID.
// Konyo: "IN FORGE tab the caster forging caster and blood etc.. its messy it wasnt like this at
// peak polish". Both were measured on a real render with a full rune+gem stash before either was
// touched, and both are independent of moving crafts to their own tab.
//
//   1. EVERY CRAFT TYPE DREW TWICE on the default ▦ All view. The convenience accordion under
//      ⚒ Make now and the dedicated ⚗️ Crafts section both call _craftAccHtml for the same types,
//      and the ⚗️ section renders whenever show('crafts') || show('all') — which includes All.
//      Measured: 4 craft types, 8 accordions, all four headers duplicated, each with all 9 slots.
//   2. CRAFT CARDS HAD NO RAIL. .f-now/.f-pipe/.f-step each carry a meaning-bearing
//      border-left-color; .f-craft had NO RULE and fell back to var(--border) rgb(58,47,30).
//      Guarded structurally in visual_lock_invariant.py too; this is the rendered half.
//
// VENUE: a browser spec. It runs on GitHub CI, never on his Mac. [[test-venue]]

async function seedFullStash(page: any) {
  await page.addInitScript(() => {
    const runes: any = {};
    ['Ral','Ort','Tal','Amn','Sol','Shael','Dol','Hel','Io','Lum','Ko','Fal','Lem','Pul','Um',
     'Mal','Ist','Gul','Vex','Ohm','Lo','Sur','Ber','Jah','Cham','Zod','Eld','Nef','Eth','Ith',
     'Tir','Thul'].forEach((r) => { runes[r] = 5; });
    const gems: any = {};
    ['Perfect Amethyst','Perfect Ruby','Perfect Emerald','Perfect Sapphire','Perfect Diamond',
     'Perfect Topaz','Perfect Skull'].forEach((g) => { gems[g] = 5; });
    localStorage.setItem('d2r_runeStash', JSON.stringify(runes));
    localStorage.setItem('d2r_gemStash', JSON.stringify(gems));
  });
}

test('the fixture really makes crafts READY, or nothing below means anything', async ({ page }) => {
  await seedFullStash(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const n = await page.evaluate(() => {
    const w: any = window;
    const s = (typeof w.forgeScan === 'function') ? w.forgeScan() : null;
    return s ? (s.crafts || []).length : 0;
  });
  // with every rune and every perfect gem in the stash, every craft slot clears gemReady && hasRune
  expect(n).toBeGreaterThan(0);
});

test('no craft type draws its accordion twice on the default ALL view', async ({ page }) => {
  await seedFullStash(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const body = document.getElementById('forge-body');
    const heads: Record<string, number> = {};
    Array.from(body ? body.querySelectorAll('summary') : []).forEach((el) => {
      const k = (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 24);
      if (k) heads[k] = (heads[k] || 0) + 1;
    });
    return {
      containers: body ? body.querySelectorAll('.forge-craftacc').length : -1,
      accordions: body ? body.querySelectorAll('.f-craftacc').length : -1,
      types: (typeof w.CRAFTS !== 'undefined' && w.CRAFTS) ? w.CRAFTS.length : -1,
      dup: Object.keys(heads).filter((k) => heads[k] > 1),
    };
  });
  expect(r.dup, `these accordion headers are drawn more than once: ${r.dup.join(' | ')}`).toEqual([]);
  expect(r.containers, 'two .forge-craftacc containers means both sites rendered').toBe(1);
  // one accordion per craft type, not two
  expect(r.accordions).toBe(r.types);
});

test('the ⚒ Make-now filter KEEPS its convenience accordion', async ({ page }) => {
  // the mirror: fixing the duplicate must not delete the one place it earns its keep, where the
  // ⚗️ section does not render at all.
  await seedFullStash(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const n = await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.forgeSetFilter && w.forgeSetFilter('now'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const body = document.getElementById('forge-body');
    return body ? body.querySelectorAll('.forge-craftacc').length : -1;
  });
  expect(n, 'the ⚒ filter lost the craft accordion — the ⚗️ section does not render here').toBe(1);
});

test('a cube craft card carries a rail colour, like every other card kind', async ({ page }) => {
  await seedFullStash(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const body = document.getElementById('forge-body');
    const el = body ? body.querySelector('.f-card.f-craft') : null;
    const step = body ? body.querySelector('.f-card.f-step, .f-card.f-now, .f-card.f-pipe') : null;
    return {
      craft: el ? getComputedStyle(el).borderLeftColor : null,
      sibling: step ? getComputedStyle(step).borderLeftColor : null,
    };
  });
  expect(r.craft, 'no craft card rendered — the fixture is wrong, not the page').not.toBeNull();
  // rgb(58,47,30) is var(--border): the fallback a card gets when NOTHING styles its kind
  expect(r.craft, 'the craft card fell back to var(--border) — its colour says nothing')
    .not.toBe('rgb(58, 47, 30)');
  if (r.sibling) expect(r.craft).not.toBe(r.sibling);
});
