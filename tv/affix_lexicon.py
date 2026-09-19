# -*- coding: utf-8 -*-
"""v3364 (#60) — THE AFFIX LEXICON: every word D2R can put in an item name, from his own install.

HIS ASK: *"the vault needs to know every single item in its data base.. and the AI ITEM CHECKER it
goes through also does.. it also needs to know what to route to garbage and what is considered HIGH
QUALITY"*.

The vault could already name a UNIQUE, a SET piece and a RUNEWORD — 1,059 roster names between
three files. It could not name anything MAGIC or RARE, because those names are not a roster: they
are COMPOSED at drop time from four affix tables and a base type. I said once that magic and rare
"cannot have a roster" and he corrected me on the spot — the 28 GB install ships
`magicprefix`/`magicsuffix`/`rareprefix`/`raresuffix` plus the base tables, so there is no finite
name list but there IS a finite VOCABULARY. This file is that vocabulary.

=== MEASURED ON HIS OWN INSTALL, 2026-09-19 ===
    magicPrefix  269    magicSuffix  298
    rarePrefix    42    rareSuffix   152
    baseType     690    (armor 218 + weapons 307 + misc 170, DISTINCT)

⚠ `item-names.json` IS NOT A BASE-TYPE LIST AND USING IT AS ONE IS A REAL TRAP. It holds 1,593
names — the FULL item string table, uniques included: `Spirit Ward`, `Death Cleaver` and
`Venom Ward` are all in it. The base TYPES are the 690 from armor/weapons/misc. Conflating them is
what makes a unique look like a plain base. It is still pulled, because it resolves 96 of the 152
rare suffixes.

=== WHAT THIS DELIBERATELY DOES NOT DO ===
⛔ IT DOES NOT TOUCH `item_identity.BASE_TAILS` OR `_roster()`. The obvious next step — widen the
tail-strip with all 690 base types so `Ice Gorgon Crossbow` resolves — is REFUSED, on a measurement
taken with both sides case-folded (the first cut of that measurement compared lowercase roster
names against TitleCase item names, agreed no matter what was in it, and reported a reassuring 0):

    death cleaver -> death      spirit ward -> spirit      venom ward -> venom

Three of his UNIQUES would permanently collapse onto three RUNEWORDS, in `vault_key` AND
`chronicle_key`, and `_name_folder`'s merge-max never subtracts. There is no un-throw in Diablo and
there is no un-fold either. [[the-unjoined-end]]

=== THE REFUSAL DISCIPLINE, WHICH IS THE POINT ===
`classify()` returns a best parse or it returns UNKNOWN. It never returns a best PARTIAL. An
unmatched token, or two parses of different kinds, is UNKNOWN — because a wrong kind here becomes a
wrong routing decision about his loot, and [[unknown-stays-unknown]] is cheaper than a wrong
confident answer every single time.

MEASURED over his 43 real `unsure` names: GRAIL 14 · BASE 12 · MAGIC 8 · RARE 4 · UNKNOWN 5.
The 5 refusals are honest: `Storm Scarab` is one, because `scarab` is one of exactly SIX rare keys
with no display string in EITHER string table, so the game's own data cannot name it here.

⚠ THE SAFETY DIRECTION IS ASYMMETRIC AND IT IS CHECKED. A consumable or a bare base reading as
PROTECTED is the expensive error (his stash never empties); a grail reading as UNKNOWN merely costs
a second look. `Sacred Rondache`, `Bone Knife`, `Horadric Cube`, `Super Mana Potion`, `Small Charm`
and `Full Rejuvenation Potion` all land BASE, verified.
"""
import hashlib
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

SKIP = 77
STORE = os.path.join(HERE, "affix_lexicon.json")

