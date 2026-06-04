import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v77 — the "crystal ball" Worldstone-Shard outcome planner + the RotW endgame
// accuracy calibration. When you tally a shard, renderShardCrystal reveals (with a
// reveal animation) exactly what it MAKES: right-click → terrorize its act, or cube
// → its matching Renewed Sunder. Both the shard name and the Sunder name route to
// their material cards via openDrop. The accuracy block guards the verified chain
// (1× of each key → 1 random portal; Lilith→Horn / Uber Izual→Brain / Uber Duriel→Eye)
// so it can never silently drift back to the old wrong mapping.
test.describe('v77 crystal-ball shard outcomes + RotW accuracy', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => { try { localStorage.clear(); } catch (e) {} });
  });

  test('SHARD_OUTCOMES exposes all 5 shards mapped to act + Renewed Sunder', async ({ page }) => {
    const data = await page.evaluate(() => (window as any).SHARD_OUTCOMES);
    expect(Array.isArray(data)).toBe(true);
    expect(data.length).toBe(5);
    const map = Object.fromEntries(data.map((s: any) => [s.n, { act: s.act, sunder: s.sunder, el: s.el }]));
    expect(map['Western Worldstone Shard']).toMatchObject({ act: 'Act 1', sunder: 'Rotting Fissure', el: 'poison' });
    expect(map['Eastern Worldstone Shard']).toMatchObject({ act: 'Act 2', sunder: 'Cold Rupture', el: 'cold' });
    expect(map['Southern Worldstone Shard']).toMatchObject({ act: 'Act 3', sunder: 'Crack of the Heavens', el: 'lightning' });
    expect(map['Deep Worldstone Shard']).toMatchObject({ act: 'Act 4', sunder: 'Flame Rift', el: 'fire' });
    expect(map['Northern Worldstone Shard']).toMatchObject({ act: 'Act 5', sunder: 'Bone Break', el: 'physical' });
  });

  test('renderShardCrystal renders the crystal panel inside the material planner', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderMaterialStash();
      const box = document.getElementById('material-craftable')!;
      const panel = box.querySelector('.crystal-panel');
      return {
        fn: typeof (window as any).renderShardCrystal,
        hasPanel: !!panel,
        head: panel?.querySelector('.crystal-head')?.textContent || '',
        rows: panel ? panel.querySelectorAll('.shard-out').length : 0,
        orb: !!panel?.querySelector('.crystal-head .orb'),
      };
    });
    expect(r.fn).toBe('function');
    expect(r.hasPanel).toBe(true);
    expect(r.head).toMatch(/Worldstone Shard outcomes/);
    expect(r.rows).toBe(5);
    expect(r.orb).toBe(true);
  });

  test('tallying a shard lights its row (.has); untallied rows stay .dim', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).adjustMaterialStash('Deep Worldstone Shard', 2);
      const box = document.getElementById('material-craftable')!;
      const deep = box.querySelector('.shard-out[data-shard="Deep Worldstone Shard"]')!;
      const west = box.querySelector('.shard-out[data-shard="Western Worldstone Shard"]')!;
      return {
        deepHas: deep.classList.contains('has'),
        deepCnt: deep.querySelector('.shard-out-cnt')?.textContent?.trim(),
        westDim: west.classList.contains('dim'),
        deepTerror: deep.querySelector('.shard-out-line .t')?.textContent || '',
        deepBody: deep.textContent || '',
      };
    });
    expect(r.deepHas).toBe(true);
    expect(r.deepCnt).toBe('×2');
    expect(r.westDim).toBe(true);
    expect(r.deepTerror).toMatch(/right-click/);
    expect(r.deepBody).toMatch(/terrorize Act 4/);
    expect(r.deepBody).toMatch(/Flame Rift/);
  });

  test('shard name and Sunder name both route to their material cards', async ({ page }) => {
    // shard name → shard card
    const shard = await page.evaluate(() => {
      (window as any).adjustMaterialStash('Northern Worldstone Shard', 1);
      const box = document.getElementById('material-craftable')!;
      (box.querySelector('.shard-out[data-shard="Northern Worldstone Shard"] .shard-out-name') as HTMLElement).click();
      const card = document.querySelector('#item-detail .material-card');
      return { has: !!card, text: card?.textContent || '' };
    });
    expect(shard.has).toBe(true);
    expect(shard.text).toMatch(/Northern/);
    expect(shard.text).toMatch(/Worldstone Shard/);
    // Sunder name → Sunder card
    const sunder = await page.evaluate(() => {
      const box = document.getElementById('material-craftable')!;
      (box.querySelector('.shard-out[data-shard="Northern Worldstone Shard"] .shard-out-line .zd-item-click') as HTMLElement).click();
      const card = document.querySelector('#item-detail .material-card');
      return { has: !!card, text: card?.textContent || '' };
    });
    expect(sunder.has).toBe(true);
    expect(sunder.text).toMatch(/Bone Break/);
  });

  test('the reveal animation is wired (crystalReveal keyframe + rows animate)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).renderMaterialStash();
      const row = document.querySelector('#material-craftable .shard-out') as HTMLElement;
      const name = getComputedStyle(row).animationName;
      return { name };
    });
    expect(r.name).toBe('crystalReveal');
  });

  // ── accuracy calibration guards ──────────────────────────────────────────
  test('Pandemonium recipe is 1× of each key → 1 random portal (not 3× one key)', async ({ page }) => {
    const txt = await page.evaluate(() => {
      const tab = document.getElementById('tab-ancients')!;
      return tab.textContent || '';
    });
    expect(txt).toMatch(/1× Key of Terror \+ 1× Key of Hate \+ 1× Key of Destruction/);
    expect(txt).not.toMatch(/3× Key of Terror.{0,40}Matron/);
  });

  test('organ→boss mapping is verified: Lilith→Horn, Uber Izual→Brain, Uber Duriel→Eye', async ({ page }) => {
    const organ = await page.evaluate(() => {
      const sd = (SPECIAL_DROPS as any).organ.items;
      return Object.fromEntries(sd.map((i: any) => [i.n, i.from[0]]));
    });
    expect(organ["Diablo's Horn"]).toMatch(/Lilith/);
    expect(organ["Mephisto's Brain"]).toMatch(/Izual/);
    expect(organ["Baal's Eye"]).toMatch(/Duriel/);
    // and the old wrong attributions are gone
    expect(organ["Diablo's Horn"]).not.toMatch(/Uber Diablo/);
    expect(organ["Mephisto's Brain"]).not.toMatch(/Uber Mephisto/);
  });

  test('shard explainer answers free-game-or-hold with the terrorize-act use', async ({ page }) => {
    const txt = await page.evaluate(() => document.getElementById('tab-rotw')?.textContent || '');
    expect(txt).toMatch(/terrorize the whole act/i);
    expect(txt).toMatch(/not free/i);
    expect(txt).not.toMatch(/worthless on its own/);
  });

  test('no console errors across the crystal-ball flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).adjustMaterialStash('Western Worldstone Shard', 1);
      (window as any).adjustMaterialStash('Southern Worldstone Shard', 3);
      (window as any).renderMaterialCraftable();
    });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
