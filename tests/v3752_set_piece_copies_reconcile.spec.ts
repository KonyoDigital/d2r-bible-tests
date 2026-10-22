import { test, expect } from '@playwright/test';

// #76 (phase 3) — SET-PIECE RECONCILE folds a duplicate NAME-FORM into one, keeping the larger copy count,
// and NEVER clamps/deletes a real count. GrokBot read his live board on v3751 (#230): the name-fold shipped
// but the copies remained — SETS-REST Mule 2 still drew FOUR Natalya's Totem cells (1 bare + 3 "(helm)"),
// because the mule draws one cell per copy (copyCount reads d2r_copies) and two intake paths (processFile
// "this item, not the pool"; the _vpCopySeen/token path) climbed an already-filed item's count on every
// re-read. v3752: (a) canonicalize set-piece names at intake + guard BOTH re-read bumps so a presence set
// piece stops auto-inflating (the permanent fix; genuine multiples ride the keep-target), (b) the reconcile
// folds the bare into its canonical slotted name and carries the copy count by MAX (same physical item under
// two names -> the larger, never the sum, never reduced). It does NOT clamp to 1: he may own 2+, and nothing
// in the console's ledgers can see a STASHED spare separate from this count, so the TRUE count is his to
// confirm (the multi-keep recount control). Apostrophe-robust so an OCR curly apostrophe still matches.
// RED (before v3752): no fold of the copy across name-forms; the guards were absent; curly never matched.
// Verified on the REAL page via CDP (4 cases) and against GrokBot's live v3751 read.
// [[the-unjoined-end]] [[unknown-stays-unknown]] [[manual-tally-is-witness]] [[d2r-curly-apostrophe-class]]

const URL = 'file://' + process.cwd() + '/bible.html';
const BARE = "Natalya's Totem", HELM = "Natalya's Totem (helm)", CURLY = "Natalya’s Totem", RAVEN = 'Raven Frost';

/* V0 spec refresh (#176, GrokBot triage: "the load-time fold consumes the seed") — the boot render runs the
   REG-2229 one-time migration window._vaultDedupeOldSetRows BEFORE any test code: a LOOSE owned set piece whose
   twin is FILED leaves owned through vaultRemove (lane 'set-dupe-migration'). Measured on the merged V1 tree:
   the curly seed's loose "Natalya’s Totem" was already removed at boot, so the reconcile under test had nothing to
   fold. That migration ran ONCE on his world, long ago (v3742); this fixture is that world — it carries the stamp
   d2r_setDupeMigrate_v2227, so the seed reaches _setPieceReconcile exactly as a new split would. (The other cases
   here seed no loose twin of a filed piece, so the migration never touched them; the stamp changes nothing there.)
   Not a regression: on the v3752 page itself (measured in node) the same boot migration consumed the curly seed —
   red from the day it was written.
   The page also runs _setPieceReconcile({}) itself, 1.5 s after load (_seedCleanseArm); on a slow runner that pass
   can fold the seed before the test's forced pass (the race #184 measured on a CI retry for v3753). So the fixture
   says that pass already ran too (a receipt no version outranks): only the test's forced pass folds. The same
   callback first runs the one-time seed cleanse, which removes an unfiled grail-seed name with no receipt (Raven
   Frost, in these seeds) — so its receipt, d2r_seedCleanse, is stamped as already run as well. */
async function seedLoad(page: any, owned: string[], assign: any, copies: any) {
  await page.addInitScript(({ owned, assign, copies }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_setPieceReconcile', JSON.stringify({ ver: 1e9, by: 'spec' }));   // the load-time pass: already ran
      localStorage.setItem('d2r_seedCleanse', JSON.stringify({ ver: 1e9, by: 'spec' }));         // the seed cleanse in that callback: already ran
      localStorage.setItem('d2r_setDupeMigrate_v2227', String(Date.now()));                     // REG-2229 already ran on this world
    } catch (e) {}
    try { if (!Object.getOwnPropertyDescriptor(navigator, 'webdriver')) Object.defineProperty(navigator, 'webdriver', { get: () => true }); } catch (e) {}
  }, { owned, assign, copies });
  await page.goto(URL);
  await page.waitForFunction(() => {
    const w = window as any;
    return w._setPieceReconcile && w._vfCanon && w._vfIsSetPiece && w.ownedPool && w.vaultRemove;
  });
}

async function run(page: any) {
  return await page.evaluate((K: any) => {
    const w = window as any;
    const res = w._setPieceReconcile({ force: true });
    const after = w.ownedPool().filter((n: string) => /Natalya|Raven/.test(n));
    let cp: any = {}; try { cp = JSON.parse(localStorage.getItem('d2r_copies') || '{}'); } catch (e) {}
    const rc = (res && res.receipt) || {};
    return {
      folded: res.folded || [], copiesFolded: res.copiesFolded || [], stamped: res.stamped,
      copiesPrior: rc.copiesPrior || {}, after,
      cpHelm: cp[K.helm], cpBare: cp[K.bare], cpCurly: cp[K.curly], cpRaven: cp[K.raven],
      canonCurly: w._vfCanon(K.curly), isSetHelm: w._vfIsSetPiece(K.helm), isSetRaven: w._vfIsSetPiece(K.raven),
      restorable: typeof w.vaultRestoreLast === 'function',
    };
  }, { helm: HELM, bare: BARE, curly: CURLY, raven: RAVEN });
}

