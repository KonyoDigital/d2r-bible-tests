// v198 — Bind Demon grant-redundancy layer (Konyo's "8 abilities" insight,
// 2026-06-12). BD grants ES/EF/Spectral/AE at 5/10/15/20; SU binds need 20 so
// all four are always on. Fixed bars burn grants (Hephasto: AE+Spectral = 2 of 4,
// PureDiablo-verified; Lister: Spectral = 1 of 4) → the rolls worth hunting are
// NON-grant mods (Stone Skin / Magic Resistant / Cursed). Plus two verified
// warnings from the diablo2.io thread: respec kills the bound demon (Malchin);
// a carried sunder charm sunders YOUR OWN pet's immunities (Drakenden).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v198 grant-redundancy + warnings', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
  });

  test('the 8-ability math block + grant flags on the affix tiles', async ({ page }) => {
    const r = await page.evaluate(() => {
      const binds = document.getElementById('tab-binds')!.textContent!;
      return {
        math: binds.includes('The 8-ability math'),
        grant5: binds.includes('BD grant at skill 5'),
        grant10: binds.includes('BD grant at skill 10'),
        grant15: binds.includes('BD grant at skill 15'),
        mrRealRoll: binds.includes('NOT a grant — a real roll'),
        podiumLens: binds.includes('BD-20 lens'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });

  test('Lister presents BOTH pokemon targets; Hephasto carries the mod-farm hunt + 2-grant note', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Lister the Tormentor');
      const lister = document.getElementById('bindsu-detail')!.textContent!;
      (window as any).openBindSUByName('Hephasto the Armorer');
      const heph = document.getElementById('bindsu-detail')!.textContent!;
      return {
        maxAbility: lister.includes('MAX-ABILITY = Stone Skin + Cursed/Magic-Resistant'),
        guaranteed: lister.includes('GUARANTEED-AURA = Stone Skin + Conviction-or-Fanaticism'),
        wastedSlot: lister.includes('wasted slot'),
        tankLock: lister.includes('Immune to Physical, the tank-maker'), // v191 lock survives
        hephTwoGrants: heph.includes('burns TWO of the four BD grants'),
        hephModFarm: heph.includes('mod-farm pick'),
        hephChain: heph.includes('Hephasto → Travincal'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });

  test('respec-kills-demon + sunder-sunders-pet warnings present', async ({ page }) => {
    const r = await page.evaluate(() => {
      const binds = document.getElementById('tab-binds')!.textContent!;
      return {
        respec: binds.includes('Respec = your bound demon DIES'),
        sunder: binds.includes('sunder YOUR OWN bound demon'),
        boneBreak: binds.includes('Bone Break') && binds.includes('per-zone trade-off'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });

  test('dream-bind rewrite keeps the v124 locked phrases', async ({ page }) => {
    const r = await page.evaluate(() => {
      const txt = document.body.textContent!;
      return {
        survival: txt.includes('Best survival rolls'),
        dream: txt.includes('The dream bind'),
        esFree: txt.includes('Extra Strong comes free from Bind Demon 5'),
      };
    });
    for (const [k, v] of Object.entries(r)) expect(v, k).toBe(true);
  });
});
