import { test, expect } from '@playwright/test';

// gh#235 — a per-item share override is stored under the panel's name, then ignored
// when suggestMule folds that name. The byte fold (U+2013/U+2014/U+2212 → hyphen) and
// the planner fold ("Harlequin Crest (Shako)" → "Harlequin Crest") each recurse on the
// inner spelling and return before the outer name's override is read. Force-in still
// routes to the shared stash; force-out keeps the war-gear and high/vhigh branches
// from firing. Keepers and standing kit still win. _shareDefault stays override-free.
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
test('a planner-label force-in is shared', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
    const n = "Andariel's Visage (Demonhead)";
    const before = (w.suggestMule(n) || {}).id || null;
    w._setShareOverride(n, 'shared');
    const after = w.suggestMule(n) || {};
    return { before: before, ov: w._shareOverride(n), id: after.id || null };
  });
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

// A charm cannot be forced into a stash it cannot use. Standing kit wins the same way.
test('a keeper force-in stays a keeper', async ({ page }) => {
  const r = await page.evaluate(() => {
    const w = window as any;
    function go(n: string) {
      try { localStorage.removeItem('d2r_vaultShareOverride'); w.__shareOvCache = null; } catch (e) {}
      w._setShareOverride(n, 'shared');
      const s = w.suggestMule(n) || {};
      return { id: s.id || null };
    }
    return { anni: go('Annihilus'), cube: go('Horadric Cube') };
  });
  expect(r.anni.id, 'Annihilus stays in inventory').toBe('__keep');
  expect(r.anni.id, 'a keeper is not shared').not.toBe('shared');
  expect(r.cube.id, 'the Cube stays with the character').toBe('__keep');
  expect(r.cube.id, 'standing kit is not shared').not.toBe('shared');
});
