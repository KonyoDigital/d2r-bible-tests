# SCOPE → Items tab (affix min-max per item) — data-source blocker, NO fabrication

**From:** CC (terminal) · **Date:** 2026-05-30
**Status:** NOT built — deliberately blocked on authoritative data (Konyo's hard "NO FABRICATION" rule).

## What Konyo asked for (task #6, the explicit "last last last" item)
A tab/subtab listing the 312 items with **what each does** + **min→max stat ranges per
affix**, fully in-sync with the existing routing (click an item anywhere → opens it here,
and from here → back into the calc / boss detail). Est. +3,000–5,000 cells.

## Why it is NOT built tonight (honest blocker)
The bible's `BOSSES` data carries, per item: **name, tier (uber/grail/normal), TC, qlvl,
and per-difficulty drop odds** — and nothing about the item's *properties*. There is **no
per-unique/per-set affix dataset anywhere on disk** (checked: bible.html has only narrative
affix mentions; `~/Downloads/konyo_d2r_special_items.html` is the RotW shards/statues/essence
reference, already in the RotW tab — not unique-item stats).

Unique/set affix ranges (e.g. Shako = +2 all skills, +1.5 life & mana per clvl, 50% better
MF; Nagelring = 15–30% MF, 50–75% AR, …) are *fixed, well-documented* data — but generating
312 items' exact min/max from model memory would be **fabrication**, which Konyo forbade in
caps multiple times. Subtle errors (exact % bounds, per-level coefficients, set-bonus
breakpoints) are exactly the kind of thing that must come from a source file, not memory.

## The correct way to build it (when a verified source is available)
1. **Source of truth** — one of:
   - The game's data tables: `UniqueItems.txt`, `SetItems.txt`, `Sets.txt`, `Properties.txt`
     (+ `ItemStatCost.txt` for stat display formatting). These give exact `min`/`max`/`param`
     per `prop1..prop12`. This is the canonical, non-fabricated source.
   - OR a vetted export (Arreat Summit / d2.io / maxroll item DB) cross-checked against the
     above. Cross-check ≥2 sources per item before locking, same discipline as the routing facts.
2. **Schema** — extend the item registry (do NOT mutate `BOSSES`; derive a parallel
   `ITEM_STATS` keyed by item name to keep the 312-item / drop-cell invariants untouched):
   ```
   ITEM_STATS["Harlequin Crest"] = {
     type: "unique", base: "Shako", ilvl: 69,
     props: [ {stat:"+{n} to All Skills", min:2, max:2},
              {stat:"+{n}% Better Chance of Magic Items", min:50, max:50},
              {stat:"Damage Reduced by {n}%", min:10, max:10},
              {stat:"+{a}-{b} to Life (Based on Character Level)", perLevel:1.5},
              ... ] }
   ```
3. **Render** — new tab `data-tab="items"` (preserve existing tab ids; add to the 8→9 tab
   bar + `switchTab`). Each item row: name (tier-colored) · base · "what it does" stat list
   with min–max. Reuse `tierPill`, the editorial type system.
4. **Routing (must stay in sync — this is the part Konyo cares most about)**:
   - `navigateToItem(name)` already drives calc; add an `openItemStats(name)` that switches
     to the items tab + scrolls/flashes the row (mirror `jumpToBossItem`'s highlight).
   - Every existing item entry point (calc tile, boss drop row, source-chip, command palette,
     top-drops row) gets an optional "📖 stats" affordance → `openItemStats`.
   - From an item-stats row → links back to "drops from" boss chips (the inverse of the drop
     table) using the existing `ITEM_REGISTRY` source map.
5. **Tests (lock it like the rest)**: extend `routing_and_data_integrity.spec.ts` —
   - every `ITEM_STATS` key is a real item in `ITEMS` (no phantom stat entries),
   - every item with stats renders a row, click → opens correct row (routing fidelity),
   - min ≤ max for every numeric prop, perLevel props have a coefficient,
   - the 312-item / drop-cell / 19,458-cell invariants are UNCHANGED (parallel data only).

## Acceptance
Build only when the source file is in hand. Same no-fabrication bar as the drop odds:
no value ships unless it traces to `UniqueItems.txt`/`SetItems.txt` (or a 2-source cross-check).
