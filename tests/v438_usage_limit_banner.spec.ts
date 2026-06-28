import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const TINY_JPG = Buffer.from(
  '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==',
  'base64'
);

// v438 — when the Anthropic key hits its monthly usage cap (HTTP 400 "You have reached your specified API
// usage limits…"), the intake must show a CLEAR banner (not a silent wall of "no tooltip text") and ABORT
// the batch — never fake empties for a billing problem.
test('a usage-limit error shows a clear banner and aborts (no false empties)', async ({ page }) => {
  await page.route('**/api/intake', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        error: 'upstream', status: 400,
        detail: '{"type":"error","error":{"type":"invalid_request_error","message":"You have reached your specified API usage limits. You will regain access on 2026-07-01 at 00:00 UTC"}}',
        items: [], unrecognized: [],
      }),
    })
  );
  await page.goto(URL);
  await page.waitForTimeout(2000);
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    (window as any).switchTab('tools');
    (window as any).renderVault();
  });
  // drop 3 files — once the cap is detected, the rest must be skipped, not faked as empty
  await page.setInputFiles('#vault-intake-file', [0,1,2].map(i => ({ name:`s${i}.jpg`, mimeType:'image/jpeg', buffer: TINY_JPG })));
  await page.waitForFunction(
    () => /usage limit|Last scan|registered/i.test(document.getElementById('vault-intake-report')?.textContent || ''),
    undefined, { timeout: 10000 }
  );
  const report = await page.evaluate(() => document.getElementById('vault-intake-report')!.textContent!);
  expect(report.toLowerCase()).toContain('usage limit');           // clear billing banner, not "no tooltip text"
  expect(report).toMatch(/Anthropic console/i);                    // tells the user how to fix it
  expect(report.toLowerCase()).not.toContain('no tooltip text');   // never a false-empty wall for a billing cap
});
