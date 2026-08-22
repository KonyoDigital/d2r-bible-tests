"""v1966 — A COMMIT THAT NAMES A VERSION MUST CARRY THAT VERSION'S STAMPS.

Konyo's rule, already written down: "A vNNNN IS A SHIP, NOT A COMMIT — number ONLY commits that
bump the four stamps." Nothing enforced it.

WHAT IT COST. On 2026-08-22 `bump_version.py v1964` REFUSED — "apostrophe in note/name would break
the single-quoted D2R_BUILD literal", because the note said `read's`. The refusal was piped through
`tail -3` inside a background command and never read, so the four stamps stayed at v1963 while the
commit went out titled "v1963 + v1964". The code was correct and every gate and CI lane was green;
only the claim was false. The board reported one version behind what it carried.

WHY IT CHECKS THE HIGHEST VERSION NAMED, NOT THE FIRST. That subject named TWO versions. A gate
that read the first would have found v1963, matched the stamps, and passed — agreeing with the
mistake. The tip's stamps must equal the HIGHEST version the subject claims.

WHAT IT DELIBERATELY DOES NOT DO. It says nothing about commits that name no version (`test:`,
`ci:`, `docs:`) — those are exactly the commits his rule says must NOT be numbered. And it never
invents a version: if no `vNNNN` appears in the subject, it passes in silence.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402

# v1966 — SECOND TIME IN ONE NIGHT. test_store_isolation.py shipped without this an hour earlier and
# the same gate refused it. This file prints an em-dash and a checkmark in its verdict, so on a
# non-UTF-8 console it would crash WHILE REPORTING — and a gate that cannot print its own verdict is
# worse than no gate. Fixing the instance is not fixing the habit: any new tv/*.py entry point that
# prints non-ASCII needs this line.
_console_safe_enable()
REPO = os.path.dirname(HERE)

# The four surfaces bump_version.py writes. If it learns a fifth, this list must learn it too.
STAMPS = (
    ("bible.html",           re.compile(r"D2R_BUILD\s*=\s*\{\s*id:\s*'(v\d+)'")),
    ("tv/tv_diablo.py",      re.compile(r"^VERSION\s*=\s*[\"'](v\d+)", re.M)),
    ("tv/WINDOWS_SHIP.json", re.compile(r'"ver"\s*:\s*"(v\d+)"')),
    # THE FOURTH SURFACE, and the one this gate shipped without. bump_version.py:6-7 names four
    # places a version lives; the first draft of STAMPS listed three, so a tree whose control_app
    # stamp had been left behind would have passed a gate whose whole purpose is that they agree.
    # bump_version requires EXACTLY ONE literal occurrence (`s.count(...) != 1` raises), which is
    # what makes this pattern unambiguous — the file's other 11 "ver" keys are `_app_ver()` calls
    # and `st.get("ver")` reads, none of them a vNNNN literal.
    ("tv/control_app.py",    re.compile(r'"ver"\s*:\s*"(v\d+)"')),
)


def subject():
    out = subprocess.run(["git", "-C", REPO, "log", "-1", "--pretty=%s"],
                         capture_output=True, text=True)
    return (out.stdout or "").strip()


def leading_versions(subj):
    """Versions in the LEADING cluster only — the part before the first separator.

    His convention, measured over 40 commits: 33 subjects START with vNNNN and NOT ONE mentions a
    version mid-text. Matching a version anywhere would therefore cost nothing today and refuse a
    perfectly good push the first time he writes "revert what v1900 broke" — a gate whose first
    real firing is a false positive teaches everyone to bypass it.

    The leading cluster still holds MORE THAN ONE version, which is the case that matters:
    "v1963 + v1964 — ..." must be read as claiming BOTH, and judged on the higher.
    """
    head = re.split(r"\s+[\u2014\u2013:]|\s+-\s+", subj, 1)[0]
    if not re.match(r"^v\d{3,5}\b", head.strip()):
        return []
    return re.findall(r"\bv(\d{3,5})\b", head)


def read_stamps():
    found = {}
    for rel, pat in STAMPS:
        path = os.path.join(REPO, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            m = pat.search(fh.read())
        found[rel] = m.group(1) if m else None
    return found


def main():
    subj = subject()
    named = leading_versions(subj)
    if not named:
        print("version-stamp: the subject names no version up front — nothing to check.")
        return 0

    want = "v%s" % max(int(n) for n in named)
    stamps = read_stamps()
    missing = [rel for rel, v in stamps.items() if v is None]
    wrong = {rel: v for rel, v in stamps.items() if v is not None and v != want}

    if missing:
        print("version-stamp: could not read a stamp from: %s" % ", ".join(sorted(missing)))
        print("               a gate that cannot read its input measures nothing — refusing.")
        return 1
    if wrong:
        print('version-stamp: the subject claims %s but the stamps say otherwise.' % want)
        for rel in sorted(wrong):
            print("               %-22s %s" % (rel, wrong[rel]))
        print("               Either bump (python3 tv/bump_version.py %s \"name\" \"note\") or drop" % want)
        print("               the version from the subject. A vNNNN is a SHIP, not a commit.")
        print("               ⚠ bump_version REFUSES apostrophes in the name/note, and its refusal")
        print("                 is ONE LINE AT THE TOP — never pipe it through `tail`.")
        return 1

    print("version-stamp: ✅ %s claimed and all %d stamps agree." % (want, len(stamps)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
