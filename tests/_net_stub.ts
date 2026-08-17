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
    /* v1749 — AND THE FONTS, for the same reason the line above exists. bible.html pulls its
       typeface from fonts.googleapis.com / fonts.gstatic.com. On a runner whose outbound network is
       slow or blocked those requests fail, and two board specs assert "no console errors" — so they
       went red on the weather rather than on the code. Measured by blocking external hosts locally:
       the reference tab logs "Failed to load resource" and `.set-card-header` measures 0px tall,
       because the bar's height comes from text that has no font to lay out. The SAME collapse
       reproduces on v1735, the last green Routine I — so it is fragility that predates this work,
       not a regression in it.

       ⚠ v1754 — THE FONT HALF OF THAT DIAGNOSIS DID NOT REPRODUCE, and the contradiction is recorded
       rather than resolved. Re-measured with context.setOffline(true), which fails every external
       request: `.set-card-header` is **78px online, 78px offline, and 78px stubbed**. The bar keeps
       its height with no font at all.

       The flake this paragraph was written about had a different cause, found later and proven
       deterministically: v157's setup called toggleCardCollapse BLIND, that function opens with
       `if (!card) return;` — a silent no-op — so on a slow shard the card stayed COLLAPSED, and a
       collapsed card resolves every colour you ask getComputedStyle for while
       getBoundingClientRect reports 0. Forcing `.collapsed` reproduces `headerH: 0` every time;
       going offline reproduces it never. (v1751 fixed the toggle; v1753's fixture is named
       `f2trap_` for an unrelated trap in the same file.)

       Two possibilities remain open and neither is worth guessing between: the original measurement
       saw a SLOW font (a hanging request leaves text in a blocking state, which offline — failing
       instantly — cannot imitate), or it attributed the collapsed-card symptom to the font. What is
       certain is that the CONSOLE-ERROR reason for this fixture is real and re-proven: bare spec
       offline logs `net::ERR_INTERNET_DISCONNECTED`, stubbed spec offline logs nothing.
       [[feedback_contradiction_is_the_finding]]
       Fulfilled with an empty stylesheet rather than aborted: an abort is itself a failed request,
       and page.screenshot waits on fonts (chrome-cdp-mac). Empty CSS succeeds, logs nothing, and
       lets the fallback face lay the text out. */
    await page.route('**://fonts.googleapis.com/**', (r) =>
      r.fulfill({ status: 200, contentType: 'text/css; charset=utf-8', body: '/* stubbed */' })
    );
    await page.route('**://fonts.gstatic.com/**', (r) =>
      r.fulfill({ status: 200, contentType: 'font/woff2', body: Buffer.alloc(0) })
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
