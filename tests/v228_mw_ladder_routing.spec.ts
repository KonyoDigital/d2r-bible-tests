// v228 — Most-Wanted ladder routing audit (Konyo, 2026-06-13): clicking
// #9 Sunder Charms must open the golden Sunder material card with ALL SIX
// charms (it previously dumped you on the bare RotW tab) — and every other
// row must route to a real card (plain rows) or expand its recipe (runeword
// rows). Same per-entity-routing family as v136 (a row that routes somewhere
// generic instead of ITS card is a latent misroute).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const SIX = ['Bone Break', 'Black Cleft', 'Crack of the Heavens', 'Cold Rupture', 'Flame Rift', 'Rotting Fissure'];

test.describe('v228 most-wanted ladder routing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2300);
  });

  test('#9 Sunder Charms opens the golden card with all 6 charms', async ({ page }) => {
    const r = await page.evaluate((six: string[]) => {
      const row = [...document.querySelectorAll('#most-wanted .mw-row')]
        .find((x: any) => x.textContent.includes('Sunder Charms')) as HTMLElement;
      row.click();
      const txt = document.getElementById('item-detail')?.textContent || '';
      return { all6: six.every((c) => txt.includes(c)), onRotwTabOnly: txt.length < 200 };
    }, SIX);
    expect(r.all6).toBe(true);
    expect(r.onRotwTabOnly).toBe(false);
  });

  test('every ladder row routes: plain rows open a real card, runeword rows expand their recipe', async ({ page }) => {
    const r = await page.evaluate(() => {
      const out: any[] = [];
      [...document.querySelectorAll('#most-wanted .mw-row')].forEach((row: any) => {
        if (row.querySelector('.mw-caret')) {
          row.click();
          out.push({ row: row.querySelector('.mw-name')?.textContent.trim(), ok: row.classList.contains('open'), kind: 'recipe' });
          row.click();
          return;
        }
        row.click();
        const len = (document.getElementById('item-detail')?.textContent || '').length;
        out.push({ row: row.querySelector('.mw-name')?.textContent.trim(), ok: len > 200, kind: 'card' });
      });
      return out;
    });
    expect(r.length).toBe(10);
    for (const e of r) expect(e.ok, `${e.kind} route failed for: ${e.row}`).toBe(true);
  });

  test('ROTW Endgame section want-chip "Sunder Charms" also opens the 6-charm card', async ({ page }) => {
    const r = await page.evaluate((six: string[]) => {
      const chip = [...document.querySelectorAll('#most-wanted .mw-want-chip')]
        .find((c: any) => c.textContent.trim() === 'Sunder Charms') as HTMLElement;
      chip.click();
      const txt = document.getElementById('item-detail')?.textContent || '';
      return six.every((c) => txt.includes(c));
    }, SIX);
    expect(r).toBe(true);
  });
});
