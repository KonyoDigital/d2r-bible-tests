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
