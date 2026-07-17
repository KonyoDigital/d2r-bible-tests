// v786 — THE OPEN DOORS (night R3 pick 1): the app rail sends BARE tab hashes with ?app=1.
// The v680 parse-time normalizer was clobbering 4 of the 5 family tabs to #tools before the
// router ran — and the family tripwire drove switchTab() directly, so it stayed green over
// the broken door. THIS spec walks the real consumer path: goto ?app=1#<tab> → tab active.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const TABS = ['session', 'tools', 'forge', 'funi', 'fsets'];

for (const tab of TABS) {
  test(`app-rail deep-link #${tab} opens its real tab`, async ({ page }) => {
    await page.goto(BIBLE + `?app=1#${tab}`);
    await page.waitForTimeout(900);
    // the hash must SURVIVE parse (not normalized to #tools)
    const hash = await page.evaluate(() => window.location.hash);
    expect(hash).toBe(`#${tab}`);
    // and the router must land on that tab
    const active = page.locator(`.tab[data-tab="${tab}"].active`);
    await expect(active).toHaveCount(1, { timeout: 4000 });
  });
}

test('plain-browser bare hash still homes to tools (v680 intact)', async ({ page }) => {
  await page.goto(BIBLE + '#funi');   // no ?app=1 → residue, not intent
  await page.waitForTimeout(900);
  const hash = await page.evaluate(() => window.location.hash);
  expect(hash).toBe('#tools');
});
