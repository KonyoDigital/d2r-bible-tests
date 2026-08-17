/* tests/v1634_profile_grail_parity.spec.ts — the guard on the d2r_owned fork question.
 *
 * WHAT THIS SPEC DEFENDS: that a unique ticked on one ACCOUNT is ticked on the other. Konyo runs a
 * MAIN and a LADDER profile on the same Mac and asked for uniques to behave "like runeword and
 * sets.. same logic" — one grail per machine. That is already true, and it is true for a reason
 * that is easy to misread from the source: d2r_owned and d2r_copies really do sit in
 * window._LP_FORKED, so they really do fork per profile — but they are the PHYSICAL vault (muled
 * keepers, socketed bases), and physical possession is per-account by design. The CHRONICLE — the
 * dated ledger of what has been found — is d2r_foundLog, which sits only in the _WP_FORKED concat,
 * resolves to one key on both profiles, and is what toggleOwned actually writes for any grail name
 * (v677: "a chronicle tick is knowledge, not possession"). funiScan reads found as the UNION of the
 * two, so a forked cache on top of a shared ledger is harmless: the union can only ever be the
 * ledger plus this account's own physical extras. That is the claim, and it is a claim about
 * OBSERVED COUNTS, not about a store name.
 *
 * WHY THE NAIVE VERSION WOULD BE AN ASSERTION THAT CANNOT FAIL: three times now the instinct has
 * been to "fix" this by moving d2r_owned into the shared set. v1633 built that migration and
 * reverted it, because the seeded names came back after a RELOAD looking untouched — the merge had
 * no lasting effect, and a spec that only asserted "d2r_owned is in _WP_FORKED" would have gone
 * green on a migration that changed nothing a user can see. Asserting where a key is filed proves
 * the file cabinet, not the grail. So every number in here is read back out of the running board:
 * funiScan().found, funiScan().missing membership, and the rendered meter's own label text, on
 * BOTH profiles, ACROSS a real reload. The reload leg is the entire point — v1633's change looked
 * right before one and evaporated after it.
 *
 * NON-VACUITY IS ENFORCED IN-BAND. A parity proof that compares two empty sets proves nothing, so
 * the baseline count is asserted to be non-zero before anything is compared, the names seeded are
 * discovered from the app's own missing list (this is the RotW mod — vanilla names are silently
 * dropped, so nothing is hardcoded), and a counter-proof test reads the FORKED namespace directly
 * to show it holds none of them: had the chronicle been forked, the ladder would have measured zero.
 * No colour, no hex, no store-name-only claim appears anywhere in this file.
 *
 * MEASURED WHEN THIS FILE WAS WRITTEN (v1634, a dated observation — not a standing assertion, which
 * is why no number below is hardcoded into any expect): a fresh automated boot floored MAIN at
 * 243/403. Ticking three uniques discovered from the board's own missing list — The Stone of Jordan,
 * Bul-Kathos Wedding Band, Dwarf Star — took MAIN to 246. Switching to LADDER measured 246, not 0
 * and not 243. Ticking two more from LADDER (Carrion Wind, Wisp Projector) took it to 248; MAIN then
 * read 248 as well, and both meters printed the same label. A full reload on each account still read
 * 248/403. VERDICT: MAIN and LADDER already agree. The fork is harmless and NO MIGRATION IS NEEDED.
 * Mutation-checked: forcing the ladder's chronicle read onto the ladder-prefixed namespace — exactly
 * what moving d2r_foundLog into _LP_FORKED would do — turns this file red on the first seeded name.
 */
// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/** The board is a single 40k-line file; give it the same settle the v1633 spec gives it. */
async function settle(page: any) {
  await page.waitForFunction(() => typeof (window as any).funiScan === 'function', null, { timeout: 20000 });
  await page.waitForTimeout(1800);
}

/** Everything the parity question needs, read off the RUNNING board — never off a store name. */
async function measure(page: any) {
  await page.evaluate(() => { try { (window as any).renderForgeUni(); } catch (e) {} });
  await page.waitForTimeout(150);
  return await page.evaluate(() => {
    const s = (window as any).funiScan();
    const missing = new Set<string>((s.missing || []).map((x: any) => x.n));
    // The meter prints its own count; the KPI line prints the named-card tally. Both are text the
    // user reads, so both are evidence — a scan that agrees with itself but not with the screen is
    // still a bug he can see.
    const lbls = Array.from(document.querySelectorAll('.fp-lbl')).map(e => (e.textContent || '').trim());
    const meter = lbls.find(t => t.indexOf('/ ' + (s.chronTotal || s.total) + ' found') >= 0) || '';
    return {
      profile: (window as any).D2R_PROFILE,
      found: s.found,
      total: s.total,
      chronTotal: s.chronTotal,
      missingCount: missing.size,
      missingNames: Array.from(missing),
      meter,
      ownedKey: (window as any).LSR.key('d2r_owned'),
      logKey: (window as any).LSR.key('d2r_foundLog'),
    };
  });
}

