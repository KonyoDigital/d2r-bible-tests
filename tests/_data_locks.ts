// Shared STRICT data-count locks (consolidated 2026-06-12, audit item B-3).
// These are deliberate tripwires: an exact count catches accidental data loss
// (a bad edit dropping 5 items turns the suite red immediately). Konyo's call:
// keep them strict — do NOT loosen to ranges or derive them from the data.
// When content is deliberately added/removed, update the ONE constant here;
// every spec imports from this file, so there is exactly one line to bump.

// Boss roster chips: 11 farmable bosses + 2 event drops
// (Summoner = Key of Hate, Dclone = Annihilus).
export const BOSS_CHIPS_TOTAL = 13;

// The calculator grid's full grail item count.
export const CALC_ITEMS_TOTAL = 322;

// Collapsible .sec-h sections on the binds tab — bump in LOCKSTEP when adding
// a binds section (the v109 memory rule).
export const BINDS_SECTIONS_TOTAL = 16;

// isEndgameRelic() canonical set size (v80).
export const ENDGAME_RELICS_TOTAL = 15;

// Nav tab bar entries (v158 dock spec). v232: +TZ tracker → 12.
export const NAV_TABS_TOTAL = 15;  // v470 + Forge · v559 + Forge·Uniques + Forge·Sets (the grail forges)

// Horadric cube recipe browser rows (v177).
export const HORADRIC_RECIPES_TOTAL = 36;
