# Nightly maxroll.gg cross-reference — gap-map (2026-06-08)

## SHIPPED STATUS (updated 2026-06-11)
- **B1 Mercenary** — SHIPPED. `#` Mercenary mechanics section in the reference tab
  (auras by hire-difficulty + best merc gear). Gap #1 is CLOSED (`mercenar` now 87 hits).
- **B2 Gambling** — SHIPPED v176 (commit `670e33a`). `#gambling-ref` reference section:
  fixed odds 1797/200/2/1 per 2000, per-act NPCs, ilvl=clvl, MF-irrelevance, RotW-flagged
  dream-uniques. Gap #2 CLOSED. Spec `v176_gambling_reference` (5).
- **B3 Breakpoints** — SHIPPED. `#` Breakpoints section (FCR/FHR caster tables) with an
  explicit RotW caveat. Gap #3 CLOSED.
- **B4 Crafted-item recipes** — SHIPPED v177 (commit `70b5cfc`, live md5 `71142643`). The
  Crafting section already had the 4-craft overview; the real gap was the EXACT per-slot
  recipe matrix. Added `#craft-recipe-matrix` collapsible: magic base + slot rune for all 9
  slots × 4 crafts (Caster/Blood/Safety/Hit Power), base-game cube recipes from maxroll's
  Crafted Items list, RotW affix-pool caveat. Also fixed the v176 gambling colour bug
  (Rare/Set/Unique cells used non-existent `--rare`/`--set` vars → `--star`/`--q-set`/`--q-unique`).
  Spec `v177_craft_recipe_matrix` (5). Gap #4 CLOSED.
- **B5 Warlock-overview cross-ref** — SHIPPED v178 (commit `c0f7d84`, live md5 `febc0520`).
  The bible covered Bind Demon exhaustively (binds tab) but never laid out the build's ACTIVE
  skill kit. Added `#warlock-skill-kit` to the reference accordion: Echoing Strike (up to 5
  weapon echoes off FCR, cone+return, scales weapon base/ED/off-weapon ED), Mirrored Blades /
  Blade Warp / Hex Bane / Levitation Mastery synergies, Demonic Mastery (10pt→2 Defilers),
  Consume, Bind Demon (cross-links to binds tab), 125% FCR target. Sourced maxroll Echoing
  Strike guide + icy-veins skill page, RotW "verify live tooltips" caveat, no fabricated
  numbers. Spec `v178_warlock_skill_kit` (6). Gap #5 CLOSED.
- **REMAINING: B6 cross-check completeness sweep** (runewords/cube/MF/TZ/sunder/immunity).
  Verify-don't-assume: grep the bible BEFORE picking the next bridge — gaps #1/#3 were already
  filled when re-checked, #4 was half-built (overview present, matrix missing), #5 was a real
  gap (deep bind mechanics present, but no active-skill overview).

Bridge 0 of the nightly project. Tab-by-tab inventory of the d2r bible vs maxroll.gg/d2
resource coverage. **ADDITIVE ONLY** (nothing cut), **zero fabrication**, **RotW-aware**
(Konyo plays Reign of the Warlock — flag where maxroll vanilla data may differ).

No `bible.html` edits in this bridge — this is the plan only. Each gap below becomes its
own bridge task, shipped one at a time (Patch-Trinity-lite: feature + spec + log + deploy).

