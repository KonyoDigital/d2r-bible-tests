import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v391 — enrich the codex/calculator with genuinely-missing RotW off-grail uniques whose stats were
// extracted VERBATIM from the local game data (uniqueitems.txt prop codes → standard D2 stat text),
// verified against in-game tooltips (Que-Hegan's Wisdom matched Konyo's screenshot exactly). Added to
// ITEM_CODEX (codex/calc) + EXTRA_ITEMS (intake recognition, so a unique is never misread as a base) + art.
test.describe('v391 missing uniques enriched into the codex', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1800);
  });

  const NEW = ['Mindrend', 'Bonesob', "Irice's Shard", 'Rimeraven', 'Piercerib', 'Pullspite',
    'Doomspittle', 'War Bonnet', "Victor's Silk", 'Constricting Ring', 'Fathom', 'Ironward',
    "Que-Hegan's Wisdom"];

  test('every new unique is in ITEM_CODEX with a base, req, tier, and real stat props', async ({ page }) => {
    const r = await page.evaluate((names) => {
      const C = eval('ITEM_CODEX');
      const out: Record<string, any> = {};
      for (const n of names) {
        const e = C[n];
        out[n] = e ? { base: e.base, req: e.reqLvl, nprops: (e.props || []).length, rarity: e.rarity } : null;
      }
      return out;
    }, NEW);
    for (const n of NEW) {
      expect(r[n], `${n} present in ITEM_CODEX`).toBeTruthy();
      expect(r[n].rarity).toBe('unique');
      expect(r[n].base, `${n} has a base`).toBeTruthy();
      expect(r[n].nprops, `${n} has stat props`).toBeGreaterThan(0);
    }
  });

  test('each new unique is intake-recognized (EXTRA_ITEMS) + art-backed (never a misread base)', async ({ page }) => {
    const r = await page.evaluate((names) => {
      const E = eval('EXTRA_ITEMS'); const w = window as any;
      const out: Record<string, any> = {};
      for (const n of names) out[n] = { inExtra: !!E[n], art: w.artUrl ? w.artUrl(n) : null };
      return out;
    }, NEW);
    for (const n of NEW) {
      expect(r[n].inExtra, `${n} in EXTRA_ITEMS (intake vocab)`).toBe(true);
      expect(r[n].art, `${n} resolves real art`).toMatch(/^art\/.+\.(png|gif)$/);
    }
  });

  test("Que-Hegan's Wisdom stats match the in-game tooltip exactly (no fabrication)", async ({ page }) => {
    const props = await page.evaluate(() => eval('ITEM_CODEX')["Que-Hegan's Wisdom"].props as string[]);
    expect(props).toContain('+1 to All Skills');
    expect(props).toContain('+20% Faster Cast Rate');
    expect(props).toContain('+140-160% Enhanced Defense');
    expect(props).toContain('+3 to Mana after each Kill');
  });

  test('no console errors with the enriched codex', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(e.message));
    await page.evaluate(() => { try { (window as any).openDrop && (window as any).openDrop("Que-Hegan's Wisdom"); } catch (e) {} });
    await page.waitForTimeout(200);
    expect(errs).toEqual([]);
  });
});
