/* v1633 — THE CHRONICLE CELEBRATION LADDER + ONE UNIQUE CHRONICLE PER MACHINE.
 *
 * Konyo asked for two things that turned out to be one job:
 *   1. "each 1 tally gets a celebration feature… 10..20..30..40... 100 should be more emphasized..
 *      200 even more emphasized. like scaling it up" — the Forge has had this since v558/v606/v618
 *      and the two GRAIL chronicles never got it.
 *   2. "for each PC its combined together as a one chronicle" / "fix them it should be like
 *      runeword and sets.. same logic" — d2r_owned + d2r_copies were the last chronicle stores
 *      still forked per PROFILE, so MAIN and LADDER kept separate lists of found uniques.
 *
 * The second is why the first needed care: a celebration fires off a RISING count, so as long as
 * MAIN and LADDER held different numbers under one memory, toggling profiles would have fired a
 * congratulation for finding nothing.
 */
// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import * as path from 'path';

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v1633 — the chronicle celebrates every tally', () => {
  test('★★★ the ladder never demotes as the count climbs', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(BOARD);
    await page.waitForTimeout(2400);
    expect(errs, 'the board must load clean').toEqual([]);

    const tiers = await page.evaluate(() => {
      const f = (window as any)._chronTier;
      if (typeof f !== 'function') return null;
      const at: Record<string, string> = {};
      for (const n of [1, 2, 7, 10, 20, 40, 99, 100, 137, 200, 300, 403])
        at[n] = f(n, 403);
      return { at, complete: f(403, 403), notComplete: f(402, 403) };
    });

    expect(tiers, '_chronTier must be exported — the ladder has to be assertable without pixels').not.toBeNull();
    const at = tiers!.at;

    // EVERY tally is celebrated: no count returns "nothing".
    for (const n of Object.keys(at))
      expect(at[n], `n=${n} must produce a celebration tier`).toBeTruthy();

    expect(at['1'],   'the first find gets its own moment').toBe('first');
    expect(at['2'],   'an ordinary tally still celebrates, at tick level').toBe('tick');
    expect(at['7'],   'an ordinary tally still celebrates, at tick level').toBe('tick');
    expect(at['10'],  'every tenth is a milestone').toBe('t1');
    expect(at['20'],  'every tenth is a milestone').toBe('t1');
    expect(at['40'],  'every tenth is a milestone').toBe('t1');
    expect(at['100'], '100 is emphasised above a plain milestone').toBe('t2');
    expect(at['200'], '200 is emphasised above 100').toBe('t3');
    expect(at['300'], 'past 200 the top tier is kept, never demoted').toBe('t3');
    expect(at['403'], 'the total is the completion moment').toBe('done');

    // "scaling it up" as an ORDERING, not five unrelated names: rank must be non-decreasing.
    const RANK: Record<string, number> = { tick: 0, first: 1, t1: 1, t2: 2, t3: 3, done: 4 };
    const climbing = [2, 7, 10, 20, 100, 200, 300, 403];
    let prev = -1;
    for (const n of climbing) {
      const r = RANK[at[n]];
      expect(r, `tier for n=${n} (${at[n]}) must not rank BELOW the previous milestone`).toBeGreaterThanOrEqual(
        n === 2 ? -1 : (n === 7 ? 0 : prev));
      if (n !== 7 && n !== 2) prev = r;
    }
  });

  test('★★★ the runeword and set chronicles are ONE per machine, across MAIN and LADDER', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2400);

    const keys = await page.evaluate(() => {
      const L: any = (window as any).LSR, was = (window as any).D2R_PROFILE;
      const read = (p: string, k: string) => { (window as any).D2R_PROFILE = p; return L.key(k); };
      const out = {
        shared:  ['d2r_setPieces', 'd2r_rwMade', 'd2r_foundLog'].map(k => [read('main', k), read('ladder', k)]),
        forked:  ['d2r_owned', 'd2r_runeStash'].map(k => [read('main', k), read('ladder', k)]),
      };
      (window as any).D2R_PROFILE = was;
      return out;
    });

    // What Konyo described, and what is actually true: the SET and RUNEWORD chronicles — and the
    // found-log the grail derives from — resolve to one key per machine, so a tally on LADDER and a
    // tally on MAIN climb the same number. This is why the celebration hook can key its memory on
    // LSR.key() and never fire a congratulation for merely switching profiles.
    for (const [m, l] of keys.shared)
      expect(l, `a machine-shared chronicle must resolve identically on both profiles (${m})`).toBe(m);

    // ...and forking still WORKS, so the assertion above means something rather than recording that
    // profile routing was switched off wholesale.
    for (const [m, l] of keys.forked)
      expect(l, `a per-profile store must still fork (${m})`).not.toBe(m);
  });

  test('★★★ a tally actually PAINTS — toast with a progress bar, overlay only above tick', async ({ page }) => {
    // motionOK() deliberately silences all of this when navigator.webdriver is true, so that an
    // automated run is never racing a full-screen overlay. That gate would also make the feature
    // untestable, so this ONE test presents itself as a real browser — which is precisely the code
    // path Konyo sees. Nothing else is stubbed: the real _chronCelebrate builds the real DOM.
    await page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
      /* v1518/REG-084 — spoofing navigator.webdriver unmasks this page as a GUEST (v1499),
         so every bare key seeded below would land in an `I·<id>·` world the app never reads
         and this spec would assert against a world that does not exist. Claim the owner
         world in the SAME init script that does the spoof, so the pairing cannot drift. */
      localStorage.setItem('d2r_ownerClaim', '*');
    });
    await page.goto(BOARD);
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => {
      const C: any = (window as any)._chronCelebrate;
      if (typeof C !== 'function') return null;
      const shot = (n: number, tot: number, chron: string) => {
        document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());
        const tier = C({ chron, icon: '🏆', noun: 'uniques', n, tot });
        const toast: any = document.querySelector('.chron-toast');
        const bar: any = toast && toast.querySelector('.ct-bar i');
        const epic: any = document.querySelector('.chron-epic');
        return {
          tier,
          toast: !!toast,
          barW: bar ? bar.style.width : null,
          barLit: bar ? getComputedStyle(bar).backgroundImage !== 'none' : false,
          epic: !!epic,
          epicCls: epic ? epic.className : null,
          runes: epic ? epic.querySelectorAll('.fe-rune').length : 0,
          txt: epic ? (epic.querySelector('.fe-txt') as any)?.textContent || '' : '',
        };
      };
      return { tick: shot(7, 403, 'uni'), ten: shot(20, 403, 'uni'),
               hundred: shot(100, 403, 'uni'), two: shot(200, 403, 'uni'),
               done: shot(135, 135, 'set') };
    });
    expect(r, '_chronCelebrate must be exported and callable').not.toBeNull();

    // EVERY tier paints the toast + a real, filled progress bar — the "in between" celebration.
    for (const k of ['tick', 'ten', 'hundred', 'two', 'done'] as const) {
      expect((r as any)[k].toast, `${k}: every tally must show a toast`).toBe(true);
      expect((r as any)[k].barW, `${k}: the toast must carry a progress bar with a width`).toBeTruthy();
      expect((r as any)[k].barLit, `${k}: the bar must actually be painted, not an empty div`).toBe(true);
    }
    expect(r!.tick.barW, 'the bar must show real progress, not a fixed width').toBe('2%');
    expect(r!.hundred.barW, 'the bar tracks the true percentage').toBe('25%');

    // An ordinary tally gets NO overlay — otherwise the milestones would not read as milestones.
    expect(r!.tick.epic, 'an ordinary tally must not throw up a full-screen overlay').toBe(false);
    for (const k of ['ten', 'hundred', 'two', 'done'] as const)
      expect((r as any)[k].epic, `${k}: a milestone must show the overlay`).toBe(true);

    // Scaling is visible in the markup, not just in the tier name.
    expect(r!.two.runes, '200 must throw more particles than a plain milestone')
      .toBeGreaterThan(r!.ten.runes);
    expect(r!.done.epicCls, 'a set milestone must wear the SET colour class').toContain('ce-set');
    expect(r!.done.txt, 'completing a chronicle must say so').toContain('COMPLETE');
    expect(r!.hundred.txt, 'a numbered milestone must name the number').toContain('100');
  });
});
