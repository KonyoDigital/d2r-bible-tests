import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1596 — THE NEXT WINDOW HAS TO BE AS READABLE AS THE LIVE ONE.
//
// Konyo, looking at a rotation whose UP NEXT was Cathedral + Catacombs: "the NEXT is catacombs.
// this is a BOSS level act for farming. how is this emphasized so i know the next terror zone is
// EMPHASIZED enough so i know not only this specific LIVE is a good farm terror zone but also the
// next."
//
// Three separate defects were behind that, and each has its own test here:
//
//   1. CATACOMBS WAS NOT IN THE TABLE. Andariel is there, and TZ_NOTABLE did not know it — so the
//      zone was ranked on density alone (680), landed mid-tier, and rendered as unremarkable. The
//      entry is cross-referenced against the board's own verified BOSSES[] array, not recalled.
//
//   2. THE MIDDLE TIER HAD NO BADGE. A decent zone and a zone the ranker had nothing to say about
//      rendered identically, so the ABSENCE of a badge was doing double duty as "fine" and as
//      "unremarkable". Those are different answers and the reader could not tell them apart.
//
//   3. ADJACENCY WAS BEING SOLD AS A BOSS. My own first fix put Cathedral in TZ_NOTABLE with the
//      note "the way into the Andariel run" — which promoted a 680-density corridor to PRIME and,
//      because it sorts first, let it take the UP NEXT header chip away from Catacombs. The panel
//      advertised the hallway instead of Andariel. Adjacency now lives in TZ_HINT, which attaches a
//      reason WITHOUT touching the verdict.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

// his actual rotation on the night he reported this
const ROTATION = {
  ok: true, current: 'Moo Moo Farm', next: 'Cathedral, Catacombs', ts: Date.now(),
};

async function open(page: any, tz: any = ROTATION) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname === '/api/tz', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(tz) }));
  await page.route((u: URL) => u.pathname.startsWith('/api/') && u.pathname !== '/api/tz',
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1200);
}

const cardFor = (page: any, name: string) => page.evaluate((n: string) => {
  const el = Array.from(document.querySelectorAll('#hd-tz .tzz'))
    .find((c) => (c.querySelector('b')?.textContent || '').trim() === n);
  if (!el) return null;
  return {
    text: (el.textContent || '').replace(/\s+/g, ' ').trim(),
    tag: (el.querySelector('.tzz-tag')?.textContent || '').trim(),
    tier: Array.from(el.classList).find((c) => /^tzz-(prime|good|thin|unknown)$/.test(c)) || '',
    clickable: !!el.getAttribute('onclick') || el.getAttribute('role') === 'button',
  };
}, name);

