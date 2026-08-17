import { test, expect } from './_net_stub';
import { ensureCardExpanded } from './_cards';
import * as fs from 'fs';
import * as path from 'path';

// v1680 — EVERY SET IS TICKABLE, AND A MANUAL TICK CELEBRATES LIKE AN F·SETS ONE.
//
// Konyo, on a screenshot of Tools → Item Set Tracker: "are all the set items here as an option?
// and the tally manual should also share the same celebrations and tallies and chronicle sync
// meaning auto both ways if registered here manually and celebrated. so it needs to share the
// same logic coding in a couple of ways" — and, separately, "the title name for item tracker
// should be set green like the rest of the console too."
//
// The answer to his question was NO. renderSetTracker mapped ITEM_SETS — 12 sets / 54 pieces —
// while __allSets() (ITEM_SETS + SET_PIECES_EXTRA + SET_PIECES_EXTRA2) is 34 / 135, which is
// exactly what fsetsScan() already counts and what F·Sets already showed him. 22 sets and 81
// pieces had no manual tick option at all.
//
// THREE THINGS THIS FILE GUARDS, and each one broke a different way:
//
//  1. COVERAGE. The roster is the union, not the first third. Asserted against __allSets() itself
//     rather than the literal 34/135, so adding a set to the data extends the wall instead of
//     silently failing a hard-coded number.
//
//  2. THE CELEBRATION FIRES ON THE FIRST TICK OF A SESSION. The set chronicle celebrates off a
//     RISE, and the rise-detector needs a PREVIOUS number to rise from. On a fresh load
//     window.__chronPrevN is {} — zero keys — and the only thing that used to prime it was
//     renderForgeSets(). So a tick made from Tools without ever opening F·Sets primed instead of
//     celebrating, and the very first probe that "verified" this feature had to call
//     _setChronBeat() by hand to make a toast appear. That workaround WAS the bug. This test does
//     NOT prime: it loads the page and clicks, exactly as he would.
//
//  3. "(set)" IS A KEY, NOT A TITLE. 20 of the 34 names carry a literal " (set)" disambiguator in
//     the data. Invisible while only the 12 ITEM_SETS entries rendered; twenty card titles read
//     "Tancred's Battlegear (set)" the moment the roster opened up. Same class as v1630's "(slot)"
//     strip, and the same rule: strip where it is READ, never where it is STORED — so this file
//     also asserts the raw suffixed name still resolves, or the strip has eaten his data.
//
// Test 2 is the one worth re-reading: it was written against the pre-fix build first and fired
// ZERO celebrations. A celebration test that primes its own detector proves nothing.

const REPO = path.resolve(__dirname, '..');
const BOARD = 'file://' + path.join(REPO, 'bible.html');

// the data-side disambiguator that must never reach a rendered title
const SET_TAIL = /\(set\)/i;

async function openTracker(page) {
  await page.goto(BOARD, { waitUntil: 'load' });
  await page.waitForFunction(() => typeof (window as any).__allSets === 'function', null, { timeout: 20000 });
  /* v1751 — was a blind toggle wrapped in a catch commented "already expanded". The catch was
     dead (toggleCardCollapse never throws) and the toggle CLOSED the card whenever it was open. */
  await ensureCardExpanded(page, 'set-tracker-card', '#set-tracker .set-card');
}

