# 👻 GHOST MODE — the Console Time Machine (Konyo arc, 2026-07-22)

> Konyo: "i thought it was just like a shell on top of the shell... like a TIME MACHINE. you click [it] and it
> ghost shells the ENTIRE console and then everything can be tracked back... i dont want anything within the
> console changing on the regular — only the shell time machine itself as an ADD-ON on top of it... make sure
> we can remove it. that button is the console's DEBUGGER SWITCH on top of the shell. lets go ship it 50+ rounds."

## THE VISION
A **debugger SWITCH** on the console — 👻 GHOST MODE (aka DEBUG MODE). Flip it ON → the ENTIRE real console
freezes + dims into "the past" (ghosted) with a macOS-Time-Machine-style scrubber → drag it and the whole
console flies back through time. Flip it OFF → the overlay VANISHES → the live console is exactly as it was.

## IRONCLAD ARCHITECTURE RULES (Konyo, non-negotiable)
1. **PURE ADD-ON OVERLAY.** The live console's code + regular behavior NEVER changes. No re-plumbing tabs, no
   "rewind-aware" components, no touching how tallies/vault/forge/scanning normally work. GHOST MODE is a
   SEPARATE overlay layer that reads history and PAINTS a ghost render itself.
2. **ONLY ON WHEN TOGGLED.** Inert until the switch is flipped. Flip off = overlay removed, ZERO trace, console
   100% unchanged (it just had a ghost floating over it).
3. **TRUTHFUL — never fake.** A debugger that shows a guessed past LIES to you. Rewind ONLY what real data backs;
   label everything else honestly as "approximate" or show current-state. No fabricated exact numbers.
4. **REMOVABLE / SAFE.** Restore point `restore-v1229-preghost` (@ v1229, all-green) exists local + remote.
   Roll back anytime: `git reset --hard restore-v1229-preghost`.

## TRUTHFUL-SCOPE MATRIX (from forensic-rewind, evidence-based — build to this)
### ✅ REAL / rewindable TODAY from existing data:
- **SCAN sessions** (frames/reads/engines): sessions.jsonl (1231 rows, all ts'd) + frames/hist/reel_<sid>/ (f_<epochMs>.jpg) + kai_report.json (closedAt, firstSeenTs). Full timeline.
- **GRAIL progress** (F·Uniques + F·Sets): `d2r_foundLog` = {itemName: dateStamp}, parseable via _flogTime()/_flogSort() (already timeline-treated). grail-at-T = count(name for name,stamp in foundLog if parse(stamp)<=T). EXACT for the common found-once-kept case (un-tick deletes the stamp = loses found→unfound→found; acceptable).
- **FORGE "make now"**: purely derived from stash (no independent store) → rewinds free iff tallies rewind.
### ⚠️ APPROXIMATE ONLY (label honestly, NEVER fake):
- **TALLIES** (rune/gem/material): current-state maps overwritten by persist(); AI-intake deltas ARE ts'd
  (sessions.jsonl intake rows + d2r_tvdTallyLog) but manual +1/-1 (adjustRuneStash/etc) + clears write NO
  journal → exact only if session was AI-intake-only; else replay is silently wrong. Show approx or current.
- **VAULT**: additions ts'd (d2r_intakeLog journalAdd) but removals (owned.delete ×7 sites) NEVER journaled →
  monotonic upper-bound only, not the true set. Label approximate.
### 🔌 To make tallies/vault EXACT later (ONLY if Konyo okays touching record paths — purely additive):
a `console_snapshot` event on each state-mutation (adjustRune/Gem/Material, clears, owned.delete ×7) recording
full {runeStash,gemStash,materialStash} + owned. NOT doing this without Konyo's explicit go (violates rule #1's spirit).

## THE BUILD (control_ui.html = the console shell polish-ui-2 owns; reads existing endpoints + same-origin bible logs)
- **KEEP the Engine Room** cockpit AS-IS — Konyo: "leave it, it's a different set of tools." GHOST MODE is separate.
- Round 1 = THE SWITCH + THE GHOST-SHELL CONTAINER: a 👻 GHOST MODE toggle; ON → dim/freeze the whole console
  into past-mode + a Time Machine scrubber overlay; OFF → gone. Diagnose the real console structure first
  (what IS "the console", where the overlay attaches to ghost-shell it). Container right BEFORE rewind depth.
- Then progressively wire the TRUTHFUL rewind: scan replay → grail-by-date → forge; label tallies/vault approx.
- Then polish: the Time Machine VISUAL (starfield-recede feel), scrub UX, per-moment detail, cohesion, ~50 rounds.

## CADENCE (Konyo-workflow)
polish-ui-2 owns control_ui.html; Fable gates every round (selective commit control_ui.html + stamps; smoke on
bible/spec; NEVER full Playwright on Mac); version-per-round; detached push → restart console AFTER push demo
hook clears (lesson from ER arc); don't restart console while Konyo's scanning (supervisor pause-flag). Grok
third-eye via dossier every few rounds. Every round: 0.00px + closeability + bulletproof-open held, 125+ tests
+ demo 7/7 green, GHOST MODE off = console provably unchanged.

_The console's Time Machine. A debugger switch on the shell. Truthful, removable, real-time. 50+ rounds._ 👻🧠🖥
