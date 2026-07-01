import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v544 — Quick-upload shortcut: one always-visible bar at the top of Tools with a button per stash (Vault /
// Runes / Gems / Materials). Tapping one EXPANDS that stash's card (so the AI-read result is visible) and opens
// the file picker straight into that section's existing AI intake. Konyo: "another shortcut easily clickable
// and uploadable to." Routes to the SAME intake each section already has — just a faster entry point.

test('the quick-upload bar renders 4 stash buttons at the top of Tools', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const bar = document.getElementById('tools-quickup');
    return { bar: !!bar, buttons: bar ? [...bar.querySelectorAll('.tqu-btn')].map((b) => b.textContent!.trim()) : [] };
  });
  expect(r.bar).toBe(true);
  expect(r.buttons.length).toBe(4);
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
