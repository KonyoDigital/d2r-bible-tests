import { test, expect } from '@playwright/test';
import * as fs from 'fs';

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

async function seedLoad(page: any, owned: string[], assign: any, copies: any) {
  await page.addInitScript(({ owned, assign, copies }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.removeItem('d2r_setPieceReconcile');
      /* the REG-2229 one-time set-dupe migration (_vaultDedupeOldSetRows) runs on the load render and folds a
         loose set-piece twin BEFORE this spec can drive _setPieceReconcile. It has its own law and spec; stamp it
         as already run on this world so the reconcile under test sees the seeded pair. */
      localStorage.setItem('d2r_setDupeMigrate_v2227', '1');
    } catch (e) {}
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

test('both re-read copy-bump sites are guarded against a presence set piece auto-climbing (#76)', async () => {
  // The permanent fix lives in two non-exposed intake paths (processFile + _vpCopySeen), so this is a
  // structural tripwire: if a future edit drops the _vfIsSetPiece guard from either copy-bump, a presence
  // set piece re-inflates on reads and this fails. Anchored to the two exact bump statements.
  const src = fs.readFileSync(process.cwd() + '/bible.html', 'utf8');
  /* v3767 (vault-spread) retired the processFile re-read copy-bump outright: a re-read of a presence item now
     records a WITNESS (_ownedAdd with the frame) and never writes copies[n]. So the guard is structural in a
     stronger form — the re-read branch must stay a witness and must not grow a copies bump back. */
  const procWit = src.match(/if \(_rk === 'witness' && _tgt <= 1 && _ownedAtStart\.has\(n\)\) \{ \/\* v3767 intake witness \*\/([\s\S]*?)fRec\.own\.push\(n\);/);
  expect(procWit, 'the processFile re-read witness branch must still exist').not.toBeNull();
  expect(procWit![1], 'the re-read branch records a witness').toContain('_ownedAdd(n');
  expect(procWit![1], 'the re-read branch must not bump copies (a presence set piece would auto-climb)').not.toMatch(/copies\[n\]\s*=/);
  /* the _vpCopySeen guard is a NESTED condition now (the outer line stays byte-identical to its red-proof anchor,
     see the bible.html comment there), so read the condition AND the block up to its copy bump */
  const vpGuard = src.match(/routed\.mode === 'already' && assign\[nm\] != null && _vpCopySeen\[nm\] !== token[^\n]*\{([\s\S]*?)copies\[nm\] = prevN \+ 1;/);
  expect(vpGuard, 'the _vpCopySeen copy-bump condition must still exist').not.toBeNull();
  expect(vpGuard![0]).toContain('_vfIsSetPiece(nm)');
});
