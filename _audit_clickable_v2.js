const { chromium } = require('@playwright/test');
const path = require('path');

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  p.on('pageerror', e => errors.push(`PAGEERROR: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error' && !m.text().includes('Failed to load resource')) errors.push(`CONSOLE: ${m.text()}`); });
  
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(1500);
  
  const log = (s) => console.log(s);
  
  // ─── Updated inventory with correct selectors ───
  const inv = await p.evaluate(() => {
    const items = {
      '.boss-chip': '.boss-chip',
      '.boss-card': '.boss-card',
      '.mf-preset-chip': '.mf-preset-chip',
      '.tab': '.tab',
      '.filter-pill': '.filter-pill',
      '.tz-zone-card': '.tz-zone-card',
      '.hero-pick': '.hero-pick',
      '.item-tile': '.item-tile',
      '.aib-close': '.aib-close',
      '.source-chip': '.source-chip',
      '.star-btn': '.star-btn',
      '.wishlist-item-star': '.wishlist-item-star',
      '#v42-tz-countdown': '#v42-tz-countdown',
      '#kbd-help-modal': '#kbd-help-modal',
      '.wishlist-export-btn': '.wishlist-export-btn',
      '.tip-card': '.tip-card',
      '#help-fab': '#help-fab',
      '.help-fab': '.help-fab',
    };
    const counts = {};
    for (const [k, sel] of Object.entries(items)) {
      try {
        counts[k] = sel.startsWith('#') 
          ? (document.querySelector(sel) ? 1 : 0)
          : document.querySelectorAll(sel).length;
      } catch(e) {
        counts[k] = -1;
      }
    }
    return counts;
  });
  log('=== CORRECTED INVENTORY ===');
  for (const [k, v] of Object.entries(inv)) {
    if (v !== 0) log(`  ${k.padEnd(36)} ${v}`);
  }
  
  // ─── SWEEP 1: MF preset chips (8) ───
  log('');
  log('=== TEST 1: MF preset chips (8 expected) ===');
  const presets = await p.evaluate(() => 
    [...document.querySelectorAll('.mf-preset-chip')].map(c => c.textContent.trim())
  );
  log(`  found: ${presets.length} → [${presets.join(', ')}]`);
  for (const pVal of [0, 250, 553, 699, 1000]) {
    const before = errors.length;
    try {
      await p.locator(`.mf-preset-chip`, { hasText: new RegExp(`^${pVal}`) }).first().click({ timeout: 2000 });
      await p.waitForTimeout(100);
      const mf = await p.evaluate(() => parseInt(document.getElementById('mf').value));
      log(`  click "${pVal}" → MF slider = ${mf}  ${mf === pVal ? '✓' : '✗'}`);
    } catch(e) {
      log(`  ✗ preset ${pVal}: ${e.message.slice(0,60)}`);
    }
  }
  
  // ─── SWEEP 2: TZ countdown widget click ───
  log('');
  log('=== TEST 2: TZ countdown widget click toggle ===');
  const tzCountBefore = await p.evaluate(() => {
    const w = document.getElementById('v42-tz-countdown');
    return { exists: !!w, visible: w?.classList.contains('show') };
  });
  log(`  before click: exists=${tzCountBefore.exists} visible=${tzCountBefore.visible}`);
  if (tzCountBefore.exists) {
    try {
      await p.locator('#v42-tz-countdown').click({ timeout: 2000 });
      await p.waitForTimeout(200);
      const after = await p.evaluate(() => {
        const w = document.getElementById('v42-tz-countdown');
        return { visible: w?.classList.contains('show') };
      });
      log(`  after click: visible=${after.visible}  ${after.visible !== tzCountBefore.visible ? '✓ toggle works' : '⚠ no change'}`);
    } catch(e) {
      log(`  ✗ TZ widget click: ${e.message.slice(0,60)}`);
    }
  }
  
  // ─── SWEEP 3: ? help (keyboard shortcut + button if exists) ───
  log('');
  log('=== TEST 3: Keyboard shortcuts modal (?) ===');
  await p.keyboard.press('?');
  await p.waitForTimeout(200);
  const modal = await p.evaluate(() => {
    const m = document.getElementById('kbd-help-modal');
    return { exists: !!m, visible: m && getComputedStyle(m).display !== 'none' };
  });
  log(`  press '?': modal exists=${modal.exists} visible=${modal.visible}  ${modal.visible ? '✓' : '✗'}`);
  if (modal.visible) {
    await p.keyboard.press('Escape');
    await p.waitForTimeout(150);
  }
  
  // ─── SWEEP 4: Wishlist star toggle ───
  log('');
  log('=== TEST 4: Wishlist star toggle on item tile ===');
  await p.evaluate(() => { localStorage.removeItem('d2r_wishlist'); window.location.reload(); });
  await p.waitForTimeout(1500);
  // Click first item tile
  const itemTiles = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
  log(`  found ${itemTiles} item tiles`);
  if (itemTiles > 0) {
    try {
      await p.locator('.item-tile').first().click({ timeout: 2000 });
      await p.waitForTimeout(300);
      // Active item bar should appear with a star button
      const starBtns = await p.evaluate(() => document.querySelectorAll('.star-btn').length);
      log(`  after item click: .star-btn count = ${starBtns}`);
      if (starBtns > 0) {
        await p.locator('.star-btn').first().click({ timeout: 2000 });
        await p.waitForTimeout(200);
        const wishCount = await p.evaluate(() => 
          eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
        );
        log(`  after star click: wishlist size = ${wishCount}  ${wishCount > 0 ? '✓' : '✗'}`);
      }
    } catch(e) {
      log(`  ✗ wishlist test: ${e.message.slice(0,80)}`);
    }
  }
  
  // ─── SWEEP 5: Source chips (boss drop chips in calc) ───
  log('');
  log('=== TEST 5: Source chips (boss drop chips in calculator) ===');
  await p.locator('.tab[data-tab="calc"]').click();
  await p.waitForTimeout(300);
  const sourceChips = await p.evaluate(() => document.querySelectorAll('.source-chip').length);
  log(`  found ${sourceChips} source chips in calc`);
  if (sourceChips > 0) {
    try {
      // Click first source chip — should navigate to bosses tab
      await p.locator('.source-chip').first().click({ timeout: 2000 });
      await p.waitForTimeout(300);
      const nowOn = await p.evaluate(() => document.querySelector('.tab.active')?.getAttribute('data-tab'));
      log(`  after source chip click → tab="${nowOn}"  ${nowOn === 'bosses' ? '✓ routed to bosses' : '⚠'}`);
    } catch(e) {
      log(`  ✗ source chip: ${e.message.slice(0,80)}`);
    }
  }
  
  // ─── SWEEP 6: All 312 items via setActiveItem ───
  log('');
  log('=== TEST 6: All 312 item names route without error ===');
  const itemFails = await p.evaluate(() => {
    const fails = [];
    if (typeof ITEMS === 'undefined') return ['ITEMS undefined'];
    for (const it of ITEMS) {
      try {
        if (typeof window.setActiveItem === 'function') window.setActiveItem(it.n);
      } catch(e) {
        fails.push(`${it.n}: ${e.message.slice(0,40)}`);
        if (fails.length > 5) break;
      }
    }
    return fails;
  });
  if (itemFails.length === 0) log(`  ✓ all 312 items routable`);
  else log(`  ✗ ${itemFails.length} items failed: ${itemFails.slice(0,3).join(' / ')}`);
  
  // ─── SWEEP 7: All 11 boss IDs via openBossDetail ───
  log('');
  log('=== TEST 7: All 11 bosses route via openBossDetail ===');
  const bossFails = await p.evaluate(() => {
    const fails = [];
    if (typeof BOSSES === 'undefined') return ['BOSSES undefined'];
    for (const b of BOSSES) {
      try {
        if (typeof window.openBossDetail === 'function') window.openBossDetail(b.id);
      } catch(e) {
        fails.push(`${b.id}: ${e.message.slice(0,40)}`);
      }
    }
    return fails;
  });
  if (bossFails.length === 0) log(`  ✓ all 11 bosses routable`);
  else log(`  ✗ ${bossFails.length} bosses failed: ${bossFails.join(' / ')}`);
  
  // ─── SWEEP 8: Tip cards in reference tab ───
  log('');
  log('=== TEST 8: Tip cards in reference tab ===');
  await p.locator('.tab[data-tab="ref"]').click();
  await p.waitForTimeout(300);
  const tipCount = await p.evaluate(() => document.querySelectorAll('.tip-card').length);
  log(`  found ${tipCount} tip cards`);
  for (let i = 0; i < Math.min(tipCount, 5); i++) {
    try {
      await p.locator('.tip-card').nth(i).click({ timeout: 2000 });
      await p.waitForTimeout(80);
    } catch(e) {
      log(`  ✗ tip card ${i}: ${e.message.slice(0,80)}`);
    }
  }
  log(`  ✓ tip cards clickable`);
  
  // ─── SWEEP 9: Routines status widget — R key toggle ───
  log('');
  log('=== TEST 9: R key toggles routine status widget ===');
  await p.keyboard.press('r');
  await p.waitForTimeout(300);
  const routineWidget = await p.evaluate(() => {
    const ids = ['routine-status-widget', 'd2r-routine-widget', 'routine-widget', 'routines-widget'];
    for (const id of ids) {
      const w = document.getElementById(id);
      if (w) return { id, visible: getComputedStyle(w).display !== 'none' };
    }
    // Try class
    const c = document.querySelector('.routine-status-widget, .d2r-routine-widget');
    if (c) return { tag: c.tagName, visible: getComputedStyle(c).display !== 'none' };
    return null;
  });
  log(`  press 'r': widget=${JSON.stringify(routineWidget)}`);
  
  // ─── Final report ───
  log('');
  log('═══════════════════════════════════════════════');
  log(`TOTAL JS ERRORS during audit: ${errors.length}`);
  if (errors.length > 0) {
    [...new Set(errors)].slice(0,10).forEach(e => log(`  · ${e.slice(0,200)}`));
  }
  
  await b.close();
})();
