import { test, expect } from './_net_stub';
import * as path from 'path';

// v775–v778 — THE NIGHT WAVES family lock. The five workshop tabs (Session · Tools · Forge ·
// F-Uniques · F-Sets) are one console product family: each carries a spine header (emblem + serif
// GOLD title + purpose/stat rail), no tab overflows its column at any width, the forge siblings'
// right-aligned section subs clear the corner FAB, and the ⌂ CONSOLE return pill shows ONLY in the
// app context (?app=1). This spec is the tripwire — it goes red if any tab drifts out of the family.
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const GOLD = 'rgb(240, 192, 96)';   // #f0c060 — the unified family title accent (v775)

// spine + title selectors per tab: Session sc-hero-tf, Tools tvf-spine, and the three forge
// siblings share .forge-head.tvf-head + .forge-title (all recolored gold in v775).
/* v1625 ITEM6 gave the two tabs that NAME an in-game quality their own title colour — F·Uniques
   wears unique tan, F·Sets wears set green — while Sessions/Tools/Forge-plain keep the v775 family
   gold because they have no quality to wear. v775 predates that and demanded gold everywhere, so
   it failed on exactly the two tabs the newer rule was written for. The family check survives; the
   two documented exceptions are now stated instead of asserted away. */
const UNIQUE = 'rgb(199, 179, 119)';   // --q-unique #c7b377
const SET    = 'rgb(0, 252, 0)';       // --q-set    #00fc00
const RUNE   = 'rgb(255, 125, 60)';    // --rune     #ff7d3c
const TAB: Record<string, { spine: string; title: string; want?: string }> = {
  session: { spine: '#tab-session .sc-hero-tf',        title: '#tab-session .sc-title' },
  tools:   { spine: '#tools-spine.tvf-spine',          title: '#tools-spine .tvf-title' },
  /* 2026-08-13 — KONYO RULED (bible.html:7924 ruling block, superseding the v1707 note this
     comment used to carry): the Forge room wears its TAB'S RUNE colour, not the runeword/unique
     gold — "these two colors cant be the same... RUNEWORD is separate from the F-UNIQUES" (v1631).
     An item NAME obeys the game; A TAB IS A LABEL FOR A ROOM. This row had fallen through to the
     family accent GOLD (#f0c060) before v1685 moved the rule below :7424; the expectation now
     moves to RUNE, and v1685_forge_family_identity.spec.ts remains the authority on this rule. */
  forge:   { spine: '#tab-forge .forge-head.tvf-head', title: '#tab-forge .forge-title', want: RUNE },
  funi:    { spine: '#tab-funi .forge-head.tvf-head',  title: '#tab-funi .forge-title', want: UNIQUE },
  fsets:   { spine: '#tab-fsets .forge-head.tvf-head', title: '#tab-fsets .forge-title', want: SET },
};

