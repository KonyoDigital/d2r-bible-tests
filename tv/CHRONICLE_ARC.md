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

## Picking it up

Everything is wired and green. The natural next steps, in value order:

1. **Run it against his real footage** — nothing here has been through a real Chronicle screenshot
   yet, only real film with stubbed readers. The prompts are the least-tested part of the arc.
2. **Set-name → pieces.** The sets ledger reads piece names; a Chronicle page grouped under a set
   NAME with unnamed piece rows is not yet resolvable.
3. **Tune the gate on real data.** `CONF_FLOOR = 0.55` and `MIN_WITNESSES = 2` are reasoned, not
   measured. Once a real sweep has run, the HELD list is the evidence for whether they are right.
