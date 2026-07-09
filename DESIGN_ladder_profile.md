# DESIGN — 🪜 Ladder Profile (parallel account), v634 candidate

**Konyo's ask (2026-07-10):** "for ladder it needs to be a toggle option, like a secondary account
with the whole website parallel to the ladder — different runes/stash/forge. But maybe just
architect it, so things don't get messy."

**The incident that motivates it:** flipping `d2r_ladderMode` to 'ladder' on the live profile made
v631 auto-promote seven 3os reads out of unknownReads (Mania suddenly fit every 3os weapon),
re-allocated the Death Mask from Radiance to Bulwark, and rewired half the Forge — all inside the
ONE shared state. Reversing took a hand-diff against a snapshot. Ladder and non-ladder are separate
in-game economies; they must be separate states here too, not one flag over shared data.

---

## Core concept — profile-prefixed storage, main untouched

One active-profile pointer, one routing seam:

```
d2r_activeProfile = 'main' (default, absent = main) | 'ladder'
```

- **main profile → the existing unprefixed `d2r_*` keys, byte-for-byte untouched.**
  Zero migration, zero risk to the 74-word live state. If the feature is ever ripped out,
  main never knew it existed.
- **ladder profile → the same keys under an `L·` prefix** (`L·d2r_runeStash`, `L·d2r_owned`, …).
  Starts empty = a fresh account.

### The seam

`bible.html:13415` — `const LS = window.localStorage`. That line becomes the router:

```js
const _PROFILE = (window.localStorage.getItem('d2r_activeProfile')==='ladder') ? 'ladder' : 'main';
const _FORKED = new Set([ /* the per-account keys, list below */ ]);
const LS = {
  getItem:    k => window.localStorage.getItem(_key(k)),
  setItem:    (k,v) => window.localStorage.setItem(_key(k), v),
  removeItem: k => window.localStorage.removeItem(_key(k)),
};
function _key(k){ return (_PROFILE==='ladder' && _FORKED.has(k)) ? 'L·'+k : k; }
```

`_PROFILE` is read ONCE at boot and never changes mid-session — **switching profiles always
means a full `location.reload()`**. That is the anti-messiness rule: no live re-pointing, no
half-migrated in-memory Sets, no cascade like today's.

**Audit required before build:** 75 accesses already go through `LS.*`, but **98 use
`localStorage.*` directly** — each direct call must be reclassified (route through LS if it
touches a forked key; leave as-is for shared/site keys). This is the bulk of the work and the
main regression risk. Mechanical, grep-driven, one commit per surface.

### Key inventory (decided per key, not blanket)

**FORKED — per-account game state:**
`d2r_owned, d2r_copies, d2r_unknownReads, d2r_magicFinds, d2r_ethereal, d2r_superiorBases,
d2r_multiKeep, d2r_wishlist, d2r_runeStash, d2r_gemStash, d2r_craftStash, d2r_craftBaseStash,
d2r_materialStash, d2r_statues, d2r_setPieces, d2r_rwMade, d2r_rwUnmade, d2r_rwBaseUsed,
d2r_rwVerify, d2r_muleAssign, d2r_muleRoster, d2r_vault, d2r_socket, d2r_forgeStep, d2r_forgeSkip,
d2r_forgeDone, d2r_intakeLog, d2r_intakeSeen, d2r_grailImportReport, d2r_createNow*`

**SHARED — site prefs, reference, plumbing:**
`d2r_activeTab, d2r_bossFilters, d2r_bossSorts, d2r_pinnedBoss, d2r_tz, d2r_mf, d2r_players,
d2r_dockCollapsed, d2r_shortcuts, d2r_logger, d2r_v, d2r_bible, d2r_casc, d2r_intakeUrl,
d2r_lastTopScan, d2r_aicDraft`

**RETIRED inside ladder profile:** `d2r_ladderMode` — the ladder PROFILE is implicitly ladder
(all 9 words unlocked, no 🪜 strip); main stays nonladder (strip shown). The old toggle buttons
in the Chronicle header become the profile switch.

### Seed rule

`_RWC_SEED` (the 74-word owner floor) applies **only when `_PROFILE==='main'`** — the ladder
account boots a genuinely empty Chronicle (0/100), empty vault, empty rune tallies. Same
condition wherever the floor re-applies (`d2r_rwProfile` fresh-pin logic composes: fresh-pin
tests keep working because they run on main).

## Toggle UX

- Persistent header pill, top-right by the nav: **`⚔ MAIN | 🪜 LADDER`** (current side lit).
  Click → confirm toast → `LS_raw.setItem('d2r_activeProfile', …)` → `location.reload()`.
- **Always-visible mode cue while in ladder:** gold 🪜 ribbon on the header + a tinted nav
  underline, so a screenshot can never be mistaken for the main account. (Chronicle title also
  reads "Ladder Chronicle — 0/100".)
- Intake: the scan writes to whichever profile is active at scan time; the report card names it
  ("intaken to 🪜 LADDER"). Folder + AI pipeline unchanged (LOCKED) — only persistence routes.

## What deliberately does NOT fork

- Art, BASE_DB/RUNEWORD_TIP reference data, SOCKET_MAX — game truth is game truth.
- Deploy, tests, routines: specs write unprefixed keys → they exercise main; new specs cover
  the ladder profile explicitly.

## Build plan (phased, each phase shippable + gated)

1. **P1 — routing core** (~1 session): LS router + `_FORKED` set + the 98 direct-localStorage
   audit + seed gating + reload-switch API. Spec: bleed-proof invariant — write a rune/base/word
   in ladder, reload into main, byte-identical main state (and vice versa).
2. **P2 — switch UI + cues**: header pill, ladder ribbon, empty-Chronicle onboarding copy,
   Forge/Chronicle headers name the account. Spec: pill switches + cue renders + strip logic
   (main: strip with 9; ladder: no strip, words tasked).
3. **P3 — lifecycle sims**: full e2e demo in the ladder profile (intake → forge → chronicle at
   0→N) mirroring v621's journey spec; routines updated (Routine I picks both profiles' specs).

**Not started. Awaiting go-ahead — build P1 or park.**
