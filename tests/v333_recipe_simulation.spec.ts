import { test, expect } from '@playwright/test';

// v333 — SIMULATION / DATA-LOCK: provably-correct crafting + runeword recipes ("see they each
// work"). Locks the full 36-cell craft rune matrix, the cube-up state machine, the top runeword
// recipes, and item footprints against canonical D2R values transcribed from maxroll / Arreat Summit.
test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).CRAFTS && (window as any)._craftSlotReady && (window as any)._itemCells);
  await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tools'));
});

const CRAFT_MATRIX: Record<string, Record<string, string>> = {
  Caster:    { Weapon:'Tir', Shield:'Eth', Helm:'Nef', 'Body Armor':'Tal', Gloves:'Ort', Belt:'Ith', Boots:'Thul', Amulet:'Ral', Ring:'Amn' },
  Blood:     { Weapon:'Ort', Shield:'Ith', Helm:'Ral', 'Body Armor':'Thul', Gloves:'Nef', Belt:'Tal', Boots:'Eth', Amulet:'Amn', Ring:'Sol' },
  Safety:    { Weapon:'Sol', Shield:'Nef', Helm:'Ith', 'Body Armor':'Eth', Gloves:'Ral', Belt:'Tal', Boots:'Ort', Amulet:'Thul', Ring:'Amn' },
  'Hit Power':{ Weapon:'Tir', Shield:'Eth', Helm:'Ith', 'Body Armor':'Nef', Gloves:'Ort', Belt:'Tal', Boots:'Ral', Amulet:'Thul', Ring:'Amn' },
};

test('the full 36-cell craft rune matrix matches canonical D2R', async ({ page }) => {
  const got = await page.evaluate(() => {
    const out: any = {};
    for (const c of (window as any).CRAFTS) { out[c.key] = {}; for (const s of Object.keys(c.slots)) out[c.key][s] = c.slots[s].rune; }
    return out;
  });
  for (const craft of Object.keys(CRAFT_MATRIX))
    for (const slot of Object.keys(CRAFT_MATRIX[craft]))
      expect(got[craft]?.[slot], `${craft} ${slot}`).toBe(CRAFT_MATRIX[craft][slot]);
});

test('craft cube-state machine: ready when holding gem+rune+base, cube when gem is cube-up-able', async ({ page }) => {
  const r = await page.evaluate(() => {
    const CRAFTS = (window as any).CRAFTS, sr = (window as any)._craftSlotReady;
    const caster = CRAFTS.find((c: any) => c.key === 'Caster');
    // 0) HONESTY (v341): hold the Perfect Amethyst + Ral rune but NO magic base → NOT ready
    (window as any).adjustGemStash('Perfect Amethyst', 1);
    (window as any).adjustRuneStash('Ral', 1);
    const noBase = sr(caster, 'Amulet');
    // 1) ready: now mark a magic Amulet base owned → cubeable for real
    (window as any).toggleCraftBase('Amulet');
    const ready = sr(caster, 'Amulet');
    // 2) cube: drop the Perfect, hold 3 Flawless (cube-up-able) + the rune (+ base still on)
    (window as any).adjustGemStash('Perfect Amethyst', -1);
    (window as any).adjustGemStash('Flawless Amethyst', 3);
    const cube = sr(caster, 'Amulet');
    (window as any).toggleCraftBase('Amulet');   // clean up the toggle
    return { noBase, ready, cube };
  });
  expect(r.noBase.ingredientsReady).toBe(true);   // gem+rune in hand …
  expect(r.noBase.haveBase).toBe(false);
  expect(r.noBase.ready).toBe(false);             // … but NOT craftable — no magic base
  expect(r.noBase.missing.some((m: string) => /magic Amulet base/.test(m))).toBe(true);
  expect(r.ready.ready).toBe(true);               // base marked → honestly cubeable now
  expect(r.cube.ready).toBe(false);
  expect(r.cube.cube).toBe(true);          // ◆ after gem cube-up
  expect(r.cube.haveGemCubed).toBe(true);
});

const RW: Record<string, string[]> = {
  Spirit:['Tal','Thul','Ort','Amn'], Grief:['Eth','Tir','Lo','Mal','Ral'], Enigma:['Jah','Ith','Ber'],
  Infinity:['Ber','Mal','Ber','Ist'], 'Call to Arms':['Amn','Ral','Mal','Ist','Ohm'], Insight:['Ral','Tir','Tal','Sol'],
  'Heart of the Oak':['Ko','Vex','Pul','Thul'], Fortitude:['El','Sol','Dol','Lo'], Phoenix:['Vex','Vex','Lo','Jah'],
  Faith:['Ohm','Jah','Lem','Eld'], Death:['Hel','El','Vex','Ort','Gul'], 'Breath of the Dying':['Vex','Hel','El','Eld','Zod','Eth'],
  'Chains of Honor':['Dol','Um','Ber','Ist'], Dream:['Io','Jah','Pul'], Delirium:['Lem','Ist','Io'],
};

test('top runeword recipes match canonical rune order', async ({ page }) => {
  const got = await page.evaluate((names) => {
    const T = (window as any).RUNEWORD_TIP || {}; const out: any = {};
    for (const n of names) out[n] = T[n] ? T[n].rec : null;
    return out;
  }, Object.keys(RW));
  for (const n of Object.keys(RW)) expect(got[n], n).toEqual(RW[n]);
});

test('item footprints match D2R inventory cells (incl. belt 2x1 fix)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._itemCells;
    return {
      ring: f('The Stone of Jordan'), skiller: f('+1 Skiller Grand Charm'),
      twoH: f('Socketed 2H Weapon (6os)'), belt: f('Goldwrap'), helm: f('Socketed Helm (3os)'),
    };
  });
  expect(r.ring).toEqual({ w: 1, h: 1 });
  expect(r.skiller).toEqual({ w: 1, h: 3 });
  expect(r.twoH).toEqual({ w: 2, h: 4 });
  expect(r.belt).toEqual({ w: 2, h: 1 });   // belts are 2x1 in D2R
  expect(r.helm).toEqual({ w: 2, h: 2 });
});
