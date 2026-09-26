# -*- coding: utf-8 -*-
"""#27 — THE REPO IS PUBLIC, AND A HOME PATH NAMES HIS ACCOUNT. THE COUNT MAY ONLY GO DOWN.

MEASURED 2026-09-26 (HEAD 71bf3cf3): 113 literals of the form /Users/<name>/ across 65 tracked files. Two of them sat in
bible.html - the PUBLISHED page - as live code (the routine-status loader), and BLUEPRINT.md's generated map carried a
third. Those three are gone (the loader builds its paths from the page's own home; blueprint.render() writes ~/). The
rest are old handoffs, BUGS.md entries and docs: rewriting published history is his call, and git keeps it anyway. So
this is a RATCHET, not a wall - the same shape as verdict_provenance: every tracked file is pinned at its count, a file
may only keep or lower it, and a file with none may never gain one. A new /Users/<name>/ written into a doc, a law or
the page is refused at the gate, before it is published.

  · READ: `git ls-files` (every TRACKED file - what the public repo actually carries), text only.
  · the baseline is home_paths_baseline.json, written by a human act: `python3 tv/test_no_new_home_path_is_published.py
    --write-baseline`. Lowering a count needs no rewrite - the law only refuses a RISE.
  · DRIVEN: the counter is fed a small source holding a home path, an escaped regex (/^\\/Users\\/[^/]+\\//), a
    placeholder (/Users/<name>/) and a bare '/Users/' prefix - it must count exactly the home path.
RED_PROOF below.
"""
import io
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASELINE = os.path.join(HERE, "home_paths_baseline.json")

#: a real account's home: /Users/ then a name made of account characters, then a slash
HOME = re.compile(r"/Users/[A-Za-z0-9._-]+/")


def count(text):
    """-> how many home-path literals this text carries."""
    return len(HOME.findall(text or ""))


def census():
    """-> ({tracked path: count > 0}, why). None when git cannot be asked - UNKNOWN, never 'no paths'."""
    try:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=REPO, capture_output=True, timeout=60)
    except Exception as e:
        return None, "git could not be asked which files are tracked (%s)" % type(e).__name__
    if r.returncode != 0:
        return None, "git ls-files exited %s" % r.returncode
    out = {}
    for rel in r.stdout.decode("utf-8", "replace").split("\0"):
        if not rel:
            continue
        p = os.path.join(REPO, rel)
        try:
            with io.open(p, "rb") as fh:
                raw = fh.read(8 * 1024 * 1024)
        except OSError:
            continue
        if b"\0" in raw[:4096]:
            continue                                   # a binary file carries no literal we could publish as text
        n = count(raw.decode("utf-8", "replace"))
        if n:
            out[rel] = n
    return out, ""


def write_baseline():
    got, why = census()
    if got is None:
        raise SystemExit("refusing to write a baseline I could not measure: %s" % why)
    with io.open(BASELINE + ".tmp", "w", encoding="utf-8") as fh:
        json.dump({"total": sum(got.values()), "files": got}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(BASELINE + ".tmp", BASELINE)
    print("wrote %s: %d literal(s) in %d file(s)" % (BASELINE, sum(got.values()), len(got)))


class NoNewHomePathIsPublished(unittest.TestCase):

    def test_the_counter_counts_a_home_path_and_nothing_else(self):
        src = ("fetch('/Users/someone/Downloads/x.js')\n"          # 1 - a real home path
               "const onMac = /^\\/Users\\/[^/]+\\//.test(p);\n"    # an escaped regex: not a path
               "on his Mac the page lives under /Users/<name>/\n"   # a placeholder: not an account
               "if (u.startsWith('file:///Users/')) bad.push(u);\n")  # a bare prefix: not an account
        self.assertEqual(count(src), 1, "the counter does not count exactly the one real home path")

    def test_no_tracked_file_carries_more_home_paths_than_its_baseline(self):
        got, why = census()
        self.assertIsNotNone(got, "UNKNOWN, not passing: %s" % why)
        with io.open(BASELINE, encoding="utf-8") as fh:
            base = json.load(fh)["files"]
        self.assertGreater(sum(got.values()) + sum(base.values()), 0,
                           "PREMISE: the census and the baseline both read zero - the counter or the listing is blind")
        rose = sorted("%s: %d -> %d" % (f, base.get(f, 0), n) for f, n in got.items() if n > base.get(f, 0))
        self.assertEqual(rose, [], "these tracked files gained a home path (/Users/<name>/) - the repo is PUBLIC; write "
                                   "~/ or build the path from the running home: %s" % rose)

    def test_the_published_page_carries_none(self):
        with io.open(os.path.join(REPO, "bible.html"), encoding="utf-8") as fh:
            self.assertEqual(count(fh.read()), 0, "bible.html - the published page - names a home directory again")


#: this law asks git which files are tracked; a heart2 sandbox is a plain copy, so it borrows the .git (APFS clone,
#: shared blocks, a write in the sandbox cannot reach his history) - test_tasks_ships_are_recorded does the same
PROOF_NEEDS = ["../.git"]

RED_PROOF = [
    {
        "why": "#27 - the routine loader names his account in the published page again",
        "file": "bible.html",
        "find": "    _v41_HOME + 'Downloads/routine_status.js',\n",
        "replace": "    '/Users/konyo/Downloads/routine_status.js',\n",
        "matches": 1,
    },
    {
        "why": "#27 - the counter stops recognising a home path, so every rise is invisible",
        "file": "test_no_new_home_path_is_published.py",
        "find": "HOME = re.compile(r\"/Users/[A-Za-z0-9._-]+/\")\n",
        "replace": "HOME = re.compile(r\"/Users/[A-Za-z0-9._-]+/NOPE\")\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    if "--write-baseline" in sys.argv:
        write_baseline()
    else:
        unittest.main(verbosity=2)
