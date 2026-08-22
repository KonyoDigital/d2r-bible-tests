import { test, expect } from './_net_stub';
import * as path from 'path';
import { seedIntake } from './_intake';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v567 — THE AUTO-RESCAN MONEY LOOP (live incident 2026-07-04 21:30-21:43): a screenshot whose AI read
// matched NOTHING was hard-DELETED from the seen-ledger (v413.1, so a manual re-scan could retry it) — but
// the v396.3 auto-watch polls every 12s, so every no-match file was re-billed to the AI forever (Konyo's 3
// stash shots → 40+ blank sessions in 13 minutes, flooding the journal). Fix: no-match files get a soft
// 'retry' mark — SEEN to the quiet auto-scan, FRESH to a manual 🔄 Scan. Plus a scan mutex (double-fire race
// produced session pairs 1s apart with contradictory reads of the same files).

const TINY_JPG = Buffer.from(
  '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64'
);

test('a NO-MATCH read gets a soft retry mark — never deleted (the loop-maker), never auto-re-read', async ({ page }) => {
  await page.route('**/api/intake', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: [], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) }));
  await page.goto(URL); await page.waitForTimeout(1800);
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    (window as any).switchTab('tools'); (window as any).renderVault();
  });
  await seedIntake(page, 'vault', [{ name: 'nomatch.png', mimeType: 'image/png', buffer: TINY_JPG }]);
  await page.waitForFunction(() => /Last scan/.test(document.getElementById('vault-intake-report')?.textContent || ''), undefined, { timeout: 15000 });
  const seen = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}'));
  expect(seen['nomatch.png']).toBe('retry');       // soft mark: the quiet auto-scan skips it (truthy)…
  // …and the MANUAL legacy scan offers it as fresh again (recovery intent preserved)
  const fresh = await page.evaluate(() => {
    const w: any = window;
    const f = new File([new Uint8Array(10)], 'nomatch.png', { type: 'image/png' });
    w.vaultScanFolderLegacy([f]);
    return (document.getElementById('vault-intake-report')?.textContent || '');
  });
  expect(fresh).toMatch(/New\s*1|1\s*new/i);       // retry-marked file counts as NEW for the manual scan
});

test('a MATCHED read gets the hard seen mark — never offered again, even by a manual scan', async ({ page }) => {
  await page.route('**/api/intake', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ items: ['The Stone of Jordan'], unrecognized: [], usage: { in: 500, out: 10, cached: 0 } }) }));
  await page.goto(URL); await page.waitForTimeout(1800);
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    (window as any).switchTab('tools'); (window as any).renderVault();
  });
  await seedIntake(page, 'vault', [{ name: 'hit.png', mimeType: 'image/png', buffer: TINY_JPG }]);
  await page.waitForFunction(() => /Last scan/.test(document.getElementById('vault-intake-report')?.textContent || ''), undefined, { timeout: 15000 });
  const r = await page.evaluate(() => {
    const w: any = window;
    const seen = JSON.parse(localStorage.getItem('d2r_intakeSeen') || '{}');
    const f = new File([new Uint8Array(10)], 'hit.png', { type: 'image/png' });
    w.vaultScanFolderLegacy([f]);
    return { mark: seen['hit.png'], menu: (document.getElementById('vault-intake-report')?.textContent || '') };
  });
  expect(r.mark).toBe(1);                          // hard mark
  expect(r.menu).not.toMatch(/New\s*1|1\s*new/i);  // not offered as new again
});
