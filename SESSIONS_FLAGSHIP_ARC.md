# 📼 SESSIONS TAB — FLAGSHIP ARC (Konyo 2026-07-22: "the main tab technically, 30+ rounds konyoworkflow style")

The Sessions tab is the console's MAIN tab → deepest, most premium treatment. 30+ gated rounds, Konyo-workflow.
Grounded in a full audit (region map + backend-data gaps). Almost all control_ui.html (UI-owner lane);
[+app] items need control_app.py (team-lead lane) to expose data first.

## THE BIG UNTAPPED ASSET
`kai_report.register[]` per reel = the ACTUAL items KAI witnessed that session — {name, firstSeenTs, frameId,
loc, tier}. There is NO "what did I find" view anywhere today. This is the flagship spine. Each item's frameId
= jump-to-the-frame-where-it-appeared. Also untapped: routing[] (per-frame AI decision trail), completeness
(coveragePct/gaps), super (recovery rate), classFrames (montage), missed[].texts, cross-session aggregates.

## IRONCLAD (every round)
- LIGHT — ride the existing /api/sessions poll (already fetched each cycle by hdShelf), lazy-load thumbs, no
  heavy per-frame main-thread work. It's a live gaming HUD.
- TRUTHFUL — register/routing/coveragePct/super only exist on Phase-C+ SEALED reels (kaiVer>=3). Provisional/
  live sessions show "sealing…"/honest gap, NEVER fabricated stats. `registered` null on old reels → render "—"
  not "0 found". Unarchived frames (frameMissing/archiveOk) degrade gracefully (onerror). LIVE GUESS stays labeled.
- DON'T TOUCH (proven, Konyo-hardened): Theatre transport/close discipline (thEscUnwind, ⋯ drawer, click-outside),
  REAL/FAST/STORY semantics + entry-pins-REAL, stub/ghost blindness, thumb-count truth, PAST-not-live ribbon.
- Cadence: polish-ui-2 owns control_ui.html; team-lead does [+app] backend; Fable gates each round; version-per-
  round; floor green (503) + demo 7/7 @0.00px; detached push; console serves UI fresh (⌘⇧R, no restart).

## ARC ORDER (audit-ranked; first 5 = the flagship spine)
- **R1 — WHAT I FOUND** [+app]: expose register[] in /api/sessions → render items as premium cards (HD art via
  _artRarity, loc/tier, 🏆 grail) on shelf cards + last-session digest; cover-art = the best find's frame; click →
  jump to firstSeenTs. THE answer to "what did I find." (audit #1+#12+#23)
- **R2 — SESSION DETAIL view** (#2+#5): shelf card → full dossier destination (hero, headline stats, items,
  coverage, verdict, fingerprint, "open in Theatre"); LAST SESSION digest → flagship card.
- **R3 — HISTORY as a board region + empty/first-run states** (#3+#27): shelf stops being a Theatre-trapped
  overlay → the off-air home of the Sessions tab; beautiful first-run hero.
- **R4 — FARMING-PRODUCTIVITY KPI bar** [+app or client] (#4+#18): sessions today, reads/hr, frames/session,
  named/session, keepers, tallies banked, grails, trend sparkline. Maxroll-grade.
- **R5 — the AI decision STORY** [+app] (#6+#7+#8): routing[] narrative ("saw 82 → 49 stash → routed 10 vault…")
  + classFrames montage + coverage meter. Watch the AI think, beautiful + honest.
- **R6-33 layer depth/nav/polish:** super-recovery badge · missed-text drill · seal-latency chip · regret
  spotlight · search/filter/sort · day-grouping · session comparison · area heatmap · best-run/streak · shelf card
  redesign · beat-card chips · animated count-ups · verdict seal stamp · filmstrip chapter markers · live-session
  preview card · session notes/naming · pin/favorite · recap export polish · grail-progress-this-session · since-
  last-session deltas.

## KEY COORDINATES
UI: thShelf (control_ui.html:4615) · hdLastSession (5884) + hdShelf (5906) · thLoadSession (4064) / thOpen (4142) ·
thDossierLine (3084). Backend: _theatre_sessions (control_app.py:5865) · reel join/register/routing (4221/4604/6148)
· per-reel truth tv/frames/hist/reel_<sid>/kai_report.json.

_One ping to Konyo at milestones (each ~5-round tier), not every round._ 📼🏆🥷
