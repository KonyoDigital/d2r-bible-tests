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

### Sync snapshot (Grok re-scan @ 2026-07-15 22:30 IDT · local HEAD `2c9bffa` / v714 · origin `2c9bffa` / v714 via `git ls-remote`)
- **DELTA — Fable shipped R5 (v714)** since last Grok scan (was at v713). HEAD **==** origin (push clean; used `ls-remote` per Fable note).
- `tv.test_agent` → **16/16 green**. Stub present. `D2R_BUILD.id` = **`v714`** ✅ (note text still says R1–R2 only — cosmetic lag, not a badge split).
- Dirty worktree (not a new commit): `M tests/v712_tv_board.spec.ts` — either mid-edit or uncommitted R5 tail; Fable should land or drop before next push.
- Live re-test still **no human verdict** in README/log (README section exists with *expected* next-run copy only).

### Closed this cycle (evidence)
- ✅ Push/stamp stack through **v714** (`ls-remote` = `2c9bffa`)
- ✅ Board latency meter + cap-visible asserts (R5 + `4.2s avg` / cap mock in `v712_tv_board.spec.ts`)
- ✅ Boot warm-up turn (`vision warm — session ready in Ns` in agent)
- ✅ Port-in-use + tiny-capture permission guards · README “Last live verdict” section
- ✅ Prior P0/P1 from R2–R4 remain closed

### P0 — open now (only real gate left is human)
1. **Live re-test (Konyo, bare Terminal — not nested Claude):**  
   `python3 tv/tv_diablo.py` → TV·D ON.  
   Expect: `⚡ boot` → `vision warm — session ready in Ns` → pause → settle → warm read (~2–10s, not 180s) → board `n/120 · Xs avg` → brain lines on skip/cap.  
   Write real ✓/✗ + measured times into README “Last live verdict” + a new log round.
2. **Land or discard dirty `tests/v712_tv_board.spec.ts`** so main stays ship-clean.

### P1 — night depth (versions 6–10 still open on the goal)
3. **Warm-up unit test** — assert boot path emits warm/skip event when `TV_CLAUDE_BIN=fake` (suite still 16; warm-up is production-only today).
4. **Worker 8-turn restart under load** — already faked; optional stress that 9th read still returns names after recycle.
5. **Windows / cousin path** — PNG twin + worker; after Mac live green.
6. **Cosmetic:** refresh `D2R_BUILD.note` to mention R3–R5 (worker · warm-up · v714) so view-source matches the night story.

### P2 — after live green
7. If first real read is still cold despite warm-up line, capture whether warm thread finished before first settle (race).
8. If warm reads regress >30s, log raw `ms` samples + worker vs one-shot path taken.
9. Cousin Windows full e2e.

### Explicit non-goals (unchanged)
- No forge/funi/fsets engine rewrites · no API keys · no fabricated names · don’t loosen settle to chase volume.

### Suggested R6 shape (Fable can rename)
**v715 — live-proof prep + warm-up TDD + clean tree**  
- Commit/drop dirty board spec · warm-up event unittest · optional note polish · **block on Konyo live** before more features.

### Grok’s next move
Keep 15m scans; always `git ls-remote` for push truth; only escalate on red tests, new commits, or a logged live fail.

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
