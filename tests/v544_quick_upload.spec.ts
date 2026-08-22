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

test('each quick-upload target has a real intake file input', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => ({
    fn: typeof (window as any).quickIntake,
    vault: !!document.getElementById('vault-intake-file'),
    rune: !!document.getElementById('rune-intake-file'),
    gem: !!document.getElementById('gem-intake-file'),
    material: !!document.getElementById('material-intake-file'),
  }));
  expect(r.fn).toBe('function');
  expect(r.vault && r.rune && r.gem && r.material).toBe(true);
});

test('quickIntake expands the target card and triggers its file picker', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const card = document.getElementById('mule-vault-card')!;
    const wasCollapsed = card.classList.contains('collapsed');
    let clicked = false;
    const f = document.getElementById('vault-intake-file') as HTMLInputElement;
    const orig = f.click; (f as any).click = () => { clicked = true; };
    w.quickIntake('vault');
    const expanded = !document.getElementById('mule-vault-card')!.classList.contains('collapsed');
    (f as any).click = orig;
    return { wasCollapsed, expanded, clicked };
  });
  expect(r.wasCollapsed).toBe(true);   // card starts collapsed
  expect(r.expanded).toBe(true);       // quick-upload expands it so the result is visible
  expect(r.clicked).toBe(true);        // …and opens that section's file picker
});
