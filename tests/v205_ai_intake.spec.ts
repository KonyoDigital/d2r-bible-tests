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
    expect(r.report).toContain('2 NEW logged');  // v342: report card "✓ 2 NEW logged + assigned"
    expect(r.report).toContain('Hephast⚒ The Armorer');
    expect(r.report).toContain('≈$');  // v342: cost shown in the card header (was "of API budget used")
  });

  test('re-uploading the SAME file is skipped for free — zero second AI read (v342.27 manual seen-ledger)', async ({ page }) => {
    let calls = 0;
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) => {
      calls++;
      return route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Harlequin Crest (Shako)'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }),
      });
    });
    // first upload reads normally
    await page.setInputFiles('#vault-intake-file', { name: 'dup.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'),
      undefined, { timeout: 10000 }
    );
    const after1 = calls;
    expect(after1).toBeGreaterThan(0);
    // SAME filename again → manual seen-ledger skips it: "Nothing new to read", and NO new AI call
    await page.setInputFiles('#vault-intake-file', { name: 'dup.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(
      () => (document.getElementById('vault-intake-report')?.textContent || '').includes('Nothing new to read'),
      undefined, { timeout: 10000 }
    );
    const report = await page.evaluate(() => document.getElementById('vault-intake-report')!.textContent!);
    expect(report).toContain('already read');
    expect(calls).toBe(after1); // zero additional reads — the repeat was free
  });

  test('re-reading a MULTI-KEEP staple under target keeps an extra copy, not a discard (v342.28)', async ({ page }) => {
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Raven Frost'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }),
      })
    );
    // first file → NEW (1 copy)
    await page.setInputFiles('#vault-intake-file', { name: 'raven1.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    // DIFFERENT filename, SAME item → already-owned but under Raven Frost's default target (4) → extra copy
    await page.setInputFiles('#vault-intake-file', { name: 'raven2.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('extra copies'), undefined, { timeout: 10000 });
    const r = await page.evaluate(() => ({
      count: eval('copies')['Raven Frost'],
      report: document.getElementById('vault-intake-report')!.textContent!,
      persisted: JSON.parse(localStorage.getItem('d2r_copies') || '{}'),
    }));
    expect(r.count).toBe(2);
    expect(r.persisted['Raven Frost']).toBe(2);
    expect(r.report).toContain('extra copies');
  });

  test('v343 — the READ request carries the cropped flag: true when a tooltip was located, false when not', async ({ page }) => {
    // The locate pass (kind:'locate') decides whether the image gets cropped to ONE tooltip; the
    // follow-up READ must tell the backend so it can enforce single-item discipline (one hovered
    // item = one registered thing). Capture both request bodies and assert the wiring.
    const reads: any[] = [];
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      if (body.kind === 'locate') {
        // locate succeeds → a box is returned → client crops → read should be cropped:true
        return route.fulfill({ status: 200, contentType: 'application/json',
          body: JSON.stringify({ found: true, box: [0.2, 0.2, 0.6, 0.6] }) });
      }
      reads.push(body);
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['The Stone of Jordan'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }) });
    });
    await page.setInputFiles('#vault-intake-file', { name: 'cropped.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(() => (document.getElementById('vault-intake-report')?.textContent || '').includes('AI intake done'), undefined, { timeout: 10000 });
    expect(reads.length).toBe(1);
    expect(reads[0].cropped).toBe(true);

    // now locate FAILS (no single tooltip) → full image → read should be cropped:false (no hard cap)
    const reads2: any[] = [];
    await page.unroute('**/api/intake');
    await page.route('**/api/intake', (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      if (body.kind === 'locate') {
        return route.fulfill({ status: 200, contentType: 'application/json',
          body: JSON.stringify({ found: false, box: [0, 0, 0, 0] }) });
      }
      reads2.push(body);
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ items: ['Manald Heal'], unrecognized: [], usage: { in: 800, out: 30, cached: 0 } }) });
    });
    await page.setInputFiles('#vault-intake-file', { name: 'fullimg.jpg', mimeType: 'image/jpeg', buffer: TINY_JPG });
    await page.waitForFunction(() => (eval('owned') as Set<string>).has('Manald Heal'), undefined, { timeout: 10000 });
    expect(reads2.length).toBe(1);
    expect(reads2[0].cropped).toBe(false);
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
