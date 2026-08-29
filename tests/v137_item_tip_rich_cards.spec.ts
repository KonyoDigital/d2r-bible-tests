import { test, expect } from './_net_stub'; // diablo2.io art stubbed — kills net-flake (audit 2026-06-12)
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v137 — every grail unique/set/runeword with a verified per-item stat block now
// gets the FULL diablo2.io-style rich hover card (the same card the sunders get),
// not just a one-liner. ITEM_TIP is the registry transcribed per-item from
// diablo2.io's RotW item DB (ajax tooltips): exact stat lines, tier, base item,
// req/quality level. Variable ranges render as green [X-Y] chips. ZERO fabrication —
// items WITHOUT a verified per-item block fall back to the ITEM_INFO one-liner.

test.describe('v137 ITEM_TIP rich stat cards (verified per-item, no fabrication)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(800);
  });

  test('ITEM_TIP is exposed with the full verified registry; every entry is well-formed', async ({ page }) => {
    const r = await page.evaluate(() => {
      const T = (window as any).ITEM_TIP || {};
      const keys = Object.keys(T);
      const ALLOWED_TIERS = new Set(['Unique', 'Elite Unique', 'Set', 'Elite Set', 'Runeword']);
      let emptyLines = 0, badTier = 0, noLinesArray = 0;
      for (const k of keys) {
        const o = T[k];
        if (!Array.isArray(o.l)) { noLinesArray++; continue; }
        if (o.l.length === 0) emptyLines++;
        if (o.t && !ALLOWED_TIERS.has(o.t)) badTier++;
      }
      return { count: keys.length, emptyLines, badTier, noLinesArray };
    });
    expect(r.count).toBeGreaterThanOrEqual(285);
    expect(r.noLinesArray).toBe(0);
    expect(r.emptyLines).toBe(0);   // no fabricated/empty cards
    expect(r.badTier).toBe(0);      // tiers only from the known set
  });

  test('flagship grail items render full rich cards (tier + base + req + stat lines)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      const probe = (n: string) => { const x = f(n); return { rich: x.rich, desc: x.desc, art: x.artName }; };
      return {
        soj: probe('The Stone of Jordan'),
        shako: probe('Harlequin Crest (Shako)'),
        mara: probe("Mara's Kaleidoscope"),
        griffon: probe("Griffon's Eye"),
      };
    });
    // SoJ — Unique Ring, exact affixes, no ranges
    expect(r.soj.rich).toBe(true);
    expect(r.soj.desc).toContain('att-type');
    expect(r.soj.desc).toContain('Unique &middot; Ring');
    expect(r.soj.desc).toContain('Req level: 29');
    expect(r.soj.desc).toContain('+1 To All Skills');

    // Shako — Elite Unique, level-based range chip
    expect(r.shako.rich).toBe(true);
    expect(r.shako.desc).toContain('Elite Unique &middot; Shako');
    expect(r.shako.desc).toContain('+2 To All Skills');
    /* v2263 — HIS LAW, AND THIS LINE WAS ASSERTING ITS OPPOSITE.
       Konyo: "it shouldnt show a range for it (it isnt a gamble) like the rest of the buffs that
       get rolled... thats the law that needs to be coded here." v2249 split the two kinds of
       bracket in _sunMarkup: a stat that ROLLS when the item is made keeps att-var (you can chase
       a better one), and a stat DERIVED from character level becomes att-lvl (re-making the item
       cannot improve it). The Shako's +[1-148] Life/Mana is the level-scaled kind — this line's own
       comment said so while asserting the roll class, and it has been red on CI since v2249.

       Measured on the live page 2026-08-29 via _arttipResolve: Shako att-lvl 2 / att-var 0;
       Mara's att-var 1 / att-lvl 0; Griffon's att-var 3 / att-lvl 0. Assert BOTH directions on the
       same page — a classifier that returned one class for everything would satisfy either half
       alone, and this pair is the only thing that can tell his law from a stuck answer. */
    expect(r.shako.desc, 'the Shako\'s [1-148] is LEVEL-SCALED, not a roll').toContain('att-lvl');
    expect(r.shako.desc, 'a level-scaled stat is being offered as a re-rollable gamble')
      .not.toContain('att-var');

    // Mara's — Unique Amulet, all-res range chip
    expect(r.mara.rich).toBe(true);
    expect(r.mara.desc).toContain('Unique &middot; Amulet');
    expect(r.mara.desc).toContain('att-var');     // +[20-30] all-res IS a roll — the other half of the pair
    expect(r.mara.desc, "Mara's all-res rolls; calling it level-scaled tells him not to chase it")
      .not.toContain('att-lvl');
    expect(r.mara.desc).toContain('+2 To All Skills');

    // Griffon's — Elite Unique Diadem
    expect(r.griffon.rich).toBe(true);
    expect(r.griffon.desc).toContain('Elite Unique &middot; Diadem');
  });

  test('range markers become green chips; resolution prefers rich card over the one-liner', async ({ page }) => {
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      // The Stone of Jordan has BOTH a curated ITEM_INFO one-liner AND a verified
      // ITEM_TIP block — it must resolve to the rich block, not the one-liner.
      const soj = f('The Stone of Jordan');
      // no raw bracket markers should survive into the rendered html
      const mara = f("Mara's Kaleidoscope");
      return {
        sojRich: soj.rich,
        sojInfo: /att-info/.test(soj.desc),         // must NOT be the one-liner wrapper
        rawBrackets: /\[[0-9]/.test(mara.desc),     // unrendered [X markers leaked?
        hasChip: /att-var/.test(mara.desc),
      };
    });
    expect(r.sojRich).toBe(true);      // rich card wins over one-liner
    expect(r.sojInfo).toBe(false);
    expect(r.rawBrackets).toBe(false); // every [X-Y] became a chip
    expect(r.hasChip).toBe(true);
  });

  test('hovering a grail item shows the rich card; data-arttip elements pick it up', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openDrop("Mara's Kaleidoscope");
      const el = document.querySelector('[data-arttip="Mara\'s Kaleidoscope"],[data-art-logo="Mara\'s Kaleidoscope"]') as HTMLElement | null;
      const tip = document.getElementById('arttip');
      if (!el) return { found: false };
      el.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 250, clientY: 250 }));
      return {
        found: true,
        on: tip?.classList.contains('on'),
        rich: tip?.classList.contains('tip-rich'),
        type: !!tip?.querySelector('.att-type'),
        aff: !!tip?.querySelector('.att-aff'),
        chip: !!tip?.querySelector('.att-var'),
        clickThrough: getComputedStyle(tip!).pointerEvents === 'none',
      };
    });
    if (r.found) {
      expect(r.on).toBe(true);
      expect(r.rich).toBe(true);
      expect(r.type).toBe(true);
      expect(r.aff).toBe(true);
      expect(r.chip).toBe(true);
      expect(r.clickThrough).toBe(true);
    }
  });

  test('rendering every ITEM_TIP card produces non-empty html with no console errors', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    const r = await page.evaluate(() => {
      const f = (window as any)._arttipResolve;
      const T = (window as any).ITEM_TIP || {};
      let empty = 0, notRich = 0;
      for (const k in T) {
        const x = f(k);
        if (!x.rich) notRich++;
        if (!x.desc || x.desc.length < 10) empty++;
      }
      return { empty, notRich, total: Object.keys(T).length };
    });
    expect(r.total).toBeGreaterThanOrEqual(285);
    expect(r.empty).toBe(0);
    expect(r.notRich).toBe(0);   // every ITEM_TIP key resolves to a rich card
    expect(errs).toEqual([]);
  });
});
