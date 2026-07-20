# 🛰 SUPERGROK TASK LIST — TV DIABLO / D2R Bible (post-v944 arc)

_Handoff from the Claude (Fable) leg, 2026-07-21. Everything below is on `main` and green
(suites 43 control + 157 agent + 56 routes + demos 7/7). Pick tasks in priority order; each
has the symptom, where to look, and how to verify. Konyo debugs side-by-side with you._

**Verify battery for ANY change:** `python3 tv/test_control.py` · `python3 tv/test_agent.py` ·
`python3 tv/test_routes.py` · `node tv/demo_console.mjs` (7 journeys). NEVER run the full
Playwright suite on the Mac (it crashes the machine) — CI Routine I is the full verdict.
Stamps must stay in parity: agent `tv/tv_diablo.py` VERSION == control `ver` == bible
`window.D2R_BUILD.id` (test_control enforces). bible.html needs the EDIT_LOCK claim/release.

---

## ✅ SUPERGROK RETURN (2026-07-21) — v944.6 WIP, holding for Claude gate+push

**Stamps ×3 green:** control `ver` = agent `VERSION` = bible `D2R_BUILD.id` = **v944.6**
(Claude had flagged control stuck at v944.5 — **already bumped** in `status_payload` ~L2697.)

**Battery (this leg):** control 43 · agent 157 · routes **66** · demos 7/7. Not pushed —
Claude holds the ship until polish-ui-2 render lands cleanly on the same green floor.

| # | Task | Status |
|---|------|--------|
| P0#1 | Never-zero re-fire | ✅ `_intake_is_real` · `_drv_empty_refire_plan` · driver re-queues freshest frame on total==0/ok=false (tally only; vault empty stays done). Display layer tab_best kept. Pins in `TestNeverZeroRefire`. |
| P0#2 | Quorum soak | ✅ 12 reels / 748 frames: **disagreement 0%**, conf&lt;2 71% (mostly single-brain/gameplay), near-dup collapsed 186. **Design Q:** do NOT extend journal panel-truth past `stash-*` yet — soak never saw inventory↔tooltip fights; leave inventory/tooltip two-ways as disagreement. |
| P1#3 | Stage 3 lanes obey ledger | ✅ `_kai_stage3_select` + closer builds PRE-fire plan, funnel/judge fire only fireable rows (`not-selected`/`cap`, conf≥2); final rebuild writes `routed` back. Vault stays `no-vault-fire`. +3 pins. |
| P1#4 | label+time near-dup | ✅ 3s window in `_kai_build_routing` (`near-dup-of:`); film never trimmed. |
| P2#5–9 | Chronicle / lease / judge soak / render / SIM name | open (render = polish-ui-2 parallel; SuperGrok is **not** editing `control_ui.html`) |

**Files SuperGrok owns this leg:** `tv/control_app.py`, `tv/test_routes.py`, `tv/tv_diablo.py` VERSION, `bible.html` stamp only (EDIT_LOCK claimed/released). Leave `control_ui.html` to polish-ui-2.

---

## P0 — REAL ACCURACY BUGS (Konyo feels these)

### 1. The runes-intake 0-error class ("still not reading the runes") ✅ DONE (v944.6)
The `/api/intake_log` (new v944.4) proved it live: one session logged `ok runes total=404`
**and** a later `error runes total=0` on the SAME tab. The 404 is a real read; the 0 is a
failed shot that still journaled a receipt and poisons the theatre ("0 read"). This is the
recurring "runes not reading" complaint — it's intermittent, not total.
- **Find:** the runes intake path in `bible.html` (`_aicApplyIntake` / the tally engine) and the
  driver fire in `tv/control_app.py` `_engine_driver`. Why does a second runes shot error to 0?
  Page shutter mid-intake? A stale frame? A race with the first (successful) shot?
- **Goal:** an errored/empty shot must NOT overwrite or shadow a good receipt for the same tab
  in the same session. Prefer the max-total receipt per tab, or suppress empty re-fires when a
  good one exists. Add a pin in `tv/test_routes.py`.
