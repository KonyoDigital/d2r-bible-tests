# -*- coding: utf-8 -*-
"""THE ITEM TABLES A CHARACTER SAVE NEEDS, FROM HIS OWN INSTALL — nothing more.

`tv/d2s_read.py` turns a .d2s into items. A save stores almost nothing about an item in plain
bytes: how wide each property is, what a 3-letter code is called, which unique a 12-bit id names —
all of it lives in the game's own excel tables. This file pulls exactly the columns the reader
needs, from the CASC of the install on this machine, into a GENERATED `tv/item_tables.json`.
Same pattern as `affix_lexicon.py` (it reuses `affix_lexicon._pull`): `build()` pulls, `--write`
stores, `load()` reads, a `sourceHash` says which install produced it, and no install is UNKNOWN —
never a crash, never a guess.

    stats      per ItemStatCost id: name, saveBits, saveAdd, saveParamBits (item bitstream)
               and csvBits, csvParam (the character 'gf' section — a DIFFERENT width: strength is
               8 bits on an item and 10 in the stats block; reading one with the other derails)
    items      per code: display name, kind armor|weapon|misc, stackable (a 9-bit quantity field)
    uniques    per *ID: display name, key (the table's `index`), code
    setItems   per *ID: display name, key, set, code
    runewords  per 1-BASED runes.txt row: display name, key (the `Name` column)

=== MEASURED ON HIS INSTALL, 2026-09-25 ===
The eight excel tables `_pull` returns are byte-identical to the copies the study decoder was proven
with. Display names come from `item-names.json` / `item-runes.json`, because a table key is not
what the game prints: 97 unique keys differ from their display string (`Thudergod's Vigor` is the
key of Thundergod's Vigor, `Mindrend` of Skull Splitter), and 14 set-item keys do.

⚠⚠ THE RUNEWORD KEY AND THE ROW DISAGREE FROM ROW 79 ON, AND THIS FILE DOES NOT PICK ONE.
`runes.txt` has no `Runeword80`: row 79 is `Runeword79 Madness`, row 80 is `Runeword81 Malice`. A
save stores a 12-bit runeword id, and on his saves `id - 26` named the right runeword by BOTH
readings (Breath of the Dying 37 -> row/key 11, Fortitude 67 -> 41, Chains of Honor 40 -> 14). From
row 80 on the two readings name DIFFERENT runewords (Spirit is row 128 but `Runeword130`), and no
save on hand has one there. Both are stored; `d2s_read` names a runeword only where they agree and
says UNKNOWN, with both candidates, where they do not. [[unknown-stays-unknown]]
"""
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass                      # console encoding only; a failure here changes no fact the tables hold

SKIP = 77
STORE = os.path.join(HERE, "item_tables.json")

#: (label, CASC path). ORDER IS FIXED — sourceHash is computed over it.
SOURCES = [
    ("itemstatcost", r"data:data\global\excel\itemstatcost.txt"),
    ("armor",        r"data:data\global\excel\armor.txt"),
    ("weapons",      r"data:data\global\excel\weapons.txt"),
    ("misc",         r"data:data\global\excel\misc.txt"),
    ("uniqueitems",  r"data:data\global\excel\uniqueitems.txt"),
    ("setitems",     r"data:data\global\excel\setitems.txt"),
    ("runes",        r"data:data\global\excel\runes.txt"),
    ("itemnames",    r"data:data\local\lng\strings\item-names.json"),
    ("itemrunes",    r"data:data\local\lng\strings\item-runes.json"),
]
#: Without these the reader cannot decode a single bit, so a build missing any of them is refused.
REQUIRED = ("itemstatcost", "armor", "weapons", "misc", "uniqueitems", "setitems", "runes")


def _pull(casc_path):
    """-> bytes or None. ⚠ NEVER wrap this in `perl -e 'alarm N; exec'` — see affix_lexicon._pull."""
    import affix_lexicon
    return affix_lexicon._pull(casc_path)


def _rows(blob):
    """A tab-separated excel table -> [dict per row], header row as keys. None if nothing arrived."""
    if blob is None:
        return None
    txt = blob.decode("utf-8-sig", "replace")
    lines = [l.rstrip("\r") for l in txt.split("\n") if l.strip()]
    if not lines:
        return None
    hdr = lines[0].split("\t")
    out = []
    for l in lines[1:]:
        c = l.split("\t")
        out.append({h: (c[i].strip() if i < len(c) else "") for i, h in enumerate(hdr)})
    return out


def _strings(blob):
    """item-*.json [{Key, enUS}] -> {Key: enUS}; None when absent OR unparseable (never {})."""
    if blob is None:
        return None
    try:
        rows = json.loads(blob.decode("utf-8-sig", "replace"))
    except ValueError:
        return None
    m = {}
    for e in rows or ():
        k, v = str((e or {}).get("Key") or ""), str((e or {}).get("enUS") or "")
        if k and v:
            m.setdefault(k, v)
    return m


def _int(s):
    s = str(s or "").strip()
    return int(s) if s.lstrip("-").isdigit() else 0


