const { chromium } = require('@playwright/test');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  
  const errs = [];
  
  // ─── TEST 1: MOBILE VIEWPORT (iPhone 13 size) ───
  console.log('=== TEST 1: MOBILE viewport (375×812) — does everything still work? ===');
  const pMobile = await b.newPage({ viewport: { width: 375, height: 812 } });
  pMobile.on('pageerror', e => errs.push(`MOBILE PAGEERROR: ${e.message}`));
  pMobile.on('console', m => { if (m.type() === 'error' && !m.text().includes('Failed to load resource')) errs.push(`MOBILE CONSOLE: ${m.text()}`); });
  
  await pMobile.goto('file://' + path.resolve('bible_routes.html'));
  await pMobile.waitForTimeout(2000);
  
  // Tab tap-target sizes
  const tabSizes = await pMobile.evaluate(() => {
    return [...document.querySelectorAll('.tab')].map(t => {
      const r = t.getBoundingClientRect();
      return { name: t.dataset.tab, h: Math.round(r.height), w: Math.round(r.width) };
    });
  });
  console.log(`  tabs (apple 44pt min): ${tabSizes.map(t => `${t.name}=${t.h}h`).join(' ')}`);
  const smallTabs = tabSizes.filter(t => t.h < 44);
  console.log(`  ${smallTabs.length === 0 ? '✓' : '✗'} all tabs ≥44pt tall`);
  
  // Boss chips on mobile
  const chipSizes = await pMobile.evaluate(() => {
    return [...document.querySelectorAll('.boss-chip')].slice(0,5).map(c => {
      const r = c.getBoundingClientRect();
      return { id: c.dataset.bossId, h: Math.round(r.height) };
    });
  });
  console.log(`  boss chips: ${chipSizes.map(c => `${c.id}=${c.h}h`).join(' ')}`);
  const smallChips = chipSizes.filter(c => c.h < 30);
  console.log(`  ${smallChips.length === 0 ? '✓' : '⚠'} chips ≥30pt`);
  
  // Click a mobile boss chip
  await pMobile.locator('.boss-chip[data-boss-id="andariel"]').click();
  await pMobile.waitForTimeout(500);
  const mobileDetailOpen = await pMobile.evaluate(() => !document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  console.log(`  mobile boss chip → detail opens: ${mobileDetailOpen ? '✓' : '✗'}`);
  
  // Mobile palette
  await pMobile.evaluate(() => { if (window._v42_openPalette) window._v42_openPalette(); });
  await pMobile.waitForTimeout(200);
  const palWidth = await pMobile.evaluate(() => {
    const pal = document.getElementById('v42-palette');
    return pal ? Math.round(pal.getBoundingClientRect().width) : null;
  });
  console.log(`  mobile palette width: ${palWidth}px (viewport=375)  ${palWidth && palWidth < 375 ? '✓' : '⚠'}`);
  
  // Input font-size check (iOS zoom prevention)
  const inputFontSize = await pMobile.evaluate(() => {
    const input = document.getElementById('v42-palette-input');
    return input ? getComputedStyle(input).fontSize : null;
  });
  console.log(`  palette input font-size: ${inputFontSize}  ${inputFontSize === '16px' ? '✓ (prevents iOS zoom)' : '⚠ might trigger iOS auto-zoom'}`);
  
  await pMobile.close();
  
  // ─── TEST 2: PERSISTENCE across reload ───
  console.log('');
  console.log('=== TEST 2: All state persists across reload ===');
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  p.on('pageerror', e => errs.push(`PAGEERROR: ${e.message}`));
  p.on('console', m => { if (m.type() === 'error' && !m.text().includes('Failed to load resource')) errs.push(`CONSOLE: ${m.text()}`); });
  
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(2000);
  
  // Set state
  await p.evaluate(() => {
    localStorage.clear();
    if (typeof toggleStar === 'function') toggleStar('Harlequin Crest (Shako)');
    if (typeof toggleOwned === 'function') toggleOwned('Tarnhelm');
    document.getElementById('mf').value = 777;
    document.getElementById('mf').dispatchEvent(new Event('input', { bubbles: true }));
    document.getElementById('players').value = 5;
    document.getElementById('players').dispatchEvent(new Event('input', { bubbles: true }));
    if (typeof window.switchTab === 'function') window.switchTab('runes');
  });
  await p.waitForTimeout(400);
  
  const setState = await p.evaluate(() => ({
    mf: document.getElementById('mf').value,
    players: document.getElementById('players').value,
    activeTab: document.querySelector('.tab.active')?.dataset.tab,
    wishlist: eval('typeof wishlist !== "undefined" ? wishlist.size : -1'),
    owned: eval('typeof owned !== "undefined" ? owned.size : -1'),
  }));
  console.log(`  set: ${JSON.stringify(setState)}`);
  
  await p.reload();
  await p.waitForTimeout(2000);
  
  const reloadedState = await p.evaluate(() => ({
    mf: document.getElementById('mf').value,
    players: document.getElementById('players').value,
    activeTab: document.querySelector('.tab.active')?.dataset.tab,
    wishlist: eval('typeof wishlist !== "undefined" ? wishlist.size : -1'),
    owned: eval('typeof owned !== "undefined" ? owned.size : -1'),
  }));
  console.log(`  after reload: ${JSON.stringify(reloadedState)}`);
  
  for (const k of ['mf','players','activeTab','wishlist','owned']) {
    const match = String(setState[k]) === String(reloadedState[k]);
    console.log(`  ${match ? '✓' : '✗'} ${k} persisted (${setState[k]} → ${reloadedState[k]})`);
  }
  
  // ─── TEST 3: URL hash routing ───
  console.log('');
  console.log('=== TEST 3: URL hash routing (#tab) ===');
  await p.goto('file://' + path.resolve('bible_routes.html') + '#calc');
  await p.waitForTimeout(1500);
  const fromHash = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log(`  load with #calc: active tab = ${fromHash}  ${fromHash === 'calc' ? '✓' : '✗'}`);
  
  await p.goto('file://' + path.resolve('bible_routes.html') + '#tz');
  await p.waitForTimeout(1500);
  const fromHash2 = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log(`  load with #tz: active tab = ${fromHash2}  ${fromHash2 === 'tz' ? '✓' : '✗'}`);
  
  // Tab change updates hash
  await p.keyboard.press('4');  // runes
  await p.waitForTimeout(300);
  const newHash = await p.evaluate(() => location.hash);
  console.log(`  press '4': hash = "${newHash}"  ${newHash === '#runes' ? '✓' : '✗'}`);
  
  // ─── TEST 4: Source chips in calc (need item selected first) ───
  console.log('');
  console.log('=== TEST 4: Source chips in calc tab (after item selection) ===');
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForTimeout(2000);
  await p.keyboard.press('2');  // calc
  await p.waitForTimeout(300);
  // Click an item tile to make it active
  await p.evaluate(() => {
    if (typeof window.setActiveItem === 'function') window.setActiveItem('Harlequin Crest (Shako)');
  });
  await p.waitForTimeout(400);
  const sourceChipsAfter = await p.evaluate(() => document.querySelectorAll('.source-chip').length);
  console.log(`  source chips visible after item select: ${sourceChipsAfter}  ${sourceChipsAfter > 0 ? '✓' : '⚠'}`);
  if (sourceChipsAfter > 0) {
    const tabBefore = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
    await p.locator('.source-chip').first().click();
    await p.waitForTimeout(500);
    const tabAfter = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
    console.log(`  click source chip: tab ${tabBefore} → ${tabAfter}  ${tabAfter === 'bosses' ? '✓ routes to bosses' : '⚠'}`);
  }
  
  // ─── TEST 5: Field Manual injection after boss detail ───
  console.log('');
  console.log('=== TEST 5: Field Manual auto-injected after boss detail load ===');
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(800);  // wait for field manual setTimeout(50)
  const fmInjected = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    if (!panel) return null;
    // Field manual usually has specific markers
    const text = panel.innerHTML;
    return {
      hasManualMarker: text.includes('Field Manual') || text.includes('field-manual') || text.includes('boss-field-manual') || text.includes('boss-tactics'),
      panelSize: text.length,
    };
  });
  console.log(`  field manual: ${JSON.stringify(fmInjected)}  ${fmInjected?.hasManualMarker ? '✓' : '⚠ no explicit marker'}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 6: Wishlist export button (after wishlist has items) ───
  console.log('');
  console.log('=== TEST 6: Wishlist export to clipboard ===');
  // Ensure wishlist has items
  await p.evaluate(() => {
    if (typeof toggleStar === 'function') {
      toggleStar('Harlequin Crest (Shako)');
      toggleStar('Tal Rashas Adjudication (Tal Rasha Amulet)');
    }
  });
  await p.waitForTimeout(400);
  
  // Try to find the export button — may be in wishlist hunt path render
  const exportFinder = await p.evaluate(() => {
    const btns = [...document.querySelectorAll('button, [onclick]')].filter(b => 
      b.textContent.includes('Export') || b.className.includes('export')
    );
    return btns.map(b => ({ text: b.textContent.trim().slice(0,40), cls: b.className.slice(0,40) }));
  });
  console.log(`  export-related buttons found: ${exportFinder.length}`);
  exportFinder.slice(0,3).forEach(e => console.log(`    · "${e.text}" [${e.cls}]`));
  
  // ─── TEST 7: kbd-tip tooltip elements ───
  console.log('');
  console.log('=== TEST 7: Hover tooltips (kbd-tip) all have data-tip ===');
  const tooltipCheck = await p.evaluate(() => {
    const tips = [...document.querySelectorAll('.kbd-tip')];
    const missing = tips.filter(t => !t.dataset.tip || t.dataset.tip.trim() === '');
    return { total: tips.length, missing: missing.length, missingTexts: missing.slice(0,3).map(t => t.textContent.slice(0,20)) };
  });
  console.log(`  total kbd-tip elements: ${tooltipCheck.total}, missing data-tip: ${tooltipCheck.missing}  ${tooltipCheck.missing === 0 ? '✓' : '⚠'}`);
  
  // ─── TEST 8: TZ countdown shows valid time ───
  console.log('');
  console.log('=== TEST 8: TZ countdown shows valid time (MM:SS) ===');
  const tzTime = await p.evaluate(() => {
    const tw = document.getElementById('v42-tz-countdown');
    if (!tw) return null;
    const txt = tw.querySelector('.v42-tz-time')?.textContent || tw.textContent;
    return txt;
  });
  const isValidTime = /\d{1,2}:\d{2}/.test(tzTime || '');
  console.log(`  TZ countdown text: "${tzTime?.slice(0,30)}"  ${isValidTime ? '✓' : '✗'}`);
  
  // ─── FINAL ───
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS errors: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,180)));
  
  await b.close();
})();
