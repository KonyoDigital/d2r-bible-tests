import { test, expect } from '@playwright/test';

// REG-2228 / #109 (#2) — ONE ADD IS ONE RECORD, even for a kind-ambiguous name.
//
// In Reign of the Warlock "Crescent Moon" names TWO known items: the RUNEWORD (in RUNEWORDS) and the
// unique AMULET (in ITEMS, via the boss drop-table registry, as "Crescent Moon (amulet)"). The Vault
// planner resolved a pick's name with _vaultResolveName alone, which deliberately PUNTS on a
// _vaultDistinctName and leaves the bare name as it is. vaultHandAdd settles by the pick's kind and so
// OWNED "Crescent Moon (amulet)", but the very next _vpRoute routed the still-bare "Crescent Moon" —
// itself a runeword — to the runewords mule: one add, two records, a phantom runeword filing. The fix
// settles the bare name by the pick's kind BEFORE resolving, exactly as tvVaultRegister already does,
// so the add, the route and _vpMade all speak the one name vaultHandAdd commits.
//
// RED (no fix): the bare "Crescent Moon" is filed to the runewords mule — d2r_muleAssign['Crescent Moon'].
// GREEN (fix):  the bare name is never filed; the only record is "Crescent Moon (amulet)".

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => {
    const w = window as any;
    return !!(w.vaultPlannerFile && w.suggestMule && w._vaultNameAmbiguity &&
              w._vaultResolveName && w.vaultHandAdd && w.LSR);
  });
});

test('a planner add of the kind-ambiguous Crescent Moon files one record, not a phantom runeword', async ({ page }) => {
  // The fixture is REAL: the catalog carries both items, so the name is genuinely kind-ambiguous.
  // (Pins the catalog — a renamed item fails this loudly instead of passing silently.)
  const pre = await page.evaluate(() => {
    const w = window as any;
    const sm = w.suggestMule('Crescent Moon');
    const amb = w._vaultNameAmbiguity('Crescent Moon', { kind: 'unique' });
    return { route: sm && sm.id, settled: amb && amb.settled, bare: w._vaultResolveName('Crescent Moon') };
  });
  expect(pre.route, 'the bare name is itself a runeword route').toBe('runewords');
  expect(pre.settled, 'the pick kind settles the bare name to the amulet').toBe('Crescent Moon (amulet)');
  expect(pre.bare, '_vaultResolveName alone leaves the distinct ambiguous name bare').toBe('Crescent Moon');

  // Drive the planner file as a UNIQUE pick whose shown name is the bare "Crescent Moon".
  const out = await page.evaluate(() => {
    const w = window as any;
    w._cbItem = () => ({});
    w._cbShown = () => ({ name: 'Crescent Moon', q: 'u' });
    w._vaultPlannerOn = true; // skip the vault re-render in a headless DOM; the filing is already saved
    const r = w.vaultPlannerFile({ id: 'cm-amulet-109', affixes: [] }, 'tok-109');
    const get = (k: string) => {
      try { return w.LSR.getItem(k); } catch (e) {
        try { return localStorage.getItem(k); } catch (e2) { return null; }
      }
    };
    let owned: string[] = [], assign: Record<string, any> = {};
    try { owned = JSON.parse(get('d2r_owned') || '[]'); } catch (e) {}
    try { assign = JSON.parse(get('d2r_muleAssign') || '{}'); } catch (e) {}
    return { why: (r && r.why) || '', owned, assign };
  });

  // THE FIX, the RED->GREEN line: the bare name is never filed — no phantom runeword record.
  expect(out.assign['Crescent Moon'], 'no bare-name phantom filing (RED files it to "runewords")').toBeFalsy();

  // One record, under the kind-settled name — the bare name is never a second owned row.
  expect(out.owned, 'the amulet is owned under its disambiguated name').toContain('Crescent Moon (amulet)');
  expect(out.owned, 'the bare name is not a second owned record').not.toContain('Crescent Moon');
});
