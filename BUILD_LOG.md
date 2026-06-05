# D2R Bible — Build Log (cross-agent shared memory)

> **Purpose:** a single Obsidian-friendly log so understanding is **never lost in
> context** between Claude Code (CC), Claude Desktop, and Konyo. Append a dated
> entry whenever something ships or a decision is made. Pairs with `BUGS.md`
> (the regression log). Maintained continuously by CC's logging loop.

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
  WHOLE suite: **403 passed, 1 skipped** (15.6m). Dead-fork check clean. Pending
  commit + Cloudflare deploy + md5 parity + push.

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
