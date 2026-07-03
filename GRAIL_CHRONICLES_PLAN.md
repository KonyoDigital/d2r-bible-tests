# Grail Chronicles — Architecture Plan
_Uniques + Sets as first-class Chronicles, parallel to Runewords. PLAN ONLY — no build until Konyo says go (runewords → 100% first)._

## Goal
Three **independent** Chronicles off **one generic engine**:

| Pillar | Store (new/existing) | Total | Your seed |
|---|---|---|---|
| Runewords | `d2r_rwMade` (exists) | 100 | 45 |
| **Uniques** | `d2r_uniMade` (new) | ~396 | ~77% (migrated once) |
| **Sets** | `d2r_setMade` (new) | ~136 | your mix (migrated once) |

Konyo's confirmed shape: *separate Chronicle, own logic, same dashboard, no clash, each resets/seeds/plans on its own.*

## The framing (Konyo, refined): THREE FORGES, one shell
Not three trackers — **three Forges**, each a full task dashboard sharing the **v552 flagship Forge shell** (the
"👉 Do this one thing" hero + KPI tiles + progress meter + HD-art task cards), with its own progress meter and its
own **task-generation logic**:

| Forge | Task kind | Fed by | Progress meter |
|---|---|---|---|
| **Forge · Runewords** (current) | MAKE (socket / cube-gamble / forge) | rune stash + owned bases + `d2r_rwMade` | N/100 |
| **Forge · Uniques** | FARM (go kill X / run area Y) | missing uniques → drop sources | found/~396 |
| **Forge · Sets** | FARM | missing set pieces → drop sources | found/~136 |

Same look + feel; the **coding of the tasks changes to be relevant** — runewords = "make it", uniques/sets = "farm
it here". Each meter is **separate + individual** (three independent progress bars, three resets).

