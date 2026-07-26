# Windows cousin / second Grok — handoff + install tips (v1404+)

**You are helping THIS Windows PC only.** Windows product path only.  
No Mac installers, no Mac launchers, no Mac capture. No shared “twin” mesh.  
Pull latest: `git -C $HOME\d2r_bible_tests pull` then re-read this file **and** `tv/WINDOWS_ONLY.md`.

## Install (one line — Windows only)

```powershell
irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
```

Whole versions only (**v1404**, v1405… — no decimals).  
Repo: `%USERPROFILE%\d2r_bible_tests` · Desktop shortcut: **TV DIABLO**.  
Ship file: `tv/WINDOWS_SHIP.json` must say `"platform":"windows"`.  
Local stamp after install: `tv/.windows_install.json`.

---

## Hard rules for the helping Grok

1. **One PowerShell command at a time.** Wait for paste-back. Do not dump 15 steps.
2. **No API keys.** Claude = subscription CLI login. Grok = SuperGrok `grok login` OIDC only.
3. **Grok Eyes optional.** Default OFF. Never block ON AIR on missing Grok.
4. **NEW PowerShell window** after every Git / Python / Claude / Grok install (PATH).
5. **Never** `winget … | Out-Null` while debugging — you need to see errors.
6. If installer looks stuck: **Ctrl+C**, install the stuck piece **visibly**, re-run IRM.

## Git push policy (multi-machine — READ)

Mac and Windows both track **one** `main`. Auto-pull on clean launch updates both.

**You MAY push** only when fixing a **proven Windows-only bug** that cannot stay local:
- Path spaces / Hebrew USERPROFILE / PS 5.1 encoding / capture_win / start_tvd_win.ps1
- Deadlocks that also hit Mac are OK if the fix is correct (e.g. RLock) — still keep change minimal

**Push rules:**
1. Whole version only: **v1404**, v1405… (no decimals).
2. Triple stamp in the **same commit**: `tv_diablo.VERSION` == control `"ver"` == `bible.html` D2R_BUILD.id.
3. Touch **only** what you need. Prefer `tv/start_tvd_win.ps1`, `tv/capture_win.ps1`, Windows-only branches in `control_app.py` / `tv_diablo.py`.
4. **Do not** rewrite Mac launchers, Theatre UI, or funnel logic unless the bug is proven cross-platform.
5. **Do not** force-push, rewrite history, or change remotes.
6. One logical fix per version. Log a short note in `tv/PINGPONG_LOG.md`.
7. After push, Mac owner may re-review; bad commits get reverted.

**Default when unsure:** fix locally on Windows, **do not push** — paste the patch into chat for Mac Grok.

---

## Stuck on “installing Git…”

Not always stuck — silent winget. If >5–10 min with no UAC:

```powershell
# Ctrl+C the IRM script first
winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
# close PowerShell, open NEW window
git --version
irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
```

Manual: https://git-scm.com/download/win

---

## Stuck on “installing Python 3.12…”

Same pattern:

```powershell
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
# NEW PowerShell
python --version
# If Windows Store stub / opens Store:
# Settings → Apps → Advanced app settings → App execution aliases → OFF python.exe + python3.exe
where.exe python
irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
```

---

## winget broken / hung

```powershell
winget --version
winget source reset --force
winget source update
```

No winget → install **App Installer** from Microsoft Store, reboot, retry.

---

## Claude missing after install

```powershell
irm https://claude.ai/install.ps1 | iex
# NEW PowerShell
claude --version
# then once: claude   (browser login)
```

Desktop shortcut can exist without Claude; ON AIR needs Claude (unless Grok Primary only — still prefer Claude for cousin).

---

## Grok CLI (optional)

```powershell
irm https://x.ai/cli/install.ps1 | iex
# NEW PowerShell
grok --version
grok login
# or later: TV DIABLO → ⚙ advanced → ⚡ Authorize (no-spam if already linked)
```

Leave **Grok Eyes OFF** if no SuperGrok.

---

## After repo exists — health check (paste all output)

```powershell
git --version
python --version
winget --version
Get-Command git, python, claude, grok -ErrorAction SilentlyContinue | Format-Table Name, Source
Test-Path $HOME\d2r_bible_tests
Test-Path $HOME\d2r_bible_tests\tv\start_tvd_win.ps1
git -C $HOME\d2r_bible_tests rev-parse --short HEAD
git -C $HOME\d2r_bible_tests log -1 --oneline
```

Pull latest if old:

```powershell
git -C $HOME\d2r_bible_tests pull --ff-only
```

---

## Start the app

```powershell
powershell -NoLogo -ExecutionPolicy Bypass -File $HOME\d2r_bible_tests\tv\start_tvd_win.ps1
```

Or double-click Desktop **TV DIABLO**.

Doctor (browser on that PC):

```text
http://127.0.0.1:17772/api/doctor
```

Want `"ok": true`. Read each `"severity":"block"` and follow its `fix` field.

Status: `http://127.0.0.1:17772/api/status` → `ver` should be whole number (v1400+).

---

## Common failure map

| Symptom | Fix |
|--------|-----|
| `git` not recognized | NEW shell after install; PATH; reinstall Git.Git |
| `python` opens Store | Disable app execution aliases |
| pywebview / blank window | WebView2 Runtime: `winget install -e --id Microsoft.EdgeWebView2Runtime` |
| Port in use / second window | Kill old TV DIABLO / python on 17772; one console only |
| Doctor claude_cli block | Install + login Claude |
| ON AIR fails | Doctor first; **D2R.exe in-game** (not only Battle.net); capture pin |
| `NO CAPTURE` / no pin | `git pull` → v1413+ · borderless windowed · `tv\frames\win_pin_debug.json` · RESTART |

### Window pin still wrong (v1413)

```powershell
cd $HOME\d2r_bible_tests
git pull
# fully quit TV DIABLO, reopen Desktop shortcut
# open D2R in-game (character select / world), prefer borderless windowed
# ON AIR → wait 5s → if still HOLD:
Get-Content $HOME\d2r_bible_tests\tv\frames\win_pin_debug.json
Get-Process D2R -ErrorAction SilentlyContinue | Format-Table Id,ProcessName,MainWindowTitle
```

Paste those two outputs back if pin still fails.
| IRM Byte[] / Invoke-Expression errors | Use Windows PowerShell 5.1+ or PowerShell 7; re-run official install line |

---

## What to ask the human for

Always: **full last error block**, not “still broken.”  
Prefer: screenshot of IRM window + paste of `Get-Command` table above.

## What NOT to do

- Don’t rewrite the whole installer from scratch  
- Don’t demand WSL for basic TV DIABLO  
- Don’t set Grok Primary without successful `grok login`  
- Don’t force-push or delete their repo  

---

## Pingpong note for Mac/dev Grok

If Windows Grok is looping: paste this file path + the human’s last 30 lines of PowerShell into the Mac session. Mac Grok owns product truth; Windows Grok owns local install execution.
