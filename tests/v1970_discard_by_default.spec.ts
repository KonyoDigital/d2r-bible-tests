import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1970 — A DISCARD HE CHOSE AND A DISCARD NOBODY CHOSE MUST NOT READ THE SAME.
 *
 * The vault keeps eight sets (_KEEP_SET) and discards everything else, so the DEFAULT is discard.
 * The v394 comment names EIGHTEEN sets he actually ruled junk; the board knows thirty-four. The
 * remaining eight — The Disciple, Sazabi's Grand Tribute, Naj's Ancient Vestige, Hwanin's Majesty,
 * Arcanna's Tricks, Bane's Garments, Heaven's Brethren, Orphan's Call — are discarded by SILENCE,
 * and every one of them read "low set piece", the same sentence as a set he had judged.
 *
 * The Disciple holds LAYING OF HANDS. Horazon's Splendor sat in exactly this position until v440,
 * and the code comment records the cost in his own words: "Konyo's 4 Horazon's pieces wrongly
 * discarded". The failure is not the routing — it is that the row gave him no way to tell a verdict
 * from a default, so the one case worth a second look looked identical to eighteen settled ones.
 *
 * ⚠ THE ROUTING ASSERTIONS BELOW ARE THE POINT, not the wording ones. Which sets are worth muling
 * is HIS call. This change must move nothing: if a future edit turns the honest label into a
 * behaviour change, these fail.
 */

const RULED_JUNK = ["Sigon's Guard", "Cleglaw's Tooth", "Vidala's Barb"];
const NEVER_RULED = ['Laying of Hands', "Sazabi's Cobalt Redeemer", "Naj's Puzzler", "Hwanin's Justice"];

test('routing is UNCHANGED — every one of these still goes to the throw-out pile', async ({ page }) => {
  await page.goto(URL);
  for (const n of [...RULED_JUNK, ...NEVER_RULED]) {
    const r = await page.evaluate((x) => (window as any).suggestMule(x), n);
    expect(r?.id, `"${n}" must still route to __throwout — this version changes wording, not routing`)
      .toBe('__throwout');
  }
});

test('a set he ruled junk still reads as a judgement', async ({ page }) => {
  await page.goto(URL);
  for (const n of RULED_JUNK) {
    const r = await page.evaluate((x) => (window as any).suggestMule(x), n);
    expect(r.why, `"${n}" is in his named junk list; it must not be labelled a default`)
      .toContain('low set piece');
    expect(r.why).not.toContain('DEFAULT');
  }
});

test('a set he never ruled says so, by name', async ({ page }) => {
  await page.goto(URL);
  for (const n of NEVER_RULED) {
    const r = await page.evaluate((x) => (window as any).suggestMule(x), n);
    expect(r.why, `"${n}" belongs to a set he has never ruled on — the row must say so, not imply he judged it`)
      .toContain('never ruled');
  }
});

/* The calibration. A test that only ever sees one branch cannot tell the branches apart, and this
   whole change IS the distinction between two branches — so assert they actually differ on real
   input rather than that each matches its own string. */
test('the two labels are genuinely different on real items', async ({ page }) => {
  await page.goto(URL);
  const ruled = await page.evaluate(() => (window as any).suggestMule("Sigon's Guard").why);
  const unruled = await page.evaluate(() => (window as any).suggestMule('Laying of Hands').why);
  expect(ruled).not.toBe(unruled);
  expect(unruled, 'the unruled label must name the set, so he knows WHICH set to rule on')
    .toContain('Disciple');
});
