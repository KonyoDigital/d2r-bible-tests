/* v1635 — THE CRAFT BOOK, PROVED IN THE PAINTED BOARD.
 *
 * v1634 shipped d2r_craftMade, window.forgeCrafted and window.forgeUncraft, and
 * tests/v1634_craft_chronicle.spec.ts proved the JS SEAM: the ladder, the fork doctrine, the derived
 * total, the crafted-orange. Every one of those tests calls the functions directly. Not one of them
 * ever touched the control Konyo touches.
 *
 * That gap is not theoretical. A ✓ button can be present in the DOM, wear the right class, call the
 * right handler when invoked from evaluate() — and still be clipped to zero height, buried under the
 * position:fixed Forge legend (~:34230), or painted in a colour nobody can read. Every one of those
 * is invisible to `expect(locator).toBeVisible()`, because "visible" in Playwright means
 * non-zero-box-and-not-display-none, not "a finger lands on it".
 *
 * SO THIS SPEC MEASURES, AND REFUSES THE FOLLOWING AS EVIDENCE:
 *
 *   - PRESENCE. `toBeVisible()` on the ✓ is not the claim. The claim is that
 *     document.elementFromPoint at the button's own centre returns the button (or a descendant),
 *     which is the only statement that survives an overlay. A real box is measured too, in px.
 *
 *   - A DECLARED colour. The label's legibility is a CONTRAST RATIO computed from the button's own
 *     resolved `color` against its own COMPOSITED background — walked up the ancestor chain to the
 *     first non-transparent paint, because a button with `background:transparent` inherits whatever
 *     is behind it and reading its own backgroundColor would score a phantom. No quality hex
 *     literal appears in this file (P6 guard); tests/_palette.ts is the only way a token is read.
 *
 *   - A SYNTHETIC click. `el.click()` inside evaluate() bypasses hit-testing entirely — it is the
 *     same seam v1634 already covers. Every state change below is driven by a real Playwright
 *     `.click()`, which routes through the browser's own hit test and would fail on exactly the
 *     obstruction the elementFromPoint assertion describes.
 *
 *   - SILENCE READ AS SUCCESS. motionOK() is false whenever navigator.webdriver is true, so under
 *     plain automation _chronCelebrate returns null and paints NOTHING. "No toast after undo" would
 *     then be green on a completely dead feature. Every test here presents itself as a real browser
 *     first (the v1633 technique), and the celebration is proved to PAINT on the way in before its
 *     ABSENCE is ever used as evidence on the way out.
 *
 *   - AN ALREADY-EMPTY QUANTITY. The no-double-count test does not assert "the store has one id"
 *     against a store that never grew; it asserts a TRANSITION — 0 → 1 on the first click, and
 *     1 → 1 on the second, with both numbers reported.
 *
 * NAVIGATION — solved once, four probes were burned rediscovering it, written down here:
 *   The webdriver override flips _D2R_OWNER to FALSE on a file:// board, so the board resolves as a
 *   GUEST world and every chronicle key gains an `I·<id8>·` prefix. The store is therefore ALWAYS
 *   read through window.LSR.key('d2r_craftMade') — never by the bare name.
 *   renderForge falls to the 'completed' filter on a virgin board and the crafts section is gated on
 *   show('crafts')||show('all') (~:34196), so forgeSetFilter('crafts') is mandatory or the section
 *   does not exist at all.
 *
 * Recipe ids are discovered from window.CRAFTS in the running page — this is the Reign of the
 * Warlock mod and a hardcoded vanilla name is silently dropped.
 *
 * MUTATION LOG — pasted in the run report. See the report for the RED/GREEN transcripts.
 */
