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


def _norm_key(s):
    """bible.html's _normKey, mirrored: NFKD, curly quotes -> ', dashes -> -, lowercase, alphanumerics only."""
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s if s is not None else ""))
    s = s.replace("\u2018", "'").replace("\u2019", "'").replace("\u02bc", "'").replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def unique_roster(src):
    """{normKey: canonical} over ITEM_VALUE and _UNI_EXTRA - the names the board's resolver can count."""
    out = {}
    for marker in ("window.ITEM_VALUE = ", "const _UNI_EXTRA = "):
        try:
            i = src.index(marker)
            a = src.index("{", i)
            depth = 0
            for k in range(a, len(src)):
                if src[k] == "{":
                    depth += 1
                elif src[k] == "}":
                    depth -= 1
                    if depth == 0:
                        for name in json.loads(src[a:k + 1]):
                            out.setdefault(_norm_key(name), name)
                        break
        except Exception:
            continue
    return out


def seed_name(n, roster):
    """-> the name to SEED for a ledger key, or None when the board could never count it.

    ⚠ REG-1274 — the v3313 bake copied `Harlequin Crest (Shako)` (a vault-key spelling sitting in his
    foundLog, v1933 debris) straight into _GRAIL_SEED. The floor then wrote a key d2rResolveItem calls
    unknown and funiScan did not count - MEASURED: seeding the resolvable `Harlequin Crest` moved a real
    page's found 297 -> 298. A trailing parenthetical is folded to its roster name; a name the roster cannot
    match at all is REPORTED and not seeded (report, never remove: his ledger keeps it)."""
    if _norm_key(n) in roster:
        return n
    bare = re.sub(r"\s*\([^)]*\)\s*$", "", n)
    if bare != n and _norm_key(bare) in roster:
        return roster[_norm_key(bare)]
    return None


def one_shot_owned(src):
    """Names a boot one-shot applies with its own provenance. Seeding them is refused. -> set

    ⚠ REG-1271 — READ FROM EACH APPLY, NEVER FROM A LINE WINDOW. This took every quoted 3-40 char
    string between the FIRST line naming d2r_v1692FleshrenderApplied (-12) and the LAST naming
    d2r_v1693RulingApplied (+60). A backup list at bible.html:~10296 later named the Fleshrender flag,
    so the window grew to ~36,500 lines and this returned 25,522 "names" - and before that growth it
    had not held The Diggler's apply, so the v3313 bake SEEDED Fleshrender, Gloom's Trap and The
    Diggler, the three names rule 4 exists to refuse (v1693's own law: a second witness changes what
    'honest' means). Every one-shot applies through `chronicleApply({ wouldAdd: { uniques: [...] } })`
    immediately before it sets its own `d2r_v...Applied` flag, so the names are read from THAT call,
    anchored on THAT flag - exactly the twelve the specs count. [[source-reading-guard]] §3
    """
    out = set()
    for got in one_shot_names_by_flag(src).values():
        out |= got
    return out


def one_shot_names_by_flag(src):
    """{flag: {names}} - each boot one-shot's names, read from its own chronicleApply (see one_shot_owned)."""
    by = {}
    for m in re.finditer(r"setItem\('(d2r_v\d{3,4}[A-Za-z]*Applied)',\s*'1'\)", src):
        names = set()
        st = src.rfind("chronicleApply(", 0, m.start())
        if st < 0 or m.start() - st > 2500:
            continue                          # a flag with no apply beside it (a repair guard) names nothing
        blk = src[st:m.start()]
        a = blk.find("uniques:")
        if a < 0:
            continue
        b = blk.find("], sets", a)
        arr = blk[a:b if b > a else len(blk)]
        if "name:" in arr:                    # [{ name: 'X', date: '...' }] - never read the dates as names
            got = re.findall(r"name:\s*(?:'([^']+)'|\"([^\"]+)\")", arr)
        else:                                 # ['X', "Y"]
            got = re.findall(r"'([^']+)'|\"([^\"]+)\"", arr)
        names |= {x or y for x, y in got if (x or y)}
        if names:
            by.setdefault(m.group(1), set()).update(names)
    return by


#: ⚠⚠ v3327 — SEEDED NAMES THE GAME LISTS AS REMAINING, DECLARED RATHER THAN SILENTLY KEPT.
#:
#: A first-found date is a HISTORICAL POSITIVE; the Remaining list is PRESENT OWNERSHIP. Found and
#: later sold satisfies both, so a name on both lists is not automatically wrong — and deleting a
#: real find is a worse error than keeping a questionable one. [[stale-reading]] §8: never compare
#: a positive and a negative observation as flat set membership.
#:
#: ⚠ BUT A DECLARATION IS NOT A LOOPHOLE. Only a name carrying its OWN distinct date may be
#: declared. The 15 that shipped in v3313 all shared ONE stamp, "Sep 16, 2026 · 15:28" — fifteen
#: set pieces are not found in one minute, so that date orders against nothing and the name is
#: UNDATABLE. Those were REMOVED, not declared, and the law refuses any declaration whose stamp is
#: shared by five or more pieces. [[unknown-stays-unknown]]
SEED_EXEMPT = {
    "Laying of Hands (bramble mitts)":
        "seeded Aug 24, 2026 - 01:10, its own distinct stamp, while the game lists it Remaining. "
        "Found-then-sold satisfies both readings, so this is SURFACED for his ruling rather than "
        "stripped. Remove it only if he says he never had it.",
    "Taebaek's Glory (ward)":
        "seeded Aug 23, 2026 - 17:46, its own distinct stamp, while the game lists it Remaining. "
        "Same reading as above: a real find he no longer holds is not a fabricated date.",
}


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


