import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v177 — Bridge B4 of the nightly maxroll gap-map: the reference tab's existing
// Crafted-item recipes block gains the EXACT per-slot recipe matrix (#craft-recipe-matrix):
// for each of the four crafts (Caster/Blood/Safety/Hit Power) the precise magic base
// + slot rune for all nine slots. All recipes are the base-game D2R cube recipes
// (Perfect gem decides the craft, the rune varies by slot) sourced from maxroll's
// Crafted Items list — VERIFIED, no fabrication. Additive: a collapsible <details>
// inside the existing Crafting section. Also folds in the v176 gambling colour fix
// (Rare/Set/Unique cells used non-existent CSS vars → now --star / --q-set / --q-unique).

test.describe('v177 Craft recipe matrix (Bridge B4)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(700);
  });

  test('the craft-recipe-matrix details exists and expands', async ({ page }) => {
    const r = await page.evaluate(() => {
      const d = document.getElementById('craft-recipe-matrix') as HTMLDetailsElement | null;
      if (!d) return { exists: false };
      const startsClosed = !d.open;
      d.open = true;
      return { exists: true, startsClosed, openAfter: d.open, tag: d.tagName };
    });
    expect(r.exists).toBe(true);
    expect(r.tag).toBe('DETAILS');
    expect(r.startsClosed).toBe(true);
    expect(r.openAfter).toBe(true);
  });

  test('all four crafts are present with their deciding perfect gem', async ({ page }) => {
    const txt = await page.evaluate(() => (document.getElementById('craft-recipe-matrix')?.textContent || '').replace(/\s+/g, ' '));
    expect(txt).toContain('Caster');
    expect(txt).toContain('Perfect Amethyst');
    expect(txt).toContain('Blood');
    expect(txt).toContain('Perfect Ruby');
    expect(txt).toContain('Safety');
    expect(txt).toContain('Perfect Emerald');
    expect(txt).toContain('Hit Power');
    expect(txt).toContain('Perfect Sapphire');
  });

  test('verified slot runes are correct (spot-check across crafts)', async ({ page }) => {
    const m = await page.evaluate(() => document.getElementById('craft-recipe-matrix') as HTMLElement);
    // Caster Amulet=Ral, Ring=Amn ; Blood Weapon=Ort, Ring=Sol ; Safety Weapon=Sol ; Hit Power Helm=Ith
    const rows = await page.$$eval('#craft-recipe-matrix tbody tr', (trs) =>
      trs.map((tr) => Array.from(tr.querySelectorAll('td')).map((td) => (td.textContent || '').trim()))
    );
    // four 9-slot tables = 36 rows
    expect(rows.length).toBe(36);
    // Caster table is first: Weapon=Tir, Amulet=Ral, Ring=Amn
    const caster = rows.slice(0, 9);
    expect(caster.find((r) => r[0] === 'Weapon')?.[1]).toBe('Tir');
    expect(caster.find((r) => r[0] === 'Amulet')?.[1]).toBe('Ral');
    expect(caster.find((r) => r[0] === 'Ring')?.[1]).toBe('Amn');
    // Blood table second: Weapon=Ort, Ring=Sol
    const blood = rows.slice(9, 18);
    expect(blood.find((r) => r[0] === 'Weapon')?.[1]).toBe('Ort');
    expect(blood.find((r) => r[0] === 'Ring')?.[1]).toBe('Sol');
    // Safety third: Weapon=Sol
    const safety = rows.slice(18, 27);
    expect(safety.find((r) => r[0] === 'Weapon')?.[1]).toBe('Sol');
    // Hit Power fourth: Helm=Ith
    const hp = rows.slice(27, 36);
    expect(hp.find((r) => r[0] === 'Helm')?.[1]).toBe('Ith');
  });

  test('the v176 gambling colour fix is applied (no non-existent --rare/--set vars)', async ({ page }) => {
    const html = await page.evaluate(() => document.getElementById('gambling-ref')?.innerHTML || '');
    expect(html).not.toContain('var(--rare)');
    expect(html).not.toContain('var(--set)');
    // the Rare / Set / Unique odds cells now use real, defined vars
    expect(html).toContain('var(--star)');     // Rare
    expect(html).toContain('var(--q-set)');     // Set
    expect(html).toContain('var(--q-unique)');  // Unique
  });

  test('no console errors expanding the matrix', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      const d = document.getElementById('craft-recipe-matrix') as HTMLDetailsElement | null;
      if (d) d.open = true;
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
