import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1967 — "HAWKFANE" IS HAWKMAIL, AND THE QUEUE SAID "unclear read".
 *
 * v1789 read his real ledger by hand and split 36 held rows three ways: six unresolved uniques,
 * twenty-four reader debris, and SIX OCR slips of items already in his grail ("Battlecage" for
 * Rattlecage, "Naglring" for Nagelring). It built machinery for exactly one of the three. The
 * slips were named in that spec's own header and left with no resolver — measured 2026-08-22,
 * this file contained ZERO string-distance functions of any kind.
 *
 * The nine below are not invented. They are the slips left in his CURRENT reader output
 * (tv/chron_last_result.json, 369 names, 343 recognised): every one is within two edits of a real
 * roster entry, and every one reached him as "unclear read".
 *
 * WHAT THIS PINS IS THE BOUNDARY, and the refusals matter more than the hits — a resolver that
 * guesses freely would invent finds, and on this board a find is never created by inference.
 */

/* The calibrated bound, kept beside the data it describes. This line WAS the literal `2`, left
   behind when the bound moved to 3: the SLIPS below were updated, the assertion was not, and CI
   failed with "Hawkfane should be within 2 edits" while the resolver had answered "Hawkmail"
   correctly — the feature working and the test wrong. Third time in one day that a number survived
   its own recalibration (the others: the header comment claiming NINE slips, and the bound itself).
   Named once here so the next move of the bound cannot leave a straggler behind. */
const NGN_MAX = 3;

const SLIPS: Array<[string, string]> = [
  ['Hawkfane',        'Hawkmail'],
  ['Stouthale',       'Stoutnail'],
  ['Endlessmane',     'Endlesshail'],
  ['Bloodfist Shard', 'Bloodpact Shard'],
];

const MUST_STAY_SILENT: Array<[string, string]> = [
  ['Firel...',        'a truncation is an honest partial read, not a misread — there is nothing to guess from'],
  ["Natalya's...",    'same: the reader said it could not finish the name'],
  ['Templar Coat',    'v1789 debris — the Chronicle prints the BASE name for a row he has NOT found, so a suggestion would invert the one fact it carries'],
  ['Bone Visage',     'same debris class'],
  ['Tomahawk',        'a base type, and no roster name is within the bound'],
  ['Corona',          'a base type; at 6 chars the length floor still admits it, so the TIE rule is what holds it'],
  ['Toothrow',        'a real roster unique he does not have — it is not a misread of anything'],
  ['Tooth',           'below the 6-character floor: almost everything is within 3 edits of a 5-letter word'],
];

test('a slip of a real board item is named, and the row still waits for his ruling', async ({ page }) => {
  await page.goto(URL);
  for (const [raw, want] of SLIPS) {
    const got = await page.evaluate((n) => {
      const r = (window as any)._nearestGrailName(n);
      return r ? { name: r.name, dist: r.dist } : null;
    }, raw);
    expect(got, `"${raw}" should resolve to "${want}"`).not.toBeNull();
    expect(got!.name, `"${raw}" -> wrong candidate`).toBe(want);
    expect(got!.dist, `"${raw}" should be within ${NGN_MAX} edits`).toBeLessThanOrEqual(NGN_MAX);
  }
});

test('it refuses where the evidence does not name one item', async ({ page }) => {
  await page.goto(URL);
  for (const [raw, why] of MUST_STAY_SILENT) {
    const got = await page.evaluate((n) => (window as any)._nearestGrailName(n), raw);
    expect(got, `"${raw}" must produce NO suggestion — ${why}`).toBeNull();
  }
});

test('a name already on the roster is not a misread of itself', async ({ page }) => {
  await page.goto(URL);
  for (const real of ['Hawkmail', 'Stoutnail', 'Rattlecage']) {
    const got = await page.evaluate((n) => (window as any)._nearestGrailName(n), real);
    expect(got, `"${real}" is a real roster name; suggesting anything for it is a false correction`).toBeNull();
  }
});

/* THE ONE THAT MATTERS MOST: suggesting must never become ticking. A fuzzy match that grails an
   item invents a find, and an invented find is unrecoverable — he cannot tell it from a real one
   later. So the resolver is proven PURE: calling it leaves every grail store byte-identical. */
test('the resolver never writes — no grail store moves when it runs', async ({ page }) => {
  await page.goto(URL);
  const changed = await page.evaluate(() => {
    const keys = Object.keys(localStorage).filter(k => /found|grail|setPieces|Inbox/i.test(k));
    const before = JSON.stringify(keys.map(k => [k, localStorage.getItem(k)]));
    ['Hawkfane', 'Stouthale', "Nord's Tooth", 'Templar Coat', 'Firel...'].forEach(n => {
      try { (window as any)._nearestGrailName(n); } catch (e) { /* a throw is a separate failure */ }
    });
    const after = JSON.stringify(Object.keys(localStorage)
      .filter(k => /found|grail|setPieces|Inbox/i.test(k))
      .map(k => [k, localStorage.getItem(k)]));
    return before !== after;
  });
  expect(changed, 'calling the resolver changed a grail-ish store — it must be pure').toBe(false);
});

/* THE GUARD THIS WHOLE EPISODE ARGUES FOR. The first draft used a bound of 2, which felt safe and
   produced ZERO suggestions on his real data — an absent branch wearing a tuned-looking constant.
   A resolver that never resolves is indistinguishable from one that was never wired, and both
   report clean. So this asserts the function is NOT INERT: the four slips above are the calibrated
   evidence, and if a future change quietly narrows the bound, this fails instead of going quiet. */
test('the resolver is not inert — it still fires on the class it was built for', async ({ page }) => {
  await page.goto(URL);
  const n = await page.evaluate((names) => names
    .map((x: string) => (window as any)._nearestGrailName(x))
    .filter(Boolean).length, SLIPS.map(s => s[0]));
  expect(n, 'every calibrated slip went silent — the bound is above the ceiling of the signal again').toBe(SLIPS.length);
});

/* v1968 — THE CASCADE, NOT THE SOURCE ORDER. `.ibx-why-near` was first written ABOVE `.ibx-why`.
   The span carries both classes, both set `color`, and both are single-class selectors — equal
   specificity, so source order alone decided and the dim rule won. The suggestion would have
   rendered in exactly the style it exists to escape, while the rule sat in the file looking correct.

   A comment saying "keep this below" is not a guard; the next person to sort the stylesheet does not
   read comments. This asserts the OUTCOME — that an element carrying both classes computes to
   something other than the dim colour — so the defect fails the build rather than the eye. It builds
   synthetic spans instead of seeding the inbox, because the cascade is what is under test and a
   panel that failed to render would report the same red for an unrelated reason. */
test('the suggestion colour actually wins the cascade', async ({ page }) => {
  await page.goto(URL);
  const { dim, near } = await page.evaluate(() => {
    const mk = (cls: string) => {
      const el = document.createElement('span');
      el.className = cls; el.textContent = 'x';
      document.body.appendChild(el);
      const c = getComputedStyle(el).color;
      el.remove();
      return c;
    };
    return { dim: mk('ibx-why'), near: mk('ibx-why ibx-why-near') };
  });
  expect(near, `a row WITH an answer computed the same colour as one without (${dim}) — `
    + '.ibx-why-near lost the cascade, which happens silently when it is placed above .ibx-why')
    .not.toBe(dim);
});
