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

### 🧠👑 THE MASTER BRAIN KAI — the conductor (Konyo, 2026-07-21 21:xx)
_"the engine that connects it all and syncs it all — the MASTER BRAIN KAI, the OG of all of them."_

Above the five reader layers sits ONE orchestrator. The layers are not five separate readers — they
are ONE brain with five passes, and the Master Brain is what makes them one: it watches each layer,
guarantees the hand-off, and is accountable for the end-to-end promise — **every captured frame ends
as a VERIFIED read rendered, or an HONEST miss; never a wrong one, never a silent drop.**

THE FIVE LAYERS it conducts (each a net for the last; the FILM is ground truth for all):
1. **🔴 LIVE EYE** — first pass, real-time. Fast hovering can outrun it (proven: a read stalled 66s in
   flight → 0 live reads). The Master Brain must DETECT a stalled/slow live eye and lean on the later
   layers instead of losing the item — a 66s live stall is a signal to route to retro, not a failure.
2. **🔵 SECOND EYE** — delayed catch, MID-SESSION, before seal (drains the text-eye backlog in idle
   gaps). GAP: at speed there are no idle gaps → it fired 0. The Master Brain must give it a working
   window even under fast play (e.g. force a backlog drain when the live eye is stalled/idle).
3. **🧠 KAI CLOSER** — post-seal retro OCR sweep of the whole reel. Works (caught 15, self-resolved a
   watchdog gap). But OCR-MATCHES only — it does not deep-re-read.
4. **🧠🔬 SUPER-ANALYZE KAI (build this — the missing organ)** — the deep retro pass: takes every
   item-text frame the gate PROVED and does a full INDEPENDENT AI re-read (not OCR-matching), so a
   fast-hovered item whose live read + OCR both garbled STILL gets a correct read rendered in the
   aftermath. This is what turns "film complete but only 3 registered" into "film complete → all
   verified." It feeds the router/register/judge with real reads recovered from the film.
5. **🚦 ROUTER KAI** — labels + routes + the ACCURACY GATE (§3.5, proven 107/held 46). The final
   arbiter of which reads are cell-correct.

MASTER-BRAIN LAWS: (a) reconcile the five layers into ONE per-item truth (live OR second OR retro OR
super-analyze — whichever is most confident, DB-verified). (b) never let a captured item die unread —
if all live passes missed, the super-analyze layer MUST attempt it. (c) surface its own health: which
layer caught each item, and where a layer stalled (the 66s stall must be visible, not silent).

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

### 3.5 THE ACCURACY GATE — the ping-pong verification mesh (Konyo's law, 2026-07-21)
_"We need accuracy levels and brains IN BETWEEN the funnels — weed out bugs, incorrect reads, and
inaccuracy of any kind. Ping-pong the items/screenshots for the AI to read, through a funneled
hardcoded backend that perfectly filters, labels, and routes each to its correct individual cell."_

**No item enters a funnel cell until it PASSES this gate.** The router picks a route; the gate proves
it before the funnel fires. It sits between §3 (Router) and §4 (Funnels) and is where inaccuracy dies.

The gate runs three checks per item/screenshot, in order — fail any → **ping-pong** (re-read a fresher
or re-cropped frame) instead of routing garbage:
1. **Hardcoded filter (backend, deterministic — cheap, first):** does the label match the frame's hard
   signals? tab-strip word · panel chrome · socket/quality shape · the ~1400-item DB name match. A rune
   label on a frame with no rune-grid signature is rejected here with ZERO AI cost. Garbage OCR
   ("IA Lla", "Ii") never survives — it matches no DB name and no cell.
2. **Brain quorum (AI, only if the filter passes):** ≥2 independent evidence classes must agree on the
   SAME label AND the SAME cell. Live read + second-eye re-read + DB cross-ref. Disagreement → ping-pong.
3. **Cell-correctness (the routing truth):** the item resolves to exactly ONE correct cell — a rune to
   its rune cell, a gem to its gem cell, a material to its material cell, an identity item to its vault
   mule/throw cell, a socketed base to the socket-aware cell. Wrong-cell (e.g. a shared-tab frame headed
   for the runes cell) is rejected — this is the exact class that caused the vault-0 and materials-miss bugs.

**Ping-pong loop:** on any fail, the gate re-reads (fresher frame / tighter crop / a different brain) up
to N tries, then either lands a proven read or records an HONEST miss (never a wrong one). This is the
never-zero doctrine generalized to ALL cells: a 0/error/ambiguous read is a failure signal, not a value.
**Output guarantee: every item that reaches a funnel cell is filtered + labeled + cell-correct, proven by
≥2 brains and the hardcoded DB filter. Wrong reads are weeded out here, not discovered later in the theatre.**

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
0. **THE ACCURACY GATE (§3.5) — build it.** The ping-pong verification mesh between router and funnels:
   hardcoded DB/chrome filter → brain quorum → cell-correctness, re-reading until proven or honestly
   missed. This is the priority organ — it weeds out every misread before it hits a cell.
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
