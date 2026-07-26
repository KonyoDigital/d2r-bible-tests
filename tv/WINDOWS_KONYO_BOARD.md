# Windows lane — KONYO WORKFLOW board (live)

**Process:** repo `KONYO_WORKFLOW.md`  
**Laws:** Windows push policy · one `main` dual-PC · safe auto-pull

## Role split

| Role | Owns |
|------|------|
| Windows Grok | Install, launch, doctor, ON AIR, Win capture pin, seven-round+ seal |
| Mac / Fable | Playwright RINSE, CF deploy, product architecture |

## Current ship

| Item | Value |
|------|--------|
| Version | **v1419** |
| Capture | C# PrintWindow `TvdCap` + always `eye.jpg` |
| Pin UX | cap_target **no BOM** · agent refreshes pin on every `/state` |
| Proof | Rogue Encampment film while D2R in-game |

## 10-round seal (2026-07-27 Windows PC)

| R | Gate | Result |
|---|------|--------|
| R1 | Laws + HEAD vs origin | main matched; ship v1418→v1419 |
| R2 | Desktop shortcut exists | `TV DIABLO.lnk` → `start_tvd_win.ps1` |
| R3 | Capture pin | `D2R via PrintWindow` · eye age &lt;3s |
| R4 | Visual film | **Rogue Encampment** (Gulzar, cart, torch, lightning) |
| R5 | Control doctor | control :17772 up |
| R6 | ON AIR | mode=live · capture=LINKED · agent bridge |
| R7 | Live session | reads ≥1 · scene **town** (encampment) |
| R8 | Hist frames | `frames/hist/1_*.jpg` + `f_*.jpg` footage |
| R9 | OFF / seal path | `/api/off` · sessionId recorded |
| R10 | Theatre/retro cross-ref | hist frame == eye proof class (town/camp) |

## User path (UX)

1. Double-click Desktop **TV DIABLO** (one window).
2. Keep **D2R.exe in-game** open (borderless preferred).
3. Click **ON AIR** — expect pin label `D2R - Diablo II: Resurrected via PrintWindow`, **not** EYE HELD.
4. Eye preview = game, not chat/IDE.
5. **END SESSION** / OFF to seal reel for Theatre.

## Proof artifacts (this PC)

- `C:\Users\Public\tvd_debug\konyo_r1_eye.jpg` — Rogue Encampment
- `konyo_t2/t10/t16_eye.jpg` — mid-session film
- `konyo_final_eye.jpg` — end-of-session film
- `frames/hist/1_1785109064522.jpg` — vision deep frame (town read, session `s_1785109054425_37292`)

## Known residual

- If PrintWindow returns black and D2R not focused: click game window once.
- Doctor can lag under D2R load; extended wait is intentional (v1417+).
- Session reel folder `reel_s_*` seals after clean OFF; force-kill control skips closer.

## Do not

- Do not force-kill control mid-ON (breaks seal).
- Do not treat "eye arming…" as truth if `eyeAgeMs` is low and `cap_target.json` says PrintWindow (fixed v1419).
