# 🗄 THE VAULT MANAGER — his brief, in his words, and what it actually asks for

**Status as of 2026-08-23 — MOSTLY BUILT. The line below used to read "SPEC ONLY. Nothing below is
built yet."** That was true when this was written on 2026-08-21 and stopped being true overnight, and
a false status line at the top of a brief is worse than none: this document exists so the next person
starts from what he SAID, and a stale header sends them to build what already exists.
[[label-outlived-referent]]

### Built and shipped (v1989 → v2011), each proven on his own film

| | |
|---|---|
| inventory lattice + occupancy | `vault_corpus`, called from `control_app` — 22 occupied / 18 free on his reels |
| **the glimpse** | a nameless read is not an empty shelf: cells counted, names never invented (v1989) |
| **names vs cells cross-check** | `over-read` = the model named more than the panel holds — the only fabrication signal this lane has (v1994) |
| **the room map** | fixed (cube/tomes/charms) · open floor · churn — 94 of 153 frames of one reel (v1995) |
| **reel → grail tick → owned → mule** | and it SURVIVES A RELOAD, which it did not before (v1991) |
| **3-session equipment/inventory lock** | `_laneLocked` gates the mule; Harlequin Crest on equipment ticks the grail and is never moved |
| lane cards start a reel | `/api/on` had never once been called from the board (v1992) |
| shadow-reader switch | the text eye has run since v932 and had no control surface (v2000) |
| pixel evidence in the ledger | glimpsed · over-read · room · pixel-lane-down, as rows he can act on (v1996, v2004) |
| vault seal is reopenable | records the reader, so a better one looks again (v2002) |
| a complete answer may seal | a grid has no names by design — stop paying to re-read it (v2003) |
| retention planner | reports what has given up its information; deletes only with `--apply --yes` (v2001, v2006) |

### Not built, and why — none of these is "we forgot"

1. **Per-slot identity on stash personal/shared.** The 10×4 inventory is the solved panel; the stash
   grids are not.
2. **Character / mule identity from film.** v1985's ruling stands: he names the character, because
   the film cannot. Printing a name the reader never read is the fabrication this board audits out.
3. **The 1:1 console render** of equipment + inventory + stash per mule.
4. **`infer_transfer`** (inventory → stash with no names) — the arithmetic is tested, and it is
   UNPROVEN ON HIS FILM. All 31 reels were scanned; not one shows the panel changing, because none
   captured him stashing. **Missing footage, not a missing function.** One reel that films the
   inventory, then the stash, with items moved between them, activates it.
5. **REG-349** — a white `Shako` and Harlequin Crest's base line arrive as the same string, so the
   throw-out verdict inverts. The fix was built and REVERTED; it is his ruling, not a bug to guess
   at. v2011 only makes the reader's own reason visible instead of a default sentence.

Written 2026-08-21 from his message so the brief survives a compaction.

> "the whole point of this is for the ai readers to log and register exactly whats currently in my
> inventory and main character equiment (SHOULD NEVER BE TOLD TO BE MOVED its locked there) because
> and until we want to move it on my own terms its not related to the other inventory or stash."

> "this will be pretty big and complicated to do I think but its worth it eventually and im patient!"

---

## The four territories, and they are NOT the same job

| # | territory | what the reader must do | what it must NEVER do |
|---|---|---|---|
| 1 | **Equipment on his main character** | after **3+ verified reads across separate sessions** showing it has not moved, log it as his and vault it **to that player** | never suggest moving it — it is **locked there** until he says otherwise |
| 2 | **Inventory fixtures** — charms, Horadric cube, tomes | same 3+ verification, then **lock in** | never tell him to move them |
| 3 | **Inventory free space** — what he loots while farming | read it as a **chronicle** event and tally a new item (this half is already coded) | do not treat it as stash inventory |
| 4 | **Stash + shared stash** | the real vault-manager job: organise, decide keep / mule / stash / throw, **mule it to the relevant mule**, after the item is verified by **3 reads** | no throw suggestion without the higher bar; a grail name is never junk (v1903) |

## The end state he described

> "so I can see exactly where my items are visually rendering in the console and synced to my in
> game.. again slowly and thoroughly.. this is a big one."

A **1:1 render**: the console shows his inventory, equipment and stash laid out as the game lays
them out, per character/mule, and that picture is what the AI readers wrote.

