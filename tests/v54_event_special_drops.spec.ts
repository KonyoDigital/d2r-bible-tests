import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v54 — pinnacle-event special drops. Each pinnacle event now leads its
// expandable body with a "holy grail of this event" block. Uber Tristram ->
// Hellfire Torch and Diablo Clone -> Annihilus are clickable, routing to the
// same material card (openDrop -> #item-detail .material-card) the rest of the
// site uses. Colossal Jewels is styled text (no codex card); Cow + 22 Nights
// honestly state they are farms/windows, not a single grail. No odds fabricated.
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

  test('Uber Tristram leads with a Hellfire Torch chip wired to openDrop', async ({ page }) => {
    await page.locator('#event-uber-tristram .event-card-head').click();
    const body = page.locator('#event-uber-tristram .event-card-body');
    await expect(body).toBeVisible();
    const chip = body.locator('.zd-item-click', { hasText: 'Hellfire Torch' });
    await expect(chip).toBeVisible();
    await expect(chip).toHaveAttribute('onclick', /openDrop\('Hellfire Torch'\)/);
  });

  test('Diablo Clone leads with an Annihilus chip wired to openDrop', async ({ page }) => {
    await page.locator('#event-diablo-clone .event-card-head').click();
    const body = page.locator('#event-diablo-clone .event-card-body');
    await expect(body).toBeVisible();
    const chip = body.locator('.zd-item-click', { hasText: 'Annihilus' });
    await expect(chip).toBeVisible();
    await expect(chip).toHaveAttribute('onclick', /openDrop\('Annihilus'\)/);
  });

  test('clicking the event Torch chip opens the unified material card', async ({ page }) => {
    await page.locator('#event-uber-tristram .event-card-head').click();
    await page.locator('#event-uber-tristram .event-card-body .zd-item-click', { hasText: 'Hellfire Torch' }).click();
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Hellfire Torch');
  });

  test('Colossal Ancients shows Colossal Jewels reward (styled text, no codex card)', async ({ page }) => {
    await page.locator('#event-colossal-ancients .event-card-head').click();
    const body = page.locator('#event-colossal-ancients .event-card-body');
    await expect(body).toBeVisible();
    await expect(body).toContainText('Colossal Jewels');
  });
});
