import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v122 — the binds tab gets a "🎯 Best roll — what to look for" section + clickable
// aura ID cards. AURA_RANK ranks the FIVE auras a 3.2 bind can actually result in
// (Fanaticism / Holy Freeze / Concentration / Vigor / Thorns) best→worst; every aura
// NAMED anywhere in the binds tab (the data-aura-logo cells) is now clickable and
// routes to bindAuraDetailHtml via openBindAuraByName. The 3 rerollable super-uniques
// (Hephasto / Bremm / Lister) carry a "best roll — top 3" block in their bind card.
// Single source of truth = BIND_AURA_POOL (+ the page's own 3.2 remap, AURA_REMAP).
test.describe('v122 aura best-roll guide + clickable aura ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('binds'));
    await page.waitForTimeout(150);
  });

  test('AURA_RANK + helpers are exposed (5 result auras, Fanaticism is the target)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const rank = (window as any).AURA_RANK || [];
      return {
        len: rank.length,
        names: rank.map((a: any) => a.name),
        first: rank[0]?.name,
        firstTier: rank[0]?.tier,
        hasDetail: typeof (window as any).bindAuraDetailHtml === 'function',
        hasOpen: typeof (window as any).openBindAuraByName === 'function',
        hasToggle: typeof (window as any).toggleBindAura === 'function',
        hasRender: typeof (window as any).renderAuraBestRoll === 'function',
      };
    });
    expect(r.len).toBe(5);
    expect(r.names).toEqual(['Fanaticism', 'Holy Freeze', 'Concentration', 'Vigor', 'Thorns']);
    expect(r.first).toBe('Fanaticism');
    expect(r.firstTier).toBe('S');
    expect(r.hasDetail).toBe(true);
    expect(r.hasOpen).toBe(true);
    expect(r.hasToggle).toBe(true);
    expect(r.hasRender).toBe(true);
  });

  test('the best-roll section renders 5 ranked rows, each routing to openBindAuraByName', async ({ page }) => {
    const r = await page.evaluate(() => {
      const sec = document.getElementById('binds-bestroll');
      const rows = sec ? Array.from(sec.querySelectorAll('#aura-bestroll .aura-rank-row')) : [];
      return {
        exists: !!sec,
        isSection: !!(sec && sec.querySelector('.sec-h .sec-chev')),
        count: rows.length,
        allRouted: rows.every((r) => (r.getAttribute('onclick') || '').includes('openBindAuraByName(')),
        topIsFanaticism: !!(rows[0] && (rows[0].textContent || '').includes('Fanaticism') && rows[0].classList.contains('aura-rank-top')),
      };
    });
    expect(r.exists).toBe(true);
    expect(r.isSection).toBe(true);
    expect(r.count).toBe(5);
    expect(r.allRouted).toBe(true);
    expect(r.topIsFanaticism).toBe(true);
  });

  test('clicking the Fanaticism row opens its aura ID card with the best-roll verdict', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindAuraByName('Fanaticism'));
    await page.waitForTimeout(120);
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindaura-detail');
      const txt = box ? (box.textContent || '') : '';
      return {
        open: box ? !box.hasAttribute('hidden') : false,
        gbc: !!(box && box.querySelector('.gbc-card')),
        name: txt.includes('Fanaticism'),
        formula: txt.includes('mlvl ÷ 8'),
        verdict: txt.includes('best-roll verdict'),
        result: txt.includes('live 3.2 bind result'),
      };
    });
    expect(r.open).toBe(true);
    expect(r.gbc).toBe(true);
    expect(r.name).toBe(true);
    expect(r.formula).toBe(true);
    expect(r.verdict).toBe(true);
    expect(r.result).toBe(true);
  });

  test('a removed aura card (Might) honestly shows the 3.2 remap target (no false "rolls")', async ({ page }) => {
    const txt = await page.evaluate(() => {
      return (window as any).bindAuraDetailHtml('Might');
    });
    expect(txt).toContain('removed / changed in 3.2');
    expect(txt).toContain('Concentration'); // Might → Concentration remap
    expect(txt).not.toContain('best-roll verdict'); // not a live result aura
  });

  test('toggle is an accordion — re-clicking the same aura closes it', async ({ page }) => {
    await page.evaluate(() => (window as any).openBindAuraByName('Holy Freeze'));
    await page.waitForTimeout(80);
    let open = await page.evaluate(() => !document.getElementById('bindaura-detail')!.hasAttribute('hidden'));
    expect(open).toBe(true);
    await page.evaluate(() => (window as any).openBindAuraByName('Holy Freeze'));
    await page.waitForTimeout(80);
    open = await page.evaluate(() => !document.getElementById('bindaura-detail')!.hasAttribute('hidden'));
    expect(open).toBe(false);
  });

  test('every tagged aura cell is now clickable and routes to the aura card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cells = Array.from(document.querySelectorAll('[data-aura-logo]'));
      const clickable = cells.filter((c) => c.classList.contains('aura-clickable') && c.getAttribute('role') === 'button');
      return { total: cells.length, clickable: clickable.length };
    });
    expect(r.total).toBeGreaterThanOrEqual(14);
    expect(r.clickable).toBe(r.total);
  });

  test('the 3 rerollable super-uniques carry a "best roll — top 3" block (Hephasto/Bremm/Lister)', async ({ page }) => {
    for (const name of ['Hephasto the Armorer', 'Bremm Sparkfist', 'Lister the Tormentor']) {
      const r = await page.evaluate((n) => {
        const html = (window as any).bindSUDetailHtml((window as any).BIND_SU.find((b: any) => b.name === n));
        return {
          hasBlock: html.includes('best roll — top 3'),
          picksFanaticism: html.includes("openBindAuraByName('Fanaticism')"),
          picksHolyFreeze: html.includes("openBindAuraByName('Holy Freeze')"),
        };
      }, name);
      expect(r.hasBlock, `${name} missing top-3 block`).toBe(true);
      expect(r.picksFanaticism, `${name} top-3 missing Fanaticism`).toBe(true);
      expect(r.picksHolyFreeze, `${name} top-3 missing Holy Freeze`).toBe(true);
    }
    // a non-rerollable super-unique (the Smith, fixed Holy Fire) gets NO top-3 block
    const smith = await page.evaluate(() =>
      (window as any).bindSUDetailHtml((window as any).BIND_SU.find((b: any) => b.name === 'The Smith')).includes('best roll — top 3'));
    expect(smith).toBe(false);
  });

  test('no console errors opening every aura ID card', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    const names = ['Fanaticism', 'Holy Freeze', 'Concentration', 'Vigor', 'Thorns',
      'Conviction', 'Might', 'Holy Fire', 'Holy Shock', 'Blessed Aim', 'Meditation'];
    for (const n of names) {
      await page.evaluate((nm) => (window as any).openBindAuraByName(nm), n);
      await page.waitForTimeout(20);
    }
    expect(errs).toEqual([]);
  });
});
