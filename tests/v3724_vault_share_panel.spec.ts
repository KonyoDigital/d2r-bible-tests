import { test, expect } from '@playwright/test';

// gh#235 (v3724) — the ADVANCED SHARED/WAR-STASH CHECKMARK PANEL (the UI half of the v3723 engine).
// renderShareSettings() lists the owned items the rules keep in the shared stash (war-gear + high/vhigh)
// as checkbox toggles, excludes keepers (Anni/Torch/Gheed's), and a toggle writes the override + re-homes.
// The engine is guarded by v3723_vault_share_override.spec.ts; this pins the PANEL that drives it.

test.beforeEach(async ({ page, context }) => {
  await context.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(
        ['War Traveler', 'Enigma', "Griffon's Eye", 'Raven Frost', 'Annihilus', "Andariel's Visage"]));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any).renderShareSettings && (window as any)._shareSettingsSetOpen && (window as any).suggestMule);
});

// The panel lists owned shared candidates as CHECKED toggles, and excludes keepers + non-candidates.
test('the share panel lists owned shared candidates, checked; keepers and med items are left out', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { w.renderVault(); } catch (e) {}
    try { w._shareSettingsSetOpen(true); } catch (e) {}
    const b = document.getElementById('vault-share-settings') as any;
    const rows = ([] as any[]).slice.call(b.querySelectorAll('.vss-row')).map((x: any) => ({
      name: (x.querySelector('.vss-name') || {}).textContent,
      checked: !!(x.querySelector('input') || {}).checked,
    }));
    return { hidden: b.hidden, rows };
  });
  expect(r.hidden, 'the panel paints when there are shared candidates').toBe(false);
  const names = r.rows.map((x: any) => x.name);
  expect(names, 'a high-trade item is a shared candidate').toContain('War Traveler');
  expect(names, 'a war-gear item is a shared candidate').toContain('Enigma');
  expect(names, 'a keeper (Annihilus) is never offered a shared toggle').not.toContain('Annihilus');
  expect(names, 'a med item does not route to shared, so it is not listed').not.toContain("Andariel's Visage");
  const wt = r.rows.find((x: any) => x.name === 'War Traveler');
  expect(wt && wt.checked, 'War Traveler is in the shared stash by default → checked').toBe(true);
});

// Unchecking a row writes the override and takes the item out of the shared stash.
test('unchecking a row sets the override to mule and removes it from shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { w.renderVault(); } catch (e) {}
    w.vaultShareToggle('War Traveler', false);
    return { ov: w._shareOverride('War Traveler'), route: (w.suggestMule('War Traveler') || {}).id };
  });
  expect(r.ov, 'the override is recorded as mule').toBe('mule');
  expect(r.route, 'War Traveler no longer routes to the shared stash').not.toBe('shared');
});
