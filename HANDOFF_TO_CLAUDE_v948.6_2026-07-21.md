# HANDOFF → Claude · v948.6 · 2026-07-21

**From:** Grok (xAI) session with Konyo  
**Repo:** `/Users/konyo/d2r_bible_tests`  
**Branch:** `main` (local mods **not committed** — see dirty files below)  
**Stamp truth:** agent = control = board = **v948.6**

---

## Mission (what Konyo is driving)

TV DIABLO live farm loop:

1. Three eyes + KAI read screen  
2. Gem/rune/material tallies + vault **grid count** (not identity vaultIntake on icon grids)  
3. **Item Checker** auto-path (subscription `intake_local`, **not** API tokens) → keep/mule/border/toss → vault + chronicle  
4. Chronicle inbox: review gate, **by session**, safe auto-triage  
5. Theatre: photos at **captureTs**, REAL vs FAST vs STORY must not lie about photo counts  

Do **not** change locked gem/rune/material intake geometry / `intake.js` prompt crops unless Konyo orders it. Bible has EDIT_LOCK areas — be careful.

---

## Uncommitted work (must preserve)

```
M  bible.html
M  tv/control_app.py
M  tv/control_ui.html
M  tv/test_routes.py
M  tv/tv_diablo.py
```

```bash
cd /Users/konyo/d2r_bible_tests
git status -sb
# verify stamps
rg -n 'VERSION = |"ver":|D2R_BUILD' tv/tv_diablo.py tv/control_app.py bible.html | head -20
python3 -m pytest tv/test_control.py tv/test_routes.py -q   # expect ~136 pass
```

---

## What shipped (v948.0 → v948.6)

### Sticky reads (v948.0)
- `tv_diablo.py`: session sticky `names_new` / `names_echo` / `names_moved`
- Register prefers NEW+MOVED (not Cube/Tome spam every deep)

### Item Checker auto-route (v948.1–v948.5)
| Piece | Where | Role |
|--------|--------|------|
| `_aicIntakeEndpoint` | `bible.html` | TV engine → same-origin `/api/intake` → `tv/intake_local.mjs` **subscription** |
| `aicJudge` | `bible.html` | Headless vision + `_aicVerdict` (no UI draft) |
| `aicJudgeApply` | `bible.html` | grail → chronicle+vault; keep → magicFinds+mule; border → hold; toss → ledger only |
| `_aicIsGrailName` | `bible.html` | **v948.5** — uses **ITEM_CODEX** (Hellfire Torch is NOT in boss-built `ITEMS[]`) |
| Stage-3 judge | `control_app.py` | Post-seal conf≥2 tooltip → aicJudge+Apply → `/kai_verdict` |
| Live judge queue | `control_app.py` `_engine_driver` | Mid-session on NEW/MOVED deeps; **v948.4** fires parallel to vaultcount (was starved) |
| `/kai_verdict` | `control_app.py` | Journals tier + `applied` + `live` |

### Chronicle (v948.5)
- `kaiChronicleTriage` — safe auto-**accept** grounded grails, auto-**dismiss** junk, **hold** border/keep  
- `kaiChroniclePropose` runs triage  
- Session batch APIs: `kaiChronicleAcceptSession`, `…Grails`, `…DismissSession`, `…DismissSessionJunk`  
- UI (`control_ui.html`): inbox **grouped by session** · ✓ Grail / ✓ All / ✕ Junk / ✕ All  

### Theatre photo sync (v948.6) — **just fixed**
**Bug:** REAL showed ~130+ film stills; “compressed beat” / HIGHLIGHTS left L/R on ~10–15 story frames only. Counters mixed session totals with filtered mode.

**Law now:**
| Mode | Photos | Time |
|------|--------|------|
| **REAL** | All session photos | Wall-clock 1:1 |
| **FAST** (was FULL) | **Same photos as REAL** | Time-zipped only |
| **STORY** (was HIGHLIGHTS) | Story AI + intakes + **sparse film near them** | Compressed |

Counters: `mode N · session total · 📹 film` + tally strip `📸 gems×… · runes×…`.

Key functions: `thFilter`, `thSessionPhotoStats`, `thModeLabel`, mode click re-sync in `tv/control_ui.html`.

---

## Live soak evidence (Konyo Mac, 2026-07-21)

### Session `s_1784636825977_40909` (~15:27) — **good tallies**
- Film: **136** `f_*.jpg`
- vault-count personal **18**, shared **72**
- gems kai-funnel + tally **693**
- runes kai-funnel **10**
- **materials: NEVER** — no `stash-materials` routing, no materials deep/intake (tab not visited)
- KAI routing labels: gameplay / stash / stash-gems×8 / stash-runes×10 / materials×0

### Session `s_1784647619282_26240` (~18:27) — **short soak, checker path**
- Film: **110** stills
- vault-count shared **25** (late, after OFF)
- runes funnel total **0** (watchdog then “resolved”)
- Live judges (after seal, delayed by vaultcount until v948.4 fix):

| Item | Journal tier | Applied | Notes |
|------|--------------|---------|--------|
| Chaotic Grand Charm | border | border-hold | OK |
| Dread Whorl | border | border-hold | OK |
| Spirit (truncated Monarch) | grail* | toss | partial name; server fullnames gate ≠ client |
| Hellfire Torch | grail* | **toss** | **fixed in v948.5** via ITEM_CODEX gate |
| (empty) | unreadable | — | no magic/rare parse |

