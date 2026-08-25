import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2130 — #59. THE TOOLS VAULT SIGNPOST HAD NO BEHAVIOUR SPEC.
//
// `grep -rn vault-moved-note tests/` was EMPTY. Its only guard was tv/console_doctor.py, a SOURCE
// grep: it faults if the id vanishes and regex-searches a fixed byte window after it for
// switchTab('<room>'). That covers deletion and a dead room name. It never opens a page, so it
// cannot see whether the card RENDERS in Tools, or whether the click LANDS in the Vault — which is
// the entire promise of a signpost.
//
// The class this belongs to is the one that keeps recurring here: a label that names an action and
// does not perform it. v1613, on the sibling chip: "a chip that SAYS 'open Forge' must open the
// Forge... A label promising an action and not performing it is worse than no label."

test('the signpost is visible in Tools and its click lands in the Vault room', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).switchTab === 'function');

  const r = await page.evaluate(() => {
    const w = window as any;
    w.switchTab('tools');
    const note = document.getElementById('vault-moved-note');
    const before = {
      present: !!note,
      // offsetParent is null for display:none AND for any hidden ancestor — v1674 hid a whole
      // column on one view and left a card that existed at 0x0, which is the failure this asks about
      visible: !!(note && (note as HTMLElement).offsetParent),
      room: (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab'),
    };
    const head = note && (note.querySelector('.boss-header') as HTMLElement | null);
    if (head) head.click();
    const after = { room: (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab') };
    return { before, after, hadHeader: !!head };
  });

  expect(r.before.present, 'the signpost is gone from the board entirely').toBe(true);
  expect(r.before.visible, 'the signpost exists but renders at 0x0 in Tools — a forwarding address '
    + 'nobody can see is not a forwarding address').toBe(true);
  expect(r.before.room, 'switchTab("tools") did not open Tools, so this spec never reached its '
    + 'subject').toBe('tools');
  expect(r.hadHeader, 'the signpost has no clickable header').toBe(true);
  expect(r.after.room, 'clicking the signpost did not land in the VAULT room — the label names a '
    + 'destination it does not reach').toBe('vault');
});

test('keyboard reaches it too — Enter does what the click does', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).switchTab === 'function');

  const room = await page.evaluate(() => {
    const w = window as any;
    w.switchTab('tools');
    const head = document.querySelector('#vault-moved-note .boss-header') as HTMLElement | null;
    if (!head) return '(no header)';
    head.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    return (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab');
  });

  expect(room, 'Enter on the signpost does not reach the Vault, so the card is mouse-only — the '
    + 'keyboard path exists on every other card of this kind').toBe('vault');
});
