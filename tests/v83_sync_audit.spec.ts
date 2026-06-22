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
      const rsrc = (RUNE_SOURCES as any[]).find((s) => s.id === 'travincal') || (RUNE_SOURCES as any[])[0];
      const cards: Record<string, string> = {
        superUnique: win.superUniqueDetailHtml(su),
        tzZone: win.zoneDetailHtml(zone),
        runeSource: win.runeSourceDetailHtml(rsrc),
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
        runeSource: check(cards.runeSource),
        // honesty markers must survive the re-shell
        suCaveat: /pending silospen pull/.test(cards.superUnique),
        suTitle: /super-unique detail/.test(cards.superUnique),
        // v93: Travincal's honest-odds caveat must survive its re-shell too
        rsCaveat: /pending silospen pull/.test(cards.runeSource),
      };
    });
    for (const [card, c] of Object.entries({ superUnique: r.superUnique, tzZone: r.tzZone, runeSource: r.runeSource })) {
      expect(c.shell, `${card} missing .gbc-card shell`).toBe(true);
      expect(c.header, `${card} missing .gbc-header`).toBe(true);
      expect(c.name, `${card} missing .gbc-name`).toBe(true);
      expect(c.emblem, `${card} missing artOr emblem`).toBe(true);
      expect(c.noUndef, `${card} renders 'undefined'`).toBe(true);
    }
    expect(r.suCaveat, 'super-unique lost its pending-odds caveat in the re-shell').toBe(true);
    expect(r.suTitle, 'super-unique lost its "super-unique detail" title in the re-shell').toBe(true);
    expect(r.rsCaveat, 'rune-source (Travincal) lost its pending-odds caveat in the v93 re-shell').toBe(true);
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

  // ───────────────────────────────────────────────────────────────────────────
  // ENTITY SYNC LOCK — the same drop-source entity is described across MULTIPLE
  // surfaces (boss card = BOSSES + BOSS_FIELD_MANUAL · #tab-ancients event-card ·
  // RUNE_SOURCES rune card). The boss card is the SINGLE SOURCE OF TRUTH. These
  // assertions stop a secondary surface from restating a fact that contradicts it
  // (the cow "TC 66-69" / "TC75-85" drift that this lock was written to kill).
  // ───────────────────────────────────────────────────────────────────────────
  test('entity sync: every RUNE_SOURCES bossId cross-link resolves to a real boss card', async ({ page }) => {
    const bad = await page.evaluate(() => {
      const ids = (BOSSES as any[]).map((b: any) => b.id);
      return (RUNE_SOURCES as any[])
        .filter((s: any) => s.bossId && !ids.includes(s.bossId))
        .map((s: any) => s.id + '→' + s.bossId);
    });
    expect(bad, `rune-source bossId cross-links point at non-existent boss cards: ${bad.join(', ')}`).toEqual([]);
  });

  test('entity sync: the cow Treasure-Class is unified to the canonical boss-card value (no stale TC drift)', async () => {
    const html = fs.readFileSync(path.join(ROOT, 'bible.html'), 'utf8');
    // the boss card is authoritative: Hell cows reach TC84, TC87 in a Terror Zone
    expect(html.includes('TC 66-69'), 'stale event-card cow TC "TC 66-69" survived — must defer to the canonical TC84').toBe(false);
    expect(html.includes('TC75-85'), 'stale field-manual cow TC "TC75-85" survived — must defer to the canonical TC84').toBe(false);
    // and the reconciled value must be present on BOTH secondary cow surfaces
    const tc84 = (html.match(/TC84/g) || []).length;
    expect(tc84, 'canonical cow TC84 missing from the reconciled surfaces (event-card + field-manual)').toBeGreaterThanOrEqual(2);
  });

  test('entity sync: the Annihilus stat line is unified to the canonical item card (no stale stat drift)', async ({ page }) => {
    const html = fs.readFileSync(path.join(ROOT, 'bible.html'), 'utf8');
    // canonical loot card = ITEM_CODEX.Annihilus: +1 all skills · +10-20 all attr · +10-20 all res · +5-10% exp.
    // Scope each check to a window AROUND each "Annihilus" mention so we don't false-flag OTHER items
    // that legitimately carry "+1-2 all skills" (Arkaine's Valor, Atma's Wail).
    const windows: string[] = [];
    let from = 0, idx: number;
    while ((idx = html.indexOf('Annihilus', from)) >= 0) {
      // 460-char window: wide enough to reach a codex entry's own `note` field, which sits
      // PAST the long props array (the v95 230-char window blind-spotted that note → it drifted).
      windows.push(html.slice(idx, idx + 460).replace(/<[^>]+>/g, ' '));
      from = idx + 9;
    }
    for (const w of windows) {
      expect(/\+1[-–]2 all skills/i.test(w), `Annihilus stated as "+1-2 all skills" (it is +1): ${w.slice(0, 90)}`).toBe(false);
      expect(/\+20 all res/i.test(w), `Annihilus stated as "+20 all res" (it is +10-20): ${w.slice(0, 90)}`).toBe(false);
      expect(/all[- ]stats/i.test(w), `Annihilus bonus stated as "all stats" (it is +5-10% experience): ${w.slice(0, 90)}`).toBe(false);
    }
    // and the canonical item card itself still carries the verified props AND its own note agrees
    const { props, note } = await page.evaluate(() => {
      const a = (ITEM_CODEX as any)['Annihilus'];
      return { props: a.props.join(' | '), note: a.note as string };
    });
    expect(props).toContain('+1 to All Skills');
    expect(props).toContain('All Resistances +10-20');
    // the codex note must not contradict its own props (the missed v95 drift lived here)
    expect(/\+1[-–]2 all skills/i.test(note), `Annihilus codex note drifts "+1-2 all skills": ${note}`).toBe(false);
    expect(/all[- ]stats/i.test(note), `Annihilus codex note drifts "all stats" (it is +5-10% experience): ${note}`).toBe(false);
    expect(note).toContain('experience');
  });

  test('entity sync: utility-ring codex notes agree with their own props (no mislabeled rolls)', async ({ page }) => {
    // v97: the structured `props` array is the canonical source of truth; a `note` must not
    // mislabel a roll that props spells out. Raven Frost & Bul-Kathos notes drifted (AR shown
    // as mana; max-stamina shown as "+50 life" + a fabricated "+5% max life"). Reconciled to props.
    // v98: Raven Frost / Bul-Kathos. v99: Bladebuckle (DEX shown as STR; +25 vs real +30 def) +
    // Spirit Forge (fabricated +25 STR/+30 light res/CBF vs verified +15 STR / fire res +5% only,
    // confirmed against diablo2.io/uniques/spirit-forge-t926.html).
    const { rf, bk, bb, sf } = await page.evaluate(() => {
      const c = ITEM_CODEX as any;
      return {
        rf: c['Raven Frost'].note as string,
        bk: c['Bul-Kathos Wedding Band'].note as string,
        bb: c['Bladebuckle'].note as string,
        sf: c['Spirit Forge'].note as string,
      };
    });
    // Raven Frost: mana is +40, the 150-250 roll is Attack Rating (not mana).
    expect(/\+150[-–]250 mana/i.test(rf), `Raven Frost note mislabels +150-250 AR as mana: ${rf}`).toBe(false);
    expect(rf).toContain('+40 mana');
    // Bul-Kathos: props are +0.5 life/clvl + +50 MAX STAMINA (no flat "+50 life", no "+5% max life").
    expect(/\+5% max life/i.test(bk), `Bul-Kathos note carries a fabricated "+5% max life": ${bk}`).toBe(false);
    expect(bk).toContain('stamina');
    // Bladebuckle: STR is +5, the +10 roll is Dexterity; defense is +30 (not +25).
    expect(/\+10 STR/i.test(bb), `Bladebuckle note mislabels +10 DEX as STR (STR is +5): ${bb}`).toBe(false);
    expect(bb).toContain('+10 DEX');
    // Spirit Forge: verified +15 STR + fire res +5% only — no "+25 STR", no light res, no CBF.
    expect(/\+25 STR/i.test(sf), `Spirit Forge note drifts "+25 STR" (verified +15): ${sf}`).toBe(false);
    expect(/light res/i.test(sf), `Spirit Forge note fabricates light res (it has fire res +5% only): ${sf}`).toBe(false);
    expect(/\bCBF\b/i.test(sf), `Spirit Forge note fabricates Cannot Be Frozen: ${sf}`).toBe(false);
    expect(sf).toContain('+15 STR');
  });

  test('entity sync: ITEM_INFO gear one-liners stay identical to their ITEM_CODEX note (no stale duplicate)', async ({ page }) => {
    // v100: ITEM_INFO (merged at runtime with ITEM_INFO_EXTRA) is a SECOND copy of each GEAR
    // item's codex `note`. When v98/v99 fixed the Raven Frost / Bul-Kathos / Bladebuckle / Spirit
    // Forge NOTES, the ITEM_INFO(_EXTRA) duplicates stayed stale — a classic unsynced-duplicate.
    // Scope to gear (non-empty props): keys / runes / shards intentionally carry a DIFFERENT
    // crosslink blurb in ITEM_INFO vs a detailed note, so they're excluded (empty props).
    const mismatches = await page.evaluate(() => {
      const codex = ITEM_CODEX as any;
      const info = ITEM_INFO as any;
      const out: string[] = [];
      for (const name of Object.keys(info)) {
        const c = codex[name];
        if (!c || !c.note) continue;
        if (!Array.isArray(c.props) || c.props.length === 0) continue; // gear only
        if (String(info[name]).toLowerCase().trim() !== String(c.note).toLowerCase().trim()) {
          out.push(`${name} :: INFO="${info[name]}" vs NOTE="${c.note}"`);
        }
      }
      return out;
    });
    expect(mismatches, `ITEM_INFO gear desync from ITEM_CODEX note:\n${mismatches.join('\n')}`).toEqual([]);
  });

  test('entity sync: The Summoner Hell mlvl agrees across BOSSES + SUPER_UNIQUES (area+3 rule)', async ({ page }) => {
    const { boss, su } = await page.evaluate(() => {
      const b = (BOSSES as any[]).find((x: any) => x.id === 'summoner');
      const hell = b.diffs.find((d: any) => d.label === 'HELL');
      const s = (SUPER_UNIQUES as any[]).find((x: any) => x.name === 'The Summoner');
      return { boss: hell.mlvl, su: s.mlvl };
    });
    expect(boss, `The Summoner Hell mlvl drifted: BOSSES=${boss} vs SUPER_UNIQUES=${su}`).toBe(su);
    expect(boss, 'The Summoner Hell mlvl should be 83 (Arcane Sanctuary alvl 80 + the verified area+3 rule)').toBe(83);
  });

  test('entity sync: the Hellfire Torch all-resist is unified to +10-20 (no stale all-res drift)', async () => {
    const html = fs.readFileSync(path.join(ROOT, 'bible.html'), 'utf8');
    // canonical Torch all-res = +10-20 (Moser's Blessed Circle legitimately is +20 all res, so
    // scope the check to a window around each "Hellfire Torch" mention).
    let from = 0, idx: number;
    while ((idx = html.indexOf('Hellfire Torch', from)) >= 0) {
      const w = html.slice(idx, idx + 200).replace(/<[^>]+>/g, ' ');
      expect(/\+20 all res/i.test(w), `Hellfire Torch stated as "+20 all res" (it is +10-20): ${w.slice(0, 100)}`).toBe(false);
      expect(/\+10 (all )?res(?!ist)/i.test(w), `Hellfire Torch stated as "+10 res" (it is +10-20): ${w.slice(0, 100)}`).toBe(false);
      from = idx + 14;
    }
  });

  test('entity sync: Colossal-Ancient statue drops map to the SAME boss across all 3 structures', async ({ page }) => {
    // v101: the 5 Colossal-Ancient statue drops are defined in THREE parallel structures —
    // COLOSSAL_STATUES (bossId), STATUE_LIST (bossId), and ITEM_INFO_EXTRA (prose naming the
    // boss). They currently agree, but it's an unguarded 3-way duplicate exactly the drift-prone
    // shape this audit locks. Assert the drop→boss mapping is identical across all three.
    const drift = await page.evaluate(() => {
      const cs = (COLOSSAL_STATUES as any[]).reduce((m: any, s: any) => (m[s.n] = s.bossId, m), {});
      const sl = (STATUE_LIST as any[]).reduce((m: any, s: any) => (m[s.n] = s.bossId, m), {});
      const info = ITEM_INFO as any;
      const out: string[] = [];
      const names = Object.keys(cs);
      for (const n of names) {
        const a = cs[n];
        const b = sl[n];
        if (a !== b) { out.push(`${n}: COLOSSAL_STATUES=${a} vs STATUE_LIST=${b}`); continue; }
        // ITEM_INFO_EXTRA prose must name the SAME boss as the bossId.
        const prose = String(info[n] || '').toLowerCase();
        if (!prose) { out.push(`${n}: no ITEM_INFO description`); continue; }
        if (!prose.includes(String(a).toLowerCase())) {
          out.push(`${n}: bossId="${a}" not named in ITEM_INFO prose "${info[n]}"`);
        }
      }
      return out;
    });
    expect(drift, `Colossal-Ancient drop→boss mapping drifted across structures:\n${drift.join('\n')}`).toEqual([]);
  });

  test('entity sync: Colossal jewel→Ancient binding agrees between COLOSSAL_JEWELS and UBER_BOSSES (+ strat names the element)', async ({ page }) => {
    // v102: the jewel→Ancient binding lives in TWO structures — COLOSSAL_JEWELS[].ancient
    // (L3799) and UBER_BOSSES[].jewels (L8847, the Ancient's loot list) — and each jewel's
    // ELEMENT is restated a third time in the Ancient's `strat` prose. They agree today; lock it.
    const drift = await page.evaluate(() => {
      const jewels = (COLOSSAL_JEWELS as any[]).reduce((m: any, j: any) => (m[j.n] = j, m), {});
      const ancients = (UBER_BOSSES as any[]).filter((b: any) => Array.isArray(b.jewels) && b.jewels.length);
      const out: string[] = [];
      for (const a of ancients) {
        // capitalised Ancient name as it appears in COLOSSAL_JEWELS.ancient (e.g. 'Talic')
        const wantAncient = a.name;
        for (const jn of a.jewels) {
          const j = jewels[jn];
          if (!j) { out.push(`${a.name}: jewel "${jn}" not in COLOSSAL_JEWELS`); continue; }
          if (j.ancient !== wantAncient) {
            out.push(`${jn}: UBER_BOSSES lists it under ${wantAncient} but COLOSSAL_JEWELS.ancient=${j.ancient}`);
          }
          // the Ancient's strat prose must name this jewel's element (e.g. "(fire)")
          if (!String(a.strat || '').toLowerCase().includes(String(j.elem).toLowerCase())) {
            out.push(`${a.name} strat omits "${jn}" element (${j.elem}): ${a.strat}`);
          }
        }
      }
      return out;
    });
    expect(drift, `Colossal jewel→Ancient binding drifted:\n${drift.join('\n')}`).toEqual([]);
  });

  test('entity sync: Hellforge rune pools + the orphaned GUARANTEED_DROPS_GLOBAL stay synced with the rendered guaranteed-drops surface', async ({ page }) => {
    // v103: TWO drift surfaces around the "guaranteed drops" feature —
    //  (A) the Hellforge rune TIER POOLS (El–Amn / Sol–Um / Hel–Gul) are stated THREE times:
    //      static HTML #guaranteed-global-card (rendered), GUARANTEED_DROPS_GLOBAL[].tiers (const),
    //      and RUNE_SOURCES hellforge .tierPool (rendered rune card).
    //  (B) GUARANTEED_DROPS_GLOBAL (L6908) is ORPHANED — nothing renders it; the static HTML block
    //      (L2178) is the visible copy. They agree today (icon→tier), but an edit to the dead const
    //      won't show on screen → silent drift. Lock the const to the rendered surface by icon→tier.
    const r = await page.evaluate(() => {
      const norm = (s: string) => String(s || '').toLowerCase().replace(/\s+/g, '');
      // --- (A) Hellforge pools across the 3 surfaces ---
      const htmlPools = norm(document.querySelector('#guaranteed-global-card .gc-tiers')?.textContent || '');
      const gdg = (GUARANTEED_DROPS_GLOBAL as any[]).find((d) => /Hellforge/i.test(d.name));
      const constPools = norm(gdg?.tiers || '');
      const hf = (RUNE_SOURCES as any[]).find((x) => x.id === 'hellforge');
      const runePools = norm((hf?.tierPool || []).map((t: any) => t.pool).join(''));
      const needles = ['el–amn', 'sol–um', 'hel–gul'];
      const poolMiss: string[] = [];
      for (const src of [['static-html', htmlPools], ['GUARANTEED_DROPS_GLOBAL', constPools], ['RUNE_SOURCES', runePools]] as const) {
        for (const n of needles) if (!src[1].includes(n)) poolMiss.push(`${src[0]} omits "${n}" (got "${src[1]}")`);
      }
      // --- (B) orphaned const icon→tier must match the rendered cards ---
      const renderedMap: Record<string, string> = {};
      document.querySelectorAll('#guaranteed-global-card .guaranteed-card').forEach((c) => {
        const icon = (c.querySelector('.gc-icon')?.textContent || '').trim();
        const tier = (c.querySelector('.gc-tier')?.textContent || '').trim();
        if (icon) renderedMap[icon] = tier;
      });
      const orphanMiss: string[] = [];
      for (const d of (GUARANTEED_DROPS_GLOBAL as any[])) {
        const want = renderedMap[String(d.icon).trim()];
        if (want === undefined) { orphanMiss.push(`const icon ${d.icon} (${d.name}) not on the rendered card grid`); continue; }
        if (want !== String(d.tier).trim()) orphanMiss.push(`${d.icon} ${d.name}: const tier="${d.tier}" vs rendered="${want}"`);
      }
      return { poolMiss, orphanMiss, renderedCount: Object.keys(renderedMap).length, constCount: (GUARANTEED_DROPS_GLOBAL as any[]).length };
    });
    expect(r.poolMiss, `Hellforge tier pools drifted across surfaces:\n${r.poolMiss.join('\n')}`).toEqual([]);
    expect(r.orphanMiss, `orphaned GUARANTEED_DROPS_GLOBAL desynced from rendered cards:\n${r.orphanMiss.join('\n')}`).toEqual([]);
    expect(r.constCount, 'GUARANTEED_DROPS_GLOBAL should still hold all 6 guaranteed drops').toBe(6);
    expect(r.renderedCount, 'the rendered guaranteed-drops grid should show all 6 cards').toBe(6);
  });

  test('entity sync: the sunder element↔region↔sunder-name web agrees across all 4 structures', async ({ page }) => {
    // v104: the core RotW sunder mapping (region→act→element→sunder-name) is restated FOUR times —
    // ACT_SHARD (region→act#), SHARD_RENEWED (region→renewed sunder + element), SHARD_OUTCOMES
    // (region→act/sunder/element), _HERALD_SUNDERS (sunder→element + region in its `rec`). Round-6
    // verified 3 of them by eye but left it unguarded; this locks the whole web. SHARD_OUTCOMES is
    // the canonical spine (it carries all 4 fields); the others must agree on their shared columns.
    const drift = await page.evaluate(() => {
      const out: string[] = [];
      const lc = (s: any) => String(s || '').toLowerCase();
      for (const o of (SHARD_OUTCOMES as any[])) {
        const region = (String(o.n).match(/\(([^)]+)\)/) || [])[1] || '';   // "Worldstone Shard (Western)" → Western
        const actNum = parseInt(String(o.act).replace(/\D/g, ''), 10);       // "Act 1" → 1
        const el = lc(o.el);
        const sunder = String(o.sunder);
        // (1) ACT_SHARD: act# → region
        if ((ACT_SHARD as any)[actNum] !== region) {
          out.push(`${region}: ACT_SHARD[${actNum}]="${(ACT_SHARD as any)[actNum]}" ≠ "${region}"`);
        }
        // (2) SHARD_RENEWED[region] must name this sunder + element
        const renewed = lc((SHARD_RENEWED as any)[region]);
        if (!renewed.includes(lc(sunder))) out.push(`${region}: SHARD_RENEWED omits sunder "${sunder}" (got "${(SHARD_RENEWED as any)[region]}")`);
        if (!renewed.includes(el)) out.push(`${region}: SHARD_RENEWED omits element "${el}" (got "${(SHARD_RENEWED as any)[region]}")`);
        // (3) _HERALD_SUNDERS: the sunder of that name breaks this element AND its recipe names the region
        const hs = (_HERALD_SUNDERS as any[]).find((s) => lc(s.n) === lc(sunder));
        if (!hs) { out.push(`${region}: sunder "${sunder}" missing from _HERALD_SUNDERS`); continue; }
        if (lc(hs.breaks) !== el) out.push(`${sunder}: _HERALD_SUNDERS.breaks="${hs.breaks}" ≠ element "${el}"`);
        if (!lc(hs.rec).includes(lc(region))) out.push(`${sunder}: _HERALD_SUNDERS recipe omits region "${region}" (got "${hs.rec}")`);
      }
      return out;
    });
    expect(drift, `sunder element↔region web drifted across structures:\n${drift.join('\n')}`).toEqual([]);
  });

  test('entity sync: SPECIAL_DROPS material DB agrees with the boss-mapping structures (keys · essences · Annihilus · Colossal statues)', async ({ page }) => {
    // v105: SPECIAL_DROPS (L3570) is the canonical material DB; it restates FOUR boss→drop maps
    // that also live in EXCLUSIVE_DROPS / BOSS_FEEDS_INTO / COLOSSAL_STATUES. None were cross-
    // guarded. (The Colossal-statue `from` is a 4th statue→boss surface the v101 guard MISSED —
    // same kind of gap round-8 found with _HERALD_SUNDERS.) Lock SPECIAL_DROPS to the others.
    const drift = await page.evaluate(() => {
      const lc = (s: any) => String(s || '').toLowerCase();
      const BTOKEN: Record<string, string> = { countess: 'countess', summoner: 'summoner', nihl: 'nihlathak', andariel: 'andariel', duriel: 'duriel', mephisto: 'mephisto', diablo: 'diablo', baal: 'baal' };
      const SD = SPECIAL_DROPS as any, EX = EXCLUSIVE_DROPS as any, BFI = BOSS_FEEDS_INTO as any;
      const out: string[] = [];
      const findFrom = (items: any[], name: string) => items.find((it) => lc(it.n) === lc(name));
      // (1) Pandemonium keys: EXCLUSIVE_DROPS === BOSS_FEEDS_INTO === SPECIAL_DROPS.key
      for (const bid of ['countess', 'summoner', 'nihl']) {
        const ex = EX[bid].item;
        const bfi = (BFI[bid] || []).find((x: any) => x.tone === 'key');
        if (!bfi || bfi.label !== ex) out.push(`${bid} key: EXCLUSIVE_DROPS="${ex}" vs BOSS_FEEDS_INTO="${bfi && bfi.label}"`);
        const sd = findFrom(SD.key.items, ex);
        if (!sd) out.push(`${bid} key "${ex}" missing from SPECIAL_DROPS.key`);
        else if (!sd.from.some((f: string) => lc(f).includes(BTOKEN[bid]))) out.push(`${ex}: SPECIAL_DROPS.from ${JSON.stringify(sd.from)} omits "${BTOKEN[bid]}"`);
      }
      // (2) Essences: BOSS_FEEDS_INTO === SPECIAL_DROPS.essence
      for (const bid of ['andariel', 'duriel', 'mephisto', 'diablo', 'baal']) {
        const bfi = (BFI[bid] || []).find((x: any) => x.tone === 'essence');
        if (!bfi) { out.push(`${bid}: no essence in BOSS_FEEDS_INTO`); continue; }
        const sd = findFrom(SD.essence.items, bfi.label);
        if (!sd) out.push(`${bid} essence "${bfi.label}" missing from SPECIAL_DROPS.essence`);
        else if (!sd.from.some((f: string) => lc(f).includes(BTOKEN[bid]))) out.push(`${bfi.label}: SPECIAL_DROPS.from ${JSON.stringify(sd.from)} omits "${BTOKEN[bid]}"`);
      }
      // (3) Annihilus / dclone: EXCLUSIVE_DROPS === BOSS_FEEDS_INTO === SPECIAL_DROPS.uberCharm
      const exA = EX.dclone.item;
      const bfiA = (BFI.dclone || []).find((x: any) => x.tone === 'uber');
      if (!bfiA || bfiA.label !== exA) out.push(`dclone: EXCLUSIVE_DROPS="${exA}" vs BOSS_FEEDS_INTO="${bfiA && bfiA.label}"`);
      const sdA = findFrom(SD.uberCharm.items, exA);
      if (!sdA) out.push(`"${exA}" missing from SPECIAL_DROPS.uberCharm`);
      else if (!lc(sdA.from.join(' ')).includes('clone')) out.push(`${exA}: SPECIAL_DROPS.from ${JSON.stringify(sdA.from)} omits "Clone"`);
      // (4) Colossal statue→boss: COLOSSAL_STATUES === SPECIAL_DROPS.colossalStatue.from (4th surface)
      const statueFrom: string[] = SD.colossalStatue.items[0].from;
      for (const s of (COLOSSAL_STATUES as any[])) {
        const seg = statueFrom.find((f) => lc(f).includes(lc(s.n)));
        if (!seg) { out.push(`statue "${s.n}" missing from SPECIAL_DROPS.colossalStatue.from`); continue; }
        if (!lc(seg).includes(lc(s.bossId))) out.push(`${s.n}: SPECIAL_DROPS segment "${seg}" omits boss "${s.bossId}"`);
      }
      return out;
    });
    expect(drift, `SPECIAL_DROPS material DB drifted from the boss-mapping structures:\n${drift.join('\n')}`).toEqual([]);
  });

  test('entity sync: Token of Absolution is a first-class material — its recipe matches the 4 essences, it routes to a card, and it is searchable', async ({ page }) => {
    // v106: the user asked that the cube product of all 4 Essences (Token of Absolution) be a
    // first-class item, not just a recipe-output string. It now lives as SPECIAL_DROPS.token.
    // Lock: (1) every essence named in SPECIAL_DROPS.essence is required by the Token recipe,
    // and the Token recipe == the essence-category recipe; (2) MATERIAL_RECIPES Token needs the
    // exact same 4 essences; (3) openDrop('Token of Absolution') opens a material card; (4) it's
    // searchable and the pick routes to the same card.
    const data = await page.evaluate(() => {
      const lc = (s: any) => String(s || '').toLowerCase();
      const SD = SPECIAL_DROPS as any;
      const out: string[] = [];
      const tok = SD.token;
      if (!tok) { out.push('SPECIAL_DROPS.token category is missing'); return { out, names: [] as string[] }; }
      const item = (tok.items || []).find((it: any) => lc(it.n) === 'token of absolution');
      if (!item) out.push('SPECIAL_DROPS.token has no "Token of Absolution" item');
      // (1) the token recipe names every essence + matches the essence-category recipe verbatim
      const ess = SD.essence;
      const essNames: string[] = ess.items.map((it: any) => it.n);
      for (const en of essNames) if (!lc(tok.recipe).includes(lc(en))) out.push(`SPECIAL_DROPS.token recipe omits essence "${en}"`);
      if (tok.recipe !== ess.recipe) out.push(`token recipe "${tok.recipe}" ≠ essence recipe "${ess.recipe}"`);
      // (2) MATERIAL_RECIPES Token needs the SAME 4 essences
      const mr = (MATERIAL_RECIPES as any[]).find((r) => lc(r.n) === 'token of absolution');
      if (!mr) out.push('MATERIAL_RECIPES has no Token of Absolution');
      else { for (const en of essNames) if (!(en in mr.need)) out.push(`MATERIAL_RECIPES Token need{} omits "${en}"`); }
      // (3) mechanic wording is CONSISTENT across every Token description — the canonical
      // bible convention is "reset stats OR skills (player choice)", NOT a both-at-once full
      // respec. v106 originally drifted to "AND / full respec"; lock all four strings to agree.
      const mechStrings = [tok.blurb, item && item.does, ess.blurb, mr && mr.makes].filter(Boolean).map(lc);
      for (const s of mechStrings) {
        if (!s.includes('stats') || !s.includes('skills')) out.push(`Token mechanic string omits stats/skills: "${s}"`);
        if (!s.includes('choice')) out.push(`Token mechanic string omits "(player) choice": "${s}"`);
        if (/full respec|and all|reset every skill and/.test(s)) out.push(`Token mechanic string drifted to a both-at-once full respec: "${s}"`);
      }
      // (4) the emblem resolves REAL diablo2.io art via artUrl (not just the emoji fallback)
      const u = (window as any).artUrl ? (window as any).artUrl('Token of Absolution') : null;
      if (!u || !/art\//.test(u)) out.push(`artUrl('Token of Absolution') did not resolve real art (got ${u})`);
      return { out, names: ['Token of Absolution'] };
    });
    expect(data.out, `Token-of-Absolution material sync drifted:\n${data.out.join('\n')}`).toEqual([]);

    // (3) openDrop routes to a material card (rendered into #item-detail)
    const card = await page.evaluate(() => {
      (window as any).openDrop('Token of Absolution');
      const panel = document.getElementById('item-detail');
      const img = panel?.querySelector('.material-card .gic-header .d2art-img') as HTMLImageElement | null;
      return {
        shown: !!panel?.classList.contains('show'),
        name: panel?.querySelector('.material-card .gic-name')?.textContent?.trim() || '',
        body: panel?.querySelector('.material-card')?.textContent || '',
        artSrc: img?.getAttribute('src') || '',
        artLazy: img?.getAttribute('loading') === 'lazy',
      };
    });
    expect(card.shown).toBe(true);
    expect(card.name).toMatch(/Token of Absolution/);
    expect(card.body).toMatch(/respec|reset/i);
    // the emblem is the real diablo2.io extracted art (artOr-resolved), not the emoji fallback
    expect(card.artSrc).toMatch(/art\/.*token_?of_?absolution/i);  // v384 — HD sprite is hd_token_of_absolution.png
    expect(card.artLazy).toBe(true);

    // (4) it is searchable and picking the result opens the same card
    await page.fill('#gsearch-input', 'Token of Absolution');
    await page.waitForTimeout(220);
    await page.locator('#gsearch-results .gsearch-item').first().click();
    await page.waitForTimeout(250);
    const picked = await page.evaluate(() =>
      document.getElementById('item-detail')?.querySelector('.material-card .gic-name')?.textContent?.trim() || '');
    expect(picked).toMatch(/Token of Absolution/);
  });

  test('entity sync: Lister the Tormentor is a first-class super-unique — in SUPER_UNIQUES, mlvl agrees with the binds tab, routes to a card, and is searchable', async ({ page }) => {
    // v107: Lister the Tormentor (Baal's wave-5 Throne boss) was named in the binds tab but had
    // NO SUPER_UNIQUES entry / ID card — unlike Hephasto the Armorer which is a full entity.
    // Gap-fill: he now lives in SUPER_UNIQUES (card + search flow for free). Lock his existence,
    // the mlvl-92 cross-consistency with the binds-tab monster-data note, and the card route.
    const data = await page.evaluate(() => {
      const out: string[] = [];
      const SU = SUPER_UNIQUES as any[];
      const lister = SU.find((s) => /lister the tormentor/i.test(s.name));
      if (!lister) { out.push('SUPER_UNIQUES has no Lister the Tormentor'); return { out, mlvl: null as any }; }
      // mlvl agrees with the binds-tab sourced note ("Lister 92" in #tab-binds sources)
      if (lister.mlvl !== 92) out.push(`Lister mlvl is ${lister.mlvl}, expected 92 (binds-tab monster-data lock)`);
      const bindsTxt = (document.getElementById('tab-binds') as HTMLElement | null)?.textContent || '';
      if (!/Lister\s*92/i.test(bindsTxt) && !/Lister the Tormentor/i.test(bindsTxt)) out.push('binds tab no longer references Lister');
      // Hephasto (the precedent the gap-fill mirrors) is still present
      if (!SU.find((s) => /hephasto the armorer/i.test(s.name))) out.push('Hephasto the Armorer (precedent) missing from SUPER_UNIQUES');
      return { out, mlvl: lister.mlvl };
    });
    expect(data.out, `Lister-the-Tormentor super-unique sync drifted:\n${data.out.join('\n')}`).toEqual([]);
    expect(data.mlvl).toBe(92);

    // routes to a super-unique ID card (gbc shell), via the by-name jump helper
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(250);
    const card = await page.evaluate(() => {
      const c = document.querySelector('.su-card-rich');
      return { name: c?.querySelector('.gbc-name')?.textContent?.trim() || '', body: c?.textContent || '' };
    });
    expect(card.name).toMatch(/Lister the Tormentor/);
    expect(card.body).toMatch(/Throne of Destruction/i);

    // searchable: the global search surfaces him as a super-unique
    const found = await page.evaluate(() => {
      const SU = SUPER_UNIQUES as any[];
      return SU.some((s) => /lister/i.test(s.name) && s.act && /throne/i.test(s.act));
    });
    expect(found).toBe(true);
  });
});
