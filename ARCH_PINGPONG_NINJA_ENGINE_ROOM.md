# 🥷🧠🖥 ARCHITECTURE PING-PONG — THE NINJA ENGINE + THE ENGINE ROOM (retro cockpit)

**Status:** DESIGN (architecture-first — ping-pong THIS before building the full flagship)
**For:** Fable ⇄ Grok ⇄ Konyo — refine the architecture, then build from the ground up
**North star:** `ENGINE_ARCHITECTURE.md` (the unified engine + Master Brain / Ninja KAI + Engine Room spec)
**Scope:** ~40 versions to build the finishing-move flagship; then 1000+ toward LEVEL 2 (a real-time product)

> Konyo: "properly architected — ping-pong the architecture even before building everything, perfectly
> built from the ground up, smartly and intelligently. This is the finishing move: the Ninja engine +
> retro button for the backend of the entire console."

This doc is the BLUEPRINT to attack/refine before code. Grok: critique the data model, the time-sync
contract, and the reconciliation logic. Fable: same. We converge the design, THEN dispatch build rounds.

---

## 0. The two things being built (keep them distinct)
1. **THE NINJA KAI (Master Brain)** — the always-on super-watchdog: the *logic* that verifies · authorizes ·
   authenticates · filters every read across live+retro, reconciles the 5 layers into one truth, and is
   accountable for total system accuracy. Invisible.
2. **THE ENGINE ROOM** — the *cockpit*: the visual debugger (one button) that shows what every engine sees
   and decides, live AND retro, time-synced, with per-process drill-down. The Ninja KAI's face.

They are coupled: the Engine Room renders what the Ninja KAI reconciles. Design the reconciliation
(the data) first; the cockpit renders it.

---

