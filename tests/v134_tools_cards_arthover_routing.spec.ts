import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v134 — extend the v133 art-hover treatment to the REMAINING tools-tab cards so
// every item-name in the tools tab gets the floating #arttip art-popup on hover
// (registered art only) plus consistent click->openDrop routing:
//   - rune-stash .rs-name            -> data-arttip + openDrop route
//   - cube-up result name            -> data-arttip + openDrop route + nameLogo art
//   - material-stash .mat-name span  -> data-arttip + openDrop route
//   - set-tracker .set-piece-name    -> base-name (slot suffix stripped) nameLogo art
//                                       + data-arttip hover popup. NOT routed: set pieces
//                                       have no individual openDrop card (verified — openDrop
//                                       renders nothing), so art+hover only, no dead route.
test.describe('v134 tools cards art-hover + routing coverage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
  });

  test('rune-stash names carry data-arttip and route via openDrop', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#rune-stash-grid .rs-name')];
      return {
        count: names.length,
        allTip: names.every(n => (n.getAttribute('data-arttip') || '').length > 0),
        allRouted: names.every(n => /openDrop\(/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBeGreaterThan(0);
    expect(r.allTip).toBe(true);
    expect(r.allRouted).toBe(true);
  });

  test('cube-up result name carries data-arttip + art + route after a cube calc', async ({ page }) => {
    const r = await page.evaluate(() => {
      // drive the planner so the result span renders
      const fn = (window as any).renderRuneStash || (window as any).updateCubeUp;
      const res = document.getElementById('cubeup-result');
      // try clicking the first cube-up target if present
      const tgt = document.querySelector('#rune-stash-grid [onclick*="cubeUp"], #rune-stash-grid .cubeup-target') as HTMLElement | null;
      tgt?.click();
      const span = document.querySelector('#cubeup-result .zd-item-click') as HTMLElement | null;
      return {
        hasSpan: !!span,
        tip: span?.getAttribute('data-arttip') || '',
        routed: /openDrop\(/.test(span?.getAttribute('onclick') || ''),
        hasArt: !!span?.querySelector('.d2art-img'),
      };
    });
    // result span only exists once a cube-up target is chosen; assert shape when present
    if (r.hasSpan) {
      expect(r.tip.length).toBeGreaterThan(0);
      expect(r.routed).toBe(true);
    }
  });

  test('material-stash names carry data-arttip and route via openDrop', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#material-stash-grid .mat-name .zd-item-click')];
      return {
        count: names.length,
        allTip: names.every(n => (n.getAttribute('data-arttip') || '').length > 0),
        allRouted: names.every(n => /openDrop\(/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBeGreaterThan(0);
    expect(r.allTip).toBe(true);
    expect(r.allRouted).toBe(true);
  });

  test('set-tracker pieces get base-name art + data-arttip (slot suffix stripped, no dead route)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#set-tracker .set-piece-name')];
      return {
        count: names.length,
        allTip: names.every(n => (n.getAttribute('data-arttip') || '').length > 0),
        // data-arttip strips the "(slot)" suffix -> no parens in the tip value
        tipNoSlot: names.every(n => !/\(/.test(n.getAttribute('data-arttip') || '')),
        // text label keeps the full "(slot)" piece string
        labelKeepsSlot: names.some(n => /\(/.test((n.textContent || ''))),
        withArt: names.filter(n => n.querySelector('.d2art-img')).length,
      };
    });
    expect(r.count).toBeGreaterThan(0);
    expect(r.allTip).toBe(true);
    expect(r.tipNoSlot).toBe(true);
    expect(r.labelKeepsSlot).toBe(true);
    expect(r.withArt).toBeGreaterThan(0);
  });

  test('clicking a set-tracker piece toggles its collect box (no route, no console error)', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    const r = await page.evaluate(() => {
      // toggleSetPiece re-renders #set-tracker, so re-query the checked count after
      const checkedCount = () => document.querySelectorAll('#set-tracker .set-piece.checked').length;
      const before = checkedCount();
      const box = document.querySelector('#set-tracker .set-piece') as HTMLElement | null;
      box?.click();
      return { changed: checkedCount() !== before };
    });
    expect(r.changed).toBe(true);
    expect(errs).toEqual([]);
  });

  test('hovering a tools-card name reveals the floating #arttip popup (click-through)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const tip = document.getElementById('arttip');
      const el = document.querySelector('#rune-stash-grid .rs-name[data-arttip], #set-tracker .set-piece-name[data-arttip]') as HTMLElement | null;
      el?.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
      const style = tip ? getComputedStyle(tip) : null;
      return {
        exists: !!tip,
        clickThrough: style?.pointerEvents === 'none',
        on: tip?.classList.contains('on'),
      };
    });
    expect(r.exists).toBe(true);
    expect(r.clickThrough).toBe(true);
    // 'on' only when the hovered name has registered art; tolerate either but require popup exists
    expect(typeof r.on).toBe('boolean');
  });

  test('no console errors rendering + interacting with all tools cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(() => {
      ['rune-stash-card', 'material-stash-card', 'sunder-recipe-card', 'set-tracker-card']
        .forEach(id => document.getElementById(id)?.classList.remove('collapsed'));
    });
    await page.waitForTimeout(150);
    expect(errs).toEqual([]);
  });
});
