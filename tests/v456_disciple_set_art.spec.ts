// v456 — Konyo's GREEN "Dark Adherent" (Dusk Shroud body of The Disciple set) was read as Magic & Rare
// because The Disciple set wasn't in the data, and its art file was a 40x40 charm-sized sprite (looked like
// Annihilus). Adds the set (findSetPiece resolves all 5 pieces → set-green + grail vocab) and corrects the art.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v456 The Disciple set + Dark Adherent art', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any).findSetPiece && (window as any).artUrl);
  });

  test('Dark Adherent resolves as The Disciple set piece (not rare)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const sp = w.findSetPiece('Dark Adherent');
      return { found: !!sp, set: sp && sp.set && sp.set.name, base: sp && sp.base };
    });
    expect(r.found).toBe(true);
    expect(r.set).toMatch(/Disciple/);
  });

  test('all 5 Disciple pieces resolve to the set', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const pieces = ['Telling of Beads', 'Dark Adherent', 'Credendum', 'Laying of Hands', 'Rite of Passage'];
      return pieces.map((p) => ({ p, ok: !!w.findSetPiece(p) }));
    });
    for (const e of r) expect(e.ok, e.p).toBe(true);
  });

  test('Disciple pieces enter the intake vocab (so the AI reads them as grail, not rare)', async ({ page }) => {
    const inVocab = await page.evaluate(() => {
      const w = window as any;
      const names = w.__setPieceNames ? w.__setPieceNames() : [];
      return ['Dark Adherent', 'Credendum', 'Telling of Beads'].every((n) => names.includes(n));
    });
    expect(inVocab).toBe(true);
  });

  test('Dark Adherent art is the Dusk Shroud sprite, NOT the 40x40 charm-sized d2io file', async ({ page }) => {
    const art = await page.evaluate(() => (window as any).artUrl('Dark Adherent'));
    expect(art).not.toContain('d2io_darkadherent'); // the broken 40x40 file
    expect(art).toMatch(/quilted_armor|duskshroud/i); // Dusk Shroud body sprite
  });
});
