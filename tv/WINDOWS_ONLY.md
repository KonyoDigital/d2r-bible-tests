# TV DIABLO — Windows only

This PC uses the **Windows** product path (your Windows QA box or cousin).  
Same GitHub product as Mac — do **not** run Mac installers/launchers/capture **on this PC**.

## What "Windows" does and does NOT decide

**Windows decides how the app is INSTALLED, LAUNCHED and CAPTURED.** That is the whole of it,
and it is the table below.

**Windows does NOT decide whose DATA you see.** Since **v1499** the world is chosen by the
INSTALL plus a human click, never by the operating system:

- A fresh install — on Windows, on a Mac, anywhere — resolves **GUEST** and gets its own private
  world `I·<id8>·` (ladder `IL·<id8>·`). Chronicle, vault and forge all read **0/0**. That is
  correct, not a bug, and not something to "fix" by flipping a switch.
- It becomes the owner world only when a person clicks **`✋ This browser is mine`**. Nothing
  else grants it: not the platform string, not the hostname, not existing keys on disk.
- Claiming **moves nothing and deletes nothing** — it writes one key. The previous world's data
  stays on disk, so a wrong claim is reversible.
- The old `mac|windows` → `W·` model is **RETIRED**. If you are reading a doc that says the
  platform decides, or looking for a `W·` prefix, that doc predates v1499.

So: your cousin's console starting empty is the product working. Konyo running this on a Windows
PC and seeing all his data is *also* the product working — he clicked claim there.

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