test('folds a set-piece name-split into one name, keeping the LARGER copy count — never clamps (#76)', async ({ page }) => {
  // his board: bare + slotted BOTH filed, copies[helm] = 3. Fold to one name; keep MAX(1,3)=3, do NOT cut to 1.
  await seedLoad(page, [BARE, HELM, RAVEN], { [BARE]: 'sets-rest', [HELM]: 'sets-rest' }, { [HELM]: 3, [BARE]: 1 });
  const r = await run(page);
  expect(r.folded).toEqual([BARE]);                 // the bare name folded away
  expect(r.after).toContain(HELM);                  // canonical slotted stays
  expect(r.after).not.toContain(BARE);              // bare gone -> one name
  expect(r.cpHelm).toBe(3);                          // count kept at MAX(1,3) — NOT clamped to 1 (his real count is his)
  expect(r.cpBare).toBeUndefined();                  // the folded form's dangling copies dropped
  expect(r.copiesFolded).toContain(BARE);
  expect(r.copiesPrior[BARE]).toBe(1);               // prior kept in the receipt
  expect(r.stamped).toBe(true);
  expect(r.restorable).toBe(true);                   // journaled / undoable
});

test('leaves a lone slotted set piece UNTOUCHED — no clamp without a name-split (#76)', async ({ page }) => {
  // pure count, no duplicate name-form: nothing to fold, and the count must NOT be auto-reduced
  await seedLoad(page, [HELM, RAVEN], { [HELM]: 'sets-rest' }, { [HELM]: 3 });
  const r = await run(page);
  expect(r.folded).toEqual([]);                      // nothing folded
  expect(r.copiesFolded).toEqual([]);
  expect(r.cpHelm).toBe(3);                          // LEFT at 3 — the reconcile never clamps a real count
});

test('folds a curly-apostrophe bare form, keeping the larger count — apostrophe-robust (#76)', async ({ page }) => {
  await seedLoad(page, [CURLY, HELM, RAVEN], { [HELM]: 'sets-rest' }, { [HELM]: 2, [CURLY]: 1 });
  const r = await run(page);
  expect(r.canonCurly).toBe(HELM);                   // _vfCanon folds curly -> straight slotted
  expect(r.folded).toEqual([CURLY]);
  expect(r.after).not.toContain(CURLY);
  expect(r.cpHelm).toBe(2);                          // MAX(1,2)
  expect(r.cpCurly).toBeUndefined();
});

test('does NOT touch a non-set-piece with copies>1 — scope is KNOWN set pieces only (#76)', async ({ page }) => {
  await seedLoad(page, [RAVEN], {}, { [RAVEN]: 3 });
  const r = await run(page);
  expect(r.cpRaven).toBe(3);                          // untouched
  expect(r.copiesFolded).not.toContain(RAVEN);
  expect(r.isSetHelm).toBe(true);                     // predicate the guards + fold rely on
  expect(r.isSetRaven).toBe(false);
});

/* V0 spec refresh (#176) — this was a SOURCE tripwire on the two re-read copy-bump statements, and both anchors
   expired; neither is a regression:
     · processFile (the photo intake) no longer HAS a copy-bump for a presence item. Since v3767 (REG-2290, his
       2026-10-18 rule "a presence re-read is +1 witness") a re-read asks window._vaultRereadKind, which answers
       'witness' when the keep-target is <= 1 — "copies[] is not climbed here" — and only a multi-keep under its
       target or a socketed base under its cap is 'copy'. The regex for the old statement matched nothing.
     · the planner's _vfIsSetPiece guard is now a NESTED condition (so the outer `if` line stays byte-identical to
       another law's red-proof anchor), so the one-line regex captured a line that no longer carries it.
   The property is re-anchored on the PUBLIC DOORS that perform each bump, and each door gets a control proving it
   CAN still climb — so a dropped guard turns these red, and so does a bump that went dead. Both measured on the
   merged V1 tree in node: two re-reads / two re-picks leave the helm at 1; the controls file copy 2. */
const JPG_1PX = '/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==';

