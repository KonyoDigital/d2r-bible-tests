# 🏓 HANDOFF → GROK · The D2R Window-Pin Bug · 2026-07-18 ~01:25 IL

**Konyo's order:** "something is terribly wrong.. lets let grok handle this.. log it all on the github for him to take over from here."
This is the complete state of the live-capture debugging. Fable pauses here; Grok owns the next move.

---

## THE SYMPTOM (what Konyo sees)

Konyo runs D2R.exe (via CrossOver, macOS, often fullscreen on its own Space).
The TV DIABLO film / NOW ON AIR stage shows his **desktop** (Terminal, Finder icons, menu bar clock),
**not the game**. He is mid-test-run and waiting; the run must land as session 1 in both theatres.

## THE ARCHITECTURE (30-second map)

- Agent `tv/tv_diablo.py` — capture loop → OCR + Sonnet vision → `/state` + `/frame` on **:17771**.
- Control app `tv/control_app.py` — pywebview shell on **:17772**, spawns the agent with `_env_clean`.
- `/frame` serves `tv/frames/read.jpg` = the **last vision-read frame**, NOT the raw capture.
- Capture: `TV_CAPTURE=auto` → `find_d2r_window_mac()` (Quartz `CGWindowListCopyWindowInfo`,
  `kCGWindowListOptionAll` since v779-pre so cross-Space windows are listed) → on hit:
  `screencapture -l <wid> -o -x -t bmp <path>`; on miss/fail: full-screen `screencapture`.

## THE DEBUG TRAIL (chronological, all verified live tonight)

1. **Spaces bug (FIXED, commit 62a9a7d):** fullscreen D2R lives on its own Space;
   `kCGWindowListOptionOnScreenOnly` never listed it → picker always missed → full-screen desktop.
   Fix: `kCGWindowListOptionAll`.
2. **Manual proof the window IS capturable:** from a bare shell,
   `screencapture -l 12799 -o -x -t bmp /tmp/pin.bmp` → rc=0, 22.4MB BMP, **verified visually a
   perfect pure-game frame** (Rogue Encampment, HUD, orbs). So macOS CAN capture this window.
3. **Inside the agent, the SAME call fails:** instrumented `_PICK_WHY` / `_CAP_WHY`; diagnostic label read:
   `{'mode':'full','label':'full screen (window capture failed rc=1 size=22485258)','wid':12752}`
   → **screencapture exits rc=1 inside the agent process while still writing a 22MB file.**
   Response: gate relaxed to trust the file (exists + >10KB) and ignore the lying exit code.
4. **Picker scoring bug (FIXED, uncommitted → this commit):** the CrossOver LAUNCHER window
   out-scored the actual game. Window list at the time:
   ```
   12799 | owner='D2R.exe'  title='Diablo II: Resurrected' | 1470x956  | onscreen True   ← THE GAME
   12752 | owner='CrossOver' title='CrossOver'             | 1150x700  | onscreen False  ← picked!
   (+ ~14 ghost windows: 1470x33 menubar strips, 500x500 stubs, Battle.net chrome)
   ```
   Old math: CrossOver launcher got +50 title-hint +30 owner +40 crossover-bonus = beat the game's 114.
   Fix: game identity is absolute (+1000 diablo/d2r in title, +500 D2R.exe owner, crossover → +5
   tiebreak only, +40 onscreen). Offline probe now returns `(12799, 'D2R.exe · Diablo II: Resurrected')`.
5. **Last-good-window cache (uncommitted → this commit):** Quartz listing is flaky from the agent's
   context (found the window at 01:13, returned None minutes later, found again after reboot).
   `_LAST_GOOD_WIN` keeps the pin until a capture with that wid actually fails; brain log now
   narrates `🎯 eye pinned to <label>` on every target change.
6. **After the scoring fix + agent cycle:** `/state.captureTarget` =
   `{'mode':'window','label':'D2R.exe','wid':12799}` and the brain log shows
   `🎯 eye pinned to D2R.exe` — **the agent believes it is capturing the game window.**