## The rule that governs all four

**THREE LOOKS TO KEEP, FOUR RECORDINGS TO THROW — AND ONLY THE THROW BAR IS ACROSS SESSIONS.**

⚠ This page said "KEEP = 2 distinct sessions, THROW = 3 distinct recordings" until this
correction. Both halves were wrong — the numbers and the unit — and the heading that stood here
("THREE INDEPENDENT VERIFICATIONS, AND THEY MUST BE ACROSS SESSIONS, NOT ACROSS FRAMES") was
false for KEEP. What `tv/vault_retro.py:163-167` actually ships is:

```python
KEEP_MIN_WITNESSES = 3                    # three DIFFERENT looks agreeing — his ruling
THROWOUT_CONF_FLOOR = 0.85                # strictly above KEEP_CONF_FLOOR
THROWOUT_MIN_WITNESSES = 4                # strictly above KEEP_MIN_WITNESSES — and >1 session,
                                          # always. Raised with the keep bar so the throw bar
                                          # is never weakened relative to it.
```

And the two bars do not count the same thing. `vault_retro.gate` defaults to
`witness_field="witness"` — a **re-look** key opened by `REOPEN_GAP_MS = 180_000` (3 minutes) — so
the three looks `KEEP_MIN_WITNESSES` demands can all come from **ONE recording** in which the shelf
was examined three times, minutes apart. Only the throw bar is called with `witness_field="session"`
(`witness_noun="recording"`), so only it demands `THROWOUT_MIN_WITNESSES = 4` **independent
recordings**. "Two runs of the same unbroken screen are ONE witness" is still true of both bars: it
rules out FRAMES, not re-looks.

So the across-sessions law he described is enforced on THROW alone. His brief asks for that law
applied to a new question — *has this item MOVED?* — which is not the same as *does this item
exist?*, and needs a per-slot identity, not just a name. **If "has it moved?" is to be corroborated
across sessions, the KEEP bar as shipped does not supply that** — it would need its own
`witness_field="session"` call, and that is a decision for him, not an assumption to build on.

## What already exists to build on — measured, not assumed

- `tv/vault_retro.py` — sweep → still-runs → gate → merge-max, with the two bars and the held pile.
- `tv/stash_eye.py` — the chrome gate, the grid fingerprint, and (v1912) **the active-tab gem**, which
  reads the SELECTED stash tab structurally: 12/12 on the labelled corpus, 0 false tabs.
- `tv/control_app.py: stash_screen_open` — the hardcoded "is his stash actually open" admission.
- `SURFACE_LANE` — stash / inventory / equipment already exist as separate lanes.
- `tv/vault_simulate.py` — six scenarios over his REAL reels, no vision calls (v1904 gave it a main).
- `art/` + the reels in `tv/frames/hist` — the photographs to reconstruct from.

## What does NOT exist yet, and is the actual work

1. **A per-SLOT identity.** Everything today is keyed by NAME. "Has it moved?" needs `(character,
   surface, tab, row, col)` — the grid position — and nothing reads a grid position today.
2. **A character/mule identity.** Nothing knows which mule a frame belongs to. The stash is shared;
   the inventory and equipment are not.
3. **A LOCK.** Once 1 and 2 land, "locked, never suggest moving" is a flag with a reason and a
   provenance row, not a rule in prose.
4. **The 1:1 render** in the console.

## The first step — DONE, 2026-08-21, and it changes the plan

`tv/vault_corpus.py` indexes the ownership footage from pixels alone. Two structural signals, no
model call: the **INVENTORY title** (gold-on-stone in a fixed band, scored as a fraction so the
lobby, the in-game menu and the Chronicle panel — all of which print gold titles — fall outside the
tight window the real title occupies) and the **active-tab gem** (v1912).

**MEASURED over the 27 reels the sweeps already walk:**

| | |
|---|---|
| frames carrying ownership evidence | **263** |
| the stash+inventory template — his exact "both panels open" | **112** |
| a structurally READABLE stash tab | **151** |
| by tab | personal **102** · shared **23** · materials **14** · runes **8** · gems **4** |
| concentrated in | `reel_s_1784984019250_95276` (90) · `reel_s_1785078127173_28278` (44) |

**So the footage he thought was missing is already on his disk.** REG-185's *"0 of 17 reels declare
an ownership surface"* was read for months as *"there is no stash footage"*; it only ever said no reel
**declared** one.

