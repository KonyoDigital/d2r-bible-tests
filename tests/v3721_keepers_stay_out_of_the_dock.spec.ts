import { test, expect } from '@playwright/test';

// REG-2207 (#109 E#5) — Annihilus, Hellfire Torch and Gheed's Fortune route to __keep (they only work
// in the inventory of the character being played, so no mule holds them). With no stored assignment they
// fell into _dockNames() — the ONE list the dock display, Auto-Sort AND "Delete unsorted" all read — so a
// Delete-unsorted click removed three grail keepers from `owned` (data loss). Reproduced in headless
// Chrome: dock = [Annihilus, Gheed's Fortune, Hellfire Torch]. They are keepers by NAME, not by a filing,
// so _dockNames now excludes KEEP_IN_INVENTORY and renderVaultRegistered counts them as kept.
//
// V0 spec refresh (#176, GrokBot triage 2026-10-22) — two premises of this spec expired, neither a defect:
//   1. REG-2241, HIS RULING 2026-10-15 (verbatim): "torches and anni stay in shared. gheeds gets muled."
//      suggestMule no longer answers __keep for them: Annihilus and Hellfire Torch take the explicit shared
//      branch (bible.html suggestMule, `if (_ov !== 'mule' && /^(Annihilus|Hellfire Torch)$/i ...)
//      return {id:'shared'...}`) and Gheed's Fortune falls through to its grand-charm mule, uni-small
//      ("jewelry/charm — base: Grand Charm"). The dock seam (_vaultSeamHome) now reads that router home
//      while assign is still null — Annihilus and the Torch as 'shared', Gheed's as filed on uni-small — so
//      _dockNames leaves all three out before its KEEP_IN_INVENTORY test is reached; that test stays as the
//      backstop for a keeper whose seam reads loose (a chronicle-only row). The data-loss half this spec
//      guards is unchanged: no keeper is on the list "Delete unsorted" removes.
//   2. REG-2290 (v3767, his 2026-10-18 rule): AUTO INTAKE is OFF until he turns it on, and while it is off
//      tvVaultRegister registers nothing ({refused:'auto-intake-off'}). Measured on the merged V1 tree: none
//      of the three was owned, so "the dock holds none of them" was true of an empty vault and proved
//      nothing. The switch is turned on here, the three are asserted OWNED first, and a control the router
//      cannot home (Blood Shield — a real RotW find no catalogue names, v1958's own example) proves the dock
//      list is live. Then the real door runs: Delete unsorted (window.vaultClearUnsorted, which removes
//      exactly _dockNames()) takes the control and leaves every keeper owned.
//
// Case 2 — THE BACKSTOP ITSELF. Case 1's keepers are homed by the router, so _dockNames drops them at the seam and
// never reaches the REG-2207 line (bible.html _dockNames, inside `if (_seamD && _seamD.loc === 'loose')`:
// `if (typeof KEEP_IN_INVENTORY !== 'undefined' && typeof _keepName === 'function' && KEEP_IN_INVENTORY.test(_keepName(n))) return false;`).
// Case 1 stays green with that line deleted (review of r3c, measured). That line is the ONLY thing that keeps a keeper
// with a loose seam out of the dock, and a keeper whose only provenance is a Chronicle read IS loose:
// _vaultSeamHome answers {loc:'loose'} for a Chronicle-only provenance row (_isChronicleOnlyRow, "v3767 seam
// chronicle") before it asks the router. Case 2 owns the three keepers that way — owned + a Chronicle-only
// _ownedProvWrite row, the seeding v203's v226 case and v327 use for Obedience — and pins every link: the seam reads
// loose (so the case reaches the backstop), the dock holds none of them, and Delete unsorted keeps all three owned.
// A Chronicle-only Obedience is the control: loose, in the dock, and taken by the door, so the dock and the door are
// both live. Measured with the backstop line deleted: dock = all three keepers, and Delete unsorted un-owns them.

const KEEPERS = ['Annihilus', 'Hellfire Torch', 'Gheed’s Fortune']; // Gheed's with a CURLY apostrophe (REG-2191)
/* where his 2026-10-15 ruling sends each one (REG-2241) */
const RULED: Record<string, string> = { 'Annihilus': 'shared', 'Hellfire Torch': 'shared', 'Gheed’s Fortune': 'uni-small' };
/* a name no catalogue knows: suggestMule answers {id:null, unsorted:true}, so it is loose in the dock */
const CONTROL = 'Blood Shield';
/* case 2's control: read only off a Chronicle page (his §28 ruling - found once, not held), so it has no home and is the
   dock chip (v203 v226, v327) */
const CHRONICLE_CONTROL = 'Obedience';

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._vaultDockNames && (window as any).tvVaultRegister && (window as any).renderVault
    && (window as any).suggestMule && (window as any)._vaultAutoIntakeSet && (window as any).vaultClearUnsorted);
});

