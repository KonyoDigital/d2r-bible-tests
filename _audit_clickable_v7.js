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
  
  // ─── TEST 5: Field Manual injection ───
  console.log('=== TEST 5: Field Manual injection on boss detail open ===');
  await p.locator('.boss-chip[data-boss-id="mephisto"]').click();
  await p.waitForTimeout(800);
  const fmCheck = await p.evaluate(() => {
    const panel = document.getElementById('boss-detail-panel');
    if (!panel) return { error: 'no panel' };
    const html = panel.innerHTML;
    return {
      panelChars: html.length,
      hasFieldManual: html.includes('Field Manual') || html.includes('field-manual'),
      hasGuide: html.includes('Strategy') || html.includes('Tactic') || html.includes('Tip'),
      hasV40Marker: html.includes('v40-field-manual') || html.includes('_v40_'),
    };
  });
  console.log(`  ${JSON.stringify(fmCheck)}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(300);
  
  // ─── TEST 6: Wishlist export button — invoke via direct call ───
  console.log('');
  console.log('=== TEST 6: Wishlist export — function + button ===');
  await p.evaluate(() => {
    localStorage.removeItem('d2r_wishlist');
    if (typeof toggleStar === 'function') {
      toggleStar('Harlequin Crest (Shako)');
      toggleStar('Tal Rashas Adjudication (Tal Rasha Amulet)');
      toggleStar('Stone of Jordan');
    }
  });
  await p.waitForTimeout(300);
  
  // First: does the function work at all?
  const exportText = await p.evaluate(() => {
    if (typeof exportWishlistAsMarkdown === 'function') {
      try { return exportWishlistAsMarkdown(); } catch(e) { return 'ERROR: ' + e.message; }
    }
    return 'function not defined';
  });
  console.log(`  exportWishlistAsMarkdown() returned: ${typeof exportText === 'string' ? exportText.slice(0,200) : exportText}`);
  console.log(`  ${exportText && exportText.length > 50 && exportText.includes('Shako') ? '✓ markdown export works' : '✗'}`);
  
  // Find the visible button
  const exportBtnCheck = await p.evaluate(() => {
    const btns = [...document.querySelectorAll('.wishlist-export-btn')];
    return {
      count: btns.length,
      texts: btns.slice(0,3).map(b => b.textContent.trim()),
      firstBtnVisible: btns[0] ? (btns[0].getBoundingClientRect().height > 0) : false,
    };
  });
  console.log(`  export button presence: ${JSON.stringify(exportBtnCheck)}`);
  
  // Click via JS to test
  if (exportBtnCheck.count > 0) {
    const clickResult = await p.evaluate(() => {
      const btn = document.querySelector('.wishlist-export-btn');
      if (!btn) return 'no button';
      try {
        btn.click();
        return 'click succeeded';
      } catch(e) {
        return 'click failed: ' + e.message;
      }
    });
    console.log(`  programmatic click: ${clickResult}`);
  }
  
  // ─── TEST 7: kbd-tip tooltips show on hover ───
  console.log('');
  console.log('=== TEST 7: kbd-tip data-tip + tooltip presence ===');
  const tipCheck = await p.evaluate(() => {
    const tips = [...document.querySelectorAll('.kbd-tip')];
    const withTip = tips.filter(t => t.dataset.tip);
    return {
      total: tips.length,
      withTip: withTip.length,
      samples: withTip.slice(0,3).map(t => ({ label: t.textContent.slice(0,15), tip: t.dataset.tip.slice(0,50) })),
    };
  });
  console.log(`  total: ${tipCheck.total}, with data-tip: ${tipCheck.withTip}`);
  tipCheck.samples.forEach(s => console.log(`    · "${s.label}" → "${s.tip}..."`));
  console.log(`  ${tipCheck.total === tipCheck.withTip ? '✓ all have data-tip' : '⚠'}`);
  
  // ─── TEST 8: TZ countdown text format ───
  console.log('');
  console.log('=== TEST 8: TZ countdown text format MM:SS ===');
  const tzWidget = await p.evaluate(() => {
    const w = document.getElementById('v42-tz-countdown');
    if (!w) return null;
    return {
      classList: [...w.classList],
      timeText: w.querySelector('.v42-tz-time')?.textContent?.trim(),
      labelText: w.querySelector('.v42-tz-label')?.textContent?.trim(),
      visible: w.classList.contains('show'),
    };
  });
  console.log(`  ${JSON.stringify(tzWidget)}`);
  const validFormat = /\d{1,2}:\d{2}/.test(tzWidget?.timeText || '');
  console.log(`  ${validFormat ? '✓ valid MM:SS' : '✗'}`);
  
  // ─── TEST 9: Active item bar appears on item selection ───
  console.log('');
  console.log('=== TEST 9: Active item bar UI fully populates ===');
  await p.evaluate(() => { if (typeof window.setActiveItem === 'function') window.setActiveItem('Harlequin Crest (Shako)'); });
  await p.waitForTimeout(400);
  const aibState = await p.evaluate(() => {
    const bar = document.getElementById('active-item-bar');
    const detail = document.getElementById('active-item-detail');
    return {
      barShown: bar?.classList.contains('show'),
      itemName: document.getElementById('aib-item-name')?.textContent,
      detailShown: detail?.classList.contains('show'),
      detailHasContent: detail ? detail.innerHTML.length > 100 : false,
    };
  });
  console.log(`  ${JSON.stringify(aibState)}`);
  console.log(`  ${aibState.barShown && aibState.itemName === 'Harlequin Crest (Shako)' ? '✓' : '✗'}`);
  
  // ─── TEST 10: Sticky header behavior — does the header stay on scroll? ───
  console.log('');
  console.log('=== TEST 10: Sticky header stays during scroll ===');
  await p.evaluate(() => window.scrollTo(0, 2000));
  await p.waitForTimeout(300);
  const headerState = await p.evaluate(() => {
    const tabs = document.querySelector('.tabs');
    const header = document.querySelector('.header');
    return {
      tabsTop: tabs ? Math.round(tabs.getBoundingClientRect().top) : null,
      tabsPosition: tabs ? getComputedStyle(tabs).position : null,
      headerTop: header ? Math.round(header.getBoundingClientRect().top) : null,
      headerPosition: header ? getComputedStyle(header).position : null,
    };
  });
  console.log(`  ${JSON.stringify(headerState)}`);
  const tabsSticky = headerState.tabsPosition === 'sticky' || headerState.tabsPosition === 'fixed' || (headerState.tabsTop >= -10 && headerState.tabsTop < 250);
  console.log(`  ${tabsSticky ? '✓ tabs stay accessible while scrolled' : '⚠ tabs scrolled out of view'}`);
  
  // ─── TEST 11: Difficulty columns in boss tables ───
  console.log('');
  console.log('=== TEST 11: Difficulty column headers (NORM/NM/Hell/TZ) in tables ===');
  await p.evaluate(() => window.scrollTo(0, 0));
  await p.keyboard.press('2');  // calc tab
  await p.waitForTimeout(300);
  const diffHeaders = await p.evaluate(() => {
    const headers = [...document.querySelectorAll('th, .diff-header, .col-header')];
    const found = headers.map(h => h.textContent.trim()).filter(t => 
      /NORM|NM|Hell|TZ/i.test(t)
    );
    return { count: found.length, sample: found.slice(0,8) };
  });
  console.log(`  difficulty headers: ${diffHeaders.count} found, samples: ${diffHeaders.sample.join(' | ')}`);
  
  // ─── TEST 12: Browser back/forward through hash routes ───
  console.log('');
  console.log('=== TEST 12: Browser back/forward navigation through hash ===');
  await p.goto('file://' + path.resolve('bible_routes.html') + '#bosses');
  await p.waitForTimeout(1000);
  await p.evaluate(() => { if (typeof window.switchTab === 'function') window.switchTab('calc'); });
  await p.waitForTimeout(300);
  await p.evaluate(() => { if (typeof window.switchTab === 'function') window.switchTab('runes'); });
  await p.waitForTimeout(300);
  await p.goBack();
  await p.waitForTimeout(500);
  const backTab = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log(`  after goBack: tab=${backTab}  ${backTab === 'calc' ? '✓' : '⚠'}`);
  await p.goForward();
  await p.waitForTimeout(500);
  const fwdTab = await p.evaluate(() => document.querySelector('.tab.active')?.dataset.tab);
  console.log(`  after goForward: tab=${fwdTab}  ${fwdTab === 'runes' ? '✓' : '⚠'}`);
  
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS errors: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,180)));
  
  await b.close();
})();
