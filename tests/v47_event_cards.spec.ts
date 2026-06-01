import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v47 — unify the Events tab. The pinnacle events (Uber Tristram, Secret Cow Level,
// Diablo Clone, Colossal Ancients, 22 Nights of Terror) were flat walls of text;
// they are now click-to-expand detail cards matching the TZ-zone / boss-detail
// inline-expand pattern (accordion: one open at a time).
const EVENT_IDS = [
  'event-uber-tristram',
  'event-cow-level',
  'event-diablo-clone',
  'event-colossal-ancients',
  'event-22-nights',
];

test.describe('v47 event cards — pinnacle events expand inline like boss/TZ detail', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    // event cards live in the (non-default) "ancients" tab — activate it so the
    // inline bodies can actually become visible (ancestor tab is display:none otherwise).
    await page.click('.tab[data-tab="ancients"]');
    await page.waitForTimeout(200);
  });

  test('toggleEventCard is exposed and every event is a collapsible card', async ({ page }) => {
    const r = await page.evaluate((ids) => ({
      hasToggle: typeof (window as any).toggleEventCard,
      cards: ids.map((id) => {
        const c = document.getElementById(id);
        if (!c) return { id, present: false };
        const head = c.querySelector('.event-card-head');
        const body = c.querySelector('.event-card-body');
        return {
          id,
          present: true,
          isCard: c.classList.contains('event-card'),
          headWired: !!head && /toggleEventCard/.test(head.getAttribute('onclick') || ''),
          bodyHidden: !!body && body.hasAttribute('hidden'),
        };
      }),
    }), EVENT_IDS);
    expect(r.hasToggle).toBe('function');
    for (const c of r.cards) {
      expect(c.present, `${c.id} present`).toBe(true);
      expect(c.isCard, `${c.id} is .event-card`).toBe(true);
      expect(c.headWired, `${c.id} head wired to toggleEventCard`).toBe(true);
      expect(c.bodyHidden, `${c.id} body collapsed by default`).toBe(true);
    }
  });

  test('clicking a card header expands its detail inline; re-click collapses', async ({ page }) => {
    const card = page.locator('#event-uber-tristram');
    const body = card.locator('.event-card-body');
    const head = card.locator('.event-card-head');
    await expect(body).toBeHidden();
    // dispatchEvent fires the head's onclick wiring directly — verifies the toggle
    // contract, not a pixel hit-test (sticky header / floating badges can intercept).
    await head.dispatchEvent('click');
    await page.waitForTimeout(200);
    await expect(body).toBeVisible();
    await expect(card).toHaveClass(/open/);
    await expect(body).toContainText('Hellfire Torch');
    await expect(body).toContainText('Key of Terror');
    await head.dispatchEvent('click');
    await page.waitForTimeout(200);
    await expect(body).toBeHidden();
    await expect(card).not.toHaveClass(/open/);
  });

  test('accordion — opening one event collapses the previously open one', async ({ page }) => {
    const a = page.locator('#event-cow-level');
    const b = page.locator('#event-diablo-clone');
    await a.locator('.event-card-head').dispatchEvent('click');
    await page.waitForTimeout(200);
    await expect(a.locator('.event-card-body')).toBeVisible();
    await b.locator('.event-card-head').dispatchEvent('click');
    await page.waitForTimeout(200);
    await expect(b.locator('.event-card-body')).toBeVisible();
    await expect(a.locator('.event-card-body')).toBeHidden();
    await expect(a).not.toHaveClass(/open/);
  });

  test('each event body retains its full reference content', async ({ page }) => {
    const expectations: Record<string, string> = {
      'event-cow-level': "Wirt's Leg",
      'event-diablo-clone': 'Annihilus',
      'event-colossal-ancients': 'Colossal Jewels',
      'event-22-nights': 'modifier',
    };
    for (const [id, needle] of Object.entries(expectations)) {
      const card = page.locator(`#${id}`);
      await card.locator('.event-card-head').dispatchEvent('click');
      await page.waitForTimeout(180);
      await expect(card.locator('.event-card-body')).toContainText(needle);
    }
  });

  test('no leftover magenta .colossal nodes remain in the events tab', async ({ page }) => {
    const stray = await page.evaluate(() =>
      document.querySelectorAll('#tab-ancients .colossal').length);
    expect(stray).toBe(0);
  });
});
