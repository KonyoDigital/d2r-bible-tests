# The fast gate (v3847)

Elad, 2026-10-30 15:29: changed-file gates plus a core set, a full run when a shared file moves, a nightly full run,
the hook never skipped.

## What a push runs now
* `hooks/pre-push` stage **fast gate set** = `run_gates.py --fast` (it used to be a ~65 min manual step, outside the hook).
  * **core** `tv/fast_core.txt`: js-syntax, test_agent, test_control, every regression law tagged v3800+, the newest 45
    laws, and the fast-gate law itself (~78 gates).
  * **+ changed**: every gate whose law file changed, or whose law names a changed file by basename or module stem
    (an `import x` is a name). The import closure is NOT followed: 735 laws import control_app.py, which imports
    most of tv/, so the closure would pick ~650 gates for any tv/ change.
  * **shared -> every gate** (`--full`): bible.html, tv/control_ui.html, tv/control_app.py, tv/gate_ledger.py,
    tv/fast_gates.py, tv/fast_core.txt, hooks/pre-push, and tv/run_gates.py outside its `GATES = [...]` list.
  * a run_gates.py change that only ADDS or EDITS registry entries (10 of its last 12 commits on main) runs those
    entries + core + changed. A dropped entry runs every gate. A selector that throws runs every gate.
* the hook's own Chrome-free suite (test_agent) starts at the top, beside the browser stages (max 1 Chrome kept).
* CI still runs every gate, sharded, after the push; `tv/nightly_full_gates.sh` runs every gate on origin/main at
  03:30 (launchd plist in tv/launchd, NOT loaded until Elad OKs it - it uses the one Chrome at night).

## PROPOSED, NOT ENABLED - a region rule for the three shared files
Most versions touch a shared file (last 120 main commits: bible.html 42, control_app.py 24, control_ui.html 19),
so under the rule above most pushes still run every gate. Proposal:

* mark regions in each file with `/* GATE-REGION: d2jsp */ ... /* /GATE-REGION */` (Python: `# GATE-REGION: ...`);
  `tv/gate_regions.json` maps each region name to its gates (seeded from the laws that read the region's ids,
  classes and function names).
* a diff whose every changed hunk lies inside named regions runs core + those regions' gates; any hunk outside a
  region (or touching a marker line) runs every gate.

Tradeoff:
* **gain**: a d2jsp-only or overlay-only edit to bible.html would run ~100-150 gates instead of 1318
  (est. 6-10 min local instead of ~65).
* **risk**: these files are one global scope. CSS cascades, shared helpers, globals and event handlers cross
  regions, so an edit "inside the d2jsp region" can break the Vault and no region gate would see it before the push.
  The map is hand-kept and drifts as code moves. Mitigations: CI and the nightly still run everything (a miss
  shows up within the hour on CI, never later than the next night), a law that every region has >= 1 gate and every
  marker is paired, and a region edit to anything global (`:root`, `window.`, top-level `function` used outside
  the region) escalates to full.
* **Grok CLI's alternative (#230 6524714814), preferred**: no hand-drawn markers. Take the line ranges each gate's
  trace already reads in the shared file, widen each to its enclosing function/rule block, and run a gate when a
  hunk lands in its widened ranges. The map comes from the trace, so it cannot drift by hand; a hunk no gate's
  range covers (new code, top-level code) runs every gate, never zero. Same cross-region risk as above, same
  CI/nightly backstop; it costs a trace-range store in the ledger and a law for it.
* in short: faster pushes on the files that change most, paid for by "caught at CI/nightly, not at the push" for
  cross-region breaks. It needs Elad's OK first.

## The 189 gates the ledger cannot record (1983 of 4153 measured CI seconds)
They start git, sips, Chrome, vm_stat or a python child the trace cannot follow, or they read a git-ignored file,
so `--changed` reruns all of them every time. Options, safest first:
1. **key on the whole tracked tree** (what suite_verdict does): carry only on byte-identical trees. Safe, but it
   only helps a re-run of the same commit (e.g. hook after the procedure run), never the next commit.
2. **declared inputs**: `Gate(..., inputs=["tv/x.py", "bible.html"])`, carry when the declared paths' blob hashes
   are unchanged. Fast, but an under-declared input is a silent stale PASS, so each declaration needs a red-proof
   that touching an undeclared file it really reads is caught (trace what we can + the declared rest).
3. **follow the children**: export the trace env to python children (15 gates) and treat `git`/`sips`/`vm_stat` as
   pure tools whose inputs are their argv files (~140 gates). Most of the win; needs a ledger change and its law.
Recommended: 3 for git/sips/vm_stat/python children, 1 for the Chrome gates. Not in this commit.
Grok CLI's review agrees with the rule kept here: an untraced gate carries only on an explicit input list it is
red-proved against, or it runs. Never a guessed hash. A gate the selector cannot map (no law file) always runs.
