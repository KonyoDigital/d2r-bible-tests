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

## ✅ SUPERGROK RETURN (2026-07-21 morning) — v945.6 Theatre + lease + Chronicle SPEC

**HEAD context:** night arc sealed at v945 / polish-ui-2 through v945.5; Fable overnight soak
de-prioritized missed→judge escalation. This leg continues the open P2 organs.

**Stamps ×3:** control = agent = board = **v945.6**

**Battery:** control 43 · agent 157 · routes **73** · demos 7/7

| # | Task | Status |
|---|------|--------|
| P0#1–2 · P1#3–4 | never-zero / quorum / Stage 3 / near-dup | ✅ shipped earlier (v944.6) |
| P2#5 | Chronicle write-in | ✅ **SPEC only** in `tv/PLAN_ONE_SYSTEM.md` (inbox + review gate + laws; no grail mutation code yet) |
| P2#6 | Intake lease | ✅ control `/intake_claim`+`/intake_release` · driver claims · bible board/vault claim (EDIT_LOCK) · +4 pins |
| P2#7 | Judge soak | ⏸ Fable overnight: de-prioritized (0 grail slip; cap rarely hit) |
| P2#8 | Render verify | polish-ui-2 shipped UI through v945.5 — live farm cross-check still open for Konyo |
| P2#9 | SIM / Theatre unify | ✅ one door labeled **Theatre** (button, marquee, bug, phase); fixed broken `foot-ports` HTML |

**Still open:** Chronicle *code* (after SPEC soak), live farm render verify, optional judge-cap tune.

---

## ✅ SUPERGROK RETURN (2026-07-21 earlier) — v944.6 shipped

**Stamps ×3 green:** control `ver` = agent `VERSION` = bible `D2R_BUILD.id` = **v944.6**
(Claude had flagged control stuck at v944.5 — **already bumped** in `status_payload`.)

**Battery (that leg):** control 43 · agent 157 · routes **66** · demos 7/7. Shipped as v944.6.

| # | Task | Status |
|---|------|--------|
| P0#1 | Never-zero re-fire | ✅ |
| P0#2 | Quorum soak | ✅ disagreement 0% on 748 frames |
| P1#3 | Stage 3 lanes obey ledger | ✅ |
| P1#4 | label+time near-dup | ✅ |

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

---

## 🔬 FABLE OVERNIGHT SOAK (autonomous, post-v945.5) — recal validated, escalation de-prioritized
Ran the miss/quorum soak over all 20 sealed reels:
- **v944.7 recal validated:** old-missed 291 → nameish-missed 186. The recal drops **105 false-positive
  miss flags (36% noise removed)** — flavor/stat lines no longer cry wolf. Confirmed on real data.
- **Zero grail slip:** DB-real-unregistered misses = **0/291**. Every grail unique/set that appeared
  was registered. The register does not miss grail items.
- **Judge cap rarely the bottleneck:** only **1/20** reels exceeds TV_KAI_JUDGE_MAX(12) tooltips.
- **→ MISSED→JUDGE ESCALATION DE-PRIORITIZED (task P0 baton):** no grail loss to escalate; the 186
  nameish misses are magic/rare/crafted items the judge already tiers. Value = at most a judge-cap
  tune on high-tooltip reels, NOT a closer rewrite. Recommend Grok NOT do the closer surgery; if
  anything, bump TV_KAI_JUDGE_MAX and re-soak. Held off touching the freshly-sealed Stage-3 closer
  overnight (no reviewer awake) — this soak is the safe deliverable that de-risks the decision.
- **NOTE on thin register data:** only 1/20 reels has a register (the feature is v943-new); real
  register/chronicle validation needs Konyo's NEW farm runs, not old reels. The write-in stage
  (task P2#5) should be designed against fresh sealed reels, not this backlog.
