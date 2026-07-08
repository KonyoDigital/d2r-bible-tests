import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v608 — DRAG HYGIENE (Konyo dragged a vault chip): a native HTML5 drag swallows mouseout AND
// pointerup, so (1) the #arttip hover card froze on screen mid-drag, and (2) the v605 gauntlet
// stayed CLOSED after the drag. Locks: dragstart force-hides the arttip; dragend/drop (and a
// buttons===0 pointermove safety) reopen the hand.

test('dragstart hides the arttip; dragend reopens the gauntlet', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const tip = document.getElementById('arttip')!;
    tip.classList.add('on');                       // simulate a live hover card
    document.body.dispatchEvent(new DragEvent('dragstart', { bubbles: true }));
    const tipHidden = !tip.classList.contains('on');
    // simulate the stuck-grab: press an interactive element, then complete a DRAG (no pointerup)
    const rt = document.documentElement;
    const tab = document.querySelector('.tab')!;
    tab.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, buttons: 1 }));
    return new Promise<any>((res) => setTimeout(() => {
      const held = rt.style.getPropertyValue('--kcur');
      window.dispatchEvent(new DragEvent('dragend', { bubbles: true }));
      setTimeout(() => res({ tipHidden, held, after: rt.style.getPropertyValue('--kcur') }), 220);
    }, 220));
  });
  expect(r.tipHidden).toBe(true);                  // the hover card can never freeze mid-drag
  expect(r.held.length).toBeGreaterThan(0);        // the press DID close the hand…
  expect(r.after).not.toBe(r.held);                // …and dragend reopened it (no stuck grab)
});

test('safety net: pointermove with no buttons releases a lost grab', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const rt = document.documentElement;
    const tab = document.querySelector('.tab')!;
    tab.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, buttons: 1 }));
    return new Promise<any>((res) => setTimeout(() => {
      const held = rt.style.getPropertyValue('--kcur');
      // pointerup was lost (released outside/over native UI) — a buttons-free move must recover
      window.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, buttons: 0 }));
      setTimeout(() => res({ held, after: rt.style.getPropertyValue('--kcur') }), 220);
    }, 220));
  });
  expect(r.held.length).toBeGreaterThan(0);
  expect(r.after).not.toBe(r.held);
});
