import { test, expect } from './_net_stub';
import * as path from 'path';

// v1812 — THE FADE SAID "MORE TO THE RIGHT" AND NEVER "MORE TO THE LEFT".
//
// The ≤700px rule masks the scroll row with one constant one-way gradient: opaque to 93%,
// transparent at the right edge. That was harmless for as long as the row always sat at
// scrollLeft 0, because there was never anything to the left of it.
//
// v1811 is what made it matter. Aligning the active tab to the strip's left edge means every tab
// BEFORE it is off-screen — on a fresh 375px load that is MAIN through REFERENCE, ten of them —
// with nothing on the page saying they exist. The row simply looks like it begins at SESSIONS.
// A fix that removes one confusion and quietly installs another is not finished.
//
// So the mask follows scroll position: fade right at the start, both when mid-row, left at the
// end, and none at all when the row is not scrollable. The state is an attribute so the
// gradients live in the stylesheet beside the rule they override, and the original one-way
// gradient stays as the fallback for the case where the JS never runs.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function edge(page: any) {
  return page.evaluate(() => {
    const s = document.querySelector('.tabs') as HTMLElement | null;
    if (!s) return { edge: 'missing', mask: '', left: 0, max: 0 };
    return {
      edge: s.getAttribute('data-edge') || '(unset)',
      mask: getComputedStyle(s).maskImage || 'none',
      left: Math.round(s.scrollLeft),
      max: Math.round(s.scrollWidth - s.clientWidth),
    };
  });
}

// a gradient "fades" on a side if it carries a transparent stop there
const fadesLeft  = (m: string) => /^linear-gradient\(90deg,\s*rgba\(0, 0, 0, 0\)/.test(m);
const fadesRight = (m: string) => /rgba\(0, 0, 0, 0\)(\s*(100%|0px))?\)\s*$/.test(m);

test('v1812 — a scrollable strip fades the side that has more tabs', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 700 });
  await page.goto(FILE);
  await page.waitForSelector('.tabs .tab', { state: 'attached' });
  await page.waitForFunction(() => {
    const s = document.querySelector('.tabs') as HTMLElement | null;
    return !!s && !!s.getAttribute('data-edge');
  }, null, { timeout: 15000 });

  // scrolled to the very start: tabs exist to the RIGHT only
  await page.evaluate(() => { (document.querySelector('.tabs') as HTMLElement).scrollLeft = 0; });
  await page.waitForTimeout(300);
  let e = await edge(page);
  expect(e.max, 'the 375px row must actually be scrollable, or this test proves nothing').toBeGreaterThan(1);
  expect(e.edge).toBe('start');
  expect(fadesRight(e.mask), `start state fades right — ${e.mask}`).toBe(true);
  expect(fadesLeft(e.mask), `start state must NOT fade left — ${e.mask}`).toBe(false);

  // scrolled to the very end: tabs exist to the LEFT only
  await page.evaluate(() => { const s = document.querySelector('.tabs') as HTMLElement; s.scrollLeft = s.scrollWidth; });
  await page.waitForTimeout(300);
  e = await edge(page);
  expect(e.edge).toBe('end');
  expect(fadesLeft(e.mask), `end state fades left — ${e.mask}`).toBe(true);
  expect(fadesRight(e.mask), `end state must NOT fade right — ${e.mask}`).toBe(false);

  // mid-row: tabs exist BOTH ways
  await page.evaluate(() => { const s = document.querySelector('.tabs') as HTMLElement; s.scrollLeft = Math.round((s.scrollWidth - s.clientWidth) / 2); });
  await page.waitForTimeout(300);
  e = await edge(page);
  expect(e.edge).toBe('both');
  expect(fadesLeft(e.mask), `both state fades left — ${e.mask}`).toBe(true);
  expect(fadesRight(e.mask), `both state fades right — ${e.mask}`).toBe(true);
});

test('v1812 — a row that fits is not faded at all', async ({ page }) => {
  // A mask on a row with nothing hidden is a lie about the content: it dims real tabs to hint at
  // tabs that are not there.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(FILE);
  await page.waitForSelector('.tabs .tab', { state: 'attached' });
  await page.waitForFunction(() => {
    const s = document.querySelector('.tabs') as HTMLElement | null;
    return !!s && !!s.getAttribute('data-edge');
  }, null, { timeout: 15000 });

  const e = await edge(page);
  expect(e.max, 'at 1440 the row wraps and does not scroll').toBeLessThanOrEqual(1);
  expect(e.edge).toBe('none');
  expect(e.mask, 'no fade on a row that fits').toBe('none');
});
