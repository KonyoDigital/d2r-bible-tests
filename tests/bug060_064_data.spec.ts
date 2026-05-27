import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-060..064 — data integrity sweep', () => {
  test('BUG-060 ≥ 100 items in calc grid (target 312)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.waitForTimeout(200);
    const count = await page.locator('#item-grid .item-tile').count();
    console.log('item-tile count:', count);
    expect(count).toBeGreaterThanOrEqual(100);
  });

  test('BUG-061 verified-anchor items (🔒) have lock indicator', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // The verified anchors are Mephisto Shako, Andariel SoJ, Andariel BK — check at least one mentions verified/locked in details
    await page.locator('.tab[data-tab="ref"]').click();
    await page.waitForTimeout(150);
    const tab = page.locator('#tab-ref');
    await expect(tab).toContainText(/verified|🔒/i);
  });

  test('BUG-062 Nagelring is searchable', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.locator('#item-search').fill('nagel');
    await page.waitForTimeout(200);
    const found = await page.locator('#item-grid .item-tile:visible').count();
    expect(found).toBeGreaterThanOrEqual(1);
    const txt = await page.locator('#item-grid .item-tile:visible').first().innerText();
    expect(txt.toLowerCase()).toContain('nagelring');
  });

  test("BUG-063 Mephisto TC78 caps qlvl 87 items (Tyrael's blocked)", async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // Inspect BOSSES data — find mephisto, check hell.tcMax is 78
    // Click meph nav chip, scroll to its card, inspect Hell diff column text
    await page.evaluate(() => {
      const el = document.getElementById('mephisto');
      el?.scrollIntoView();
    });
    await page.waitForTimeout(200);
    const hellText = await page.locator('#mephisto').innerText();
    // Hell diff section should mention TC≤78 OR TC 78
    expect(hellText).toMatch(/TC[ \xa0]?(≤|<=)?[ \xa0]?78/i);
  });

  test('BUG-064 Pindle hell mlvl ≤ 86 (blocks qlvl 87 items)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.evaluate(() => document.getElementById('pindle')?.scrollIntoView());
    await page.waitForTimeout(200);
    const text = await page.locator('#pindle').innerText();
    // Pindle's Hell mlvl is 86 — verify "86" appears in context of mlvl
    expect(text).toMatch(/mlvl[ \xa0]?86|86[ \xa0]?(mlvl|·)/i);
  });
});
