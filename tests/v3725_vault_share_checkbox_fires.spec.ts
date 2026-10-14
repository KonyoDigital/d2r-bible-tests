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

// Firing the RENDERED checkbox's onchange must write the override — the thing the dead handler
// could not do. v3724's guard missed the break by calling vaultShareToggle() DIRECTLY; here we
// dispatch a real 'change' event on the rendered checkbox so the onchange ATTRIBUTE handler runs,
// which only fires if esc() kept the attribute intact (a truncated attribute compiles to a null
// handler, so the override is never written → RED on the pre-fix bytes).
//
// Done synchronously in ONE evaluate on purpose: renderVault() kicks off an async ownership-proof
// callback (_vaultAskProven) that re-renders the vault and wipes an open panel — so a later async
// locator query raced it and a .uncheck() locator found nothing on CI. Rendering, firing and
// reading the override in the same tick avoids that environment race while still exercising the
// real rendered attribute handler.
test('firing the rendered checkbox onchange writes the mule override and pulls it from shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { w.renderVault(); } catch (e) {}
    try { w._shareSettingsSetOpen(true); } catch (e) {}
    const rows = Array.prototype.slice.call(document.querySelectorAll('#vault-share-settings .vss-row'));
    const row = rows.filter(function (x: any) {
      return ((x.querySelector('.vss-name') || {}).textContent) === 'War Traveler';
    })[0];
    const cb = row ? row.querySelector('input') : null;
    const foundChecked = !!(cb && cb.checked);
    if (cb) {
      cb.checked = false;                                        // what the user's click leaves it at
      cb.dispatchEvent(new Event('change', { bubbles: true }));  // fires the onchange ATTRIBUTE handler
    }
    return {
      found: !!cb,
      foundChecked: foundChecked,
      ov: w._shareOverride('War Traveler'),
      route: (w.suggestMule('War Traveler') || {}).id,
    };
  });
  expect(r.found, 'the War Traveler row rendered a checkbox').toBe(true);
  expect(r.foundChecked, 'War Traveler is checked by default (routes to shared)').toBe(true);
  expect(r.ov, 'firing the rendered onchange recorded the mule override').toBe('mule');
  expect(r.route, 'War Traveler no longer routes to shared').not.toBe('shared');
});
