# 🎞 THE SIMULATION — Product Spec (Konyo's words, structured)
_v831 baseline · 2026-07-18 · the north star for the next ~50 versions. ON AIR work is FROZEN
until SIMULATION is perfect. Owner's phrasing preserved; structure added for Grok (3rd eye)
and Kimi 3 (possible 4th eye)._

## The one-sentence mission
> "I need to know exactly what the thought process was for the AI — every single analyzed
> thing it did or thought of. The Simulation is my EYES, visually, for the coding behind it
> all — so we can go back in simulation mode and literally surgically fix what the AI is
> reading ON AIR, once we understand what it was reading, in past tense."

**SIMULATION = the visual debugger of the AI's mind.** Not a highlight reel, not a viewer —
an instrument. If the AI mis-reads a stash panel ON AIR, the owner must be able to find that
exact moment in SIM, open it, and SEE why — then we fix the code.

## The contract, surface by surface

### 1. Session picker (click SIMULATION)
- Every previous REAL run, perfectly accurate, paginated per session (one ON AIR = one reel).
- Perfect cross-reference: session wall-clock span, read count, footage seconds, sessionId.

### 2. The film (per-frame screen)
- Time-span cross-referenced: every frame stamped with capture wall-clock (ms precision) and
  session-relative T+ — the exact moment while ON AIR.
