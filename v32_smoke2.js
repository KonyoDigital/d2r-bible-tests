const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(500);
  const BOSS_IDS = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  for (const id of BOSS_IDS) {
    const t = Date.now();
    await page.evaluate((bossId) => window.openBossDetail(bossId), id);
    const t1 = Date.now()-t;
    await page.waitForTimeout(80);
    const cls = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
    const t2 = Date.now()-t;
    let name;
    try { name = await page.locator('.boss-detail-header .bd-name').innerText({timeout:2000}); }
    catch(e) { name = 'TIMEOUT'; }
    const t3 = Date.now()-t;
    await page.keyboard.press('Escape');
    await page.waitForTimeout(80);
    const cls2 = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
    const t4 = Date.now()-t;
    console.log(`${id}: open=${t1}ms cls=${cls} t2=${t2}ms name="${name.substring(0,30)}" t3=${t3}ms after-esc=${cls2} total=${t4}ms`);
  }
  console.log('errors:', errors.length === 0 ? 'NONE' : errors);
  await browser.close();
})();
