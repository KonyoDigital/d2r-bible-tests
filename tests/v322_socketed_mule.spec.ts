import { test, expect } from '@playwright/test';

// v322 — Socketed bases get a home. Generic "Socketed <Slot>" reference entries register via
// AI intake (now in vocab via EXTRA_ITEMS), route to the SOCKETED mule, and read in-game white.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._artRarity && (window as any).EXTRA_ITEMS);
});

test('the generic socketed buckets exist in EXTRA_ITEMS (basic rarity, Socketed bases cat)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS;
    // v324: only the 4 D2-socketable slots — weapons split 1H/2H. gloves/belt/boots can't be socketed.
    const slots = ['Socketed Body Armor','Socketed Helm','Socketed Shield','Socketed 1H Weapon','Socketed 2H Weapon'];
    const removed = ['Socketed Gloves','Socketed Belt','Socketed Boots','Socketed Weapon'];
    return {
      slots: slots.map(s => ({ s, present: !!E[s], rarity: E[s] && E[s].rarity, cat: E[s] && E[s].cat })),
      removed: removed.map(s => ({ s, present: !!E[s] })),
    };
  });
  for (const e of r.slots) {
    expect(e.present, e.s).toBe(true);
    expect(e.rarity, e.s).toBe('basic');
    expect(e.cat, e.s).toBe('Socketed bases');
  }
  for (const e of r.removed) expect(e.present, e.s + ' should be gone (not socketable)').toBe(false);
});

test('socketed buckets resolve to in-game white (--q-normal) via _artRarity/_qStyle', async ({ page }) => {
  const r = await page.evaluate(() => {
    const ar = (window as any)._artRarity, qh = (window as any)._qHex;
    return { rar: ar('Socketed Body Armor'), hex: qh('Socketed 2H Weapon') };
  });
  expect(r.rar).toBe('basic');
  expect(r.hex).toBe('var(--q-normal)');
});

test('socketed items are in the intake vocab (so the AI can register them)', async ({ page }) => {
  const inVocab = await page.evaluate(() => {
    const vocab = Object.keys((window as any).EXTRA_ITEMS);
    return ['Socketed Body Armor','Socketed Helm','Socketed Shield','Socketed 1H Weapon','Socketed 2H Weapon'].every(n => vocab.includes(n));
  });
  expect(inVocab).toBe(true);
});

test('the SOCKETED mule exists and socketed items route to it', async ({ page }) => {
  // open Tools tab so the vault module initialises its roster + suggestMule
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); (window as any).renderVault && (window as any).renderVault(); });
  const r = await page.evaluate(() => {
    const sm = (window as any).suggestMule;
    return sm ? {
      armor: sm('Socketed Body Armor'),
      w1: sm('Socketed 1H Weapon (5os)'),
      w2: sm('Socketed 2H Weapon (4os)'),
    } : null;
  });
  expect(r).not.toBeNull();
  expect(r!.armor.id).toBe('bases');
  expect(r!.w1.id).toBe('bases');
  expect(r!.w2.id).toBe('bases');
});
