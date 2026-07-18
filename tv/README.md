# 📺 TV DIABLO — live game-screen scanner

Play Diablo II. TV DIABLO watches the screen and streams the tally into the
Farming Bible's ⚡ session → 📺 panel.

**Playstyle (v842 unit engine):** you farm *normally*. You do **not** need a
deliberate stop+hover ritual. Mid-play on-screen loot **text** is snagged by the
scout sense path; full freezes (stash/panels/optional pauses) still go through
settle. Same clock, one dual-lane — not separate random readers.

## The three rules (why this is clean)

1. **Read-only by construction.** You launch it yourself, in a separate
   terminal. It only takes screenshots of what is already on your screen —
   no game-process access, no memory reading, no input automation, no
   overlay, no injection. It is the manual stash-screenshot workflow, automated.
2. **Subscription, not API keys.** Vision runs through the Claude Code CLI
   (`claude -p`) — billed to *your* Claude plan. Nothing metered, nothing to
   rotate, nothing in the repo. The agent **strips `ANTHROPIC_API_KEY` /
   `ANTHROPIC_AUTH_TOKEN` from vision subprocesses** so a shell API key cannot
   steal auth from your login (v720 / live run #2).
3. **Frugal unit engine.** One poll clock · sense→decide→act. Scout samples
   mid-play text; settle catches context freezes; one Claude deep at a time.
   Cruise gap ~4s · priority/scout ~1.2s · soft session cap 240.

## Mac (Konyo) — one-click install (mirrors Windows)

```bash
curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash
```

That installs git/python/Claude Code if needed, clones the repo, puts `tvd` on
your PATH, and drops **TV DIABLO.app** on your Desktop (+ `~/Applications`).

**Double-click the app** → **real native window** via **pywebview** (not Chrome).
Buttons **ON · OFF · STOP · RESTART · SIM**. ON starts the **hidden** agent and
auto-connects the bible **📺 TV·D** board (`#tvd-on`).

Requires once: `python3 -m pip install --user pywebview` (installers do this).

**One-word launcher** (also installed at `~/.local/bin/tvd`):

```bash
tvd              # open HD control app (same as Desktop)
tvd bare         # agent in this terminal (debug)
tvd status       # control + bridge status
tvd restart      # restart agent
tvd stop         # stop agent (farewell read)
tvd sim          # simulation mode
tvd --test img   # one-shot vision check
```

Or the long form: `python3 tv/tv_diablo.py`

**Use a bare Terminal window** — not a shell inside a Claude Code session (nested
`claude -p` calls hang; your first live run proved it).

First run: macOS will ask for Screen Recording permission for your terminal —
grant it (System Settings → Privacy & Security → Screen Recording).

**Fullscreen D2R** works best (menu-bar clocks thrash settle). For max mid-play
hits: enable **show-items / ground loot name labels** — the engine reads *text on
screen*, never invents names from bare icons (read-only doctrine).

One-shot vision check (no bridge):

```bash
python3 tv/tv_diablo.py --test tests/golden/intake/chronicle_mid.jpg
```

## Windows (the cousin) — one-click install · **same control app as Mac**

```powershell
irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex
```

That installs Git/Python/Claude if needed, clones the repo, and drops
**TV DIABLO** on the Desktop (+ Start Menu).

**Double-click TV DIABLO** → **same native pywebview window as Mac** (Edge
WebView2 under the hood — not a Chrome tab). Buttons **ON · OFF · STOP · RESTART · SIM**.

| Button | Windows under the hood |
|--------|-------------------------|
| **ON** | Hidden `capture_win.ps1` (auto-pin D2R.exe + `eye.jpg` film) + `tv_diablo.py --watch` — **no second window** |
| **OFF / STOP / RESTART** | Same control APIs as Mac (farewell on STOP) |
| **SIM** | In-console theatre: last session, capture-ts locked to `hist/{frameId}.jpg` |
| **Bible rail / TV·D** | Same window → `/board?app=1#…` (⌂ CONSOLE returns) |

Capture default on Windows: **`TV_CAPTURE=auto`** (pin native D2R when present; full virtual screen as fallback). Set `TV_CAPTURE=full` to force desktop-wide.
| **OFF** | Soft stop capture + reader + board off |
| **STOP** | Full stop + farewell read |
| **RESTART** | Stop → ON |
| **SIM** | Stub reads (zero vision $) + board auto-on |

Manual two-terminal debug form (optional):

```powershell
powershell -ExecutionPolicy Bypass -File tv\capture_win.ps1   # terminal 1
python tv\tv_diablo.py --watch                                # terminal 2
```

## Then, in the bible

⚡ session → **📺 TV DIABLO** → flip the switch. OFF → CONNECTING (amber) →
LIVE (green) once the bridge answers on `http://127.0.0.1:17771`. New reads
appear in the feed; matched grail/set names offer one-tap ✓ apply (review-first
— the scanner never silently changes your Chronicle).

## Future

The public version is the same architecture productized: users subscribe to
the app and authenticate their *own* Claude — the Claude Agent SDK supports
exactly this bring-your-own-Claude model.

## Models (v725 — live-proven)
- **Fast default: Sonnet** (`TV_MODEL=sonnet`) — run #3: Haiku warm was **13–16s**, Sonnet was
  **6–10s**, so the default flipped. Opt into Haiku with `TV_MODEL=haiku` if you want to retest.
- **Genius escalate:** only when `TV_MODEL` ≠ `TV_MODEL_ESCALATE` (e.g. haiku→sonnet experiments).
  Cap: `TV_ESCALATE_CAP=40`. Still **subscription login**, never API-key burn.
- **No empty-gameplay cool (v726):** a 20s cool after empty combat pauses delayed real pile
  stops — removed. Thrash control = same-view skip + MIN_GAP **6s** only.
- **Loot lifecycle:** floor `loot` → intent `seen` (review-first chips).
  `inventory` / `stash` → intent `farmed` → auto-tick engines + `tvVaultRegister` into the
  vault shelf (same owned/mule path as AI intake, **no photo**).

## Session history (v724) — TV tab
- **SESSION HISTORY** panel under the signal feed: **LIVE** + **LAST SESSION** tabs.
- Survives agent restart / page reload (`d2r_tvdHist`, account-forked).
- Each read is time-stamped with HD art (`artUrl`), **HIT / DB / NO DB** cross-ref against
  rune/gem/unique/set engines + the ~1400 `ITEMS` table, intent (seen/farmed), model, ms,
  and 🏦 vault tags when farmed auto-filed.
- **Last frame** the AI saw: agent serves `GET /frame` (JPEG) into the eye preview when live.

## Last live verdict
- **2026-07-16 evening — GATE PASSED ✅**: boot → `vision warm in 3s` → real reads
  `[warm 6-10s]` — scene detection ✓ (inventory), five real item names from live game.
- **v723:** Haiku-first + Sonnet genius ladder · floor≠farmed · vault wire for farmed only.
  Restore point: `restore-point-pre-tv-speed-loot-lifecycle-2026-07-16_201534`.
