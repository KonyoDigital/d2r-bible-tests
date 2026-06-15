import { test, expect } from '@playwright/test';
test('every EXTRA_ITEM routes to a sensible mule (calibration audit)', async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).suggestMule && (window as any).EXTRA_ITEMS);
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const rows = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS, sm = (window as any).suggestMule;
    return Object.keys(E).map(n => ({ n, cat: E[n].cat||'', dest: (sm(n)||{id:'(null/shared)'}).id }));
  });
  // group by category -> destinations
  const byCat: Record<string, Record<string, string[]>> = {};
  for (const r of rows) { (byCat[r.cat] = byCat[r.cat]||{}); (byCat[r.cat][r.dest]=byCat[r.cat][r.dest]||[]).push(r.n); }
  console.log('\n===== EXTRA_ITEMS ROUTING BY CATEGORY =====');
  for (const cat of Object.keys(byCat).sort()) {
    console.log(`\n## ${cat}`);
    for (const dest of Object.keys(byCat[cat])) console.log(`   -> ${dest}: ${byCat[cat][dest].length}  e.g. ${byCat[cat][dest].slice(0,3).join(' | ')}`);
  }
  // hard assertions on the expected destinations
  const dest = (n:string)=> rows.find(r=>r.n===n)?.dest;
  expect(dest('Amazon Javelin & Spear Skiller (GC)')).toBe('uni-small');
  expect(dest('Paladin Combat Skiller (GC)')).toBe('uni-small');
  expect(dest('Eth Giant Thresher (Infinity base)')).toBe('bases');
  expect(dest('Socketed Body Armor')).toBe('bases');
  expect(dest('Socketed 2H Weapon (6os)')).toBe('bases');
  expect(dest('Crafted Caster Gloves (jackpot)')).toBe('uni-armor');
  expect(dest('Crafted Caster Ring (jackpot)')).toBe('uni-small');
  expect(dest('Marshal\'s Amulet')).toBe('uni-small');
  expect(dest('Godly Rare Jewel (40 ED / 15 IAS)')).toBe('uni-small');
  expect(dest('Arioc\'s Needle')).toBe('uni-weap');   // Hyperion SPEAR — not the shield (regex collision fixed)
  // no EXTRA item should ever default to uni-weap unless it's an actual weapon unique
  const weaponMisfiles = rows.filter(r => r.dest==='uni-weap' && /charm|jewel|jewelry|socketed bases|runeword bases/i.test(r.cat));
  expect(weaponMisfiles.map(r=>r.n).join(',')).toBe('');
});
