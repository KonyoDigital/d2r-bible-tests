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

/* v2094 MOVED THE ROOM, NOT THE DEFECT. Crafts left #tab-forge for #tab-crafts, and the chronicle
   room no longer sees them at all: renderForge('crafts') writes into #crafts-body and blanks
   now/pipeline/onestep/farm/ladder, while the default render blanks crafts/craftOnestep/craftTypes
   (bible.html:37969-37970), and the ⚗️ section is gated `if (_isCrafts && …)` (bible.html:38520).
   So #forge-body is CORRECTLY empty of crafts now and measuring it would assert nothing.
   BOTH render sites moved with the crafts and both still exist inside the one room — the
   convenience accordion at bible.html:38378 and the dedicated ⚗️ section at bible.html:38543 —
   so the double-draw this file exists for is still possible, just one tab to the right. */
test('no craft type draws its accordion twice on the default ALL view', async ({ page }) => {
  await seedFullStash(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab && w.switchTab('crafts'); } catch (e) {}
    try { w.renderCrafts && w.renderCrafts(); } catch (e) {}
    const body = document.getElementById('crafts-body');
    /* WAS `querySelectorAll('summary')`, WHICH MATCHED NOTHING. _craftAccHtml builds its header as
       `<div class="f-craftacc-h" role="button">` with the title in `.f-craftacc-name`
       (bible.html:37899-37901) — there is not one <summary> element in the craft feed, so `heads`
       was always {} and the `dup` assertion below could never fail. The file's own header names
       the evidence it is supposed to catch — "Create Caster", "Create Blood", each drawn twice —
       and that is exactly what .f-craftacc-name holds. [[regression-guard]] */
    const heads: Record<string, number> = {};
    Array.from(body ? body.querySelectorAll('.f-craftacc-name') : []).forEach((el) => {
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
    try { w.switchTab && w.switchTab('crafts'); } catch (e) {}
    // v2094 — the crafts room keeps its OWN chip state in _craftsFilter, so the filter call has to
    // name the scope; forgeSetFilter('now') with no scope writes the CHRONICLE's chip instead and
    // leaves this room on ▦ All, where the ⚗️ section renders and the assertion below means nothing.
    try { w.forgeSetFilter && w.forgeSetFilter('now', 'crafts'); } catch (e) {}
    const body = document.getElementById('crafts-body');
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
    try { w.switchTab && w.switchTab('crafts'); } catch (e) {}   // v2094 — craft cards live here now
    try { w.renderCrafts && w.renderCrafts(); } catch (e) {}
    /* v2094 — the sibling has to come from the CHRONICLE room now. renderForge('crafts') blanks
       now/pipeline/onestep, so there is no .f-now/.f-pipe/.f-step in #crafts-body and a same-room
       lookup would leave `sibling` null forever — the comparison below would stop running without
       ever going red. [[regression-guard]] The rail rules are one shared stylesheet scoped
       `:is(#tab-forge,#tab-crafts,#tab-funi,#tab-fsets)`, so reading across the two rooms compares
       the same declarations. #forge-body is a static element, so rendering it while the Crafts tab
       is the active one still fills it; border-left-color resolves under display:none. */
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const body = document.getElementById('crafts-body');
    const chron = document.getElementById('forge-body');
    const el = body ? body.querySelector('.f-card.f-craft') : null;
    const step = chron ? chron.querySelector('.f-card.f-step, .f-card.f-now, .f-card.f-pipe') : null;
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