#: ⚠ THE DEFAULTS ARE THE SURVIVING TOOLCHAIN, NOT /tmp. `extract_ui_icons.py` defaults these to
#: `/tmp/casc_extract` and `/tmp/CascLib/build`, and /tmp was wiped — so those defaults describe a
#: machine that no longer exists. The real binary and framework live under ~/casc-tools and were
#: verified running here. Env still wins, so nothing is hardcoded shut.
D2R = os.environ.get("D2R_INSTALL") or os.path.join(
    os.path.expanduser("~"), "CXPBottles", "Battle.net Desktop App",
    "drive_c", "Program Files (x86)", "Diablo II Resurrected")
EXTRACT = os.environ.get("CASC_EXTRACT",
                         os.path.join(os.path.expanduser("~"), "casc-tools", "casc_extract"))
FRAMEWORK = os.environ.get("CASC_FRAMEWORK",
                           os.path.join(os.path.expanduser("~"), "casc-tools", "CascLib", "build"))

#: (label, CASC path). ORDER IS FIXED — sourceHash is computed over it.
SOURCES = [
    ("magicprefix", r"data:data\global\excel\magicprefix.txt"),
    ("magicsuffix", r"data:data\global\excel\magicsuffix.txt"),
    ("rareprefix",  r"data:data\global\excel\rareprefix.txt"),
    ("raresuffix",  r"data:data\global\excel\raresuffix.txt"),
    ("armor",       r"data:data\global\excel\armor.txt"),
    ("weapons",     r"data:data\global\excel\weapons.txt"),
    ("misc",        r"data:data\global\excel\misc.txt"),
    ("nameaffixes", r"data:data\local\lng\strings\item-nameaffixes.json"),
    ("itemnames",   r"data:data\local\lng\strings\item-names.json"),
]


def _pull(casc_path, timeout=150):
    """-> bytes, or None. Streams to STDOUT; nothing is written to disk.

    ⚠⚠ THE ENV IS BUILT INSIDE THIS CALL AND THE HOUSE `perl -e 'alarm N; exec @ARGV'` IDIOM MUST
    NOT WRAP IT. MEASURED here, both ways, on the same file: direct -> rc 0, 59,837 bytes;
    perl-wrapped -> rc -6 and `dyld: Library not loaded: @rpath/casc.framework`. `/usr/bin/perl`
    is SIP-restricted, so dyld strips every `DYLD_*` variable across that exec and the extractor
    cannot find its own framework. The failure reads exactly like a missing toolchain, which is
    how a working install gets declared dead. `subprocess` carries its own timeout, so the wrapper
    buys nothing here anyway.
    """
    if not (os.path.exists(EXTRACT) and os.path.isdir(os.path.join(D2R, "Data"))):
        return None
    try:
        r = subprocess.run([EXTRACT, os.path.join(D2R, "Data"), casc_path],
                           env=dict(os.environ, DYLD_FRAMEWORK_PATH=FRAMEWORK),
                           capture_output=True, timeout=timeout)
    except Exception:
        return None
    return r.stdout if r.returncode == 0 and r.stdout else None


def _col0(blob):
    """-> [first column], header skipped. The excel tables are tab separated with a header row."""
    txt = (blob or b"").decode("utf-8-sig", "replace")
    lines = [l for l in txt.split("\n") if l.strip()]
    out = []
    for l in lines[1:]:
        c = l.split("\t")
        if c and c[0].strip():
            out.append(c[0].strip())
    return out


def _named(blob, col="name"):
    txt = (blob or b"").decode("utf-8-sig", "replace")
    lines = [l for l in txt.split("\n") if l.strip()]
    if not lines:
        return []
    hdr = lines[0].split("\t")
    i = hdr.index(col) if col in hdr else 0
    out = []
    for l in lines[1:]:
        c = l.split("\t")
        if len(c) > i and c[i].strip():
            out.append(c[i].strip())
    return out


def _strings(blob):
    """item-*.json is [{Key, enUS, ...}] -> {key.lower(): enUS}."""
    try:
        rows = json.loads((blob or b"").decode("utf-8-sig", "replace"))
    except Exception:
        return {}
    m = {}
    for e in rows or ():
        k = str((e or {}).get("Key") or "").strip()
        v = str((e or {}).get("enUS") or "").strip()
        if k and v:
            m.setdefault(k.lower(), v)
    return m


