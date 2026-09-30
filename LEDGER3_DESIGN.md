# LEDGER 3.0 — the proof of the ledgers, as a section of the console (#58)

**His order, 2026-09-28 (handoff §33):** *"the ledger also needs flagship 3.0 upgrade architecture and rendering
with its own section properly.. like the evidence the proof the tooltips the sections related the witnesses
everything there backend might need to be physically showing too so it has a dashboard of some sort connected to it
so we can see what got tallied.. like for instance we do a scenario pinpointed tests now.. i want to see the reels n
shelf great we have that now the extraction and tallying and counting and proof of ledgers to all need that same
visual rendering so i can see that it was tallied properly and counted correctly. and where it was seen.. and the
hardening passes all of that logic.. might need to be surgically fixed in retrospect. so make sure to plan and
architect it as needed.."*

**His rulings, 2026-09-28 (handoff §34):**
1. **DOOR — "Room, no new tab."** 📒 LEDGER opens as a full overlay from a 📒 button next to 📚 Shelf in the Theatre
   and from an *open in 📒* link on the Vault tab's routing ledger; deep links `#ledger/session|item|test/<id>`.
2. **INFLATED TIERS — "Keep filed, flag 'retro: WATCHED'."** A look is a distinct VISIT, never a frame of a still
   screen. Radiance and the Horadric Cube stay filed at their true tier with the retro flag (shipped as P0, v3522).
3. **VETO — "Drop out of the count."** A vetoed misread stops counting, recorded with his veto and the frame; never
   a miss.
4. **SCENARIO RESULTS — "Tick the file too."** A scenario's verdict also ticks `TESTING_PHASE.md`; the repo is
   public, so only the scenario id, pass/fail/unknown and the date are written there.

**The one rule under all of it:** Ledger 3.0 is a SCREEN over the stores that already exist. It never keeps a
parallel copy of a fact. Where a fact is missing today, the fix is to make the owner of that fact persist it at the
moment of knowledge (heart-first rule 6), never to re-derive it in the room.

---

## 0. What ships in this slice (2026-09-29)

| piece | where | state |
|---|---|---|
| the per-session extraction record | `tv/ledger3.py` `session_record` | **shipped**, 13-case law, 11 red-proofs |
| its doors | `GET /api/ledger3/session?id=` · `GET /api/ledger3/sessions?limit=` | **shipped** (read-only) |
| its heart | doctor row `ledger3 sessions` (PERIODIC) · `corroborate.NO_JOINT_YET` | **shipped** |
| this design | `LEDGER3_DESIGN.md` | this file |
| the 📒 room, item proof card, scenario view, fixes | §4–§7 | **planned**, phases in §8 |

Everything below the line in §2 was measured read-only on his stores on 2026-09-28/29; the numbers are dated and
will move.

---

## 1. The stores (nothing new is written by this slice)

