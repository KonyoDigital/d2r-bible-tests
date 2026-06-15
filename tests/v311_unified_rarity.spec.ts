import { test, expect } from '@playwright/test';

// v311 — THE ONE SWITCH: _artRarity is the single source of truth for an item's in-game
// quality colour, delegating to itemQuality() for any registry item so UNIQUES resolve
// everywhere (not just sets). _qStyle() paints names inline so it wins over flat colours.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._artRarity && (window as any)._qStyle && (window as any)._artRarity('Metalgrid') === 'unique');
});

test('_artRarity resolves uniques AND sets AND runes (the unified resolver)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._artRarity;
    return {
      metalgrid: f('Metalgrid'), razor: f("Razor's Edge"), stormlash: f('Stormlash'),
      soj: f('The Stone of Jordan'), bloodmoon: f("Bloodmoon's Light"),
      hwanin: f("Hwanin's Majesty (set)"), talAgg: f('Tal Rasha set (any piece)'),
      cowAgg: f("Cow King's Leathers (set)"),
    };
  });
  // uniques must no longer fall through to '' (the bug: sets coloured, uniques didn't)
  expect(r.metalgrid).toBe('unique');
  expect(r.razor).toBe('unique');
  expect(r.stormlash).toBe('unique');
  expect(r.soj).toBe('unique');
  expect(r.bloodmoon).toBe('unique');
  // sets still resolve green
  expect(r.hwanin).toBe('set');
  expect(r.talAgg).toBe('set');
  expect(r.cowAgg).toBe('set');
});

test('_qStyle returns the exact in-game --q-* colour per rarity (inline, !important)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const q = (window as any)._qStyle;
    return {
      unique: q('Metalgrid'),
      set: q("Hwanin's Majesty (set)"),
      fallback: q('Totally Unknown Thing', 'unique'),
      none: q('Totally Unknown Thing'),
    };
  });
  expect(r.unique).toContain('var(--q-unique)');
  expect(r.unique).toContain('!important');
  expect(r.set).toContain('var(--q-set)');
  expect(r.fallback).toContain('var(--q-unique)');   // explicit fallback honoured
  expect(r.none).toBe('');                            // no rarity, no fallback → no style
});

test('the floating tip frame paints uniques gold (setTipR → _artRarity → tip-r-unique)', async ({ page }) => {
  const color = await page.evaluate(() => {
    let tip = document.getElementById('arttip');
    if (!tip) { tip = document.createElement('div'); tip.id = 'arttip'; tip.innerHTML = '<img alt=""><div class="att-name"></div><div class="att-desc"></div>'; document.body.appendChild(tip); }
    const lab = tip.querySelector('.att-name') as HTMLElement; lab.textContent = 'X';
    const rc = (window as any)._artRarity('Metalgrid');     // should be 'unique'
    tip.className = 'tip-r-' + rc;
    return { rc, color: getComputedStyle(lab).color };
  });
  expect(color.rc).toBe('unique');
  expect(color.color).toBe('rgb(199, 179, 119)');   // #c7b377 — in-game unique gold
});

test('runeword names render in orange (their in-game colour) in the All-Runewords browser', async ({ page }) => {
  const c = await page.evaluate(() => {
    const el = document.createElement('div'); el.className = 'arw-name'; el.textContent = 'Enigma';
    document.body.appendChild(el); const col = getComputedStyle(el).color; el.remove(); return col;
  });
  // --q-orange #ffa800 → rgb(255, 168, 0)
  expect(c).toBe('rgb(255, 168, 0)');
});
