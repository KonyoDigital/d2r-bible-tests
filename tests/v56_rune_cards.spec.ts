import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v56 — per-rune ID cards. Individual runes (Lo/Ohm/Vex…) previously had no
// detail card, so a clicked rune name was a dead end. This closes that last
// routing gap: each of the 33 runes becomes ONE canonical golden card
// (findRune → runeDetailHtml → openDrop) reachable from the Countess rune
// table and every RUNE_SOURCES grid. Stats are canonical D2R values; per-rune
// Countess Hell rates are pulled from the EXISTING COUNTESS_RUNES table — no
// odds are fabricated. Aggregated rows (Amn-Sol) + grail items do NOT resolve.
test.describe('v56 per-rune ID cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('findRune resolves runes (format-tolerant), null for aggregates/grail/non-runes', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fr = (window as any).findRune;
      const nm = (n: string) => { const m = fr(n); return m ? m.n : null; };
      return {
        isFn: typeof fr,
        bare: nm('Lo'),
        numbered: nm('Lo #28'),
        withWord: nm('Lo Rune'),
        zod: nm('Zod'),
        hel: nm('Hel'),
        // aggregated Countess rows are NOT a single rune → must stay null
        agg1: nm('Amn-Sol'),
        agg2: nm('Ral-El-Tir-Tal-Ith-Ort'),
        // grail items / non-runes must not false-match
        grail: nm('Harlequin Crest (Shako)'),
        nonsense: nm('Totally Not A Rune'),
        runeCount: (RUNES as any).length,
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.bare).toBe('Lo');
    expect(r.numbered).toBe('Lo');
    expect(r.withWord).toBe('Lo');
    expect(r.zod).toBe('Zod');
    expect(r.hel).toBe('Hel');
    expect(r.agg1).toBeNull();
    expect(r.agg2).toBeNull();
    expect(r.grail).toBeNull();
    expect(r.nonsense).toBeNull();
    expect(r.runeCount).toBe(33);
  });

  test('runeDetailHtml renders a complete card: grants/where/cube/runewords, no undefined, every rune caveated', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any).runeDetailHtml;
      const lo = html('Lo #28');
      const zod = html('Zod');
      const hel = html('Hel');
      return {
        isFn: typeof html,
        loName: /Lo Rune/.test(lo),
        loGrants: /What it grants/.test(lo),
        loWeapon: /in a weapon/.test(lo) && /Deadly Strike/.test(lo),
        loArmor: /in body armor/.test(lo),
        loShield: /in a shield/.test(lo),
        loWhere: /Where it drops/.test(lo),
        loCountess: /Countess \(Hell\)/.test(lo),     // pulled from COUNTESS_RUNES
        loCube: /Cube upgrade/.test(lo) && /Perfect Amethyst/.test(lo),
        loRunewords: /Key runewords/.test(lo) && /Fortitude/.test(lo),
        loNoUndef: !/undefined/.test(lo),
        // Zod is the top rune — no cube-up target
        zodTop: /top rune/.test(zod) && !/undefined/.test(zod),
        // Hel has no level requirement
        helNoReq: /no level requirement/.test(hel) && !/undefined/.test(hel),
        // every one of the 33 cards is clean + carries the honesty caveat
        allClean: (RUNES as any).every((rr: any) => {
          const c = html(rr.n);
          return !/undefined/.test(c) && /not fabricated/.test(c) && /What it grants/.test(c);
        }),
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.loName).toBe(true);
    expect(r.loGrants).toBe(true);
    expect(r.loWeapon).toBe(true);
    expect(r.loArmor).toBe(true);
    expect(r.loShield).toBe(true);
    expect(r.loWhere).toBe(true);
    expect(r.loCountess).toBe(true);
    expect(r.loCube).toBe(true);
    expect(r.loRunewords).toBe(true);
    expect(r.loNoUndef).toBe(true);
    expect(r.zodTop).toBe(true);
    expect(r.helNoReq).toBe(true);
    expect(r.allClean).toBe(true);
  });

  test('Countess Hell rates in the card match the published COUNTESS_RUNES data (no fabrication)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any).runeDetailHtml;
      // Lo Hell rate in COUNTESS_RUNES is 320197 → card must show that exact figure
      const loRow = (COUNTESS_RUNES as any).find((x: any) => /^Lo/.test(x.n));
      const card = html('Lo');
      return {
        usesPublished: card.includes(loRow.hell.toLocaleString()),
        // El is not a single-rune Countess row → card must NOT invent a per-kill
        // data row (the low-tier prose mentions the Countess, but no numeric rate)
        elHasNoCountessRow: !/Countess \(Hell\)<\/span><span class="zd-v">/.test(html('El')),
        loHasCountessRow: /Countess \(Hell\)<\/span><span class="zd-v">/.test(card),
      };
    });
    expect(r.usesPublished).toBe(true);
    expect(r.loHasCountessRow).toBe(true);
    expect(r.elHasNoCountessRow).toBe(true);
  });

  test('openDrop routes runes → rune card, grail items → calc golden card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const od = (window as any).openDrop;
      od('Lo #28');
      const runeCard = document.querySelector('#item-detail .rune-card');
      const runeName = runeCard ? (runeCard.querySelector('.gic-name')?.textContent || '').trim() : '';
      const activeRune = (window as any).__activeRune;
      od('Harlequin Crest (Shako)');
      const aid = document.querySelector('#item-detail .aid-card');
      const stillRune = document.querySelector('#item-detail .rune-card');
      return {
        isFn: typeof od,
        runeCardShown: !!runeCard,
        runeNameContains: /Lo Rune/.test(runeName),
        activeRuneSet: activeRune === 'Lo #28',
        grailAidShown: !!aid,
        grailNotRune: !stillRune,
      };
    });
    expect(r.isFn).toBe('function');
    expect(r.runeCardShown).toBe(true);
    expect(r.runeNameContains).toBe(true);
    expect(r.activeRuneSet).toBe(true);
    expect(r.grailAidShown).toBe(true);
    expect(r.grailNotRune).toBe(true);
  });

  test('closeDrop + ESC dismiss the rune card', async ({ page }) => {
    const afterClose = await page.evaluate(() => {
      (window as any).openDrop('Ber');
      (window as any).closeDrop();
      return {
        gone: !document.querySelector('#item-detail .rune-card'),
        cleared: !(window as any).__activeRune,
      };
    });
    expect(afterClose.gone).toBe(true);
    expect(afterClose.cleared).toBe(true);
    await page.evaluate(() => (window as any).openDrop('Ber'));
    expect(await page.locator('#item-detail .rune-card').count()).toBe(1);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(120);
    expect(await page.locator('#item-detail .rune-card').count()).toBe(0);
    expect(await page.evaluate(() => !!(window as any).__activeRune)).toBe(false);
  });

  test('Countess rune table: single-rune cell is clickable and opens the card; aggregated row stays plain', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderRuneTable();
      const target = document.getElementById('rune-table-target');
      const cells = [...target!.querySelectorAll('td.item-name')];
      const find = (txt: string) => cells.find(c => (c.textContent || '').includes(txt));
      const lo = find('Lo #28');
      const agg = find('Amn-Sol');
      return {
        loClickable: !!lo && lo.classList.contains('zd-item-click') && /openDrop\('Lo #28'\)/.test(lo.getAttribute('onclick') || ''),
        aggPlain: !!agg && !agg.classList.contains('zd-item-click') && !agg.getAttribute('onclick'),
      };
    });
    expect(r.loClickable).toBe(true);
    expect(r.aggPlain).toBe(true);
    // real UI flow: click the cell → rune card opens
    await page.evaluate(() => {
      (window as any).renderRuneTable();
      const cell = [...document.querySelectorAll('#rune-table-target td.item-name')]
        .find(c => (c.textContent || '').includes('Vex #26')) as HTMLElement;
      cell.click();
    });
    await page.waitForTimeout(250);
    const card = page.locator('#item-detail .rune-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.gic-name')).toContainText('Vex Rune');
    await expect(card).not.toContainText('undefined');
  });

  test('RUNE_SOURCES grid (Travincal) rune cells are clickable golden links', async ({ page }) => {
    const r = await page.evaluate(() => {
      const src = (RUNE_SOURCES as any).find((s: any) => s.id === 'travincal');
      const strip = (window as any).runeSourceDetailHtml(src);
      const div = document.createElement('div'); div.innerHTML = strip;
      const cells = [...div.querySelectorAll('td.item-name')];
      const lo = cells.find(c => (c.textContent || '').includes('Lo #28'));
      return {
        loClickable: !!lo && lo.classList.contains('zd-item-click') && /openDrop\('Lo #28'\)/.test(lo.getAttribute('onclick') || ''),
        allWired: cells.every(c => c.classList.contains('zd-item-click')),
      };
    });
    expect(r.loClickable).toBe(true);
    expect(r.allWired).toBe(true);
  });

  test('no console errors across the rune-card flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).openDrop('Lo #28');
      (window as any).openDrop('Zod');
      (window as any).openDrop('Hel');
      (window as any).openDrop('El');
      (window as any).closeDrop();
    });
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
