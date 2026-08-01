# 📜 THE CHRONICLE AUTO-TALLY — v1509 → v1528

> Konyo: *"make sure the AI and readers are prepared and ready to read and register the screenshots
> for chronicles... when chronicle/menu is clicked ingame it should automatically know we are about
> to register and read and analyze the CHRONICLE lists... retro and live... especially retro most
> important... SETS/ and UNIQUES completes SEPARATED accordingly."*
>
> *"i want to save time manually trying to update and screenshot or manually tally each one."*

This is what got built, why each piece is shaped the way it is, and where to pick it up.

---

## The chain, end to end

```
  he opens the Chronicle in game
        │
        ├─ LIVE  ─ the agent RECORDS the visit (free) ──────────┐   v1522
        │          frames · which ledger · how long             │
        │                                                       ▼
  sealed reels on disk                                    a VISIT you can read
        │                                                  in one click, with
        └─ RETRO ─ still-runs → classify one frame per run  ZERO classifies    v1527
                   → read only the Chronicle runs                │
                          v1511 · v1519                          │
                                    │                            │
                                    └──────────┬─────────────────┘
                                               ▼
                                    two lanes read each page          v1514
                                    Claude (primary) + Grok
                                    disagreement REPORTED, not averaged
                                               │
                                               ▼
                                    the GATE: 2 independent witnesses  v1513
                                    cross-lane · cross-reel · cross-frame · printed
                                               │
                            ┌──────────────────┴──────────────────┐
                            ▼                                     ▼
                     WOULD ADD (with its reason)              HELD (with its reason)
                            │                                     │
                            ▼                                     ▼
                     he presses register              he decides by hand, looking
                            │                          at the frames               v1525
                            ▼
                   the BOARD applies it                                            v1521
                   dated · merge-max · undoable as a batch
```

## The laws, and why they exist

**1. Read-only until Apply.** `chronicle_retro.py` has no write-mode `open`, no `remove`, no
`json.dump` — asserted by a test. A sweep that silently ticked 400 grail rows would be unauditable
and un-untickable: there is no *unfind* in Diablo.

**2. Merge-max.** A chronicle read only ever ADDS. A reel from March cannot un-find something found
in July, and a page that scrolled past a row is not evidence the row is empty. `notFound` is carried
for auditing and subtracts from nothing.

**3. Pay for runs, not frames.** Measured on his real film: **394 frames → 11 classifies, 97%
cheaper.** A visit sweep costs **zero** classifies, because opening the panel already answered the
question the classify stage exists for.

**4. Two ledgers, never one.** Uniques → `d2r_foundLog`; sets → `d2r_setPieces`. A Sets screen tallied
as Uniques is worse than no tally at all. Every layer refuses rather than guesses: the prompt leaves
`chronicleTab` empty when unsure, `chronicle_kind()` returns None, the visit sweep refuses outright.

**5. Nothing grounds on one sighting.** Two INDEPENDENT witnesses, and *independent* is doing the
work — the same frame read twice is one witness, and one reader confident twice is one witness. The
confidence floor is checked FIRST: corroborating a guess with another guess is not evidence.

**6. Every verdict explains itself.** Pass or fail, in a sentence. When his grail doesn't move he
gets *why*; when it does, the reason survives being questioned.

## Where the pieces live

| what | where |
|---|---|
| the `chronicle` scene + `chronicleTab` | `tv/tv_diablo.py` — `READ_PROMPT`, `_norm_chron_tab` |
| Claude's chronicle lane | `tv/tv_diablo.py` — `CHRONICLE_READ_PROMPT`, `claude_chronicle_read` |
| Grok's second eye | `tv/g5_grok_eyes.py` — `CHRONICLE_VISION_PROMPT`, `g5_chronicle_read` |
| the engine (pure, never writes) | `tv/chronicle_retro.py` |
| the job, routes, memory | `tv/control_app.py` — `chronicle_*` |
| the panel | `tv/control_ui.html` — `#hd-chron` |
| the apply | `bible.html` — `chronicleApply` / `chronicleUndoLast` |
| worker intake kinds | `functions/api/intake.js` — `chronicle-uniques` / `chronicle-sets` |
| the photo intake (no console) | `bible.html` — `chronicleShotIntake` / `chronicleShotApply` (v1540) |
| why an empty sweep is empty | `tv/chronicle_retro.py` — `sweep_verdict` (v1541) |
| blank-capture refusal | `tv/chronicle_retro.py` — `is_dead_frame` / `live_probe` (v1543) |

Tests: `tv/test_chronicle_retro.py` (78), `tv/test_chronicle_chain.py` (10), the chronicle classes in
`tv/test_control.py` and `tv/test_agent.py`, and `tests/v1510_*`, `tests/v1520_*`, `tests/v1521_*`,
`tests/v1540_*` (12).

## What is deliberately NOT done

- **The live lane never fires a read by itself.** Recording is free; reading is offered. Auto-reading
  mid-farm would spend subscription budget without asking, on frames he is scrolling past. A test
  fails if that seam ever grows a call to `claude_chronicle_read`.
- **The console never writes the grail.** It asks the board. One write path, not two.
- **A visit whose ledger was never read is never swept.** The cost of refusing is him re-opening a
  panel for a second. The cost of guessing is a corrupted ledger.