test.describe('v1680 — the Item Set Tracker holds the whole roster', () => {
  test('★★★ every set the app knows about is on the wall, and every piece is tickable', async ({ page }) => {
    await openTracker(page);
    const m = await page.evaluate(() => {
      const all = (window as any).__allSets();
      return {
        dataSets: all.length,
        dataPieces: all.reduce((n, s) => n + s.pieces.length, 0),
        cards: document.querySelectorAll('#set-tracker .set-card').length,
        pieces: document.querySelectorAll('#set-tracker .set-piece').length,
        // a piece nobody can click is not an option, whatever the count says
        sized: [...document.querySelectorAll('#set-tracker .set-piece')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
        scan: (window as any).fsetsScan ? (window as any).fsetsScan().totalPieces : null,
      };
    });
    // the union, not a subset — this is the whole complaint
    expect(m.cards, `the wall shows ${m.cards} sets, the data has ${m.dataSets}`).toBe(m.dataSets);
    expect(m.pieces, `the wall shows ${m.pieces} pieces, the data has ${m.dataPieces}`).toBe(m.dataPieces);
    expect(m.sized, 'a set piece rendered at zero size cannot be ticked').toBe(m.pieces);
    // and the tracker agrees with the F·Sets meter it is supposed to be in sync with
    expect(m.pieces, 'the tracker and fsetsScan disagree on how many pieces exist').toBe(m.scan);
  });

  test('★★★ the FIRST tick of a session celebrates — no priming, F·Sets never opened', async ({ page }) => {
    await openTracker(page);
    const r = await page.evaluate(() => {
      const cel: any[] = [];
      const orig = (window as any)._chronCelebrate;
      (window as any)._chronCelebrate = function (o) { cel.push(o); return orig && orig.apply(this, arguments); };
      const piece = document.querySelector('#set-tracker .set-piece:not(.checked)') as HTMLElement;
      const label = piece ? piece.textContent!.trim() : null;
      piece && piece.click();
      const onTick = cel.length;
      // the SAME piece again — un-marking must never celebrate (v559.1)
      const again = [...document.querySelectorAll('#set-tracker .set-piece.checked')]
        .find((e) => e.textContent!.trim() === label) as HTMLElement;
      again && again.click();
      (window as any)._chronCelebrate = orig;
      return { onTick, onUntick: cel.length - onTick, first: cel[0] || null,
               fsetsActive: !!document.querySelector('#tab-fsets.active') };
    });
    // the fixture must actually be the case he described: F·Sets NOT open
    expect(r.fsetsActive, 'F·Sets is open, so this is not the Tools-only path he reported').toBe(false);
    expect(r.onTick, 'the first manual tick of the session fired no celebration').toBe(1);
    expect(r.first?.chron, 'the manual tick did not use the SET chronicle').toBe('set');
    // one shared path, called from both renderForgeSets and toggleSetPiece — but never twice
    expect(r.onTick, 'the tick celebrated more than once (double-fire)').toBeLessThan(2);
    expect(r.onUntick, 'un-ticking a piece celebrated — v559.1 says it never may').toBe(0);
  });

  test('★★★ "(set)" leaves the title, not the data', async ({ page }) => {
    await openTracker(page);
    const r = await page.evaluate(() => {
      const titles = [...document.querySelectorAll('#set-tracker .set-card-name')]
        .map((n) => n.textContent!.trim());
      const raw = (window as any).__allSets().map((s) => s.name).filter((n) => /\(set\)$/i.test(n));
      /* THE REAL INVARIANT IS THE ROUTE, NOT A RESOLVE COUNT. My first version of this asserted
         that all 20 suffixed names satisfy isSetAggregate — it fails 18/20, and that has nothing
         to do with the strip: two of those sets are simply not codex-backed, so their cards render
         as plain un-clickable titles and always did. What the strip must never do is change the
         string the card ROUTES with. So: for every routable card, the openDrop argument still
         carries the raw suffixed key while the visible text does not. */
      const routed = [...document.querySelectorAll('#set-tracker .set-card-open')].map((n) => ({
        shown: n.textContent!.replace(/[↗✓]/g, '').trim(),
        onclick: n.getAttribute('onclick') || '',
      }));
      const suffixedRouted = routed.filter((c) => raw.some(
        (n) => n.replace(/\s*\(set\)$/i, '') === c.shown));
      return {
        rendered: titles.filter((t) => /\(set\)/i.test(t)),
        rawCount: raw.length,
        suffixedRouted: suffixedRouted.length,
        // the route must still carry the DATA key, "(set)" and all
        routeKeepsKey: suffixedRouted.filter((c) => /\(set\)/i.test(c.onclick)).length,
        // the class tag on the original 12 is NOT the same thing and must survive
        classTags: titles.filter((t) => /\((Sorc|Barb|Necro|Ama|Sin|Pala|Druid)\)/.test(t)).length,
      };
    });
    // NON-VACUITY: if the data ever stops carrying the suffix this test is measuring nothing
    expect(r.rawCount, 'FIXTURE IS BLIND — no set name carries a "(set)" suffix any more').toBeGreaterThan(0);
    expect(r.suffixedRouted, 'FIXTURE IS BLIND — no suffixed set renders a routable card, so the '
                           + 'display-vs-key split below cannot be observed').toBeGreaterThan(0);
    expect(r.rendered, `${r.rendered.length} card title(s) still print "(set)"`).toEqual([]);
    expect(r.routeKeepsKey, 'a card dropped "(set)" from its openDrop key — the strip reached the DATA')
      .toBe(r.suffixedRouted);
    expect(r.classTags, 'the "(Sorc)"/"(Barb)" class tags were stripped too — those are not the suffix')
      .toBeGreaterThan(0);
  });

  test('★★★ every set card wears a real picture, not a shared shield', async ({ page }) => {
    /* v1684 — opening the roster to 34 exposed that 17 cards fell back to an identical generic
       🛡️, because their SET name resolves no art. Measured: all 17 have at least one PIECE that
       does, and stripping "(set)" recovers art for exactly 0 of them — so the emblem falls
       through to the first piece with art. Asserted as "no card is left on the text fallback",
       which is the thing he sees, rather than a filename list that rots as art is added. */
    await openTracker(page);
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#set-tracker .set-card')];
      return {
        cards: cards.length,
        shields: cards.filter((c) => !c.querySelector('.set-card-emblem img'))
          .map((c) => c.querySelector('.set-card-name')!.textContent!.trim()),
        // decoding, not just present: a broken <img> is a worse shield than the shield
        broken: cards.map((c) => c.querySelector('.set-card-emblem img') as HTMLImageElement | null)
          .filter((i) => i && i.complete && i.naturalWidth === 0).length,
      };
    });
    expect(r.cards).toBeGreaterThan(0);
    expect(r.shields, `${r.shields.length} set card(s) still show the generic shield: `
                    + r.shields.slice(0, 6).join(' · ')).toEqual([]);
    expect(r.broken, 'a set emblem resolved to an image that does not decode').toBe(0);
  });

  test('★★ the tracker title is set green, not chrome gold', async ({ page }) => {
    await openTracker(page);
    const r = await page.evaluate(() => {
      const mine = document.querySelector('#set-tracker-card .boss-name')!;
      const other = [...document.querySelectorAll('.boss-name')].find((n) => !n.closest('#set-tracker-card'))!;
      const token = getComputedStyle(document.documentElement).getPropertyValue('--q-set').trim();
      const probe = document.createElement('span');
      probe.style.color = token; document.body.appendChild(probe);
      const resolved = getComputedStyle(probe).color; probe.remove();
      return { mine: getComputedStyle(mine).color, other: getComputedStyle(other).color, resolved };
    });
    expect(r.mine, 'the Item Set Tracker title is not the --q-set token').toBe(r.resolved);
    // LAST RULE WINS is the live hazard here — a rule that loses at runtime looks fine in the diff
    expect(r.mine, 'the title still renders the same colour as every other card — the rule lost')
      .not.toBe(r.other);
  });
});
