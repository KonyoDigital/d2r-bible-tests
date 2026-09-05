// v2473 — REG-443, asserted BEHAVIOURALLY, because the source guard could be refactored past.
//
// THE LAW: this page may only hide its own tab row when something else is provably carrying it.
// `?engine=1` is written in exactly one place in the repo — the #tvd-eng iframe in
// tv/control_ui.html — and it arms `body.app-ctx.engine-driven .tabs { display:none !important }`
// on the stated theory that inside the console shell the console header IS the rail. Top-level
// there is no rail, and he was left with 0 of 19 tabs and an empty header band.
//
// ⚠⚠ WHY THIS EXISTS ALONGSIDE tv/test_app_ctx_nav.py, WHICH ALREADY "COVERS" THIS.
// The v2471 review-after-ship pass reproduced two ways to defeat that source guard while leaving
// the bug live and the whole gate green:
//
//   1. Its detector matches ONE call shape — the literal `classList.add('engine-driven')`.
//      Rewriting a site to `classList.toggle('engine-driven', <test>)`, or `className += ' …'`,
//      or even `classList.add('engine-driven','x')` (two args defeat its `\s*\)` tail), makes the
//      site invisible to it. Measured on copies: the module went GREEN with the bug restored.
//   2. Its assertion checks the framing string is PRESENT in the enclosing scope, never that it
//      GATES the add. Leaving `var _framed = window.top !== window.self` in place as a dead
//      variable while dropping `&& _framed` from the condition also passed.
//
// Both are the same class of failure: a guard that reads for a WORD cannot see a wrong BRANCH.
// This spec reads neither. It opens the page in the two contexts that matter and counts the tabs
// a person could actually click, so no refactor of the source can make it lie.
//
// It must FAIL in both directions to be worth anything — a spec that only asserts "tabs visible"
// would also pass if the rule were deleted outright, which would break the console pane the rule
// exists for. So the framed case is asserted too.
import { test, expect } from './_net_stub';

import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/** Tabs a person could actually click: laid out, not display:none. */
async function clickableTabs(scope: any): Promise<number> {
  return await scope.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.tab')) as HTMLElement[];
    return all.filter((t) => {
      const r = t.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(t).display !== 'none';
    }).length;
  });
}

