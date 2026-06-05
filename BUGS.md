# v21_kai → v21_kai_fixed bug tracker

## Strategy
- Side branch: `/Users/konyo/Downloads/konyo_d2r_bible_v21_kai.html`
- Test bench: `/Users/konyo/d2r_bible_tests/bible.html` (copy)
- TDD: write Playwright test → confirm fail → patch → confirm pass
- Vanilla HTML/CSS/JS preserved (no React migration)

## P0 — render crashes
- [x] BUG-001 `renderBossCards()` line 1623: `r50.toLocaleString()` crashes when `runsFor()` returns null. Kills 11 boss cards + cascades to TZ/Runes/RotW.

## P1 — missing universal boss detail page (user explicit ask)
- [x] BUG-010 Universal boss detail panel — overlay, 6-diff grid, top-12 drops, esc/× close ✓ 9/9 tests
- [x] BUG-011 Boss-nav chip click → smooth-scroll + flash header + flash chip ✓
- [x] BUG-012 Boss-card header clickable → opens universal detail ✓
- [x] BUG-013 TZ-zone card click → boss detail (11 zone→boss mappings) ✓
- [x] BUG-014 Cmd/Ctrl+click on calc source-chip → boss detail (plain click preserved) ✓

## P1 — subtab rendering (CASCADE CLEARED by BUG-001 fix)
- [x] BUG-020 TZ tab: zones rendered count (8+ zones ✓)
- [x] BUG-021 Runes tab: rune table rendered (10+ rows ✓)
- [x] BUG-022 RotW tab: shards/statues/essences/sunders/sets all render (7 sets, 5 statues ✓)
- [x] BUG-023 Ancients tab: full mechanics card (Talic/Korlic/Madawc + 4 stats) ✓
- [x] BUG-024 Reference tab: TC + qlvl explainer + MF math ✓

## P2 — UX/aesthetics
- [ ] BUG-030 Boss-card visual consistency across all 11 cards
- [ ] BUG-031 Section header typography (uppercase mono, gold divider)
- [ ] BUG-032 Color contrast on blocked cells (orange qlvl, pink TC)
- [ ] BUG-033 Hover/focus states on every interactive element
- [ ] BUG-034 Mobile responsive layout
- [ ] BUG-035 Compare-difficulty table styling

## P2 — interaction tests (each click verified)
- [ ] BUG-040 Click any item tile → calc detail renders
- [ ] BUG-041 Click any source chip → bosses tab + correct boss + correct diff
- [ ] BUG-042 Star/unstar item persists to localStorage
- [ ] BUG-043 Mark owned/unowned persists to localStorage
- [ ] BUG-044 MF slider live-updates all cells
- [ ] BUG-045 Player slider live-updates
- [ ] BUG-046 Search counter updates on filter
- [ ] BUG-047 Filter pills (all/grail/uber/tc87/etc) work
- [ ] BUG-048 Sort by column (boss card tables)
- [ ] BUG-049 Keyboard shortcuts (/, ?, 1-7, Esc, B)
- [ ] BUG-050 Statue tracker click toggles

## P2 — data integrity
- [ ] BUG-060 All 312 items present in calc
- [ ] BUG-061 Verified anchors (🔒) intact
- [ ] BUG-062 Nagelring searchable
- [ ] BUG-063 Mephisto TC78 cap blocks Tyrael's etc.
- [ ] BUG-064 Pindle mlvl 86 blocks qlvl 87 items

## P3 — polish
- [ ] BUG-100 Hero card 5 picks update on MF change
- [ ] BUG-101 Tonight's Mission appears when wishlist > 0
- [ ] BUG-102 Grail progress dial animates correctly
- [ ] BUG-103 Drop simulator runs N trials
- [ ] BUG-104 Set tracker pieces check off
- [ ] BUG-105 Cube recipes render
- [ ] BUG-106 Help modal (?) opens/closes
- [ ] BUG-107 Reset data button confirms + clears localStorage

## P2 — UX/aesthetics ✅ ALL SHIPPED
- [x] BUG-030 Boss-card visual consistency (11 cards: header, emoji, name, tier-tag, body) ✓
- [x] BUG-031 Section header typography (uppercase + gold rgb dominant) ✓
- [x] BUG-032 Color contrast on blocked cells ✓
- [x] BUG-033 Hover/focus states present (boss-header.clickable:hover CSS rule) ✓
- [x] BUG-034 Mobile responsive layout (375px, no h-overflow) ✓
- [x] BUG-035 Compare-difficulty grid renders per boss ✓ (+035b detail card mobile width)

## P2 — interactions ✅ ALL SHIPPED
- [x] BUG-040 item tile → calc detail
- [x] BUG-041 source-chip → bosses tab
- [x] BUG-042 star persists `d2r_wishlist`
- [x] BUG-043 owned persists `d2r_owned`
- [x] BUG-044 MF slider live update
- [x] BUG-045 Players slider live update
- [x] BUG-046 search counter filters
- [x] BUG-047 filter pill "grail" filters
- [x] BUG-048 sort column toggle direction class
- [x] BUG-049 kbd "/" focuses search
- [x] BUG-049b Esc clears active item
- [x] BUG-050 statue tracker toggles

