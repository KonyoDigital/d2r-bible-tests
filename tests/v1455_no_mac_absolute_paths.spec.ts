import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

// v1455 — REG-031 guard. The routine-status loader used to inject two ABSOLUTE Mac paths
// (/Users/konyo/d2r_bible_routines/... and /Users/konyo/Downloads/...) on every file:// load.
// On Konyo's Mac both resolve, so the Mac saw a clean console — but on the Linux CI runner
// (and the Windows cousin) each injection was a guaranteed net::ERR_FILE_NOT_FOUND: exactly
// 2 console errors on EVERY page load. That pinned Routine G at 7/8 categories and tripped
// the ~76 "no console errors" specs, and it was invisible to every Mac-side test.
//
// This spec is machine-independent BY CONSTRUCTION: it copies bible.html to a temp dir that
// is NOT under /Users/, which is what CI looks like. Any absolute /Users/ fetch is then a
// bug no matter whose machine runs the test. Asserting on REQUEST URLS (not console text)
// keeps it precise — the temp copy has no art/ siblings, so unrelated 404s are expected.
test.describe('v1455 — no Mac-absolute fetches off a /Users/ host', () => {
  let tmpDir = '';
  let tmpBible = '';

  test.beforeAll(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'd2r-ci-like-'));
    const repo = path.resolve(__dirname, '..');
    tmpBible = path.join(tmpDir, 'bible.html');
    fs.copyFileSync(path.join(repo, 'bible.html'), tmpBible);
    // ship the sibling stub too — it is the last (and off-Mac only) fallback path
    fs.copyFileSync(path.join(repo, 'routine_status.js'), path.join(tmpDir, 'routine_status.js'));
  });

  test.afterAll(() => {
    if (tmpDir) fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  test('a CI-like host fetches 0 absolute /Users/ paths and 1 sibling routine_status.js', async ({ page }) => {
    expect(tmpBible.startsWith('/Users/')).toBe(false); // the premise of this test
    const absolute: string[] = [];
    const statusReqs: string[] = [];
    page.on('request', (r) => {
      const u = r.url();
      if (u.startsWith('file:///Users/')) absolute.push(u);
      if (/routine_status\.js/.test(u)) statusReqs.push(u);
    });
    await page.goto('file://' + tmpBible);
    await page.waitForTimeout(2500);
    expect(absolute, 'off-Mac hosts must never fetch /Users/… paths').toEqual([]);
    expect(statusReqs.length, 'exactly the sibling stub, no baker fallbacks').toBe(1);
    expect(statusReqs[0]).toContain(tmpDir);
  });

  test('failed requests on a CI-like host name no routine_status path', async ({ page }) => {
    const failed: string[] = [];
    page.on('requestfailed', (r) => failed.push(r.url()));
    await page.goto('file://' + tmpBible);
    await page.waitForTimeout(2500);
    const statusFails = failed.filter((u) => /routine_status\.js/.test(u));
    expect(statusFails, `routine_status must not 404 off-Mac (got ${statusFails.length})`).toEqual([]);
  });

  test('on Konyo’s Mac the live baker path is still tried first (no regression)', async ({ page }) => {
    const repoBible = path.resolve(__dirname, '..', 'bible.html');
    test.skip(!repoBible.startsWith('/Users/'), 'Mac-only half of the contract');
    const statusReqs: string[] = [];
    page.on('request', (r) => { if (/routine_status\.js/.test(r.url())) statusReqs.push(r.url()); });
    await page.goto('file://' + repoBible);
    await page.waitForTimeout(2500);
    expect(statusReqs.length).toBeGreaterThan(0);
    expect(statusReqs[0]).toContain('/d2r_bible_routines/obsidian_data/routine_status.js');
  });
});
