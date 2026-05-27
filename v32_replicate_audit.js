const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => { errors.push(e.message); console.log('PAGEERROR:', e.message); });
  page.on('console', m => { if (m.type() === 'error') console.log('CONSOLE-ERR:', m.text()); });
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(400);
  const BOSS_IDS = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  for (const id of BOSS_IDS) {
    const tb = Date.now();
    try {
      await page.evaluate((bossId) => window.openBossDetail(bossId), id);
      await page.waitForTimeout(80);
      const cls = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
      if (/hidden/.test(cls)) { console.log(`${id}: FAIL — overlay hidden, cls=${cls}`); break; }
      const name = await page.locator('.boss-detail-header .bd-name').innerText({timeout:5000});
      await page.keyboard.press('Escape');
      await page.waitForTimeout(80);
      const cls2 = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
      if (!/hidden/.test(cls2)) { console.log(`${id}: FAIL — esc didn't hide, cls2=${cls2}`); break; }
      console.log(`${id}: ${Date.now()-tb}ms ✓ open+name+esc cycle`);
    } catch(e) {
      console.log(`${id}: EXCEPTION after ${Date.now()-tb}ms — ${e.message.substring(0,150)}`);
      break;
    }
  }
  await browser.close();
})();
