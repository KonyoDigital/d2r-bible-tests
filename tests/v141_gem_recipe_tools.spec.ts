// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v141 — two new Tools-tab planners:
//   - GEM_TYPES: 7 gem types × 5 grades = 35 verified variants (socket stats
//     transcribed verbatim from the D2R game-data gems file). findGem + gemDetailHtml
//     + an openDrop branch (EXACT match, before findMaterial) give every gem a
//     clickable socket ID card; _arttipResolve gives every gem a rich hover card.
//     #gem-stash-card mirrors the rune stash: 35-cell counter + 3→1 cube-up planner.
//   - HORADRIC_RECIPES: the general Horadric Cube recipe browser (#horadric-recipe-card)
//     with a filter box; rune & gem tokens auto-linkify → openDrop.
// ZERO fabrication: gem socket values come straight from gems.json.

const GEM_TYPE_NAMES = ['Amethyst', 'Diamond', 'Emerald', 'Ruby', 'Sapphire', 'Topaz', 'Skull'];

test.describe('v141 gem stash + cube-up planner + Horadric recipe browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(800);
  });

  test('GEM_TYPES holds 7 types × 5 well-formed grades (35 variants)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const G = (window as any).GEM_TYPES || [];
      let variants = 0, emptyW = 0, emptyA = 0, emptyS = 0, badGrades = 0;
      const order = ['Chipped', 'Flawed', 'Normal', 'Flawless', 'Perfect'];
      for (const t of G) {
        if (!Array.isArray(t.q) || t.q.length !== 5) badGrades++;
        t.q.forEach((g: any, i: number) => {
          variants++;
          if (g.q !== order[i]) badGrades++;
          if (!g.w) emptyW++; if (!g.a) emptyA++; if (!g.s) emptyS++;
        });
      }
      return { types: G.length, variants, emptyW, emptyA, emptyS, badGrades };
    });
    expect(r.types).toBe(7);
    expect(r.variants).toBe(35);
    expect(r.emptyW).toBe(0);
    expect(r.emptyA).toBe(0);
    expect(r.emptyS).toBe(0);
    expect(r.badGrades).toBe(0);
  });

  test('findGem normalizes full + bare gem names; rejects non-gems', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any).findGem;
      return {
        perfAme: f('Perfect Amethyst'),
        lower: f('perfect amethyst'),
        bareSkull: f('Skull'),
        bareDiamond: f('Diamond'),
        chippedTopaz: f('Chipped Topaz'),
        bogus: f('Not A Gem'),
        rune: f('Jah'),
      };
    });
    expect(r.perfAme).toBe('Perfect Amethyst');
    expect(r.lower).toBe('Perfect Amethyst');
    expect(r.bareSkull).toBe('Skull');
    expect(r.bareDiamond).toBe('Diamond');
    expect(r.chippedTopaz).toBe('Chipped Topaz');
    expect(r.bogus).toBeNull();
    expect(r.rune).toBeNull();
  });

  test('socket stats match the verified game data (Diamond armor = AR, not Strength)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const G = (window as any).GEM_TYPES;
      const find = (type: string, q: string) => G.find((t: any) => t.type === type).q.find((g: any) => g.q === q);
      return {
        perfDiamondArmor: find('Diamond', 'Perfect').a,         // verified: +100 Attack Rating
        perfEmeraldWeapon: find('Emerald', 'Perfect').w,        // verified poison total
        perfSkullWeapon: find('Skull', 'Perfect').w,            // dual leech
        perfAmethystShield: find('Amethyst', 'Perfect').s,
        chippedTopazArmor: find('Topaz', 'Chipped').a,
      };
    });
    expect(r.perfDiamondArmor).toBe('+100 Attack Rating');
    expect(r.perfEmeraldWeapon).toBe('+100 Poison Damage over 7 seconds');
    expect(r.perfSkullWeapon).toContain('Life Stolen');
    expect(r.perfSkullWeapon).toContain('Mana Stolen');
    expect(r.perfAmethystShield).toBe('+30 Defense');
    expect(r.chippedTopazArmor).toContain('Magic Items');
  });

  test('_arttipResolve gives every gem a rich (image-less) socket card', async ({ page }) => {
    const r = await page.evaluate((types) => {
      const f = (window as any)._arttipResolve;
      const out: Record<string, { rich: boolean; gem: boolean; slots: boolean }> = {};
      for (const t of types) {
        const x = f('Perfect ' + t);
        out[t] = {
          rich: x.rich,
          gem: /att-type/.test(x.desc) && /Gem/.test(x.desc),
          slots: /Weapon/.test(x.desc) && /Helm\/Armor/.test(x.desc) && /Shield/.test(x.desc),
        };
      }
      return out;
    }, GEM_TYPE_NAMES);
    for (const t of GEM_TYPE_NAMES) {
      expect(r[t].rich, t).toBe(true);
      expect(r[t].gem, t).toBe(true);
      expect(r[t].slots, t).toBe(true);
    }
  });

  test('openDrop routes a gem to its .gem-card socket card with the grade table', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Perfect Amethyst');
      const panel = document.getElementById('item-detail')!;
      const card = panel.querySelector('.gem-card');
      return {
        shown: panel.classList.contains('show'),
        hasCard: !!card,
        name: card?.querySelector('.gic-name')?.textContent?.includes('Perfect Amethyst'),
        grades: panel.querySelectorAll('.gemd-q').length,
        marked: panel.querySelectorAll('.gemd-q.gem-q-on').length,
      };
    });
    expect(r.shown).toBe(true);
    expect(r.hasCard).toBe(true);
    expect(r.name).toBe(true);
    expect(r.grades).toBe(5);
    expect(r.marked).toBe(1);   // the hovered grade is highlighted
  });

  test('a bare gem name (Skull) routes to ITS card, not a material substring collision', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('Skull');
      const panel = document.getElementById('item-detail')!;
      return {
        gemCard: !!panel.querySelector('.gem-card'),
        materialCard: !!panel.querySelector('.material-card'),
        name: panel.querySelector('.gic-name')?.textContent?.includes('Skull'),
      };
    });
    expect(r.gemCard).toBe(true);
    expect(r.materialCard).toBe(false);
    expect(r.name).toBe(true);
  });

  test('gem cube-up planner cascades 3→1 honestly', async ({ page }) => {
    const r = await page.evaluate(() => {
      const pot = (window as any).gemCubeUpPotential;
      const adj = (window as any).adjustGemStash;
      (window as any).clearGemStash();
      // 9 Chipped Amethyst → 3 Flawed → 1 Normal → 0 Perfect
      for (let i = 0; i < 9; i++) adj('Chipped Amethyst', 1);
      const out = {
        toNormal: pot('Amethyst', 2),    // 1
        toFlawless: pot('Amethyst', 3),  // 0
        toPerfect: pot('Amethyst', 4),   // 0
        otherType: pot('Ruby', 4),       // 0 (untouched)
      };
      (window as any).clearGemStash();
      return out;
    });
    expect(r.toNormal).toBe(1);
    expect(r.toFlawless).toBe(0);
    expect(r.toPerfect).toBe(0);
    expect(r.otherType).toBe(0);
  });

  test('the gem stash grid renders 35 cells; +/- adjusts and persists', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).clearGemStash();
      (window as any).renderGemStash();
      const grid = document.getElementById('gem-stash-grid')!;
      const cells = grid.querySelectorAll('.gem-cell').length;
      const rows = grid.querySelectorAll('.gem-row').length;
      (window as any).adjustGemStash('Perfect Topaz', 3);
      const count = document.querySelector('[data-gem-count="Perfect Topaz"]')?.textContent;
      const ls = JSON.parse(localStorage.getItem('d2r_gemStash') || '{}');
      (window as any).clearGemStash();
      return { cells, rows, count, persisted: ls['Perfect Topaz'] };
    });
    expect(r.cells).toBe(35);
    expect(r.rows).toBe(7);
    expect(r.count).toBe('3');
    expect(r.persisted).toBe(3);
  });

  test('the Horadric recipe browser lists every recipe; filterable; rune/gem chips clickable', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderHoradricRecipes();
      const list = document.getElementById('horadric-list')!;
      const allRows = list.querySelectorAll('.hcr-row').length;
      const totalData = (window as any).HORADRIC_RECIPES.length;
      const chip = list.querySelector('.rec-chip') as HTMLElement | null;
      const chipClickable = !!chip && /openDrop/.test(chip.getAttribute('onclick') || '') && chip.hasAttribute('data-arttip');
      // filter
      const f = document.getElementById('horadric-filter') as HTMLInputElement;
      f.value = 'socket';
      (window as any).renderHoradricRecipes();
      const filtered = list.querySelectorAll('.hcr-row').length;
      f.value = '';
      (window as any).renderHoradricRecipes();
      return { allRows, totalData, chipClickable, filtered };
    });
    expect(r.allRows).toBe(r.totalData);
    expect(r.allRows).toBeGreaterThanOrEqual(30);
    expect(r.chipClickable).toBe(true);
    expect(r.filtered).toBeGreaterThan(0);
    expect(r.filtered).toBeLessThan(r.allRows);
  });

  test('a recipe-browser gem chip routes to the gem ID card via openDrop', async ({ page }) => {
    await page.evaluate(() => {
      const f = document.getElementById('horadric-filter') as HTMLInputElement;
      f.value = 'perfect emerald';
      (window as any).renderHoradricRecipes();
      const chip = [...document.querySelectorAll('#horadric-list .rec-chip')]
        .find((el) => /Perfect Emerald/.test(el.textContent || '')) as HTMLElement;
      chip?.click();
    });
    await page.waitForTimeout(120);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('item-detail')!;
      return {
        gemCard: !!panel.querySelector('.gem-card'),
        name: panel.querySelector('.gic-name')?.textContent?.includes('Emerald'),
      };
    });
    expect(r.gemCard).toBe(true);
    expect(r.name).toBe(true);
  });

  test('the gem + recipe rollout produces no console errors', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      const G = (window as any).GEM_TYPES;
      const f = (window as any)._arttipResolve;
      for (const t of G) for (const g of t.q) { f(g.name); (window as any).gemDetailHtml(g.name); }
      (window as any).renderGemStash();
      (window as any).renderHoradricRecipes();
      (window as any).openDrop('Perfect Skull');
      (window as any).openDrop('Diamond');
    });
    await page.waitForTimeout(120);
    expect(errs).toEqual([]);
  });
});