test('a photo re-read of an owned presence set piece adds a witness, never a copy; a wanted spare still climbs (#76)', async ({ page }) => {
  // the AI read of every photo here is the BARE chronicle name; the intake folds it to the slotted vault key
  await page.route('**/api/intake', (route) => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ items: [BARE], unrecognized: [], usage: { in: 700, out: 20, cached: 0 } }),
  }));
  await seedLoad(page, [HELM], { [HELM]: 'sets-rest' }, {});
  const r = await page.evaluate(async (K: any) => {
    const w = window as any;
    localStorage.setItem('d2r_intakeUrl', 'https://intake.test/api/intake');
    w._vaultAutoIntakeSet(true);                 // REG-2290: the photo door registers nothing while AUTO INTAKE is off
    const gate = w._vaultIntakeGate();
    const read = async (name: string) => {
      const bytes = Uint8Array.from(atob(K.jpg), (c: string) => c.charCodeAt(0));
      return w.vaultIntake([new File([bytes], name, { type: 'image/jpeg' })]);
    };
    const cp = () => { try { return JSON.parse(localStorage.getItem('d2r_copies') || '{}'); } catch (e) { return {}; } };
    await read('reread_a.jpg');
    await read('reread_b.jpg');
    const presence = { copies: cp()[K.helm], helmOwned: eval('owned').has(K.helm), bareOwned: eval('owned').has(K.bare) };
    const kinds = { presence: w._vaultRereadKind(K.helm, { tgt: 1, cur: 1, qtyBase: false }),
                    wanted: w._vaultRereadKind(K.helm, { tgt: 3, cur: 1, qtyBase: false }) };
    // control: he asks for spares of it (the Multi-copy Keepers "+ Add" box) — the SAME door now files a copy
    let inp: any = document.getElementById('vmk-add-input');
    if (!inp) { inp = document.createElement('input'); inp.id = 'vmk-add-input'; document.body.appendChild(inp); }
    inp.value = K.bare;
    w.vaultMultiKeepAdd();
    await read('reread_c.jpg');
    return { gate, presence, kinds, wantedCopies: cp()[K.helm] };
  }, { helm: HELM, bare: BARE, jpg: JPG_1PX });
  expect(r.gate, 'the photo door is open: AUTO INTAKE on, the vault not held').toBeNull();
  expect(r.presence.helmOwned, 'PREMISE: the piece is owned under its slotted vault key').toBe(true);
  expect(r.presence.bareOwned, 'the bare read folded onto the slotted key — one item, one name (#76)').toBe(false);
  expect(r.presence.copies ?? 1, 'two re-reads of a presence set piece must not climb its copy count').toBe(1);
  expect(r.kinds.presence, 'the re-read decision for a presence item').toBe('witness');
  expect(r.kinds.wanted, 'the re-read decision for a wanted multiple under its target').toBe('copy');
  expect(r.wantedCopies, 'control: once he wants spares, the same door files the re-read as copy 2').toBe(2);
});

test('a planner re-pick of a filed presence set piece is the same helm, not a copy; a runeword re-pick still is (#76)', async ({ page }) => {
  await seedLoad(page, [HELM, 'Grief'], { [HELM]: 'sets-rest', Grief: 'uni-weap' }, {});
  const r = await page.evaluate((K: any) => {
    const W = window as any;
    const readCopies = () => { try { return JSON.parse(W.LSR.getItem('d2r_copies') || '{}') || {}; } catch (e) { return {}; } };
    // vaultPlannerFile reaches these four resolvers through window; stubbed exactly as the REG-2227 spec stubs them
    // (v3740_planner_copy_survives_second_pick): each entry resolves to its own name, while the copy bump,
    // _vpCopySeen, copies and assign stay the REAL closure values
    W._cbItem = (id: any) => ({ id });
    W._cbShown = (entry: any) => ({ name: entry && entry.name, q: entry && entry.q, base: (entry && entry.base) || '' });
    W._vaultResolveName = (n: any) => n;
    W.vaultHandAdd = () => ({ ok: true });
    W._vaultPlannerOn = true;
    const a = W.vaultPlannerFile({ id: 'ENTRY-NATALYA-TOTEM', name: K.helm, q: 's' }, 'vp-76-tok-A');
    const b = W.vaultPlannerFile({ id: 'ENTRY-NATALYA-TOTEM', name: K.helm, q: 's' }, 'vp-76-tok-B');
    const afterSet = readCopies();
    const g = W.vaultPlannerFile({ id: 'ENTRY-GRIEF', name: 'Grief', q: 'r', base: 'Phase Blade' }, 'vp-76-tok-C');
    const afterGrief = readCopies();
    return { aMode: a && a.mode, bMode: b && b.mode, helm: afterSet[K.helm], isSet: W._vfIsSetPiece(K.helm),
             gMode: g && g.mode, grief: afterGrief['Grief'] };
  }, { helm: HELM });
  expect(r.isSet, 'PREMISE: the guard keys on a KNOWN set piece').toBe(true);
  expect(r.aMode, 'a re-pick of the filed helm is recognised as already filed').toBe('already');
  expect(r.bMode, 'a second session token is still the same helm').toBe('already');
  expect(r.helm ?? 1, 'two re-picks of a presence set piece must not climb its copy count').toBe(1);
  expect(r.gMode, 'control: a filed runeword re-picked under a new token IS a copy').toBe('copy');
  expect(r.grief, 'control: the runeword re-pick files copy 2').toBe(2);
});
