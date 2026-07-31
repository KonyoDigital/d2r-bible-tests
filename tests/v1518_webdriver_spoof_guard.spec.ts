import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// v1518 — THE TRAP, CLOSED (REG-084).
//
// v1499 made a browser a GUEST until a human claims it, and it identifies the SUITE by
// navigator.webdriver + file://. Three specs spoof navigator.webdriver to false — legitimately, to
// unmask motion effects the app silences under automation — and in doing so they unmasked themselves
// as guests. Every bare key they seeded landed in an `I·<id>·` world the app never reads, so the app
// saw an empty chronicle and the specs asserted against a world that did not exist.
//
// The failure mode is the dangerous kind: the spoof and the breakage are in different files, written
// months apart, and the symptom ("the milestone epic didn't fire") points at neither. This guard
// makes the pairing structural — spoof the tell, claim the world, or fail here with the reason.

const DIR = __dirname;
const SPOOF = /navigator,\s*['"]webdriver['"]/;

test('every spec that spoofs navigator.webdriver also claims the owner world', () => {
  const offenders: string[] = [];
  const spoofers: string[] = [];
  for (const f of fs.readdirSync(DIR).filter((n) => n.endsWith('.spec.ts'))) {
    if (f === path.basename(__filename)) continue;
    const src = fs.readFileSync(path.join(DIR, f), 'utf8');
    if (!SPOOF.test(src)) continue;
    spoofers.push(f);
    if (!src.includes('d2r_ownerClaim')) offenders.push(f);
  }
  expect(spoofers.length, 'the spoof pattern should still be findable — if this hits zero the regex ' +
    'has drifted and this guard is silently protecting nothing').toBeGreaterThan(0);
  expect(offenders,
    'these specs spoof navigator.webdriver, which makes the page a GUEST (v1499) — so every bare key ' +
    'they seed lands in an I·<id>· world the app never reads, and they assert against a world that ' +
    "does not exist. Add: await page.addInitScript(() => localStorage.setItem('d2r_ownerClaim', '*'));"
  ).toEqual([]);
});

test('the owner-claim escape hatch the guard depends on is still real', () => {
  // if bible.html ever stops honouring the '*' claim, the fix above becomes a no-op and every
  // spoofing spec silently rots back to guest — so the guard checks its own foundation
  const bible = fs.readFileSync(path.resolve(DIR, '..', 'bible.html'), 'utf8');
  expect(bible).toContain('d2r_ownerClaim');
  expect(bible, "the wildcard claim ('*' = any browser is the owner) is what the suite relies on")
    .toMatch(/claim\s*===\s*['"]\*['"]/);
});
