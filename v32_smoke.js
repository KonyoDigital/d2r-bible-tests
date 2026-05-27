const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('CONSOLE: ' + m.text()); });
  const t0 = Date.now();
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  console.log('goto took', Date.now()-t0, 'ms');
  await page.waitForTimeout(2000);
  console.log('after 2s wait:');
  console.log('  errors:', errors.length === 0 ? 'NONE' : errors.slice(0,5));
  // Check openBossDetail exists
  const exists = await page.evaluate(() => typeof window.openBossDetail);
  console.log('  typeof openBossDetail:', exists);
  // Try calling it
  const t1 = Date.now();
  try {
    await page.evaluate(() => { window.openBossDetail('countess'); });
    console.log('  openBossDetail(countess):', Date.now()-t1, 'ms');
  } catch(e) {
    console.log('  openBossDetail ERROR:', e.message.substring(0, 200));
  }
  // Check overlay state
  const cls = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
  console.log('  overlay class:', cls);
  await browser.close();
})();
