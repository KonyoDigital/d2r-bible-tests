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
