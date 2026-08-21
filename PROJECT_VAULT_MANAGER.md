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

## The first honest step

Not code — **a labelled corpus**, the same move that closed REG-203/REG-205: take his existing reels,
label a handful of inventory/equipment frames with what is actually in each slot, and measure what
the readers get right today. Everything above is unbuildable until "did it move?" can be scored.
