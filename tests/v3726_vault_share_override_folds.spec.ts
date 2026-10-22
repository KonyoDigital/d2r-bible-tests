import { test, expect } from '@playwright/test';

// gh#235 — a per-item share override is stored under the panel's name, then ignored
// when suggestMule folds that name. The byte fold (U+2013/U+2014/U+2212 → hyphen) and
// the planner fold ("Harlequin Crest (Shako)" → "Harlequin Crest") each recurse on the
// inner spelling and return before the outer name's override is read. Force-in still
// routes to the shared stash; force-out keeps the war-gear and high/vhigh branches
// from firing. Standing kit still wins (REG-2241 moved the charm keepers to the shared
// stash, so they follow the switch). _shareDefault stays override-free.
//
// Each case does its work inside one evaluate. The vault re-renders asynchronously
// and can wipe a panel between an evaluate and a later locator.

test.beforeEach(async ({ page, context }) => {
  await context.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify([
        'Harlequin Crest (Shako)',
        'Bul-Kathos Wedding Band',
        'Buriza-Do Kyanon',
        "Andariel's Visage",
        'Annihilus',
        'Horadric Cube',
      ]));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() =>
    (window as any).suggestMule && (window as any)._shareOverride &&
    (window as any)._shareDefault && (window as any)._setShareOverride);
});

// The planner's own label is a real register key. Unchecking it must leave the shared stash.
test('a planner-label force-mule is not shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    const n = 'Harlequin Crest (Shako)';
    const plain = w.suggestMule(n) || {};
    w._setShareOverride(n, 'mule');
    const after = w.suggestMule(n) || {};
    return {
      before: plain.id || null,
      why: plain.why || '',
      ov: w._shareOverride(n),
      def: w._shareDefault(n),
      id: after.id || null,
    };
  });
  expect(r.before, 'precondition: the planner label routes to the shared stash').toBe('shared');
  expect(r.why, 'REG-1913: the planner names the item').toContain('the planner names it');
  expect(r.why, 'REG-1913: filed as the canonical name').toContain('filed as Harlequin Crest');
  expect(r.why, 'REG-1913: a planner label is not called a misread').not.toContain('misread');
  expect(r.ov, 'the override is stored on the planner label').toBe('mule');
  expect(r.def, '_shareDefault ignores the override and does not recurse').toBe('shared');
  expect(r.id, 'force-mule leaves the shared stash').not.toBe('shared');
  expect(r.id, 'force-mule still has a home').toBeTruthy();
});

// Register key "Bul-Kathos Wedding Band" (ASCII hyphen, high trade, shared). No shared
// candidate stores U+2013/U+2014/U+2212 — the only such key is a mid jewel whose fold is
// the unsorted exception. The byte fold's input is this register key with U+2013 where
// the hyphen is, and that read was returning shared after the override was saved.
test('a dashed register name force-mule is not shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    const reg = 'Bul-Kathos Wedding Band';
    const n = reg.replace('-', '\u2013');
    const before = (w.suggestMule(n) || {}).id || null;
    w._setShareOverride(n, 'mule');
    const after = w.suggestMule(n) || {};
    return {
      inReg: !!(w.ITEM_REGISTRY && w.ITEM_REGISTRY[reg]),
      cp: n.codePointAt(n.indexOf('\u2013')),
      before: before,
      ov: w._shareOverride(n),
      id: after.id || null,
    };
  });
  expect(r.inReg, 'Bul-Kathos Wedding Band is a register key').toBe(true);
  expect(r.cp, 'the tested spelling carries an en dash').toBe(0x2013);
  expect(r.before, 'precondition: the dashed read is a shared candidate').toBe('shared');
  expect(r.ov, 'the override is stored on the dashed spelling').toBe('mule');
  expect(r.id, 'force-mule leaves the shared stash').not.toBe('shared');
  expect(r.id, 'force-mule still has a home').toBeTruthy();
});

