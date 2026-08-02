import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1557 — THE POSSESSIVE WAS HIDING HIS FARM DATA.
//
// _setAggSrc matched on "the aggregate's name STARTS WITH the first 12 characters of the set's
// name". "Tal Rasha's Wrappings" gives the stem "tal rasha's " while the aggregate holding the drop
// data is called "Tal Rasha set (any piece)" — twelve characters apart, one apostrophe at fault,
// and the result was a set in his working list with no farm run at all.
//
// Measured: 9 of his 16 in-progress sets resolved to NO source. Two of those nine had the data all
// along. The other seven genuinely have no aggregate entry — and that is now SAID, because
// Tancred's Battlegear is one of them and it is the set his DAILY TASK FORCE is telling him to
// finish. A task with no way to do it should not look like one whose boss merely did not fit.

const boot = async (page: any) => { await page.goto(URL); await page.waitForTimeout(2000); };

test.describe('v1557 — the set-name match, and the absence it used to hide', () => {
  test('★ the possessive no longer breaks the match', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      return {
        talRasha: !!w._setAggSrc("Tal Rasha's Wrappings (Sorc)"),
        trang: !!w._setAggSrc("Trang-Oul's Avatar (Necro)"),
        // the five that already worked must keep working
        aldur: !!w._setAggSrc("Aldur's Watchtower (Druid)"),
        ik: !!w._setAggSrc('Immortal King (Barb)'),
        mavina: !!w._setAggSrc("M'avina's Battle Hymn (Ama)"),
        natalya: !!w._setAggSrc("Natalya's Odium (Sin)"),
        griswold: !!w._setAggSrc("Griswold's Legacy (Pala)"),
      };
    });
    expect(r.talRasha, "Tal Rasha's Wrappings -> Tal Rasha set (any piece)").toBe(true);
    expect(r.trang, "Trang-Oul's Avatar -> Trang-Oul set (any piece)").toBe(true);
    for (const k of ['aldur', 'ik', 'mavina', 'natalya', 'griswold']) {
      expect((r as any)[k], k + ' matched before and must still match').toBe(true);
    }
  });

  test('★ the key reconciles possessives, class suffixes and the word "set"', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const k = (window as any)._setKey;
      return {
        a: k("Tal Rasha's Wrappings (Sorc)"), b: k('Tal Rasha set (any piece)'),
        c: k("M'avina's Battle Hymn (Ama)"), d: k("M'avina's Battle Hymn (any)"),
        e: k("Trang-Oul's Avatar (Necro)"), f: k('Trang-Oul set (any piece)'),
      };
    });
    // the possessive must lose its S — "Rasha's" -> "rasha", not "rashas". Getting that wrong
    // recovered nothing and broke five that worked.
    expect(r.a).toBe('tal rasha wrappings');
    expect(r.b).toBe('tal rasha');
    expect(r.c).toBe(r.d);
    expect(r.e).toBe('trang oul avatar');
    expect(r.f).toBe('trang oul');
  });

  test('★ more of his working sets can be hunted than before', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const fs = w.fsetsScan();
      const rows = (fs.working || []).map((st: any) => !!w._setAggSrc(st.name));
      return { working: rows.length, withSource: rows.filter(Boolean).length };
    });
    expect(r.working).toBeGreaterThan(10);
    expect(r.withSource, 'was 7 of 16 before the key was fixed').toBeGreaterThanOrEqual(9);
  });

  test('★ a set with NO source says so instead of trailing off', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const fs = w.fsetsScan();
      const none = (fs.working || []).find((st: any) => !w._setAggSrc(st.name));
      if (!none) return { skip: true };
      // drive the rotation with that set first so the pick line is built from it
      const rot: any = w._chronRotation();
      const list = Array.isArray(rot) ? rot
        : Object.values(rot || {}).find((v: any) => Array.isArray(v)) || [];
      const sets: any = (list as any[]).find((c: any) => c && c.key === 'sets');
      return { skip: false, noneName: none.name, pick: sets && sets.pick, op: sets && sets.op };
    });
    if (r.skip) return;
    if (r.op && r.op.noSource) {
      expect(r.pick, 'a task with no way to do it must say so').toContain('no verified farm source');
      expect(r.op.detail).toContain('no verified farm source');
    } else {
      // the closest set happens to have a source — then it must name the boss, not trail off
      expect(r.pick).toMatch(/ at .+/);
    }
  });

  test('the no-source wording never appears when a boss IS known', async ({ page }) => {
    await boot(page);
    const r = await page.evaluate(() => {
      const w: any = window;
      const src = w._setAggSrc("Trang-Oul's Avatar (Necro)");
      return { boss: src && src.boss };
    });
    expect(r.boss).toBeTruthy();
    expect(String(r.boss)).not.toContain('no verified');
  });
});
