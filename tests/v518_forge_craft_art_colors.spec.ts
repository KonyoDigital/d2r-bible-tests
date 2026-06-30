import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v516–v519 regression guard: craft ingredient art + tooltips, crafted-orange slot names,
// in-game rarity colour sync (runeword orange / white base white), jewel HD art + magic-blue
// tooltip, and the ideal/merc/endgame base role badges. These are pure-UI features with no
// prior coverage — this locks them so a future forge edit can't silently regress them.

test.beforeEach(async ({ page }) => { await page.goto(URL); await page.waitForTimeout(1600); });

test('jewel art + tooltip resolve to a magic-blue jewel (not the corrupt base_ placeholder)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    // forge registers the jewel art on load; force a forge render to be safe
    try { w.renderForge && w.renderForge(); } catch (e) {}
    const resolve = w._arttipResolve ? w._arttipResolve('any jewel') : null;
    return {
      jewelArt: w.artUrl('any jewel'),
      tipTint: w._tipTint ? w._tipTint('any jewel') : '',
      rich: resolve ? resolve.rich : false,
      descLen: resolve ? (resolve.desc || '').length : 0,
    };
  });
  expect(r.jewelArt).toContain('jewel');           // a real jewel sprite
  expect(r.jewelArt).not.toContain('/base_');      // NOT a corrupt blue-gem placeholder
  expect(r.tipTint).toBe('#9fb0ff');               // magic-blue floating-card title
  expect(r.rich).toBe(true);
  expect(r.descLen).toBeGreaterThan(50);           // the rich jewel card body
});

test('in-game rarity colour: runeword → orange, white base → white, basic tooltip → white', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      rwHex: w._qHex('Breath of the Dying'),
      baseHex: w._qHex('Phase Blade'),
      tipRW: w._tipTint('Breath of the Dying'),
      tipBase: w._tipTint('Phase Blade'),
      tipBow: w._tipTint('Shadow Bow'),
    };
  });
  expect(r.rwHex).toBe('var(--q-orange)');   // runewords orange
  expect(r.baseHex).toBe('var(--q-normal)'); // white bases white
  expect(r.tipRW).toBe('#ffa800');           // floating title orange for a runeword
  expect(r.tipBase).toBe('#f4f4f4');         // floating title white for a base
  expect(r.tipBow).toBe('#f4f4f4');          // and for a base bow
});

test('craft recipe rows: each ingredient (rune / base / jewel) carries HD art + a resolving tooltip', async ({ page }) => {
  // a Caster craft needs a Perfect Amethyst + the slot rune (Ral for the amulet) to surface
  await page.addInitScript(() => {
    localStorage.setItem('d2r_gemStash', JSON.stringify({ 'Perfect Amethyst': 3 }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Ith: 2, Ort: 2, Amn: 2 }));
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    // navigate to forge tab + render + open the Caster craft accordion
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.renderForge && w.renderForge(); } catch (e) {}
    try { w.forgeCraftToggle && w.forgeCraftToggle('Caster'); } catch (e) {}
    const row = document.querySelector('#tab-forge .f-craftrow');
    const rune = document.querySelector('#tab-forge .f-cing-rune');
    const base = document.querySelector('#tab-forge .f-cing-base');
    const jewel = document.querySelector('#tab-forge .f-cing-jewel');
    const slot = document.querySelector('#tab-forge .f-craftrow-slot') as HTMLElement;
    return {
      hasRow: !!row,
      runeArt: rune ? !!rune.querySelector('img') : false,
      runeTip: rune ? rune.getAttribute('data-arttip') : '',
      baseTip: base ? base.getAttribute('data-arttip') : '',
      baseArt: base ? !!base.querySelector('img') : false,
      jewelArt: jewel ? (jewel.querySelector('img') as HTMLImageElement || {}).src || '' : '',
      jewelTip: jewel ? jewel.getAttribute('data-arttip') : '',
      slotColor: slot ? slot.getAttribute('style') : '',
    };
  });
  expect(r.hasRow).toBe(true);
  expect(r.runeArt).toBe(true);                         // rune HD icon
  expect(r.runeTip).toBeTruthy();                       // rune tooltip name
  expect(r.baseArt).toBe(true);                         // base slot HD icon
  expect(r.baseTip).toMatch(/^magic .+ base$/);         // resolves the rich base-options card
  expect(r.jewelArt).toContain('jewel');                // jewel HD art
  expect(r.jewelTip).toBe('any jewel');                 // resolves the jewel card (not "a jewel")
  expect(r.slotColor || '').toContain('q-orange');      // crafted-orange slot name
});

