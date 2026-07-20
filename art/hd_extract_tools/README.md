# HD art extraction toolchain (v2, 2026-07-21 pass)

Pulls true in-game item sprites from the local D2R install (vanilla Battle.net client,
via CrossOver) instead of relying on diablo2.io/maxroll backups. This extends the
existing v384 CASC pipeline (see project memory `d2r_casc_hd_art_extraction.md` and
`d2r_casc_toolchain_rebuild.md`) — same method, just re-run for a fresh set of items.

## Rebuild (CascLib gets wiped from /tmp between sessions — this is expected/by design)

```
git clone --depth 1 https://github.com/ladislav-zezula/CascLib.git /tmp/CascLib
cd /tmp/CascLib && mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCASC_BUILD_SHARED_LIB=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ..
make -j4        # -> /tmp/CascLib/build/casc.framework

g++ -O2 -std=c++17 -I/tmp/CascLib/src -x c++ casc_extract.c \
    -F/tmp/CascLib/build -framework casc -o /tmp/casc_extract
export DYLD_FRAMEWORK_PATH=/tmp/CascLib/build
```

## D2R install location

```
D2R="/Users/konyo/CXPBottles/Battle.net Desktop App/drive_c/Program Files (x86)/Diablo II Resurrected"
```
CASC store is under `$D2R/Data`. Confirmed present, 28GB, 175,827 enumerable files (verified 2026-07-21).

## Usage

Enumerate (find sprite paths by substring):
```
/tmp/casc_extract "$D2R" --enum "" /tmp/full_enum.txt        # all files
grep -i "\.sprite$" /tmp/full_enum.txt | grep -i items | grep -iv lowend   # item icons only (~445)
```

Extract one file by its EXACT enumerated path (must include the `data:` prefix):
```
/tmp/casc_extract "$D2R" 'data:data\hd\global\ui\items\misc\key\mephisto_key.sprite' /tmp/out.sprite
```

Decode SpA1 (raw RGBA8888, 40-byte header) -> cropped PNG:
```
python3 spa1_decode.py /tmp/out.sprite     # writes /tmp/out.png next to it
```

## Item name -> game code -> invfile -> sprite path

To find which sprite backs a display name, pull the relevant excel table and check its
`code`/`invfile` columns (misc.txt for keys/potions/organs/essences/tokens; weapons.txt/
armor.txt for gear, `invfile` col 53/26 varies by table — check the header row first,
column order is NOT constant across tables):
```
/tmp/casc_extract "$D2R" "data:data/global/excel/misc.txt" /tmp/misc.txt
head -1 /tmp/misc.txt | tr '\t' '\n' | cat -n     # find the real column indices
```

## What this pass added (2026-07-21)

- `art/hd_mephisto_key.png` — Pandemonium Keys (Terror/Hate/Destruction all share ONE
  sprite in-game: misc.txt shows all 3 codes pk1/pk2/pk3 -> invfile=invmph).
- `art/hd_full_rejuv_potion.png`, `art/hd_rejuv_potion.png` — Full/Partial Rejuvenation
  Potions (misc.txt: rvl->invvpl->full_rejuv_potion.sprite, rvs->invvps->rejuv_potion.sprite).
- Sunder Charms (Bone Break, Black Cleft, Crack of the Heavens, Cold Rupture, Flame Rift,
  Rotting Fissure) mapped in the manifest to the EXISTING `art/hd_charm_large.png` — no new
  extraction needed, they're RotW-mod Grand Charms and D2R renders every Grand Charm
  (unique or not) with the single generic Grand Charm icon.

## Confirmed NOT extractable (searched full 175,827-file enumeration, no match)

- Worldstone Shard (Western/Eastern/Southern/Northern/Deep) — RotW-mod-exclusive name,
  no matching sprite anywhere under `items/misc` in the vanilla CASC store. Left on
  existing diablo2.io fallback art. Do not fabricate.
- Colossal Ancient Jewels (Bile/Thunder/Frost/Fire/Stone/Light) — same story, RotW-only.

See `../HD_ART_MANIFEST.json` for the full item-name -> art-path mapping (639 entries).
