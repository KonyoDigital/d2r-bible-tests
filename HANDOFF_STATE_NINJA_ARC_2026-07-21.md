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

## ✅ GATED: v1178 (6/80) — HEAD 78e0f60 — 🎉 TYPOGRAPHY ARC R1→R5 COMPLETE
Typography R5 — CONSISTENCY SWEEP (polish-ui-2, control_ui.html): brought the flagship ENGINE ROOM into the design system (.er-band gold accent-bar labels + panel chrome unified with tally/legend overlay family). Quality-over-churn (2 real fixes). ×3 parity v1178, floor control 64, demo 7/7 (0.00px both axes · three eyes · signal), smoke+deploy live.

### THE UX/TYPOGRAPHY ARC (v1173→v1178, DONE):
- v1173 R1 type scale (--fs-* clamp system, 13px fullscreen floor, 2nd competing system retired)
- v1174 R2 motion (every toggle → unified CSS shell animations, reduced-motion/endurance opt-out)
- v1175 R3 fullscreen (@2560×1440: caption clip + rail width fixed)
- v1177 R4 structure (rail section labels: READER NET, SESSION HEALTH)
- v1178 R5 consistency (Engine Room joins the design system; every overlay one family)
Net: type/motion/fullscreen/structure/consistency pull one direction — one designed product. All CSS-only, all invariants held. (v1176 = the stability crash-fix interleaved.)

## ⚠️ APP LAUNCH STATE (post-midnight 2026-07-22)
:17772 now running HEADLESS (nohup python3 control_app.py --no-open) @ v1178 — stays up (no window death vector, --no-open skips pywebview). The .app/Terminal-reroute launch stopped bringing :17772 up in this session (Terminal Automation likely not granting post-midnight) AND shell launches lack Screen-Recording TCC anyway. FOR REAL D2R SCANNING: Konyo must relaunch TV DIABLO.app himself (double-click) so the capture grant is inherited. OFFERED: a launchd KeepAlive supervisor for bulletproof always-up — awaiting Konyo's go (persistent system config, needs explicit OK).

## NEXT (7/80 →): typography arc done. Remaining mandate = LANE B PER-ENGINE 100+ POLISH (PER_ENGINE_PERFECTION_ROADMAP.md): 📷 capture · 👁 read · 🚦 route+gate · 🩹 funnel. Optional: Grok third-eye pass on the finished console (polish-ui-2's R1→R5 before/after summary is in its v1178 handback; before/after Engine Room shots in scratchpad r5_before/after_06_engineroom.png). Counter: 6/80 · at v1178 · target v1252 · north star v2000.

## 🛡️ CONSOLE SUPERVISOR INSTALLED (2026-07-22, Konyo authorized) — :17772 bulletproof always-up
launchd LaunchAgent com.konyo.tvd-console (~/Library/LaunchAgents/, in-repo copy tv/com.konyo.tvd-console.plist) runs tv/tvd_supervisor.sh: every ~20s ensures :17772 answers, brings up headless (control_app.py --no-open) if not. KeepAlive respawns the supervisor; RunAtLoad at login. TESTED: kill console → auto-resurrected <10s. HEAD 6f37045 (ops, no version bump).
- POLITE (respects TCC): supervisor honors pause-flag tv/.tvd_supervisor_pause so the real TCC app can own the port for scanning.
- **TO SCAN LIVE:** `bash tv/tvd-scan.sh` (pauses supervisor + opens TV DIABLO.app, TCC-correct). **DONE SCANNING:** `bash tv/tvd-console.sh` (restores immortal console).
- Manage: launchctl list|grep tvd-console · unload = launchctl unload ~/Library/LaunchAgents/com.konyo.tvd-console.plist
Complements the v1176 in-process window-death fix (that stops window-close deaths; this respawns after ANY death incl SIGTERM/sleep).

## 🤖 AUTONOMOUS MODE (Konyo "work autonomously" 2026-07-22): running Lane B per-engine polish, gating each round.
IN FLIGHT: engine-read (tv_diablo.py read stack — bounded reads / no-starve) → gates v1179 (7/80). Sequential engine rounds (stamp-parity couples tv_diablo.py+control_app.py+bible.html → one uncommitted stamped-file round at a time). Counter: 6/80 · at v1178 · target v1252.

