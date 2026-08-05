import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1556 → v1630 — THE PREMISE MOVED. THE CONCERN DID NOT.
//
// WHAT v1556 DEFENDED. The Sessions hub carried a 🏆 HOLY GRAIL meter (#hub-meter, built by
// window._hubMeter). Its caption said "160 grails still out there" — 403 − 243, the GAME's
// denominator — while only 125 of those 160 have a card and a source in this app (internal-typo
// aliases, the 8 Rainbow Facet rows, quest uniques and RotW customs cannot be hunted, ranked or
// ticked here). So the meter promised 35 more hunts than it could keep, and v1556 pinned the
// caption to say both numbers.
//
// WHY THE METER IS GONE (v1630, item B). Konyo: "the HOLY GRAIL on the right corner top it can be
// like removed.. we have this in sessions already on the bottom along with the sets. so its just
// taking up space.. rather it be structured so i can see THE HUNT". The meter said 243 / 403 and
// the DAILY TASK FORCE row twelve inches below it said Grail Uniques · 243 / 403. One fact, twice,
// and the duplicate pushed the TZ tracker below the fold. The element and its builder were deleted.
//
// THIS FILE IS NOT RETREATING — IT IS SWAPPING PREMISE. The meter's caption was never the point;
// the point was that his grail numbers must be TRUE and VISIBLE. They still are, on the Daily Task
// Force rows, which is where he already reads them. So:
//   · the board export test below is UNCHANGED (it never touched the meter and is still exactly
//     true: found 243 / chronTotal 403 / carded 368 / huntable 125),
//   · the caption tests are REPLACED by tests that read the Task Force rows out of the LIVE
//     document and prove the numbers MOVE WITH the seeded payload (markup cannot fake them),
//   · a DUPLICATION GUARD is added — #hub-meter is null, _hubMeter is not a function, and the
//     grail found/total pair appears in exactly ONE region of the hub — so "removed" is a
//     guarantee and a future re-add goes red,
//   · the Ⅰ banner rename (THE HUNT → TZ TRACKER, item B2) is pinned by CLASS, not by old text.
//
// ONE THING GENUINELY LOST, STATED OUT LOUD: the honest-coverage caveat ("125 with a known hunt
// here") had exactly one surface in the whole product — the meter's caption. With the meter gone,
// no user-visible surface states the 160-vs-125 distinction. The DATA still exists (the board
// still computes and publishes grail.huntable into d2r_forgeSummary), so the last test below
// guards the export rather than pretending a surface carries it. If a surface is ever chosen for
// it, assert it there and delete that test's apology.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

type Payload = { grail: any; sets?: any };

// Render the Sessions hub with a seeded forgeSummary. Same scaffolding v1556 used (route the /ui
// document, seed the lsFork route as "bare" so the console reads the bare key rather than us
// guessing its prefix) — only the seam changed: _hubMeter is gone, _hubResync is the published
// handle that repaints the Task Force.
async function hub(page: any, p: Payload) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  // FULFILL, never abort — an aborted document/API leaves the console mid-boot and a red here
  // would be the stub's fault, not the app's.
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await seed(page, p);
}

async function seed(page: any, p: Payload) {
  await page.evaluate((q: Payload) => {
    document.body.dataset.view = 'sessions';
    localStorage.setItem('d2r_lsrRoute', JSON.stringify({ prefix: '' }));
    localStorage.setItem('d2r_forgeSummary', JSON.stringify(q));
  }, p);
  // NO optional chaining: if the repaint seam is missing the test must FAIL loudly, not quietly
  // render nothing and let a zero-row scan pass.
  await page.evaluate(() => (window as any)._hubResync());
  await page.waitForTimeout(700);   // _hubResync debounces 260ms
}

