# 🔒 LOCKED TYPE SYSTEM — TV DIABLO (VISUAL-LOCK)

Konyo's VISUAL-LOCK goal: the flagship look is single-sourced onto CSS custom-property tokens
and **frozen against drift** by an invariant test. This doc is the frozen contract.

## Surfaces
- **`bible.html`** — the grail-hunting board (bull-4-u.com/d2r + the app board).
- **`tv/control_ui.html`** — the TV DIABLO control console.

## The `--fw-*` weight tokens (SOURCE OF TRUTH — never write a raw `font-weight:NNN`)
Every weight is a token; the token value is the literal it replaced (identity — swaps are
zero-visual-change). Defined in each file's `:root`:

| token            | value | role                    |
|------------------|-------|-------------------------|
| `--fw-regular`   | 400   | body / de-emphasis      |
| `--fw-normal`    | 500   | default UI text         |
| `--fw-medium`    | 600   | card names / labels     |
| `--fw-semibold`  | 700   | headers / emphasis      |
| `--fw-bold`      | 800   | flagship titles         |
| `--fw-black`     | 900   | rare heavy display      |

- **bible.html** defines all six. **control_ui.html** defines the four it uses (normal/medium/
  semibold/bold); add `--fw-regular`/`--fw-black` there only if a 400/900 weight is introduced.
- **Usage:** `font-weight: var(--fw-semibold);` — in CSS rules AND in JS-string inline styles
  (`style="font-weight:var(--fw-semibold)"`) — `var()` resolves against `:root` in both.

## Other established token families
- **`--fs-*`** (font-size): both surfaces use a shared size scale. bible: display/title/body/
  meta/micro; console: its own `--fs-*` set. (Not yet invariant-locked; weights were the drift.)
- **`--ls-*` / `--lh-*`** (letter-spacing / line-height): **console-only so far.** bible has ~471
  letter-spacing + ~330 line-height literals across ~157 distinct values (mixed px/em) — these
  CANNOT be identity-folded to the console's 13 em tokens without a deliberate visual
  normalization (a design call, Konyo's eye). Tracked in `MORNING_QUESTIONS.md`; NOT locked.

## The invariant test — `visual_lock_invariant.py`
Freezes the weight system so no future edit can silently reintroduce a raw literal.
```
python3 visual_lock_invariant.py     # exit 0 = locked · exit 1 = drift (names file:line)
```
Asserts, for **both** surfaces: (1) **0 raw `font-weight:NNN`** literals (spaced or not);
(2) the `--fw-*` token set is defined in `:root`. Pure stdlib, no deps, CI-runnable. Wire it
into any pre-push / CI gate. If a raw weight creeps back it fails loudly with the file:line and
the token to use.

## History
Weight tokenization: console v1288-v1296 (sessions-visual); bible v1314→v1321 (g3-sweep),
733→0 raw literals across 6 identity-swap passes (headers · chips/tables · card bodies · all
component bodies · JS-string inline · the spaced-syntax + `!important` finish). Every pass
proved 0 non-font-weight changes on the diff = byte-identical render.
