import { test, expect } from '@playwright/test';

// REG-2207 (#109 E#5) — Annihilus, Hellfire Torch and Gheed's Fortune route to __keep (they only work
// in the inventory of the character being played, so no mule holds them). With no stored assignment they
// fell into _dockNames() — the ONE list the dock display, Auto-Sort AND "Delete unsorted" all read — so a
// Delete-unsorted click removed three grail keepers from `owned` (data loss). Reproduced in headless
// Chrome: dock = [Annihilus, Gheed's Fortune, Hellfire Torch]. They are keepers by NAME, not by a filing,
// so _dockNames now excludes KEEP_IN_INVENTORY and renderVaultRegistered counts them as kept.

const KEEPERS = ['Annihilus', 'Hellfire Torch', 'Gheed’s Fortune']; // Gheed's with a CURLY apostrophe (REG-2191)

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._vaultDockNames && (window as any).tvVaultRegister && (window as any).renderVault && (window as any).suggestMule);
});

test('a keep-in-inventory charm is never in the unsorted dock (so Delete-unsorted cannot remove it)', async ({ page }) => {
  const r = await page.evaluate((keepers: string[]) => {
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    keepers.forEach(n => { try { (window as any).tvVaultRegister(n); } catch (e) {} });
    (window as any).renderVault();
    const dock: string[] = (window as any)._vaultDockNames() || [];
    const sg: Record<string, string> = {};
    keepers.forEach(n => { const s = (window as any).suggestMule(n); sg[n] = s && s.id; });
    // the dock must hold NONE of the three keepers (match by apostrophe-folded name)
    const fold = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();
    const dockFolded = dock.map(fold);
    const leaked = keepers.filter(n => dockFolded.indexOf(fold(n)) >= 0);
    return { dock, leaked, sg };
  }, KEEPERS);
  // REG-2241 (his ruling 2026-10-15: "torches and anni stay in shared. gheeds gets muled") — the three no
  // longer route to __keep: Anni + Torch file to the SHARED stash, Gheed's to its grand-charm mule. The
  // data-loss guard below is unchanged: none of them may sit in the dock Delete-unsorted reads.
  expect(r.sg['Annihilus'], 'Annihilus rides in the shared stash').toBe('shared');
  expect(r.sg['Hellfire Torch'], 'the Torch rides in the shared stash').toBe('shared');
  expect(r.sg['Gheed’s Fortune'], "Gheed's is muled to its charm mule").toBe('uni-small');
  // the data-loss guard: none of them is in the dock list Delete-unsorted reads
  expect(r.leaked, 'a keeper leaked into the unsorted dock — Delete-unsorted would nuke it').toEqual([]);
});
