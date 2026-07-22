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
- [ ] v1299 · G4 module scaffold — self-contained bolt-on, ON/OFF toggle OFF-default, cousin-safe, own key, clean removal seam
- [ ] v1300 · G4 touchpoint #1 (cheap) — verify UNCERTAIN chronicle auto-routes only (not every item)
- [ ] v1301 · G4 touchpoint #2 (cheap) — verify BORDERLINE Item-Checker keep/toss calls
- [ ] v1302 · G4 touchpoint #3 (cheap) — re-check an important grail claim / uncertain sealed find
- [ ] v1303 · G4 "🟣 Grok verdict" surface + disagreement flag → review queue
- [ ] v1304 · G4 credit-aware rate limit + selective config (only uncertain/important; never bulk)
- [ ] v1305 · G4 REMOVAL TEST — prove the whole module lifts out clean (toggle off = identical to today) + docs
- [ ] v1306 · G4 cohesion + honest labeling pass

## PHASE C · SESSIONS FLAGSHIP DEPTH (remaining D-rounds) — v1307–1320
- [ ] v1307 · D14 session comparison (diff two runs)
- [ ] v1308 · D16 area heatmap (where you farm most)
- [ ] v1309 · D17 best-run / streak highlights
- [ ] v1310 · D18 shelf card redesign (Maxroll-grade cinematic)
- [ ] v1311 · D19 beat-card chips (Theatre caption → iconographic)
- [ ] v1312 · D20 animated stat count-ups on the dossier
- [ ] v1313 · D21 verdict seal-stamp polish
- [ ] v1314 · D22 filmstrip chapter markers (read/find/film beats)
- [ ] v1315 · D24 live-session preview card (recording-now)
- [ ] v1316 · D25 session notes / naming ("Meph 200x")
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
- [ ] v1328 · E1b funnel-2× accuracy reconcile (check an item twice before attaching stats)
- [ ] v1329 · E1c thrown-with-stats comparison log (muled-with-stats vs thrown, side by side)
- [ ] v1330 · Vault Integrity Checker deepening (more classes; the G3/checker/vault unification)
- [ ] v1331 · Vault manager full pass (stats + mule + capacity + ladder)
- [ ] v1332 · Vault cohesion + verify

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
- [~] v1341–1345 · TYPOGRAPHY — finalize ONE type scale/hierarchy across every surface (console + bible + all tabs); consistent weights/sizes/spacing; every surface obeys it. **BROUGHT FORWARD (Konyo's flagship-look emphasis):** [x] v1293 — console weights ALL tokenized onto --fw-* (0 residual) + dead override removed; [ ] letter-spacing/line-height token-set completion (next); [ ] bible-side + cross-app pass still Phase-G-proper.
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
