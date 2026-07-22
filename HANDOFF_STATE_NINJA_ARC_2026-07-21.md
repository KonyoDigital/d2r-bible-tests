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

## ✅ GATED: v1192 (20/80) — HEAD b9bff60 — READ round 3 (rewarm lock-contention on live default)
engine-read r3 (tv_diablo.py + test_agent.py): _rewarm fires a 60s background health-ping holding w.lock on the SINGLE worker (POOL_N==1, live default) → next live read blocks up to 60s invisibly to LIVE_READ_TIMEOUT_S. FIX: `if POOL_N<=1: return` (worker self-heals on next ask()). +2 tests (agent 181→183). ×3 parity, floor agent 183 · control 83, smoke+deploy. Counter: 20/80 (QUARTER) · at v1192 · target v1252.
ROUND-3 SWEEP: route/gate(v1189) · capture(v1190) · read(v1192) done; funnel round 3 pending (→ v1193). [v1191 Engine Room bulletproof-open interleaved.] Test floor climbed 171→183 agent / 43→83 control across the mandate.
NEXT: funnel round 3 (dispatch → v1193).

## ✅ GATED: v1193 (21/80) — HEAD 1e25eb9 — FUNNEL round 3 (register tier best-wins) — ROUND-3 SWEEP COMPLETE
engine-funnel r3 (control_app.py + test_control.py): _kai_compile_register used "first tier wins" → a stale early border froze the register even after a later super-analyze proved grail. FIX: _KAI_TIER_RANK best-wins (grail>keep>border), tier-domain analog of never-zero. +5 tests (new coverage, control 83→88). ×3 parity, floor control 88 · agent 183, smoke+deploy.
### ROUND-3 SWEEP DONE (v1189/v1190/v1192/v1193 + v1191 ER open): route/gate·capture·read·funnel all 3× hardened. Test floor: agent 171→183, control 43→88 (65 new regression tests). Counter: 21/80 · at v1193 · target v1252 → then +20 Engine Room (v1253→v1272).
NEXT: round 4 of per-engine polish (dispatch → v1194+). Diminishing obvious bugs — watch for honest "no new gap" hand-backs and rotate/escalate to deeper/rarer classes.

## ✅ GATED: v1194 (22/80) — HEAD e2b7339 — ROUTE/GATE round 4 (grid-vote independence)
engine-route r4 (control_app.py + test_control.py): reel-scan credited the "grid" evidence class from the OCR-driven FUSED tab without checking grid was in the fusion sources → a single chrome-OCR read double-counted as tabstrip+grid, falsely clearing ≥2 quorum. FIX: pure _kai_grid_vote_label() with "grid in sources" check, falls back to raw pixel classify_stash_grid(). +5 tests (control 88→93). ×3 parity, floor control 93 · agent 183, smoke+deploy. Counter: 22/80 · at v1194 · target v1252 → +20 ER (v1272).
NEXT: round 4 continues — capture/read/funnel round 4 (dispatch → v1195). Honesty clause active (report no-new-gap rather than churn).

## ✅ GATED: v1195 (23/80) — HEAD 90de5d8 — CAPTURE round 4 (never-starve bridge un-starved)
engine-capture r4 (tv_diablo.py + test_agent.py): _archive_footage_copy advances the 1fps due-clock unconditionally before the write, so the never-starve fallback's 2nd call (bridge-last-good) was rejected by the clock the failed 1st call already advanced — dead code in its own failure case. FIX: _consume_due param, caller owns the due-gate once. +2 tests (agent 183→185). ×3 parity, floor agent 185 · control 93, smoke+deploy. Counter: 23/80 · at v1195 · target v1252 → +20 ER (v1272).
NEXT: read round 4 or funnel round 4 (dispatch → v1196). Round 4: route/gate ✅ capture ✅; read + funnel round 4 pending. Honesty clause active.

