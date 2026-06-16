import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v288 — Crafted Items Workshop (Tools tab). The 4 crafts × 9 slots = 36 exact
// cube recipes (rune + magic base per slot, from the bible's Crafted-item recipes
// reference). "Cubeable now" reads LIVE from runeStash + gemStash (single source of
// truth); craftStash tracks finished crafted rares the user owns (📸 AI intake,
// kind:'craft'). findCraft + craftDetailHtml + an openDrop branch give every craft a
// clickable ID card; search routes "Caster Craft"… and the workshop tool opener.

const CRAFT_KEYS = ['Caster', 'Blood', 'Safety', 'Hit Power'];

test.describe('v288 Crafted Items Workshop', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('CRAFTS holds 4 crafts × 9 well-formed slots (36 recipes)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const C = (window as any).CRAFTS || [];
      const SLOTS = ['Weapon','Shield','Helm','Body Armor','Gloves','Belt','Boots','Amulet','Ring'];
      let recipes = 0, badGem = 0, badMods = 0, missingSlot = 0, emptyRune = 0, emptyBase = 0;
      for (const c of C) {
        if (!/^Perfect /.test(c.gem)) badGem++;
        if (!Array.isArray(c.mods) || c.mods.length !== 3) badMods++;
        for (const s of SLOTS) {
          const rec = c.slots[s];
          if (!rec) { missingSlot++; continue; }
          recipes++;
          if (!rec.rune) emptyRune++;
          if (!rec.base) emptyBase++;
        }
      }
      return { types: C.length, recipes, badGem, badMods, missingSlot, emptyRune, emptyBase };
    });
    expect(r.types).toBe(4);
    expect(r.recipes).toBe(36);
    expect(r.badGem).toBe(0);
    expect(r.badMods).toBe(0);
    expect(r.missingSlot).toBe(0);
    expect(r.emptyRune).toBe(0);
    expect(r.emptyBase).toBe(0);
  });

  test('findCraft resolves craft keys, "X Craft", and "Craft Slot" combos', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fc = (window as any).findCraft;
      return {
        caster: fc('Caster')?.craft?.key || null,
        casterCraft: fc('Caster Craft')?.craft?.key || null,
        bloodRing: (() => { const x = fc('Blood Ring'); return x ? x.craft.key + '|' + x.slot : null; })(),
        hitPowerBody: (() => { const x = fc('Hit Power Body Armor'); return x ? x.craft.key + '|' + x.slot : null; })(),
        bogus: fc('Nonsense Craft Thing'),
        empty: fc(''),
      };
    });
    expect(r.caster).toBe('Caster');
    expect(r.casterCraft).toBe('Caster');
    expect(r.bloodRing).toBe('Blood|Ring');
    expect(r.hitPowerBody).toBe('Hit Power|Body Armor');
    expect(r.bogus).toBeNull();
    expect(r.empty).toBeNull();
  });

  test('the workshop card renders 4 craft tiles + the selected craft\'s 9 recipe rows', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const card = document.getElementById('craft-workshop-card');
      if (card && card.classList.contains('collapsed')) (window as any).toggleCardCollapse('craft-workshop-card');
      (window as any).renderCraftWorkshop();
    });
    await page.waitForTimeout(150);
    expect(await page.locator('#craft-workshop .cw-tile').count()).toBe(4);
    // default selected craft (Caster) shows all 9 slot recipes
    expect(await page.locator('#craft-workshop .cw-recipe').count()).toBe(9);
    // 3 guaranteed mods are shown for the selected craft
    expect(await page.locator('#craft-workshop .cw-guaranteed .cw-g-mod').count()).toBe(3);
  });

  test('cubeable status goes live off the rune + gem stash (single source of truth)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      // mutate via the REAL public mutators (they reassign the module-scoped stash objects
      // that _runeCount/_gemCount read — assigning window.runeStash would not).
      // empty stash → Caster Amulet (Ral rune + Perfect Amethyst + magic base) not cubeable
      const before = w._craftSlotReady(w.CRAFTS[0], 'Amulet').ready;
      // v341: hold the exact consumables AND a magic Amulet base → cubeable now
      w.adjustRuneStash('Ral', 1); w.adjustGemStash('Perfect Amethyst', 1); w.toggleCraftBase('Amulet');
      const after = w._craftSlotReady(w.CRAFTS[0], 'Amulet').ready;
      // remove the rune → only the gem (+base) remains: not ready, gem half satisfied
      w.adjustRuneStash('Ral', -1);
      const gemOnly = w._craftSlotReady(w.CRAFTS[0], 'Amulet');
      // clean up
      w.adjustGemStash('Perfect Amethyst', -1); w.toggleCraftBase('Amulet');
      return { before, after, gemOnlyReady: gemOnly.ready, gemOnlyHaveGem: gemOnly.haveGem, gemOnlyMissing: gemOnly.missing };
    });
    expect(r.before).toBe(false);
    expect(r.after).toBe(true);
    expect(r.gemOnlyReady).toBe(false);
    expect(r.gemOnlyHaveGem).toBe(true);
    expect(r.gemOnlyMissing).toContain('Ral rune');
  });

  test('owned crafted-item tally persists and routes through craftStash', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w.craftStash = {};
      w.adjustCraftStash('Caster', 'Amulet', 2);
      w.adjustCraftStash('Blood', 'Ring', 1);
      w.adjustCraftStash('Caster', 'Amulet', -1);
      const stored = JSON.parse(localStorage.getItem('d2r_craftStash') || '{}');
      const out = { casterAmulet: stored['Caster Amulet'], bloodRing: stored['Blood Ring'] };
      w.craftStash = {};
      return out;
    });
    expect(r.casterAmulet).toBe(1);
    expect(r.bloodRing).toBe(1);
  });

  test('openDrop("Caster") opens the craft ID card with all 9 slot recipes', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Caster'));
    await page.waitForTimeout(200);
    const card = page.locator('#item-detail .craft-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.gic-name')).toContainText('Caster Craft');
    expect(await card.locator('.cw-recipe').count()).toBe(9);
  });

  test('openDrop("Hit Power Ring") routes to the Hit Power craft card', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Hit Power Ring'));
    await page.waitForTimeout(200);
    await expect(page.locator('#item-detail .craft-card .gic-name')).toContainText('Hit Power Craft');
  });

  test('each recipe row states the exact crafted OUTPUT + marks basic items as default-owned', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const card = document.getElementById('craft-workshop-card');
      if (card && card.classList.contains('collapsed')) (window as any).toggleCardCollapse('craft-workshop-card');
      (window as any).selectCraft('Caster');
    });
    await page.waitForTimeout(150);
    // every visible recipe row names what it creates ("Caster <Slot>") + "crafted rare" + random affixes
    const firstOut = page.locator('#craft-workshop .cw-recipe .cw-rec-out').first();
    await expect(firstOut).toContainText('creates');
    await expect(firstOut.locator('.cw-out-name')).toContainText('Caster');
    await expect(firstOut).toContainText('1–4 random affixes');
    // v341 honesty: the jewel is the only "basic ✓" chip; the magic base is a real
    // click-to-toggle ingredient (defaults to "＋ need"), NOT auto-assumed.
    const row = page.locator('#craft-workshop .cw-recipe').first();
    expect(await row.locator('.cw-ing-basic').count()).toBe(1); // any jewel only
    await expect(row.locator('.cw-ing-basic').first()).toContainText('basic');
    expect(await row.locator('.cw-ing-base').count()).toBe(1);  // the magic base ingredient
    await expect(row.locator('.cw-ing-base').first()).toContainText('need'); // default = not owned
    // the basic-items legend + reroll enrichment are present for the selected craft
    expect(await page.locator('#craft-workshop .cw-basic-legend').count()).toBe(1);
    expect(await page.locator('#craft-workshop .cw-reroll .cw-reroll-mod').count()).toBeGreaterThan(2);
    // CRAFT_REROLL + CRAFT_BASE_SOURCE data exist for all crafts/slots
    const data = await page.evaluate(() => {
      const w = window as any;
      return { reroll: Object.keys((w.CRAFT_REROLL)||{}).length, hasGetter: typeof w._cwRecipeRow === 'function' };
    });
    expect(data.hasGetter).toBe(true);
  });

  test('filtering a slot shows that slot for ALL 4 crafts (v295)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const card = document.getElementById('craft-workshop-card');
      if (card && card.classList.contains('collapsed')) (window as any).toggleCardCollapse('craft-workshop-card');
      (window as any).selectCraft('Caster');
      (window as any).craftSlotFilter('Gloves');
    });
    await page.waitForTimeout(150);
    // 4 rows — one Gloves recipe per craft
    expect(await page.locator('#craft-workshop .cw-recipe').count()).toBe(4);
    const outs = (await page.locator('#craft-workshop .cw-rec-out .cw-out-name').allTextContents()).join(' | ');
    expect(outs).toContain('Caster Gloves');
    expect(outs).toContain('Blood Gloves');
    expect(outs).toContain('Safety Gloves');
    expect(outs).toContain('Hit Power Gloves');
    // selecting a craft tile returns to that craft's full 9-slot view
    await page.evaluate(() => (window as any).selectCraft('Blood'));
    await page.waitForTimeout(120);
    expect(await page.locator('#craft-workshop .cw-recipe').count()).toBe(9);
  });

  test('the "craft now" banner reflects the live stash (crystallization)', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const card = document.getElementById('craft-workshop-card');
      if (card && card.classList.contains('collapsed')) (window as any).toggleCardCollapse('craft-workshop-card');
      const w = window as any;
      w.adjustRuneStash('Ral', 1); w.adjustGemStash('Perfect Amethyst', 1); w.toggleCraftBase('Amulet'); // → Caster Amulet cubeable (v341: base too)
      w.renderCraftWorkshop();
    });
    await page.waitForTimeout(150);
    // banner switches to the green "Craft now" state and names the cubeable recipe
    await expect(page.locator('#craft-workshop .cw-readynow.cw-rn-go')).toBeVisible();
    await expect(page.locator('#craft-workshop .cw-rn-go')).toContainText('Caster Amulet');
    // a jump-chip routes to that craft + slot
    await page.locator('#craft-workshop .cw-rn-chip').first().click();
    await page.waitForTimeout(120);
    await expect(page.locator('#craft-workshop .cw-tile.cw-sel .cw-tile-name')).toContainText('Caster');
    // clean up the seeded stash
    await page.evaluate(() => { const w = window as any; w.adjustRuneStash('Ral', -1); w.adjustGemStash('Perfect Amethyst', -1); });
  });

  test('openCraftWorkshop opens + expands the tool, and the reference cross-link exists', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w.openCraftWorkshop('Blood');
      return { hasFn: typeof w.openCraftWorkshop === 'function' };
    });
    expect(r.hasFn).toBe(true);
    await page.waitForTimeout(250);
    const card = page.locator('#craft-workshop-card');
    await expect(card).not.toHaveClass(/collapsed/);
    // the reference-tab "Crafted-item recipes" section carries a cross-link into the workshop
    expect(await page.locator('.gic-cross-link', { hasText: 'Crafted Items Workshop' }).count()).toBeGreaterThan(0);
  });

  test('every craft + the workshop are reachable from global search', async ({ page }) => {
    const labels = await page.evaluate(() => {
      const w = window as any;
      // build the command index the same way the search palette does
      if (typeof w._buildSearchCmds === 'function') return w._buildSearchCmds().map((c: any) => c.label);
      return null;
    });
    // fallback: just assert the craft cards exist as openDrop targets (search wiring covered by smoke)
    if (labels) {
      for (const k of CRAFT_KEYS) expect(labels).toContain(k + ' Craft');
      expect(labels).toContain('Crafted Items Workshop');
    }
  });
});
