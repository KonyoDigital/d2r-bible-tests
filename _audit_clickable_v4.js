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
  
  // Clear state
  await p.evaluate(() => {
    localStorage.removeItem('d2r_wishlist');
    localStorage.removeItem('d2r_owned');
  });
  await p.reload();
  await p.waitForTimeout(2000);
  
  // ─── Inline star button — in CALC tab table (corrected location) ───
  console.log('=== INLINE star button — calc tab table ===');
  await p.keyboard.press('2');  // calc tab
  await p.waitForTimeout(400);
  const starCount = await p.evaluate(() => document.querySelectorAll('.star-btn').length);
  console.log(`  found ${starCount} star buttons in calc tab`);
  
  const beforeWish = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  await p.locator('.star-btn').first().click();
  await p.waitForTimeout(300);
  const afterWish = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  console.log(`  wishlist: ${beforeWish} → ${afterWish}  ${afterWish === beforeWish + 1 ? '✓' : '✗'}`);
  
  // ─── Verify localStorage actually persists ───
  const stored = await p.evaluate(() => localStorage.getItem('d2r_wishlist'));
  console.log(`  localStorage d2r_wishlist: ${stored?.slice(0, 80)}`);
  console.log(`  ${stored && stored.length > 5 ? '✓ persisted to localStorage' : '✗ NOT persisted (saveWishlist bug)'}`);
  
  // ─── Reload and verify state survives ───
  console.log('');
  console.log('=== Reload to verify wishlist survives across page loads ===');
  await p.reload();
  await p.waitForTimeout(2000);
  const afterReload = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  console.log(`  wishlist after reload: ${afterReload}  ${afterReload === 1 ? '✓' : '✗'}`);
  
  // ─── Owned button ───
  console.log('');
  console.log('=== Inline OWNED button ===');
  await p.keyboard.press('2');
  await p.waitForTimeout(300);
  const ownedCount = await p.evaluate(() => document.querySelectorAll('.owned-btn').length);
  console.log(`  found ${ownedCount} owned buttons`);
  await p.locator('.owned-btn').first().click();
  await p.waitForTimeout(300);
  const ownedSize = await p.evaluate(() => 
    eval('typeof owned !== "undefined" ? owned.size : -1')
  );
  const ownedStored = await p.evaluate(() => localStorage.getItem('d2r_owned'));
  console.log(`  owned in memory: ${ownedSize}, localStorage: ${ownedStored?.slice(0,40)}`);
  console.log(`  ${ownedSize > 0 && ownedStored ? '✓ persists' : '✗'}`);
  
  // ─── ? modal — toggle test ───
  console.log('');
  console.log('=== ? modal toggle ===');
  await p.keyboard.press('?');
  await p.waitForTimeout(400);
  const modal1 = await p.evaluate(() => {
    const m = document.getElementById('kbd-help-modal');
    return { exists: !!m, hasShow: m?.classList.contains('show') };
  });
  console.log(`  after ? : ${JSON.stringify(modal1)}  ${modal1.hasShow ? '✓' : '✗'}`);
  
  // Click close button
  if (modal1.exists) {
    await p.locator('.kbd-help-close').click();
    await p.waitForTimeout(300);
    const modal2 = await p.evaluate(() => 
      document.getElementById('kbd-help-modal')?.classList.contains('show')
    );
    console.log(`  after close btn: hasShow=${modal2}  ${!modal2 ? '✓' : '✗'}`);
  }
  
  // ─── Click outside modal closes it ───
  console.log('');
  console.log('=== Click outside modal closes it ===');
  await p.keyboard.press('?');
  await p.waitForTimeout(300);
  // Click far outside the card (top-left corner of the modal backdrop)
  await p.mouse.click(20, 20);
  await p.waitForTimeout(300);
  const modal3 = await p.evaluate(() => 
    document.getElementById('kbd-help-modal')?.classList.contains('show')
  );
  console.log(`  click-outside closes: ${!modal3 ? '✓' : '⚠ stayed open'}`);
  
  // ─── Test that palette star command now actually persists ───
  console.log('');
  console.log('=== Palette "star <item>" persists (the bug we just fixed) ===');
  await p.evaluate(() => localStorage.removeItem('d2r_wishlist'));
  await p.reload();
  await p.waitForTimeout(2000);
  
  await p.evaluate(() => { if (window._v42_openPalette) window._v42_openPalette(); });
  await p.waitForTimeout(200);
  await p.locator('#v42-palette-input').fill('star tal rasha');
  await p.waitForTimeout(150);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(400);
  const palWish = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  const palStored = await p.evaluate(() => localStorage.getItem('d2r_wishlist'));
  console.log(`  in-memory: ${palWish}, localStorage: ${palStored?.length || 0} chars`);
  
  await p.reload();
  await p.waitForTimeout(2000);
  const palAfterReload = await p.evaluate(() => 
    eval('typeof wishlist !== "undefined" ? wishlist.size : -1')
  );
  console.log(`  after reload: ${palAfterReload}  ${palAfterReload === palWish && palWish > 0 ? '✓ persists across reload' : '✗'}`);
  
  console.log('');
  console.log('═══════════════════════════════════════════════');
  console.log(`JS errors: ${errs.length}`);
  if (errs.length) [...new Set(errs)].slice(0,5).forEach(e => console.log('  · ' + e.slice(0,180)));
  
  await b.close();
})();
