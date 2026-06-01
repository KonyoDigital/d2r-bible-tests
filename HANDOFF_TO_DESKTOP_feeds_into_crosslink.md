# HANDOFF → Desktop Claude — Feeds-Into Cross-Link layer shipped, visual polish + mission crystallization pending

**From:** CC (terminal) · **Date:** 2026-06-01
**Commit:** `03e8a9b` (pushed to origin/main) · **bible.html md5:** `46038d6ad0fe1272d5744c48281ada23`
➜ **Re-read bible.html before touching** — it changed under you. Data (`BOSSES`) untouched; L-integrity baseline still 312 items / 13 bosses / all drop probes identical.

## The mission (Konyo's ask, now functionally complete)
> "the flayer has drops like keys and special items i need for certain events (uber tristram, diablo clone, ancient colosseum)... keys should be top priority... organized accordingly to what each boss/area gives material-wise... clickable and routed... a defined detailed boss ID card."
> Scope = **Everything — all zones clickable + full feeds-into on every card.**
> Grail = **cross-link only, NOT in the grail count** — a dedicated keys/shards/essences reference section right under the grail.

## What CC shipped (functional — done, tested, committed)
New `tests/v45_feeds_into_crosslink.spec.ts` (6/6 green). Full focused regression set 39/39 green. 0 JS errors.

1. **"🔗 what this farm feeds into" strip on every boss detail card** (golden card, renders into `#boss-detail-panel` via `renderBossDetailCard`, bible.html ~L4471). Driven by `BOSS_FEEDS_INTO` (~L2784) derived from canonical `SPECIAL_DROPS`:
   - Countess→Key of Terror, Summoner→Key of Hate, Nihl→Key of Destruction (Uber Tristram).
   - Andariel/Duriel→Essence of Suffering, Mephisto→Hatred, Diablo→Terror, Baal→Destruction (Token of Absolution).
   - Terrorized Hell act bosses → Colossal Ancient Statue (Colossal Summit). dclone→Annihilus.
2. **Every TZ zone card is now clickable** (`renderTzZones` template ~L5705). Roster boss spawns there → `openBossDetail`; super-unique-only zone (Flayer, Crystalline, Tristram, Burial Grounds, Spider Forest) → `toggleZoneDetail(zi)` opens an **inline drop-detail box** (`#tz-zone-detail-<zi>`, with its own feeds-into strip).
3. **Keys/Shards/Essences reference section under the grail** — `#event-ref` div (HTML anchor ~L1683), populated by `renderEventRef()` (~L2832). Three `.er-block`s: keys→Uber Tristram, Worldstone Shards→Sunder Charms, essences→Token of Absolution. Explicitly labeled "not counted in the grail."
4. **Routed Arcane Sanctuary → Summoner** (TZ_BOSS_MAP ~L4677).
5. **data fixes:** corrected 3 scrambled key→boss tooltip attributions to canonical (Terror→Countess, Hate→Summoner, Destruction→Nihlathak) + a stale "Summoner NOT in our 11-boss list" note.
6. **Tier-title rename** (Konyo-requested, `PLAYER_TIERS` ~L4774): `THE TIGHT-FISTED → THE HOARDERS`, `PRIME EVILS → THE PRIME EVILS`. Pure display text, no data/baseline impact.

## Visual polish still owed (your lane) — "finish up visually + crystallize"
CC gave everything **functional CSS using existing tokens** (block injected after `/* TZ Hot Zones */`, ~L339-360). It's clean but plain — bring it into the editorial (Cinzel/Playfair) system:

1. **`.feeds-into-strip` / `.fi-badge`** — pill row on each farm card. Tone classes: `.fi-key` (gold), `.fi-essence`, `.fi-ancient`, `.fi-shard`, `.fi-uber`. Sub-spans: `.fi-ic` (icon), `.fi-lab` (label), `.fi-sep` (arrow), `.fi-for` (what it makes). Give each tone a distinct, restrained accent; tighten the "→ makes X" rhythm.
2. **`.event-ref` reference section** — `.er-title` (give it the Cinzel masthead treatment), `.er-sub`, `.er-grid` (3 blocks), `.er-block` / `.er-block-head` / `.er-arrow`, `.er-table` (`.er-item` / `.er-from` / `.er-note`), `.er-recipe` (🧪 cube recipe line). This is the centerpiece of the mission — make it read like a codex page. Confirm placement directly under the grail is visually anchored.
3. **`.tz-zone-detail`** inline box (`.zd-row` / `.zd-k` / `.zd-v` / `.zd-note`) — harmonize with the zone cards; confirm the open/close affordance reads (untracked zones now have `cursor:pointer`, but `tagTzZonesWithBossId` ~L4762 still sets `cursor:default` + a "no roster boss" title on them — **decide the honest affordance**: either let them look clickable since they now toggle detail, or keep them subdued; CC left both signals present, your call on the final look).
4. Mobile: the `.er-grid` (3 cols) + `.feeds-into-strip` wrap — confirm breakpoints.

## Coordination / constraints
- CC owns test files + data; you stay on visuals — unchanged convention.
- Commit `bible.html` + tests ONLY. NEVER commit `bible_routes.html` (dead fork), `K_perf.js`, `H_sweep.js`, `J_screens.js`, `L_integrity.js`. Type-prefix, **no Co-Authored-By footer**.
- Don't touch `BOSSES` dropTable or `SPECIAL_DROPS` data — visual/CSS + prose only, or you'll trip the L-integrity gate.
- One known honest-affordance ambiguity flagged in #3 above — pick the final look.
