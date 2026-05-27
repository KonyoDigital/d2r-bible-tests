const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  
  const url = 'file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html');
  await page.goto(url);
  await page.waitForTimeout(900);
  
  // ── Test 1: Tab persistence ──
  await page.locator('.tab[data-tab="calc"]').click();
  await page.waitForTimeout(200);
  const persisted = await page.evaluate(() => localStorage.getItem('d2r_activeTab'));
  console.log('✓ Tab persistence:', persisted === 'calc' ? 'PASS' : `FAIL (got ${persisted})`);
  
  // ── Test 2: URL hash sync ──
  const hash = await page.evaluate(() => location.hash);
  console.log('✓ URL hash on tab switch:', hash === '#calc' ? 'PASS' : `FAIL (got ${hash})`);
  
  // ── Test 3: Restore tab from localStorage ──
  await page.reload();
  await page.waitForTimeout(800);
  const restored = await page.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log('✓ Tab restored after reload:', restored === 'calc' ? 'PASS' : `FAIL (got ${restored})`);
  
  // ── Test 4: Deep-link via hash (#tab/boss) ──
  await page.goto(url + '#bosses/mephisto');
  await page.waitForTimeout(900);
  const isOnBosses = await page.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  const overlayOpen = await page.evaluate(() => {
    const o = document.querySelector('.gbc-overlay, .gbc');
    return o && getComputedStyle(o).display !== 'none';
  });
  console.log('✓ Deep-link #bosses/mephisto → tab:', isOnBosses === 'bosses' ? 'PASS' : `FAIL`);
  console.log('✓ Deep-link opens boss overlay:', overlayOpen ? 'PASS' : 'FAIL');
  
  // ── Test 5: Sync pulse class fires on MF change ──
  await page.keyboard.press('Escape');
  await page.waitForTimeout(200);
  await page.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = '500';
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await page.waitForTimeout(50);
  const syncingCount = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log('✓ Sync pulse on MF change: ' + (syncingCount > 0 ? `PASS (${syncingCount} cells flashed)` : 'FAIL (no .syncing class found)'));
  
  // ── Test 6: CSS variables resolve correctly ──
  const cssCheck = await page.evaluate(() => {
    const s = getComputedStyle(document.documentElement);
    return {
      gold: s.getPropertyValue('--gold-bright').trim(),
      bg: s.getPropertyValue('--bg').trim(),
    };
  });
  console.log('✓ CSS vars:', cssCheck.gold && cssCheck.bg ? `PASS (--gold-bright=${cssCheck.gold})` : 'FAIL');
  
  // ── Test 7: prefers-reduced-motion guard exists ──
  const motionCss = await page.evaluate(() => {
    let found = false;
    for (const sheet of document.styleSheets) {
      try {
        for (const rule of sheet.cssRules) {
          if (rule.type === CSSRule.MEDIA_RULE && rule.conditionText && rule.conditionText.includes('reduced-motion')) {
            found = true;
            break;
          }
        }
      } catch(e) {}
      if (found) break;
    }
    return found;
  });
  console.log('✓ @media prefers-reduced-motion guard:', motionCss ? 'PASS' : 'FAIL');
  
  // ── Test 8: Custom scrollbar styling applied ──
  const scrollbarCss = await page.evaluate(() => {
    let found = false;
    for (const sheet of document.styleSheets) {
      try {
        for (const rule of sheet.cssRules) {
          if (rule.cssText && rule.cssText.includes('::-webkit-scrollbar')) {
            found = true;
            break;
          }
        }
      } catch(e) {}
      if (found) break;
    }
    return found;
  });
  console.log('✓ Custom scrollbar styling:', scrollbarCss ? 'PASS' : 'FAIL');
  
  // ── Test 9: Routine widget still works ──
  await page.keyboard.press('R');
  await page.waitForTimeout(200);
  const widgetVis = await page.evaluate(() => {
    const w = document.getElementById('routine-status-bar') || document.getElementById('routine-toggle-pulse');
    return w && getComputedStyle(w).display !== 'none';
  });
  console.log('✓ Routine widget toggle (R key):', widgetVis ? 'PASS' : 'FAIL');
  
  // ── Test 10: 20 picks per boss preserved ──
  await page.evaluate(() => location.hash = '');
  await page.evaluate(() => window.openBossDetail('baal'));
  await page.waitForTimeout(300);
  const picksOnBaal = await page.evaluate(() => document.querySelectorAll('.hero-pick').length);
  console.log('✓ Unified 20 picks (baal):', picksOnBaal === 20 ? 'PASS' : `FAIL (got ${picksOnBaal})`);
  
  console.log('');
  console.log('Page errors:', errors.length);
  if (errors.length) console.log(errors.slice(0, 3));
  
  await browser.close();
})();