- **KONYO'S EXPLICIT RULE (2026-07-21):** "I don't want ANYTHING read 0. This should be updated and
  read according to the new/updated picture." A 0/error read is NEVER the final answer — it must
  trigger a RE-READ of the latest/updated frame for that tab and update the count accordingly.
  Zero is a failure signal, not a value: the pipeline should self-heal (re-fire against the freshest
  archived frame of that tab) until it gets a real count, and only the real count is journaled/shown.
  Build it as: on `total==0` or `ok==false` for a stash tab, the driver/closer re-reads the most
  recent non-dup frame classed to that tab and supersedes the empty receipt (dedupe key already
  collapses duplicates; make the SUPERSEDE explicit so the theatre + Chronicle always show the
  updated picture's real count, never the 0).
- **Verify:** replay a runes session → theatre shows the real count (e.g. 404), never a 0; a forced
  empty shot is auto-superseded by a re-read of the newest frame; pin proves 0 never wins.

### 2. Quorum disagreement policy — real-reel soak
Stage 2 (`_kai_quorum_label` in control_app.py) flags `disagreement` when ≥2 distinct
non-gameplay labels have no ≥2 winner. Untested against volume of REAL reels.
- **Task:** run the router over 10+ archived reels (`tv/frames/hist/reel_*/kai_report.json`),
  tally how often `disagreement` / `confidence<2` fire, and judge whether the policy is too
  strict (real stash frames getting dropped) or too loose. Tune, pin the tuned thresholds.
- **Open design Q (my baton to you):** ocr says `tooltip`, journal says `inventory` — right now
  that's a disagreement → no route. Is that correct, or should journal-panel-truth extend beyond
  `stash-*`? Decide + document.

---

## P1 — ROUTER STAGE 3 (the ledger must DO something)

### 3. Lanes obey the ledger + receipts written back
Stages 1+2 build the routing ledger (per-frame label/route/routed/skipReason/confidence). The
funnel/judge lanes in `_kai_closer_loop` still fire on their OWN logic, not the ledger.
- **Task:** make the KAI funnel + judge lanes CONSUME `report["routing"]`: only fire on rows the
  ledger marked routable (`route` set, `skipReason` null, `confidence>=2`), and write the actual
  receipt back onto the row (`routed` = what fired). Close the loop so the ledger is the source
  of truth, not a parallel observer.
- **Watch:** the `no-vault-fire` skip — inventory/stash frames route to `vault` but nothing fires
  there yet. Stage 3 is where the vault funnel actually processes those frames through the LOCKED
  vault intake (mule/throw-out). Respect the intake-lease question (task 6).
- **Verify:** a sealed reel's `routedCount` matches the receipts journaled; pins in test_routes.

### 4. Fuzzy-vs-exact dedupe (challenge my call)
Dedupe is EXACT-sig (`_kai_frame_sig`, JPEG sampled bytes). I argued fuzzy byte-tolerance is
meaningless post-entropy-coding, so near-identical stash-sitting frames DON'T collapse — I
deferred near-dup collapsing to a Stage-2 **label+time grouping** (same label + within N seconds
= one logical event) instead of pixel tolerance.
- **Task:** either implement the label+time grouping for routing (route once per stash-sitting
  run, all frames still in film), OR prove a cheaper pixel-domain signature that fuzzy-matches
  reliably and challenge my reasoning. Konyo's intent: "duplicate photos get DEDUPED within the
  router... they exist only within the film simulation" (routing-only, film never trimmed).

---

## P2 — UNBUILT ORGANS & POLISH

### 5. Chronicle write-in (the last unbuilt organ)
KAI registers witnessed items to a ledger (`_kai_compile_register`) but nothing writes them into
the actual grail/Chronicle in bible.html. This is bible-side and needs dedup laws + EDIT_LOCK
discipline (Claude Desktop also edits bible.html — lost-update incident on record).
- **Task:** design the auto-register write-in: a witnessed DB-real item → Chronicle found-state,
  with a dedup law (never double-count, never overwrite a manual mark), gated behind a review so
  it can't corrupt the sealed 99/99. START WITH A SPEC in `tv/PLAN_ONE_SYSTEM.md`, not code.

### 6. Intake lease (engine-vs-open-board double AI call)
When the engine iframe AND a board tab are both open, an intake can fire twice (SET-wrapper makes
it safe today, but it's wasteful). A lease (one owner holds the intake token at a time) was
deferred all arc.
- **Task:** design + build a lightweight lease in control_app.py so exactly one context fires a
  given tab's intake. Low risk, additive.

### 7. Judge calibration soak (crafted/rare verdicts)
KAI's judge (`aicJudge` in bible.html, `_jcap` lane in control_app) now knows 3,135 names incl.
generated rares + crafted, split so rares aren't grail-shielded. Never soaked against real
gameplay verdicts.
- **Task:** run the judge over a reel's tooltip frames, compare its keep/toss/border calls to what
  Konyo would actually do, tune the `_aicVerdict` thresholds. Konyo noted L3 wants OPUS-level
  smarts ("if it wasn't so expensive"); document where a model bump would most move accuracy.

### 8. Render verification (after polish-ui-2 ships the v944.4 UI)
New server data (`dossier.readStatus`, `dossier.router`, `/api/intake_log`) is being rendered by
the Claude leg's ui owner. Once it lands: verify against a REAL farm session that the read-status
MISS verdict, the receipt log status dots, and the clickable tally detail all match the journal
truth. This is Konyo's core ask — "I want it 1000000% accurate, every screenshot synced and
cross-referenced." Cross-check the theatre against `/api/intake_log` row-by-row.

### 9. SIM / Theatre naming unification
Konyo repeatedly asked "SIMULATION vs THEATRE — why two? is it the same coded?" They ARE the same
player (one door). Unify the naming/entry so there's no confusion — one labeled entry, no phantom
second window. Cosmetic but he's raised it 4+ times.

---

## STANDING CONTEXT
- **Three-eyes + funnel doctrine:** 🔴 live text-triggered → 🔵 trailing verify (now with the
  text-eye BACKLOG sweeper, v943.9) → 🧠 KAI post-seal sweep → 📸 frames funneled through the
  LOCKED vault/tally/item-checker (never a new reader). Spec: `tv/PLAN_ONE_SYSTEM.md`.
- **Read-only law:** screenshots only, no game input. Auto-mule = automated accounting, never hands.
- **Journal law:** `ts == captureTs`; frameId filename = capture ms.
- **v925-LIGHT trap:** lanes historically shipped OFF by default; now hardcoded ON. If a lane looks
  dead, check the env gate FIRST (`TV_OCR`/`TV_FILM`/`TV_KAI`).
- **Never run the full Playwright suite on the Mac.** Smoke + targeted only; CI = full verdict.