## P2 — data integrity ✅ ALL SHIPPED
- [x] BUG-060 312 items in calc grid ✓
- [x] BUG-061 verified anchors in Ref tab ✓
- [x] BUG-062 Nagelring searchable ✓
- [x] BUG-063 Mephisto Hell TC≤78 ✓
- [x] BUG-064 Pindle Hell mlvl 86 ✓

## P3 — polish (5 of 8)
- [x] BUG-100 hero card renders
- [ ] BUG-101 Tonight's Mission visibility when wishlist > 0
- [x] BUG-102 grail progress dial exists
- [ ] BUG-103 drop simulator runs N trials
- [x] BUG-104 set tracker ≥7 sets
- [x] BUG-105 cube recipes in rotw/ref/runes
- [ ] BUG-106 help (?) modal (feature absent)
- [x] BUG-107 reset button attached

## Discovery sweep 1 ✅ ALL SHIPPED (BUG-110..124)
- [x] BUG-110 rune table ≥10 rows
- [x] BUG-111 every boss has 6 diff columns
- [x] BUG-112 every boss has ≥1 drop row
- [x] BUG-113 search clear restores grid
- [x] BUG-114 set-piece toggle adds class
- [x] BUG-115 MF math 54.5% @ MF300
- [x] BUG-116 reset confirms (no auto-clear)
- [x] BUG-117 hero updates with MF
- [x] BUG-118 filter "all" reset
- [x] BUG-119 sort persists across re-renders
- [x] BUG-120 all 11 detail open w/o error
- [x] BUG-121 11 boss-nav chips
- [x] BUG-122 TZ ≥10 zones
- [x] BUG-123 RotW ≥5 statues
- [x] BUG-124 detail re-opens for different boss

## Status — 2026-05-26
**56/150 bugs shipped. 73 tests passing, 1 skipped, 0 failing.**
Snapshot: `/Users/konyo/Downloads/konyo_d2r_bible_v21_kai_fixed.html` (614 KB)
Next session: BUG-125+ visual regression, feature audits for 101/103/106.

## Status — 2026-05-26 17:10 — ROUTE-AUDIT lane (second version)
Konyo split work: Claude Desktop = visuals/features (v23/v24), Claude Code = routes/backend/symmetry (no visuals).
- Branch: `/Users/konyo/d2r_bible_tests/bible_routes.html` (fork of v21_kai_fixed)
- Ship: `/Users/konyo/Downloads/konyo_d2r_bible_v23_routes.html` (614 KB)
- New suite: `tests/route_audit_v23r.spec.ts` — **24/24 GREEN**
  - 7/7 sub-tabs render content (bosses, calc, tz, runes, rotw, ancients, ref)
  - 11 boss-nav chips + 11 detail openings + Esc close
  - 11 boss-cards × 6 diffs × ≥1 drop row symmetry
  - TZ→boss routing, calc tile→detail, source-chip plain & Cmd+click routing
  - MF/Players sliders no errors; overlay switch ≠ stack
- Total project tests: **97 passing** (73 original + 24 route-audit), 1 skipped, 0 failing

---

# Regression log (post-ship breakages caught by CI)

> **Companion docs (cross-referenced):** `GAME_RULES.md` (durable RoW game-truth +
> drop-odds provenance) · `BUILD_LOG.md` (dated ship/decision log + key invariants).
> Append every post-ship breakage here as `REG-NNN`.

Format: what broke · how it was caught · root cause · fix · prevention.

## REG-001 — 2026-06-05 · artOr() lazy-load strip → calc-grid load storm
- **Symptom**: Routine I (Playwright) shard 3/3 failed — 3 tests red:
  v71_d2art `calc grid tiles` + `boss-nav chips` (assert `loading="lazy"`),
  v74_material_search `Colossal Ancient Statues header` (assert `loading="lazy"`).
- **Caught by**: scheduled CI run (push commit `4b80ba5`, headSha) — NOT a local run.
- **Root cause**: commit `4b80ba5` ("eager-load the 8 boss-card portraits" for a
  Safari rendering fix) dropped `loading="lazy"` from the **central `artOr()` helper**
  and the statue `<h2>` header — far wider scope than "8 portraits". That eager-loaded
  the hundreds of calc-grid item images (a load-time storm) and broke the tested
  lazy invariant in 3 places. **The commit was pushed to `main` without running the
  full Playwright suite** (the BULLETPROOF mandate) — that is the real gap.
- **Fix**: commit `74ae7f3` — restored `loading="lazy"` in `artOr()` + the statue
  head. Kept the 7 *targeted* static eager-loads Desktop added (Countess card header
  + 5 event-card logos): no test asserts `loading` on them, and those are the actual
  in-hidden-tab portraits Safari failed to render. 391 passed / 1 skipped local, green.
- **Prevention**: (1) ALWAYS run `npx playwright test` to green BEFORE pushing — esp.
  any edit to a *central* helper (`artOr`, `openDrop`, `switchTab`), whose blast radius
  is site-wide. (2) Editing a shared template means re-running the whole suite, not just
  the spec you think you touched. (3) CI (Routine I) is the backstop, not the gate —
  treat a red scheduled run as a real regression first, re-run the failing spec in
  isolation to rule out suite-tail fatigue (this one reproduced in isolation = real).