/** Switch accounts the way the board itself does: profileSwitch() writes the pointer and reloads. */
async function switchProfile(page: any, p: 'main' | 'ladder') {
  await page.evaluate((t: string) => { (window as any).profileSwitch(t); }, p).catch(() => {});
  await page.waitForFunction(
    (t: string) => (window as any).D2R_PROFILE === t && typeof (window as any).funiScan === 'function',
    p, { timeout: 20000 });
  await page.waitForTimeout(1800);
}

test.describe('v1634 — one grail across MAIN and LADDER', () => {

  test('★★★ a unique ticked on either account is ticked on the other, and survives a reload', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(BOARD);
    await settle(page);
    expect(errs, 'the board must load clean').toEqual([]);

    // ── BASELINE ON MAIN ─────────────────────────────────────────────────────────────────────
    const base = await measure(page);
    expect(base.profile, 'a fresh load lands on MAIN').toBe('main');
    // NON-VACUITY GATE #1: the seed floor must have put a real chronicle under this test. Comparing
    // two zeroes across two profiles would pass forever and mean nothing.
    expect(base.found, 'the MAIN baseline must be a real, non-empty grail').toBeGreaterThan(0);
    expect(base.missingCount, 'and it must not already be complete, or nothing can be seeded').toBeGreaterThan(4);

    // ── SEED ON MAIN, THROUGH THE APP'S OWN ACTION ───────────────────────────────────────────
    // Names come from the board's own missing list: this is the RotW mod, and a vanilla name that
    // does not exist in this DB is silently dropped, which would leave a vacuous test.
    const onMain: string[] = base.missingNames.slice(0, 3);
    expect(onMain.length, 'three genuinely-unfound uniques must exist to seed').toBe(3);
    await page.evaluate((names: string[]) => {
      names.forEach(n => (window as any).toggleOwned(n));
    }, onMain);
    const afterMain = await measure(page);
    // NON-VACUITY GATE #2: the seeding itself must have MOVED the number, or the parity that
    // follows is parity over an unchanged board.
    expect(afterMain.found, 'ticking three uniques must raise MAIN by exactly three')
      .toBe(base.found + 3);
    for (const n of onMain)
      expect(afterMain.missingNames, `${n} must have left MAIN's missing list`).not.toContain(n);

    // ── CROSS TO LADDER ──────────────────────────────────────────────────────────────────────
    await switchProfile(page, 'ladder');
    const ladder = await measure(page);
    expect(ladder.profile, 'profileSwitch must have landed on LADDER').toBe('ladder');

    // The doctrine, measured rather than recited: the two accounts resolve the SAME chronicle key
    // and DIFFERENT vault keys. This is why a forked cache is harmless.
    expect(ladder.logKey, 'the chronicle resolves to ONE key on both accounts').toBe(afterMain.logKey);
    expect(ladder.ownedKey, 'while the physical vault legitimately forks').not.toBe(afterMain.ownedKey);

    // THE CLAIM, DIRECTION 1: found on MAIN ⇒ found on LADDER.
    for (const n of onMain)
      expect(ladder.missingNames, `${n} was ticked on MAIN and must be found on LADDER too`).not.toContain(n);
    expect(ladder.found, 'both accounts count the same grail').toBe(afterMain.found);
    expect(ladder.missingCount, 'and therefore the same missing list').toBe(afterMain.missingCount);
    expect(new Set(ladder.missingNames), 'the missing NAMES agree, not just their count')
      .toEqual(new Set(afterMain.missingNames));
    // The screen has to agree with the scan, or he reads one answer and the engine holds another.
    expect(ladder.meter, 'the rendered meter must print the same tally on both accounts').toBe(afterMain.meter);
    expect(ladder.meter.length, 'the meter must actually have been rendered').toBeGreaterThan(0);

    // ── SEED ON LADDER, CROSS BACK ───────────────────────────────────────────────────────────
    const onLadder: string[] = ladder.missingNames.slice(0, 2);
    expect(onLadder.length, 'two more unfound uniques must exist to seed from LADDER').toBe(2);
    await page.evaluate((names: string[]) => {
      names.forEach(n => (window as any).toggleOwned(n));
    }, onLadder);
    const afterLadder = await measure(page);
    expect(afterLadder.found, 'ticking two uniques must raise LADDER by exactly two').toBe(ladder.found + 2);

    await switchProfile(page, 'main');
    const back = await measure(page);
    expect(back.profile, 'profileSwitch must have landed back on MAIN').toBe('main');

    // THE CLAIM, DIRECTION 2: found on LADDER ⇒ found on MAIN.
    for (const n of onLadder)
      expect(back.missingNames, `${n} was ticked on LADDER and must be found on MAIN too`).not.toContain(n);
    for (const n of onMain)
      expect(back.missingNames, `${n} must still be found on MAIN after the round trip`).not.toContain(n);
    expect(back.found, 'MAIN carries all five ticks: three of its own plus two from LADDER')
      .toBe(base.found + 5);
    expect(back.found, 'and the two accounts still agree').toBe(afterLadder.found);

    // ── THE RELOAD LEG — the whole reason this file exists ───────────────────────────────────
    // v1633's migration looked correct before a reload and evaporated after one. Any answer this
    // spec gives is worthless unless it survives a fresh boot, INCLUDING the boot seed floor and
    // the vault cleanse that run on every MAIN load.
    await page.reload();
    await settle(page);
    const reloadedMain = await measure(page);
    expect(reloadedMain.found, 'the five ticks survive a full reload on MAIN').toBe(back.found);
    for (const n of onMain.concat(onLadder))
      expect(reloadedMain.missingNames, `${n} must still be found on MAIN after a reload`).not.toContain(n);

    await switchProfile(page, 'ladder');
    const reloadedLadder = await measure(page);
    expect(reloadedLadder.found, 'and LADDER still agrees after the reload').toBe(reloadedMain.found);
    for (const n of onMain.concat(onLadder))
      expect(reloadedLadder.missingNames, `${n} must still be found on LADDER after a reload`).not.toContain(n);
    expect(new Set(reloadedLadder.missingNames), 'the missing NAMES still agree after the reload')
      .toEqual(new Set(reloadedMain.missingNames));

    expect(errs, 'no page error anywhere in the round trip').toEqual([]);
  });

  test('★★ the counter-proof: the ladder namespace holds no chronicle of its own', async ({ page }) => {
    // This is the test that makes the one above non-vacuous. If d2r_foundLog were forked — the exact
    // shape of the world before v949, and the shape a fourth blind re-attempt at the v1633 migration
    // would recreate — the ladder would read a SEPARATE ledger and measure zero of MAIN's finds.
    // So: tick on MAIN, then look inside the ladder-prefixed namespace with raw localStorage and
    // show it is empty of them, while the shared key holds them all.
    await page.goto(BOARD);
    await settle(page);

    const seeded = await page.evaluate(() => {
      const s = (window as any).funiScan();
      const names = (s.missing || []).slice(0, 3).map((x: any) => x.n);
      names.forEach((n: string) => (window as any).toggleOwned(n));
      const LSR = (window as any).LSR;
      const sharedKey = LSR.key('d2r_foundLog');
      const shared = JSON.parse(LSR.raw.getItem(sharedKey) || '{}');
      // The key the chronicle WOULD live under had it been filed with the forked vault. Built from
      // the board's OWN published ladder prefix, never a hand-typed string: v1499 made the prefixes
      // install-derived, so a literal here would be a guess that quietly stopped matching.
      const forkedKey = (window as any)._D2R_LPFX + 'd2r_foundLog';
      const forkedRaw = LSR.raw.getItem(forkedKey);
      return {
        names, sharedKey, forkedKey, forkedRaw,
        inShared: names.filter((n: string) => shared[n] != null).length,
        sharedSize: Object.keys(shared).length,
        lpHasLog: (window as any)._LP_FORKED.has('d2r_foundLog'),
        wpHasLog: (window as any)._WP_FORKED.has('d2r_foundLog'),
        lpHasOwned: (window as any)._LP_FORKED.has('d2r_owned'),
        lpHasCopies: (window as any)._LP_FORKED.has('d2r_copies'),
      };
    });

    expect(seeded.names.length, 'three real RotW uniques were discovered from the board').toBe(3);
    expect(seeded.sharedSize, 'the shared chronicle is a real, populated ledger').toBeGreaterThan(3);
    expect(seeded.inShared, 'every tick landed in the SHARED chronicle').toBe(3);
    expect(seeded.forkedKey, 'the ladder-prefixed chronicle key is a different string').not.toBe(seeded.sharedKey);
    expect(seeded.forkedRaw, 'and nothing is written under it — there is no second chronicle').toBeNull();

    // The filing that produces the behaviour above. Asserted LAST and only as the EXPLANATION of a
    // measured result, never as the result itself — see this file's header for why the reverse
    // (asserting the store name alone) is an assertion that cannot fail.
    expect(seeded.lpHasLog, 'the chronicle is NOT forked per profile').toBe(false);
    expect(seeded.wpHasLog, 'but it IS forked per machine — the Windows cousin keeps its own').toBe(true);
    expect(seeded.lpHasOwned, 'the physical vault stays forked per account, and that is correct').toBe(true);
    expect(seeded.lpHasCopies, 'as does its copy tally').toBe(true);
  });
});
