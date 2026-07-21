# 🥷 STATE + GROK HANDOFF — Ninja Engine / Engine Room arc (2026-07-21, Fable near context limit)

**HEAD:** v948.21 · all pushed · console LIVE on :17772. For: Grok / post-reset Fable to continue.

## WHERE WE ARE (the finishing-move flagship, in progress)
Building THE NINJA KAI (Master Brain super-watchdog) + THE ENGINE ROOM (retro+live visual-debugger cockpit).
Architecture is SETTLED (6-agent critique panel). North-star docs on GitHub:
- `ENGINE_ARCHITECTURE.md` — the unified engine (4 engines + Master Brain + Engine Room)
- `ARCH_PINGPONG_NINJA_ENGINE_ROOM.md` — the design + the 6 SETTLED DECISIONS + build order
- `PER_ENGINE_PERFECTION_ROADMAP.md` — Konyo's 100+ version commitment (perfect each of 4 engines)
- `UX_TYPOGRAPHY_POLISH_ARC.md` — queued 5-round app-wide typography/polish arc
- `FORENSIC_CROSSREF_2026-07-21_2105_fast_run.md` — Grok's forensic punch list (mostly fixed below)

## THE 4 ENGINES (separate beasts, unified by the Master Brain, seen through the Engine Room)
1. 📷 CAPTURE (tv_diablo.py) · 2. 👁 READ (tv_diablo.py, 5-layer stack) · 3. 🚦 ROUTE/GATE (control_app.py) ·
4. 🩹 FUNNEL (control_app.py + bible.html + intake.js). Master Brain conducts; Engine Room observes.

## SHIPPED THIS ARC (v948.17 → v948.21)
- v948.17 STORY hand-off chips (retro-catch visible) · v948.18 aftermath integrity (runes 404→4 clobber
  guard, gems receipt, atomic kai_report, 2nd-eye stall-drain, 35s read cap) · v948.19 Spirit grail/toss
  reconciled + materials classifier recal (3204-frame) · v948.20 Engine Room v1 (spine + live cursor) ·
  v948.21 Phase A0 captureTs BLOCKER fixed (retro trustworthy).

## IN FLIGHT (uncommitted agent WIP — GATE when they hand back)
- **control_ui.html** = polish-ui-2, ENGINE ROOM v2 (retro scrub — drag cursor left → engine state at past ts).
- **control_app.py** = engine agent, PHASE B (4th SUPER-ANALYZE organ — deep AI re-read of gate-proved
  frames the live eye missed; turns "film complete but 3 registered" → "all recovered").
- GATE PATTERN: verify floor (test_control/routes/agent green) → SELECTIVE commit (one lane's files only,
  never cross the other's WIP) → push (smoke on bible/spec) → bump stamp on significant engine rounds
  (v948.22 ×3 parity, EDIT_LOCK for bible) → relaunch app → dispatch next.

## REMAINING BUILD ORDER (from the settled arch)
- Phase B: 4th super-analyze organ (IN FLIGHT) → Phase C: `_kai_reconcile()` (1 pure fn, NO new threads —
  called from closer post-seal + driver live; sealed owner kaiVer≥3 wins) → Phase D: materialize
  `_kai_build_engine_frames()` into kai_report + `liveRing` in status_payload (memory, rawHead cap 160,
  NOT from journal) → Engine Room v2 retro scrub (in flight) + v3 click-to-detail drill-down → then the
  PER-ENGINE perfection arcs (100+) + the UX/typography 5-round arc → Level 2 (v2000).

## GUARDRAILS (non-negotiable)
LOCKED intake crop fractions in functions/api/intake.js — NEVER change without Konyo. Never rewrite the
locked vault identity reader. NEVER run the full Playwright suite on the Mac (crashes it — targeted specs
only; CI Routine I = full verdict). Every ship green + smoke on bible/spec. ts==captureTs invariant is now
"captureTs == the frame's capture ms; retro joins on captureTs, never ts" (Phase A0 fixed intakes).
One-owner-per-file; Fable serializes gates. The Engine Room OBSERVES, never drives.

## OPS NOTES
- The v877 cinema spec spawns/kills control servers → can kill Konyo's live :17772. Recover:
  `pkill -f control_app.py; open ~/Desktop/"TV DIABLO.app"`. polish-ui-2 correctly never touches the port.
- Konyo's "outdated" complaints are often a STALE CACHED TAB (?cb=/?v= pin) — hard refresh ⌘⇧R first.
- Routine I "jumping" = cancel-in-progress + rapid pushes; all real reds fixed (v123/v76 key-art, v877
  cinema). Let pushes quiet for a run to complete green.

_Fable saving at ~98% context. Two agents mid-flight — gate their hand-backs with the pattern above._ 🥷
