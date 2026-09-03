// v2474 — #135. THE DAILY PICK VANISHED WHEN THE GRAIL WALL RAN OUT, AND NEVER CAME BACK.
//
// The grail chronicle counts the game's 403 Chronicle ROWS while the wall offers 398 NAMES
// (tv/chronicle_total.py: 403 spawnable-and-in-Chronicle, 396 distinct names because Rainbow Facet
// occupies 8 rows, and a 398-entry roster whose difference from 396 is recorded there as an OPEN
// measurement). `done` counts names, so it tops out below `total` and `complete` never becomes
// true for grail.
//
// The rotation's grail arm only assigned `c.pick` inside `if (it)`. Once the wall is exhausted
// there is no runs[0] and no missing[0], so `it` was null, no pick was written, and
// dailyCreateAi fell past both of its arms:
//
//     if (_rot.target && _rot.target.pick)   -> false, no pick
//     else if (_rot.sealed)                  -> false, it is NOT sealed
//     else  removeItem('d2r_createNowAi')    -> THE DAILY PICK IS WIPED
//
// and because the same state recurs every day, it never returned.
//
// MEASURED before the fix, by driving the arm over three constructed states:
//     0   of 403  -> a pick        -> branch A
//     398 of 403  -> pick UNDEFINED -> branch C, wiped     <- the dead end
//     403 of 403  -> complete       -> branch B, unreachable for grail by the arithmetic above
//
// ⚠ WHAT THIS SPEC MUST NOT ASSERT. The copy may not explain the 403/398 gap — chronicle_total.py
// calls it unaccounted — so this checks that the pick NAMES the state and does NOT claim a
// completion, never that it gives a particular reason for the difference.
import { test, expect } from './_net_stub';

import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/** Put the grail wall in a chosen state and re-derive the rotation. */
async function rotateWith(page: any, fu: any) {
  return await page.evaluate((stub: any) => {
    (window as any).funiScan = () => stub;
    try {
      delete (window as any)._chronRotMemo;
    } catch (e) {
      (window as any)._chronRotMemo = null;
    }
    const r = (window as any)._chronRotation ? (window as any)._chronRotation() : null;
    if (!r) return null;
    const g = (r.all || []).filter((c: any) => c.key === 'grail')[0] || null;
    return {
      sealed: r.sealed,
      targetHasPick: !!(r.target && r.target.pick),
      grail: g && {
        done: g.done, total: g.total, left: g.left, complete: g.complete,
        hasPick: !!g.pick, exhausted: !!g.exhausted, pick: String(g.pick || ''),
      },
    };
  }, fu);
}

test.describe('#135 — an exhausted grail wall must still name its state', () => {
  test('every name owned, chronicle NOT complete: a pick still exists', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);

    const got = await rotateWith(page, {
      found: 398, chronTotal: 403, total: 403, runs: [], missing: [],
    });
    expect(got, 'the rotation returned nothing').toBeTruthy();
    expect(got!.grail, 'no grail chronicle in the rotation').toBeTruthy();

    const g = got!.grail!;
    expect(g.complete, 'the grail chronicle reported complete at 398 of 403').toBe(false);
    expect(
      g.hasPick,
      'the grail chronicle is incomplete and produced NO pick, so dailyCreateAi falls through to ' +
        'removeItem and the Daily Pick is wiped — silently, every day, for good. This is #135.',
    ).toBe(true);

    // it must NAME the state rather than imply a win
    expect(
      g.pick.toLowerCase(),
      'the pick claims a completion while the chronicle is not complete',
    ).not.toMatch(/\bcomplete\b|\bsealed\b|🎉|🏅/);
    expect(g.pick, 'the pick does not carry the real counts').toContain('398/403');
  });

  test('a wall with things left to hunt is unaffected', async ({ page }) => {
    // The other direction. A fix that made every state produce the exhausted sentence would pass
    // the test above and destroy the ordinary case.
    await page.goto(BIBLE);
    await page.waitForTimeout(800);

    const got = await rotateWith(page, {
      found: 10, chronTotal: 403, total: 403, runs: [],
      missing: [{ n: 'Shadow Killer' }, { n: 'Fleshrender' }],
    });
    const g = got!.grail!;
    expect(g.hasPick, 'a wall with missing names produced no pick').toBe(true);
    expect(
      g.exhausted,
      'a wall with 2 missing names was reported as exhausted — the fallback swallowed the ' +
        'ordinary case',
    ).toBe(false);
    expect(g.pick).toMatch(/hunt/i);
  });

  test('a genuinely sealed chronicle is skipped, not given an exhausted sentence', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);

    const got = await rotateWith(page, {
      found: 403, chronTotal: 403, total: 403, runs: [], missing: [],
    });
    const g = got!.grail!;
    expect(g.complete, '403 of 403 did not read as complete').toBe(true);
    expect(
      g.hasPick,
      'a sealed chronicle was given a pick; sealed chronicles are skipped so that dailyCreateAi ' +
        'can reach its all-sealed message',
    ).toBe(false);
  });
});