## Nav (recommendation)
Keep ONE **Forge** tab; add a **pillar switcher** at the top — `Runewords · Uniques · Sets` chips. Selecting a pillar
swaps the hero + tiles + meter + task list to that Forge. One nav entry, three Forges. (Konyo's "Forge Uniques /
Forge Sets" titles become the switcher labels — shorter than "…Chronicle".)

## The generic engine — `makeForge(spec)`
A factory. The **shell is shared** (hero / tiles / progress meter / cards / reset — the existing v552 render, generalized);
only the **task-generation `scan(spec)`** differs per pillar. Given a spec it returns a self-contained Forge:
- **data**: `items` list, `total`, `storeKey`, `seed`, `fresh`-profile flag (per-pillar reset — multi-player)
- **scan**: pillar-specific → produces the task list the shared shell renders
  - runewords `scan` = the current `forgeScan` (make/pipeline/onestep/crafts)
  - uniques/sets `scan` = **missing items grouped by drop SOURCE**, low-level-first
- **hooks**: `onToggle` → re-render + refresh create-now + AI snapshot
- **hero**: the "do this one thing" — top MAKE task (runewords) or top FARM target (uniques/sets)

### Pillar specs
```
runewords: { key:'d2r_rwMade',  items:RUNEWORD_TIP, total:100,  scan:forgeScan,   kind:'make' }
uniques  : { key:'d2r_uniMade', items:ITEMS(unique),total:~396, scan:farmScan,    kind:'farm', seedFrom:'d2r_owned' }
sets     : { key:'d2r_setMade',  items:SETS,         total:~136, scan:farmScan,    kind:'farm', seedFrom:'setPieces' }
```
`farmScan(missing)` = for each unowned item → its best drop source (`ITEMS[].sources` + `navigateToItem`), grouped by
source, sorted low-qlvl-first → task cards like "Run **Normal Countess** → these 4 low uniques you're missing".

## Data model
- `d2r_rwMade` / `d2r_uniMade` / `d2r_setMade` — each `{ itemName: dateOrFlag }`.
- Per-pillar fresh flag — `d2r_rwProfile` / `d2r_uniProfile` / `d2r_setProfile` = `'fresh'` suppresses that pillar's seed (multi-player: **cousin = 3 empty Chronicles**, each resettable on its own).
- **One-time migration** (on first build, unless fresh): seed `d2r_uniMade` from `d2r_owned` ∩ uniques, `d2r_setMade` from `setPieces`. So **Konyo's 77% carries over**, then lives as its own Chronicle.

## Why NOT just reuse the old grail (`d2r_owned`)
It's a flat owned-Set, not a seedable/resettable per-pillar Chronicle. Making Uniques/Sets real Chronicles gives each person + each pillar independent reset/seed/track — same as runewords now. The Calculator ✓ can stay as an *input* that syncs into the Uniques Chronicle (both write the same made-map).

## Dashboard UX (recommendation)
Keep the existing Chronicle card, add a **pillar switcher** (Runewords · Uniques · Sets chips) at its top → one card, three views, identical look. (Alt: 3 separate Tools cards — decide at build time.)

## Planner integration (the payoff)
- Runewords → **make** targets (rune stash) — exists.
- Uniques/Sets → **farm** targets: missing items grouped by **drop SOURCE** (boss/area/TZ), **low-level-first** (Konyo's gap = low uniques he skipped). Reuse `ITEMS[].sources` + `navigateToItem`.
- "Do this one thing" hero + AI snapshot: once runewords are done, name the highest-value **missing grail item + where to farm it**. (v555.5 already falls through to "items/crafts" when no runeword is makeable — extend that to name a real farm target.)
- Cross-pillar priority: **runewords > uniques/sets** (by achievability), auto-shifting as each pillar completes.

## Sync map — each Forge ↔ the bible (single source of truth per pillar)
The pillar's made-map is the ONE source of truth; every relevant surface reads/writes it, so a tick anywhere syncs
everywhere (exactly like the runeword Chronicle ↔ Forge ↔ create-now sync already works, v555).

- **Forge · Runewords** ⇄ Rune Stash · Gem Stash · Vault (owned bases) · Chronicle (`d2r_rwMade`) · create-now
  dashboard · Top Picks · AI snapshot. _[exists — live]_
- **Forge · Uniques** ⇄ `d2r_uniMade` **⇄ `d2r_owned`** (the Calculator ✓ **and** the Main "Grail Progress" widget
  read/write the SAME found-set — mark a unique found in the Calculator and it drops off the Uniques Forge, and
  vice-versa) · Bosses / Calculator / TZ data (the drop SOURCES that build the farm tasks) · AI snapshot
  (`snap.grail.uniques`). _[new]_
- **Forge · Sets** ⇄ `d2r_setMade` **⇄ `setPieces`** (the set tracker + Calculator sets) · sources · AI snapshot
  (`snap.grail.sets`). _[new]_

**Rule:** never a second copy of "what I own" — the Uniques/Sets Forges bind to the SAME owned-state the Calculator +
Grail widget use (bridged into the made-map), so the whole bible stays one coherent picture. Backup & Share already
serialises all LS keys, so the new stores ride along automatically.

## No-clash guarantees
Purely additive: new stores, new render fns, new snapshot fields. The ONE touch to existing code = refactoring the Runeword Chronicle's internals into `makeChronicle` — it must behave **identically**, locked by the current specs (v369, v549, v555). Everything else is new instances.

## Build phases (when runewords ~done)
1. Extract `makeChronicle(spec)` from the runeword Chronicle — invisible refactor, all Chronicle/create-now specs stay green.
2. Uniques Chronicle instance + one-time migration from `d2r_owned` + its view + reset.
3. Sets Chronicle instance (+ migration from `setPieces`). Decide per-piece vs per-set-complete.
4. Farm-planner for missing uniques/sets (by source, low-level-first) → Smart Insights "🏆 Grail radar" + the hero pick.
5. AI snapshot `snap.grail` + prompt awareness (the AI answers "what am I missing / where do I farm it").

## Open questions (decide at build time)
- One Chronicle card w/ a pillar switcher, or 3 separate cards?
- Uniques input: Calculator ✓ only, or tickable in the Chronicle too (both sync the same map)?
- Sets: track per-PIECE or per-completed-SET?
- Migration: seed the full 77% at once, or let Konyo re-verify via a fresh intake?
