// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v181 — internal-contradiction fix. The Breakpoints section's "For Konyo (Warlock)"
// box previously told Konyo to aim for 63% FCR (8-frame) "assuming the Warlock casts
// on the Sorceress table". But v178's Warlock skill kit cites the VERIFIED maxroll
// Echoing Strike guide target of 125% FCR as the build's priority breakpoint — and the
// Sorc FCR table jumps 105 -> 200 with no 125 row, so it can't capture the Warlock's
// actual breakpoint. This fix corrects the recommendation to the verified 125% FCR
// (no fabricated frame count), PRESERVES the Sorc table as a labeled reference, and
// keeps the whole site internally consistent (125% in both the skill kit + breakpoints).

function breakpointsBodyText() {
  const heads = Array.from(document.querySelectorAll('#tab-ref .sec-h'));
  const head = heads.find((h) => (h.querySelector('.sec-h-t')?.textContent || '').trim() === 'Breakpoints');
  const body = head ? (head.nextElementSibling as HTMLElement) : null;
  return (body?.textContent || '').replace(/\s+/g, ' ');
}

test.describe('v181 Warlock FCR breakpoint correction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(600);
  });

  test('the "For Konyo (Warlock)" box now targets the verified 125% FCR breakpoint', async ({ page }) => {
    const txt = await page.evaluate(breakpointsBodyText);
    expect(txt).toContain('For Konyo (Warlock)');
    expect(txt).toMatch(/125% FCR/);
    expect(txt).toMatch(/priority breakpoint/i);
  });

  test('the stale 63%/37% Sorceress-table recommendation is gone', async ({ page }) => {
    const txt = await page.evaluate(breakpointsBodyText);
    // the contradictory recommendation text must no longer be present
    expect(txt).not.toMatch(/aim for 63% FCR \(8-frame\)/);
    expect(txt).not.toMatch(/assuming the Warlock casts on the Sorceress table/);
  });

  test('the Sorceress FCR table is PRESERVED as a labeled reference (additive, nothing cut)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const heads = Array.from(document.querySelectorAll('#tab-ref .sec-h'));
      const head = heads.find((h) => (h.querySelector('.sec-h-t')?.textContent || '').trim() === 'Breakpoints');
      const body = head ? (head.nextElementSibling as HTMLElement) : null;
      const rows = body ? Array.from(body.querySelectorAll('table.ref-tbl tbody tr')) : [];
      const firstCells = rows.map((tr) => (tr.querySelector('td')?.textContent || '').trim());
      return { firstCells };
    });
    // the canonical Sorc FCR breakpoints (incl. the 105 -> 200 jump with no 125 row) remain
    for (const v of ['0', '9', '15', '20', '37', '63', '105', '200']) {
      expect(r.firstCells, `FCR ${v} row present`).toContain(v);
    }
    expect(r.firstCells).not.toContain('125'); // Sorc table genuinely has no 125 row
  });

  test('the source cite credits the Echoing Strike Warlock guide for 125%', async ({ page }) => {
    const txt = await page.evaluate(breakpointsBodyText);
    expect(txt).toMatch(/Echoing Strike Warlock guide/i);
    expect(txt).toMatch(/125% FCR priority breakpoint/i);
    expect(txt).toMatch(/RotW Warlock frame counts to be confirmed in-game/i);
  });

  test('no console errors opening the Breakpoints section', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => {
      const heads = Array.from(document.querySelectorAll('#tab-ref .sec-h'));
      const head = heads.find((h) => (h.querySelector('.sec-h-t')?.textContent || '').trim() === 'Breakpoints') as HTMLElement;
      head && head.click();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
