import { test, expect } from '@playwright/test';

// REG-2221 — the console STATE panel's "change →" on an ANSWERED question (the SHADOW GATE: "Keep it
// as it is") did nothing. It calls _hubGoAsk(askId) → d2rOpenAsk(askId), which un-collapses the inbox
// card but queried #ibx-needsyou WITHOUT rendering it first — so a collapsed / not-yet-drawn inbox had
// no .ibx-ny-done[data-ask] row to find, d2rOpenAsk returned {landed:null}, and the button read as dead.
// The fix renders the inbox (synchronous, from _eagleNY) before the query. The board inbox already
// carries each answered row's own "change" → _askWithdraw, so once found he can change the answer.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).d2rOpenAsk === 'function'
    && typeof (window as any).renderInbox === 'function');
});

test('d2rOpenAsk renders the inbox so an ANSWERED question is reachable (REG-2221)', async ({ page }) => {
  const r = await page.evaluate(() => {
    // an answered-but-held question, exactly the shadow-gate shape the state panel shows
    (window as any)._eagleNY = {
      needsYou: [],
      answered: [{
        check: 'shadow gate',
        answered: [{ askId: 'shadowgate', key: 'keep', label: 'Keep it as it is',
                     at: Date.now(), until: Date.now() + 1e9, effect: 'hold',
                     q: 'Should the console ask you before it ticks a grail item by itself?' }],
      }],
    };
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
