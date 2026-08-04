/* v1634 — THE CRAFT BENCH JOINS THE CELEBRATION LADDER.
 *
 * v1633 built one celebration engine (_chronCelebrate / _chronTier) and wired the two GRAIL
 * chronicles to it. The craft bench was left out for an honest reason: the Forge's craft section is
 * a PLANNER, and a planner has no "I made this" moment to fire from. Konyo's answer was to create
 * one — "no need for a craft tally.. just when created in general and made one a celebration
 * trigger for it" — so v1634 records the recipe in a chronicle store (d2r_craftMade) and celebrates
 * the RISE.
 *
 * WHAT THIS SPEC REFUSES TO ACCEPT AS EVIDENCE, and why each refusal cost this project a ship:
 *
 *   - A DECLARED total. The ladder's "done" tier is n === tot, so a wrong tot means the completion
 *     moment never fires (too high) or fires early forever (too low). The expected total is
 *     therefore COMPUTED IN THE PAGE from the live CRAFTS array. Add a tenth slot to a craft and
 *     this test still passes; hardcode 36 and it would go red on Konyo's next recipe.
 *
 *   - A DECLARED fork doctrine. "d2r_craftMade is machine-shared" is a claim about LSR.key(), not
 *     about a comment. So the assertion is a CONTRAST: the chronicle key must resolve identically
 *     on main and ladder, while d2r_craftStash — the per-profile owned tally living beside it —
 *     must resolve DIFFERENTLY across those same two profiles. Without the second half, switching
 *     profile routing off wholesale would pass.
 *
 *   - A colour asserted as a hex literal. v1621/v1622: a spec that copies a value defends the copy,
 *     not the rule. The crafted-orange is READ from the document through tests/_palette.ts and
 *     compared to what the celebration actually computes.
 *
 *   - Silence read as success. motionOK() returns false when navigator.webdriver is true, so under
 *     plain automation _chronCelebrate returns null and paints NOTHING. A test that asserted "no
 *     toast after undo" without lifting that gate would be green on a completely dead feature.
 *     Every test below that touches paint presents itself as a real browser first — the same code
 *     path Konyo sees — which is what makes the v559.1 undo assertion non-vacuous.
 *
 * Modelled on tests/v1633_chronicle_celebration.spec.ts (the webdriver override) and
 * tests/v949_chronicle_sync.spec.ts (asserting store routing from _LP_FORKED / _WP_FORKED).
 *
 * MUTATION LOG — each claim below was proved able to fail by breaking bible.html and watching this
 * spec go RED, then restoring the file byte-for-byte (md5 verified):
 *   rise-only ........ dropped the `!_s.has(_id)` guard and relaxed `_cn > _prev` to `>=`, so the
 *                      hook fires on any WRITE rather than a RISE           → RED
 *   fork doctrine .... removed 'd2r_craftMade' from the _WP_FORKED concat   → RED
 *   derived total .... replaced _craftRecipeTot's reduce with `return 35`   → RED
 *   undo is quiet .... made forgeUncraft call _chronCelebrate after removal → RED
 *   crafted-orange ... repointed .ce-craft's --cec at the SET token         → RED
 * ONE mutation stayed GREEN and is recorded here rather than hidden: replacing the reduce with
 * `return 36` — today's correct answer written down. No runtime assertion can tell a derivation
 * from a literal that currently agrees with it; what test 2 does guarantee is that the number is
 * BOUND to CRAFTS, so the literal goes red the moment Konyo adds a recipe. That is the failure
 * mode worth catching, and it is caught.
 */
import { test, expect } from '@playwright/test';
import * as path from 'path';
import { boardTokens, assertTokens } from './_palette';

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* The chronicle store and the per-profile store it must NOT behave like. Named once. */
const CHRON_KEY = 'd2r_craftMade';
const FORKED_NEIGHBOUR = 'd2r_craftStash';

/* Wipe every routing of the craft chronicle BEFORE the board boots, so "the first craft" is really
 * the first. Bare = MAIN/Mac, L· = ladder, W·/WL· = the Windows cousin. Left-over rows from an
 * earlier run would make the "first" tier unreachable and quietly downgrade test 4 to a tick. */
async function freshChronicle(page: any) {
  await page.addInitScript((k: string) => {
    for (const p of ['', 'L·', 'W·', 'WL·']) { try { localStorage.removeItem(p + k); } catch (e) {} }
  }, CHRON_KEY);
}