\*Server `/kai_verdict` grail-gate upgraded tier after client already applied toss. Client gate now runs **before** apply.

---

## Open bugs / next work for Claude

### P0 — verify after control restart
1. Hard restart control (`tvd` / quit TV window + relaunch) so **v948.6** UI+engine load.  
2. Theatre on last session: REAL photo count ≈ FAST photo count ≈ film N; STORY fewer but not empty.  
3. Hover a unique (Torch-class) live: journal must show `applied=grail` not toss.  

### P1 — Item Checker / grail gate
- [ ] Server and client grail gates still diverge on **runeword bare names** (`Spirit`) — tighten server `_kai_fullnames` grail gate to unique/set only (mirror `_aicIsGrailName`).  
- [ ] Truncated rare names (Monarch → “Spirit”) should not waste vision / not grail-gate.  
- [ ] Optional: re-process ledger rows that were wrongly `toss` with known unique names (Torch).  

### P1 — Live judge robustness
- [ ] If vaultcount still races intake_local, log clearly; v948.4 already unblocks parallel fire.  
- [ ] Cap/queue: `TV_KAI_JUDGE_LIVE`, `TV_KAI_JUDGE_LIVE_MAX=24`, `TV_KAI_JUDGE_LIVE_GAP_S=18`.  
- [ ] Materials never-zero: if user opens materials tab, ensure sticky tab OCR + funnel fire (same as gems). **Do not invent materials visits.**  

### P2 — Chronicle
- [ ] Session labels in inbox: prefer human clock from `firstSeenTs` (done) + optional Theatre jump via `sessionId`+`frameId`.  
- [ ] Phase B analyzer AI for **border only** (subscription) — Konyo asked; safe rules first (already in).  
- [ ] Auto-accept only when `_aicIsGrailName` grounded — already required.  

### P2 — Theatre
- [ ] Confirm filmstrip + L/R + timeline all use `TH.beats` after filter; session film count from `TH.allBeats`.  
- [ ] Intake beats without resolvable `frame` — resolve reel hist when possible so gem/rune tallies show a still.  

### Do **not**
- Touch locked gem/rune/material **crop geometry** in `functions/api/intake.js` / tally prep without explicit ask.  
- Full Playwright on Mac for verify — use `tv/test_control.py`, `test_routes.py`, `test_agent.py`, `demo_console` only.  
- Burn `ANTHROPIC_API_KEY` for TV intake — subscription lane first (`TV_INTAKE_LOCAL=1`).  

---

## Key files map

| Path | Owns |
|------|------|
| `tv/tv_diablo.py` | Agent, sticky names, VERSION |
| `tv/control_app.py` | Control :17772, Stage-3, live judge, `/kai_verdict`, `/api/intake` proxy |
| `tv/control_ui.html` | Theatre modes, chronicle modal, session groups |
| `bible.html` | Item Checker, aicJudge/Apply, chronicle APIs, D2R_BUILD |
| `tv/intake_local.mjs` | Subscription Claude CLI shim |
| `tv/test_routes.py` | Live-judge pure gates (`TestLiveJudgeQueue`) |
| `tv/test_control.py` | Stamp parity agent=control=board |
| `tv/sessions.jsonl` | Journal (read-only for forensics; `ts==captureTs` law) |
| `tv/frames/hist/reel_s_*` | Film `f_*.jpg` + `kai_report.json` |

---

## How to run (Mac)

```bash
# Control + UI
tvd status          # :17772 control, :17771 agent
tvd                 # open control if down
# ON AIR from UI (or POST /api/on)

# Tests (no full Playwright)
cd /Users/konyo/d2r_bible_tests
python3 -m pytest tv/test_control.py tv/test_routes.py -q

# Restart after pulling this handoff code
# Quit TV window → tvd → hard refresh engine iframe
```

Ports: **control 17772**, **agent 17771**.  
Capture pin: **D2R.exe** only (see `AGENTS.md`).

---

## Suggested first commits (if Claude commits)

1. `v948.1–.5 Item Checker live route + chronicle session auto`  
2. `v948.6 Theatre REAL/FAST photo parity + STORY sparse film`  

Or one commit: `v948.6 — checker auto-route, chronicle session triage, theatre photo sync`.

---

## Konyo language (quick)

- “brains / layers” = live deep, verify, KAI, Stage-3 funnel/judge/vault, intake receipts  
- “never-zero” = empty tally re-fire  
- “subscription not API tokens” = `intake_local.mjs` / claude CLI  
- “leave a github for claude” = this handoff  

---

## One-line resume prompt for Claude

> Resume TV DIABLO at **v948.6** from `HANDOFF_TO_CLAUDE_v948.6_2026-07-21.md`. Uncommitted: bible + control_app + control_ui + tv_diablo + test_routes. Verify Theatre REAL≈FAST photo counts; fix server grail-gate vs bare runeword names; confirm live-judge applies grail for ITEM_CODEX uniques; materials only if tab visited. Tests: `pytest tv/test_control.py tv/test_routes.py -q`. Do not break locked gem/rune intake crops.

---

*End handoff · 2026-07-21 ~18:43 IDT*
