import { test, expect } from '@playwright/test';

// REG-2206 (GrokBot batch T, #230) — a UNIQUE or SET piece is sized by its FIXED base, from the
// game's own inventory dims (window._cbFoot = the CB_DB base's invwidth x invheight), never by
// matching keywords in its NAME. The keyword heuristic in _itemCells guessed, and guessed WRONG for
// a dozen owned uniques that carry no stored base: The Oculus 2x2→1x3, Bonehew 1x3→2x4, Death
// Cleaver 2x4→2x3, Schaefer's Hammer 1x3→2x3, etc. Reproduced in headless Chrome (every current
// value matched GrokBot's wrong "app size" exactly); base-derived matches true D2 for 10/10.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._itemCells && (window as any)._cbDb && (window as any)._cbFoot);
});

// The LAW: a unique's footprint IS its fixed base's game footprint. Pinning the mechanism, not a
// bare number — if the CB_DB base size ever changes, this follows it.
test('a unique is sized by its fixed base (_cbFoot), not by its name', async ({ page }) => {
  const r = await page.evaluate(() => {
    const d = (window as any)._cbDb();
    function baseFoot(name: string) {
      let hit: any = null;
      (d.it || []).forEach((it: any) => { if (it && it[1] === name && (it[2] === 'u' || it[2] === 's') && !hit) hit = it; });
      if (!hit) return null;
      const code = ((window as any)._cbBasesOf(hit) || [])[0];
      const f = code ? (window as any)._cbFoot({ base: code }) : null;
      return f ? { w: f[0], h: f[1] } : null;
    }
    const names = ['The Oculus', 'Bonehew', 'Death Cleaver', 'The Grandfather', 'Windforce'];
    const out: any = {};
    names.forEach(n => { out[n] = { cells: (window as any)._itemCells(n), base: baseFoot(n) }; });
    return out;
  });
  for (const n of Object.keys(r)) {
    expect(r[n].base, `${n} must resolve a base`).not.toBeNull();
    expect({ w: r[n].cells.w, h: r[n].cells.h }, `${n} footprint must equal its base footprint`).toEqual(r[n].base);
  }
});

// The true-D2 ground truth GrokBot measured on the live board — these were all wrong before the fix.
test('the dozen mis-sized uniques now draw their true D2 footprint', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._itemCells;
    const want: Record<string, [number, number]> = {
      'The Oculus': [1, 3], "Arioc's Needle": [2, 4], "Bartuc's Cut-Throat": [1, 3],
      'Bonehew': [2, 4], 'Death Cleaver': [2, 3], 'Jade Talon': [1, 3],
      "Schaefer's Hammer": [2, 3], "Titan's Revenge": [1, 3], 'Warshrike': [1, 2], 'Wizardspike': [1, 2],
    };
    const out: any = {};
    Object.keys(want).forEach(n => { const c = f(n); out[n] = { got: [c.w, c.h], want: want[n], approx: !!c.approx }; });
    return out;
  });
  for (const n of Object.keys(r)) {
    expect(r[n].got, `${n} true D2 footprint`).toEqual(r[n].want);
    expect(r[n].approx, `${n} must be a resolved size, not a guess`).toBe(false);
  }
});

// The EXCLUSION: a runeword's base varies, so it must NOT be pinned to one base by this tier —
// without a stored base it stays an honest approximate guess (the dashed-edge "unknown" tile).
test('a runeword is NOT pinned to a single base by the unique tier', async ({ page }) => {
  const grief = await page.evaluate(() => (window as any)._itemCells('Grief'));
  expect(grief.approx, 'a baseless Grief stays an honest guess, not a confident unique pin').toBe(true);
});
