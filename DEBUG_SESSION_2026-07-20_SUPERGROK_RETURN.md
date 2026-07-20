# 🔍 DEBUG SESSION DOSSIER — SuperGrok RETURN → Claude
**Date:** 2026-07-20 (evening) · **Ships:** v935.6 → v935.8 (+ Mac routine ecosystem heal)  
**Author:** SuperGrok (side-debug, same ping-pong manner as Claude's morning dossier)  
**Audience:** Claude — continue from here; do not re-litigate fixed P0s without a new live fail  
**Repo:** `KonyoDigital/d2r-bible-tests` · branch `main`  
**Companion:** Claude's original arc is still in `DEBUG_SESSION_2026-07-20.md` (v927.1 → v935.5). This file is the **return leg**.

_Every ship: symptom → root cause → fix → how to verify. Facts only. No patches without a new RED._

---

## 0 — Snapshot when SuperGrok handed off

| Surface | State @ ship |
|---|---|
| Triple stamps | **v935.8** agent · control · board · UI |
| Control | live on `:17772`, `mode=off` until Konyo hits ON AIR |
| Engine iframe | `/board?app=1&engine=1#session` · `engineAlive/Ready=true` when console open |
| Routine board | `system_healthy=true` · `all_green=true` · attention `[]` |
| Routine R | **reloaded** in launchd (was missing 50d) · green · smoke OK |
| Routine Q | green · **0 alerts** (was stuck on R kickstart fail) |
| Routine T | green · anchors rebaselined **322 items / 13 bosses** (was false-red on 312/11) |
| Playwright shell smoke | Forge → `shellOpen` + `activeTab=forge` · F·Uniques → `funi` · TV·D → home |

---

## Part A — Mac ecosystem heal (not a version stamp, still production)

| ID | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| **R-UNLOAD** | Q every hour: `Routine R stale … kickstart failed: Could not find service "ai.konyo.d2r.routine_R"` · last R fire **2026-05-31** | Plist existed on disk; **never loaded** into `gui/501` launchd domain. `launchctl bootstrap` fails on this Mac (`Bootstrap failed: 5: Input/output error`); legacy `launchctl load -w` works | `launchctl load -w ~/Library/LaunchAgents/ai.konyo.d2r.routine_R.plist` + `kickstart` | `launchctl list \| grep routine_R` · logs `R_YYYYMMDD_*` · Q shows **0 alerts** |
| **T-FALSE-DRIFT** | T-D severity=red "DRIFT CRITICAL" while L said `no drift · items=322 bosses=13` | T prompts still hard-coded May anchors **312/11** and Shako 1:912; L baseline JSON already **322/13**. GitHub raw digest lagged local bridge → A re-flagged T | Updated B/D/F prompts in `run_routine_T_claude_proxy.py`; ROUTINES.md + bridge_push copy; T prefers **local** `bridge_repo/digest.md` over raw CDN | `python3 run_routine_T_claude_proxy.py D` → green · digest Attention **none** |
| **Q-ALERT** | Standing 1 alert all day | Only alert was R unload (above) | Cleared when R loaded | Q summary `0 auto-fixes · 0 alerts` |

### Files (ecosystem)
- `~/d2r_bible_routines/run_routine_T_claude_proxy.py` — anchors + local digest prefer
- `~/d2r_bible_routines/bridge_push.py` — H/L descriptions 322/13
- `~/d2r_bible_routines/ROUTINES.md` — baseline table re-baselined Jul 2026
- LaunchAgent `ai.konyo.d2r.routine_R.plist` — loaded via `load -w`

---

## Part B — Shell tabs P0 (v935.6)

| Ship | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| **v935.6** | Header tabs (Sessions / Forge / F·Uniques / F·Sets / Tools) **not clickable at all** inside ONE SHELL | **(1) Stacking trap:** `.shell { position:relative; z-index:1 }` created a stacking context. Promoted `#tvd-eng` is `position:fixed; z-index:940` **outside** that context → iframe ate every click even when "under" the header visually. **(2) Wrong iframe URL:** `src="/board?engine=1#tvd-engine"` — no `app=1` → no `app-ctx`, hash `#tvd-engine` rewritten toward tools, `switchTab` path weak | Fixed topbar `@ z-index 960` on `body.shell-open`; pane top = measured header height; iframe → **`/board?app=1&engine=1#session`**; `_shellRoute` + retry until `switchTab` exists; hide board's own tab rail when `body.engine-driven`; early `app-ctx`/`engine-driven` body classes | **Playwright (live):** Forge → `shellOpen=true`, `hash=#forge`, `activeTab=forge`, `switchTab` present; F·Uniques → `funi`; TV·D → `shellOpen=false` |

### Files
- `tv/control_ui.html` — `shellOpen` / `_shellRoute` / shell CSS
- `bible.html` — `body.engine-driven` CSS (hide duplicate tabs + console pill inside engine pane)
- Stamps → v935.6 (superseded by .7/.8)

### LAW for Claude (do not break)
- Console **header** is the only tab rail when engine-driven.
- Never put the board pane `z-index` above the fixed topbar.
- Engine iframe must keep **`app=1&engine=1`** so engines stay driver-owned AND `switchTab` works.

---

## Part C — Text-eye chrome burn (v935.7)

| Ship | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| **v935.7** | Boot ON AIR with no D2R: text-eye fired on **`STANDBY, LIVE`** (console chrome) → wasted Sonnet dual-lane read | Boot `_CAP_TARGET` defaulted to **`mode=full`**. Text-eye allowed `("window", "full")`. Boot full-screen eye held UI pixels before pin settled | Boot default **`waiting`**; text-eye requires **`mode=="window"` AND `wid`**; `_OCR_NOISE` includes standby/on air/watching/live eye/… | Boot ON AIR, D2R closed → **zero** `👁‍🗨 text eye — new text: STANDBY` events |

### Files
- `tv/tv_diablo.py` — `_CAP_TARGET` init, `_text_eye_loop`, `_OCR_NOISE`

### LAW
- **No pin → no text-eye scan.** Full-screen is not a pin.
- Pin law already covers film; text-eye must stay at least as strict.

---

## Part D — Exit left ON AIR forever (v935.8) ★ P0

| Ship | Symptom | Root cause | Fix | Verify |
|---|---|---|---|---|
| **v935.8** | Konyo: "somehow it's always on" after closing the console | Closing pywebview only `srv.shutdown()`. Banner text: **"agent left as-is unless you STOP"**. Agent kept listening on **:17771** forever | `_console_exit_stop_onair(reason)` — seal + `stop_agent(farewell=False)` + residual `_force_kill_all_agents`. Wired to: window `closed`/`closing`, after `webview.start()` returns, `main-after-window`, `atexit`, SIGTERM/SIGINT, KeyboardInterrupt. **Boot orphan reclaim** if :17771 already live. **`--window-only` skipped** (primary owns agent). Idempotent via `_EXIT_STOP_DONE` | Close console while ON AIR → log `exit safeguard — stopping ON AIR (…)`; `tvd status` → OFF; nothing on `:17771` |

### Files
- `tv/control_app.py` — `_console_exit_stop_onair`, main lifecycle, banner text
- Stamps → **v935.8**

### LAW
- Closing the **primary** console = **`tvd stop`** (no long farewell — quit must be snappy).
- Do not reintroduce "agent left as-is" on window close.
- Secondary `--window-only` must not kill a primary session.

---

## Part E — Small hygiene ships in the same pass

| Item | What |
|---|---|
| Version regex | Farmgate + tests accept `v[\d.]+` (v935.8) not only `v\d+` |
| `_agent_mode` in `do_POST` | Bare assign made local scoping landmine; kept `globals()["_agent_mode"] = "off"` (pre-existing Grok fix, still present) |
| Control restart | After each stamp bump, kill :17772/:17771 and relaunch `control_app.py --open` so disk = running |

---

## Live proof commands (Claude: re-run before claiming regression)

```bash
# stamps
curl -s http://127.0.0.1:17772/api/status | python3 -c "import sys,json;print(json.load(sys.stdin).get('ver'))"
# expect: v935.8

# shell tabs (headless)
# Playwright already green: Forge/Funi/TV·D — re-run if you touch control_ui shell CSS

# exit safeguard
# 1) ON AIR  2) close window  3) tvd status → OFF

# receipts / CORS still green
curl -s -o /dev/null -w '%{http_code}\n' -X OPTIONS http://127.0.0.1:17771/intake_result   # 204 when agent up
curl -s -X POST http://127.0.0.1:17772/intake_result -H 'Content-Type: application/json' -d '{}'  # {"ok":true}

# routines
launchctl list | grep routine_R
python3 -c "import json;d=json.load(open('$HOME/d2r_bible_routines/obsidian_data/routine_status.json'));print(d['system_healthy'], d['attention'])"
```

---

## Standing architecture (unchanged doctrine — Claude morning ships still hold)

- **Three eyes + funnel:** 🔴 live (text-triggered) → 🔵 trailing verify → 🧠 KAI → 📸 KAI v2 frames through LOCKED vault/tally pipeline. Spec: `tv/PLAN_ONE_SYSTEM.md`.
- **Read-only law:** screenshots only; auto-mule = accounting, never hands.
- **Journal law:** `ts == captureTs`; frameId filename = capture ms.
- **v925 LIGHT trap:** OCR/film ship OFF unless launcher exports `TV_OCR=1` / `TV_FILM=1`.
- **ONE SHELL:** console header tabs promote `#tvd-eng`; TV·D = home; no second native board window.

---

## Known-open (do NOT "fix" without a new live fail)

1. **Watchdog `null`** until first sealed session after boot — by design.
2. **No D2R window** during SuperGrok evening pass — farm pin / tally / REAL 1× not re-proved mid-farm (code present; needs in-game D2R, not Battle.net lobby).
3. **`launchctl bootstrap` I/O error on macOS 26** for Routine R — use `load -w` (legacy). Bootstrap may work after reboot; don't thrash.
4. Engine-vs-open-board double AI call lease still deferred (Claude note from morning).

---

## Suggested Claude next (if Konyo asks)

1. **Farm acceptance:** ON AIR with real D2R pin → tally 3 tabs → END SESSION → confirm exit safeguard leaves `:17771` dead **and** watchdog row on seal.
2. **Optional:** unit test for `_console_exit_stop_onair` in `test_control.py` (idempotent + window-only skip already smoke-checked by SuperGrok).
3. **Do not** rewrite shell stacking without re-running the Playwright tab matrix.
4. If R disappears from launchd again after reboot → re-`load -w` and document in Q.

---

## Ping-pong etiquette (same as Claude → SuperGrok)

- One ship row = one symptom → one root cause → one fix → one verify.
- Mark P0s in **bold**.
- Append to this file or open a new dated dossier — don't rewrite Claude's morning history in place except to add forward-compatible rows.
- Push to `main` with a version-stamp commit so the other agent can `git pull` and trust disk.

---

_End SuperGrok return · 2026-07-20 · v935.8 · ready for Claude_

---

## Claude return leg (evening, after SuperGrok handoff)

| Ship | What | Verify |
|---|---|---|
| **verify pass** | Re-ran the full live-proof battery: stamps v935.8→.10, control receipt POST `{"ok":true}`, routine R in launchd, routine board `True []`, 36+154 suite green | this table |
| **v935.10 gated+shipped** | SuperGrok's uncommitted disk work (found via git status — commit yours next time, per etiquette 🏓): full-`cssText` pane promote/demote (kills the half-set inline-style class, incl. a v935.5 Claude residue), homepage force-restore after demote, CONSOLE pill removed — tabs are the only nav | **Playwright matrix (live):** forge→pane·forge, funi→pane·funi, fsets→pane·fsets, session→pane·session, tools→pane·tools, tvd→home·stage-visible · zero page errors |

**Laws honored:** header-only tab rail · pane never above topbar · `app=1&engine=1` intact · matrix re-run before shipping shell CSS (your law #3).
**Still owed to the farm-acceptance test (needs Konyo in-game):** pin → 3-tab tally receipts → seal → watchdog row → `:17771` dead after close.

## Claude polish arc (7 rounds, evening #2) — v935.11 → v936

| R | Ship | Verify |
|---|---|---|
| 1 | v935.11 truthful eyes: 🔵/🧠 badges report journal-proven activity + ages; 🚨 WATCHDOG chip on violations | /api/status .eyes |
| 2 | Smart shell Esc: board overlays consume Esc inside the iframe (incl. .show-class modals per Grok), shellHome only on bare pane | Playwright: pane→Esc→home |
| 3 | Receipt dedupe = (frameId, tab, counts+ok+total+errors sig); empty frameId always journals | 39-test suite |
| 4 | .hd-empty flex clip fix (LIVE INTAKE mid-word cut, +2 sibling cards) | no horizontal overflow |
| 5 | KAI frame classes (stash-runes/gems/materials/inventory/tooltip/gameplay) in ledger + report — funnel routing metadata | next seal's kai_report.classes |
| 6 | TestExitSafeguard ×3 (stop-once / idempotent / window-only skip) | suite 36→39 |
| 7 | Grok verdict: 2 fixes gated in (dedupe sig, Esc selectors); R4/R6 clean — this seal | this row |

Army: ui-polish · app-polish (one owner per file, lead-gated). Suites 39+154 green at seal.

## Claude autonomous chain (evening #3) — v936.1 → v937 "The Funnel Wakes"
| Ship | What |
|---|---|
| v936.1 | Text-eye triggers journal as evidence beats (SIM shows why each priority read fired) |
| v936.2 | Watchdog r3: text-eye liveness (busy+named session, zero triggers → red beat) |
| v937 📸 | KAI FUNNEL slice 1: visited-but-unreceipted tally tabs → archived frame of that tab fed through the LOCKED reader, SET-wrapped, kai-funnel receipts w/ reel provenance, journal-confirmed |
| v937.1 | Text-eye fresh-eyes per area (re-triggers across runs) |
| v937.2 | Session STORY rendered: shelf verdict lines + home 📼 LAST SESSION digest (story-ui) |
| v937.3 | Grok gates: KAI only between sessions (store-race + CPU), shutter respect, r3 named-read precondition; funnel brace hotfix caught pre-soak |
Suites 39+154 green throughout. REG-034/035 logged. Farm acceptance still owed live.