## 1. DESIGN PRINCIPLES (the ground rules — challenge these first)
- **Film is ground truth.** Every debug view derives from the reel + the journal, never re-derives.
- **captureTs == the frame's capture ms for every artifact; retro joins on captureTs, never ts.**
  (Amended 2026-07-21 — the panel's Q5 finding: `ts==captureTs` was the wrong wording because it let
  a receipt's `ts` = its own captureTs, both equal to the RECEIPT-LANDING time, which passes the check
  numerically while still floating seconds right of the frame it describes. `ts` is legitimately
  DIFFERENT per artifact — when it was answered/received — never the join key. Live and retro are the
  SAME timeline; "now" is just the rightmost captureTs. If any layer's artifact isn't stamped to its
  TRUE capture ms, the cockpit can't sync it → that's a bug to fix at the source, not paper over in the UI.
  Fixed at the source for intake receipts in Phase A0 (`control_app.py`, `tv_diablo.py`): captureTs is
  now derived from the receipt's `frameId`, never from the client's receipt-landing `Date.now()`.
- **Observe, never drive.** The Engine Room reads; it never issues a game action or mutates state. (The one
  exception already exists: /api/kai_reclose as an explicit human-triggered re-run — a button, not automatic.)
- **Additive + defensive.** New per-process fields ride existing journals/status; the cockpit lights up as
  they land, no-ops otherwise (the gate/HD-art pattern). No big-bang schema.
- **One data contract, two clocks.** Live source = /api/status (the now-cursor). Retro source = the sealed
  reel's journal + kai_report + /api/beat. SAME shape where possible so the cockpit renders one model.

## 2. THE DATA MODEL — the "engine frame" (the atom the cockpit renders)
Every capture ms produces ONE reconcilable record. Design this schema NOW (it's the contract):
```
EngineFrame @ ts {
  frame: reel path | live eye path
  capture: { fps, pinned, gameOk }
  layers: {
    live:   { state: reading|idle|stalled, inFlightMs, names[], ocrRaw[], model }
    second: { state: draining|idle, backlogDepth, drained[] }
    kai:    { state: swept|pending, missedTexts[], caughtNames[] }
    super:  { state: reread|—, deepNames[] }          # 4th organ (to build)
    router: { label, quorumVotes{ocr,journal,read,judge}, confidence }
    gate:   { gatePass, gateReason, gateSources[] }
    funnel: { fired, tab, receiptTotal, ok, refires }
  }
  owner: which layer produced the FINAL accepted read (Master Brain's reconciliation)
  verdict: keep|toss|grail|border|miss   (judge/register)
}
```
**Open Qs for ping-pong:** (a) build this record at seal (materialize into kai_report) vs derive on-read in
/api/beat? (b) how much live per-process state can /api/status carry without bloating the 1.8s poll? (c) the
`owner`/reconciliation field — computed where (closer? a new master-brain pass?) — see §4.

## 3. THE TIMELINE ENGINE (live ↔ retro, one axis)
- ONE horizontal time axis. Live cursor pinned at the right edge, advancing. Scrub left = retro into sealed
  reels (multiple reels = segments on the axis).
- Scrubbing sets a `focusTs`. The cockpit resolves the EngineFrame at/nearest `focusTs` and renders every
  organ's state AT THAT MS. Live mode = focusTs follows now; retro = focusTs pinned to the scrub point.
- **Open Qs:** (a) live per-process detail granularity — do we keep a rolling in-memory ring of the last N
  live EngineFrames server-side, or reconstruct from the journal tail? (b) how to render a 66s stall on the
  axis (a wide "in-flight" band, not a point).

## 4. THE MASTER-BRAIN RECONCILER (the Ninja logic — the hard part, design carefully)
The `owner` + final read per item = whichever layer is most confident AND DB-verified, in priority:
super-analyze deep-read > live named > kai-retro named > OCR-only. Laws:
- Never let a captured item die unread (if all live missed, super-analyze MUST attempt it).
- Never let a thin funnel clobber a good tally (already fixed v948.18 — generalize the never-zero law to
  ALL writes: max-verified-total wins per cell).
- Every accepted read carries WHICH layer owned it + WHY (the audit trail the cockpit renders).
- **Open Qs:** where does the reconciler run — extend _kai_closer_loop (post-seal) + a live shim? Is it a
  new always-on thread (the true "always running super-watchdog"), or a pass over the journal? Grok: weigh in.

## 5. THE ~40-VERSION BUILD ROADMAP (AFTER the architecture settles)
Phase A — HARDEN (in progress): aftermath integrity (v948.18 ✅) · Spirit-split · materials · gems/runes.
Phase B — THE 4th ORGAN: super-analyze deep-retro re-read of gate-proved film frames → EngineFrame.super.
Phase C — THE RECONCILER: the Master-Brain owner/verdict per item (§4) → EngineFrame.owner + audit.
Phase D — THE DATA CONTRACT: materialize EngineFrame into kai_report + a live ring in /api/status.
Phase E — THE ENGINE ROOM: spine + live-cursor timeline → retro scrub → click-to-detail drill-down (staged).
Phase F — POLISH + PERFORM: the 1000-version road to LEVEL 2 (real-time product).

## 6. PING-PONG QUESTIONS (answer these before building Phase D/E)
1. EngineFrame: materialize-at-seal vs derive-on-read? (perf vs freshness)
2. Live per-process ring in /api/status — size, fields, poll cost?
3. Reconciler: post-seal pass vs always-on thread? (the "always running" Ninja promise)
4. Retro scrub across MULTIPLE reels — one axis with segments, or a reel picker + per-reel axis?
5. What's the minimum EngineFrame that makes the cockpit useful, so we ship Phase E v1 early and iterate?

---
_Architecture first. Ping-pong this. Then build the Ninja from the ground up._ 🥷🧠🖥

---

## ✅ SETTLED DECISIONS — from the 6-agent critique panel (2026-07-21, converged, grounded in code)

The six critiques converged cleanly (no contradictions). The codebase already half-answered most with the
right split — the job is to GENERALIZE the working pattern, not invent a new one. **One correctness BLOCKER.**

**Q1 · EngineFrame — HYBRID.** Materialize the *semantic* reconciliation (owner/verdict/per-layer) into
`kai_report.json` at seal (a per-frame array); keep *presentation* + the *live cursor* derived on-read.
The deciding layer (4th organ) only runs post-seal, so owner/verdict are seal-time facts by construction;
freshness = `kaiVer` re-close. First step: `_kai_build_engine_frames()` beside `_kai_build_routing`, written
via `_kai_write_report_atomic`.

**Q2 · Reconciler — ONE pure fn, ZERO new threads.** `_kai_reconcile()` called from the two EXISTING
mutually-exclusive threads (authoritative in `_kai_closer_loop`; provisional live in `_engine_driver`'s 2s
loop into an in-memory deque). A 3rd always-on thread would revive the race the `_agent_mode/_agent_alive()`
gate killed (v937.3). "Always running" = an OBSERVABILITY promise (the `_WATCHDOG_LAST` compute→stash→render
pattern), NOT a literal thread. Sealed owner (kaiVer≥3) always wins over the live provisional guess.

**Q3 · Timeline — ONE continuous axis, SEGMENTED BY REEL** (per-reel splice, between-reel dead time = thin
divider; not wall-clock, not a picker). One `captureTs→(reel,frame)→EngineFrame` resolver for both modes;
"now" = rightmost frame of newest reel; only the exact right edge overlays live `/api/status`. **Key every
segment by stable `sessionId`, never positional `n`** (n renumbers after each seal). Ruler from
`_theatre_sessions()`.

**Q4 · Live ring — YES, ~12-16 frames in control_app MEMORY**, projected from the already-cached
`_BR_CACHE["st"]["reads"]` + one synthetic in-flight head from `health` (the stall lives only in the agent's
live state — a stalled read has NO journal row yet). Fields `{ts(=captureTs),lane,ms,ocrMs,conf,names[:3],
rawHead}`, **rawHead HARD-CAPPED ~160 chars**; quorum votes blank-but-present live (seal-time, filled on
scrub). Add `"liveRing"` to `status_payload()`. **Do NOT derive from `_kai_journal_rows()`** (parses the
897KB journal per poll).

**Q5 · Time-sync — ✅ FIXED (Phase A0, 2026-07-21, engine agent).** 3 of 5 layers were clean (deep/kai/gate
anchor captureTs to the frame). **Offender: INTAKE RECEIPTS** — both writers (`control_app.py:5753`,
`tv_diablo.py:458`) stamped captureTs = the client's `Date.now()` receipt-landing time, so it floated SECONDS
right of the frame it describes → retro scrub could not trust it. **FIX:** both sites now derive captureTs
from the receipt's `frameId` (`_capture_ts_from_frame_id` — reused in `tv_diablo.py`, mirrored in
`control_app.py` since it's a separate process); `ts` stays the receipt-landing time (legitimately
different — when it answered, not when the photo was taken). No frameId → falls back to `ts` (can't do
better) and the row carries `"capSrc":"receipt-fallback"` so retro readers know honestly it isn't
frame-anchored; a frame-derived row carries `"capSrc":"frame"`. Pinned in `test_routes.py`
(`TestIntakeReceiptDedupe.test_captureTs_derived_from_frame_id_not_receipt_time` +
`test_captureTs_falls_back_honestly_with_no_frame_id`). **VERIFY rows** are `ts=now, captureTs=cap_ms`
(retro-safe, readers prefer captureTs — left as-is). **Invariant (amended, both docs):** *"captureTs ==
the frame's capture ms for every artifact; retro joins on captureTs, never ts."* All 4 layers (deep/kai
rows, gate/routing rows, and now intake receipts) hold it; VERIFY rows hold the retro-safe variant.

**Q6 · MVP cockpit — SHIP READ-ONLY v1 projecting what ALREADY exists** (live now-cursor from
`status_payload()`, retro per-frame from `kai_report.routing[]`), with super/owner/verdict STUBBED null
(gate/HD-art light-up pattern). Two zones: (A) the SPINE — 6 organ panels from status (live-eye RED when
`visionBusyMs` > stall threshold); (B) the RETRO TIMELINE — a sealed reel's `routing[]` on one ts axis
colored by gatePass/routed/skipReason, frame-click → existing `/api/beat` drill-down. Do NOT block v1 on the
4th organ/reconciler.

**REVISED BUILD ORDER:** Phase A0 (✅ DONE, 2026-07-21) — fix intake captureTs → the frame's capture ms ·
Phase E-v1 MVP cockpit (ships now, existing data) · Phase B 4th organ · Phase C reconciler · Phase D
materialize EngineFrame + live ring · Phase E-v2/v3 super/owner/quorum fill-in. **The MVP (E-v1) can start
immediately now that the blocker is cleared; B/C/D refine what the cockpit shows.**
