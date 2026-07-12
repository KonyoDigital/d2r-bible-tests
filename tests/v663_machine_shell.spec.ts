import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v663 — MASTER MACHINE SWITCH (Konyo: "a master switch between the two — WINDOWS/MAC, same style,
// same structure, same everything"). MAC = his world, byte-identical (bare keys + L· ladder fork).
// WINDOWS = the cousin's OWN isolated world: the WHOLE d2r_* keyspace routes to W·, the chronicle
// does NOT share (unlike ladder's one-grail), and every owner seed floor is suppressed — the cousin
// starts from zero and the progress-staged filter tightens with HIS progress (name = Cousin<N>).

test('WINDOWS shell: full isolation, zero seeds, Cousin<N> filter, wide socketed stage; MAC survives byte-level', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2200);
  const mac = await page.evaluate(() => ({
    machine: (window as any).D2R_MACHINE,
    made: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length,
    found: (window as any).funiScan().found,
  }));
  // ascend to WINDOWS
  await page.evaluate(() => localStorage.setItem('d2r_activeMachine', 'windows'));
  await page.reload(); await page.waitForTimeout(2200);
  const win = await page.evaluate(() => {
    const w: any = window;
    const fj = JSON.parse(w.buildEndgameFilter().text);
    // the cousin lives a little: tallies runes, forges HIS first word (one Konyo forged long ago —
    // the cousin's ledger must be independent of the owner's)
    w.LSR.setItem('d2r_runeStash', JSON.stringify({ Tal: 1, Eth: 1 }));
    const made: any = {}; made['Stealth'] = 'Jul 12, 2026 · 21:30';
    w.LSR.setItem('d2r_rwMade', JSON.stringify(made));
    return {
      machine: w.D2R_MACHINE, isCousin: w._isCousinShell, profile: w.D2R_PROFILE,
      madeAtBoot: Object.keys(JSON.parse(w.LSR.raw.getItem('W·d2r_rwMade') || '{}')).length <= 1,  // no 88-seed
      found: w.funiScan().found,                                       // no 229 grail floor
      filterName: fj.name,
      sockHides: fj.rules.filter((r: any) => r.ruleType === 'hide' && r.filterEtherealSocketed === true).length,
      ribbon: !!document.getElementById('cousin-ribbon'),
      profilePillVisible: getComputedStyle(document.getElementById('profile-pill')!).display !== 'none',   // v665.1 — WINDOWS has its own Main/Ladder pair
      wKeys: Object.keys(localStorage).filter((k) => k.indexOf('W·') === 0).length,
    };
  });
  // wipe scoping: a cousin wipe must ONLY remove W· keys
  const wipe = await page.evaluate(() => {
    const w: any = window;
    const before = Object.keys(localStorage).filter((k) => k.indexOf('W·') !== 0 && k !== 'd2r_activeMachine').length;
    const killed = w.LSR.wipeProfile();
    const after = Object.keys(localStorage).filter((k) => k.indexOf('W·') !== 0 && k !== 'd2r_activeMachine').length;
    return { killed, macKeysIntact: before === after, wLeft: Object.keys(localStorage).filter((k) => k.indexOf('W·') === 0).length };
  });
  // descend to MAC — everything his
  await page.evaluate(() => localStorage.setItem('d2r_activeMachine', 'mac'));
  await page.reload(); await page.waitForTimeout(2200);
  const back = await page.evaluate(() => ({
    machine: (window as any).D2R_MACHINE,
    made: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length,
    found: (window as any).funiScan().found,
    ribbon: !!document.getElementById('cousin-ribbon'),
    filterName: JSON.parse((window as any).buildEndgameFilter().text).name,
  }));
  await page.evaluate(() => { Object.keys(localStorage).filter((k) => k.indexOf('W·') === 0).forEach((k) => localStorage.removeItem(k)); localStorage.removeItem('d2r_activeMachine'); });

  expect(mac.machine).toBe('mac');
  expect(mac.made).toBeGreaterThanOrEqual(88);
  expect(win.machine).toBe('windows');
  expect(win.isCousin).toBe(true);
  expect(win.profile).toBe('main');                 // v665.1 — fresh WINDOWS boot lands on the cousin's MAIN (own pointer, d2r_activeProfileWin)
  expect(win.madeAtBoot).toBe(true);                // ★ no owner seed
  expect(win.found).toBe(0);                        // ★ no owner grail floor
  expect(win.filterName).toBe('Cousin0');           // the cousin's own progress number
  expect(win.sockHides).toBe(0);                    // <50% forged → wide stage: sockets always show
  expect(win.ribbon).toBe(true);
  expect(win.profilePillVisible).toBe(true);        // v665.1 — the cousin gets the Main/Ladder toggle too
  expect(win.wKeys).toBeGreaterThan(0);
  expect(wipe.killed).toBeGreaterThan(0);
  expect(wipe.macKeysIntact).toBe(true);            // ★ a cousin wipe never touches MAC keys
  expect(wipe.wLeft).toBe(0);
  expect(back.machine).toBe('mac');
  expect(back.made).toBe(mac.made);                 // ★ byte-level MAC survival
  expect(back.found).toBe(mac.found);
  expect(back.ribbon).toBe(false);
  expect(back.filterName).toMatch(/^KonyoEndgame\d+$/);
});

