const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  const t = Date.now();
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  console.log('goto returned at:', Date.now()-t, 'ms');
  // Now run the SAME 400ms wait the test does, then immediately call openBossDetail
  await page.waitForTimeout(400);
  console.log('after 400ms wait, at:', Date.now()-t, 'ms');
  // First boss
  const t1 = Date.now();
  await page.evaluate(() => window.openBossDetail('countess'));
  console.log('first openBossDetail took:', Date.now()-t1, 'ms');
  // Test the EXACT test pattern: 11 bosses with the test's waitForTimeout
  console.log('--- replicating test loop ---');
  const BOSS_IDS = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  const tloop = Date.now();
  try {
    for (const id of BOSS_IDS) {
      const tb = Date.now();
      await page.evaluate((bossId) => window.openBossDetail(bossId), id);
      await page.waitForTimeout(80);
      const cls = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
      const name = await page.locator('.boss-detail-header .bd-name').innerText();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(80);
      const cls2 = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
      console.log(`  ${id}: ${Date.now()-tb}ms cls=${cls} name="${name.substring(0,20)}" cls2=${cls2}`);
    }
  } catch (e) {
    console.log('LOOP ERROR:', e.message.substring(0, 200));
  }
  console.log('loop total:', Date.now()-tloop, 'ms');
  await browser.close();
})();