⚠ **AND THE ARCHIVE IS TWO ARCHIVES.** `frames/hist` holds **883 loose frames**; the 27 reels hold
**1,970**; they share **zero filenames**. Every stash measurement before this — the 68-frame corpus,
the gem calibration, `stash_grid_truth.json` — was taken on the **loose** half, **which no sweep has
ever walked**. That is why the vault lane looked starved.

✅ **A side effect worth the whole scan:** v1912 derived the tab pitch from three tabs and predicted
gems at 0.508 and runes at 0.875 with no frames to check. The reels have both. Opened and looked at:
**runes reads 0.874, gems reads 0.506.** The gem reader is 5 of 5 tabs, verified on his own footage.

## The step after this one — STARTED, and the first two attempts FAILED

**Label what is IN the slots**, because *"has it moved?"* cannot be scored until *"what is in slot
(row, col)?"* can be. That needs a slot ADDRESS, which needs the cell lattice.

Opened `f_1784984271825` (GEMS tab) and looked: it is an unmistakable **7 × 5 lattice** of bordered
cells, each holding one gem with its stack count in the corner, with the Horadric cube's 3 × 4 grid
below it. To the eye it could not be clearer.

**Five attempts. THE ROWS ARE SOLVED AND CONFIRMED ON THE PIXELS; the columns are not.** Every
attempt is recorded with its numbers so the sixth does not repeat one:

| # | attempt | expected | got |
|---|---|---|---|
| 1 | peak-pick the brightness projection | 7 columns, even pitch | 14 columns, pitch sd **34 on a mean of 70** — locked onto gem highlights and stack digits |
| 2 | autocorrelate the brightness profile | pitch ≈ 151 px | **216 px**, a harmonic; at the true lag the correlation is strongly **negative** |
| 3 | autocorrelate the dark-cell/divider fraction | a clean square wave | best lag **108 px**, ac **0.023** — no peak near 151 |
| 4 | **project EDGE energy instead of brightness** | dividers are long straight lines, gems are blobs | ✅ **ROWS: 6 boundaries at pitch 92 ± 7.5** against a truth of 5 rows at 96 — and drawing them back onto the frame puts **every line on a real divider**. ❌ columns: 7 peaks, pitch sd **31** |
| 5 | mask the column projection to the empty band under each row divider | only dividers survive | **worse** — 5 peaks at pitch 235. The band clips item art rather than background |

**Attempt 4 is the method.** A horizontal divider spans the full panel width and nothing else does,
so the row axis falls out cleanly. The column axis carries the gems' own vertical edges *and* the
stack-count digits at each cell's right edge, which is why the same projection fails on it.

**What to try next, on the columns only:**
1. **The cell BOX, not a 1-D projection.** Every cell is a bordered rectangle of one fixed size. Match
   one cell template across the panel; the lattice is a grid of boxes, and a projection throws away
   the very fact that makes it recognisable.
2. **Use the SOLVED rows as the template height** — one axis is known, which halves the search.
3. **Derive the panel rectangle first.** Every attempt above used a hand-eyeballed crop box, and a
   crop whose edges include panel chrome distorts every statistic taken inside it.

**And the lesson is REG-205's, one subsystem over: the obvious feature is the wrong feature.** There,
five equal cells and argmax luminance got 1 of 3, and the answer was a small structural marker — the
active-tab gem — that no projection would ever have found. Here the same held twice: brightness was
the wrong feature and EDGES were the right one, and the axis that works is the one whose divider has
no competition.

**Then, and only then, label.** A slot map built on a lattice that was fitted rather than FOUND is a
plausible-but-wrong detector, which is the precise failure v1857/v1859 already cost.

⚠ **The tally tabs are not a smaller version of the problem — they are OUTSIDE it.** In his words,
2026-08-21:

> "gems/runes/materials — these never move... these go to their templates grid in stash where they
> have infinite room they stack up on the same inventroy cell block unit.. so nothing to automate
> here. they should be like sort of ghosts.. cuz before the third reel witness it gets stashed
> already."

Three consequences, and the third is the one that would have been got wrong:

1. **No slot tracking.** A catalogue cell is fixed by TYPE, with infinite depth. There is no "where
   is it" question to answer, so no lattice address is needed for these tabs at all.