test('base option chips carry ideal / merc / endgame role badges (Insight → merc polearms)', async ({ page }) => {
  // Insight runes (Ral+Tir+Tal+Sol) in hand, NO base → a "need a base" One-step card whose
  // recommended bases are merc polearms (Insight is a 2H merc word) at the elite tier.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.forgeSetFilter && w.forgeSetFilter('onestep'); } catch (e) {}
    const chips = Array.from(document.querySelectorAll('#tab-forge .forge-sec-step .f-getchip-base'));
    // find the chip group for a known merc polearm (Thresher / Cryptic Axe / Giant Thresher)
    const polearm = chips.find((c) => /Thresher|Cryptic Axe|Giant Thresher|Colossus Voulge/.test(c.textContent || ''));
    const badges = polearm ? Array.from(polearm.querySelectorAll('.f-rb')).map((b) => b.textContent) : [];
    const firstChip = chips[0];
    const firstBadges = firstChip ? Array.from(firstChip.querySelectorAll('.f-rb')).map((b) => b.textContent) : [];
    return { chipCount: chips.length, polearmText: polearm ? (polearm.firstChild as any).textContent.trim() : '', badges, firstBadges };
  });
  expect(r.chipCount).toBeGreaterThan(0);
  // a merc polearm base must be tagged "merc" (mercenary 2H gear), never "1H"
  expect(r.badges.join(' ')).toContain('merc');
  expect(r.badges.join(' ')).not.toContain('1H');
  // the first recommended option is flagged ideal
  expect(r.firstBadges.join(' ')).toContain('ideal');
});

test('pipeline card body colours the forged runeword orange and the base white (v522)', async ({ page }) => {
  // an unsocketed owned base + runes in hand → a PIPELINE card (socket-then-forge). Insight on a
  // Larzuk-base Colossus Voulge: title + step text should colour the runeword orange, the base white.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 1, Tir: 1, Tal: 1, Sol: 1 }));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    (['Colossus Voulge (Larzuk base)']).forEach((n) => w._ensureSocketBaseEntry && w._ensureSocketBaseEntry(n));
    try { w.switchTab && w.switchTab('forge'); } catch (e) {}
    try { w.forgeSetFilter && w.forgeSetFilter('pipeline'); } catch (e) {}
    const card = document.querySelector('#tab-forge .f-pipe');
    if (!card) return { hasCard: false };
    // the title's runeword <b> should be orange
    const titleRW = card.querySelector('.f-cardtitle b[data-arttip]') as HTMLElement;
    const titleColor = titleRW ? getComputedStyle(titleRW).color : '';
    // a base name in the step body should be white (q-normal)
    const baseSpan = card.querySelector('.f-step b span[style*="color"]') as HTMLElement;
    const baseColor = baseSpan ? getComputedStyle(baseSpan).color : '';
    return { hasCard: true, titleRW: titleRW ? titleRW.textContent : '', titleColor, baseSpanText: baseSpan ? baseSpan.textContent : '', baseColor };
  });
  expect(r.hasCard).toBe(true);
  expect(r.titleColor).toBe('rgb(255, 168, 0)');   // runeword orange
  expect(r.baseColor).toBe('rgb(244, 244, 244)');  // base white
});