// v1754 — through the shared net stub, so this spec's measurements do not depend on the
// runner reaching fonts.googleapis.com. bible.html makes exactly FIVE external requests and
// all five are fonts; stubbing them removes the whole external surface.
//
// ⚠ NOT because a failed font collapses this layout — I checked, and it does not. Measured
// three ways, .set-card-header is 78px ONLINE, 78px OFFLINE and 78px STUBBED. The v1749
// note on _net_stub says a font failure makes that bar 0px; offline does not reproduce it,
// and the flake it was written about turned out to be a blind toggleCardCollapse leaving
// the card COLLAPSED (fixed in v1751, proven by forcing .collapsed). The honest reason to
// stub here is determinism, not a defect anyone has shown. [[inherited_claim_is_not_evidence]]
import { test, expect } from './_net_stub';
import * as path from 'path';

const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* The chronicle store. Named once; always resolved through LSR.key() at read time. */
const CHRON_KEY = 'd2r_craftMade';

/* WCAG AA for normal-size text. The ✓ label renders at 11px (:7441), which is small text by any
 * reading, so the small-text floor is the honest one. This is a FLOOR, not a copied value: it is not
 * derived from what the board happens to paint today, and if the palette moves under it the number
 * here does not move to follow. */
const CONTRAST_FLOOR = 4.5;

/* Celebrations are gated on motionOK() — false under automation. Lift the gate the way v1633 does;
 * nothing else is stubbed, the real engine builds the real DOM. Also wipes every routing of the
 * craft chronicle BEFORE boot so "the first craft" is really the first: a left-over row would make
 * the 'first' tier unreachable and quietly downgrade the celebration assertions to a tick. */
async function asRealBrowser(page: any) {
  await page.addInitScript((k: string) => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false, configurable: true });
    /* v1518/REG-084 — spoofing navigator.webdriver unmasks this page as a GUEST (v1499),
       so every bare key seeded below would land in an `I·<id>·` world the app never reads
       and this spec would assert against a world that does not exist. Claim the owner
       world in the SAME init script that does the spoof, so the pairing cannot drift. */
    localStorage.setItem('d2r_ownerClaim', '*');
    try {
      const doomed: string[] = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key === k || key.endsWith('·' + k))) doomed.push(key);
      }
      doomed.forEach(key => localStorage.removeItem(key));
    } catch (e) { /* a storage failure must never stop the board booting */ }
  }, CHRON_KEY);
}

/* Board → Forge tab → crafts filter. The two waits are the board's own async render settling; the
 * spec asserts a real row count afterwards so a short wait shows up as a failure, never as a skip. */
async function openCraftBench(page: any) {
  await page.goto(BOARD);
  await page.waitForTimeout(2500);
  await page.evaluate(() => {
    (window as any).switchTab('forge');
    (window as any).forgeSetFilter('crafts');
  });
  await page.waitForTimeout(1200);
}

/* Read the chronicle out of the store the app actually routed it to — the truth the counts are
 * derived FROM, not the number a surface happens to be showing. */
const READ_IDS = (k: string) => {
  const w: any = window;
  let raw: any = null;
  try { raw = localStorage.getItem(w.LSR.key(k)); } catch (e) { return []; }
  let v: any = null;
  try { v = JSON.parse(raw || 'null'); } catch (e) { return []; }
  return Array.isArray(v) ? v.map(String) : [];
};

/* Contrast ratio from two resolved `rgb(...)` strings, WCAG relative-luminance. Lives in the spec
 * rather than in the page so the page cannot flatter itself. */
function ratio(fg: string, bg: string): number {
  const chan = (s: string) => {
    const m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x.trim()));
    return [p[0], p[1], p[2]];
  };
  const lum = (c: number[]) => {
    const f = c.map(v => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4); });
    return 0.2126 * f[0] + 0.7152 * f[1] + 0.0722 * f[2];
  };
  const a = chan(fg), b = chan(bg);
  if (!a || !b) return 0;
  const la = lum(a), lb = lum(b);
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

