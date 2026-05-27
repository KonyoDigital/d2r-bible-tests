const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(900);
  
  // Test 1: Tips & Wisdom rendered in ref tab
  await page.evaluate(() => window.switchTab && window.switchTab('ref'));
  await page.waitForTimeout(400);
  const tipsCount = await page.evaluate(() => document.querySelectorAll('.tip-card').length);
  console.log('1. Tips & Wisdom cards in ref tab:', tipsCount >= 12 ? `✅ PASS (${tipsCount} cards)` : `❌ FAIL (only ${tipsCount})`);
  
  // Test 2: Methodology accordion present
  const methHas = await page.evaluate(() => !!document.querySelector('.methodology-block'));
  console.log('2. Methodology accordion present:', methHas ? '✅ PASS' : '❌ FAIL');
  
  // Test 3: Methodology accordion opens
  await page.locator('.methodology-block summary').click();
  await page.waitForTimeout(200);
  const methOpen = await page.evaluate(() => document.querySelector('.methodology-block').open);
  console.log('3. Methodology opens on click:', methOpen ? '✅ PASS' : '❌ FAIL');
  
  // Test 4: Switch to bosses + open Mephisto → Field Manual injected
  await page.evaluate(() => window.switchTab && window.switchTab('bosses'));
  await page.waitForTimeout(300);
  await page.evaluate(() => window.openBossDetail && window.openBossDetail('mephisto'));
  await page.waitForTimeout(400);
  const fmInjected = await page.evaluate(() => {
    const p = document.getElementById('boss-detail-panel');
    return p && !!p.querySelector('.field-manual');
  });
  console.log('4. Field Manual injected for Mephisto:', fmInjected ? '✅ PASS' : '❌ FAIL');
  
  // Test 5: Field Manual has all 5 sections (Run, Targets, Pitfalls, Pro Tip, Quest)
  const fmSections = await page.evaluate(() => {
    const fm = document.querySelector('.field-manual');
    if (!fm) return 0;
    return fm.querySelectorAll('.fm-section').length;
  });
  console.log('5. Field Manual sections (expect 5):', fmSections === 5 ? '✅ PASS' : `❌ FAIL (${fmSections})`);
  
  // Test 6: Close + reopen → no duplicate injection
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  await page.evaluate(() => window.openBossDetail && window.openBossDetail('mephisto'));
  await page.waitForTimeout(300);
  const fmCount = await page.evaluate(() => {
    const p = document.getElementById('boss-detail-panel');
    return p ? p.querySelectorAll('.field-manual').length : 0;
  });
  console.log('6. No duplicate FM on reopen:', fmCount === 1 ? '✅ PASS' : `❌ FAIL (${fmCount} found)`);
  
  // Test 7: All 11 bosses get unique field manuals
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  const bossIds = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
  let bossesWithFM = 0;
  const fmContents = new Set();
  for (const id of bossIds) {
    await page.evaluate(b => window.openBossDetail(b), id);
    await page.waitForTimeout(180);
    const fmText = await page.evaluate(() => {
      const fm = document.querySelector('.field-manual');
      return fm ? fm.textContent.trim().slice(0, 100) : null;
    });
    if (fmText) { bossesWithFM++; fmContents.add(fmText); }
    await page.keyboard.press('Escape');
    await page.waitForTimeout(80);
  }
  console.log(`7. All 11 bosses have FM:`, bossesWithFM === 11 ? '✅ PASS' : `❌ FAIL (${bossesWithFM}/11)`);
  console.log(`8. FMs are unique per boss:`, fmContents.size === 11 ? `✅ PASS (${fmContents.size}/11 unique)` : `❌ FAIL (${fmContents.size}/11 unique)`);
  
  // Test 9: v39 features still work (sync pulse on MF change)
  await page.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = '550';
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(100);
  const syncCount = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log('9. v39 sync pulse still fires:', syncCount > 30 ? `✅ PASS (${syncCount} cells)` : `❌ FAIL`);
  
  // Test 10: Page errors
  console.log('10. Page errors:', errors.length === 0 ? '✅ PASS (0)' : `❌ FAIL (${errors.length}): ${errors[0]}`);
  
  await browser.close();
})();
