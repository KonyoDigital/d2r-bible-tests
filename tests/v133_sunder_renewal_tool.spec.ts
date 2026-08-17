// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v133 — the Sunder Charm Renewal recipe tool. A new collapsible tools-tab card
// answers "what's the recipe to renew my Sunder Charm?" by surfacing the EXISTING
// verified per-charm Renewed-upgrade recipes (transcribed from SPECIAL_DROPS.sunder /
// Maxroll, corroborated by d2db.net) as clickable, routable rows: each charm + its
// Latent base + Perfect Gem + Rune + matching region Worldstone Shard. The rune +
// shard ingredients route via openDrop(); a floating art-hover popup (#arttip)
// reveals in-game art for any [data-arttip]/[data-art-logo] chip. Global search
// keyword routing ("renew sunder", "sunder recipe", per-charm) opens the tool.
const CHARMS: Record<string, { gem: string; rune: string; shards: string[] }> = {
  'Cold Rupture':         { gem: 'Perfect Sapphire', rune: 'Lum', shards: ['Worldstone Shard (Eastern)'] },
  'Flame Rift':           { gem: 'Perfect Ruby',     rune: 'Io',  shards: ['Worldstone Shard (Deep)'] },
  'Crack of the Heavens': { gem: 'Perfect Topaz',    rune: 'Fal', shards: ['Worldstone Shard (Southern)'] },
  'Rotting Fissure':      { gem: 'Perfect Emerald',  rune: 'Ko',  shards: ['Worldstone Shard (Western)'] },
  'Bone Break':           { gem: 'Perfect Amethyst', rune: 'Pul', shards: ['Worldstone Shard (Northern)'] },
  'Black Cleft':          { gem: 'Perfect Diamond',  rune: 'Mal', shards: ['Worldstone Shard (Southern)', 'Worldstone Shard (Deep)', 'Worldstone Shard (Northern)'] },
};

