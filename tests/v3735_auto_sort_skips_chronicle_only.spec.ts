import { test, expect } from '@playwright/test';

// REG-2223 (#131, review-after-ship on REG-2219) — Auto-Sort's new SHARED branch filed a name to the
// shared stash from the war rule (which routes on the NAME), BEFORE asking whether he actually HOLDS it.
// A row whose only evidence is a Chronicle found-ever tick (he saw it once — d2r-bible §6: his ledger is
// testimony, not state) then landed in the shared stash as a held spare. The fix blocks the shared filing
// when the row is chronicle-ONLY (every look loc/scene === 'chronicle') and not his hand; it falls to
// "no picture" instead, the same gate a mule CELL already stops on.
//
// The seed is faithful: window._ownedAdd (the ONE owned door) writes a kind:'owned' RECEIPT whose look
// carries loc:'chronicle' — exactly what a Chronicle apply produces (bible.html:21158). A frameless
// register (REG-2219's name-only war gear) writes looks:[] — so _isChronicleOnlyRow is FALSE for it and
// it STILL files. That second item is the no-regression guard for v3731.
//
// RED without the fix: the chronicle-only item is vaultFile'd to shared (appears in res.rows, leaves the
// dock). GREEN with the fix: it is in res.noPicture, never res.rows, and stays in the dock — while the
// holding war gear still files to shared.

const CHRON = 'Arachnid Mesh';     // a war-gear unique — routes to the shared stash
const HOLD  = "Dracul's Grasp";    // same shared route, but a real holding (v3731's case)
const fold = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._vaultDockNames && (window as any)._ownedAdd
    && (window as any).tvVaultRegister && (window as any).vaultAutoSortByHand && (window as any).vaultPropose);
});

test('Auto-Sort does NOT file a chronicle-only found-ever tick to the shared stash, but STILL files held war gear (REG-2223)', async ({ page }) => {
  const r = await page.evaluate(({ chron, hold }) => {
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    if ((window as any).LSR) (window as any).LSR.setItem('d2r_vaultAutoIntake', 'on'); /* Elad 2026-10-18: the holding's register runs only while AUTO INTAKE is on */
    // (1) a chronicle-ONLY found-ever tick — one look, loc/scene 'chronicle', no holding picture
    (window as any)._ownedAdd(chron, { source: 'chronicle-apply', by: 'chronicle', loc: 'chronicle',
      scene: 'chronicle', frameId: 'f_chron_1', sessionId: 's_test_chron', at: Date.now() });
    // (2) a real holding, name-only (no frame) — REG-2219's war gear; looks:[] so it is NOT chronicle-only
    (window as any).tvVaultRegister(hold);
    try { (window as any).renderVault && (window as any).renderVault(); } catch (e) {}

    const foldJS = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();
    const dock = () => ((window as any)._vaultDockNames() || []).map(foldJS);
    const inDock = (n: string) => dock().indexOf(foldJS(n)) >= 0;
    const looksChron = (() => {
      try {
        const row = (window as any)._vaultProvAll()[chron] || {};
        const ls = Array.isArray(row.looks) ? row.looks : [];
        return { kind: row.kind, count: ls.length,
          allChronicle: ls.length > 0 && ls.every((e: any) =>
            String((e && e.loc) || '').toLowerCase() === 'chronicle' || String((e && e.scene) || '').toLowerCase() === 'chronicle') };
      } catch (e) { return { kind: null, count: -1, allChronicle: false }; }
    })();

    const proposeChron = (window as any).vaultPropose(chron);
    const proposeHold = (window as any).vaultPropose(hold);
    const dockChron0 = inDock(chron);
    const dockHold0 = inDock(hold);
    const seamHold = (((window as any)._vaultSeamHome(hold) || {}).loc) || null;
    const holdOwned = eval('owned').has(hold);

    const res = (window as any).vaultAutoSortByHand() || {};
    const rows = Array.isArray(res.rows) ? res.rows : [];
    const noPic = (Array.isArray(res.noPicture) ? res.noPicture : []).map(foldJS);
    const filedToShared = (n: string) => rows.some((x: any) => foldJS(x && x.name) === foldJS(n) && x.mule === 'shared');

    return {
      looksChron, proposeChron, proposeHold, dockChron0, dockHold0, seamHold, holdOwned,
      chronFiled: filedToShared(chron), chronNoPicture: noPic.indexOf(foldJS(chron)) >= 0, chronStillInDock: inDock(chron),
      holdFiled: filedToShared(hold),
    };
  }, { chron: CHRON, hold: HOLD });

  // both route to the shared stash by the war rule
  const routesShared = (p: any) => !!(p && p.ok === true && (p.kind === 'shared' || p.id === 'shared'));
  expect(routesShared(r.proposeChron), `${CHRON} must route to the shared stash`).toBe(true);
  expect(routesShared(r.proposeHold), `${HOLD} must route to the shared stash`).toBe(true);

  // the seed is faithful: the chronicle item is a kind:'owned' receipt whose looks are all chronicle
  expect(r.looksChron.kind, 'the chronicle item is a kind:owned receipt').toBe('owned');
  expect(r.looksChron.allChronicle, 'its looks are all chronicle (found-ever, not a holding picture)').toBe(true);

  // the chronicle-only tick is homeless testimony, so it starts in the dock
  expect(r.dockChron0, `${CHRON} should start in the dock`).toBe(true);
  /* Elad 2026-10-18 — the holding is a name the router already knows. It is homed
     on shared at read time and is not an unsorted dock chip. */
  expect(r.holdOwned, `${HOLD} must be recorded`).toBe(true);
  expect(r.seamHold, `${HOLD} is homed on the shared stash`).toBe('shared');
  expect(r.dockHold0, `${HOLD} is homed, so it does not start in the dock`).toBe(false);

  // REG-2223: the chronicle-ONLY tick is NOT filed to shared — it goes to noPicture and stays in the dock
  expect(r.chronFiled, `${CHRON} (chronicle-only) must NOT be filed to the shared stash`).toBe(false);
  expect(r.chronNoPicture, `${CHRON} must fall to "no picture"`).toBe(true);
  expect(r.chronStillInDock, `${CHRON} must stay in the dock`).toBe(true);

  /* The holding is already homed by the seam, which does not write assign, so
     Auto-Sort (it walks the dock) has nothing to file. The regression guard is
     the seam home above, not a second write into the mule map. */
  expect(r.holdFiled, `${HOLD} is already homed — Auto-Sort must not need a dock filing`).toBe(false);
});
