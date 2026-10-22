import { test, expect } from '@playwright/test';

// #76 (phase 4) — v3752's reconcile was correct in DIRECTION (fold bare->slotted, keep MAX, never clamp) but a
// cross-family (Grok) review found the RECOUNT control was disconnected and the persist/undo was unsafe. The
// vault keys set pieces on the SLOTTED ledger form ("Natalya's Totem (helm)"); the grail/chronicle uses the BARE
// form ("Natalya's Totem"). vaultMultiKeepAdd (the ONE vault control that re-derives a name through the grail
// resolver) set multiKeep on the BARE key while owned/copies/mule key on SLOTTED — so the user could never
// recount. v3753: the recount UI canonicalizes to the slotted ledger key (Add falls back to the set-piece canon
// since a set piece is not in the grail vocab; the steppers canonicalize; an inflated count can walk DOWN;
// renderMultiKeep surfaces an owned inflated set piece with no target). Plus the reconcile sweeps a dead bare
// copies key left by a prior split (never raising the keeper), and an undo re-arms the one-time stamp.
// RED before v3753: vaultMultiKeepAdd rejects a set-piece name; the steppers touch the bare key; no dead-key
// sweep; undo leaves the stamp. Verified on the REAL page via CDP (recount walks 3->2; dead-key swept).
// [[the-unjoined-end]] [[manual-tally-is-witness]] [[d2r-curly-apostrophe-class]]

const URL = 'file://' + process.cwd() + '/bible.html';
const BARE = "Natalya's Totem", HELM = "Natalya's Totem (helm)", RAVEN = 'Raven Frost';

// #184 (REG-2531) — THE SEED AND THE WEBDRIVER FLAG ARE SEPARATE STEPS. A second seedLoad on the same page registers a
// second init script, and both run on the next load. navigator.webdriver is by then this page's own non-configurable
// property, so redefining it threw, the one catch swallowed it, and every write after it was skipped: the second load ran
// on the FIRST seed ({helm: 3, bare: 2}) and the fold answered MAX(3,2) = 3 where the test asked MAX(1,4) = 4. `stamp`
// tells the page's own load-time pass (1.5 s after load) that it already ran, so only the test's forced pass folds;
// otherwise it can sweep the dead key first and the forced pass finds none (the CI retry of run 39726369389).
async function seedLoad(page: any, owned: string[], assign: any, copies: any, multiKeep: any, stamp?: boolean) {
  await page.addInitScript(({ owned, assign, copies, multiKeep, stamp }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_multiKeep', JSON.stringify(multiKeep));
      if (stamp) localStorage.setItem('d2r_setPieceReconcile', JSON.stringify({ ver: 1e9, by: 'spec' }));
      else localStorage.removeItem('d2r_setPieceReconcile');
    } catch (e) {}
    try {
      if (!Object.getOwnPropertyDescriptor(navigator, 'webdriver')) Object.defineProperty(navigator, 'webdriver', { get: () => true });
    } catch (e) {}
  }, { owned, assign, copies, multiKeep, stamp: !!stamp });
  await page.goto(URL);
  await page.waitForFunction(() => {
    const w = window as any;
    return w._setPieceReconcile && w.vaultMultiKeepAdd && w.vaultCopyAdjust && w._vfCanon && w.vaultRestoreLast;
  });
}

test('recount: a BARE set-piece name typed in the Add box keys the SLOTTED ledger form, and HAVE walks down (#76)', async ({ page }) => {
  await seedLoad(page, [HELM], { [HELM]: 'sets-rest' }, { [HELM]: 3 }, {});
  const r = await page.evaluate((K: any) => {
    const w = window as any;
    let inp: any = document.getElementById('vmk-add-input');
    if (!inp) { inp = document.createElement('input'); inp.id = 'vmk-add-input'; document.body.appendChild(inp); }
    inp.value = K.bare;                 // the BARE chronicle name — not in the grail vocab
    w.vaultMultiKeepAdd();              // must fall back to the set-piece canon and key SLOTTED
    let mk: any = {}; try { mk = JSON.parse(localStorage.getItem('d2r_multiKeep') || '{}'); } catch (e) {}
    w.vaultCopyAdjust(K.bare, -1);      // bare input -> slotted key, walk 3 -> 2
    let cp: any = {}; try { cp = JSON.parse(localStorage.getItem('d2r_copies') || '{}'); } catch (e) {}
    return { mkHelm: mk[K.helm], mkBare: mk[K.bare], cpHelm: cp[K.helm], cpBare: cp[K.bare] };
  }, { bare: BARE, helm: HELM });
  expect(r.mkHelm).toBe(2);            // multiKeep keyed on the SLOTTED ledger form
  expect(r.mkBare).toBeUndefined();    // NOT the dead bare grail key
  expect(r.cpHelm).toBe(2);            // the stepper walked the slotted count 3 -> 2
  expect(r.cpBare).toBeUndefined();
});