## ✅ GATED: v1196 (24/80) — HEAD dfc83ef — READ round 4 (one-shot budget compounding)
engine-read r4 (tv_diablo.py + test_agent.py): _oneshot spent LIVE_READ_TIMEOUT_S twice (gate-acquire wait + subprocess run) → up to 2×budget under the throttle-cascade the gate serializes. FIX: deduct gate-wait, pass max(1.0, timeout-elapsed). +2 tests (agent 185→187). ×3 parity, floor agent 187 · control 93, smoke+deploy. Counter: 24/80 · at v1196 · target v1252 → +20 ER (v1272).
NEXT: funnel round 4 (dispatch → v1197) completes round-4 sweep. Test floor: agent 171→187, control 43→93. Honesty clause active.

## 🎯 PRIORITY (Konyo 2026-07-22): THE CONSOLE > the website
The TV DIABLO CONSOLE (tv_diablo.py capture/read · control_app.py route/gate/funnel · control_ui.html cockpit) is the priority — MORE important than the website (bible.html D2R farming bible). The per-engine rounds + the +20 Engine Room arc ARE all console. bible.html is touched ONLY for the version-stamp/note (parity contract), not website features. Website feature work happens ONLY on explicit Konyo request (e.g. v1183 Blood, v1184 cube-up were his live reports). Keep autonomous effort on the console.

## ✅ GATED: v1197 (25/80) — HEAD 6283e2f — FUNNEL round 4 (routed-mark requires ok) — ROUND-4 SWEEP COMPLETE
engine-funnel r4 (control_app.py + test_control.py): _kai_build_routing marked a frame routed for any kai-funnel receipt without checking ok → a v1185 honest-miss (ok:false) got narrated as success + blocked re-selection (audit-trail bug; tally path safe via _intake_is_real). FIX: gate routed-mark on ik.get("ok"). +3 tests (control 93→96). ×3 parity, floor control 96 · agent 187, smoke+deploy.
### ROUND-4 SWEEP DONE (v1194/v1195/v1196/v1197): route/gate(grid-vote indep) · capture(never-starve bridge) · read(oneshot budget) · funnel(routed-requires-ok). All evidence-based, honesty-clause held. Test floor: agent 171→187, control 43→96 (85 new regression tests). Counter: 25/80 · at v1197 · target v1252 → +20 ER (v1272).
NEXT: round 5 (dispatch → v1198). 4 rounds deep — obvious bugs thinning; expect more honest "no new gap" → rotate/escalate to Grok third-eye audit or move toward the Engine Room arc early if engines converge clean.

