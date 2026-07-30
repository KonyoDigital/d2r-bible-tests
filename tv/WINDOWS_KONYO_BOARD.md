# Windows lane — KONYO WORKFLOW board (live)

## Current ship
| Item | Value |
|------|--------|
| Version | **v1461** |
| Suites | test_agent **201 OK** · test_control **267 OK** — Windows finally green |
| Launch | spawn no longer hides the app window · window presence verified, not assumed |
| Pull | skipped if already up · 12s cap · timed-out job really stops before spawn |

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
