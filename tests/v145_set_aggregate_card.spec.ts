// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';
import { ensureCardExpanded } from './_cards';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v145 — the unified full-set ID card (same structure as the Sunder Charms card).
// Opening a set's collective name (e.g. "Tal Rasha's Wrappings") routes to ONE rich
// card: every piece as an art tile at the bottom (name + slot + req lvl, no "(slot)"
// duplication) + the full set bonus ("the additives") section. Built ENTIRELY off the
// verified ITEM_CODEX set-cat data — no fabrication, no parallel array. The set tracker
// card title becomes a clickable gateway. Individual piece names still NOT routable.
test.describe('v145 unified full-set ID card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
  });

  // ITEM_CODEX is module-scoped (not on window), so drive through the window-exposed
  // helpers with the known verified set names.
  const KNOWN_SETS = [
    "Tal Rasha's Wrappings", "Trang-Oul's Avatar", "Immortal King", "M'avina's Battle Hymn",
    "Natalya's Odium", "Griswold's Legacy", "Aldur's Watchtower", "Sigon's Complete Steel",
    "Sazabi's Grand Tribute", "Naj's Ancient Vestige", "Hwanin's Majesty", "Orphan's Call",
  ];

  test('isSetAggregate + setDetailHtml resolve every known set, and individual pieces do NOT', async ({ page }) => {
    const r = await page.evaluate((sets) => {
      const isAgg = (window as any).isSetAggregate as (n: string) => boolean;
      const html = (window as any).setDetailHtml as (n: string) => string;
      return {
        allAgg: sets.every((n) => isAgg(n)),
        allRender: sets.every((n) => /set-items-card/.test(html(n))),
        // a single piece is NOT a set aggregate (keeps its art+hover-only behaviour)
        pieceNotAgg: !isAgg("Tal Rasha's Adjudication"),
        unmappedNotAgg: !isAgg('No Such Set 999'),
        // tracker-style "(Class)" suffix still resolves
        suffixAgg: isAgg("Tal Rasha's Wrappings (Sorc)"),
      };
    }, KNOWN_SETS);
    expect(r.allAgg).toBe(true);
    expect(r.allRender).toBe(true);
    expect(r.pieceNotAgg).toBe(true);
    expect(r.unmappedNotAgg).toBe(true);
    expect(r.suffixAgg).toBe(true);
  });

  test('openDrop renders the Tal Rasha set card: all pieces as art tiles + the full set bonus', async ({ page }) => {
    const r = await page.evaluate(async () => {
      (window as any).openDrop("Tal Rasha's Wrappings (Sorc)");
      await new Promise((res) => setTimeout(res, 1400));
      const card = document.querySelector('#item-detail .set-items-card');
      const tiles = [...document.querySelectorAll('#item-detail .set-items-card .colossal-grid .colossal-tile')];
      const bonuses = [...document.querySelectorAll('#item-detail .set-items-card .set-bonus-row .zd-v')].map((e) => e.textContent || '');
      const title = (document.querySelector('#item-detail .set-items-card .gic-name')?.firstChild?.textContent || '').trim();
      return {
        shown: !!card,
        title,
        tileCount: tiles.length,
        allHaveArt: tiles.every((t) => !!t.querySelector('.d2art-img')),
        noFailed: tiles.every((t) => !t.querySelector('.d2art-wrap.d2art-failed')),
        // slot text shows the base slot WITHOUT the redundant "(slot)" parenthetical
        slots: tiles.map((t) => t.querySelector('.ct-sub')?.textContent || ''),
        names: tiles.map((t) => t.querySelector('.ct-name')?.textContent || ''),
        bonuses,
      };
    });
    expect(r.shown).toBe(true);
    expect(r.title).toBe("Tal Rasha's Wrappings");
    expect(r.tileCount).toBe(5);
    expect(r.allHaveArt).toBe(true);
    expect(r.noFailed).toBe(true);
    // no duplicate "(amulet)"-style suffix in either the name or the slot line
    expect(r.names.every((n) => !/\(/.test(n))).toBe(true);
    expect(r.slots.every((s) => !/\(/.test(s))).toBe(true);
    expect(r.slots[0]).toContain('Amulet');
    // the full set bonus (the "additives") is present
    expect(r.bonuses).toContain('+3 to Sorceress Skill Levels');
    expect(r.bonuses.length).toBeGreaterThanOrEqual(5);
  });

  test('the Item Set Tracker title is a clickable gateway for every codex-backed set', async ({ page }) => {
    // v1751 — through the shared helper; the blind toggle here closed the card whenever a
    // previous step had already opened it, and a closed card has no .set-card-open to find.
    await ensureCardExpanded(page, 'set-tracker-card', '#set-tracker .set-card');
    const r = await page.evaluate(async () => {
      const opens = [...document.querySelectorAll('#set-tracker .set-card-open')];
      const isAgg = (window as any).isSetAggregate as (n: string) => boolean;
      const titleName = (el: Element) => (el.textContent || '').replace(/[↗✓]/g, '').trim();
      // every clickable title must actually resolve to a set card (no dead routes)
      const allResolve = opens.every((o) => isAgg(titleName(o)));
      // sets WITHOUT verified codex data must NOT be clickable (honest: no dead route)
      const sets = [...document.querySelectorAll('#set-tracker .set-card')];
      const nonRoutableHaveNoOpen = sets
        .map((c) => ({ name: titleName(c.querySelector('.set-card-name') as Element), open: !!c.querySelector('.set-card-open') }))
        .filter((s) => !isAgg(s.name))
        .every((s) => !s.open);
      return { clickable: opens.length, allResolve, nonRoutableHaveNoOpen };
    });
    expect(r.clickable).toBeGreaterThanOrEqual(8);
    expect(r.allResolve).toBe(true);
    expect(r.nonRoutableHaveNoOpen).toBe(true);
  });

  test('no console errors when opening a set card', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.evaluate(async () => {
      (window as any).openDrop("Natalya's Odium (Sin)");
      await new Promise((res) => setTimeout(res, 800));
      (window as any).openDrop("Immortal King (Barb)");
      await new Promise((res) => setTimeout(res, 800));
    });
    expect(errs).toEqual([]);
  });
});
