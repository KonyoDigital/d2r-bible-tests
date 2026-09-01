# HANDOFF — the swallowed-exception ratchet, and the repos that have not adopted it

Written 2026-09-01, at v2387. For whoever picks this up — another session, another model, or
Konyo six weeks from now.

---

## 1. WHAT IS DONE, AND WHERE IT LIVES

`d2r_bible_tests` is **gated**. Nothing is outstanding here.

| piece | path | what it does |
|---|---|---|
| the census | `tv/swallow_census.py` | AST pass over every `.py`, ranks each `except` handler |
| the baseline | `baseline/swallow_baseline.json` | `rank1=74 rank2=699 rank3=707 ok=233` |
| CI | `.github/workflows/routine-m-swallows.yml` | push · PR · edits to itself |
| local gate | `tv/run_gates.py` gate #60 `swallow_ratchet` | so `pre-push` catches it before GitHub |
| guards | `tv/test_control.py TestV2387TheVendoredCensusHasNotDRIFTED` | the gate is registered, the baseline parses, any vendored copy matches upstream |

Run it by hand:

```bash
python3 tv/swallow_census.py            # the full picture
python3 tv/swallow_census.py --check    # the verdict (this is what CI runs)
python3 tv/swallow_census.py --write-baseline   # ONLY after a deliberate reduction
```

---

## 2. THE ONE THING TO UNDERSTAND BEFORE TOUCHING IT

**RANK 1 is a shape, not a defect count.** It counts handlers where a failed read hands the
caller DATA — `0`, `{}`, `[]`, `""` — so "nobody could ask" is indistinguishable from "measured
zero".

That number has been wrong three times in one day, and every correction came from **reading
sites**, never from the tool:

| claimed | why it was wrong |
|---|---|
| 537 | a grep that only saw `except: pass` and missed `except: return {}` — undercount |
| 262 | every falsy default called a lie, including the honest `return None` — overcount |
| 94 | a tuple of `None`s graded as an empty container; checked sentinels graded as claims |
| **74** | current, after both classifier bugs were fixed |

**And 74 is still not a defect count.** Twenty sites were hand-read. The grading came out at
roughly **1 in 4 solid, 1 in 3 not a defect at all**. The most common reason a flagged site is
fine: the CALLER already treats the default as failure, which no file-local pass can see —
`art/verify_boss_portraits.py:79` says so in its own docstring.

So: **never quote the rank-1 number as "N bugs".** The tool prints that caveat in its own output
for exactly this reason.

---

## 3. WHY IT IS A RATCHET AND NOT A CLEANUP ORDER

RANK 1 may **fall** freely and may never **rise**.

A gate that demanded the standing 74 be fixed first would sit red for months and be ignored —
which is the same defect as a gate that is green forever. Both have stopped carrying information.
The ratchet protects from the first push and rewards every reduction.

Two properties that are load-bearing and easy to delete by accident:

- **No baseline is NOT a pass.** An unconfigured gate that exits 0 is indistinguishable from a
  clean tree. It says UNCONFIGURED and fails.
- **The workflow proves itself on every run.** Its last step writes a throwaway file containing
  one deliberately-lying swallow, expects `--check` to FAIL, and deletes it. If that step ever
  passes silently, the green verdict above it means nothing.

---

## 4. THE DEFERRED WORK — the other repos

**Konyo, 2026-09-01:** *"dont fix the other repo though.. that for a later day in the future after
we perfect diablo first repos"*

It was **built and proven in both, then backed out untouched.** Both trees are clean of it. This
is a decision, not a gap.

Measured while it was in place (real numbers, worktrees and snapshots excluded):

| repo | handlers | RANK 1 |
|---|---|---|
| `kai-achilles` | 475 | **34** |
| `achilles-revival` | 2,834 | **149** |
| `predicter` | 12 | **0** |

> ⚠ `achilles-revival` was first reported as **561**. That was wrong — it was scanning
> `.claude/worktrees/` and `.snapshots/`. The shipping-code number is **149**. The skip list is
> now `backups`, `.snapshots`, `worktrees`, `.venv`, `venv`, and the output NAMES what it skipped.

### When the day comes, it is three files per repo (~15 min, already rehearsed)

1. **Vendor** `tv/swallow_census.py` → `<repo>/tools/swallow_census.py`, replacing the module
   docstring with a header naming the upstream and stamping `UPSTREAM_DIGEST` (sha256[:16] of the
   upstream file). It is vendored rather than imported because CI checks out ONE repo and a
   cross-repo fetch is a second thing that can fail.
2. **Baseline**: `python3 tools/swallow_census.py --write-baseline`
3. **Workflow**: `.github/workflows/swallow-ratchet.yml` — copy the shape from
   `d2r_bible_tests/.github/workflows/routine-m-swallows.yml`, changing `tv/` → `tools/`. Keep the
   self-test step; it is the reason the green means anything.

Then `TestV2387TheVendoredCensusHasNotDRIFTED` in d2r starts CHECKING those copies instead of
reporting them skipped — it already knows about both repos by name, and it compares the digest
**and** the code, because a stamp agreeing is not the same as the code agreeing.

---

## 5. HOW TO WORK THIS, PROCESS-WISE

- **One session per repo.** `hooks/pre-push` grades the WORKING TREE, not the commit. Two sessions
  on one tree produces a green verdict about bytes that are not shipping. This has bitten before.
- **Do not open a parallel session on `d2r_bible_tests` while one is running.**
- The other repos are independent trees — a session on them collides with nothing here.

---

## 6. WHAT IS STILL OPEN IN DIABLO (the real queue)

Ordered by damage, highest first. Full detail is in each task.

1. **#133 — the vault writes "he HOLDS it" through THREE doors.** Root cause found by an 11-agent
   fleet and confirmed by a skeptic. `bible.html:43816`, `:43901`, and the one nothing had traced,
   `:47021` (reached via `out.grail`, which is the grail-tick list, not the vault list). The gate
   the author already wrote at `:48630` just needs mirroring at all three. Measured: `d2r_owned`
   oscillating 162→285→…→169 while `d2r_setPieces` never moved; the 124-name diff is 124/124 in
   the sweep's `wouldAdd.uniques`. **This writes a false possession claim into his records.**
2. **#142 — a cached empty name-space wrote a wrong TIER into the append-only journal.** The
   `_kai_fullnames` half is FIXED in v2386. The remaining half is the consequence audit.
3. **#134** MINI(AUTOMATIC) autopilot · **#135** daily pick · **#136** `witnesses_required`
4. **#140** the 74 · **#141** the collapsed `kinds` field · **#143** the contradicting all-clear
   toast · **#144** the floor re-harvesting 6MB per call

**Standing instruction as of 2026-09-01:** *"no more features gonna be being built until
everything is perfected."*
