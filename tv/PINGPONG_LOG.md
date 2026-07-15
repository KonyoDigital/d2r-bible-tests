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

### Sync snapshot (Grok re-scan @ 2026-07-15 22:15 IDT · local HEAD `da10eab` / v713 · origin `92b616b` / v712)
- **DELTA — Fable shipped R2 (v712) + R3+R4 (v713)** since last Grok scan (was stuck at v711).
- Ahead of origin by **1**: only `da10eab` v713 unpushed. (v712 is on GitHub ✅)
- `tv.test_agent` → **16/16 green** (re-ran this scan). `stub_manifest.json` **present**. `fake_claude.py` + `VisionWorker` present. `tests/v712_tv_board.spec.ts` present.
- `D2R_BUILD.id` = **`v712`** (note still R1–R2 only) — **lags agent HEAD v713**.
- Live re-test (JPEG + persistent worker warm path) still **no human verdict** in the log.

### Closed since last scan (evidence)
- ✅ P0-1 stub committed (`tv/stub_manifest.json` on disk; R2 notes test no longer deletes it)
- ✅ P0-2 push through v712 (`origin/main` = `92b616b`)
- ✅ P0-3 build stamp → v712 (title/meta/`D2R_BUILD`)
- ✅ P1-5/6/7/8 + P2-9/10 per R2 ledger + suite growth 9→12→16
- ✅ R3+R4 persistent worker + latency meter (commit subject + `VisionWorker` / `WORKER_MAX_TURNS=8` / `ms` on reads)

### P0 — open now
1. **Push v713 to origin.** Local `da10eab` only; CI/GitHub still advertise v712 without the worker.
2. **Bump `D2R_BUILD` / title / meta → v713** (or next ship id). Runtime stamp is still v712 while agent is v713 — same split-brain class as pre-R2.
3. **Live re-test gate (Konyo, bare Terminal):**  
   `python3 tv/tv_diablo.py` → TV·D ON.  
   Expect: `⚡ boot` · transport JPEG line · on pause settle → **warm** read (target ~2–10s after first; not 180s) · `ms` on read records · board `n/120 · Xs avg` · brain never silent on fail (worker kill → one-shot fallback).  
   Log capture/settle/vision/latency under a new round. Still the only P0 that needs a human.

### P1 — next TDD / night depth (toward 10 versions)
4. **Board spec for latency meter** — mock `/state` with `reads[].ms` and assert the READS chip shows avg seconds (v712 board suite doesn’t cover the new meter yet).
5. **Worker fallback e2e in brain log** — when fake_claude is `junk`/`slow`, assert `/state.events` gets a `cap` (or equivalent) and a successful one-shot path still can complete (if wired); don’t leave CRT on READING.
6. **README last-live-verdict one-liner** — still open (P2-12 from prior list).
7. **Windows path parity** — still open; don’t block Mac night.

### P2 — after live green
8. Watch **first-read cold** vs **2nd+ warm** latency in a real session; if cold is still brutal, consider a boot-time worker warm-up turn (empty/tiny prompt) so the first loot pause isn’t the cold start.
9. Confirm **8-turn restart** doesn’t drop a read mid-farm (fake covers restart; live is the proof).
10. Cousin Windows: PNG twin + `TV_CLAUDE_BIN` / worker on Win — after Mac live is green.

### Explicit non-goals (unchanged)
- No forge/funi/fsets engine rewrites · no API keys · no fabricated names · don’t loosen settle to chase volume.

### Suggested R5 shape (Fable can rename)
**v714 — stamp + push + board latency TDD**  
- `D2R_BUILD`→v713/v714 · push `da10eab` · extend `v712_tv_board.spec.ts` (or v714) for `ms` avg meter · leave live re-test for Konyo.

### Grok’s next move
Re-scan every ~15m; mark P0 push/stamp when origin/HEAD/`D2R_BUILD` match; escalate only on red tests or a logged live fail.

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
