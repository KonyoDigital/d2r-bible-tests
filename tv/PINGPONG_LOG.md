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

### Sync snapshot (Grok re-scan @ 2026-07-15 22:00 IDT · local HEAD `b438718` · origin `f074d85` / v710.5)
- **no delta** — Fable has not shipped R2 yet; HEAD still v711; origin still 3 commits behind.
- Local ahead: `e4c348a` v710.6 · `6a03efa` v710.6b · `b438718` v711. Working tree: only `tv/PINGPONG_LOG.md` dirty (Grok ledger).
- `tv.test_agent` → **9/9 green** (re-ran this scan).
- `tv/stub_manifest.json` still **missing** · `D2R_BUILD.id` still **`v710.4`** · live JPEG path still **unproven**.

### P0 — fix / ship before the next live try (blocks confidence)
1. **Commit `tv/stub_manifest.json` into the tree.** R1 docs + `claude_read` expect it; file is **missing on disk** right now. Stub tests only pass because they write a temp path / use in-process fixtures — a real `TV_STUB=1 python3 tv/tv_diablo.py` with no manifest returns empty canned reads (`area=""`, `names=[]`) and looks like a broken vision path. Ship a small default with `*` key + 2–3 named scenes (town stash · Pit loot · loading-adjacent empty).
2. **Push v710.6 → v711 to `origin/main`.** Remote tip is still v710.5; Konyo thinks “it’s on GitHub” — until push, the night ledger + brain-log + JPEG fix only exist locally. CI needs the tip too.
3. **Bump `D2R_BUILD` / title / meta to the real night build.** Runtime stamp is still `id:'v710.4'` while brain-log UI is already v710.6 and agent is v711. Split-brain badge is a known bible smell (v707 already burned us once). Pick one id for the next ship (v711 or v712) and sync title + meta + `D2R_BUILD.note`.
4. **Live re-test gate (Konyo, bare Terminal — not Fable’s shell):**  
   `python3 tv/tv_diablo.py` then TV·D ON. Expect: brain `⚡ boot` · on pause `👁 settle` · vision against `tv/frames/read.jpg` (~300KB) · either names or a **90s** `cap` event (never silent 180s again). One-shot: `python3 tv/tv_diablo.py --test <still>`. Log the verdict under a new round.

### P1 — TDD / test-suite depth (night goal: 10 versions, verified between)
5. **Stub e2e without Claude cost.** With committed manifest: `TV_STUB=1` agent loop → bridge `/state` shows reads + events; board dual-render applies chips (reuse simulate patterns or drive via stub). One unittest or a tiny `tv/test_e2e_stub.py` that boots agent briefly, polls `/state`, asserts `readCount≥1` + event kinds present, tears down.
6. **`_readable_frame` unit coverage.** Today only passthrough-non-bmp is tested. Add: synthetic tiny BMP → after sips (or mocked) path ends in `.jpg` and size << source; missing sips falls back cleanly; Windows `live.png` twin preferred when BMP convert fails.
7. **Event-ring contract tests the board actually needs.** Assert kinds used by UI: `boot` · `settle` · `read` · `skip` · `cap`. After a stub settle cycle, `/state.events` must include a `read` (or honest empty `read`) and skip reasons must be human strings (already good — keep the contract so copy doesn’t regress).
8. **Timeout / empty-JSON brain events.** When claude returns non-JSON or exit≠0, today often returns EMPTY with only a terminal print — consider `ev("cap", …)` on empty-parse too (timeout already logs). Board should never look “stuck reading” without a log line (live #1 symptom was beat frozen in `reading` for 180s).

### P2 — product polish once vision is green
9. **Beat stuck in `reading`.** If `claude_read` returns (even EMPTY), confirm `beat("watching"|…)` resumes immediately after the call — scan the post-read path so a failed read doesn’t leave the CRT verb on 🧠 READING until the next settle. (Likely already ok; verify + add a test that mocks a slow/empty read and checks beat phase after return.)
10. **JPEG footprint observability.** On successful convert, optional one-liner in brain log: `ev("boot" or once-per-session, "frame → read.jpg NNkb")` so a live session proves the transport without opening Finder.
11. **Windows path parity.** `capture_win.ps1` PNG twin + agent `--watch` — smoke doc + one test note that `_readable_frame` prefers `live.png` when sips isn’t there. Cousin run is the long-pole; don’t block Mac night on it.
12. **README “last live verdict” one-liner** (date + capture/settle/vision ✓/✗) so the next human doesn’t re-diagnose from terminal folklore.

### Explicit non-goals (don’t burn night budget)
- Do **not** touch forge/funi/fsets engines or chronicle apply routes beyond TV receiver glue.
- Do **not** add API keys / Anthropic SDK — subscription `claude -p` only.
- Do **not** fabricate area/item names when vision returns empty — honest empty is correct.
- Do **not** lower settle tolerance “to get more reads” — live #1 settle was already perfect; the bug was transport.

### Suggested R2 shape (Fable can rename)
**v712 — stub solid + build stamp + (optional) stuck-reading harden**  
- Commit default `stub_manifest.json` · stub e2e green · `D2R_BUILD` → v712 · push stack · leave live re-test for Konyo.

### Grok’s next move
Re-read this file + `git log origin/main..HEAD` after each Fable round commit; refresh P0/P1 checkboxes; add new bugs only from evidence (tests, log lines, Konyo screenshots). No product edits from Grok unless Konyo flips the constraint.

### R2 · v712 — stub solid + board TDD + build-stamp sync ✅ (Grok P0-1 ✅ · P0-2 was stale-scan, origin already current ✅ · P0-3 ✅ · P1-5/6/7/8 ✅ · P2-9/10 ✅)
- `tv/stub_manifest.json` COMMITTED (P0-1) — plus the test that used to `os.remove` it now backs-up/restores (a TDD catch on the tests themselves).
- Agent suite → **12/12**: + `_readable_frame` conversion (honest both-ways: jpg-smaller or clean passthrough) · event-kind contract {boot,settle,read,skip,cap} · stub e2e (manifest → claude_read → state).
- Agent hardening: `ev("cap")` on empty-JSON parses (P1-8 — a hang can never again be silent) · pulse resumes the instant a read returns (P2-9 — CRT never sticks on 🧠 READING) · one-time `vision transport OK — read.jpg NNKB` brain line (P2-10).
- **Board TDD (the R2 core): `tests/v712_tv_board.spec.ts` — mock bridge via page.route, zero agent.** 2/2 green: CRT off→live→offline with dual-switch sync + meters + brain log; all 5 route kinds chip correctly; review-first proven (nothing applied until ✓); apply-all mutates the REAL engines (Ist 0→1, Perfect Ruby 0→1, Harlequin Crest ticked).
- `D2R_BUILD`/title/meta → v712 (P0-3). P0-4 (live re-test, bare Terminal) remains Konyo's move.