test.describe('v133 Sunder Charm Renewal recipe tool', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('SUNDER_RECIPES exposes the 6 verified per-charm recipes', async ({ page }) => {
    const r = await page.evaluate(() => {
      const R = (window as any).SUNDER_RECIPES;
      return {
        len: R?.length,
        map: Object.fromEntries((R || []).map((s: any) => [s.n, { gem: s.gem, rune: s.rune, shards: s.shards }])),
        fns: ['renderSunderRecipes', 'openSunderRecipes'].map((f) => typeof (window as any)[f]),
      };
    });
    expect(r.len).toBe(6);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
    for (const [n, exp] of Object.entries(CHARMS)) {
      expect(r.map[n]).toEqual(exp);
    }
  });

  test('the tool card renders 6 expandable charm recipe rows with the right ingredient chips', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const grid = document.getElementById('sunder-recipe-grid');
      const rows = [...(grid?.querySelectorAll('details.sun-recipe') || [])];
      return rows.map((row) => {
        const charm = row.getAttribute('data-charm') || '';
        const ings = [...row.querySelectorAll('.sun-ing')].map((e) => (e.textContent || '').trim());
        const routed = [...row.querySelectorAll('.sun-ing.route')].map((e) => e.getAttribute('onclick') || '');
        return { charm, ings, routed };
      });
    });
    expect(r.length).toBe(6);
    for (const row of r) {
      const exp = CHARMS[row.charm];
      expect(exp).toBeTruthy();
      // Latent base + gem + rune + each shard all appear as ingredient chips
      expect(row.ings.some((t) => t.includes('Latent ' + row.charm))).toBe(true);
      expect(row.ings.some((t) => t.includes(exp.gem))).toBe(true);
      expect(row.ings.some((t) => t.includes(exp.rune + ' Rune'))).toBe(true);
      for (const sh of exp.shards) expect(row.ings.some((t) => t.includes(sh))).toBe(true);
      // rune + shards route via openDrop (gem + Latent base are non-routable text)
      expect(row.routed.some((oc) => oc.includes("openDrop('" + exp.rune + " Rune')"))).toBe(true);
      for (const sh of exp.shards) {
        expect(row.routed.some((oc) => oc.includes('openDrop(') && oc.includes(sh.replace(/'/g, "\\'")))).toBe(true);
      }
    }
  });

  test('each recipe row shows a Horadric Cube preview image', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('#sunder-recipe-grid details.sun-recipe')];
      const cubes = rows.map((row) => row.querySelector('.sun-formula img.sun-cube') as HTMLImageElement | null);
      return {
        rows: rows.length,
        withCube: cubes.filter(Boolean).length,
        srcs: [...new Set(cubes.filter(Boolean).map((c) => c!.getAttribute('src') || ''))],
        allHttp: cubes.filter(Boolean).every((c) => /^art\//.test(c!.getAttribute('src') || '')),
      };
    });
    expect(r.rows).toBe(6);
    expect(r.withCube).toBe(6);
    expect(r.srcs.length).toBe(1);
    expect(r.allHttp).toBe(true);
  });

  test('charm name in each row routes to its own card (no toggling the details open)', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const names = [...document.querySelectorAll('#sunder-recipe-grid .sun-charm')];
      return {
        count: names.length,
        allRouted: names.every((n) => /openDrop\(/.test(n.getAttribute('onclick') || '')),
        allStop: names.every((n) => /stopPropagation/.test(n.getAttribute('onclick') || '')),
      };
    });
    expect(r.count).toBe(6);
    expect(r.allRouted).toBe(true);
    expect(r.allStop).toBe(true);
  });

  test('clicking a recipe rune chip opens that rune card', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const opened = await page.evaluate(() => {
      const chip = document.querySelector('#sunder-recipe-grid .sun-ing.route[onclick*="Rune"]') as HTMLElement | null;
      chip?.click();
      return !!document.getElementById('item-detail')?.querySelector('.rune-card');
    });
    expect(opened).toBe(true);
    expect(errs).toEqual([]);
  });

  test('openSunderRecipes switches to tools + un-collapses the card', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openSunderRecipes();
      const card = document.getElementById('sunder-recipe-card');
      return {
        toolsActive: document.getElementById('tab-tools')?.classList.contains('active'),
        open: card ? !card.classList.contains('collapsed') : false,
      };
    });
    expect(r.toolsActive).toBe(true);
    expect(r.open).toBe(true);
  });

  test('global search "renew sunder" + per-charm routes to the recipe tool', async ({ page }) => {
    await page.fill('#gsearch-input', 'renew sunder charm recipe');
    await page.waitForTimeout(200);
    const top = await page.evaluate(() => {
      const el = document.querySelector('#gsearch-results .gsearch-item');
      return {
        lab: (el?.querySelector('.gsearch-lab') as HTMLElement)?.textContent?.trim() || '',
        cat: (el?.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() || '',
      };
    });
    expect(/renew/i.test(top.lab)).toBe(true);
    expect(top.cat.toLowerCase()).toContain('recipe');

    // per-charm intent — "renew cold rupture" surfaces a recipe command
    await page.fill('#gsearch-input', 'renew cold rupture');
    await page.waitForTimeout(200);
    const hasRecipe = await page.evaluate(() => [...document.querySelectorAll('#gsearch-results .gsearch-item')]
      .some((el) => /recipe/i.test((el.querySelector('.gsearch-cat') as HTMLElement)?.textContent || '')));
    expect(hasRecipe).toBe(true);
  });

  test('the floating art-hover popup reveals registered art and stays click-through', async ({ page }) => {
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const tip = document.getElementById('arttip');
      const charm = document.querySelector('#sunder-recipe-grid .sun-charm') as HTMLElement | null;
      charm?.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 200, clientY: 200 }));
      const style = tip ? getComputedStyle(tip) : null;
      return {
        exists: !!tip,
        clickThrough: style?.pointerEvents === 'none',
        on: tip?.classList.contains('on'),
        imgSrc: (tip?.querySelector('img') as HTMLImageElement)?.getAttribute('src') || '',
        name: (tip?.querySelector('.att-name') as HTMLElement)?.textContent || '',
      };
    });
    expect(r.exists).toBe(true);
    expect(r.clickThrough).toBe(true);
    expect(r.on).toBe(true);
    expect(r.imgSrc).toContain('art/');
    expect(r.name.length).toBeGreaterThan(0);
  });

  test('no console errors rendering + interacting with the tool', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(200);
    await page.evaluate(() => {
      document.querySelectorAll('#sunder-recipe-grid details.sun-recipe').forEach((d) => d.setAttribute('open', ''));
    });
    await page.waitForTimeout(100);
    expect(errs).toEqual([]);
  });
});