## maxroll resource index (43 pages, from /d2/category/resources)
Class overviews (Ama/Asn/Barb/Druid/Necro/Pala/Sorc/**Warlock**), Attack Modifiers, Attack
Speed, Breakpoints & Animations, Chance to Block, Crowd Control, Damage Calculation, Damage
Reductions, Death, Durability & Quantity, **Elite Groups & Act Bosses**, Equipment Granted
Skills, Experience, Game Walkthrough, **Gold Find & Magic Find**, Hit Chance, **Horadric Cube
Recipes**, Immunities, Important Quests, Leveling, Life & Mana, Map Reading, **Mercenary
Mechanics**, Next Hit Delay, Player Settings, Poison Damage, Run/Walk, Rushing, Shrines &
Wells, Sorceress…, Staff Mods, **Sunder Charms**, **Secret Cow Level**, **Terror Zones**,
Trading, **Warlock Overview**, plus Items category: **Runewords**, item qualities, **Gambling**,
**Crafting**, Treasure Class.

## Bible tabs (current)
main · bosses · calculator · TZ zones · runes · RotW special · events · endgame · binds · reference · tools

## VERIFIED gaps (grep-confirmed against bible.html)
| # | Gap | Current coverage | Maps to maxroll | Bridge value |
|---|-----|------------------|-----------------|--------------|
| 1 | **Mercenary reference** | **0** (`mercenar` = 0 hits) | Mercenary Mechanics | HIGH — a Warlock buffs his merc; Act-2 aura mercs + Insight/Infinity/CtA are core |
| 2 | **Gambling reference** | **0** (`gambl` = 0 hits) | Gambling | HIGH — what to gamble (rings→SoJ/BK, amulets, circlets→coronet), gold-cost scaling, affix odds |
| 3 | **Character breakpoints** | thin — only the `/players` breakpoint exists; FCR appears 45× but ONLY inside item/runeword stat strings, no breakpoint TABLE | Breakpoints & Animations + Attack Speed | HIGH — FCR/FHR/IAS/FBR tables; **RotW Warlock breakpoints may differ from vanilla — verify vs maxroll Warlock Overview** |
| 4 | **Crafted-item recipes** | partial — reference tab has rune-upgrade + uber-key + "useful cubing" recipes, but NO caster/blood/safety/hit-power CRAFT recipes | Crafting + Horadric Cube Recipes | MED — the magic-base + rune + jewel + gem craft formulas |
| 5 | **Warlock class overview** | RotW-special + binds tabs exist (bind system just finished v107-v112) | Warlock Overview | MED — cross-check Echoing Strike / Demonic Mastery / synergies for missing mechanics |

## CROSS-CHECK passes (verify-don't-assume — bible likely has these; confirm completeness only)
| Topic | Bible home | maxroll page | Note |
|-------|-----------|--------------|------|
| Runewords | runes tab (`runeword` 47×) | Runewords | well covered — completeness diff only |
| Cube recipes | reference tab | Horadric Cube Recipes | confirm rune/gem/uber recipes complete |
| MF / gold-find DR | reference tab (MF math present) | Gold Find & Magic Find | add gold-find + the unique/set/rare DR curve if thin |
| Terror Zones | TZ tab | Terror Zones | confirm zone list + mlvl 96 / TC ceilings match |
| Sunder Charms | endgame/TZ | Sunder Charms | confirm the 5 sunders + immunity-break math |
| Immunities | per-boss + binds | Immunities | additive: how much −res / sunder to break an immunity |
| Uber Tristram | endgame/events | (activity) | key→organ→torch flow present — confirm |
| Secret Cow Level | events | Secret Cow Level | confirm recipe + drops |

## RotW guard-rails for every bridge
- Konyo plays **Reign of the Warlock**, not vanilla. maxroll documents vanilla D2R (it DOES
  now have a "Warlock Overview" page — likely RotW-aware; use it but cross-check vs Konyo's
  in-game experience, which is authoritative when it nuances a table cell).
- Drop odds stay silospen-RoW-sourced; maxroll is used for MECHANICS (breakpoints, merc,
  gambling, crafting), not for drop-rate numbers.
- Additive only — new collapsible sections in the matching tab; nothing cut, format matches
  the site (`.sec-h`/`.sec-body`, clickable/routable chips where items are referenced).

## Bridge order (proposed)
B1 Mercenary · B2 Gambling · B3 Breakpoints · B4 Crafted-item recipes · B5 Warlock-overview
cross-ref · B6 cross-check sweep (runewords/cube/MF/TZ/sunder/immunity completeness).
Each ships independently. No pressure — bridge by bridge.
