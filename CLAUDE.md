# Working in this repo — read this before the first tool call

> ## ⏩ RESUMING? READ `RESUME_HERE.md` FIRST.
> It carries the exact next action, what is committed but unpushed, what the gate refused and why,
> and the three files holding the open work (`OPEN_WORK.md`, `OPEN_WORK_NOTES.md`, `TASKS.md`).
> Written 2026-09-02 after a forced restart, so a new session starts where the last one stopped.

This file loads automatically for every session in `~/d2r_bible_tests`. It exists because on
2026-09-01 Konyo had to say, six separate times, that carved skills were not loaded — while a
SessionStart hook that names them was already firing. **A hook is advisory text and depends on the
model choosing to act on it. This file is context. It arrives whether anyone remembers or not.**

> *"why do i have to keep on telling you these same things when i start you up… its like your a
> brand new person."* — 2026-09-01

---

## 1. LOAD THESE SKILLS BEFORE TOUCHING THE WORK — not at verification time

**Always, in this repo, no exceptions.** Loading a carved skill at verification time only shapes the
check; loading it at step 0 shapes the build.

| Skill | Why it is mandatory here |
|---|---|
| **d2r-bible** | a push to main PUBLISHES the live site · a version is four stamps · `bible.html` has a second writer · his ticks are testimony · the gate set fails by going silent |
| **test-venue** | browser/Playwright suites run on GitHub CI, **NEVER on his Mac** — `test_control` takes 19.5 s idle and **565.9 s** while a local suite runs |
| **regression-guard** | before saying anything shipped or passed: a sample is not a verdict, a skip is not a pass, pin the LAW not the number |
| **the-unjoined-end** | two halves each built right and never joined — this repo's single most repeated defect |
| **unknown-stays-unknown** | `0` = measured-and-zero, `None` = nobody looked. Collapsing them is a lie with no author |

### Load the moment the work turns into one of these — the territory widens mid-session

| The moment | Load |
|---|---|
| ANY UI, layout, screenshot, "how it looks" | **visual-regression-detector** · chrome-cdp-mac · grok-second-eye |
| building ANY engine, lane, filter, gate or analyzer | **heart-first** — the corroborator/watchdog/eagle-eye/doctor are built WITH it, never after |
| a guard that greps SOURCE text, or a test reading a file | **source-reading-guard** |
| a number he acts on, a default, a freshness badge | unknown-stays-unknown · **stale-reading** |
| driving a UI HE also has open | **borrowed-surface** |
| starting/killing a server or a port | **process-port-discipline** — `pkill -f` is BANNED, kill by port |
| a skills/install/vendor/synced dir, or "the fix did not take" | **copy-drift** |
| after ANY `git push`, or a version stamp moving | **review-after-ship** (MANDATORY) |
| finishing a fix, before saying "done" | **sweep-dont-ask** — sweep for siblings of the same defect |
| a claim can only be settled by looking at HIS screen | **human-eyes-harness** (project skill) |
| before launching ANY Workflow / fan-out | **workflow-topology** + the cost gate |
| finishing serious work | ship-skill · self-improvement |
| 3+ scars piled up in one territory | carving-skill |

⚠ **`d2r-bible` and `human-eyes-harness` are DIRECTORY-SCOPED to this repo.** The Skill tool answers
"Unknown skill" from `~`. That is not absence — read `.claude/skills/<name>/SKILL.md` directly.

---

## 2. THE KONYO WAY — how this repo has been worked for six days

- **Fix it, don't offer it.** In-territory, broken, and I know the fix → do it and report in past tense.
- **Verify the thing, never a proxy.** A passing test is not a look. A rect is not a picture.
- **Every UI change is verified on real pixels**, then shown to a DIFFERENT model family to refute.
- **A gate never seen RED is measuring nothing.** Prove red before trusting green.
- **The contradiction IS the finding.** Two checks disagreeing is the result — publish both, never average.
- **Suspect the instrument first.** The count is usually the tell.
- **Silence is not evidence.** An unreachable eye is an EMPTY SEAT, never agreement.
- **An inherited claim is not evidence** — including a claim from my own earlier prompt.
- **Batch 3–4 versions per push**; the gate cost is per-push, not per-version.
- **A `vNNNN` label means the four stamps MOVED.** Use `fix:` / `test:` / `ci:` for everything else.

