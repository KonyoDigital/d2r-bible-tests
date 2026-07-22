# 🗒️ TV DIABLO — MASTER TASK LIST (Konyo 2026-07-22: "70-120 rounds for it all, lots of rounds + pingpong per item, nothing left out")

Cadence per item = build → **Grok third-eye pingpong consult** → refine (doctrines intact) → specs/verify → gate → deploy.
Konyo-workflow: polish-ui-2 owns control_ui.html; team-lead owns engine (control_app.py/tv_diablo.py/stash_eye.py) + gates;
version-per-round; floor green (511); ×3 stamp parity; detached push; console serves UI fresh (⌘⇧R). One ping at milestones.
STATUS KEY: ✅ done · 🔵 in flight · ⬜ queued.

## A. 🔬 AUDIT FIXES (from the 5-agent swarm — HIGHEST PRIORITY, accuracy)
- 🔵 **A1 · panel-open / is-D2R guard** — no stash/tally classification unless real stash chrome present (kills wallpaper→Gems false positives). [engine, FIX A in flight]
- 🔵 **A2 · phantom-ocr gate honesty** — stop double-counting one grid read as 2 witnesses; sanctioned grid-solo route w/ tighter threshold (folded into A1). [engine]
- ⬜ **A3 · kaiVer→4 re-seal** — old reels auto-resweep to pick up v1254-v1256 + guards; wallpaper reels QUARANTINED not re-sealed. [engine]
- ⬜ **A4 · grail tooltip name extraction** — Enigma / Harlequin Crest were legible but left unnamed (OCR garble). The flagship reads. [engine]
- ⬜ **A5 · UI sealed-wins guard** — _erOwnerVerdict key on frame-presence not owner-truthiness (live-leak-into-retro); route through canonical _kai_engine_frame_effective (currently test-only dead code). [UI]
- ⬜ **A6 · re-close persistence** — reels missing routing/register/engineFrames ledger; per-reel gatePass schema drift. [engine, mostly via A3]

## B. 🗣️🎮 DIABLO-LANGUAGE ACCURACY ARC (10 rounds; 3 shipped)
- ✅ B1 carry scene through (v1254) · ✅ B2 scene visible live+retro, one dictionary (v1255) · ✅ B3 detect gems tab (v1256)
- ⬜ **B4 · AREA/ZONE in Diablo terms** (ENTERING banner / automap per frame)
- ⬜ **B5 · TOWN vs FARMING** distinction (safe vs drops)
- ⬜ **B6 · SCENE keyword chips polish** (live, refine)
- ⬜ **B7 · RETRO scene sync polish** (per-frame, refine)
- ⬜ **B8 · SESSION scene fingerprint** ("this run: 62% farming · 3 portals · 2 town trips")
- ⬜ **B9 · item-read Diablo precision** (uniques/sets/runes/gems exact rarity+name; tooltip = "inspecting <item>") — overlaps A4
- ⬜ **B10 · accuracy pass + edge states** (verify vs real frames, honest "unclear")

## C. 🖥 CONSOLE VISUAL SMOKE-TEST FIXES (pipeline PASSES all 6 stages; these are the found bugs)
- ⬜ **C1 · P1 capture pill wrap** (real bug — "Locked · Diablo II" wraps at ≤1728 rail) [UI]
- ⬜ **C2 · P2 KAI eye status wrap** (clamp to 2 lines, trim tail) [UI]
- ⬜ **C3 · P3 forge chip count mismatch** (hdEngines fs.now.length vs FORGE QUESTS — verify same source) [UI/verify]
- ⬜ **C4 · P4 funnels tab ok/miss count** (verify vs real sessionHealth.tabs shape) [verify]

## D. 📼 SESSIONS FLAGSHIP ARC (the MAIN tab — 30+ rounds, audit-grounded, SESSIONS_FLAGSHIP_ARC.md)
- ⬜ **D1 · WHAT I FOUND** — register[] items as premium cards (Enigma/grail etc.) on shelf + digest; click→jump-to-frame [+app+UI]
- ⬜ **D2 · Session Detail view** — shelf card → full dossier destination; last-session flagship card [UI]
- ⬜ **D3 · History as a board region** + first-run/empty states [UI]
- ⬜ **D4 · Farming-productivity KPIs** (reads/hr, grails, finds, trend) [+app+UI]
- ⬜ **D5 · the AI decision STORY** (routing narrative + classFrames montage + coverage meter) [+app+UI]
- ⬜ **D6-33** — super-recovery badge · missed-text drill · seal-latency · regret spotlight · search/filter/sort · day-grouping · session compare · area heatmap · best-run/streak · card redesign · beat-card chips · count-ups · verdict seal · chapter markers · live-session preview · session notes/naming · pin/favorite · recap export · grail-progress-this-session · since-last deltas

## E. 🏦📊 VAULT MANAGER — attach AI-Item-Checker stats to muled items (website finishing, VAULT_STATS_TASK.md)
- ⬜ **E1** — checker read → attach stats to muled vault entry (funnel 2x for accuracy); muled-with-stats vs thrown [bible.html]