test('v665.1 — the 2×2 matrix: WINDOWS-ladder forks WL·, shares the COUSIN chronicle, never touches MAC or cousin-main vaults', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2200);
  // cousin main: forge a word + own a base
  await page.evaluate(() => { localStorage.setItem('d2r_activeMachine', 'windows'); });
  await page.reload(); await page.waitForTimeout(2200);
  await page.evaluate(() => {
    const w: any = window;
    const made: any = { Stealth: 'Jul 12, 2026 · 23:30' };
    w.LSR.setItem('d2r_rwMade', JSON.stringify(made));
    w.LSR.setItem('d2r_owned', JSON.stringify(['Flail (5os)']));
  });
  // ascend to cousin LADDER
  await page.evaluate(() => { localStorage.setItem('d2r_activeProfileWin', 'ladder'); });
  await page.reload(); await page.waitForTimeout(2200);
  const cl = await page.evaluate(() => {
    const w: any = window;
    w.LSR.setItem('d2r_owned', JSON.stringify(['Monarch (4os)']));   // cousin-ladder physical
    return {
      profile: w.D2R_PROFILE, machine: w.D2R_MACHINE,
      seesCousinForge: !!JSON.parse(w.LSR.getItem('d2r_rwMade') || '{}')['Stealth'],   // chronicle shared cousin-main↔cousin-ladder
      vaultClean: JSON.parse(w.LSR.getItem('d2r_owned') || '[]'),
      wlKey: w.LSR.raw.getItem('WL·d2r_owned'),
      ribbons: !!document.getElementById('cousin-ribbon') && !!document.getElementById('ladder-ribbon'),
    };
  });
  // back to cousin MAIN: vault separate, chronicle same
  await page.evaluate(() => { localStorage.setItem('d2r_activeProfileWin', 'main'); });
  await page.reload(); await page.waitForTimeout(2200);
  const cm = await page.evaluate(() => ({
    vault: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]'),
    made: Object.keys(JSON.parse((window as any).LSR.getItem('d2r_rwMade') || '{}')),
  }));
  // back to MAC: everything his, no W/WL leakage
  await page.evaluate(() => { localStorage.setItem('d2r_activeMachine', 'mac'); });
  await page.reload(); await page.waitForTimeout(2200);
  const mac = await page.evaluate(() => ({
    made: Object.keys(JSON.parse(localStorage.getItem('d2r_rwMade') || '{}')).length,
    profile: (window as any).D2R_PROFILE,
  }));
  await page.evaluate(() => { Object.keys(localStorage).filter((k) => k.indexOf('W·') === 0 || k.indexOf('WL·') === 0).forEach((k) => localStorage.removeItem(k)); localStorage.removeItem('d2r_activeMachine'); localStorage.removeItem('d2r_activeProfileWin'); });
  expect(cl.machine).toBe('windows');
  expect(cl.profile).toBe('ladder');
  expect(cl.seesCousinForge).toBe(true);                       // ★ ONE cousin grail across his two accounts
  expect(cl.vaultClean).toEqual(['Monarch (4os)']);            // ★ physical NEVER crosses (cousin-main's Flail absent)
  expect(cl.wlKey).toBe(JSON.stringify(['Monarch (4os)']));    // parked under WL·
  expect(cl.ribbons).toBe(true);                               // both cues stack
  expect(cm.vault).toEqual(['Flail (5os)']);                   // cousin-main vault intact
  expect(cm.made).toContain('Stealth');
  expect(mac.made).toBeGreaterThanOrEqual(88);                 // MAC untouched
  expect(mac.profile).toBe('main');                            // MAC pointer never moved
});
