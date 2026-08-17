// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v142 — the Horadric recipe browser becomes a live TOOL, wired to the rune + gem
// stash tallies (like the other Tools-tab planners):
//   - _recIngredients(in) parses the TRACKABLE rune + gem ingredients (with counts).
//   - _recReady(recipe) cross-checks against runeStash + gemStash → {trackable, ready, missing}.
//   - each rendered row gets a status chip: green "✓ cubeable" when you hold every
//     rune & gem it lists, else "need N× <name>".
//   - a "🎒 Cubeable now" toggle (toggleHoradricReady) filters to only fully-cubeable recipes.
//   - bumping the rune or gem stash re-renders the recipe list live.
// Also v142: the RotW tab's 6 section headers are unified into symmetric art+title bars.

test.describe('v142 recipe browser wired to the stash tallies', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(800);
    await page.evaluate(() => { (window as any).clearRuneStash?.(); (window as any).clearGemStash?.(); });
  });

  test('_recIngredients parses only the trackable rune + gem tokens with counts', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._recIngredients;
      const socket = f('Ral + Amn + Perfect Amethyst + Normal Weapon'); // 2 runes + 1 gem, base untracked
      const gems3 = f('3× identical gems (same type + grade, except Perfect)'); // descriptive rule — nothing trackable
      const potions = f('3× Health Potion + 3× Mana Potion + 1× Standard Gem'); // a generic Standard (Normal) gem IS trackable
      const quality = f('El + Chipped Gem + Low Quality Weapon'); // rune + generic chipped-grade gem
      return {
        socketLen: socket.length,
        socketNames: socket.map((i: any) => i.name + ':' + i.type + ':' + i.need),
        gems3Len: gems3.length,
        potions: potions.map((i: any) => i.type + ':' + (i.grades ? i.grades.join('/') : i.name) + ':' + i.need),
        quality: quality.map((i: any) => i.type + ':' + (i.grades ? i.grades.join('/') : i.name) + ':' + i.need),
      };
    });
    expect(r.socketLen).toBe(3);
    expect(r.socketNames).toContain('Ral:rune:1');
    expect(r.socketNames).toContain('Amn:rune:1');
    expect(r.socketNames).toContain('Perfect Amethyst:gem:1');
    expect(r.gems3Len).toBe(0);
    // generic gem-grade requirements are now tracked (fixes recipes shown cubeable without the gem)
    expect(r.potions).toEqual(['gemGrade:Normal:1']);
    expect(r.quality).toEqual(['rune:El:1', 'gemGrade:Chipped:1']);
  });

  test('_recReady flips to ready once the stash holds every rune + gem', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ready = (window as any)._recReady;
      const adjR = (window as any).adjustRuneStash;
      const adjG = (window as any).adjustGemStash;
      const recipe = { c: '🔩 Sockets', in: 'Ral + Amn + Perfect Amethyst + Normal Weapon', out: 'Socketed Weapon' };
      const before = ready(recipe);
      adjR('Ral', 1); adjR('Amn', 1); adjG('Perfect Amethyst', 1);
      const after = ready(recipe);
      const untracked = ready({ c: 'x', in: '3× Ring', out: '1× Amulet' });
      (window as any).clearRuneStash(); (window as any).clearGemStash();
      return {
        beforeTrackable: before.trackable, beforeReady: before.ready, beforeMissing: before.missing.length,
        afterReady: after.ready, afterMissing: after.missing.length,
        untrackedTrackable: untracked.trackable,
      };
    });
    expect(r.beforeTrackable).toBe(true);
    expect(r.beforeReady).toBe(false);
    expect(r.beforeMissing).toBe(3);
    expect(r.afterReady).toBe(true);
    expect(r.afterMissing).toBe(0);
    expect(r.untrackedTrackable).toBe(false); // a Ring->Amulet recipe has no trackable rune/gem
  });

  test('rows render a status chip; the Cubeable-now toggle filters to ready recipes', async ({ page }) => {
    const r = await page.evaluate(() => {
      const adjR = (window as any).adjustRuneStash;
      const adjG = (window as any).adjustGemStash;
      // make exactly ONE recipe cubeable: Ral + Amn + Perfect Amethyst + Normal Weapon
      adjR('Ral', 1); adjR('Amn', 1); adjG('Perfect Amethyst', 1);
      (window as any).renderHoradricRecipes();
      const list = document.getElementById('horadric-list')!;
      const allRows = list.querySelectorAll('.hcr-row').length;
      const readyChips = list.querySelectorAll('.hcr-status.hcr-ready').length;
      const needChips = list.querySelectorAll('.hcr-status.hcr-need').length;
      // toggle "Cubeable now"
      (window as any).toggleHoradricReady();
      const filteredRows = list.querySelectorAll('.hcr-row').length;
      const filteredReady = list.querySelectorAll('.hcr-status.hcr-ready').length;
      const toggleOn = document.getElementById('horadric-ready-toggle')!.classList.contains('on');
      (window as any).toggleHoradricReady(); // back off
      const restored = list.querySelectorAll('.hcr-row').length;
      (window as any).clearRuneStash(); (window as any).clearGemStash();
      return { allRows, readyChips, needChips, filteredRows, filteredReady, toggleOn, restored };
    });
    expect(r.readyChips).toBeGreaterThanOrEqual(1);
    expect(r.needChips).toBeGreaterThan(0);
    expect(r.filteredRows).toBe(r.filteredReady); // every shown row is a ready row
    expect(r.filteredRows).toBeLessThan(r.allRows);
    expect(r.toggleOn).toBe(true);
    expect(r.restored).toBe(r.allRows);
  });

  test('adjusting the gem stash re-renders the recipe list live', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderHoradricRecipes();
      const list = document.getElementById('horadric-list')!;
      const before = list.querySelectorAll('.hcr-status.hcr-ready').length;
      // satisfy the all-gem prismatic-amulet recipe is hard; instead satisfy a socket recipe via renderGemStash path
      (window as any).adjustRuneStash('Tal', 1);
      (window as any).adjustRuneStash('Thul', 1);
      (window as any).adjustGemStash('Perfect Topaz', 1); // Tal+Thul+Perfect Topaz+Normal Body Armor
      // adjustGemStash calls renderGemStash → renderHoradricRecipes; assert without manual re-render
      const after = list.querySelectorAll('.hcr-status.hcr-ready').length;
      (window as any).clearRuneStash(); (window as any).clearGemStash();
      return { before, after };
    });
    expect(r.after).toBeGreaterThan(r.before);
  });

  test('the RotW tab section headers are unified art+title bars', async ({ page }) => {
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(200);
    const r = await page.evaluate(() => {
      const heads = [...document.querySelectorAll('#tab-rotw .sec-h')] as HTMLElement[];
      const withTitle = heads.filter((h) => h.querySelector('.sec-h-t')).length;
      const withArt = heads.filter((h) => h.querySelector('.sec-h-art')).length;
      const withChev = heads.filter((h) => h.querySelector('.sec-chev')).length;
      const noInlineFlex = heads.every((h) => !/display:flex/.test(h.getAttribute('style') || ''));
      return { total: heads.length, withTitle, withArt, withChev, noInlineFlex };
    });
    expect(r.total).toBe(6);
    expect(r.withTitle).toBe(6);
    expect(r.withArt).toBe(6);   // every header now carries an art/emoji wrapper
    expect(r.withChev).toBe(6);
    expect(r.noInlineFlex).toBe(true); // ad-hoc inline flex styles removed → CSS-driven symmetry
  });

  test('no console errors across the recipe-tool + RotW-header flow', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      (window as any).adjustRuneStash('Ral', 1);
      (window as any).adjustGemStash('Perfect Amethyst', 1);
      (window as any).renderHoradricRecipes();
      (window as any).toggleHoradricReady();
      (window as any).toggleHoradricReady();
      (window as any).clearRuneStash(); (window as any).clearGemStash();
    });
    await page.click('.tab[data-tab="rotw"]');
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });
});
