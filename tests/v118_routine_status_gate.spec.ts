import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v118 — the v41 routine-status widget injects <script> tags for routine_status.js from
// 3 fallback paths. routine_status.js only exists next to the LOCAL file:// copies; the
// deployed https site never serves it, so each path 404s to the SPA HTML fallback and the
// browser logs a "Refused to execute script (MIME 'text/html')" error the onerror handler
// can't suppress — 3 errors every 60s on the live site. Fix: gate the injection to
// location.protocol === 'file:' so the public site never attempts it (widget shows its
// idle "— / —" state instead). file:// behaviour (where the stub exists) is unchanged.
test.describe('v118 routine-status loader gated to file://', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  test('the loader carries the file:// protocol gate', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fn = (window as any)._v41_loadStatusScript;
      return {
        isFn: typeof fn === 'function',
        hasGate: typeof fn === 'function' && /location\.protocol\s*!==\s*'file:'/.test(fn.toString()),
      };
    });
    expect(r.isFn).toBe(true);
    expect(r.hasGate).toBe(true);
  });

  test('on file:// the local stub still loads (no regression)', async ({ page }) => {
    // The repo ships routine_status.js next to bible.html (first fallback path), so on
    // file:// the gate passes and window.ROUTINE_STATUS is populated by the stub.
    const loaded = await page.evaluate(() => typeof (window as any).ROUTINE_STATUS !== 'undefined');
    expect(loaded).toBe(true);
  });

  test('no console errors on load, and none from a manual status refresh', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.reload();
    await page.waitForTimeout(800);
    // force a refresh cycle (what the 60s interval / ↻ button do) — must stay clean
    await page.evaluate(() => (window as any)._v41_refreshStatus && (window as any)._v41_refreshStatus());
    await page.waitForTimeout(500);
    expect(errs).toEqual([]);
  });
});
