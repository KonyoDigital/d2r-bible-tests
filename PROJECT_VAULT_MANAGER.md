# 🗄 THE VAULT MANAGER — his brief, in his words, and what it actually asks for

**Status: SPEC ONLY. Nothing below is built yet.** Written 2026-08-21 from his message so the brief
survives a compaction, and so the first person to work on it starts from what he said rather than
from a summary of a summary.

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

**THREE INDEPENDENT VERIFICATIONS, AND THEY MUST BE ACROSS SESSIONS, NOT ACROSS FRAMES.** The vault
lane already knows this (`vault_retro.gate`, KEEP = 2 distinct sessions, THROW = 3 distinct
recordings, and "two runs of the same unbroken screen are ONE witness"). His brief asks for the same
law applied to a new question — *has this item MOVED?* — which is not the same as *does this item
exist?*, and needs a per-slot identity, not just a name.

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

**Two cheap recoveries were tried and neither worked**, and both are recorded so the third does not
repeat them:

| attempt | expected | got |
|---|---|---|
| peak-picking the column/row brightness projection | 7 columns, even pitch | 14 columns, pitch sd **34 on a mean of 70** — it locked onto gem highlights and stack digits, not dividers |
| autocorrelating the brightness profile | pitch ≈ 151 px | **216 px** (a harmonic); at the true lag the correlation is strongly **negative** |
| autocorrelating the dark-cell/divider fraction | a clean square wave | best lag **108 px**, ac **0.023** — no peak anywhere near 151 |

**The lesson is REG-205's, one subsystem over: the obvious feature is the wrong feature.** There, five
equal cells and argmax luminance got 1 of 3, and the answer turned out to be a small structural
marker — the active-tab gem — that no projection would ever have found.

**What to try next, in order:**
1. **The cell BOX, not the projection.** Every cell is a bordered rectangle of a fixed size. Match one
   cell template across the panel, or find the repeated rectangle directly. The lattice is a grid of
   boxes; a 1-D projection throws away the fact that makes it recognisable.
2. **Derive the panel rectangle first.** Every attempt above used a hand-eyeballed crop box, and a
   crop whose edges include panel chrome distorts every statistic taken inside it. The panel's inner
   frame is a strong rectangle — find it, then the grid is a known fraction of it.
3. **Then, and only then, label.** A slot map built on a lattice that was fitted rather than found is
   a plausible-but-wrong detector, which is the precise failure v1857/v1859 already cost.

⚠ **And the tally tabs are a different problem from the free-form ones.** GEMS / RUNES / MATERIALS are
a fixed catalogue grid ordered by type — "did it move" is close to meaningless there, and the vault
lane's existing COUNT logic already owns them. The movement question is only real for **personal**,
**shared**, **inventory** and **equipment**. That splits the work, and it means the 102 personal and
23 shared frames are the ones that matter for the lock.
