import { test, expect } from '@playwright/test';

// REG-2221 — the console STATE panel's "change →" on an ANSWERED question (the SHADOW GATE: "Keep it
// as it is") did nothing. _hubGoAsk(askId) → d2rOpenAsk(askId) un-collapsed the inbox card but queried
// #ibx-needsyou WITHOUT rendering it first — a collapsed / not-yet-drawn inbox had no .ibx-ny-done[data-ask]
// row, d2rOpenAsk returned {landed:null}, and the button read as dead. The fix (bible.html:67233) calls
// window.renderInbox() before the query, so the answered section is drawn before we look.
//
// ⚠ THIS TESTS C's WIRING, not renderInbox's internal _eagleNY rendering. d2rOpenAsk calls
// `window.renderInbox` DYNAMICALLY (67233), so a stub that populates #ibx-needsyou fires iff d2rOpenAsk
// re-renders before querying — RED without the fix (the stub never runs, the row stays absent), GREEN with
// it. Earlier cuts tried to seed the real _eagleNY path (direct window._eagleNY, then _eagleNYAdopt) and both
// shipped RED on CI (#132): on a bare file:// with no console the render state could not be driven from the
// spec reliably. The answered-section render itself is pre-existing, separately-working behaviour (the console
// already showed the answered shadow-gate — that is why a "change" button existed to be clicked); C only added
// the render CALL, which is exactly what this guard pins.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).d2rOpenAsk === 'function');
});

test('d2rOpenAsk re-renders the inbox before looking, so an ANSWERED question is reachable (REG-2221)', async ({ page }) => {
  const r = await page.evaluate(() => {
    // renderInbox (whatever it draws from) WILL show this answered row — stub it so the test controls the
    // render and does not depend on a console the CI file:// page cannot reach.
    (window as any).renderInbox = function () {
      var ny = document.getElementById('ibx-needsyou');
      if (ny) ny.innerHTML = '<div class="ibx-ny-done" data-ask="shadowgate">Keep it as it is '
        + '<button type="button" class="ibx-ny-b" data-ask="shadowgate">change</button></div>';
    };
    // the dead-button condition: the inbox is collapsed AND empty (nothing for d2rOpenAsk to find yet)
    const card = document.getElementById('inbox-card'); if (card) card.classList.add('collapsed');
    const ny = document.getElementById('ibx-needsyou'); if (ny) ny.innerHTML = '';
    const before = !!document.querySelector('#ibx-needsyou [data-ask="shadowgate"]');
    const got: any = (window as any).d2rOpenAsk('shadowgate');
    const after = !!document.querySelector('#ibx-needsyou [data-ask="shadowgate"]');
    const hasChange = !!document.querySelector('#ibx-needsyou .ibx-ny-done[data-ask="shadowgate"] button');
    return { before, after, hasChange, why: got && got.why };
  });
  // the answered question is NOT in the un-rendered inbox (the dead-button state)...
  expect(r.before).toBe(false);
  // ...and d2rOpenAsk RE-RENDERED first (the fix), so the row — with its own "change" button — is now found
  expect(r.after).toBe(true);
  expect(r.hasChange).toBe(true);
  // a found row never returns the "inbox does not show this question" refusal
  expect(String(r.why || '')).not.toContain('does not show');
});
