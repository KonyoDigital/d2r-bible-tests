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
  console.log('1. Tab persistence:', persisted === 'calc' ? '✅ PASS' : `❌ FAIL (got ${persisted})`);
  
  // ── Test 2: URL hash sync ──
  const hash = await page.evaluate(() => location.hash);
  console.log('2. URL hash on tab switch:', hash === '#calc' ? '✅ PASS' : `❌ FAIL (got ${hash})`);
  
  // ── Test 3: Restore tab from localStorage ──
  await page.reload();
  await page.waitForTimeout(800);
  const restored = await page.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log('3. Tab restored after reload:', restored === 'calc' ? '✅ PASS' : `❌ FAIL (got ${restored})`);
  
  // ── Test 4: Deep-link via hash (#tab/boss) — fixed selector ──
  await page.evaluate(() => localStorage.removeItem('d2r_activeTab'));
  await page.goto(url + '#bosses/mephisto');
  await page.waitForTimeout(1200);
  const tab4 = await page.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  const overlayClasses = await page.evaluate(() => {
    const o = document.getElementById('boss-detail-panel');
    return o ? o.className : '(not found)';
  });
  const overlayVisible = overlayClasses.includes('show');
  console.log('4a. Deep-link #bosses/mephisto → tab:', tab4 === 'bosses' ? '✅ PASS' : `❌ FAIL (got ${tab4})`);
  console.log('4b. Deep-link opens boss overlay:', overlayVisible ? '✅ PASS' : `❌ FAIL (classes: ${overlayClasses})`);
  
  // ── Test 5: Sync pulse fires on MF change — fixed selectors ──
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
  // Move to bosses tab to ensure .diff-col cells are visible
  await page.evaluate(() => window.switchTab && window.switchTab('bosses'));
  await page.waitForTimeout(400);
  // Trigger MF change
  await page.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = '500';
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  // Wait one frame past the rAF-rAF chain
  await page.waitForTimeout(100);
  const syncingCount = await page.evaluate(() => document.querySelectorAll('.syncing').length);
  console.log('5. Sync pulse on MF change:', syncingCount > 50 ? `✅ PASS (${syncingCount} cells flashed)` : `❌ FAIL (only ${syncingCount} cells)`);
  
  // ── Test 6: Overlay CSS transitions are applied (computed style check) ──
  await page.evaluate(() => window.openBossDetail('travincal'));
  await page.waitForTimeout(250);
  const overlayTransition = await page.evaluate(() => {
    const o = document.getElementById('boss-detail-panel');
    return o ? getComputedStyle(o).transition : '(no panel)';
  });
  console.log('6. Overlay has CSS transition:', /\.[0-9]+s|[0-9]ms/.test(overlayTransition) ? `✅ PASS (${overlayTransition.slice(0,60)})` : `❌ FAIL (${overlayTransition})`);
  
  // ── Test 7: 20 picks still 20 on each boss ──
  const picksOnTravincal = await page.evaluate(() => document.querySelectorAll('.hero-pick').length);
  console.log('7. Unified 20 picks (travincal):', picksOnTravincal === 20 ? '✅ PASS' : `❌ FAIL (got ${picksOnTravincal})`);
  
  // ── Test 8: Page errors ──
  console.log('8. Page errors:', errors.length === 0 ? '✅ PASS (0 errors)' : `❌ FAIL (${errors.length}: ${errors[0]})`);
  
  await browser.close();
})();
