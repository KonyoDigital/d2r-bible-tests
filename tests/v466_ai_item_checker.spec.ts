// v466 — 🔬 AI Item Checker: isolated flagship tool to judge a MAGIC/RARE item. Transparent affix-value verdict
// (keep/borderline/toss) cross-referencing the slot's runeword bar, manual affix editing, and Mule/Toss actions.
// All verdict logic lives here so the regular cards stay clean.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v466 AI Item Checker', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any)._aicVerdict && (window as any).renderAIItemChecker && (window as any).aicMule);
    await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
    await page.waitForTimeout(800);
  });

  test('strong caster roll → KEEP, with a transparent breakdown', async ({ page }) => {
    const v = await page.evaluate(() => (window as any)._aicVerdict({
      base: 'Crystal Sword', q: 'rare',
      mods: ['+2 to All Skills', '+40% Faster Cast Rate', '+12 to All Attributes'],
    }));
    expect(v.tier).toBe('keep');
    expect(v.score).toBeGreaterThanOrEqual(14);
    expect(v.breakdown.length).toBe(3);          // each valued affix is itemized (not a black box)
    expect(v.ctx.join(' ')).toMatch(/cannot be a runeword base/i);
  });

  test('pure melee junk roll → TOSS', async ({ page }) => {
    const v = await page.evaluate(() => (window as any)._aicVerdict({
      base: 'Crystal Sword', q: 'magic',
      mods: ['+10% Increased Attack Speed', '+45% Enhanced Damage', '+75 to Attack Rating'],
    }));
    expect(v.tier).toBe('toss');
    expect(v.score).toBeLessThan(7);
  });

  test('mid roll → BORDERLINE', async ({ page }) => {
    const v = await page.evaluate(() => (window as any)._aicVerdict({
      base: 'Sharkskin Belt', q: 'rare', mods: ['+30% Faster Hit Recovery', '+20 to Life'],
    }));
    expect(v.tier).toBe('border');
  });

  test('verdict states the slot benchmark for the base type', async ({ page }) => {
    const v = await page.evaluate(() => (window as any)._aicVerdict({ base: 'Archon Plate', q: 'rare', mods: ['+100 Defense'] }));
    expect(v.ctx.join(' ')).toMatch(/Enigma|Fortitude|Chains of Honor/);
  });

  test('each affix scores its HIGHEST matching weight (no double-count)', async ({ page }) => {
    // "All Resistances" must score the all-res weight (6), not also the single-resist weight (2)
    const v = await page.evaluate(() => (window as any)._aicVerdict({ base: 'Tower Shield', q: 'rare', mods: ['+30 to All Resistances'] }));
    expect(v.score).toBe(6);
  });

  test('Mule it → registers to Magic & Rare, assigns a mule, clears the draft', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._aicSetDraft({ name: 'Caster Wonder', base: 'Crystal Sword', q: 'rare', mods: ['+2 to All Skills', '+40% Faster Cast Rate'] });
      w.aicMule();
      const mf = JSON.parse(localStorage.getItem('d2r_magicFinds') || '{}');
      const assign = JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}');
      return { registered: !!mf['Caster Wonder'], q: mf['Caster Wonder'] && mf['Caster Wonder'].q,
               mods: mf['Caster Wonder'] && mf['Caster Wonder'].mods.length, mule: assign['Caster Wonder'],
               draftCleared: w._aicGetDraft().base === '' && w._aicGetDraft().mods.length === 0 };
    });
    expect(r.registered).toBe(true);
    expect(r.q).toBe('rare');
    expect(r.mods).toBe(2);
    expect(r.mule).toBeTruthy();       // auto-assigned to a mule
    expect(r.draftCleared).toBe(true);
  });

  test('Toss → clears the draft without registering', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w._aicSetDraft({ name: 'Junk', base: 'Crystal Sword', q: 'magic', mods: ['+45% Enhanced Damage'] });
      w.aicToss();
      const mf = JSON.parse(localStorage.getItem('d2r_magicFinds') || '{}');
      return { notRegistered: !mf['Junk'], cleared: w._aicGetDraft().base === '' };
    });
    expect(r.notRegistered).toBe(true);
    expect(r.cleared).toBe(true);
  });

  test('the section renders (drop zone + editor + actions)', async ({ page }) => {
    const html = await page.evaluate(() => {
      const w = window as any;
      w._aicSetDraft({ name: '', base: 'Crystal Sword', q: 'rare', mods: ['+2 to All Skills'] });
      w.renderAIItemChecker();
      return (document.getElementById('aic-wrap') || {}).innerHTML || '';
    });
    expect(html).toContain('Drop a magic/rare item screenshot');
    expect(html).toContain('aicMule');
    expect(html).toContain('aicToss');
    expect(html).toMatch(/WORTH KEEPING|BORDERLINE|NOT WORTH IT/);
  });
});
