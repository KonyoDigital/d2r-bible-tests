import { test, expect } from '@playwright/test';

// REG-2221 — the console STATE panel's "change →" on an ANSWERED question (the SHADOW GATE: "Keep it
// as it is") did nothing. It calls _hubGoAsk(askId) → d2rOpenAsk(askId), which un-collapses the inbox
// card but queried #ibx-needsyou WITHOUT rendering it first — so a collapsed / not-yet-drawn inbox had
// no .ibx-ny-done[data-ask] row to find, d2rOpenAsk returned {landed:null}, and the button read as dead.
// The fix renders the inbox (synchronous, from _eagleNY) before the query (bible.html:67233).
//
// ⚠ THE SEED GOES THROUGH THE REAL TRANSFORM — window._eagleNYAdopt(eagle) → _eagleNYFromEagle builds
// {st:'clear', answered:[the row]} and sets the actual _eagleNY that renderInbox reads. The first cut of
// this spec set window._eagleNY = {needsYou, answered} DIRECTLY, with no 'st' field — so renderInbox fell
// through every st-branch to the dim-UNKNOWN default (bible.html:67079) and never called _answeredHtml,
// and _eagleNY is never a window property anyway (it may be an IIFE local the assignment can't reach).
// That shipped RED on CI for two versions and was caught by review-after-ship (#132). Adopting through the
// exposed mutator is both faithful (the server's own builder) and immune to the identifier's scope.
//
// RED without the fix: after clearing #ibx-needsyou, d2rOpenAsk does NOT re-render it, so the answered row
// is absent. GREEN with the fix: d2rOpenAsk renders the inbox first, so the row (with its own "change"
// button → _askWithdraw) is found.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).d2rOpenAsk === 'function'
    && typeof (window as any).renderInbox === 'function'
    && typeof (window as any)._eagleNYAdopt === 'function');
});

test('d2rOpenAsk renders the inbox so an ANSWERED question is reachable (REG-2221)', async ({ page }) => {
  const r = await page.evaluate(() => {
    // an answered-but-held question, exactly the shadow-gate shape — a non-missing row whose `check` is in
    // answeredWhat becomes _eagleNY.answered with st:'clear' (bible.html:67318/67333/67338).
    (window as any)._eagleNYAdopt({
      needsYou: [],
      answeredWhat: ['shadow gate'],
      rows: [{
        check: 'shadow gate', state: 'answered',
        answered: [{ askId: 'shadowgate', key: 'keep', label: 'Keep it as it is',
                     at: Date.now(), until: Date.now() + 1e9, effect: 'hold',
                     q: 'Should the console ask you before it ticks a grail item by itself?' }],
      }],
      say: 'all clear',
    });
    // reproduce the dead-button condition: the inbox is collapsed AND not rendered
    const card = document.getElementById('inbox-card'); if (card) card.classList.add('collapsed');
    const ny = document.getElementById('ibx-needsyou'); if (ny) ny.innerHTML = '';
    const before = !!document.querySelector('#ibx-needsyou [data-ask="shadowgate"]');
    const got: any = (window as any).d2rOpenAsk('shadowgate');
    const after = !!document.querySelector('#ibx-needsyou [data-ask="shadowgate"]');
    const hasChange = !!document.querySelector('#ibx-needsyou .ibx-ny-done[data-ask="shadowgate"] button');
    return { before, after, hasChange, why: got && got.why };
  });
  // the answered question is NOT in the unrendered inbox (the dead-button state)...
  expect(r.before).toBe(false);
  // ...and after d2rOpenAsk the fix rendered it, so it is found with its own "change" button
  expect(r.after).toBe(true);
  expect(r.hasChange).toBe(true);
  expect(String(r.why || '')).not.toContain('does not show');
});
