import { test, expect } from '@playwright/test';
import * as path from 'path';
import { boardTokens, tokenRGB, assertTokens } from './_palette';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v294 (rewritten v1632) — every grail surface must render its item name in the IN-GAME
// quality colour that the app itself declares.
//
// THE PALETTE IS THE APP'S, NOT THE TEST'S. Deliberately, NO hex literal and NO rgb()
// literal appears anywhere in this file — not in an expectation, not in a test title,
// not in this comment. The old version pinned set green and magic blue as literals; when
// the palette was re-extracted from Konyo's install (the real FontColor* values) the file
// went RED ON THE FIX, and its prose header kept teaching the next reader the wrong
// numbers. A test that restates a constant the app owns is defending a value, not a rule.
//
// What is asserted instead, all read live off :root:
//   assertTokens  — every --q-* the app promises is DECLARED and RESOLVES to a real
//                   colour, so a deleted token fails loudly instead of null === null.
//   distinctness  — the quality colours are MUTUALLY DISTINCT, and none of them has
//                   collapsed onto the app's chrome gold (--gold/--gold-bright/--su).
//                   This is the assertion class that v1622 walked straight past: three
//                   tests checked a rarity CLASS was present and never what it computed
//                   to, so a rarity painted in chrome gold stayed green.
//   per-surface   — each rendered surface EQUALS its own resolved token AND DIFFERS from
//                   every other quality (its nearest confusable neighbours included).
//
// ✅ CLOSED at v1633. The divergence this block described — tiles and .arw-name on
// `--q-runeword` since v1628 while the runeword CARD TITLE still read `--q-orange`
// (crafted orange) — is fixed in bible.html, and the test below flipped with it, exactly
// as the pin instructed. Kept as a record of why that test asserts what it asserts.

// The five mutually-distinct board qualities, by _palette key (NOT by hex).
const QUALITIES = ['unique', 'set', 'magic', 'rare', 'orange'] as const;
type Quality = typeof QUALITIES[number];
// `runeword` is an ALIAS (declared as var(--q-unique)), so it is resolved and gated but
// deliberately excluded from the mutual-distinctness set.
const GATED = [...QUALITIES, 'runeword'] as const;
// Chrome/UI golds a rarity must never collapse onto — the v1622 shape. Board chrome gold
// comes from _palette's map; the other two are read by CSS name through tokenRGB.
const CHROME_BY_NAME = ['--gold', '--su'] as const;

type Tokens = Record<string, string | null>;

/** Board palette + the extra chrome golds, all resolved by the shared _palette spine. */
async function readTokens(page: any): Promise<Tokens> {
  const t: Tokens = { ...(await boardTokens(page)) };
  for (const n of CHROME_BY_NAME) t[n] = await tokenRGB(page, n);
  // assertTokens() throws PaletteTokenMissingError naming every key that did not resolve —
  // a renamed/deleted token fails LOUDLY here instead of null === null passing downstream.
  assertTokens(t, ...GATED, 'goldBright', ...CHROME_BY_NAME);
  return t;
}

async function colorOf(page: any, item: string, sel: string): Promise<string> {
  await page.evaluate((n: string) => (window as any).openDrop(n), item);
  await page.waitForTimeout(200);
  const c = await page.evaluate((s: string) => {
    const el = document.querySelector('#item-detail ' + s) as HTMLElement | null;
    return el ? getComputedStyle(el).color : null;
  }, sel);
  // A missing surface used to return null and could sail past a null-ish comparison.
  expect(c, `expected a rendered surface at "#item-detail ${sel}" for "${item}"`).not.toBeNull();
  return c as string;
}

/** surface === its own token, AND differs from every other quality. */
function expectQuality(color: string, t: Tokens, q: Quality, label: string) {
  expect(color, `${label} must equal the ${q} token (${t[q]})`).toBe(t[q]);
  for (const other of QUALITIES) {
    if (other === q) continue;
    expect(color, `${label} must NOT be painted the ${other} token`).not.toBe(t[other]);
  }
}

