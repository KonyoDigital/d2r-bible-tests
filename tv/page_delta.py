# -*- coding: utf-8 -*-
"""REG-1753 (#160) - DID THE PAGE CHANGE, OR ONLY ITS BUILD STAMP?

Every version bump rewrites exactly ONE line of bible.html (tv/bump_version.py, the only correct way to stamp):

      window.D2R_BUILD = { id:'vN', name:'vN - ...', date:'YYYY-MM-DD', note:'...' };

The pre-push hook keyed its render gate (3-5 min) and its Playwright smoke (~2 min) on the bare file NAME, so a
console-only ship paid both to re-grade a page whose only change was its version string. MEASURED on the pushes of
10-02/10-03 (v3562, v3563, v3565, v3566 - every one console-only): render 2m56s-5m04s and smoke 2m06s-2m16s of a
8m16s-11m27s gate - more than half of every push.

The stamp cannot move what a render or a smoke grades: the build badge that shows it fits itself (bible.html v2466 -
id + date always survive, the name is shown only when it fits, measured after render), and no smoke spec reads it.

    python3 tv/page_delta.py --range A..B    exit 0 = the page changed beyond its stamp -> run the gates
    python3 tv/page_delta.py --cached        exit 1 = the page did not change, or only its stamp line did -> skip

FAIL CLOSED. Anything this cannot read - git failing, a bad range, an undecodable diff - answers 0 (changed), so the
gates run. A stamp line in any shape but bump_version's own (code appended to it, a hand-edit) is a page change.
Only the render/smoke TRIGGERS ask this; the deploy still keys on the file name, so the new stamp still publishes.
[[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PAGE = "bible.html"

# bump_version's line, whole: id, name, date, note in that order, single-quoted, nothing before or after it.
STAMP_LINE = re.compile(
    r"^\s*window\.D2R_BUILD = \{ id:'v\d+(?:\.\d+)*', name:'(?:[^'\\]|\\.)*', "
    r"date:'\d{4}-\d{2}-\d{2}', note:'(?:[^'\\]|\\.)*' \};\s*$")


def stamp_only(diff_text):
    """True when a unified diff changes at least one line and EVERY changed line is a whole build-stamp line."""
    changed = 0
    for line in (diff_text or "").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line and line[0] in "+-":
            changed += 1
            if not STAMP_LINE.match(line[1:]):
                return False
    return changed > 0


def _git(args, repo):
    return subprocess.run(["git"] + args, cwd=repo, capture_output=True,
                          encoding="utf-8", errors="strict", timeout=60)


def page_changed(git_args, repo=None):
    """-> (changed, why). changed is True when the page changed beyond its stamp OR nothing could be read
    (fail closed); False when the page is untouched by git_args or only its stamp line moved."""
    repo = repo or REPO
    try:
        names = _git(["diff", "--name-only"] + list(git_args) + ["--", PAGE], repo)
        if names.returncode != 0:
            return True, "git could not list the change (%s) - UNKNOWN, so the gates run" % (
                (names.stderr or "").strip()[:120] or "exit %d" % names.returncode)
        if not names.stdout.strip():
            return False, ""
        diff = _git(["diff", "-U0", "--no-color", "--no-ext-diff"] + list(git_args) + ["--", PAGE], repo)
        if diff.returncode != 0:
            return True, "git could not diff the page - UNKNOWN, so the gates run"
        if stamp_only(diff.stdout):
            return False, ("page_delta: bible.html changed ONLY its build stamp (window.D2R_BUILD) - "
                           "not a page change, so render + smoke have nothing new to grade (REG-1753)")
        return True, ""
    except Exception as e:  # undecodable bytes, no git, a timeout: say so and run the gates
        return True, "page_delta could not read the change (%s) - UNKNOWN, so the gates run" % (
            type(e).__name__,)


def main(argv):
    if len(argv) == 1 and argv[0] == "--cached":
        args = ["--cached"]
    elif len(argv) == 2 and argv[0] == "--range" and argv[1]:
        args = [argv[1]]
    else:
        print("usage: page_delta.py --range A..B | --cached   (exit 0 = page changed, 1 = it did not)")
        return 0                       # a malformed call is not evidence the page is unchanged
    changed, why = page_changed(args)
    if why:
        print(why)
    return 0 if changed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
