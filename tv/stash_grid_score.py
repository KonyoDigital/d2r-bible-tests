#!/usr/bin/env python3
"""Score `classify_stash_grid` against the hand-labelled frames — the corpus REG-205 asked for.

    python3 tv/stash_grid_score.py

REG-203 (a fire-lit fight called `stash-gems`) and REG-205 (the tab is in the pixels and reading it
is not solved) were both filed OPEN with the same reason: *retuning a pixel fingerprint needs its own
before/after sweep over the whole corpus*, and there was no labelled corpus to sweep against. Three
hand-labelled frames, in REG-205's own words, is not a corpus.

This is twelve, labelled by opening the images, and this script is the before/after. It prints the
confusion, names every disagreement, and exits non-zero if the score is worse than the ratchet in
tv/test_stash_eye_aspect.py — so a retune can be MEASURED instead of argued.

It reads only frames already in the repo, spends no vision, and writes nothing.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

TRUTH_PATH = os.path.join(HERE, "stash_grid_truth.json")


def load_truth():
    with open(TRUTH_PATH, encoding="utf-8") as fh:
        return (json.load(fh) or {}).get("_frames") or {}


TALLY_TABS = ("runes", "gems", "materials")


def tally_score(rows):
    """The axis that carries the information: does the grid name a TALLY, and is it right?

    v1909 — the first version of this scorer graded `label != "gameplay"`, and that axis is nearly
    constant: the grid answers `stash` for almost any dark frame, so BOTH a sabotage that capped
    dark_cols and a sabotage that refused every panel outright scored identically to the real code.
    A metric two opposite sabotages cannot move is measuring nothing.
    [[feedback-blind-fixture-green-gate]]

    -> (false_tallies, missed_tallies). A false tally is the expensive one: it writes a tally count
    for a panel that was never open. A missed one costs another look, and the funnel rechecks.
    """
    false_t, missed_t = [], []
    for frame, panel, tab, label, dc, _ok in rows:
        named = label[len("stash-"):] if label.startswith("stash-") else None
        want = tab if (panel and tab in TALLY_TABS) else None
        if named and named != want:
            false_t.append("%s: said %s, truth %s" % (frame, named, want or "no tally"))
        elif want and not named:
            missed_t.append("%s: %s not named" % (frame, want))
    return false_t, missed_t


def score(hist_dir=None):
    """-> (rows, missing). A row is (frame, truth_panel, truth_tab, label, dark_cols, agrees)."""
    import stash_eye as se
    hist = hist_dir or os.path.join(HERE, "frames", "hist")
    rows, missing = [], []
    for frame, t in sorted(load_truth().items()):
        # v1919 — a corpus entry may name a frame INSIDE a reel ("reel_x/f_y.jpg"), because the two
        # tabs that verified the gem geometry live there. os.path.join handles both; what changed is
        # that the corpus is no longer confined to the loose half of the archive.
        p = os.path.join(hist, frame)
        if not os.path.isfile(p):
            missing.append(frame)
            continue
        label, detail = se.classify_stash_grid(p)
        claims_panel = label != "gameplay"
        rows.append((frame, bool(t.get("panel")), t.get("tab"), label,
                     detail.get("dark_cols"), claims_panel == bool(t.get("panel"))))
    return rows, missing


def main():
    rows, missing = score()
    if missing:
        # An absent frame must never read as a pass — the whole point of a corpus is that it is there.
        print("⚠ %d labelled frame(s) are not in this checkout: %s"
              % (len(missing), ", ".join(missing[:4])))
    if not rows:
        print("⚠ nothing scored — the labelled frames are missing entirely. Not a pass.")
        return 2
    print("\n%-24s %-6s %-10s %-17s %-5s" % ("frame", "panel", "tab", "grid says", "dcols"))
    for frame, panel, tab, label, dc, ok in rows:
        print("%-24s %-6s %-10s %-17s %-5s %s"
              % (frame, panel, tab or "-", label, dc, "" if ok else "← DISAGREES"))
    bad = [r for r in rows if not r[5]]
    real = [r for r in rows if r[1]]
    kept = [r for r in real if r[5]]
    false_t, missed_t = tally_score(rows)
    print("\nTALLY  — false: %d   missed: %d        <- the axis that decides anything"
          % (len(false_t), len(missed_t)))
    for line in false_t + missed_t:
        print("   %s" % line)
    print("PANEL  — %d of %d disagree · %d/%d real panels still claimed"
          % (len(bad), len(rows), len(kept), len(real)))
    print("\n⚠ THE PANEL AXIS IS NEARLY CONSTANT and must not be read as a score: the grid answers "
          "`stash` for almost any dark frame, so a cap on dark_cols and a refusal of every panel "
          "score the SAME on it. Grade the tally axis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