- Playback modes: 🎬 CUT (story) · 📼 FULL (compressed) · ⏱ REAL (theatre-ms == wall-ms:
  the reel runs the session's literal duration; with v826 footage = real video).
- ON the frame: AI data "clearer and visually short and to the point — even keywords."
  The read line (📸 CAPTURE / 🧠 AI READ / 📖 IT SAW / ⚡ OCR) is close; polish toward
  keyword-density, never a debug dump.

### 3. The `I` drawer (in-depth EVERYTHING)
> "every single thing thought, even, or relevant to the thought, at the time of the AI reads"
Must render, per read:
- **THE DISPATCH** — why THIS frame was read at all: motion value, settle ticks, interest
  score and its components, priority state, gap timers, queue/drain origin (settle-queue?).
- **THE THOUGHT** — the model's RAW response text (what it literally said), the parse
  outcome (which fields survived, which were dropped/normalized and why), model + latency.
- **THE DECISION CHAIN** — per item name: location (equipped/inventory/stash/floor), the
  lifecycle verdict AND ITS REASON (seen-because-floor-label · held-because-inventory ·
  vaulted-because-stash-with-chain · blocked-because-no-chain · skipped-because-equipped ·
  already-owned), and what was sent to the board (vault/chronicle/nothing).
- **THE LANES** — OCR raw lines vs filtered names vs deep names vs confirmed, with both clocks.

### 4. Accuracy doctrine
- Everything timestamped to the millisecond of capture, cross-referenced to the frame file.
- No invented data: if a field wasn't captured for an old session, the drawer says
  "not recorded before vNNN" — never blank, never fake.

## Gap analysis (v831 → the mission)
| Have | Missing |
|------|---------|
| parsed outputs (names/scene/area/conf/loc), both clocks, lanes, lifecycle TAGS, footage, REAL mode | the RAW model text · the dispatch context (motion/interest/priority at fire time) · lifecycle REASONS (tags say what, not why) · parse-drop audit · prompt identity (which prompt version read this frame) |

**Root implication: the agent must JOURNAL THE BRAIN, not just the verdicts.** Every read row
gains: `raw` (model text, truncated ~2KB), `dispatch` {motion, interest, priority, settleTicks,
gapMs, origin: live|queue|farewell}, `decisions` {name: {loc, verdict, reason}}, `promptVer`.
Storage cost at ~10-40 reads/session is trivial next to frames.

## Ship arc (v832+, ~50 versions, SIMULATION ONLY)
1. **Journal the brain** — agent captures raw/dispatch/decisions/promptVer per read.
2. **Drawer: THE THOUGHT + THE DISPATCH + THE DECISION CHAIN** sections (graceful for old rows).
3. **Lifecycle reasons** — every tag gains a why (engine returns {tag, why}).
4. **On-frame keyword polish** — read line tightened per owner's "short, keywords" note.
5. **Session picker face-lift** — real picker UI (cards per session, spans, counts) replacing
   blind ⏮⏭ pagination.
6. Then: Grok rounds against THIS spec until dry — pixel polish, scrub ergonomics, footage
  density, decision-chain visualizations, cross-session search ("show me every read that
  said Harlequin"), export parity.

## Workflow
- Konyo Workflow: version-per-round, full suites + visual verify per ship, Fable gates.
- SuperGrok = standing third eye (CLI). This file is Grok's briefing — critique it, extend it.
- Kimi 3 may join as fourth eye; keep round prompts model-agnostic.

---

# Third Eye Addendum — SuperGrok · 2026-07-18 (post-v831)

_Standing instrument critique. Grounded in live `sessions.jsonl` (268 reads, tag
distribution: seen 158 · holding 8 · stash-no-chain 4 · vault:stash 1) and agent code
(`tv_diablo.py` LootLifecycle + `_journal` rec + `_parse_read` + `ap_interest`)._

## A. Gap analysis critique — what ELSE must be captured

The v831 gap table is **correct but incomplete**. It lists *verdict-side* holes
(raw / dispatch / reasons / parse-drop / promptVer). To surgically debug a mis-read from
the past, you also need **pipeline-side** and **negative-path** truth. If it isn't in the
journal, SIM cannot show it — the `I` drawer cannot invent it later.

### A1. Spec already names (keep — these are non-negotiable)

| Field | Why |
|-------|-----|
| `raw` (~2KB model text) | "IT SAW" is post-parse; mis-reads often live in the *literal* reply (markdown wrap, truncated JSON, chatter before `{`) |
| `dispatch` | Why this frame fired at all — without it every wrong read looks like a model bug when it was a settle/queue bug |
| `decisions[name] = {loc, verdict, reason}` | Tags say WHAT; reasons say WHY. Engine already *computes* reasons (`seen→stash`, `hold`, `floor-again`) then **throws them away** into a flat tag string |
| `promptVer` | Prompt text is the actual "eyes" — v730 shortened it; without version you cannot bisect "eyes got worse after vN" |

### A2. Missing from the gap table — capture these too

**1. `dispatch` must be a decomposition, not a flat score.**
Journal already has `interest: 1.0` and `priority: true` on many rows — useless for forensics
because almost every real fire is 1.0. Need the *inputs* that made the score:

```json
"dispatch": {
  "origin": "live|queue|farewell",
  "motion": 0.12,
  "peak": 0.41,
  "stableTicks": 2,
  "settleTicks": 3,
  "interest": 0.95,
  "interestParts": {"peak": 0.45, "priority": 0.25, "stable": 0.1, "named": 0.1, "empty": -0.08},
  "priority": true,
  "gapMs": 1200,
  "emptyStreak": 0,
  "namedStreak": 2,
  "apMode": "settle",
  "queueDepth": 0,
  "frameSrc": "live|settle-queue|farewell-force"
}
```

**2. `parse` audit (not just "which fields survived").**

```json
"parse": {
  "ok": true,
  "strategy": "balanced|first-last|none",
  "rawLen": 842,
  "dropped": [
    {"field": "scene", "from": "loading", "to": "gameplay", "why": "unknown-scene-clamp"},
    {"field": "names_loc.Foo", "from": "bag", "to": null, "why": "invalid-loc"}
  ],
  "normalized": [
    {"field": "stashTab", "from": "Runes Tab", "to": "runes"}
  ],
  "truncated": {"names": false, "count": 0}
}
```

Silent clamps have already burned us (v769: `transition` was killed to `gameplay`).
Without the audit, SIM shows the *post-clamp* world as if the model said it.

**3. `pre` — name triage BEFORE lifecycle.**
Lifecycle never sees junk/anchors/never-vault the same way. Today they become tags *or*
vanish. Journal must list every name the model uttered and what the gate did:

```json
"pre": [
  {"name": "Healing Potion", "gate": "junk"},
  {"name": "Horadric Cube", "gate": "anchor"},
  {"name": "Unidentified", "gate": "never-vault"},
  {"name": "Harlequin Crest", "gate": "pass"}
]
```

**4. `chain` — provenance snapshot AT decision time (per name).**
`stash-no-chain` is the canonical mis-read class (4× in live journal). Tag alone cannot
tell you *whether the engine was right*. Need:

```json
"chain": {
  "Harlequin Crest": {
    "wasSeen": false, "wasPending": false, "wasCand": false, "wasVaulted": false,
    "heldMs": null, "firstSeenTs": null, "hasChain": false
  }
}
```

Owner question: "Did the AI never SEE it on the floor, or did the chain state get wiped?"
Answer lives here — not in the tag.

**5. `board` — what actually left the agent.**
Verdict ≠ board effect. Journal:

```json
"board": {
  "vault": ["…"],       // tvVaultRegister attempted
  "chronicle": ["…"],    // discovered / equipped tally
  "seen": ["…"],         // floor review chips
  "unvault": ["…"],
  "nothing": ["…"]       // names with zero board write + why
}
```

**6. `vision` — which image the model actually ate.**

```json
"vision": {
  "path": "frames/hist/10_….jpg",
  "bytes": 192034,
  "sig8": "a1b2c3d4",
  "wh": [1920, 1080],
  "modelPath": "…/read.jpg",   // path string inside the prompt
  "timeoutMs": 75000,
  "escalated": false,
  "escalateWhy": null,         // or "parse-none" | "low-conf" | …
  "fastModel": "haiku",
  "finalModel": "sonnet"
}
```

A mis-read of a stash panel is often "wrong crop / stale queue freeze / eye.jpg age", not
"Sonnet is dumb."

**7. `ocr` raw lane (pre-filter).**
We journal `ocr_names` (post-filter). Need `ocr_raw: string[]` (or first ~40 lines) +
`ocr_dropped: [{line, why}]` so "OCR saw Hazade / waypoint label and we correctly killed it"
is provable — and so a false kill is too.

**8. Negative events (non-reads that explain silence).**
Not every gap is a read row. Journal lightweight events (same file, `kind: "skip"`):

- vision-busy drop · settle-queue stale drop · gap-wait · parse-null · timeout ·
  capture-fail · warm-thread race · empty-honest (scene gameplay, 0 names, fired on purpose)

Without these, SIM looks like "AI went blind for 40s" when the agent was correctly waiting
or thrashing on a dead capture.

**9. `agentVer` + `promptHash` beside `promptVer`.**
`promptVer` alone drifts if two ships share a number. `agentVer` (= VERSION) + short hash of
`READ_PROMPT` freezes the eyes for that row forever.

**10. Do NOT capture (storage / privacy / noise).**
- Full multi-MB BMP blobs (hist JPEG + frameId is enough)
- Entire lifecycle maps for all names every read (per-name chain for *this* read's names only)
- Full `_EVENTS` ring (summarize origin; don't dump 60 lines into every row)
- Raw API transport frames / auth

### A3. Schema contract (implementation-ready, additive)

```json
{
  "...existing v831 fields...": true,
  "agentVer": "v832",
  "promptVer": 3,
  "promptHash": "c0ffee12",
  "raw": "{…model text…}",
  "dispatch": { },
  "parse": { },
  "pre": [ ],
  "decisions": {
    "Harlequin Crest": {
      "loc": "stash",
      "verdict": "blocked",
      "reason": "stash-no-chain",
      "why": "no floor/hold/candidate provenance this session",
      "board": "nothing",
      "chain": { "wasSeen": false, "wasPending": false, "wasCand": false, "hasChain": false }
    }
  },
  "ocr_raw": [],
  "ocr_dropped": [],
  "vision": { },
  "board": { }
}
```

**Accuracy doctrine extension:** missing keys render as
`not recorded before vNNN` (map each key → introduced version in one table in code).
Never synthesize `why` from tag heuristics for old rows — that is faking data.

**Lifecycle engine change (required for honest reasons):**
`LootLifecycle.process` returns `decisions` map; tags become a *projection* of verdict+reason
for back-compat board chips. Stop embedding reason only inside `vault:stash` strings.

---

## B. First 10 ships (concrete, ordered)

Principle: **capture before chrome.** Drawer sections without journal fields are theater.
Visual decision-chain is not "later polish" — it IS the instrument the owner asked for.

| # | Ship | Version slot | Deliverable | Gate |
|---|------|--------------|-------------|------|
| **1** | **Lifecycle returns `{tag, why, board}`** | v832 | Engine-only. Every name that touches process() gets a decision object. Tags stay string-compatible. Unit tests for: seen / holding / vault:hold / vault:stash / stash-no-chain / already-vaulted / equipped / junk / throw-out / hold-low-conf / skip-weak / gone-candidate | agent suite green; no UI yet |
| **2** | **Journal the brain (schema v2)** | v833 | Append `raw`, `dispatch` (with parts), `decisions`, `parse`, `pre`, `vision`, `promptVer`+`promptHash`+`agentVer`, `board` on every `_journal(rec)`. Cap `raw` at 2KB. Old writers untouched. Fixture: one stub read asserts all keys present | journal fixture lock; 0 regression on old rows loading |
| **3** | **Negative-path journal** | v834 | `kind:"skip"` (or `lane:"skip"`) rows for busy/queue-drop/timeout/parse-null/capture-fail. SIM film can show a dim "no eyes" tick instead of a hole | doctor integrity ignores skips for frame% OR treats as optional |
| **4** | **Drawer: THE THOUGHT + THE DISPATCH** | v835 | `I` drawer sections; graceful `not recorded before v833`. Raw in monospace collapse; dispatch as spark meters (motion/interest/parts) | visual: open a v833+ session + a pre-v833 session |
| **5** | **Drawer: THE DECISION CHAIN visual** | v836 | Per §C below — pipeline river, not a log dump. Hover chip on film reuses same component | visual: stash-no-chain row paints red break at VAULT; vault:stash paints mint full path |
| **6** | **On-frame keyword polish** | v837 | Read line → keyword density: `stash·shared · Harlequin Crest 🏦blocked · conf.9 · sonnet 21s`. Kill prose. Seals only when they add info (already half-done v824) | screenshot before/after same beat |
| **7** | **Session picker cards** | v838 | Replace ⏮⏭ blind pagination with card grid: wall span, reads, named, vaulted, footage-s, sessionId tail, "has brain journal" badge if any row has `raw` | open SIM → pick oldest / newest / empty |
| **8** | **OCR raw lane + pre-filter audit in drawer** | v839 | THE LANES section: raw lines · filtered · deep · confirmed · dropped(why). Both clocks | row with OCR garble shows drop reason |
| **9** | **Cross-session search** | v840 | "show me every read that said Harlequin" — search box over journal (name / tag / reason / scene). Results jump theatre to session+beat | 1 query, land on frame |
| **10** | **Export parity + scrub ergonomics pack** | v841 | Export JSON includes full brain fields; REAL-mode scrub stickiness; beat-density on timeline for decision severity (red ticks = blocked/throw; mint = vault); footage↔read alignment fix list from v826 residuals | export round-trip; REAL mode 1:1 within 50ms on stub |

**Ships 11–50 (parked, do not steal focus):** pixel polish, cinema density, decision-chain
session-timeline ("this name's life across the reel"), multi-name diff, prompt-diff viewer,
Kimi 4th-eye rounds, ON AIR unfreeze criteria checklist.

**Reorder notes vs original 6:**
- Lifecycle reasons **before** journal (else journal stores empty whys).
- Decision-chain **visual** pulled forward (was buried in "then Grok rounds").
- Negative-path + OCR raw + search + export made explicit — they are instrument, not polish.
- On-frame polish stays mid-arc (owner feels it early without blocking brain capture).

---

## C. THE DECISION CHAIN — visual design (implementation-ready)

### C1. Goal
Non-programmer owner opens `I` on a past frame and in **under 2 seconds** knows:
1. WHERE each name was (floor / inv / stash / equipped)
2. HOW FAR it got in the pipeline
3. WHERE it stopped (the break)
4. WHY in plain English
5. Whether the bug is **eyes** (model/OCR/scene) or **brain** (lifecycle/board)

### C2. Pipeline model (fixed stages, left → right)

```
👁 EYES → 📍 LOC → 🔗 CHAIN → ⚖ VERDICT → 📡 BOARD
```

Expanded stage chips (always same order; absent stages dim):

| Stage | Meaning | Win color |
|-------|---------|-----------|
| EYES | Model uttered this name (in `names` or `ocr`) | gold text |
| LOC | equipped / inventory / stash / floor | icon 🎽🎒🏦🧱 |
| CHAIN | provenance: seen? hold? cand? | mint if hasChain |
| VERDICT | seen · holding · vaulted · blocked · thrown · skip · owned | see C3 |
| BOARD | vault / chronicle / seen-chip / nothing | mint if write happened |

### C3. Verdict color + glyph language (match existing theatre)

| verdict | glyph | color | film tick |
|---------|-------|-------|-----------|
| vaulted | 🏦 | mint `#8fe6a0` | tall mint beat |
| holding | ⏳ | warm gold `#ffd97a` | medium gold |
| seen | 👁 | soft gold | named beat |
| blocked | ⨯ | coral `#f88` | red tick |
| thrown | 🗑 | dim red | — |
| skip / junk / anchor | — | opacity .4 | — |
| owned (already-vaulted) | ✓ | dim mint | — |
| equipped | 🎽 | blue-gray | — |

### C4. Per-name card (drawer body)

One card per name in `decisions` (fallback: synthesize shallow card from tags for old rows,
labeled `reconstructed from tag · reasons not recorded before v832`).

```
┌─ HARLEQUIN CREST ─────────────────────────────────────┐
│  LOC  🏦 stash · tab shared                           │
│                                                       │
│  EYES ──●── LOC ──●── CHAIN ──○── VERDICT ──●── BOARD │
│   ok        stash     no chain    ⨯ blocked    nothing│
│                          ▲                            │
│                     BREAK HERE                        │
│                                                       │
│  WHY  no floor / hold / candidate this session        │
│       (stash-no-chain)                                │
│                                                       │
│  DIAGNOSIS  Engine refused vault correctly.           │
│  If this drop was real: bug is UPSTREAM — floor SEEN  │
│  never fired for this name (eyes/scene/OCR), not the  │
│  vault gate.                                          │
└───────────────────────────────────────────────────────┘
```

**Rules:**
- Break marker sits on the first failed stage (CHAIN fail → break under CHAIN).
- `WHY` is the engine `why` string; never invent.
- `DIAGNOSIS` is a **pure function of (verdict, reason, chain)** from a closed table
  (see C6) — still not "AI commentary"; it's a lookup the owner can trust.

### C5. Compact film chip (on-frame / hover)

Reuse `thChain` → upgrade to:

```
Harlequin Crest  🏦⨯ no-chain
```

Hover popover = mini river (same stages, one line):

```
EYES● LOC● CHAIN○ VERDICT⨯ BOARD○
stash · no floor chain this session
```

### C6. Diagnosis lookup (closed set — implement as dict)

| reason / verdict | diagnosis (owner English) |
|------------------|---------------------------|
| stash-no-chain | Engine refused vault correctly. If the item was truly farmed, the floor SEEN never happened — check earlier frames / scene mis-tag. |
| vault:stash / vault:hold | Committed. Board should show vault. If board empty, board-send bug not lifecycle. |
| holding | In bag; waiting hold timer or stash. Not farmed yet. |
| hold-low-conf | Inventory seen but anchors missing / conf low — hold deferred on purpose. |
| already-vaulted | Same instance echo; no second commit. Fresh drop needs new floor provenance. |
| throw-out | Was held/vaulted, now on floor again — cancelled. |
| equipped | Worn gear; never vault. Chronicle-only if at all. |
| junk / skip-weak | Filtered by policy; model may still have "seen" it. |
| seen | Floor label only; review chip, not farmed. |
| gone-candidate | Was on floor, missed twice in-area — candidate for later inv/stash chain. |

### C7. DOM / CSS sketch (control_ui.html)

```html
<section class="dc">
  <h4>decision chain</h4>
  <div class="dc-card" data-verdict="blocked">
    <div class="dc-name">Harlequin Crest</div>
    <div class="dc-loc">🏦 stash · shared</div>
    <ol class="dc-river">
      <li class="ok">eyes</li>
      <li class="ok">loc</li>
      <li class="break">chain</li>
      <li class="bad">blocked</li>
      <li class="dim">board</li>
    </ol>
    <p class="dc-why">no floor / hold / candidate this session</p>
    <p class="dc-diag">Engine refused vault correctly. If farmed for real: bug is upstream…</p>
  </div>
</section>
```

```css
.dc-card { border: 1px solid var(--edge); border-radius: 8px; padding: 10px 12px; margin: 8px 0;
           background: rgba(0,0,0,.25); }
.dc-card[data-verdict="vaulted"] { box-shadow: inset 3px 0 0 var(--mint); }
.dc-card[data-verdict="blocked"] { box-shadow: inset 3px 0 0 #f88; }
.dc-river { display: flex; gap: 0; list-style: none; padding: 0; margin: 8px 0; font: 700 9px/1 ui-monospace,monospace; text-transform: uppercase; letter-spacing: .04em; }
.dc-river li { flex: 1; text-align: center; padding: 6px 2px; border-bottom: 2px solid rgba(255,255,255,.12); opacity: .45; }
.dc-river li.ok { border-color: var(--mint); color: var(--mint); opacity: 1; }
.dc-river li.break { border-color: #f88; color: #f88; opacity: 1; position: relative; }
.dc-river li.break::after { content: "▾ break"; position: absolute; left: 0; right: 0; top: 100%; font-size: 8px; color: #f88; }
.dc-river li.bad { border-color: #f88; color: #f88; opacity: 1; }
.dc-why { margin: 10px 0 4px; color: var(--gold-hi); font: 600 11px/1.35 ui-sans-serif, system-ui, sans-serif; }
.dc-diag { margin: 0; opacity: .7; font: 400 10.5px/1.4 ui-sans-serif, system-ui, sans-serif; }
```

### C8. Aggregation strip (top of DECISION CHAIN section)

One line above the cards, keyword-dense:

```
3 names · 1 vaulted · 1 holding · 1 blocked · board writes: 1
```

Blocked/thrown count in coral so the owner’s eye lands on the problem card first.
Sort cards: blocked → thrown → vaulted → holding → seen → skip.

### C9. What this is NOT
- Not a JSON tree viewer
- Not a full session lifecycle dump of every name ever seen
- Not a second film — the film stays sacred; the river is the instrument panel

---

## D. Instrument definition of done (when ON AIR may unfreeze)

SIM is "perfect" enough to resume ON AIR work when:
1. Any past v833+ read can answer: *why fired · what model said · what parse did · what
   lifecycle decided per name and why · what board got*
2. stash-no-chain and false-vault classes are diagnosable in <30s by the owner alone
3. Pre-v833 rows never fake; they badge honest gaps
4. Session picker + search can find the moment without ⏮⏭ archaeology
5. Full suite + visual verify green on the above

Until then: **ON AIR stays frozen.** Eye rounds (Grok / Kimi) hit THIS document, not vibes.
