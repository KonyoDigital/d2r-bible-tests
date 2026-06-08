import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v138 — hovering any data-aura-logo cell floats the ENLARGED animated aura icon
// (the AURA_ART gif) in the #arttip popup, with the aura name. Reuses the existing
// arttip delegation (pointer-events:none, click-through). Additive: the cell's
// existing click-to-open-ID-card behaviour is untouched.
const AURAS = ['Fanaticism', 'Conviction', 'Holy Freeze', 'Holy Fire', 'Holy Shock', 'Blessed Aim', 'Might'];

test.describe('v138 aura hover popup (enlarged aura icon)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('hovering a Fanaticism aura cell floats the enlarged AURA_ART gif + name', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cell = document.querySelector('[data-aura-logo="Fanaticism"]') as HTMLElement | null;
      if (!cell) return { found: false };
      const tip = document.getElementById('arttip')!;
      cell.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 300, clientY: 300 }));
      const img = tip.querySelector('img') as HTMLImageElement;
      return {
        found: true,
        on: tip.classList.contains('on'),
        rich: tip.classList.contains('tip-rich'),
        name: tip.querySelector('.att-name')!.textContent,
        src: img.src,
        expected: (window as any).AURA_ART['Fanaticism'],
        imgShown: img.style.display !== 'none',
        clickThrough: getComputedStyle(tip).pointerEvents === 'none',
      };
    });
    expect(r.found).toBe(true);
    expect(r.on).toBe(true);
    expect(r.rich).toBe(false);
    expect(r.name).toBe('Fanaticism aura');
    expect(r.src).toBe(r.expected);     // the verified AURA_ART gif, enlarged
    expect(r.imgShown).toBe(true);
    expect(r.clickThrough).toBe(true);
  });

  test('every aura in the level table floats its own mapped icon on hover', async ({ page }) => {
    const r = await page.evaluate((auras) => {
      const tip = document.getElementById('arttip')!;
      const img = tip.querySelector('img') as HTMLImageElement;
      const out: Record<string, { src: string; expected: string; name: string }> = {};
      for (const a of auras) {
        const cell = document.querySelector('[data-aura-logo="' + a + '"]') as HTMLElement | null;
        if (!cell) { out[a] = { src: 'MISSING', expected: '', name: '' }; continue; }
        cell.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
        out[a] = { src: img.src, expected: (window as any).AURA_ART[a], name: tip.querySelector('.att-name')!.textContent || '' };
      }
      return out;
    }, AURAS);
    for (const a of AURAS) {
      expect(r[a].src, a).toBe(r[a].expected);
      expect(r[a].name, a).toBe(a + ' aura');
    }
  });

  test('aura hover does NOT break the item rich-card path (data-arttip still works)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      const soj = f('The Stone of Jordan');
      return { rich: soj.rich, type: /att-type/.test(soj.desc) };
    });
    expect(r.rich).toBe(true);
    expect(r.type).toBe(true);
  });

  test('no console errors hovering aura cells', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate((auras) => {
      for (const a of auras) {
        const cell = document.querySelector('[data-aura-logo="' + a + '"]') as HTMLElement | null;
        if (cell) {
          cell.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
          cell.dispatchEvent(new MouseEvent('mouseout', { bubbles: true }));
        }
      }
    }, AURAS);
    await page.waitForTimeout(100);
    expect(errs).toEqual([]);
  });
});