#: v3475 (#159) — where the last check is remembered. Tests point TV_BAKE_RECEIPT elsewhere; the
#: live file is gitignored and named in run_gates._LIVE_STATE, so a test that writes it FAILS on CI.
RECEIPT = os.environ.get("TV_BAKE_RECEIPT") or os.path.join(HERE, ".bake_seed_receipt.json")


def receipt_path():
    """Where the receipt lives, for the WRITER and the DOCTOR alike. -> str

    ⚠ #219 follow-up — the second eye on ea3f05da: write_receipt read `env or RECEIPT` while the
    doctor row read `env or <its own hard-coded path>`, so patching RECEIPT moved the writer and not
    the reader — the receipt landed in the patched path and the row still opened the live file.
    One resolver, two readers. [[copy-drift]]
    """
    return os.environ.get("TV_BAKE_RECEIPT") or RECEIPT

def write_receipt(outcome, **facts):
    """Remember THAT the seed was checked, WHEN, and what it found. Never silent, never fatal.

    ⚠⚠ #159 — THE VERDICT WAS PRINTED AND THEN GONE. Asked 2026-09-23, the baker answered "no
    drift — the shipped seed already matches his board" to stdout and left no artefact, so nothing
    on his console could answer "when was the seed last checked against his board", and a heart row
    had nothing to read. A verdict with no expiry is not a verdict. [[stale-reading]] §4
    """
    import time as _t
    path = receipt_path()
    rec = dict(facts, outcome=outcome, ts=int(_t.time() * 1000))
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception as e:
        print("⚠ the check ran but its receipt could not be written (%s) — nothing will remember "
              "it" % type(e).__name__)
    return rec


def bake(write=False, root=None):
    db = find_board_store(root)
    if not db:
        print("no board store found under %s" % (root or WEBKIT))
        print("   (is the console pywebview? has the board ever been opened?)")
        write_receipt("no-store", mode=("write" if write else "report"))
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
    roster = unique_roster(src)
    unseedable = []
    for n, d in fl.items():
        if n in sp_set or n in owned or not d:
            continue                      # rules 3 + 4
        sn = seed_name(n, roster) if roster else n      # REG-1274 — rule 5: seed only what the board can count
        if sn is None:
            unseedable.append(n)
            continue
        # ⚠ rule 4 stays ONE line above - a second copy here made that refusal's own proof BLIND (REG-1274);
        # a suffixed one-shot spelling that folds onto a one-shot name is caught by the seed law at the gate.
        new_grail.setdefault(sn, d)
    if unseedable:
        print("not seeded (the board's roster cannot count them - his ledger keeps them): %s" % ", ".join(sorted(unseedable)[:12]))

    assert set(old_set) <= set(new_set), "the bake would LOSE set names"      # rule 2
    assert set(old_grail) <= set(new_grail), "the bake would LOSE grail names"

    print("board store : %s" % db.replace(os.path.expanduser("~"), "~"))
    print("his board   : setPieces %d · foundLog %d" % (len(sp), len(fl)))
    print()
    print("_SET_SEED   %3d -> %3d   (+%d)" % (len(old_set), len(new_set), len(new_set) - len(old_set)))
    print("_GRAIL_SEED %3d -> %3d   (+%d)" % (len(old_grail), len(new_grail), len(new_grail) - len(old_grail)))
    drift = (len(new_set) - len(old_set)) + (len(new_grail) - len(old_grail))
    _facts = dict(mode=("write" if write else "report"), boardSetPieces=len(sp),
                  boardFoundLog=len(fl), setSeed=[len(old_set), len(new_set)],
                  grailSeed=[len(old_grail), len(new_grail)], drift=drift)
    if not drift:
        write_receipt("no-drift", **_facts)
        print("\nno drift — the shipped seed already matches his board.")
        return 0
    if not write:
        write_receipt("drift", **_facts)
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
    # v2712 — atomic, because his console re-reads bible.html per request and
    # `open(...,"w")` leaves it ZERO BYTES until the 6 MB write completes.
    # Measured: 4.8% of concurrent reads saw an empty file. [[stale-render]]
    _tmp = BIBLE + ".tmp"
    with open(_tmp, "w", encoding="utf-8") as _fh:
        _fh.write(s)
    os.replace(_tmp, BIBLE)
    write_receipt("written", **_facts)
    print("\nWRITTEN. Now re-run the three specs above and update what they report.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="apply the bake (default: report only)")
    ap.add_argument("--root", default=None, help="WebKit Default dir (for fixtures)")
    a = ap.parse_args()
    sys.exit(bake(write=a.write, root=a.root))
