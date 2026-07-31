# HANDOFF — automatic CHRONICLE registration (Konyo's ask, 2026-07-31)

STATUS: **specified, not built.** Written at the end of a long session so the next one starts with
the survey already done rather than repeating it.

## What he asked for, in his words

> "when chronicle /menu is clicked ingame it should automatically know we are about to register and
> read and analyze the CHRONICLE lists that we didn't register yet / or some that are registered and
> some that are getting registered and updated when read by the KAI READERS.. retro and live..
> especially retro most important... SETS / and UNIQUES completes SEPARATED accordingly...
> I want to save time manually trying to update and screenshot or manually tally each one."

Three requirements, in his priority order:
1. **RETRO first** — the sealed reels already on disk contain Chronicle screens he has opened during
   past runs. Those should be swept and tallied without him replaying anything.
2. **LIVE** — opening the in-game Chronicle should put the readers into a "registering" mode.
3. **SETS and UNIQUES kept SEPARATE**, matching how the console already models them
   (`d2r_foundLog` = grail uniques, `d2r_setPieces` = set pieces; 243/403 and 108/135 today).

## What the survey found (verified, not assumed)

- **The scene vocabulary has no chronicle scene.** `tv/tv_diablo.py` recognises `stash` (16 refs),
  `gameplay` (14), `inventory` (12), `waypoint` (2). The single `"chronicle"` hit at tv_diablo.py:5937
  is unrelated — it is a field in a read payload, not a scene the classifier can emit. **A new scene
  has to be added to the classifier prompt and the scene enum before anything downstream can fire.**
- **The intake lane has no chronicle kind.** Kinds in control_app.py today: `tally`, `vault`,
  `vault-count`, `kai-funnel`, `kai-vault`. A `chronicle-uniques` and `chronicle-sets` kind (kept
  separate per his ask) is the natural extension of the existing `kind:'tally'` path, which already
  does photo→count for runes/gems/materials.
- **The retro machinery already exists** — `_kai_*` reads sealed reels frame by frame, and
  `_kai_super_select` re-reads chosen frames at higher effort. A retro chronicle sweep is a new
  consumer of that existing pass, not new infrastructure.
- **The write targets already exist and are world-routed** — `d2r_foundLog` and `d2r_setPieces` are
  in `_LP_FORKED`/`_WP_FORKED`, so anything written goes to the right world automatically after
  v1499. Do NOT write them raw; go through `LSR`.

## The shape to build

1. **Scene**: add `chronicle` to the classifier, with the two sub-shapes the game actually shows
   (Uniques tab, Sets tab). The grounder must distinguish them — a Sets screen tallied as Uniques is
   worse than no tally.
2. **Kinds**: `chronicle-uniques` / `chronicle-sets`, each returning `{names:[...], page:n}`.
3. **Retro sweep**: a Tools action ("sweep my chronicle screens") that walks sealed reels, finds
   chronicle frames, reads them, and produces a merge-max proposal — read-only until he presses
   Apply, exactly like the existing G3 Auto-route Sweep.
4. **Merge law**: **merge-max, never lower a count.** A partial screenshot (scrolled list) must not
   erase names an earlier frame proved. This is the single most important rule in the feature — his
   chronicle is 243/403 and 108/135 of real progress.
5. **Honesty**: every registered name carries its provenance (frame id + gate verdict) so the
   receipts feed can show `✓ gated` vs `live guess`, per v1506.

## Traps this codebase has already taught

- **Multi-witness before grounding** (memory: `d2r_multiwitness_corroboration`) — require 2+ agreeing
  signals before registering a name. A single OCR line is not enough; that is how the gem-grid
  mis-tally happened.
- **The accuracy gate exists** — `gatePass` / `gateReason`. Chronicle reads must flow through it, not
  around it.
- **Never trust a clean tooltip grounder** — loosening it caused a false-positive flood before.

## BOTH EYES, NOT ONE — Konyo's addition

> "we have both claude which is the most important.. but grok for me specifically i can use as a
> second pair of eyes and a different view for also these exact things! it must be also coded in so
> it is identically trying to read and retro chronicle these tallied in"

Two-lane **by design**, not Claude with an optional Grok bolt-on:

- **Claude = primary reader.** Unchanged, and the one that must always work.
- **Grok (G5) = an independent second pair of eyes**, running the SAME chronicle prompt over the SAME
  frames, live and retro, returning its own name list.

Why it matters more here than anywhere else: a chronicle screen is a **LIST**, and list reads fail by
**omission**. A name quietly missing is invisible, unlike a wrong name, which looks wrong. Two readers
over one frame turn omission into disagreement — and disagreement is detectable.

**The rule:** compare the two lists, propose the union, and SURFACE the difference rather than
silently merging it.
- both readers agree → `✓ gated` (the two independent witnesses the accuracy gate already wants)
- only one saw it → registered, marked `live guess` (v1506 provenance tags)
- counts differ → say so on the sweep card. A silent `max()` would hide the exact omission the second
  eye was bought to catch.

G5 was repaired in v1501 — it had been switched to PRIMARY and silently dark for weeks because the
console's launchd PATH could not see `~/.grok/bin/grok`. Any two-lane work must confirm
`/api/g5_status` reports `mode=primary` before assuming the second eye is reading, and must degrade
to one lane **labelled as one lane** when it is not.
