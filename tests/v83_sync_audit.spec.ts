import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const ROOT = path.resolve(__dirname, '..');
const URL = 'file://' + path.join(ROOT, 'bible.html');

// ─────────────────────────────────────────────────────────────────────────────
// v83 — WEBSITE SYNCHRONIZATION AUDIT
//
// A standing "is everything still wired to everything" sweep. The bible's whole
// architecture is symmetry: every nav tab has a panel + a nav-widget chip + a
// global-search command; every named drop in a data module routes to a real card
// AND is searchable; the art helper never drops loading="lazy" (REG-001); and the
// 3 RoW drop anchors agree across the live data, the anchor spec, and the docs.
//
// This spec is the machine-readable contract for that symmetry. When an agent adds
// a feature (a tab, a data module, an anchor) but forgets to wire one of its mirror
// surfaces, THIS goes red — surfacing the drift instead of letting it ship silently.
// Keep it green by wiring the mirror, not by relaxing the assertion.
// Cross-referenced docs: GAME_RULES.md (anchors/provenance) · BUILD_LOG.md (ships).
// ─────────────────────────────────────────────────────────────────────────────

test.describe('v83 website synchronization audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('tab parity: every nav tab has a panel AND a nav-widget chip (no orphans either way)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const navTabs = [...document.querySelectorAll('.tabs .tab[data-tab]')].map(b => (b as HTMLElement).dataset.tab!);
      const panels = [...document.querySelectorAll('.tab-content[id^="tab-"]')].map(p => p.id.replace(/^tab-/, ''));
      const chips = [...document.querySelectorAll('#nav-widget .nav-chip[data-nav]')].map(c => c.getAttribute('data-nav')!);
      const missingPanel = navTabs.filter(t => !panels.includes(t));
      const missingChip = navTabs.filter(t => !chips.includes(t));
      const orphanPanel = panels.filter(p => !navTabs.includes(p));   // a panel with no nav button
      return { navTabs, panels, chips, missingPanel, missingChip, orphanPanel };
    });
    // every tab button resolves to a real panel + a navigation chip
    expect(r.missingPanel, `nav tabs with no #tab-<id> panel: ${r.missingPanel}`).toEqual([]);
    expect(r.missingChip, `nav tabs with no nav-widget chip: ${r.missingChip}`).toEqual([]);
    // and no panel is stranded without a way to reach it from the bar
    expect(r.orphanPanel, `panels with no nav tab button: ${r.orphanPanel}`).toEqual([]);
    // sanity: the bar grew to its current size (catches an accidental tab deletion)
    expect(r.navTabs.length).toBeGreaterThanOrEqual(10);
  });

  test('search parity: every nav tab (bar the home) is reachable from global search', async ({ page }) => {
    const tabs = await page.evaluate(() =>
      [...document.querySelectorAll('.tabs .tab[data-tab]')]
        .map(b => (b as HTMLElement).dataset.tab!)
        .filter(t => t !== 'main'));
    const missing: string[] = [];
    for (const id of tabs) {
      await page.fill('#gsearch-input', id);
      await page.waitForTimeout(180);
      const hit = await page.evaluate(() =>
        [...document.querySelectorAll('#gsearch-results .gsearch-item')]
          .some(el => (el.querySelector('.gsearch-cat') as HTMLElement)?.textContent?.trim() === 'tab'
                   && /switch to/i.test((el.querySelector('.gsearch-lab') as HTMLElement)?.textContent || '')));
      if (!hit) missing.push(id);
    }
    expect(missing, `nav tabs with NO "Switch to …" global-search command: ${missing}`).toEqual([]);
  });

  test('route parity: every named drop in the data modules resolves through the openDrop chain', async ({ page }) => {
    const r = await page.evaluate(() => {
      // mirror openDrop()'s resolution order exactly — a name "resolves" if any branch claims it
      const resolves = (name: string) => !!(
        (window as any).findHeraldTier(name) ||
        (window as any).findRune(name) ||
        (window as any).findColossalJewel(name) ||
        (window as any).findColossalStatue(name) ||
        (typeof (window as any).findMaterial === 'function' ? (window as any).findMaterial(name) : (findMaterial as any)(name)) ||
        (typeof ITEMS !== 'undefined' && (ITEMS as any[]).find(i => i.n === name))
      );
      const check = (names: string[]) => names.filter(n => !resolves(n));
      const jewels = (window as any).COLOSSAL_JEWELS.map((j: any) => j.n);
      const statues = (window as any).COLOSSAL_STATUES.map((s: any) => s.n);
      const heralds = (window as any).HERALD_TIERS.map((h: any) => h.n);
      const uberDrops = [...new Set((window as any).UBER_BOSSES.filter((b: any) => b.drop).map((b: any) => b.drop))] as string[];
      return {
        jewelMiss: check(jewels), statueMiss: check(statues),
        heraldMiss: check(heralds), uberDropMiss: check(uberDrops),
        counts: { jewels: jewels.length, statues: statues.length, heralds: heralds.length, uberDrops: uberDrops.length },
      };
    });
    expect(r.counts.jewels).toBe(6);
    expect(r.counts.statues).toBe(5);
    expect(r.counts.heralds).toBe(5);
    expect(r.jewelMiss, `Colossal jewels that route to NOTHING: ${r.jewelMiss}`).toEqual([]);
    expect(r.statueMiss, `Colossal statues that route to NOTHING: ${r.statueMiss}`).toEqual([]);
    expect(r.heraldMiss, `Herald tiers that route to NOTHING: ${r.heraldMiss}`).toEqual([]);
    expect(r.uberDropMiss, `Uber-boss drops that route to NOTHING: ${r.uberDropMiss}`).toEqual([]);
  });

  test('endgame-relic parity: every pinnacle relic name still resolves to a card', async ({ page }) => {
    const miss = await page.evaluate(() => {
      const resolves = (name: string) => !!(
        (window as any).findHeraldTier(name) || (window as any).findRune(name) ||
        (window as any).findColossalJewel(name) || (window as any).findColossalStatue(name) ||
        (typeof (window as any).findMaterial === 'function' ? (window as any).findMaterial(name) : (findMaterial as any)(name)) ||
        (typeof ITEMS !== 'undefined' && (ITEMS as any[]).find(i => i.n === name))
      );
      return [...(ENDGAME_RELICS as Set<string>)].filter(n => !resolves(n));
    });
    expect(miss, `ENDGAME_RELICS members that route to NOTHING: ${miss}`).toEqual([]);
  });

  test('collapse parity: every planner in the 🧰 tools tab is a collapsible card (no odd-one-out)', async ({ page }) => {
    // The user-flagged asymmetry: two planners were collapsible boss-cards with a
    // proper title + ▾ chevron, but the Item Set Tracker was a bare always-open <h2>.
    // Tools all share ONE idiom: .boss-card.collapsible (toggleCardCollapse). This
    // smokes out any future tool added without matching the established pattern.
    const r = await page.evaluate(() => {
      const panel = document.getElementById('tab-tools')!;
      const cards = [...panel.querySelectorAll(':scope > .boss-card')];
      const bad = cards.filter(c =>
        !c.classList.contains('collapsible') ||
        !c.querySelector(':scope > .boss-header[onclick*="toggleCardCollapse"]') ||
        !c.querySelector(':scope > .boss-body'));
      // a bare <h2> section directly in the panel is the exact old asymmetry
      const bareH2 = [...panel.querySelectorAll(':scope > h2')].map(h => (h.textContent || '').trim());
      const startCollapsed = cards.every(c => c.classList.contains('collapsed'));
      return { cardCount: cards.length, badIds: bad.map(c => c.id), bareH2, startCollapsed };
    });
    expect(r.cardCount).toBeGreaterThanOrEqual(3);
    expect(r.badIds, `tools-tab cards that are NOT collapsible boss-cards: ${r.badIds}`).toEqual([]);
    expect(r.bareH2, `tools-tab has bare <h2> sections that should be collapsible cards: ${r.bareH2}`).toEqual([]);
    expect(r.startCollapsed, 'tools-tab cards should default collapsed (tidy, title-only)').toBe(true);
  });

  test('section-header parity: every section-list tab (main · rotw · ref) uses ONLY collapsible .sec-h cards (no bare <h2>)', async ({ page }) => {
    // v89 unified the Reference tab: it used to be 8 bare, always-open <h2> headers —
    // the odd-one-out vs main/rotw, which use the tidy collapsible .sec-h + .sec-body
    // idiom (toggleSec, ▾ chevron, collapsed by default). This invariant locks the
    // symmetry: in any of the three "list of sections" tabs, every DIRECT-CHILD <h2>
    // must be a .sec-h with a toggleSec handler, a ▾ chevron, and an adjacent .sec-body.
    // (Detail-card <h2.gbc-name>/<h2.gic-name> are nested, not direct children — exempt.)
    const r = await page.evaluate(() => {
      const tabs = ['main', 'rotw', 'ref'];
      const bad: Record<string, string[]> = {};
      for (const id of tabs) {
        const panel = document.getElementById('tab-' + id);
        if (!panel) { bad[id] = ['<missing panel>']; continue; }
        const heads = [...panel.querySelectorAll(':scope > h2')];
        const offenders = heads.filter(h =>
          !h.classList.contains('sec-h') ||
          !(h.getAttribute('onclick') || '').includes('toggleSec') ||
          !h.querySelector('.sec-chev') ||
          !(h.nextElementSibling && h.nextElementSibling.classList.contains('sec-body'))
        ).map(h => (h.textContent || '').trim().slice(0, 40));
        if (offenders.length) bad[id] = offenders;
      }
      const counts = Object.fromEntries(tabs.map(id => {
        const p = document.getElementById('tab-' + id);
        return [id, p ? p.querySelectorAll(':scope > h2.sec-h').length : 0];
      }));
      return { bad, counts };
    });
    expect(r.bad, `section-list tabs with bare/non-collapsible <h2> headers: ${JSON.stringify(r.bad)}`).toEqual({});
    // sanity: each tab still has its sections (catches an accidental wipe)
    expect(r.counts.ref, 'ref should have its 8 collapsible sections').toBeGreaterThanOrEqual(8);
    expect(r.counts.main).toBeGreaterThanOrEqual(4);
    expect(r.counts.rotw).toBeGreaterThanOrEqual(5);
  });

  test('hover-glow parity: every clickable item/row/chip hover carries the golden box-shadow glow', async ({ page }) => {
    // v90 (Batch 3) — the bible's clickable affordances (item tiles, grail tiles, boss
    // nav chips, source jump-chips, top-drop rows) used to lift inconsistently: some had
    // the canonical golden glow (transform + box-shadow, as on .fi-clickable/.zd-item-click),
    // others only swapped a border colour with no shadow. This locks the unification:
    // every one of these clickable hover selectors must declare a box-shadow glow.
    // (Match selectors EXACTLY so ::after / .blocked / scoped variants don't satisfy it.)
    const r = await page.evaluate(() => {
      const targets = ['.item-tile:hover', '.boss-chip:hover', '.gbc-grail-item:hover',
        '.source-chip:hover', '.top-drop-row:hover', '.fi-clickable:hover', '.zd-item-click:hover'];
      const acc: Record<string, string> = Object.fromEntries(targets.map((t) => [t, '']));
      for (const sheet of [...document.styleSheets]) {
        let rules: CSSRule[];
        try { rules = [...((sheet as CSSStyleSheet).cssRules || [])]; } catch { continue; }
        for (const rule of rules) {
          if (!(rule instanceof CSSStyleRule)) continue;
          const parts = (rule.selectorText || '').split(',').map((s) => s.trim());
          for (const t of targets) if (parts.includes(t)) acc[t] += ' ' + rule.style.cssText;
        }
      }
      const missing = targets.filter((t) => !/box-shadow/.test(acc[t]));
      return { missing, acc };
    });
    expect(r.missing, `clickable hover selectors missing the box-shadow glow: ${JSON.stringify(r.missing)}`).toEqual([]);
  });

  test('gbc-format parity: every drop-source entity card uses the golden .gbc-card shell with an artOr emblem', async ({ page }) => {
    // #52 / v91 — the master goal is one unified "Baal boss-card" design language for
    // every drop-SOURCE entity. Boss + TZ-zone + Herald-apex were already .gbc-card;
    // v91 brought super-uniques into the same shell (they used the lean .zd-* idiom).
    // This locks it: each entity detail builder must emit a .gbc-card with .gbc-header,
    // .gbc-name, and an artOr emblem (<img> for real art OR the emoji/gbc-emoji fallback).
    const r = await page.evaluate(() => {
      const win = window as any;
      const su = (SUPER_UNIQUES as any[]).find((s) => s.name === 'Eldritch the Rectifier') || (SUPER_UNIQUES as any[])[0];
      const zone = (TZ_ZONES as any[])[0];
      const cards: Record<string, string> = {
        superUnique: win.superUniqueDetailHtml(su),
        tzZone: win.zoneDetailHtml(zone),
      };
      const check = (html: string) => ({
        shell: /class="gbc-card/.test(html),
        header: /gbc-header/.test(html),
        name: /gbc-name/.test(html),
        emblem: /<img\b|gbc-emoji|d2art-fallback/.test(html),
        noUndef: !/undefined/.test(html),
      });
      return {
        superUnique: check(cards.superUnique),
        tzZone: check(cards.tzZone),
        // honesty markers must survive the re-shell
        suCaveat: /pending silospen pull/.test(cards.superUnique),
        suTitle: /super-unique detail/.test(cards.superUnique),
      };
    });
    for (const [card, c] of Object.entries({ superUnique: r.superUnique, tzZone: r.tzZone })) {
      expect(c.shell, `${card} missing .gbc-card shell`).toBe(true);
      expect(c.header, `${card} missing .gbc-header`).toBe(true);
      expect(c.name, `${card} missing .gbc-name`).toBe(true);
      expect(c.emblem, `${card} missing artOr emblem`).toBe(true);
      expect(c.noUndef, `${card} renders 'undefined'`).toBe(true);
    }
    expect(r.suCaveat, 'super-unique lost its pending-odds caveat in the re-shell').toBe(true);
    expect(r.suTitle, 'super-unique lost its "super-unique detail" title in the re-shell').toBe(true);
  });

  test('event-card head parity (#52 / v92): every pinnacle event-card head shares the golden banner — emblem + titles + tier badge', async ({ page }) => {
    // v92 — the #tab-ancients drop-source events (Uber Tristram, Diablo Clone, Secret
    // Cow Level, Colossal Ancients, the 9-card + relic indexes, 22 Nights) used the lean
    // .ec-* head. This brings them into the .gbc-header banner design language: every head
    // now carries an artOr-structure emblem (.d2art-wrap.ec-logo > .d2art-img|.d2art-fallback),
    // the .ec-titles block, a chevron, AND a .ec-tier badge (label + val) mirroring .gbc-tier.
    // Locks the unification so a future event card can't ship as a bare head again.
    const r = await page.evaluate(() => {
      const heads = [...document.querySelectorAll('#tab-ancients > .event-card > .event-card-head')];
      const bad = heads.map((h) => {
        const card = (h.parentElement as HTMLElement).id;
        const problems: string[] = [];
        // 22 Nights is a seasonal modifier WINDOW (not a drop-source) -> deliberately no
        // item art / emblem (locked by v47). Every other head must carry the artOr emblem.
        const seasonalNoArt = card.includes('22-nights');
        if (!seasonalNoArt && !h.querySelector('.d2art-wrap.ec-logo')) problems.push('no emblem');
        if (!seasonalNoArt && !h.querySelector('.ec-logo .d2art-img, .ec-logo .d2art-fallback')) problems.push('emblem lacks artOr img/fallback structure');
        if (!h.querySelector('.ec-titles .ec-title')) problems.push('no .ec-title');
        const tier = h.querySelector(':scope > .ec-tier');
        if (!tier) problems.push('no .ec-tier badge');
        else if (!tier.querySelector('.ec-tier-label') || !tier.querySelector('.ec-tier-val')) problems.push('tier badge missing label/val');
        if (!h.querySelector('.ec-chevron')) problems.push('no chevron (collapse affordance)');
        return problems.length ? { card, problems } : null;
      }).filter(Boolean);
      return { count: heads.length, bad };
    });
    expect(r.count, 'expected the 7 pinnacle event cards').toBeGreaterThanOrEqual(7);
    expect(r.bad, `event-card heads not matching the golden banner contract: ${JSON.stringify(r.bad)}`).toEqual([]);
  });

  test('art invariant (REG-001 lock): artOr keeps loading="lazy" on real art', async ({ page }) => {
    const r = await page.evaluate(() => {
      // a name with verified art → an <img>; a name without → the emoji fallback only
      const withArt = (window as any).artOr('Zod', '🪨', 'sm');
      const noArt = (window as any).artOr('___definitely_no_art___', '👑', 'lg');
      return {
        hasImg: /<img\b/.test(withArt),
        lazy: /loading="lazy"/.test(withArt),
        onerr: /onerror=/.test(withArt),
        fallbackNoImg: !/<img\b/.test(noArt) && /d2art-fallback/.test(noArt),
      };
    });
    expect(r.hasImg).toBe(true);
    expect(r.lazy, 'artOr dropped loading="lazy" — this is exactly REG-001').toBe(true);
    expect(r.onerr).toBe(true);
    expect(r.fallbackNoImg).toBe(true);
  });

  test('docs ↔ data anchor sync: the 3 RoW anchors agree across data, anchor spec, and GAME_RULES', async () => {
    // No page needed — this is a cross-file consistency check (the kind of drift that
    // happens when one agent re-tunes an anchor and forgets a mirror surface).
    const anchorsSpec = fs.readFileSync(path.join(ROOT, 'tests', '02_verified_anchors.spec.ts'), 'utf8');
    const gameRules = fs.readFileSync(path.join(ROOT, 'GAME_RULES.md'), 'utf8');
    const baseline = JSON.parse(fs.readFileSync(path.join(ROOT, 'baseline', 'integrity_baseline.json'), 'utf8'));

    // canonical RoW anchors (see GAME_RULES.md drop-odds provenance)
    const ANCHORS = ['1:836', '1:2,286', '1:4,080'];
    for (const a of ANCHORS) {
      expect(anchorsSpec.includes(a), `anchor ${a} missing from 02_verified_anchors.spec.ts`).toBe(true);
      expect(gameRules.includes(a), `anchor ${a} missing from GAME_RULES.md`).toBe(true);
    }
    // and the integrity baseline's Meph/Hell/Shako probe must equal the 836 anchor
    expect(baseline.probe_meph_shako?.hell, 'integrity baseline probe_meph_shako.hell drifted from the 1:836 anchor').toBe(836);
  });
});
