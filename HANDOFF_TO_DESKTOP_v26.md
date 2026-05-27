# Handoff to Claude Desktop — v25 verifier FAILED, second pass needed

Ran the route-audit verifier on `konyo_d2r_bible_v25.html`. Result: **14/24 FAIL — identical to v24.** Neither regression was addressed by the alias/parallel-ID work.

CSS aliases and parallel IDs only help if the DOM gets rendered. The DOM is empty because `renderBossCards()` crashes before producing a single card.

## Hard evidence from in-page probe (verbatim)

```
pageerror: Cannot read properties of null (reading 'toLocaleString')
         @ bible_routes.html:2420:214

has_openBossDetail:        "undefined"
has_showBossPanel:         "undefined"
has_closeBossDetail:       "undefined"
boss_cards_count:           0     ← .boss-card selector
boss_cards_alias_count:     0     ← .gbc-card OR .boss-card selector (alias also empty)
item_grid_count:            0
runes_rows:                 0
statue_count:               0
set_piece_count:            0
tz_card_count:             10     ← static, fine
tz_with_data_boss:          0     ← STILL no data-boss-id
first_boss_header_class:    "none"  ← no boss header element exists at all
first_boss_header_onclick:  "none"
overlay_exists:            false   ← #boss-detail-overlay removed
overlay_panel_exists:       true   ← #boss-detail-panel div exists but no JS opens it
```

## Why the aliases don't help

You wrote: *"alias class names, parallel ID, defensive Esc, simplified TZ click."*

- **Class aliases (`.gbc-card`)**: `.gbc-card OR .boss-card` selector still returns 0 elements. The aliases are CSS-level, but no DOM is produced because of the crash.
- **Parallel ID (`#boss-detail-panel`)**: exists as an empty div. No JavaScript function opens it — neither `openBossDetail`, `showBossPanel`, nor `closeBossDetail` exist on `window`.
- **Defensive Esc**: cannot close what never opened.
- **Simplified TZ click**: TZ cards no longer expose `data-boss-id` at all (`tz_with_data_boss=0`). Whatever simplification you made dropped the routing attribute the audit verifies.

## The two regressions are still both present

### REG-1 · BUG-001 null crash — still active

The unguarded `r50.toLocaleString()` block just moved from line 2359 (v24) to line 2420 (v25). Same throw, same cascade, same 5 empty containers. Until this is guarded, **no dynamic rendering happens** — every CSS alias, every new feature, every visual addition you make is invisible because the cascade kills the renders that produce the DOM.

**Mandatory fix at line 2420** (same guard pattern used at line 1623 in v21_kai_fixed):
```js
if (bestRow && r50 !== null && hrs !== null) {
  quickTake = `<div class="quick-take">⚡ <strong>Quick take @ ${mf}% MF:</strong> ... ${r50.toLocaleString()} runs ... ${fmtHours(hrs)} ...</div>`;
}
```

Recommend: grep for every `.toLocaleString()` and `fmtHours(` call inside `renderBossCards` and gate each one on a non-null check. There may be a third site.

### REG-2 · routing global — still missing

After v25, none of these exist:
- `window.openBossDetail` ❌
- `window.showBossPanel` ❌
- `window.closeBossDetail` ❌

A parallel ID without a function is a dead end. Pick exactly one of these:

**Pattern A — façade restoring the original contract** (minimum delta, no callsite edits needed):
```js
window.openBossDetail = function(bossId, focusDiff) {
  // call whatever internal function v25 uses to populate #boss-detail-panel
  // e.g. _showInlineBossPanel(bossId, focusDiff);
};
window.closeBossDetail = function() { /* hide #boss-detail-panel */ };
```

**Pattern B — new contract, fully rewired**: rename to `openBossPanel` everywhere, but then update all 4 callsites yourself:
1. `renderBossNav` chip onclick
2. `renderBossCards` header onclick
3. `renderTzZones` zone-card onclick (and re-add `data-boss-id="${bossId}"`)
4. Document-level capture-phase Cmd/Ctrl+source-chip handler

Either pattern works. Mixing them (parallel ID without parallel function) is what we have now and it routes nothing.

## What you can verify locally before claiming a ship

Drop this into the v25/v26 browser console:
```js
({
  global: typeof window.openBossDetail,
  cards: document.querySelectorAll('#boss-cards .boss-card, #boss-cards .gbc-card').length,
  tzRouted: document.querySelectorAll('.tz-zone-card[data-boss-id]').length,
  errors: 'check devtools console for r50.toLocaleString'
})
```

All four must be: `function`, `11`, `≥1`, `clean`. If any of those is off, the route audit will fail.

## Lane fence still respected by CC

I am not patching v25. When v26 ships, swap and re-run:
```bash
cp /Users/konyo/Downloads/konyo_d2r_bible_v26.html /Users/konyo/d2r_bible_tests/bible_routes.html
cd /Users/konyo/d2r_bible_tests
npx playwright test tests/route_audit_v23r.spec.ts --reporter=line
```

Target: 24/24 GREEN.
