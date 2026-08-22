import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v544 — Quick-upload shortcut: one always-visible bar at the top of Tools with a button per stash (Vault /
// Runes / Gems / Materials). Tapping one EXPANDS that stash's card (so the AI-read result is visible) and opens
// the file picker straight into that section's existing AI intake. Konyo: "another shortcut easily clickable
// and uploadable to." Routes to the SAME intake each section already has — just a faster entry point.

/* v1975 — THE BAR SURVIVED; THE FILE PICKERS DID NOT.
 *
 * Konyo: "surgically remove … the manual ones and have like a on/off for that specific MINI ON AIR …
 * that way it forces me and my cuzin also to just hit reel session instead of anything manual."
 *
 * So the four stash entries above are no longer buttons that open a file dialog — they are ON/OFF
 * lane pills. What did NOT change is the machinery behind them: tvStashAutoIntake hands the reel's
 * frame to the very same window.runeIntake / gemIntake / materialIntake, so each section keeps its
 * own crop (_runeSheetPrep, _tallyPrepImage) and its own `kind` template. The manual button was only
 * ever a second way to supply the same File.
 *
 * quickIntake KEEPS ITS NAME on purpose. Every call site guards with `window.quickIntake &&`, so
 * deleting it would have failed SILENTLY — the worst possible outcome. It now expands the card as
 * before and arms the lane instead of asking for a photo.
 */
test('the lane bar renders 4 stash lanes at the top of Tools', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const bar = document.getElementById('tools-quickup');
    return { bar: !!bar, buttons: bar ? [...bar.querySelectorAll('.tqu-btn')].map((b) => b.textContent!.trim()) : [] };
  });
  expect(r.bar).toBe(true);
  expect(r.buttons.length, 'four lanes: Vault / Runes / Gems / Mats').toBe(4);
  expect(r.buttons.join(' ')).toMatch(/Vault/);
  expect(r.buttons.join(' ')).toMatch(/Runes/);
  expect(r.buttons.join(' ')).toMatch(/Gems/);
});

/* v1993 — THIS SPEC ASSERTED THE DOOR KONYO ASKED ME TO REMOVE.
 *
 * v544 built a quick-upload bar: tap a card, expand it, open that section's FILE PICKER. v1975 and
 * v1976 retired exactly that — "surgically remove them all… that way it forces me and my cuzin to
 * just hit reel session instead of anything manual" — so #vault-intake-file and its three siblings
 * no longer exist. These two tests kept asserting they did, and Playwright waited out its full 120s
 * on a selector that will never appear. CI shard 4/6 has been RED on every ship since.
 *
 * A test that pins a retired contract is worse than no test: it is a red gate that everyone learns
 * to scroll past, which is how the next REAL failure goes unread.
 *
 * So they now pin the CURRENT contract, which is what v1992 finished wiring: tapping a lane card
 * expands it, keeps the lane armed, and asks the console to start a reel — the intake functions
 * still exist and are fed by tvStashAutoIntake instead of by a human with a screenshot.
 */
test('the manual file doors are gone and the intake functions they fed are not', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => ({
    quick: typeof (window as any).quickIntake,
    start: typeof (window as any)._laneStartReel,
    doors: document.querySelectorAll(
      '#vault-intake-file,#rune-intake-file,#gem-intake-file,#material-intake-file').length,
    fns: ['vaultIntake', 'runeIntake', 'gemIntake', 'materialIntake']
      .map((f) => typeof (window as any)[f]),
  }));
  expect(r.doors, 'a manual intake file input came back — the manual door was removed on purpose').toBe(0);
  expect(r.quick).toBe('function');
  expect(r.start, 'the lane card no longer reaches for a reel').toBe('function');
  // the seam tvStashAutoIntake dispatches to BY NAME must survive the door's removal
  for (const t of r.fns) expect(t).toBe('function');
});

test('tapping a lane expands its card, keeps the lane armed, and reaches for a reel', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const card = document.getElementById('mule-vault-card')!;
    const wasCollapsed = card.classList.contains('collapsed');
    let reached = false;
    const orig = w._laneStartReel;
    w._laneStartReel = () => { reached = true; return Promise.resolve({ ok: false }); };
    const out = w.quickIntake('vault');
    w._laneStartReel = orig;
    return {
      wasCollapsed, out, reached,
      expanded: !document.getElementById('mule-vault-card')!.classList.contains('collapsed'),
      armed: w._miniOnAirOn('vault'),
    };
  });
  expect(r.wasCollapsed).toBe(true);          // card starts collapsed
  expect(r.expanded).toBe(true);              // tapping expands it so the result is visible
  expect(r.out.ok).toBe(true);
  expect(r.out.lane).toBe('vault');
  expect(r.armed, 'an untouched lane is ARMED by default — doing nothing must still auto-intake').toBe(true);
  expect(r.reached, 'the lane no longer asks the console to record — it is a dead switch again').toBe(true);
});