def build():
    """-> (lexicon dict, None) or (None, reason). Pulls everything; writes nothing."""
    blobs, absent = {}, []
    for label, path in SOURCES:
        b = _pull(path)
        blobs[label] = b
        if b is None:
            absent.append(label)
    if len(absent) == len(SOURCES):
        return None, ("no source could be pulled — extractor %s, install %s"
                      % ("present" if os.path.exists(EXTRACT) else "MISSING",
                         "present" if os.path.isdir(os.path.join(D2R, "Data")) else "MISSING"))
    aff = _strings(blobs.get("nameaffixes"))
    nms = _strings(blobs.get("itemnames"))

    def resolve(keys):
        hit, miss = set(), []
        for k in keys:
            lk = k.strip().lower()
            if lk in aff:
                hit.add(aff[lk])
            elif lk in nms:
                hit.add(nms[lk])
            else:
                miss.append(k)
        return sorted(hit), sorted(set(miss))

    rp, rp_miss = resolve(set(_col0(blobs.get("rareprefix")) or ()))
    rs, rs_miss = resolve(set(_col0(blobs.get("raresuffix")) or ()))
    base = set()
    for t in ("armor", "weapons", "misc"):
        base |= set(_named(blobs.get(t)) or ())
    mp = sorted({x for x in (_col0(blobs.get("magicprefix")) or ()) if x.lower() != "expansion"})
    ms = sorted({x for x in (_col0(blobs.get("magicsuffix")) or ()) if x.lower() != "expansion"})

    h = hashlib.sha256()
    for label, path in SOURCES:
        b = blobs.get(label)
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(hashlib.sha256(b if b is not None else b"<ABSENT>").hexdigest().encode("ascii"))
    lex = {
        "_comment": "GENERATED from the D2R CASC. Do not hand-edit - run: python3 tv/affix_lexicon.py --write",
        "sourceHash": h.hexdigest(),
        "sourcesAbsent": absent,
        "counts": {"magicPrefix": len(mp), "magicSuffix": len(ms),
                   "rarePrefix": len(rp), "rareSuffix": len(rs), "baseType": len(base)},
        # ⚠ STORED, NEVER DROPPED. "we looked and the game has no display string" and "nobody
        # looked" must not read the same. `scarab` lives here, which is exactly why his live
        # `Storm Scarab` stays UNKNOWN instead of being guessed into a lane.
        "unresolvedKeys": {"rarePrefix": rp_miss, "rareSuffix": rs_miss},
        "magicPrefix": mp,
        "magicSuffix": ms,
        "rarePrefix": rp,
        "rareSuffix": rs,
        "baseType": sorted(base),
    }
    return lex, None


_CACHE = [None]


def load(path=None):
    """-> lexicon dict, or None when it has never been generated. NEVER an empty dict."""
    p = path or STORE
    if _CACHE[0] is not None and path is None:
        return _CACHE[0]
    try:
        d = json.loads(io.open(p, encoding="utf-8").read())
    except Exception:
        return None
    if not isinstance(d, dict) or not d.get("counts"):
        return None
    if path is None:
        _CACHE[0] = d
    return d


def _folded(lex):
    f = lambda xs: {str(x).strip().lower() for x in (xs or ())}
    return (f(lex.get("magicPrefix")), f(lex.get("magicSuffix")),
            f(lex.get("rarePrefix")), f(lex.get("rareSuffix")), f(lex.get("baseType")))


