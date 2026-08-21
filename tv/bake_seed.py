#!/usr/bin/env python3
"""BAKE THE SHIPPED SEED FROM HIS ACTUAL BOARD — report by default, write only when asked.

Konyo, 2026-08-21: "yes regenerate the seed, export it? you do it.. make it an automatic thing maybe
that an AI does on regular tasked engine?"

WHY THIS IS A SCRIPT AND NOT A ONE-OFF EDIT. I hand-built a seed from his board at 00:30 and was two
steps from shipping it. By 03:00 — same night, same conversation — his board had moved from 117
set pieces / 389 ledger rows to 118 / 396. A hand-baked seed is stale the moment he plays, and every
manual bake also drags the v659 / v1692 / v1693 recalibration behind it. The answer is not to bake
more carefully; it is to stop baking by hand.

WHAT THE SEED IS FOR. bible.html ships `_GRAIL_SEED` and `_SET_SEED` so a FRESH profile — a new
browser, cleared site data, the Windows machine — shows his real progress instead of an empty board.
It never affects the board he uses: that reads its own localStorage. Measured 2026-08-22: a fresh
profile showed 107/135 pieces and 248/403 uniques while his own board showed 116/135 and ~272.

WHERE HIS BOARD ACTUALLY LIVES, which took a long detour to find. NOT Chrome — Chrome holds a
convincing but months-stale copy. The console is pywebview/WKWebView, and its localStorage is
sqlite under ~/Library/WebKit/com.apple.python3/WebsiteData/Default/<hash>/<hash>/LocalStorage/,
values in UTF-16-LE. Three origin dirs exist; the board is the one that actually has d2r_foundLog.
⚠ Copy them to SEPARATE directories — copying all three into one lets the small ones overwrite the
board, and the script then cheerfully reports zero.

SAFETY, in order of how much it would hurt to get wrong:
  1. REPORT ONLY unless --write. A seed is his history.
  2. NEVER SHRINK. Every name already in the shipped seed survives, always. A bake that can lose a
     name is the one failure here that is not re-derivable.
  3. NEVER SEED A PIECE THE GAME SAYS HE LACKS. _SET_MISSING is the game's own Remaining page; a
     piece on it must not be seeded and then removed again by the boot repair.
  4. NEVER SEED A NAME A BOOT ONE-SHOT OWNS. v1692/v1693 apply specific finds with their own dated
     provenance; seeding those changes what "honest" means in those specs, and v1693 refuses it in
     as many words.
"""
import argparse
import glob
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIBLE = os.path.join(REPO, "bible.html")

# v1947 — MAKE OUR OWN OUTPUT SURVIVE HIS CONSOLE. This file prints non-ASCII (arrows, the warning
# sign) and on a non-UTF-8 console — his Windows machine — that dies inside print() while REPORTING,
# so a run that WORKED exits 1 with a UnicodeEncodeError instead of its answer. REG-044/054/077 are
# three separate versions of exactly that. tv/test_control.py enforces it on every CLI here.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()

WEBKIT = os.path.expanduser(
    "~/Library/WebKit/com.apple.python3/WebsiteData/Default")


def find_board_store(root=None):
    """The origin store that actually holds his board.

    ⚠ RANK BY HOW MUCH LEDGER IS IN IT, NOT BY FILE SIZE, AND NOT BY WHETHER THE KEY EXISTS.
    Both weaker tests were tried and both are wrong:
      · file size alone picks whichever origin happens to be fattest — his console writes three,
        and the board is not always the biggest;
      · "has a d2r_foundLog key" passes a store whose ledger is `{}`, which is exactly what a
        freshly-created or decoy origin looks like.
    A store with a real ledger beats one with an empty one, however large the file. Caught by
    tv/test_bake_seed.py, which plants a bigger decoy carrying an empty foundLog."""
    root = root or WEBKIT
    best = None
    for db in glob.glob(os.path.join(root, "*", "*", "LocalStorage", "localstorage.sqlite3")):
        try:
            con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
            row = con.execute(
                "SELECT value FROM ItemTable WHERE key='d2r_foundLog'").fetchone()
            con.close()
        except Exception:
            continue
        if not row or not row[0]:
            continue
        try:
            raw = row[0]
            txt = raw.decode("utf-16-le") if isinstance(raw, (bytes, bytearray)) else str(raw)
            n = len(json.loads(txt) or {})
        except Exception:
            n = 0
        if n <= 0:
            continue
        if best is None or n > best[1]:
            best = (db, n)
    return best[0] if best else None


def read_board(db):
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    out = {}
    for k, v in con.execute("SELECT key, value FROM ItemTable"):
        try:
            out[k] = v.decode("utf-16-le") if isinstance(v, (bytes, bytearray)) else str(v)
        except Exception:
            out[k] = ""
    con.close()
    fl = json.loads(out.get("d2r_foundLog") or "{}")
    sp = json.loads(out.get("d2r_setPieces") or "[]")
    return fl, sp


