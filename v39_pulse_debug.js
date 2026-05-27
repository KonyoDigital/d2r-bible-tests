const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('[BROWSER]', msg.text()));
  
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(1000);
  
  console.log('Listener attached?', await page.evaluate(() => {
    return typeof window._v39_whenReady === 'function';
  }));
  
  // Check existence of target cells BEFORE MF change
  const beforeMF = await page.evaluate(() => {
    return {
      diffCol: document.querySelectorAll('.diff-col').length,
      heroPickChance: document.querySelectorAll('.hero-pick-chance').length,
      sdItemRate: document.querySelectorAll('.sd-item-rate').length,
      verifiedCell: document.querySelectorAll('.verified-cell').length,
      statValue: document.querySelectorAll('.stat-value').length,
    };
  });
  console.log('Cell counts before MF change:', JSON.stringify(beforeMF));
  
  // Manually run the pulse function
  console.log('Trying manual pulse...');
  const manualResult = await page.evaluate(() => {
    if (typeof _v39_pulseAllSyncedCells === 'function') {
      _v39_pulseAllSyncedCells();
      return { exists: true, syncingNow: document.querySelectorAll('.syncing').length };
    }
    return { exists: false };
  });
  console.log('Manual pulse result:', JSON.stringify(manualResult));
  
  // Wait a frame
  await page.waitForTimeout(50);
  const afterManual = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log('Syncing count 50ms after manual pulse:', afterManual);
  
  // Now try via MF slider
  await page.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = '600';
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(80);
  const afterMF = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log('Syncing count 80ms after MF dispatch:', afterMF);
  
  // Also check what listener gives us
  const listenerCheck = await page.evaluate(() => {
    // Try calling pulse with the actual querySelectorAll the function uses
    const targets = document.querySelectorAll(
      '.diff-col, .hero-pick-chance, .sd-item-rate, .verified-cell, .stat-value'
    );
    return targets.length;
  });
  console.log('Targets matched by selector:', listenerCheck);
  
  await browser.close();
})();
