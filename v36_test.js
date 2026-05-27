const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(700);
  
  // Navigate to calc tab and select an item via search/click
  await page.locator('.tab[data-tab="calc"]').click();
  await page.waitForTimeout(400);
  
  // Type in search to filter, then click first item
  await page.locator('#item-search').fill("Shako");
  await page.waitForTimeout(300);
  
  // Click first matching item
  const firstItem = page.locator('.item-card, .item-tile, [data-item]').first();
  const itemExists = await firstItem.count();
  console.log(`Item search returned: ${itemExists} matches`);
  
  if (itemExists > 0) {
    await firstItem.evaluate(el => el.click());
    await page.waitForTimeout(500);
    
    // Check for power user deep dive
    const puvExists = await page.evaluate(() => !!document.querySelector('.puv-deep-dive'));
    console.log(`Power User Deep Dive panel: ${puvExists ? '✓' : '✗'}`);
    
    if (puvExists) {
      const confidenceCells = await page.evaluate(() => document.querySelectorAll('.puv-conf-cell').length);
      console.log(`  Confidence cells: ${confidenceCells}/7`);
      
      const mfCells = await page.evaluate(() => document.querySelectorAll('.puv-mf-cell').length);
      console.log(`  MF comparison cells: ${mfCells}`);
      
      const trialChips = await page.evaluate(() => document.querySelectorAll('.puv-trial-chip').length);
      console.log(`  Trial count chips: ${trialChips}/4`);
      
      // Click 500 trials, then RUN
      await page.evaluate(() => window.setPuvTrials(500));
      await page.waitForTimeout(100);
      await page.evaluate(() => document.querySelector('.puv-sim-btn').click());
      await page.waitForTimeout(800);  // 500 trials × 500 runs = 250k Math.random calls
      
      const histoBars = await page.evaluate(() => document.querySelectorAll('.puv-histo-col').length);
      const statTiles = await page.evaluate(() => document.querySelectorAll('.puv-stat').length);
      console.log(`  Histogram columns: ${histoBars}`);
      console.log(`  Stat tiles: ${statTiles}/9`);
      
      const sampleStat = await page.evaluate(() => {
        const labels = Array.from(document.querySelectorAll('.puv-stat-label')).map(e => e.textContent.trim());
        const vals = Array.from(document.querySelectorAll('.puv-stat-val')).map(e => e.textContent.trim());
        return labels.map((l, i) => `${l}: ${vals[i]}`).join(' · ');
      });
      console.log(`\n  Stats:\n  ${sampleStat}`);
    }
  }
  await browser.close();
})();
