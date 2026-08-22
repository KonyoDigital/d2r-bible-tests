import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v1992 — THE "AUTO LANES" CARDS PROMISED A REEL AND ONLY FLIPPED A FLAG.
 *
 * Konyo, after hunting the Tools tab for a button that did not exist: "i want it to start a reel
 * for the vault manager.. it needs to read and analyze those items that are in the reel", and then
 * the thesis for the whole arc: "the whole point of vault manager and the ai reader and the reels
 * and THE ON AIR is for this to be combined as a whole unit working together".
 *
 * quickIntake armed a lane in d2r_autoLanes and stopped. That flag is only read LATER, by
 * tvStashAutoIntake, while a session is ALREADY recording — so with no session running, all four
 * cards were switches wired to nothing he could see. The card's own subtitle says "the reel reads
 * these", which is true only once a reel exists.
 *
 * The console has had the door open since forever: POST /api/on starts the agent
 * (control_app.py:15598). MEASURED: zero occurrences of /api/on in bible.html before v1992. Two
 * halves, each correct, never joined. [[the-unjoined-end]]
 *
 * This spec pins the OFF-CONSOLE half, which is the one a file:// run can actually observe: the
 * public site must never poke a service on his laptop, and it must SAY so rather than fail silently.
 * The on-console half was proven against a stub on :17771 (never :17772, his live console):
 *     ok        -> "ON AIR — the reel is recording; the vault lane reads and files what it sees."
 *     refusal   -> "could not start the reel: already recording — seal the current session first (42s left)"
 * i.e. the console's REASON reaches the screen instead of being thrown away.
 */

test('the vault lane arms AND reaches for a reel, and says which happened', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);

  // the join exists at all — a deleted/renamed starter must fail here, not silently do nothing
  const wired = await page.evaluate(() => {
    const w: any = window;
    return { start: typeof w._laneStartReel, say: typeof w._laneSay, quick: typeof w.quickIntake };
  });
  expect(wired.start, '_laneStartReel is gone — the lane card is a dead switch again').toBe('function');
  expect(wired.say).toBe('function');
  expect(wired.quick).toBe('function');

  const r = await page.evaluate(() => (window as any).quickIntake('vault'));
  expect(r.ok).toBe(true);
  expect(r.lane).toBe('vault');

  // DEFAULT IS ON: _miniOnAirOn returns true for an unset key, so an untouched lane is armed
  expect(await page.evaluate(() => (window as any)._miniOnAirOn('vault'))).toBe(true);

  await page.waitForTimeout(600);
  const said = await page.evaluate(() => {
    const e = document.getElementById('tqu-say');
    return e ? e.textContent || '' : '';
  });
  // off-console it must be explicit, never silent
  expect(said, 'clicking a lane off-console said nothing at all').not.toBe('');
  expect(said).toContain('ARMED');
  expect(said.toLowerCase()).toContain('console');
});

test('the say-line cannot squeeze the four lane cards', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  await page.evaluate(() => (window as any)._laneSay(
    'a deliberately long message about the console refusing to start the reel right now'));
  await page.waitForTimeout(300);
  const geo = await page.evaluate(() => {
    const say: any = document.getElementById('tqu-say');
    const cards: any = document.querySelector('#tools-quickup .tqu-cards');
    if (!say || !cards) return null;
    const s = say.getBoundingClientRect(), c = cards.getBoundingClientRect();
    return { sTop: s.top, cBottom: c.bottom, sH: s.height, scrollW: say.scrollWidth, clientW: say.clientWidth };
  });
  expect(geo, '#tqu-say or .tqu-cards missing').not.toBeNull();
  // its own row, below the cards — never beside them
  expect(geo!.sTop).toBeGreaterThanOrEqual(geo!.cBottom - 2);
  // and the text is not clipped horizontally
  expect(geo!.scrollW).toBeLessThanOrEqual(geo!.clientW + 1);
});
