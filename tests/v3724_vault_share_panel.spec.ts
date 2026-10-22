import { test, expect } from '@playwright/test';

// gh#235 (v3724) — the ADVANCED SHARED/WAR-STASH CHECKMARK PANEL (the UI half of the v3723 engine).
// renderShareSettings() lists the owned items the rules keep in the shared stash (war-gear + high/vhigh)
// as checkbox toggles, and a toggle writes the override + re-homes.
// The engine is guarded by v3723_vault_share_override.spec.ts; this pins the PANEL that drives it.
//
// V0 spec refresh (#176, GrokBot triage 2026-10-22) — two of its exclusions were retired by his rulings:
//   * REG-2241 (2026-10-15, "torches and anni stay in shared. gheeds gets muled."): Annihilus is no longer a
//     keeper the panel hides. renderShareSettings lists every owned name whose route IS the shared stash
//     (bible.html renderShareSettings: `var eff = (suggestMule(n) || {}).id === 'shared'; if (eff) rows.push
//     ({ n:n, on:true ...})`, with the REG-2241 note "Anni/Torch are NO LONGER hidden here"), so Annihilus is
//     a CHECKED row he can untick to mule it.
//   * REG-2242 (merc gear → shared, his ruling): Andariel's Visage is mercenary gear (MERC_GEAR), routed to
//     the shared stash, so it is a checked row too. "A med item is not listed" is re-anchored on a med-tier
//     NON-merc helm that still routes to its slot mule: Nightwing's Veil (uni-armor, measured on the merged
//     V1 tree). (The triage's example, Shako, is HIGH trade value and routes to shared, so it cannot be it.)

test.beforeEach(async ({ page, context }) => {
  await context.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(
        ['War Traveler', 'Enigma', "Griffon's Eye", 'Raven Frost', 'Annihilus', "Andariel's Visage", "Nightwing's Veil"]));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any).renderShareSettings && (window as any)._shareSettingsSetOpen && (window as any).suggestMule);
});

// The panel lists owned shared candidates as CHECKED toggles, and leaves out an item that mules.
test('the share panel lists owned shared candidates, checked; a med item that mules is left out', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { w.renderVault(); } catch (e) {}
    try { w._shareSettingsSetOpen(true); } catch (e) {}
    const b = document.getElementById('vault-share-settings') as any;
    const rows = ([] as any[]).slice.call(b.querySelectorAll('.vss-row')).map((x: any) => ({
      name: (x.querySelector('.vss-name') || {}).textContent,
      checked: !!(x.querySelector('input') || {}).checked,
    }));
    return { hidden: b.hidden, rows, nightwing: (w.suggestMule("Nightwing's Veil") || {}).id };
  });
  expect(r.hidden, 'the panel paints when there are shared candidates').toBe(false);
  const names = r.rows.map((x: any) => x.name);
  const on = (n: string) => { const row = r.rows.find((x: any) => x.name === n); return !!(row && row.checked); };
  expect(names, 'a high-trade item is a shared candidate').toContain('War Traveler');
  expect(names, 'a war-gear item is a shared candidate').toContain('Enigma');
  expect(names, 'REG-2241: Annihilus rides the shared stash, so it has a toggle').toContain('Annihilus');
  expect(on('Annihilus'), 'REG-2241: Annihilus is shared by default → checked').toBe(true);
  expect(names, 'REG-2242: merc gear is a shared candidate').toContain("Andariel's Visage");
  expect(on("Andariel's Visage"), 'REG-2242: merc gear is shared by default → checked').toBe(true);
  expect(r.nightwing, "PREMISE: Nightwing's Veil (med, not merc gear) routes to its slot mule").toBe('uni-armor');
  expect(names, 'a med item does not route to shared, so it is not listed').not.toContain("Nightwing's Veil");
  expect(on('War Traveler'), 'War Traveler is in the shared stash by default → checked').toBe(true);
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
