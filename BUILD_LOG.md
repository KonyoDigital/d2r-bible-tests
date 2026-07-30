
## v1462 — 2026-07-30 — the icon, the launcher's last non-ASCII, and test port isolation
Three follow-ups Konyo asked for after the v1460/v1461 ships. The first one nearly re-shipped
the v1460 bug, and only a controlled A/B caught it.

**1. pywebview 6 `icon=` drift (REG-053) — and the trap inside the fix.**
`create_window()` dropped `icon=` in pywebview 6 (6.2.1 is what's installed here); it moved to
`start(icon=)`. The old code passed `icon=` to `create_window` and caught the resulting
`TypeError` into a hardcoded reduced call, so on v6 every window silently lost its icon **and**
`text_select` / `confirm_close` / `easy_drag` — options v6 supports perfectly well. Replaced the
guesswork with `inspect.signature`: keep every option the installed version accepts, and route
the icon to whichever call owns it.
**The trap:** routing the icon to `start()` on Windows with the existing `.png` candidate made
the WebView2 host window **never show** — silently, no exception, no log line. Measured A/B,
same command, only the icon file differing:

| icon file | window |
|-----------|--------|
| `tv_diablo_icon.png` | `IsWindowVisible = False` |
| none | `IsWindowVisible = True` |
| `appicon.ico` | `IsWindowVisible = True` |

That is the v1460 dead-icon failure exactly, and a naive "fix the icon" would have re-shipped it
to every machine that has an icon file. Windows now takes **`appicon.ico` only** (it already
ships, the Desktop `.lnk` uses it); a non-`.ico` is refused outright, because a missing icon is
infinitely cheaper than a missing window. The `.png` candidates stay Mac/Linux-only.

**2. `tv/start_tvd_win.ps1` is ASCII again (REG-046 hygiene).** 8 em-dashes had crept back into
v1444–v1448 comments. The BOM meant the parse gate still passed, so this was latent rather than
broken — but the standing rule is Windows ship `.ps1` files stay ASCII. Comments only; no code
touched; BOM preserved; parse + embedded-C# compile re-gated.

**3. `test_control.py` port isolation.** It never set `TV_CONTROL_PORT`/`TV_PORT`, so importing
`control_app` bound the module globals to the REAL 17772/17771. Nothing binds them today (the
suite boots its own Handler on an ephemeral port), but a future test calling
`_sock_open(CONTROL_PORT)` or `_reclaim_headless_for_scan()` would reach into Konyo's running
app. `test_agent.py` has guarded its agent port this way since v711; same courtesy now.
**Correction to the v1461 ship note:** I had claimed test_control kills a live TV DIABLO. It does
not — proven by running both suites with the app up (pid 21112 survived, window visible, API
serving). The earlier death was my own cleanup, misattributed. This change is hardening, not a
bug fix.

- **Verify:** PS parse 0 errors · embedded C# compiles · BOM present · 0 non-ASCII ·
  py_compile ×4 · `test_agent` **201 OK** · `test_control` **267 OK** (3 consecutive clean runs) ·
  cold launch through the real `.lnk` chain with the `.ico` active →
  `launch complete (window up)`, 1 window `VISIBLE=True`.
- **Known flake (pre-existing, not from this arc):** `test_doctor_endpoint_live` errored once in
  5 runs — `_get()` uses a 3s urlopen timeout against `/api/doctor`, which the launcher itself
  documents as slow; it tripped while the box was loaded with icon experiments. Green 3/3 after.

## v1461 — 2026-07-30 — Windows: test_agent finally green, 201/201 (REG-052)
- **Symptom:** `tv/test_agent.py` = **7 failures + 2 errors** on Windows, green on the Mac.
  Every one in a fake-worker fixture; the giveaway in the noise was
  `⚠ read failed: [WinError 193] %1 is not a valid Win32 application`.
- **Root cause:** the fakes are **scripts**, and the seams that carry them
  (`CLAUDE_BIN` → argv[0] of `_claude_lean_args`; `TV_OCR_BIN` → argv[0] of
  `_ocr_worker_cmd`) hold a single executable **PATH**. On the Mac `fake_claude.py`'s shebang
  and the `#!/usr/bin/env bash` OCR fakes are directly executable; on Windows neither is a
  valid CreateProcess image, so **the worker never started** and every assertion read `None`.
- **Second, hidden cause:** `_ocr_worker_cmd()` returns the real `ocr_win.ps1` on Windows
  **before** it ever consults `OCR_BIN` — so the OCR fixtures, which patched only the module
  global `tv.OCR_BIN`, were silently driving the genuine Windows OCR script.
- **Rejected fix (recorded so nobody retries it):** wrapping the fake in a `.cmd` shim. It
  works, but inserts a process between the worker and the fake — `p.kill()` reaps the shim
  and **orphans** the real child still holding the stdout pipe. That is exactly the leak the
  v1204/v1206 shutdown tests police, and it hung `TV_FAKE_MODE=slow` forever (observed live:
  `python.exe` pid 25100 surviving its dead cmd.exe parent).
- **Fix:** new `_argv_seam(env, default)` in `tv_diablo.py` — an **optional JSON-list**
  override for a spawn's argv prefix (`TV_CLAUDE_ARGV`, `TV_OCR_ARGV`). The suites pass
  `[sys.executable, "-u", fake]`, so the interpreter is spawned **directly**: process tree
  one deep, kill semantics identical on every platform. Unset in production → byte-identical
  behaviour (asserted: unset keeps `claude -p`; malformed JSON falls back to `CLAUDE_BIN`).
  This mirrors what `_ocr_worker_cmd` already did for the Windows OCR lane (powershell+.ps1).
  The two bash OCR fakes are now one Python implementation (`write_fake_ocr`), so the
  duplicated copies can no longer drift.
- **`CLAUDE_BIN` still points at `fake_claude.py`** on purpose: `_vision_budget_armed()`
  disarms the subscription circuit by finding `fake_claude` in its basename. The argv seam
  carries the spawn; the path carries the identity.
- **A false pass, now real:** `test_timeout_kills_worker_returns_none` was PASSING on Windows
  for the wrong reason — it asserts `r is None` and `w.p is None`, which a *failed spawn*
  also satisfies. It never exercised the timeout path at all. Proven real now: the worker
  spawns (pid), answers `Worker Keep`, reuses one process across turns, and reaps to `None`.
- **Verify:** `test_agent` **201 OK** (was 7F/2E) · `test_control` **267 OK** (2 skipped) ·
  py_compile both · no orphaned `python.exe`/`cmd.exe` after the run · suite back to ~11s.

## v1460 — 2026-07-30 — Windows: the Desktop icon actually opens (REG-051)
- **Symptom (Konyo, live):** double-click Desktop **TV DIABLO** → two black consoles blink and
  close, no app. Repeatable, every time, for days.
- **ROOT CAUSE:** `tv/start_tvd_win.ps1` spawned the app with
  `Start-Process pythonw ... -WindowStyle Hidden` (added in **v1444**, `c43bb1e`). That sets
  `STARTUPINFO.wShowWindow = SW_HIDE`, and .NET WinForms applies the startup show-command to the
  process's **first top-level window** — which is pywebview's WebView2 host window. So the window
  was created perfectly (title `TV DIABLO`, 1120x737, on-screen) and then **never shown**. The flag
  was never needed: `pythonw.exe` is a GUI-subsystem binary with no console to hide.
  Proven A/B on the Hebrew-locale box: same script spawned `-WindowStyle Hidden` →
  `IsWindowVisible False`; spawned default → `True`.
- **Why it stayed invisible for days:** the *same* v1444 commit swapped the ready probe from
  `doctor.ok` to `/api/status`. Control answered on :17772, so the launcher logged
  `ready status OK` + `launch complete` for a process with no window, and `mode=off` means
  nothing is ever written to `control_agent.log` — zero diagnostics at boot.
- **Fixes (all Windows lane):**
  1. `-WindowStyle Hidden` removed from the spawn — the actual cure.
  2. `Focus-TvdWindow` (PS) + `_win_focus_existing_console` (py) no longer skip non-visible
     windows and no longer handle only `IsIconic`; they `SW_SHOW` a hidden window, and return
     **true only when it is really visible** (a cross-process `ShowWindow` does not reliably
     un-hide a WinForms window born `SW_HIDE` — measured, so it must be verified not assumed).
  3. `Stop-Job -Force` → `Stop-Job` + `Wait-Job`. `Stop-Job` has **no** `-Force` on Windows
     PowerShell 5.1, so the 12s-timeout branch threw a ParameterBindingException past
     `-ErrorAction` into the outer catch and the job was never stopped: it kept running and its
     `merge --ff-only`/`reset --hard` rewrote `control_app.py` + `control_ui.html` **0.59s after
     python had already started** (measured: python 01:16:24.615, tree rewritten 01:16:25.207),
     leaving the app serving swapped UI files from stale code. New `Wait-TvdGitQuiet` also blocks
     the spawn until no `git.exe` is running, since `Stop-Job` does not kill the job's git child.
  4. `_request_console_exit` no longer falls back to `hide()` when `destroy()` raises — that
     combination produced the worst state: process alive holding :17772 with an invisible window
     and no recovery path. Destroy only; the `_arm_force_exit` deadline is the guarantee.
  5. Launcher log tells the truth (Law 9): `launch complete (window up)` vs
     `WARN control up but NO TV DIABLO window`, plus a warning if `control_app.py` is rewritten
     mid-boot.
- **Parity (Law 11):** `tv/WINDOWS_SHIP.json` and `tv/WINDOWS_KONYO_BOARD.md` were frozen at
  **v1448** while the triple stamp had reached v1459 — 11 versions of drift. Both re-stamped;
  triple stamp `tv_diablo.VERSION` == control `"ver"` == `bible.html` D2R_BUILD.id == **v1460**.
- **Verify:** PS `Parser::ParseFile` 0 errors · embedded C# compiles · `py_compile` OK · BOM intact ·
  cold launch through the real `.lnk` chain →
  `focused existing TV DIABLO window [visible raised=True]` + `launch complete (window up)`,
  `EnumWindows` → exactly **1** window `VISIBLE=True`, `MainWindowTitle='TV DIABLO'` (was empty
  through the whole zombie era) · second double-click → `control already up - focusing`, still
  1 window / 1 `pythonw`.
- **Follow-up (not shipped here, logged in BUGS.md):** pywebview **6.2.1** dropped `icon=` from
  `create_window()` (it moved to `start(icon=...)`), so `open_control_window()`'s
  `except TypeError` fallback silently discards `confirm_close`/`text_select`/`easy_drag` and the
  icon on any box where an icon file exists. Latent here (neither candidate file is present).
  Left untouched deliberately — that path is cross-platform and the handoff forbids touching the
  Mac lane without proof.

## v1380.0 — 2026-07-25 — G5 Grok Eyes (SuperGrok subscription CLI)
- Additive optional vision lane: `grok -p` + SuperGrok login (NO XAI_API_KEY / api.x.ai)
- Modes OFF (default) / SHADOW / PRIMARY — console ⚙ advanced 3-way switch
- Cousin-safe; removable fences GROK EYES (G5); sidecar prove + unit tests
- Claude path unchanged when OFF

## v1458 — 2026-07-30 — G4 Grok add-on REMOVED · G5 failure surfaced
- **G4 (api.x.ai API-KEY accuracy add-on) DELETED** — dormant, never activated, and its lane
  violates Konyo's rule that Grok runs on the SuperGrok SUBSCRIPTION only. Removed exactly as
  `tv/G4_GROK_REMOVAL.md` prescribed: `tv/g4_grok.py` gone, all fenced blocks stripped
  (191 lines control_app.py + 170 bible.html), `.gitignore` state line dropped.
  **0 traces** of `g4_grok` / `_g4` / `GROK ADD-ON` remain; control_app compiles; every real
  inline bible script still compiles (the 4 `type="application/json"` blocks are data, and
  fail-to-compile identically before and after — not JS). Reversible in one revert.
- **G5 Grok Eyes KEPT** (Konyo's mandated primary vision lane, `grok -p` + SuperGrok, no keys)
  and made honest: a primary-lane failure used to fall through to Claude while
  `_STATS["last_error"]` held the reason and nobody ever saw it. The agent event now carries
  the WHY (`⚠ G5 primary vision returned None — Claude fallback · why: grok CLI not on PATH`),
  and the console's G5 card shows its own intake-lane `last_error` + error/call counts.
- Suites: test_control 264 OK · test_agent 201 OK · visual-lock OK.

# D2R Bible — Build Log (cross-agent shared memory)

> **Purpose:** a single Obsidian-friendly log so understanding is **never lost in
> context** between Claude Code (CC), Claude Desktop, and Konyo. Append a dated
> entry whenever something ships or a decision is made. Maintained continuously by
> CC's logging loop.
>
> **Companion docs (cross-referenced):** `TRACKING.md` (**the living project board +
> ship gate — nothing is real until listed/shipped there**) · `GAME_RULES.md`
> (durable RoW game-truth + drop-odds provenance + deploy/CI facts) · `BUGS.md`
> (regression log, `REG-NNN` / `TV-NOTE-NNN`).

## 2026-07-19 — Grok: v901 Auto Intake · SESSIONS · Robot frozen

- **Product:** ON AIR default = Auto Intake (settle → feed locked Tools/Vault 📸). Continuous multi-worker Robot FROZEN (`TV_ROBOT=1` only).
- **IA:** Console home tab **SESSIONS**; TV·D peer tab hidden; `#tvd*` → session.
- **Agent:** `POOL_N=1`, no heartbeat dual-lane, gap 3.5s, film ~5fps; no-game pause kept.
- **Board:** `tvVaultAutoIntake` for personal/shared; tally tabs via `tvStashAutoIntake`.
- **Gates:** agent+control **182 OK**; triple stamp v901; Fable/Claude third-eye pingpong still the critique lane.
- **Files:** `tv/tv_diablo.py`, `tv/control_app.py`, `tv/control_ui.html`, `bible.html`, tests, README, PINGPONG_LOG.

## How the agents split work
- **Desktop** = visuals/features; often pushes straight to `main` WITHOUT running
  the suite (recurring — Routine I CI is the BACKSTOP, not the gate).
- **CC** = routes/backend/symmetry/test-integrity + end-to-end shipping
  (commit → Cloudflare deploy → md5 parity → push).
- **Konyo** routes prompts between the two and plays **Reign of the Warlock (RoW)**,
  NOT vanilla D2R.

## Key invariants (do not regress)
- `bible.html` is a single-file app. Central helpers `artOr()` / `openDrop()` /
  `switchTab()` have **site-wide blast radius** — edit them → re-run the WHOLE suite.
  (REG-001: a Safari fix dropped `loading="lazy"` from `artOr()` → load-storm → 3 red.)
- Pre-push smoke gate runs `01_smoke + v71_d2art + v74_material_search +
  v80_endgame_relics` automatically (`hooks/pre-push`, `core.hooksPath=hooks`).
- Deploy is MANUAL: `cp bible.html /tmp/d2r_dist/d2r/index.html && cd /tmp/d2r_dist &&
  set -a && . ~/.config/cf-d2r/env && set +a && npx wrangler@latest pages deploy .
  --project-name=d2r-bible --branch=main`; then verify md5 parity
  (`curl -s -A 'Mozilla/5.0' https://bull-4-u.com/d2r/ | md5 -q` == `md5 -q bible.html`).
- Dead-fork strays (`H_sweep.js`/`K_perf.js`/`J_screens.js`/`L_integrity.js`) get
  spurious local edits — `git checkout --` them, NEVER commit. `git status` before commits.

## 2026-07-17 — v765 THE THEATRE (eyes on history, in the app)

- **What:** the SIM button reborn as THE THEATRE — replays REAL past sessions in the
  control app: archived frames full-bleed w/ scanline grade, caption bar (time · read # ·
  🗺 area · scene · name chips · portal notes), beat timeline scrubber (named reads stand
  taller), play/pause · 1×/2×/4× · 9-session paginator. Zero agents — pure eyes-on-history.
- **Why:** "it's not really simulated anymore… its own independent VIEW." Plus two live
  bugs: /api/stop no longer opens a phantom board window and skips the 90s farewell wait
  for sim agents (the stuck-SIM screen); restart uses the open-once guard.
- **Also:** toggle-glow buttons (lit while their mode runs, re-click = off) · Grok-audit
  batch — ONE version truth v765 everywhere, chronicle NEGATIVES locked (garble/'Ring'/
  'Grand Charm' never chronicle), control_agent.log 2MB rotation, dead "flip the switch" copy.
- **Server:** /api/sessions · /api/session?n · /hist/<id>.jpg (path-safe).
- **Tests:** control **7/7** (new `tv/test_control.py`: theatre endpoints · hist traversal
  block · stop-never-opens-board · open-once) · agent 57/57 · board 14/14 · live on his 9-session archive.

---

## 2026-07-17 — v763+v764 TV → THE CHRONICLES + the switch becomes a LAMP

- **v763 chronicle routing:** ONE head `window.tvChronicleRoute` knocks on each engine's
  door — uniques→toggleOwned (dated foundLog), set pieces→toggleSetPiece — with suffix-
  tolerant canonical resolution (ticks 'Harlequin Crest (Shako)', never a duplicate). Two
  feeders: vault commits stamp the ledger LIVE, and a NEW chat DISCOVERY lane ('<player>
  has found <item>' → discovered_names, chronicle-only 💬🏆 chip, NEVER vaulted).
- **v764 auto-sync:** the board SENSES the agent — a light /ping probe every 2.5s auto-
  engages the live poll when the app's ON/SIM starts the bridge; both switches are passive
  LAMPS now (clicks/keys removed). `_tvdToggle` stays as the spec/manual seam; probe webdriver-gated.
- **Also:** SIM wrong-page bug fixed (macOS `open` drops file:// fragments → direct browser
  spawn + open-once per control session).
- **Tests:** board **14/14** (new chronicle lock: canonical uni+set stamps · discovery chip ·
  never-vault · idempotent re-broadcast · live vault stamp) · agent **57/57** · html clean.

---

## 2026-07-17 — v757–v762 CONTROL APP + native shell + Windows twin + icon

- **v757:** TV DIABLO control app (Mac) — hidden agent + HD window, one-click launch.
- **v759 broadcast console:** true fullscreen 100dvh grid face — giant state-tinted serif
  phase (STANDBY/SIMULATION/LIVE), breathing Diablo silhouette from the HD art DB, scanlines/
  sweep/vignette, five state-ringed action cards, /art/<name> route (realpath-safe, mime
  whitelist, traversal→404). Konyo's mandate: "stretched, structured, breathing, full screen."
- **v760+v760.1 Windows twin:** cross-platform spawns (CREATE_NO_WINDOW/NEW_PROCESS_GROUP,
  netstat detection). Trap fixed: Windows soft-stop was `taskkill` w/o /F → windowless console
  never gets WM_CLOSE → farewell lost (run-#7 class). Agent registers SIGBREAK; app soft-stops
  its own child via CTRL_BREAK_EVENT, taskkill only for foreign pids.
- **v761+v761.1 native shell:** the console opens in a REAL OS window via pywebview (WKWebView/
  WebView2), pip-installed by both installers with PEP-668 resilience (--break-system-packages
  retry + re-probe); Chrome/Edge --app demoted to fallback; headless bare-run preserved.
- **v762 the icon:** Diablo-on-grimoire-CRT tile → .icns (Mac .app) + .ico (Windows shortcut),
  bundled by both installers; live apps re-iconized. No more white box.
- **Tests:** agent 55/55 across the wave · py ast clean · art route 200 + traversal blocked ·
  screenshots at 2000/1440/1280 looked at.

---

## 2026-07-17 — v758 the v754 board pass lands complete

- **What:** all 8 v754 audit items landed (badge identity · scanning ghosts · light thumbs ·
  mobile hero band 760+640 · TV-B7 chip→card ↗ affordances with scoped listeners · overflow
  root cause = .tvd-switch stretched by column-flex ×1.35 → align-self:flex-start).
- **Item 7 routines jump root-caused** (Konyo: "all the routines are jumping"): the 60s status
  counter was the only variable-width element in a right-anchored fixed pill, shoving the whole
  G–T strip every refresh; two warring !important right-offsets broke narrow screens. One clean
  dock rule + counter locked to 150px tabular-nums; strip position now constant at 1440+720.
- **Item 8:** CI flake killed — toggle-OFF assert condition-waits (waitForFunction) not a 300ms sleep.
- **v758.1 / REG-019 (the product race behind the flake):** a late in-flight poll response could
  `setState('live')` AFTER the switch was flipped OFF → the stage stayed up forever (Routine I
  shard-6, and "the switch was already on"). Guard: `if(!T) return` in the poll's then+catch;
  every call site sets `T` synchronously. Stress: v747 test 6×@workers=2 all green.
- **Tests:** board **13/13** · agent 55/55 · html clean · D2R_BUILD → v758.

---

## 2026-07-17 — v755 THE COUSIN MOVE: one-line Windows install

- **What:** `irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex` — one paste: winget-installs
  Git + Python + Claude Code if missing, clones/updates the public repo, drops a "TV DIABLO"
  Desktop shortcut. The one unskippable human step (the cousin's own Claude login) is walked on
  first run. His subscription, zero API keys.
- **tv/start_tvd_win.ps1:** strips API-key env (v720 lesson, Windows edition) · pull-first ·
  capture_win.ps1 minimized + reader --watch in one window · Ctrl-C stops both, farewell included.
- **Serving:** deploy.sh copies the installer into the dist scaffold; `functions/_middleware.js`
  exempts exactly /d2r/install-tvd.ps1 from the password gate (zero secrets — public repo anyway).
- **Follow-ups:** v755.1 harden + serve as text/plain · v755.2 `$args` rename + Store-stub-aware
  Python pick · v755.3 portable frame archive (sips wrapped, raw-copy fallback for Windows/Linux).

---

## 2026-07-17 — v752+v753 REPLAY + the full-audit agent batch

- **v752 📼 REPLAY:** `tvd sim` (canned demo) · `tvd replay` (--list/--n/--pace/--exit-after) —
  re-runs a REAL past session through the REAL loop (archived frames + recorded reads via the
  TV_STUB manifest + TV_FRAMES_DIR watch seams). Persistent journal `tv/sessions.jsonl`
  (gitignored, 4MB rotation), seeded with his 97 frame-backed browser-history reads —
  `replay --n 1` re-broadcasts the 03:18 Meph run incl. the Civerb's Ward + Face of Horror
  double-grail. Honesty: never journals itself, never OCRs replayed pixels, only replays extant frames.
- **v753 audit batch:** ONE version truth (VERSION const → banner/HUD/state) · frame archive
  1920→2560px, keep 80→600 + 500MB ceiling (the pruner was eating his photos — the "not
  openable" class) · farewell can never hang (capture timeout → read.jpg → newest-archived
  fallback chain) · run-#8 fix: gameplay+names = loot-class (grail piles enter the SEEN chain) ·
  journal lane field · watch accepts .jpg · journal-write failure surfaces once.
- **Tests:** agent **55/55** (lifecycle-class + replay manifest + journal + seam locks) · replay
  e2e proven on the real Meph session.
- **Non-goals (whole arc):** no forge rewrite · no fabricated names · don't loosen settle ·
  don't rewire the vault photo-intake.

---

## 2026-07-17 — v747–v751 NOW ON AIR arc (the live chapter stage)

- **v747 THE STAGE** (Grok design · Fable visual-coding-architect built · Fable code-reviewer
  SHIP): full-width live chapter card between the CRT hero and THE RUN STORY, LIVE-only. NOW ON
  AIR ● + read #N (synapse-synced), per-scene skin (loot/inventory/stash/town/transition), big
  🗺 area line, caption = area + scene + intent. Cast = one HD-art tile per resolved name w/
  rarity ring + lifecycle-on-art (⚡ocr→✓deep · ⏳hold · 🏦vault · 🗑struck); READING… = type-on +
  ghosts; honesty gate keeps notes/garble off the cast. Boss portrait chip + 🔥 terror tick when
  tz agrees. Latent v746 gap fixed: live FEED entries now carry note/transition_from.
- **v748–v750 (Grok's post-ship trio):** v748 CAST=CREDITS (66px mid-token ellipsis murdered
  names → autosize 96px, 2-line wrap; asserts full "Harlequin Crest") · v749 CHAPTER CAST MEMORY
  (union of honest routes in the current area, cap 12, latest-lifecycle-per-name wins, cleared on
  area change — never invents) · v750 PORTAL KEEPS THE CHROME (boss/tz resolve from
  transition_from/chapter memory, ONE hourglass, chapter cast dims to ghosts under the wash).
- **v751 THE HERO BAND:** the stage rebuilt as a full-bleed broadcast lower-third (edge-to-edge
  CRT grimoire plate, serif display headline, on-air bug, jeweled boss/terror pills, phosphor
  vault glow, portal flare, teleprompter-caret reading ghosts). A latent 337px horizontal
  overflow (predates the pass, present on v750) contained by `html{overflow-x:clip}`.
- **Tests:** board **11/11** (NOW-stage lock: hidden-off · cast honesty · lifecycle rings ·
  portal wash · read-# sync; all three v748–v750 locks folded in) · agent 49/49 · screenshots verified.
- **Ops note:** the Grok MCP XAI_API_KEY was dead this arc — both pingpong rounds ran through the
  signed-in Grok CLI instead. Rotate at console.x.ai to restore the MCP path.

---

## 2026-07-17 — v741–v746 THE CINEMA ARC (the run never goes dark)

- **v741 lightbox surgery + THE SYNAPSE:** two live lightbox bugs fixed (ancestor-containment
  trap → fixed overlays moved to document.body on open, the v512 forge-legend lesson; stuck
  archive-fallback flag → reset per open, one clean bridge→archive→missing chain). KNOWN-DEAD
  FRAMES: an empty deep read teaches that frame's signature (cap 8) so a re-match is recognized
  locally in ~0ms, zero vision. THE SYNAPSE: the brain log reborn as a thought-spine — typed
  glowing orbs (⚡pulse 👁sense 📦result ⏳transition ⛔fault), newest = the breathing active thought.
- **v742 Esc stack + persistent learning:** the lightbox's Escape acts ONLY as the visible top
  layer (capture-phase consume) so vault/search underneath don't close in the same press; learned
  transition frames survive restarts (tv/known_frames.json, gitignored) — loading screen learned once.
- **v743 synapse burst readability:** identical repeated thoughts collapse into one node w/ an
  amber ×N counter (skip-storms = one quiet line).
- **v744 THE CINEMA ARC (Grok's dawn audit):** CRT FACE — the live /frame breathes inside the TV
  bezel (4s throttle), click = fullscreen LIVE view · THE RUN STORY — the session as a film strip
  above SIGNAL FEED (🗺 area chapters · seen/held/vaulted/tossed/transition ticks from the same
  persisted reads; click a tick → history row scrolls+pulses; identical ticks collapse) · friction
  calm (honest tab copy · NO DB → quiet `base` badge · ONE primary MOTION meter).
- **v745 the story never goes dark:** the v744 reel followed the LIVE/LAST toggle and hid when the
  agent was off (looked invisible). Fallback narrates the newest ARCHIVED session (`📼 RUN STORY ·
  LAST SESSION`); clicking a fallback tick flips to LAST first. History list storylined with 🗺
  chapter dividers on area change.
- **v746 ⏳ ENTERING, pinpoint:** the real bug — `known_dead_match` was defined (v741) but NEVER
  CALLED (parallel-edit merge casualty), so the agent paid 7.2s of Sonnet on the learned portal
  frame. Wired into the live loop: a learned frame publishes an honest ⏳ transition read at 0ms,
  zero vision. LAST_AREA rides every deep read so the label reads the story ("through the portal —
  leaving <area>" / "entering a new game"); vision prompt gains scene `transition`; the board
  renders ⏳ ENTERING in feed + history instead of "nothing readable".
- **Tests:** agent 46/46 → **49/49** (transition context · should_learn_dead · prompt vocab) ·
  board 9/9 → **10/10** (fallback cap · chapter · transition-honesty locks) · real-loop e2e proof.

---

## 2026-07-17 — Grok: v740 farewell read (run #7 end-stash race)

- **Miss:** garbage stashed then agent killed within seconds → no settle/gap/deep → nothing
  vaulted. Farewell: on SIGINT/SIGTERM one final capture + deep read (flag `farewell:true`).
- `tvd stop` waits up to 90s for farewell before SIGKILL. Suite 43/43.

---

## 2026-07-17 — Grok: v738 chain vault (run #4 Crossbow + Jewel)

- **Live miss:** floor SEEN Colossus Crossbow; stash vaulted Blood Shield/Compendium/
  Unidentified; Jewel vaulted without floor chain; Crossbow never farmed.
- **Fix:** stash-commit ONLY if name is SEEN, HOLDING, or gone-candidate this session.
  Hard-ban Unidentified; tag `stash-no-chain` / `skip-weak`. Inv hold→stash still works.
- Suite **42/42** incl. run #4 scenario unit tests.

---

## 2026-07-17 — Grok: v735 per-read frame history (eyes on the AI)

- Each settle archives `tv/frames/hist/{n}_{ts}.jpg` (~1920 JPEG from the capture).
- Read records carry `frameId`; board history rows show a thumb; click → fullscreen
  lightbox (`GET /frame?id=`). Last-frame eye still works. Offline copy → `tvd`.
- History paint also drops archived OCR `NO DB` notes (garble scrub). Ring keep=80.

---

## 2026-07-17 — Grok: v734 stash-tab auto-intake

- Konyo design (Fable backlog): stand on RotW Runes/Gems/Materials stash tab → TV hands
  the frame to the **locked** tally intake (`runeIntake`/`gemIntake`/`materialIntake`).
- Agent deep-read adds `stashTab`; board fetches `GET /frame` → File → intake. Once per
  stash-visit per tab. Personal/shared = normal item flow only. OCR never fires intake.
- Intake machinery untouched. Agent tests + board mock for debounce/OCR guard.

---

## 2026-07-16 — Grok: v732 OCR fast lane (pile→chip ~0.1–0.2s feel)

- Physics: LLM vision floors ~3–6s. Local Vision OCR + warm worker = **~10–50ms** (bench
  warm ~27ms; single-ROI 800px). Board poll **2s→250ms** so chips land sub-second.
- Dual lane: OCR provisional `lane=ocr` ⚡ocr review-first · never `vault_names` · Claude
  deep confirms (`confirmed_names` / ✓ conf). `tv/bin/ocr_mac` + `ocr_mac.swift`.
- `TV_OCR=0` disables · `TV_OCR_BIN` seam for TDD. Suite green + OCR unit tests.

---

## 2026-07-16 — Grok: v731 commitment vault (hold / stash / throw-out)

- **Problem (run #4):** inv glimpse after ID→throw still vaulted; 🏦 badge without lasting
  owned entry; gold/junk noise; HIT confused with vault.
- **Rules:** floor = SEEN only · inv = HOLDING (pending) · vault only after `HOLD_MS` (~30s)
  still in bag **or** town **stash** · floor-again = THROW-OUT (cancel pending / unvault).
- `LootLifecycle` pending/vaulted/thrown · board `vault_names` only · `tvVaultUnregister` ·
  belt `tvVaultRegister` for every committed name · hist chips ⏳ hold vs 🏦 vault.
- Agent suite **30/30**. Live **Run #5** next.

---

## 2026-07-16 — Grok: v726 kill empty-gameplay 20s cool

- Konyo: cool made pile/inv stops feel dead after any empty combat pause.
- Removed dynamic EMPTY_GAP; thrash control = same-view skip + MIN_GAP 6s only.
- Agent suite 22/22. `tvd restart` / agent relaunched sonnet warm 3s.

## 2026-07-16 — Grok: v729 LOOT LIFECYCLE v2 (object permanence)

- Run #3 design (Konyo/Fable backlog): floor SEEN → same-area GONE (grace) → inv CONFIRM.
- `LootLifecycle` session engine · `farmed_names` only auto-apply · baseline never re-tally ·
  anchors (Cube/TP/ID tomes) · GONE alone never applies · inv-only still works.
- Agent suite **30/30**. Board uses `farmed_names`. Run #4 live-verify next.

---

## 2026-07-16 — Grok: v730 post-run #4 lifecycle tune

- Live state.json: inv read 25.8s · anchors OK · but farmed_names=[] (first inv baselined loot).
- Soft first-panel: farm Blade Bow/Crown once then lock · junk (potions/arrows) filtered.
- Shorter vision prompt for speed. Suite 29/29.

---

---

## 2026-07-16 — Grok: v727 Autopilot core (Tesla-style when-to-read)

- Continuous interest scorer: hard motion → stop = PRIORITY (gap **2.5s**, 1-tick settle).
- Cruise: gap 6s · 2-tick settle for low interest (no 20s cool).
- `/state.ap` + board INTEREST/AP meters. Roadmap: `tv/PLAN_FSD.md`.
- Suite **24/24** agent. Sonnet default unchanged.

---

---

## 2026-07-16 — Grok: v725 TV speed flip (run #3)

- **Live #3:** Haiku warm **13–16s** (slower than prior Sonnet **6–10s**) · 43 empty gameplay settles.
- **Ship:** default `TV_MODEL=sonnet` · MIN_GAP **6s** · empty gameplay/town cool **20s**.
- Agent suite **22/22**. Warm re-proof: sonnet ready in **3s**. Restart: `tvd restart`.

---

## 2026-07-16 — Grok: TRACKING.md contract (project board so 700+ versions stay legible)

- Added **`TRACKING.md`**: single living backlog + **9-step ship gate** (TDD → suites →
  BUILD_LOG → BUGS → commit → **push GitHub**). Rule: if it is not tracked + pushed, it
  does not exist for other agents. No separate GitHub Project yet — this file *is* the project.
- TV active stream + open IDs TV-B5…B10 listed there (B1–B4 done with v723–v724).

## 2026-07-16 — Grok: TV-KAI v723–v724 (Haiku+genius · farmed vault wire · session history)

> **Surface:** TV DIABLO only (`tv/**` + TV receiver slice of `bible.html` + board specs).
> Restore freeze BEFORE this wave: git tag
> `restore-point-pre-tv-speed-loot-lifecycle-2026-07-16_201534` @ `f5886b8` (v722) +
> hardcopy `backups/RESTORE_2026-07-16_201534/` (local, not committed).

### v723 — speed + loot lifecycle + thin vault door
- **Haiku default** (`TV_MODEL=haiku`) warm worker; **Sonnet genius escalate**
  (`TV_MODEL_ESCALATE=sonnet`) when conf low / empty loot / shaky farmed names
  (cap `TV_ESCALATE_CAP=40`). Subscription only — still strips `ANTHROPIC_API_KEY`.
- **Intent:** floor `loot` → `seen` (review-first); `inventory`/`stash` → `farmed`
  (auto-tick engines + `window.tvVaultRegister` → owned/muleAssign, no photo AI).
- Agent state rings: `seen[]` / `farmed[]` + model/conf/intent on each read.

### v724 — SESSION HISTORY board (pre run #3)
- TV tab panel: **LIVE** / **LAST SESSION** · clock-time rows · HD art ·
  HIT/DB/NO DB badges (engines + ~1400 ITEMS) · 🏦 vault tags · last JPEG via
  agent `GET /frame`.
- Persisted `d2r_tvdHist` (account-forked in `_LP_FORKED`) so last session
  survives agent restart / page reload.

### TDD / CI gates
- `python3 tv/test_agent.py` → **22/22** (CI: `.github/workflows/tv-tests.yml` on `tv/**`)
- `npx playwright test tests/v712_tv_board.spec.ts` → **4/4**
  (CRT · routing/review-first · history panel · farmed auto vs floor review-first)
- Ledger: `tv/PINGPONG_LOG.md` R12–R13 · plan: `tv/PLAN_SPEED_AND_LOOT_LIFECYCLE.md`

### Non-goals (kept intact)
- No forge rewrite · no vault photo-intake rewrite · no settle loosening ·
  no fabricated item names.

---

## 2026-06-08 — CC: v115 — animated aura GIFs (2x) + nightly B1 Mercenary section
- **Ships** (one deploy): commit `25ec2a8` (gifs) + `5476017` (B1 merc), live md5
  `7188c8de71748b5d6edc5bd5ef13917c` (apex parity OK).
- **v115 animated aura gifs**: Konyo — "I want the aura icons as the animated gifs
  cryptography posted on diablo2.io/skills/ (Conviction = i.imgur.com/EflB9N4.gif),
  lively, 2x bigger." Swapped the 8 static aura PNGs in `AURA_ART` for the live
  **imgur gifs** (each scraped from `diablo2.io/skills/<aura>-t<id>.html` raw HTML
  via curl-grep, then curl-verified 200 image/gif ~8 MB): Fanaticism geASVE4,
  Meditation qlL3lxn, Conviction EflB9N4, Holy Freeze DXnRCP0, Holy Fire CQCYZ9t,
  Holy Shock 9GMvWz7, Might vVASShr, Blessed Aim hj5K54S. Aura logo bumped to **2x
  (76px)** via `.aura-tile .aura-logo` CSS. Still lazy-loaded; glyph fallback still
  covers an imgur hotlink hiccup. v113 spec URL asserts updated diablo2.io→imgur.
  **Lesson: WebFetch's markdown converter DROPS imgur embeds — scrape forum-post
  images with `curl … | grep -oE 'i\.imgur\.com/[A-Za-z0-9]+\.gif'`. Skill-page IDs
  found via `diablo2.io/skills/` index grep.** Gif weight ~8 MB each (~60 MB when a
  bind card opens all 7-8) — acceptable because lazy + only the 3 bind cards use them.
- **Nightly B1 — Mercenary mechanics** (first bridge of the maxroll cross-ref):
  additive `🛡️ Mercenary mechanics` collapsible in `#tab-ref` (nothing cut). 4
  hirelings; the Act 2 Desert Merc **aura-by-difficulty** table (Normal&Hell vs NM —
  Combat Prayer/Thorns · Defensive Defiance/**Holy Freeze** · Offensive Blessed Aim/
  **Might**; "hire in NIGHTMARE, Hell reverts to Normal"); revive cost
  `min(int(hlvl×hlvl/2)×15, 50000)`; best gear (Infinity/Insight/Reaper's/Pride ·
  Andariel's/Tal's/Vamp Gaze · Fortitude/Treachery); ethereal-on-merc. maxroll
  vanilla mechanics + **explicit RotW verify-in-game caveat**; cross-refs the binds
  tab (Konyo's Lister Meditation → Insight merc redundant, run Infinity/Holy Freeze).
  Merc-gear names kept as styled text (honest-affordance — runewords route differently).
  Guard `tests/v114_mercenary_reference.spec.ts` (4 tests).
- **Tests**: v115/v113 7/7 · v114 4/4 · smoke 8/8 · push gate 38/38 (both pushes).
- **Nightly progress**: bridge 0 gap-map committed (`2e95151`); B1 done. Remaining
  bridges B2 Gambling · B3 Breakpoints (verify FCR/FHR vs Konyo) · B4 Crafted recipes
  · B5 Warlock-overview cross-ref · B6 cross-check sweep.

## 2026-06-08 — CC: v113 — glowing bind-aura logo grid + The Smith as a 3rd bind card
- **Ship**: commit `0ee7953`, live md5 `e28e21501337097a4035240310962a60` (apex parity OK).
- **What**: Lister, Hephasto and (NEW) **The Smith** each carry an eye-candy,
  maxroll-elite-monster-style **aura logo grid** on their super-unique ID card. Each
  tile leads with the **actual in-game Paladin-aura icon** so Konyo knows exactly
  "what to look for" floating over the boss's head. Unified logic: one `AURA_ART`
  map + one `auraGridHtml()` renderer feeds all three cards (mirrors `artOr`).
  - **Lister**: fixed Lvl-15 Meditation lead tile (violet glow) + the 7-aura reroll
    pool; the Fanaticism ⭐ TARGET tile pulses gold.
  - **Hephasto**: the 7-aura random reroll pool, no fixed tile.
  - **The Smith**: was a plain super-unique → now an enriched bind card. Fixed-only
    Holy Fire grid (no reroll lottery, per the bible's own `#binds-elite` "Smith's
    fixed aura") + a **Baal-parity drop-pool grid** (Tristram TZ mlvl 96 / TC85),
    matching Lister/Hephasto. He is the 3rd fully-sourced bind target.
- **Zero-fabrication discipline**: aura divisors/caps reuse the published
  `#binds-elite` table (no new numbers); each of the 8 aura icon URLs was
  curl-verified live (HTTP 200, image/png, ~9 KB) — NOT guessed. Levels =
  `floor(mlvl/div)` capped, shown at mlvl 96. `auraArt` keeps the artOr graceful
  fallback (load error → glyph, never a broken-image box).
- **Spec churn**: v111 + v112 "exactly TWO targets" assertions widened to THREE
  (Hephasto/Lister/The Smith). New `tests/v113_aura_logo_grid.spec.ts` (7 tests).
- **Tests**: v113 7/7, v111 5/5, v112 9/9, smoke+d2art+v83 48/48, push gate 38/38.
- **New site API**: `AURA_ART`, `auraArt(name,glyph,size)`, `BIND_AURA_POOL`,
  `auraGridHtml({mlvl,fixed,fixedOnly})`; new `su.auraGrid` descriptor on the 3
  targets; new `.aura-grid`/`.aura-tile` CSS + `.d2art-wrap.md` (38px) size.

## 2026-06-07 — CC: Herald of Terror card — farming-grounds + pro-tips enrichment

**Ask (Konyo):** more depth on the Herald spawn/ladder mechanics + optimal farming,
**additive only** ("I don't want changing, I want adding").

**Shipped:** two new `.gbc-section` blocks in `#herald-card` (after "optimal farming
strategies", before the Sunder-charm table) — **🗺️ where to draw ire** (best
high-density elite zones: Chaos Sanctuary / WSK→Throne / Pit lvl2 / Ancient Tunnels)
and **⚡ work the two-step like a pro** (bank-ire-then-reveal · big-teleport reveals ·
elites-only-for-ire / minions don't count · lightning telegraph tell · never
backtrack/exit · speed>MF post-3.2). **Zero fabrication:** every line is either
verified against the DiabloBytes "Heralds of Terror" guide (zones, telegraph,
speed>MF) or logically DERIVED from the card's own stated ~2% ire / ~1% hunt / 5×
stack / per-kill tier-bump rules. No new numbers invented; existing sections + all
sourcing (TheBugWarrior, Maxroll) untouched. Static HTML only — no CSS/JS/helper
touched (minimal blast radius), but ran the FULL suite anyway (live deploy): **427
passed / 1 skipped**. Herald specs (v72/v75/v85/v56_rotw) green.

**Ship:** commit `545674d` → deploy `0eafb3e9` → md5 parity `6ab019a3…` → pushed
(smoke 36/36). Research via WebSearch + DiabloBytes WebFetch (rpgstash 403'd;
diablobytes' looser per-zone-killcount framing was NOT adopted — it conflicts with
the card's precise two-step, so only its non-conflicting facts were used).

---

## 2026-06-07 — CC: rune-source detail cards → golden .gbc-card shell (v93)

**Premise correction:** the v92 audit said "Travincal has rows, not a card." That
was **wrong**. Travincal is a `RUNE_SOURCES` entry (`id:'travincal'`, bible.html
~L8192) already rendered in the **Runes tab** by `renderRuneSources()` as a clickable
expand card — it just used the **legacy `.boss-*` shell**, not the golden `.gbc-*`.
So the gap was a *shell re-skin*, not new authoring. **No new card built, no odds
fabricated.**

**Shipped:** `runeSourceDetailHtml()` now wraps its detail in the golden
`.gbc-card rune-src-card-rich` banner (artOr emblem + `.gbc-name`/`.gbc-subtitle`/
`.gbc-loc` + `.gbc-tier` badge + `.gbc-close`) over a `.gbc-body` of the EXISTING
grid / tier-pool / why / action / warn / notes — **content verbatim**. This upgrades
all 4 rune sources at once (Travincal, Hellforge, Cows, LK) into parity with the
Baal / Herald / TZ-zone / super-unique cards. Followed the **v85.1/v91 wrapper-strip
precedent**: extended the `.tz-zone-detail/.su-detail:has(>.gbc-card)` strip rule to
`.rune-src-detail`, and rescoped the `.rune-src-card` 40px emblem clamp to
`> .boss-header` so the nested gbc emblem isn't shrunk.

**Tests:** relocated the v53 "editorial frame" assertion from the wrapper to the
inner `.gbc-card` (frame moved there, per zone/SU); added a v53 v93 banner-parity
lock (emblem + name + tier + close collapses); extended the v83 `gbc-format parity`
guard to also assert `runeSourceDetailHtml` emits the gbc shell AND that Travincal's
`pending silospen pull` honest-odds caveat survives the re-shell. **Full suite 427
passed / 1 skipped.**

**Ship:** commit `98bfd49` → deploy `38c16f34` → md5 parity `2af1afc6…`
(local==live) → pushed (pre-push smoke 36/36 green).

**Drop-source gbc-parity is now COMPLETE** across bosses · super-uniques · TZ-zones ·
Herald-apex · event heads (v92) · rune-sources (v93). Remaining follow-ups are
sub-card shells only (inner `.ubc` 9-boss cards + `.colossal-tile` index), not
top-level drop-source gaps.

---

## 2026-06-07 — CC: event-card heads → golden .gbc-header banner (v92, #52 / #51)

**Context:** v92 audit (`AUDIT_v92_event_monsters.md`) scored the `#tab-ancients`
"Pinnacle Events" drop-sources against the golden shell. Finding: they're
**procedural how-to guides** (farm->cube->fight), not stat ID cards — so the
unifiable surface is the **header banner**, not a forced stat-grid. The Pit was
already gbc-parity (renders via the TZ-zone rich card); Travincal has rows but no
card (deferred to v93 — it's new authoring, not a re-shell).

**Shipped:** the 7 top-level `.event-card` heads now wear the `.gbc-header` golden
gradient banner + a `.ec-tier` badge mirroring `.gbc-tier`. Badge values are all
in-card facts (zero fabrication): Uber Tristram `access/Hell` · Uber Boss ID Cards
`cards/9` · Colossal Endgame `relics/11` · Cows `bovines/~400` · Diablo Clone
`mlvl/110` · Colossal Ancients `ancients/3` · 22 Nights `nights/22`. **22 Nights
stays emblem-free** — seasonal modifier *window*, not a drop-source (locked by v47
"no fabricated art"). Additive only; collapse contract + lazy-load untouched (all
new CSS is `#tab-ancients`-scoped). New v83 invariant `event-card head parity
(#52 / v92)` locks emblem(+exempt 22N) + titles + tier badge + chevron on every head.

**Verify/ship:** full suite **426 passed / 1 skipped** (13.6m). commit `4ff0fc7` ·
deploy `30d540d7` · md5 parity check ok (`7a85399...`, apex == pages.dev == local) ·
pushed (pre-push smoke 36/36). Note: `/tmp/d2r_dist` scaffold was cleared by the Mac
restart — recreated `{d2r/index.html, _redirects, index.html}` before deploy.

**Next (v93):** author a Travincal Council drop-source card (high-rune throughput
king) — the last drop-source gap. Then sweep inner `.ubc`/`.colossal-tile` sub-cards.

---

## 2026-06-06 — CC: super-unique cards → golden .gbc-card shell (v91, #58 / #51-#52)

**Context:** The #51 ID-card parity audit (`AUDIT_id_card_parity.md`) found the
super-unique detail cards were the one drop-SOURCE entity still on the lean `.zd-*`
idiom while bosses / TZ zones / Herald-apex already use the rich Baal `.gbc-card`
shell. This brings them into the same design language — master-goal progress.

**Change (additive — content preserved verbatim):** `superUniqueDetailHtml`
(L4334) now returns a `.gbc-card` with a `.gbc-header` (artOr `lg` emblem · name ·
subtitle `super-unique detail · {role}` · `📍 {act} · Hell mlvl N` · mlvl tier
badge · ✕ close) wrapping the existing stats / drops / TZ cross-link / DClone note /
full-table link / pending-odds caveat inside a `.gbc-body`. Extended the
`:has(> .gbc-card)` wrapper-strip rule to `.su-detail` (mirrors the TZ
`.tz-zone-detail` card-in-card fix) so no double border/shadow.

**Honesty:** NO odds fabricated — the "pending silospen pull" caveat is retained
(v51 `allCaveated` still green). All v51 content assertions (super-unique detail
title, Frigid Highlands cross-link, grail-uniques-reachable, Diablo Walks the
Earth, `openBossDetail('…')` links, no `undefined`) preserved.

**Guard (#52):** new `v83_sync_audit.spec.ts` test *"gbc-format parity"* — asserts
each drop-source entity builder (super-unique + TZ-zone) emits `.gbc-card` +
`.gbc-header` + `.gbc-name` + an artOr emblem, no `undefined`, and the super-unique
keeps its caveat + title through the re-shell. Locks the unification against drift.

---

## 2026-06-06 — CC: hover-glow unification (v90, Batch 3 / #53)

**Context:** Batch 3 of the unify-every-card master goal — make every clickable
item/row/chip lift with the SAME golden glow. Canonical reference was already
`.fi-clickable:hover` + `.zd-item-click:hover` (`transform:translateY(-1px)` +
`box-shadow:0 2px 8px rgba(0,0,0,.3-.35)` + gold-bright border). Laggards only
swapped a border colour with no shadow/lift.

**Change (CSS-only, additive):** added the `box-shadow:0 2px 8px rgba(0,0,0,.3)`
glow (and where missing, the `translateY(-1px)` lift + gold-bright border) to:
- `.item-tile:hover` (calc grid) — border →gold-bright + glow (lift already via `.item-tile:focus,:hover`).
- `.boss-chip:hover` (boss nav chips) — added lift + glow + gold-bright.
- `.gbc-grail-item:hover` (Top-Drops grail tiles) — added glow.
- `.source-chip:hover` (item-detail jump chips) — added glow; kept `--star` accent (semantic: source nav).
- `.top-drop-row:hover` — added glow over the existing golden gradient+lift.

**Guard:** new `v83_sync_audit.spec.ts` test *"hover-glow parity"* — scans the
stylesheet and asserts all 7 canonical clickable hover selectors declare a
`box-shadow`. No markup/JS/behavior touched; no click contract changed.

---

## 2026-06-06 — CC: tab-ref section-header unification (v89, #47 sweep)

**Context:** Konyo: *"#47 sweep tabs for title/section asymmetries."* Swept all 11
tab panels for title/section/collapsible asymmetries. Result: every tab is
internally consistent; the lone cross-tab outlier was **tab-ref**, whose 8 section
headers were bare `<h2>` while the other section-list tabs (tab-main, tab-rotw)
use the collapsible `.sec-h` + `.sec-body` idiom. Konyo chose "Convert to
collapsible."

**Change:** Converted all 8 tab-ref `<h2>` headers to
`<h2 class="sec-h collapsed" onclick="toggleSec(this)">… <span class="sec-chev">▾</span></h2>`
immediately followed by `<div class="sec-body" hidden>…</div>`. Inner content
preserved verbatim; only wrapped. The 8 sections: two-filters, verified anchors,
TC ramp, MF math, P# slider, Cube recipes, Tristram Stones, Confidence formula.

**Test sync:** `v50_p_slider_explainer.spec.ts` test 1 switched `#tab-ref`
`.innerText()` → `.textContent()` (collapsed `.sec-body` is `hidden`; innerText is
visible-only). Other tab-ref consumers use `toContainText`/evaluate-click → no change.

**Guard added:** new `v83_sync_audit.spec.ts` test *"section-header parity"* —
asserts every section-list tab (main · rotw · ref) uses ONLY collapsible `.sec-h`
cards (scoped to `:scope > h2`, so nested `.gbc-name`/`.gic-name` detail-card h2s
are exempt). ref ≥8, main ≥4, rotw ≥5.

---

## 2026-06-06 — CC: Herald ladder research + tier-card enrichment (v88)

**Context:** Konyo: *"start the Herald ladder research work autonomously on them
all."* Research the 5-tier RoW Herald ladder (Fright→Dread→Fear→Horror→Terror) from
official sources, NO fabrication, then enrich all 5 tier ID cards.

**Research (#49)** — cross-checked diablo2.io (authoritative monster page) +
diablobytes guide + WebSearch (rpgstash 403-blocked; d2db used with caution).
Verified facts now baked: spawn **Hell TZ only** (summoned by killing TZ monsters,
chance rises with kills — *exact threshold not published*); each kill advances the
next spawn one tier; tier is **per-session, resets to Fright on leave/disconnect**;
after Terror every spawn stays Terror; **Heralds always carry an aura, can roll two
at once** (Terror = two auras + minion pack); **drop scaling matches what the bible
already had** (Fright/Dread normal · Fear/Horror +1 · Terror +2); **all tiers can
drop Latent Sunder Charms**; **Patch 3.2 / S14 (live 2026-05-22):** Latents drop from
any MF monster, increased-Herald chance starts at tier 1, player-count no longer
heavily modifies Latent/Worldstone rates. **Flagged unverified (NOT baked):** d2db's
life/dmg table + 2% ire / 5 stacks / 1% conversion + element weights (contradicts
diablo2.io); Worldstone Shard ≈ 1:500 elite/boss is community-estimated only.

**Enrichment (#50)** — `heraldTierDetailHtml` (lean card for the 4 lower rungs):
added **⚙ How it spawns & climbs** (where · summoned-by · this-rung · next-spawn ·
tier-resets · aura) and a **🩹 Patch 3.2 / S14** section; folded the always-aura /
dual-aura fact into *what it is*; the *what it drops* line now says **every rung
including this one** can drop the 6 Latent Sunders; the closing note explicitly flags
the 3 unpublished gaps (kill threshold, per-tier mlvl/HP/immunity, Worldstone rate)
instead of inventing them. The apex rich `#herald-card` (already beyond Baal-format)
got a one-line **Patch 3.2 reconciliation** under the tier table — its pre-3.2
"Sunder threshold opens at T4" column now reads correctly against the all-tiers /
tier-1-start truth, without gutting the cited TheBugWarrior/Maxroll content.

**Invariants preserved:** every v75 test gate (5 tiers · apex=Terror · searchable ·
≥6 sunder chips · next-rung naming · HERALD_PORTRAIT emblem + 👹 fallback + lazy ·
no console errors) stays green. Pure additive copy — no math/data touched.

**Verify:** `v75_herald_tiers` + `v72_herald` 15/15 green; full suite green.

## 2026-06-06 — CC: hide NORM/NM site-wide — Hell-only view (v87)

**Context:** Konyo plays Hell-only RoW. Direction (verbatim): *"now hide NORM/NM
across the boss cards, calc grid, and rune tables"* with the standing constraint
*"i dont want [the math] touched.. just hidden."* So this is a **render-only** hide —
the drop math/data and the DOM are entirely intact; only `display:none` is applied.

**Shipped (visual hide, zero data/math change):**
- One CSS rule (after the `.t-hell` block) hides four per-difficulty class families:
  `dcol-*` (table columns) · `gdc-*` (boss-detail diff grid) · existing `t-*` (boss
  list diff grid) · `csrc-*` (calc source-table rows) · `acr-*` (aid-card compare
  rows) · `schip-*` (aid-card source chips) — each for `norm`/`normTz`/`nm`/`nmTz`.
- Per-difficulty classes added at every render surface: boss list diff-grid (existing
  `t-*`), boss-detail diff-grid (index-based `gdc-*`), boss-detail top-12 grid,
  boss full drop table (header + cells via a `dcol` lookup), Countess rune table
  (header + `cell()` gains a class arg), calc item-detail source table rows, and the
  aid-card compare-rows + source-chips.
- **Why CSS, not DOM removal:** positional integrity probes (`02_verified_anchors`
  `nth(4)`=hell / `nth(2)`=nm SoJ 1:2,286; `03_cell_correctness`; `v41_deep_audit` &
  `routing_and_data_integrity` column-index no-fabrication scans; `01_smoke` th=8 /
  diff-grid=6) all read the DOM positionally — `display:none` keeps every cell in the
  tree so they stay green untouched. The drop scaling/anchors are literally unchanged.

**Test updates (Hell-only reality):** 2 source-chip-click specs (`bug013_014`,
`bug040_050`) clicked `.source-chip').first()` — for Nagelring the first DOM chip is
now a hidden NORM/NM source → not actionable. Retargeted to `.source-chip:visible`
first (the real post-hide UX). Full suite **423 green**.

---

## 2026-06-06 — CC: TZ-zone Hell drops GRID — boss-card parity (v86)

**Context:** Konyo wanted the TZ zones to carry the boss-card "drops grid" look.
Direction (verbatim): *"i dont want [the drop math] touched.. just hidden. or just
leave it.. and add to the TZ zones the hell drops grid."* The Hell-only render is the
RoW reality (Konyo plays Hell endgame).

**Shipped (additive — nothing cut, math untouched):**
- New `zoneHellGridHtml(z)` renders a **rarest-first ranked TABLE** (the boss
  top-drops grid look) of the zone's TC-reachable grail/uber pool, ranked by **TC
  ceiling** (the rarity proxy) with `# · item · TC · qlvl` columns. Top-20 inline +
  a `<details>` "show all N" full table. Every row routes to the one canonical item
  card via `navigateToItem` (same as the boss grid rows). Placed ahead of the
  existing categorical chip block (`zoneDropBlockHtml`), which is **KEPT** alongside.
- **HONESTY (zero fabrication):** the grid deliberately omits per-kill `1:N` columns
  because the silospen terrorized-zone pull is still pending — TC ceiling + qlvl only,
  with an inline note explaining why no per-run odds are shown.
- CSS: `.zd-hell-grid` + `.zd-hg-*` (boss-card `.drops` table idiom, gold hover rows).
- **Tests:** `tests/v86_tz_hell_grid.spec.ts` (6 tests) — exposed + rarest-first +
  no-fake-odds + grid-in-every-pool-zone + rows route via navigateToItem + chips kept
  alongside + live row-click opens item card + no console errors. Full suite green.

> NORM/NM "wipe everywhere" stays deferred per Konyo's "or just leave it" — the math
> is untouched; only the additive Hell-framed grid was added. If a full hide is wanted
> later it's UI-render-only (keep dropTable data + scaling math intact).

---

## 2026-06-06 — CC: TZ-zone ID cards enriched to Baal-card depth (batch 4, v85)

**Context:** Konyo's unified-card-template vision — "update these 10-20 TZ zones to
match that same very format enriched and indetail we already have for Baal", "add a
dedicated area for anything special/uncommon", ADDITIVE only ("nothing gets cut out"),
ZERO fabrication. TZ zones are areas (not bosses) that DO drop loot.

**Shipped (all additive to `zoneDetailHtml`, isolated blast radius — NOT a central helper):**
- **Dedicated SPECIAL-DROPS area** (`zoneSpecialDropsHtml`) — the Baal "guaranteed /
  endgame specials" module, rebuilt for terror zones from the **single-source
  `SPECIAL_DROPS` / `ACT_SHARD` data** (no fabricated odds). Surfaces, as clickable
  chips routed through `openDrop`:
  - 💠 **Sunder Charm** — Heralds of Terror roam every active Hell TZ → Latent Sunder
    (chip opens the Herald ladder); notes the zone's terror tier (mlvl 96 vs lower).
  - 💎 **Worldstone Shard** — the act-matched shard (`ACT_SHARD`) named with its
    Renewed-Sunder cube target (`SHARD_RENEWED`).
  - 🔱 **zone specials** gated on real per-zone facts: ⚒️ Hellforge rune (River of
    Flame), 🔑 Key of Hate (Arcane), 🔑 Key of Destruction (Halls), Griswold's Legacy
    set (Tristram).
- **best-character** module (`zoneBestCharHtml`) — derived from real zone facts:
  density → AoE; the named super-uniques' FIXED immunities → "bring a 2nd damage type";
  ghost/Arcane → casters; mlvl 96 → terror-only elite farm. Strategy advice, not odds.
- **action-plan** module (`zoneActionPlanHtml`) — auto-built route from the multi-area
  zone name (`A + B + C` → "clear in order"), the super-unique finisher, the roaming
  Herald, and the act shard to save. Rendered as an `<ol class="zd-plan">`.
- **head emblem** now `artOr(z.name, z.emoji, 'sm')` (was a bare 📦) — graceful
  emoji fallback, keeps `loading="lazy"` (REG-001).
- New CSS: `.zd-item-dim` (muted non-clickable chip), `.zd-plan` (ordered list).

**Test:** `tests/v85_tz_enrichment.spec.ts` (6) — every zone has all 3 modules; the
act-matched shard + zone-specific Key/Hellforge/Griswold specials; the Herald chip
actually opens the Herald card; artOr head keeps lazy; no console errors across all
zones. **Full suite green: 416 passed / 1 skipped (18.5m).** No dead-fork strays.

**v85.1 — golden shell:** Konyo flagged the zones still didn't *look* like the Baal
card. Rewrapped `zoneDetailHtml` in the **same `.gbc-card` + `.gbc-header` golden shell**
the Baal/Herald cards use (gradient header banner with artOr emblem `lg` + name +
location/mlvl/TC subtitle + tier badge + ✕ close), body in `.gbc-body`. Wrapper
`.tz-zone-detail:has(> .gbc-card)` strips its own border/bg so there's no card-in-card.
Now the terror-zone detail reads as the unified ID-card design language. v85 head test
updated to assert the gbc-card shell; all 28 TZ specs + full suite green.

**HONESTY BOUNDARY (per Konyo's no-fabrication rule):** the boss cards' 6-difficulty
mlvl/TC grid, "Quick take @ MF" line, and per-item **1:N odds** in TOP DROPS come from
the SOURCED silospen RoW per-boss odds pull. **TZ zones have NO sourced per-kill odds
yet** (the standing flagged gap — silospen `desecrated` pull pending). So those numeric
sections CANNOT be faithfully built for zones without fabricating. Honest alternative
(next): a rarest-first TOP-DROPS grid built from the real TC-reachable pool
(`zoneGrailDrops`, ranked by TC tier), styled like the boss grid but labelled by
TC/"TZ-reachable" — no invented 1:N. Difficulty grid omitted for zones (boss-only data).

**Unified-template note:** convergence is achieved ADDITIVELY — the leaner cards gain
the missing Baal modules + the golden `.gbc-card` shell, so they read as one design
language without a risky rewrite of every renderer. TZ zones are the first instance.

---

## 2026-06-06 — CC: sync-audit framework + tools/search/super-unique sync (batch 1)

**Context:** Konyo asked the loops to "look for synchronization across the website…
alert us or fix it automatically", then to unify everything to the rich Baal boss-card
format and upgrade every title emoji to artOr. This batch ships the standing audit +
the safe, fully-verified mechanical fixes. Big data-enrichment work (Heralds, all
droppers → Baal format) is tracked separately (needs official RoW data, no fabrication).

### Batch 1 ✅ (full suite 410 passed / 1 skipped, 17.4m)
- **v83 sync audit** (`tests/v83_sync_audit.spec.ts`, 7 tests) — machine-readable
  symmetry contract: tab↔panel↔nav-chip parity, search parity, openDrop route parity,
  endgame-relic parity, tools-tab collapse parity, REG-001 artOr lazy lock, docs↔data
  anchor sync. This is the "is everything still wired" standing sweep.
- **Global search tab sync** — `v42BuildCommands` derived its "Switch to …" commands
  from a hardcoded 8-tab list (drifted: endgame + tools missing). Now DOM-derived from
  `.tabs .tab` → permanently sync-proof.
- **Item Set Tracker → collapsible card** — was a bare always-open `<h2>` in the 🧰 tools
  tab while the 2 stash planners were collapsible boss-cards. Now `.boss-card.collapsible`
  (`#set-tracker-card`), symmetric + title-only by default. (`bug110_149` BUG-114 updated.)
- **Super-unique artOr upgrade** — su-card + zd-su-card titles now use
  `artOr(su.name, emoji, 'sm')` (emoji fallback, zero fabrication). Added 8 super-unique
  art keys to `D2IO_ART`, each probed live HTTP 200 + image/png on 2026-06-06: The Summoner,
  Izual, Hephasto the Armorer, Shenk the Overseer, Nihlathak, Frozenstein, The Smith,
  Sszark the Burning. The other named super-uniques have no diablo2.io art → keep emoji.

### Out-of-sync backlog (Konyo's "perfect what we built" list — tracked, not yet done)
- **Heralds:** research the 5-tier ladder from official RoW sources, then enrich every
  tier card (not just apex) to Baal format; 👹 emblem → artOr. (Sunder Charms are
  Herald-exclusive — the RoW holy grail.)
- **Baal-format parity sweep:** every loot-dropper (ubers, DClone, super-uniques,
  Ancients, quest rewards/Hellforge/Anya, events) → the rich boss-detail format. Build a
  coverage matrix first; real data only.
- **artOr title sweep:** remaining bare-emoji titles (Herald emblem, static TZ "🎯" meta).
- **boss-nav symmetry:** WORLD EVENT (Uber Diablo) chip grid alignment vs the other tiers.

### Batch 2 ✅ (full suite 410 passed / 1 skipped, 17.6m · commit `3956432` · deploy `8b9ff767` · md5 parity ✓)
- **Emblem unification through artOr** — super-unique *detail-header* emblem (was bare 💀),
  uber-boss emblem (was a hardcoded `<img>`), and Herald tier 1-4 emblems (were bare 👹) now
  all route through the central art helper. Uber art is mirrored into `D2IO_ART` from each
  entry's existing `b.art` (single source, no duplicated URLs); Herald tiers wear the verified
  `HERALD_PORTRAIT` (the same monster art the apex card uses) with 👹 fallback. All REG-001-safe
  (`loading="lazy"` + onerror). `D2IO_ART` stays a pure diablo2.io-URL map — `HERALD_PORTRAIT`
  (a data-URI) is built inline, NOT injected into the map (would break the v71 URL invariant).
- **boss-nav alignment** — reserved a uniform 2-line label height
  (`.boss-nav-sticky .boss-nav-group-label{min-height:2.4em}`) so every tier column's chips
  start at the same Y. Root cause: single-line labels (ACT BOSSES) sat 23px higher than the
  2-line ones; WORLD EVENT's lone chip only *looked* off next to taller stacks. Verified all 6
  columns now share chipTop.
- **Coverage matrix delivered** — per-entity-class audit of the 12 Baal-card sections (BOSSES
  full ✓; ubers/super-uniques/heralds have gaps in why-farm/feeds-into/best-char/action-plan/
  top-grail/top-table; numeric columns for ubers blocked on real RoW odds — flagged, never faked).
- **v75 test updated** to assert the Herald *portrait* (not a charm graphic) + lazy lock.

### Batch 3+ backlog (Konyo's unified-ID-card vision — additive, no cuts, no fabrication)
- **TZ-zone enrichment:** the ~11 terror zones + the Pit cross-link get the unified rich card
  (already have location/mlvl/TC/density/super-unique roster/grail pool/why-farm/feeds-into).
  ADD: a dedicated **special-drops** area (Worldstone Shards → Sunder, Hellforge rune, set/quest
  specials Konyo has actually found), best-char + action-plan, unified card shell. TZ zones are
  areas not bosses — keep them as zone cards but visually consistent with the boss ID card.
- **Unified card-template system:** one shared visual shell + type-specific section modules so
  bosses / ubers / events / super-uniques / heralds / TZ zones / tips all read as one design
  language (eye-candy, clean-cut), routed + clickable. Sections an entity lacks are simply
  omitted, not faked.
- **Hover-glow unification (batch 3):** unify the row/chip hover treatment site-wide (the clean
  `translateY(-1px)`+gold-border+soft-shadow idiom) so the hovered/selected entity is obvious.

---

## 2026-06-06 — CC night session: Colossal endgame enrichment + Herald dedup

**Context:** Konyo asked for a large, multi-phase enrichment of the RotW endgame
(Colossal Ancients) plus a Herald-of-Terror dedup, working autonomously overnight.
Data is "mostly extracted from diablo2.io"; the 6 jewel stats Konyo pasted are
authoritative. ZERO fabrication mandate.

### Phase 32 — Herald of Terror dedup ✅ SHIPPED-LOCAL (pending commit)
- **Problem:** `'Herald of Terror'` resolved to TWO cards — the lean
  `heraldTierDetailHtml` tier card (via `openDrop` → `findHeraldTier`, checked first)
  AND the rich dedicated RotW `#herald-card` (search cmd + `renderHeraldCard`).
  Two search results, one richer than the other.
- **Fix:** added `window.openHeraldCard()` (switchTab rotw → expand section → scroll
  to `#herald-card`). `openDrop()` apex branch now redirects to it. Search:
  removed the duplicate apex entry from the HERALD_TIERS loop (`if (t.apex) return`);
  the dedicated RotW search cmd now calls `openHeraldCard()`. The 4 lower rungs
  (Fright/Dread/Fear/Horror) keep their lean tier cards.
- **Tests:** v75 updated (apex now asserts the rich RotW card, + a "only ONE
  Herald of Terror search result" guard). 26/26 green (v75+v72+v56+v80).

### Phase 33 — Endgame tab emblem/logo sync (Desktop continuation) ✅ SHIPPED-LOCAL
- The 4 `.road-branch` cards on the endgame maintab used flat emoji `<h3>` titles
  instead of the upgraded **animated** art emblems (`relicArtGlow` runs on
  `.d2art-img` inside `.endgame-relic`).
- Added `branchEmblem`/`branchEmblemRaw` helpers in `renderEndgameRoad()`; the 4
  branches now carry art emblems (Diablo Clone=`diablo_graphic.png`,
  Colossal=`talic-opt_graphic.png`, Herald=`HERALD_PORTRAIT`, Sunder=`Crack of the
  Heavens` charm art) + `.endgame-relic` glow. Sunder branch now routes via
  `openDrop('Crack of the Heavens')` (a real card) instead of a bare tab-switch.
  CSS: `.road-branch h3` → flex; `.rb-art` 38px. v80 7/7 green.

### Phase 34 — 6 Colossal Ancient Jewel ID cards + routing ✅ SHIPPED-LOCAL
- Self-contained `COLOSSAL_JEWELS` (6) module (line ~3657) → `findColossalJewel`
  + `colossalJewelDetailHtml` render a calculator-style `.colossal-jewel-card`
  into `#item-detail`. NOT folded into `SPECIAL_DROPS` (avoids
  `renderSpecialDrops`/`MATERIALS`/statue-tracker/baseline ripple — pure additive).
- `openDrop` hook inserted BEFORE `findMaterial` (exact normalized match), so the
  aggregate "Colossal Ancient Jewels" material card still resolves (additive, not
  a replacement). Global search: 6 jewel cmds (cat `colossal jewel`).
- Each Ancient's drop-row (Talic/Korlic/Madawc) now renders its **2 specific
  jewel chips** via a `jewels:[...]` field on `UBER_BOSSES` + `_jewelChips` in
  `renderUberBossCards`. Talic→Fire/Bile, Korlic→Frost/Stone, Madawc→Thunder/Light.

### Phase 35 — 5 named Colossal Statue ID cards + routing ✅ SHIPPED-LOCAL
- `COLOSSAL_STATUES` (5) + `findColossalStatue` + `colossalStatueDetailHtml`
  (`.colossal-statue-card`, drop-boss links via `openBossDetail`). `openDrop` hook
  + 5 search cmds (cat `colossal statue`). Aggregate "Colossal Ancient Statue"
  card untouched.
- Aggregate statue card's DROPS-FROM rows now link each named statue: statue-aware
  branch in the SHARED `materialDetailHtml` `fromRows` builder (prefix-matches the
  5 statue names only → every other material card renders unchanged).
- Statue tracker rows (`renderStatueTracker`): the name is now an `openDrop` link
  with `event.stopPropagation()` so it routes to the ID card without toggling collect.

### Phase 36 — glowing Colossal Endgame Showcase under Events ✅ SHIPPED-LOCAL
- New `#event-colossal-showcase` event-card in the ancients tab (under Events);
  `renderColossalShowcase()` paints 11 `.colossal-tile.endgame-relic` tiles (6
  jewels + 5 statues), each `openDrop`-routed + `artOr` emblem. Called at init
  after `renderUberBossCards()`. CSS `.colossal-grid`/`.colossal-tile` near
  `.statue-tracker`. The storyline `endgame` tab is left as-is.
- Sync: the existing `#event-colossal-ancients` jewel table's 6 names are now
  clickable → their new jewel cards (`event.stopPropagation();openDrop(...)`).

### Verification — full suite GREEN
- New spec `tests/v81_colossal_jewels.spec.ts` (11 tests): data modules, jewel/statue
  card render, additive-aggregate guard, global search, Ancient drop-row pairs,
  aggregate-statue DROPS-FROM links, statue-tracker routing, the 11-tile glowing
  showcase, event-table jewel links, no console errors. Gotcha for future specs:
  onclick attrs escape `'` as `\'`; an apostrophe-aware matcher
  (`/openDrop\('((?:\\.|[^'])*)'\)/` then unescape) is required to extract names
  like "Defender's Bile" — naive `[^']+` truncates at the inner apostrophe.
- `openDrop` + `materialDetailHtml` are CENTRAL (site-wide blast radius) → ran the
  WHOLE suite: **403 passed, 1 skipped** (15.6m). Dead-fork check clean.

### Ship complete — committed, deployed, pushed, CI-green
- Committed `f5e91a8` (Colossal pinnacle ID cards + Herald dedup + endgame emblem
  sync) + `2df6373` (Obsidian docs cross-ref + drop-odds/deploy provenance).
- Cloudflare deploy + md5 parity confirmed: local == live `47ead1c1…` at
  `https://bull-4-u.com/d2r/`. Pushed `ccdde35..f5e91a8` then `f5e91a8..2df6373`.
- CI backstop GREEN: scheduled Routine I run **27057755096** (headSha `2df6373`)
  all 4 jobs success (shard 1/3, 2/3, 3/3, merge reports). Golden smoke 51/51 local.

### Data — the 6 Colossal Ancient Jewels (Konyo-provided, diablo2.io)
All: 1% chance-to-cast its element armor when struck · +element dmg · +5-10% to
that skill-damage type · -5-10% to enemy element resist · +3-5% experience ·
+25-50% extra gold · +15-35% MF. ilvl 75. Strictly better than Rainbow Facets.
You get the jewel matching the Ancient you kill **last**.
| Jewel | Element | CtC armor (lvl) | +elem dmg | enemy res |
|---|---|---|---|---|
| Defender's Bile | poison | Bone Armor (25) | +95 poison/1s | -5-10% |
| Guardian's Thunder | lightning | Cyclone Armor (25) | +1-75 light | -5-10% |
| Protector's Frost | cold | Frozen Armor (25) | +10-30 cold | -5-10% |
| Defender's Fire | fire | Blaze (25) | +20-60 fire | -5-10% |
| Protector's Stone | physical | Fade (15) | +30-50% ED, +10-30 | -5-10% phys-dmg res |
| Guardian's Light | magic | Psychic Ward (25) | +15-35 magic | -5-10% |

Ancient → jewel pair (which Ancient drops which, by last-kill):
- **Talic** (sword/shield, WW) → Defender's Fire / Defender's Bile
- **Korlic** (polearm, Leap) → Protector's Frost / Protector's Stone
- **Madawc** (throwing axes) → Guardian's Thunder / Guardian's Light

### Data — the 5 named Colossal Statues (each from a TERRORIZED Hell act boss)
- Talic's Anguish — Hell Andariel
- Korlic's Pain — Hell Duriel
- Madawc's Ire — Hell Mephisto
- Bul-Kathos' Nightmare — Hell Diablo
- Worusk's End — Hell Baal
Rate ~1:8 to 1:15 per kill, terror only; MF does not affect. Cube all 5 →
Colossal Summit → summon the Colossal Ancients.

---

## v94 — Entity sync lock: unify the cow level across its 4 surfaces (single source of truth)

User directive: "this needs to be synced... not having duplicates of the same thing
and especially them not being synced. they need to be unified and rich... only
additive, nothing cut, only upgraded, and check for others like this."

### Duplication audit (ground truth)
Every drop-source entity is keyed by the SAME id across structures. The canonical
pair is **`BOSSES` (drop-table) + `BOSS_FIELD_MANUAL` (run tips)** — joined by id
into the one rich golden boss card. The *extra* surfaces (`#tab-ancients` event-card,
`RUNE_SOURCES` rune card) restate the same facts and had DRIFTED.

| Entity | Canonical (boss card) | Extra surfaces | Drift |
|---|---|---|---|
| cows | BOSSES.cows + FM.cows (Hell TC84 / TZ TC87) | event-card + RUNE_SOURCES.cow | **TC: card=TC84, FM="TC75-85", event="TC 66-69"; density "200+" vs "~400"** |
| travincal | BOSSES.travincal + FM | RUNE_SOURCES.travincal | none (FM "TC85 boss-quality" = super-unique bump over area TC84 — defensible) |
| pit | BOSSES.pit + FM | TZ-zone-rich card | none (mlvl85/TC85 agree) |
| countess | BOSSES.countess + FM | COUNTESS_RUNES table | none — that table is the ONLY verified per-rune data, unique not duplicate |

### Changes (additive + reconcile, nothing cut)
1. **Reconciled cow TC to the canonical boss-card value** (the authoritative, verified
   per-difficulty source): event-card "TC 66-69" → "TC84 in Hell (TC87 in a Terror
   Zone)"; `BOSS_FIELD_MANUAL.cows` "TC75-85" → same; density "200+" → "~400" (matches
   the figure already used on the other two cow surfaces + the canonical "highest
   density of any zone").
2. **Cross-links to the single source of truth**: added `bossId` to `RUNE_SOURCES.cow`
   ('cows') + `.travincal` ('travincal'); `runeSourceDetailHtml()` now renders a
   "🗺️ Full verified drop pool →" link that opens the canonical boss card. The cow
   event-card's TC line links to the Hell Bovines drop card too.
3. **No fabricated rune table**: only Countess has real per-rune 1:N odds. Cows/Travincal
   roll normal-monster odds with no published per-rune grid — kept the honest
   "would be fabricated" note instead of inventing one.

### Guard (the actual sync lock)
Two new tests in `tests/v83_sync_audit.spec.ts`:
- `entity sync: every RUNE_SOURCES bossId cross-link resolves to a real boss card`
- `entity sync: the cow Treasure-Class is unified to the canonical boss-card value`
  (asserts the stale "TC 66-69"/"TC75-85" strings are GONE and TC84 is present on both
  reconciled surfaces). Stops the drift from silently re-shipping.

Suite: v83 13/13, v53 9/9, 01_smoke + v71 21/21 green.

---

## v95 — "check for others like this": cross-surface dup sweep + Annihilus stat unify

Swept every entity defined in >1 structure (BOSSES ↔ SUPER_UNIQUES ↔ event-cards ↔
ITEM_CODEX). Findings:

| Entity | Surfaces | Status |
|---|---|---|
| Pindleskin | BOSSES.pindle + SUPER_UNIQUES | ✓ synced (both mlvl 86) |
| Nihlathak | BOSSES.nihl + SUPER_UNIQUES | ✓ synced (both mlvl 85) |
| The Summoner | BOSSES.summoner (mlvl 82) + SUPER_UNIQUES (mlvl 83) | ✗ 1-level drift — FLAGGED for Konyo (verified-stat lock; area+3 rule favours 83) |
| Annihilus | ITEM_CODEX (canonical) + 4 restatements | ✗ stat drift in 2 → FIXED |
| Hellfire Torch | ITEM_CODEX + restatements | ✗ "+20 all res" looks like the same drift — FLAGGED |

### Fixed (unambiguous — deferring to canonical ITEM_CODEX.Annihilus)
Canonical Anni = +1 All Skills · +10-20 All Attributes · +10-20 All Resistances ·
+5-10% Experience. Reconciled 4 wrong restatements:
- dclone event-card top box: "+20 all res" → "+10-20 all res · +5-10% experience"
- summary-map one-liner: "+1-2 ALL skills … +5-10% all stats" → canonical
- Road-tab prose: "+1–2 all skills, all-resist and all-stats" → canonical
- "who drops what" note: "+20 all res" → "+10-20 all res · +5-10% experience"

### Guard
New v83_sync_audit test: scans a window around EVERY "Annihilus" mention and asserts
none say "+1-2 all skills" / "+20 all res" / "all stats" (Anni-scoped so it doesn't
false-flag Arkaine's Valor / Atma's Wail which really are +1-2 all skills) + the
canonical ITEM_CODEX.Annihilus props survive.

### Flagged (NOT changed — need Konyo's verified-value call)
- The Summoner mlvl 82 (BOSSES) vs 83 (SUPER_UNIQUES). Pindle/Nihl both follow the
  project's verified area+3 rule and agree across surfaces; by that rule Summoner = 83
  (Arcane Sanctuary alvl 80 +3). Likely BOSSES 82 is the typo, but it touches the
  deliberate v43-binds-verified mlvl lock → confirm before flipping.
- Hellfire Torch "+20 all res" restatements (Torch is +10-20 all res) — same error
  pattern, different item.

Suite: v83 14/14, 01_smoke + v74 16/16 green.

---

## v96 — fix the two flagged drifts: Summoner mlvl + Hellfire Torch all-res

Konyo confirmed: fix both. Both reconciled toward the project's canonical/verified values.

### The Summoner mlvl 82 → 83
`BOSSES.summoner` Hell mlvl was 82; `SUPER_UNIQUES` "The Summoner" was 83. Per the
project's verified **area+3 rule** (Pindle = Nihlathak's-Temple alvl83 +3 = 86; Nihl =
Halls-of-Vaught alvl82 +3 = 85, both agreeing across surfaces), Summoner = Arcane
Sanctuary alvl80 +3 = **83**. Flipped BOSSES.summoner Hell mlvl 82 → 83 (drop unchanged:
Key of Hate 36%). `"mlvl":82` was unique in BOSSES; no test/baseline hardcoded 82.

### Hellfire Torch all-resist → +10-20 (unified)
Canonical Torch all-res = +10-20 (`"Hellfire Torch"` summary L4654 + Road-tab L5613).
Five restatements drifted ("+20 all res" ×2, "+10 res"/"+10 all res" ×3). Reconciled all
five to "+10-20 all res" (uber-tristram event top-box + body + Anya cube-output + the
"who drops what" note + the wishlist `why`). Left the SEPARATE attribute wording
("+20 stats" vs "+10-20 attr") untouched — not flagged, no single clean canonical.
Moser's Blessed Circle "+20 all res" is LEGIT (it really is +20) — Torch guard is
Torch-scoped (window around each "Hellfire Torch" mention), not a global match.

### Guards
2 new `v83_sync_audit` tests: Summoner mlvl agrees across BOSSES + SUPER_UNIQUES (=83);
Hellfire Torch carries no "+20 all res"/"+10 res" in any Torch-scoped window.

Suite: v83 16/16; v44 + v51 + smoke 23/23; FULL 432 pass/1 skip, 19.8min.

## v97 — "check for others like this" (round 2): the Annihilus codex note self-contradicted its own props

Second dup-sweep pass. Systematically cross-checked the remaining cross-surface entities:

### SUPER_UNIQUES ↔ BOSSES mlvl — all 3 overlaps now agree
Only 3 entities live in BOTH structures: Pindleskin (86=86 ✓), Nihlathak (85=85 ✓),
The Summoner (83=83 ✓, fixed v96). The other 14 super-uniques (Shenk, Eldritch,
Frozenstein, Hephasto, Izual, Endugu, Sszark, Blood Raven, Coldcrow, Smith, Griswold,
Bone Ash, Rakanishu, Bishibosh) are NOT in BOSSES → no cross-structure mlvl drift. Clean.

### The miss: ITEM_CODEX.Annihilus `note` drifted from its OWN `props`
The v95 Annihilus guard used a 230-char window around each "Annihilus" mention. A codex
entry's `note` field sits PAST its long `props` array (~330+ chars in), so the window never
reached it — and that note still read the pre-v95 drift:
`"+1-2 ALL skills · +10-20 all res · +5-10% all stats"` while the SAME object's props array
(the material-card source of truth) reads `+1 to All Skills / +10-20 to All Attributes /
All Resistances +10-20 / +5-10% to Experience Gained`. Reconciled the note to its own props:
`"+1 all skills · +10-20 all attributes · +10-20 all res · +5-10% experience · the SC charm grail"`.
Zero fabrication — every value already lived in the props array beside it.

### Guard hardening
Widened the Annihilus window 230 → 460 chars (reaches a codex `note`), and added an explicit
`page.evaluate` assertion that `ITEM_CODEX.Annihilus.note` contains no "+1-2 all skills" /
"all stats" and DOES contain "experience". The note-vs-props blind spot is now locked.

### Flagged (NOT auto-fixed — deferred to Konyo)
Two non-grail utility rings have a `note` that contradicts their own `props`, but the "right"
value is ambiguous (possible RoW-mod paraphrase / no clean canonical) so they were NOT touched:
- **Raven Frost** — note "+150-250 mana"; props say +40 Mana + 150-250 **Attack Rating**
  (the note mislabels the AR roll as mana).
- **Bul-Kathos Wedding Band** — note "+5% max life · +50 life"; props say +0.5 life/clvl +
  +50 Maximum **Stamina** (no "+5% max life"; the +50 is stamina, not life).
These are minor utility-ring display notes (not items Konyo is grail-hunting); listed here so
they can be reconciled deliberately rather than guessed.

Suite: v83 16/16; 01_smoke + v74_material_search 16/16 (note renders in the material card).

## v98 — reconcile the 2 flagged utility-ring notes to their own props

Konyo confirmed: fix both. Both notes reconciled toward their structured `props` array (the
canonical material-card source of truth) — zero fabrication, every value already lives in props.

### Raven Frost note — AR-as-mana mislabel fixed
Was "+15-20 DEX · +150-250 mana · Cannot Be Frozen". Props: +40 to Mana, +150-250 to **Attack
Rating** (the 150-250 roll is AR, not mana). → "+15-20 DEX · +40 mana · +150-250 AR · Cannot Be
Frozen · ESSENTIAL CBF ring for most builds".

### Bul-Kathos Wedding Band note — stamina-as-life + fabricated max-life fixed
Was "+1 ALL skills · +5% max life · +50 life". Props: +0.5 to Life (per clvl), +1 to All Skills,
3-5% Life Stolen, +50 Maximum **Stamina** — no flat "+50 life", no "+5% max life". →
"+1 all skills · +0.5 life/clvl · 3-5% life leech · +50 max stamina · pairs w/ SoJ for +2 skills total".

### Guard
New `v83_sync_audit` test "utility-ring codex notes agree with their own props": Raven Frost note
carries no "+150-250 mana" and DOES contain "+40 mana"; Bul-Kathos note carries no "+5% max life"
and DOES contain "stamina". Locks the note↔props self-consistency for these two.

Suite: v83 17/17; v74_material_search clean (note renders in the material card).

## v99 — note↔props sweep round 3: Bladebuckle relabel + Spirit Forge de-fabrication

Swept all 312 ITEM_CODEX notes with a PRECISE mislabel detector (same number, props tie it to
stat X but the note ties it to stat Y). The broad "note mentions a stat absent from props" scan
threw 49 hits — ALL false positives (abbreviated/flavor notes, named-skill props like "+1 Shadow
Disciplines" = "sin skills", individual resists summarized as "all res", empty-props sets/runes).
The tight detector found exactly 2 real ones:

### Bladebuckle (merc belt) — DEX shown as STR + def typo
Note was "+10 STR · +25 def". Props: +5 to Strength, +10 to **Dexterity**, +30 Defense. The +10 is
DEX (STR is +5); def is +30 (not +25). Reconciled to props (zero fabrication):
"+5 STR · +10 DEX · +30 def · merc belt".

### Spirit Forge (body armor) — fabricated stats, verified vs diablo2.io
Note was "+25 STR · light res +30 · CBF". This wasn't a clean relabel (those values weren't in
props), so it was FLAGGED to Konyo as possible RoW-mod-vs-stale. Konyo supplied the authoritative
source (diablo2.io/uniques/spirit-forge-t926.html): real Spirit Forge = **+15 To Strength**, Fire
Resist +5% (NO light res), Adds 20-65 Fire Damage, +120-160% ED, +1.25 life/clvl, +4 light radius,
2 sockets, **no Cannot Be Frozen** — i.e. the PROPS were already correct and the note fabricated
+25 STR / +30 light res / CBF. Reconciled the note to the verified data:
"+15 STR · +5% fire res · adds 20-65 fire dmg · 2 sockets · niche zealer body".

### Guard
Extended the v83 "utility-ring codex notes agree with their own props" test: Bladebuckle note
carries no "+10 STR" + has "+10 DEX"; Spirit Forge note carries no "+25 STR"/"light res"/"CBF" +
has "+15 STR".

Suite: v83 17/17; v74_material_search clean. ITEM_CODEX note↔props sweep now exhausted
(Annihilus v97 · Raven Frost + Bul-Kathos v98 · Bladebuckle + Spirit Forge v99).

## v100 — the unsynced-duplicate ROOT: ITEM_INFO is a second copy of the codex notes

"Check for others like this" round 4 found the structural reason the v98/v99 fixes were
incomplete: **`ITEM_INFO` is a SECOND hardcoded copy of each gear item's codex `note`** (merged
at runtime with `ITEM_INFO_EXTRA` via `for(k in EXTRA){ if(!(k in ITEM_INFO)) ITEM_INFO[k]=… }`,
L4945). The material card renders `ITEM_INFO[name]`, NOT the codex note — so fixing only the
codex note (v98 RF/BK, v99 Bladebuckle/Spirit Forge) left the USER-VISIBLE one-liner stale.

### Stale duplicates synced (4 gear items)
- **Raven Frost** ITEM_INFO: "+150-250 mana" → "+40 mana · +150-250 AR" (matches v98 note)
- **Bul-Kathos** ITEM_INFO: "+5% max life · +50 life" → "+0.5 life/clvl · 3-5% life leech · +50 max stamina"
- **Spirit Forge** ITEM_INFO_EXTRA (L4696): "+25 STR · light res +30 · CBF" → "+15 STR · +5% fire res · adds 20-65 fire dmg · 2 sockets" (diablo2.io-verified)
- **Bladebuckle** ITEM_INFO_EXTRA (L4750): "+10 STR · +25 def" → "+5 STR · +10 DEX · +30 def"

### Guard — the general lock (supersedes piecemeal note checks)
New v83 test "ITEM_INFO gear one-liners stay identical to their ITEM_CODEX note": for every
GEAR item (non-empty `props`) present in both maps, INFO must equal the note (case-insensitive).
Scoped to gear so keys/runes/shards — which intentionally carry a short crosslink blurb in
ITEM_INFO vs a detailed `note` (empty props) — are excluded. This locks ALL ~96 shared gear
one-liners, so a future single-surface edit can't silently desync the pair again.

### Lesson
The material card's source of truth is `ITEM_INFO[name]` (with codex-note fallback), and
ITEM_INFO duplicates the notes. ANY item-stat edit must touch BOTH (or the guard fails). The
v98/v99 guards only checked `codex.note` → blind to the visible ITEM_INFO copy. Fixed by the
map-level identity invariant above.

Suite: v83 18/18; v74_material_search clean.

---

## v101 — Colossal-Ancient 3-way mapping lock (guard-only, 2026-06-07)

Round-5 "check for others like this": audited the ITEM_INFO/ITEM_INFO_EXTRA duplicate-map
surface. Structural findings: (A) ~20 shadowed EXTRA keys identical to their ITEM_INFO copy
(harmless dead duplicates, can't remove under additive-only); (B) no gear note missing a
one-liner; (C) 6 orphan descriptions with no codex card — the 5 Colossal-Ancient statue
drops + Hellfire Torch (latter already locked v100-era).

### The one drift-prone shape surfaced — and it was CLEAN
The 5 Colossal-Ancient statue drops are defined in THREE parallel structures:
- `COLOSSAL_STATUES` (L3807, `bossId`)
- `STATUE_LIST` (L4949, `bossId`)
- `ITEM_INFO_EXTRA` (L4915, prose naming the boss)

The drop→boss mapping (Talic's Anguish→andariel, Korlic's Pain→duriel, Madawc's Ire→mephisto,
Bul-Kathos' Nightmare→diablo, Worusk's End→baal) AGREES across all three. **No fix needed —
no fabrication.** But it was an UNGUARDED 3-way duplicate, exactly the drift shape this audit
locks, so it got a guard rather than a data edit.

### Guard added
New v83 test "Colossal-Ancient statue drops map to the SAME boss across all 3 structures":
asserts `COLOSSAL_STATUES.bossId === STATUE_LIST.bossId` AND the `ITEM_INFO` prose names that
same boss, for each of the 5 drops. Locks the 3-way mapping against future single-structure edits.

### Lesson
Not every "check for others" round ends in a data fix — when the parallel structures already
agree, the honest outcome is "clean + add the lock", not a manufactured edit. `bible.html`
UNCHANGED this ship (no md5 change → no live redeploy needed); only the test file grew 18→19.

Suite: v83 19/19; v74_material_search 8/8 clean.

---

## v102 — Colossal jewel→Ancient binding lock (guard-only, 2026-06-07)

Round-6 "check for others like this". First confirmed the sunder/shard element↔region mapping
is consistent across its 3 structures (ACT_SHARD L3678, SHARD_RENEWED L4232, SHARD_OUTCOMES
L8600) — all agree (Western/poison/Rotting Fissure, Eastern/cold/Cold Rupture, Southern/
lightning/Crack of the Heavens, Deep/fire/Flame Rift, Northern/physical/Bone Break). No fix.

### The drift-prone shape surfaced — and it was CLEAN
The jewel→Ancient binding lives in TWO structures plus a third prose restatement:
- `COLOSSAL_JEWELS[].ancient` (L3799)
- `UBER_BOSSES[].jewels` (L8847, the Ancient's loot list)
- each jewel's ELEMENT restated in the Ancient's `strat` prose (L8848/8857/8866)

All three AGREE: talic→{Defender's Fire (fire), Defender's Bile (poison)}, korlic→
{Protector's Frost (cold), Protector's Stone (physical)}, madawc→{Guardian's Thunder
(lightning), Guardian's Light (magic)}. No fabrication, no data edit.

### Guard added
New v83 test "Colossal jewel→Ancient binding agrees between COLOSSAL_JEWELS and UBER_BOSSES
(+ strat names the element)": for each Ancient's jewel, assert COLOSSAL_JEWELS.ancient matches
the UBER_BOSSES owner AND the Ancient's strat prose names that jewel's element. Locks the 2+1
restatement against future single-structure drift. bible.html UNCHANGED (live still `a8485e3`).

Suite: v83 20/20; v74_material_search 8/8 clean.

---

## v103 — guaranteed-drops orphan + Hellforge pool lock (guard-only, 2026-06-07)

Round-7 "check for others like this". Surfaced two drift surfaces around the "guaranteed drops"
feature — both currently consistent, so guard-only (no data edit, bible.html UNCHANGED).

### (A) Hellforge rune tier pools — stated 3× , all agree
El–Amn / Sol–Um / Hel–Gul (max Gul) appears in: static HTML `#guaranteed-global-card .gc-tiers`
(L2184, rendered), `GUARANTEED_DROPS_GLOBAL[].tiers` (L6914, const), and `RUNE_SOURCES` hellforge
`.tierPool` (L8231-8233, rendered rune card). No fabrication.

### (B) GUARANTEED_DROPS_GLOBAL is an ORPHANED duplicate
The const at L6908 (6 guaranteed drops) is NEVER rendered — only `GUARANTEED_PER_BOSS` (L6965)
is used (boss-card section L6848). The visible "guaranteed drops" grid is the STATIC HTML block
at L2178-2221 hardcoding the same 6 drops. They agree today on icon→tier (⚒️S+, 🛡️A, 💎A, 🔨S,
📖B+, 📜—) but an edit to the dead const would never show on screen → silent drift. Per
additive-only the orphan const is NOT deleted; instead it's LOCKED to the rendered surface.

### Guard added
New v83 test: (1) all 3 surfaces contain each Hellforge pool token (el–amn/sol–um/hel–gul);
(2) every GUARANTEED_DROPS_GLOBAL item's icon→tier equals the rendered guaranteed-card grid;
(3) both the const and the grid still hold all 6 drops. Locks the orphan to the visible HTML.

### Lesson
An orphaned const that mirrors static HTML is a latent drift trap — nothing breaks visually if
it drifts, so it goes undetected. When additive-only forbids deletion, LOCK the dead copy to the
rendered surface instead. Note for a future pass: `GUARANTEED_DROPS_GLOBAL` carries richer fields
(where/what/cadence) than the static HTML uses — a real dedup would render the const and delete
the hardcoded block, but that's a refactor, not this sync sweep.

Suite: v83 21/21; v74_material_search 8/8 clean.

---

## v104 — sunder element↔region 4-way web lock (guard-only, 2026-06-07)

Round-8 "check for others like this". The core RotW **sunder mapping** (region→act→element→
sunder-name) is restated across FOUR structures and was entirely unguarded:
- `ACT_SHARD` (L3678) — region→act number
- `SHARD_RENEWED` (L4232) — region→renewed-sunder name + element
- `SHARD_OUTCOMES` (L8600) — region→act / sunder / element (the canonical 4-field spine)
- `_HERALD_SUNDERS` (L8730) — sunder→element (`breaks`) + region (in `rec`)

All four AGREE: Western/1/poison/Rotting Fissure · Eastern/2/cold/Cold Rupture · Southern/3/
lightning/Crack of the Heavens · Deep/4/fire/Flame Rift · Northern/5/physical/Bone Break. (The
6th sunder, Black Cleft/Magic, is a 3-shard combo with no single region — correctly absent from
the 5-region spine.) No fabrication, no data edit; bible.html UNCHANGED (live still `a8485e3`).

### Guard added
New v83 test iterates SHARD_OUTCOMES (the spine) and asserts, per region: ACT_SHARD[act#]===region,
SHARD_RENEWED[region] names both the sunder + element, and _HERALD_SUNDERS (matched by sunder
name) `breaks` the element + its recipe names the region. Locks all 4 surfaces together. This is
the proper follow-through on round-6, where the same web was eyeballed-clean but left unguarded.

### Lesson
Round-6 verified 3 of these by eye and judged a guard "not needed" — but I'd MISSED the 4th
structure (_HERALD_SUNDERS) entirely. "Verified clean by eye" is not the same as "locked": a
4-way grail-relevant web with zero guards is a standing drift risk. When a sweep finds a
consistent multi-structure mapping, LOCK it even if it looks clean — that's the whole point.

Suite: v83 22/22; v74_material_search 8/8 clean.

---

## v105 — SPECIAL_DROPS ↔ boss-mapping cross-lock (guard-only, 2026-06-07)

Round-9 "check for others like this". `SPECIAL_DROPS` (L3570) is the canonical material DB; it
restates FOUR boss→drop maps that ALSO live in other structures — none were cross-guarded:
- **boss→Pandemonium-key** — `EXCLUSIVE_DROPS` (L7103) · `BOSS_FEEDS_INTO` (L3667) · `SPECIAL_DROPS.key`
  (countess→Key of Terror, summoner→Key of Hate, nihl→Key of Destruction)
- **boss→Essence** — `BOSS_FEEDS_INTO` · `SPECIAL_DROPS.essence` (Andariel+Duriel→Suffering,
  Mephisto→Hatred, Diablo→Terror, Baal→Destruction — Andariel & Duriel SHARE Suffering, verified)
- **dclone→Annihilus** — `EXCLUSIVE_DROPS` · `BOSS_FEEDS_INTO` · `SPECIAL_DROPS.uberCharm`
- **Colossal statue→boss** — `SPECIAL_DROPS.colossalStatue.from` is a 4th statue→boss surface that
  the v101 guard MISSED (same gap pattern round-8 hit with `_HERALD_SUNDERS`)

All four AGREE. No fabrication, no data edit; bible.html UNCHANGED (live still `a8485e3`).

### Guard added
One comprehensive v83 test cross-checks SPECIAL_DROPS against EXCLUSIVE_DROPS / BOSS_FEEDS_INTO /
COLOSSAL_STATUES for all four maps (key label match + `from` names the boss; essence label + from;
Annihilus label + from contains "Clone"; each statue's `from` segment names its bossId).

### Lesson
SPECIAL_DROPS is the single most-restated data hub — keys/essences/organs/charms/statues/shards
all also appear in the per-boss feed structures. Each new guard round keeps finding the SAME
shape: a canonical structure whose mapping is duplicated in 2-3 sibling structures, consistent
but unguarded. The recurring "missed a 4th surface" (v104 _HERALD_SUNDERS, v105 SPECIAL_DROPS
colossalStatue) confirms: when locking a mapping, grep ALL structures that could restate it
before declaring the web fully covered.

Suite: v83 23/23; v74_material_search 8/8 clean.

---

## v106 — Token of Absolution as a first-class item (FEATURE, ships bible.html)

User request: "ALL 4 ESSENCES we have for essences should create something of destruction —
it's called something... this should also be an item and updated accordingly to the tabs and
subtabs associated with it." The cube product of the 4 Essences is the **Token of Absolution**;
it previously existed ONLY as a recipe-output string (`MATERIAL_RECIPES` + essence blurb/recipe),
never as a routable/searchable item.

### What shipped (additive, DRY — flows through existing generic code)
- New `SPECIAL_DROPS.token` category (between `essence` and `key`, L3583) — icon 🎟️, label
  "Token of Absolution", blurb + 1 item (`from:["Horadric Cube (4 Essences)"]`, `does:` full
  respec, `note:` cube the 4 essences). `recipe` is VERBATIM the essence-category recipe.
- `MATERIAL_FEEDS.token = 'a full respec (reset skills + stats)'` (L3713).
- `SD_META.token` (search builder, L10545) — icon/sub/keywords so it's globally searchable.
- `renderEventRef` "who drops what" grid gains a 4th block `block(sd.token,'Full Respec')` (L4492).

This auto-flows into: the material ID card (`materialDetailHtml`), the Special-Drops grid
(`renderSpecialDrops` iterates `Object.entries(SPECIAL_DROPS)`), global search + `openDrop`
routing, and the Main-tab cross-link reference — ALL via existing generic code paths.
`MATERIAL_CATS` (stash tally) deliberately UNCHANGED (5 cats) so the stash count stays 21.

### Zero fabrication
Standard D2R facts: cube the 4 Hell-act-boss essences (Suffering+Hatred+Terror+Destruction) →
1 Token; right-click to reset ALL skill AND stat points (full respec); single-use/consumed;
farmable & stackable (unlike the 1-per-difficulty Akara respec).

### Guard added (v83 test 24)
Token recipe names every essence + == the essence-category recipe; `MATERIAL_RECIPES` Token
`need{}` holds the same 4 essences; `openDrop('Token of Absolution')` opens a `.material-card`
in `#item-detail` (respec/reset text present); global search → pick → opens the same card.

Suite: v83 24/24; v74_material_search + v52 + v70 + v55 29/29; smoke 01+v71 21/21.

---

## v107 — Lister the Tormentor as a first-class super-unique (FEATURE, ships bible.html)

Konyo: "listor the tormentor ... this is the best to bind and as a search like its own idcard ...
like hephasto the armorer i see we have it.. so listor needs to be also gap filled accordingly."

Lister the Tormentor (Baal's wave-5 Throne of Destruction boss) was NAMED in the binds tab
(wave table + monster-data sources) but had NO `SUPER_UNIQUES` entry — unlike Hephasto the
Armorer, which is a full entity with an ID card. Gap-filled by appending one `SUPER_UNIQUES`
member (after Bishibosh, end of array → no index shift). That single struct auto-flows into:
the super-unique ID card (`superUniqueDetailHtml` golden `.gbc-card` shell), the TZ-tab
super-unique roster (`renderSuperUniques`), global search (`SU_DATA.forEach`, L10513), and
`linkifySU`/`suIndexByName` name-routing — all via existing generic code.

### Zero fabrication (sourced from the bible's OWN binds tab + standard D2 facts)
- mlvl **92** (binds-tab monster-data lock, L3407 "Lister 92 (custom overrides)").
- Leads **7 Minions of Destruction** in Hell (NM 6 / Norm 5) (binds wave table L3369).
- Act 5 · Throne of Destruction; not on the TZ rotation (Throne-only, not on-demand farmable).
- One of only TWO super-uniques (with The Smith) whose bind/Consume stats are fully sourced.
- Immunity set to **"random (Hell)"** (NOT a hardcoded Physical immunity — honestly flagged in
  prose: Throne-boss Hell immunities roll per spawn; a Physical-immune Lister is common, so
  bring a 2nd damage type or a Bone Break sunder. Answers Konyo's "physical immunity right?"
  without fabricating a fixed immunity.)

### Guard added (v83 test, now 25 sync tests)
Lister is in SUPER_UNIQUES · mlvl===92 agrees with the binds-tab note · binds tab still
references him · Hephasto (the precedent) still present · `jumpToSuperUniqueByName` opens his
`.su-card-rich` gbc card naming "Throne of Destruction" · he's searchable as a Throne super-unique.

Suite: v83 25 sync tests (31/31 w/ Token) ; v51_superuniques + v41 + v40 + routing 41/41 ;
v64 routing green. No console errors, no fabricated-odds violation (v51 sanity).

---

## v108 — full super-unique artOr coverage (real diablo2.io portraits) — 2026-06-08 (CC, opus4)

**FEATURE (ships bible.html).** Konyo: "art0r for all logos of items/bosses/uniques —
check others." Audited every drop-source entity for emoji-only fallback and closed the
super-unique gap end-to-end.

### Added (D2IO_ART, 9 verified URLs)
- **Lister the Tormentor** → `items/thetormentor_graphic.png` (the v107 entry shipped on the
  👿 emoji — now real art).
- **Eldritch the Rectifier · Witch Doctor Endugu · Blood Raven · Coldcrow · Griswold ·
  Bone Ash · Rakanishu · Bishibosh** → `images/avatars/gallery/6. Super Unique Monsters/<Name>.gif`
  (spaces %20-encoded).
- Every URL probed live (HTTP 200 + image content-type) before adding — **zero guessed URLs.**
  Result: **all 18 SUPER_UNIQUES now carry real diablo2.io art** (the other 9 — Shenk, Summoner,
  Nihlathak, Hephasto, Izual, Frozenstein, Pindleskin, Sszark, The Smith — were already mapped).

### Verified-absent (kept honest emoji fallback — NO fabrication)
- 4 **Essences** (Suffering/Hatred/Terror/Destruction) and 5 **Worldstone Shards**
  (Western/Eastern/Southern/Northern/Deep) + **Colossal Ancient Jewels**: diablo2.io has no
  graphic under any tried naming (`_graphic.png`, gallery `0. Items`, item-code, base-name).
  RotW-mod / quest items absent from the avatar gallery. They keep 🩸/💠/💎 emoji.
- All 13 tracked BOSSES already had art (confirmed programmatically).

### Guards (v71_d2art — IN the pre-push smoke gate, now 15 tests)
- "every super-unique resolves verified diablo2.io art" — `SUPER_UNIQUES.filter(s=>!artUrl(s.name))`
  must be `[]`; locks 18/18 coverage so a future SU can't silently regress to emoji-only.
- "the new Lister super-unique card renders its verified portrait art" — jump→card→`.gbc-header
  .d2art-img` src matches `thetormentor_graphic.png` + `loading=lazy`.

Suite: v71_d2art 15/15 · v51_superuniques + v83 sync (37) + v45 all green. Smoke 36→still gated.

---

## v109 — Warlock Bind Demon tab made collapsible (matches the site idiom) — 2026-06-08 (CC, opus4)

**FEATURE (ships bible.html).** Konyo: "bind section i see isnt collapsible and isnt
matching the other tabs.. maybe needs an update too." The `#tab-binds` tab was a stack of
always-open `.colossal` blocks with plain `<h3>` headers — the only tab that didn't use the
site-wide collapsible `.sec-h`/`.sec-body` dropdown idiom (v56/v63, default-COLLAPSED).

### Change (additive re-wrap — content verbatim, nothing cut)
All **12** binds sections (binds-gate · aura · howto · cant · champion · unique · superunique ·
fieldguide · packsizes · tz · konyo · sources) converted to the generic `toggleSec()` pattern:
- plain-`<h3>` heads → `<h3 class="sec-h collapsed" onclick="toggleSec(this)">…<span class="sec-chev">▾</span></h3>`
  + body wrapped in `<div class="sec-body" hidden>`.
- the 3 **tier-header** sections (Champion/Unique/Super-Unique) keep their fancy gradient banner —
  the `.tier-header` div now also carries `sec-h collapsed` + the toggle, so the whole banner is the
  clickable header. The `#binds-superunique .tier-header h3` glow CSS still applies (banner unchanged).
- the `.events-intro` banner stays always-on (the tab description, like RotW keeps its Herald head).

### Guard — `tests/v109_binds_collapsible.spec.ts` (4 tests)
12 `.sec-h` + 12 `.sec-body` all `[hidden]` by default · 12 chevrons · intro still visible ·
click-expand/click-collapse on a plain head · the tier-header Super-Unique section toggles + still
shows Lister/Hephasto rows · `#tab-binds` textContent still carries the Lister-92 / Throne data the
v83 sync test depends on (textContent reaches collapsed sections, so v83 stays green).

Suite: v109 4/4 · v83 25/25 · 01_smoke + bug023 static-tabs green. Div-balance verified 0.

---

## v110 — Lister art fix: monster portrait, not the item (commit `8f28486`, live `00f586e7`)

### Bug
v108 mapped `Lister the Tormentor → thetormentor_graphic.png` — that's the unique **item**
"The Tormentor" (a Battle Cestus), NOT the monster. Konyo caught the wrong logo.

### Fix
diablo2.io's monster page (`lister-the-tormentor-t4331.html`) serves **`lister01_graphic.png`** —
the real extracted portrait. One-line D2IO_ART swap. Audited the other item-path SU graphics
(`summoner`/`hephasto`/`shenk`/`smith`/`sszark`/`nihlathak`/`reanimatedhorde`): all genuinely monster
art (no unique item shares those names) — only "The Tormentor" collided with an item. v71_d2art
assertions updated to `/lister01_graphic\.png$/`. **Lesson:** when a super-unique's TITLE doubles as
a unique item name, the `_graphic.png` item-path will grab the ITEM — pull the portrait the monster
page actually references instead.

---

## v111 — Warlock-bind callouts on the Lister & Hephasto cards (commit `c712bcb`, live `b7145498`)

### Request (Konyo)
In-depth Lister card: TZ Physical-immune detail + "what's the best roll?" + emphasize it's the OP
Warlock bind. Then "same logic + emphasis for Hephasto". Cleared to research beyond the bible.

### Research (diablo2.io forums · aoeah · icy-veins · the bible's own verified-3.2 binds tab)
Two-layer model resolves the fixed-vs-rolls tension:
- **Lister** — permanent CONSUME (fixed): **+150% ED · 25% Physical DR (rare) · Lvl 15 Meditation**
  (mana engine, out-regens merc Insight). PROJECTED Aura Enchanted **rolls per spawn** → save&exit /
  re-make and **reroll for Fanaticism** (Conviction for fire), bind at lvl 94+ in a **TZ (mlvl 96)**
  to cap aura at `floor(96/8)=12`. ~31.8k HP / ~348 res + 7 Minions = aggro meat-shield; guaranteed
  Throne Wave 5 = easiest top bind; persists between games. Hell immunity rolls per spawn (often
  **Physical Immune**; Fire/Cold/Lit/Pois/Magic all possible) — bring a 2nd damage type / Bone Break.
- **Hephasto** — **always Aura-Enchanted, solo** at the Hellforge → **reroll for Fanaticism** = BiS
  damage. Fire-immune. 20 hard points.

### Change (additive, data-driven)
Added `bind` (rich HTML) + `bindTier` to the Lister & Hephasto SUPER_UNIQUES entries; `superUniqueDetailHtml`
renders a gold/purple **⚜️ Warlock Bind** callout when `su.bind` exists (only those two show it).

### Guard — `tests/v111_warlock_bind_cards.spec.ts` (5 tests)
exactly {Hephasto, Lister} carry su.bind · Lister callout has 150% ED / 25% DR / Meditation /
Fanaticism / Terror Zone / 20 hard points · Hephasto callout has Always Aura Enchanted / Fanaticism /
solo / Fire Immune · a non-bind SU (Shenk) shows none · no console errors.

Suite: v111 5/5 · v71 15/15 · v83 30/30 · v109 4/4 (49 green together). Smoke gate 38/38 on push.

---

## v112 — binds tier-list card + Aura Enchanted elite-affix deep-dive + Lister/Hephasto drop pools (2026-06-08)

Commit `7206e27` · live md5 `e2033c39e16c734ca27bc37f7dc5d07b` (apex parity verified).

Three additive ships, all clickable/routable in the site's existing format:

1. **🏆 Best Warlock Binds — Tier List** (`#binds-tierlist`, top of binds tab) — ranked
   best→budget (S: Hephasto→Fana / TZ-Urdar 15pt / Lister · A: Smith / champ-Urdar 10pt ·
   B-C: Council / 1-pt splash). The 3 fully-sourced targets (Hephasto/Lister/Smith) route to
   their super-unique ID cards via `jumpToSuperUniqueByName`; Urdar/Council route to their
   tier tables via NEW `window.openBindSection(id)` helper (expands collapsed sec + scrolls).

2. **⚜️ Aura Enchanted — exact aura levels & Hell elite-affix pool** (`#binds-elite`) — from
   maxroll's Elite Monster guide. Per-aura level divisors (Fanaticism/Conviction/Holy Shock
   = mlvl÷8 → cap 12 · Holy Freeze ÷7 · Holy Fire/Might ÷6 · Blessed Aim ÷5), aura RANDOM per
   spawn (confirms Konyo's "the aura changes"), 3 Hell affixes / 1 Aura-Enchanted max, full
   13-affix roll pool incl. Mana Burn (= Lister's "I can't"). Busts the "everything is ÷8" myth.

3. **Baal-card-parity DROP POOLS** on Lister + Hephasto cards — NEW `su.pool:{tcMax,mlvl,src}`
   field drives a `zoneHellGridHtml(pz)` ranked grid (reused engine, every row routes via
   `navigateToItem`, zero fabricated odds). Lister = Throne Wave 5 · TC87/mlvl 92 (bible L9755
   "all TC87 quality"). Hephasto = terrored River of Flame · mlvl 96/TC87. Shenk (no pool) = none.

**Source consolidation** (Konyo: "keep the source in the reference tab, separate it nicely"):
all bind/aura citations moved into a new `📐 reference` tab section "⚜️ Warlock bind & Aura
Enchanted — sources" (maxroll Elite Monster · maxroll Summoner Warlock · diablo2.io · this
tab's verified-3.2 · silospen). Inline notes slimmed to "(sources in the 📐 reference tab)".

### Guard — `tests/v112_binds_tierlist_droppool.spec.ts` (9 tests)
tier-list 7 rows + 4 routes · elite-affix per-aura table + Mana Burn + random-per-spawn ·
sources in ref tab not on cards · openBindSection expands · only Lister/Hephasto have su.pool ·
Lister grid TC87 clickable · Hephasto grid River of Flame · Shenk no pool · no console errors.

Suite: v112 9/9 · v111 5/5 · smoke-set+v83 63/63. Smoke gate 38/38 on push.
