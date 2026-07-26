# Windows TV DIABLO launch report (this PC session)

**Date:** 2026-07-26  
**Machine:** Windows · USERPROFILE contains Hebrew + space (`עדי חוסיד`)  
**Ship on disk:** v1400 (tv_diablo.VERSION / bible D2R_BUILD.id / control doctor `ver`)  
**Repo:** https://github.com/KonyoDigital/d2r-bible-tests  
**Local clone:** `%USERPROFILE%\d2r_bible_tests`

---

## Symptom (user)

- Desktop **TV DIABLO** opens then immediately closes (flash / “browser window” gone).
- `http://127.0.0.1:17772/api/doctor` does not load / connection refused.
- Looks like the app is broken; often misread as a browser/WebView crash.

## Root cause (proven)

`tv/start_tvd_win.ps1` launched with:

```powershell
Start-Process -FilePath 'pythonw' -ArgumentList @($control, '--open') ...
# or: -ArgumentList @($control, '--open')
```

PowerShell’s `Start-Process -ArgumentList` **does not quote** array elements. Paths with spaces become multiple argv tokens.

**Exact error (reproduced):**

```text
python.exe: can't open file 'C:\\Users\\עדי': [Errno 2] No such file or directory
Exit code: 2
```

So Python never loads `control_app.py` → nothing listens on `:17772` → doctor fails → Desktop shortcut’s Hidden PowerShell exits with no useful UI.

**Not** primarily: missing Claude, missing Grok, WebView2 missing, or need for API keys.

## Fix applied (local)

File: `tv/start_tvd_win.ps1`

1. Pass a **single** `-ArgumentList` string with a **quoted** script path:
   - `"C:\Users\...\control_app.py" --open`
2. Detach child (`-PassThru`, no infinite `-Wait` on headless tail).
3. Probe `http://127.0.0.1:17772/api/doctor` for a few seconds.
4. On failure: MessageBox + write `tv/start_tvd_win.log`.

## Environment snapshot (this session)

| Item | Value |
|------|--------|
| Git | 2.55.0.windows.3 |
| Python | 3.12.10 (real, not Store stub) |
| pywebview | 6.2.1 |
| WebView2 | 150.0.4078.99 (doctor ok) |
| Claude Code | 2.1.220 · `~\.local\bin\claude.exe` (User PATH seeded) |
| Grok CLI | 0.2.112 · `~\.grok\auth.json` present |
| Claude login file | `~\.claude.json` present |
| Grok Eyes | leave **OFF** unless SuperGrok intentionally enabled |
| Desktop shortcut | yes · `powershell -File "...\start_tvd_win.ps1"` (quoted -File path OK) |

## Doctor (healthy example after control is up)

```json
{"ok": true, "platform": "windows", "ver": "v1400", ...}
```

Agent port `:17771` may be down when OFF AIR — **normal**.

## For the next agent (no shared memory)

1. Confirm path bug is fixed in `start_tvd_win.ps1` (search `v1401 — CRITICAL Windows path bug`).
2. If doctor dead: check `tv/start_tvd_win.log` then launch:

```powershell
$repo = "$HOME\d2r_bible_tests"
$c = Join-Path $repo 'tv\control_app.py'
Start-Process python -ArgumentList "`"$c`" --open" -WorkingDirectory $repo
# then:
irm http://127.0.0.1:17772/api/doctor
```

3. Never require Grok / API keys for basic console.
4. Whole-number versions only (v1400, v1401, …).
5. Do not force-restart mid ON AIR farm.

## Verification after fix (same PC, 2026-07-26 21:02)

```text
launch FileName=...\Python312\pythonw.exe Args="...\control_app.py" --open
started pid=1564
doctor OK: {"ok": true, "platform": "windows", "ver": "v1400", ...}
LISTENING 127.0.0.1:17772  pid 1564 pythonw
```

Runtime log: `tv/start_tvd_win.log` (local only; do not need to commit).

## GitHub

`gh` CLI was **not** installed on this PC at report time. This file is the durable handoff in the clone. Push/PR when credentials allow:

```text
git -C %USERPROFILE%\d2r_bible_tests add tv/start_tvd_win.ps1 tv/WINDOWS_LAUNCH_REPORT.md tv/PINGPONG_LOG.md
git commit -m "fix(win): quote control_app path in Desktop launcher (USERPROFILE spaces)"
git push
```

Optional issue title:  
`Windows: Desktop TV DIABLO flash-close when USERPROFILE has spaces (Start-Process ArgumentList)`
