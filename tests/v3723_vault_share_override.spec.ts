import { test, expect } from '@playwright/test';

// gh#235 / #264 (2026-10-14) — HIS PER-ITEM SHARED-STASH SWITCH. The war-gear and high/vhigh-trade
// rules in suggestMule are the DEFAULT; _shareOverride lets him force ONE item in or out of the
// shared (war) stash. His words: "so i can checkmark what should or should not be in the shared/war
// stash ... like war traveler.. eventually i dont want it there and might mule it.. so if i uncheck
// it it can remove it from the shared and mule it automatically".
//
// Pins the LAW, not a route id: _shareDefault is the oracle for what the rules alone say, so if the
// trade tiers are ever retuned this still follows them. RED-proved via the CDP harness
// (scratchpad/share_override_probe.py): with the `_ov !== 'mule'` gate removed, unchecking a
// high-trade item leaves it `shared` — the gate is load-bearing.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any).suggestMule && (window as any)._shareOverride &&
    (window as any)._shareDefault && (window as any)._setShareOverride);
  // a clean slate — no override may leak between cases
  await page.evaluate(() => { try { localStorage.removeItem('d2r_vaultShareOverride'); (window as any).__shareOvCache = null; } catch (e) {} });
});

const routeOf = (name: string) => (page: any) =>
  page.evaluate((n: string) => { const s = (window as any).suggestMule(n); return (s && s.id) || null; }, name);

// A default-shared item, unchecked, STOPS being shared and gets a real mule home.
test('unchecking a default-shared item removes it from the shared stash', async ({ page }) => {
  const W = 'War Traveler';
  const def = await page.evaluate((n: string) => (window as any)._shareDefault(n), W);
  expect(def, 'precondition: the rules put War Traveler in the shared stash').toBe('shared');
  expect(await routeOf(W)(page), 'default route follows the rule').toBe('shared');

  const eff = await page.evaluate((n: string) => (window as any)._setShareOverride(n, 'mule'), W);
  expect(eff, 'effective state after unchecking').toBe('mule');
  expect(await page.evaluate((n: string) => (window as any)._shareOverride(n), W)).toBe('mule');

  const r = await routeOf(W)(page);
  expect(r, 'unchecked → not the shared stash').not.toBe('shared');
  expect(r, 'unchecked → a real mule, not nowhere').toBeTruthy();
});

// A default-mule item, force-checked, BECOMES shared.
// V0 spec refresh (#176) — REG-2242, his ruling (mercenary gear lives in the shared stash): Andariel's Visage is
// MERC_GEAR, so its rule default is now 'shared' and it can no longer be the default-mule case. Re-anchored on a
// med-tier helm that is NOT merc gear and still mules by default: Nightwing's Veil (rules → uni-armor, measured on
// the merged V1 tree). Shako, the triage's suggestion, is HIGH trade value and already shared by default.
test('force-checking a default-mule item puts it in the shared stash', async ({ page }) => {
  const M = "Nightwing's Veil";
  const def = await page.evaluate((n: string) => (window as any)._shareDefault(n), M);
  expect(def, 'precondition: the rules do NOT share this (med tier, not merc gear)').toBe('mule');
  expect(await routeOf(M)(page), 'default route is not shared').not.toBe('shared');

  const eff = await page.evaluate((n: string) => (window as any)._setShareOverride(n, 'shared'), M);
  expect(eff).toBe('shared');
  expect(await routeOf(M)(page), 'forced → shared stash').toBe('shared');
});

// An override that EQUALS the rule default is not stored, so retuning the rules still flows through.
test('an override equal to the default is not persisted', async ({ page }) => {
  const W = 'War Traveler'; // default 'shared'
  await page.evaluate((n: string) => (window as any)._setShareOverride(n, 'shared'), W);
  expect(await page.evaluate((n: string) => (window as any)._shareOverride(n), W),
    'setting shared on an already-shared item stores nothing').toBeNull();
  expect(await routeOf(W)(page)).toBe('shared');
});

// Clearing ('auto') hands the item back to the rules.
test("clearing an override ('auto') restores the rule route", async ({ page }) => {
  const W = 'War Traveler';
  await page.evaluate((n: string) => (window as any)._setShareOverride(n, 'mule'), W);
  expect(await routeOf(W)(page)).not.toBe('shared');
  await page.evaluate((n: string) => (window as any)._setShareOverride(n, 'auto'), W);
  expect(await page.evaluate((n: string) => (window as any)._shareOverride(n), W), 'override cleared').toBeNull();
  expect(await routeOf(W)(page), 'back to the rule route').toBe('shared');
});
