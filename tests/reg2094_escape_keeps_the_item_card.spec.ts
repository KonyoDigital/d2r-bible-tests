// REG-2094 (#231 eye on v43 0133be32 / 113be899) — Escape closes the card the latch names, never an item card opened
// after it. A material card sets window.__activeMaterial so Escape can close it; navigateToItem (a grail chip, a search
// pick) painted an item card over it and left the latch set, so the next Escape wiped the item card he had just opened.
// The baseline asserts Escape still closes a material card, so this spec cannot pass by Escape doing nothing.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('REG-2094 Escape and the card latch', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => typeof (window as any).openDrop === 'function' && typeof (window as any).navigateToItem === 'function');
  });

  test('baseline: Escape closes an open material card', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Key of Terror'));
    await expect(page.locator('#item-detail')).toHaveClass(/\bshow\b/);
    await page.keyboard.press('Escape');
    await expect(page.locator('#item-detail')).not.toHaveClass(/\bshow\b/);
  });

  test('an item card opened after a material card survives Escape', async ({ page }) => {
    const name = await page.evaluate(() => {
      const w = window as any;
      w.openDrop('Key of Terror');
      const nm = ((w.ITEMS || []).find((i: any) => /Harlequin/.test(i.n)) || (w.ITEMS || [])[0]).n;
      w.navigateToItem(nm, null);
      return nm;
    });
    expect(await page.evaluate(() => (window as any).__activeMaterial)).toBeNull();
    await page.keyboard.press('Escape');
    await expect(page.locator('#item-detail')).toHaveClass(/\bshow\b/);
    await expect(page.locator('#item-detail')).toContainText(name);
  });
});
