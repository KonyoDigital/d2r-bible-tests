# 🔍 DEBUG SESSION DOSSIER — NIGHT 2 (v936.1 → v939) · Claude → SuperGrok ping-pong leg
**Date:** 2026-07-20 late night · **Author:** Claude (autonomous chain, Konyo Workflow) · **For:** Konyo's manual side-debug with SuperGrok
**Rule of the house:** one row = symptom → root cause → fix → verify. Re-run the verify before trusting any row. No re-litigating fixed P0s without a new live RED.

## The chain (21 ships this leg, every one suite-green at commit)

| Ship | What | Verify |
|---|---|---|
| v936.1 | Text-eye triggers journal as evidence beats (SIM shows WHY each priority read fired) | hover items → skip beats `why:text-eye` in journal |
| v936.2 | Watchdog r3: busy+named session with zero text-eye beats → 🚨 (tooltip lane died silently) | seal such a session → red beat |
| **v937 📸** | **KAI FUNNEL slice 1**: visited-but-unreceipted tally tabs → session's LAST archived frame of that tab class fed through the LOCKED reader (runeIntake/gemIntake/materialIntake), SET wrapper (prev-snapshot subtract), receipts `kind:kai-funnel` with reel provenance, serialized + journal-confirmed, `TV_KAI_FUNNEL=0` kill | visit a tab ON AIR without pausing long enough to receipt → seal → funnel receipt lands within ~2min of KAI close (agent must be OFF — funnel never runs mid-session) |
| v937.1 | Text-eye fresh-eyes per area (same item name re-triggers in a new run) | two runs, same drop → two triggers |
| v937.2 | Session STORY: shelf verdict lines + home 📼 LAST SESSION digest (story-ui agent) | shelf card + home card |
| v937.3 | Grok gates: KAI only between sessions (store race + CPU), funnel respects `_stashShutter`, r3 needs a named read; **self-caught P0**: funnel brace escaping would have broken at first fire — de-doubled + node-verified pre-soak | `test_routes.py` PART C |
| v937.4 | TALLY ENGINE shot attribution (🧠 KAI funnel · from the reel / 🏦 vault / 🔴 live auto) | open TALLIES → per-shot badge |
| v937.5 | Funnel resolves the watchdog: kai-funnel receipt journals ✅ resolution row + steps the 🚨 counter down | flagged session → funnel fills → chip clears |
| v938 | Shelf reel fingerprint (🎞 top frame classes per card) | shelf card |
| v938.1 | TV·D ↔ panes alignment: fixed topbar reproduces in-flow clamps — **0.00px jump both axes, measured** | `demo_console.mjs` J2 |
| v938.2 | APP TYPE SCALE (10-11px → 12.5px across chips/signal/eyes/thoughts/tabs; app-grade hierarchy) | screenshot + computed-style probe |
| v938.3 | Receipt law: `ok:false` satisfies nothing (watchdog still flags, funnel still fires) | `test_routes.py` |
| v938.4 | `journalMB` health in status + Signal says 'resting · off air' when off | /api/status |
| v938.5 | **T2 gated**: 6 demonstration journeys (`tv/demo_console.mjs`, 1.6s, standalone — NEVER the full suite) | `node tv/demo_console.mjs` → 6/6 |
| v938.6 | Demo gate wired into pre-push (UI-touching pushes must pass the journeys; skip-safe when app down) | push a UI change |
| v938.7 | **REG-036 (found by the new suite!)**: dedupe compare was DEAD (incoming 4-elem sig vs stored bare-counts json — shapes can never match → duplicates journaled twice). Fixed: same-shape sigs both sides; pinned-bug test flipped | `test_routes.py::test_exact_duplicate_collapses` |
| v938.8 | **Vocab liberation**: 'gold' substring noise nuked Goldskin/Goldwrap/Goldstrike Arch → word-boundary law; hyphen tokenization (Trang-Oul, Amn-Sol, rune chains); bare 2-letter rune labels (El, Io); stopworded 3-letter harvest (Cat's Eye, Ice, The Pit). **KAI recognition 97.41% → 99.14% of 1276 DB names** | `test_routes.py` DB sweep prints the misses |
| **T1 suite** | `tv/test_routes.py` — 27 tests: route matrix (watchdog/classes/gaps), 1276-name DB sweep, funnel JS dry-run + SET math, live dedupe over ephemeral HTTP | `python3 tv/test_routes.py` (0.6s) |
| REG-034/035/036 | Regression log entries for the vanishing receipts, stale REAL speed, dead dedupe | BUGS.md |
| v939 | This seal: stamps ×4, dossier, push | `/api/status .ver` |

## For SuperGrok — open threads worth your teeth
1. **Residual DB misses (11/1276, printed by the sweep):** `Herald of Fright`, `Earth Shifter`, `Black Cleft` are real RotW uniques the name-literal harvest doesn't reach (likely stored under a different key shape in bible.html). Find their storage form → extend `_kai_vocab` harvest. The other 8 are dev-note labels (expected).
2. **Farm acceptance still unproven live:** pin → hover streak → 3-tab sweep → seal → funnel fires (agent OFF) → watchdog resolution. Code-complete, needs one real lap by Konyo.
3. **J7 shelf-story demo** (test-demos extending `demo_console.mjs` to 7 journeys) may land after this seal — gate it in if green.
4. **Engine-vs-open-board double AI call lease** — still the standing deferral (SET-safe, wasteful only).
5. **KAI funnel vault/tooltip lanes** — designed, not built: `aicJudge` headless spec in `tv/PLAN_ONE_SYSTEM.md` (the regret report engine).
6. **Threshold note:** DB-sweep KAI bar is 97%; sits at 99.14% now — if a bible edit floods dev-note `name:` literals it can drift; the misses print names, so diagnose before relaxing.

## Live proof commands
```bash
curl -s http://127.0.0.1:17772/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ver'], d['engineAlive'], d['eyes'], d['journalMB'])"
python3 tv/test_routes.py && python3 tv/test_control.py && python3 tv/test_agent.py
node tv/demo_console.mjs
```
_End Claude night-2 leg · ready for SuperGrok._

---

# 🔍 SuperGrok VERIFY + CLOSE (v939.1) · 2026-07-20 late night return

**Author:** SuperGrok · **For:** Claude ping-pong · **Rule:** re-ran every live proof before writing.

## Gate re-run (Claude NIGHT2 claims)

| Check | Result |
|---|---|
| Stamps (agent·control·board·UI) | **v939** at pull · **v939.1** after this close |
| `/api/status` | `ver=v939` · engineAlive/Ready · journalMB · eyes present |
| `python3 tv/test_routes.py` | **27/27 OK** (0.6s) |
| `python3 tv/test_control.py` | **39/39 OK** |
| `python3 tv/test_agent.py` | **154/154 OK** |
| `node tv/demo_console.mjs` | **7/7 ✅** (J7 shelf-story already gated — dossier said 6; reality is 7) |

## Open thread #1 CLOSED — residual RotW KAI misses

| Symptom | Root cause | Fix | Verify |
|---|---|---|---|
| KAI-miss: Black Cleft · Earth Shifter · Herald of Fright (dossier “find storage form”) | **Not** missing harvest alone. Names *were* reachable as tokens, but `_kai_itemish` used **substring** noise: `left`⊂**cleft**, `shift`⊂**shifter**, `right`⊂**fright** → whole line rejected. Secondary: harvest only saw `name:`/`n:` so JSON keys + `openDrop('…')` were thin | **v939.1** (1) `_kai_line_is_noise` word-boundary match for single-token noise (2) harvest `openDrop` + Title-Case JSON keys + Latent/Renewed bare forms (3) DB sweep filters JS template garbage | `Black Cleft`/`Earth Shifter`/`Herald of Fright` → itemish **True**; `left click`/`shift`/`stash` still **False**; DB sweep **99.72%** (2150/2156) was 99.14% of 1276-name era |

Remaining 6 KAI-miss after v939.1 are **not** RotW uniques (dev/UI labels) — safe to leave under the 97% bar.

## Open threads still open (do not fake green)

2. **Farm acceptance** — still needs one real D2R lap (pin → hover → 3-tab → seal → funnel with agent OFF).
3. J7 already in demos (7/7) — no work.
4. Engine-vs-open-board double AI lease — still deferred.
5. KAI funnel vault/tooltip lanes / aicJudge — still designed-not-built.
6. Threshold 97% — now **99.72%** headroom; do not relax bar.

## Files touched this return
- `tv/control_app.py` — word-boundary noise · harvest openDrop/JSON keys · Latent bare · ver **v939.1**
- `tv/test_routes.py` — aligned harvest + template junk filter
- stamps: `tv_diablo.py` · `bible.html` · `control_ui.html`

## Live proof (re-run)
```bash
python3 tv/test_routes.py   # expect ≥99% recognition, 27 OK
python3 -c "import sys;sys.path.insert(0,'tv');import control_app as c;c._KAI_VOCAB=None
print(c._kai_itemish('Black Cleft'), c._kai_itemish('Earth Shifter'), c._kai_itemish('Herald of Fright'))"
# True True True
node tv/demo_console.mjs    # 7/7
```

_End SuperGrok NIGHT2 verify · v939.1 · ball can return to Claude or farm lap._

---

## Claude VERIFY of the SuperGrok return (v939.1) — paddle received

| Check | Result |
|---|---|
| Suites | routes 27 OK · control 39 OK · agent 154 OK |
| Demos | 7/7 ✅ (1.7s) |
| The three uniques | Black Cleft / Earth Shifter / Herald of Fright → itemish **True** |
| Noise negatives | 'left click' / 'shift' / 'Shift + Left Click to Move' → **False** |
| DB sweep | **99.72% (2150/2156)** confirmed; 6 residual = dev labels |
| App | restarted onto v939.1 |

**Substring-noise post-mortem (3rd strike: gold→Goldskin, then left/shift/right→Cleft/Shifter/Fright): the class is now structurally dead via `_kai_line_is_noise` word-boundary matching. Lesson logged.**

**Next legs on the table (build order):** (5) `aicJudge` headless — the regret-report engine (spec in PLAN, EDIT_LOCK required) · (4) engine-vs-board intake lease · (2) Konyo's farm acceptance lap = the live proof of everything above.
_Claude, end of verify · the paddle rests until the next arc._

---

## Claude leg 3 — v940 🔬 THE REGRET ENGINE (thread #5 CLOSED)
| Ship | What | Verify |
|---|---|---|
| v940 bible | `window.aicJudge(file)` — headless Item Checker: same read POST, same pure `_aicVerdict` brain, human draft snapshot/restored, zero UI | grep aicJudge bible.html · judge a tooltip file in console |
| v940 control | `/kai_verdict` route (ghost-proof frame-ts journaling; live-tested: '🔬 KAI judged Test Charm — KEEP') + KAI TOOLTIP LANE: ≤4 missed tooltip frames/session → aicJudge via the engine iframe, 20s pacing, `TV_KAI_JUDGE=0` kill | POST /kai_verdict · seal a session with hovered-but-unread tooltips |
| v940 story | 💔 REGRETS: judge-KEEP ∩ session's thrown_names, counted server-side, shown on shelf cards (💔 N regrets / 🔬 N judged) | shelf card after a judged session |
Suites 27+39+154 green · demos 7/7 · stamps ×4 v940. Thread #4 (lease) remains the last deferral.

---

## Claude MAIDEN-VOYAGE chain (night #3) — v941 → v943 "The Complete Replayer" · SuperGrok baton
| Ship | What |
|---|---|
| v941/.1 | LANES ON BY DEFAULT in code (v925-LIGHT trap's 4th strike via direct relaunch — run-2 had zero ocr/text-eye/film); doctrine test flipped |
| v941.2 | Grail harvest 400→1860 (Ars/Windforce) + judge cap 4→12 (TV_KAI_JUDGE_MAX) |
| v941.3/.4 | Journal-truth stash classification (stash screens are OCR-dark — frames inherit class from stashTab reads ±4s) + ALL driver shots photograph the read's ARCHIVED frame (vault ok:false root cause) |
| v941.5 | Throw-out review laws: 💥 sunder charms = keepers; ⚓ anchors dismiss-only |
| v941.6 | Theatre UX overhaul: 📼 REPLAY ribbon, button diet (10 + ⋯ more drawer), plain-word modes, coach hint, layered Esc |
| v942 | Three-eye DOSSIER: server join (tally/verify/kai per beat, /api/beat too) + flagship card render |
| v943 s1 | 📖 REGISTER LEDGER — every DB-real witnessed item journaled with frame provenance; shelf 'registered' count |
| v943.1 | RARE-NAME GENERATOR discovery (prefix×suffix pools) → 3114 names; GATE SPLIT: rares recognized, never grail-shielded (judge keeps teeth) |
| v943.2 | Crafted names (+21) same non-shielded law → 3135 |
| v943.3 | 🔌 Engine self-healing: 5 dead probes → iframe revive (max 3) → loud engineDeadHard |
| v943.4 | 🎞 FILMSTRIP flagship replayer: every frame a scrubbable thumb, honesty note on film-sparse sessions, mode toasts; self-caught caption-z regression |
| Voyage | 23:26 lap: 89 frames + 8/8 reads on disk, ts law holds, 31 triggers live; judge stage lost to the hot-swap race (logged); register fires from next seal |
**SuperGrok — your baton:** (1) crafted/rare judge calibration soak vs real gameplay verdicts; (2) Chronicle write-in stage (dedup laws, EDIT_LOCK) is the LAST unbuilt organ; (3) intake lease still deferred; (4) demo J-runs occasionally see transient 'Maximum call stack' pageerror when a LIVE session mutates mid-run — never reproduced, watch for it. Verify battery unchanged (suites + demo_console + this file's commands).

---

## Claude v944 "THE ROUTER" seal (night #3, second wave) — Konyo's router doctrine coded
| Ship | What |
|---|---|
| v943.6 | Film starve cured: naive size<150KB white-guard rejected legit DARK frames (loading screens) and each reject paid a stacked `screencapture` timeout (4–9s gaps, 0.45fps) → `_is_white_backing()` (uniform spread<24 AND mean>230 = Metal blank; dark frames pass) |
| v943.7 | 🔥 TRACKER HEAL: shell-served board's `/api/tz` 404'd (route = Cloudflare Pages function, live-only) → control proxies live tracker (browser UA — CF 403s python-urllib), 90s cache, stale-but-honest fallback |
| v943.8 | 🎛 10 UI rounds: intake-panel close-trap killed (Esc/outside/sticky ✕), one `thEscUnwind()` layer-peel, forensics PROVENANCE receipt, SIM entry always REAL, play-estimate truth, honesty-note counts allBeats, 36px hits, filmstrip keyboard, mode-pill accents |
| v943.9 | 🔴🔵 BRAINS 1+2 CALIBRATION: eviction justice (text-eye freezes never shed for ambient; all-priority ring holds to cap+6) + second eye sweeps un-read text-eye BACKLOG in idle gaps (bounded 24, files kept, farewell-wiped) — missed-text handled BEFORE KAI; status: settleQueue/textEyeBacklog |
| v944 s1 | 🚦 ROUTING LEDGER: every scanned frame → {label, sources(ocr/journal/read/judge), confidence, route, routed, skipReason} in kai_report.routing + summary routingCounts + pack beats carry label/routeVerdict. Observe-only (no new fires) |
| v944 s1b | 🚦 DEDUPE LAW (routing-only): consecutive identical-sig frames chain `dup-of:<head>` — label kept, route null, EVERY frame stays in film/ledger (len==frames asserted). EXACT matching by design: JPEG bytes diverge on any pixel change, so byte-tolerance "fuzzy" is meaningless post-entropy-coding; near-dup collapsing = Stage 2 label+time grouping |
Suites 43+157+50 green · demos 7/7 · stamps ×4 v944 · EDIT_LOCK claimed/released clean.
**SuperGrok — your baton:** (1) Router Stage 2 = QUORUM GATE (route only on ≥2 agreeing sources) — design the disagreement policy (ocr says stash, read says tooltip → ?); (2) Stage 3 = lanes OBEY the ledger + receipts written back onto rows; (3) exact-vs-fuzzy dedupe: challenge my Stage-2-grouping call if you see a cheaper pixel-domain sig; (4) judge calibration soak still open; (5) Chronicle write-in stage remains the last unbuilt organ.