## ✅ GATED: v1179 (7/80) — HEAD 5ba9e7c — READ engine polish #1
engine-read (tv_diablo.py + test_agent.py): _VERIFY_Q closer/second-look STARVE fix — the second-look queue was drained only in the live idle gap, never at session close → last reads' second looks silently vanished. FIX: _pool_shutdown drains it within the existing FAREWELL budget (no-op past deadline, never slows shutdown). +2 regression tests. ×3 parity v1179, floor agent 173 · control 64, smoke+deploy live. Supervisor auto-respawned console @ v1179. Counter: 7/80 · at v1178→v1179 · target v1252.
NEXT: route/gate engine round on control_app.py (dispatched → v1180).

## ✅ GATED: v1180 (8/80) — HEAD c2ef218 — ROUTE/GATE engine polish #1
engine-route (control_app.py + test_control.py): honest promotion sources — the v947 weak-quorum promote branch unioned STALE sources (a brain voting a contradicting label folded in as agreeing), inflating confidence + polluting gateSources. FIX: carry forward only brains that voted the promoted label + the 2 confirmed eyes. +2 tests. ×3 parity v1180, floor control 66 · agent 173, smoke+deploy live, supervisor respawned @ v1180. Counter: 8/80 · at v1180 · target v1252.
NEXT: capture engine round on tv_diablo.py (dispatched → v1181). Per-engine coverage so far: read(v1179) · route/gate(v1180) · capture(→v1181) · funnel pending.

## ✅ GATED: v1181 (9/80) — HEAD 0d72b3b — CAPTURE engine polish #1
engine-capture (tv_diablo.py + test_agent.py): blank-frame guard on ALL lanes — _is_white_backing was applied only on the window lane, not the full-screen/never-starve lanes (the paths that fire right after a white-reject demotion), so blank Metal surfaces could be archived as real gameplay. FIX: shared _grab_full_screen_frame() applies the guard everywhere (+_FILM_WHITE_REJECTS telemetry); captureTs law untouched (stamps land only on real pixels). +2 tests. ×3 parity v1181, floor agent 175 · control 66, smoke+deploy live, supervisor respawned @ v1181. Counter: 9/80 · at v1181 · target v1252.
NEXT: funnel engine round on control_app.py (dispatched → v1182) — completes the 4-engine sweep (read·route/gate·capture·funnel).

## ⚠️ SUPERVISOR PAUSED (Konyo scanning on :17772, 2026-07-22)
Konyo hit "app already open" — the supervisor's headless console held :17772. PAUSED it (touch tv/.tvd_supervisor_pause) + freed the port so he can double-click TV DIABLO.app for LIVE SCANNING. WHILE PAUSED / while he's scanning: the v1182 gate (and any gate) must NOT restart the headless console (no `pkill control_app.py --no-open`, no port grab) — Konyo owns :17772. Commit/push/deploy as normal; skip the console-restart step. When he's done scanning, `bash tv/tvd-console.sh` (or clear the flag) restores the immortal console. FUTURE IDEA (offered to Konyo): fold an app-side auto-takeover into an engine round so double-click always works, no helper script.

## 📌 FUNNEL next-round target (flagged by engine-funnel v1182): the live-driver tally/vault/vaultcount JS chains end in a bare `.catch(function(){})` with NO /intake_result POST on rejection — a silent-drop class; the Stage-3 funnel got the honest-miss-on-rejection hardening at v948.17 (Grok P0-2) but these live sites didn't. Good future FUNNEL round.

