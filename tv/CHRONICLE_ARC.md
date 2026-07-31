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

Tests: `tv/test_chronicle_retro.py` (60), the chronicle classes in `tv/test_control.py` and
`tv/test_agent.py`, and `tests/v1510_*`, `tests/v1520_*`, `tests/v1521_*`.

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

## ⚠ THE ONE THING STILL UNVERIFIED

**No part of this has ever read a real Chronicle screenshot.** Everything has been exercised against
real film with stubbed readers, and against real readers with synthetic frames. The machinery is
verified; the READING is not. The prompts are the least-tested code in the arc.

**It cannot be verified from inside a Claude Code session.** `claude -p` hangs when nested (the agent
warns about this itself at `tv_diablo.py:5023`), so the one command that would answer it has to be
run by a human in a BARE terminal:

```bash
cd ~/d2r_bible_tests
python3 tv/chronicle_doctor.py          # confirm the arc is wired on this machine (free)
python3 tv/chronicle_retro.py --cost    # what a sweep would cost, on your own film (free)
# then, in the console: 📜 CHRONICLE SWEEP → "run it for real"
```

Until that has run once against footage containing an actual Chronicle panel, treat every claim in
this document as "the machinery is right", never as "the tally is right".

## ⚠ ALSO UNWIRED: the worker intake kinds

`functions/api/intake.js` gained `chronicle-uniques` / `chronicle-sets` in v1510 and **nothing calls
them**. The sweep reads through the Claude and Grok lanes directly, so the worker kinds have 9 tests
and zero callers. They are not wrong — they are the same contract `normalize_page` speaks — but
today they are a road with no traffic.

Where they SHOULD be wired, and why it matters for the fleet: a photographed or screenshotted
Chronicle, posted from the board the way the v561 `grail` import already works. That is the path
that works when the console is **not** watching — on his phone, or on the Windows PC and his
cousin's box, which may never run TV DIABLO at all. The live and retro lanes both assume the console
is running; this one does not.

## Picking it up

Everything is wired and green. The natural next steps, in value order:

1. **Run it against his real footage** — see the section above. This is the gap that decides whether
   any of the rest was worth building.
2. **Wire the worker kinds to a board photo-intake** — the only Chronicle path that works without
   the console running, which is the only path the Windows PC and the cousin's box may ever have.
3. ~~Set-name → pieces~~ — closed in v1530.
4. ~~Tune the gate on real data~~ — the *tooling* is closed in v1531 (`/api/chronicle_gate`); the
   tuning itself still needs a real sweep to tune against.
