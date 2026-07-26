# Windows lane — KONYO WORKFLOW board (live)

**Source of truth for process:** repo root `KONYO_WORKFLOW.md`  
**This file:** how the **Windows Grok** lane maps onto that workflow (no Mac mesh).

## Role split (do not blur)

| Role | Owns |
|------|------|
| **Windows Grok (this PC)** | Install, Desktop launch, doctor, ON AIR live probe, Windows-only ship files, Hebrew/Windows locale bugs |
| **Mac / Fable / product Grok** | Full suite army, Playwright RINSE, Cloudflare deploy, seven-round seal, product architecture |

Windows Grok may **ship emergency Windows fixes** to `main` with triple stamp + ledger + REG, then hand Mac the **back-pass** (Step 13 rounds 2–7).

## Mandatory before claiming a Windows version SEALED

From `KONYO_WORKFLOW.md` — no skipping:

1. TDD / suites green (agent py + control py + Playwright) — Mac CI or local if available  
2. UX pass on touched surfaces  
3. User-experience drive (RINSE pattern) + screenshots **looked at**  
4. SuperGrok pingpong back-pass  
5. Patch discipline (re-grep live file)  
6. **Syntax gates:** `ast.parse` py · **Parser::ParseFile** on every Windows `.ps1`  
7. Visual verification when UI touched  
8. **Triple stamp:** `WINDOWS_SHIP.ver` == `tv_diablo.VERSION` == control `"ver"` == `D2R_BUILD.id`  
9. Ledger: `PINGPONG_LOG` round + `BUGS.md` REG-NNN  
10. Commit + push; deploy only from Mac lane when required; **never cycle while user ON AIR farming**  
11. Army only when scale needs it; one owner per file  
12. Permanent RINSE / latency / soak where they exist  
13. **Seven-round rule** before SEAL (R1–R7 in PINGPONG)

## Current arc status (2026-07-26)

| Ver | State | Notes |
|-----|--------|--------|
| v1402 | **DRAFT shipped** | capture UTF-8 / agent stdio — needs Fable back-pass |
| v1403 | **DRAFT shipped** | RLock ON AIR deadlock — needs suite lock |
| v1404 | **DRAFT shipped** | Windows-only ship identity — **R1** (implement + local gates). Need R2–R7 |

**Not sealed.** Do not tell Konyo "done forever" until Step 13 completes.

## Windows-only commands (this PC)

```powershell
# Health
irm http://127.0.0.1:17772/api/doctor
# Expect: platform=windows, shipPlatform=windows, shipVer=ver match, ok=true

# Syntax gate (PowerShell 5.1)
# Parser::ParseFile on start_tvd_win.ps1, install-tvd.ps1, capture_win.ps1

# ON AIR probe (only if user not mid-farm)
# POST /api/on then status mode=live bridge=true
```

## Files Windows owns for ship identity

- `tv/WINDOWS_SHIP.json`
- `tv/WINDOWS_ONLY.md`
- `tv/WINDOWS_COUSIN_HANDOFF.md`
- `tv/install-tvd.ps1` / `tv/start_tvd_win.ps1` / `tv/capture_win.ps1`
- `tv/.windows_install.json` (local stamp only, gitignored)
