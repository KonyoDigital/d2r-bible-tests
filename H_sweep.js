const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message.substring(0,150)));
  await page.goto('file://' + (process.argv[2] || path.resolve(__dirname, 'bible_routes.html')));
  await page.waitForTimeout(800);
  const items = await page.evaluate(() => ITEMS.map(i => i.n));
  const t0 = Date.now();
  let opened = 0, failed = [];
  for (const name of items) {
    await page.evaluate(n => window.openItemDetail(n), name);
    await page.waitForTimeout(12);
    const ok = await page.evaluate(() => {
      const p = document.getElementById('item-detail-panel');
      return p && !p.classList.contains('hidden') && p.innerHTML.length > 100;
    });
    if (ok) opened++; else failed.push(name);
    await page.evaluate(() => window.closeItemDetail && window.closeItemDetail());
  }
  console.log(JSON.stringify({ tested: items.length, opened, fail_count: failed.length, fails: failed.slice(0,20), errors: errors.slice(0,5), elapsed_ms: Date.now()-t0 }));
  await browser.close();
})();
