# -*- coding: utf-8 -*-
"""v3294 — THE STANDING RULINGS, MARKED, WITH A DENOMINATOR THAT ADMITS WHAT IT CANNOT SEE.

Three times in one session a recorded ruling stopped me shipping the obvious fix, and each time I
found it by luck of grep:

    v1631  a TAB labels a ROOM, so the Forge tab wears the RUNE colour, not the gold a runeword's
           NAME is painted. His words: "these two colors cant be the same"
    v2397  the footer's hover wall was REMOVED on his instruction - "i dont want this mess when i
           hover over it all the time. i want it clean". Do not re-add it.
    —      test_a_lane_count_names_the_population_it_counted: "THE STRIP IS NOT THE DEFECT - DO
           NOT FIX IT. Its arithmetic is internally consistent."

⚠⚠ EXTRACTION WAS TRIED FIRST AND IT DOES NOT WORK. Four designs, measured 2026-09-18, with one
acceptance test: does it find those three?

    ⚠⚠ marker + prohibition language ....  223 entries, finds 0 of 3
    prohibition language, any marker ....  13,974 hits (2,547 even restricted to DO NOT / NEVER)
    topic + prohibition ................  usable counts, finds v2397, MISSES v1631
    topic + comment blocks, no filter ..  noisier (36 for "forge tab"), misses more

The reasons are structural, not fixable by a better regex: **the marker is not a reliable key**
(v1631 carries no warning marker at all; the other two use a single ⚠), and **the language is not
distinctive** - v1631's constraint is stated as a plain fact in his own words and contains no
prohibition word anywhere.

A 223-row index that omits every ruling that matters is WORSE than no index, because it reads as
complete. So this does not extract. It reads an explicit marker, and it says loudly how much it
cannot see. [[zero-needs-a-denominator]] [[unknown-stays-unknown]]

HOW TO MARK ONE, anywhere a comment can live:

    @@RULING v1631: a TAB labels a ROOM - the Forge tab wears --rar-rune, not the gold a
    runeword NAME is painted. Do not "sync" them.

Usage:
    python3 tv/rulings.py                 every marked ruling
    python3 tv/rulings.py rune tab        only those matching ALL the words
"""
import io
import os
import re
import sys

# ⚠ CAUGHT BY console_safe's OWN CLI, minutes after that CLI shipped: this file's docstring carries
# non-ASCII and it is an entry point, so on a cp1255 console it would crash WHILE PRINTING the
# index. The rule prescribed exactly this line and the tool found the file that needed it.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# @@RULING <optional vNNNN>: <the ruling, to the end of the comment run>
#
# ⚠ THE SIGIL IS "@@RULING", NOT "RULING:", AND THAT WAS MEASURED. A plain `RULING:` matched NINE
# existing places on its first run - comments quoting him with phrases like "HIS RULING:" - so the
# index would have opened with nine phantom entries. A marker that can collide with prose is not a
# marker. `@@RULING` occurs zero times in the repo today.
#
# ⚠ AND IT IS ASCII ON PURPOSE. A non-ASCII sigil inside a python entry point would trip the very
# encoding rule shipped one version earlier (console_safe.audit), which is a silly way to make a
# guard fight a guard.
MARK = re.compile(r"@@RULING\s*(v\d{3,4})?\s*:\s*(.+?)(?=\n\s*\n|\*/|$)", re.S)
SCAN_DIRS = ("tv",)
SCAN_FILES = ("bible.html", "BUGS.md", "hooks/pre-push")
EXT = (".py", ".html", ".md", ".ts", ".js")


# ⚠ THE TOOL AND ITS TEST MUST NOT INDEX THEMSELVES. Measured on the first run: 6 "rulings", of
# which TWO were this file's own usage example and the marker string inside the law's red-proof.
# An index that lists its own documentation as a standing ruling is 33% wrong on day one, and the
# entries look exactly like the real ones. These two files are the only places where the marker
# appears as an EXAMPLE rather than as a ruling, so they are the only exclusions — test files in
# general are NOT excluded, because a real ruling lives in one
# (test_a_lane_count_names_the_population_it_counted). [[presence-law-vs-reachability-law]]
SELF = ("rulings.py", "test_a_ruling_index_admits_what_it_cannot_see.py")


def _paths(root):
    out = [os.path.join(root, f) for f in SCAN_FILES]
    for d in SCAN_DIRS:
        base = os.path.join(root, d)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            if name.endswith(EXT):
                out.append(os.path.join(base, name))
    return [p for p in out
            if os.path.exists(p) and os.path.basename(p) not in SELF]


def scan(root=None):
    """-> [{file, line, version, text}] every MARKED ruling. Sorted and stable."""
    root = root or ROOT
    out = []
    for path in _paths(root):
        try:
            src = io.open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for m in MARK.finditer(src):
            body = " ".join((m.group(2) or "").split())
            if not body:
                continue
            out.append({
                "file": os.path.relpath(path, root),
                "line": src[:m.start()].count("\n") + 1,
                "version": m.group(1) or "",
                "text": body[:400],
            })
    out.sort(key=lambda r: (r["file"], r["line"]))
    return out


def _limit_sentence(n):
    return ("%d ruling(s) are MARKED. An UNMARKED ruling is invisible here, and absence from this "
            "list is not permission - it means nobody has marked it yet. BUGS.md holds the long "
            "form." % n)


def main(argv):
    words = [w.lower() for w in argv]
    rows = scan()
    total = len(rows)
    if words:
        rows = [r for r in rows
                if all(w in r["text"].lower() or w in r["file"].lower() for w in words)]
    if not rows:
        print("no MARKED ruling matches %r." % (" ".join(words) or "(everything)"))
        print("  " + _limit_sentence(total))
        return 0
    print("%d of %d marked ruling(s)%s\n"
          % (len(rows), total, (" matching %r" % " ".join(words)) if words else ""))
    for r in rows:
        t = r["text"]
        print("  %s:%d%s" % (r["file"], r["line"], ("  [" + r["version"] + "]") if r["version"] else ""))
        print("      %s\n" % (t[:200] + ("…" if len(t) > 200 else "")))
    print("  " + _limit_sentence(total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
