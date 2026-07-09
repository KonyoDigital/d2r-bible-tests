import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v634 — TIER-1 LADDER PREVIEW: a pure VIEW toggle on the 🪜 strip. Expanded, each ladder word
// shows a full read-only plan (recipe · base to farm · ladder-economy note). ZERO writes to game
// state — the exact anti-messiness contract Konyo asked for after the live-flip incident.

test('toggle expands 9 plan cards (recipes + base + 🪜 ribbon, Hustle = legacy note), collapses back — and game state is BYTE-IDENTICAL', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const KEYS = ['d2r_owned','d2r_unknownReads','d2r_rwMade','d2r_ladderMode','d2r_rwBaseUsed','d2r_copies','d2r_runeStash'];
    const snap = () => KEYS.map((k) => k + '=' + (localStorage.getItem(k) || '')).join('|');
    const before = snap();
    w.switchTab('forge'); try { w.renderForge(); } catch (e) {}
    const strip0 = document.getElementById('forge-ladder-strip')!;
    const collapsed = strip0.querySelectorAll('.forge-ladder-plan').length === 0 && strip0.querySelectorAll('.f-getchip').length >= 8;
    (document.getElementById('forge-ladder-preview-btn') as any).click();          // 🪜 show ladder plans
    const strip1 = document.getElementById('forge-ladder-strip')!;
    const plans = [...strip1.querySelectorAll('.forge-ladder-plan')];
    const mania = plans.find((c) => /Mania/.test(c.textContent || ''));
    const hustle = plans.find((c) => /Hustle/.test(c.textContent || ''));
    const expanded = {
      count: plans.length,
      allRibboned: plans.every((c) => /ladder-only/.test(c.textContent || '')),
      maniaRecipe: !!(mania && mania.querySelector('.f-atomrecipe')),
      maniaBase: !!(mania && /base:/.test(mania.textContent || '')),
      hustleLegacy: !!(hustle && /legacy|never cube/i.test(hustle.textContent || '')),
      hustleNoRecipe: !!(hustle && !hustle.querySelector('.f-atomrecipe')),
      noButtons: plans.every((c) => c.querySelectorAll('button').length === 0),     // read-only: no ✓ created
    };
    (document.getElementById('forge-ladder-preview-btn') as any).click();          // hide again
    const strip2 = document.getElementById('forge-ladder-strip')!;
    const recollapsed = strip2.querySelectorAll('.forge-ladder-plan').length === 0;
    const after = snap();
    localStorage.removeItem('d2r_ladderPreview');
    return { collapsed, expanded, recollapsed, stateIdentical: before === after };
  });
  expect(r.collapsed).toBe(true);
  expect(r.expanded.count).toBe(9);
  expect(r.expanded.allRibboned).toBe(true);
  expect(r.expanded.maniaRecipe).toBe(true);
  expect(r.expanded.maniaBase).toBe(true);
  expect(r.expanded.hustleLegacy).toBe(true);
  expect(r.expanded.hustleNoRecipe).toBe(true);
  expect(r.expanded.noButtons).toBe(true);
  expect(r.recollapsed).toBe(true);
  expect(r.stateIdentical).toBe(true);   // THE contract: previewing never touches the account
});
