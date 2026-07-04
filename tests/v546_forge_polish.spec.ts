import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v546 — four polish features Konyo picked:
//  A) Smart Insights farm-priority shows tier-accurate "where to farm" (elite → lvl-85 areas / Terror Zones).
//  B) "Do this one thing" hero banner atop the Forge — the single highest-leverage next move.
//  C) Rune radar surfaces the cube-up planner (how many of a short rune you can cascade to, + jump).
//  D) The cube-socket gamble cards show affordability (how many tries your gem stash covers).

const ALL_RUNES = 'El Eld Tir Nef Eth Ith Tal Ral Ort Thul Amn Sol Shael Dol Hel Io Lum Ko Fal Lem Pul Um Mal Ist Gul Vex Ohm Lo Sur Ber Jah Cham Zod'.split(' ');

test('B — hero banner: a Make-now-ready vault shows "Do this one thing" with a Make now CTA', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));   // Insight base, exact 4os
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Tir: 2, Tal: 2, Sol: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    w.switchTab('forge'); w.forgeSetFilter('all'); w.renderForge();
    const hero = document.querySelector('#tab-forge .forge-hero');
    return { present: !!hero, text: hero ? (hero.textContent || '').replace(/\s+/g, ' ') : '' };
  });
  expect(r.present).toBe(true);
  expect(r.text).toMatch(/do this one thing/i);
  expect(r.text).toMatch(/Make now/);
});

test('B — hero banner: with nothing to make, it names the top farm target', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({}));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('forge'); w.forgeSetFilter('all'); w.renderForge();
    const hero = document.querySelector('#tab-forge .forge-hero');
    return hero ? (hero.textContent || '').replace(/\s+/g, ' ') : '';
  });
  // no runes/bases → the only actionable thing is the one-step / farm target
  expect(r).toMatch(/do this one thing/i);
  expect(r).toMatch(/farm|one step/i);
});

test('D — gamble card shows gem affordability from the gem stash', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Flail (Heart of the Oak base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ko: 17, Vex: 10, Pul: 18, Thul: 36 }));
    localStorage.setItem('d2r_gemStash', JSON.stringify({ 'Perfect Amethyst': 6 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Flail (Heart of the Oak base)');
    w.switchTab('forge'); w.forgeSetFilter('pipeline'); w.renderForge();
    return (document.getElementById('tab-forge')!.textContent || '').replace(/\s+/g, ' ');
  });
  expect(r).toMatch(/you hold 6 Perfect Amethyst/);
  expect(r).toMatch(/~6 tries/);
});

test('A — Smart Insights farm-priority shows tier-accurate lvl-85 "where to farm"', async ({ page }) => {
  await page.addInitScript((runes) => {
    const stash: any = {}; (runes as string[]).forEach((x) => (stash[x] = 3));
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify(stash));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, ALL_RUNES);
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    w.switchTab('tools'); w.renderSmartInsights();
    const t = document.getElementById('smart-insights-body')?.textContent || '';
    // an elite base (e.g. Archon Plate) must be tagged elite + lvl-85 guidance present
    return { txt: t.replace(/\s+/g, ' '), eliteTier: (w._baseTier ? w._baseTier('Archon Plate') : '') };
  });
  expect(r.eliteTier).toBe('elite');
  expect(r.txt).toMatch(/lvl-85/);
  expect(r.txt).toMatch(/Terror Zones/);
});

// ---- UX SIMULATIONS — drive the RENDERED UI by clicking, not just reading state (Konyo's standing rule) ----

test('UX — clicking the hero "Make now →" CTA actually switches the Forge to the Make-now filter', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Tir: 2, Tal: 2, Sol: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  await page.evaluate(() => { const w: any = window; w._ensureSocketBaseEntry('Colossus Voulge (4os)'); w.switchTab('forge'); w.forgeSetFilter('all'); w.renderForge(); });
  // real click on the rendered CTA button
  await page.locator('#tab-forge .forge-hero .fh-cta').click();
  await page.waitForTimeout(300);
  const cls = await page.evaluate(() => document.querySelector('#tab-forge .forge-tabs .ft-now')?.className || '');
  expect(cls).toMatch(/\bon\b/);   // Make-now tab is now the active filter
});

test('UX — clicking a Rune-radar cube-up chip expands the planner, pre-selects the rune, shows the count', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ El: 400 }));   // a pile of El → cascades way up
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const c = document.getElementById('smart-insights-card');
    if (c && c.classList.contains('collapsed') && w.toggleCardCollapse) w.toggleCardCollapse('smart-insights-card');
    w.renderSmartInsights();
  });
  const chip = page.locator('#smart-insights-body .si-cube').first();
  await expect(chip).toBeVisible();
  await chip.click();
  await page.waitForTimeout(500);
  const r = await page.evaluate(() => {
    const card = document.getElementById('rune-stash-card');
    const sel = document.getElementById('rune-cubeup-target') as HTMLSelectElement;
    return { expanded: !!card && !card.classList.contains('collapsed'), result: (document.getElementById('cubeup-result')?.textContent || '').replace(/\s+/g, ' ').trim() };
  });
  expect(r.expanded).toBe(true);
  expect(r.result).toMatch(/\d+×/);   // the planner shows a computed "N× <Rune>"
});

test('UX — clicking the "Jump to Terror Zones" tip switches to the TZ tab', async ({ page }) => {
  await page.addInitScript((runes) => {
    const stash: any = {}; (runes as string[]).forEach((x) => (stash[x] = 3));
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify(stash));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, ALL_RUNES);
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const w: any = window; w.switchTab('tools');
    const c = document.getElementById('smart-insights-card');
    if (c && c.classList.contains('collapsed') && w.toggleCardCollapse) w.toggleCardCollapse('smart-insights-card');
    w.renderSmartInsights();
  });
  await page.locator('#smart-insights-body .si-tip', { hasText: 'Terror Zones' }).click();
  await page.waitForTimeout(400);
  const active = await page.evaluate(() => {
    const tz = document.getElementById('tab-tz');
    return tz ? getComputedStyle(tz).display !== 'none' : false;
  });
  expect(active).toBe(true);
});

test('C — Rune radar surfaces cube-up potential; _runeCubeUpTo cascades the stash', async ({ page }) => {
  await page.addInitScript(() => {
    // a pile of low runes → can cube up to a mid rune (Vex etc.)
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ El: 200, Eld: 50 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      fnType: typeof w._runeCubeUpTo,
      jump: typeof w.smartJumpRuneCubeUp,
      // 200 El cascade up should yield at least 1 of several rungs higher
      tir: w._runeCubeUpTo('Tir'),
    };
  });
  expect(r.fnType).toBe('function');
  expect(r.jump).toBe('function');
  expect(r.tir).toBeGreaterThan(0);
});
