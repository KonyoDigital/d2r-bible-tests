"""Drive the vault lane end to end and SHOW what it decides — no vision calls, no writes.

Konyo: "simulate it based on the reels you already have and the sessions available run scenario
demonstration and simulated tests isolated for the coding relevant and test and optimize it to
perfection make sure its coded properly and make sure its not discading anything it shouldnt. and
make sure its muling anything it is."

WHY A SIMULATOR AND NOT JUST TESTS. The vault lane has never run on real footage — 0 of 17 reels
declare an ownership surface (REG-185) — so every claim about what it "would do" was theory. Tests
assert one fact each; this prints the whole decision for a scenario in the words the Vault manager
would use, so a wrong rule is visible rather than merely unasserted.

IT USES HIS REAL REELS for structure — real frame names, real timestamps, real still-run grouping via
chronicle_retro — and injects only the READER's answer, because that is the one thing the archive does
not contain. So the runs exercise the real grouping, the real gate and the real merge, not a mock of
them.

THE RULE IT EXISTS TO PROVE: seeing an item more often NEVER means throw it away. Repetition decides
whether he OWNS it; only the reader's own junk flag can even propose a discard, and then only across
three separate recordings. A simulator that cannot show that distinction failing is not proving it, so
the scenarios below include the cases that SHOULD refuse.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import chronicle_retro as cr          # noqa: E402
import vault_retro as vr              # noqa: E402


def _reel_frames(reel_dir, limit=None):
    """Real frame rows from a real reel index — names and timestamps he actually recorded."""
    idx = cr.load_index(reel_dir) or {}
    rows = [f for f in (idx.get("frames") or []) if f.get("f")]
    return rows[:limit] if limit else rows


def scripted_reader(script):
    """reader(path, surface) -> the answer this scenario says the AI gave for that frame.

    `script` maps a frame BASENAME to an items list. A frame with no entry returns a page that was
    read and held nothing — which is different from a refusal, and vault_retro treats them
    differently, so the simulator must be able to express both.
    """
    def _reader(path, surface):
        name = os.path.basename(path)
        entry = script.get(name, None)
        if entry is None:
            return {"items": [], "conf": 0.9}
        if isinstance(entry, dict) and "note" in entry:
            return entry                      # an explicit REFUSAL
        return {"items": entry, "conf": 0.9}
    return _reader


def run(scenario, hist_dir=None):
    """-> the raw proposal. Pure: classify/reader are injected, nothing is written."""
    hist = hist_dir or os.path.join(HERE, "frames", "hist")
    dirs = [os.path.join(hist, d) for d in scenario["reels"]]
    return vr.sweep(dirs, sig=cr.jpeg_sig,
                    classify=lambda p: scenario.get("surface", "stash"),
                    reader=scripted_reader(scenario["script"]))


def explain(prop):
    """The proposal in the words the Vault manager would use to him."""
    out = []
    if not prop.get("ok"):
        return ["REFUSED — %s" % prop.get("why")]
    for r in prop.get("owned") or []:
        out.append("OWN     %-26s conf %.2f · %d witness(es) → goes to the Vault manager, which "
                   "assigns the mule and the cell" % (r["name"], r.get("conf") or 0,
                                                      len(r.get("witnesses") or [])))
    for r in prop.get("throwOut") or []:
        out.append("DISCARD %-26s SUGGESTION ONLY — %s" % (r["name"], r.get("why")))
    for r in prop.get("unsure") or []:
        if r.get("name"):
            out.append("UNSURE  %-26s %s" % (r["name"], r.get("why")))
    for r in (prop.get("held") or [])[:6]:
        if r.get("name"):
            out.append("HELD    %-26s %s" % (r["name"], r.get("why")))
    return out or ["(nothing proposed)"]


# ── THE SCENARIOS ───────────────────────────────────────────────────────────────
# Each one is a claim about what SHOULD happen, written so a wrong rule is visible in the transcript
# rather than merely unasserted. `expect` is what the scenario is asserting, in his words.

SCENARIOS = [
    {"id": "seen-once",
     "say": "one look at a Shako. One sighting is not two, so it must NOT be counted as owned.",
     "reels": ["reel_s_1786998496819_31092"],
     "frames": 12,
     "plant": {0: [{"name": "Harlequin Crest", "kind": "item", "conf": 0.95}]},
     "expect": "UNSURE, never OWN"},

    {"id": "two-recordings",
     "say": "the same Shako in TWO separate recordings — that is two independent witnesses, so it is "
            "owned and goes to the Vault manager to be assigned a mule and a cell.",
     "reels": ["reel_s_1786998496819_31092", "reel_s_1786998671206_32230"],
     "frames": 12,
     "plant": {0: [{"name": "Harlequin Crest", "kind": "item", "conf": 0.95}]},
     "plant_all_reels": True,
     "expect": "OWN"},

    {"id": "junk-one-recording",
     "say": "the reader flags a cracked sash as junk, but only in ONE recording. There is no un-throw "
            "in Diablo, so it must NOT suggest discarding it.",
     "reels": ["reel_s_1786998496819_31092"],
     "frames": 12,
     "plant": {0: [{"name": "Cracked Sash", "kind": "item", "conf": 0.99,
                    "throwOut": True, "throwWhy": "white base, no sockets"}]},
     "expect": "HELD — no discard suggestion"},

    {"id": "junk-three-recordings",
     "say": "the same junk flagged in THREE separate recordings at high confidence. Now it may be "
            "SUGGESTED for discard — and only ever as a suggestion he presses.",
     "reels": ["reel_s_1786998496819_31092", "reel_s_1786998671206_32230",
               "reel_s_1786998775577_33262"],
     "frames": 12,
     "plant": {0: [{"name": "Cracked Sash", "kind": "item", "conf": 0.99,
                    "throwOut": True, "throwWhy": "white base, no sockets"}]},
     "plant_all_reels": True,
     "expect": "DISCARD (suggestion only)"},

    {"id": "repetition-is-not-a-discard",
     "say": "THE RULE HE ASKED ABOUT: a Shako seen in three recordings. Seeing it more often makes it "
            "more certainly OWNED — it must never become a discard.",
     "reels": ["reel_s_1786998496819_31092", "reel_s_1786998671206_32230",
               "reel_s_1786998775577_33262"],
     "frames": 12,
     "plant": {0: [{"name": "Harlequin Crest", "kind": "item", "conf": 0.99}]},
     "plant_all_reels": True,
     "expect": "OWN, and nothing in DISCARD"},

    {"id": "merge-max",
     "say": "a later recording sees FEWER of an item than an earlier one. A read may never lower a "
            "count — an obstructed panel is a normal event, not evidence he threw something away.",
     "reels": ["reel_s_1786998496819_31092", "reel_s_1786998671206_32230"],
     "frames": 12,
     "plant": {0: [{"name": "Ral", "kind": "rune", "count": 5, "conf": 0.95}]},
     "plant_second": {0: [{"name": "Ral", "kind": "rune", "count": 2, "conf": 0.95}]},
     "expect": "count stays 5"},
]


def build(scn, hist_dir=None):
    """Turn a scenario into a real script over his real frames."""
    hist = hist_dir or os.path.join(HERE, "frames", "hist")
    script = {}
    for i, reel in enumerate(scn["reels"]):
        rows = _reel_frames(os.path.join(hist, reel), scn.get("frames"))
        if not rows:
            continue
        plant = scn["plant"]
        if i > 0 and not scn.get("plant_all_reels") and not scn.get("plant_second"):
            plant = {}
        if i > 0 and scn.get("plant_second"):
            plant = scn["plant_second"]
        for idx, items in plant.items():
            # plant on a RUN of consecutive frames so still_runs makes it a readable page
            for row in rows[idx:idx + 4]:
                script[row["f"]] = items
    return {"reels": scn["reels"], "script": script, "surface": "stash"}
