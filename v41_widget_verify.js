const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve('/Users/konyo/d2r_bible_tests/bible_routes.html'));
  await page.waitForTimeout(1500);
  
  const probe = await page.evaluate(() => {
    // What ID does the widget actually use?
    const candidates = ['routine-status-bar', 'routine-bar', 'routine-toggle-pulse', 'routine-widget'];
    const found = {};
    candidates.forEach(id => {
      const el = document.getElementById(id);
      found[id] = el ? {
        present: true,
        display: getComputedStyle(el).display,
        classes: el.className,
        innerHTMLLen: el.innerHTML.length,
      } : null;
    });
    // What contains the fires-counter?
    const counter = document.getElementById('routine-fires-counter');
    if (counter) {
      let parent = counter.parentElement;
      const ancestors = [];
      while (parent && parent !== document.body) {
        ancestors.push({ tag: parent.tagName, id: parent.id || '(no id)', classes: parent.className });
        parent = parent.parentElement;
      }
      found._counter_ancestors = ancestors;
    }
    return found;
  });
  console.log(JSON.stringify(probe, null, 2));
  await browser.close();
})();
