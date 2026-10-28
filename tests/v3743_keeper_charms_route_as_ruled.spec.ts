import { test, expect } from '@playwright/test';

// REG-2241 - his ruling 2026-10-15 (verbatim): "torches and anni stay in shared. gheeds gets muled."
// Before this, all three iconic charms routed to __keep (stay on MAIN): GrokBot saw Annihilus sitting in
// UNI-SMALL and Gheed's Fortune reading "stays with your MAIN" - both live-wrong. His call splits them:
// Annihilus + Hellfire Torch belong in the SHARED stash every character reaches; Gheed's Fortune mules by
// slot like any grand charm (-> UNI-SMALL), never __keep, never shared. The per-item share switch still
// wins above the rule.
//
// RED before the fix: suggestMule returns {id:'__keep'} for all three, so every id assertion below fails.
// GREEN after: Anni/Torch -> 'shared', Gheed's -> a real mule id (uni-small; the CHARMS mule since his 2026-10-28
// ruling, REG-2895), override and fold hops hold.

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any).suggestMule && (window as any)._shareDefault
    && (window as any)._setShareOverride && (window as any).d2rItemLookup);
});

test('the three keeper charms route per his 2026-10-15 ruling', async ({ page }) => {
  const r = await page.evaluate(() => {
    try { localStorage.removeItem('d2r_vaultShareOverride'); } catch (e) {}
    try { (window as any).__shareOvCache = undefined; } catch (e) {}
    const sm = (window as any).suggestMule;
    const id = (n: string) => { const v = sm(n); return v ? v.id : '__null'; };
    return {
      anni: id('Annihilus'),
      torch: id('Hellfire Torch'),
      gheed: id("Gheed's Fortune"),
      gheedCurly: id('Gheed’s Fortune'),   // the catalogue stores the apostrophe curly
      defAnni: (window as any)._shareDefault('Annihilus'),
      defTorch: (window as any)._shareDefault('Hellfire Torch'),
      defGheed: (window as any)._shareDefault("Gheed's Fortune"),
    };
  });
  // Annihilus and the Hellfire Torch ride in the shared stash
  expect(r.anni, 'Annihilus must route to the shared stash').toBe('shared');
  expect(r.torch, 'Hellfire Torch must route to the shared stash').toBe('shared');
  // Gheed's Fortune is MULED - a real mule id, never 'shared'/'__keep'/'__throwout'/null
  expect(r.gheed, "Gheed's Fortune must NOT stay shared").not.toBe('shared');
  expect(['__keep', '__throwout', '__null', null, undefined, ''],
    "Gheed's Fortune must route to a real mule, not a keep/throwout sentinel").not.toContain(r.gheed);
  // REG-2895 - his 2026-10-28 ruling: Gheed's Fortune, a magic-find charm, mules on the dedicated CHARMS mule
  expect(r.gheed, "Gheed's Fortune (a magic-find grand charm) mules to the CHARMS mule").toBe('charms');
  // the apostrophe-fold hop answers the curly catalogue name the SAME way
  expect(r.gheedCurly, "curly 'Gheed’s Fortune' must fold to the same mule as the straight one").toBe(r.gheed);
  // the share panel reads its defaults from the same rule
  expect(r.defAnni, 'the panel default for Annihilus is shared').toBe('shared');
  expect(r.defTorch, 'the panel default for Hellfire Torch is shared').toBe('shared');
  expect(r.defGheed, "the panel default for Gheed's Fortune is mule").toBe('mule');
});

test('his per-item share switch still wins over the ruling', async ({ page }) => {
  const r = await page.evaluate(() => {
    const sm = (window as any).suggestMule;
    const set = (window as any)._setShareOverride;
    const id = (n: string) => { const v = sm(n); return v ? v.id : '__null'; };
    try { localStorage.removeItem('d2r_vaultShareOverride'); } catch (e) {}
    try { (window as any).__shareOvCache = undefined; } catch (e) {}
    set('Annihilus', 'mule');                       // force it OUT of the shared stash
    const anniForcedOut = id('Annihilus');
    set("Gheed's Fortune", 'shared');               // force it INTO the shared stash
    const gheedForcedIn = id("Gheed's Fortune");
    set('Annihilus', 'auto');                        // back to the rule default
    set("Gheed's Fortune", 'auto');
    const anniAuto = id('Annihilus');
    const gheedAuto = id("Gheed's Fortune");
    try { localStorage.removeItem('d2r_vaultShareOverride'); } catch (e) {}
    try { (window as any).__shareOvCache = undefined; } catch (e) {}
    return { anniForcedOut, gheedForcedIn, anniAuto, gheedAuto };
  });
  // forced out: Annihilus leaves the shared stash for a real mule (his switch beats the ruling)
  expect(r.anniForcedOut, 'a forced-out Annihilus must leave the shared stash').not.toBe('shared');
  expect(['__keep', '__throwout', '__null', null, undefined, ''],
    'a forced-out Annihilus must land on a real mule').not.toContain(r.anniForcedOut);
  // forced in: Gheed's Fortune obeys the switch into the shared stash
  expect(r.gheedForcedIn, "a forced-in Gheed's Fortune must enter the shared stash").toBe('shared');
  // 'auto' restores the ruling defaults
  expect(r.anniAuto, 'auto restores Annihilus to the shared stash').toBe('shared');
  expect(r.gheedAuto, "auto restores Gheed's Fortune to its mule").toBe('charms');   // REG-2895, 2026-10-28
});
