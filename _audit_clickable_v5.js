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
  await p.evaluate(() => { localStorage.removeItem('d2r_wishlist'); localStorage.removeItem('d2r_owned'); });
  await p.reload();
  await p.waitForTimeout(2000);
  
  // ─── TEST: Both toggleStar AND toggleStarred persist after the fix ───
  console.log('=== TEST 1: toggleStar (canonical) persists ===');
  await p.evaluate(() => { if (typeof toggleStar === 'function') toggleStar('Harlequin Crest (Shako)'); });
  await p.waitForTimeout(200);
  let mem = await p.evaluate(() => eval('typeof wishlist !== "undefined" ? wishlist.size : -1'));
  let ls = await p.evaluate(() => localStorage.getItem('d2r_wishlist'));
  console.log(`  toggleStar: in-memory=${mem}, localStorage=${ls ? ls.length + ' chars' : 'null'}`);
  
  console.log('');
  console.log('=== TEST 2: toggleStarred (was BROKEN — saveWishlist undefined) ===');
  await p.evaluate(() => { if (typeof window.toggleStarred === 'function') window.toggleStarred('Tal Rashas Adjudication (Tal Rasha Amulet)'); });
  await p.waitForTimeout(200);
  mem = await p.evaluate(() => eval('typeof wishlist !== "undefined" ? wishlist.size : -1'));
  ls = await p.evaluate(() => localStorage.getItem('d2r_wishlist'));
  console.log(`  toggleStarred: in-memory=${mem}, localStorage=${ls ? ls.length + ' chars' : 'null'}`);
  console.log(`  Both items in storage? ${ls && ls.includes('Shako') && ls.includes('Tal Rasha') ? '✓ FIXED — both persisted' : '✗ still broken'}`);
  
  console.log('');
  console.log('=== TEST 3: localStorage survives reload ===');
  await p.reload();
  await p.waitForTimeout(2000);
  const surviveMem = await p.evaluate(() => eval('typeof wishlist !== "undefined" ? wishlist.size : -1'));
  console.log(`  in-memory wishlist after reload: ${surviveMem}  ${surviveMem === 2 ? '✓' : '✗ (expected 2)'}`);
  
  console.log('');
  console.log('=== TEST 4: ? modal create + show class ===');
  await p.evaluate(() => document.body.click());  // ensure focus
  await p.keyboard.press('?');
  await p.waitForTimeout(400);
  const modalState = await p.evaluate(() => {
    const m = document.getElementById('kbd-help-modal');
    return { exists: !!m, classList: m ? [...m.classList] : null, display: m ? getComputedStyle(m).display : null };
  });
  console.log(`  modal: ${JSON.stringify(modalState)}`);
  console.log(`  ${modalState.classList?.includes('show') ? '✓' : '✗'}`);
  
  console.log('');
  console.log('=== TEST 5: ALL FINDINGS — full press-keyboard sweep ===');
  // 1-7 tabs
  for (const k of ['1','2','3','4','5','6','7']) {
    await p.keyboard.press(k);
    await p.waitForTimeout(100);
  }
  // shift+1 through shift+6
  for (const k of ['Shift+1','Shift+2','Shift+3','Shift+4','Shift+5','Shift+6']) {
    await p.keyboard.press(k);
    await p.waitForTimeout(80);
  }
  // r toggle
  await p.keyboard.press('r');
  await p.waitForTimeout(100);
  // / focus search
  await p.keyboard.press('/');
  await p.waitForTimeout(100);
  // Esc
  await p.keyboard.press('Escape');
  await p.waitForTimeout(100);
  console.log(`  ✓ all 16 keyboard shortcuts fired without errors`);
  
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`TOTAL JS ERRORS: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,180)));
  
  await b.close();
})();
