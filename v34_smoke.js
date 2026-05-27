const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  page.on('pageerror', e => console.log('PAGEERROR:', e.message));
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(800);

  const snap = async (bossId) => {
    await page.evaluate((b) => window.openBossDetail(b), bossId);
    await page.waitForTimeout(350);
    return await page.evaluate(() => {
      return Array.from(document.querySelectorAll('#hero-picks .hero-pick')).map(el => ({
        item: el.querySelector('.hero-pick-item')?.textContent?.trim(),
        source: el.querySelector('.hero-pick-boss')?.textContent?.trim(),
      }));
    });
  };

  console.log('=== Travincal vs Countess (was 100% identical) ===');
  const trav = await snap('travincal');
  const count = await snap('countess');
  const travSet = new Set(trav.map(p=>p.item));
  const countSet = new Set(count.map(p=>p.item));
  const inter = [...travSet].filter(x => countSet.has(x));
  console.log(`travincal: ${trav.length} picks, e.g. "${trav[0]?.item}" @ "${trav[0]?.source}"`);
  console.log(`countess: ${count.length} picks, e.g. "${count[0]?.item}" @ "${count[0]?.source}"`);
  console.log(`overlap: ${inter.length}/${Math.min(travSet.size, countSet.size)} (${Math.round(100*inter.length/Math.min(travSet.size,countSet.size))}%)`);

  console.log('\n=== Diablo vs Baal vs Nihl vs Pit (was 100% identical 4-way) ===');
  for (const b of ['diablo','baal','nihl','pit']) {
    const s = await snap(b);
    console.log(`${b}: ${s.length} picks, e.g. "${s[0]?.item}" @ "${s[0]?.source}"`);
  }

  console.log('\n=== Source label check (CC test 4) ===');
  const travLabels = trav.map(p => p.source);
  const onBrand = travLabels.filter(s => /travincal|council/i.test(s)).length;
  console.log(`travincal picks with brand label: ${onBrand}/${travLabels.length}`);
  console.log(`  sample labels: ${travLabels.slice(0,3).join(' | ')}`);

  await browser.close();
})();
