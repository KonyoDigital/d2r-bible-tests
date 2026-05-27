const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(800);
  const BOSS_IDS = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  const results = {};
  for (const bid of BOSS_IDS) {
    await page.evaluate(b => window.openBossDetail(b), bid);
    await page.waitForTimeout(180);
    const n = await page.evaluate(() => document.querySelectorAll('.hero-pick').length);
    results[bid] = n;
    await page.keyboard.press('Escape');
    await page.waitForTimeout(60);
  }
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})();
