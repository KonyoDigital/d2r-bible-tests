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

  test('★ CATHEDRAL is honestly GOOD — adjacency is not a boss', async ({ page }) => {
    await open(page);
    const c = await cardFor(page, 'Cathedral');
    expect(c).toBeTruthy();
    expect(c!.tag,
      'promoting a 680-density corridor to PRIME on its neighbour\'s boss is advice, not data — ' +
      'and it stole the header chip from the zone that actually has Andariel').toBe('GOOD');
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
          lock: !!c.querySelector('.tzz-lock'),
        })));
    expect(verdicts.length).toBeGreaterThanOrEqual(4);
    for (const v of verdicts) {
      expect(v.tag || (v.lock ? 'LOCKED' : ''),
        `"${v.name}" rendered with no verdict at all — an absent badge cannot mean both "fine" ` +
        'and "unremarkable"').not.toBe('');
    }
  });

  test('★ a THIN zone is still locked and unclickable — the new badge did not soften it', async ({ page }) => {
    await open(page, { ok: true, current: 'Blood Moor', next: 'Catacombs', ts: Date.now() });
    const c = await page.evaluate(() => {
      const el = Array.from(document.querySelectorAll('#hd-tz .tzz'))
        .find((x) => (x.querySelector('b')?.textContent || '').trim() === 'Blood Moor');
      if (!el) return null;
      return {
        locked: el.classList.contains('tzz-locked'),
        disabled: el.getAttribute('aria-disabled') === 'true',
        role: el.getAttribute('role'),
        tabindex: el.getAttribute('tabindex'),
        onclick: el.getAttribute('onclick'),
        hasLockGlyph: !!el.querySelector('.tzz-lock'),
      };
    });
    expect(c).toBeTruthy();
    expect(c!.locked).toBe(true);
    expect(c!.disabled).toBe(true);
    expect(c!.role, 'a worthless zone must not be a button').not.toBe('button');
    expect(c!.tabindex, 'nor keyboard-reachable as one').toBeNull();
    expect(c!.onclick, 'nor routable').toBeNull();
    expect(c!.hasLockGlyph).toBe(true);
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
