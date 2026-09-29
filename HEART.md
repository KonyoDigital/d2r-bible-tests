# THE HEART — what watches the console

Derived by `tv/heart_map.py`. Do not edit by hand: it is regenerated on every bump and
the pre-push refuses when it is stale, exactly like BLUEPRINT.md.

A surface here is an `id` the console paints — the honest unit, because a class may be
shared by forty nodes while an id names one thing. WATCHED means its name appears in
`console_doctor.py`, `health_engine.py`, `corroborate.py` or `heart2.py`.

⚠ UNWATCHED IS NOT A DEFECT. Most surfaces neither need nor will ever have a watcher.
What is refused is a surface going unwatched SILENTLY — the count below is a ratchet and
may not fall without a human saying why in `heart_floor.json`.

| | |
|---|---|
| surfaces the console paints | **366** |
| of those, watched | **17** |
| coverage | **4.6%** |

## Watched

- `bug`
- `clock`
- `heart-chip`
- `hero`
- `phase`
- `sadv-sha`
- `sadv-tip`
- `sh-stationbar`
- `sigil`
- `stage`
- `stage-hold`
- `th-shelf`
- `th-shelf-x`
- `th-shelfov`
- `theatre`
- `vault-body`
- `win-ctl`

## The board — `bible.html`

The page the console runs in its window: the builder, the 👤 Characters tab, the mule
window and the Vault paint their surfaces here. Same unit (an `id`), same watchers, its own
ratchet under `board` in `heart_floor.json`. Before 2026-09-29 this page was not mapped at
all, so its surfaces could be neither watched nor unwatched — only unsaid.

| | |
|---|---|
| surfaces the board paints | **513** |
| of those, watched | **1** |
| coverage | **0.2%** |

### Watched on the board

- `vault-moved-note`
