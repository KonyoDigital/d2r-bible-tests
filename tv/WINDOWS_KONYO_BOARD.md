# Windows lane — KONYO WORKFLOW board (live)

> ⚠ **THE `W·` MODEL ON THIS BOARD WAS RETIRED AT v1499.** Everything below was written for the
> `mac|windows` × `main|ladder` 2×2, where the OS decided whose data you saw. It does not any
> more — see the Identity row. A helper diagnosing a Windows box against the old model will
> chase a `W·` namespace the shipping code no longer writes. Corrected 2026-08-15 at v1712.

## Current ship
| Item | Value |
|------|--------|
| Version | **v1712** |
| Suites | test_agent **201 OK** · test_control **267 OK** — in a PLAIN `python tv/test_*.py`, no env vars |
| Launch | spawn no longer hides the app window · window presence verified, not assumed |
| Icon | `appicon.ico` via pywebview 6 `start(icon=)` — **.ico only** (a .png silently kills the window) |
| Pull | skipped if already up · 12s cap · timed-out job really stops before spawn |
| Identity | **the INSTALL decides, never the OS** (v1499). Ownership is claimed by a HUMAN CLICK — the `✋ This browser is mine` banner — and by nothing else: not the platform string, not the hostname, not the presence of existing keys. Every unclaimed install gets its OWN world `I·<id8>·` (ladder `IL·<id8>·`), chronicle + forge 0/0. Resolution is synchronous, so there is no path where a slow console or a timeout yields the owner world |
| Sigil | every install mints `tv/.tvd_identity.json` (gitignored) → colour+rune+name+code chip. Shown in the CONSOLE header and on the BOARD beside the world pills, same id + same generator. This PC = **AMBER ANVIL · B210** |
| Geometry | ships 1120x660 logical + a MOVE-only on-screen nudge on `shown` — verified bottom edge meets the work area exactly |
| Sessions | each movement is a `<section class="zone">` owning its banner + cards · a zone with no visible body hides itself · KPI card labelled · a real `0` reads dim |

## Fixed in v1460 — the dead Desktop icon (REG-051)
`-WindowStyle Hidden` on the pythonw spawn (added v1444) set STARTUPINFO SW_HIDE, and WinForms
applied it to pywebview's host window: the window existed, correct title and size, but was
never shown. The same commit swapped the ready probe to `/api/status`, so the launcher stopped
noticing and logged `launch complete` over a window nobody could see.

## Open UX (v1444–v1460)
1. Double-click Desktop **TV DIABLO** once
2. Expect ONE **visible** window, fast (~3s)
3. If already open → focus only (no second spawn)
4. Launcher log now states the truth: `launch complete (window up)` vs
   `WARN control up but NO TV DIABLO window`