test.describe('v1635 — the craft ✓ works for a human, not just for evaluate()', () => {

  test('★★★ the ✓ crafted control is REACHABLE — a real box, and a finger lands on IT', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(String(e)));
    await asRealBrowser(page);
    await openCraftBench(page);
    expect(errs, 'the craft bench must render clean').toEqual([]);

    const rows = page.locator('.f-craftrow');
    const btns = page.locator('.f-craft-made');
    /* Non-vacuity: hit-testing zero buttons is green and proves nothing. */
    expect(await rows.count(), 'the crafts section must actually render recipe rows').toBeGreaterThan(0);
    expect(await btns.count(), 'every recipe row must carry a ✓ crafted control').toBeGreaterThan(0);

    const btn = btns.first();
    await btn.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);

    /* A REAL BOX, in px. A control collapsed by a flex/overflow rule reads 0 here and Playwright's
     * own toBeVisible() would still be green on a 0x0 element in some layouts. */
    const box = await btn.boundingBox();
    expect(box, 'the ✓ control must have a laid-out box').not.toBeNull();
    expect(box!.width, 'the ✓ control must have real width').toBeGreaterThan(0);
    expect(box!.height, 'the ✓ control must have real height').toBeGreaterThan(0);
    /* Big enough to aim at: below this it is present but not usable. */
    expect(box!.width, 'the ✓ control must be wide enough to tap').toBeGreaterThan(24);
    expect(box!.height, 'the ✓ control must be tall enough to tap').toBeGreaterThan(12);

    /* THE HIT TEST — the assertion presence cannot substitute for. If the position:fixed Forge
     * legend, a toast, or any z-index accident covers the control, this is what says so. */
    const hit = await page.evaluate(() => {
      const b: any = document.querySelector('.f-craft-made');
      if (!b) return { ok: false, why: 'no button' };
      const r = b.getBoundingClientRect();
      const el: any = document.elementFromPoint(Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2));
      if (!el) return { ok: false, why: 'elementFromPoint returned nothing — the centre is off-viewport' };
      return {
        ok: el === b || b.contains(el),
        why: 'topmost element at the ✓ centre was <' + el.tagName.toLowerCase() + ' class="' + (el.className || '') + '">',
        text: (b.textContent || '').trim(),
      };
    });
    expect(hit.ok, 'a tap at the ✓ centre must land on the ✓ itself: ' + hit.why).toBe(true);
    expect(hit.text, 'the control must read as an action, not an empty box').toContain('crafted');

    /* Every <img> carries onerror=this.remove(), so a 404 fails SILENTLY and the row still looks
     * fine. Assert the craft art actually decoded — and that there IS art, or the check is vacuous. */
    const art = await page.evaluate(() => {
      const imgs = Array.from(document.querySelectorAll('.f-craftrow img')) as any[];
      return { n: imgs.length, dead: imgs.filter(i => !(i.naturalWidth > 0)).map(i => i.getAttribute('src')) };
    });
    expect(art.n, 'the craft rows must carry slot art — asserting over zero images proves nothing').toBeGreaterThan(0);
    expect(art.dead, 'every craft-row image must have decoded (naturalWidth > 0)').toEqual([]);
  });

  test('★★★ the ✓ label is LEGIBLE against what is actually painted behind it', async ({ page }) => {
    await asRealBrowser(page);
    await openCraftBench(page);

    const m = await page.evaluate(() => {
      const b: any = document.querySelector('.f-craft-made');
      if (!b) return null;
      const parse = (c: string): number[] | null => {
        const mm = String(c).match(/rgba?\(([^)]+)\)/);
        if (!mm) return null;
        const p = mm[1].split(/[,\s/]+/).filter(Boolean).map(x => parseFloat(x));
        return [p[0], p[1], p[2], p.length > 3 && !isNaN(p[3]) ? p[3] : 1];
      };
      /* The COMPOSITED background. A button declaring background:transparent — and every
         semi-transparent panel between it and the page — shows through, so scoring against the
         button's own declaration would invent a contrast nobody ever sees, and stopping at the
         first opaque ancestor would ignore the translucent layers stacked on top of it. Collect the
         whole stack up to the first opaque paint, then composite it back down in paint order. */
      const stack: number[][] = [];
      let node: any = b, from = '';
      while (node) {
        const c = parse(getComputedStyle(node).backgroundColor);
        if (c && c[3] > 0) {
          stack.push(c);
          if (c[3] >= 0.999) { from = node.tagName.toLowerCase() + '.' + String(node.className || '').split(' ')[0]; break; }
        }
        node = node.parentElement;
      }
      if (!from) { stack.push([0, 0, 0, 1]); from = 'page (no opaque ancestor found)'; }
      /* stack[last] is the bottom-most (opaque) layer; composite upward towards the button. */
      let out = stack[stack.length - 1].slice(0, 3);
      for (let i = stack.length - 2; i >= 0; i--) {
        const l = stack[i], a = l[3];
        out = [0, 1, 2].map(j => l[j] * a + out[j] * (1 - a));
      }
      const cs = getComputedStyle(b);
      return {
        fg: cs.color,
        bg: 'rgb(' + out.map(v => Math.round(v)).join(', ') + ')',
        from, layers: stack.length, size: parseFloat(cs.fontSize), weight: cs.fontWeight,
      };
    });

    expect(m, 'the ✓ control must exist to be measured').not.toBeNull();
    const r = ratio(m!.fg, m!.bg);
    /* Non-vacuity: a ratio of 0 means one of the two colours failed to parse, which would sail
       under any floor comparison written the other way round. */
    expect(r, 'both colours must have resolved — a ratio of 0 means the measurement failed, not that it passed')
      .toBeGreaterThan(1);
    expect(r, `the ✓ label (${m!.fg} at ${m!.size}px on ${m!.bg} from ${m!.from}) must clear the small-text contrast floor — measured ${r.toFixed(2)}:1`)
      .toBeGreaterThanOrEqual(CONTRAST_FLOOR);
  });

  test('★★★ a REAL click records the recipe and the celebration actually PAINTS', async ({ page }) => {
    await asRealBrowser(page);
    await openCraftBench(page);

    /* Discover the recipe the first row belongs to FROM THE APP — this is the RotW mod and a
       hardcoded vanilla craft/slot pair would be silently dropped. */
    const pre = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      return { ids: read(k) as string[], count: w._craftChronCount(), recipes: (w.CRAFTS || []).length };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    /* BEFORE, with real numbers: the book is empty and the recipe book is not. */
    expect(pre.recipes, 'CRAFTS must hold recipes or every number below is vacuous').toBeGreaterThan(0);
    expect(pre.ids.length, 'the craft book must start empty — otherwise "the first craft" is not first').toBe(0);
    expect(pre.count.n, 'the derived count must agree the book is empty').toBe(0);
    expect(pre.count.tot, 'the total must be a real derived number, not an empty reduce').toBeGreaterThan(0);

    const btn = page.locator('.f-craft-made').first();
    await btn.scrollIntoViewIfNeeded();
    await btn.click();                                  /* REAL hit-tested click — the whole point */
    await page.waitForTimeout(400);

    const post = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      const sub: any = document.querySelector('.forge-sec-craft .forge-sec-sub');
      const toast: any = document.querySelector('.chron-toast.ce-craft');
      const epic: any = document.querySelector('.chron-epic.ce-craft');
      return {
        ids: read(k) as string[],
        key: w.LSR.key(k),
        count: w._craftChronCount(),
        sub: sub ? (sub.textContent || '') : null,
        toastCls: toast ? toast.className : null,
        epicCls: epic ? epic.className : null,
      };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    /* AFTER: 0 → 1, and the id is a real "Craft|Slot" pair the app minted, not one this spec made up. */
    expect(post.ids.length, `one real click must add exactly one recipe (store ${post.key} went ${pre.ids.length} → ${post.ids.length})`).toBe(1);
    expect(post.ids[0], 'the recorded id must be the distinct-recipe form Craft|Slot').toMatch(/^.+\|.+$/);
    expect(post.count.n, 'the derived count must read the rise').toBe(1);
    expect(post.count.tot, 'the total must not move when a recipe is logged').toBe(pre.count.tot);

    /* The number has a home on the page, and it is the SAME number. */
    expect(post.sub, 'the Forge crafts header must carry a chronicled sub-line').toBeTruthy();
    const hm = String(post.sub).match(/(\d+)\s*\/\s*(\d+)\s+recipes chronicled/);
    expect(hm, 'the Forge sub-line must state n / tot recipes chronicled — got: ' + post.sub).not.toBeNull();
    expect(Number(hm![1]), 'the Forge header n must equal the store').toBe(post.count.n);
    expect(Number(hm![2]), 'the Forge header total must equal the derived total').toBe(post.count.tot);

    /* IT PAINTED. Asserted BEFORE any later test uses absence as evidence — that ordering is what
       makes the v559.1 undo assertion non-vacuous rather than a screenshot of a dead feature. */
    expect(post.toastCls, 'the first craft must paint a toast wearing the craft colour class').toBeTruthy();
    expect(post.toastCls, 'the toast must be the shared chronicle toast, not a bespoke one').toContain('chron-toast');
    expect(post.epicCls, 'the first craft is the "first" tier and must paint the overlay').toBeTruthy();
    expect(post.epicCls, 'the overlay must wear the first-find tier class').toContain('ce-first');
  });

  test('★★★ a second ✓ on the SAME recipe does not double-count and does not celebrate again', async ({ page }) => {
    await asRealBrowser(page);
    await openCraftBench(page);

    const btn = page.locator('.f-craft-made').first();
    await btn.scrollIntoViewIfNeeded();
    await btn.click();
    await page.waitForTimeout(400);

    const first = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      /* Clear the painted celebration and spy the engine, so "no second celebration" is measured on
         a clean surface rather than confused with the first one still on screen. */
      document.querySelectorAll('.chron-toast,.chron-epic,.forge-toast,.forge-epic').forEach(e => e.remove());
      w.__spyN = 0;
      const orig = w._chronCelebrate;
      w.__origCelebrate = orig;
      w._chronCelebrate = function (o: any) { w.__spyN++; return orig.apply(this, arguments as any); };
      return { ids: read(k) as string[], n: w._craftChronCount().n };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    /* The transition being tested is 1 → 1, so the 0 → 1 leg must be real first. */
    expect(first.ids.length, 'the first click must have recorded exactly one recipe').toBe(1);
    expect(first.n, 'the derived count must read 1 before the second click').toBe(1);

    /* Same row, same recipe, real click. renderForge replaced the node, so re-resolve the locator. */
    const again = page.locator('.f-craft-made').first();
    await again.scrollIntoViewIfNeeded();
    await again.click();
    await page.waitForTimeout(400);

    const second = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      return {
        ids: read(k) as string[],
        n: w._craftChronCount().n,
        spy: w.__spyN,
        painted: document.querySelectorAll('.chron-toast,.chron-epic').length,
      };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    expect(second.ids.length, `the book is a SET of distinct recipes: ${first.ids.length} → ${second.ids.length} after logging the same one twice`).toBe(1);
    expect(second.ids, 'the second click must not have minted a second id').toEqual(first.ids);
    expect(second.n, 'the derived count must not climb on a duplicate').toBe(1);
    expect(second.spy, 'a duplicate raises nothing, so it must celebrate nothing').toBe(0);
    expect(second.painted, 'no second celebration may paint for a recipe already in the book').toBe(0);
  });

  test('★★★ the armed two-tap undo is DISCOVERABLE, silent, and leaves a re-log celebratable', async ({ page }) => {
    await asRealBrowser(page);
    await openCraftBench(page);

    await page.locator('.f-craft-made').first().scrollIntoViewIfNeeded();
    await page.locator('.f-craft-made').first().click();
    await page.waitForTimeout(400);

    /* The ✕ only exists on a row already in the book, so its presence is itself evidence the record
       reached the render. */
    const un = page.locator('.f-craft-unchron').first();
    expect(await page.locator('.f-craft-unchron').count(), 'a chronicled row must offer the un-chronicle control').toBeGreaterThan(0);
    await un.scrollIntoViewIfNeeded();

    /* BOTH readings are taken with the control BLURRED and the pointer parked away from it. A real
       .click() leaves focus on the button, so measuring rest-before / armed-after would let a
       :focus or :hover rule masquerade as the armed skin and the assertion would be green on a
       feature that paints nothing. This is the one line that keeps that assertion honest. */
    const settle = async () => {
      await page.mouse.move(0, 0);
      await page.evaluate(() => { const a: any = document.activeElement; if (a && a.blur) a.blur(); });
      await page.waitForTimeout(250);              /* let any colour transition finish resolving */
    };
    await settle();

    const rest = await page.evaluate(() => {
      const b: any = document.querySelector('.f-craft-unchron');
      const cs = getComputedStyle(b);
      return { border: cs.borderColor, color: cs.color, bg: cs.backgroundColor, text: (b.textContent || '').trim() };
    });
    expect(rest.text, 'at rest the control reads as a remove affordance').toBe('✕');

    await un.click();                                   /* first tap = ARM, not remove */
    await settle();                                     /* same blurred, unhovered conditions as rest */

    const armed = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      const b: any = document.querySelector('.f-craft-unchron');
      const cs = getComputedStyle(b);
      return {
        border: cs.borderColor, color: cs.color, bg: cs.backgroundColor,
        text: (b.textContent || '').trim(), cls: b.className,
        ids: read(k) as string[],
      };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    /* ARMING IS NOT REMOVING — the first tap must be reversible. */
    expect(armed.ids.length, 'the first tap arms only; the book must be untouched').toBe(1);
    expect(armed.text, 'the armed state must say what the next tap does').toBe('remove?');

    /* DISCOVERABLE BY A COMPUTED PROPERTY, not by a class name. At v1634 .gp-rm-armed was declared
       only under `.gf-piece .gp-rm` (:3836), so the class landed on this button and painted
       NOTHING — border, colour and background were byte-identical armed and at rest. A class-name
       assertion is green on that; this one is not. The label change alone is not accepted: a
       destructive armed state must read as destructive at a glance. */
    const moved = (armed.border !== rest.border) || (armed.color !== rest.color) || (armed.bg !== rest.bg);
    expect(moved,
      `the armed state must be VISUALLY distinct from rest, not only relabelled — ` +
      `border ${rest.border} → ${armed.border}, color ${rest.color} → ${armed.color}, bg ${rest.bg} → ${armed.bg}`)
      .toBe(true);

    /* THE v559.1 RULE: un-marking NEVER celebrates. Spy the real engine, on a cleared surface, with
       the motion gate already lifted — so silence here is a decision, not the gate. */
    await page.evaluate(() => {
      const w: any = window;
      document.querySelectorAll('.chron-toast,.chron-epic,.forge-toast,.forge-epic').forEach(e => e.remove());
      w.__spyN = 0;
      const orig = w._chronCelebrate;
      w.__origCelebrate = orig;
      w._chronCelebrate = function () { w.__spyN++; return orig.apply(this, arguments as any); };
    });

    await page.locator('.f-craft-unchron').first().click();   /* second tap = CONFIRM */
    await page.waitForTimeout(400);

    const removed = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      return {
        ids: read(k) as string[],
        n: w._craftChronCount().n,
        spy: w.__spyN,
        painted: document.querySelectorAll('.chron-toast,.chron-epic').length,
        prev: w.__chronPrevN ? w.__chronPrevN[w.LSR.key(k)] : undefined,
      };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    expect(removed.ids.length, 'the confirmed tap must empty the book (1 → 0)').toBe(0);
    expect(removed.n, 'the derived count must follow the store down').toBe(0);
    expect(removed.spy, 'v559.1: un-marking must never celebrate').toBe(0);
    expect(removed.painted, 'no celebration may paint on an un-mark').toBe(0);
    /* The lowered baseline must be a real, non-negative memory of where the count now stands — a
       stale or negative one would suppress (or fake) the next legitimate rise. */
    expect(removed.prev, 'the chronicle baseline must have been lowered to the new size').toBe(0);

    /* …and the recipe is celebratable AGAIN, as a rise of one. This is the half that proves the
       baseline was lowered correctly rather than merely written to something. */
    await page.evaluate(() => { (window as any).__spyN = 0; });
    const relog = page.locator('.f-craft-made').first();
    await relog.scrollIntoViewIfNeeded();
    await relog.click();
    await page.waitForTimeout(400);

    const back = await page.evaluate(({ k, src }) => {
      const w: any = window;
      // eslint-disable-next-line no-new-func
      const read = new Function('k', 'return (' + src + ')(k)');
      return {
        ids: read(k) as string[], n: w._craftChronCount().n, spy: w.__spyN,
        epic: document.querySelectorAll('.chron-epic.ce-craft').length,
      };
    }, { k: CHRON_KEY, src: READ_IDS.toString() });

    expect(back.ids.length, 're-logging the same recipe must record it again').toBe(1);
    expect(back.n, 'the count must climb back to one').toBe(1);
    expect(back.spy, 'a re-log after an undo is a genuine rise and MUST celebrate').toBe(1);
    expect(back.epic, 'the rise of one after an undo is the first tier again, and paints').toBeGreaterThan(0);
  });

  test('★★★ the Forge header and the Craft Workshop footer agree with the store and each other', async ({ page }) => {
    await asRealBrowser(page);
    await openCraftBench(page);

    await page.locator('.f-craft-made').first().scrollIntoViewIfNeeded();
    await page.locator('.f-craft-made').first().click();
    await page.waitForTimeout(400);

    const forge = await page.evaluate(() => {
      const w: any = window;
      const sub: any = document.querySelector('.forge-sec-craft .forge-sec-sub');
      return { sub: sub ? (sub.textContent || '') : null, count: w._craftChronCount() };
    });
    const hm = String(forge.sub).match(/(\d+)\s*\/\s*(\d+)\s+recipes chronicled/);
    expect(hm, 'the Forge sub-line must state n / tot — got: ' + forge.sub).not.toBeNull();
    const headerN = Number(hm![1]), headerTot = Number(hm![2]);

    /* Now the OTHER surface. Same fact, different screen — the shape this project has shipped wrong
       before is two screens quoting different numbers with nothing comparing them. */
    await page.evaluate(() => {
      (window as any).switchTab('tools');
      try { if (typeof (window as any).renderCraftWorkshop === 'function') (window as any).renderCraftWorkshop(); } catch (e) {}
    });
    await page.waitForTimeout(900);

    const foot = await page.evaluate(() => {
      const el: any = document.querySelector('.cw-foot .cw-summary');
      return el ? (el.textContent || '') : null;
    });
    expect(foot, 'the Craft Workshop must render its footer summary').toBeTruthy();

    const fm = String(foot).match(/of\s+(\d+)\s+recipes cubeable now/);
    expect(fm, 'the workshop footer must state the recipe TOTAL — got: ' + foot).not.toBeNull();
    const footTot = Number(fm![1]);

    /* THE TOTALS AGREE — three sources, one number. v1634 derived this footer from CRAFTS precisely
       so it can never drift from the Forge chronicle line. */
    expect(footTot, 'the workshop footer total must equal the Forge header total').toBe(headerTot);
    expect(footTot, 'and both must equal the store-derived total').toBe(forge.count.tot);
    expect(headerN, 'the Forge header n must equal the store').toBe(forge.count.n);
    expect(forge.count.tot, 'non-vacuity: the total must be a real number, not zero on both sides').toBeGreaterThan(0);

    /* DELIBERATELY NOT ASSERTED: that the footer's "N crafted items logged" equals the book count.
       Those are different quantities on purpose — the footer number is d2r_craftStash (how many
       COPIES you own, per profile), the book is d2r_craftMade (how many DISTINCT recipes you have
       ever made, machine-shared). Asserting them equal would encode a falsehood and would go red the
       first time Konyo cubes a second Caster Amulet. */
  });
});
