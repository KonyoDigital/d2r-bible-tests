const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(900);
  
  // Open Mephisto
  await page.evaluate(() => window.openBossDetail('mephisto'));
  await page.waitForTimeout(300);
  let state = await page.evaluate(() => {
    const p = document.getElementById('boss-detail-panel');
    const fm = p?.querySelector('.field-manual');
    return {
      panelExists: !!p,
      panelClasses: p?.className,
      panelDisplayed: p ? getComputedStyle(p).display : null,
      fmExists: !!fm,
      fmTextLen: fm?.textContent.length || 0,
      fmFirst40: fm?.textContent.slice(0,40),
    };
  });
  console.log('Mephisto FIRST open:', JSON.stringify(state, null, 2));
  
  // Press escape
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  state = await page.evaluate(() => {
    const p = document.getElementById('boss-detail-panel');
    const fm = p?.querySelector('.field-manual');
    return {
      panelClasses: p?.className,
      panelDisplayed: p ? getComputedStyle(p).display : null,
      fmExists: !!fm,
      fmTextLen: fm?.textContent.length || 0,
    };
  });
  console.log('AFTER escape:', JSON.stringify(state, null, 2));
  
  // Open Travincal
  await page.evaluate(() => window.openBossDetail('travincal'));
  await page.waitForTimeout(300);
  state = await page.evaluate(() => {
    const p = document.getElementById('boss-detail-panel');
    const fm = p?.querySelector('.field-manual');
    return {
      panelClasses: p?.className,
      panelDisplayed: p ? getComputedStyle(p).display : null,
      fmExists: !!fm,
      fmTextLen: fm?.textContent.length || 0,
      fmFirst40: fm?.textContent.slice(0,40),
    };
  });
  console.log('Travincal SECOND open:', JSON.stringify(state, null, 2));
  
  await browser.close();
})();