## ✅ GATED: v1182 (10/80) — HEAD cda3135 — FUNNEL engine #1 (completes 4-engine sweep)
engine-funnel (control_app.py + test_control.py): never-zero on the LIVE tally path — the guard existed only on the Stage-3 closer, not the high-freq live driver fire; a thin live photo could stomp a larger tally (Konyo's "404 then 4" on the live path). FIX: session-scoped _tab_best_total gate + guardHeld honest receipt. +tests (control 66→72). ×3 parity, floor control 72 · agent 175, smoke+deploy live. THIS is the fix that stops gem/rune counts getting stomped to 0.

## ✅ GATED: v1183 (11/80) — HEAD 2b086d0 — FORGE: Blood craft restored
Konyo reported the Blood craft vanished from the Forge. ROOT CAUSE: forgeScan ~30947 skips a whole craft type when _gemCount(gem)<1; his Perfect Ruby read 0 (stomped by the pre-v1182 live-clobber). Data was always intact. FIX (bible.html): ⚗️ Crafts section always renders all 4 craft types (makeable first); _craftSlots gem-gates readiness (gem AND rune); rows show "need Perfect Ruby" when the gem's missing. Chosen with Konyo (BOTH this + v1182). ×3 parity, floor control 72 · agent 175, SMOKE PASSED + deploy live.
NOTE: Konyo on a STALE tab (screenshot showed v1181) — needs ONE ⌘⇧R to see Blood. Supervisor still PAUSED (he's scanning) — did NOT restart headless. First full 4-engine sweep DONE (read·route/gate·capture·funnel) + 2 Konyo-reported fixes. Counter: 11/80 · at v1183 · target v1252.

## ✅ GATED: v1184 (12/80) — HEAD 13bd06e — FORGE AI-smart gem cube-up
Konyo: "I have enough red gems to make Perfect — read that automatically, 4/4." The Forge counted a craft's Perfect gem only if pre-made, ignoring the 3-to-1 cube-up chain it already does for runes. FIX (bible.html): new _craftGemReady() {ready,own,cube} — own a Perfect OR cube lower grades up via gemCubeUpPotential(); _craftSlots + forgeScan use it, so Blood reads 4/4 make-now from a stash of lower rubies; rows note "· cube 3→1 Perfect Ruby". ×3 parity, floor control 72 · agent 175, smoke+deploy live. Konyo needs ⌘⇧R. Supervisor still paused (scanning). Counter: 12/80 · at v1184 · target v1252.
PRINCIPLE (Konyo standing directive): "this is exactly the kind of syncing and coding the app needs to be attached to" — the app should AI-smart-sync stash → capability EVERYWHERE (cube-up gems/runes, derive what's makeable from what's owned). Apply this lens across the app.

## ✅ GATED: v1185 (13/80) — HEAD 64b35a4 — FUNNEL round 2 (honest-miss on live driver)
engine-funnel r2 (control_app.py + test_control.py): 3 live-driver fire chains (tally·vault·vaultcount) ended in bare .catch(){} with no /intake_result on rejection → silent drop. FIX: each .catch posts honest-miss receipt (ok:false,errors:1) so the refire ladder retries (distinct from v1182 guardHeld). node --check-verified JS; +4 tests (control 72→76). ×3 parity, floor control 76 · agent 175, smoke+deploy. Counter: 13/80 · at v1185 · target v1252. NEXT: route/gate round 2 (dispatched → v1186).

## ✅ GATED: v1186 (14/80) — HEAD 4a2af75 — ROUTE/GATE round 2 (quorum tie = disagreement)
engine-route r2 (control_app.py + test_control.py): _kai_quorum_label flagged only weak top counts, not 2+ tied leaders — Counter.most_common broke a real 2-2 tie by insertion order → silent confident winner, losing side vanished from sources (chrome veto blind to non-tabstrip/grid pairs). Live-reachable (judge 'tooltip' vs tabstrip+grid 'stash-*'). FIX: tied_leaders>1 → disagreement → route=None. +4 tests (control 76→80). ×3 parity, floor control 80 · agent 175, smoke+deploy. Counter: 14/80 · at v1186 · target v1252. NEXT: capture round 2 (dispatch → v1187).

## ✅ GATED: v1187 (15/80) — HEAD 061e6f3 — CAPTURE round 2 (captureTs join-law on drain paths)
engine-capture r2 (tv_diablo.py + test_agent.py): _fire_read stamped captureTs=NOW even when draining frames captured earlier (settle-queue up to 120s stale, text-eye queue/stall) → retro join key desynced from pixels under fast play. FIX: _resolve_read_ts(cap_ts_override) helper; 3 drain sites pass the frame's own "ts"; live reads still now(). frame_id/join law preserved. +2 tests (agent 175→177). ×3 parity, floor agent 177 · control 80, smoke+deploy. Counter: 15/80 · at v1187 · target v1252. NEXT: read round 2 (dispatch → v1188). Also gitignored tv/.tvd_supervisor_pause (runtime flag).

## ✅ GATED: v1188 (16/80) — HEAD 9187ce0 — READ round 2 (bound genius-escalate) — ROUND-2 SWEEP COMPLETE
engine-read r2 (tv_diablo.py + test_agent.py): _maybe_genius escalate pass called _oneshot(timeout=90) decoupled from LIVE_READ_TIMEOUT_S → could hold lane ~125s if fired (dormant today, FAST==GENIUS; one env var from live). FIX: timeout=LIVE_READ_TIMEOUT_S. +1 test (agent 177→178). ×3 parity, floor agent 178 · control 80, smoke+deploy.

### ROUND-2 SWEEP DONE (v1185–v1188): funnel(honest-miss live driver) · route/gate(quorum tie=disagreement) · capture(captureTs drain-path) · read(bound genius-escalate). All evidence-based, tested. Counter: 16/80 · at v1188 · target v1252.
NEXT: round 3 of per-engine polish (dispatch → v1189+). Both round-1 and round-2 sweeps complete; engines increasingly hardened.

## ✅ GATED: v1189 (17/80) — HEAD 92df985 — ROUTE/GATE round 3 (dedupe never erases a receipt)
engine-route r3 (control_app.py + test_control.py): the v944 exact-sig dedupe branch nulled `routed` (historical fact = a receipt landed on this frameId) on any sig-dup → a receipted static-panel frame (receipt fires on newest, shares predecessor sig) got falsely reconciled as a miss + undercounted. FIX: guard with `routed is None` (mirrors near-dup branch). +3 tests (control 80→83). ×3 parity, floor control 83 · agent 178, smoke+deploy. Counter: 17/80 · at v1189 · target v1252.
LESSON: NO backticks in git commit -m messages (shell command-substitutes them → v1189 body lost two `routed` words, cosmetic). Use plain text / single quotes.
NEXT: round 3 continues — rotate to capture or funnel round 3 (dispatch → v1190).

## ✅ GATED: v1190 (18/80) HEAD ac7e041 — CAPTURE r3: footage archive torn-write fix (_archive_footage_copy → _cap_promote atomic pattern, tmp+size+os.replace); +3 tests (agent 178→181).
## ✅ GATED: v1191 (19/80) HEAD 29016e4 — ENGINE ROOM bulletproof open (Konyo "click does nothing"). Served code was CORRECT (his window = stale load); hardened _engineRoomOpen to show overlay first + guard each panel render + log [EngineRoom] failures loudly. control_ui.html. Konyo must RELOAD his console window (⌘R or quit+relaunch) to pick it up. NOTE: Chrome extension disconnected — couldn't browser-debug live; if it recurs after reload, need the [EngineRoom] console error.
Counter: 19/80 · at v1191 · target v1252. Round-3 sweep: route/gate ✅ capture ✅ (v1189/v1190); read + funnel round 3 pending.

## 🎯 MANDATE EXTENDED (Konyo 2026-07-22): +20 ENGINE ROOM ROUNDS = 100 TOTAL (v1173→v1272)
After the current 80 per-engine rounds (v1173→v1252), ship an EXTRA 20 rounds dedicated SPECIFICALLY to the ENGINE ROOM (the cockpit), Konyo-workflow style (agent army · Fable gates · Grok third-eye · version-per-round). So: 80 per-engine + 20 Engine-Room = 100 versions, v1173 → v1272. Work autonomously, gate each round as it lands.
The Engine-Room 20-arc (v1253→v1272) = deep polish of the cockpit: bulletproof open (done early, v1191) · live spine fidelity · retro scrub UX · drill-down detail depth · timeline clarity · per-organ readouts · owner/verdict authority surfacing · time-sync accuracy · visual/typography polish of the cockpit · "see what the AI sees" completeness. Lane: control_ui.html (polish-ui-2) primary + control_app.py data-surface support where needed. Konyo's north star: the Engine Room IS the visual debugger of the AI's mind — "I need to see what the AI sees so I can surgically fix and debug."
