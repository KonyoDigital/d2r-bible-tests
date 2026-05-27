const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(700);
  const first = page.locator('#hero-picks .hero-pick').first();
  const name = await first.evaluate(el => el.querySelector('.hero-pick-item')?.textContent?.trim());
  console.log(`First pick: "${name}"`);
  await first.evaluate(el => el.click());
  await page.waitForTimeout(300);
  const cardOpen = await page.evaluate(() => {
    const p = document.getElementById('item-detail-panel');
    return p && !p.classList.contains('hidden') && p.innerHTML.length > 100;
  });
  console.log(`Card opened: ${cardOpen ? '✓' : '✗'}`);
  console.log(`Errors: ${errors.length === 0 ? 'NONE ✓' : errors.slice(0,2).join(' | ')}`);
  await browser.close();
})();
