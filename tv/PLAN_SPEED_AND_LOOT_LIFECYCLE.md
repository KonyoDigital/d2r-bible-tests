# TV-KAI — Speed + loot lifecycle (post restore-point)

**Restore freeze:** `restore-point-pre-tv-speed-loot-lifecycle-2026-07-16_201534`  
**Do not start code until that tag + hardcopy exist (they do).**

## Goals

1. **Super-fast in-game reads** — pause-on-pile should feel instant, not “wait a beat.”
2. **Know what / when / why** — every read is tagged with intent:
   - `floor` — labels on ground (seen, not yet farmed)
   - `inventory` / `stash` — on character / in stash (farmed / registered)
   - `hover` — tooltip only (identity, not ownership yet)
   - `gameplay` / `town` — context only
3. **Farming truth** — floor @ 20:01 without pickup ≠ farmed.  
   Same name later in inv/stash = **looted / farmed for real**.
4. **Vault manager later** — farmed events are the feed that eventually posts into vault/chronicle apply (review-first stays).

## Speed levers (subscription, not API key)

| Lever | Current (v722) | Target |
|-------|----------------|--------|
| Model | sonnet | **haiku default** for vision; sonnet opt-in via `TV_MODEL` |
| MIN_GAP | 8s | 4–6s if haiku holds quality |
| POLL eyes | 0.25s | keep (or 0.2s) |
| Worker | warm stream-json | keep; haiku cold start should be snappier |
| Prompt | long 4-field | **scene-gated short prompts** (floor vs inv vs stash) |

**Cost note:** Haiku on Max/Pro subscription is almost always the right default for high-frequency screen reads. Sonnet only when a read is ambiguous or user forces `TV_MODEL=sonnet`.

Auth path stays **subscription only** (`_claude_env` strips API keys).

## Loot lifecycle state machine

```
  [floor labels]  --seen-->  SEEN(floor, ts, names[], area)
        | pickup (player)
        v
  [inventory/stash panel] --confirm-->  FARMED(from SEEN or new, ts, names[], where)
        |
        v
  [session feed] --> optional vault/chronicle apply (later, review-first)
```

### Rules
- Floor read **never** auto-increments grail/farm counters.
- Inventory/stash read **can** mark farmed (still review-first on bible apply).
- Dedupe: same name floor→inv within session = one farm event with `seen_at` + `farmed_at`.
- Timeout: SEEN floor items age out of “pending pickup” after N minutes (config).

## Implementation slices

1. **v723 — DONE** · Haiku default + Sonnet genius escalate · intent seen/farmed ·
   `seen[]`/`farmed[]` in state · board auto-apply farmed only · `tvVaultRegister` thin vault wire  
2. **v724 — next** · scene-gated shorter prompts (floor vs panel) for more speed  
3. **v725 — later** · vault journal “TV farmed @ time” line items  
4. **later** · richer vault manager UX for TV source (not required for file path)  

## Success metrics
- Warm read p50 **&lt; 4s** on haiku (stretch &lt; 2.5s)
- Floor pile → chip visible **&lt; 8s** wall clock including settle
- Zero false farm from floor-only reads
- Subscription auth only (no API key burn)

---

## LOOT LIFECYCLE v2 — OBJECT PERMANENCE (Konyo's design, 2026-07-16 run #3 debrief)

> "when its suddenly not on the floor anymore it knows that its maybe in the inventory —
> and especially after it sees it there and READS it, that's where the small wire routes it
> to the vault and gets automatically tallied and muled/thrown out. it just goes into the
> system smoothly."

The correlation layer (no new machinery — rides existing reads + tvVaultRegister):

1. **BASELINE** — the first inventory/stash read of a session snapshots the known-items set.
   Items in the baseline NEVER re-tally (his pre-run inventory was empty = clean baseline).
2. **SEEN ledger** — every floor (`loot`) read records `{name → area, firstSeen, lastSeen, count}`.
3. **GONE detection** — a later loot read in the SAME area that no longer contains a
   previously-seen name marks it `candidate: picked-up` (1-read grace for label flicker).
4. **CONFIRM** — the next inventory/stash read containing that name (and not in baseline)
   = CONFIRMED farmed → the existing v723 wire fires: engines tally + tvVaultRegister
   (mule / throwout). Confidence tag: `seen→gone→inventory` = the strongest intent signal.
5. **HONESTY RULES** — GONE alone NEVER auto-applies (he may have walked away / despawn).
   Inventory-read alone still works (v723 behavior) — the lifecycle only UPGRADES confidence.
6. **ANCHOR LANDMARKS** — the Horadric Cube / TP tome / ID tome hold fixed inventory slots.
   Locate them per inventory read: anchors legible = high-confidence read; anchors missing
   or garbled = low confidence → escalate model / hold auto-apply for that read.

Run #3 evidence this builds on: pre-run empty inventory · 3 items picked (2 tossed) · town →
stash scenario at session end — the full arc is in the session history for replay-testing.

Owner: Grok codes · Fable gates · Konyo live-verifies (run #4).

---

## LOOT LIFECYCLE v2 — OBJECT PERMANENCE (Konyo's design, 2026-07-16 run #3 debrief)

> "when its suddenly not on the floor anymore it knows that its maybe in the inventory —
> and especially after it sees it there and READS it, that's where the small wire routes it
> to the vault and gets automatically tallied and muled/thrown out. it just goes into the
> system smoothly."

The correlation layer (no new machinery — rides existing reads + tvVaultRegister):

1. **BASELINE** — the first inventory/stash read of a session snapshots the known-items set.
   Items in the baseline NEVER re-tally (his pre-run inventory was empty = clean baseline).
2. **SEEN ledger** — every floor (`loot`) read records `{name → area, firstSeen, lastSeen, count}`.
3. **GONE detection** — a later loot read in the SAME area that no longer contains a
   previously-seen name marks it `candidate: picked-up` (1-read grace for label flicker).
4. **CONFIRM** — the next inventory/stash read containing that name (and not in baseline)
   = CONFIRMED farmed → the existing v723 wire fires: engines tally + tvVaultRegister
   (mule / throwout). Confidence tag: `seen→gone→inventory` = the strongest intent signal.
5. **HONESTY RULES** — GONE alone NEVER auto-applies (he may have walked away / despawn).
   Inventory-read alone still works (v723 behavior) — the lifecycle only UPGRADES confidence.
6. **ANCHOR LANDMARKS** — the Horadric Cube / TP tome / ID tome hold fixed inventory slots.
   Locate them per inventory read: anchors legible = high-confidence read; anchors missing
   or garbled = low confidence → escalate model / hold auto-apply for that read.

Run #3 evidence this builds on: pre-run empty inventory · 3 items picked (2 tossed) · town →
stash scenario at session end — the full arc is in the session history for replay-testing.

Owner: Grok codes · Fable gates · Konyo live-verifies (run #4).
