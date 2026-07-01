import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v396.2/v396.3/v397 → v539 — (1) any runeword stuck in the throw-out pile is RECOGNIZED on render so it's
// never thrown out (dropped from unknownReads), BUT — v539 — it is NO LONGER auto-registered to `owned` (the
// RUNEWORDS locker) or the Chronicle. An OCR'd runeword NAME is too ambiguous (UI text / a base's can-make
// list / a Forge-tab screenshot) and kept injecting phantom runewords (Konyo). Forged runewords are managed
// only via the Chronicle ✓. (2) folder auto-watch wired; (3) per-user intake logging.
test.describe('v397 runeword rescue + folder auto-watch + per-user logging', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
  });

  test('a runeword stranded in throw-out is recognized (removed from throw-out) but NOT auto-owned (v539)', async ({ page }) => {
    const r = await page.evaluate(() => {
      eval("unknownReads.add('Enigma'); unknownReads.add('Spirit'); unknownReads.add('Broad Sword (4os)')");
      (window as any).renderVault && (window as any).renderVault();   // triggers renderThrowoutReview's recognition
      return {
        enigmaInThrowout: eval("unknownReads.has('Enigma')"),
        enigmaOwned: eval("owned.has('Enigma')"),
        spiritOwned: eval("owned.has('Spirit')"),
        baseStillThrowout: eval("unknownReads.has('Broad Sword (4os)')"),  // a real base stays
      };
    });
    expect(r.enigmaInThrowout).toBe(false);   // recognized → never thrown out
    expect(r.enigmaOwned).toBe(false);        // v539 — NOT auto-registered to owned (was true pre-v539)
    expect(r.spiritOwned).toBe(false);        // v539 — same
    expect(r.baseStillThrowout).toBe(true);   // a real base still needs review
  });

  test('folder auto-watch helpers are wired (poll + on-focus quiet scan)', async ({ page }) => {
    const r = await page.evaluate(() => ({
      startWatch: typeof (window as any)._startFolderAutoWatch === 'function',
      scanFolder: typeof (window as any).vaultScanFolder === 'function',
      connectFolder: typeof (window as any).vaultConnectFolder === 'function',
    }));
    expect(r.startWatch).toBe(true);
    expect(r.scanFolder).toBe(true);
    expect(r.connectFolder).toBe(true);
  });

  test('per-user intake logger get/set works', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const def = w.getIntakeLogger();
      w.setIntakeLogger('Cousin');
      const set = w.getIntakeLogger();
      w.setIntakeLogger('');           // empties → falls back to default
      const fallback = w.getIntakeLogger();
      w.setIntakeLogger('Konyo');
      return { def, set, fallback };
    });
    expect(r.def).toBeTruthy();
    expect(r.set).toBe('Cousin');
    expect(r.fallback).toBe('Konyo');
  });
});
