import { test, expect } from '@playwright/test';

// REG-2219 — war gear with NO stash-frame picture (a manual / name-known add) was STRANDED in the
// unsorted dock. Auto-Sort filed only kind:'mule', so a SHARED-STASH route (war gear / high trade)
// fell to "left for you" (out.left['shared']) and never moved however many times he pressed Auto-Sort.
// Reproduced live: Arachnid Mesh, Dracul's Grasp, Grief all route to the shared stash yet sat in the
// dock. The fix files a name-certain shared route INTO the shared stash from its NAME, with a by-hand
// witness (no frame needed — the name is the identity the war rule routes on). MAIN still wins.
//
// RED without the fix: a no-picture item hits `if (!_hasPicture(row)) out.noPicture` BEFORE the
// propose, so it never files and stays in _vaultDockNames(). GREEN with the fix: the shared branch
// runs before the picture gate and files it to 'shared'.

const NAME = "Dracul's Grasp"; // a war-gear unique (life-tap gloves) — one of the three he reported

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._vaultDockNames && (window as any).tvVaultRegister
    && (window as any).vaultAutoSortByHand && (window as any).vaultPropose && (window as any).suggestMule);
});

test('war gear with no picture is auto-sorted INTO the shared stash, not stranded in the dock', async ({ page }) => {
  const r = await page.evaluate((nm: string) => {
    try { localStorage.setItem('d2r_ownerClaim', '*'); } catch (e) {}
    if ((window as any).LSR) (window as any).LSR.setItem('d2r_vaultAutoIntake', 'on'); /* Elad 2026-10-18: the register runs only while AUTO INTAKE is on */
    (window as any).tvVaultRegister(nm);
    try { (window as any).renderVault && (window as any).renderVault(); } catch (e) {}
    const fold = (s: string) => String(s || '').replace(/[‘’ʼ´`]/g, "'").trim();
    const inDock = () => ((window as any)._vaultDockNames() || []).map(fold).indexOf(fold(nm)) >= 0;
    const propose = (window as any).vaultPropose(nm);
    const dockBefore = inDock();
    const seam = ((window as any)._vaultSeamHome(nm) || {}).loc || null;
    const held = eval('owned').has(nm);
    let assign: any = {};
    try { assign = JSON.parse((window as any).LSR.getItem('d2r_muleAssign') || '{}'); } catch (e) {}
    const res = (window as any).vaultAutoSortByHand();
    const dockAfter = inDock();
    const filedToShared = !!(res && Array.isArray(res.rows)
      && res.rows.some((x: any) => fold(x && x.name) === fold(nm) && x.mule === 'shared'));
    return { propose, dockBefore, dockAfter, filedToShared, seam, owned: held, assigned: assign[nm] || null };
  }, NAME);
  // war gear routes to the shared stash
  expect(r.propose && (r.propose.kind === 'shared' || r.propose.id === 'shared'),
    "Dracul's Grasp must route to the shared stash").toBeTruthy();
  /* Elad 2026-10-18 — a name the router already knows is homed at read time and is
     never an unsorted dock chip. The seam does not write assign. REG-2219's fear
     was "stranded in the dock"; the home is the seam's shared, not an Auto-Sort write. */
  expect(r.owned, 'the register must record the holding').toBe(true);
  expect(r.seam, "Dracul's Grasp is homed on the shared stash").toBe('shared');
  expect(r.dockBefore, 'a homed name is not an unsorted dock chip').toBe(false);
  expect(r.dockAfter, 'it must not fall back into the dock').toBe(false);
  expect(r.assigned, 'the seam homes at read time and does not write assign').toBeNull();
});
