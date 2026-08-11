import { test, expect } from './_net_stub';
import * as path from 'path';
import { suppressOneShots } from './_oneshots';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v949 — CHRONICLE SYNC (Konyo: "ladder↔non-ladder the chronicles are the SAME and should be SYNCED
// to non-ladder; the vault manager and mules stay separate"). The grail found-log (d2r_foundLog), the
// set chronicle (d2r_setPieces) and the transient grail import report leave _LP_FORKED so the two MAC
// accounts read ONE shared chronicle. Vault/mule/inventory keys stay forked. A one-time boot MERGE
// unions any pre-existing bare + L· copies so nothing is lost. The WINDOWS cousin stays fully isolated.

test('(a) chronicle keys are SHARED (not forked) — same bare key resolves on main AND ladder', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    return {
      // fork-set membership: chronicle OUT, vault/mule/account IN
      foundLogForked: w._LP_FORKED.has('d2r_foundLog'),
      setPiecesForked: w._LP_FORKED.has('d2r_setPieces'),
      importForked: w._LP_FORKED.has('d2r_grailImportReport'),
      ownedForked: w._LP_FORKED.has('d2r_owned'),
      copiesForked: w._LP_FORKED.has('d2r_copies'),
      muleAssignForked: w._LP_FORKED.has('d2r_muleAssign'),
      muleRosterForked: w._LP_FORKED.has('d2r_muleRoster'),
      runeStashForked: w._LP_FORKED.has('d2r_runeStash'),
      rwVerifyForked: w._LP_FORKED.has('d2r_rwVerify'),   // rwVerify STAYS forked (non-ladder FAIL != ladder truth)
      // the WINDOWS cousin keeps its own isolated chronicle (W·)
      foundLogWP: w._WP_FORKED.has('d2r_foundLog'),
      setPiecesWP: w._WP_FORKED.has('d2r_setPieces'),
      importWP: w._WP_FORKED.has('d2r_grailImportReport'),
      // main routes chronicle + vault to bare
      mainFoundLogKey: w.LSR.key('d2r_foundLog'),
      mainOwnedKey: w.LSR.key('d2r_owned'),
    };
  });
  // chronicle un-forked
  expect(r.foundLogForked).toBe(false);
  expect(r.setPiecesForked).toBe(false);
  expect(r.importForked).toBe(false);
  // vault / mule / inventory / rwVerify STILL forked
  expect(r.ownedForked).toBe(true);
  expect(r.copiesForked).toBe(true);
  expect(r.muleAssignForked).toBe(true);
  expect(r.muleRosterForked).toBe(true);
  expect(r.runeStashForked).toBe(true);
  expect(r.rwVerifyForked).toBe(true);
  // cousin still isolated
  expect(r.foundLogWP).toBe(true);
  expect(r.setPiecesWP).toBe(true);
  expect(r.importWP).toBe(true);
  // main routes to bare
  expect(r.mainFoundLogKey).toBe('d2r_foundLog');
  expect(r.mainOwnedKey).toBe('d2r_owned');

  // ascend to ladder — the chronicle key stays BARE (shared); the vault key forks to L·
  await page.evaluate(() => { localStorage.setItem('d2r_activeProfile', 'ladder'); });
  await page.reload(); await page.waitForTimeout(1400);
  const l = await page.evaluate(() => {
    const w: any = window;
    return {
      profile: w.D2R_PROFILE,
      foundLogKey: w.LSR.key('d2r_foundLog'),
      setPiecesKey: w.LSR.key('d2r_setPieces'),
      ownedKey: w.LSR.key('d2r_owned'),
      muleKey: w.LSR.key('d2r_muleAssign'),
      runeKey: w.LSR.key('d2r_runeStash'),
    };
  });
  await page.evaluate(() => { localStorage.removeItem('d2r_activeProfile'); Object.keys(localStorage).filter((k) => k.indexOf('L·') === 0).forEach((k) => localStorage.removeItem(k)); });
  expect(l.profile).toBe('ladder');
  // SHARED chronicle: ladder resolves to the SAME bare key main uses
  expect(l.foundLogKey).toBe('d2r_foundLog');
  expect(l.setPiecesKey).toBe('d2r_setPieces');
  // SEPARATE vault/mule/inventory: ladder forks to L·
  expect(l.ownedKey).toBe('L·d2r_owned');
  expect(l.muleKey).toBe('L·d2r_muleAssign');
  expect(l.runeKey).toBe('L·d2r_runeStash');
});

