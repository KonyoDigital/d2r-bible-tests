import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v549 — MULTI-PLAYER CHRONICLE. The owner's 45 created runewords are seeded as a durable floor every load, which
// wrongly pre-fills a NEW player's Chronicle. A 'fresh' profile flag (d2r_rwProfile='fresh', set by the Chronicle
// Reset button) suppresses the seed so a new player tracks their own from zero; the owner can re-load the seed.
// Konyo: "each to his own cookies right?"

test('default profile: the owner seed IS applied (durable floor, unchanged behaviour)', async ({ page }) => {
  await page.addInitScript(() => { localStorage.removeItem('d2r_rwMade'); localStorage.removeItem('d2r_rwProfile'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    return { count: Object.keys(made).length, fresh: (window as any)._rwIsFresh() };
  });
  expect(r.fresh).toBe(false);
  expect(r.count).toBeGreaterThanOrEqual(45);   // owner's floor present
});

test('a fresh profile suppresses the seed entirely — Chronicle starts empty', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_rwProfile', 'fresh'); localStorage.removeItem('d2r_rwMade'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    return { count: Object.keys(made).length, fresh: (window as any)._rwIsFresh() };
  });
  expect(r.fresh).toBe(true);
  expect(r.count).toBe(0);   // no owner seed forced onto a new player
});

test('a fresh player can mark their OWN runeword and it sticks (no floor re-adds the owner set)', async ({ page }) => {
  await page.addInitScript(() => { localStorage.setItem('d2r_rwProfile', 'fresh'); localStorage.removeItem('d2r_rwMade'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.rwToggleMade('Spirit');   // the new player forges Spirit
    const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    return { keys: Object.keys(made), hasSpirit: !!made['Spirit'] };
  });
  expect(r.hasSpirit).toBe(true);
  expect(r.keys.length).toBe(1);   // ONLY their own, not the owner's 45
});

test('chronicleReset() flips to fresh + empties; chronicleLoadSeed() restores the owner set', async ({ page }) => {
  await page.addInitScript(() => { localStorage.removeItem('d2r_rwMade'); localStorage.removeItem('d2r_rwProfile'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  // stub uiConfirm to auto-accept so the flow runs headless
  const r = await page.evaluate(async () => {
    const w: any = window;
    w.uiConfirm = async () => true;
    await w.chronicleReset();
    const afterReset = { fresh: w._rwIsFresh(), count: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length };
    await w.chronicleLoadSeed();
    const afterSeed = { fresh: w._rwIsFresh(), count: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length };
    return { afterReset, afterSeed };
  });
  expect(r.afterReset.fresh).toBe(true);
  expect(r.afterReset.count).toBe(0);
  expect(r.afterSeed.fresh).toBe(false);
  expect(r.afterSeed.count).toBeGreaterThanOrEqual(45);
});

test('the Reset control renders in the Chronicle and reflects the profile mode', async ({ page }) => {
  await page.addInitScript(() => { localStorage.removeItem('d2r_rwProfile'); localStorage.removeItem('d2r_rwMade'); });
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('tools'); w.renderRunewordChronicle(); w.renderChronicleProfile();
    const owner = document.getElementById('rwc-profile')?.textContent || '';
    localStorage.setItem('d2r_rwProfile', 'fresh'); w.renderChronicleProfile();
    const fresh = document.getElementById('rwc-profile')?.textContent || '';
    return { owner, fresh };
  });
  expect(r.owner).toMatch(/Reset to a fresh Chronicle/);
  expect(r.fresh).toMatch(/Fresh profile/);
});
