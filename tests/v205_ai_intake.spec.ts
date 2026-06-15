// v205 — 📸 AI intake: screenshots → /api/intake (Pages Function holding the
// Anthropic key server-side) → Claude vision extracts item names constrained
// to the ITEMS vocabulary → ✓ owned + vault auto-assign + report. The endpoint
// is MOCKED here (page.route) — the real one was verified live end-to-end
// (Hephasto banner screenshot → correct unrecognized extraction, ~$0.001/shot).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// 1×1 white JPEG for the file input
const TINY_JPG = Buffer.from(
  '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64'
);

test.describe('v205 AI intake', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: ['Harlequin Crest (Shako)', 'The Stone of Jordan'],
          unrecognized: ["Hephast⚒ The Armorer"],
          usage: { in: 800, out: 30, cached: 0 },
        }),
      })
    );
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => {
      localStorage.clear();
      // file:// pages can't fetch relative paths — point the intake at a
      // routable http URL (page.route intercepts it before any real network)
      localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
      (window as any).switchTab('tools');
      (window as any).renderVault();
    });
  });

  test('intake button + file input exist in the vault toolbar', async ({ page }) => {
    const r = await page.evaluate(() => ({
      btn: !!document.querySelector('#mule-vault-card .vault-btn[title*="AI reads"]'),
      input: !!document.getElementById('vault-intake-file'),
      multiple: (document.getElementById('vault-intake-file') as HTMLInputElement)?.multiple,
    }));
    expect(r.btn).toBe(true);
    expect(r.input).toBe(true);
    expect(r.multiple).toBe(true);
  });

  test('uploading a screenshot logs items as owned, assigns them, persists, and reports', async ({ page }) => {
    await page.setInputFiles('#vault-intake-file', {
      name: 'stash.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG,
    });
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'),
      undefined, { timeout: 10000 }
    );
    const r = await page.evaluate(() => ({
      report: document.getElementById('vault-intake-report')!.textContent!,
      ownedShako: eval('owned').has('Harlequin Crest (Shako)'),
      ownedSoj: eval('owned').has('The Stone of Jordan'),
      persisted: JSON.parse(localStorage.getItem('d2r_owned') || '[]'),
      assigned: JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'),
    }));
    expect(r.ownedShako).toBe(true);
    expect(r.ownedSoj).toBe(true);
    expect(r.persisted).toContain('Harlequin Crest (Shako)');
    expect(r.assigned['The Stone of Jordan']).toBe('uni-small');
    expect(r.assigned['Harlequin Crest (Shako)']).toBe('uni-armor');
    expect(r.report).toContain('2 NEW items logged');  // v310: report distinguishes NEW vs already-owned
    expect(r.report).toContain('Hephast⚒ The Armorer');
    expect(r.report).toContain('API budget');
  });

  test('endpoint failure reports an error instead of silently dropping', async ({ page }) => {
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) => route.fulfill({ status: 502, body: '{"error":"upstream"}' }));
    await page.setInputFiles('#vault-intake-file', {
      name: 'stash.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG,
    });
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'),
      undefined, { timeout: 10000 }
    );
    const report = await page.evaluate(() => document.getElementById('vault-intake-report')!.textContent!);
    expect(report).toContain('1 screenshot failed');
  });
});
