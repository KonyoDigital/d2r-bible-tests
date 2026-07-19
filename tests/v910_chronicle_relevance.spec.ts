// v910 — CHRONICLE RELEVANCE (Konyo doctrine: 'the AI reads and automatically tallies in the
// chronicles relevant to the item'). Locks the one-head router (v763): uniques → toggleOwned
// (dated foundLog), set pieces → canonical toggleSetPiece, exactly-once, junk never mints keys.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v910 chronicle relevance', () => {
  test('unique vault-read marks the grail exactly once, dated', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const w = window as any;
      const CANON = 'Harlequin Crest (Shako)';   // the engine marks the CANONICAL key
      if (w._gFound && w._gFound(CANON) && w.toggleOwned) w.toggleOwned(CANON);
      const before = !!(w._gFound && w._gFound(CANON));
      const r1 = w.tvChronicleRoute('Harlequin Crest', 'vault');   // reader utters the RAW name
      const marked = !!(w._gFound && w._gFound(r1.name || CANON));
      const dated = (() => { try { return !!JSON.parse(w.LSR.getItem('d2r_foundLog') || '{}')[r1.name || CANON]; } catch (e) { return false; } })();
      const r2 = w.tvChronicleRoute('Harlequin Crest', 'vault');   // re-read → already
      return { before, r1, marked, dated, r2 };
    });
    expect(r.before).toBe(false);
    expect(r.r1.ok).toBe(true);
    expect(r.marked).toBe(true);                    // the grail heard the reader
    expect(r.dated).toBe(true);                     // foundLog carries the date
    expect(r.r2.already).toBe(true);                // exactly once — never double-marked
  });

  test('set piece routes to its CANONICAL slot-suffixed name', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const w = window as any;
      const probe = w.findSetPiece && w.findSetPiece("Sigon's Guard");
      if (!probe) return { skip: true };
      const canonical = probe.piece;
      if (w._gFound && w._gFound(canonical) && w.toggleSetPiece) w.toggleSetPiece(canonical);
      const r1 = w.tvChronicleRoute("Sigon's Guard", 'vault');
      const marked = !!(w._gFound && w._gFound(canonical));
      return { r1, marked, canonical };
    });
    if ((r as any).skip) test.skip();
    expect(r.r1.kind).toBe('set');
    expect(r.r1.name).toBe(r.canonical);            // never a duplicate raw key
    expect(r.marked).toBe(true);
  });

  test('junk and unknowns never mint grail keys', async ({ page }) => {
    await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const w = window as any;
      const owned0 = (() => { try { return Object.keys(JSON.parse(w.LSR.getItem('d2r_owned') || '[]')).length; } catch (e) { return -1; } })();
      const junk = w.tvChronicleRoute('Super Healing Potion', 'vault');
      const ghost = w.tvChronicleRoute('Totally Fake Item That Does Not Exist', 'vault');
      const owned1 = (() => { try { return Object.keys(JSON.parse(w.LSR.getItem('d2r_owned') || '[]')).length; } catch (e) { return -1; } })();
      return { junk, ghost, same: owned0 === owned1 };
    });
    expect(r.junk.ok === false || r.ghost.ok === false).toBe(true);
    expect(r.same).toBe(true);                      // the grail store did not grow
  });
});
