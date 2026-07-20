# 🔍 DEBUG SESSION DOSSIER — 2026-07-20 (v927.1 → v935.8, "WindowServer crash" → "The Shell" → SuperGrok return)
_For Konyo's side-debug with SuperGrok (morning Claude leg). Every ship: symptom → root cause → fix → how to verify. One day, one arc. All pushed to main; tv suites green on every push; Routine I = CI verdict._

> **SuperGrok RETURN leg (evening):** see **`DEBUG_SESSION_2026-07-20_SUPERGROK_RETURN.md`** — shell tabs P0, text-eye chrome burn, exit-ON-AIR forever, Routine R/T heal. Claude: start there for the ping-pong.

## Part 1 — The crash recovery (v927.1–v927.5)
| Ship | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| v927.1 | Capture showed desktop wallpaper, not D2R | WindowServer crash wiped the Screen Recording TCC grant; the unsigned TV DIABLO.app wrapper can't re-prompt | Launcher self-reroutes Finder launches through Terminal (grant inherited at spawn); boot tab auto-closes | Double-click icon → boot log `Screen Recording OK` |
| v927.2 | Reads ~10s each, "ocr binary missing" | LIE: binary existed; v925 LIGHT ships the OCR lane OFF (`TV_OCR=0` default) | `TV_OCR=1` exported in launcher + honest skip message | Boot log `ocr warm — Vision ready (~50ms probe)` |
| v927.3 | Preview showed a previous session's photo ("still broken!") | `frames/live.bmp`/`eye.jpg` persist across sessions; dormant boot serves stale pixels | Agent boot deletes frames >30s old | Fresh boot shows splash, never an old photo |
| v927.4 | Mid-play: "D2R window missing" flicker, feed torn down | One flaky `CGWindowListCopyWindowInfo` poll (CrossOver fullscreen drops from the list) instantly closed the gate | 6s debounce grace before dormancy | No missing-banner flashes during play |
| v927.5 | "TALLIES · 0 synced" forever, on every surface, always | Bridge (:17771) had NO `do_OPTIONS`; every cross-origin `intake_result` POST died in CORS preflight, silently | `do_OPTIONS` (204 + allow content-type). ALSO: pgrep process-alive fallback for minutes-long loading-screen HOLDs | `curl -X OPTIONS :17771/intake_result` → 204 |

## Part 2 — One System (v928–v931.1)
| Ship | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| v928 | Rune/gem/material tallies NEVER fired hands-free | The auto-intake engine lives ONLY in bible.html JS; with just the console open, no engine existed. ALSO `private_mode=False` was claimed in a comment but never passed → app localStorage silently ephemeral for years | Engine board instance + real `private_mode=False` | — superseded by v931 |
| v928.1 | SIM retro had ~20 stills for a 6-min session | v925 LIGHT ships the FILM thread OFF too (same disease as OCR) | `TV_FILM=1` in launcher; control serves `/tv/frames/hist/` so replays render agent-off | Reel gains ~60 f_*.jpg per minute |
| v928.2 | Infinite mirror in preview; desktop frames archived | Film lane kept full-screen-grabbing with no game — privacy leak | Film obeys the game gate: no D2R → no capture | Close D2R → preview holds last game frame |
| v928.3 | Giant WATCHING/HOLD curtain cut the feed | Stale eye tore stage down to the splash | `film-held`: last real frame stays, dimmed, labeled with age | Loading screen → dimmed frame + "HELD · Ns old" chip |
| v929 | "What exactly was tallied?" | No drilldown existed | 🧰 TALLY ENGINE overlay: /api/tallies + per-shot cards (counts + the photo) | Click TALLIES chip |
| v929.1 | Grok r1 P0: process-alive fallback re-opened the desktop grab | auto mode fell through to full-screen with no window pin | LAW: no pin → no eye (capture_mac + film) | 'waiting' pin → zero new frames |
| v930 | Off-screen engine window: lamp said "linked", zero intakes | macOS suspends occluded off-screen WKWebViews — timers AND evaluate_js (pywebview call blocks forever, hung the driver thread) | `_ejs()` hard-timeout wrapper + control-side driver thread + truthful probed lamp | REG-033 |
| v930.1 | "6-min session, only 7 frames!" | Shelf list froze mid-seal while 437 frames folded into the reel; plus a NameError (`n` vs `i`) silently killed live-card thumbs | Shelf refetches on open; loop-var fix | Reopen shelf → true counts |
| v930.3 | Retro played WHITE frames instead of the game | Quartz window-grab of CrossOver's Metal surface returns a blank white backing that still "succeeds" (same 93,577-byte JPEG on repeat) | Grabs <150KB = failures → demote machinery gets real pixels; 306 white frames purged | Replay shows game pixels only |
| v931/.1 | Extra "TVD ENGINE" side window (ugly); materials tally silently eaten | Architecture: engine now an invisible same-origin IFRAME inside the console (JS alive because host visible; driver via contentWindow). Materials: second tab read hit the page shutter mid-runes-intake → visit slot burned on silent 'busy' | Serialized intake queue: one shot at a time, done only on JOURNALED receipt, one retry | One window only; sweep 3 tabs → 3 receipts |

