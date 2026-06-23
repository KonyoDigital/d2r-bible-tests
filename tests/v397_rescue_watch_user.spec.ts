import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v396.2/v396.3/v397 — (1) any runeword stuck in the throw-out pile from an old read is RESCUED on render
// (recognized → owned, dropped from unknownReads) — "never throw out an Enigma"; (2) the folder auto-watch
// (poll + on-focus quiet scan) is wired so new screenshots auto-register; (3) per-user intake logging.
test.describe('v397 runeword rescue + folder auto-watch + per-user logging', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
  });

  test('a runeword stranded in throw-out is rescued (recognized, removed from unknownReads)', async ({ page }) => {
    const r = await page.evaluate(() => {
      eval("unknownReads.add('Enigma'); unknownReads.add('Spirit'); unknownReads.add('Broad Sword (4os)')");
      (window as any).renderVault && (window as any).renderVault();   // triggers renderThrowoutReview's rescue
      return {
        enigmaInThrowout: eval("unknownReads.has('Enigma')"),
        enigmaOwned: eval("owned.has('Enigma')"),
        spiritOwned: eval("owned.has('Spirit')"),
        baseStillThrowout: eval("unknownReads.has('Broad Sword (4os)')"),  // a real base stays
      };
    });
    expect(r.enigmaInThrowout).toBe(false);
    expect(r.enigmaOwned).toBe(true);
    expect(r.spiritOwned).toBe(true);
    expect(r.baseStillThrowout).toBe(true);
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