// Read the chronicle rows out of the LIVE document — the rendered numbers, not a restated constant.
async function chronRows(page: any) {
  const rows = await page.evaluate(() => {
    const out: any[] = [];
    document.querySelectorAll('#hd-tf-rows .tf-row.tf-chron').forEach((r: Element) => {
      const t = (r.querySelector('.tf-t') as HTMLElement | null);
      const b = (r.querySelector('.tf-t b') as HTMLElement | null);
      const tag = (r.querySelector('.tf-tag') as HTMLElement | null);
      const txt = ((t && t.textContent) || '').replace(/\s+/g, ' ').trim();
      // v1636 MOVED the count out of the sentence into its own cell so the three chronicles line
      // up as columns: `<span class="tf-n">243<i>/</i><u>403</u></span>`. This parser still read
      // `found / total` out of .tf-t, found no match, and returned null for BOTH numbers — so
      // three tests failed on `Expected 243, Received null` while the app was rendering perfectly.
      // Read the count where it now lives, and fall back to the sentence so an older render (or a
      // regression that puts it back) is still parsed rather than silently reported as null.
      const n = (r.querySelector('.tf-n') as HTMLElement | null);
      const numTxt = ((n && n.textContent) || '').replace(/\s+/g, ' ').trim();
      const m = numTxt.match(/(\d+)\s*\/\s*(\d+)/) || txt.match(/(\d+)\s*\/\s*(\d+)/);
      out.push({
        name: ((b && b.textContent) || '').trim(),
        found: m ? +m[1] : null,
        total: m ? +m[2] : null,
        tag: ((tag && tag.textContent) || '').trim(),
        text: txt,
      });
    });
    return out;
  });
  // a zero-node scan is a FAILURE, not a vacuous pass
  expect(rows.length, 'the Daily Task Force must render chronicle rows at all').toBeGreaterThan(0);
  return rows as any[];
}
const pick = (rows: any[], name: string) => rows.find((r) => r.name === name);

