import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-100..107 — polish sweep', () => {
  test('BUG-100 hero card 5 picks render', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.evaluate(() => (window as any).switchTab('main'));   // v681 — TOOLS is the landing tab now (v680); hero picks live on Main
    await page.waitForTimeout(300);
    // v63: dropdown sections default-collapsed → expand Today's Best Grail Picks first
    await page.locator('.sec-h', { hasText: 'Best Grail Picks' }).click();
    const hero = page.locator('#hero, .hero-card, [class*="hero"]').first();
    await expect(hero).toBeVisible();
  });

  test('BUG-102 grail progress dial element exists', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const dial = page.locator('#grail-progress, .grail-dial, [class*="grail"]').first();
    expect(await dial.count()).toBeGreaterThanOrEqual(1);
  });

  test('BUG-104 set tracker renders 7+ sets', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="rotw"]').click();
    await page.waitForTimeout(200);
    const sets = await page.locator('#set-tracker .set-card').count();
    expect(sets).toBeGreaterThanOrEqual(7);
  });

  test('BUG-105 cube recipes block exists in ref/rotw', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // Just check at least one tab mentions cube
    let foundCube = false;
    for (const tab of ['rotw', 'ref', 'runes']) {
      await page.locator(`.tab[data-tab="${tab}"]`).click();
      await page.waitForTimeout(150);
      const text = await page.locator(`#tab-${tab}`).innerText();
      if (/cube|cubed|cubing/i.test(text)) { foundCube = true; break; }
    }
    expect(foundCube).toBe(true);
  });

  /* v1754 — THIS TEST HAD NEVER RUN, AND THE FEATURE WAS FINE ALL ALONG.
     It asked `el.offsetParent !== null` as its visibility check. #help-modal is `position:fixed`,
     and offsetParent is null for EVERY fixed-position element by specification — so the check could
     never be true, helpVis was always null, and the next line skipped. "help feature may not exist
     yet" was a guess that then made itself unfalsifiable: the board has 39 position:fixed rules.

     Measured, the feature works exactly as the on-screen hint promises
     ("/ search · 1-9·0 tabs · ? help · Esc close"):

         at rest  -> class "help-modal",       display none,  0x0
         after ?  -> class "help-modal show",  display flex,  1440x1000
         after Esc-> class "help-modal",       display none,  0x0

     So it now asserts geometry — display plus a real rect — which is true of fixed and flowed
     elements alike, and it checks the CLOSE half too, because a modal that opens and cannot be
     dismissed is worse than one that never opens. [[feedback_blind_fixture_green_gate]] */
  test('BUG-106 help (?) modal opens, and Esc closes it', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);

    const read = () => page.evaluate(() => {
      const m = document.getElementById('help-modal');
      if (!m) return { exists: false, shown: false };
      const cs = getComputedStyle(m);
      const r = m.getBoundingClientRect();
      return { exists: true, shown: cs.display !== 'none' && r.width > 0 && r.height > 0 };
    });

    const atRest = await read();
    expect(atRest.exists, 'the board has no #help-modal at all').toBe(true);
    // non-vacuity: it must start CLOSED, or "it opened" proves nothing
    expect(atRest.shown, 'the help modal is already open before the shortcut is pressed').toBe(false);

    await page.keyboard.press('?');
    await page.waitForTimeout(400);
    expect((await read()).shown, 'pressing ? did not open the help modal').toBe(true);

    await page.keyboard.press('Escape');
    await page.waitForTimeout(400);
    expect((await read()).shown, 'Escape did not close the help modal').toBe(false);
  });

  test('BUG-107 reset button exists in footer', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const btn = page.locator('.reset-btn, [onclick*="localStorage.clear"]').first();
    await expect(btn).toBeAttached();
  });
});
