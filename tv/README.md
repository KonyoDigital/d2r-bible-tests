# 📺 TV DIABLO — live game-screen scanner

Play Diablo II. TV DIABLO watches the screen, reads the items you stop to look
at, and streams the tally into the Farming Bible's ⚡ session → 📺 panel.

## The three rules (why this is clean)

1. **Read-only by construction.** You launch it yourself, in a separate
   terminal. It only takes screenshots of what is already on your screen —
   no game-process access, no memory reading, no input automation, no
   overlay, no injection. It is the manual stash-screenshot workflow, automated.
2. **Subscription, not API keys.** Vision runs through the Claude Code CLI
   (`claude -p`) — billed to *your* Claude plan. Nothing metered, nothing to
   rotate, nothing in the repo.
3. **Frugal by design.** A read fires only when the screen *settles* (you
   stopped moving = you're reading items). Hard caps: ≥20s between reads,
   120 reads/session.

## Mac (Konyo)

```bash
python3 tv/tv_diablo.py
```
First run: macOS will ask for Screen Recording permission for your terminal —
grant it (System Settings → Privacy & Security → Screen Recording).

**Fullscreen D2R** works best: the settle detector is a strict pixel md5, so a
visible menu-bar clock (or any ticking HUD) keeps every frame “different” and
reads never fire. Fullscreen game → stable frames when you stop on loot.

One-shot vision check (no bridge):

```bash
python3 tv/tv_diablo.py --test tests/golden/intake/chronicle_mid.jpg
```

## Windows (the cousin)

Prereqs once: install Python 3 + Claude Code, then `claude` login with **your
own** account (your subscription pays for your reads — nothing rides Konyo's).

```powershell
# terminal 1 — capture loop (zero installs, built-in .NET)
powershell -ExecutionPolicy Bypass -File tv\capture_win.ps1
# terminal 2 — reader + bridge
python tv\tv_diablo.py --watch
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
