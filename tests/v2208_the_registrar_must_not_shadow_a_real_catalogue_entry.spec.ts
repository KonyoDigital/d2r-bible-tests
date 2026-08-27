import { test, expect } from './_net_stub';
import * as path from 'path';

// v2208 — THE VAULT REGISTRAR WROTE A `rarity:'basic'` PLACEHOLDER OVER THREE REAL ITEMS.
//
// tvVaultRegister carries a "universe guarantee" (v739): anything TV registers must be DRAWABLE, so
// a name no catalogue knows gets a minimal EXTRA_ITEMS entry. The guarantee is right. The test for
// "no catalogue knows it" was asking three catalogues — ITEMS, d2rItemLookup, EXTRA_ITEMS — and the
// page has more. Measured on a real load, registering the seventeen names from tv/vault_seen.json:
//
//     Enigma      is in RUNEWORDS       -> got a stub
//     Obsession   is in RUNEWORDS       -> got a stub
//     Bone Break  is in SUNDER_CHARMS   -> got a stub
//
// ⚠ THE WITNESS WAS THE CARD, NOT THE DATA. `openDrop('Bone Break')` rendered
// `.gic-card.extra-item-card` where it had rendered `.gic-card.material-card`, so the sunder
// charm's rich card became a generic vault tile. The ARTWORK stayed correct the whole time —
// `art/bonebreakcharm_graphic.png` either way — which is precisely why every check of the form
// "does the picture load" stayed green. Two shipped specs (v71_d2art, v74_material_search) caught
// it and blocked the push.
//
// ⚠ AND THE FIX HAD TO BE TWO-SIDED, WHICH IS THE HALF WORTH PINNING. Teaching only the registrar
// to skip the stub DELETES Enigma on the next reload: the stub was the thing the load-time prune
// recognised. That is v2205/#48 one catalogue over. So the prune and the registrar now ask the SAME
// function, `window.d2rCatalogueKnows`, and this spec asserts both halves — no stub, AND it
// survives a reload — because either one alone reads as a fix and is not one.
// [[copy-drift]] [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// name -> the catalogue that already knows it. Not a hand-list: each was measured false in all
// three catalogues the registrar used to consult, and true in this one.
const SHADOWED: Record<string, string> = {
  Enigma: 'runeword',
  Obsession: 'runeword',
  'Bone Break': 'sunder',
};

