# HANDOFF → Claude · v948.7 · DEBUGGER + SHIPMENT UPGRADE

**Date:** 2026-07-21  
**Repo:** `/Users/konyo/d2r_bible_tests`  
**Stamp:** agent = control = board = **v948.7**  
**Prior handoff:** `HANDOFF_TO_CLAUDE_v948.6_2026-07-21.md` (superseded for tally retro)

---

## Konyo’s correction (read this first)

> “We have the screenshots right? And 3 other KAI layer eyes and brains… why are these screenshots not being checked in retro and rechecked… if I can see the photo in Theatre it means it was recording… reimburse and reroute.”

**He is right.** Live deep miss ≠ permanent miss. Film on the reel is ground truth. Post-seal KAI + Stage-3 funnel must **re-label and re-tally** from those stills even when live never sticky-named the tab.

### What was broken (root cause)

| Layer | Failure |
|-------|---------|
| Live deep | Only names `stashTab` when that frame is deep-read. Materials never deeped → no journal sticky. |
| Journal sticky | 25s hold after personal/shared deeps cast a **vault “stash” vote** that **vetoed** tally grid votes (materials/gems) in the router. |
| `fuse_tab_signals` | Grid tally required journal/model/ocr — **blocked grid-solo** on pure film. |
| Stage-3 | Only fired funnel for conf≥2 `tally:*` rows. No “gap funnel” for eye-labeled tabs without receipt. |
| Result on 15:27 soak | gems/runes funnelled (deep sticky). **materials×0** forever despite 66 plain-stash conf≥2 film frames. |

---

## What v948.7 ships

### 1. Retro reel recheck (`tv/stash_eye.py` + `tv/control_app.py`)

- `fuse_tab_signals(..., allow_grid_solo=True)` for **KAI closer only** (live path stays strict).
- `analyze_frame(..., allow_grid_solo=True)` on every film still.
- Journal personal/shared → weak label `"stash"` only (panel open), **not** a veto against `stash-materials|gems|runes`.
- Router: skip weak journal vote when grid/tabstrip already says a tally tab.
- `_kai_retro_promote_tally(routing_scan)` — consecutive stash clusters majority-vote to materials/gems/runes.
- `_kai_stage3_gap_funnels(plan, sess_rows)` — if eyes labeled a tally tab and **no real receipt**, still queue one SET funnel from best frame.
- `kaiVer: 3` — reels with kai_report < 3 are **auto re-closed** by `_kai_closer_loop` (agent must be OFF).

### 2. Debugger API

```http
POST http://127.0.0.1:17772/api/kai_reclose
Content-Type: application/json

{"sessionId":"s_1784636825977_40909"}
# or {"n": 1}  // theatre session index
```

- Clears/renames `kai_report.json` → closer re-scans within ~30s.
- **Only when agent is OFF** (won’t race ON AIR).
- Response: `{ok, sessionId, kaiVerTarget:3}`.

### 3. Still in tree (v948.0–.6)

- Sticky NEW/echo deeps  
- Item Checker live + Stage-3 + aicJudgeApply (ITEM_CODEX grail gate for Torch)  
- Chronicle session groups + safe auto-triage  
- Theatre REAL/FAST same photos; STORY sparse film  

---

## Uncommitted files (DO NOT LOSE)

```
M  bible.html
M  tv/control_app.py
M  tv/control_ui.html
M  tv/stash_eye.py
M  tv/test_routes.py
M  tv/tv_diablo.py
?? HANDOFF_TO_CLAUDE_v948.6_2026-07-21.md
?? HANDOFF_TO_CLAUDE_v948.7_2026-07-21.md
```

```bash
cd /Users/konyo/d2r_bible_tests
python3 -m pytest tv/test_control.py tv/test_routes.py -q   # expect ≥138 pass
```

New tests:
- `TestLiveJudgeQueue` (v948.2)
- `test_grid_solo_materials_kai_retro`
- `test_retro_promote_and_gap_funnel`

---

## Debugger playbook (Claude — do this next)

### A. Force reclose the 15:27 reel (materials audit)

