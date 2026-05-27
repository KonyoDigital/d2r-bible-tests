const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(1200); // allow status load
  
  // 1. Widget exists
  const widget = await page.evaluate(() => !!document.getElementById('routine-status-bar'));
  console.log('1. Routine widget present:', widget ? '✅' : '❌');
  
  // 2. Toggle widget visible
  await page.keyboard.press('R');
  await page.waitForTimeout(300);
  const visible = await page.evaluate(() => {
    const b = document.getElementById('routine-status-bar');
    return b && getComputedStyle(b).display !== 'none';
  });
  console.log('2. Widget toggled visible (R key):', visible ? '✅' : '❌');
  
  // 3. Fires counter injected
  const counterExists = await page.evaluate(() => !!document.getElementById('routine-fires-counter'));
  console.log('3. Fires counter present:', counterExists ? '✅' : '❌');
  
  // 4. Status applied to letters
  const letterStatuses = await page.evaluate(() => {
    const els = document.querySelectorAll('.routine-letter');
    return Array.from(els).map(el => ({
      r: el.getAttribute('data-r'),
      status: el.getAttribute('data-status'),
      hasTooltip: !!el.getAttribute('data-tooltip'),
    }));
  });
  const withStatus = letterStatuses.filter(l => l.status).length;
  const withTooltip = letterStatuses.filter(l => l.hasTooltip).length;
  console.log(`4. Letters with status applied: ${withStatus}/${letterStatuses.length}`, withStatus > 0 ? '✅' : '❌');
  console.log(`5. Letters with tooltip data: ${withTooltip}/${letterStatuses.length}`, withTooltip > 0 ? '✅' : '❌');
  
  // 6. Counter text shows fires
  const counterText = await page.evaluate(() => document.getElementById('routine-fires-counter')?.textContent);
  console.log(`6. Counter text: "${counterText}"`, /\d+\/\d+/.test(counterText) ? '✅' : '❌');
  
  // 7. Refresh button works
  const refreshBtn = await page.evaluate(() => !!document.getElementById('routine-refresh-btn'));
  console.log('7. Refresh button present:', refreshBtn ? '✅' : '❌');
  
  // 8. v40 features still work — open boss → field manual injects
  await page.evaluate(() => window.openBossDetail && window.openBossDetail('mephisto'));
  await page.waitForTimeout(400);
  const fmInjected = await page.evaluate(() => !!document.querySelector('.field-manual'));
  console.log('8. v40 Field Manual still injects:', fmInjected ? '✅' : '❌');
  
  // 9. v39 sync pulse still fires on MF change
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  await page.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = '550';
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(100);
  const sync = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log(`9. v39 sync pulse: ${sync} cells`, sync > 30 ? '✅' : '❌');
  
  // 10. v38 unified 20 picks preserved
  await page.evaluate(() => window.openBossDetail('countess'));
  await page.waitForTimeout(300);
  const picks = await page.evaluate(() => document.querySelectorAll('.hero-pick').length);
  console.log(`10. Unified 20 picks: ${picks}`, picks === 20 ? '✅' : '❌');
  
  // 11. Page errors
  console.log(`11. Page errors: ${errors.length}`, errors.length === 0 ? '✅' : `❌ ${errors[0]}`);
  
  // Status data inspection
  console.log('');
  console.log('=== STATUS DATA APPLIED ===');
  letterStatuses.forEach(l => {
    console.log(`  ${l.r}: status=${l.status} tooltip=${l.hasTooltip}`);
  });
  
  await browser.close();
})();
