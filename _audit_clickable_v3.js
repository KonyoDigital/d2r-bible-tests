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
  
  const findings = [];
  const note = (status, what) => {
    console.log(`  ${status} ${what}`);
    if (status.includes('✗')) findings.push(what);
  };
  
  // ─── TEST 1: Drop row click navigates to item ───
  console.log('=== TEST 1: Drop row click in boss detail ===');
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(400);
  // Inside the panel, find a drop row with item name link
  const dropClickResult = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    if (!panel) return { error: 'no panel' };
    // Find first item-name td
    const itemCell = panel.querySelector('td.item-name, .item-name');
    if (!itemCell) return { error: 'no item-name cell found in panel' };
    const itemText = itemCell.textContent.trim().slice(0, 40);
    const hasOnclick = !!itemCell.closest('[onclick]');
    return { found: true, text: itemText, hasOnclick };
  });
  console.log(`  drop row probe: ${JSON.stringify(dropClickResult)}`);
  note(dropClickResult.found ? '✓' : '✗', `drop rows present in boss detail`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 2: Star button on a drop row (inline) ───
  console.log('');
  console.log('=== TEST 2: Inline star button on drop rows ===');
  await p.evaluate(() => localStorage.removeItem('d2r_wishlist'));
  await p.reload();
  await p.waitForTimeout(2000);
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(400);
  const beforeStar = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  // Click the first star button in the boss detail panel
  const starClicked = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    const star = panel?.querySelector('.star-btn');
    if (!star) return { error: 'no .star-btn in panel' };
    const wasStarred = star.classList.contains('starred');
    star.click();
    return { wasStarred, name: star.dataset.star };
  });
  await p.waitForTimeout(200);
  const afterStar = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  console.log(`  star action: ${JSON.stringify(starClicked)}`);
  console.log(`  wishlist: ${beforeStar} → ${afterStar}`);
  note(afterStar > beforeStar ? '✓' : '✗', `inline star button toggles wishlist`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 3: Owned button on a drop row ───
  console.log('');
  console.log('=== TEST 3: Inline "owned" button (☐/✓) ===');
  await p.evaluate(() => localStorage.removeItem('d2r_owned'));
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(400);
  const ownedResult = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    const ownedBtn = panel?.querySelector('.owned-btn');
    if (!ownedBtn) return { error: 'no .owned-btn in panel' };
    const wasOwned = ownedBtn.classList.contains('owned');
    ownedBtn.click();
    return { wasOwned, label: ownedBtn.textContent.trim() };
  });
  await p.waitForTimeout(200);
  const afterOwned = await p.evaluate(() => {
    try {
      return eval('typeof owned !== "undefined" ? owned.size : (typeof ownedSet !== "undefined" ? ownedSet.size : (JSON.parse(localStorage.getItem("d2r_owned")||"[]")).length)');
    } catch(e) { return -1; }
  });
  console.log(`  owned action: ${JSON.stringify(ownedResult)}`);
  console.log(`  owned count: ${afterOwned}`);
  note(afterOwned > 0 ? '✓' : '✗', `inline owned button toggles state`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 4: aib-close (active item bar close) ───
  console.log('');
  console.log('=== TEST 4: Active-item-bar "clear" button ===');
  await p.evaluate(() => { window.setActiveItem('Harlequin Crest (Shako)'); });
  await p.waitForTimeout(400);
  const barShown = await p.evaluate(() => 
    document.getElementById('active-item-bar')?.classList.contains('show')
  );
  console.log(`  bar shown after setActiveItem: ${barShown}`);
  await p.locator('.aib-close').click();
  await p.waitForTimeout(500);  // wait for route-back scroll
  const barHidden = await p.evaluate(() => 
    !document.getElementById('active-item-bar')?.classList.contains('show')
  );
  note(barShown && barHidden ? '✓' : '✗', `aib-close button clears item bar`);
  
  // ─── TEST 5: All keyboard shortcuts (1-7, /, ?, r, Esc, Shift+1-6) ───
  console.log('');
  console.log('=== TEST 5: All keyboard shortcuts ===');
  const shortcuts = [
    { key: '1', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'bosses') },
    { key: '2', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'calc') },
    { key: '3', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'tz') },
    { key: '4', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'runes') },
    { key: '5', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'rotw') },
    { key: '6', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'ancients') },
    { key: '7', expect: () => p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab === 'ref') },
  ];
  for (const s of shortcuts) {
    await p.keyboard.press(s.key);
    await p.waitForTimeout(200);
    const ok = await s.expect();
    note(ok ? '✓' : '✗', `keyboard '${s.key}' switches to expected tab`);
  }
  
  // Shift+1 = MF 250
  await p.keyboard.press('Shift+1');
  await p.waitForTimeout(150);
  const mf1 = await p.evaluate(() => parseInt(document.getElementById('mf').value));
  note(mf1 === 250 ? '✓' : '✗', `Shift+1 sets MF=250 (got ${mf1})`);
  
  await p.keyboard.press('Shift+3');
  await p.waitForTimeout(150);
  const mf3 = await p.evaluate(() => parseInt(document.getElementById('mf').value));
  note(mf3 === 553 ? '✓' : '✗', `Shift+3 sets MF=553 Konyolock (got ${mf3})`);
  
  await p.keyboard.press('Shift+4');
  await p.waitForTimeout(150);
  const mf4 = await p.evaluate(() => parseInt(document.getElementById('mf').value));
  note(mf4 === 699 ? '✓' : '✗', `Shift+4 sets MF=699 swap (got ${mf4})`);
  
  // ─── TEST 6: Boss cards in main grid (.boss-card, not chip) ───
  console.log('');
  console.log('=== TEST 6: Boss cards (16 in main grid) ===');
  await p.keyboard.press('1');  // back to bosses tab
  await p.waitForTimeout(300);
  const bossCardCount = await p.evaluate(() => document.querySelectorAll('.boss-card').length);
  console.log(`  found ${bossCardCount} boss-card elements`);
  // Click first boss card's header
  const beforeOpen = await p.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  await p.locator('.boss-card .boss-header').first().click();
  await p.waitForTimeout(400);
  const afterOpen = await p.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  note(beforeOpen && !afterOpen ? '✓' : '⚠', `boss-card click opens detail (before hidden=${beforeOpen}, after hidden=${afterOpen})`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  
  // ─── TEST 7: Item search input typing filters ───
  console.log('');
  console.log('=== TEST 7: Item search input ===');
  await p.keyboard.press('2');  // calc tab
  await p.waitForTimeout(300);
  const searchInput = await p.evaluate(() => !!document.getElementById('item-search'));
  if (searchInput) {
    const beforeFilter = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
    await p.locator('#item-search').fill('shako');
    await p.waitForTimeout(300);
    const afterFilter = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
    note(afterFilter < beforeFilter ? '✓' : '✗', `item-search filters (${beforeFilter} → ${afterFilter})`);
    await p.locator('#item-search').fill('');  // clear
    await p.waitForTimeout(200);
  } else {
    note('⚠', 'item-search input not found');
  }
  
  // ─── TEST 8: kbd-help-modal close button ───
  console.log('');
  console.log('=== TEST 8: ? modal open + close ===');
  await p.keyboard.press('?');
  await p.waitForTimeout(300);
  const modalOpen = await p.evaluate(() => {
    const m = document.getElementById('kbd-help-modal');
    return m && getComputedStyle(m).display !== 'none';
  });
  console.log(`  modal open after '?': ${modalOpen}`);
  // Try close button
  const hasCloseBtn = await p.evaluate(() => !!document.querySelector('.kbd-help-close'));
  if (hasCloseBtn) {
    await p.locator('.kbd-help-close').click();
    await p.waitForTimeout(200);
    const modalClosed = await p.evaluate(() => {
      const m = document.getElementById('kbd-help-modal');
      return !m || getComputedStyle(m).display === 'none';
    });
    note(modalOpen && modalClosed ? '✓' : '✗', `? modal close button works`);
  }
  // Esc should also close
  await p.keyboard.press('?');
  await p.waitForTimeout(200);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  const closedByEsc = await p.evaluate(() => {
    const m = document.getElementById('kbd-help-modal');
    return !m || getComputedStyle(m).display === 'none';
  });
  note(closedByEsc ? '✓' : '✗', `Esc closes ? modal`);
  
  // ─── TEST 9: Wishlist export button (only appears when wishlist has items) ───
  console.log('');
  console.log('=== TEST 9: Wishlist export button ===');
  await p.evaluate(() => {
    // Add an item to wishlist via the global toggle if available
    if (typeof window.toggleStarred === 'function') window.toggleStarred('Harlequin Crest (Shako)');
    if (typeof renderWishlistHuntPath === 'function') renderWishlistHuntPath();
  });
  await p.waitForTimeout(400);
  const exportBtnPresent = await p.evaluate(() => !!document.querySelector('.wishlist-export-btn'));
  if (exportBtnPresent) {
    // Override copy to capture without actually copying
    await p.evaluate(() => {
      window._captured = null;
      navigator.clipboard = navigator.clipboard || {};
      navigator.clipboard.writeText = async (t) => { window._captured = t; return; };
    });
    await p.locator('.wishlist-export-btn').first().click();
    await p.waitForTimeout(300);
    const exported = await p.evaluate(() => window._captured);
    note(exported && exported.length > 0 ? '✓' : '⚠', `export button writes to clipboard (got ${exported ? exported.length+' chars' : 'nothing'})`);
  } else {
    note('⚠', 'wishlist export button not visible (may need rendered wishlist first)');
  }
  
  // ─── TEST 10: Esc key cascading close ───
  console.log('');
  console.log('=== TEST 10: Esc key closes overlays ===');
  // Open boss detail
  await p.locator('.boss-chip[data-boss-id="diablo"]').click();
  await p.waitForTimeout(300);
  const detailOpen = await p.evaluate(() => !document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  const detailClosed = await p.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  note(detailOpen && detailClosed ? '✓' : '✗', `Esc closes boss detail overlay`);
  
  // Open palette
  await p.evaluate(() => { if (window._v42_openPalette) window._v42_openPalette(); });
  await p.waitForTimeout(200);
  const palOpen = await p.evaluate(() => 
    !!document.getElementById('v42-palette-overlay')?.classList.contains('show')
  );
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  const palClosed = await p.evaluate(() => 
    !document.getElementById('v42-palette-overlay')?.classList.contains('show')
  );
  note(palOpen && palClosed ? '✓' : '✗', `Esc closes Cmd+K palette`);
  
  // ─── FINAL ───
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`FINDINGS: ${findings.length} issues`);
  findings.forEach(f => console.log('  · ' + f));
  console.log(`JS errors: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,150)));
  
  await b.close();
})();
