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
- **One LOGICAL AI path · POOL of N warm Claude workers (v863, Konyo-ordered):** settle/queue/heartbeat → dual-lane, dispatched onto up to TV_POOL=8 concurrent readers with capture-order apply. The freestyle scout stays dead. Film is high-FPS HD; ON AIR status is a tiny chip (never giant READING over the game).

## Two agents at once (Claude + Grok) — the branch protocol

Added 2026-08-24, after a night where both worked the same tree. It cost real time, and the parts
that WORKED are worth keeping.

### What actually happened, so the rules have evidence
* **The good half.** Grok wrote v2052 (the ledger keeps its dates); Claude verified it against live
  data — `_gameStampToLedger` driven in node, `d2r_gameFound` agreeing with the surviving dates
  **32 of 32**. Separately, Grok's `fix: register the vault-seen path` caught a gap Claude had left,
  through the repo's own import-bound gate. **Neither found those alone.**
* **The bad half.** Both edited `tv/control_app.py`. One had to stop and wait; the other's test
  mocks (`lambda sample=0:`) broke the moment a kwarg was added. Separately a Playwright run left
  going on the Mac wrote **9.5 GB into `test-results/` in 95 minutes** and took the disk to 2.8 GB.

### The rules

**1. One branch per agent. `main` is for merges only.**
```
git switch -c claude/<topic>      # or  grok/<topic>
```
A push to a non-main branch **cannot publish**: `hooks/pre-push` only auto-deploys on
`refs/heads/main` touching `bible.html` / `art` / `functions`. So a branch is safe by construction,
and the full gate still runs on every push.

**2. Split by ROLE, not by file. Whoever did not write it, verifies it.**
That pairing is what found the defects above. "You take these files, I take those" does not, because
the interesting failures live at the seams between them.

**3. Never edit a file while the other's change to it is uncommitted.**
`git status` before touching anything. An uncommitted diff in a shared file is a held lock.

**4. A test mock must survive a signature change.** Use `**kw`. The v2041 mocks were brittle, not
the code that broke them.

**5. Browser suites do not run on his Mac.** They run on GitHub CI. `hooks/pre-push` runs Playwright
deliberately as a gate — never kill that — but do not start a bare `npx playwright test` here.

### Why this also fixes `/code-review ultra`
That review diffs the CURRENT BRANCH against the default branch. Work already merged into `main`
produces an empty diff and the honest answer *"no commits to review"* — which is exactly what he hit
on 2026-08-24 with five shipped versions sitting in `main`. **Work on a branch, review before the
merge, and the review has something to read.**