def _lit(src, name):
    m = re.search(r"const %s = (\{.*?\});" % name, src, re.S)
    return json.loads(m.group(1)), m


def one_shot_owned(src):
    """Names a boot one-shot applies with its own provenance. Seeding them is refused."""
    lines = src.split("\n")
    lo, hi = None, None
    for i, l in enumerate(lines):
        if "d2r_v1692FleshrenderApplied" in l and lo is None:
            lo = max(0, i - 12)
        if "d2r_v1693RulingApplied" in l:
            hi = i + 60
    if lo is None or hi is None:
        return set()
    region = "\n".join(lines[lo:hi])
    return {n for pair in re.findall(r"'([^']{3,40})'|\"([^\"]{3,40})\"", region) for n in pair if n}


def game_says_missing(src):
    m = re.search(r"window\._SET_MISSING\s*=\s*(\{.*?\});", src, re.S)
    if m:
        try:
            return set((json.loads(m.group(1)) or {}).get("names") or [])
        except Exception:
            pass
    for p in sorted(glob.glob(os.path.join(HERE, "remaining", "sets_*.json")), reverse=True):
        try:
            d = json.load(open(p, encoding="utf-8"))
            return set(d.get("names") or [r["piece"] for r in (d.get("rows") or [])])
        except Exception:
            continue
    return set()


def bake(write=False, root=None):
    db = find_board_store(root)
    if not db:
        print("no board store found under %s" % (root or WEBKIT))
        print("   (is the console pywebview? has the board ever been opened?)")
        return 2
    fl, sp = read_board(db)
    src = open(BIBLE, encoding="utf-8").read()
    old_set, m_set = _lit(src, "_SET_SEED")
    old_grail, m_gr = _lit(src, "_GRAIL_SEED")
    missing = game_says_missing(src)
    owned = one_shot_owned(src)

    sp_set = set(sp)
    new_set = dict(old_set)
    for n in sp_set:
        if n in missing:
            continue                      # rule 3
        d = fl.get(n)
        if d:
            new_set.setdefault(n, d)
    for n in list(new_set):
        if n in missing and n not in old_set:
            del new_set[n]

    new_grail = dict(old_grail)
    for n, d in fl.items():
        if n in sp_set or n in owned or not d:
            continue                      # rules 3 + 4
        new_grail.setdefault(n, d)

    assert set(old_set) <= set(new_set), "the bake would LOSE set names"      # rule 2
    assert set(old_grail) <= set(new_grail), "the bake would LOSE grail names"

    print("board store : %s" % db.replace(os.path.expanduser("~"), "~"))
    print("his board   : setPieces %d · foundLog %d" % (len(sp), len(fl)))
    print()
    print("_SET_SEED   %3d -> %3d   (+%d)" % (len(old_set), len(new_set), len(new_set) - len(old_set)))
    print("_GRAIL_SEED %3d -> %3d   (+%d)" % (len(old_grail), len(new_grail), len(new_grail) - len(old_grail)))
    drift = (len(new_set) - len(old_set)) + (len(new_grail) - len(old_grail))
    if not drift:
        print("\nno drift — the shipped seed already matches his board.")
        return 0
    if not write:
        print("\n%d name(s) of drift. Nothing written (pass --write to apply)." % drift)
        print("⚠ A WRITE ALSO MOVES SEED-DERIVED SPEC CONSTANTS. Re-run these and read what they")
        print("   report — never derive the numbers on paper:")
        print("     tests/v659_grail_seed.spec.ts        seedN, found")
        print("     tests/v1692_tally_counts_the_chronicle.spec.ts   N_UNIQUES, N_AFTER, post-boot ledger")
        print("     tests/v1693_the_nine_applied.spec.ts N_RAW_UNIQUES, N_AFTER, N_V1692_ONLY")
        return 1
    def lit(d):
        return json.dumps({k: d[k] for k in sorted(d)}, ensure_ascii=True, separators=(",", ":"))
    s = src[:m_set.start(1)] + lit(new_set) + src[m_set.end(1):]
    m_gr2 = re.search(r"const _GRAIL_SEED = (\{.*?\});", s, re.S)
    s = s[:m_gr2.start(1)] + lit(new_grail) + s[m_gr2.end(1):]
    open(BIBLE, "w", encoding="utf-8").write(s)
    print("\nWRITTEN. Now re-run the three specs above and update what they report.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply the bake (default: report only)")
    ap.add_argument("--root", default=None, help="WebKit Default dir (for fixtures)")
    a = ap.parse_args()
    sys.exit(bake(write=a.write, root=a.root))