---

## 3. THE TASK LIST IS A FILE, NOT A SESSION

`TASKS.md` in this repo, plus GitHub issues, plus the terminal task panel. **A list that lives in a
session is not a list** — on 2026-09-01 the whole thing was lost on a restart because the memory
queue had saved the numbers (`#135 · #143 · #159`) and not what they meant. 993 of his turns had to
be pulled back out of a 688 MB transcript.

**When he asks for something that will not finish in one breath, it goes in `TASKS.md` AND as a
GitHub issue BEFORE the work starts.**

---

## 4. THE GROK BOT HARNESS — he is the eyes, Claude is the code

The channel is GitHub, and it is **looped every 10 minutes leaving messages**. Poll it.

| | Claude | Grok Bot |
|---|---|---|
| read the code, stores, journals · ship a gated fix | ✅ | ✗ |
| **see his live console · act as him** | **✗** | ✅ |

- `gh #179` — backend queue (`GB-B-n`) · `gh #180` — live/eyes queue (`GB-L-n`)
- A brief must carry a **refutable claim**, keep observation separate from conclusion, and treat
  **UNKNOWN as a first-class answer**. Plus a don't-touch list, every time.
- ⚠ The repo is **PUBLIC**. Never put install ids, hostnames, tokens or `/Users/konyo` paths in a brief.

---

## 5. HARD RULES — each one cost something

- **Never `--no-verify`.** It skips the gates *and* the publish, so the repo and the live site
  silently disagree from that moment on.
- **Never `git checkout <file>` while a fleet is running.** Agents write unstaged and edit via Bash,
  so there are no Edit calls to replay. Measured 2026-09-01: it destroyed a completed build.
- **⚠ NEVER `cp -R tv/` OR `cp -R` THE REPO. Use `python3 tv/safe_copy.py <dest> [subdir]`.**
  `tv/` carries the reel store (**5.8 GB** of his footage). On 2026-09-03 three review agents each
  copied it to `/tmp` for a sabotage test — **20.5 GB in four minutes** onto a volume with ~9 GB
  free. It hit ENOSPC, and then *every Bash call in the session failed before it ran*, because the
  harness could not create its own output file: nobody could run `df`, let alone `rm`. The prompt
  that said "work on copies under /tmp" was the defect — reasonable words, catastrophic in a repo
  holding gigabytes of footage. `safe_copy.py` excludes `frames`, `.render_shots`, `.git` and
  `node_modules`, refuses above 400 MB, and refuses any copy that would leave under 4 GB free.
  Measured: `tv/` is 5,865 MB; the safe copy is **43.7 MB**.
- **Never `pkill -f`.** It cannot tell his process from mine. Kill by port. `:17772` is his live
  console, `:9222` his Chrome, `:9223` TradingView; scratch goes on `:9224+` and `:179xx`.
- **`timeout` is NOT installed on this Mac.** Use `perl -e 'alarm N; exec @ARGV'`.
- **Read `bible.html.EDIT_LOCK` before writing `bible.html`** — Claude Desktop writes it too.
- **The pre-push gate grades the WORKING TREE, not the commit.** Do not edit mid-push.
- **`git push | tail` reports tail's exit status.** Confirm `origin/main` actually moved before
  claiming anything shipped.

---

## 6. WHERE THE REST LIVES

- **Persistent memory:** `~/.claude/projects/-Users-konyo/memory/` — 204 files, git-backed to a
  private repo, daily 09:30. `MEMORY.md` is the index; `open_queue.md` is the work queue.
- **Founding rules:** `~/.konyo-workflow/SCARS.md`
- **Regression log:** repo-root `BUGS.md`, as `REG-NNN`
