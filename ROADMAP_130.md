# 🌙🗺️ TV DIABLO — 130-ROUND NIGHTLY ROADMAP (v1291 → ~v1420) — Konyo 2026-07-23

**Konyo's standing order (2026-07-23 night):** "show me the task rounds list for the next 130 rounds and check them off as we go — nightly project work autonomously, questions save for morning." → I run this chain autonomously overnight, ✅ each round as it gates, and **batch any decision/question in `MORNING_QUESTIONS.md`** (never block waiting; continue + backtrack).

Rules: integer version per round · ×3 stamp parity (tv_diablo VERSION == control_app "ver" == bible D2R_BUILD.id) · bible.html serializes (one writer) · UI (control_ui.html) + engine parallelize · selective commits (one lane's files) · detached pushes · verify before gate (JS/brace + real-data test; never the full Playwright suite on the Mac). North star: **v2000 = Level 2 rebrand.**

## ✅ DONE — the run that got us here (v1270–v1290)
- [x] v1270–1272 · G2 Task-Force rotation brain · D3 history · GHOST retired
- [x] v1273 · LIVE FIX set-mission "item not found" → F·Sets Quick-wins
- [x] v1274–1286 · Sessions flagship arc (KPIs · decision-story · recovery · seal/regret · search/filter/sort/group/timeline)
- [x] v1281 · 🔍 Vault Integrity Checker (routing/dedup/grail-safety)
- [x] v1287 · E1 vault stats (AI Checker verdict on muled items)
- [x] v1288–1290 · Sessions flagship VISUAL pass (type system · matched-height symmetry · off-air hero overlap fix)

---

## PHASE A · G3 UNIFIED AUTO-ROUTE / TALLY (finish the sunder-tally arc) — v1291–1298
Architecture (Konyo 2026-07-23): **chronicle/tracked items → full AI auto-pipeline (judge→route→verify→tally); everything else → AI Item Checker → vault mule/throw.** Sweep already built read-only + reviewed.
- [x] v1291 · G3 server `/api/autoroute-sweep` endpoint (read-only, intake-inclusive, MAX-snapshot) **+ the bible apply UI (merge-max diff + Apply + provenance "🤖 KAI filled" + honest "review manually" bucket)** — delivered TOGETHER; endpoint JSON-verified on real data, merge-max 13/13 in node, live-vocab recovers the undercount uniques. **Folds in what I'd planned as 1292 (apply UI) + 1294 (provenance).**
- [x] v1292 · G3 THREE-OUTCOME routing — chronicle→auto-tally · non-chronicle (RotW bases/white/rolled)→"🔬 Item Checker & vault" section + open-checker button · genuinely-unreadable→tiny "unclear" (0 on real data). 23/23 node tests; real-data buckets itemChecker 36 / ignored 18 / unclear 0. Clean G4 seam left.
- [ ] v1293 · G3 live-routing forward — chronicle items auto-route into trackers as scanned (same brain, going forward)
- [ ] v1294 · (folded into v1291 — provenance done)
- [ ] v1295 · G3 sunder(4/6)+statue(5/5) seed verified on Konyo's real apply (happens when he clicks Apply); de-dup/held-count truth
- [x] v1296 · (folded — non-chronicle→checker list in v1291) **+ v1294 the live HAND-OFF: per-item "🔬 send to checker" + bulk send-all queue + load-next; seeds the aic draft (rolled→name/base→base). 12/12 tests, regression 23/23. Konyo's chronicle/else model now COMPLETE end-to-end.**
- [ ] v1297 · G3 auto-route audit/verify pass (no false tallies; honest "unclear"; RotW-base labels)
- [ ] v1298 · G3 cohesion + verify — one unified smart routing brain, end to end

## PHASE B · G4 GROK — CHEAP, REMOVABLE ACCURACY TOUCHPOINTS — v1299–1306
Konyo (2026-07-23): "GROK is one of the addons to a set of places for accuracy.. i want its fingers in a couple of places that are cheap and efficient" + "implement it to be taken out eventually." → NOT one big watchdog: a few surgical, low-cost Grok verify hooks at accuracy-critical points, behind ONE ON/OFF toggle (OFF default, cousin-safe, own xAI key), built as a **self-contained removable module with a clean seam** (lifts out with zero scars).
- [x] v1299 · G4 module scaffold **(landed as v1295)** — self-contained `tv/g4_grok.py`, ON/OFF (switch AND key), OFF-default, cousin-safe, one-grep removal seam. 3 cheap seams chosen (uncertain auto-route · borderline keep/toss · grail promotion). OFF-path proven byte-identical (zero network). No touchpoint wired yet.
- [x] v1300 · G4 touchpoint #1 **(landed v1297)** — uncertain chronicle auto-route: seal-time, tier==border only, capped 10/seal, flag-never-override (flag rides into kai_report for the review surface). OFF byte-identical.
- [x] (v1298) · G4 TOGGLE — 🟣 Grok Accuracy card in Tools (honest 3-state OFF/needs-key/active, POWER-USER opt-in), reads g4_status/posts g4_toggle. 5/5 paint tests.
- [x] v1301 · G4 touchpoint #2 **(landed v1299)** — borderline keep/toss: fires only near-cutoff (keep 14–16, toss 5–6), flag-never-override into the journal. 12/12 band test. OFF byte-identical.
- [x] v1302 · G4 touchpoint #3 **(landed v1300)** — grail-promotion re-check (split-brain class, highest value): fires only on toss/border→grail promotion, flag-never-override. All 3 seams complete; flag map = register(kai_report) + journal(sessions.jsonl). OFF byte-identical.
- [x] v1303 · G4 "🟣 Grok caught this" review surface **(landed v1302)** — GET /api/g4_flags + panel in the Grok card; reads g4.agree===false from register+journal; honest empty state (0 on real data). 6/6 tests.
- [x] v1304 · G4 credit-aware rate limit + selective config **(landed v1304)** — daily(300)+hourly(40) caps from one 24h ring, per-seam G4_GROK_SEAMS (run only e.g. grail-recheck), budget surfaced in the card, seam-gate no-network. + G4_GROK_REMOVAL.md doc.
- [x] v1305 · G4 REMOVAL TEST — **PASSED.** Anchored-fence stripper on scratch copies: `rm g4_grok.py` + delete every fenced block → py_compile holds, 16 bible scripts compile, 0 G4 traces (`grep GROK ADD-ON|g4_grok|_g4` empty), G3 sweep returns identical (sunders 4/6, runes 32, gems 33). Proves "lifts out clean." Doc `tv/G4_GROK_REMOVAL.md` (stripper + proof). Verification-only (no code change) → certification folds into the v1306 commit.
- [x] v1306 · G4 cohesion + honest labeling **(landed v1305)** — self-describing `kind` per seam flag; full-arc verify green (23/23 regression, removal test still clean). **✅ PHASE B / G4 COMPLETE end-to-end, provably removable.**

## PHASE C · SESSIONS FLAGSHIP DEPTH (remaining D-rounds) — v1307–1320
- [x] v1307 · D14 session comparison **(landed v1301)** — ⚖ Compare overlay, 8 metric rows w/ ▲/▼ deltas (farming higher-better mint/red + winner glow), scene-mix diff, honest "—", pure UI. [in flight: D16 area heatmap]
- [x] v1308 · D16 area heatmap **(landed v1303)** — ranked heat-bars by run frequency (opacity heat-scales), runs/%/reads/🏆 per area; honest — grails not zone-pinned (labeled + footnoted, no fabricated attribution). [in flight: D17 best-run/streak]
- [x] v1309 · D17 best-run / streak highlights **(landed v1306)** — 🏆 best run · ⚡ most reads · 📈 top hr · 📊 best coverage · 🔥 streak; honest omission, tap-to-dossier. [in flight: D18 shelf card redesign]
- [x] v1310 · D18 shelf card redesign **(landed v1309)** — film-reel-still: cover-art hero + broadcast lower-third (Cinzel title + verdict seal) + gold headline-grail + 4-cell stat grid + rarity accents. Machinery preserved, tap-to-dossier intact. [in flight: D19 beat-card chips]
- [x] v1311 · D19 beat-card chips **(landed v1311)** — "⚡ The beats" story ribbon on the dossier (🔥entered·⚔farmed·🏛town·📸tallied·🏆grails·💎keeps·🔬judged·💔regrets·🛡seal); honest, no fabricated timestamps, chips omit when absent. [in flight: D20 count-ups]
- [x] v1312 · D20 animated stat count-ups **(landed v1313)** — dossier numbers tick 0→value (easeOutCubic 520ms), truth-safe (final=exact), reduced-motion aware, poll-guarded. [in flight: D21 seal-stamp polish]
- [x] v1313 · D21 verdict seal-stamp polish **(landed v1315)** — embossed wax/broadcast stamp (92px, double-ring, 🛡/🚨/◌), press-down stamp-in (poll-guarded, reduced-motion CSS), unified with D18 card chip. [in flight: D22 chapter markers]
- [x] v1314 · D22 filmstrip chapter markers **(landed v1318)** — 🎞 jump-to-chapter ribbon (scene chapters collapse, click→jump) + truthful find-markers (badge only on exact frameId match); honest limit (real chapters, not fabricated timeline). [in flight: D24 live preview]
- [x] v1315 · D24 live-session preview card **(landed v1322)** — on-air "● REC · recording now" card atop the shelf (elapsed · reads · scene chip · phase · newest find), in-place paint, hidden off-air, honest. [in flight: D25 notes/naming]
- [x] v1316 · D25 session notes/naming **(landed v1323)** — inline name+note editor, stable-sessionId keyed, "SESSION N" eyebrow kept, overrides shelf card + feeds search, poll-guarded. [in flight: D26 pin/favorite]
- [x] 🔒 **VISUAL-LOCK invariant TEST (v1323→v1324)** — `visual_lock_invariant.py` asserts 0 raw weights + --fw tokens on BOTH surfaces (fails file:line). Caught 3 console stragglers (v1323) THEN the `font:` SHORTHAND blind spot (v1324: 2 more console + 13 bible that the font-weight:-only scan missed) — folded all, widened the test to catch both `font-weight:NNN` AND `font:NNN`, proven green + catches injection. `LOCKED_TYPE_SYSTEM.md`. **Whole-app WEIGHT type system FULLY LOCKED + drift-tested (both syntaxes).** The test found what two "100%" human passes missed — truth standard working. (ls/lh + pre-push wiring = Konyo's morning calls.)
- [ ] v1317 · D26 pin / favorite sessions
- [ ] v1318 · D27 recap export polish (+items +coverage)
- [ ] v1319 · D28 grail-progress-this-session (Chronicle tie-in)
- [ ] v1320 · D29 since-last-session deltas · D30 cover-art = best find · D31 Sessions cohesion pass

## PHASE D · DIABLO-LANGUAGE COMPLETION (B4–B10) — v1321–1327
- [ ] v1321 · B4 AREA/ZONE in Diablo terms (ENTERING banner / automap per frame)
- [ ] v1322 · B5 TOWN vs FARMING distinction (safe vs drops)
- [ ] v1323 · B6 scene keyword-chips polish (live)
- [ ] v1324 · B7 retro scene-sync polish (per-frame)
- [ ] v1325 · B8 session scene fingerprint ("62% farming · 3 portals · 2 town")
- [ ] v1326 · B9 item-read Diablo precision (exact rarity + name; "inspecting <item>")
- [ ] v1327 · B10 Diablo-language accuracy pass + edge states (honest "unclear")

## PHASE E · VAULT + E1 FOLLOW-UPS — v1328–1332
- [x] v1328 · E1b funnel-2× accuracy reconcile **(landed v1307)** — 2nd checker read reconciles: agree→"✓✓ 2× confirmed", verdict-differ→honest "⚖ unclear", stat-differ→disputed (never dropped). 7/7 tests. [in flight: E1c thrown-with-stats]
- [x] v1329 · E1c thrown-with-stats comparison **(landed v1308)** — aicToss logs tossed items w/ their read; "📊 Kept vs Tossed" side-by-side panel. 8/8 tests. **✅ E1 follow-ups COMPLETE (Konyo's full muled-vs-thrown vision).**
- [x] v1330 · Vault Integrity Checker deepening **(landed v1310)** — +2 classes (🔬 checker-toss-kept review-only, 🤖 g3-vault-conflict auto-fix) + provenance on every finding (✋manual/🤖G3/🔬checked). Cross-references G3+E1+Checker. 9/9 tests. [in flight: full-system cohesion/verify round]
- [ ] v1331 · Vault manager full pass (stats + mule + capacity + ladder)
- [x] v1332 · Vault cohesion + verify **(landed v1312)** — FULL-SYSTEM COHESION CERT: 89 assertions green (75 node + 14 py), 0 regressions across v1291→v1310, data contracts aligned, G4 removal still clean. BUGS.md cert note. [next g3: bible-side visual-lock typography]

## PHASE F · CONSOLE POLISH (F-group) — v1333–1340
- [ ] v1333 · F2 reads sparkline / session-vitals ribbon
- [ ] v1334 · F3 Agent Mind glow-up (per-thought icon + rarity + landing anim)
- [ ] v1335 · F5 intake hero card ("📸 RUNES +14")
- [ ] v1336 · F6 live INTEREST gauge (money-moment needle)
- [ ] v1337 · "now reading" in-flight frame thumbnail
- [ ] v1338 · driver dispatch mini-flow (seen→queued→fired)
- [ ] v1339 · engine-health inline drilldown
- [ ] v1340 · console polish cohesion + verify

## PHASE G · 🔒 THE VISUAL LOCK ARC (Konyo's standing order — 20 rounds) — v1341–1360
After the feature build, HALT feature depth and lock the visual side before going deeper toward v2000. Typography + structure + hardcode + lock, across the WHOLE app (console + bible + all tabs).
- [~] v1341–1345 · TYPOGRAPHY — finalize ONE type scale/hierarchy across every surface. **BROUGHT FORWARD (Konyo's flagship-look emphasis) — CONSOLE SIDE COMPLETE:** [x] v1293 console weights → --fw-* (0 residual) + dead override removed; [x] v1296 console letter-spacing + line-height → 7 --ls-* + 6 --lh-* roles (254 folds, annotated one-offs). Console type system fully single-sourced. [~] bible.html-side pass STARTED: [x] v1314 --fw token foundation + 5 flagship headers (bible had --fs but 0 weight tokens; 733 literals → folding in identity-safe batches toward 0 residual, like the console); [x] v1316 pass 2 (31→697); [x] v1317 pass 3 (189→508); [x] v1319 pass 4 (386, CSS-side COMPLETE, 611/733 tokenized, 122 residual); [x] v1320 pass 5 (98.8%); [x] v1321 pass 6 (WEIGHTS 100% LOCKED, 0 residual, matches console; caught the 47-missed-literal gap; !important folded-not-removed). **BIBLE WEIGHT SYSTEM LOCKED both surfaces.** [ ] v1322 the VISUAL-LOCK invariant test (0-raw-weight assertion + token-set check, freeze against drift) [in flight]. ls/lh normalization + !important removal → Konyo's design call (MORNING_QUESTIONS).
- [ ] v1346–1351 · STRUCTURE — lock the layout/IA of every screen (home · Sessions · Forge · F·Uniques · F·Sets · Tools/Vault); consistent regions/gutters/chrome family
- [ ] v1352–1357 · HARDCODE + LOCK — freeze design tokens (colors/type/spacing/rarity+scene palettes/chrome) into one locked source of truth; invariant tests so the system can't drift; document it
- [ ] v1358–1360 · the stable visual base sealed; feature work resumes on a frozen foundation

## PHASE H · HARDENING → v2000 RUNWAY — v1361–1420
- [ ] v1361 · full-suite CI green pass (Windows) — first full-green since the arc
- [ ] v1362 · accuracy RE-AUDIT swarm (verify fixes held on real data)
- [ ] v1363 · Grok-watchdog full historical audit (if G4 on) / retro RE-SEAL sweep (kaiVer truth)
- [ ] v1364 · honesty verification pass (every claim vs real data, no overclaim)
- [ ] v1365 · performance / anti-lag hardening (light under full game load)
- [ ] v1366 · mobile-readiness audit (app-console wrap path)
- [ ] v1367 · chronicle cohesion (ladder/non-ladder synced, verified end-to-end)
- [ ] v1368 · task-force intelligence deepening (multi-goal, EV-ranked, learns pace)
- [ ] v1369 · unified auto-sync deepening (every RotW item type covered)
- [ ] v1370 · Forge / Create-Now cross-check with the rotation engine
- [ ] v1371 · Sessions × Chronicle × Task-Force unification (one loop: scan → find → task)
- [ ] v1372 · the "one glance" home pass (everything needed in 5s)
- [ ] v1373 · reference-item + grail denominator truth audit
- [ ] v1374 · backup/share + cross-machine (Mac/Windows/ladder) integrity pass
- [ ] v1375 · docs + memory + handoff refresh (self-documenting)
- [ ] v1376 · accessibility + contrast + reduced-motion sweep
- [ ] v1377 · final bug-sweep swarm (adversarial, loop-until-dry)
- [ ] v1378 · pre-Level-2 cohesion — the whole app as one designed product
- [ ] v1379–1420 · deep polish + per-engine perfection + live-bug fixes + whatever Konyo flags → the v2000 Level-2 rebrand runway (41 rounds of buffer for his live requests, new ideas, and quality deepening; order flexes to his morning notes)

---
_Order flexes to Konyo's live bugs + new ideas (they slot in; everything after shifts). One ✅ per gated round. Questions → `MORNING_QUESTIONS.md`._