## Part 3 — Three Eyes (v932–v934.3b)
| Ship | What | Verify |
|---|---|---|
| v932 | 👁‍🗨 TEXT-TRIGGERED EYE: continuous local OCR of the live eye; NEW item text (tooltips/tab swaps — invisible to motion-settle) → priority read of the frozen frame, bypassing the same-view dedup. Killed the "20 items shown, 4 reads" class (next session: 14 reads in 2.5min) | Hover items → `👁‍🗨 text eye — new text` events |
| v933 | 🔵 SECOND EYE rendered: blue timeline ticks, ⚡ pulsing recal markers on disagreements, verdict captions pinned to the re-checked frame | Timeline blue ticks after reads |
| v934 | 🧠 KAI THE CLOSER v1: post-seal reel sweep (warm OCR worker, nice'd), missed-text ledger, kai_report.json per reel, gold 🧠 timeline ticks | End session → `🧠 KAI closed the session` beat |
| v934.1 | KAI ghost-proofed: ledger rows obey ts==captureTs anchored in-session (split_sessions would have spawned ghost session blocks); honest shelf read counts | No duplicate session cards |
| v934.2 | Text eye pin-gated (was OCR-reading the DESKTOP during pin-waiting — burned a read on terminal text) | No reads while game closed |
| v934.3/b | Tally-driver telemetry (`driver: {seen,queued,fired,err}` in /api/status), flushed prints, failed fires re-queue | `curl /api/status` |

## Part 4 — The Shell arc (v935–v935.3, agent army: app-owner · ui-owner · theatre-owner)
| Ship | What | Verify |
|---|---|---|
| v935 | 🐚 THE SHELL: zero-reload tab switching — board tabs promote the engine iframe to a full-window pane (state persists BOTH sides), ⌂ CONSOLE/esc returns; TV·D tab = the console itself (stale peer dead) | Click Forge → instant pane, esc back — no reload |
| v935.1 | 🔴🔵🧠 signal panel humanized: THREE EYES badges w/ plain words; BRIDGE→Signal·connected, CAPTURE→Watching·"Diablo II window", LAST READ→Last thought, MODEL→footer; dark/seal/bridge/gate in a closed ⚙ drawer | Look at the right panel |
| v935.2 | **THE VANISHING TALLIES (P0)**: receipts POSTed to the agent bridge, which DIES at END SESSION — any tally finishing after seal lost its receipt forever (driver proved fired=1, journaled=0). Fix: control-side `/intake_result` (always alive, ±5min dedupe) + board dual-post fallback. PLUS 🚨 Watchdog v1 (tally tab visited ⇒ receipt must exist, else red beat) + KAI vocab grounded in 1,211 real item tokens (Windforce keeps, WARRIV dies) | Seal mid-tally → receipt still journals |
| v935.3 | ⏱ REAL means real: stale CUT/FULL skim-speed multiplier persisted into REAL mode (axis was always wall-true) — entering REAL pins 1× | 6-min session plays ~6 min |
| v935.4 | Grok seal-verdict P0: driver confirms receipts from the JOURNAL too (bridge dies at seal; post-seal control `/intake_result` was invisible → wedged queue) | Seal mid-tally → journaled ✓ |
| v935.5 | ONE SHELL layout: pane under persistent header (intent) | Tabs stay visible above board |
| **v935.6** | **TABS DEAD FIX (P0)**: root cause = `.shell {z-index:1}` stacking context trapped header UNDER fixed `#tvd-eng` (z-index 940) so clicks never hit `.ht`; engine iframe also lacked `?app=1` so `switchTab`/app-ctx never armed. Fix: fixed topbar @ z 960 on shell-open, pane sized under header, iframe `?app=1&engine=1#session`, route retry until `switchTab` ready, hide duplicate board tab rail in engine-driven pane | Click 🔨 Forge → board pane under header, gold active tab, esc/⌂/TV·D returns to console; Sessions/F·Uniques/F·Sets/Tools same |
| **v935.7** | **Text-eye chrome burn**: boot `_CAP_TARGET` was `full`, so text-eye OCR'd console STANDBY/LIVE and spent a Sonnet read. Fix: boot `waiting`, text-eye requires `mode=window` + `wid`, OCR noise list includes console chrome; early `engine-driven` body class | Boot ON AIR with no D2R → zero text-eye priority reads |
| **v935.8** | **Exit left ON AIR forever (P0)**: closing the console only `srv.shutdown()` — banner said "agent left as-is". Agent stayed live on :17771. Fix: `_console_exit_stop_onair` on window closed / webview return / atexit / SIGTERM/SIGINT — same as `tvd stop` (farewell off, seal + kill). Idempotent; `--window-only` skipped | Close console while ON AIR → agent dead, `:17771` free, log says `exit safeguard — stopping ON AIR` |

## Standing architecture (for SuperGrok context)
- **Three eyes + funnel doctrine**: 🔴 live (text-triggered) → 🔵 trailing verify → 🧠 KAI sweep → 📸 KAI v2 = frames chauffeured through the LOCKED vault/tally/item-checker pipeline (never a new reader). Spec: `tv/PLAN_ONE_SYSTEM.md`.
- **Read-only law**: screenshots only, no game input — auto-mule means automated *accounting*, never automated hands.
- **Journal law**: `ts == captureTs` (capture moment), completedTs = when the AI answered; frameId's filename IS its capture millisecond.
- **v925-LIGHT trap**: lanes ship OFF by default (`TV_OCR`, `TV_FILM`) — check LIGHT gates before debugging any "broken lane".
- Known-open: Watchdog `watchdog:None` until first sealed session; engine-vs-open-board double AI call (SET-safe, lease deferred); Cain-class NPC names ground KAI's vocab (harmless).
