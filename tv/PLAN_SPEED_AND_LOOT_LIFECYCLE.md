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
