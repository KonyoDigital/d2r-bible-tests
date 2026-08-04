# WINDOWS CATCH-UP — v1489 / v1551 → v1634

Report only. Nothing on either Windows box was touched, and no migration ships with this note.
Run every command in **GIT BASH** (a bare `bash` opens an empty WSL on your machines — documented trap).

---

## 1. THE SHORT ANSWER: nothing to install

Verified at HEAD `7c8f652` (v1634):

- `tv/WINDOWS_SHIP.json` is coherent: `ver` = v1634 = `D2R_BUILD.id`; all six `requires[]` paths are tracked in `git ls-files`; declared ports match the code — `control_app.py:63-64` binds `TV_CONTROL_PORT` default **17772** and `TV_PORT` default **17771**, and `tv_diablo.py:55` binds **17771**. No drift.
- **No new runtime dependency** landed between v1489 and v1634 — no `npm install`, no `pip install`. The only config change is `playwright.config.ts` (`workers: 2`), which you override on Windows anyway.
- **No Mac-absolute path in the Windows runtime path.** `/Users/konyo` appears only in `tv/com.konyo.tvd-console.plist` (a macOS launchd file, never loaded on Windows), `tv/control_agent.log`, and two prose comments. Routines H/J/K/L all resolve the board as `path.resolve(__dirname, 'bible.html')` — repo-relative, portable, no hardcoded Mac path. Path contract intact.
- The ~39 added files are art (`art/tz_*.jpg`, `art/ui_*.png`) and ~20 new `tests/` specs plus `tests/_palette.ts` — all arrive with `git pull`, no manual step.

So for the software: **`git pull` is the whole upgrade.** Deploys stay Mac-only. Pull before you edit, push after.

---

## 2. THE ONE THING THAT WILL BREAK — v1489 BOX ONLY (read before you pull)

**v1499 changed the guest storage prefix.** Before v1499 every non-owner world used one shared `W·` (ladder `WL·`). Since v1499, `bible.html:3531-3532` computes it per install:

```js
window._D2R_PFX  = window._D2R_OWNER ? ''   : ('I·'  + String(window._D2R_INSTALL).slice(0,8) + '·');
window._D2R_LPFX = window._D2R_OWNER ? 'L·' : ('IL·' + String(window._D2R_INSTALL).slice(0,8) + '·');
```

I grepped every `W·` in `bible.html` at v1634: all nine remaining hits are **comments or protection guards** (the wipe at :3677 and the backup/restore at :18523/:18565 deliberately *skip* `W·` keys so they are never destroyed). **There is no `W·` → `I·` adoption or migration anywhere.**

**Predicted consequence, first time the v1489 box opens the board after pulling:** it mints a fresh `d2r_installId`, routes to `I·<newid8>·`, reads **empty**, and shows the unclaimed-guest banner. It will look like that machine lost its entire Windows chronicle and vault. **The data is not deleted** — it is still sitting in localStorage under `W·` / `WL·`, orphaned.

The only escape hatch in the code is `d2r_ownerClaim` (:3514) — setting it to `'*'` makes that browser resolve as OWNER and read **bare** keys. That is Konyo's Mac world, **not** the `W·` data, so claiming does *not* recover it either.

**This is your decision, not a bug to be patched behind your back.** Two options: (a) accept the reset on that machine and start its cousin world clean, or (b) ask for a one-time `W·` → `I·` adoption in a later version. Before deciding, look at the data yourself — open the same bible URL/tab you normally use on that machine (localStorage is per-origin, so it must be the same origin), press **F12**, and paste into the Console:

```js
Object.keys(localStorage).filter(k=>/^W(L)?·/.test(k)).map(k=>k+'  ('+(localStorage[k]||'').length+' chars)').sort().join('\n')
```

Non-empty output = your Windows chronicle survived and is recoverable. Empty output = that machine never had a `W·` world and there is nothing to lose.

**The v1551 box is post-v1499 and is NOT exposed** — it already writes `I·<id8>·` and pulls straight through.

---

## 3. COMMANDS — v1489 BOX (do §2 first)

```bash
cd ~/d2r_bible_tests && git status --short          # must be clean; commit with: git commit -F msg.txt
git pull --ff-only
grep -o "id:'v[0-9]\+'" bible.html | head -1        # expect: id:'v1634'
python tv/run_gates.py                              # expect: all gates PASS
```

Then open the board once and expect the unclaimed-guest banner (that is §2, not a failure).

## 4. COMMANDS — v1551 BOX

```bash
cd ~/d2r_bible_tests && git status --short
git pull --ff-only
grep -o "id:'v[0-9]\+'" bible.html | head -1        # expect: id:'v1634'
python tv/run_gates.py                              # expect: all gates PASS
```

## 5. IF YOU RUN TESTS ON WINDOWS

```bash
npx playwright test tests/<one_spec>.spec.ts --workers=3
```

Always `--workers=3` (never the repo default, never a bare `npx playwright test`).

## 6. GOTCHAS — do not improvise around these

- Commit messages: `git commit -F msg.txt`, never `-m` with unicode (native-exe piping corrupts tokens via BOM).
- Deleting a file from PowerShell: `[IO.File]::Delete('path')` — `Remove-Item` is sandbox-blocked.
- One machine edits `bible.html` at a time; check `bible.html.EDIT_LOCK` first.
- Pull first, push after. **Deploys are Mac-only** — never deploy from Windows.

## 7. DONE WHEN

`grep -o "id:'v[0-9]\+'" bible.html | head -1` prints **`id:'v1634'`** on both machines and `python tv/run_gates.py` reports all gates PASS.
