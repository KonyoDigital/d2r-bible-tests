# HANDOFF → Desktop Claude: Unified Droppable ID-Card Epic

**From:** Claude Code (CC) · **Date:** 2026-06-01 · **Status:** foundation SHIPPED + LIVE, replication pass remaining

Konyo's vision: **every entity** (boss / TZ zone / super-unique / material / rune-source / pinnacle event)
is ONE canonical, editorial, **droppable expanding** ID card — glowing header, titled, perfectly formatted,
in-depth, with **clickable grail items that route to the SAME golden item card** the boss top-drops route to.
Any reference anywhere on the site links to that single card. "It's 90% built — architect/wire it in, don't
rewrite it." **No fabricated per-kill odds** — keep the "pending silospen pull" caveat where odds are unknown.

---

## THE CANONICAL PATTERN (already built — replicate this, don't reinvent)

All in `/Users/konyo/d2r_bible_tests/bible.html` (single-file app, ~1.1MB).

### The golden item card (the routing TARGET — leave as-is)
- `navigateToItem(name)` → switches to **calc** tab, renders `#item-detail .aid-card` (the golden item card).
- Boss top-drops rows + zone chips + SU chips ALL call `navigateToItem('<item>')`. ONE card, linked everywhere.
- Item names must be canonical `ITEMS[].n` / `ITEM_CODEX` keys (e.g. `Harlequin Crest (Shako)`, not `Shako`).

### The droppable detail-box pattern (the card to REPLICATE)
- Card click → toggle fn → fills an inline `.tz-zone-detail` / `.su-detail` box (hidden by default) with `*DetailHtml()`.
- Editorial CSS classes: `.zd-head` (glowing gold header band), `.zd-stats`/`.zd-stat`/`.zd-sk`/`.zd-sv` (stat grid),
  `.zd-row`/`.zd-k`/`.zd-v` (label rows), `.zd-note` (italic caveat).
- **Clickable grail chips:** `zoneDropBlockHtml(z)` (bible.html ~L3096) renders the TC-reachable grail/uber pool as
  `.zd-item.zd-item-click` chips, each `onclick="...navigateToItem('<item>')"`. This is the reusable holy-grail block.
- Detail boxes now have the boss editorial frame: gold border, drop-shadow, rounded overflow, glowing `.zd-head`
  (CSS ~L363–374).

### Honest-odds rule
Zones / super-uniques have NO per-kill odds (TC-reachable POOL only) → chips, NOT a rarest-first 1:N grid.
A ranked "1:N rarest-first" grid (like boss top-drops `.top-drops`, render ~L5321) is ONLY valid where real
per-item odds exist (bosses have `dropTable` + `effChance()`; zones do not). Do not fabricate odds to fake a grid.

---

## DONE & LIVE (CC, committed to main + deployed to bull-4-u.com/d2r/)

| Commit | What |
|--------|------|
| `ff57d9f` | Phase 1: every TZ zone is its own droppable ID card; roster-boss zones cross-link the boss via `zoneBossLinkHtml` |
| `0133be3` | Phase 2: SPECIAL_DROPS materials (keys/essences/organs/charms/shards) → unified `materialDetailHtml` card via `openDrop()`; feeds-into badges clickable; ESC closes. Spec `tests/v52_material_cards.spec.ts` (7 tests) |
| `113be89` | TZ-zone grail chips clickable → `navigateToItem` (`.zd-item-click`) |
| `27cffbd` | Editorial frame + glowing header on `.tz-zone-detail` / `.su-detail` |
| `00e4b6b` | Super-unique detail embeds the clickable `zoneDropBlockHtml` grail pool |

Material router: `window.openDrop(name)` (bible.html ~L3053) — material-first (SPECIAL_DROPS wins, since Pandemonium
keys ALSO live in ITEMS), grail-item fallback → `navigateToItem`. `findMaterial()` is direction-tolerant
("Northern Worldstone Shard" ↔ "Worldstone Shard (Northern)"). `MATERIAL_FEEDS`, `_materialIndex`, `materialDetailHtml`.

---

## REMAINING — pick these up (each = wire the pattern into a section that doesn't have it yet)

1. **WSK L1-L3 zone card** — Konyo's specific report: it "routes wrong + has no droppable expanding." Phase 1 made all
   TZ zones droppable; CONFIRM WSK opens its own `.tz-zone-detail` with the clickable grail pool + a `baal` cross-link
   (it's a roster-boss zone). Verify against `tzZoneBoss("Worldstone Keep L1-L3")`.
2. **Rune sources** — replicate the Countess `COUNTESS_RUNES` / `renderRuneTable` grid format for **Travincal, Hellforge,
   Cow Level, LK Chests** as Countess-style droppable rune-grid cards. Each droppable, with rune grids. (Not yet started.)
3. **Pinnacle / special events** — in-depth droppable cards for the SPECIAL UNIQUE DROPS per event: Uber Tristram →
   Hellfire Torch, Diablo Clone → Annihilus, Cow Level, Colossal Ancients → Colossal Jewels, "22 Nights". Cross-link the
   torch/anni into the unified `materialDetailHtml` (those entries already exist in `SPECIAL_DROPS.uberCharm`).
4. **Material card editorial parity (optional polish)** — `materialDetailHtml` uses `gic-*` classes (already glowing
   `.gic-name`). Confirm it reads as in-depth as a boss card; add a clickable "feeds → recipe target" if helpful.

### Data-accuracy flag for Konyo (do NOT silently "fix")
`SPECIAL_DROPS.worldstoneShard` (Worldstone Shard → Sunder Charm recipe) is **non-canonical** — in real D2R, Sunder
Charms drop directly from terrorized Hell monsters (6 element types), there is no "Worldstone Shard" item or cube recipe.
Keys / essences / organs / torch / anni ARE accurate. CC chose to faithfully surface EXISTING data, not rewrite the model.
**Ask Konyo before changing the shard data model.**

---

## PROTOCOL (mandatory)
- **Commit ONLY** `bible.html` + test/baseline files. **NEVER** commit `bible_routes.html`, `K_perf.js`, `H_sweep.js`,
  `J_screens.js`, `L_integrity.js` (they show as modified — leave them unstaged).
- Type-prefixed commits (`feat:` / `fix:` / `style:`), **NO Co-Authored-By footer**.
- Every card change: add/extend a Playwright spec, run it + the touched zone/SU specs (`bug013_014_routing`,
  `v40_lockdown`, `v49_zone_drops`, `v51_superuniques`, `v52_material_cards`) **in isolation** (`npx playwright test <spec>`).
  Suite-tail fatigue is real past ~140 tests — always re-run a failing spec in isolation before declaring a regression.
- **Deploy (manual):** `cp bible.html /tmp/d2r_dist/d2r/index.html` →
  `cd /tmp/d2r_dist && npx wrangler pages deploy . --project-name=d2r-bible --commit-dirty=true` →
  verify `curl -s -A 'Mozilla/5.0' https://bull-4-u.com/d2r/ | md5` == local `md5 -q bible.html` (use the deployment-
  specific `*.pages.dev` URL to dodge edge cache).
- No fabricated odds. Keep pending-silospen / official-source (silospen / d2runewizard / diablo2.io / Maxroll) caveats.

CC will keep working the same epic from the Mac side — coordinate via this file + the existing `HANDOFF_TO_DESKTOP_*`
convention. Suggest Desktop take **#2 (rune sources)** since it's the largest greenfield piece and independent of the
TZ/SU wiring CC is in.
