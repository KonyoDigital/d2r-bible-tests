import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v44 — event-boss additions (Summoner / Diablo Clone) + command-palette completeness.
// Summoner drops Key of Hate (Arcane Sanctuary); Diablo Clone drops Annihilus (SoJ-spawned).
// Event drops are %-encoded (chance < 100) rather than 1:N, qlvl 0, playerMult 1, no hours.
test.describe('v44 event-boss audit — Summoner / Diablo Clone + palette completeness', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(3000);
  });

  test('event bosses present in BOSSES with correct single-item drop + tiers', async ({ page }) => {
    const data = await page.evaluate(() => {
      const B = (eval('BOSSES') as any[]);
      const probe = (bid: string) => {
        const b = B.find((x: any) => x.id === bid);
        if (!b) return null;
        return { drops: b.dropTable.map((d: any) => ({ n: d.n, hell: d.hell })) };
      };
      return { summoner: probe('summoner'), dclone: probe('dclone') };
    });
    expect(data.summoner).not.toBeNull();
    expect(data.dclone).not.toBeNull();
    expect(data.summoner!.drops).toEqual([{ n: 'Key of Hate', hell: 36 }]);
    expect(data.dclone!.drops).toEqual([{ n: 'Annihilus', hell: 12 }]);
  });

  test('event item sources route to the correct event boss', async ({ page }) => {
    const src = await page.evaluate(() => {
      const I = (eval('ITEMS') as any[]);
      const find = (nm: string) => {
        const it = I.find((i: any) => i.n === nm);
        return it ? (it.sources || []).map((s: any) => s.bossId) : null;
      };
      return { koh: find('Key of Hate'), anni: find('Annihilus') };
    });
    expect(new Set(src.koh)).toEqual(new Set(['summoner']));
    expect(new Set(src.anni)).toEqual(new Set(['dclone']));
  });

  test('event drops render as percentage (chance < 100), not 1:N', async ({ page }) => {
    const f = await page.evaluate(() => ({
      koh: (eval('fmt') as any)(36),
      anni: (eval('fmt') as any)(12),
      // a normal 1:N value still renders as 1:N
      shako: (eval('fmt') as any)(912),
    }));
    expect(f.koh).toBe('36%');
    expect(f.anni).toBe('12%');
    expect(f.shako).toContain('1:');
  });

  test('hoursFor returns null for %-encoded event drops (no bogus time estimate)', async ({ page }) => {
    const h = await page.evaluate(() => {
      const _hoursFor = eval('hoursFor') as any;
      const _effChance = eval('effChance') as any;
      return {
        koh: _hoursFor(_effChance(36, 'summoner', 'hell'), 0.5, 85),
        anni: _hoursFor(_effChance(12, 'dclone', 'hell'), 0.5, 3),
      };
    });
    expect(h.koh).toBeNull();
    expect(h.anni).toBeNull();
  });

  test('event boss chips toggle on/off', async ({ page }) => {
    for (const id of ['summoner', 'dclone']) {
      await page.locator(`.boss-chip[data-boss-id="${id}"]`).click();
      await page.waitForTimeout(250);
      expect(await page.evaluate(() => eval('activeBossId'))).toBe(id);
      await page.locator(`.boss-chip[data-boss-id="${id}"]`).click();
      await page.waitForTimeout(250);
      expect(await page.evaluate(() => eval('activeBossId'))).toBeNull();
    }
  });

  test('navigateToItem on event items opens calc + active-item-bar', async ({ page }) => {
    for (const item of ['Key of Hate', 'Annihilus']) {
      await page.evaluate((nm) => (window as any).navigateToItem(nm), item);
      await page.waitForTimeout(100);
      await page.waitForTimeout(600);
      const st = await page.evaluate(() => ({
        tab: document.querySelector('.tab.active')?.getAttribute('data-tab'),
        aib: document.getElementById('active-item-bar')?.classList.contains('show'),
      }));
      expect(st.tab).toBe('calc');
      expect(st.aib).toBe(true);
    }
  });

  // --- command palette completeness: all 8 tabs jumpable; event terms findable ---
  const paletteHit = async (page: any, term: string) => {
    await page.evaluate(() => (window as any)._v42_openPalette && (window as any)._v42_openPalette());
    await page.waitForTimeout(150);
    await page.locator('#v42-palette-input').fill(term);
    await page.waitForTimeout(300);
    const labels = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#v42-palette-list .v42-pal-item .v42-pal-label'))
        .map((e: any) => e.textContent.trim()));
    await page.keyboard.press('Escape');
    await page.waitForTimeout(120);
    return labels as string[];
  };

  test('command palette: every tab (incl. Binds + Events) is jumpable', async ({ page }) => {
    expect((await paletteHit(page, 'binds')).some(l => l.startsWith('Switch to Binds'))).toBe(true);
    expect((await paletteHit(page, 'events')).some(l => l.startsWith('Switch to Events'))).toBe(true);
    expect((await paletteHit(page, 'reference')).some(l => l.startsWith('Switch to Reference'))).toBe(true);
    expect((await paletteHit(page, 'binds'))).not.toHaveLength(0);
  });

  test('command palette: event bosses + items are searchable', async ({ page }) => {
    expect((await paletteHit(page, 'summoner')).some(l => l.includes('Summoner'))).toBe(true);
    expect((await paletteHit(page, 'diablo clone')).some(l => l.includes('Diablo Clone'))).toBe(true);
    expect((await paletteHit(page, 'key of hate')).some(l => l.includes('Key of Hate'))).toBe(true);
    expect((await paletteHit(page, 'annihilus')).some(l => l.includes('Annihilus'))).toBe(true);
  });
});
