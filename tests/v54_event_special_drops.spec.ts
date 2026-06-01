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
    for (const id of ['event-uber-tristram','event-diablo-clone','event-colossal-ancients','event-cow-level','event-22-nights']) {
      await expect(page.locator('#'+id)).toContainText('🏆');
    }
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
    await page.locator('#event-colossal-ancients .event-card-body .zd-item-click', { hasText: 'Colossal Ancient Jewels' }).click();
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Colossal Ancient Jewels');
  });

  test('Colossal Ancients body lists the 6 jewels with real affixes', async ({ page }) => {
    await page.locator('#event-colossal-ancients .event-card-head').click();
    const body = page.locator('#event-colossal-ancients .event-card-body');
    await expect(body).toContainText("Defender's Bile");
    await expect(body).toContainText("Guardian's Thunder");
    await expect(body).toContainText('Psychic Ward');
  });

});