def build():
    """-> (tables dict, None) or (None, reason). Pulls everything; writes nothing."""
    blobs = {label: _pull(path) for label, path in SOURCES}
    absent = [label for label, _ in SOURCES if blobs[label] is None]
    missing = [label for label in REQUIRED if label in absent]
    if missing:
        import affix_lexicon as _A
        return None, ("could not pull %s — extractor %s, install %s. Without them no bit of an item "
                      "can be read, so there is no table, not an empty one"
                      % (", ".join(missing), "present" if os.path.exists(_A.EXTRACT) else "MISSING",
                         "present" if os.path.isdir(os.path.join(_A.D2R, "Data")) else "MISSING"))
    names = _strings(blobs["itemnames"])
    runes_s = _strings(blobs["itemrunes"])
    unreadable = [lbl for lbl, m in (("itemnames", names), ("itemrunes", runes_s))
                  if blobs[lbl] is not None and m is None]
    if unreadable:
        return None, "pulled but would not parse: %s — a corrupt source is not an empty one" % unreadable
    names, runes_s = names or {}, runes_s or {}

    def shown(key, fallback=None):
        return names.get(key) or runes_s.get(key) or fallback or key

    stats = {}
    for r in _rows(blobs["itemstatcost"]):
        sid = r.get("*ID") if "*ID" in r else r.get("ID")
        if not str(sid or "").isdigit():
            continue
        stats[str(int(sid))] = {"name": r.get("Stat") or "",
                                "saveBits": _int(r.get("Save Bits")),
                                "saveAdd": _int(r.get("Save Add")),
                                "saveParamBits": _int(r.get("Save Param Bits")),
                                "csvBits": _int(r.get("CSvBits")),
                                "csvParam": _int(r.get("CSvParam"))}
    items = {}
    for kind, label in (("armor", "armor"), ("weapon", "weapons"), ("misc", "misc")):
        for r in _rows(blobs[label]):
            code = r.get("code") or ""
            if not code:
                continue
            items[code] = {"name": shown(r.get("namestr") or code, r.get("name")),
                           "kind": kind, "stackable": r.get("stackable") == "1"}
    uniques = {}
    for r in _rows(blobs["uniqueitems"]):
        if str(r.get("*ID") or "").isdigit():
            uniques[str(int(r["*ID"]))] = {"name": shown(r.get("index")), "key": r.get("index"),
                                           "code": r.get("code") or ""}
    sets = {}
    for r in _rows(blobs["setitems"]):
        if str(r.get("*ID") or "").isdigit():
            sets[str(int(r["*ID"]))] = {"name": shown(r.get("index")), "key": r.get("index"),
                                        "set": shown(r.get("set")), "code": r.get("item") or ""}
    runewords = {}
    for i, r in enumerate(_rows(blobs["runes"])):
        key = r.get("Name") or ""
        runewords[str(i + 1)] = {"name": shown(key, r.get("*Rune Name")), "key": key}

    h = hashlib.sha256()
    for label, path in SOURCES:
        b = blobs.get(label)
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(hashlib.sha256(b if b is not None else b"<ABSENT>").hexdigest().encode("ascii"))
    return {
        "_comment": "GENERATED from the D2R CASC. Do not hand-edit - run: python3 tv/item_tables.py --write",
        "sourceHash": h.hexdigest(),
        "sourcesAbsent": absent,
        # ⚠ SAID, NOT IMPLIED: without the string tables every name below is a table KEY, and a key
        # is not what the game prints (Thudergod's Vigor). A reader must be able to tell.
        "namesFrom": "strings" if not ({"itemnames", "itemrunes"} & set(absent)) else "table keys",
        "counts": {"stats": len(stats), "items": len(items), "uniques": len(uniques),
                   "setItems": len(sets), "runewords": len(runewords)},
        "stats": stats,
        "items": items,
        "uniques": uniques,
        "setItems": sets,
        "runewords": runewords,
    }, None


_CACHE = [None]


def load(path=None):
    """-> tables dict, or None when never generated / unreadable. NEVER an empty dict."""
    if path is None and _CACHE[0] is not None:
        return _CACHE[0]
    try:
        with io.open(path or STORE, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None           # UNKNOWN, and callers say so: d2s_read reports "tables UNKNOWN"
    if not isinstance(d, dict) or not d.get("stats") or not d.get("items"):
        return None
    if path is None:
        _CACHE[0] = d
    return d


def verify():
    """-> (code, say). 0 fresh · 1 STALE · 77 cannot tell. ⚠ 77 IS NOT GREEN."""
    have = load()
    if have is None:
        return SKIP, "no item tables on this machine yet — UNKNOWN, not clean. Run --write."
    fresh, why = build()
    if fresh is None:
        return SKIP, "cannot re-derive here (%s), so freshness is UNKNOWN" % why
    if fresh.get("sourceHash") == have.get("sourceHash"):
        return 0, "item tables match the install (%s)" % ", ".join(
            "%s %d" % (k, v) for k, v in sorted((have.get("counts") or {}).items()))
    return 1, ("the install has changed since the item tables were generated: stored %s, now %s"
               % (str(have.get("sourceHash"))[:12], str(fresh.get("sourceHash"))[:12]))


def main(argv):
    if "--verify" in argv:
        c, say = verify()
        print(("   ✅ " if c == 0 else "   ⚠ ") + say)
        return c
    if "--write" in argv:
        t, why = build()
        if t is None:
            print("   ⏭  SKIP: %s" % why)
            return SKIP
        body = json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
        from bump_version import atomic_write
        atomic_write(STORE, body)
        print("   wrote %s (names from %s)" % (STORE, t["namesFrom"]))
        for k, v in sorted(t["counts"].items()):
            print("      %-10s %d" % (k, v))
        return 0
    c, say = verify()
    print(say)
    return c


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