test.describe('v294 in-game rarity colours', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('every quality token is declared, resolves, and no two qualities share a colour', async ({ page }) => {
    const t = await readTokens(page);

    // Mutually distinct: the whole point of a rarity palette is telling rarities apart.
    const resolved = QUALITIES.map(q => t[q] as string);
    expect(new Set(resolved).size,
      `the ${QUALITIES.length} quality colours must be mutually distinct, got ${resolved.join(' / ')}`).toBe(QUALITIES.length);

    // ...and none may collapse onto the app's own chrome gold (the v1622 shape: a rarity
    // shipped as UI gold, invisible to any test that only checks a class is present).
    for (const q of QUALITIES) {
      for (const c of ['goldBright', ...CHROME_BY_NAME]) {
        expect(t[q], `the ${q} token must not be the chrome colour ${c}`).not.toBe(t[c]);
      }
    }

    // The alias must actually alias something in the palette, not dangle.
    expect(resolved, 'the runeword token must resolve to one of the declared quality colours')
      .toContain(t.runeword);
  });

  test('a unique item ID-card name is painted with the unique token', async ({ page }) => {
    const t = await readTokens(page);
    const c = await colorOf(page, 'The Stone of Jordan', '.aid-card.aid-r-unique .aid-item-name');
    expectQuality(c, t, 'unique', 'unique ID-card name');
  });

  test('a set item card title is painted with the set token', async ({ page }) => {
    const t = await readTokens(page);
    const c = await colorOf(page, "Sigon's Complete Steel", '.set-items-card .gic-name');
    expectQuality(c, t, 'set', 'set card title');
  });

  test('a runeword card title uses the runeword token, NOT crafted orange', async ({ page }) => {
    const t = await readTokens(page);
    const c = await colorOf(page, 'Spirit', '.runeword-card .gic-name');
    // v1633 flipped this, as the header pin instructed. A completed runeword is not a crafted
    // item and must never borrow crafted orange: the game paints its name FontColorGoldYellow,
    // the same gold as a unique, which is what --q-runeword resolves to.
    // NOT expectQuality(): that helper asserts the surface differs from every OTHER quality,
    // and a runeword's gold is legitimately identical to the unique token. Asserted directly.
    expect(c, 'the runeword card title must equal the --q-runeword token').toBe(t.runeword);
    // The claim is only meaningful while the two tokens are actually different colours — if
    // --q-orange were ever aliased onto the runeword gold, the line above would pass on a
    // surface still painting crafted orange and prove nothing.
    expect(t.runeword, 'runeword and crafted-orange tokens must stay distinguishable')
      .not.toBe(t.orange);
    // The remaining qualities it must never be confused with. `unique` is excluded on purpose
    // and only on purpose: the game paints both the same gold.
    for (const other of ['set', 'magic', 'rare', 'orange'] as const) {
      expect(c, `the runeword card title must NOT be the ${other} token`).not.toBe(t[other]);
    }
  });

  test('every grail item carries a rarity → none would fall back to default gold', async ({ page }) => {
    // KEPT (was already sound): _artRarity must classify every aid-card-routed grail
    // unique/set. Strengthened only by relationship — a classifier that answered the same
    // rarity for everything satisfied `!== ''` perfectly.
    const r = await page.evaluate(() => {
      const ar = (window as any)._artRarity;
      const names = ['The Stone of Jordan', 'Nagelring', "Sigon's Complete Steel", 'Tal Rasha set (any piece)'];
      return names.map(n => ({ n, r: ar(n) }));
    });
    for (const x of r) expect(x.r, `_artRarity("${x.n}") must classify`).not.toBe('');
    const byName: Record<string, string> = Object.fromEntries(r.map((x: any) => [x.n, x.r]));
    expect(byName["Sigon's Complete Steel"], 'a set item must not be classified as the unique quality')
      .not.toBe(byName['The Stone of Jordan']);
    expect(byName['Tal Rasha set (any piece)'], 'both set items must classify the same')
      .toBe(byName["Sigon's Complete Steel"]);
    expect(byName['Nagelring'], 'both uniques must classify the same').toBe(byName['The Stone of Jordan']);
  });
});

// ── v1632 — THE FLOATING TIP'S RUNEWORD AND RUNE CLASSES ──────────────────────────────────────
// The v1632 audit found a dead literal `#arttip.tip-r-rw .att-name,#arttip.tip-r-rune
// .att-name{color:#ffc070}` sitting ONE LINE BELOW the token rules at EQUAL specificity, so it won
// both: a completed runeword painted #ffc070 instead of --q-runeword, and a rune painted #ffc070
// instead of --rune. It removed the literal — and then a mutation check showed nothing had gone
// red, because the only tip-colour spec probed five rarity classes and never these two.
//
// A fix nobody can prove is a fix nobody can keep. This is the assertion that bites: it puts the
// real classes on the real element and compares the computed colour to the document's own token.
test.describe('v1632 — the tip colours runewords and runes from the token', () => {
  test('★★★ tip-r-rw is --q-runeword and tip-r-rune is --rune, not a literal', async ({ page }) => {
    await page.goto('file://' + require('path').resolve(__dirname, '..', 'bible.html'));
    await page.waitForTimeout(2400);
    const r = await page.evaluate(() => {
      const cs = getComputedStyle(document.documentElement);
      const hexToRgb = (h: string) => {
        const m = h.trim().replace('#', '').match(/.{2}/g) || [];
        return `rgb(${m.map((x) => parseInt(x, 16)).join(', ')})`;
      };
      // build the tip the way the app does: the rarity class lives on #arttip, the name inside it
      let tip: any = document.getElementById('arttip');
      if (!tip) {
        tip = document.createElement('div'); tip.id = 'arttip';
        tip.innerHTML = '<img alt=""><div class="att-name"></div><div class="att-desc"></div>';
        document.body.appendChild(tip);
      }
      const name: any = tip.querySelector('.att-name');
      const read = (cls: string) => {
        tip.classList.remove('tip-r-rw', 'tip-r-rune');
        tip.classList.add(cls);
        const c = getComputedStyle(name).color;
        tip.classList.remove(cls);
        return c;
      };
      return {
        rw: read('tip-r-rw'),
        rune: read('tip-r-rune'),
        wantRw: hexToRgb(cs.getPropertyValue('--q-runeword') || cs.getPropertyValue('--q-unique')),
        wantRune: hexToRgb(cs.getPropertyValue('--rune')),
      };
    });
    expect(r.rw, "a completed runeword's name is the unique gold, from the token").toBe(r.wantRw);
    expect(r.rune, 'a rune item wears its own orange, from the token').toBe(r.wantRune);
    // the specific literal that was overriding both, named so a reintroduction is unmistakable
    expect(r.rw, 'the dead #ffc070 literal is back').not.toBe('rgb(255, 192, 112)');
    expect(r.rune, 'the dead #ffc070 literal is back').not.toBe('rgb(255, 192, 112)');
  });
});
