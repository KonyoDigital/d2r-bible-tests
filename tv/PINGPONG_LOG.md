# 📺 TV DIABLO — 🏓 PINGPONG NIGHT LOG (2026-07-15 → 16)

> The public round-by-round ledger of the TV-specific pingpong run (Konyo's order:
> "full TDD and test suites + ping-pong upgrades — ship at least 10 versions,
> end-to-end, verified in between"). **Ownership (2026-07-16):** Grok owns the
> **TV-KAI surface only** (`tv/**` agent + this ledger + TV README). Bible/forge/
> chronicles stay untouched. Constraint stack: read-only scanner · player's own
> Claude subscription · Sonnet for reads · no fabrication.

## State entering the night (v710.6b)
- Live run #1 verdict: capture ✓ · settle detector ✓ (fired exactly at pauses) ·
  bridge ✓ · board ✓ · **vision ✗ — every read hit the 180s timeout** (claude's
  Read choked on the 16MB raw BMP). Konyo saw "reads every ~3 minutes" = the
  timeout cadence, not the design.
- Fixed pre-night: BMP→1568px JPEG before vision (sips, ~300KB) · timeout 90s ·
  🧠 brain log (agent event ring → board panel: settles/skips-with-reasons/reads) ·
  stale sim flag cleared on boot · nested-Claude warning · README bare-terminal note.
- **Not yet re-tested live** — Konyo closed the agent; next launch picks it all up.

## Rounds

### R1 · v711 — TDD foundation: TV_STUB seam + agent test suite ✅
- `TV_STUB=1` makes `claude_read` return canned reads from `tv/stub_manifest.json`
  (basename key, `*` fallback) — the FULL agent loop runs with zero vision cost.
- `TV_PORT` env override (tests + port-conflict recovery).
- `tv/test_agent.py` (stdlib unittest, synthetic BMPs — no fixtures): 9/9 green —
  sig invariants (identical=0 · ±10 flicker settles · half-screen swing = motion ·
  None = 1.0) · loading-guard threshold · stub manifest · event-ring cap 60 ·
  live bridge GET /state + /ping with beat merge.

---

## GROK OWNERSHIP LOG (TV-only · ships code in `tv/**`)

### R11 · v720 / v720.1 — auth path + worker lock (live run #2 → #3) ✅ suite 19/19
- **Run #2 (v719.2, 2026-07-16 ~19:49 IDT):** agent fresh, transport OK (`read.jpg` 391KB),
  child had `--strict-mcp-config`, settle fired — but warm “didn't answer” and oneshot hit
  90s `cap` → honest-empty reads. Not a JPEG problem anymore.
- **Root cause:** shell `ANTHROPIC_API_KEY` makes headless `claude -p` prefer API auth over
  Claude subscription login. Probe: **with key → 40s timeout empty**; **key stripped →
  text `pong` in ~7s, image read JSON in ~21s**.
- **v720 fix:** `_claude_env()` strips `ANTHROPIC_API_KEY` + `ANTHROPIC_AUTH_TOKEN` for
  worker spawn and oneshot; one-time brain `vision auth: stripped …`. Parent shell unchanged.
- **Live proof after restart:** `vision warm — session ready in 14s` · oneshot **15.9s** ·
  warm reads **6.8s / 9.3s** (honest empty when not on D2R loot — correct).
- **v720.1:** worker `ask()` lock (warm thread vs settle-read race caused “non-JSON” on first
  fire) · persist `mode` on state reads · suite **19/19**.
- **Scope:** `tv/**` only. No bible / forge / chronicles.

### R12 · v723 — Haiku speed + genius Sonnet escalate + farmed→vault wire
- **Fast model:** `TV_MODEL=haiku` (warm worker). **Genius:** auto-escalate to
  `TV_MODEL_ESCALATE=sonnet` when conf low / empty loot / shaky farmed names.
  Cap `TV_ESCALATE_CAP=40`. Subscription only (API key still stripped).
- **Intent:** loot→`seen` (review-first) · inv/stash→`farmed` (auto engines + vault).
- **Vault:** new thin `window.tvVaultRegister(name)` — reuses owned + suggestMule +
  muleAssign from intake. **No photo AI. No vault redesign.** Floor never auto-files.

### R13 · v724 — SESSION HISTORY board (pre run #3)
- TV tab panel: LIVE / LAST SESSION · clock-time rows · HD art · HIT/DB/NO DB badges
  against engines + ~1400 ITEMS · farmed vault tags · last vision JPEG via `GET /frame`.
- Persisted `d2r_tvdHist` (account-forked) so last session survives agent restart.
- Board specs **4/4** · agent suite **22/22**. Restore point unchanged.

### R14 · v725 — run #3: Haiku slower live → Sonnet default + combat-pause filter
- **Live #3 observation:** Haiku warm **13–16s** vs prior Sonnet **6–10s** (opposite of plan).
  43 honest-empty gameplay settles burned budget on combat pauses.
- **Default flip:** `TV_MODEL=sonnet` (haiku opt-in). Gap 8→6s. Empty gameplay/town →
  **20s cool** so stands don’t re-fire vision. Warm re-proof: sonnet ready in **3s**.

### Explicit non-goals (unchanged)
- No forge rewrite · no fabricated names · don’t loosen settle · don’t rewire vault intake photos.

### R2 · v712 — stub solid + board TDD + build-stamp sync ✅ (Grok P0-1 ✅ · P0-2 was stale-scan, origin already current ✅ · P0-3 ✅ · P1-5/6/7/8 ✅ · P2-9/10 ✅)
- `tv/stub_manifest.json` COMMITTED (P0-1) — plus the test that used to `os.remove` it now backs-up/restores (a TDD catch on the tests themselves).
- Agent suite → **12/12**: + `_readable_frame` conversion (honest both-ways: jpg-smaller or clean passthrough) · event-kind contract {boot,settle,read,skip,cap} · stub e2e (manifest → claude_read → state).
- Agent hardening: `ev("cap")` on empty-JSON parses (P1-8 — a hang can never again be silent) · pulse resumes the instant a read returns (P2-9 — CRT never sticks on 🧠 READING) · one-time `vision transport OK — read.jpg NNKB` brain line (P2-10).
- **Board TDD (the R2 core): `tests/v712_tv_board.spec.ts` — mock bridge via page.route, zero agent.** 2/2 green: CRT off→live→offline with dual-switch sync + meters + brain log; all 5 route kinds chip correctly; review-first proven (nothing applied until ✓); apply-all mutates the REAL engines (Ist 0→1, Perfect Ruby 0→1, Harlequin Crest ticked).
- `D2R_BUILD`/title/meta → v712 (P0-3). P0-4 (live re-test, bare Terminal) remains Konyo's move.

### R3+R4 · v713 — PERSISTENT VISION WORKER (the speed fix) + latency meters ✅
- One long-lived claude session (stream-json in/out): each frame = a TURN, not a cold start.
  Context-bloat guard: worker self-restarts every 8 turns. ANY wobble (timeout · dead stream ·
  junk output) kills the worker and falls back to the one-shot path — never a wedged reuse.
- `TV_CLAUDE_BIN` seam + `tv/fake_claude.py` (speaks stream-json; modes ok/slow/junk) →
  suite now **16/16**: multi-turn SAME-PID reuse · restart-after-max-turns · timeout-kill
  returns None (fallback proven) · junk parses to None (fallback proven).
- Read latency measured per read (`ms` on the record) → board READS meter shows `n / 120 · Xs avg`.
- Expected live effect: reads land in ~2-10s warm (vs 180s hangs run #1, ~15-30s one-shot cold).

### R5 · v714 — Grok's shape + robustness ✅ (P0-1 stale-scan: v713 WAS pushed · P0-2 ✅ stamp v714 · P1-4 ✅ · P1-5 ✅ · P1-6 ✅ · P2-8 ✅)
- Board spec extended: latency meter (`4.2s avg`) + cap events visible in the brain log — failures can never be silent on the board. 2/2 green.
- **Boot warm-up turn (Grok P2-8)**: the worker fires a tiny turn at launch → `vision warm — session ready in Ns` brain line; the first loot pause is never the cold start.
- Robustness: port-in-use → one clear line + exit (merged with Desktop's parallel guard — we collided mid-file and merged to one) · suspiciously-tiny capture → screen-recording-permission hint (once).
- README carries a "Last live verdict" section from now on.
- Note for Grok's scanner: two rounds in a row your "unpushed" flag was seconds stale — trust `git ls-remote` over cached scans.

### R6 · v715 — THE TZ WELD ✅
- TZ SEEN meter now cross-checks the SCREEN's purple list against the TRACKER's live rotation
  (`window._tzPeek`): agreement = `✓ tracker agrees` (two independent sources), disagreement shown
  honestly (`· tracker: <zone>`), no data = no claim. Board spec asserts the weld (stubbed _tzPeek).

### R7 · v716 — SESSION DIGEST → the cockpit 📓 log ✅
- Turning the TV off (or the agent dying) flushes one honest line into the Session log:
  `📺 TV session: N reads · M applied · Area → Area`. E2E-verified headless (mock reads → apply →
  toggle off → line present in d2r_sessionLog through LSR, account-forked like the rest of the log).

### R8 · v717 — CI for the agent suite ✅
- `.github/workflows/tv-tests.yml`: every tv/** push runs the 16-test suite on ubuntu in seconds
  (sips-less linux exercises the honest passthrough branch; fake_claude exec bit locked in git).

### R10 · v718 — Grok's end-of-night picks ✅ (formal consult, full text in the session)
- **Legibility**: every read event now carries its transport — `[warm 3.2s]` / `[oneshot 14s]` —
  and read records carry `mode`; a session's health is readable off the brain log alone.
- **Auto re-warm**: a worker death fires a debounced background warm turn — one-shot is a bridge,
  never the new normal (`vision re-warmed in Ns — back to fast reads`).
- Pick #3 (hold applies on empty/TZ-disagree) = already the design: applies are review-first ✓-only.
- **THE ONE REMAINING GATE IS HUMAN**: Konyo's bare-terminal live re-run — expect boot → warm-in-Ns
  → warm reads 2–10s. Everything else tonight is engineering-complete per Grok's verdict.

## Night tally
v710.6 · v710.6b · v711 · v712 · v713 · v714 · v715 · v716 · v717 · v718 = **10 shipped versions**,
every one gated (agent suite grew 0→16 · board specs 0→2 rich locks · CI job live) — rinse-and-repeated
with Grok co-piloting in this file throughout.

## 🏁 GATE PASSED — 2026-07-16 evening (live, Konyo's machine, his subscription)
`AGENT BOOTED → vision warm — session ready in 3s → [warm 10.4s] honest empty →`
`inventory · Superior Dagger | Light Healing Potion | Hard Leather Armor | … [warm 6.2s]`
Full pipeline proven in production: capture → settle → JPEG → warm session → scene + names →
bridge → board → route chips. Three root causes across two live runs, all fixed and shipped:
transport (v710.6, Fable) · MCP stalls (v719.1, Fable) · **API-key-over-login auth (v720, GROK
— his catch, his code, Fable gated 18/18)**. The pingpong triangle delivered.

### R11 · v721 — chips join the DATABASE + HD art ✅ (Konyo, live during his first real session)
- Every signal-feed chip now carries `data-arttip` (the bible's universal hover card — odds ·
  bases · rarity) and `artUrl()` HD art with the in-game look. Runes resolve as '<X> Rune',
  base-suffixes stripped for uniques. Board spec still 2/2; screenshot-verified.

### R12 · v722 — LATENCY RETUNE (Konyo's live feedback: floor pile read ~1min late)
- Honest diagnosis: eyes were never the lag — the 20s READ COOLDOWN stacking with ~7s vision was.
- POLL_S 0.5→0.25s (his ask, cheap) · **MIN_GAP_S 20→8s (the real lever)** · SESSION_CAP 120→240
  (same discipline, sized for the cadence) · cap published in /state, meter reads it dynamically.
- Expected feel: pause-on-pile → chip in ~10-16s worst case (was up to ~60s when gaps stacked).
- Floor-vs-inventory is already distinguished per read (scene chip ⚔️ loot vs 🎒 inventory).
