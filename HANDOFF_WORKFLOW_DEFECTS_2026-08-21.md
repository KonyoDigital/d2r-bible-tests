# HANDOFF — defects in the Konyo workflow engine, found by running it

**For a fresh session.** Nothing here is about `d2r_bible_tests`; it is about
`~/.claude/workflows/konyo-workflow.js`. Konyo asked for this because the run below produced good
findings *and* three engine-level problems that will repeat on every future run until fixed.

**The run:** `wf_7ad48f08-5dc`, 2026-08-21, gate-hardening sweep over six named defect classes.
1h 17m, **24 agents, 4.37M tokens**, verdict `BLOCKED`, `shippable: false`.
Journal: `~/.claude/projects/-Users-konyo/7acba61c-.../subagents/workflows/wf_7ad48f08-5dc/journal.jsonl`

---

## What it did WELL (so nobody "fixes" this away)

The adversarial skeptics were the best part of the run and caught a real defect I had shipped hours
earlier: my live-data canary in `tv/conftest.py` was **going red for a neighbour's reason**. With
Konyo's own console alive (pid 96342), a clean suite errored —
`A TEST WROTE TO LIVE DATA ... sessions.jsonl 1973509->1974432` — and then blamed a fixture redirect
that never happened. The skeptic proved it: run B on the identical tree, 0 errors; a 50s idle probe
with no test running showed the files quiescent; the only writer was his console. **It also ran the
sabotage proofs it was asked for** rather than asserting. That is exactly the value the fleet is for.

---

## DEFECT 1 — the agent ceiling TRIMS SILENTLY, and it trimmed a third of the job

```
"ceiling": { "cap": 24, "spent": 24, "hit": true, "complete": false,
             "trimmedFromPlan": ["tv/test_payload_reach.py", "tv/test_name_overlap.py",
                                 "tv/control_app.py", "tv/tv_diablo.py"] }
```

The brief named **six** defect classes. Class 3 (*computed and never rendered*) and class 4 (*a guard
that cannot reach its subject*) map exactly onto `test_payload_reach.py` and `test_name_overlap.py`
— **both trimmed**. So two of six classes were never swept, and the run still returned a verdict
that reads as a completed sweep with blockers.

⚠ This is the known scar `feedback_size_maxagents_before_launch` — *"it truncates from the BACK,
eating the gates"* — arriving again, one layer up: here it ate **work items**, not gates.

**What to change (suggestions, not a spec):**
- Size the plan against the cap *before* spawning, and if it does not fit, say so at launch and let
  the caller cut scope deliberately. Silently dropping the last N items is the one option that
  should not exist.
- Make `complete: false` a **blocker**, not a field. It currently sits beside `verdict: "BLOCKED"`
  for unrelated reasons and is easy to miss.
- Trimmed items belong in the human-facing summary line, not only in a nested key.

## DEFECT 2 — "2-seat adversarial panel" reported 1 cast vote on 3 of 4 items

```
"skeptics": { "used": 2, "of": 3, "floor": 2, "floored": true,
              "thin_panels": [ {"file":"tv/test_import_bound_paths.py","cast":1,"panel":2},
                               {"file":"tv/conftest.py","cast":1,"panel":2},
                               {"file":"tv/run_gates.py","cast":1,"panel":2} ],
              "thin_panel_count": 3 }
```

The engine's own docstring already names this risk: at the 2-seat floor, seat 2 is Grok, an
unreachable Grok casts **no** vote (correctly — it must never become a Claude opinion), so `cast=1`,
`refutedN * 2 > cast` lets **one Claude approval ship a change**, and the payload still says a
2-seat panel reviewed it.

It fired on **3 of 4 items** in this run. The mechanism is documented and the outcome is still
misleading, which is the definition of a live problem rather than a known one.

**Worth investigating first:** *why* was the second seat empty here? Grok unreachable, ceiling
exhausted before the seat could spawn (see Defect 1 — the ceiling was hit **during** the run), or
something else? `konyo-workflow.js:440-459` distinguishes these; the payload did not surface which.
**Do not fix the symptom until that is measured** — a null read must never be presentable as a
verdict, and "the run could not afford to ask" and "the API is down" are opposite facts.

## DEFECT 3 — LAW19 flagged a dead seam the fleet itself created

```
"LAW19 REACHABILITY FAILED — tv/conftest.py:120-198 redirect_module_path / redirect_path fixture —
 zero call sites anywhere in the repo; even tv/test_import_bound_paths.py, which prescribes it,
 uses mock.patch.object instead."
```

One agent wrote a helper, another agent's tests prescribed it, and **neither called it**. LAW19 was
right and this is the engine working — but it shows the fan-out has no way for item B to consume
item A's new API within the same run.

*(Fixed by hand in the repo: `tv/test_chronicle_chain.py` now calls it. Left here because the
coordination gap will recur.)*

---

## Cost note, for sizing future runs

4.37M subagent tokens and 1h 17m for six classes, of which four were swept. `completeness.ran:
false` because `quality: "lean"` deliberately does not buy the critic — that is correct and
documented, and it is also why nobody noticed the two trimmed classes from inside the run.

## The one-line ask

**Make an incomplete run impossible to mistake for a complete one.** All three defects share that
shape: a trimmed plan, a thin panel, and a dead seam each produced output that *reads* finished.
That is the same class the sweep was commissioned to find, occurring in the thing doing the sweeping.
