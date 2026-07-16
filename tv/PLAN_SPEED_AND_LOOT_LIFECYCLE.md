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

### v729 — SHIPPED (Grok)
- `LootLifecycle` in `tv/tv_diablo.py`: baseline · seen · gone-candidate (1-miss grace) · confirm
- Read fields: `farmed_names`, `lifecycle_tags`, `anchor`, `gone_candidates`
- Board auto-apply uses **only** `farmed_names` (baseline/anchors excluded)
- Unit tests: `TestLootLifecycleV2` (6 cases) · suite 30/30
- Run #4 live-verify: empty inv baseline → pile SEEN → gone candidate → inv CONFIRM → vault

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

## SPEED v2 — THE OCR FAST LANE (Konyo's target: reads in 0.5–1s · 2026-07-16)

Physics first: an LLM vision round-trip (even warm Sonnet) floors at ~3–6s inference — no
tuning reaches sub-second. The architecture that DOES:

**Two lanes per settled frame:**
1. **FAST (0.2–0.5s, local, free)** — macOS Vision framework OCR on the frame (on-device,
   no network, no cost; Windows: WinRT OCR). Extracted strings → the bible's OWN vocab
   matchers (same fuzzy logic as intake) → instant chips. Labels/tooltips ARE text — OCR
   is the right tool for names.
2. **DEEP (3–8s, Claude, subscription)** — the existing read: scene · area · tz ·
   verification. Confirms/enriches/corrects the fast lane; resolves what OCR garbles.

Feed semantics: fast-lane chips land ~instantly marked `⚡ocr`, the deep read upgrades them
(`✓ confirmed` / corrections). Honesty holds: OCR-only names stay review-first until the
deep read or the lifecycle chain confirms.

Implementation sketch (mac): a tiny Swift/`osascript` helper or `shortcuts` invoking
VNRecognizeTextRequest on read.jpg → JSON strings; agent merges. Zero new deps beyond an
OS the player already has.

Owner: Grok codes · Fable gates · target = pile-to-chip FEELS instant on run #5.

### Shipped v732 (Grok) — tuned harder than 0.5–1s
- Warm single-ROI Vision OCR **~10–50ms** (not 0.5s — we pushed the fast lane lower).
- Persistent `tv/bin/ocr_mac --worker` · board poll **250ms** · ⚡ocr chips review-first.
- Claude remains deep lane (3–8s) for scene/area/confirm + commitment vault.
- True 1ms end-to-end is not reachable (capture + poll + OCR still ~50–200ms wall);
  the *feel* is instant once the pile freezes.

---

## STASH-TAB AUTO-INTAKE (Konyo's design, 2026-07-17 — "give the photo to the system already perfected")

The RotW stash has tabs: Personal · Shared · Gems · Materials · Runes. When TV-D sees the
stash open (inventory auto-opens on the right — a strong stash tell) AND identifies WHICH
tab is active on the left, the frame itself is handed to the LOCKED intake pipeline — the
same Sonnet crop/tally system that already reads these exact screenshots 33/33.

**Surgical wiring — reuse, never rebuild (the intake stays LOCKED, we only FEED it):**
1. **Agent**: deep-read prompt extends scene detection — when scene=stash, also report
   `stashTab: personal|shared|gems|materials|runes|""` (the active tab header is legible —
   proven in Konyo's video #1).
2. **Receiver**: read arrives with scene=stash + stashTab∈{runes,gems,materials} →
   fetch the frame from the agent's existing `GET /frame` → Blob → File → feed the SAME
   function the 📸 quick-upload file-picker uses (kind: rune/gem/material). The tally lands
   exactly as if Konyo uploaded it by hand — crops, layouts, verify-flags, all the locked
   machinery untouched.
3. **Guards**: once per stash-visit per tab (debounce — don't re-tally the same stand-still);
   review-report shown as always (the intake's own report UI); never fires from OCR lane
   (deep-read scene only); personal/shared tabs = normal item flow, NOT tally intake.

Owner: Grok codes · Fable gates · Konyo verifies by literally standing in front of his rune
stash on the next run.
