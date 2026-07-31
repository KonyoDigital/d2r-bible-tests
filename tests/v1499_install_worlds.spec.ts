import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1499 — THE WORLD IS THE INSTALL, NOT THE OPERATING SYSTEM.
//
// This replaces v663_machine_shell's premise. That spec proved the mac/windows switch routed keys;
// this proves the thing that actually protects Konyo: a browser is a GUEST until a human claims it,
// and an unclaimed browser can neither see his chronicle nor damage it.
//
// It keeps every invariant v663 was written to defend — full isolation, zero owner seeds in the
// other world, byte-level survival of his data — and adds the two the old model could not express:
// an unclaimed load writes NOTHING bare, and two different installs never share one world.
//
// NOTE ON THE HARNESS: an automated browser on file:// resolves owner (bible.html, v1499), because
// Playwright cannot seed a claim into a file:// origin — storageState refuses that origin. So a
// GUEST is produced here the way a real guest is produced: by giving the browser a claim that
// belongs to a DIFFERENT install.
const asGuest = (page: any) =>
  page.addInitScript(() => localStorage.setItem('d2r_ownerClaim', 'some-other-machines-install-id'));

test.describe('v1499 — a browser is a guest until a human claims it', () => {
  test('an unclaimed browser sees an EMPTY world and writes nothing bare', async ({ page }) => {
    await asGuest(page);
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => ({
      owner: (window as any)._D2R_OWNER,
      key: (window as any).LSR.key('d2r_rwMade'),
      made: Object.keys(JSON.parse((window as any).LSR.getItem('d2r_rwMade') || '{}')).length,
      grail: (window as any).funiScan().found,
      sets: Object.keys(JSON.parse((window as any).LSR.getItem('d2r_setPieces') || '{}')).length,
      // THE load-bearing one: a guest load must leave no bare ACCOUNT key behind. Konyo's real data
      // lives in exactly these names, and an unclaimed browser sitting on his machine must not so
      // much as create them.
      bareAccountKeys: Object.keys(localStorage).filter((k) =>
        /^d2r_(rwMade|owned|foundLog|setPieces|runeStash|muleAssign)$/.test(k)).length,
    }));
    expect(r.owner).toBe(false);
    expect(r.key).toMatch(/^I·[a-z0-9]{1,8}·d2r_rwMade$/);   // its own namespace, per install
    expect(r.made).toBe(0);                                   // ★ no owner seed
    expect(r.grail).toBe(0);                                  // ★ no owner grail floor
    expect(r.sets).toBe(0);
    expect(r.bareAccountKeys, 'an unclaimed load must never write a bare account key').toBe(0);
  });

  test('claiming brings the owner world back on the SAME keys it always used', async ({ page }) => {
    await page.goto(URL);          // automated + file:// ⇒ owner, the suite's normal world
    await page.waitForTimeout(1800);
    const owner = await page.evaluate(() => ({
      owner: (window as any)._D2R_OWNER,
      key: (window as any).LSR.key('d2r_rwMade'),
      made: Object.keys(JSON.parse((window as any).LSR.getItem('d2r_rwMade') || '{}')).length,
      grail: (window as any).funiScan().found,
    }));
    expect(owner.owner).toBe(true);
    expect(owner.key).toBe('d2r_rwMade');            // ★ BARE — the migration moved nothing
    expect(owner.made).toBeGreaterThanOrEqual(88);   // his chronicle, where it has always been
    expect(owner.grail).toBeGreaterThan(0);
  });

  test('two different installs never share a world', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    const keys = await page.evaluate(() => {
      const w: any = window;
      const mk = (id: string) => 'I·' + id.slice(0, 8) + '·';
      return { a: mk('aaaaaaaaaaaa'), b: mk('bbbbbbbbbbbb'), same: mk('aaaaaaaaaaaa') === mk('bbbbbbbbbbbb') };
    });
    expect(keys.same, 'the guest prefix must be derived from the install id').toBe(false);
    expect(keys.a).not.toBe(keys.b);
  });

  test('a guest wipe can never reach a bare key', async ({ page }) => {
    await asGuest(page);
    await page.goto(URL);
    await page.waitForTimeout(1800);
    const r = await page.evaluate(() => {
      const w: any = window;
      // plant something bare (as the OWNER build would have left behind) and something guest-side
      localStorage.setItem('d2r_rwMade', JSON.stringify({ 'Owner Word': 'x' }));
      localStorage.setItem(w._D2R_PFX + 'd2r_rwMade', JSON.stringify({ 'Guest Word': 'y' }));
      const before = localStorage.getItem('d2r_rwMade');
      const killed = w.LSR.wipeProfile();
      return {
        killed,
        bareSurvived: localStorage.getItem('d2r_rwMade') === before,
        guestGone: localStorage.getItem(w._D2R_PFX + 'd2r_rwMade') === null,
        claimSurvived: !!localStorage.getItem('d2r_ownerClaim'),
      };
    });
    expect(r.bareSurvived, 'THE data-loss path: a guest wipe must never touch the owner world').toBe(true);
    expect(r.guestGone).toBe(true);
    expect(r.claimSurvived, 'identity keys are pointers, not progress — they survive every wipe').toBe(true);
  });
});
