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
  
  // ─── TEST 1: Memory leak — 50x open/close of boss detail ───
  console.log('=== TEST 1: Memory leak — 50× open/close ===');
  const startDom = await p.evaluate(() => document.querySelectorAll('*').length);
  const startListeners = await p.evaluate(() => {
    // Approximate event listener count via attached handlers (not perfect but indicative)
    return [...document.querySelectorAll('*')].filter(el => el.onclick || el.onmousedown).length;
  });
  console.log(`  start: ${startDom} DOM nodes, ${startListeners} with onclick`);
  
  for (let i = 0; i < 50; i++) {
    await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail('mephisto'); });
    await p.waitForTimeout(20);
    await p.evaluate(() => { if (window.clearActiveBoss) window.clearActiveBoss(); });
    await p.waitForTimeout(20);
  }
  
  const endDom = await p.evaluate(() => document.querySelectorAll('*').length);
  const endListeners = await p.evaluate(() => 
    [...document.querySelectorAll('*')].filter(el => el.onclick || el.onmousedown).length
  );
  const domGrowth = endDom - startDom;
  console.log(`  after 50x: ${endDom} DOM nodes (Δ${domGrowth >= 0 ? '+' : ''}${domGrowth}), ${endListeners} with onclick`);
  console.log(`  ${Math.abs(domGrowth) < 100 ? '✓ no significant DOM bloat' : '✗ DOM grew by ' + domGrowth + ' nodes'}`);
  
  // ─── TEST 2: Click on backdrop closes boss detail ───
  console.log('');
  console.log('=== TEST 2: Click on backdrop (overlay outside panel) closes detail ===');
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail('andariel'); });
  await p.waitForTimeout(400);
  const beforeBackdrop = await p.evaluate(() => !document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  // Click in the top-left corner (should be on the backdrop overlay, not the panel which is centered)
  await p.mouse.click(10, 10);
  await p.waitForTimeout(400);
  const afterBackdrop = await p.evaluate(() => document.getElementById('boss-detail-overlay')?.classList.contains('hidden'));
  console.log(`  before: open=${beforeBackdrop}, after click(10,10): hidden=${afterBackdrop}`);
  console.log(`  ${afterBackdrop ? '✓ backdrop click closes' : '⚠ backdrop click does NOT close (need Esc)'}`);
  if (!afterBackdrop) await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 3: Cmd+K toggle — open when closed, close when open ───
  console.log('');
  console.log('=== TEST 3: Cmd+K toggle behavior ===');
  await p.keyboard.press('Meta+k');
  await p.waitForTimeout(300);
  const p1 = await p.evaluate(() => document.getElementById('v42-palette-overlay')?.classList.contains('show'));
  console.log(`  press Cmd+K (closed): open=${p1}  ${p1 ? '✓' : '✗'}`);
  await p.keyboard.press('Meta+k');
  await p.waitForTimeout(300);
  const p2 = await p.evaluate(() => document.getElementById('v42-palette-overlay')?.classList.contains('show'));
  console.log(`  press Cmd+K (open): closed=${!p2}  ${!p2 ? '✓ toggles' : '✗ stuck open'}`);
  if (p2) await p.keyboard.press('Escape');
  
  // ─── TEST 4: Boss detail with INVALID bossId — graceful failure ───
  console.log('');
  console.log('=== TEST 4: Boss detail with invalid bossId ===');
  const initialErrors = errs.length;
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail('not_a_real_boss'); });
  await p.waitForTimeout(400);
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail(null); });
  await p.waitForTimeout(200);
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail(undefined); });
  await p.waitForTimeout(200);
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail(''); });
  await p.waitForTimeout(200);
  const newErrors = errs.length - initialErrors;
  console.log(`  invalid bossIds (4 variants): JS errors added = ${newErrors}  ${newErrors === 0 ? '✓ no errors thrown' : '⚠'}`);
  
  // ─── TEST 5: setActiveItem with invalid name ───
  console.log('');
  console.log('=== TEST 5: setActiveItem with invalid name ===');
  const before5 = errs.length;
  await p.evaluate(() => { 
    if (window.setActiveItem) {
      window.setActiveItem('not_a_real_item_anywhere');
      window.setActiveItem(null);
      window.setActiveItem(undefined);
    }
  });
  await p.waitForTimeout(400);
  console.log(`  invalid items: errors added = ${errs.length - before5}  ${errs.length === before5 ? '✓' : '⚠'}`);
  
  // ─── TEST 6: Window resize during open detail ───
  console.log('');
  console.log('=== TEST 6: Window resize during open boss detail ===');
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.evaluate(() => { if (window.openBossDetail) window.openBossDetail('mephisto'); });
  await p.waitForTimeout(400);
  // Resize from 1280 → 375 (mobile) while detail is open
  await p.setViewportSize({ width: 375, height: 812 });
  await p.waitForTimeout(400);
  const mobileState = await p.evaluate(() => {
    const overlay = document.getElementById('boss-detail-overlay');
    const panel = document.getElementById('boss-detail-panel');
    return {
      stillOpen: !overlay?.classList.contains('hidden'),
      panelWidth: panel ? Math.round(panel.getBoundingClientRect().width) : null,
      panelOverflowsViewport: panel ? panel.getBoundingClientRect().right > 380 : false,
    };
  });
  console.log(`  after resize 1280→375: ${JSON.stringify(mobileState)}`);
  console.log(`  ${mobileState.stillOpen && !mobileState.panelOverflowsViewport ? '✓ adapts to mobile' : '⚠'}`);
  // Resize back
  await p.setViewportSize({ width: 1280, height: 900 });
  await p.waitForTimeout(400);
  const backState = await p.evaluate(() => ({
    panelWidth: Math.round(document.getElementById('boss-detail-panel')?.getBoundingClientRect().width || 0),
  }));
  console.log(`  resize back 375→1280: panel width=${backState.panelWidth}px`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(200);
  
  // ─── TEST 7: Hash routing with bossId (#bosses/mephisto) ───
  console.log('');
  console.log('=== TEST 7: Hash route with bossId (#bosses/mephisto) ===');
  await p.goto('file://' + path.resolve('bible_routes.html') + '#bosses/mephisto');
  await p.waitForTimeout(2000);
  const hashRoute = await p.evaluate(() => ({
    activeTab: document.querySelector('.tab.active')?.dataset.tab,
    activeBoss: eval('typeof activeBossId !== "undefined" ? activeBossId : null'),
  }));
  console.log(`  ${JSON.stringify(hashRoute)}`);
  console.log(`  ${hashRoute.activeBoss === 'mephisto' ? '✓ hash route opens boss directly' : '⚠ hash bossId not honored'}`);
  
  // ─── TEST 8: Item names with special characters render safely (no XSS) ───
  console.log('');
  console.log('=== TEST 8: Item names with quotes/apostrophes render safely ===');
  // ITEMS likely has Tal Rasha's Adjudication etc. with apostrophes
  const apostropheItems = await p.evaluate(() => {
    if (typeof ITEMS === 'undefined') return [];
    return ITEMS.filter(i => i.n.includes("'") || i.n.includes('"') || i.n.includes('&')).map(i => i.n).slice(0,5);
  });
  console.log(`  found ${apostropheItems.length} items with special chars: ${apostropheItems.slice(0,3).join(' | ')}`);
  if (apostropheItems.length > 0) {
    const errsBefore = errs.length;
    for (const name of apostropheItems) {
      await p.evaluate((n) => { if (window.setActiveItem) window.setActiveItem(n); }, name);
      await p.waitForTimeout(80);
    }
    console.log(`  routed all ${apostropheItems.length}: errors added = ${errs.length - errsBefore}  ${errs.length === errsBefore ? '✓' : '✗'}`);
  }
  
  // ─── TEST 9: Page load time ───
  console.log('');
  console.log('=== TEST 9: Page load performance ===');
  const t0 = Date.now();
  await p.goto('file://' + path.resolve('bible_routes.html'));
  await p.waitForLoadState('domcontentloaded');
  const tDOM = Date.now() - t0;
  await p.waitForLoadState('load');
  const tLoad = Date.now() - t0;
  await p.waitForFunction(() => typeof ITEMS !== 'undefined' && ITEMS.length === 312);
  const tReady = Date.now() - t0;
  console.log(`  DOMContentLoaded: ${tDOM}ms`);
  console.log(`  load event: ${tLoad}ms`);
  console.log(`  app ready (ITEMS.length===312): ${tReady}ms`);
  console.log(`  ${tReady < 3000 ? '✓ <3s ready' : '⚠ slow'}`);
  
  // ─── TEST 10: Accessibility quick scan ───
  console.log('');
  console.log('=== TEST 10: Accessibility — aria/role/alt ===');
  const a11y = await p.evaluate(() => {
    const imgs = [...document.querySelectorAll('img')];
    const imgsNoAlt = imgs.filter(i => !i.alt);
    const btns = [...document.querySelectorAll('button')];
    const btnsNoText = btns.filter(b => !b.textContent.trim() && !b.getAttribute('aria-label'));
    const inputs = [...document.querySelectorAll('input')];
    const inputsNoLabel = inputs.filter(i => !i.getAttribute('aria-label') && !i.id);  // ID lets a <label for> work
    return {
      images: imgs.length,
      imagesNoAlt: imgsNoAlt.length,
      buttons: btns.length,
      buttonsNoTextOrAria: btnsNoText.length,
      inputs: inputs.length,
      inputsNoLabel: inputsNoLabel.length,
      langAttr: document.documentElement.lang,
    };
  });
  console.log(`  ${JSON.stringify(a11y, null, 2)}`);
  if (a11y.langAttr) console.log(`  ✓ has <html lang="${a11y.langAttr}">`);
  if (a11y.imagesNoAlt > 0) console.log(`  ⚠ ${a11y.imagesNoAlt} images missing alt`);
  if (a11y.buttonsNoTextOrAria > 0) console.log(`  ⚠ ${a11y.buttonsNoTextOrAria} buttons missing label`);
  
  // ─── FINAL ───
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS ERRORS: ${errs.length}, WARNINGS: ${warns.length}`);
  if (errs.length) [...new Set(errs)].slice(0,3).forEach(e => console.log('  ERR · ' + e.slice(0,180)));
  if (warns.length) [...new Set(warns)].slice(0,5).forEach(w => console.log('  WARN · ' + w.slice(0,180)));
  
  await b.close();
})();
