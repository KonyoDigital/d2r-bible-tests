// v375 — generic socketed/Larzuk BASES are QUANTITY items, not presence-only grail uniques.
// Two SEPARATE screenshots that read the same generic base label ("Larzuk 2H Weapon Base") are two
// DIFFERENT physical bases (Konyo's two white Threshers: same label, different files + durability) —
// so each distinct read counts as an extra copy (×N), NOT collapsed to a phantom "duplicate shot".
// A grail UNIQUE re-read still collapses (you don't own two Tyrael's).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const TINY_JPG = Buffer.from(
  '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64'
);

test.describe('v375 base quantity dedup', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Larzuk 2H Weapon Base'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }),
      })
    );
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => {
      localStorage.clear();
      localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
      (window as any).switchTab('tools');
      (window as any).renderVault();
    });
  });

  test('two base reads in ONE batch (fresh vault) → ×2 copies, NOT a collapsed duplicate shot', async ({ page }) => {
    // BOTH files in a single batch — the exact bug scenario (7 shots at once, two white Threshers).
    // _preReg = 0 at batch start, so the OLD code would collapse the 2nd to a phantom "duplicate shot".
    await page.setInputFiles('#vault-intake-file', [
      { name: 'thresher1.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG },
      { name: 'thresher2.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG },
    ]);
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    const r = await page.evaluate(() => ({
      count: eval('copies')['Larzuk 2H Weapon Base'],
      persisted: JSON.parse(localStorage.getItem('d2r_copies') || '{}'),
      report: document.getElementById('vault-intake-report')!.textContent!,
    }));
    expect(r.count).toBe(2);                                   // both counted, even in one fresh batch (NOT collapsed)
    expect(r.persisted['Larzuk 2H Weapon Base']).toBe(2);      // persisted
    expect(r.report).toContain('extra copies');                // framed as a kept copy
    expect(r.report).not.toContain('1 duplicate shot');        // the 2nd base is NOT a collapsed dup shot
  });

  test('two UNIQUE reads in ONE batch still collapse (presence-only, not a quantity item)', async ({ page }) => {
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Windforce'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }),
      })
    );
    await page.setInputFiles('#vault-intake-file', [
      { name: 'wf1.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG },
      { name: 'wf2.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG },
    ]);
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    const r = await page.evaluate(() => ({
      count: eval('copies')['Windforce'] || 1,
      report: document.getElementById('vault-intake-report')!.textContent!,
    }));
    // Windforce is a unique (target 1) — the same item photographed twice in one fresh batch →
    // collapses to one, NOT bumped to ×2. (Contrast with the base label above, which DOES count.)
    expect(r.count).toBe(1);
    expect(r.report).toContain('duplicate shot');
  });
});