## ✅ GATED: v1198 (26/80) — HEAD 4f13cd8 — ROUTE/GATE round 5 (retro-promote fabricated grid witness)
engine-route r5 (control_app.py + test_control.py): _kai_retro_promote_tally fabricated grid=True/gridLabel onto gridless cluster frames (borrowed neighbors' evidence) → 1-real-vote frame cleared 2-class quorum on a fake witness. Same false-independence as round 4, cluster level. FIX: removed the fabrication, kept honest label rewrite. +3 tests (control 96→99). ×3 parity, floor control 99 · agent 187, smoke+deploy. Counter: 26/80 · at v1198 · target v1252 → +20 ER (v1272).
THEME: the Accuracy Gate's evidence-independence keeps yielding real bugs (v1186 tie, v1194 fused-tab, v1198 cluster) — route/gate is the richest vein. NEXT: capture/read/funnel round 5 (dispatch → v1199). Honesty clause active; obvious bugs thinning — consider a Grok third-eye audit pass soon + the +20 Engine Room arc once engines converge.

## ✅ GATED: v1199 (27/80) — HEAD a7ba087 — CAPTURE round 5 (film cadence clock-skew → monotonic)
engine-capture r5 (tv_diablo.py + test_agent.py): _film_loop paced with wall-clock time.time() → a backward NTP/sleep-wake jump makes dt negative → sleep(~jump duration) → multi-minute film blackout. FIX: 3 t0-elapsed exprs → time.monotonic() (captureTs/frame_id/_FOOTAGE_DUE keep wall-clock). +1 test (source-lock). ×3 parity, floor agent 188 · control 99, smoke+deploy. Counter: 27/80 · at v1199 · target v1252 → +20 ER (v1272). NOTE: next ship = v1200 (round milestone).
NEXT: read/funnel round 5 (dispatch → v1200). Test floor: agent 171→188, control 43→99 (91 new tests). Honesty clause active — bugs thinning, watch for no-gap → rotate/Grok-audit/Engine-Room-arc.

## ✅ GATED: v1200 (28/80) — HEAD 5eb19f5 — READ round 5 (clock-skew sweep, 5 read-lane loops → monotonic)
engine-read r5 (tv_diablo.py + test_agent.py): swept the wall-clock→monotonic class across 5 read-lane deadline loops — critically VisionWorker.ask() (the LIVE_READ_TIMEOUT_S enforcement itself), OcrWorker.read(), _pool_shutdown+_verify_drain (shared deadline), _oneshot. Updated 2 round-1 tests to monotonic deadline domain. Flagged _live_stall_ms out-of-scope. +5 tests (agent 188→193). ×3 parity, floor agent 193 · control 99, smoke+deploy. Counter: 28/80 · at v1200 · target v1252 → +20 ER (v1272).
CROSS-ENGINE THEME v1199+v1200: wall-clock-vs-monotonic in pacing/deadlines (film loop + 5 read-lane spots). Possible remaining: control_app.py timing loops (funnel/route) may share the class — a candidate for funnel/route round 6. Test floor: agent 171→193, control 43→99 (96 new tests). NEXT: funnel round 5 (dispatch → v1201).

## ✅ GATED: v1201 (29/80) — HEAD 1d11fd8 — FUNNEL round 5 (closer-loop clock-skew) — ROUND-5 SWEEP COMPLETE
engine-funnel r5 (control_app.py + test_control.py): _kai_closer_loop's 2 receipt-wait loops (funnel-fire 120s, super-analyze 40s) were wall-clock pacing → backward jump = multi-minute SERIAL stall blocking the whole post-seal pass. FIX: monotonic anchors; _t0f kept wall-clock for its journal comparison + separate monotonic anchor. +4 tests (control 99→103). ×3 parity, floor control 103 · agent 193, smoke+deploy.
### ROUND-5 SWEEP DONE (v1198/v1199/v1200/v1201): route/gate(cluster grid-fabrication) · capture(film clock-skew) · read(5-spot clock-skew) · funnel(closer clock-skew). CROSS-ENGINE THEME = wall-clock→monotonic swept across film+read+closer. FLAGGED next: _intake_lease TTL (same class), _live_stall_ms (needs busy-lamp co-fix). Test floor: agent 171→193, control 43→103 (100 new tests!). Counter: 29/80 · at v1201 · target v1252 → +20 ER (v1272).
NEXT: round 6 (dispatch → v1202) — likely the flagged _intake_lease clock-skew (funnel) + fresh classes. Consider a Grok third-eye audit soon to seed round-6 leads.

## ✅ GATED: v1202 (30/80) — HEAD 336c77c — FUNNEL round 6 (intake-lease clock-skew)
engine-funnel r6 (control_app.py + test_control.py): _intake_lease compared `until` (wall-clock) directly → backward jump leaks a busy-tab lock. FIX: keep `until` wall-clock (surfaced to /intake_claim + /api/status), add internal untilMono for expiry. +7 REAL behavioral tests (control 103→110). ×3 parity, floor control 110 · agent 193, smoke+deploy.
### CLOCK-SKEW CLASS FULLY SWEPT (v1199 film · v1200 read×5 · v1201 closer×2 · v1202 lease). Remaining flagged: _live_stall_ms (needs busy-lamp co-fix, wider). Counter: 30/80 (milestone) · at v1202 · target v1252 → +20 ER (v1272). Test floor: agent 171→193, control 43→110 (107 new tests).
NEXT: round 6 continues / round 7 — the easy-vein clock-skew is exhausted; expect more honest no-gaps. Options: (a) capture/read/route round 6 fresh classes; (b) a Grok third-eye AUDIT pass to seed new leads; (c) start the +20 Engine Room arc early if engines converge clean. LEAN toward a Grok audit next to find non-obvious classes before more rounds.

## ✅ GATED: v1203 (31/80) — HEAD d58d2ea — ROUTE/GATE round 6 (live-row sources match winning label)
engine-route r6 (control_app.py + test_control.py): _kai_live_routing_row set sources=["read"] from raw names truthiness even when label was stash-* → _kai_reconcile false owner="ocr" (live telemetry only, sealed-wins overrides). FIX: sources track winning label. +4 tests (control 110→114). ×3 parity, floor control 114 · agent 193, smoke+deploy. Counter: 31/80 · at v1203 · target v1252 → +20 ER (v1272).

## ⚖️ DESIGN QUESTION SURFACED TO KONYO (engine-route r6 FYI, needs his call):
_router_conf maps BOTH read+judge to the same "content" class (v944.2). So a label=="tooltip" row can ONLY gate-pass if OCR ALSO independently read itemish text on that frame (pixel+content=2 classes). A pure read+judge tooltip (no OCR corroboration) ALWAYS fails quorum<2 by construction. Then _kai_super_select (requires gatePass=True) AND _kai_gate_pingpong_plan (requires skipReason "gate:") BOTH permanently exclude these frames from retry/rescue. → A FAST HOVER OCR NEVER SAW is permanently excluded from the deep-retro super-analyze rescue — which appears to undercut _kai_super_select's OWN stated purpose ("a fast-hovered item whose live read AND OCR both garbled stays unread forever... this is the deep retro pass that closes that gap"). This is EXACTLY Konyo's north-star motivation for the 4th organ (rescue fast hovers the live eye missed). But both exclusions are declared LAWs ("never re-read a frame the gate didn't prove" / ping-pong "conservative by design"); fixing = loosen a LAW or widen AI-call volume. AWAITING KONYO'S DECISION before any change here.

## 🟢 CAPTURE ENGINE CONVERGED (round 6 = honest NO-GAP, v1203 baseline, no ship)
engine-capture swept all 5 fresh classes with evidence, ruled each out: film thread can't escape its try/except (all Exception subclasses caught, incl MemoryError); no coordinate/geometry math in the capture path; _FILM_TIMES/_FOOT_TIMES/_EVENTS all bounded (maxlen/del); the _quartz tmp "leak" self-cleans within one loop tick (fixed dest_path, stale .part removed at next call start) — churn to "fix"; white-reject threshold proven-tuned (1736 frames, 0 false-pos, "AND bright" half protects dark frames). CAPTURE = 5 fixes (v1181/v1190/v1195/v1199 + blank-guard) then converged. DO NOT re-dispatch capture without a concrete new lead. Counter unchanged: 31/80 · at v1203.
NEXT: read/route/funnel may converge similarly soon. Forensic-fasthover (Konyo's fast-hover-rescue evidence trace) IN FLIGHT — his decision pending. When engines converge, pivot: Grok third-eye audit for non-obvious classes, OR start the +20 Engine Room arc.

## ⚖️ RESOLVED — fast-hover-rescue design question: NOT A REAL GAP (forensic-fasthover, 2026-07-22)
Konyo chose "investigate first." forensic traced ALL 26 sealed sessions (his fast-hover test day). The code mechanism (read+judge=same "content" class → quorum<2 tooltip → excluded from super-select+ping-pong) is 100% real, BUT 0 items lost / 24 quorum<2 tooltip rows accounted for (19 = genuine noise, KAI's own contemporaneous read = names:[]; 5 = Hard Leather Armor, already in register via live deep-read + inline judge). ARCHITECTURAL REASON: _kai_compile_register (control_app.py:2455) builds the register DIRECTLY from live journal (lane:deep names + lane:kai tiers) with ZERO dependency on gatePass/skipReason/quorum. The gate/ping-pong/super-select is a downstream RETRO-FIRE (spend an EXTRA judge call) layer, NOT the register's source of truth. A named item is registered the moment the live read fires. VERDICT: leave the law alone (recommended + Konyo-aligned). Optional belt-and-suspenders (super-select also admit gateReason==quorum<2 + tooltip + content-only sources + _kai_super_already_named clear) documented but HELD until a real recurrence. Data: sessions.jsonl (897KB) + frames/hist/reel_<sid>/kai_report.json (routing/register/missed).

## ✅ GATED: v1204 (32/80) — HEAD ddb40dd — READ round 6 (stall-worker orphan-process leak)
engine-read r6 (tv_diablo.py + test_agent.py): _STALL_WORKER (stall-drain net, kept outside _WORKERS by design) never .stop()'d → orphan claude -p subprocess (~200-600MB, quota) leaks forever when the stall path fires; accumulates per supervisor-respawn. FIX: _pool_shutdown stops it (no-op if never created). +2 tests (agent 193→195). ×3 parity, floor agent 195 · control 114, smoke+deploy. Counter: 32/80 · at v1204 · target v1252 → +20 ER (v1272).
NOTE: this leak is MORE likely now BECAUSE of the console supervisor (routine respawns) — good that it's fixed. Test floor: agent 171→195, control 43→114 (113 new tests).
NEXT: route/funnel round 6/7, or engines converging → pivot to Grok audit / Engine Room arc. Capture already converged.

## ✅ GATED: v1205 (33/80) — HEAD 0e7a1b8 — FUNNEL round 7 (engine-driver unbounded memory leak)
engine-funnel r7 (control_app.py + test_control.py): _engine_driver's live_judged set (function-scope, thread runs process-lifetime) grew unbounded (one per judge-candidate, never trimmed; frameIds globally unique so old ones useless). FIX: bounded _drv_live_judged_reserve(cap=2000, clear+re-add on cross). +5 tests (control 114→119). ×3 parity, floor control 119 · agent 195, smoke+deploy. Counter: 33/80 · at v1205 · target v1252 → +20 ER (v1272).
RESOURCE-LEAK MINI-THEME (v1204 orphan process + v1205 unbounded set) — both amplified by the always-on supervisor; both fixed. Test floor: agent 171→195, control 43→119 (118 new tests). NEXT: route round 7 or engines converging → Grok audit / Engine Room arc.

## 🟢 ROUTE/GATE ENGINE CONVERGED (round 7 = evidence-backed NO-GAP, v1205 baseline, no ship)
engine-route swept with specifics: all route/gate-domain accumulators bounded (_super_recovered/_attempted per-reel-GC'd · gate_pingpong tries per-reel-file · _ENGINE_FRAMES_LIVE deque(16) · _GATE_COUNT/_COMPLETENESS single-slot dicts · _label_last/_prev_sig call-local · live_judged already-capped-v1205 · judge_q<16 · fire_q reset). Concurrency: _kai_build_routing/reconcile/gate_check/quorum all PURE, threads share only files (kai_report atomic os.replace, sessions.jsonl append-only w/ torn-line try/except). Sealed-wins _kai_engine_frame_effective correct (no None-collision). Cross-tab register keyed by name globally (correct by design). ROUTE/GATE = 6 fixes (v1180/1186/1189/1194/1198/1203) then converged.
### ENGINES CONVERGED: 📷 capture (5 fixes) · 🚦 route/gate (6 fixes). STILL ACTIVE: 🔴 read (6 fixes, r6=orphan leak real) · 🩹 funnel (7 fixes, r7=mem leak real). Counter: 33/80 · at v1205.
### PIVOT PLAN as engines converge: (1) keep read+funnel rounds while productive; (2) when all 4 converge, a GROK THIRD-EYE AUDIT to re-seed non-obvious classes (Konyo-workflow signature); (3) then the +20 ENGINE ROOM arc (v1253→v1272). NOTE: honesty clause means the full 80 per-engine may resolve as "converged early" rather than 80 forced bugs — Konyo values honesty over version-count. Surface this to Konyo at the next natural checkpoint.

## ✅ GATED: v1206 (34/80) — HEAD f03697f — READ round 7 (core _WORKER + _OCR orphan leaks)
engine-read r7 (tv_diablo.py + test_agent.py): _pool_shutdown skipped _WORKER (index 0, CORE live-read subprocess) for a farewell that's OPT-IN/OFF by default → orphans EVERY session close in Konyo's config (bigger than v1204). _OCR never stopped anywhere. FIX: keep_worker0 param (threaded from close_session's farewell bool) + unconditional _OCR.stop(). +3 tests (agent 195→198). ×3 parity, floor agent 198 · control 119, smoke+deploy. Counter: 34/80 · at v1206 · target v1252 → +20 ER (v1272).
RESOURCE-LEAK THEME now 3 fixes (v1204 stall-worker · v1205 mem-set · v1206 core-worker+OCR) — ALL amplified by the supervisor I installed; all fixed. This was a genuinely high-value vein (orphan claude -p procs burning RAM+quota every session). Test floor: agent 171→198, control 43→119 (121 new tests). NEXT: read may converge next round; funnel round 8; then Grok audit + Engine Room arc.

## ✅ GATED: v1207 (35/80) — HEAD 680b845 — FUNNEL round 8 (closer OCR worker never orphaned)
engine-funnel r8 (control_app.py + test_control.py): _kai_closer_loop's per-reel ocr_mac --worker (wp) cleanup was after the loop, not in try/finally → any per-frame exception orphans wp, and COMPOUNDS per reel. FIX: try/finally wrap (pure re-indent, diff -b = 11 real lines, verified no logic drift + py_compile). +2 tests (control 119→121). ×3 parity, floor control 121 · agent 198, smoke+deploy. Counter: 35/80 · at v1207 · target v1252 → +20 ER (v1272).
RESOURCE-LEAK THEME = 4 fixes (v1204/1205/1206/1207) — orphan claude/ocr procs + unbounded set, all amplified by supervisor. Genuinely the highest-value vein of the mandate. Test floor: agent 171→198, control 43→121 (123 new tests). NEXT: read/funnel likely converge next round; then Grok audit + Engine Room arc.

## 🟢 READ ENGINE CONVERGED (round 8 = exhaustive evidence-backed NO-GAP, v1207 baseline, no ship)
engine-read grepped ALL 4 worker sites (all now cleaned v1206/1207), all 16 Popen/run (one-shots reaped by CPython, long-lived ones tracked), all open() (all `with`), all per-iter loop cleanups (all try/except per-iteration), all accumulators (_TEXT_EYE_BACKLOG cap32 · _SLOT_DEATHS deque8 · _REWARM_AT/_ESCALATE_N bounded), parse-edge (_parse_audit v835 already hardened 3×), off-by-ones (already boundary-tested). READ = 7 fixes (v1179/1188/1192/1196/1200/1204/1206) then converged.
### DECLINED (flagged, non-shippable at this depth — for the record): (a) _note_slot_death mutates _SLOT_DEATHS/_THROTTLED_UNTIL[0] unlocked from 2 threads — but list-append/index-assign are GIL-atomic, worst case = both compute near-identical throttle deadline (benign, no corruption/crash). (b) _settle_queue_clear runs only at close_session not startup → a hard-kill leaves a few bounded .bmp in frames/queue/ until next graceful close (disk-only, bounded, unreachable-by-in-process-code either way). Both = defensive nice-to-haves, NOT correctness bugs.
### ENGINES CONVERGED: 📷 capture(5) · 🚦 route/gate(6) · 🔴 read(7). ACTIVE: 🩹 funnel(8 fixes, round 9 dispatched). Counter: 35/80 · at v1207.
### PIVOT IMMINENT: when funnel converges → all 4 engines done → (1) Grok third-eye AUDIT (re-seed non-obvious classes across whole console) → (2) +20 ENGINE ROOM arc (v1253→v1272). Per-engine mandate converging HONESTLY at ~35 real fixes (not 80 forced) — surface to Konyo: honesty-over-count means the "80" resolves as thorough convergence + the real remaining value is the Engine Room arc.

## ✅ GATED: v1208 (36/80) — HEAD e23ff17 — FUNNEL round 9 (straggler receipt → right session)
engine-funnel r9 (control_app.py + test_control.py): /intake_result tagged a straggler receipt to the LATEST journal sessionId → in back-to-back farming, session A's slow POST lands after session B started → mis-tagged onto B, pollutes B's tally + suppresses a real gap-funnel. FIX: extract sid from frameId (reel_<sid>/, timing-immune) when reel-shaped; fall back to journal-scan for board calls. +3 real e2e tests (control 121→124). ×3 parity, floor control 124 · agent 198, smoke+deploy. Counter: 36/80 · at v1208.
NOTE: funnel did NOT converge (round 9 = real fix). Funnel = 9 fixes now, most productive engine. Capture/route/gate/read converged. Test floor: agent 171→198, control 43→124 (126 new tests). NEXT: funnel round 10 (last?) or converge → then Grok audit + Engine Room arc.

## ✅ GATED: v1209 (37/80) — HEAD 8739dd9 — FUNNEL round 10 (gate-pingpong atomic write)
engine-funnel r10 (control_app.py + test_control.py): gate_pingpong.json bare open+json.dump → torn write on crash forgets retry-tries → a maxed frame re-tried past cap (API-cost, not grail). FIX: route through _kai_write_report_atomic. 3 angles swept clean. +1 test (control 124→125). ×3 parity, floor control 125 · agent 198, smoke+deploy. Counter: 37/80 · at v1209.
FUNNEL = 10 fixes, STILL not converged (most productive engine by far). Test floor: agent 171→198, control 43→125 (127 new tests). NEXT: funnel round 11 or converge → Grok audit + Engine Room arc.

## 🎉🟢 FUNNEL CONVERGED (round 11 evidence no-gap, v1209) — ALL 4 ENGINES CONVERGED — PER-ENGINE ARC COMPLETE
engine-funnel checked at correctness-bar: reconcile narration (consistent w/ v1193/v1197), dedupe (_csig can't collapse different finds), lease retry (no data loss), super-already-named (skips opportunity only), watchdog, register session-filter — all clean. Declined 2 below-bar (bible.html-LOCKED client double-apply; gate-check false-neg = efficiency not loss). FUNNEL = 10 fixes.
### ★ ALL 4 ENGINES CONVERGED: 📷 capture(5) · 🚦 route/gate(6) · 🔴 read(7) · 🩹 funnel(10) = 28 engine correctness fixes. Total mandate: 37 versions (v1173→v1209) = integer-reset + typography R1-R5 + stability + supervisor + Blood/cube-up + Engine-Room-bulletproof + 28 engine fixes. 127 new regression tests (agent 171→198, control 43→125). ALL GREEN.
### PER-ENGINE MANDATE RESOLVED HONESTLY: the "80 per-engine" converged at 37 real versions — every real bug found + fixed + tested, convergence declared with evidence when veins dried, NO churn (Konyo's honesty-over-count principle). The 4 engines are now genuinely hardened.
### PIVOT NOW: (1) OPTIONAL Grok third-eye audit (re-seed non-obvious cross-console classes). (2) THE +20 ENGINE ROOM ARC (v1210+ → cockpit build/polish, the flagship Konyo's most excited about — will NOT converge, it's build not bug-hunt). Lane: control_ui.html (polish-ui-2) + control_app.py data-surface. Spec seeds in ENGINE_ARCHITECTURE.md §THE ENGINE ROOM + the arc list in the mandate section above.

## ✅ GATED: v1210 (38/80) — HEAD 741e91e — 🧠🖥 ENGINE ROOM ARC ROUND 1 (read-chain strip)
polish-ui-2 (control_ui.html): read-chain strip in the per-frame drill-down — 5-node pipeline 🔴live→🔵second→🧠KAI→🧠🔬super→🚦gate, lit=fired, gold-ring OWNS=owner (from Phase-D reconciler). Live-node fire aligned to owner-row inference (no contradiction). Widened label col (no 2-line wrap). Reads existing beat/liveRing fields, no new endpoints. ×3 parity, floor control 125 · agent 198, demo 7/7 + closeability held + bulletproof-open untouched, smoke+deploy.
NOTE: :17772 was down + supervisor pause-flag STALE (Konyo's scan ended) → cleared the flag, supervisor auto-restored console @ v1210. Konyo can reload to see the read-chain strip. Counter: 38/80 · at v1210 · +20 ER arc = round 1/20 done → v1272.
### ENGINE ROOM ARC PROGRESS: 1/20. Remaining ~19 rounds of cockpit polish (control_ui.html primary): spine engine-health clarity, retro scrub UX, timeline "you are here", per-organ readouts, owner/verdict legend, live+retro time-sync visual, typography/visual polish of the cockpit, "see what the AI sees" completeness. polish-ui-2 owns the lane.

## ✅ CONFIRMED: v1211 (39/80) landed HEAD 188996c — ER arc 2/20 (labeled playhead flag). LESSON: do NOT pkill/restart the headless console until AFTER the pre-push demo hook clears — a mid-respawn console flaked the demo hook once (false "push blocked"); re-push clean succeeded. Console live @ v1211. NEXT: ER arc round 3 → v1212.

## ✅ GATED: v1212 (40/80 MILESTONE) — HEAD 70444c2 — 🧠🖥 ENGINE ROOM ARC ROUND 3 (live health pills)
polish-ui-2 (control_ui.html): HEALTHY/STRAINED/DOWN/IDLE pills per organ on the cockpit LIVE spine (bottleneck reads at a glance). Scoped to big cockpit organs (home small-cards + retro spine = 0 pills, verified). Mirrors existing pulse, no new semantics. ×3 parity, floor control 125 · agent 198, demo 7/7, smoke+deploy. Console restored @ v1212. Counter: 40/80 (HALFWAY to v1252) · at v1212 · ER arc 3/20 → v1272.
PUSH LESSON REINFORCED: detached push can look "died" if checked too early — the harness task notification is the source of truth (exit 0 = landed). Round 4 dispatched (in flight → v1213).

## ✅ GATED: v1213 (41/80) — HEAD d922af7 — 🧠🖥 ENGINE ROOM ARC ROUND 4 (always-visible key)
polish-ui-2 (control_ui.html): compact always-visible KEY footer decoding read-chain (🔴🔵🧠🧠🔬🚦) + health dots in one quiet line, present all 3 states, subtle. Cockpit now self-documenting. ×3 parity, floor control 125 · agent 198, demo 7/7, smoke+deploy. Console @ v1213. Counter: 41/80 · at v1213 · ER arc 4/20 → v1272. Round 5 in flight → v1214.

## ✅ GATED: v1214 (42/80) — HEAD 90e2c84 — 🧠🖥 ENGINE ROOM ARC ROUND 5 (sealed|live boundary). Console @ v1214. ER arc 5/20 → v1272. Round 6 in flight → v1215.
