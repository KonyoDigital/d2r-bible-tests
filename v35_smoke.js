const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => { errors.push(e.message); console.log('PAGEERROR:', e.message); });
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(800);

  // Click a hero pick to open item card
  const firstPick = page.locator('#hero-picks .hero-pick').first();
  const pickName = await firstPick.evaluate(el => el.querySelector('.hero-pick-item')?.textContent?.trim());
  console.log(`Clicking first pick: "${pickName}"`);
  await firstPick.evaluate(el => el.click());
  await page.waitForTimeout(400);

  // Check that item card opened
  const cardVisible = await page.evaluate(() => {
    const panel = document.getElementById('item-detail-panel');
    return panel && !panel.classList.contains('hidden') && panel.innerHTML.length > 100;
  });
  console.log(`Golden Item Card opened: ${cardVisible ? '✓' : '✗'}`);

  // Check simulator visible
  const simExists = await page.evaluate(() => {
    return !!document.getElementById('gic-sim-runs');
  });
  console.log(`Simulator visible in card: ${simExists ? '✓' : '✗'}`);

  if (simExists) {
    // Click simulate button
    const simRuns = await page.evaluate(() => document.getElementById('gic-sim-runs').value);
    console.log(`  default sim runs: ${simRuns}`);
    await page.evaluate(() => document.querySelector('.gic-sim-btn')?.click());
    await page.waitForTimeout(200);
    const simResult = await page.evaluate(() => document.getElementById('gic-sim-result').textContent.substring(0, 100));
    console.log(`  sim result snippet: "${simResult}..."`);
    const barCount = await page.evaluate(() => document.querySelectorAll('.gic-sim-bar').length);
    console.log(`  ${barCount} sim bars rendered (expect 20)`);
  }

  console.log(`\nErrors: ${errors.length === 0 ? 'NONE' : errors}`);
  await browser.close();
})();
