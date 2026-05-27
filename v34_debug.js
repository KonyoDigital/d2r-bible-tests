const { chromium } = require('@playwright/test');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + require('path').resolve('bible_routes.html'));
  await page.waitForTimeout(800);

  const snap = async (bossId) => {
    await page.evaluate((b) => window.openBossDetail(b), bossId);
    await page.waitForTimeout(300);
    return await page.evaluate(() => {
      return Array.from(document.querySelectorAll('#hero-picks .hero-pick')).map(el => 
        el.querySelector('.hero-pick-item')?.textContent?.trim()
      );
    });
  };

  // Get all picks for all bosses
  const all = {};
  for (const b of ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit']) {
    all[b] = await snap(b);
  }
  for (const [b, items] of Object.entries(all)) {
    console.log(`${b}: ${items.length} → ${items.slice(0, 5).join(', ')}${items.length>5?', ...':''}`);
  }
  console.log('\n--- Pair overlaps ---');
  const bosses = Object.keys(all);
  const tooSimilar = [];
  for (let i = 0; i < bosses.length; i++) {
    for (let j = i+1; j < bosses.length; j++) {
      const a = new Set(all[bosses[i]]), b = new Set(all[bosses[j]]);
      const inter = [...a].filter(x => b.has(x)).length;
      const minN = Math.min(a.size, b.size) || 1;
      const pct = Math.round(100 * inter / minN);
      if (pct >= 80) tooSimilar.push({a:bosses[i], b:bosses[j], pct, inter, minN});
    }
  }
  console.log(`Pairs ≥80% overlap: ${tooSimilar.length}/55`);
  tooSimilar.slice(0, 8).forEach(p => console.log(`  ${p.a} vs ${p.b}: ${p.pct}% (${p.inter}/${p.minN})`));
  
  // Find what items overlap between countess and travincal
  console.log('\n--- countess ∩ travincal ---');
  const countSet = new Set(all.countess);
  const travShared = all.travincal.filter(x => countSet.has(x));
  console.log(`shared (${travShared.length}): ${travShared.join(' | ')}`);

  await browser.close();
})();
