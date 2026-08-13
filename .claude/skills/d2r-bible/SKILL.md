---
name: d2r-bible
description: "Rules for working in the D2R Farming Bible repo (~/d2r_bible_tests) that are not visible from the code — a push to main PUBLISHES the live site, a version means four stamps and a ship, bible.html has a second writer (Claude Desktop), his grail ticks are testimony rather than state, the game is Reign of the Warlock rather than vanilla, and the 30-gate set fails by going silent. Use when editing bible.html, tv/*, tests/*, functions/* or hooks/*, bumping a version, running or adding a gate, deploying, or touching anything that reads or writes his ledgers."
---

# The D2R Farming Bible repo

A single-file HTML app (`bible.html`, ~41,700 lines), a desktop console beside it (`tv/`), ~380
Playwright spec files, and a live site he uses while playing. The code is readable. What is not
readable from the code is everything below — each rule here cost something to learn, and the
evidence travels with it.

Related carved skills, which this one does NOT repeat: [[test-venue]] (where tests may run),
[[chrome-cdp-mac]] (driving Chrome here), [[process-port-discipline]] (his ports, and why
`pkill -f` is banned), [[copy-drift]], [[unknown-stays-unknown]].

---

## 1. A push to main PUBLISHES. There is no separate deploy step.

`git config core.hooksPath` is **`hooks`** — a *tracked* directory, not `.git/hooks`. So the hooks
are code: editing one is a change other machines receive, and a hook is not a local convenience.

`hooks/pre-push` does three things before the ref moves:

1. runs gates (visual-lock, boss-portrait integrity, and a Playwright smoke of **10 named specs**),
2. and then, for `refs/heads/main` touching `bible.html` / art / `functions/` /
   `tv/install-tvd.ps1` / `deploy.sh`, **runs `deploy.sh` and publishes the live site**.

**Consequences to hold in your head before typing `git push`:**

- A push that touches `bible.html` is a **release to a site he opens on his phone mid-game.**
  Docs-only and `tv/`-only pushes skip both smoke and deploy — which is why `tv/` work can be
  pushed freely and `bible.html` work cannot.
- The deploy MUST carry `functions/api/intake.js`; `deploy.sh` owns that copy. A deploy that
  drops it leaves the site up and the AI intake dead — a half-live state that looks fine.
- **A Cloudflare Pages secret needs a REDEPLOY to take effect.** Setting it in the dashboard
  changes nothing until the next publish.
- Never `--no-verify`. It skips the gates *and* the publish, so the repo and the live site
  silently disagree from that moment on.

⚠ The smoke's 10 specs are the ONE sanctioned local browser run, and they exist because commits
used to land on main unverified. Everything beyond those 10 goes to CI — see [[test-venue]], and
note the measurement behind it: `test_control` takes 19.5 s idle and **565.9 s** while a local
suite is running, which is how a legitimate push got refused.

---

## 2. A version is FOUR stamps, and it means a SHIP

`python3 tv/bump_version.py v<N> <name> <note>` — the only correct way. It writes exactly four
surfaces (`tv/bump_version.py:64–94`):

| surface | what reads it |
|---|---|
| `bible.html` → `D2R_BUILD.id` | the page, and every `?v=` cache-buster it builds |
| `tv/control_app.py` → `"ver"` | the console's own status API |
| `tv/tv_diablo.py` → `VERSION` | the agent process |
| `tv/WINDOWS_SHIP.json` | the Windows machine |

Hand-editing produces a **half-bump**, and the gate refuses the push. `kai_check`-style
comparisons ask three questions that must agree: the tree, the served page, and the *running*
process.

**A `vNNNN` label means the four stamps MOVED.** Use `fix:` / `test:` / `ci:` for everything else.
Evidence: five test-only commits were labelled `vNNNN`, his console then read five ships behind
what the repo said, and he asked about it twice. A version number is a promise about what he is
looking at, not a commit counter.

Whole numbers only. Batch 3–4 versions per push — the gate cost is per-push, not per-version.

---

## 3. `bible.html` has a SECOND writer

Claude Desktop edits this file too. **Read `bible.html.EDIT_LOCK` first; if it is held, do not
write.** Absent = free. This is the only file in the repo with a lock, because it is the only one
two agents both want.

At ~41,700 lines it is also the file where a careless whole-file rewrite is unrecoverable. Prefer
targeted edits; never regenerate it wholesale.

---

## 4. The cascade decides, not your edit

