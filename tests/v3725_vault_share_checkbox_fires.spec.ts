import { test, expect } from '@playwright/test';

// gh#235 (v3725) — the share/war-stash checkbox must FIRE when the user clicks it.
// v3724 rendered the panel with onchange="window.vaultShareToggle(" + JSON.stringify(name) + ...",
// but JSON.stringify emits double quotes INSIDE a double-quoted attribute, so the attribute ended
// at the first quote and the handler was a dead, truncated call. The v3724 guard called
// vaultShareToggle() DIRECTLY and never clicked the checkbox, so it missed the dead handler.
// This spec drives a REAL uncheck (a trusted change event) and proves the override is written —
// it goes RED on the pre-fix bytes (esc() absent → broken attribute → no call → no override).

test.beforeEach(async ({ page, context }) => {
  await context.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(['War Traveler', 'Enigma', 'Raven Frost']));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any).renderShareSettings && (window as any)._shareSettingsSetOpen && (window as any).suggestMule);
});

// The attribute the browser actually parsed must carry the full call, not a truncated one.
test('the checkbox onchange carries the whole call, not a truncated one', async ({ page }) => {
  const attr = await page.evaluate(() => {
    const w = window as any;
    try { w.renderVault(); } catch (e) {}
    try { w._shareSettingsSetOpen(true); } catch (e) {}
    const inp = document.querySelector('#vault-share-settings .vss-row input') as any;
    return inp ? (inp.getAttribute('onchange') || '') : null;
  });
  expect(attr, 'a checkbox is rendered').not.toBeNull();
  // the real item name must survive inside the handler (escaped quotes decode back to a string arg)
  expect(attr, 'the call reaches this.checked — the attribute was not cut off at the name quote')
    .toContain('this.checked');
});

// A real user click on the checkbox writes the override (the thing the dead handler could not do).
test('a real uncheck click writes the mule override and pulls it from shared', async ({ page }) => {
  const box = page.locator('#vault-share-settings');
  await page.evaluate(() => { const w = window as any; try { w.renderVault(); } catch (e) {} try { w._shareSettingsSetOpen(true); } catch (e) {} });
  const cb = box.locator('.vss-row', { hasText: 'War Traveler' }).locator('input');
  await expect(cb, 'War Traveler is checked by default').toBeChecked();
  await cb.uncheck();   // a trusted change event — exactly what the user does
  const r = await page.evaluate(() => {
    const w = window as any;
    return { ov: w._shareOverride('War Traveler'), route: (w.suggestMule('War Traveler') || {}).id };
  });
  expect(r.ov, 'the click fired the handler and recorded the override').toBe('mule');
  expect(r.route, 'War Traveler no longer routes to shared').not.toBe('shared');
});