test.describe('v2208 the registrar must not shadow a real catalogue entry', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('d2rCatalogueKnows names the catalogue, and is exposed for BOTH sides to share', async ({ page }) => {
    const r = await page.evaluate((names: string[]) => ({
      fn: typeof (window as any).d2rCatalogueKnows,
      says: names.map((n) => (window as any).d2rCatalogueKnows(n)),
      // a name no catalogue holds must come back false, or the predicate would keep everything and
      // the universe guarantee would never fire again
      unknown: (window as any).d2rCatalogueKnows('Totally Not A Real Item ZZZ'),
      empty: (window as any).d2rCatalogueKnows(''),
    }), Object.keys(SHADOWED));
    expect(r.fn, 'd2rCatalogueKnows is not exposed — the prune and the registrar cannot share it, '
      + 'and two copies of one question is how this defect happened').toBe('function');
    expect(r.says).toEqual(Object.values(SHADOWED));
    expect(r.unknown, 'the predicate answers TRUE for a name nothing knows — it would suppress the '
      + 'universe guarantee for every rolled item and they would all become undrawable').toBe(false);
    expect(r.empty).toBe(false);
  });

  test('registering a runeword or a sunder charm writes NO basic placeholder over it', async ({ page }) => {
    const r = await page.evaluate((names: string[]) => {
      const out: any = { before: {}, after: {}, ok: {} };
      for (const n of names) out.before[n] = !!(window as any).EXTRA_ITEMS?.[n];
      for (const n of names) {
        const res = (window as any).tvVaultRegister(n);
        out.ok[n] = !!(res && res.ok);
        const e = (window as any).EXTRA_ITEMS?.[n];
        out.after[n] = e ? { rarity: e.rarity, cat: e.cat } : null;
      }
      return out;
    }, Object.keys(SHADOWED));

    for (const n of Object.keys(SHADOWED)) {
      expect(r.before[n], `${n} already had an EXTRA_ITEMS entry before registering, so this test `
        + `cannot tell a suppressed stub from a pre-existing one`).toBe(false);
      expect(r.ok[n], `tvVaultRegister refused ${n} outright — it must still register, it just must `
        + `not invent a placeholder`).toBe(true);
      expect(r.after[n], `registering ${n} wrote ${JSON.stringify(r.after[n])} over a real `
        + `${SHADOWED[n]} entry. rarity:'basic' is the universe guarantee firing for an item the `
        + `page already knows, and it is what turned Bone Break's material card into a generic `
        + `vault tile.`).toBeNull();
    }
  });

  test("Bone Break's ID card is still the sunder MATERIAL card, not a generic vault tile", async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).tvVaultRegister('Bone Break');
      (window as any).openDrop('Bone Break');
      const panel = document.getElementById('item-detail');
      const img = panel?.querySelector('.material-card .gic-header .d2art-img') as HTMLImageElement | null;
      return {
        material: !!panel?.querySelector('.material-card'),
        extra: !!panel?.querySelector('.extra-item-card'),
        src: img?.getAttribute('src') || '',
      };
    });
    // ⚠ the art assertion is LAST and deliberately weakest: it was correct throughout the defect.
    expect(r.material, 'Bone Break rendered without a .material-card after being vaulted — the '
      + 'sunder charm was demoted to a generic extra-item tile').toBe(true);
    expect(r.extra, 'Bone Break rendered as .extra-item-card — that IS the demotion').toBe(false);
    expect(r.src).toMatch(/bonebreakcharm/);
  });

  test('a runeword put in the vault is still there after a reload', async ({ page }) => {
    // THE HALF THAT MAKES THE OTHER HALF SAFE. Without the matching prune clause, suppressing the
    // stub means the load-time prune no longer recognises Enigma and deletes it — a "fix" that
    // trades a wrong card for a missing item.
    await page.evaluate(() => {
      (window as any).tvVaultRegister('Enigma');
      (window as any).tvVaultRegister('Obsession');
      (window as any).tvVaultRegister('Bone Break');
    });
    const before = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('d2r_owned') || '[]') || []);
    for (const n of Object.keys(SHADOWED)) expect(before).toContain(n);

    // ⚠ AND CLEAR THE MULE FILING FIRST, because otherwise this test proves nothing. MEASURED: with
    // d2r_muleAssign left in place, deleting the prune's catalogue clause STILL passed — registering
    // a runeword files it to the `runewords` locker, and the prune's separate `_maKeep` clause
    // (v2128, "his own mule filing") was the thing keeping it. The assertion below claimed to
    // measure the catalogue clause and was measuring a different one.
    //
    // With the filing cleared and the clause removed, the same run reads
    // ["Enigma=false", "Obsession=false", "Bone Break=true"] — the two runewords die and the sunder
    // charm lives on _SHARED_KEEP, which is exactly the split the fix predicts.
    // [[feedback-blind-fixture-green-gate]] [[feedback-suspect-the-instrument]]
    await page.evaluate(() => localStorage.removeItem('d2r_muleAssign'));
    await page.reload();
    await page.waitForTimeout(1200);
    const after = await page.evaluate(() =>
      JSON.parse(localStorage.getItem('d2r_owned') || '[]') || []);
    for (const n of Object.keys(SHADOWED)) {
      expect(after, `"${n}" was in the vault and the load-time prune deleted it. It has no `
        + `EXTRA_ITEMS stub any more (correctly), so the prune must keep it by the same `
        + `d2rCatalogueKnows the registrar skipped the stub by. One side moved without the other.`)
        .toContain(n);
    }
  });

  test('the v2207 evidence restore does NOT run on a board that was never damaged', async ({ page }) => {
    // It shipped with no gate, so it put 22 items into every board that loads the page — a fresh
    // visitor's, and every test fixture's. A repair that runs where nothing was broken is the v2200
    // mistake with a different list.
    //
    // ⚠ THE SECOND LOAD IS THE POINT OF THIS TEST, and it is what failed the first gate I
    // wrote. The obvious marker — `d2r_vaultBackfill_v2200` — is stamped by the RETIRED
    // v2200 migration on every board, so it means "this page has loaded once", not "this board lost
    // items". Gating on it looked correct and simply moved the unwanted restore to load 2. A single
    // goto could never see that. [[label-outlived-referent]] [[feedback-blind-fixture-green-gate]]
    await page.reload();
    await page.waitForTimeout(1200);
    const fresh = await page.evaluate(() => ({
      ran: !!(window as any)._vaultEvidenceRestore_v2207,
      backfill: localStorage.getItem('d2r_vaultBackfill_v2200'),
    }));
    expect(fresh.backfill, 'the retired v2200 stopped stamping its flag — if that changed, the '
      + 'comment above is stale and this test no longer measures what it claims').not.toBeNull();
    expect(fresh.ran, 'the v2207 restore ran on an undamaged board on its SECOND load — it '
      + 'handed 22 items to someone who never lost any. The gate is asking a flag, not the damage.')
      .toBe(false);

    // and it MUST still fire where the damage really happened: an undo that dropped real names
    await page.evaluate(() => localStorage.setItem('d2r_vaultBackfillUndo_v2205',
      JSON.stringify({ at: 1, keptN: 5, droppedN: 383, dropped: [] })));
    await page.reload();
    await page.waitForTimeout(1200);
    const damaged = await page.evaluate(() =>
      ((window as any)._vaultEvidenceRestore_v2207 || {}).added || 0);
    expect(damaged, 'the restore did not fire on a board whose undo dropped 383 names — the '
      + 'gate is now refusing the one board it exists for').toBeGreaterThanOrEqual(20);
  });
});
