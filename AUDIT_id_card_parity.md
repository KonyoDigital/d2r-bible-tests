# ID-Card Baal-Format Parity Audit (#51)

> CC, 2026-06-06. Master goal: unify **every loot-dropping ENTITY's** ID card to
> the rich Baal boss-card (`.gbc-card`) format. Constraints: ZERO FABRICATION,
> ADDITIVE ONLY, clean eye-candy. This is the gap matrix + enrichment plan.

## The canonical Baal format (`.gbc-card`, renderBossDetailCard L6717)
Structural checklist a fully-unified entity card should hit:
1. `.gbc-card` golden shell (2px gold-dim border, radius 14, deep shadow).
2. `.gbc-header`: `artOr(name,…, 'lg')` emblem · `.gbc-name` title · `.gbc-subtitle`
   · `.gbc-loc` (location + kills/hr baseline) · `.gbc-tier` badge · close button.
3. `.gbc-section` blocks (each `.gbc-section-label`), as data allows:
   🏆 signature drop · 🎯 why farm · 🔗 feeds-into · 📊 stats×6-diff grid ·
   ⭐ best char from roster · 📋 pre-run action plan · 💎 top-15 grail picks
   (MF-adj, sorted) · 🎯 guaranteed drop · 🔥 TZ behavior · 📦 top-12 drops table.

## Two legitimate card families (do NOT force-merge)
- **Drop-SOURCE entities** → should reach `.gbc-card` parity (bosses, super-uniques,
  TZ zones, Heralds, event monsters, cows/travincal…). These are the master-goal targets.
- **LOOT items** (the things that drop: uniques/sets, runes, materials, keys/organs,
  colossal jewels/statues, Herald charms) → correctly use the leaner `.gic-card`
  item-card (sources + where-to-farm). NOT in scope for gbc-conversion — a rune is
  not a "dropper."

## Gap matrix — drop-source entities

| Entity | Builder | Shell | Parity | Gap / action |
|---|---|---|---|---|
| Act bosses + minions | `renderBossDetailCard` L6717 | `.gbc-card` | ✅ CANONICAL | reference |
| TZ zones | `zoneDetailHtml` L4251 | `.gbc-card` | 🟢 high (v85.1/v86: header + drop grid) | verify it has why/feeds-into where data exists; likely fine |
| Herald apex | `#herald-card` L2422 | `.gbc-card` | 🟢 high (custom rich) | fine |
| **Super-uniques** | `superUniqueDetailHtml` L4334 | **`.zd-*` (lean)** | 🔴 **LOW** | **primary gap** — no golden shell, no top-grail pool styling, no header/tier block. Has: stats, drops, TZ link, DClone note, full-table link, pending-odds caveat. → wrap in `.gbc-card` shell, keep ALL content. **v51 asserts CONTENT only** (`super-unique detail`, `Frigid Highlands`, `grail uniques reachable`, `Diablo Walks the Earth`, `openBossDetail('…')`, `pending silospen pull`, no `undefined`) → restyle safe if content preserved. |
| **Uber bosses** (Uber Meph/Diablo/Baal, Lilith, Izual, the 3 Ancients, …) | `renderUberBossCards` L8800 | **`.ubc-*` (rich, OWN shell)** | 🟡 rich-but-different | Already a RICH detailed card: emblem · name/role · loc · type · stat grid (mlvl/hp/def/block/immune) · resists · abilities list · "🏆 ONLY DROPS HERE" drop row · strategy. NOT `.gbc-card`. Full visual unification = a large rewrite that must remap all bespoke fields into gbc-sections AND rewrite ~15 v78 structural assertions (`.ubc-immune strong`, `.ubc-stat strong`, `.ubc-body`, `.ubc-drop`). **DECISION: defer** — high regression risk + needs visual review (do it WITH Konyo able to eyeball, not blind/autonomous). Content quality already meets the "detailed & enriched" bar; only the shell differs. Tracked as the ubc→gbc follow-up batch. |
| Event guide cards (Uber Tristram / Cow / DClone / 22-nights walkthroughs) | static `.event-card` (tab-ancients) | n/a | ✅ correct as-is | These are read-through GUIDES (mechanics walkthroughs), not single-entity drop ID cards — gbc-conversion would be wrong. Leave. |
| Cows / Travincal / Pit | boss-table rows + boss cards | n/a | ✅ | covered by boss cards/tables already |

### Master-goal status (drop-source entities)
- ✅ `.gbc-card`: act bosses + minions · TZ zones (v85.1) · Herald apex · **super-uniques (v91)**
- 🟡 rich sibling shell (`.ubc-*`): Uber bosses — deferred cosmetic unification (above)
- The substantive goal ("every dropper has a rich, detailed, enriched, honest ID card")
  is **met**; what remains is purely the optional ubc→gbc *visual* shell merge.

## Loot-item cards (gic-card — confirm consistency, not gbc-conversion)
| Loot | Builder | Notes |
|---|---|---|
| Grail uniques/sets | `renderItemDetailCard` L6172 | gic-card, source-driven — correct |
| Materials (keys/organs/shards/tokens) | `materialDetailHtml` L3697 | gic-card |
| Runes | `runeDetailHtml` L3880 | gic-card |
| Colossal jewels/statues | `colossal*DetailHtml` L3783/3826 | gic-card |
| Herald Latent Sunder charms | (charm chips) | open via gic |
| Herald tiers | `heraldTierDetailHtml` L3942 | gic-card, v88-enriched — these ARE droppers (the Herald rungs) but render as gic; borderline. Leave as-is unless we promote the whole Herald ladder to gbc later. |

## Recommended ship order (lowest risk first)
1. **#52 lock (safe):** v83 invariants — (a) every entity/loot card builder emits an
   `artOr(...)` title emblem; (b) the already-`.gbc-card` entities keep header + ≥N
   `.gbc-section` blocks. Catches future drift. Ship.
2. **Super-unique golden-shell enrichment (targeted):** wrap `superUniqueDetailHtml`
   in `.gbc-card` + `.gbc-header` (artOr lg emblem, name, subtitle=role, loc, tier=mlvl),
   keep every existing `.zd-row`/note verbatim inside `.gbc-section` blocks. Re-run
   v51 + v64 + v45 + bug013_014 + routing + full suite. Ship.
3. Event-monster card mapping — separate batch once the above lands.

## Honesty guardrails (NEVER violate)
- No fabricated per-kill odds for super-uniques — keep the "pending silospen pull" caveat.
- Additive: nothing in the current cards gets removed, only re-shelled/enriched.
