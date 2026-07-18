# AGENTS.md — D2R Farming Bible / TV DIABLO (Konyo Mac)

Hardcoded operational truth. Do **not** invent alternate play or capture paths.

## Mac game launch (ONLY path)

1. Open **`~/Desktop/CrossOver_patched.app`** (the patched app — not a random DMG / App Translocation copy).
2. Bottle: **`Battle.net Desktop App`** at **`~/CXPBottles/Battle.net Desktop App/`**.
3. Click **Battle.net** tile inside CrossOver (not a broken “Diablo II Resurrected.app” Mac wrapper).
4. In Battle.net → **Diablo II Resurrected → Play**.
5. Game process on Mac: **`D2R.exe`** with title **`Diablo II: Resurrected`**.

**Never:**
- Launch Battle.net / D2R via raw `wine` CLI “for the user” unless they explicitly ask.
- Use native Mac Battle.net (does not work for this setup).
- Delete, move, or “fix” bottles under `~/CXPBottles/` while debugging TV DIABLO.
- Assume CrossOver Home or Battle.net lobby is the game window.

## TV DIABLO capture pin (Mac console / agent)

- **Pin target = `D2R.exe` game window only** (title contains Diablo / Resurrected).
- **Never pin:** CrossOver Home UI, Battle.net shell, Chrome bible tabs, Terminal, TV DIABLO control UI.
- Default `TV_CAPTURE=auto`: window pin when `D2R.exe` exists; full-screen only as fallback.
- Read-only doctrine: screenshots only — no game input, no memory, no injection.

## Agent discipline

- TV DIABLO code lives under `tv/` — version stamps must stay ONE truth: agent `VERSION` · control `ver` · UI footer · `bible.html` `D2R_BUILD`.
- If the user cannot open the game: diagnose CrossOver_patched + bottle + broken Mac launcher tiles — **do not** reinstall or wipe CXPBottles.
- **One AI reader (v845+ / v846 Tesla Drive):** settle freeze → dual-lane only. Scout secondary is **removed**. Film is high-FPS HD; ON AIR status is a tiny chip (never giant READING over the game). Do not re-add a freestyle second deep path unless Konyo asks.
