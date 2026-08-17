// Shared network-stub fixture (audit 2026-06-12, hygiene item B-2).
// Specs that load external diablo2.io art AND assert "no console errors" red
// intermittently on a slow/offline link (9× net::ERR_INTERNET_DISCONNECTED in
// one full run; v114 + v136 flaked). This fixture fulfills every diablo2.io
// request with a 1×1 PNG so image loads are deterministic and silent.
// NOTE: safe for the d2art-failed assertions — they all check the onerror
// ATTRIBUTE markup or assert the failed class is ABSENT, never that a real
// network failure occurred.
import { test as base } from '@playwright/test';

const PNG_1X1 = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64'
);

export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route('**://diablo2.io/**', (r) =>
      r.fulfill({ status: 200, contentType: 'image/png', body: PNG_1X1 })
    );
    await use(page);
  },
});

/* v1749 — A CONSOLE WITH DATA BUT NO ROUTE IS AN IMPOSSIBLE STATE, AND TWELVE SPECS MODELLED IT.
   The console reads the board's world through `lsFork`, and v1736 made that honour bible.html's own
   v1499 instruction: "a reader that finds no route... must resolve UNKNOWN and read nothing.
   Guessing bare is how the harm happened." Before that it fell back to the bare key.

   Twelve console specs seed d2r_forgeSummary / d2r_grailFarm / d2r_setFarm and NO d2r_lsrRoute, so
   they were leaning on the guess that was removed — and Routine I went red on surfaces that render
   from that data (the Task Force icons in v1615). In production the state they model cannot occur:
   the data exists only because the board ran, and the board writes the route as it does.

   So the fixture supplies the route a real console always has — ONE definition, imported, never
   twelve pasted copies of a payload shape that would then drift from bible.html's. [[copy-drift]]
   OWNER, main profile: pfx '' and lpfx 'L·', which is what makes lsFork land on the bare keys these
   specs seed. */
export const OWNER_ROUTE = {
  v: 2,
  owner: true,
  id: 'spec-owner-install',
  m: 'owner',
  p: 'main',
  pfx: '',
  lpfx: 'L·',
  lp: [] as string[],
  wp: [] as string[],
};

/** Seed the world a real console reads from. Call BEFORE page.goto, like any other init script. */
export async function seedOwnerRoute(page: any) {
  await page.addInitScript((route: any) => {
    localStorage.setItem('d2r_lsrRoute', JSON.stringify(route));
  }, OWNER_ROUTE);
}

export { expect } from '@playwright/test';
