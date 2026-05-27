const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(1500);
  
  const result = await page.evaluate(() => {
    const bar = document.getElementById('routine-toggle-pulse');
    const counter = document.getElementById('routine-fires-counter');
    const letters = document.querySelectorAll('.routine-letter');
    const statuses = {};
    letters.forEach(el => {
      statuses[el.getAttribute('data-r')] = el.getAttribute('data-status');
    });
    return {
      widgetExists: !!bar,
      counterText: counter?.textContent,
      counterClass: counter?.className,
      letterCount: letters.length,
      statuses
    };
  });
  console.log('Widget exists:', result.widgetExists);
  console.log('Counter:', result.counterText, `(class="${result.counterClass}")`);
  console.log('Letters:', result.letterCount, 'with statuses:');
  Object.entries(result.statuses).forEach(([k,v]) => console.log(`  ${k}: ${v}`));
  console.log('Page errors:', errors.length);
  await browser.close();
})();
