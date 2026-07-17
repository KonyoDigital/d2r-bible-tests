# 🏓 HANDOFF CLOSED · v779 The Honest Eye · 2026-07-18

**Status: SOLVED → SHIPPED through v783.** Grok closed the pin mystery (v779), then one-window (v781), async vision (v782), snappy film (v783). See PINGPONG v779–v783.

## Root cause (two stacked bugs)

1. **THE STALE-FILE LIE** — `capture_mac` wrote with `screencapture -l <wid> … path` then trusted
   `os.path.exists(path) && size > 10KB`. When screencapture failed (rc=1, wrote nothing), a
   *previous* desktop BMP still sat at `frames/live.bmp` → agent claimed `🎯 eye pinned` while the
   film was wallpaper. Fixed: always capture to a unique temp path, `os.replace` only on real bytes.

2. **Screen Recording TCC for Python-as-responsible** — Terminal's Screen Recording grant does
   *not* cover the control→agent child. Agent under an orphaned control (ppid 1) got rc=1/size=0.
   Fixed: `CGPreflightScreenCaptureAccess` / `CGRequestScreenCaptureAccess` at boot, Settings
   deep-link on failure, and Mac agent spawn no longer uses `start_new_session` (setsid broke the
   TCC chain).

## Also shipped

- `/frame` prefers live `eye.jpg` preview over stale `read.jpg` (film tracks the pin during skip)
- Version truth: agent · control · UI · `D2R_BUILD` all **v779**
- BrokenPipe hardening on `/ping` and `/frame` writes
- 3 new unit locks on the promote gate · full agent+control suites **83/83 OK**

## Live proof (Konyo's machine, mid-session)

```
cap  {'mode':'window','label':'D2R.exe · Diablo II: Resurrected','wid':12799}
boot Screen Recording OK — eye can pin the D2R window
cap  🎯 eye pinned to D2R.exe · Diablo II: Resurrected
read · gameplay — no readable item text (honest empty) [warm sonnet ⚡ 7.8s]
```
Film = pure Rogue Encampment (not desktop).

## If film goes dark again

System Settings → Privacy & Security → Screen Recording → enable **Python** (Command Line Tools
Python.app). Then RESTART in the app. The brain log will say `Screen Recording DENIED` and open
Settings automatically when preflight fails.