test('a keep-in-inventory charm is never in the unsorted dock (so Delete-unsorted cannot remove it)', async ({ page }) => {
  const r = await page.evaluate(async ({ keepers, control }: { keepers: string[]; control: string }) => {
    const w = window as any;
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    const ai = w._vaultAutoIntakeSet(true);                       // REG-2290: the TV register reads nothing while off
    keepers.concat([control]).forEach(n => { try { w.tvVaultRegister(n); } catch (e) {} });
    w.renderVault();
    const fold = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();
    const ownedNow = (): string[] => Array.from(eval('owned') as Set<string>).map(fold);
    const ownedBefore = keepers.concat([control]).map(n => ownedNow().indexOf(fold(n)) >= 0);
    const dock: string[] = (w._vaultDockNames() || []).slice();
    const sg: Record<string, string> = {};
    keepers.forEach(n => { const s = w.suggestMule(n); sg[n] = s && s.id; });
    // the dock must hold NONE of the three keepers (match by apostrophe-folded name)
    const dockFolded = dock.map(fold);
    const leaked = keepers.filter(n => dockFolded.indexOf(fold(n)) >= 0);
    // the door the dock list feeds: Delete unsorted removes exactly _dockNames() from owned (journaled)
    w.uiConfirm = () => Promise.resolve(true);
    await w.vaultClearUnsorted();
    const ownedAfter = keepers.concat([control]).map(n => ownedNow().indexOf(fold(n)) >= 0);
    return { aiOn: !!(ai && ai.on), ownedBefore, dock, leaked, sg, ownedAfter };
  }, { keepers: KEEPERS, control: CONTROL });
  // premises — without them every assertion below is about an empty vault
  expect(r.aiOn, 'AUTO INTAKE did not turn on — tvVaultRegister would register nothing (REG-2290)').toBe(true);
  expect(r.ownedBefore, 'the three keepers and the control must be OWNED before the dock is read').toEqual([true, true, true, true]);
  expect(r.dock, 'the dock list is live: the name the router cannot home is in it').toContain(CONTROL);
  // identity: each routes where he ruled (REG-2241)
  for (const n of KEEPERS) expect(r.sg[n], `${n} must route to ${RULED[n]} (his 2026-10-15 ruling)`).toBe(RULED[n]);
  // the data-loss guard: none of them is in the dock list Delete-unsorted reads
  expect(r.leaked, 'a keeper leaked into the unsorted dock — Delete-unsorted would nuke it').toEqual([]);
  // and the door itself: it removed the loose control and no keeper
  expect(r.ownedAfter, 'Delete unsorted must take the loose control and keep all three keepers owned').toEqual([true, true, true, false]);
});

test('a keeper owned only through a Chronicle read reaches the REG-2207 backstop and still never enters the dock', async ({ page }) => {
  await page.waitForFunction(() => (window as any)._ownedProvWrite && (window as any)._vaultSeamHome);
  const r = await page.evaluate(async ({ keepers, control }: { keepers: string[]; control: string }) => {
    const w = window as any;
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    const names = keepers.concat([control]);
    // owned, with a provenance row whose every look is the game's Chronicle page (the v203 v226 / v327 seeding)
    const wrote = names.map((n, i) => {
      (eval('owned') as Set<string>).add(n);
      const res = w._ownedProvWrite(n, { source: 'intake-read', by: 'law', holder: 'Chronicle', loc: 'chronicle', scene: 'chronicle',
        sessionId: 's-chron-' + i, frameId: 'f-chron-' + i, ts: Date.now() });
      return !!(res && res.ok);
    });
    w.renderVault();
    const fold = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();
    const ownedNow = (): string[] => Array.from(eval('owned') as Set<string>).map(fold);
    const ownedBefore = names.map(n => ownedNow().indexOf(fold(n)) >= 0);
    const seam: Record<string, string | null> = {};
    names.forEach(n => { const s = w._vaultSeamHome(n); seam[n] = s ? s.loc : null; });
    const dock: string[] = (w._vaultDockNames() || []).slice();
    const dockFolded = dock.map(fold);
    const leaked = keepers.filter(n => dockFolded.indexOf(fold(n)) >= 0);
    w.uiConfirm = () => Promise.resolve(true);
    await w.vaultClearUnsorted();
    const ownedAfter = names.map(n => ownedNow().indexOf(fold(n)) >= 0);
    return { wrote, ownedBefore, seam, dock, leaked, ownedAfter };
  }, { keepers: KEEPERS, control: CHRONICLE_CONTROL });
  // premises — the rows were written and the names owned, and every seam reads loose, so _dockNames reaches the backstop
  expect(r.wrote, 'every Chronicle-only provenance row was written').toEqual([true, true, true, true]);
  expect(r.ownedBefore, 'the three keepers and the control must be OWNED before the dock is read').toEqual([true, true, true, true]);
  for (const n of KEEPERS.concat([CHRONICLE_CONTROL]))
    expect(r.seam[n], `PREMISE: ${n} has a Chronicle-only provenance row, so its dock seam is loose and only the REG-2207 line stands between it and the dock`).toBe('loose');
  expect(r.dock, 'the dock list is live: the Chronicle-only control is in it').toContain(CHRONICLE_CONTROL);
  // the data-loss guard: the backstop keeps every keeper out of the list Delete unsorted reads
  expect(r.leaked, 'a Chronicle-only keeper leaked into the unsorted dock — Delete unsorted would un-own it').toEqual([]);
  // and the door: it took the loose control and no keeper
  expect(r.ownedAfter, 'Delete unsorted must take the Chronicle-only control and keep all three keepers owned').toEqual([true, true, true, false]);
});