// A folding name whose rules say mule, forced in, must become shared.
// V0 spec refresh (#176) — REG-2242 (his ruling: merc gear lives in the shared stash) made Andariel's Visage
// shared by default, so its planner label can no longer be the "rules say mule" case. Re-anchored on a med-tier,
// NON-merc helm whose planner label still folds: "Nightwing's Veil (Spired Helm)" — d2rResolveItem calls it
// unknown, the fuzzy fold hop files it as Nightwing's Veil ("the planner names it"), and it routes to uni-armor
// (measured on the merged V1 tree). The why-text premise keeps this case on the fold hop it was written for.
test('a planner-label force-in is shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    const n = "Nightwing's Veil (Spired Helm)";
    const plain = w.suggestMule(n) || {};
    w._setShareOverride(n, 'shared');
    const after = w.suggestMule(n) || {};
    return { before: plain.id || null, why: plain.why || '', ov: w._shareOverride(n), id: after.id || null };
  });
  expect(r.why, 'precondition: the label reaches the planner fold hop (REG-1913)').toContain('the planner names it');
  expect(r.before, 'precondition: the rules do not share this planner label').not.toBe('shared');
  expect(r.ov, 'the force-in is stored').toBe('shared');
  expect(r.id, 'force-in routes to the shared stash').toBe('shared');
});

test('a dashed-name force-in is shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    const reg = 'Buriza-Do Kyanon';
    const n = reg.replace('-', '\u2013');
    const before = (w.suggestMule(n) || {}).id || null;
    w._setShareOverride(n, 'shared');
    const after = w.suggestMule(n) || {};
    return {
      inReg: !!(w.ITEM_REGISTRY && w.ITEM_REGISTRY[reg]),
      cp: n.codePointAt(n.indexOf('\u2013')),
      before: before,
      ov: w._shareOverride(n),
      id: after.id || null,
    };
  });
  expect(r.inReg, 'Buriza-Do Kyanon is a register key').toBe(true);
  expect(r.cp, 'the tested spelling carries an en dash').toBe(0x2013);
  expect(r.before, 'precondition: the rules do not share this dashed name').not.toBe('shared');
  expect(r.ov, 'the force-in is stored').toBe('shared');
  expect(r.id, 'force-in routes to the shared stash').toBe('shared');
});

// Standing kit cannot be forced into the shared stash: it stays with the character.
// V0 spec refresh (#176) — REG-2241, his ruling 2026-10-15 (verbatim): "torches and anni stay in shared. gheeds
// gets muled." Annihilus is no longer a MAIN keeper (__keep): the rules alone put it in the shared stash
// (suggestMule: `if (_ov !== 'mule' && /^(Annihilus|Hellfire Torch)$/i ...) return {id:'shared'...}`), so his
// per-item switch decides it like any shared item — ticked it stays shared, unticked it goes to its charm mule
// (uni-small, measured on the merged V1 tree), never to MAIN and never nowhere. Standing kit (_keepHome, the §29
// furniture list, read ABOVE the override) is the keeper that still wins over a forced tick.
test('a keeper force-in stays a keeper; Annihilus follows his switch (REG-2241)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    function go(n: string, v: string) {
      try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
      w._setShareOverride(n, v);
      const s = w.suggestMule(n) || {};
      return { id: s.id || null, ov: w._shareOverride(n) };
    }
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    return { anniDefault: w._shareDefault('Annihilus'), anniIn: go('Annihilus', 'shared'), anniOut: go('Annihilus', 'mule'),
             cube: go('Horadric Cube', 'shared') };
  });
  expect(r.anniDefault, 'REG-2241: the rules alone keep Annihilus in the shared stash').toBe('shared');
  expect(r.anniIn.id, 'ticked → the shared stash').toBe('shared');
  expect(r.anniOut.ov, 'unticking differs from the default, so it is stored').toBe('mule');
  expect(r.anniOut.id, 'unticked → out of the shared stash').not.toBe('shared');
  expect(r.anniOut.id, 'unticked → its charm mule, never parked on MAIN').toBe('uni-small');
  expect(r.cube.id, 'the Cube stays with the character').toBe('__keep');
  expect(r.cube.id, 'standing kit is not shared').not.toBe('shared');
});