test('(c) one-time MERGE unions both accounts’ chronicles with NO loss, and is idempotent', async ({ page }) => {
  // seed ONCE (before the page migration runs) both a bare (main) and an L· (ladder) chronicle with
  // DIFFERENT progress + a collision that has different dates → the merge must union everything and
  // keep the EARLIEST date on the collision. The guard makes seeding happen only on the first load.
  /* v1696 — AND suppress the one-shot boot applies. `fresh` kills the grail-seed FLOOR but NOT the
     v1692/v1693 one-shots: those fire whenever d2r_foundLog is non-empty, and this test deliberately
     seeds it with two names. So twelve ruled/verified finds were applied into a fixture whose whole
     assertion is "the union is EXACTLY these three", and the union assertion failed by exactly those
     twelve. The flags are derived from bible.html (tests/_oneshots.ts), never hand-listed, so the
     next one-shot cannot re-arm this. */
  await page.addInitScript((flags: Record<string, string>) => {
    try {
      // fresh profile suppresses the owner grail-seed FLOOR (which would otherwise flood d2r_foundLog
      // with the full seed) so the union assertion sees exactly the two accounts' seeded finds.
      localStorage.setItem('d2r_rwProfile', 'fresh');
      for (const k of Object.keys(flags)) localStorage.setItem(k, flags[k]);
      if (!localStorage.getItem('__v949_seeded')) {
        localStorage.setItem('d2r_foundLog', JSON.stringify({ 'Shako': 'Jan 1, 2026 · 10:00', 'Windforce': 'Mar 3, 2026 · 09:00' }));
        localStorage.setItem('L·d2r_foundLog', JSON.stringify({ 'Griffon’s Eye': 'Feb 2, 2026 · 08:00', 'Windforce': 'Jan 15, 2026 · 07:00' }));
        localStorage.setItem('d2r_setPieces', JSON.stringify(['Tal Rasha’s Guardianship (Armor)']));
        localStorage.setItem('L·d2r_setPieces', JSON.stringify(['Immortal King’s Will (Helm)']));
        localStorage.setItem('__v949_seeded', '1');
      }
    } catch (e) {}
  }, suppressOneShots());
  await page.goto(URL); await page.waitForTimeout(1400);
  const merged = await page.evaluate(() => {
    const w: any = window;
    return {
      found: JSON.parse(localStorage.getItem('d2r_foundLog') || '{}'),
      setP: JSON.parse(localStorage.getItem('d2r_setPieces') || '[]'),
      lFoundGone: localStorage.getItem('L·d2r_foundLog') === null,
      lSetGone: localStorage.getItem('L·d2r_setPieces') === null,
      flag: localStorage.getItem('d2r_chronSyncMerged_v1'),
    };
  });
  // union of BOTH accounts, nothing dropped
  expect(Object.keys(merged.found).sort()).toEqual(['Griffon’s Eye', 'Shako', 'Windforce']);
  // collision: the NON-LADDER (sync-target) stamp is authoritative and kept; ladder never overwrites it
  expect(merged.found['Windforce']).toBe('Mar 3, 2026 · 09:00');
  // the ladder-only find carried its ladder date across (nothing invented)
  expect(merged.found['Griffon’s Eye']).toBe('Feb 2, 2026 · 08:00');
  expect(merged.setP.sort()).toEqual(['Immortal King’s Will (Helm)', 'Tal Rasha’s Guardianship (Armor)']);
  // orphaned L· copies removed; flag set
  expect(merged.lFoundGone).toBe(true);
  expect(merged.lSetGone).toBe(true);
  expect(merged.flag).toBe('1');

  // IDEMPOTENT: reload — the flag skips a second merge, the union is unchanged, nothing resurrected
  await page.reload(); await page.waitForTimeout(1400);
  const again = await page.evaluate(() => ({
    found: JSON.parse(localStorage.getItem('d2r_foundLog') || '{}'),
    setP: JSON.parse(localStorage.getItem('d2r_setPieces') || '[]'),
    lFoundGone: localStorage.getItem('L·d2r_foundLog') === null,
  }));
  expect(Object.keys(again.found).sort()).toEqual(['Griffon’s Eye', 'Shako', 'Windforce']);
  expect(again.found['Windforce']).toBe('Mar 3, 2026 · 09:00');
  expect(again.setP.sort()).toEqual(['Immortal King’s Will (Helm)', 'Tal Rasha’s Guardianship (Armor)']);
  expect(again.lFoundGone).toBe(true);

  await page.evaluate(() => { ['d2r_foundLog', 'd2r_setPieces', 'd2r_chronSyncMerged_v1', '__v949_seeded', 'd2r_grailImportReport', 'd2r_rwProfile'].forEach((k) => localStorage.removeItem(k)); });
});

test('(d) a ladder-only runeword STILL renders as ladder-only on the non-ladder (main) account', async ({ page }) => {
  // the Chronicle groups words into Ladder-only vs Non-Ladder; a fresh profile suppresses the seal so
  // both groups populate. The sync did NOT touch this render — ladder-only stays visibly ladder-only.
  await page.addInitScript(() => { try { localStorage.setItem('d2r_rwProfile', 'fresh'); } catch (e) {} });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    return { profile: w.D2R_PROFILE, blocks: typeof w._rwLadderBlocked === 'function' };
  });
  const groups = await page.evaluate(() => {
    const w: any = window;
    try { w.rwSetLadderMode('nonladder'); w.renderRunewordChronicle(); } catch (e) {}
    return Array.from(document.querySelectorAll('#rwc-list .rwc-grp-hdr')).map((h) => (h as HTMLElement).classList.contains('rwc-grp-ladder'));
  });
  await page.evaluate(() => { localStorage.removeItem('d2r_rwProfile'); });
  expect(r.profile).toBe('main');
  // on the MAIN account a ladder-only group is present + labelled ladder-only (render untouched by the sync)
  expect(groups.some((isLadder) => isLadder === true)).toBe(true);
  expect(groups.some((isLadder) => isLadder === false)).toBe(true);
});
