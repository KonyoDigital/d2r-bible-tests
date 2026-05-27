const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(800);
  
  const bossIds = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  const fmFullTexts = [];
  for (const id of bossIds) {
    await page.evaluate(b => window.openBossDetail(b), id);
    await page.waitForTimeout(150);
    const text = await page.evaluate(() => {
      const fm = document.querySelector('.field-manual');
      return fm ? fm.textContent.trim() : null;
    });
    fmFullTexts.push({ id, length: text?.length || 0, hash: text ? text.slice(0,40) + '...' + text.slice(-40) : 'NONE' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(70);
  }
  
  // Full uniqueness check (use full text, not slice)
  const fullSet = new Set(fmFullTexts.map(f => f.hash));
  console.log(`Full FM uniqueness: ${fullSet.size}/11 unique by full content`);
  console.log('');
  console.log('Per boss FM length + hash (start...end):');
  fmFullTexts.forEach(f => console.log(`  ${f.id.padEnd(10)} · ${f.length}ch · ${f.hash}`));
  
  await browser.close();
})();
