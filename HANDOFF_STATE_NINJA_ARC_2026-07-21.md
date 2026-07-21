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

## UPDATE @ v948.23 (both big organs landed)
- v948.22 Engine Room v2 RETRO SCRUB ✅ · v948.23 Phase B 4th SUPER-ANALYZE organ ✅ — both shipped, green, pushed.
- NOW IN FLIGHT (gate when they hand back, selective-commit per lane):
  - **control_ui.html** = polish-ui-2, ENGINE ROOM v3 (click-to-detail drill-down: click organ/frame → raw process
    at that ts — read ms, OCR text, quorum votes, gate decision, funnel receipt, super-analyze recovery, which layer owns it).
  - **control_app.py** = engine agent, PHASE C `_kai_reconcile()` (1 pure fn, ZERO new threads; closer post-seal +
    driver live deque; sealed owner kaiVer≥3 wins; materialize `_kai_build_engine_frames` → report["engineFrames"] via atomic writer).
- After these: Engine Room is COMPLETE (v1+v2+v3); reconciler done → then Phase D (liveRing in status_payload) is mostly the
  remaining data-contract work, then per-engine 100+ polish + UX 5-round arc.

## UPDATE @ v948.25 (Phase C DONE — Master Brain core complete)
- v948.24 Engine Room v3 (drill-down) ✅ → COCKPIT COMPLETE. v948.25 Phase C `_kai_reconcile` + `engineFrames` ✅.
- The Master Brain's reconciliation logic + the full cockpit are DONE. 9 versions this arc (v948.17→v948.25).
- REMAINING (no agents in flight now — dispatch fresh):
  - Phase D: surface `_ENGINE_FRAMES_LIVE` deque + engineFrames in `status_payload()` as `liveRing`/`engineFrames`
    (the reconciler already fills the deque; just expose it, rawHead cap 160, per the settled Q4).
  - UI: surface authoritative `owner`/`verdict` from engineFrames in the Engine Room drill-down (polish-ui-2 —
    right now it infers ownership; the reconciler makes it definitive).
  - Then: PER-ENGINE 100+ polish arcs (PER_ENGINE_PERFECTION_ROADMAP) + the UX/TYPOGRAPHY 5-round arc.
- All green: control 60 · routes 173 · agent 171. HEAD clean, pushed. Gate pattern above.

## UPDATE @ v948.26 (Phase D DONE — reconciler surfaced to client)
- v948.26 Phase D ✅: status.liveRing[] (now-cursor) + beat.engineFrame{owner,verdict,layers,sealed} (retro). Stamps ×3 v948.26. Floor 64+174+171 green, smoke 64.
- 10 versions this Ninja arc (v948.17→v948.26). The full stack: hardened engine · accuracy gate · 4th super-analyze organ · Master-Brain reconciler · complete Engine Room cockpit · reconciler surfaced.
- IN FLIGHT: polish-ui-2 UI owner/verdict SWAP (control_ui.html — use beat.engineFrame.owner/verdict authoritatively, fall back to inference when absent). Gate when it hands back (selective commit control_ui.html only, no bible → no smoke, no stamp bump).
- THEN (no engine work pending): the UX/TYPOGRAPHY 5-round arc (UX_TYPOGRAPHY_POLISH_ARC.md) + the PER-ENGINE 100+ polish arcs (PER_ENGINE_PERFECTION_ROADMAP.md). The flagship CORE is complete; what remains is polish + per-engine perfection toward Level 2.

## 🎯 STANDING MANDATE (Konyo 2026-07-21): SHIP 80 MORE VERSIONS
Autonomous Konyo-workflow chain toward Level 2. Gate every round as it lands (Konyo: "keep gating the rounds as they land"). Round queue, collision-safe (one owner per file), sequential on shared files:

