# Handoff to Claude Desktop — v33 verifier findings

Two unrelated bugs co-existing in the current v33 build. Mechanical evidence below for both.

---

## BUG A · `renderWishlistHuntPath` paste-bug — STILL present in v33

Same as v32. The function declaration is still inside the `<style>` block. Browser parses it as CSS text and discards. Evidence:

```
typeof window.renderWishlistHuntPath  →  "undefined"
```

- `#wishlist-hunt-path` div exists but `child_count=0` (empty card)
- MF slider + Players slider both fire `ReferenceError: renderWishlistHuntPath is not defined`
- Route audit: 22/24 — same two slider tests fail as v32

**Fix unchanged from v32 handoff:** Cut the v32 JS payload (function definition, `window.X = X` alias, all onclick template strings) out of the `<style>` block. Paste between `<script>` open (line ~1614) and the first call site.

**1-line verifier after paste:**
```js
typeof window.renderWishlistHuntPath  // must be "function"
```

---

## BUG B · Boss-aware picks ranking — too loose, produces near-identical sets across bosses

Good news: the picks card IS boss-aware. Title morphs correctly ("TOP GRAIL DROPS FROM 💰 TRAVINCAL COUNCIL"), per-boss odds recompute (e.g. Andariel's Visage = 1:997 @ Travincal vs 1:491 @ Mephisto). The filter is firing.

Bad news: the **item set is nearly identical across 6+ endgame bosses**. Overlap matrix from 11-boss sweep:

| Pair | Overlap |
|---|---|
| diablo ↔ baal ↔ nihl ↔ pit | **100%** (15/15 identical items) |
| pindle ↔ cows | **100%** |
| countess ↔ travincal | **100%** |
| andariel ↔ mephisto | 93% |
| diablo ↔ pindle ↔ cows | 93% |

That's the bug Konyo is feeling. Clicking Travincal vs Diablo vs Baal shows visually-identical lists.

### Why it happens

The current filter shipped in v33 reads as: *"include any grail item this boss CAN drop, rank by global fastest source."*

For endgame TC85 bosses (Diablo, Baal, Pindle, Nihlathak, Pit, Cows), the drop universe is huge and largely overlapping — they all qualify for the same Stormshield, Templar's Might, Veil of Steel, Sandstorm Trek, Dracul's Grasp pool. The "rank by speed" tiebreaker pulls in the same 15 every time.

Additional symptom: when Travincal is active, the source column on each pick still says **"HELL TZ"** generic, not **"Travincal Council"**. So the rank is computed from a TZ pool, then displayed with a label that doesn't reflect the active boss.

### Recommended algorithm (any of these fixes the symptom)

**Option 1 — Tighten the filter (preferred):**
- Rank picks by `(this boss's odds) / (best alternative source's odds)` — items where THIS boss is the fastest source bubble to the top.
- Items the boss can technically drop but where another source is dramatically faster fall off the list.
- Boss-specialty items (Mephisto → Shako, Mephisto → Ber rune, Andariel → Wizardspike, Pindle → Templar's Might, Travincal → Dracul's Grasp) naturally surface.

**Option 2 — Hard-anchor the source label:**
- When a boss is active, ALL displayed picks must show that boss as the source, not "HELL TZ".
- If an item's fastest source is a different boss, EITHER (a) exclude it OR (b) show it with a "but X is faster" footnote.

**Option 3 — Lift item count from 15 → 20 AND apply Option 1:**
- Konyo asked for more than 5 picks (already 15, good), but a tighter filter on 20 slots gives more visible diversity per boss.

### Spec-by-example

Travincal Council's top picks should heavily feature: **Dracul's Grasp, Stormshield, Sandstorm Trek, Veil of Steel, Templar's Might (when Lower Kurast pool active), Shadowdancer (when shrine TZ active)**. Not: Andariel's Visage (Hell Andariel is faster) or Harlequin Crest (Hell Mephisto is faster).

Mephisto's top picks should heavily feature: **Harlequin Crest (Shako), Duriel's Shell, Homunculus, The Ward, Wizardspike**. Not: Templar's Might (Hell Pindleskin faster) or Sandstorm Trek (Hell Travincal faster).

If after the fix, `overlap(travincal, mephisto) < 60%` and `overlap(diablo, baal) < 90%`, the algorithm is healthy.

---

## Verifier protocol when v34 ships

```bash
cp /Users/konyo/Downloads/konyo_d2r_bible_v34.html /Users/konyo/d2r_bible_tests/bible_routes.html
cd /Users/konyo/d2r_bible_tests
npx playwright test tests/route_audit_v23r.spec.ts --reporter=line     # 24/24 (proves paste-bug fixed)
node v33_picks_overlap_check.js                                         # picks set diff per boss
```

I'll have the picks-overlap probe ready to run as a single command.

---

## Lane fence — what I did NOT touch

- `bible_routes.html` — read-only diagnostics only
- `Downloads/konyo_d2r_bible_v33.html` — not opened for write
- Visual styling, picks algorithm, hero card layout — entirely Desktop's lane

What I produced: diagnostic specs (read-only), this brief, an overlap-matrix probe (to be staged).
