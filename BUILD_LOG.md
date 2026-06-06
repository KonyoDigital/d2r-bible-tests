# D2R Bible — Build Log (cross-agent shared memory)

> **Purpose:** a single Obsidian-friendly log so understanding is **never lost in
> context** between Claude Code (CC), Claude Desktop, and Konyo. Append a dated
> entry whenever something ships or a decision is made. Maintained continuously by
> CC's logging loop.
>
> **Companion docs (cross-referenced):** `GAME_RULES.md` (durable RoW game-truth +
> drop-odds provenance + deploy/CI facts) · `BUGS.md` (regression log, `REG-NNN`).

## How the agents split work
- **Desktop** = visuals/features; often pushes straight to `main` WITHOUT running
  the suite (recurring — Routine I CI is the BACKSTOP, not the gate).
- **CC** = routes/backend/symmetry/test-integrity + end-to-end shipping
  (commit → Cloudflare deploy → md5 parity → push).
- **Konyo** routes prompts between the two and plays **Reign of the Warlock (RoW)**,
  NOT vanilla D2R.

## Key invariants (do not regress)
- `bible.html` is a single-file app. Central helpers `artOr()` / `openDrop()` /
  `switchTab()` have **site-wide blast radius** — edit them → re-run the WHOLE suite.
  (REG-001: a Safari fix dropped `loading="lazy"` from `artOr()` → load-storm → 3 red.)
- Pre-push smoke gate runs `01_smoke + v71_d2art + v74_material_search +
  v80_endgame_relics` automatically (`hooks/pre-push`, `core.hooksPath=hooks`).
- Deploy is MANUAL: `cp bible.html /tmp/d2r_dist/d2r/index.html && cd /tmp/d2r_dist &&
  set -a && . ~/.config/cf-d2r/env && set +a && npx wrangler@latest pages deploy .
  --project-name=d2r-bible --branch=main`; then verify md5 parity
  (`curl -s -A 'Mozilla/5.0' https://bull-4-u.com/d2r/ | md5 -q` == `md5 -q bible.html`).
- Dead-fork strays (`H_sweep.js`/`K_perf.js`/`J_screens.js`/`L_integrity.js`) get
  spurious local edits — `git checkout --` them, NEVER commit. `git status` before commits.

---

## 2026-06-06 — CC: Herald ladder research + tier-card enrichment (v88)

**Context:** Konyo: *"start the Herald ladder research work autonomously on them
all."* Research the 5-tier RoW Herald ladder (Fright→Dread→Fear→Horror→Terror) from
official sources, NO fabrication, then enrich all 5 tier ID cards.