2. **No movement question.** Nothing there can move, so the lock, the 3-session no-move check and
   the whole equipment/inventory apparatus simply do not apply.
3. ⚠ **THE THREE-WITNESS BAR IS WRONG FOR THEM.** The vault gate demands corroboration across
   recordings before it will believe an item. For a tally tab the item is *already stashed by the
   time a third reel exists* — the game did it automatically. Applying the KEEP bar there does not
   make the answer safer, it makes it LATE, and a rule that is right everywhere else can be wrong
   here precisely because the game is doing the work. They are **ghosts**: counted, never gated,
   never routed.

So the movement work is only ever about **personal**, **shared**, **inventory** and **equipment** —
which is where 102 personal + 23 shared of the indexed frames sit.

---

## Attempt 6 — SOLVED, and the first five were aimed at the wrong panel (2026-08-21)

**The premise above was wrong, and looking at the frame settled it in seconds.** The doc says the
GEMS tab is "an unmistakable 7 × 5 lattice of bordered cells". Opened at half scale, it is not:
**the gems tab has no cell borders at all.** Gems sit on a flat dark field with a stack count beside
each. Five attempts hunted vertical dividers in a panel that has none — which is why every column
statistic came back as noise while the rows (the gems' own regular vertical spacing) looked fine.

**And the gems tab is out of scope by his own words** — *"gems/runes/materials never move… they
should be like sort of ghosts"*. Five attempts were spent on the one panel he had already excluded.

### The panel that matters, and it is easy

The **INVENTORY grid** has real bordered cells, and it is where free space actually lives.

| axis | pitch | lines | cells |
|---|---|---|---|
| columns | **86.75 px** | 11 | **10** |
| rows | **85.75 px** | 5 | **4** |

Square cells to within 1 px, and 10 × 4 is exactly the D2 inventory. Crop
`(0.595W, 0.495H) → (0.915W, 0.70H)`; lines at
`cols [35,122,208,295,382,469,556,642,729,816,902]`, `rows [32,118,204,289,375]`.

### What made it work — the property every earlier attempt threw away

**A LATTICE IS REGULAR. Fit pitch and phase; do not pick peaks independently.** Attempts 1–5 all
peak-picked, so a bright piece of item art competed on equal terms with a divider. Scanning
pitch ∈ [70,100] × phase and scoring the ridge energy at the *predicted* line positions makes item
art irrelevant: it has to land on a periodic grid to score, and it does not.

Two supporting fixes, both needed:
- **Ridge, not brightness.** A border is a local maximum against *both* neighbourhoods. Absolute
  brightness fails because **border visibility depends on occupancy** — the border of a blue
  occupied cell is obvious, the same border around a black empty cell is nearly invisible, so no
  global threshold exists. That single fact explains the left-half/right-half split in the profile.
- **Median down the axis, not mean.** Item art is bright at *some* y; a border is bright at *every* y.

### Occupancy — solved, with a margin that needs no tuning

⚠ **The obvious feature was wrong for the THIRD time in this territory.** Occupied cells are
blue-tinted, so "blue tint" looks like the detector — but **the item art covers the blue
background**: a grey cube, an orange torch and silver coins all score *negative* on `B − R`. It
found 4 of 22.

The real signal is that an **empty cell is uniformly near-black**:

```
empty     mean 4.3   std 0.6–1.0
occupied  mean 31–169  std 20–78
```

Thresholds `(18,12)`, `(20,15)` and `(25,18)` all return **22 occupied, 18 free** — identical
answers from three different cut points, which is what a real bimodal signal looks like and what a
tuned constant never does. Verified cell-for-cell against the picture.

**`FREE INVENTORY SPACE = 18` on this frame**, which is the number his vault manager needs.

### What is next

1. Lift this into `tv/vault_corpus.py` as `inventory_lattice(frame)` / `inventory_occupancy(frame)`,
   with the thresholds recorded as a measured range rather than a magic number.
2. Prove it on a SECOND frame before trusting it — one frame is a fixture, and this project has
   already paid for believing a single-frame reading. [[feedback-blind-fixture-green-gate]]
3. Only then the personal/shared stash grids, which are the same problem at a different size.

**The standing lesson, now three-for-three in this subsystem:** the obvious feature is the wrong
feature. Brightness lost to edges; edges lost to a fitted lattice; hue lost to variance. Each time
the winning feature was the one that survives what varies — occupancy, item art, and stack digits.

### And then it accepted the LOBBY MENU — the false positive that matters

Run across all 153 frames of the reel, the first version accepted **101** of them and confidently
reported *"18 occupied, 9 free"* for a cluster of seven. Opening one: it is the **game-creation
lobby** — a column of checkboxes beside *Level Difference · Friends List Joining · Item Spacing ·
Terrorized* and a **Create Game** button. A checkbox list is periodic, so a lattice fitter finds a
lattice in it, and nothing in the answer looks wrong.

**A periodic grid is a PROXY. The titled panel is the thing.** [[feedback-verify-not-proxy]]

Two gates fixed it, and both are facts about the game rather than tuned numbers:

- **The D2 inventory is ALWAYS exactly 10 × 4.** The ±1 tolerance was letting a 9 × 3 through.
- **Its cells are SQUARE.** Menu rows and columns are not (the lobby fitted 93 × 96+ unevenly).

⚠ **The obvious gate did not work, and it is worth knowing why.** `vault_corpus.title_score` reads
the gold INVENTORY title and looked like the right check. Measured: the **real inventory frame
scores 0.00024 — BELOW the documented window of 0.0006–0.0012 — while the LOBBY MENU scores
0.00261, above it.** Used as the gate it would have rejected the truth and accepted the false
positive, exactly inverted. **That window is mis-calibrated and `vault_corpus` should not be trusted
on this frame size until it is re-measured** — recorded here rather than quietly worked around.

### The verified result

| | |
|---|---|
| frames scanned | 153 |
| accepted | **94** |
| refused | 59 — pitch at the search bound (33), noise floor (7), not 10×4 (13), wrong frame size (6) |
| **93 of 94 agree exactly** | **occupied 22 · free 18** |
| pitch | 86.75 × 85.75 on 90 frames, 86.75 × 85.5 on 4 |

**Ninety-three independent photographs of the same screen returning the identical count** is the
strongest corroboration available here, and it is what the third-witness rule was asking for.

⚠ **One frame reads 23 / 17 and it is NOT rounded away.** A single disagreeing frame is either a
genuine moment (an item on the cursor mid-move, a tooltip overlapping a cell) or the first sign of
an edge case. It is recorded so the next pass can open it, rather than being absorbed into a
majority. [[unknown-stays-unknown]]

### The outlier, opened — and the fix is the one he already asked for

`f_1784984248692` reads 23/17. Opened: an **item TOOLTIP is drawn over the inventory** — *Very Fast
Attack Speed · +to All Skills · Enhanced Damage · 5-30 fire damage* — and its text lands inside an
empty cell, which then reads as occupied. Not a different inventory. A contaminated photograph.

**A per-frame occlusion detector was tried and REJECTED, and the numbers are why.** A tooltip covers
the grid's own divider lines, so divider continuity should expose it — no colour heuristics, nothing
item art can imitate. Measured: **median divider intact 0.477 clean vs 0.452 occluded.** The
per-divider values do lean the right way (0.24 → 0.15 on the most-covered line), but 0.477 vs 0.452
is not a separation, it is a threshold I would be choosing to make the answer come out. **A tuned
constant dressed as a measurement is the thing this project keeps paying for**, so it is not
shipped. [[feedback-threshold-above-the-ceiling]]

**The design already solves it.** His rule was *3+ verified reads across sessions showing nothing
moved* — and that rule absorbs this exactly: 93 of 94 frames say 22/18, one contaminated frame says
23/17, and the modal reading is right. **Corroboration across frames is the occlusion detector**, and
no per-frame heuristic is needed. This is the third-witness requirement earning its keep rather than
being a formality.

### Still to do

1. Lift `lattice()` / `occupancy()` into `tv/vault_corpus.py` with the refusals intact — **the
   refusals are the feature**; without them it reports a confident number for a lobby menu.
2. Take the MODAL reading across a reel, never a single frame, and report how many frames agreed —
   a count of 93/94 is evidence; a count of 1/1 is a fixture.
3. Re-measure `TITLE_BAND` / `TITLE_MIN..MAX`, which are currently inverted on this frame size:
   the real inventory scores 0.00024 against a 0.0006–0.0012 window while the lobby scores 0.00261.
4. Then the personal/shared stash grids — same method, different known dimensions.
