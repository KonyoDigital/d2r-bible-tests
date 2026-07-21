# 🧠⚙️ THE TV·D UNIFIED ENGINE — one loop, six organs, feeding each other

_Konyo's north star (2026-07-21, new week): "the whole Theatre / ON AIR / TV-D / KAI thing — a
perfected, architected system that feeds each other and works unified as an engine with logic."_

**This is the authoritative architecture.** Every round in the arc moves the real code toward this
shape. The organs already exist (see `tv/PLAN_ONE_SYSTEM.md` for each); this doc is how they become
ONE engine. When a feature is added, it must plug into this loop — not sit beside it.

---

## THE SPINE — a frame's journey (one direction, always the same)

```
   ┌──────────┐   frames   ┌───────────┐  votes   ┌──────────┐ routes ┌──────────┐ receipts ┌─────────┐
   │ CAPTURE  │──────────▶ │ THE       │────────▶ │ THE      │──────▶ │ THE      │────────▶ │ THE     │
   │ ON AIR   │            │ READERS   │          │ ROUTER   │        │ FUNNELS  │          │ LEDGERS │
   │ film+pin │            │ 🔴🔵🧠     │          │ quorum   │        │ (LOCKED) │          │ journal │
   └──────────┘            └───────────┘          └──────────┘        └──────────┘          └─────────┘
        │                        ▲                     │                    │                     │
        │                        │ retro re-read        │ re-label from film │ never-zero re-fire  │
        │                        └──────────────────────┴────────────────────┘                     │
        │                                                                                           │
        └──────────────────────────────▶  THE THEATRE (the mirror — replays the whole loop) ◀──────┘
```

## THE SIX ORGANS

### 1. CAPTURE (ON AIR) — the senses
Film thread archives **every** frame to the reel (~5fps) = **ground truth**. The eye pins the D2R
window (no pin → no eye). Produces: reel frames + a live "something changed" signal (motion/OCR text).

### 2. THE READERS (🔴🔵🧠) — layered eyes, each a net for the last
- **🔴 Live eye** — deep-reads the current frame (names items) when text-eye/motion triggers. First pass, fast.
- **🔵 Second eye** — in idle gaps, re-reads the text-eye backlog the live eye rushed past. Corrections.
- **🧠 KAI** (post-seal) — sweeps the WHOLE reel from film, re-labels + re-tallies what live never caught.
**Law: no reader is authoritative alone — the FILM is.** Live miss → 🔵 catches → 🧠 retro catches.
This is why `kaiVer` re-closes old reels: the readers keep improving; the film lets them re-try forever.

### 3. THE ROUTER — the brain that decides (the LOGIC layer)
Every frame (live + retro) earns a **label** by **quorum** of independent evidence classes
(pixel/OCR · time/journal · content/read+judge). Label → route: `tally:*` · `vault` · `gridcount` ·
`judge`. Confidence < 2 or disagreement → no fire. This is the single point where the readers' votes
become ONE decision per frame. Dedupe is routing-only (film never trimmed).

### 4. THE FUNNELS — the hands (LOCKED intakes, never replaced)
Routed frames flow through the perfected readers: rune/gem/material tally (count icons),
`vaultGridCount` (count occupied slots), `vaultIntake` (identity — manual/tooltip only),
`aicJudge` (Item Checker keep/toss). **The engine FEEDS these frames; it never rewrites them.**
Receipts flow BACK to the router (routed → fired → confirmed).

### 5. THE LEDGERS — the memory
Reads + receipts + verdicts journal to `sessions.jsonl` (**law: ts == captureTs**). KAI compiles
the register; Chronicle **inbox** proposes grail write-ins (review-gated, never a silent grail write).

### 6. THE THEATRE — the mirror (where Konyo debugs the engine)
Replays the ENTIRE loop per frame: each photo carries its **stamp ledger** — which reader saw it,
the router label, the funnel receipt, the verdict, the socket count. **REAL** = every photo 1:1 ·
**FAST** = every photo time-zipped · **STORY** = the AI-reader-focused cut (read-to-read). The theatre
is not a viewer — it is the engine's self-portrait, the surface where every other organ is auditable.

---

## THE FEEDBACK LOOPS (what makes it an ENGINE, not a pipeline)
1. **Readers → Router → Funnels → Ledger → Theatre** (forward spine).
2. **Retro re-read**: KAI re-runs the router on the FILM after seal → re-funnels tabs live missed
   (`_kai_stage3_gap_funnels`, `_kai_retro_promote_tally`). The engine self-corrects from ground truth.
3. **Never-zero**: a funnel 0/error feeds back → re-fire against a fresher frame (tally + vault-count).
4. **Receipts → Router**: a landed receipt closes the routed row; a gap triggers a funnel.
5. **Theatre → Human → Engine**: Konyo sees a miss in the theatre → `/api/kai_reclose` → the loop reruns.

## THE UNIFYING LAWS (the logic that binds every organ)
- **Film is ground truth.** A live miss is never permanent.
- **ts == captureTs.** Every artifact anchored to its capture millisecond.
- **No pin → no eye.** Readers only run on a pinned game.
- **Locked intakes are the hands.** The engine routes frames to them; it never becomes them.
- **Every frame is knowable.** The theatre can always show a frame's full stamp ledger.
- **Quorum over any single eye.** ≥2 independent evidence classes to route.

## WHERE IT'S NOT YET FULLY UNIFIED (the arc's targets, in order)
1. **Materials retro** — the router must re-label materials from film when live missed the tab (v948.7; audit running).
2. **Film ↔ registration completeness** — every item Konyo hovers should yield a read AND a reel frame; find dropped hovers.
3. **STORY = AI-reader-focused** — center the replay on the read frames themselves (in flight).
4. **Reader hand-off telemetry** — the theatre should show, per frame, WHICH reader owns it and whether the next net caught what the last missed (make the feedback loops visible).
5. **One engine-state surface** — a single live "engine health" view: capture fps, reader queue depths, router routedCount, funnel receipts, ledger lag — the whole loop at a glance.

---

## HOW THE ARC WORKS (Konyo Workflow, this file = the spec)
- Each round moves ONE organ or ONE feedback loop toward this architecture. Version per round.
- Engine agent owns tv/*.py + intake plumbing; UI owner owns control_ui.html (the theatre/mirror);
  SuperGrok third-eyes each; **Fable gates + commits + pushes** every round.
- Guardrails (non-negotiable): don't touch LOCKED intake crop fractions in `functions/api/intake.js`;
  don't rewrite the locked vault identity reader; subscription intake only; NEVER the full Playwright
  suite on the Mac; every ship green (test_control/test_routes/test_agent/demo 7/7) + smoke on bible changes.

_This document is the engine's blueprint. If a change doesn't plug into the loop above, it doesn't ship._