def classify(name, lex=None, roster=None):
    """-> (kind, why). kind in GRAIL / BASE / MAGIC / RARE / UNKNOWN.

    ⚠⚠ NEVER A BEST PARTIAL. An unmatched token, or parses of two different kinds, is UNKNOWN.
    A wrong kind becomes a wrong routing decision about his loot; a refusal costs one more look.
    """
    lex = lex if lex is not None else load()
    if lex is None:
        return "UNKNOWN", "the lexicon has never been generated on this machine"
    n = str(name or "").strip().lower()
    if not n:
        return "UNKNOWN", "no name"
    if roster is None:
        roster = _roster_folded()
    if roster and n in roster:
        return "GRAIL", "on his roster"
    mp, ms, rp, rs, bt = _folded(lex)
    if n in bt:
        return "BASE", "exact base type"
    toks = n.split()
    parses = []
    for i in range(len(toks)):
        for j in range(i + 1, len(toks) + 1):
            if " ".join(toks[i:j]) not in bt:
                continue
            pre, suf = " ".join(toks[:i]), " ".join(toks[j:])
            if (not pre or pre in mp) and (not suf or suf in ms) and (pre or suf):
                parses.append(("MAGIC", "%s + %s + %s" % (pre or "-", " ".join(toks[i:j]), suf or "-")))
    if len(toks) == 2 and toks[0] in rp and toks[1] in rs:
        parses.append(("RARE", "%s + %s" % (toks[0], toks[1])))
    if not parses:
        return "UNKNOWN", "no parse against the lexicon"
    if len({k for k, _ in parses}) > 1:
        return "UNKNOWN", "AMBIGUOUS: %d parses of differing kind" % len(parses)
    return parses[0]


_RCACHE = [None]


def _roster_folded():
    if _RCACHE[0] is not None:
        return _RCACHE[0]
    names = set()
    for mod, fn in (("chronicle_resolve", "load_roster"),
                    ("chronicle_resolve", "load_set_roster"),
                    ("item_identity", "_roster")):
        try:
            m = __import__(mod)
            names |= {str(x).strip().lower() for x in (getattr(m, fn)() or ())}
        except Exception:
            pass
    _RCACHE[0] = names
    return names


def verify():
    """-> (code, say). 0 fresh · 1 STALE · 77 cannot tell. ⚠ 77 IS NOT GREEN."""
    have = load()
    if have is None:
        return SKIP, "no lexicon on this machine yet — UNKNOWN, not clean. Run --write."
    fresh, why = build()
    if fresh is None:
        return SKIP, "cannot re-derive here (%s), so freshness is UNKNOWN" % why
    if fresh.get("sourceHash") == have.get("sourceHash"):
        return 0, "lexicon matches the install (%s)" % ", ".join(
            "%s %d" % (k, v) for k, v in sorted((have.get("counts") or {}).items()))
    return 1, ("the install has changed since the lexicon was generated: stored %s, now %s"
               % (str(have.get("sourceHash"))[:12], str(fresh.get("sourceHash"))[:12]))


def main(argv):
    if "--verify" in argv:
        c, say = verify()
        print(("   ✅ " if c == 0 else "   ⚠ ") + say)
        return c
    if "--write" in argv:
        lex, why = build()
        if lex is None:
            print("   ⏭  SKIP: %s" % why)
            print("      rebuild: see tv/chronicle_total.py for the CascLib recipe")
            return SKIP
        try:
            from bump_version import atomic_write
            atomic_write(STORE, json.dumps(lex, ensure_ascii=False, indent=1) + "\n")
        except Exception:
            tmp = STORE + ".tmp"
            io.open(tmp, "w", encoding="utf-8").write(
                json.dumps(lex, ensure_ascii=False, indent=1) + "\n")
            os.replace(tmp, STORE)
        print("   wrote %s" % STORE)
        for k, v in sorted((lex.get("counts") or {}).items()):
            print("      %-12s %d" % (k, v))
        ur = lex.get("unresolvedKeys") or {}
        print("      unresolved rare keys: prefix %s suffix %s"
              % (ur.get("rarePrefix"), ur.get("rareSuffix")))
        return 0
    c, say = verify()
    print(say)
    return c


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