test.describe('v775 — the five tabs are one console family', () => {
  for (const [name, sel] of Object.entries(TAB)) {
    test(`${name}: console spine present + GOLD serif title, no h-overflow @1280/1500/1920`, async ({ page }) => {
      await page.goto(URL); await page.waitForTimeout(1400);
      for (const vw of [1500, 1280, 1920]) {
        await page.setViewportSize({ width: vw, height: 980 });
        const r = await page.evaluate(({ n, s, t }) => {
          const w: any = window; w.switchTab(n); w.scrollTo(0, 0);
          const spine = document.querySelector(s);
          const title = document.querySelector(t) as HTMLElement | null;
          const de = document.documentElement;
          return {
            spine: !!spine,
            title: !!title,
            color: title ? getComputedStyle(title).color : null,
            overflow: de.scrollWidth - window.innerWidth,
          };
        }, { n: name, s: sel.spine, t: sel.title });
        expect(r.spine, `${name} spine present @${vw}`).toBe(true);
        expect(r.title, `${name} title present @${vw}`).toBe(true);
        expect(r.color, `${name} title colour @${vw}`).toBe(sel.want || GOLD);
        expect(r.overflow, `${name} no h-overflow @${vw}`).toBeLessThanOrEqual(1);
      }
    });
  }

  test('funi/fsets: right-aligned section subs clear the corner FAB (unclipped)', async ({ page }) => {
    await page.setViewportSize({ width: 1500, height: 980 });
    await page.goto(URL); await page.waitForTimeout(1400);
    for (const tab of ['funi', 'fsets']) {
      const clipped = await page.evaluate((t) => {
        const w: any = window; w.switchTab(t); w.scrollTo(0, 0);
        const fab = document.querySelector('.nav-fab');
        const fabLeft = fab ? fab.getBoundingClientRect().left : Infinity;
        let clip = false;
        document.querySelectorAll('.tab-content.active .forge-sec-sub').forEach((s) => {
          const rc = (s as HTMLElement).getBoundingClientRect();
          if (rc.width > 0 && rc.right > fabLeft - 2) clip = true;
        });
        return clip;
      }, tab);
      expect(clipped, `${tab} section subtitle overlaps the FAB`).toBe(false);
    }
  });

  test('⌂ CONSOLE pill: present in app context (?app=1) and returns to the console (/)', async ({ page }) => {
    await page.goto(URL + '?app=1'); await page.waitForTimeout(1200);
    const app = await page.evaluate(() => {
      const el = document.getElementById('tvf-console-return');
      return { pill: !!el, cls: document.body.classList.contains('app-ctx'), txt: el ? el.textContent || '' : '' };
    });
    expect(app.pill, 'pill present with ?app=1').toBe(true);
    expect(app.cls, 'body.app-ctx set').toBe(true);
    expect(app.txt).toContain('CONSOLE');
    // clicking sets location to '/' (the console root); on file:// that navigates to file:///
    await page.click('#tvf-console-return').catch(() => {});
    await page.waitForTimeout(500);
    // note: the `URL` const above shadows the global — use globalThis.URL for the constructor
    expect(new globalThis.URL(page.url()).pathname, 'pill navigates to /').toBe('/');
  });

  test('⌂ CONSOLE pill: ABSENT without ?app=1 (the browser tab / file://)', async ({ page }) => {
    await page.goto(URL); await page.waitForTimeout(1000);
    const r = await page.evaluate(() => ({
      pill: !!document.getElementById('tvf-console-return'),
      cls: document.body.classList.contains('app-ctx'),
    }));
    expect(r.pill, 'no pill without ?app=1').toBe(false);
    expect(r.cls, 'no app-ctx class without ?app=1').toBe(false);
  });

  // v778 — the board must not lag the app on stop. The agent stamps st.stopping the instant the
  // ≤90s farewell begins (its bridge still answers online:true); the receiver drops to offline on the
  // very next poll so the website never glows after the app shows stopped.
  test('TV·D board leaves LIVE within one poll of the agent reporting stopping', async ({ page }) => {
    const BRIDGE = 'http://127.0.0.1:17771/state';
    let stopping = false;
    await page.route(BRIDGE + '**', (route) =>
      route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({
          online: true, startedAt: 1, now: Date.now(), readCount: 1, stopping,
          beat: { ts: Date.now(), phase: 'watching', motion: 0.08 }, events: [], reads: [],
        }),
      })
    );
    await page.goto(URL); await page.waitForTimeout(1400);
    await page.evaluate(() => (window as any).switchTab('tvd')); await page.waitForTimeout(300);
    await page.evaluate(() => (window as any)._tvdToggle());
    await page.waitForTimeout(1000);
    const live = await page.evaluate(() => document.getElementById('tvb-screen')!.className);
    expect(live, 'board is LIVE before the farewell').toContain('tvb-live');

    // farewell begins: bridge still online:true, but stopping:true
    stopping = true;
    await page.waitForTimeout(900);   // poll runs every 250ms — one cycle is plenty
    const after = await page.evaluate(() => document.getElementById('tvb-screen')!.className);
    expect(after, 'board must leave LIVE the moment stopping arrives').not.toContain('tvb-live');
    expect(after, 'board drops to offline on stopping').toContain('tvb-offline');
  });
});
