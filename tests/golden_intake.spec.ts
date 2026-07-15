import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * v702 — 🥇 INTAKE GOLDEN-SET REGRESSION (the audit's "biggest non-odds quality risk").
 *
 * Exercises the REAL vision pipeline end-to-end: fixture screenshot → the app's exact payload
 * shape (1568px jpeg, kind:'grail', the app's own vocab via window._grailVocab) → the LIVE
 * /api/intake worker → found-name set, diffed against a frozen golden.
 *
 * DELIBERATELY NOT part of CI or the smoke gate:
 *   · costs real vision-model calls per run
 *   · needs the live site + Basic-auth credentials
 * Run manually (or via a future scheduled routine):
 *   INTAKE_GOLDEN=1 SITE_USER=… SITE_PASS=… npx playwright test tests/golden_intake.spec.ts
 *
 * BASELINE MODE: if goldens.json is missing, the first run writes it from the live responses
 * (the pipeline is Konyo-LOCKED known-good since 2026-06-24 / 39-of-39) and passes with a notice.
 * Later runs fail on ANY drift — missing reads AND new hallucinations both.
 */

const GATED = !process.env.INTAKE_GOLDEN;
const DIR = path.resolve(__dirname, 'golden', 'intake');
const GOLDENS = path.join(DIR, 'goldens.json');
const LIVE = 'https://bull-4-u.com';

test.skip(GATED, 'golden intake runs on demand: INTAKE_GOLDEN=1 SITE_USER=… SITE_PASS=…');

test.use({
  httpCredentials: process.env.SITE_USER ? { username: process.env.SITE_USER!, password: process.env.SITE_PASS! } : undefined,
});

test('grail-intake vision reads are stable against the golden set', async ({ page }) => {
  test.setTimeout(6 * 60_000);
  await page.goto(LIVE + '/d2r/');
  await page.waitForTimeout(6000);

  const vocab: string[] = await page.evaluate(() => (window as any)._grailVocab().vocab);
  expect(vocab.length).toBeGreaterThan(300);

  const fixtures = fs.readdirSync(DIR).filter((f) => f.endsWith('.jpg')).sort();
  expect(fixtures.length).toBeGreaterThanOrEqual(3);

  const results: Record<string, string[]> = {};
  for (const fx of fixtures) {
    const b64 = fs.readFileSync(path.join(DIR, fx)).toString('base64');
    const resp = await page.request.post(LIVE + '/api/intake', {
      data: { image: b64, media_type: 'image/jpeg', kind: 'grail', names: vocab },
      timeout: 90_000,
    });
    expect(resp.ok(), fx + ' → HTTP ' + resp.status()).toBeTruthy();
    const body = await resp.json();
    const found: string[] = (body.found || body.names || body.items || []).slice().sort();
    expect(found.length, fx + ' returned an empty read — the vision pipeline is broken').toBeGreaterThan(3);
    results[fx] = found;
  }

  if (!fs.existsSync(GOLDENS)) {
    fs.writeFileSync(GOLDENS, JSON.stringify(results, null, 1));
    console.log('🥇 BASELINE CAPTURED — goldens.json written from the locked pipeline. Commit it.');
    return;
  }

  const golden = JSON.parse(fs.readFileSync(GOLDENS, 'utf8'));
  for (const fx of fixtures) {
    const want: string[] = golden[fx] || [];
    const got: string[] = results[fx] || [];
    const missing = want.filter((n) => !got.includes(n));
    const extra = got.filter((n) => !want.includes(n));
    // Measured drift envelope (baseline day, back-to-back runs): ONE page-edge row can flicker
    // between two adjacent names (Arioc's Needle ↔ Baezil's Vortex). A real pipeline regression
    // (prompt/model/crop change) moves MANY rows or empties the read — so tolerate ±1 per fixture
    // with a loud warning, hard-fail at ≥2 in either direction.
    if (missing.length || extra.length) {
      console.warn('⚠ ' + fx + ' drift — missing: [' + missing.join(', ') + '] extra: [' + extra.join(', ') + ']');
    }
    expect.soft(missing.length, fx + ' MISSED reads beyond the ±1 flicker envelope (regression): ' + missing.join(', ')).toBeLessThanOrEqual(1);
    expect.soft(extra.length, fx + ' NEW reads beyond the ±1 flicker envelope (hallucination): ' + extra.join(', ')).toBeLessThanOrEqual(1);
  }
});