**Last *declaration* wins — CSS and JS alike.** `.hero-title` had FOUR rules; editing the first
match changed nothing and looked like a broken browser. A twin `filterSilver` definition cost a
whole pane.

⚠ **The cascade is per-PROPERTY.** The winning rule for `color` can leave an earlier rule's
`white-space: nowrap` still governing, so "I found the winner" is only true for the property you
checked.

**Method:** count the declarations for that selector, edit the one that wins, and prove it with
`getComputedStyle` — not by reading the file.

---

## 5. His browser is pinned to an old build more often than you think

His tabs hold stale `?cb=` / `?v=` URLs. **Check the URL he is actually on before diagnosing
anything he reports.**

⚠ `no-cache` cannot evict what is already cached under the previous `max-age`. A fix that is
correct in the repo, correct on the CDN, and invisible to him is the normal shape of a bug report
here.

---

## 6. His ledgers are TESTIMONY, not application state

- **There is no unfind in Diablo.** Chronicle applies are **ADDS ONLY** — merge-max, dated,
  undoable — and go exclusively through `window.chronicleApply()` (`bible.html:36217`), the same
  function his hand-tick uses, so they inherit its rules.
- **`d2r_grailUnfound` is USER TRUTH.** Only he may overrule his own un-tick. Nine un-ticks
  contradict the game's own data and **all nine stay**, because a tally that argues with him is
  worth less than one that records him. His uniques total is ~248, never 236.
- ⚠ A **resized crop hallucinated item names**. Judge a row only at native resolution.
- **Fixtures never touch live data** — guard the fixture, not the call site, and run the suite
  twice. `TV_HIST`, `G5_BUDGET_PATH`, `G5_STATS_PATH` and `TV_STUB_MANIFEST` exist so a guard can
  point somewhere harmless; use them rather than trusting a test to behave.

---

## 7. The game is Reign of the Warlock

He plays **RotW**, not vanilla D2R. Runewords come from **diablo2.io v3.2**; the AB wiki is the
RotW authority. A "correct" vanilla fact can be wrong here, and that is not a data bug.

---

## 8. The gate set is the verdict — and its failure mode is SILENCE

`python3 tv/run_gates.py` runs **30 gates** and returns one verdict. CI runs the same file, so the
two cannot drift (they did: CI hand-listed 7 while the file knew 26).

- `TestNoOrphanSuite` fails on any `tv/test_*.py` missing from the list — so **a new suite must be
  registered in `run_gates.py`**, and a runnable check that is *not* a `tv/test_*.py` can never be
  caught by it. `robot_smoke` was nearly dropped for exactly that reason.
- **A gate that always skips is the same defect as one that never runs.** `js-syntax` skipped for
  ~220 versions (Chrome will not answer `--dump-dom` over loopback on his Mac);
  `test_button_matrix` skipped whenever his console happened to be closed. Both now remove the
  dependency instead of tolerating it — `node --check`, and booting a private `control_app` on an
  ephemeral port (**never :17772, his live console**).
- **The host machine is a fixture.** Consolidating CI onto the full set produced four reds and
  **zero regressions** — every one a test asking the host (his footage, his Grok login, his Claude
  CLI) instead of its fixture. See [[feedback-blind-fixture-green-gate]].
- Regressions are logged in repo-root `BUGS.md` as `REG-NNN` (218 entries and counting).
- Suite-tail fatigue sets in past ~140 tests per worker; `--shard` splits by **file count, not
  duration**, which is why heavy sims live in the `slow` project.

**Never trust a green gate you have not seen go red for the reason you care about.**

---

## 9. Things that are LOCKED — change only if he says so

- **AI intake: Sonnet + crop.** Calibrated, and marked do-not-change.
- **`visual_lock_invariant.py` / `LOCKED_TYPE_SYSTEM.md`** — font weights, structure, spacing and
  line-height on `bible.html` and `tv/control_ui.html` are gated on every push.
- **Boss portraits must be the images a human actually opened**, and `BOSS_PORTRAIT` must serve
  exactly those files. `pit` is not a boss; `pindle` has no portrait *by decision*.

---

## Where this skill is thin

- The **art pipeline** (CASC extraction, HD routing, corrupt `base_` assets) is documented only in
  memory files, not here — it changes rarely and is better read fresh when needed.
- The **Windows machine's** half of the workflow is covered in `windows_machine_setup.md`; only its
  version stamp appears above.
- Section 6's list of isolation env vars is the set observed in use, not an audited inventory —
  check `tv/` before assuming a given fixture has one.
