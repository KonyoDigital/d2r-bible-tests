import { test, expect, seedOwnerRoute } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v3744 — THE CONSOLE ITEM CARD, HOVERED FOR REAL, SUPPRESSES THE NATIVE TITLE (REG-2244, ↩#220/#42).
//
// The double-tooltip defect: ~672 elements carry BOTH a `data-itip` (the console's rich item card)
// and a native `title` — on themselves or on the card/row around them — so a hover painted the
// styled card WITH the grey OS box on top of it. GrokBot photographed it three times (ticks
// 392 / 407 / 422: the eyes card, a stray "default OFF" line, the Accumulator's LOCKED box).
// Konyo's words on the same class, board-side: "i want hdart only not double one is rendering a
// regular OS message box."
//
// REG-2116 (v3631, 2026-10-09) FIXED it: `_itemTip.show()` now calls `_holdItem()`, which borrows
// the hovered node's own `title` AND every title above it into `data-tip-held` for the length of
// the hover and gives them back on release — the same borrow `say()` has shipped since v2105 /
// REG-1871. So the native box has no attribute to open while the card is up.
//
// WHY THIS SPEC EXISTS ON TOP OF THAT FIX. REG-2116's only guard is TestReg2116TheItemCardBorrows-
// LikeTheProseLane in tv/test_control.py, which drives `show()` DIRECTLY over REG-1871's fake DOM.
// That proves the function's shape; it cannot prove the WIRING — that a real pointer move over a
// `[data-itip]` node reaches `show()` through the document-level mousemove delegate, and that a
// real move away reaches `hide()` and gives the title back. That is the exact gap v2130 named for
// the board lane ("NOTHING EVER HOVERED"): a guard that calls the internal function can never go
// red for the delegate that calls it. This is the console lane's real-hover complement — no
// internal call, a dispatched event the shipped listener handles.
//
// RED-FIRST (reasoned, not run — browser specs run on GitHub CI, never on his Mac; see test-venue):
// revert `_holdItem(node)` to the pre-REG-2116 body (`show()` only calling `this.release()`) and
// the hovered node keeps its `title` — enter.hostTitle is the OS text, not null — so the first
// `toBeNull()` below fails. The spec is pinned to the LAW (no native title while the card is up),
// not to any constant.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

/** Load the console the proven way (v1617): serve control_ui.html at a real http origin so its
 *  scripts run and the mousemove delegate binds. seedOwnerRoute gives it the route a real console
 *  always has (v1736/v1749); /api and /art are stubbed so load neither hangs nor errors. */
async function openConsole(page: any) {
  await seedOwnerRoute(page);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'),
    (r: any) => r.fulfill({ status: 404, body: '' }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() =>
    !!(window as any)._itemTip && typeof (window as any)._itemTip.show === 'function');
}

test.describe('v3744 — the console item card suppresses the native title on a real hover', () => {
  test('★★★ a [data-itip] node (and its titled ancestor) has its native title neutralised while #itip is up, and restored on leave', async ({ page }) => {
    await openConsole(page);

    const r = await page.evaluate(() => {
      // Build the documented defect on a node the lane REALLY binds. The item lane is a
      // document-level mousemove delegate (closest('[data-itip]')), so an appended node with valid
      // data-itip JSON is a genuine hover target — and REG-1871's half (a title on the CARD/ROW
      // around the item) is modelled by putting a title on an ancestor too.
      const HOST_TITLE = 'OS BOX ON THE HOST';
      const ABOVE_TITLE = 'OS BOX ON THE CARD AROUND IT';

      const above = document.createElement('div');
      above.setAttribute('title', ABOVE_TITLE);
      const host = document.createElement('span');
      host.textContent = 'Frostburn';
      host.setAttribute('title', HOST_TITLE);
      host.setAttribute('data-itip', JSON.stringify({
        name: 'Frostburn', art: '', rarity: 'unique',
        tip: { t: 'Unique', b: 'Gauntlets', r: 29, q: 32, l: ['+30 Defense'] } }));
      above.appendChild(host);
      document.body.appendChild(above);

      const snap = () => {
        const tip = document.getElementById('itip');
        return {
          card: !!tip && tip.classList.contains('on'),
          hostTitle: host.getAttribute('title'),
          hostHeld: host.getAttribute('data-tip-held'),
          aboveTitle: above.getAttribute('title'),
          aboveHeld: above.getAttribute('data-tip-held'),
        };
      };
      const move = (t: EventTarget) =>
        t.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: 60, clientY: 60 }));

      const rest = snap();      // before any hover — #itip is not even built yet
      move(host);               // HOVER the item: the bound delegate runs _itemTip.show()
      const enter = snap();
      move(document.body);      // leave onto bare chrome: the delegate runs _itemTip.hide()
      const leave = snap();

      host.remove(); above.remove();
      return { rest, enter, leave, HOST_TITLE, ABOVE_TITLE };
    });

    // non-vacuity: the rich card MUST actually open on the dispatched hover, or this spec measured
    // nothing about suppression (v2130's lesson — and it would also catch a delegate that stopped
    // binding at all).
    expect(r.rest.card, 'the card was already up before any hover — the probe is dirty').toBe(false);
    expect(r.enter.card, 'the item card never opened on a real mousemove — either the lane did not '
      + 'bind or show() refused the node; nothing below proves anything if #itip is not up').toBe(true);

    // THE LAW, while the styled card is up: no native title is left to open the grey OS box.
    expect(r.enter.hostTitle, 'the hovered node kept its native title, so the OS box opens ON TOP '
      + 'of the rich card — the exact doubling GrokBot photographed (ticks 392/407/422)').toBeNull();
    expect(r.enter.hostHeld, 'the title was dropped but not parked in data-tip-held, so it can '
      + 'never be given back').toBe(r.HOST_TITLE);
    // REG-1871's half — a title on the CARD/ROW above the item opens the box too, and must be taken.
    expect(r.enter.aboveTitle, 'a titled ancestor still opens the OS box over the card').toBeNull();
    expect(r.enter.aboveHeld, 'the ancestor title was dropped but not parked').toBe(r.ABOVE_TITLE);

    // a borrow, never a theft: everything is given back when the pointer leaves the item.
    expect(r.leave.card, 'the card stayed up after the pointer genuinely left the item').toBe(false);
    expect(r.leave.hostTitle, 'the borrowed title was NOT restored — the node has permanently lost '
      + 'its tooltip text').toBe(r.HOST_TITLE);
    expect(r.leave.hostHeld, 'data-tip-held was left behind, so the next hover reads a stale steal')
      .toBeNull();
    expect(r.leave.aboveTitle, 'the ancestor title was not restored on leave').toBe(r.ABOVE_TITLE);
    expect(r.leave.aboveHeld, 'the ancestor was left parked in data-tip-held').toBeNull();
  });
});