**Research (#49)** — cross-checked diablo2.io (authoritative monster page) +
diablobytes guide + WebSearch (rpgstash 403-blocked; d2db used with caution).
Verified facts now baked: spawn **Hell TZ only** (summoned by killing TZ monsters,
chance rises with kills — *exact threshold not published*); each kill advances the
next spawn one tier; tier is **per-session, resets to Fright on leave/disconnect**;
after Terror every spawn stays Terror; **Heralds always carry an aura, can roll two
at once** (Terror = two auras + minion pack); **drop scaling matches what the bible
already had** (Fright/Dread normal · Fear/Horror +1 · Terror +2); **all tiers can
drop Latent Sunder Charms**; **Patch 3.2 / S14 (live 2026-05-22):** Latents drop from
any MF monster, increased-Herald chance starts at tier 1, player-count no longer
heavily modifies Latent/Worldstone rates. **Flagged unverified (NOT baked):** d2db's
life/dmg table + 2% ire / 5 stacks / 1% conversion + element weights (contradicts
diablo2.io); Worldstone Shard ≈ 1:500 elite/boss is community-estimated only.

**Enrichment (#50)** — `heraldTierDetailHtml` (lean card for the 4 lower rungs):
added **⚙ How it spawns & climbs** (where · summoned-by · this-rung · next-spawn ·
tier-resets · aura) and a **🩹 Patch 3.2 / S14** section; folded the always-aura /
dual-aura fact into *what it is*; the *what it drops* line now says **every rung
including this one** can drop the 6 Latent Sunders; the closing note explicitly flags
the 3 unpublished gaps (kill threshold, per-tier mlvl/HP/immunity, Worldstone rate)
instead of inventing them. The apex rich `#herald-card` (already beyond Baal-format)
got a one-line **Patch 3.2 reconciliation** under the tier table — its pre-3.2
"Sunder threshold opens at T4" column now reads correctly against the all-tiers /
tier-1-start truth, without gutting the cited TheBugWarrior/Maxroll content.

**Invariants preserved:** every v75 test gate (5 tiers · apex=Terror · searchable ·
≥6 sunder chips · next-rung naming · HERALD_PORTRAIT emblem + 👹 fallback + lazy ·
no console errors) stays green. Pure additive copy — no math/data touched.

**Verify:** `v75_herald_tiers` + `v72_herald` 15/15 green; full suite green.

## 2026-06-06 — CC: hide NORM/NM site-wide — Hell-only view (v87)

**Context:** Konyo plays Hell-only RoW. Direction (verbatim): *"now hide NORM/NM
across the boss cards, calc grid, and rune tables"* with the standing constraint
*"i dont want [the math] touched.. just hidden."* So this is a **render-only** hide —
the drop math/data and the DOM are entirely intact; only `display:none` is applied.

**Shipped (visual hide, zero data/math change):**
- One CSS rule (after the `.t-hell` block) hides four per-difficulty class families:
  `dcol-*` (table columns) · `gdc-*` (boss-detail diff grid) · existing `t-*` (boss
  list diff grid) · `csrc-*` (calc source-table rows) · `acr-*` (aid-card compare
  rows) · `schip-*` (aid-card source chips) — each for `norm`/`normTz`/`nm`/`nmTz`.
- Per-difficulty classes added at every render surface: boss list diff-grid (existing
  `t-*`), boss-detail diff-grid (index-based `gdc-*`), boss-detail top-12 grid,
  boss full drop table (header + cells via a `dcol` lookup), Countess rune table
  (header + `cell()` gains a class arg), calc item-detail source table rows, and the
  aid-card compare-rows + source-chips.
- **Why CSS, not DOM removal:** positional integrity probes (`02_verified_anchors`
  `nth(4)`=hell / `nth(2)`=nm SoJ 1:2,286; `03_cell_correctness`; `v41_deep_audit` &
  `routing_and_data_integrity` column-index no-fabrication scans; `01_smoke` th=8 /
  diff-grid=6) all read the DOM positionally — `display:none` keeps every cell in the
  tree so they stay green untouched. The drop scaling/anchors are literally unchanged.

**Test updates (Hell-only reality):** 2 source-chip-click specs (`bug013_014`,
`bug040_050`) clicked `.source-chip').first()` — for Nagelring the first DOM chip is
now a hidden NORM/NM source → not actionable. Retargeted to `.source-chip:visible`
first (the real post-hide UX). Full suite **423 green**.

---

## 2026-06-06 — CC: TZ-zone Hell drops GRID — boss-card parity (v86)

**Context:** Konyo wanted the TZ zones to carry the boss-card "drops grid" look.
Direction (verbatim): *"i dont want [the drop math] touched.. just hidden. or just
leave it.. and add to the TZ zones the hell drops grid."* The Hell-only render is the
RoW reality (Konyo plays Hell endgame).

**Shipped (additive — nothing cut, math untouched):**
- New `zoneHellGridHtml(z)` renders a **rarest-first ranked TABLE** (the boss
  top-drops grid look) of the zone's TC-reachable grail/uber pool, ranked by **TC
  ceiling** (the rarity proxy) with `# · item · TC · qlvl` columns. Top-20 inline +
  a `<details>` "show all N" full table. Every row routes to the one canonical item
  card via `navigateToItem` (same as the boss grid rows). Placed ahead of the
  existing categorical chip block (`zoneDropBlockHtml`), which is **KEPT** alongside.
- **HONESTY (zero fabrication):** the grid deliberately omits per-kill `1:N` columns
  because the silospen terrorized-zone pull is still pending — TC ceiling + qlvl only,
  with an inline note explaining why no per-run odds are shown.
- CSS: `.zd-hell-grid` + `.zd-hg-*` (boss-card `.drops` table idiom, gold hover rows).
- **Tests:** `tests/v86_tz_hell_grid.spec.ts` (6 tests) — exposed + rarest-first +
  no-fake-odds + grid-in-every-pool-zone + rows route via navigateToItem + chips kept
  alongside + live row-click opens item card + no console errors. Full suite green.

> NORM/NM "wipe everywhere" stays deferred per Konyo's "or just leave it" — the math
> is untouched; only the additive Hell-framed grid was added. If a full hide is wanted
> later it's UI-render-only (keep dropTable data + scaling math intact).

---

## 2026-06-06 — CC: TZ-zone ID cards enriched to Baal-card depth (batch 4, v85)

**Context:** Konyo's unified-card-template vision — "update these 10-20 TZ zones to
match that same very format enriched and indetail we already have for Baal", "add a
dedicated area for anything special/uncommon", ADDITIVE only ("nothing gets cut out"),
ZERO fabrication. TZ zones are areas (not bosses) that DO drop loot.

**Shipped (all additive to `zoneDetailHtml`, isolated blast radius — NOT a central helper):**
- **Dedicated SPECIAL-DROPS area** (`zoneSpecialDropsHtml`) — the Baal "guaranteed /
  endgame specials" module, rebuilt for terror zones from the **single-source
  `SPECIAL_DROPS` / `ACT_SHARD` data** (no fabricated odds). Surfaces, as clickable
  chips routed through `openDrop`:
  - 💠 **Sunder Charm** — Heralds of Terror roam every active Hell TZ → Latent Sunder
    (chip opens the Herald ladder); notes the zone's terror tier (mlvl 96 vs lower).
  - 💎 **Worldstone Shard** — the act-matched shard (`ACT_SHARD`) named with its
    Renewed-Sunder cube target (`SHARD_RENEWED`).
  - 🔱 **zone specials** gated on real per-zone facts: ⚒️ Hellforge rune (River of
    Flame), 🔑 Key of Hate (Arcane), 🔑 Key of Destruction (Halls), Griswold's Legacy
    set (Tristram).
- **best-character** module (`zoneBestCharHtml`) — derived from real zone facts:
  density → AoE; the named super-uniques' FIXED immunities → "bring a 2nd damage type";
  ghost/Arcane → casters; mlvl 96 → terror-only elite farm. Strategy advice, not odds.
- **action-plan** module (`zoneActionPlanHtml`) — auto-built route from the multi-area
  zone name (`A + B + C` → "clear in order"), the super-unique finisher, the roaming
  Herald, and the act shard to save. Rendered as an `<ol class="zd-plan">`.
- **head emblem** now `artOr(z.name, z.emoji, 'sm')` (was a bare 📦) — graceful
  emoji fallback, keeps `loading="lazy"` (REG-001).
- New CSS: `.zd-item-dim` (muted non-clickable chip), `.zd-plan` (ordered list).

**Test:** `tests/v85_tz_enrichment.spec.ts` (6) — every zone has all 3 modules; the
act-matched shard + zone-specific Key/Hellforge/Griswold specials; the Herald chip
actually opens the Herald card; artOr head keeps lazy; no console errors across all
zones. **Full suite green: 416 passed / 1 skipped (18.5m).** No dead-fork strays.

**v85.1 — golden shell:** Konyo flagged the zones still didn't *look* like the Baal
card. Rewrapped `zoneDetailHtml` in the **same `.gbc-card` + `.gbc-header` golden shell**
the Baal/Herald cards use (gradient header banner with artOr emblem `lg` + name +
location/mlvl/TC subtitle + tier badge + ✕ close), body in `.gbc-body`. Wrapper
`.tz-zone-detail:has(> .gbc-card)` strips its own border/bg so there's no card-in-card.
Now the terror-zone detail reads as the unified ID-card design language. v85 head test
updated to assert the gbc-card shell; all 28 TZ specs + full suite green.

**HONESTY BOUNDARY (per Konyo's no-fabrication rule):** the boss cards' 6-difficulty
mlvl/TC grid, "Quick take @ MF" line, and per-item **1:N odds** in TOP DROPS come from
the SOURCED silospen RoW per-boss odds pull. **TZ zones have NO sourced per-kill odds
yet** (the standing flagged gap — silospen `desecrated` pull pending). So those numeric
sections CANNOT be faithfully built for zones without fabricating. Honest alternative
(next): a rarest-first TOP-DROPS grid built from the real TC-reachable pool
(`zoneGrailDrops`, ranked by TC tier), styled like the boss grid but labelled by
TC/"TZ-reachable" — no invented 1:N. Difficulty grid omitted for zones (boss-only data).

**Unified-template note:** convergence is achieved ADDITIVELY — the leaner cards gain
the missing Baal modules + the golden `.gbc-card` shell, so they read as one design
language without a risky rewrite of every renderer. TZ zones are the first instance.

---

## 2026-06-06 — CC: sync-audit framework + tools/search/super-unique sync (batch 1)

**Context:** Konyo asked the loops to "look for synchronization across the website…
alert us or fix it automatically", then to unify everything to the rich Baal boss-card
format and upgrade every title emoji to artOr. This batch ships the standing audit +
the safe, fully-verified mechanical fixes. Big data-enrichment work (Heralds, all
droppers → Baal format) is tracked separately (needs official RoW data, no fabrication).

### Batch 1 ✅ (full suite 410 passed / 1 skipped, 17.4m)
- **v83 sync audit** (`tests/v83_sync_audit.spec.ts`, 7 tests) — machine-readable
  symmetry contract: tab↔panel↔nav-chip parity, search parity, openDrop route parity,
  endgame-relic parity, tools-tab collapse parity, REG-001 artOr lazy lock, docs↔data
  anchor sync. This is the "is everything still wired" standing sweep.
- **Global search tab sync** — `v42BuildCommands` derived its "Switch to …" commands
  from a hardcoded 8-tab list (drifted: endgame + tools missing). Now DOM-derived from
  `.tabs .tab` → permanently sync-proof.
- **Item Set Tracker → collapsible card** — was a bare always-open `<h2>` in the 🧰 tools
  tab while the 2 stash planners were collapsible boss-cards. Now `.boss-card.collapsible`
  (`#set-tracker-card`), symmetric + title-only by default. (`bug110_149` BUG-114 updated.)
- **Super-unique artOr upgrade** — su-card + zd-su-card titles now use
  `artOr(su.name, emoji, 'sm')` (emoji fallback, zero fabrication). Added 8 super-unique
  art keys to `D2IO_ART`, each probed live HTTP 200 + image/png on 2026-06-06: The Summoner,
  Izual, Hephasto the Armorer, Shenk the Overseer, Nihlathak, Frozenstein, The Smith,
  Sszark the Burning. The other named super-uniques have no diablo2.io art → keep emoji.

### Out-of-sync backlog (Konyo's "perfect what we built" list — tracked, not yet done)
- **Heralds:** research the 5-tier ladder from official RoW sources, then enrich every
  tier card (not just apex) to Baal format; 👹 emblem → artOr. (Sunder Charms are
  Herald-exclusive — the RoW holy grail.)
- **Baal-format parity sweep:** every loot-dropper (ubers, DClone, super-uniques,
  Ancients, quest rewards/Hellforge/Anya, events) → the rich boss-detail format. Build a
  coverage matrix first; real data only.
- **artOr title sweep:** remaining bare-emoji titles (Herald emblem, static TZ "🎯" meta).
- **boss-nav symmetry:** WORLD EVENT (Uber Diablo) chip grid alignment vs the other tiers.

### Batch 2 ✅ (full suite 410 passed / 1 skipped, 17.6m · commit `3956432` · deploy `8b9ff767` · md5 parity ✓)
- **Emblem unification through artOr** — super-unique *detail-header* emblem (was bare 💀),
  uber-boss emblem (was a hardcoded `<img>`), and Herald tier 1-4 emblems (were bare 👹) now
  all route through the central art helper. Uber art is mirrored into `D2IO_ART` from each
  entry's existing `b.art` (single source, no duplicated URLs); Herald tiers wear the verified
  `HERALD_PORTRAIT` (the same monster art the apex card uses) with 👹 fallback. All REG-001-safe
  (`loading="lazy"` + onerror). `D2IO_ART` stays a pure diablo2.io-URL map — `HERALD_PORTRAIT`
  (a data-URI) is built inline, NOT injected into the map (would break the v71 URL invariant).
- **boss-nav alignment** — reserved a uniform 2-line label height
  (`.boss-nav-sticky .boss-nav-group-label{min-height:2.4em}`) so every tier column's chips
  start at the same Y. Root cause: single-line labels (ACT BOSSES) sat 23px higher than the
  2-line ones; WORLD EVENT's lone chip only *looked* off next to taller stacks. Verified all 6
  columns now share chipTop.
- **Coverage matrix delivered** — per-entity-class audit of the 12 Baal-card sections (BOSSES
  full ✓; ubers/super-uniques/heralds have gaps in why-farm/feeds-into/best-char/action-plan/
  top-grail/top-table; numeric columns for ubers blocked on real RoW odds — flagged, never faked).
- **v75 test updated** to assert the Herald *portrait* (not a charm graphic) + lazy lock.

### Batch 3+ backlog (Konyo's unified-ID-card vision — additive, no cuts, no fabrication)
- **TZ-zone enrichment:** the ~11 terror zones + the Pit cross-link get the unified rich card
  (already have location/mlvl/TC/density/super-unique roster/grail pool/why-farm/feeds-into).
  ADD: a dedicated **special-drops** area (Worldstone Shards → Sunder, Hellforge rune, set/quest
  specials Konyo has actually found), best-char + action-plan, unified card shell. TZ zones are
  areas not bosses — keep them as zone cards but visually consistent with the boss ID card.
- **Unified card-template system:** one shared visual shell + type-specific section modules so
  bosses / ubers / events / super-uniques / heralds / TZ zones / tips all read as one design
  language (eye-candy, clean-cut), routed + clickable. Sections an entity lacks are simply
  omitted, not faked.
- **Hover-glow unification (batch 3):** unify the row/chip hover treatment site-wide (the clean
  `translateY(-1px)`+gold-border+soft-shadow idiom) so the hovered/selected entity is obvious.

---

## 2026-06-06 — CC night session: Colossal endgame enrichment + Herald dedup

**Context:** Konyo asked for a large, multi-phase enrichment of the RotW endgame
(Colossal Ancients) plus a Herald-of-Terror dedup, working autonomously overnight.
Data is "mostly extracted from diablo2.io"; the 6 jewel stats Konyo pasted are
authoritative. ZERO fabrication mandate.

### Phase 32 — Herald of Terror dedup ✅ SHIPPED-LOCAL (pending commit)
- **Problem:** `'Herald of Terror'` resolved to TWO cards — the lean
  `heraldTierDetailHtml` tier card (via `openDrop` → `findHeraldTier`, checked first)
  AND the rich dedicated RotW `#herald-card` (search cmd + `renderHeraldCard`).
  Two search results, one richer than the other.
- **Fix:** added `window.openHeraldCard()` (switchTab rotw → expand section → scroll
  to `#herald-card`). `openDrop()` apex branch now redirects to it. Search:
  removed the duplicate apex entry from the HERALD_TIERS loop (`if (t.apex) return`);
  the dedicated RotW search cmd now calls `openHeraldCard()`. The 4 lower rungs
  (Fright/Dread/Fear/Horror) keep their lean tier cards.
- **Tests:** v75 updated (apex now asserts the rich RotW card, + a "only ONE
  Herald of Terror search result" guard). 26/26 green (v75+v72+v56+v80).

### Phase 33 — Endgame tab emblem/logo sync (Desktop continuation) ✅ SHIPPED-LOCAL
- The 4 `.road-branch` cards on the endgame maintab used flat emoji `<h3>` titles
  instead of the upgraded **animated** art emblems (`relicArtGlow` runs on
  `.d2art-img` inside `.endgame-relic`).
- Added `branchEmblem`/`branchEmblemRaw` helpers in `renderEndgameRoad()`; the 4
  branches now carry art emblems (Diablo Clone=`diablo_graphic.png`,
  Colossal=`talic-opt_graphic.png`, Herald=`HERALD_PORTRAIT`, Sunder=`Crack of the
  Heavens` charm art) + `.endgame-relic` glow. Sunder branch now routes via
  `openDrop('Crack of the Heavens')` (a real card) instead of a bare tab-switch.
  CSS: `.road-branch h3` → flex; `.rb-art` 38px. v80 7/7 green.

### Phase 34 — 6 Colossal Ancient Jewel ID cards + routing ✅ SHIPPED-LOCAL
- Self-contained `COLOSSAL_JEWELS` (6) module (line ~3657) → `findColossalJewel`
  + `colossalJewelDetailHtml` render a calculator-style `.colossal-jewel-card`
  into `#item-detail`. NOT folded into `SPECIAL_DROPS` (avoids
  `renderSpecialDrops`/`MATERIALS`/statue-tracker/baseline ripple — pure additive).
- `openDrop` hook inserted BEFORE `findMaterial` (exact normalized match), so the
  aggregate "Colossal Ancient Jewels" material card still resolves (additive, not
  a replacement). Global search: 6 jewel cmds (cat `colossal jewel`).
- Each Ancient's drop-row (Talic/Korlic/Madawc) now renders its **2 specific
  jewel chips** via a `jewels:[...]` field on `UBER_BOSSES` + `_jewelChips` in
  `renderUberBossCards`. Talic→Fire/Bile, Korlic→Frost/Stone, Madawc→Thunder/Light.

### Phase 35 — 5 named Colossal Statue ID cards + routing ✅ SHIPPED-LOCAL
- `COLOSSAL_STATUES` (5) + `findColossalStatue` + `colossalStatueDetailHtml`
  (`.colossal-statue-card`, drop-boss links via `openBossDetail`). `openDrop` hook
  + 5 search cmds (cat `colossal statue`). Aggregate "Colossal Ancient Statue"
  card untouched.
- Aggregate statue card's DROPS-FROM rows now link each named statue: statue-aware
  branch in the SHARED `materialDetailHtml` `fromRows` builder (prefix-matches the
  5 statue names only → every other material card renders unchanged).
- Statue tracker rows (`renderStatueTracker`): the name is now an `openDrop` link
  with `event.stopPropagation()` so it routes to the ID card without toggling collect.

### Phase 36 — glowing Colossal Endgame Showcase under Events ✅ SHIPPED-LOCAL
- New `#event-colossal-showcase` event-card in the ancients tab (under Events);
  `renderColossalShowcase()` paints 11 `.colossal-tile.endgame-relic` tiles (6
  jewels + 5 statues), each `openDrop`-routed + `artOr` emblem. Called at init
  after `renderUberBossCards()`. CSS `.colossal-grid`/`.colossal-tile` near
  `.statue-tracker`. The storyline `endgame` tab is left as-is.
- Sync: the existing `#event-colossal-ancients` jewel table's 6 names are now
  clickable → their new jewel cards (`event.stopPropagation();openDrop(...)`).

### Verification — full suite GREEN
- New spec `tests/v81_colossal_jewels.spec.ts` (11 tests): data modules, jewel/statue
  card render, additive-aggregate guard, global search, Ancient drop-row pairs,
  aggregate-statue DROPS-FROM links, statue-tracker routing, the 11-tile glowing
  showcase, event-table jewel links, no console errors. Gotcha for future specs:
  onclick attrs escape `'` as `\'`; an apostrophe-aware matcher
  (`/openDrop\('((?:\\.|[^'])*)'\)/` then unescape) is required to extract names
  like "Defender's Bile" — naive `[^']+` truncates at the inner apostrophe.
- `openDrop` + `materialDetailHtml` are CENTRAL (site-wide blast radius) → ran the
  WHOLE suite: **403 passed, 1 skipped** (15.6m). Dead-fork check clean.

### Ship complete — committed, deployed, pushed, CI-green
- Committed `f5e91a8` (Colossal pinnacle ID cards + Herald dedup + endgame emblem
  sync) + `2df6373` (Obsidian docs cross-ref + drop-odds/deploy provenance).
- Cloudflare deploy + md5 parity confirmed: local == live `47ead1c1…` at
  `https://bull-4-u.com/d2r/`. Pushed `ccdde35..f5e91a8` then `f5e91a8..2df6373`.
- CI backstop GREEN: scheduled Routine I run **27057755096** (headSha `2df6373`)
  all 4 jobs success (shard 1/3, 2/3, 3/3, merge reports). Golden smoke 51/51 local.

### Data — the 6 Colossal Ancient Jewels (Konyo-provided, diablo2.io)
All: 1% chance-to-cast its element armor when struck · +element dmg · +5-10% to
that skill-damage type · -5-10% to enemy element resist · +3-5% experience ·
+25-50% extra gold · +15-35% MF. ilvl 75. Strictly better than Rainbow Facets.
You get the jewel matching the Ancient you kill **last**.
| Jewel | Element | CtC armor (lvl) | +elem dmg | enemy res |
|---|---|---|---|---|
| Defender's Bile | poison | Bone Armor (25) | +95 poison/1s | -5-10% |
| Guardian's Thunder | lightning | Cyclone Armor (25) | +1-75 light | -5-10% |
| Protector's Frost | cold | Frozen Armor (25) | +10-30 cold | -5-10% |
| Defender's Fire | fire | Blaze (25) | +20-60 fire | -5-10% |
| Protector's Stone | physical | Fade (15) | +30-50% ED, +10-30 | -5-10% phys-dmg res |
| Guardian's Light | magic | Psychic Ward (25) | +15-35 magic | -5-10% |

Ancient → jewel pair (which Ancient drops which, by last-kill):
- **Talic** (sword/shield, WW) → Defender's Fire / Defender's Bile
- **Korlic** (polearm, Leap) → Protector's Frost / Protector's Stone
- **Madawc** (throwing axes) → Guardian's Thunder / Guardian's Light

### Data — the 5 named Colossal Statues (each from a TERRORIZED Hell act boss)
- Talic's Anguish — Hell Andariel
- Korlic's Pain — Hell Duriel
- Madawc's Ire — Hell Mephisto
- Bul-Kathos' Nightmare — Hell Diablo
- Worusk's End — Hell Baal
Rate ~1:8 to 1:15 per kill, terror only; MF does not affect. Cube all 5 →
Colossal Summit → summon the Colossal Ancients.
