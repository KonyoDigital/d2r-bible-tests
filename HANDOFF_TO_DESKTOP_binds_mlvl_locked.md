# Handoff: Binds tab — per-monster mlvl lock + remaining visual polish

**From:** Claude Code (CC, deep web-fetch capable)
**To:** Claude Desktop
**Date:** 2026-05-28
**Bible md5 (all 3 copies synced):** `34fdbd23fa87186a790737489cc1c56d`
**Repo HEAD:** `1ba7661` "fix(binds): mlvl lock pass"

## What I just landed

Deep per-monster verification against **lootcube.net** (reads `MonStats.txt` / `SuperUniques.txt` direct) cross-checked with the **Diablo Archive wiki canonical rule**: super-unique Hell mlvl = `max(SuperUniques.txt custom level, area_level + 3)`.

19 anchor-based replacements in `_binds_mlvl_lock.py` (kept in repo for audit trail, safe to inspect/delete).

### Throne wave — NOT uniform 92

Your `92f3694` ship had "all Throne = 92 (MonStats)". That's only true for **Lister**. The other waves have their own custom levels:

| Wave | Boss | Was | Now | Source |
|------|------|-----|-----|--------|
| 1 | Colenzo | 92 | **88** | lootcube custom=83, below area+3 floor → spawns 88 |
| 3 | Bartuc | 92 | **93** | lootcube custom override |
| 4 | Ventar | 92 | **93** | lootcube custom override |
| 5 | Lister | 92 | **92** | lootcube custom override (correct) |

### A1/A3 super-uniques

Most non-Throne super-uniques follow the canonical `area_level + 3` rule. The pre-CC numbers had multiple drift errors that `92f3694` either kept or made worse:

| Boss | Was | Now | Area-level math |
|------|-----|-----|-----------------|
| Bishibosh | 71 | **74** | Cold Plains alvl 71 + 3 |
| Coldcrow | 72 | **80** | Cave L1 alvl 77 + 3 (was wrong before) |
| Rakanishu | 72 | **74** | Stony Field alvl 71 + 3 |
| The Smith | 73 | **79** | lootcube custom override |
| Pitspawn Fouldog | 74 | **79** | Jail L2 alvl 76 + 3 |
| Witch Doctor Endugu | 83 | **86** | Flayer L3 alvl 83 + 3 |
| Battlemaid Sarina | 82 | **87** | Ruined Temple alvl 84 + 3 |
| Ismail / Geleb / Toorc | 85 | **86** | Travincal alvl 83 + 3 |
| Bremm / Wyand / Maffer | 85 | **86** | Durance L3 alvl 83 + 3 |

### Already correct (unchanged)

Infector of Souls 88 · Hephasto 88 · Shenk 83 · Dac Farren 83 · Sharptooth 84 · Lister 92.

### Champion-tier fix

- Frenzied Hell Spawn 82 → **83** (Arreat Plateau alvl 81 + 2). Rest of champion table all 87 = RoF/Throne/etc area-level 85 + 2 ✓.

### Demonic Mastery body text

The contradiction I caught earlier (body said 1/10/20, source note said 1/5/10) — body now matches: `rank 1 = 1 slot · rank 5 = 2 slots · rank 10 = 3 slots (max)`. Per Patch 3.2 reduction.

### Sources note

Rewrote the "Corrected this pass" section to reflect this lootcube/MonStats lock. Removed the inaccurate "all Throne = 92" claim, replaced with per-wave breakdown.

## What I did NOT verify per-monster (still trust-on-faith from `92f3694`)

- **Hephasto's "always Aura Enchanted random" claim** — diablo2.io comments confirmed it's random in v3.1.91636+ (not 1.09-era fixed Conviction/Holy Fire). High confidence, kept.
- **The Smith fixed consume** (+180% ED / -20% phys / L15 Holy Fire) — lootcube confirms Holy Fire aura. Other specifics unverified.
- **Lister Lvl 15 Meditation + 7 minions** — community-canonical, kept.
- **In-game-name ↔ internal-family decoder rows** (megademon = Pit Lord, blunderbore = Urdar, succubuswitch = Stygian Fury, etc.) — sourced from aoeah list, kept.
- **Hell Temptress mlvl variance** (HoV 85 vs WSK3 87 — written in decoder note as "HoV=83→champ 85, WSK3=85→champ 87"). That's actually wrong with the area+3 rule: Halls of Vaught Hell alvl IS 85 (not 83), so champion=87 there too. Worth verifying.

## Flagged for your pass (worth checking)

1. **Hell Temptress decoder row** — current text claims "Primary spawn Halls of Vaught (aLvl 83 → champ 85); WSK3 aLvl 85 → champ 87". The Halls of Vaught Hell alvl is **85**, not 83. Fix: "Halls of Vaught & WSK3 both aLvl 85 → champ 87".

2. **Possibly missing bindable super-uniques** in the 22-row table:
   - **Blood Raven** (A1 Burial Grounds) — Corrupt Rogue super-unique, coded Demon. Quest-locked single-bind per character, but technically bindable. Worth adding with a "⚠️ quest-locked" flag.
   - **Treehead Woodfist** (Dark Wood) — Brute super-unique, Brutes are Demons. Should be bindable.
   - **Bonebreaker** (Crypt) — also Brute family.

3. **The Smith mlvl 79** is from lootcube custom override but Barracks Hell alvl is 75, so area+3=78. Custom 79 is +1 above the floor. Worth a screenshot check.

4. **Aura formula `floor(mlvl/8)`** — still unsourced as first-party. The math works out for the published examples (mlvl 88 → aura 11, mlvl 96 → aura 12) so it's almost certainly correct, but watch for a Maxroll/Blizzard explicit citation.

## Files

- **Production bibles**: `~/Downloads/` + `~/Desktop/` — synced, md5 `34fdbd23`
- **Test mirror**: `/Users/konyo/d2r_bible_tests/bible.html` — same md5, committed `1ba7661`
- **Backups**: `bible.html.bak_pre_mlvl_lock_20260528_205348` in each location
- **Patch script** (idempotent, kept in repo): `_binds_mlvl_lock.py`

## Test status

- Smoke + BUG-040..050 sweep: **20/20 GREEN** (1.2m, workers=1)
- Did NOT run full 155-test sweep (no DOM structure changes, mlvl text-only swaps shouldn't affect any test). Run if you want belt+braces.

## Your turn

Pre-flip checks before re-editing:
```
md5 /Users/konyo/d2r_bible_tests/bible.html
# should show 34fdbd23fa87186a790737489cc1c56d
```

Then:
1. Apply the 4 flagged items above (Hell Temptress alvl 83→85, optional Blood Raven add)
2. Re-sync 3 copies
3. Smoke test
4. Hold `v43-binds-verified` tag until your pass lands clean
