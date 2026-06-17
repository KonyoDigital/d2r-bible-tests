import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v70 — Materials Stash & Uber Planner (events tab). Same architecture as the v67/v68
// rune stash: a pure tally of the user's Pandemonium keys / uber organs / Token essences /
// Worldstone Shards / Sunder charms, read LIVE from SPECIAL_DROPS (zero fabricated data),
// driving a "what can I make" readiness panel for the three clean cube goals (open an uber
// portal, run Uber Tristram → Hellfire Torch, cube a Token of Absolution). Collapsible card,
// tally import, localStorage persistence, and rides the Backup & Share export.
test.describe('v70 material stash + uber planner', () => {
  test.beforeEach(async ({ page }) => {
    page.on('dialog', (d) => d.accept());
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.evaluate(() => { try { localStorage.removeItem('d2r_materialStash'); } catch (e) {} });
    await page.reload();
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(150);
  });

  test('MATERIALS + recipes are derived live from SPECIAL_DROPS, with all helper fns exposed', async ({ page }) => {
    const r = await page.evaluate(() => {
      const M = (window as any).MATERIALS as any[];
      const R = (window as any).MATERIAL_RECIPES as any[];
      const SD = (window as any).SPECIAL_DROPS || (SPECIAL_DROPS as any);
      // every material name must come straight from a SPECIAL_DROPS item (no fabrication)
      const allSdNames = new Set<string>();
      ['key', 'organ', 'essence', 'token', 'rejuv', 'worldstoneShard', 'sunder'].forEach((c) => (SD[c]?.items || []).forEach((i: any) => allSdNames.add(i.n)));
      // every recipe ingredient must be a real tracked material; the category-based
      // recipes (needCat) reference a SPECIAL_DROPS category rather than named items.
      const matNames = new Set(M.map((m) => m.n));
      const recipeKeysValid = R.every((rc) => rc.need
        ? Object.keys(rc.need).every((n) => matNames.has(n))
        : Array.isArray(rc.needCat) && rc.needCat.every((c: any) => c.key in SD));
      return {
        len: M.length,
        allFromSd: M.every((m) => allSdNames.has(m.n)),
        cats: [...new Set(M.map((m) => m.cat))],
        recipeNames: R.map((x) => x.n),
        recipeKeysValid,
        fns: ['adjustMaterialStash', 'clearMaterialStash', 'canMakeMaterial', 'materialMissing', 'materialCraftStatus', 'renderMaterialStash', 'renderMaterialCraftable', 'importMaterialTally', 'toggleCardCollapse']
          .map((n) => typeof (window as any)[n]),
      };
    });
    expect(r.len).toBe(24);                       // 3 keys + 3 organs + 4 essences + 1 token + 2 rejuv + 5 shards + 6 sunders (v280: mirror in-game Materials tab)
    expect(r.allFromSd).toBe(true);
    expect(r.cats).toEqual(['Pandemonium Keys', 'Uber Organs', 'Essences', 'Token of Absolution', 'Rejuvenation Potions', 'Worldstone Shards', 'Sunder Charms']);
    expect(r.recipeNames).toEqual(['Pandemonium Portal', 'Uber Tristram', 'Token of Absolution', 'Latent Sunder (cube 3 shards)', 'Renewed Sunder (upgrade a Latent)']);
    expect(r.recipeKeysValid).toBe(true);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
  });

  test('the card is collapsible: starts title-only, header click expands and re-collapses', async ({ page }) => {
    const card = page.locator('#material-stash-card');
    await expect(card).toHaveClass(/collapsed/);
    expect(await page.locator('#material-stash-card .boss-body').isVisible()).toBe(false);
    await page.click('#material-stash-card .boss-header');
    await page.waitForTimeout(120);
    await expect(card).not.toHaveClass(/collapsed/);
    expect(await page.locator('#material-stash-card .boss-body').isVisible()).toBe(true);
    expect(await page.getAttribute('#material-stash-card .boss-header', 'aria-expanded')).toBe('true');
    await page.click('#material-stash-card .boss-header');
    await page.waitForTimeout(120);
    await expect(card).toHaveClass(/collapsed/);
  });

  test('adjusting a counter persists to localStorage and floors at zero', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).adjustMaterialStash('Key of Terror', 1);
      (window as any).adjustMaterialStash('Key of Terror', 1);
      const afterPlus = JSON.parse(localStorage.getItem('d2r_materialStash') || '{}')['Key of Terror'];
      const shownPlus = (document.querySelector('.rs-count[data-material-count="Key of Terror"]') as HTMLElement).textContent!.trim();
      (window as any).adjustMaterialStash('Key of Terror', -1);
      (window as any).adjustMaterialStash('Key of Terror', -1);
      (window as any).adjustMaterialStash('Key of Terror', -1);
      const afterMinus = JSON.parse(localStorage.getItem('d2r_materialStash') || '{}')['Key of Terror'];
      const shownMinus = (document.querySelector('.rs-count[data-material-count="Key of Terror"]') as HTMLElement).textContent!.trim();
      return { afterPlus, shownPlus, afterMinus, shownMinus };
    });
    expect(r.afterPlus).toBe(2);
    expect(r.shownPlus).toBe('2');
    expect(r.afterMinus).toBeUndefined();
    expect(r.shownMinus).toBe('0');
  });

  test('readiness is honest: Uber Tristram needs all 3 organs, Token all 4 essences, portal 1 of each key', async ({ page }) => {
    const r = await page.evaluate(() => {
      const status0 = (window as any).materialCraftStatus();
      // give exactly the 3 organs → Uber Tristram ready, others not
      (window as any).adjustMaterialStash("Diablo's Horn", 1);
      (window as any).adjustMaterialStash("Mephisto's Brain", 1);
      (window as any).adjustMaterialStash("Baal's Eye", 1);
      const trist = (window as any).canMakeMaterial({ "Diablo's Horn": 1, "Mephisto's Brain": 1, "Baal's Eye": 1 });
      // 2 of the 3 keys → portal NOT ready yet (missing 1)
      (window as any).adjustMaterialStash('Key of Terror', 1);
      (window as any).adjustMaterialStash('Key of Hate', 1);
      const portalPartial = (window as any).canMakeMaterial({ 'Key of Terror': 1, 'Key of Hate': 1, 'Key of Destruction': 1 });
      const missing = (window as any).materialMissing({ 'Key of Terror': 1, 'Key of Hate': 1, 'Key of Destruction': 1 });
      (window as any).adjustMaterialStash('Key of Destruction', 1);
      const portalFull = (window as any).canMakeMaterial({ 'Key of Terror': 1, 'Key of Hate': 1, 'Key of Destruction': 1 });
      const status = (window as any).materialCraftStatus();
      return {
        noneReadyAtStart: status0.every((s: any) => !s.ready),
        trist, portalPartial, portalFull,
        missingDest: missing['Key of Destruction'],
        readyNames: status.filter((s: any) => s.ready).map((s: any) => s.recipe.n),
      };
    });
    expect(r.noneReadyAtStart).toBe(true);
    expect(r.trist).toBe(true);
    expect(r.portalPartial).toBe(false);
    expect(r.missingDest).toBe(1);
    expect(r.portalFull).toBe(true);
    expect(r.readyNames).toContain('Uber Tristram');
    expect(r.readyNames).toContain('Pandemonium Portal');
    expect(r.readyNames).not.toContain('Token of Absolution');
  });

  test('the planner DOM shows ready vs needed lines and the X/5 header count', async ({ page }) => {
    await page.click('#material-stash-card .boss-header');
    const r = await page.evaluate(() => {
      ['Essence of Suffering', 'Essence of Hatred', 'Essence of Terror', 'Essence of Destruction']
        .forEach((n) => (window as any).adjustMaterialStash(n, 1));
      const box = document.getElementById('material-craftable') as HTMLElement;
      const tokenRow = box.querySelector('.rw-row[data-recipe="Token of Absolution"]') as HTMLElement;
      const tristRow = box.querySelector('.rw-row[data-recipe="Uber Tristram"]') as HTMLElement;
      return {
        head: box.querySelector('.rw-make-head')!.textContent,
        tokenReady: tokenRow.className.includes('rw-ready'),
        tokenText: tokenRow.querySelector('.rw-recipe')!.textContent!.trim(),
        tristText: tristRow.querySelector('.rw-recipe')!.textContent!.trim(),
      };
    });
    expect(r.head).toMatch(/1\/5/);                     // only Token ready (of 5 recipes)
    expect(r.tokenReady).toBe(true);
    expect(r.tokenText).toMatch(/ready now/);
    expect(r.tristText).toMatch(/need .*Horn/);          // still missing organs
  });

  test('importing a tally writes counts (mixed case + apostrophes + shards) and persists', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ta = document.getElementById('material-import-box') as HTMLTextAreaElement;
      ta.value = "Key of Terror: 3\ndiablo's horn = 1\nWorldstone Shard (Western): 2\nEssence of Hatred 4";
      (window as any).importMaterialTally();
      const saved = JSON.parse(localStorage.getItem('d2r_materialStash') || '{}');
      const status = (document.getElementById('material-import-status') as HTMLElement).textContent || '';
      const junk = (window as any).importMaterialTally; // fn still defined
      return { saved, status, junkType: typeof junk };
    });
    expect(r.saved['Key of Terror']).toBe(3);
    expect(r.saved["Diablo's Horn"]).toBe(1);            // lowercase normalised to canonical
    expect(r.saved['Worldstone Shard (Western)']).toBe(2);
    expect(r.saved['Essence of Hatred']).toBe(4);
    expect(r.status.toLowerCase()).toMatch(/loaded/);
    expect(r.junkType).toBe('function');
  });

  test('material stash rides along in the Backup & Share export', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).adjustMaterialStash("Baal's Eye", 2);
      (window as any).exportProgress();
      const ta = document.getElementById('backup-textarea') as HTMLTextAreaElement;
      const parsed = JSON.parse(ta.value);
      const stash = JSON.parse(parsed.data['d2r_materialStash'] || '{}');
      return { hasKey: 'd2r_materialStash' in parsed.data, eye: stash["Baal's Eye"] };
    });
    expect(r.hasKey).toBe(true);
    expect(r.eye).toBe(2);
  });

  test('no console errors across the material craft + collapse + import flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tools"]');
    await page.click('#material-stash-card .boss-header');
    await page.evaluate(() => {
      const ta = document.getElementById('material-import-box') as HTMLTextAreaElement;
      ta.value = "Key of Hate:2 Mephisto's Brain:1 Worldstone Shard (Deep):1";
      (window as any).importMaterialTally();
      (window as any).renderMaterialStash();
    });
    await page.waitForTimeout(120);
    expect(errors).toEqual([]);
  });
});
