import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// CONVERGENCE LOCK (2026-05-31) — the shipping app is bible.html.
// A prior bug had 10 specs silently validating the stale bible_routes.html fork,
// so half the suite green-lit a file that never ships. This guard is a static
// source-scan (no browser) that FAILS CI the instant any spec's BIBLE target — or
// any sweep-script (H/J/K/L) page.goto default — points back at the fork.

const TESTS_DIR = __dirname;
const REPO_ROOT = path.resolve(__dirname, '..');
const SELF = path.basename(__filename);

test.describe('convergence lock — canonical target is bible.html', () => {
  test('no spec declares its BIBLE/BIBLE_URL target as bible_routes.html', () => {
    const specs = fs.readdirSync(TESTS_DIR).filter(f => f.endsWith('.spec.ts') && f !== SELF);
    const offenders: string[] = [];
    for (const f of specs) {
      const src = fs.readFileSync(path.join(TESTS_DIR, f), 'utf8');
      for (const line of src.split('\n')) {
        if (/const\s+BIBLE(_URL)?\s*=/.test(line) && /bible_routes\.html/.test(line)) {
          offenders.push(`${f}: ${line.trim()}`);
        }
      }
    }
    expect(offenders, `specs still targeting the stale fork:\n${offenders.join('\n')}`).toEqual([]);
    expect(specs.length, 'guard should find the spec suite to scan').toBeGreaterThan(10);
  });

  test('every sweep script (H/J/K/L) navigates to bible.html, not the fork', () => {
    const sweeps = ['H_sweep.js', 'J_screens.js', 'K_perf.js', 'L_integrity.js'];
    const offenders: string[] = [];
    for (const f of sweeps) {
      const src = fs.readFileSync(path.join(REPO_ROOT, f), 'utf8');
      for (const line of src.split('\n')) {
        if (!/page\.goto/.test(line)) continue;
        if (/bible_routes\.html/.test(line)) offenders.push(`${f} (stale fork): ${line.trim()}`);
        // v533 — a hardcoded ABSOLUTE path (/Users/… , /home/… , C:\…) loads fine on Konyo's Mac but breaks
        // on the CI runner (/home/runner/…) + Windows. The goto MUST be portable (path.resolve(__dirname, …)).
        if (/['"]\/(Users|home|root)\//.test(line) || /['"][A-Za-z]:\\/.test(line)) {
          offenders.push(`${f} (hardcoded absolute path — not portable): ${line.trim()}`);
        }
      }
    }
    expect(offenders, `sweep scripts must target bible.html via a PORTABLE path:\n${offenders.join('\n')}`).toEqual([]);
  });
});