/* Celebrations are gated on motionOK(), which is false under automation. Lift the gate the way
 * v1633 does — nothing else is stubbed; the real engine builds the real DOM. */
async function asRealBrowser(page: any) {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
  });
}

/* Read the chronicle straight out of the store the app routed it to — the truth the count is
 * derived FROM, not the number the UI happens to be showing. Returns the recipe ids. */
const READ_IDS = (k: string) => {
  const w: any = window;
  let raw: any = null;
  try { raw = localStorage.getItem(w.LSR.key(k)); } catch (e) { return []; }
  let v: any = null;
  try { v = JSON.parse(raw || 'null'); } catch (e) { return []; }
  if (!v) return [];
  if (Array.isArray(v)) return v.map(String);
  if (typeof v === 'object') return Object.keys(v).filter(id => v[id] !== false && v[id] !== 0);
  return [];
};

test.describe('v1634 — the craft bench climbs the same ladder', () => {
  test('★★★ the ladder is the SHARED one, and it never demotes as crafts accumulate', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(String(e)));
    await page.goto(BOARD);
    await page.waitForTimeout(2400);
    expect(errs, 'the board must load clean').toEqual([]);

    const r = await page.evaluate(() => {
      const f = (window as any)._chronTier;
      if (typeof f !== 'function') return null;
      const at: Record<string, string> = {};
      for (const n of [1, 2, 7, 9, 10, 20, 36, 99, 100, 101, 199, 200, 250, 300]) at[n] = f(n, 403);
      return {
        at,
        doneAtTot: f(36, 36),          // a craft-sized chronicle completes at its own total…
        notDone: f(35, 36),            // …and not one before it
        doneIsTotalRelative: f(36, 403), // 36 is nothing special against a 403-long chronicle
      };
    });
    expect(r, '_chronTier must be exported — v1634 must reuse v1633 ladder, not fork a second one').not.toBeNull();
    const at = r!.at;

    /* EVERY tally celebrates: no count is allowed to return nothing. That is the whole ask. */
    for (const n of Object.keys(at))
      expect(at[n], `n=${n} must produce a celebration tier`).toBeTruthy();

    expect(at['1'], 'the first craft gets its own moment').toBe('first');
    expect(at['2'], 'an ordinary craft still celebrates, at tick level').toBe('tick');
    expect(at['7'], 'an ordinary craft still celebrates, at tick level').toBe('tick');
    expect(at['9'], 'an ordinary craft still celebrates, at tick level').toBe('tick');
    expect(at['10'], 'every tenth is a milestone').toBe('t1');
    expect(at['20'], 'every tenth is a milestone').toBe('t1');
    expect(at['100'], '100 is emphasised above a plain milestone').toBe('t2');
    expect(at['101'], 'past 100 an ordinary tally is ordinary again').toBe('tick');
    expect(at['200'], '200 is emphasised above 100').toBe('t3');
    expect(at['300'], 'past 200 the top tier is kept, never demoted').toBe('t3');

    /* "done" is TOTAL-relative, which is the property the craft chronicle depends on: its total is
     * 36, not 403, so 36 must complete it — and must NOT complete a longer one. */
    expect(r!.doneAtTot, 'a chronicle completes at ITS OWN total').toBe('done');
    expect(r!.notDone, 'one short of the total is not completion').not.toBe('done');
    expect(r!.doneIsTotalRelative, 'the same n against a longer chronicle is not completion').not.toBe('done');

    /* Scaling as an ORDERING, not five unrelated names. */
    const RANK: Record<string, number> = { tick: 0, first: 1, t1: 1, t2: 2, t3: 3, done: 4 };
    let prev = -1;
    for (const n of [10, 20, 100, 200, 300]) {
      const rank = RANK[at[n]];
      expect(rank, `tier for n=${n} (${at[n]}) must not rank BELOW the previous milestone`).toBeGreaterThanOrEqual(prev);
      prev = rank;
    }
  });

  test('★★★ the craft total is DERIVED from the live recipe book, not written down', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2400);

    const r = await page.evaluate(() => {
      const w: any = window;
      if (typeof w._craftChronCount !== 'function') return { missing: true } as any;
      const c = w._craftChronCount();
      const CR = w.CRAFTS || [];
      return {
        missing: false,
        tot: c && c.tot,
        expected: CR.reduce((a: number, x: any) => a + Object.keys(x.slots || {}).length, 0),
        recipes: CR.length,
        slotsPerCraft: CR.map((x: any) => Object.keys(x.slots || {}).length),
      };
    });

    expect(r.missing, '_craftChronCount must be exported so the craft ladder is assertable').toBe(false);

    /* Non-vacuity first: a reduce over an EMPTY CRAFTS is 0, and 0 === 0 would pass while proving
     * nothing at all. Pin that there is a real recipe book underneath before comparing. */
    expect(r.recipes, 'CRAFTS must actually hold recipes — comparing two zeroes proves nothing').toBeGreaterThan(0);
    expect(r.expected, 'the derived total must be a real count, not an empty reduce').toBeGreaterThan(0);
    for (const n of r.slotsPerCraft)
      expect(n, 'every craft must contribute slots to the total').toBeGreaterThan(0);

    /* …and the app's number must BE that number. Add a recipe and both sides move together; this
     * assertion survives it, where a literal 36 would have to be edited. */
    expect(r.tot, 'the craft chronicle total must equal the recipe book, computed live').toBe(r.expected);
  });

  test('★★★ the craft CHRONICLE is one per machine, while the craft STASH stays per profile', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2400);

    const r = await page.evaluate(([chron, forked]) => {
      const w: any = window, L = w.LSR, was = w.D2R_PROFILE;
      const key = (p: string, k: string) => { w.D2R_PROFILE = p; return L.key(k); };
      const out = {
        /* membership read from the real sets — never a hardcoded doctrine */
        chronInLP: w._LP_FORKED.has(chron),
        chronInWP: w._WP_FORKED.has(chron),
        stashInLP: w._LP_FORKED.has(forked),
        stashInWP: w._WP_FORKED.has(forked),
        /* the shape the set + runeword chronicles already have, for comparison */
        setPiecesInLP: w._LP_FORKED.has('d2r_setPieces'),
        setPiecesInWP: w._WP_FORKED.has('d2r_setPieces'),
        rwMadeInLP: w._LP_FORKED.has('d2r_rwMade'),
        rwMadeInWP: w._WP_FORKED.has('d2r_rwMade'),
        chronMain: key('main', chron), chronLadder: key('ladder', chron),
        stashMain: key('main', forked), stashLadder: key('ladder', forked),
      };
      w.D2R_PROFILE = was;
      return out;
    }, [CHRON_KEY, FORKED_NEIGHBOUR]);

    /* A craft record is a CHRONICLE, so it must wear the chronicle shape exactly: out of the
     * profile fork (MAIN and LADDER are one memory), inside the machine fork (the Windows cousin
     * keeps its own bench). Asserted against the two chronicles that already work, so this test
     * describes a rule rather than a preference. */
    expect(r.setPiecesInLP, 'baseline: the set chronicle is not profile-forked').toBe(false);
    expect(r.setPiecesInWP, 'baseline: the set chronicle IS machine-forked').toBe(true);
    expect(r.rwMadeInLP, 'baseline: the runeword chronicle is not profile-forked').toBe(false);
    expect(r.rwMadeInWP, 'baseline: the runeword chronicle IS machine-forked').toBe(true);

    expect(r.chronInLP, `${CHRON_KEY} must NOT be profile-forked — a craft you made is a craft you made`).toBe(false);
    expect(r.chronInWP, `${CHRON_KEY} must be machine-forked, like every other chronicle`).toBe(true);

    /* The CONTRAST that makes the claim real: the owned-count stash beside it still forks. */
    expect(r.stashInLP, `${FORKED_NEIGHBOUR} is per-profile inventory and must STILL fork`).toBe(true);

    /* Membership is doctrine; key resolution is what the app actually stores under. */
    expect(r.chronLadder, 'the craft chronicle must resolve to ONE key across main and ladder').toBe(r.chronMain);
    expect(r.stashLadder, 'the per-profile stash must still resolve to a DIFFERENT key on ladder').not.toBe(r.stashMain);
  });

  test('★★★ the first craft CELEBRATES in crafted-orange; a repeat does not; undo never does', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(String(e)));
    await freshChronicle(page);
    await asRealBrowser(page);
    await page.goto(BOARD);
    await page.waitForTimeout(2400);
    expect(errs, 'the board must load clean').toEqual([]);

    /* Discover a real recipe from the live CRAFTS — never a remembered name. RotW's data is the
     * mod's, and a guessed craft/slot pair would be silently dropped by forgeCrafted. */
    const pick = await page.evaluate((k: string) => {
      const w: any = window;
      const CR = w.CRAFTS || [];
      const have = new Set((function () {
        try { const v = JSON.parse(localStorage.getItem(w.LSR.key(k)) || 'null');
              return v ? (Array.isArray(v) ? v.map(String) : Object.keys(v)) : []; } catch (e) { return []; }
      })());
      for (const c of CR) for (const s of Object.keys(c.slots || {}))
        if (!have.has(c.key + ' ' + s) && !have.has(c.key + '·' + s)) return { ck: c.key, slot: s };
      return null;
    }, CHRON_KEY);
    expect(pick, 'the live CRAFTS array must offer an unrecorded recipe to log').not.toBeNull();

    const before = await page.evaluate(READ_IDS, CHRON_KEY);
    expect(before.length, 'the chronicle must start empty for "first" to be reachable — otherwise this test silently downgrades to a tick').toBe(0);

    /* ── 4. FIRST CRAFT CELEBRATES ─────────────────────────────────────────────────────────── */
    const first = await page.evaluate(([p, k]: any) => {
      const w: any = window;
      document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());
      if (typeof w.forgeCrafted !== 'function') return { missing: true } as any;
      w.forgeCrafted(p.ck, p.slot);
      const epic: any = document.querySelector('.chron-epic');
      const toast: any = document.querySelector('.chron-toast');
      const txt: any = epic && epic.querySelector('.fe-txt');
      const b: any = toast && toast.querySelector('b');
      return {
        missing: false,
        n: (w._craftChronCount && w._craftChronCount().n),
        tot: (w._craftChronCount && w._craftChronCount().tot),
        epic: !!epic, epicCls: epic ? epic.className : null,
        toast: !!toast, toastCls: toast ? toast.className : null,
        txtColor: txt ? getComputedStyle(txt).color : null,
        bColor: b ? getComputedStyle(b).color : null,
        headline: txt ? txt.textContent || '' : '',
      };
    }, [pick, CHRON_KEY]);

    expect(first.missing, 'window.forgeCrafted must exist — it is the "I made this" action the celebration hangs off').toBe(false);

    const after = await page.evaluate(READ_IDS, CHRON_KEY);
    expect(after.length, 'logging a craft must add exactly one recipe to the chronicle').toBe(before.length + 1);
    const added = after.filter(id => before.indexOf(id) < 0);
    expect(added.length, 'exactly one new recipe id, not a blanket rewrite of the store').toBe(1);

    /* The count the ladder is driven by must agree with the store it is derived from — two numbers
     * that disagree is the failure nothing catches. */
    expect(first.n, '_craftChronCount().n must agree with the chronicle store').toBe(after.length);

    expect(first.toast, 'every craft must show a toast — the "in between" celebration').toBe(true);
    expect(first.epic, 'the FIRST craft must throw the full overlay, not a plain tick').toBe(true);
    expect(first.epicCls, 'the craft celebration must wear the CRAFT colour class').toContain('ce-craft');
    expect(first.epicCls, 'the first craft must be the "first" tier').toContain('ce-first');
    expect(first.toastCls, 'the toast must wear the craft colour class too').toContain('ce-craft');
    expect(first.headline, 'the first craft must say so').toContain('CRAFT');

    /* COLOUR: read the token from the document, never write a quality hex in an expectation. */
    const tok = await boardTokens(page);
    assertTokens(tok, 'orange', 'unique', 'set');
    expect(first.txtColor, 'the craft celebration must paint the crafted-orange token').toBe(tok.orange);
    expect(first.bColor, 'the craft toast count must paint the crafted-orange token').toBe(tok.orange);
    /* …and must not be either of the chronicles it is NOT. Without this, an accidental fallback to
     * the default unique-gold would still satisfy an equality against a mis-set token. */
    expect(tok.orange, 'crafted-orange must be a colour of its own, distinct from unique').not.toBe(tok.unique);
    expect(first.txtColor, 'the craft celebration must not be painted set-green').not.toBe(tok.set);

    /* ── 5. RISE-ONLY: the same recipe again is not a new craft ────────────────────────────── */
    const repeat = await page.evaluate(([p, k]: any) => {
      const w: any = window;
      document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());
      w.forgeCrafted(p.ck, p.slot);
      return {
        n: w._craftChronCount().n,
        toasts: document.querySelectorAll('.chron-toast').length,
        epics: document.querySelectorAll('.chron-epic').length,
      };
    }, [pick, CHRON_KEY]);

    const afterRepeat = await page.evaluate(READ_IDS, CHRON_KEY);
    expect(afterRepeat.length, 're-logging the SAME recipe must not grow the chronicle').toBe(after.length);
    expect(repeat.n, 'the count must not move for a recipe already chronicled').toBe(first.n);
    expect(repeat.toasts, 'a repeat must not re-celebrate — the hook fires on a RISE, not on a write').toBe(0);
    expect(repeat.epics, 'a repeat must not throw an overlay').toBe(0);

    /* ── 6. UNDO NEVER CELEBRATES (v559.1) ────────────────────────────────────────────────── */
    /* Prove the celebration is still ARMED right now, so a silent "no toast" below cannot be the
     * feature being dead rather than the undo being quiet. */
    const armed = await page.evaluate(() => {
      const w: any = window;
      document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());
      const tier = w._chronCelebrate({ chron: 'craft', icon: '⚗', noun: 'crafts', n: 2, tot: 36 });
      const painted = document.querySelectorAll('.chron-toast').length;
      document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());
      return { tier, painted };
    });
    expect(armed.tier, 'the engine must be live in this page — otherwise the undo assertion is vacuous').toBeTruthy();
    expect(armed.painted, 'the engine must actually paint in this page').toBe(1);

    /* Drive the app's REAL undo control: the ✕ chip v1634 renders on a chronicled recipe row. It is
     * an arm-then-confirm two-tap (a dense recipe row is easy to mis-tap), so this CLICKS UNTIL the
     * recipe actually leaves the book rather than assuming one tap does it — the arming tap is a
     * no-op on the store by design and must not be mistaken for a broken undo.
     * Deliberately NOT discovered by scanning window for /craft.*clear/: clearCraftStash awaits a
     * uiConfirm modal and would hang the run — a "find any undo-ish function" loop is how this spec
     * timed out at 180s before. The control under test is the one Konyo presses. */
    const undo = await page.evaluate(([p, k]: any) => {
      const w: any = window;
      const has = () => !!w._craftMadeHas(p.ck, p.slot);
      const btnFor = () => Array.from(document.querySelectorAll('.f-craft-unchron')).find((b: any) => {
        const oc = b.getAttribute('onclick') || '';
        return oc.indexOf("'" + p.ck + "'") >= 0 && oc.indexOf("'" + p.slot + "'") >= 0;
      }) as any;

      const seen = { armTapWasNoop: false, taps: 0, via: '' as string };
      document.querySelectorAll('.chron-toast,.chron-epic').forEach(e => e.remove());

      let b = btnFor();
      if (b) {
        seen.via = 'the ✕ un-chronicle control';
        for (let i = 0; i < 4 && has(); i++) {
          b = btnFor() || b;
          b.click(); seen.taps++;
          if (i === 0) seen.armTapWasNoop = has();   // the arming tap must not have removed anything
        }
      } else {
        /* The row is only in the DOM when the craft card is open; falling back to the same function
         * the control calls keeps the assertion about the app's undo, not about accordion state. */
        seen.via = 'window.forgeUncraft (row not rendered)';
        w.forgeUncraft(null, p.ck, p.slot); seen.taps++;
      }
      return { via: seen.via, taps: seen.taps, armTapWasNoop: seen.armTapWasNoop, ok: !has(),
               n: w._craftChronCount().n,
               toasts: document.querySelectorAll('.chron-toast').length,
               epics: document.querySelectorAll('.chron-epic').length };
    }, [pick, CHRON_KEY]);

    expect(undo.ok,
      `v1634 must ship an UNDO for a logged craft — a chronicle you cannot correct is a trap ` +
      `(drove ${undo.via}, ${undo.taps} tap(s))`).toBe(true);

    const afterUndo = await page.evaluate(READ_IDS, CHRON_KEY);
    expect(afterUndo.length, `undo (via ${undo.via}) must remove the recipe from the chronicle`).toBe(after.length - 1);
    expect(undo.n, 'the count must go DOWN on undo').toBeLessThan(first.n as number);
    /* v559.1 — un-marking is a correction, never an achievement. */
    expect(undo.toasts, 'undo must NOT show a toast').toBe(0);
    expect(undo.epics, 'undo must NOT throw an overlay').toBe(0);

    expect(errs, 'no page errors along the whole record → repeat → undo path').toEqual([]);
  });
});