## ⚠️ THE OPEN MYSTERY (this is Grok's case)

With the pin reported LIVE on wid 12799, `/frame` still returned a **full-desktop image whose
menu-bar clock reads 00:58** (fetched at 01:21; `frames/read.jpg` mtime 01:21, 382,223 bytes).
Two contradictions:

- A true `screencapture -l` output contains ONLY the window — no menu bar, no desktop.
  The served frame has both → **the bytes are not a window capture.**
- Agent events after reboot: `⏳ entering a new game · recognized instantly (learned frame)` then
  `skip — settled, but same view I already read` → the **fingerprint of the new "window" capture
  matches the old desktop view**, i.e. the capture pipeline is still producing desktop-ish frames
  even when the window path claims success.

### Prime suspect: macOS TCC / Screen Recording permission for the agent's spawn context

Known macOS behavior: a process **without** Screen Recording permission gets degraded capture
(desktop wallpaper / own windows; window lists lose titles). The chain here is
`TV DIABLO app (pywebview, LaunchServices) → control_app.py → subprocess agent` — the *responsible
process* for TCC may be different from the bare Terminal where the manual capture worked (rc=0,
pure game). The rc=1-but-file-written signature and desktop-content frames both smell like TCC
partial-denial for **window-specific** capture in that context.

**First move (cheap, could end the whole case):** System Settings → Privacy & Security →
Screen Recording → ensure **the app that hosts the agent** is enabled (Terminal is likely already
on; check **Python / TV DIABLO / the pywebview app bundle** — whatever appears after an ON cycle),
then fully quit + relaunch TV DIABLO and re-test. If the film turns into the game, the whole night
was one checkbox.

### Second suspect: read.jpg staleness masking success

`/frame` = last **vision read**, not live capture. If fingerprint-skip fires because the *first*
capture after boot was desktop (pre-pin) and subsequent *window* captures coincidentally
fingerprint-match (unlikely) or the skip gate compares against the learned-transition frame, the
film would freeze on desktop even while raw capture is fine. Verify by dumping the RAW capture:
run the capture function directly in the agent's env and eyeball the BMP:
```bash
cd /Users/konyo/d2r_bible_tests/tv && python3 - <<'PY'
import tv_diablo as tv
ok = tv.capture_mac('/tmp/raw_probe.bmp')
print(ok, tv._CAP_TARGET, tv._CAP_WHY)
PY
open /tmp/raw_probe.bmp   # ← is THIS the game or the desktop? This one answer splits the tree.
```
- Game → capture is fine; bug is in read/skip/publish path (fingerprint gate or read.jpg writer).
- Desktop → capture itself is degraded → TCC theory confirmed → fix is the permission checkbox
  (plus, in code, a self-check: if window-capture output dimensions ≈ full-screen dimensions,
  flag `⚠ capture degraded — grant Screen Recording` in the brain log instead of lying).

## STATE OF THE TREE (this commit)

- `tv/tv_diablo.py` — all of tonight's live-debug work: `_PICK_WHY`/`_CAP_WHY` diagnostics,
  reason-carrying labels, file-over-rc trust gate, absolute game-identity scoring,
  `_LAST_GOOD_WIN` cache, 🎯 pin narration. Agent suite: 68/68 OK. Syntax/import clean.
- Live processes left RUNNING (agent :17771 pinned to 12799, control :17772, game open).
- Konyo's test run is ON HOLD until the film shows Diablo.

## RULES FOR GROK (unchanged doctrines)

- Host never forks: ON/SIM/RESTART spawn NO new windows (REG-020).
- One truth path: `tvVaultRegister` / `tvChronicleRoute` only.
- Round-trip every boundary (the R3 parse sleeper class).
- Mac = smoke + targeted tests only; full suites on CI/Windows.
- bible.html EDIT_LOCK protocol before touching the board.

*— Fable, pausing on Konyo's order. The suites are green; the eye still lies. Over to the third eye.*
