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
// v1717 — STAYS 322. The v1716 silospen pull added 216 item names to the drop tables, and for a
// few hours they landed in ITEMS too, which tripled the Calculator grid to 538 and put 66 of the
// 69 _UNI_EXTRA uniques inside the one surface bible.html says in words they must never enter.
// The routing now reads window.ITEM_REGISTRY (every droppable item) while ITEMS stays the curated
// calculator DB — so this tripwire keeps doing its job and the number it guards did not move.
export const CALC_ITEMS_TOTAL = 322;

// Distinct item names across every boss dropTable — the MASTER drop index that
// ITEM_REGISTRY is built from, and what the farm routing reads. This is a different
// number from CALC_ITEMS_TOTAL by design since v1717: the silospen RoW 3.0 pull put 216
// more real drops into the tables, and rows the calculator has no card for carry `nc:1`
// so they join the registry WITHOUT joining the curated calculator grid.
// Same tripwire rule as its sibling: exact, and bumped deliberately.
export const DROP_INDEX_TOTAL = 538;

// Collapsible .sec-h sections on the binds tab — bump in LOCKSTEP when adding
// a binds section (the v109 memory rule).
export const BINDS_SECTIONS_TOTAL = 16;

// isEndgameRelic() canonical set size (v80).
export const ENDGAME_RELICS_TOTAL = 15;

// Nav tab bar entries (v158 dock spec). v232: +TZ tracker → 12.
export const NAV_TABS_TOTAL = 17;   // v710.4 — +📺 TV·D (the live scanner's flagship board) joined the workshop group

// Horadric cube recipe browser rows (v177).
export const HORADRIC_RECIPES_TOTAL = 36;
