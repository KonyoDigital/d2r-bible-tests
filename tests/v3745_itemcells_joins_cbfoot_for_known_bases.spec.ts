import { test, expect } from '@playwright/test';

// REG-2248 (GrokBot #230 — live locker retest on v3743: items still drew approximated, header
// "(sizes approximated)", drawn size == tooltip size — "the stored footprint is wrong, not the
// renderer"). A magic / rare / base item whose NAME is not a unique or set in CB_DB, but whose
// CODEX base IS a real game base, must still draw the GAME footprint (window._cbFoot = the CB_DB
// base's invwidth x invheight), not the 1x2 "(sizes approximated)" guess.
//
// Root cause: _itemCells reached _cbFoot ONLY through a planner-STORED base (a CODE); the base it
// resolves from the codex (ITEM_CODEX.base / ITEM_TIP.b / EXTRA_ITEMS.base / set-piece slot) is a
// NAME and never reached _cbFoot, so a freshly-added item fell to the keyword guesses or the
// {1,2,approx:true} default even though CB_DB knew its base. The fix resolves that base NAME to its
// CB_DB code — off the SAME table _cbFoot reads — and sizes it, dropping approx. A base CB_DB cannot
// size, and a runeword (its base varies), stay approx.
//
// Why these bases and NOT the task's "Monarch"/"Archon Plate": those NAMES already match the keyword
// table in _itemCells (both -> 2x3), so a rare on them was never the approx case — the spec would be
// GREEN before the fix. Mancatcher, Caduceus and Hurlbat match NO keyword rule (verified against the
// live regex chain), so before the fix they fell to {1,2,approx:true} — the exact defect GrokBot
// saw. Each is a single, unambiguous CB_DB base.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any)._itemCells && (window as any)._cbDb && (window as any)._cbFoot && (window as any).EXTRA_ITEMS);
});

test('a magic/rare item on a known base draws the CB_DB footprint, not a 1x2 approximation', async ({ page }) => {
  const r = await page.evaluate(() => {
    const d = (window as any)._cbDb();
    // Resolve a base NAME to its game footprint off the SAME table the renderer uses — pinning the
    // mechanism, not a bare number. If a base's CB_DB size ever changes, the expectation follows it.
    function baseFoot(baseName: string) {
      let code = '';
      const keys = Object.keys(d.b);
      for (let i = 0; i < keys.length && !code; i++) {
        const row = d.b[keys[i]];
        if (row && row[0] && String(row[0]).toLowerCase() === baseName.toLowerCase()) code = keys[i];
      }
      const f = code ? (window as any)._cbFoot({ base: code }) : null;
      return f ? { w: f[0], h: f[1] } : null;
    }
    const E = (window as any).EXTRA_ITEMS;
    const bases = ['Mancatcher', 'Caduceus', 'Hurlbat'];
    const out: any = {};
    bases.forEach((baseName, i) => {
      // A freshly-added rare known only by its base: EXTRA_ITEMS with a base and NO .cells, so the
      // renderer must size it from the base. The NAME is unknown to CB_DB (not a unique/set).
      const nm = 'REG2248 Rare Probe ' + i;
      E[nm] = { base: baseName };
      const c = (window as any)._itemCells(nm);
      out[baseName] = { got: { w: c.w, h: c.h }, approx: !!c.approx, want: baseFoot(baseName) };
      delete E[nm];
    });
    return out;
  });
  for (const baseName of Object.keys(r)) {
    expect(r[baseName].want, `${baseName} must be a sizable CB_DB base`).not.toBeNull();
    expect(r[baseName].got, `${baseName}: a rare on it must draw its CB_DB footprint`).toEqual(r[baseName].want);
    expect(r[baseName].approx, `${baseName}: a known base is a resolved size, not a guess`).toBe(false);
  }
});

test('a name CB_DB cannot size stays an honest approximation (no invented footprint)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS;
    const f = (window as any)._itemCells;
    // 1) a bare unknown name — no catalogue entry, no base at all.
    const bareCells = f('REG2248 Totally Unknown Name');
    // 2) an item whose base is NOT a CB_DB base — the fix must not conjure a size from the word.
    E['REG2248 Unknown Base Item'] = { base: 'Zzqwx Qmblr' };
    const unknownBaseCells = f('REG2248 Unknown Base Item');
    delete E['REG2248 Unknown Base Item'];
    return { bare: !!bareCells.approx, unknownBase: !!unknownBaseCells.approx };
  });
  expect(r.bare, 'a nameless-base item stays approx').toBe(true);
  expect(r.unknownBase, 'a base CB_DB does not know stays approx — never invented from the word').toBe(true);
});

test('a runeword is still NOT pinned to a base by this tier (exclusion preserved)', async ({ page }) => {
  // Grief carries no codex base, so it rides the runeword path and stays an honest guess. The new
  // codex-base tier excludes runewords by design (their base varies); this guards it still does.
  const grief = await page.evaluate(() => (window as any)._itemCells('Grief'));
  expect(grief.approx, 'a baseless Grief stays an honest guess, not a base-pinned size').toBe(true);
});