test.describe('REG-443 — the page may not hide its nav for a rail that is not there', () => {
  test('TOP-LEVEL with ?app=1&engine=1: the tab row is reachable', async ({ page }) => {
    await page.goto(BIBLE + '?app=1&engine=1');
    await page.waitForTimeout(1200);

    const cls = await page.evaluate(() => document.body.className);
    expect(
      cls,
      'a top-level document must NOT carry engine-driven: that class hides the whole tab row on ' +
        'the theory that the console shell rail replaces it, and top-level there is no shell.',
    ).not.toMatch(/\bengine-driven\b/);

    const tabs = await clickableTabs(page);
    expect(
      tabs,
      'no tab is clickable on a top-level board. This is REG-443 verbatim: he opened the shell ' +
        'URL in a window of its own and had 0 of 19 tabs with an empty header band.',
    ).toBeGreaterThan(0);

    const rowHidden = await page.evaluate(() => {
      const t = document.querySelector('.tabs') as HTMLElement | null;
      return !t || getComputedStyle(t).display === 'none';
    });
    expect(rowHidden, 'the .tabs row itself computed display:none top-level').toBe(false);
  });

  test('FRAMED with ?app=1&engine=1: the duplicate rail is still hidden', async ({ page }) => {
    // The other direction, and the reason the fix is a frame check rather than a deletion of the
    // rule. Inside the shell the console header owns the rail; two rails is the defect that rule
    // was written for. A spec that only checked the case above would pass on a deleted rule.
    /* ⚠⚠ v2689 — THE PARENT MUST BE file:// TOO, OR THE FRAME NEVER LOADS. This used
       page.setContent(), which leaves the page's own URL at about:blank, and Chromium does not let
       a non-file document frame a file:// URL. The child silently never loaded, page.frames() never
       contained bible.html, and the test failed with 'the board never loaded inside the iframe' —
       an assertion that never RAN, wearing a failure's clothes. The evidence was inside this same
       file: the sibling test above does page.goto(BIBLE + ...) and passes.
       So navigate to the board first (same scheme, same directory), then replace the document with
       the iframe host in-page. The rule under test — a FRAMED board carries `engine-driven` so the
       shell does not show two nav rails — is unchanged; only the venue is made able to host it. */
    await page.goto(BIBLE);
    await page.evaluate(() => {
      document.body.style.margin = '0';
      document.body.innerHTML =
        '<iframe id="f" style="width:1200px;height:900px;border:0"></iframe>';
    });
    await page.evaluate((src) => {
      (document.getElementById('f') as HTMLIFrameElement).src = src;
    }, BIBLE + '?app=1&engine=1');
    const frame = page.frameLocator('#f');
    await frame.locator('body').waitFor({ state: 'attached', timeout: 30000 });

    const inner = page.frames().find((f) => f.url().includes('bible.html'));
    expect(inner, 'the board never loaded inside the iframe').toBeTruthy();

    /* ⚠⚠ v2692 — WAIT FOR THE CONDITION, NOT FOR A GUESSED DURATION. This used a flat 2500ms, and
       that timing had NEVER been exercised: until the parent was given a file:// origin the frame
       did not load at all, so the test failed earlier and this line was never reached. The first
       run that got this far reported body.className === "" — not even `app-ctx` — which is not a
       missing rule but an init that had not run yet, against a 6MB page on a shared CI runner.
       bible.html:48885-48886 add `app-ctx` then `engine-driven` (engineDriven() = engine=1 AND
       framed(), per v2471's ruling that "engine=1 IS A CLAIM ABOUT CONTEXT"). So poll for the class
       the assertion is about.
       ⚠ Raising the sleep to some larger number would only move the flake: a fixed wait encodes a
       guess about a machine, and the next slower runner reopens it. A poll fails ONLY if the class
       genuinely never arrives, which is the thing this spec exists to catch.
       ⚠ AND IT MUST NOT SWALLOW THE FAILURE. On timeout it falls through with whatever className
       is actually there, so the expect below reports the real value rather than a timeout message
       that hides it. */
    const cls = await inner!.evaluate(async () => {
      const deadline = Date.now() + 20000;
      while (Date.now() < deadline) {
        const c = document.body.className || '';
        if (/\bengine-driven\b/.test(c) || /\bapp-ctx\b/.test(c)) return c;
        await new Promise((r) => setTimeout(r, 200));
      }
      return document.body.className || '';
    });
    expect(
      cls,
      'a framed board must carry engine-driven — inside the shell its own tab row is a duplicate ' +
        'of the console header rail, which is what that rule is for.',
    ).toMatch(/\bengine-driven\b/);

    const tabs = await clickableTabs(inner!);
    expect(
      tabs,
      'the framed board is showing its own tab row again, so the console pane now has two rails.',
    ).toBe(0);
  });

  test('top-level app context still reaches every workshop tab by name', async ({ page }) => {
    // Restoring the row exposed that .tabs-data is always empty in app context (its tabs are
    // hidden by name), so it painted two empty captioned frames. Hiding that container is only
    // correct while every re-shown tab lives in .tabs-workshop — asserted here on the rendered
    // page rather than on the stylesheet.
    await page.goto(BIBLE + '?app=1&engine=1');
    await page.waitForTimeout(1200);
    const shown = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.tab'))
        .filter((t) => {
          const r = (t as HTMLElement).getBoundingClientRect();
          return r.width > 0 && r.height > 0;
        })
        .map((t) => ({
          tab: t.getAttribute('data-tab'),
          inWorkshop: !!t.closest('.tabs-workshop'),
        })),
    );
    expect(shown.length, 'no tabs rendered in app context').toBeGreaterThan(0);
    const stray = shown.filter((s) => !s.inWorkshop).map((s) => s.tab);
    expect(
      stray,
      'these tabs render in app context but sit outside .tabs-workshop, whose sibling ' +
        '.tabs-data is hidden wholesale. A tab that lands there is built, styled and invisible.',
    ).toEqual([]);
  });
});
