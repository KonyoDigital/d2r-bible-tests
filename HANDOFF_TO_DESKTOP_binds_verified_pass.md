# Handoff: Binds tab — verified surgical pass + remaining unverified items

**From:** Claude Code (CC, web tools available)
**To:** Claude Desktop (Desktop Commander, 3-copy sync)
**Date:** 2026-05-28
**Bible md5 (all 3 copies in sync):** `4f9cd953722b054f5b816a9696c3c3d7`
**Test repo commit:** see latest after `ae5eab6` (binds-surgical)

## What I just landed (verified against real fetches)

Pulled actual patch 3.2 notes from Maxroll + bind-demon page from diablo2.io + RotW bind list from aoeah. Fixed 6 fabricated claims that were in the tab. All 3 copies (Downloads, Desktop, test mirror) synced to `4f9cd953`. Test suite 4/4 GREEN on smoke (binds keyboard nav + boot integrity + BUG-040/050).

| # | What was wrong | What it says now | Source |
|---|---|---|---|
| 1 | "Bind chance 20% → 56%, get below ~25% HP" | Real 3.2 mechanics: Death Mark synergy halved (1→0.5%/lvl), missing-HP benefit reduced, per-demon max-HP cap introduced. No fixed % published. | [Maxroll 3.2 PTR](https://maxroll.gg/d2/news/patch-3-2-ptr) |
| 2 | "Aura remap deterministic 1:1 (Conviction→Fanaticism, Might→Concentration, Holy Fire→Vigor, Holy Shock→Vigor, Blessed Aim→Thorns)" | Verbatim patch note: removed auras (Conviction/Holy Fire/Holy Lightning/Blessed Aim/Might) replaced with one of {Fanaticism, Vigor, Thorns, Concentration}. **Not deterministic, not 1:1**. Holy Freeze still rolls. | [Maxroll 3.2 PTR](https://maxroll.gg/d2/news/patch-3-2-ptr) |
| 3 | "Slot cap: 5 pts = 2 demons, 10 pts = 3" | Slots come from **Demonic Mastery** (separate skill): rank 1 = 1 slot, rank 10 = 2 slots, rank 20 = 3 max. | [aoeah RotW bind guide](https://www.aoeah.com/news/4396--d2r-best-warlock-demons-to-bind-demonic-mastery--consume-buffs-rotw) |
| 4 | "Above ~50% HP usually fails. Get it under ~25% first" | Bind chance scales with missing HP; per-demon max-HP cap means thresholds vary. Drop as low as possible. | Maxroll patch notes |
| 5 | "Roughly 1-in-5 roll for Fanaticism on Aura Enchanted unique" | Removed — no published roll weight. Just reroll. | (no source for original 20% claim) |
| 6 | "<40% Heph/Lister, <50% Council" as authoritative thresholds | Flagged as pre-3.2 community-derived; 3.2 changed the rules (per-demon cap). | [Maxroll 3.2 PTR](https://maxroll.gg/d2/news/patch-3-2-ptr) |

## What's still unverified — your turn (when you get web fetch)

These weren't touched. They MAY be correct, but I couldn't fetch enough monster-page detail to confirm. Recommend deep `diablo2.io/monsters/` pulls per family.

### Champion + Unique tier tables (`#binds-champion`, `#binds-unique`)
Both tables claim mlvl 87/88 with these family names: **Urdar**, **Minion of Destruction**, **Pit Lord**, **Venom Lord**, **Maw Fiend**, **Hell Temptress**, **Stygian Fury**, **Grotesque Wyrm**, **Frenzied Hell Spawn**.

What I confirmed from the aoeah RotW bind list (internal-name table):
- `bighead1-5` = Tainted Goatman (Lit Res)
- `fallen1-5`, `fallenshaman1-5` (Fire Res)
- `corruptrogue1-5`, `cr_archer1-5`, `cr_lancer1-5` (multi-res)
- `goatman1-5` (multi-res)
- `vulture3` = Vulture Demon (Fire Res)
- `fetish1-5`, `fetishshaman1-5`, `fetishblow1-5` (multi-res)
- `blunderbore1-4` = **Blunderbore (covers Frenzytaur)** (multi-res + Damage %)
- `vilemother1-3`, `vilechild1-3` (Cold Res)
- `regurgitator1-3` (Poison Res)
- `councilmember1-3` (Fire/Lit Res) — **confirmed bindable**
- `megademon1-3` = **Megademon (the actual Pit Lord internal name)** (Fire Res)
- `minion5,7`, `suicideminion5,7` (Fire Res) — Lister's wave
- `succubus1-5`, `succubuswitch1-5` (multi-res + Damage Reduction)
- `overseer1-5` (Cold Res)
- `imp1-5` (Fire Res)
- `putriddefiler1-5` (Poison Res)

**Action for you:** verify each champion/unique row against this internal list + fetch `diablo2.io/monsters/<family>` for exact mlvl and spawn areas. Some user-facing names (Urdar, Hell Temptress, Stygian Fury) need cross-referencing — they may be sub-variants of the internal families.

### Super-Unique 22-row table (`#binds-superunique`)
Specific mlvls (71/73/85/86/87/88) and fixed-aura columns claimed for: Bishibosh, Coldcrow, Rakanishu, The Smith, Pitspawn Fouldog, Witch Doctor Endugu, Battlemaid Sarina, Ismail Vilehand, Geleb Flamefinger, Toorc Icefist, Bremm Sparkfist, etc.

**Action for you:** pull each from `diablo2.io/monsters/` to verify mlvl + spawn area + fixed aura. The diablo2.io bind-demon skill page only confirmed these names exist; specific data needs per-monster fetches.

### "Aura level = floor(mlvl / 8)" formula (`#binds-unique`)
Unsourced. Could be community math, could be wrong. Verify against a wiki.

### Field guide Act 4 / Act 5 deep cards (`#binds-fieldguide`)
Visual ID + spawn detail blocks. Probably mostly classic-D2 stable but worth a spot check.

## Files

- **Production bibles**: `~/Downloads/` + `~/Desktop/` — synced, md5 `4f9cd953`
- **Test mirror**: `/Users/konyo/d2r_bible_tests/bible.html` — same md5, committed
- **Backup**: `bible.html.bak_pre_binds_surgical_20260528_175104` in test repo
- **Patch script** (idempotent, safe to inspect): `_binds_surgical_fix.py` — will be deleted after commit
- **Sources note** (`#binds-sources`): may need a "2026-05-28 CC verification pass" line added

## Notes for the next sync

When you do the deep monster-page verification, **drop me a follow-up handoff or commit directly** — the bible's currently consistent across all 3 copies, so you have a clean baseline to work from. Race-safe: just ping the test-repo md5 before/after your edit so we can both see if we're on the same baseline.
