const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(800);

  // Snapshot 1: global mode
  const globalPicks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#hero-picks .hero-pick')).map(el => ({
      item: el.querySelector('.hero-pick-item')?.textContent?.trim(),
      boss: el.querySelector('.hero-pick-boss')?.textContent?.trim(),
    }));
  });
  console.log(`GLOBAL mode: ${globalPicks.length} picks`);
  globalPicks.slice(0,8).forEach((p,i) => console.log(`  ${i+1}. ${p.item} @ ${p.boss}`));

  // Click Travincal boss chip
  await page.evaluate(() => window.openBossDetail('travincal'));
  await page.waitForTimeout(400);

  const travincalPicks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#hero-picks .hero-pick')).map(el => ({
      item: el.querySelector('.hero-pick-item')?.textContent?.trim(),
      diff: el.querySelector('.hero-pick-boss')?.textContent?.trim(),
    }));
  });
  const subTitle = await page.evaluate(() => document.getElementById('hero-sub')?.textContent?.substring(0, 100));
  console.log(`\nTRAVINCAL mode: ${travincalPicks.length} picks`);
  console.log(`  sub: ${subTitle}`);
  travincalPicks.slice(0,10).forEach((p,i) => console.log(`  ${i+1}. ${p.item} (${p.diff})`));

  // Click another boss
  await page.evaluate(() => window.openBossDetail('mephisto'));
  await page.waitForTimeout(400);
  const mephPicks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('#hero-picks .hero-pick')).map(el => ({
      item: el.querySelector('.hero-pick-item')?.textContent?.trim(),
      diff: el.querySelector('.hero-pick-boss')?.textContent?.trim(),
    }));
  });
  console.log(`\nMEPHISTO mode: ${mephPicks.length} picks`);
  mephPicks.slice(0,5).forEach((p,i) => console.log(`  ${i+1}. ${p.item} (${p.diff})`));

  // Clear → back to global
  await page.evaluate(() => window.clearActiveBoss());
  await page.waitForTimeout(200);
  const backToGlobal = await page.evaluate(() => document.querySelectorAll('#hero-picks .hero-pick').length);
  console.log(`\nAfter clear: ${backToGlobal} picks (back to global)`);

  await browser.close();
})();
