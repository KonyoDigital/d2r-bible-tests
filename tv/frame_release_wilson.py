# -*- coding: utf-8 -*-
"""A2 — `frame.release`: can `seal_releases_frames()` refuse when it must?

The gate between a seal and a deletion. `frame_authority.frame_verdict` asks it before letting any
frame go, and Konyo's 2026-09-06 ruling made it decide real reels for the first time: an
examined-empty seal may release, a bare "nothing was taken" may not.

⚠⚠ THIS HARNESS DELETES NOTHING AND ARMS NOTHING, and the shape of it guarantees that rather than a
comment promising it. It calls exactly one PURE predicate, `seal_releases_frames(row)`, on
dictionaries it builds in memory. It never touches the seal store, `apply_plan`, `_prune_once`,
`os.remove`, `unlink` or `rmtree`, and it never writes to `TV_AUTO_PRUNE`. There is no code path
here that can remove a byte, and `tv/test_frame_release_wilson.py` asserts that by reading this
file's own source.

⚠ WHY A NEW LOCK RATHER THAN BANKING THESE UNDER prune.arm. These attacks are against a FRAME
granularity authority. `prune.arm` is "may the prune RUN"; `vault.apply` is the write door. Filing
seven real sabotages under a lock whose subject they do not attack would move a counter and prove
nothing — the exact cheat `_hardening_gap`'s docstring names ("calling a fixture `live`, or an
agreement a `sabotage`, would clear this gap on paper and prove nothing"). [[join-gate-heart]]

⚠ EVERY ATTACK IS A DISTINCT IDEA, NOT A PARAMETER SWEEP. The A2 census counts `attacks`, and
`wilsonByAttack` exists precisely because 80 of printer.stream's 83 were two functions applied to
40 reels each. Five variants of "a falsy flag" would be ONE idea; they are grouped as one attack
below, and the count reported is the number of distinct refusal-states attempted.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import frame_authority as FA


def _contract():
    return list(FA.EXTRACTION_CONTRACT)


#: Each entry is ONE distinct idea about a state in which the gate MUST refuse (or must allow).
#: (name, row, must_release, why_it_matters)
ATTACKS = (
    ("a seal that never looked", {}, False,
     "no evidence at all — nobody-looked must never release"),

    ("a seal predating the contract", {"promptVer": "p1", "extracted": None}, False,
     "it certifies a reader but never says WHAT it took; an unstated fact is an unextracted one"),

    ("a bare 'nothing was taken'",
     {"extracted": [], "extractedWhy": "nothing was taken", "rows": 0}, False,
     "the DEFAULT branch for any sweep that grounded no rows — it says the sweep found nothing, "
     "NOT that anyone established there was nothing to find. Six of his 31 real seals look like "
     "this, and the loose read would have released all six"),

    ("a falsy examinedEmpty",
     {"extracted": [], "extractedWhy": "nothing was taken", "rows": 0, "examinedEmpty": False}, False,
     "the sweep answering NO is not the sweep declaring emptiness; only True is a declaration"),

    ("a partial contract",
     {"extracted": ["name"], "rows": 2}, False,
     "naming one fact of three is not the contract — location and provenance are still unextracted"),

    ("a non-list `extracted`",
     {"extracted": "name,location,provenance", "rows": 2}, False,
     "a string that happens to contain the words is not a list of facts"),

    ("a declared examined-empty seal",
     {"extracted": [], "extractedWhy": "examined and there was nothing to take",
      "examinedEmpty": True, "rows": 0}, True,
     "HIS RULING — this one MUST release, or the ruling was never implemented and the gate is "
     "merely stuck shut. A lock that only ever refuses proves nothing about judgement"),

    ("a fully covered seal", {"extracted": None, "rows": 3}, True,
     "the ordinary success path — filled in at runtime with the real contract"),
)


def run():
    """-> (attempts, refused_correctly, rows). Pure; touches nothing."""
    rows, ok = [], 0
    for name, row, must_release, why in ATTACKS:
        r = dict(row)
        if name == "a fully covered seal":
            r["extracted"] = _contract()
        released, said = FA.seal_releases_frames(r)
        correct = (bool(released) == bool(must_release))
        ok += 1 if correct else 0
        rows.append({"attack": name, "expected": "release" if must_release else "REFUSE",
                     "got": "release" if released else "REFUSE",
                     "correct": correct, "why": why, "said": str(said)[:120]})
    return len(ATTACKS), ok, rows


def main(argv):
    n, ok, rows = run()
    bank = "--bank" in argv
    print("\nA2 — frame.release: can the gate before a deletion refuse when it must?\n")
    for r in rows:
        print("  %s %-34s expected %-7s got %-7s" %
              ("✅" if r["correct"] else "❌", r["attack"], r["expected"], r["got"]))
        if not r["correct"]:
            print("       ⚠ %s" % r["why"])
            print("       said: %s" % r["said"])
    print("\n  %d of %d distinct states answered correctly" % (ok, n))
    if not bank:
        print("  (report only — pass --bank to record this as evidence)")
        return 0 if ok == n else 1
    if ok != n:
        print("  🔴 NOT BANKING — a harness that failed its own attempts is not evidence.")
        return 1
    import self_arming as SA
    row = SA.bank("frame.release", "sabotage", "frame_release_wilson", n=n, k=ok,
                  attacks=n,
                  note="each attack is a DISTINCT refusal-state of seal_releases_frames, not a "
                       "parameter sweep; the two must-release cases are included so the lock "
                       "cannot pass by refusing everything")
    print("  banked: %s" % {k: row.get(k) for k in ("lock", "kind", "src", "n", "k", "attacks")})
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
