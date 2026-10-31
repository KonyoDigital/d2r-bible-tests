# FAST_GATE.md: how a version ships in under 20 minutes

v3847 spent more than 5 hours on reruns: full sets after every red, and proves restarted on every CI fix. These rules
replace that. Every ship note reports the time of each stage and the TOTAL gate wall time, including reruns.

## The order of a ship
1. **Pre-check locally, first.** Run `python3 tv/heart2.py --changed-gates` and run only those gates
   (`python3 tv/run_gates.py --only …`), plus the overlay, visual and test_control laws for any selector you touched.
   Fix reds here. At the same moment, push the branch to `ci/*` so CI starts early.
2. **Run the fast set** (`run_gates.py --fast`): the core set plus every gate whose law reads a changed file.
   A full set runs only when a shared input moved (run_gates.py, heart2.py, gate_ledger.py, BLUEPRINT.md,
   bible.html, control_ui.html). Say why in the ship note.
3. **After a red, rerun only the reds:** `run_gates.py --rerun-failed [--only <gates the fix touches>]`.
   The last run's reds are kept in this worktree's git dir. The ledger banks every pass, so the bump inherits them.
4. **Prove once,** on the final commit, after CI is green: `heart2.py --prove --changed`, never the full set.
   Do not restart it for a CI fix that does not touch a proven law; passed proofs are reused.
   A clean-wave ALREADY RED gets a root cause. It is never blessed.
5. **Push through the hook** (never `--no-verify`). On a red: find the root cause, fix it, pre-check the failed and
   touched gates locally, then retry. A flake that is green 3 of 3 times on its own may be retried once without a
   code change, and its root cause is owed in the next version.
6. **Census after the push:** the touched proofs only. The full census runs nightly.

## Nightly
`tv/nightly_full_gates.sh` runs from launchd (`tv/launchd/com.konyo.tv-nightly-gates.plist`) at **04:00 IDT** and
runs every gate on origin/main. It skips, logs and exits 75 if a gate run, prove or census, or push hook is running,
or if less than 15 GB is free. It uses at most one headless Chrome.

## Hygiene
- Commit the tree before any gate run. A dirty `tv/.self_arming.jsonl` stops banking
  ("proved on uncommitted …").
- A fresh worktree needs no hand-copied state. The render sandbox seeds its own census (v3848).

## Lessons
- v3847: a cold `--only` child run mapped all ~1320 gates (>200 s), so test_control timed out in prove
  sandboxes (e3a70d0b6).
- v3847: the J9 terror-zone demo flake was a stale /api/tz answer painting over a newer one (fixed in v3848).
