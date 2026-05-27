const { chromium } = require('@playwright/test');
const path = require('path');

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } });
  
  const jsErrors = [];
  p.on('pageerror', e => jsErrors.push(`PAGEERROR: ${e.message}`));
  p.on('console', m => {
    if (m.type() === 'error') jsErrors.push(`CONSOLE.error: ${m.text()}`);
  });
  
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(1500);
  
  // ─── PHASE 1: Inventory every clickable element ───
  const inventory = await p.evaluate(() => {
    const selectors = [
      '.boss-chip',
      '.boss-card',
      '.boss-card .boss-header',
      '.tab',
      '.mf-preset',
      '.filter-pill',
      '.tz-zone-card',
      '.runeword-card',
      '.hero-pick',
      '.item-tile',
      '.aib-close',
      '[data-tab]',
      'button:not(.kbd-tip)',
      '[onclick]',
      'tr[data-item]',
      '.wish-star',
      '.tip-card',
      '.tip-card.clickable',
    ];
    const counts = {};
    for (const sel of selectors) {
      try {
        counts[sel] = document.querySelectorAll(sel).length;
      } catch(e) {
        counts[sel] = `ERR: ${e.message}`;
      }
    }
    return counts;
  });
  
  console.log('=== CLICKABLE INVENTORY ===');
  for (const [sel, count] of Object.entries(inventory)) {
    if (count > 0) console.log(`  ${sel.padEnd(40)} ${count}`);
  }
  
  console.log('');
  console.log('=== SWEEP 1: Boss chips (all 11) ===');
  const bossIds = await p.evaluate(() => 
    [...document.querySelectorAll('.boss-chip')].map(c => c.dataset.bossId)
  );
  for (const id of bossIds) {
    try {
      await p.locator(`.boss-chip[data-boss-id="${id}"]`).click({ timeout: 2000 });
      await p.waitForTimeout(100);
      await p.keyboard.press('Escape');
      await p.waitForTimeout(80);
    } catch(e) {
      console.log(`  ✗ boss chip ${id}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ ${bossIds.length} boss chips clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 2: All 7 tabs ===');
  const tabs = ['bosses', 'calc', 'tz', 'runes', 'rotw', 'ancients', 'ref'];
  for (const t of tabs) {
    try {
      await p.locator(`.tab[data-tab="${t}"]`).click({ timeout: 2000 });
      await p.waitForTimeout(120);
    } catch(e) {
      console.log(`  ✗ tab ${t}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ 7 tabs clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 3: MF presets (all 8) ===');
  const presets = await p.evaluate(() => 
    [...document.querySelectorAll('.mf-preset')].map(p => p.textContent.trim())
  );
  for (const sel of presets) {
    try {
      await p.locator(`.mf-preset`, { hasText: sel }).first().click({ timeout: 2000 });
      await p.waitForTimeout(80);
    } catch(e) {
      console.log(`  ✗ MF preset ${sel}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ ${presets.length} MF presets clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 4: TZ zone cards (jump to bosses tab first) ===');
  await p.locator('.tab[data-tab="tz"]').click();
  await p.waitForTimeout(300);
  const tzCount = await p.evaluate(() => document.querySelectorAll('.tz-zone-card').length);
  console.log(`  found ${tzCount} TZ zone cards`);
  // Click first 5 to avoid timeout
  const sample = Math.min(5, tzCount);
  for (let i = 0; i < sample; i++) {
    try {
      const card = await p.locator('.tz-zone-card').nth(i);
      await card.click({ timeout: 2000 });
      await p.waitForTimeout(300);
      // Should have switched to bosses tab + opened a boss
      await p.locator('.tab[data-tab="tz"]').click();
      await p.waitForTimeout(150);
    } catch(e) {
      console.log(`  ✗ TZ card ${i}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ ${sample}/${tzCount} TZ cards clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 5: Runeword cards ===');
  await p.locator('.tab[data-tab="runes"]').click();
  await p.waitForTimeout(300);
  const rwCount = await p.evaluate(() => document.querySelectorAll('.runeword-card').length);
  console.log(`  found ${rwCount} runeword cards`);
  
  console.log('');
  console.log('=== SWEEP 6: Hero picks ===');
  await p.locator('.tab[data-tab="bosses"]').click();
  await p.waitForTimeout(300);
  const heroCount = await p.evaluate(() => document.querySelectorAll('.hero-pick').length);
  console.log(`  found ${heroCount} hero picks`);
  for (let i = 0; i < Math.min(3, heroCount); i++) {
    try {
      await p.locator('.hero-pick').nth(i).click({ timeout: 2000 });
      await p.waitForTimeout(250);
      await p.keyboard.press('Escape');
      await p.waitForTimeout(100);
    } catch(e) {
      console.log(`  ✗ hero pick ${i}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ ${Math.min(3, heroCount)} hero picks clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 7: Filter pills ===');
  await p.locator('.tab[data-tab="calc"]').click();
  await p.waitForTimeout(300);
  const pillCount = await p.evaluate(() => document.querySelectorAll('.filter-pill').length);
  console.log(`  found ${pillCount} filter pills`);
  for (let i = 0; i < pillCount; i++) {
    try {
      await p.locator('.filter-pill').nth(i).click({ timeout: 2000 });
      await p.waitForTimeout(80);
    } catch(e) {
      console.log(`  ✗ filter pill ${i}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ ${pillCount} filter pills clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('=== SWEEP 8: Item tiles (sample of 20) ===');
  const itemTileCount = await p.evaluate(() => document.querySelectorAll('.item-tile').length);
  console.log(`  found ${itemTileCount} item tiles`);
  for (let i = 0; i < Math.min(20, itemTileCount); i++) {
    try {
      await p.locator('.item-tile').nth(i).click({ timeout: 2000 });
      await p.waitForTimeout(80);
    } catch(e) {
      console.log(`  ✗ item tile ${i}: ${e.message.slice(0, 80)}`);
    }
  }
  console.log(`  ✓ sample item tiles clicked, JS errors so far: ${jsErrors.length}`);
  
  console.log('');
  console.log('===========================================');
  console.log(`FINAL JS ERRORS: ${jsErrors.length}`);
  if (jsErrors.length > 0) {
    console.log('---');
    const unique = [...new Set(jsErrors)];
    unique.slice(0, 20).forEach(e => console.log(`  · ${e.slice(0, 200)}`));
  }
  
  await b.close();
})();
