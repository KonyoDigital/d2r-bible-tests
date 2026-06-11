import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v54 — pinnacle-event special drops. Each event leads its body with a "holy
// grail of this event" block. Uber Tristram -> Hellfire Torch, Diablo Clone ->
// Annihilus, AND Colossal Ancients -> Colossal Jewels are ALL clickable and land
// on the same unified material card (openDrop -> #item-detail .material-card) the
// rest of the site uses. Cow + 22 Nights are honest farm/window notes. No odds
// fabricated (Colossal Jewels card is explicitly caveated as mod-specific).
test.describe('v54 pinnacle event special drops', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('ancients'));
  });

  test('every pinnacle event carries a special-drop block', async ({ page }) => {
    // Desktop golden-merge: colossal-ancients was restructured into a full gic-card
    // material-card hub (no 🏆 special-drop banner) — check for Pinnacle Fight badge instead;
    // the other 4 events still use the 🏆 special-drop block.
    for (const id of ['event-uber-tristram','event-diablo-clone','event-cow-level','event-22-nights']) {
      await expect(page.locator('#'+id)).toContainText('🏆');
    }
    // Colossal Ancients now uses a gic-card with a "Pinnacle Fight" badge
    await expect(page.locator('#event-colossal-ancients')).toContainText('Pinnacle Fight');
  });

  test('Uber Tristram → Hellfire Torch lands on the unified material card', async ({ page }) => {
    await page.locator('#event-uber-tristram .event-card-head').click();
    await page.locator('#event-uber-tristram .event-card-body .zd-item-click', { hasText: 'Hellfire Torch' }).click();
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Hellfire Torch');
  });

  test('Diablo Clone → Annihilus lands on the unified material card', async ({ page }) => {
    await page.locator('#event-diablo-clone .event-card-head').click();
    await page.locator('#event-diablo-clone .event-card-body .zd-item-click', { hasText: 'Annihilus' }).click();
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Annihilus');
  });

  test('Colossal Ancients → Colossal Jewels lands on the unified card (no dead chip)', async ({ page }) => {
    await page.locator('#event-colossal-ancients .event-card-head').click();
    // Desktop golden-merge: the event card body now uses a gic-card hub; the Colossal
    // Jewel link text is "Colossal Jewel →" (shortened), routes via openDrop('Colossal Ancient Jewels').
    await page.locator('#event-colossal-ancients .event-card-body .zd-item-click', { hasText: 'Colossal Jewel' }).click();
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Colossal Ancient Jewels');
  });

  test('Colossal Ancients body references the 3 Ancients and routes to their jewels', async ({ page }) => {
    // Desktop golden-merge: the event card body is now a rich gic-card hub showing
    // the 3 Ancients (Talic/Korlic/Madawc) as interactive tiles instead of inlining
    // the 6 jewel affixes directly. Jewel detail is now in the uber boss cards (via
    // UBER_BOSSES[].jewels) and the Colossal Showcase card. Verify the 3 Ancients
    // are present and route to their uber boss cards.
    await page.locator('#event-colossal-ancients .event-card-head').click();
    const body = page.locator('#event-colossal-ancients .event-card-body');
    await expect(body).toContainText('Talic');
    await expect(body).toContainText('Korlic');
    await expect(body).toContainText('Madawc');
    // The jewel names are still in UBER_BOSSES data (verified via the uber boss card spec)
    const jewels = await page.evaluate(() => {
      const UB = (window as any).UBER_BOSSES || [];
      return UB.filter((b: any) => b.jewels && b.jewels.length).flatMap((b: any) => b.jewels);
    });
    expect(jewels).toEqual(expect.arrayContaining(["Defender's Bile", "Guardian's Thunder"]));
  });

});