## Added after the first write-up (v1529 → v1533)

| version | what |
|---|---|
| v1530 | a set the panel calls **COMPLETE** expands to all its pieces — gated the same as any name, expanded by the board (which owns `__allSets()`) |
| v1531 | **tune the gate for free** — `GET /api/chronicle_gate?floor=&witnesses=` re-runs the gate over the last sweep's evidence and NAMES what loosening would let in and tightening would keep out |
| v1532 | **the whole chain in one test** — `tv/test_chronicle_chain.py`; every other suite mocks its neighbours, this one walks the seams |
| v1533 | **the doctor** — `python3 tv/chronicle_doctor.py` says whether the arc is wired on THIS machine |

Two of the three gaps named below are now closed: set-NAME rows (v1530) and
unmeasurable thresholds (v1531). One remains, and it is the important one.

## THE READING ITSELF — reported working (2026-08-02)

For thirty versions this section read: *"No part of this has ever read a real Chronicle screenshot."*
Everything was exercised against real film with stubbed readers and against real readers with
synthetic frames; the machinery was verified and the READING was not.

Konyo has now run it on his own machine and reports it working. That is one person's report rather
than a test, so treat it as it is: the prompts are no longer unexercised, and they are still the
least-covered code in the arc. The cheap checks remain free and worth running after any prompt change:

```bash
python3 tv/chronicle_doctor.py          # is the arc wired on THIS machine
python3 tv/chronicle_retro.py --cost    # what a sweep would cost + which frames + the verdict
```

## ✅ CLOSED: the worker intake kinds now have a caller (v1540)

`functions/api/intake.js` gained `chronicle-uniques` / `chronicle-sets` in v1510 and for thirty
versions nothing called them — nine tests, zero callers, a road with no traffic.

**v1540 built the road.** The Forge tabs carry 📜 **Read my Chronicle · UNIQUES** and 🧩 **· SETS**:
photograph the in-game panel, it reads as evidence, and nothing is written until he presses register.

This is the only Chronicle path that works when the console is **not** running — on his phone, on the
Windows PC, on his cousin's box. The live and retro lanes both assume TV DIABLO is watching; this one
does not, which is the whole reason it exists.

It inherits rather than reinvents: the caller states the ledger (two buttons, never auto-detect), the
read is read-only until Apply, found[] merge-maxes across pages, and the write goes through the one
`chronicleApply()` so the owned-item guard (REG-087) and the batch undo come along. Refusals
(`wrong-ledger`, `no-found-state`) are shown, not swallowed. Tests: `tests/v1540_*` (12).

## An empty sweep now says WHICH nothing it is (v1541)

Konyo ran the retro sweep on his Windows PC: *"it didnt work properly."* It may well have worked —
a sweep over footage with no Chronicle in it correctly proposes nothing and renders exactly like a
broken one.

`sweep_verdict()` separates six outcomes, and only ONE of them is the reader:

| state | meaning |
|---|---|
| `no-footage` | no sealed reels yet |
| `all-swept` | the memory doing its job |
| `no-stills` | nothing held still long enough to be worth reading |
| `no-chronicle` | screens WERE examined and none was a Chronicle page |
| `read-nothing` | **pages were read and yielded nothing — this one is the reading itself** |
| `found` | names proposed |

`--cost` also lists the frames a real sweep would pay to classify. On a machine nobody can reach,
that listing is the difference between a diagnosis and a guess.

## Blank captures are refused, and counted (v1543)

Three of the eleven still screens in the Mac's reels are blank captures — a white window, a black
one, and a black one with a title bar. The sweep paid a classify for each.

Measured: dead frames at **95.0%** and **99.4%** single-tone; the busiest legitimately-dark real
frame (the D2R title screen) at **82.7%**. `DEAD_FLATNESS = 0.92`.

A blank *middle* frame does not condemn the run — `live_probe` steps outward, because a window that
blanked mid-visit is exactly when the rest of the run is still real. An unmeasurable frame is still
read. And the skip is COUNTED: a silent one would turn a capture fault into a smaller invoice and
nothing else.

## Picking it up

Everything is wired and green. What is left, in value order:

1. **Tune the gate against a real sweep.** The *tooling* has existed since v1531
   (`/api/chronicle_gate?floor=&witnesses=` re-runs the gate over the last sweep's evidence for free
   and names what loosening would let in). It has never been pointed at a real proposal, so
   `CONF_FLOOR = 0.55` and `MIN_WITNESSES = 2` are still guesses that have never been wrong in
   anger — which is not the same as being right.
2. **Fix the blank captures at the source.** v1543 stops paying for them; it does not stop them
   happening. Something in the capture lane is grabbing the window with nothing on it, and that same
   fault would eat a real Chronicle frame just as happily as a lobby one.
3. **A second machine's verdict.** Every number in this document was measured on the Mac. The
   Windows PC and the cousin's box are where the reads actually fail (REG-086), and
   `chronicle_retro.py --cost` now prints enough for either of them to be diagnosed remotely.
4. ~~Run it against real footage~~ — reported working 2026-08-02.
5. ~~Wire the worker kinds to a board photo-intake~~ — closed in v1540.
6. ~~Set-name → pieces~~ — closed in v1530.
