import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1270 (G2) — TASK-FORCE AI PRIORITY-ROTATION ENGINE. The Daily Pick / OPS queue / Mission Brief used to
// DEAD-END the moment the runeword Chronicle sealed (99/99) — "no runewords remain" / "queue clear" — even
// with grail uniques (246/403) and sets (108/135) still to hunt. window._chronRotation() now reads EVERY
// chronicle's real completion, treats a sealed one as DONE, DESCENDS past it, ranks the incomplete ones
// (runewords = priority tier; else closest-to-done wins) and hands each surface a REAL farm move built from
// the same funiScan / fsetsScan / boss-source truth. Konyo: "descend and intelligently ROTATE to the next
// incomplete chronicle." Runewords still task FIRST whenever any remain (easiest / priority).

// Seal every runeword in the live Chronicle + bust the rotation memo. Returns rw completion truth.
async function sealRunewords(page: any) {
  return await page.evaluate(() => {
    const w: any = window;
    const TIP = (typeof (globalThis as any).RUNEWORD_TIP !== 'undefined') ? (globalThis as any).RUNEWORD_TIP : (w.RUNEWORD_TIP || {});
    const names = Object.keys(TIP);
    // fast path — mutate the live rwMade closure object the engine reads; fall back to the public toggle
    try {
      // @ts-ignore — rwMade is a top-level binding shared in this realm
      names.forEach((n) => { rwMade[n] = 'sealed'; });
      // @ts-ignore
      localStorage.setItem('d2r_rwMade', JSON.stringify(rwMade));
    } catch (e) {
      const made = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
      names.forEach((n) => { if (!made[n]) w.rwToggleMade(n); });
    }
    w._chronRotMemo = null;
    const rot = w._chronRotation();
    const rw = rot.all.find((c: any) => c.key === 'rw');
    return { total: names.length, rwComplete: !!(rw && rw.complete), rwDone: rw ? rw.done : -1 };
  });
}

test('runewords sealed → rotation DESCENDS to grail/sets, never dead-ends on runewords', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2200);
  const seal = await sealRunewords(page);
  expect(seal.rwComplete).toBe(true);              // the runeword chronicle is genuinely complete
  const r = await page.evaluate(() => {
    const w: any = window;
    w._chronRotMemo = null;
    const rot = w._chronRotation();
    return {
      sealed: rot.sealed,
      targetKey: rot.target ? rot.target.key : null,
      targetPick: rot.target ? rot.target.pick : '',
      incompleteKeys: rot.incomplete.map((c: any) => c.key),
    };
  });
  expect(r.sealed).toBe(false);                    // grail + sets still incomplete on the seeded profile
  expect(r.targetKey).not.toBe('rw');              // it descended PAST the sealed runeword chronicle
  expect(['grail', 'sets']).toContain(r.targetKey);
  expect(r.targetPick.length).toBeGreaterThan(10); // a real actionable move, not empty
  expect(r.targetPick).toMatch(/🏆|🧩/);            // grail or set move
  expect(r.incompleteKeys).not.toContain('rw');    // runewords no longer in the incomplete list
});

test('a still-makeable runeword ranks FIRST — rotation tasks runewords before grail/sets', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_rwMade', '{}');       // no runewords made → chronicle incomplete
  });
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._chronRotMemo = null;
    const rot = w._chronRotation();
    const rw = rot.all.find((c: any) => c.key === 'rw');
    return { rwComplete: !!(rw && rw.complete), targetKey: rot.target ? rot.target.key : null };
  });
  expect(r.rwComplete).toBe(false);                // runewords still open
  expect(r.targetKey).toBe('rw');                  // priority tier → runewords task first
});

test('dailyCreateAi descends: no makeable runeword/craft → grail/set Daily Pick, never "no runewords remain"', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_runeStash', '{}');    // no runes → no makeable runeword
    localStorage.setItem('d2r_gemStash', '{}');     // no gems  → no makeable craft
    localStorage.setItem('d2r_craftStash', '{}');
  });
  await page.goto(URL); await page.waitForTimeout(2000);
  await sealRunewords(page);
  const pick = await page.evaluate(() => {
    const w: any = window;
    w.__allowDailyAi = true;                         // permit the fn to run under Playwright (no fetch on this path)
    localStorage.removeItem('d2r_createNowAi');
    localStorage.removeItem('d2r_createNowAiDate');
    w._chronRotMemo = null;
    w.dailyCreateAi(true);
    return w.LSR.getItem('d2r_createNowAi') || '';
  });
  expect(pick.length).toBeGreaterThan(10);          // the pick is NOT wiped
  expect(pick).toMatch(/🏆|🧩/);                     // it names the next incomplete chronicle's move
  expect(pick.toLowerCase()).not.toContain('no runewords');
});

test('OPS queue + Mission Brief descend to a real grail/set op instead of "queue clear"', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_runeStash', '{}');
    localStorage.setItem('d2r_gemStash', '{}');
    localStorage.setItem('d2r_craftStash', '{}');
    localStorage.removeItem('d2r_chroniclePin');    // no pin → the general descends the rotation
  });
  await page.goto(URL); await page.waitForTimeout(2000);
  await sealRunewords(page);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._chronRotMemo = null;
    w.switchTab('session');
    w.renderSessionCockpit();
    const ops = document.getElementById('sc-ops-body')!.textContent || '';
    const mission = document.getElementById('sc-mission-body')!.textContent || '';
    return { ops, mission, mkind: w._scMission ? w._scMission.kind : '', pick: w.LSR.getItem('d2r_createNowAi') || '' };
  });
  // OPS queue is NOT the dead-end message and carries a real grail/set hunt
  expect(r.ops).not.toContain('queue clear');
  expect(r.ops).toMatch(/🏆|🧩|uniques left/);
  // Mission Brief descended to a grail OR set target (rotation ranks closest-to-done;
  // sets can outrank grail when their completion % is higher — both are valid hunts).
  expect(['grail', 'set']).toContain(r.mkind);
  expect(r.mission).not.toContain('Stand by');
  expect(r.mission.length).toBeGreaterThan(15);
});

test('ONLY when every chronicle is truly complete does it say "all chronicles sealed"', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  await sealRunewords(page);
  const r = await page.evaluate(() => {
    const w: any = window;
    // stub the grail + set scans to fully complete (can't realistically find 403 uniques in a test)
    const fu = w.funiScan(); w.funiScan = () => ({ ...fu, found: fu.chronTotal || fu.total, missing: [], runs: [] });
    const fs = w.fsetsScan(); w.fsetsScan = () => ({ ...fs, havePieces: fs.totalPieces, working: [], oneAway: [] });
    w._chronRotMemo = null;
    const rot = w._chronRotation();
    w.__allowDailyAi = true;
    localStorage.removeItem('d2r_createNowAi');
    localStorage.removeItem('d2r_createNowAiDate');
    localStorage.setItem('d2r_runeStash', '{}'); localStorage.setItem('d2r_gemStash', '{}');
    w._chronRotMemo = null;
    w.dailyCreateAi(true);
    return { sealed: rot.sealed, target: rot.target, pick: w.LSR.getItem('d2r_createNowAi') || '' };
  });
  expect(r.sealed).toBe(true);
  expect(r.target).toBeNull();
  expect(r.pick.toLowerCase()).toContain('sealed');
});
