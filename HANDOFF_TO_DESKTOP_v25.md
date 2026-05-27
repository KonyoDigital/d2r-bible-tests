# Handoff to Claude Desktop — v24 → v25 route regressions

Route-audit ran on `konyo_d2r_bible_v24.html` against the green baseline `konyo_d2r_bible_v23_routes.html`. **14/24 probes FAIL.** Two clean root causes:

## REG-1 · BUG-001 reintroduced (Quick-take block, line 2359)

You added a `Quick take @ MF` block inside `renderBossCards` that uses `r50.toLocaleString()` and `fmtHours(hrs)` without the null-guard the older callsite (~line 1623) already has. `runsFor()` returns null for unreachable/blocked drops, so the first boss-card to hit that branch throws — the throw kills `renderBossCards()` mid-`.map()` and cascades to:

- `#boss-cards` count = 0
- `#item-grid` count = 0 (calc tiles)
- `#tab-runes tbody tr` count = 0
- `#statue-tracker > div` count = 0
- `.set-piece` count = 0

Pageerror: `TypeError: Cannot read properties of null (reading 'toLocaleString') at line 2359:214`

**Fix shape** (same guard used at line 1623):
```js
if (bestRow && r50 !== null && hrs !== null) {
  quickTake = `<div class="quick-take">⚡ <strong>Quick take @ ${mf}% MF:</strong> ... ${r50.toLocaleString()} runs ... ${fmtHours(hrs)} ...</div>`;
}
```

## REG-2 · `window.openBossDetail` global removed

`typeof window.openBossDetail === "undefined"` in v24. You replaced the universal overlay (`#boss-detail-overlay`) with an inline `#boss-detail-panel`, but the four callsites still call `openBossDetail(bossId)`:

1. `renderBossNav` chip template → `onclick="openBossDetail('${id}')"`
2. `renderBossCards` header template → `<div class="boss-header clickable" onclick="openBossDetail('${boss.id}')">`
3. `renderTzZones` zone-card template → `onclick="openBossDetail('${bossId}')"` (also lost `data-boss-id` attribute)
4. Document-level capture-phase click handler → Cmd/Ctrl + `.source-chip` → `openBossDetail(bossId)`

**Two clean fix options:**

**Option A — keep the new inline panel, restore the global as a façade:**
```js
window.openBossDetail = function(bossId, focusDiff) {
  // delegate to whatever the new inline-panel function is named
  showBossPanel(bossId, focusDiff);
};
```

**Option B — rewire all four callsites** to call the new function name directly. Make sure you also re-add `data-boss-id="${bossId}"` on TZ-zone cards or the audit can't verify zone→boss mapping survived.

## Untouched (these still pass)

- 7/7 sub-tab switch (`switchTab` intact)
- 11/11 boss-nav chip count
- ancients tab (Talic/Korlic/Madawc static)
- ref tab (TC/qlvl/MF/cube tokens)

## Verifier (run after v25 ships)

```bash
cp /Users/konyo/Downloads/konyo_d2r_bible_v25.html /Users/konyo/d2r_bible_tests/bible_routes.html
cd /Users/konyo/d2r_bible_tests
npx playwright test tests/route_audit_v23r.spec.ts --reporter=line
```

Target: **24/24 GREEN** (matches the v23_routes baseline).

## Lane fence reminder

Claude Code is staying on routes/backend/symmetry. No visual edits from this side. Both regressions above are inside your visual/feature lane — restore the four routing contracts and v24's golden-card/picks work is fully compatible with the route-audit suite.
