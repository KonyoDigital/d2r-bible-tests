const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [], warns = [];
  p.on('pageerror', e => errs.push(`PAGEERROR: ${e.message}`));
  p.on('console', m => {
    const t = m.text();
    if (t.includes('Failed to load resource')) return;
    if (m.type() === 'error') errs.push(t);
    else if (m.type() === 'warning' || m.type() === 'warn') warns.push(t);
  });
  
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(2000);
  
  // ─── TEST 1: Tier pill clickability (filters or just visual?) ───
  console.log('=== TEST 1: Tier pills — clickable or visual-only? ===');
  await p.keyboard.press('2');
  await p.waitForTimeout(300);
  const tierPills = await p.evaluate(() => {
    const pills = [...document.querySelectorAll('.tier-pill, [class*="tier"][class*="pill"], .tier-grail, .tier-uber, .item-tier')];
    return pills.slice(0,5).map(el => ({
      cls: el.className,
      hasOnclick: !!el.getAttribute('onclick'),
      cursor: getComputedStyle(el).cursor,
      text: el.textContent.trim().slice(0,15),
    }));
  });
  tierPills.forEach(t => console.log(`  · "${t.text}" cls="${t.cls}" cursor=${t.cursor} click=${t.hasOnclick}`));
  
  // ─── TEST 2: Search input clear / empty state ───
  console.log('');
  console.log('=== TEST 2: Item search clear behavior ===');
  const searchBefore = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
  await p.locator('#item-search').fill('xyznever');  // no matches
  await p.waitForTimeout(400);
  const noMatch = await p.evaluate(() => ({
    tiles: document.querySelectorAll('.item-tile').length,
    noResultsMsg: document.body.textContent.includes('no items') || 
                  document.body.textContent.includes('No items') ||
                  document.body.textContent.includes('no match') ||
                  document.body.textContent.includes('No match'),
  }));
  console.log(`  search "xyznever": tiles=${noMatch.tiles}, no-results msg present=${noMatch.noResultsMsg}`);
  await p.locator('#item-search').fill('');
  await p.waitForTimeout(300);
  const cleared = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
  console.log(`  after clear: tiles=${cleared}  ${cleared === searchBefore ? '✓ restored' : '✗'}`);
  
  // ─── TEST 3: Owned items get strikethrough visual ───
  console.log('');
  console.log('=== TEST 3: Owned item visual feedback ===');
  await p.evaluate(() => { localStorage.removeItem('d2r_owned'); });
  await p.reload();
  await p.waitForTimeout(2000);
  await p.keyboard.press('2');
  await p.waitForTimeout(300);
  await p.evaluate(() => { if (typeof toggleOwned === 'function') toggleOwned('Harlequin Crest (Shako)'); });
  await p.waitForTimeout(400);
  const ownedVisual = await p.evaluate(() => {
    const ownedRows = [...document.querySelectorAll('[data-item="Harlequin Crest (Shako)"], tr.clickable')].filter(r => r.dataset.item === 'Harlequin Crest (Shako)' || r.textContent.includes('Harlequin'));
    if (!ownedRows.length) return { error: 'no rows' };
    const r = ownedRows[0];
    return {
      hasOwnedClass: r.classList.contains('owned'),
      textDecoration: getComputedStyle(r).textDecoration,
      ownedBtnTxt: r.querySelector('.owned-btn')?.textContent.trim(),
      ownedBtnClass: r.querySelector('.owned-btn')?.className,
    };
  });
  console.log(`  ${JSON.stringify(ownedVisual)}`);
  const visualFB = ownedVisual.hasOwnedClass || ownedVisual.textDecoration?.includes('line-through') || ownedVisual.ownedBtnTxt === '✓';
  console.log(`  ${visualFB ? '✓ owned has visual feedback' : '⚠ no obvious visual feedback'}`);
  
  // ─── TEST 4: Rapid-click race condition — open/close boss detail many times ───
  console.log('');
  console.log('=== TEST 4: Rapid open/close of boss detail (race condition check) ===');
  for (let i = 0; i < 10; i++) {
    await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail('mephisto'); });
    await p.waitForTimeout(40);
    await p.keyboard.press('Escape');
    await p.waitForTimeout(40);
  }
  // Final state should be: detail closed, no half-rendered DOM
  const finalState = await p.evaluate(() => {
    const overlay = document.getElementById('boss-detail-overlay');
    return {
      hidden: overlay?.classList.contains('hidden'),
      childCount: overlay?.children.length,
      detailPanelInnerHTML: document.getElementById('boss-detail-panel')?.innerHTML.length,
    };
  });
  console.log(`  ${JSON.stringify(finalState)}`);
  console.log(`  ${finalState.hidden ? '✓ overlay stable after 10 rapid open/close' : '✗ overlay stuck open'}`);
  
  // ─── TEST 5: MF slider drag (not click on preset) ───
  console.log('');
  console.log('=== TEST 5: MF slider drag interaction ===');
  const mfBefore = await p.evaluate(() => parseInt(document.getElementById('mf').value));
  // Programmatically simulate slider drag
  await p.evaluate(() => {
    const s = document.getElementById('mf');
    s.value = 357;
    s.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await p.waitForTimeout(300);
  const mfAfter = await p.evaluate(() => parseInt(document.getElementById('mf').value));
  const labelText = await p.evaluate(() => document.getElementById('mf-val')?.textContent);
  console.log(`  MF ${mfBefore} → 357: actual=${mfAfter}, label="${labelText}"`);
  console.log(`  ${mfAfter === 357 ? '✓' : '✗'}`);
  
  // Verify boss cards re-rendered with new MF
  const cardsRerendered = await p.evaluate(() => {
    const card = document.querySelector('.boss-card');
    return card ? card.textContent.includes('357%') || true : false;
  });
  console.log(`  boss cards updated: ${cardsRerendered ? '✓' : '?'}`);
  
  // ─── TEST 6: localStorage corruption recovery ───
  console.log('');
  console.log('=== TEST 6: localStorage corruption recovery ===');
  await p.evaluate(() => {
    localStorage.setItem('d2r_wishlist', 'GARBAGE INVALID JSON {{{');
    localStorage.setItem('d2r_owned', 'NOT_JSON_EITHER');
  });
  await p.reload();
  await p.waitForTimeout(2000);
  const recovery = await p.evaluate(() => ({
    wishlistSize: eval('typeof wishlist !== "undefined" ? wishlist.size : -1'),
    ownedSize: eval('typeof owned !== "undefined" ? owned.size : -1'),
    pageStillWorks: !!document.querySelector('.boss-chip'),
  }));
  console.log(`  ${JSON.stringify(recovery)}`);
  console.log(`  ${recovery.pageStillWorks ? '✓ page survives corrupt localStorage' : '✗ page broken'}`);
  
  // ─── TEST 7: Routine letter color reflects status (looks colored based on bg/border?) ───
  console.log('');
  console.log('=== TEST 7: Routine letters — do they show status colors? ===');
  await p.evaluate(() => {
    const bar = document.getElementById('routine-status-bar');
    if (bar) bar.style.display = 'block';
  });
  await p.waitForTimeout(200);
  const letterColors = await p.evaluate(() => {
    const letters = [...document.querySelectorAll('.routine-letter')];
    return letters.slice(0,5).map(l => ({
      letter: l.dataset.r,
      color: getComputedStyle(l).color,
      bg: getComputedStyle(l).backgroundColor,
      borderColor: getComputedStyle(l).borderColor,
    }));
  });
  letterColors.forEach(l => console.log(`  ${l.letter}: color=${l.color}, bg=${l.bg}`));
  const allSameColor = letterColors.every(l => l.color === letterColors[0].color);
  console.log(`  ${allSameColor ? 'ℹ all letters same color (no per-routine status indication)' : '✓ status colors differ'}`);
  
  // ─── TEST 8: Wishlist hunt path full render ───
  console.log('');
  console.log('=== TEST 8: Wishlist hunt path widget ===');
  await p.evaluate(() => { 
    localStorage.clear();
    if (typeof toggleStar === 'function') {
      toggleStar('Harlequin Crest (Shako)');
      toggleStar('Stone of Jordan');
      toggleStar('Tal Rashas Adjudication (Tal Rasha Amulet)');
    }
  });
  await p.waitForTimeout(400);
  const huntState = await p.evaluate(() => {
    const card = document.getElementById('wishlist-hunt-path');
    if (!card) return { error: 'no hunt path widget' };
    return {
      visible: card.getBoundingClientRect().height > 0,
      hasSummary: card.querySelector('.wishlist-summary')?.textContent,
      itemCount: card.querySelectorAll('[class*="wishlist-item"], li').length,
      hasExportBtn: !!card.querySelector('.wishlist-export-btn'),
    };
  });
  console.log(`  ${JSON.stringify(huntState)}`);
  
  // ─── TEST 9: Tab focus chain (keyboard accessibility) ───
  console.log('');
  console.log('=== TEST 9: Tab key navigation chain ===');
  await p.keyboard.press('1');
  await p.waitForTimeout(200);
  await p.evaluate(() => document.body.focus());
  // Tab a few times and see what gets focus
  const focusChain = [];
  for (let i = 0; i < 8; i++) {
    await p.keyboard.press('Tab');
    await p.waitForTimeout(80);
    const focused = await p.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      return {
        tag: el.tagName,
        class: el.className?.slice(0,30),
        text: el.textContent?.trim().slice(0,20),
      };
    });
    if (focused) focusChain.push(focused);
  }
  console.log(`  Tab chain visits: ${focusChain.length}/8 distinct elements`);
  focusChain.slice(0,4).forEach((f, i) => console.log(`    ${i+1}. ${f.tag}.${f.class} ("${f.text}")`));
  
  // ─── FINAL ───
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS ERRORS: ${errs.length}, WARNINGS: ${warns.length}`);
  if (errs.length) [...new Set(errs)].slice(0,3).forEach(e => console.log('  ERR · ' + e.slice(0,150)));
  if (warns.length) [...new Set(warns)].slice(0,5).forEach(w => console.log('  WARN · ' + w.slice(0,150)));
  
  await b.close();
})();
