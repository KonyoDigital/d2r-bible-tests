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
  expect(dest('Crafted Caster Gloves (jackpot)')).toBe('uni-armor');
  expect(dest('Crafted Caster Ring (jackpot)')).toBe('uni-small');
  expect(dest('Marshal\'s Amulet')).toBe('uni-small');
  expect(dest('Godly Rare Jewel (40 ED / 15 IAS)')).toBe('uni-small');
  // (Arioc's Needle moved into the grail in v341.33 — no longer an EXTRA_ITEM, so not audited here)
  // NAMED runeword bases route by SLOT (not the generic SOCKETED mule)
  expect(dest('Eth Giant Thresher (Infinity base)')).toBe('uni-weap'); // Polearm = weapon
  expect(dest('Eth Archon Plate (Enigma/CoH base)')).toBe('uni-armor');
  expect(dest('4-socket Monarch (Spirit base)')).toBe('uni-armor');    // shield
  // GENERIC socketed junk-bases stay in SOCKETED
  expect(dest('Socketed Body Armor')).toBe('bases');
  expect(dest('Socketed 2H Weapon (6os)')).toBe('bases');
  // charms never land in weapons
  const weaponMisfiles = rows.filter(r => r.dest==='uni-weap' && /charm|jewel|jewelry|socketed bases/i.test(r.cat));
  expect(weaponMisfiles.map(r=>r.n).join(',')).toBe('');
});

test('the 9-item live test set routes 100% correctly (rank-1)', async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).suggestMule && (window as any).EXTRA_ITEMS);
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const got = await page.evaluate(() => {
    const sm = (window as any).suggestMule;
    const set = [
      ['Socketed 2H Weapon (6os)','bases'],
      ['Death Cleaver','uni-weap'],
      ['Socketed Body Armor (3os)','bases'],
      ['Chance Guards','uni-armor'],
      ['Bonesnap','uni-weap'],
      ['Amazon Javelin & Spear Skiller (GC)','uni-small'],
      ['Eth Giant Thresher (Infinity base)','uni-weap'],
      ['Paladin Combat Skiller (GC)','uni-small'],
      ['Socketed Body Armor','bases'],
    ];
    return set.map(([n,exp]) => ({ n, exp, got: (sm(n)||{id:'(null)'}).id }));
  });
  const wrong = got.filter(r => r.got !== r.exp);
  console.log('9-ITEM TEST SET:'); got.forEach(r => console.log(`  ${r.got===r.exp?'✓':'✗'} ${r.n} -> ${r.got} (expected ${r.exp})`));
  expect(wrong.map(w=>`${w.n}:${w.got}≠${w.exp}`).join(' | ')).toBe('');
});
