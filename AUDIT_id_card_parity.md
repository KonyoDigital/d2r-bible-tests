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
| Event monsters (DClone, Uber Tristram triune, Pandemonium) | event-card / boss-table | mixed | 🟡 medium | audit whether each has a detail card or only a row; out-of-scope until mapped |
| Cows / Travincal / Pit | boss-table rows | n/a | 🟡 | covered by boss cards/tables already |

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
