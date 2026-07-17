# D2R Bible — TRACKING (nothing is real until it is here)

> **This is the living project board.**  
> 700+ versions stay coherent only if every agent (Grok · Claude Code · Desktop · Konyo)
> treats this file + git + tests as the source of truth.  
> **If it is not in TRACKING / BUILD_LOG / BUGS / git history — it does not exist.**

---

## The ship gate (every version, no exceptions)

A version is **not shipped** until **all** of these are true:

| # | Gate | Where |
|---|------|--------|
| 1 | **TDD first** — failing/green tests for the change | `tests/**` and/or `tv/test_agent.py` |
| 2 | **Suites green** — at least the touched surface suite | agent · board · or full Playwright |
| 3 | **Version id** stamped (commit subject `vNNN — …`) | git |
| 4 | **BUILD_LOG** entry (what / why / tests / non-goals) | `BUILD_LOG.md` (top, after invariants) |
| 5 | **BUGS** note if it fixed a live miss or regression | `BUGS.md` (`REG-NNN` or `TV-NOTE-NNN`) |
| 6 | **Surface ledger** if TV work | `tv/PINGPONG_LOG.md` |
| 7 | **Commit** on `main` | `git commit` |
| 8 | **Push to GitHub** | `git push origin main` (pre-push smoke may run) |
| 9 | **Deploy** only if `bible.html` / art / functions changed and Konyo wants live | `hooks/pre-push` auto-deploy or manual |

**Restore points** before risky waves:

```bash
git tag -a restore-point-<reason>-$(date +%Y-%m-%d_%H%M%S) -m "why"
# optional hardcopy: backups/RESTORE_…  (local; do NOT commit multi‑MB archives)
```

---

## Where truth lives (do not invent a second system)

| Artifact | Role |
|----------|------|
| **git / GitHub** | Code + history. Remote = shared brain. Local-only commits can vanish. |
| **TRACKING.md** | This file — open backlog + active stream + ship gate. |
| **BUILD_LOG.md** | Shipped decisions (append forever). |
| **BUGS.md** | Regressions + live notes (`REG-` / `TV-NOTE-`). |
| **tv/PINGPONG_LOG.md** | TV-KAI round ledger. |
| **tv/PLAN_*.md** | Forward plans (not done until ship gate). |
| **CI** | `.github/workflows/tv-tests.yml` on `tv/**` · Routine G/H/I/… for bible. |
| **D2R_BUILD** in `bible.html` | Runtime identity badge (keep honest when bible ships). |

There is **no** separate GitHub Project board yet. Until one exists, **this file is the project**.

---

## Active stream — TV-KAI (Grok owns `tv/**` + TV receiver slice)

**Restore freeze:** `restore-point-pre-tv-speed-loot-lifecycle-2026-07-16_201534` @ v722  
**Shipped (commit `6d0f8b3` when pushed):** v723 Haiku+genius · farmed vault wire · v724 session history  

### Open backlog (ordered)

| ID | Status | Item | Notes |
|----|--------|------|--------|
| TV-B1 | **done** | Haiku default + Sonnet escalate | v723 |
| TV-B2 | **done** | Floor=seen / inv-stash=farmed | v723 |
| TV-B3 | **done** | Thin `tvVaultRegister` vault door | v723 — no photo intake rewrite |
| TV-B4 | **done** | Session history LIVE/LAST + DB badges + `/frame` | v724 |
| TV-B5 | **done** | **Run #3 live proof** | area/scene/pile/Sonnet/floor-review all ✅ |
| TV-B6 | **done** | Autopilot L2 interest + priority gap | v727 |
| TV-B13 | **done** | LOOT LIFECYCLE v2 object permanence | v729 |
| TV-B14 | **done** | Post-run fix: soft first-inv farm + junk filter + short prompt | v730 |
| TV-B15 | **done** | Commitment vault: hold ≥30s / stash commit; throw-out cancel | v731 — no vault on inv glimpse |
| TV-B16 | **done** | SPEED v2 OCR fast lane (~10–50ms warm) + 250ms board poll | v732 — Claude deep remains |
| TV-B17 | **done** | Stash-tab auto-intake (runes/gems/materials → locked tally) | v734 — once/visit; OCR never |
| TV-B18 | **done** | Per-read frame history + fullscreen lightbox (~1920) | v735 — eyes on AI |
| TV-B19 | **done** | Chain vault: stash only SEEN/HOLDING; ban Unidentified | v738 — run #4 Crossbow+Jewel |
| TV-B20 | **done** | Farewell read on Ctrl-C / tvd stop (end-stash race) | v740 — run #7 miss |
| TV-B7 | open | History: click chip → openDrop / vault card | UX polish |
| TV-B8 | open | Multi-frame confirm (low-interest only) | |
| TV-B9 | open | Shadow metrics (pile-to-chip p50) | |
| TV-B10 | open | Board Autopilot HUD polish | partial v727 |
| TV-B11 | open | **Run #5** live proof: ⚡ocr flash + hold→vault · stash · throw-out | after v732 ship |
| TV-B12 | later | Public product path | Out of scope until Konyo says go |

### Rules for TV work
- **In scope:** `tv/**`, TV receiver in `bible.html`, `tests/v712_tv_board.spec.ts`, ledgers above.  
- **Out of scope unless asked:** forge engines, vault photo intake, chronicles rewrite, settle loosening.  
- **Auth:** subscription only — never burn API keys for vision.  
- **Launch:** one-word `tvd` (`~/.local/bin/tvd`) — strips API keys, same as bare `python3 tv/tv_diablo.py`.

---

## How any agent starts a session

1. `git status` + `git log -3 --oneline` + `git status -sb` vs `origin/main`  
2. Read **this file** (active backlog)  
3. Read latest `BUILD_LOG` entry + relevant `BUGS` / `tv/PINGPONG_LOG`  
4. Work only the next open backlog ID  
5. Ship gate above before saying “done”  
6. **Push** so GitHub has it — unpushed commits are not shared memory  

---

## Version naming

- Bible / TV product stamps: `vNNN` or `vNNN.M` in commit subject  
- Nightly TV pingpong: also log round in `tv/PINGPONG_LOG.md`  
- Never reuse a version number for a different change  

---

*Last updated: 2026-07-16 — Grok (TV-KAI tracking contract established).*
