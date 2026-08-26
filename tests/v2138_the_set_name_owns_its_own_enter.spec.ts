import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2138 — ONE KEYSTROKE, TWO ACTIONS. v2137 made a completed set card fold, toggled by its header.
// `.set-card-name` inside that header is ITSELF a role=button that opens the set ID card, and its
// inline onclick calls stopPropagation — so the CLICK never reached the fold listener. Its inline
// onkeydown does NOT, so pressing Enter on a finished set name opened the ID card AND folded the
// card underneath it. Measured before the fix: openDrop fired once and `sc-open` flipped
// false -> true in a single keystroke.
//
// The rule this pins is not "the name is special" — it is that a control inside the header owns
// its own activation. Assert BOTH halves, because a fix that silences the header entirely would
// pass the first check alone. [[the-unjoined-end]]

async function seed(page: any) {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).renderSetTracker === 'function'
                                && typeof (window as any).switchTab === 'function');
  await page.evaluate(() => {
    const w = window as any;
    w.switchTab('tools');
    const card = document.getElementById('set-tracker-card');
    if (card && card.classList.contains('collapsed')) w.toggleCardCollapse('set-tracker-card');
    const sets = w.__allSets();
    // `setPieces` is a top-level let/const — a global BINDING, not a property of window, so
    // w.setPieces is undefined and .add threw. Filed as #168. Use the real door instead: the same
    // toggleSetPiece the piece rows call, which is genuinely on window (bible.html:22372) and
    // also files the tick the way a real tick is filed.
    sets[0].pieces.forEach((p: string) => w.toggleSetPiece(p));
    w.renderSetTracker();
    w.__drops = 0;
    w.openDrop = () => { w.__drops++; };
  });
  const complete = await page.locator('#set-tracker .set-card.complete').count();
  expect(complete, 'the seed must produce a completed card, or this spec proves nothing').toBeGreaterThan(0);
}

// The seed produces MANY completed cards, not one — CI failed with "strict mode violation" on a
// bare locator. Both the focus targets and this reader must therefore name the SAME card, and the
// first one is the card querySelector returns below.
const read = (page: any) => page.evaluate(() => {
  const c = document.querySelector('#set-tracker .set-card.complete')!;
  return { open: c.classList.contains('sc-open'), drops: (window as any).__drops };
});

test('Enter on a finished set NAME opens its ID card and does not fold the card', async ({ page }) => {
  await seed(page);
  await page.locator('#set-tracker .set-card.complete .set-card-name').first().focus();
  const before = await read(page);
  await page.keyboard.press('Enter');
  const after = await read(page);
  expect(after.drops, 'the name must still open the set ID card').toBe(before.drops + 1);
  expect(after.open, 'and it must NOT toggle the fold underneath it').toBe(before.open);
});

test('Enter on the HEADER itself still folds, and does not open the ID card', async ({ page }) => {
  await seed(page);
  await page.locator('#set-tracker .set-card.complete .set-card-header').first().focus();
  const before = await read(page);
  await page.keyboard.press('Enter');
  const after = await read(page);
  expect(after.open, 'the header is the fold control').toBe(!before.open);
  expect(after.drops, 'and it must not open the ID card').toBe(before.drops);
});
