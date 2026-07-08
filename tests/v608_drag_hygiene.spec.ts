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

// v611 — ✦ grab magic: closing the hand on a grabbable bursts glints at the fingertip; they self-
// remove; a blank press spawns nothing; reduced motion spawns nothing.
test('grab burst sparkles appear, self-remove, and respect blank-space + reduced motion', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => new Promise<any>((res) => {
    const tab = document.querySelector('.tab')!;
    const bb = tab.getBoundingClientRect();
    tab.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, buttons: 1, clientX: bb.x + 5, clientY: bb.y + 5 }));
    const burst = document.querySelectorAll('.kspark').length;
    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
    setTimeout(() => res({ burst, after: document.querySelectorAll('.kspark').length }), 1100);
  }));
  expect(r.burst).toBeGreaterThanOrEqual(4);   // the close bursts glints at the fingertip
  expect(r.after).toBe(0);                     // all self-removed — no DOM litter
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const r2 = await page.evaluate(() => {
    const tab = document.querySelector('.tab')!;
    tab.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, buttons: 1, clientX: 60, clientY: 60 }));
    const n = document.querySelectorAll('.kspark').length;
    window.dispatchEvent(new PointerEvent('pointerup', { bubbles: true }));
    return n;
  });
  expect(r2).toBe(0);                          // silent under reduced motion
});