## F. ✨ CONSOLE POLISH BACKLOG (deferred)
- ⬜ **F1 · GHOST MODE tasteful fidelity** (deferred r13 — only if Konyo wants more "past" feel, kept calm)
- ⬜ **F2 · reads sparkline / session vitals ribbon** (audit #7/#10) · **F3 · Agent Mind glow-up** (#5) · **F4 · accuracy-gate "🛡 KAI caught N misreads" badge** (#6) · **F5 · intake hero card** (#9) · **F6 · live INTEREST gauge** (#8, [+app])

## PARKED (done, don't touch): GHOST MODE / Time Machine (v1246) · console home restructure (v1247-v1253) · Grok v1251 TCC fix
## NORTH STAR: v2000 = Level 2 rename/rebrand (perfection reachable before then). Currently ~v1257. ~70-120 rounds across A-F.

## 🆕 NEW D2R REQUESTS (Konyo 2026-07-22 eve) — bible.html serializes (one at a time)
- 🔵 **G1 · CHRONICLE-SYNC ladder↔non-ladder** [bible.html, agent in flight] — chronicles (grail foundLog, setPieces, made-runewords) SHARED across ladder+non-ladder (remove from _LP_FORKED); vault/mules stay FORKED; ladder-only runewords still render ladder-only; SAFE merge migration (union both accounts, never overwrite). rwVerify fail-verdicts may stay forked (decide).
- ⬜ **G2 · TASK FORCE AI ROTATION** [bible.html+control_ui.html] — the DAILY PICK (dailyCreateAi ~bible 20220-20301), OPS QUEUE, and MISSION BRIEF all dead-end on runewords 99/99. Build an AI priority-rotation engine: read every chronicle's completion → runewords done (easiest, hit) → DESCEND + intelligently rotate/prioritize to the next incomplete chronicle (grail 246/403, sets 108/135; closest-to-done / best-EV) → feed the daily pick ("hunt <grail> at <boss>"), fill the OPS QUEUE with grail/set ops (not "queue clear · enjoy the sun"), deepen the mission brief. Konyo: "AI read the chronicles needing to reach, from runewords first (easiest, hit) so descend and intelligently rotate." NOTE: "OP QUE" = the OPS QUEUE label.
- ⬜ **G3 · UNIFIED AI-SMART AUTO-ROUTE/TALLY (retro + live, all item types)** [engine + bible.html] — Konyo's big unifying vision. KAI already read his items across DOZENS of sessions but the trackers sit empty (e.g. SUNDER CHARMS tracker = 0 though sunders were read many times). Build ONE smart routing brain: every KAI read → SURGICALLY routed to its correct home, individually — sunders → sunder tracker, runes → rune stash, gems → gem stash, materials → materials, grail uniques → grail chronicle, sets → set pieces. TWO passes: (a) RETRO — sweep every recorded session's register/reads (already stored) and back-fill each tracker from what KAI saw; (b) LIVE — same, going forward. UNIFIED (not scattered per-feature logic) + TRUTHFUL (only real reads; honest counts; de-dup so the same charm read across N sessions counts once as "have IN", not N). The 6 sunders = Crack of the Heavens/Rotting Fissure/Bone Break/Flame Rift/Black Cleft/Cold Rupture. Konyo: "properly tallied and routed individually and surgically... other items/logic like this too needs to be smart and unified." Generalizes [[d2r_ai_smart_stash_sync]]. BIG round(s) — likely its own mini-arc.

## 🟣 G4 · GROK EYE — second AI reader in the console (Konyo 2026-07-22 eve, "authorize grok as a second AI reader with a different viewpoint, within the console, on the subscription")
- [engine: tv_diablo.py reader pool + control_app.py reconciler] Add GROK as a reader layer alongside LIVE/SECOND/KAI, calling the xAI Grok VISION API (XAI_API_KEY — Konyo has it via SuperGrok / Grok-MCP example.env). Its reads flow into _kai_reconcile as another independent source/vote. A 🟣 GROK EYE in THE READER NET.
- WHY IT MATTERS (ties to audit A2): a genuinely INDEPENDENT second model = a REAL second witness → the accuracy gate's "2 independent witnesses" becomes true (not one detector wearing two hats). Sonnet+Grok agree = real corroboration; disagree = KAI flags honestly. Different viewpoints catch each other's misses.
- LIGHT/SELECTIVE (don't burn credits): Grok reads UNCERTAIN frames + IMPORTANT ones (grails/keeps, or where Sonnet+OCR disagree), NOT every frame. A gap/verify third eye, not a live-every-frame reader.
- TRUTHFUL: label GROK reads honestly (own eye/owner); reconciler priority extended cleanly; honest disagreement surfacing. Config to enable/disable + a credit-aware rate limit.
- Meaty engine feature — its own mini-arc. Reuses the multi-reader reconciler already built (owner/verdict ladder). Konyo already uses Grok as a third-eye consult; this embeds it IN the live/retro pipeline.