test.describe('v1630 — the grail numbers live on the Task Force, once', () => {
  // UNCHANGED FROM v1556 — this never read the meter. The board's own export is still the honest
  // source of the 403-vs-368 gap, and its numbers are not adjusted here.
  test('★ the board exports how many missing grails are HUNTABLE', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.funiScan();
      const huntable = (s.missing || []).filter((x: any) => !!w._pickSrc(x.sources)).length;
      return { found: s.found, chronTotal: s.chronTotal, carded: s.total,
        missing: (s.missing || []).length, huntable,
        gap: (s.chronTotal - s.found) - huntable };
    });
    expect(r.huntable, 'every missing item with a card must have a source').toBe(r.missing);
    expect(r.gap, 'the game counts more still-out-there than this app has cards for')
      .toBeGreaterThan(0);
    expect(r.chronTotal).toBeGreaterThan(r.carded);
  });

  test('★ the Task Force rows carry his grail and set numbers', async ({ page }) => {
    // the expectations are read back off the SEED object, never re-typed as literals
    const P: Payload = { grail: { found: 243, total: 403, carded: 368, huntable: 125 },
                         sets: { found: 108, total: 135 } };
    await hub(page, P);
    const rows = await chronRows(page);

    const u = pick(rows, 'Grail Uniques');
    expect(u, 'the Grail Uniques chronicle row must exist').toBeTruthy();
    expect(u.found).toBe(P.grail.found);
    expect(u.total).toBe(P.grail.total);

    const s = pick(rows, 'Sets');
    expect(s, 'the Sets chronicle row must exist').toBeTruthy();
    expect(s.found).toBe(P.sets.found);
    expect(s.total).toBe(P.sets.total);

    // the percentage uses the GAME denominator (243/403 = 60%), not the carded 368 (which would
    // read 66% and overstate his grail). Computed from the seed, not typed.
    expect(u.tag).toBe(Math.round(P.grail.found / P.grail.total * 100) + '%');
    expect(u.tag).not.toBe(Math.round(P.grail.found / P.grail.carded * 100) + '%');

    // and the remainder is still stated, in the row's own note
    expect(u.text).toContain(String(P.grail.total - P.grail.found));
  });

  test('★★ the rendered numbers MOVE with the payload (markup cannot fake them)', async ({ page }) => {
    const A: Payload = { grail: { found: 243, total: 403 }, sets: { found: 108, total: 135 } };
    const B: Payload = { grail: { found: 301, total: 411 }, sets: { found: 117, total: 140 } };
    await hub(page, A);
    const a = await chronRows(page);
    await seed(page, B);
    const b = await chronRows(page);

    const ua = pick(a, 'Grail Uniques'), ub = pick(b, 'Grail Uniques');
    const sa = pick(a, 'Sets'),          sb = pick(b, 'Sets');
    expect(ua && ub && sa && sb, 'both renders must produce both chronicle rows').toBeTruthy();
    expect(ua.found).toBe(A.grail.found);
    expect(ub.found).toBe(B.grail.found);
    expect(ub.total).toBe(B.grail.total);
    expect(sb.found).toBe(B.sets.found);
    expect(sb.total).toBe(B.sets.total);
    expect(ub.found, 'a hardcoded row would not have moved').not.toBe(ua.found);
    expect(ub.tag).toBe(Math.round(B.grail.found / B.grail.total * 100) + '%');
  });

  test('★★ the duplicate meter is REMOVED, not merely hidden', async ({ page }) => {
    const P: Payload = { grail: { found: 243, total: 403, carded: 368, huntable: 125 },
                         sets: { found: 108, total: 135 } };
    await hub(page, P);

    const gone = await page.evaluate(() => ({
      el: document.getElementById('hub-meter') === null,
      builder: typeof (window as any)._hubMeter !== 'function',
      classHits: document.querySelectorAll('.hub-meter').length,
    }));
    expect(gone.el, '#hub-meter must not exist after the hub renders').toBe(true);
    expect(gone.builder, 'window._hubMeter must be gone with its element').toBe(true);
    expect(gone.classHits, 'no orphan .hub-meter host may remain').toBe(0);

    // …and the found/total pair is printed in exactly ONE place in the Sessions hub. Counted on
    // the DEEPEST elements that carry it, so ancestors do not inflate the count.
    const regions = await page.evaluate((pair: string) => {
      const root = document.getElementById('home-dash');
      if (!root) return -1;                       // fail loudly rather than pass on a missing hub
      // v1636 renders the pair as `243<i>/</i><u>403</u>`, whose textContent is "243/403" with NO
      // spaces, while this guard searched for "243 / 403" and therefore found ZERO — reporting a
      // missing meter as if it were a duplicate-free hub. Collapse the spacing around the slash on
      // BOTH sides so either rendering is caught: the guard gets STRONGER, not looser.
      const norm = (s: string) => (s || '').replace(/\s+/g, ' ').replace(/\s*\/\s*/g, '/');
      const hits: Element[] = [];
      root.querySelectorAll('*').forEach((el) => {
        if (norm(el.textContent || '').indexOf(pair) === -1) return;
        for (let i = 0; i < el.children.length; i++) {
          if (norm(el.children[i].textContent || '').indexOf(pair) !== -1) return;  // not deepest
        }
        hits.push(el);
      });
      return hits.length;
    }, `${P.grail.found}/${P.grail.total}`);
    expect(regions, 'the hub must not print the grail pair in two places').toBe(1);
  });

  test('★ the Ⅰ zone banner reads TZ TRACKER', async ({ page }) => {
    // located by CLASS (.zone-banner.zone-hunt), never by the old text — v1630 renamed the label
    // ("THE HUNT" → "TZ TRACKER") because what the zone renders IS the terror-zone tracker.
    const P: Payload = { grail: { found: 243, total: 403 }, sets: { found: 108, total: 135 } };
    await hub(page, P);
    const z = await page.evaluate(() => {
      const el = document.querySelector('.zone-banner.zone-hunt');
      if (!el) return null;
      const sub = el.querySelector('.zb-sub');
      const full = (el.textContent || '').replace(/\s+/g, ' ').trim();
      const subTxt = ((sub && sub.textContent) || '').replace(/\s+/g, ' ').trim();
      return { full, label: subTxt ? full.replace(subTxt, '').trim() : full };
    });
    expect(z, 'the Ⅰ zone banner must exist').not.toBeNull();
    expect(z!.label.toUpperCase()).toContain('TZ TRACKER');
    expect(z!.full, 'the old label must be gone from user-visible text').not.toMatch(/\bTHE HUNT\b/i);
  });

  test('the honest-coverage number still EXISTS in the bridge, even with no surface for it', async ({ page }) => {
    // Stated plainly: with #hub-meter deleted, the 160-vs-125 caveat has no user-visible home. The
    // board still publishes it, so the fact is not lost — only unshown. This test keeps the export
    // alive so a future surface has something true to render. If one is built, assert it THERE.
    await page.goto(BOARD);
    await page.waitForTimeout(2000);
    const g = await page.evaluate(() => {
      const raw = localStorage.getItem('d2r_forgeSummary');
      if (!raw) return null;
      const fsum = JSON.parse(raw);
      return fsum && fsum.grail ? fsum.grail : null;
    });
    expect(g, 'the board must publish a grail block on d2r_forgeSummary').not.toBeNull();
    expect(typeof g!.huntable, 'grail.huntable must survive the meter it used to feed').toBe('number');
    expect(g!.huntable).toBeGreaterThan(0);
    expect(g!.huntable, 'the app can guide fewer hunts than the game still counts')
      .toBeLessThan(g!.total - g!.found);
  });
});
