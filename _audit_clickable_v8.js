const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  p.on('pageerror', e => errs.push(`PAGEERROR: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error' && !m.text().includes('Failed to load resource')) errs.push(`CONSOLE: ${m.text()}`); });
  
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(2000);
  
  // ─── TEST 1: Drop row click in boss detail navigates somewhere useful ───
  console.log('=== TEST 1: Click a drop row in boss detail ===');
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(500);
  
  const dropProbe = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    if (!panel) return null;
    // Find clickable item row
    const clickableRow = panel.querySelector('tr.clickable, tr[data-item], tr[onclick]');
    if (!clickableRow) return { error: 'no clickable rows in panel' };
    return {
      item: clickableRow.dataset.item || clickableRow.querySelector('td')?.textContent?.trim().slice(0, 40),
      onclick: clickableRow.getAttribute('onclick')?.slice(0, 100),
      hasClickable: clickableRow.classList.contains('clickable'),
    };
  });
  console.log(`  drop row probe: ${JSON.stringify(dropProbe)}`);
  
  if (dropProbe?.item) {
    const tabBefore = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
    const itemBefore = await p.evaluate(() => eval('typeof activeItem !== "undefined" ? activeItem : null'));
    
    // Click via JS (avoid viewport issues)
    await p.evaluate(() => {
      const panel = document.getElementById('boss-detail-panel');
      const row = panel.querySelector('tr.clickable, tr[data-item], tr[onclick]');
      if (row) row.click();
    });
    await p.waitForTimeout(500);
    
    const tabAfter = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
    const itemAfter = await p.evaluate(() => eval('typeof activeItem !== "undefined" ? activeItem : null'));
    console.log(`  before: tab=${tabBefore} item=${itemBefore}`);
    console.log(`  after:  tab=${tabAfter} item=${itemAfter}`);
    console.log(`  ${itemAfter && itemAfter !== itemBefore ? '✓ drop row click sets active item' : '⚠ no item change'}`);
  }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  
  // ─── TEST 2: Tip cards have onclick / interactivity ───
  console.log('');
  console.log('=== TEST 2: Tip cards interactive? ===');
  await p.keyboard.press('7');  // ref tab
  await p.waitForTimeout(300);
  const tipProbe = await p.evaluate(() => {
    const cards = [...document.querySelectorAll('.tip-card')];
    return cards.slice(0, 3).map(c => ({
      hasOnclick: !!c.getAttribute('onclick'),
      hasCursor: getComputedStyle(c).cursor,
      hasClickListener: c.classList.contains('clickable'),
      text: c.textContent.slice(0, 40),
    }));
  });
  tipProbe.forEach(t => console.log(`  · onclick=${t.hasOnclick} cursor=${t.hasCursor} text="${t.text}..."`));
  const tipsInteractive = tipProbe.some(t => t.hasOnclick || t.hasCursor === 'pointer');
  console.log(`  ${tipsInteractive ? '✓ tip cards are interactive' : 'ℹ tip cards are read-only (which is fine)'}`);
  
  // ─── TEST 3: Star buttons visually reflect state (★ vs ☆) ───
  console.log('');
  console.log('=== TEST 3: Star button visual state matches data ===');
  await p.evaluate(() => { localStorage.removeItem('d2r_wishlist'); });
  await p.reload();
  await p.waitForTimeout(2000);
  await p.keyboard.press('2');  // calc tab
  await p.waitForTimeout(300);
  
  // Star a specific item
  await p.evaluate(() => { if (typeof toggleStar === 'function') toggleStar('Harlequin Crest (Shako)'); });
  await p.waitForTimeout(300);
  
  const starCheck = await p.evaluate(() => {
    const starred = [...document.querySelectorAll('.star-btn[data-star="Harlequin Crest (Shako)"]')];
    if (starred.length === 0) return { error: 'no star buttons for Shako found' };
    return starred.slice(0, 3).map(s => ({
      hasStarredClass: s.classList.contains('starred'),
      textChar: s.textContent.trim(),
    }));
  });
  console.log(`  Shako stars: ${JSON.stringify(starCheck)}`);
  const allMatch = starCheck.every?.(s => s.hasStarredClass && s.textChar === '★');
  console.log(`  ${allMatch ? '✓ all Shako stars show ★' : '⚠'}`);
  
  // ─── TEST 4: Real-world scroll-then-click on an offscreen item ───
  console.log('');
  console.log('=== TEST 4: Scroll-and-click an offscreen item tile ===');
  // Item count: 312. Pick one near the end.
  const targetItem = await p.evaluate(() => {
    const tiles = document.querySelectorAll('.item-tile');
    if (tiles.length < 200) return null;
    const target = tiles[200];
    return {
      name: target.textContent.trim().slice(0, 40),
      rect: target.getBoundingClientRect(),
    };
  });
  console.log(`  target tile @ index 200: "${targetItem?.name}" at y=${Math.round(targetItem?.rect?.top || 0)}`);
  
  // Scroll into view + click
  await p.locator('.item-tile').nth(200).scrollIntoViewIfNeeded();
  await p.waitForTimeout(300);
  await p.locator('.item-tile').nth(200).click();
  await p.waitForTimeout(400);
  const clickResult = await p.evaluate(() => ({
    activeItem: eval('typeof activeItem !== "undefined" ? activeItem : null'),
    barShown: document.getElementById('active-item-bar')?.classList.contains('show'),
  }));
  console.log(`  after click: ${JSON.stringify(clickResult)}`);
  console.log(`  ${clickResult.activeItem ? '✓' : '✗'} scroll-and-click flow works`);
  
  // ─── TEST 5: Click count by category (sanity check) ───
  console.log('');
  console.log('=== TEST 5: Click counts inventory ===');
  await p.evaluate(() => window.scrollTo(0,0));
  await p.keyboard.press('1');  // bosses
  await p.waitForTimeout(300);
  const allClickables = await p.evaluate(() => {
    return {
      // Elements with onclick attribute
      onclickAttr: document.querySelectorAll('[onclick]').length,
      // Elements with cursor pointer (likely clickable)
      cursorPointer: [...document.querySelectorAll('*')].filter(el => getComputedStyle(el).cursor === 'pointer').length,
      // Buttons
      buttons: document.querySelectorAll('button').length,
      // Links
      links: document.querySelectorAll('a').length,
      // Items
      itemTiles: document.querySelectorAll('.item-tile').length,
      bossChips: document.querySelectorAll('.boss-chip').length,
      bossCards: document.querySelectorAll('.boss-card').length,
      starBtns: document.querySelectorAll('.star-btn').length,
      ownedBtns: document.querySelectorAll('.owned-btn').length,
      sourceChips: document.querySelectorAll('.source-chip').length,
      filterPills: document.querySelectorAll('.filter-pill').length,
      tabs: document.querySelectorAll('.tab').length,
      mfPresets: document.querySelectorAll('.mf-preset-chip').length,
      tipCards: document.querySelectorAll('.tip-card').length,
      tzZones: document.querySelectorAll('.tz-zone-card').length,
      heroPicks: document.querySelectorAll('.hero-pick').length,
      routineLetters: document.querySelectorAll('.routine-letter').length,
    };
  });
  console.log(`  ${JSON.stringify(allClickables, null, 2)}`);
  
  // ─── FINAL ───
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS errors: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,180)));
  
  await b.close();
})();