**LANE A — UX/TYPOGRAPHY 5-round arc (control_ui.html, then bible.html w/ EDIT_LOCK)** — polish-ui-2 + typo-r1 alternate, ONE at a time on control_ui.html:
- R1 typography system (IN FLIGHT: typo-r1, atop polish-ui-2's Phase D swap) → gate combined → R2
- R2 toggle sweep · R3 fullscreen optimization · R4 structure+hierarchy · R5 visual polish (spec: UX_TYPOGRAPHY_POLISH_ARC.md)

**LANE B — PER-ENGINE 100+ polish (PER_ENGINE_PERFECTION_ROADMAP.md)** — engine agents, one owner per python file:
- 📷 capture (tv_diablo.py) · 👁 read (tv_diablo.py READ_PROMPT/timeouts) · 🚦 route+gate (control_app.py) · 🩹 funnel (control_app.py/stash_eye.py). control_app.py & tv_diablo.py are SHARED → sequential per file, never two agents at once.

**GATE PATTERN (every round):** verify floor (control 43/64 · demo/routes · agent) → selective commit ONLY that lane's file(s) → stamp bump if bible/logic → smoke ONLY if bible/spec changed → push → relaunch app if python changed (pkill -f control_app.py; open "TV DIABLO.app"). Fable serializes gates. Grok third-eye via GitHub dossier each few rounds.

**GUARDRAILS (unchanged):** LOCKED intake crops untouched · NEVER full Playwright suite on Mac · Engine Room observes never drives · runewords=KEEP · never leak memory files to the public repo · captureTs==frame ms join law.

**PROGRESS:** 0/80 shipped under this mandate (chain start HEAD afb7083 / v948.26). Increment as rounds land.

## 🔢 VERSIONING CHANGE (Konyo 2026-07-21): INTEGER VERSIONS, +1 PER SHIP
Decimals RETIRED. We are at milestone v948. Every shipped version from here = ONE integer bump: next ship stamps **v949**, then v950, v951 … NO more decimals.
- The 80-version mandate = **v949 → v1028** (integer count 949…1028).
- Every gate stamps the next integer across ALL THREE (bible D2R_BUILD.id == control ver == agent VERSION — stamp-parity test enforces equality).
- The NEXT gate (typo-r1 R1 + polish-ui-2 Phase D swap, combined) ships as **v949** (progress 1/80).
- Progress counter: "N/80 · vNNN". Chain start = milestone v948 / HEAD a3d33cd.

## 🔢 CORRECTION (Konyo 2026-07-21): REAL VERSION COUNT = 1172 (decimals were real versions)
Konyo: count the REAL version — every decimal WAS a shipped version. Counted all distinct versions ever shipped (decimals included, mandate-text pollution removed) = **1172**. The old "v948" milestone counter was undercounting because ~224 decimal sub-versions never bumped the integer.
- **REAL current version = v1172. NEXT SHIP = v1173** (supersedes the earlier wrong "v949" note — that ignored the decimals).
- Integers only, +1 per ship, NO decimals ever again.
- 80-version mandate = **v1173 → v1252**.
- NEXT gate (typo-r1 R1 + Phase D swap combined) ships as **v1173** (1/80). Stamp all three parity points (bible D2R_BUILD.id == control ver == agent VERSION) = "v1173".

## 🏆 NORTH STAR (Konyo 2026-07-21): v2000 = LEVEL 2 = RENAME + REBRAND
At version **v2000**, TV DIABLO graduates to Level 2 — a full rename + rebrand. That's the destination the version count is climbing toward. From v1172 today = 828 versions out. The 80-mandate (v1173→v1252) is leg 1. Every gated integer is a step toward the rebrand. Keep the climb: land → gate → +1 → repeat.

## ✅ GATED: v1173 (1/80) — HEAD 26a5781
Integer reset (decimals retired, real count 1172→v1173) + Typography R1 (one type-scale, fullscreen floor, 2nd competing system retired — typo-r1) + Phase D owner/verdict swap (Engine Room drill-down authoritative — polish-ui-2). ×3 parity v1173, floor control 64 · agent 171, smoke+deploy green, app relaunched, EDIT_LOCK released. NEXT: polish-ui-2 owns R2 (toggle sweep) on control_ui.html; typo-r1 steps off that file. Counter: 1/80 · at v1173 · target v1252 · north star v2000.

## ✅ GATED: v1174 (2/80) — HEAD a5a341d
Typography R2 — TOGGLE SWEEP (polish-ui-2, control_ui.html): one-shell law applied to every toggle (modals backdrop-fade+panel-rise · in-place panels smooth reveal · <details> ease · dash cards gentle), reduced-motion/endurance opt-out, built on the v1173 --fs-* scale, zero raw font-sizes added. Shell-tab→iframe promote left un-animated (protects 0.00px invariant). ×3 parity v1174, floor control 64, smoke passed + deploy live, app recovered @ v1174, EDIT_LOCK released.
NOTE: :17772 had crashed again before this gate (recovered via .app relaunch during the stamp bump). NEXT: polish-ui-2 owns R3 (fullscreen optimization). Counter: 2/80 · at v1174 · target v1252 · north star v2000.

## ✅ GATED: v1175 (3/80) — HEAD fef3da7
Typography R3 — FULLSCREEN OPTIMIZATION (polish-ui-2, control_ui.html @2560×1440): hero standby caption un-clipped (OFF stage min-height clamp, clears meters 52px) + right rail breathes (clamp 238→430px, was capped 360). 0 sideways scroll, 0 sub-floor text, 0.00px head-tab invariant held. ×3 parity v1175, smoke passed + deploy live, app recovered @ v1175.

## 🔧 RECURRING :17772 CRASH — root cause found, hardening in flight (Lane B → v1176)
Root cause: control_app.py main() runs the HTTP server as a DAEMON thread (line ~6846) while the pywebview native window (board_window) blocks the main thread. When the window dies/returns, main() exits → daemon server dies → :17772 down. Plus _orphan_watch() (line ~6727) os._exit(0)s the whole process if /api/status is unreachable 3×20s. DISPATCHED engine-stability agent to decouple server lifetime from the window + defang the self-kill (control_app.py only, NOT the ver stamp). Gate as v1176 when it hands back — BEFORE R4, since every gate stamps control_app.py (serialize gates on the shared file).

GATE ORDER: engine-stability (v1176, control_app.py) gates BEFORE polish-ui-2 R4 (v1177, control_ui.html). Both work in parallel (different files); only gates serialize. Counter: 3/80 · at v1175 · target v1252 · north star v2000.

## ✅ GATED: v1176 (4/80) — HEAD 7e96c5d — RECURRING :17772 CRASH FIXED
engine-stability lane (control_app.py). Root cause (control_app.log evidence): main() --open branch called srv.shutdown()+return when the pywebview window closed (incl. flaky macOS WKWebView self-close after sleep/wake/GPU hiccups), no supervisor → :17772 dead until manual restart. FIX: window close → HEADLESS keep-alive (server lifetime decoupled from window); _orphan_watch widened 60s→100s + logs. Only /api/quit + SIGTERM end the process now. ×3 parity v1176, floor control 64 · agent 171, private-port sim (window-close → HTTP 200 survives), smoke+deploy live. APP RELAUNCHED @ v1176 via .app (TCC-correct path) — now hardened against this crash class. Selective commit (control_ui.html R4 NOT staged).
NOTE: launcher = tv/start_tvd_mac.sh → exec python3 control_app.py --open (reroutes through Terminal for Screen-Recording TCC). Relaunch = pkill -f control_app.py; open "TV DIABLO.app".
NEXT: polish-ui-2 R4 (structure+hierarchy, control_ui.html, IN PROGRESS) gates as v1177. Counter: 4/80 · at v1176 · target v1252 · north star v2000.

## ✅ GATED: v1177 (5/80) — HEAD 009936d
Typography R4 — STRUCTURE + HIERARCHY (polish-ui-2, control_ui.html): rail lower half given the dash's section discipline — THE READER NET (🔴🔵🧠 under gold accent-bar label) + SESSION HEALTH (labeled, rows top-aligned). CSS ::before labels, zero markup/ID/data changes. ×3 parity v1177, floor control 64, demo 7/7 (0.00px · 3 eyes · signal panel · closeability held), smoke+deploy live, app @ v1177.
NEXT: polish-ui-2 R5 — VISUAL POLISH + CONSISTENCY SWEEP (final typography round → v1178), Grok third-eye on before/after. After R5 the UX/typography 5-round arc is COMPLETE; then Lane B per-engine 100+ polish continues toward v1252. Counter: 5/80 · at v1177 · target v1252 · north star v2000.
