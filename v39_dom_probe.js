const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(800);
  
  // What are the actual class names of chance-value cells?
  const probe1 = await page.evaluate(() => {
    const result = {};
    // Sample cell classes from boss tables
    const cells = document.querySelectorAll('td');
    const classCounts = {};
    cells.forEach(c => {
      if (c.textContent && /^1:[\d,]+$/.test(c.textContent.trim())) {
        const cl = c.className || '(no class)';
        classCounts[cl] = (classCounts[cl] || 0) + 1;
      }
    });
    result.chanceTdClasses = classCounts;
    
    // Sample of all common classes used
    const all = document.querySelectorAll('*');
    const classCount = {};
    all.forEach(el => {
      if (el.className && typeof el.className === 'string') {
        el.className.split(/\s+/).forEach(cl => {
          if (cl) classCount[cl] = (classCount[cl] || 0) + 1;
        });
      }
    });
    // Sort by count descending, take ones that look chance-related
    result.relevantClasses = Object.entries(classCount)
      .filter(([k]) => /chance|val|rate|hours|pick|boss|chip|cell/.test(k.toLowerCase()))
      .sort((a,b) => b[1]-a[1])
      .slice(0, 30);
    return result;
  });
  console.log('=== CHANCE-VALUE CELL CLASSES ===');
  console.log(JSON.stringify(probe1.chanceTdClasses, null, 2));
  console.log('=== TOP RELEVANT CLASSES ===');
  probe1.relevantClasses.forEach(([cls, n]) => console.log(`  ${cls} (${n})`));
  
  // Probe overlay structure after opening boss
  await page.evaluate(() => window.openBossDetail('mephisto'));
  await page.waitForTimeout(400);
  const probe2 = await page.evaluate(() => {
    const candidates = ['.gbc', '.gbc-overlay', '#boss-detail-panel', '#boss-detail-overlay', '.boss-detail-overlay'];
    const result = {};
    candidates.forEach(sel => {
      const el = document.querySelector(sel);
      result[sel] = el ? {
        found: true,
        display: getComputedStyle(el).display,
        opacity: getComputedStyle(el).opacity,
        classes: el.className,
        hidden: el.hidden,
      } : { found: false };
    });
    // Also dump any element that contains "Mephisto" prominently in opened state
    const headers = document.querySelectorAll('h1, h2, h3');
    result.mephistoHeader = Array.from(headers).filter(h => h.textContent.includes('Mephisto')).map(h => ({ tag: h.tagName, text: h.textContent.slice(0,80), parentClass: h.parentElement?.className }));
    return result;
  });
  console.log('=== OVERLAY STRUCTURE ===');
  console.log(JSON.stringify(probe2, null, 2));
  
  await browser.close();
})();
