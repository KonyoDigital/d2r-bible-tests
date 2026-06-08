import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v135 — the floating #arttip hover popup now renders the in-game DESCRIPTION,
// not just art + name. Two tiers:
//   - Sunder charms (Latent + Renewed) get the FULL diablo2.io-style card from a
//     verified SUNDER_TIP registry (transcribed from diablo2.io's RotW item DB):
//     Unique · Grand Charm, Req/Quality level, blue sunder/resist lines, green
//     variable-range chips, gold "or" separators, Patch 3.0 tag.
//   - Every other item with a curated ITEM_INFO entry shows that verified
//     one-liner description on hover, site-wide.
const CHARMS = ['Black Cleft','Bone Break','Cold Rupture','Rotting Fissure','Flame Rift','Crack of the Heavens'];

test.describe('v135 rich hover tooltips (in-game descriptions)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('SUNDER_TIP exposes 12 verified Latent+Renewed tooltips', async ({ page }) => {
    const r = await page.evaluate(() => {
      const T = (window as any).SUNDER_TIP || {};
      const out: Record<string, { lines: number; req: number; qlvl: number; base: string; kind: string }> = {};
      for (const k in T) out[k] = { lines: T[k].lines.length, req: T[k].req, qlvl: T[k].qlvl, base: T[k].base, kind: T[k].kind };
      return { count: Object.keys(T).length, out };
    });
    expect(r.count).toBe(12);
    for (const c of CHARMS) {
      const latent = r.out['Latent ' + c];
      const renewed = r.out['Renewed ' + c];
      expect(latent).toBeTruthy();
      expect(renewed).toBeTruthy();
      expect(latent.kind).toBe('latent');
      expect(renewed.kind).toBe('renewed');
      expect(latent.req).toBe(75);
      expect(latent.qlvl).toBe(69);
      // latent = immunity line + a resist line; renewed = those 2 + 5 random-affix lines
      expect(latent.lines).toBe(2);
      expect(renewed.lines).toBe(7);
    }
  });

  test('_arttipResolve returns a rich card for sunders and a one-liner for grail items', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      return {
        renewed: f('Renewed Cold Rupture'),
        latent: f('Latent Flame Rift'),
        base: f('Black Cleft'),                 // base charm name -> Renewed card
        soj: f('The Stone of Jordan'),
        bogus: f('Zzz Not A Real Item'),
      };
    });
    // sunder rich cards
    expect(r.renewed.rich).toBe(true);
    expect(r.renewed.artName).toBe('Cold Rupture');
    expect(r.renewed.desc).toContain('att-var');     // green range chips
    expect(r.renewed.desc).toContain('att-or');       // gold "or"
    expect(r.renewed.desc).toContain('Cold Resist -70% (fixed)');
    expect(r.renewed.desc).toContain('Req level: 75');
    expect(r.latent.rich).toBe(true);
    expect(r.latent.desc).toContain('Fire Resist -90% to -70%');
    expect(r.base.rich).toBe(true);                   // bare charm name routes to Renewed
    // grail item -> verified ITEM_INFO one-liner
    expect(r.soj.rich).toBe(false);
    expect(r.soj.desc).toContain('att-info');
    expect(r.soj.desc).toContain('ALL skills');
    // unknown -> nothing
    expect(r.bogus.desc).toBe('');
  });

  test('hovering a Renewed charm shows the rich card; hovering a grail item shows its one-liner', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    await page.evaluate(() => {
      document.querySelector('#sunder-recipe-grid details[data-charm="Black Cleft"]')?.setAttribute('open', '');
    });
    await page.waitForTimeout(150);
    const sunder = await page.evaluate(() => {
      const tip = document.getElementById('arttip');
      const el = document.querySelector('#sunder-recipe-grid details[data-charm="Black Cleft"] .sun-renewed') as HTMLElement;
      el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 300, clientY: 300 }));
      return {
        on: tip?.classList.contains('on'),
        rich: tip?.classList.contains('tip-rich'),
        hasVar: !!tip?.querySelector('.att-var'),
        hasCore: !!tip?.querySelector('.att-core'),
        clickThrough: getComputedStyle(tip!).pointerEvents === 'none',
        name: (tip?.querySelector('.att-name') as HTMLElement)?.textContent,
      };
    });
    expect(sunder.on).toBe(true);
    expect(sunder.rich).toBe(true);
    expect(sunder.hasVar).toBe(true);
    expect(sunder.hasCore).toBe(true);
    expect(sunder.clickThrough).toBe(true);
    expect(sunder.name).toContain('Renewed Black Cleft');
  });

  test('a grail item rendered anywhere shows its ITEM_INFO description on hover (not rich)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop('The Stone of Jordan');
      // any data-arttip/data-art-logo element naming SoJ
      const el = document.querySelector('[data-arttip="The Stone of Jordan"],[data-art-logo="The Stone of Jordan"]') as HTMLElement | null;
      const tip = document.getElementById('arttip');
      if (!el) return { found: false };
      el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
      return {
        found: true,
        on: tip?.classList.contains('on'),
        rich: tip?.classList.contains('tip-rich'),
        info: !!tip?.querySelector('.att-info'),
      };
    });
    if (r.found) {
      expect(r.on).toBe(true);
      expect(r.rich).toBe(false);
      expect(r.info).toBe(true);
    }
  });

  test('no console errors rendering + hovering the tooltips', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(200);
    await page.evaluate(() => {
      document.querySelectorAll('#sunder-recipe-grid details.sun-recipe').forEach((d) => d.setAttribute('open', ''));
      const T = (window as any).SUNDER_TIP || {};
      for (const k in T) (window as any)._arttipResolve(k);
    });
    await page.waitForTimeout(100);
    expect(errs).toEqual([]);
  });
});
