import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v296 — the Immortal King set pieces were stored with the abbreviation "IK's X", but the
// game (and the AI reading a screenshot) uses the full "Immortal King's X". So the Vault
// intake never matched them → all 6 IK pieces were read-but-skipped. Renamed to full names
// (+ the 2 art-map keys) so findSetPiece + the intake vocabulary recognise them.

const IK = ["Immortal King's Will", "Immortal King's Soul Cage", "Immortal King's Detail",
            "Immortal King's Forge", "Immortal King's Pillar", "Immortal King's Stone Crusher"];

test.describe('v296 Immortal King set-piece names', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('all 6 IK pieces resolve via findSetPiece under their full in-game names', async ({ page }) => {
    const hits = await page.evaluate((names) => {
      const fsp = (window as any).findSetPiece;
      return names.map((n: string) => ({ n, set: fsp(n)?.set?.name || null }));
    }, IK);
    for (const h of hits) {
      expect(h.set, `${h.n} should resolve`).toBe('Immortal King (Barb)');
    }
  });

  test('the IK pieces are in the Vault intake vocabulary (so a screenshot read matches)', async ({ page }) => {
    const vocab = await page.evaluate(() => (window as any).__setPieceNames ? (window as any).__setPieceNames() : []);
    for (const n of IK) expect(vocab).toContain(n);
    // and the old abbreviation is gone
    expect(vocab.some((v: string) => /^IK's /.test(v))).toBe(false);
  });

  test('the renamed IK pieces keep their art (art-map keys updated too)', async ({ page }) => {
    const r = await page.evaluate(() => ({
      soul: (window as any).artUrl ? !!(window as any).artUrl("Immortal King's Soul Cage") : false,
      will: (window as any).artUrl ? !!(window as any).artUrl("Immortal King's Will") : false,
      oldGone: (window as any).artUrl ? !(window as any).artUrl("IK's Will") : true,
    }));
    expect(r.soul).toBe(true);
    expect(r.will).toBe(true);
    expect(r.oldGone).toBe(true);
  });
});
