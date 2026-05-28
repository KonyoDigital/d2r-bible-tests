#!/usr/bin/env python3
"""
binds tab — per-monster mlvl lock pass

Authoritative source: lootcube.net (reads MonStats.txt / SuperUniques.txt direct)
+ canonical Diablo Archive rule: super-unique Hell mlvl = max(SuperUniques.txt
custom level, area_level + 3). Throne wave bosses have custom overrides that
exceed area+3 (Lister 92, Bartuc 93, Ventar 93). Colenzo's custom 83 is below
the area+3 floor (85+3=88), so he spawns at 88.

Also fixes:
- Demonic Mastery body text 1/10/20 → 1/5/10 (matches sources note already
  inside the same tab — Patch 3.2 reduced slot thresholds)
- Frenzied Hell Spawn champion mlvl 82 → 83 (Arreat Plateau Hell alvl 81 + 2)

Idempotent. Backs up to .bak_pre_mlvl_lock_<ts>. Syncs 3 copies.
"""
import os, shutil, sys, hashlib
from datetime import datetime

TS = datetime.now().strftime("%Y%m%d_%H%M%S")

TEST_FILE = "/Users/konyo/d2r_bible_tests/bible.html"
DL_FILE   = os.path.expanduser("~/Downloads/konyo_d2r_bible_v43.html")
DESK_FILE = os.path.expanduser("~/Desktop/konyo_d2r_bible_v43.html")

# (old_fragment, new_fragment) — each must occur exactly once
# Format: super-unique row mlvl cell
EDITS = [
    # ---- super-unique table mlvl corrections ----
    ('<tr><td class="item-name" style="color:var(--uber)">Bishibosh</td><td>A1 · Cold Plains</td><td>71</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Bishibosh</td><td>A1 · Cold Plains</td><td>74</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Coldcrow</td><td>A1 · Cave L1</td><td>72</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Coldcrow</td><td>A1 · Cave L1</td><td>80</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Rakanishu</td><td>A1 · Stony Field</td><td>72</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Rakanishu</td><td>A1 · Stony Field</td><td>74</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">The Smith</td><td>A1 · Barracks</td><td>73</td>',
     '<tr><td class="item-name" style="color:var(--uber)">The Smith</td><td>A1 · Barracks</td><td>79</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Pitspawn Fouldog</td><td>A1 · Jail L2</td><td>74</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Pitspawn Fouldog</td><td>A1 · Jail L2</td><td>79</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Witch Doctor Endugu</td><td>A3 · Flayer Dungeon L3</td><td>83</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Witch Doctor Endugu</td><td>A3 · Flayer Dungeon L3</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Battlemaid Sarina</td><td>A3 · Ruined Temple</td><td>82</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Battlemaid Sarina</td><td>A3 · Ruined Temple</td><td>87</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Ismail Vilehand</td><td>A3 · Travincal</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Ismail Vilehand</td><td>A3 · Travincal</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Geleb Flamefinger</td><td>A3 · Travincal</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Geleb Flamefinger</td><td>A3 · Travincal</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Toorc Icefist</td><td>A3 · Travincal</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Toorc Icefist</td><td>A3 · Travincal</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Bremm Sparkfist</td><td>A3 · Durance of Hate L3</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Bremm Sparkfist</td><td>A3 · Durance of Hate L3</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Wyand Voidbringer</td><td>A3 · Durance of Hate L3</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Wyand Voidbringer</td><td>A3 · Durance of Hate L3</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Maffer Dragonhand</td><td>A3 · Durance of Hate L3</td><td>85</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Maffer Dragonhand</td><td>A3 · Durance of Hate L3</td><td>86</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Colenzo the Annihilator</td><td>A5 · Throne (Wave 1)</td><td>92</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Colenzo the Annihilator</td><td>A5 · Throne (Wave 1)</td><td>88</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Bartuc the Bloody ⚠️</td><td>A5 · Throne (Wave 3)</td><td>92</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Bartuc the Bloody ⚠️</td><td>A5 · Throne (Wave 3)</td><td>93</td>'),
    ('<tr><td class="item-name" style="color:var(--uber)">Ventar the Unholy</td><td>A5 · Throne (Wave 4)</td><td>92</td>',
     '<tr><td class="item-name" style="color:var(--uber)">Ventar the Unholy</td><td>A5 · Throne (Wave 4)</td><td>93</td>'),

    # ---- champion-tier Frenzied Hell Spawn mlvl ----
    ('<tr><td class="item-name">Frenzied Hell Spawn</td><td>A5 · Arreat Plateau</td><td>82</td>',
     '<tr><td class="item-name">Frenzied Hell Spawn</td><td>A5 · Arreat Plateau</td><td>83</td>'),

    # ---- Demonic Mastery body text — match sources note 1/5/10 ----
    ('Slots come from <strong>Demonic Mastery</strong> (separate skill): rank 1 = 1 slot · rank 10 = 2 slots · rank 20 = 3 slots (max). Full = can\'t bind more — Consume one to free a slot',
     'Slots come from <strong>Demonic Mastery</strong> (separate skill, Patch 3.2 reduced): rank 1 = 1 slot · rank 5 = 2 slots · rank 10 = 3 slots (max). Full = can\'t bind more — Consume one to free a slot'),

    # ---- update sources note with this verification pass ----
    ('<strong>Corrected this pass:</strong> Throne wave bosses are mlvl <strong>92</strong> (MonStats), not 88 — rankedboost\'s aLvl+3 is wrong. Hephasto\'s aura is <strong>RANDOM</strong> (always Aura Enchanted), NOT fixed Holy Fire — the old "always Conviction/Holy Fire" line is 1.09-era data. The Smith fixed consume verified (+180% ED, -20% phys taken, Lvl 15 Holy Fire). A1/A3 mlvls corrected (Coldcrow 72, Rakanishu 72, Endugu 83, Sarina 82, Council 85).',
     '<strong>Corrected this pass (2026-05-28 lootcube/MonStats lock):</strong> Throne wave is NOT uniform mlvl 92 — Colenzo spawns at 88 (custom 83 + area-floor 85+3), Bartuc 93, Ventar 93, Lister 92 (custom overrides). Most A1/A3 super-uniques follow the <strong>area-level + 3</strong> rule: Bishibosh 74, Coldcrow 80, Rakanishu 74, Smith 79 (lootcube override), Pitspawn 79, Endugu 86, Sarina 87, Council family 86 (Travincal/Durance alvl 83+3). Hephasto\'s aura is <strong>RANDOM</strong> (always Aura Enchanted, diablo2.io v3.1.91636 comment), NOT fixed Holy Fire — the old "always Conviction/Holy Fire" line is 1.09-era data. The Smith fixed consume verified (+180% ED, -20% phys taken, Lvl 15 Holy Fire). Frenzied Hell Spawn champion mlvl 82→83 (Arreat Plateau Hell alvl 81+2). Demonic Mastery slot progression in body text aligned to 1/5/10 (Patch 3.2 reduction).'),
]


