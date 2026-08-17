import { test, expect } from './_net_stub';
import * as path from 'path';
import { boardTokens, assertTokens } from './_palette';
import { ensureCardExpanded } from './_cards';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v157 — the Item-Set tracker cards (#set-tracker .set-card) adopt the rich gradient-header
// first-glance of the TZ/Runes cards (Konyo: "i want the bottom of the page also like this"):
// a compact emblem + in-game-green set name + N/M progress line across the card top, while the
// per-piece collect checklist body is unchanged. The header text node (.set-card-name) stays a
// PURE set name (no emblem text leaks in) so v145's titleName gateway resolver still works, and
// the per-piece data-arttip hover (v134) is untouched. ZERO fabrication — ITEM_SETS unchanged.
test.describe('v157 set-tracker cards mirror the rich gradient-header first-glance', () => {
  /* v1751 — ENSURE EXPANDED, NEVER TOGGLE BLIND.
     This used to `goto` -> wait 1000ms -> switchTab -> toggleCardCollapse -> wait 400ms, and it
     went flaky on CI with `headerH: 0` while the gradient assertion one line above it PASSED.
     That pairing is the whole tell: a COLLAPSED card still resolves getComputedStyle, so
     `linear-gradient` reads back fine, and only getBoundingClientRect() reports the truth.

     The mechanism is in the app, and it is not a bug there: toggleCardCollapse opens with
     `if (!card) return;` — a SILENT no-op. Fired at a fixed 1000ms on a loaded shard, before the
     board had rendered the Tools tab, the toggle did nothing, the card stayed collapsed, and the
     suite measured a card that was never opened. A blind toggle is a coin flip against boot time;
     it also means that if the card ever DEFAULTS to open, this same line closes it.

     bible.html already uses the correct idiom twice of its own accord (`if (card &&
     card.classList.contains('collapsed')) toggleCardCollapse(...)`, at :5868 and :21601). This
     borrows it, and waits for the STATE it needs — card present, not collapsed, cards rendered —
     instead of for a number of milliseconds. The height assertion stays a real assertion: we wait
     for the card to be OPEN, never for it to be tall, so a card that opens flat still goes red.
     [[feedback_suspect_the_instrument]] */
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await ensureCardExpanded(page, 'set-tracker-card', '#set-tracker .set-card .set-card-header');
  });

  test('every set-card has the rich header (emblem + name block + progress)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#set-tracker .set-card')] as HTMLElement[];
      return {
        count: cards.length,
        withHeader: cards.filter((c) => !!c.querySelector('.set-card-header')).length,
        withEmblem: cards.filter((c) => !!c.querySelector('.set-card-header .sec-h-art.set-card-emblem')).length,
        withBlock: cards.filter((c) => !!c.querySelector('.set-card-header .set-card-title-block')).length,
        nameInBlock: cards.filter((c) => !!c.querySelector('.set-card-title-block > .set-card-name')).length,
        progressInBlock: cards.filter((c) => /\d+ \/ \d+ pieces/.test(c.querySelector('.set-card-title-block > .set-card-progress')?.textContent || '')).length,
        piecesStillThere: cards.filter((c) => !!c.querySelector('.set-pieces .set-piece')).length,
      };
    });
    expect(r.count).toBeGreaterThanOrEqual(8);
    expect(r.withHeader).toBe(r.count);
    expect(r.withEmblem).toBe(r.count);
    expect(r.withBlock).toBe(r.count);
    expect(r.nameInBlock).toBe(r.count);
    expect(r.progressInBlock).toBe(r.count);
    expect(r.piecesStillThere).toBe(r.count);  // checklist body intact under the bar
  });

  // AUDIT v1632 — this spec used to pin `toBe('rgb(0, 255, 0)')`, a hardcoded duplicate of an app
  // constant (shape 1). When --q-set was corrected to D2's real FontColorGreen #00fc00 the test went
  // RED ON THE FIX: it was defending a VALUE, never the RULE. It now reads the token live out of the
  // document and asserts the RELATIONSHIP — the set name equals --q-set and is DISTINCT from
  // --q-unique (the v1622 chrome-gold defect) and from --q-normal (silently falling back to body text).
  test('the name resolves to the live --q-set token (not unique, not default) + gradient bar; emblem text does not leak into the name', async ({ page }) => {
    // The palette spine resolves each :root token through the SAME engine that paints the card, so
    // no hex is ever restated here. assertTokens() is the null-guard: a renamed/deleted token would
    // otherwise resolve to null on BOTH sides and compare green, proving nothing.
    const t = await boardTokens(page);
    assertTokens(t, 'set', 'unique', 'normal');

    const r = await page.evaluate(() => {
      const card = document.querySelector('#set-tracker .set-card') as HTMLElement;
      const header = card.querySelector('.set-card-header') as HTMLElement;
      const name = card.querySelector('.set-card-name') as HTMLElement;
      const emblem = card.querySelector('.set-card-emblem') as HTMLElement;
      // v145 titleName: strip ↗ ✓ and trim — must equal a real set name (no emblem glyph)
      const titleName = (name.textContent || '').replace(/[↗✓]/g, '').trim();
      const isAgg = (window as any).isSetAggregate;
      return {
        nameColor: getComputedStyle(name).color,
        headerBg: getComputedStyle(header).backgroundImage,
        headerH: header.getBoundingClientRect().height,
        /* v1754 — WHEN THIS GOES 0 ON CI, SAY WHY. It has now flaked through two fixes of mine
           (the blind toggle, then the hidden tab) and neither closed it, and I cannot reproduce it
           locally: CPU throttled to 20x, four viewports including the configured 1280x720, and
           offline all measure 78px. So the next failure has to carry its own diagnosis instead of
           the bare "Received: 0" that sent me guessing twice. Cheap to collect, and only ever read
           when the assertion below fails. */
        _why: (() => {
          const tab = document.getElementById('tab-tools');
          const cardEl = document.getElementById('set-tracker-card');
          const r = (e: Element | null) => {
            if (!e) return null;
            const b = e.getBoundingClientRect();
            return [Math.round(b.width), Math.round(b.height)];
          };
          return {
            tabDisplay: tab ? getComputedStyle(tab).display : 'NO #tab-tools',
            cardCollapsed: cardEl ? cardEl.classList.contains('collapsed') : 'NO card',
            cardRect: r(cardEl),
            setCards: document.querySelectorAll('#set-tracker .set-card').length,
            firstCardRect: r(card),
            headerDisplay: getComputedStyle(header).display,
            headerText: (header.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40),
            headerChildren: header.children.length,
            docReady: document.readyState,
          };
        })(),
        titleName,
        // NO SILENT-TRUE FALLBACK: a missing resolver reports its own absence ('undefined'), it does
        // not answer `true` on the app's behalf. The two questions are asserted separately below.
        isAggType: typeof isAgg,
        nameResolves: typeof isAgg === 'function' ? isAgg(titleName) : null,
        emblemIsSibling: emblem.parentElement === header && !name.contains(emblem),
      };
    });
    // WHICH colour — equal to the token the stylesheet names, never a pinned literal
    expect(r.nameColor, `set-card-name must paint --q-set (${t.set})`).toBe(t.set);
    expect(r.nameColor, 'set names must NOT render in unique gold (the v1622 defect class)').not.toBe(t.unique);
    expect(r.nameColor, 'set names must NOT fall back to default body text').not.toBe(t.normal);
    // the header is a real, painted gradient bar — not a flat fill and not a 0px-tall nothing
    expect(r.headerBg, 'set-card-header must be a gradient bar').toContain('linear-gradient');
    expect(r.headerH, 'the gradient bar must actually occupy space — state at failure: '
      + JSON.stringify((r as any)._why)).toBeGreaterThan(0);
    // the v145 gateway resolver must EXIST — asserted on its own so its absence can never be
    // mistaken for a passing answer …
    expect(r.isAggType, 'window.isSetAggregate (v145 titleName gateway) must exist').toBe('function');
    // … and must actually resolve THIS card's title (first card is a codex-backed set → clean name)
    expect(r.nameResolves, `isSetAggregate(${JSON.stringify(r.titleName)}) must resolve the rendered set-card title`).toBe(true);
    expect(r.emblemIsSibling).toBe(true);            // emblem outside .set-card-name (no titleName pollution)
  });

  test('toggling a piece still re-renders + the rich header survives', async ({ page }) => {
    const r = await page.evaluate(() => {
      const checked = () => document.querySelectorAll('#set-tracker .set-piece.checked').length;
      const before = checked();
      const piece = document.querySelector('#set-tracker .set-piece') as HTMLElement;
      piece.click();
      const afterFirst = checked();
      // header still present post re-render
      const headers = document.querySelectorAll('#set-tracker .set-card .set-card-header').length;
      const cards = document.querySelectorAll('#set-tracker .set-card').length;
      // toggle back to leave state clean
      (document.querySelector('#set-tracker .set-piece') as HTMLElement).click();
      return { before, afterFirst, headers, cards };
    });
    expect(r.afterFirst).toBe(r.before + 1);
    expect(r.headers).toBe(r.cards);     // every card kept its rich header after the re-render
  });

  test('no console errors rendering the restyled set-tracker', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await ensureCardExpanded(page, 'set-tracker-card', '#set-tracker .set-card .set-card-header');
    expect(errors).toEqual([]);
  });
});