test.describe('v1596 — the NEXT terror zone states its own worth', () => {
  test('★ CATACOMBS is PRIME and says why: Andariel', async ({ page }) => {
    await open(page);
    const c = await cardFor(page, 'Catacombs');
    expect(c, 'the Catacombs card must render').toBeTruthy();
    expect(c!.tag, 'a boss zone is PRIME, not middle-tier').toBe('PRIME');
    expect(c!.tier).toBe('tzz-prime');
    expect(c!.text, 'and it must name the boss — the reason he would go').toContain('Andariel');
  });

  test('★ CATHEDRAL is ranked on its own density — adjacency is not a boss', async ({ page }) => {
    /* v1805 — THE EXPECTED VALUE MOVED, THE POINT DID NOT.
       This test was written to stop Cathedral being promoted to PRIME on its neighbour's boss —
       it has density 680 and Andariel is next door in the Catacombs, not here. It pinned that as
       "GOOD" because 680 scored 0.304 under the old formula, which added 0.15 weighted on base
       level. v1801 removed that term from both surfaces (a terror zone lifts any TZ area to mlvl
       96, so base level is precisely what the boost overrides — v1585 had said so and fixed only
       the floor), and on density alone 680 scores 0.263 against the 0.28 GOOD threshold. THIN.

       Konyo asked for exactly this, looking at two 600-700 density zones badged GOOD: "density is
       low and its not a terror zone worth farming". So the number this test was guarding did what
       he asked it to do, and the assertion has to follow the ranking rather than pin the ranking
       to whatever it was the day the test was written.

       What is asserted now is the INTENT plus the current verdict: never PRIME (the original
       point, and the part that must never regress), and THIN because that is what its density
       says today. Both, so that a future change that quietly re-promotes it still fails here. */
    await open(page);
    const c = await cardFor(page, 'Cathedral');
    expect(c).toBeTruthy();
    expect(c!.tag,
      'promoting a 680-density corridor to PRIME on its neighbour\'s boss is advice, not data — ' +
      'and it would steal the header chip from the zone that actually has Andariel').not.toBe('PRIME');
    expect(c!.tag,
      'Cathedral is density 680, which is below the GOOD threshold once the level term is gone')
      .toBe('THIN');
    expect(c!.text, 'it still explains where it sits').toContain('the way into the Andariel run');
    expect(c!.text, 'and still shows the numbers the verdict rests on').toContain('680 density');
  });

  test('★ the UP NEXT header names the best zone of the window, with its reason', async ({ page }) => {
    await open(page);
    const chip = await page.evaluate(() => {
      const slot = document.querySelector('#hd-tz .tz-slot.next');
      return (slot?.querySelector('.tz-verdict')?.textContent || '').trim();
    });
    expect(chip, 'he should not have to read two cards to learn the next window is worth staying for')
      .toContain('PRIME');
    expect(chip, 'and best-of must pick the BOSS zone, not whichever sorted first').toContain('Andariel');
  });

  test('the LIVE slot carries the same header verdict — one grammar for both rows', async ({ page }) => {
    await open(page);
    const chip = await page.evaluate(() => {
      const slot = document.querySelector('#hd-tz .tz-slot.now');
      return (slot?.querySelector('.tz-verdict')?.textContent || '').trim();
    });
    expect(chip).toContain('PRIME');
    expect(chip).toContain('the Cow King');
  });

  test('★ EVERY card states a verdict — no card is silent', async ({ page }) => {
    await open(page, { ok: true, current: 'Moo Moo Farm', next: 'Cathedral, Catacombs, Blood Moor',
                       ts: Date.now() });
    const verdicts = await page.evaluate(() =>
      Array.from(document.querySelectorAll('#hd-tz .tzz'))
        .filter((c) => !c.classList.contains('tzz-pending'))
        .map((c) => ({
          name: (c.querySelector('b')?.textContent || '').trim(),
          tag: (c.querySelector('.tzz-tag')?.textContent || '').trim(),
        })));
    expect(verdicts.length).toBeGreaterThanOrEqual(4);
    for (const v of verdicts) {
      // v1801 — the padlock is gone (see below), so the TAG is now the only verdict carrier and
      // every card must have one. That is a STRONGER assertion than the original, which accepted
      // a lock glyph in place of a badge.
      expect(v.tag,
        `"${v.name}" rendered with no verdict at all — an absent badge cannot mean both "fine" ` +
        'and "unremarkable"').not.toBe('');
    }
  });

  /* v1801 — THIS TEST WAS INVERTED ON PURPOSE, and the reason is recorded rather than the old
     assertion quietly deleted.

     v1588 made a thin zone inert — aria-disabled, no role, no handler, a padlock where the tag
     goes — and this spec pinned it. That was defensible while 15 of 66 zones were thin. v1801
     removes the level term from _tzTier (v1585 had already diagnosed it as meaningless: terror
     lifts any TZ area to mlvl 96, so base level is precisely what the boost overrides), which
     takes thin to 40 of 66. A lock over most of the map stops informing him of a ranking and
     starts punishing him for one.

     Konyo, asked directly, chose: greyed and cancelled, still clickable. So the VERDICT must
     survive in full — the tag, the grey, the wording — and only the DEAD HANDLER goes. This test
     now pins exactly that pair, because the easy way to get this wrong is to unlock the card and
     let it stop looking thin. */
  test('★ a THIN zone still reads as thin — but it is no longer a dead card', async ({ page }) => {
    await open(page, { ok: true, current: 'Blood Moor', next: 'Catacombs', ts: Date.now() });
    const c = await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('#hd-tz .tzz'))
        .find((x) => (x.querySelector('b')?.textContent || '').trim() === 'Blood Moor');
      if (!el) return null;
      return {
        tier: el.classList.contains('tzz-thin'),
        opacity: getComputedStyle(el).opacity,
        grayscale: getComputedStyle(el).filter.indexOf('grayscale') >= 0,
        tag: (el.querySelector('.tzz-tag')?.textContent || '').trim(),
        title: el.getAttribute('title') || '',
        role: el.getAttribute('role'),
        tabindex: el.getAttribute('tabindex'),
        onclick: el.getAttribute('onclick'),
        disabled: el.getAttribute('aria-disabled'),
        hasLockGlyph: !!el.querySelector('.tzz-lock'),
      };
    });
    expect(c).toBeTruthy();
    // the verdict, undiminished
    expect(c!.tier, 'Blood Moor (den 520) must still be thin').toBe(true);
    expect(parseFloat(c!.opacity), 'a thin zone that is not greyed tells him nothing').toBeLessThanOrEqual(0.35);
    expect(c!.grayscale, 'the grayscale half of the treatment is gone').toBe(true);
    expect(c!.tag, 'the tag is now the ONLY verdict carrier — it cannot be empty').toBe('THIN');
    expect(c!.title.toLowerCase(), 'the card must still say why it is thin').toContain('not worth the window');
    // ...and the dead handler, gone
    expect(c!.role, 'he chose clickable — this must route').toBe('button');
    expect(c!.tabindex, 'and be keyboard reachable').not.toBeNull();
    expect(c!.onclick, 'and actually carry a handler').not.toBeNull();
    expect(c!.disabled, 'aria-disabled contradicts a card that routes').toBeNull();
    expect(c!.hasLockGlyph, 'a padlock promises the click will not work, and now it does').toBe(false);
  });

  test('★ v1602 — a group that SPANS ACTS says so; a same-act group stays quiet', async ({ page }) => {
    /* Konyo, seeing Frozen Tundra (act 5) beside Infernal Pit (act 4) under one UP NEXT: "how can
       act 4 and act 5 be in the same NEXT terror zone?" They can — the upstream feed serves that
       pair as ONE group, and of the 34 distinct groups in his own 95-window history TWO pair an
       Act 4 pit with an Act 5 zone ("Arreat Plateau and Pit of Acheron" is the other). Terror-zone
       slots are the game's own definitions, not areas that touch. Every OTHER group is contiguous,
       which is exactly why the two that are not read as a bug — so the panel now says it. */
    await open(page, { ok: true, current: 'Tamoe Highland, Outer Cloister, and The Pit',
                       next: 'Frozen Tundra and Infernal Pit', ts: Date.now() });
    const chips = await page.evaluate(() => ({
      next: (document.querySelector('#hd-tz .tz-slot.next .tz-together')?.textContent || '').trim(),
      now: (document.querySelector('#hd-tz .tz-slot.now .tz-together')?.textContent || '').trim(),
    }));
    expect(chips.next, 'the cross-act group must name its acts, or it reads as two slots glued together')
      .toMatch(/acts\s*4\+5/i);
    expect(chips.now, 'three Act 1 zones need no act note — that would be noise on the common case')
      .not.toMatch(/acts/i);
    expect(chips.now, 'the count itself still shows').toContain('3');
  });
});
