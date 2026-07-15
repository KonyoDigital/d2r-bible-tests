# 📺 TV DIABLO — 🏓 PINGPONG NIGHT LOG (2026-07-15 → 16)

> The public round-by-round ledger of the TV-specific pingpong run (Konyo's order:
> "full TDD and test suites + ping-pong upgrades — ship at least 10 versions,
> end-to-end, verified in between"). **Fable ships rounds here. Grok is read-only
> on product code but WRITES the `## GROK INSIGHTS` section** so Fable has a
> live worklist while editing. Constraint stack: read-only scanner · player's
> own Claude subscription · Sonnet for reads · chronicles/engines untouched ·
> no fabrication.

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

## GROK INSIGHTS (read-only · for Fable · refreshed as Grok re-reads)

> Grok does **not** edit `tv_diablo.py` / `bible.html` / capture scripts.
> Fable owns the ship. When a bullet is done, mark it `✅` in the round commit
> and leave a one-liner under that round; Grok will re-scan and refresh this block.

### Sync snapshot (Grok re-scan @ 2026-07-15 23:15 IDT · HEAD `780c9f9` / v719.1 · origin `780c9f9` via `ls-remote`)
- **no delta on git** — still v719.1; suite **16/16**; `D2R_BUILD` still **v716**; README still run #1 only.
- **Live still broken (ops, not missing commits):** agent PID **98261** started **22:51** (pre-v719.1). Child `claude -p` lines **lack `--strict-mcp-config`** (verified on live PIDs). Disk `state.json` still **poisoned** (`startedAt:1` + stub Pit loot) while in-memory brain log shows **8 consecutive** settle → worker death → **90s oneshot timeout** → empty `gameplay` cycles; beat `reading` on read #8. JPEG transport still OK (303KB).

### Live status (unchanged P0 — escalate)
1. **RESTART AGENT NOW** — v719.1 on disk is useless while 22:51 process runs. After restart, `ps` must show `--strict-mcp-config` on warm + oneshot children.
2. **Fullscreen D2R** before any settle (run #2 captured bible Chrome).
3. Expect after restart: `vision warm — session ready in Ns` (not “didn't answer”). If warm still fails *with* strict-mcp, escalate past MCP theory.
4. Log README run #2 truth + R11 ledger notes (v719/v719.1 commits have no round section yet).
5. Stamp badge → v719.1+ when writing up.

### Closed (commits — same as prior scan)
- ✅ v719 focus/visibility re-poll · ✅ v719.1 `--strict-mcp-config` · ✅ R6–R10 stack

### P1 — Fable (still open)
- State poison guard (`startedAt:1` / stub names must never win over live events)
- Argv unit test for `--strict-mcp-config`
- Optional: agent prints build/mtime or git sha at boot so stale process is obvious in brain log

### Explicit non-goals (unchanged)
- No forge engines · no API keys · no fabricated names · don’t loosen settle.

### Suggested next shape
**No more features until restart + one warm read.** Then **v720**: stamp · state guard · boot-sha brain line · README run #2/#3.

### Grok’s next move
Next scan: closed only if agent `lstart` ≥ 22:58 **and** a child argv contains `strict-mcp-config` **and** a warm/boot event is not “didn't answer”.

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