| store | owner (store_owners / path authority) | what it holds that the ledger reads |
|---|---|---|
| the journal ring `sessions*.jsonl` | the live reader (`replay.load_journal` reads the 5-generation ring) | one row per read/skip/verify/intake/system/kai event: `sessionId`, `lane`, `model`, `mode`, `ts`, `frameId`, `names`, `names_loc`, `lifecycle_tags`, `vault_names` / `thrown_names` / `pending_names` / `farmed_names` / `unvault_names`, `provisional`, `verify.confirm`, `kai.register.items`, `intake`, `door`, `ver` |
| the chronicle book | `control_app._chron_evidence_load` (`TV_CHRON_EVIDENCE`) | `{uniques\|sets}[name] -> [{reel, frame, lane, conf, witness, foundAt, droppedBy}]`, plus `refused[]`, `contested`, `notFound`, `pagesRead` |
| the vault witness ledger | `vault_retro` writes, `vault_evidence._load_owned` reads (`TV_VAULT_LEDGER`) | `owned[] -> {name, lane, kind, witnesses[{session, witness, frame, conf, lane, crop\|cropWhy}]}` |
| the shelf | `HIST_DIR` (`TV_HIST`) | `reel_<sid>/f_*.jpg`, `index.json`, `kai_report.json` (sealed = the report exists) |
| the river stamps | `river_stamp` (fixture root) | `{reel, station, from, by, why, at}` per hop |
| the structural survey | `retro_triage.load()` | per reel: `panels`, `frames`, `kinds`, `full`, `ts` |
| the tombstones | `control_app.tombstone_view` (reel_retention's path) | `{reel, session, mb, pages, frames, why, deletedTs}` + `kept[]` on a frame-level pass; ONE ROW PER PASS - a reel released in passes has several (REG-1557: measured 3 of 29 shelf reels, 14 rows, one reel four then six) |
| the board's own stores (later slices) | bible.html, read only through the board's door | `d2r_vaultProv`, `d2r_foundEvidence`, `d2r_chronicleInboxLog`, `d2r_tvdTallyLog`, `d2r_grailUnfound`, `foundLog` |
| `board_tally.json` | `board_tally_merge` | per PC/route: `sets` / `uniques` / `runewords` `{have, total}`, `drops[]` |
| `shadow_ledger.json` | `shadow_ledger` | per name: where the Wilson and live gates split |

**One key per fact, borrowed and never copied:** a reel is `chronicle_retro._reel_key` (`reel_s_X` and `s_X` are one
reel — 3,914 of 8,517 chronicle sightings are the same row under both spellings); a name is `item_identity.vault_key`
then `trace_spine.name_key` (qualifier kept, glyphs and case folded — his *Saracen's Chance* is straight-quoted in one
store and curly in another); a visit is `vault_retro.look_id` folded by `_fold_bare_sessions`; a tier is
`vault_evidence.tier`; independence is `chronicle_retro.witnesses`; the vault verdict is `vault_retro.gate`, the
chronicle verdict `chronicle_retro.gate_verdict`.

**Unknown is never 0.** Every side of every record is one of three things: a measurement, `None` with its reason in
`unknown[]`, or absent because the thing genuinely does not apply. A store that cannot be read never reads as empty.

---

## 2. The per-session EXTRACTION RECORD (shipped) — `GET /api/ledger3/session?id=<sid | reel_sid>`

What one reel/session yielded, joined across every store that knows it. Either spelling of the id opens the same
record.

```
{
  ok: true, v: 1,
  session: "s_…", reel: "reel_s_…",
  door: "shadow"|"live"|null, ver: "vNNNN"|null, span: {t0, t1}|null,
  journal: {                                  // the live reader's own rows for this reel, or null (UNKNOWN)
    rows, lanes: {deep, ocr, verify, skip, kai, intake, deep-owed, system, …},
    reads: {answered, owed, lost},            // lost = a deep-owed frame no deep row ever answered
    readers: {"grok-subscription-cli": n, "ocr-mac": n, "lane:verify": n, …},   // WHO read it
    intakeShots, registered, door, ver, span },
  readers: <journal.readers>|null,
  film:    {frames, onShelf, sealed, why, released?}   // the shelf (+ what the passes took), or the LAST pass's account, or UNKNOWN with why
  station: {current, hops, why}               // river_stamp's own history; hops null = stamps unreadable
  survey:  {panels, frames, full, ts}|null    // retro_triage; null with a why in `unknown` when unreadable
  tombstone: {reel, session, mb, pages, frames, why, deletedTs, kept?}|null,   // the LATEST act (reel_custody's rule)
  releases: {n, lastTs, released, kept}|null,   // every pass counted; `released` null when a pass nobody counted
  items: [ {                                  // ONE ROW PER NAME, the union of the three stores
    key, name,
    journal: { reads, frames[], firstTs, lastTs, lanes[], readBy[],   // who read THIS name
               loc: "stash"|"inventory"|"equipped"|…|null,             // WHERE it was seen (names_loc)
               tag, confirmed, provisional,                            // a verify second look; OCR-only
               routed: {vault|unvault|farmed|pending|thrown: true},    // how the reader routed it
               registered: {tier, loc, frameId} }|null,
    chronicle: { ledger: "uniques"|"sets", sightings, frames[], lanes[],  // banked from THIS reel
                 witnessTags[], independentReels, hand }|null,           // over ALL its sightings
    vault:     { lane, kind, witnessesHere, visitsHere, sawItHere, frames[],   // THIS visit
                 tier: {tier, bound, successes, trials, why}, retro }|null    // the item today
  } … ],
  yield: {named, provisional, registered, chronicle, vault, routedVault, thrown, pending, confirmed},
  evidenceFrames: {journal, chronicle, vault},
  agreement: {both[], journalOnly[], vaultOnly[], why}|null,    // reader vs vault sweep, side by side
  knownBy: ["journal","chronicle","vault","shelf","tombstone","river","survey"],
  unknown: ["…why a side is UNKNOWN…"]
}
```

Rules the law pins (`tv/test_a_session_says_what_it_yielded.py`):
- **who read it** is the model that answered, else `lane:<lane>`; measured off read rows (`deep`, `ocr`, `verify`).
- **a provisional name** (every read of it OCR-provisional) is listed apart and never counted as named — measured:
  *"Your Gamlng Rlg Is Readyl"* ×4 rides his journal as `names`.
- **one reel once**, whichever way it was spelled; the same sighting under both spellings is one row.
- **a visit, never a frame** (§34.2): one still screen held for 12 frames is one visit here and in the tier.
- **the agreement** is two engines (the live deep reader → journal; `vault_retro`'s sweep → witnesses) shown side by
  side, never averaged; provisional names are left out and the count of them is said.
- **a session no store knows** is `ok:false` with a why; **an unreadable side** is `None` with its sentence.

`GET /api/ledger3/sessions?limit=` lists every journalled session newest first as cheap journal-only rows
(`readers`, `named`, `provisional`, `registered`, `intakeShots`, `routedVault`, `thrown`, `reads`), with `total`
beside `shown`. Measured: 0.04 s over 365 sessions; one record 10–24 ms.

**Heart.** Doctor row `ledger3 sessions` (PERIODIC, 0.40 s measured over 32 shelf reels): MISSING names each sealed
reel on the shelf with no journal rows — the ring rotates by size, the shelf drains by count, so footage he still
has can lose its trail; UNKNOWN when the ring or the shelf cannot be read; OK carries the agreement census.
`corroborate.NO_JOINT_YET` says why it is one source today and what the joint would be.

**What the record cannot say yet, and who must persist it (never re-derive in the room):**
| gap | measured | the owner that should persist it |
|---|---|---|
| WHERE on the frame (cell/slot) | `cell` read by `vault_evidence._measure`, written by nothing; 0 of 10,318 chronicle sightings carry `loc` | #55 P2 pixel spots write `cell`; `_stamp_sighting_locs` at merge |
| the CHARACTER | no store stamps it | #54 / #55 P1 save truth |
| which TALLY moved ±1 for a name | `d2r_tvdTallyLog` holds `sid\|frameId\|kind:key\|±` and trims at 2000 against its own "forever" | the board writes an untrimmed per-name tick receipt |
| what a RELEASED reel routed | tombstones list no names (a frame-level pass lists what it `kept`, never what it routed) | an append-only `reel_routes.jsonl` written at seal (§8 P2) |
| a test id on a session | 0 journal keys tie a session to a scenario | `test_runs.jsonl` (§6) |

---

## 3. The four views and the FIXES strip — the room (§34.1)

📒 LEDGER is one overlay (the shelf's `th-shelfov` pattern), no 10th header tab (the strip uses 526 of 543 px at
900). Doors: a 📒 button beside 📚 in the Theatre rail; *open in 📒* on the Vault tab's routing-ledger header; the old
📒 text box (`_ledgerView`) and the 🩹 repair button route into it. Deep links `#ledger/session/<reel>`,
`#ledger/item/<name>`, `#ledger/test/<id>`. A top line: tier census · book-vs-board count · pictures gone · open
fixes — each UNKNOWN when unreadable, never 0. One frame viewer: `_tvdOpenFrame` plus the pager `_vaultEvidenceStep`
(0 callers today), never a sixth viewer. Two sources disagreeing are shown side by side, never averaged.

### 3.1 SESSION (the trail) — reads §2
One reel drawn as a river: `READ <frames> ▶ NAMED <n> ▶ REGISTERED <n> ▶ ROUTED <n> ▶ BANKED <chronicle+vault>`, each
stage clickable to list its rows (e.g. *read but never registered* = journal names with no `registered` and no
chronicle/vault side). Each name row: seen ×n · readBy · loc · route pill (`_CH_PILL_MAP` vocabulary) · chronicle
sightings/independent reels · vault visits/tier (+ `retro:` flag) · a frame thumb opening the one viewer.
Provisional names fold under one *OCR saw N things* line. The shelf card gets a *📒 what it yielded* door keyed by
reel id + frameId (never `_tvdJumpFind`'s ordinal).

### 3.2 ITEM (the proof card) — §4
### 3.3 COUNT (did it count correctly?) — §5
### 3.4 SCENARIO (his pinpointed tests) — §6
### 3.5 FIXES (surgical retro) — §7

---

## 4. The per-item PROOF CARD — `GET /api/ledger3/item?name=` (planned, P1)

Backbone: `trace_spine.spine(name)` (reel → ledger → routing → endpoint, with `independence()`), exposed read-only;
`evidence_for` for the chronicle side (after P0: `witnesses` from `chronicle_retro.witnesses`, reels deduped by
`_reel_key`, `hand` counted apart); `vault_evidence._measure` + `tier` + `_retro_row` for the vault side.

```
{
  name, key, ledger: "uniques"|"sets"|null,
  tier:   {tier, bound, successes, trials, why},        // vault_evidence.tier over VISITS
  frames: {successes, trials},                          // the old per-frame count, BESIDE, never instead
  retro:  "retro: WATCHED"|null, keepFiled,             // §34.2
  owes:   {visits, why},                                // self_arming._hardening_gap pattern: what it still owes
  passes: [ {tier, at, session, by} … ],                // P3: tier crossings, appended when a merge changes a tier
  looks:  [ {session, visit, frame, conf, lane, cell|null, char|null, released, vetoed} … ],   // every look, pageable
  where:  {surface, cell|UNKNOWN, char|UNKNOWN},        // #55 supplies cell and char; UNKNOWN until then
  book:   {sightings, rows, independentReels, lanes[], witnessTags[], foundAt, droppedBy, hand},   // chronicle
  vault:  {witnesses, visits, sessions[], lane, kind, gate: vault_retro.gate(...) verdict + why},
  chronicle: {verdict: chronicle_retro.gate_verdict(...), contested, denied, shadow: shadow_ledger split},
  provenance: "hand"|"d2s"|"witnessed"|"NO WITNESS",    // ONE vocabulary (bible.html has two today)
  board:  {owned, filed: {mule, tier, by}, ticked, unticked},   // read through the board's door only
  contradictions: [ {side_a, side_b, what} … ],         // shown in two columns, never resolved here
  unknown: [...]
}
```
Doors into it: the ◉ receipt (bible.html), the vault tile evidence button, the chronicle name cell, the Theatre name
chips, and every name row of §3.1. Heart `ledger.item`: the doctor counts cited pictures that are gone
(`vault_evidence.picture_losses`, dated by tombstone — BASELINE before the keep, MISSING after); the corroborator is
`/api/evidence`'s independent-reel count against `trace_spine.independence` on the same rows.

---

## 5. COUNT CHECK — `GET /api/ledger3/count?ledger=` (planned, P3)

A name-by-name join of the chronicle book against the board's tally, three columns: *in the book, not ticked* (with
why: un-tick ✋ by his ruling, held at 1 look, contested), *ticked with no evidence* (✋ hand or NO WITNESS), *in both*.
Runes, gems and materials show every ± with its frame from the per-name tick receipt (P3 store, untrimmed). Heart
`ledger.count`: `board_tally.json`'s aggregate against the join; every Δ explained or listed; UNKNOWN without the board.
Nothing here re-derives a count — uniques are counted against the in-page roster and only the board may state that.

---

## 6. SCENARIO view — his pinpointed tests (planned, P4)

1. Pick a `TESTING_PHASE.md` id. 2. ▶ START appends `{id, startedAt, pc, reel, baseline:{uniques, sets, runewords,
owned, unsure}}` to a per-PC, gitignored `tv/test_runs.jsonl` (the baselines the setups ask him to write by hand).
3. The screen lists every §2 record and every §3.1 row with `ts ≥ startedAt` beside the scenario's ✅ Expect / ❌ Fail
prose and the actual deltas. 4. His ✅/❌/❓ appends `{id, verdict, at, frames[]}` — and, per §34.4, ticks the index
row of `TESTING_PHASE.md` with only the id, the verdict and the date (a public file: never a character, path or id).
Heart `ledger.test`: a run started with no verdict after 24 h reads STOPPED; UNKNOWN when the run store cannot be read.
The code key is `testRun` (the word *scenario* already means PANEL/FLOOR/CHRONICLE in `extract_gap`).

---

## 7. SURGICAL RETRO FIXES — plan, apply, journal (planned, P5)

Three actions from any trail row or proof-card look, each in three steps, and the evidence stores are never edited:

| action | PLAN (read-only, says what would change) | APPLY (a board door, never the console) | JOURNAL row |
|---|---|---|---|
| ↺ re-route (found→vault, vault→dismissed, locker A→B) | `POST /api/ledger3/fix/plan` → `{name, from, to, would:{stores, tallies}, frame}` | `window.vaultFile` / `chronicleApply` / the inbox Chronicle\|Vault\|ignore door — the same doors his hand uses, so the fix inherits their rules (adds-only, witnessed, undoable) | `{n, at, kind:"reroute", name, from, to, frame, plan, receipt}` |
| ✕ veto a misread look (§34.3) | which item and tier the veto would change | the board records the veto | `{kind:"veto", name, session, frame, readAs, by:"him"}` — an OVERLAY read by `vault_evidence._measure` / `gate` at scoring time: the look drops out of the count, never a miss, and the ledger row stays as written |
| ↩ undo | the reversing plan | the same door, reversed | a NEW row `{kind:"undo", of: n}` — undo appends, never deletes |

The journal is an append-only, per-PC, gitignored `tv/ledger_fixes.jsonl`; every row carries the frame as proof and
the board's receipt. Heart `ledger.fixes`: a fix whose receipt never returned reads STOPPED; the corroborator is the
journal against `d2r_vaultProv` / `foundLog` through the board's read door; red-proof: an apply that bypasses the
board door must be refused. The RETRO PLAN (`vault_evidence.retro_plan`, shipped P0) lists items filed above what
their visits earn, kept filed by §34.2, for review here.

---

## 8. Phases and what each must bring (one law + red-proofs + `Gate why=` + doctor row + corroborate entry + engine_index entry, every ship)

| phase | builds | store it needs | heart |
|---|---|---|---|
| **P0** (v3522, shipped) | visits not frames; retro flags kept filed; `evidence_for` witnesses + reel dedup; board_tally drop episodes; hand ticks as witnesses | — | doctor `evidence tiers`; corroborate `a-tier-stands-on-its-looks` |
| **P1a** (this slice, shipped) | the per-session record + its two doors + the lost-trail row | — | doctor `ledger3 sessions` (PERIODIC); `NO_JOINT_YET` |
| **P1b** | `/api/ledger3/item` on `trace_spine`; the 📒 room with SESSION + ITEM; the one viewer's prev/next; the doors listed in §4 | — | `ledger.item`: pictures gone (dated), evidence count vs independent reels |
| **P2** | `reel_routes.jsonl` written at seal `{reel, name, frameKey, routedTo, why, gate}`; the funnel clickable; shelf card door by reel id + frameId | new, owner: the sealer | `ledger.session` corroborator: trail names vs `river_stamp`'s count; watchdog: a sealed reel with no route receipt |
| **P3** | item tier-crossing log (appended when a merge changes a tier); per-name tick receipts on the board (untrimmed); COUNT view | new, owners: `vault_retro` merge; the board | `ledger.count`: every Δ explained or listed |
| **P4** | `test_runs.jsonl`, START with auto-baselines, verdict buttons, `TESTING_PHASE.md` tick (id/verdict/date only) | new, per PC, gitignored | `ledger.test`: open runs with no verdict |
| **P5** | `ledger_fixes.jsonl`, plan/apply through board doors, the veto overlay read by `tier()`/`gate()`, undo as a new row, RETRO PLAN review | new, per PC, gitignored | `ledger.fixes`: no receipt = STOPPED; red-proof: a bypass is refused |

Order across the flagships: #53 evidence route → P0 → **P1a** → P1b → #54/#55 save truth (character) → P2 → #55 pixel
spots (cell) → P3 → P4 (depends only on P2, can move earlier for hand tests) → P5 → #39 Roster/Fleet 3.0 last (§32:
no mirror; only honest per-PC tiers leave a machine).

---

## 9. Blueprint and heart integration (how the generated maps come to name it)

`BLUEPRINT.md` is generated: ENGINE from `tv/engine_index.json` (this slice adds `ledger3.py`, territory
`ledger-profile`, entry points spelling the routes), GATES from `run_gates.GATES` (`test_a_session_says_what_it_yielded`),
LANES from `control_app` loops (none added — the record is on demand, the row is the eagle's). `HEART.md` counts
`id="…"` in `control_ui.html` watched by a doctor row — the 📒 room's ids (`lg-room`, `lg-top`, `lg-session`,
`lg-item`, `lg-count`, `lg-test`, `lg-fixes`) arrive with P1b and are named by their rows in `console_doctor.CHECKS`,
then `heart_map --bless` raises the floor. Each new store (P2–P5) is declared in `store_owners.STORES` with its owner
and every reader's reason, and in `.gitignore`. `bump_version.py` regenerates both maps on the ship.
