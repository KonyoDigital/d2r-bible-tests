# TV DIABLO — Windows only

This PC uses the **Windows** product path (your Windows QA box or cousin).  
Same GitHub product as Mac — do **not** run Mac installers/launchers/capture **on this PC**.

## Install (Windows)

```powershell
irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
```

| Item | Windows path |
|------|----------------|
| Installer | `tv/install-tvd.ps1` |
| Desktop launcher | `tv/start_tvd_win.ps1` |
| Capture | `tv/capture_win.ps1` (D2R pin / full screen) |
| Control | `tv/control_app.py` + WebView2 |
| Agent | `tv/tv_diablo.py --watch` |
| Ship identity | `tv/WINDOWS_SHIP.json` → `"platform":"windows"` |
| Local stamp | `tv/.windows_install.json` (this PC only) |

## Not used on Windows

- `tv/install-tvd.sh`
- `tv/start_tvd_mac.sh`
- macOS `screencapture` / Screen Recording TCC
- Any “run the Mac twin” instructions on this machine

## Version

Whole numbers only (`v1404`, `v1405`, …).  
Triple stamp must match on Windows:

1. `tv/WINDOWS_SHIP.json` → `ver`
2. `tv/tv_diablo.py` → `VERSION`
3. `tv/control_app.py` status `"ver"`
4. `bible.html` → `D2R_BUILD.id`

Doctor: `http://127.0.0.1:17772/api/doctor`  
Expect `"platform":"windows"`, `"shipPlatform":"windows"`, `"shipVer":"v…"` matching `"ver"`.

## Helping Grok on this PC

Read `tv/WINDOWS_COUSIN_HANDOFF.md` + this file.  
You are **Windows-only**. Mac session memory does not apply.