def patch_one(path):
    with open(path) as f:
        src = f.read()
    orig = src
    applied = 0
    skipped = 0
    for old, new in EDITS:
        c_old = src.count(old)
        c_new = src.count(new)
        if c_new >= 1 and c_old == 0:
            skipped += 1
            continue
        if c_old == 0:
            print(f"  ✗ MISSING anchor: {old[:80]}...")
            return False
        if c_old > 1:
            print(f"  ✗ AMBIGUOUS anchor (n={c_old}): {old[:80]}...")
            return False
        src = src.replace(old, new, 1)
        applied += 1

    if src == orig:
        print(f"  · {path}: no-op (already patched)")
        return True

    bak = f"{path}.bak_pre_mlvl_lock_{TS}"
    shutil.copy(path, bak)
    with open(path, "w") as f:
        f.write(src)
    new_md5 = hashlib.md5(src.encode()).hexdigest()
    print(f"  ✓ {path}: applied={applied} skipped={skipped} md5={new_md5[:12]} bak={os.path.basename(bak)}")
    return True


def main():
    targets = [TEST_FILE]
    if os.path.exists(DL_FILE):
        targets.append(DL_FILE)
    if os.path.exists(DESK_FILE):
        targets.append(DESK_FILE)

    for t in targets:
        if not patch_one(t):
            print("ABORT")
            sys.exit(1)

    print("\n--- 3-copy md5 check ---")
    for t in targets:
        with open(t) as f:
            h = hashlib.md5(f.read().encode()).hexdigest()
        print(f"{h}  {t}")


if __name__ == "__main__":
    main()