test('renderMultiKeep surfaces an owned inflated set piece with NO keep-target (walk-down without typing) (#76)', async ({ page }) => {
  await seedLoad(page, [HELM, RAVEN], { [HELM]: 'sets-rest' }, { [HELM]: 3 }, {});
  const r = await page.evaluate((K: any) => {
    const w = window as any;
    let el: any = document.getElementById('vault-multikeep');
    if (!el) { el = document.createElement('div'); el.id = 'vault-multikeep'; document.body.appendChild(el); }
    w.renderMultiKeep();
    const html = el.innerHTML || '';
    return { surfaced: html.indexOf(K.helm) >= 0, hasHaveStepper: /vaultCopyAdjust/.test(html) };
  }, { helm: HELM });
  expect(r.surfaced).toBe(true);       // the inflated set piece appears without being typed
  expect(r.hasHaveStepper).toBe(true); // with a HAVE stepper to walk it down
});

async function sweepRun(page: any) {
  return await page.evaluate((K: any) => {
    const w = window as any;
    const res = w._setPieceReconcile({ force: true });
    let cp: any = {}; try { cp = JSON.parse(localStorage.getItem('d2r_copies') || '{}'); } catch (e) {}
    const rc = (res && res.receipt) || {};
    return { dead: rc.copiesDeadKeys || [], cpHelm: cp[K.helm], cpBare: cp[K.bare], stamped: res.stamped };
  }, { helm: HELM, bare: BARE });
}

test('the reconcile sweeps a dead bare copies key, folding its count onto the keeper by MAX — never lost (#76)', async ({ page }) => {
  // a prior version removed the bare from owned but left a copies["Natalya's Totem"] key behind.
  // dead count (2) BELOW the keeper (3): keeper unchanged, orphan swept
  await seedLoad(page, [HELM], { [HELM]: 'sets-rest' }, { [HELM]: 3, [BARE]: 2 }, {}, true);
  let r = await sweepRun(page);
  expect(r.dead).toContain(BARE);
  expect(r.cpBare).toBeUndefined();
  expect(r.cpHelm).toBe(3);            // MAX(3,2) — keeper not over-raised
  expect(r.stamped).toBe(true);
  // dead count (4) ABOVE the keeper (absent -> 1): MOVED onto the keeper, never deleted-and-lost
  await seedLoad(page, [HELM], { [HELM]: 'sets-rest' }, { [BARE]: 4 }, {}, true);
  r = await sweepRun(page);
  expect(r.dead).toContain(BARE);
  expect(r.cpBare).toBeUndefined();
  expect(r.cpHelm).toBe(4);            // MAX(1,4) — the real count is PRESERVED on the ledger key (Grok v3753 #2)
});

test('undoing a reconcile batch re-arms the one-time stamp so the fold re-runs next load (#76)', async ({ page }) => {
  await seedLoad(page, [BARE, HELM, RAVEN], { [BARE]: 'sets-rest', [HELM]: 'sets-rest' }, { [HELM]: 3, [BARE]: 1 }, {});
  const r = await page.evaluate(() => {
    const w = window as any;
    w._setPieceReconcile({ force: true });                   // folds bare -> slotted, stamps
    const stampedAfter = localStorage.getItem('d2r_setPieceReconcile') != null;
    w.vaultRestoreLast();                                     // undo the fold batch
    const stampAfterUndo = localStorage.getItem('d2r_setPieceReconcile');
    return { stampedAfter, clearedOnUndo: stampAfterUndo == null };
  });
  expect(r.stampedAfter).toBe(true);   // the fold stamped
  expect(r.clearedOnUndo).toBe(true);  // the undo cleared the stamp -> next load re-folds (no permanent split)
});
