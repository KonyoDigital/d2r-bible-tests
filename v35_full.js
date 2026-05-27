const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(700);
  
  // Click a hero pick (Templar's Might has apostrophe — was crashing before)
  await page.locator('#hero-picks .hero-pick').first().evaluate(el => el.click());
  await page.waitForTimeout(400);
  
  // Verify item card opened with simulator visible
  const state = await page.evaluate(() => ({
    cardOpen: !document.getElementById('item-detail-panel')?.classList.contains('hidden'),
    itemName: document.querySelector('.gic-name')?.textContent?.trim()?.substring(0, 60),
    simExists: !!document.getElementById('gic-sim-runs'),
    simBtnExists: !!document.querySelector('.gic-sim-btn'),
    defaultRuns: document.getElementById('gic-sim-runs')?.value,
    bossName: document.querySelector('.gic-meta-chip:nth-child(2)')?.textContent
  }));
  console.log('Card open:', state.cardOpen ? '✓' : '✗');
  console.log('Item name:', state.itemName);
  console.log('Sim widget present:', state.simExists ? '✓' : '✗');
  console.log('Sim default runs:', state.defaultRuns);
  
  // Click simulate
  await page.evaluate(() => document.querySelector('.gic-sim-btn').click());
  await page.waitForTimeout(300);
  
  const simResult = await page.evaluate(() => ({
    barCount: document.querySelectorAll('.gic-sim-bar').length,
    statsCount: document.querySelectorAll('.gic-sim-stats > div').length,
    expected: document.querySelector('.gic-sim-stats > div:first-child .gic-sim-stat-val')?.textContent,
  }));
  console.log('\nSimulation result:');
  console.log(`  bars: ${simResult.barCount}/20`);
  console.log(`  stat tiles: ${simResult.statsCount}/6`);
  console.log(`  expected drops: ${simResult.expected}`);
  
  // Switch to a boss with apostrophe item — Andariel
  await page.evaluate(() => window.openBossDetail('andariel'));
  await page.waitForTimeout(400);
  const heroPicks = await page.evaluate(() => 
    Array.from(document.querySelectorAll('#hero-picks .hero-pick-item')).map(e => e.textContent.trim())
  );
  console.log('\nAndariel picks (apostrophe stress test):');
  heroPicks.slice(0,5).forEach(p => console.log(`  - ${p}`));
  
  // Click Andariel's Visage (her exclusive — heavy apostrophe stress)
  const andriaVisage = heroPicks.find(p => p.includes("Andariel"));
  if (andriaVisage) {
    await page.evaluate((name) => {
      const links = document.querySelectorAll('#hero-picks .hero-pick');
      links.forEach(el => {
        if (el.querySelector('.hero-pick-item')?.textContent.trim() === name) {
          el.click();
        }
      });
    }, andriaVisage);
    await page.waitForTimeout(400);
    const opened = await page.evaluate(() => document.querySelector('.gic-name')?.textContent?.trim()?.substring(0, 40));
    console.log(`  click "${andriaVisage}" → opened "${opened}" ${opened.includes("Andariel") ? '✓' : '✗'}`);
  }
  
  await browser.close();
})();