```bash
# 1) Ensure agent OFF
tvd status   # should show OFF on :17771

# 2) Restart control so v948.7 code is loaded
#    Quit TV DIABLO window → tvd

# 3) Reclose
curl -sS -X POST http://127.0.0.1:17772/api/kai_reclose \
  -H 'Content-Type: application/json' \
  -d '{"sessionId":"s_1784636825977_40909"}'

# 4) Wait ~2–5 min for KAI closer (agent OFF required)
# 5) Inspect
python3 - <<'PY'
import json
from collections import Counter
p='tv/frames/hist/reel_s_1784636825977_40909/kai_report.json'
k=json.load(open(p))
print('kaiVer', k.get('kaiVer'), 'eyeNote', k.get('eyeNote'))
print(Counter(r.get('label') for r in (k.get('routing') or [])))
PY
# 6) Journal intakes for materials
rg 'materials' tv/sessions.jsonl | rg '1784636825977' | tail
```

**Success criteria:**  
- `kaiVer >= 3`  
- routing shows `stash-materials` **if** grid/chrome actually sees materials layout on film  
- if film truly only has shared/gems/runes (no materials pixels), materials still 0 is **honest** — not a funnel bug  
- if materials pixels exist and still 0 → improve `classify_stash_grid` materials branch in `stash_eye.py`

### B. Theatre photo sync check

Open Theatre → last session:  
- REAL photo count ≈ FAST photo count ≈ 📹 film N  
- STORY fewer, sparse film near AI  

### C. Live Item Checker

Hover unique (Torch) → journal `applied=grail` not toss.

---

## Shipment checklist (before commit/push)

- [ ] `pytest tv/test_control.py tv/test_routes.py -q` green  
- [ ] Stamps all **v948.7** (`tv_diablo.VERSION`, control `ver`, `D2R_BUILD`)  
- [ ] `POST /api/kai_reclose` works with agent off  
- [ ] Reclose 15:27 reel; document materials result (found / honest-zero)  
- [ ] One commit message e.g.  
  `v948.7 — retro reel tally recheck (grid-solo, cluster promote, gap funnel) + kai_reclose`  
- [ ] Do **not** change locked gem/rune/material **crop fractions** in `functions/api/intake.js` without Konyo  
- [ ] Subscription intake only (`TV_INTAKE_LOCAL=1`)  

---

## Code map (this upgrade)

| Function / endpoint | File | Role |
|---------------------|------|------|
| `fuse_tab_signals(allow_grid_solo=)` | `tv/stash_eye.py` | Grid-solo for KAI retro |
| `analyze_frame(allow_grid_solo=)` | `tv/stash_eye.py` | KAI closer uses True |
| `_kai_retro_promote_tally` | `tv/control_app.py` | Cluster majority → stash-materials/gems/runes |
| `_kai_stage3_gap_funnels` | `tv/control_app.py` | Funnel unreceipted eye-labeled tabs |
| Stage-3 funnel loop merge gaps | `tv/control_app.py` | After `_kai_stage3_select` |
| `_kai_build_routing` journal veto skip | `tv/control_app.py` | Vault sticky vs tally eyes |
| `POST /api/kai_reclose` | `tv/control_app.py` | Debugger force re-scan |
| kaiVer 3 re-queue | `_kai_closer_loop` | Auto reclose old reports |

---

## Honest note on the 15:27 soak (offline sample)

Offline re-OCR of 8 plain-stash frames all fused to **shared** (gear grid), not materials. That can mean:

1. That session’s film never showed the Materials tab, **or**  
2. `classify_stash_grid` under-detects materials (dark+chroma band).

v948.7 still **must** recheck and funnel when eyes *do* see materials. If Theatre UI shows materials chrome to a human but classifier says shared → next fix is materials fingerprint / chrome OCR, not “user must open tab live.”

---

## One-line resume for Claude

> Read `HANDOFF_TO_CLAUDE_v948.7_2026-07-21.md`. Ship v948.7 uncommitted work: retro film recheck (grid-solo, cluster promote, gap funnel), `POST /api/kai_reclose`. Restart control, reclose `s_1784636825977_40909`, report materials routing + intake. Do not break locked intake crops. Tests: `pytest tv/test_control.py tv/test_routes.py -q`.

---

*End · v948.7 debugger + shipment upgrade · 2026-07-21*
