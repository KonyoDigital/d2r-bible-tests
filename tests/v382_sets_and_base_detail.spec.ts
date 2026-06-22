// v382 — (1) the 17 classic + 2 RotW sets are integrated: every piece resolves (search/tracker/ID card)
// and each set has its golden detailed card (setDetailHtml from the rich codex). (2) base ID cards/tooltips
// now show the full BASE_DB detail grid (dmg, sockets, reqs, qlvl, weight) like diablo2.io.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v382 sets + base detail', () => {
  test.beforeEach(async ({ page }) => { await page.goto(URL); await page.waitForTimeout(2000); });

  test('newly-added sets resolve pieces + render the golden detailed card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return {
        cleglawPiece: !!w.findSetPiece("Cleglaw's Tooth"),
        arcticPiece: !!w.findSetPiece('Arctic Furs'),
        horazonPiece: !!w.findSetPiece("Horazon's Hold"),
        banePiece: !!w.findSetPiece("Bane's Oathmaker"),
        arcticCodex: !!w._setCodexByName('Arctic Gear'),
        arcticCard: w.setDetailHtml('Arctic Gear') || '',
        horazonCard: w.setDetailHtml("Horazon's Splendor") || '',
      };
    });
    expect(r.cleglawPiece).toBe(true);
    expect(r.arcticPiece).toBe(true);
    expect(r.horazonPiece).toBe(true);
    expect(r.banePiece).toBe(true);
    expect(r.arcticCodex).toBe(true);
    expect(r.arcticCard).toContain('Arctic Furs');       // piece tile
    expect(r.arcticCard).toContain('Cannot Be Frozen');  // full set bonus
    expect(r.horazonCard).toContain('Warlock');          // RotW Warlock set bonus
  });

  test('base ID card detail grid (BASE_DB) renders for a base', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return {
        crypticSword: w._baseDetailRows('Cryptic Sword'),
        monarch: w._baseDetailRows('Monarch'),
        empty: w._baseDetailRows('Not A Real Base'),
      };
    });
    expect(r.crypticSword).toContain('Max Sockets');
    expect(r.crypticSword).toContain('Req Strength');
    expect(r.crypticSword).toContain('Quality Level');
    expect(r.monarch).toContain('Req Strength');
    expect(r.empty).toBe('');   // unknown base → no grid (never fabricates)
  });
});
