# -*- coding: utf-8 -*-
"""#174 — THE SKILL TREES OF EVERY CLASS, FROM HIS OWN INSTALL — never from memory.

The mule/character window is being rebuilt to match the maxroll d2planner, whose centre panel is
three skill trees per class ("Elemental / Shape Shifting / Summoning · N Points Spent"): every
skill an icon at a fixed row and column, arrows from its prerequisites, points per skill. The repo
held no class, skill or tab data at all. This file pulls it from the CASC of the install on this
machine into a GENERATED `tv/skill_tables.json`, the same way `item_tables.py` and
`affix_lexicon.py` do: `build()` pulls, `assemble()` is the pure part, `--write` stores, `load()`
reads, `sourceHash` says which install produced it, and no install is UNKNOWN — never a crash,
never a guess.

    classes   per class code (skills.txt `charclass`): id (playerclass row order), name, and
              three tabs, each {index, page, name, skills}, skills as
              {id, key, name, row, col, reqlevel, prereqs, prereqKeys, iconIndex, maxlvl}
    grid      the tree's rows x columns, from the panel layout's own skillRow / skillColumn

WHERE EACH FACT COMES FROM — one table per fact, and a null wherever no table says it:
    id          skills.txt row order; `*Id` is a comment column, used only as a cross-check —
                where the two disagree the id is null, neither is picked
    row, col    skilldesc.txt SkillRow / SkillColumn, joined by the skills.txt `skilldesc` KEY
    page        skilldesc.txt SkillPage (1..3)
    iconIndex   skilldesc.txt IconCel — a frame of the class's icon sheet (`iconFile`, below)
    reqlevel, maxlvl   skills.txt
    prereqs     skills.txt reqskill1..3, which name skills by KEY; resolved to ids
    name        skilldesc `str name` -> strings/skills.json. A KEY IS NOT A NAME: 27 of the 240
                tree skills print something else (`Wearwolf` is Werewolf, `Plague Poppy` is Poison
                Creeper, `Levitate` is Levitation Mastery). No string -> null, never the key.
    tab name    the HD skill-tree layout (ui/layouts/skillstreepanelhd.json) textTab0/1/2, per
                class id -> SkillCategory* in strings/skills.json. WHICH tab shows WHICH page is
                not stated by any one table — see THE TAB ORDER below.
    class name  playerclass.txt `Player Class` -> strings/ui.json

=== MEASURED ON HIS INSTALL, 2026-09-25 ===
EIGHT classes, not seven: playerclass.txt lists `Warlock war` after the Assassin — the Reign of the
Warlock class. 8 x 3 tabs x 10 skills = 240 tree skills; every row 1..6, every column 1..3, no two
skills in one cell; every prerequisite in the same class and the same tab, never below the skill
(three sit beside it in the same row: Skeleton Mastery, Lycanthropy, Demonic Mastery). SkillRow and
reqlevel agree on all 240 (row 1..6 = level 1, 6, 12, 18, 24, 30) — two columns in two tables
telling one fact, which is what makes the skilldesc join checkable.
`data\\global\\excel\\base\\` holds a second set of these tables (the non-RotW game): identical for
the seven classic classes, and the Warlock's 30 rows there are placeholders with no id and no
skilldesc. The RotW set (`excel\\` itself) is the one pulled.

⚠ A SKILLPAGE DOES NOT MAKE A TREE SKILL. Monster skills carry SkillPage too (`DiabWall` 3,
`Cold Enchant` 1), so a tree is filtered on skills.txt `charclass`, never on SkillPage.

=== THE TAB ORDER, AND WHY IT IS DERIVED RATHER THAN ASSUMED ===
The layout names tabs by POSITION (textTab0 is the leftmost, the planner's first) and the skills
name their tab by PAGE. Nothing states the link. The obvious guess — tab i is page i+1 — is WRONG:
it would put Firestorm and Tornado (page 3) under "Summoning". And the string keys cannot be
trusted to encode it either: the Warlock's leftmost tab is `@SkillCategoryWa3` (Chaos) while every
classic class's is `...1`.
So the order is DERIVED from a second, independent table: charstats StrSkillTab1..3 name each PAGE
through its item modifier ("%+d to Elemental Skills" is the Druid's StrSkillTab3). For every class
the one assignment of pages to tab positions whose words agree is kept — only if it is the unique
best, every pair shares a word, and the layout's class slot is proven to BE that class (its
skillButtonFile folder names the class). Anything short of that is a tab with index and name null
and a `tabWhy`, not a guess. MEASURED: all 8 classes resolve uniquely, and to position = 3 - page.

⚠ NEVER wrap the pull in `perl -e 'alarm N; exec'` — see affix_lexicon._pull (dyld strips the
extractor's framework path across the SIP-restricted perl; it reads exactly like a dead install).
"""
import hashlib
import io
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass                      # console encoding only; a failure here changes no fact the tables hold

from item_tables import _rows, _strings  # noqa: E402  ONE parser for the excel/string tables, not two

SKIP = 77
STORE = os.path.join(HERE, "skill_tables.json")

#: (label, CASC path). ORDER IS FIXED — sourceHash is computed over it.
SOURCES = [
    ("skills",      r"data:data\global\excel\skills.txt"),
    ("skilldesc",   r"data:data\global\excel\skilldesc.txt"),
    ("playerclass", r"data:data\global\excel\playerclass.txt"),
    ("charstats",   r"data:data\global\excel\charstats.txt"),
    ("treelayout",  r"data:data\global\ui\layouts\skillstreepanelhd.json"),
    ("skillnames",  r"data:data\local\lng\strings\skills.json"),
    ("uinames",     r"data:data\local\lng\strings\ui.json"),
    ("itemmods",    r"data:data\local\lng\strings\item-modifiers.json"),
]
#: Without these there is no tree to describe, so a build missing any of them is refused.
REQUIRED = ("skills", "skilldesc", "playerclass")
#: Arrived-but-unparseable is its own answer for these, never an empty table.
_STRING_SOURCES = ("skillnames", "uinames", "itemmods")

#: Words that every tab string shares and so cannot tell two tabs apart.
_NOISE = frozenset(("d", "to", "and", "skills", "skill", "spells"))


def _pull(casc_path):
    """-> bytes or None. ⚠ NEVER wrap this in `perl -e 'alarm N; exec'` — see affix_lexicon._pull."""
    import affix_lexicon
    return affix_lexicon._pull(casc_path)


def _int(s):
    """-> int, or None when the cell does not hold one. None is UNKNOWN; it is never 0."""
    s = str(s if s is not None else "").strip()
    return int(s) if s.lstrip("-").isdigit() else None


def _loose_json(blob):
    """The game's layout files are JSON with // comments and trailing commas. -> dict or None."""
    if blob is None:
        return None
    txt = blob.decode("utf-8-sig", "replace")
    out, i, n, in_str = [], 0, len(txt), False
    while i < n:
        c = txt[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(txt[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
            out.append(c)
        elif c == "/" and txt[i + 1:i + 2] == "/":
            j = txt.find("\n", i)
            i = n if j < 0 else j
            continue
        else:
            out.append(c)
        i += 1
    clean = re.sub(r",(\s*[}\]])", r"\1", "".join(out))
    try:
        d = json.loads(clean)
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def _words(s):
    return {w for w in re.findall(r"[a-z]+", str(s or "").lower()) if w not in _NOISE}


def _tab_positions(page_words, slot_words):
    """Which layout position shows which page. -> ({page: position}, None) or (None, why)

    `page_words` {page: words of its charstats item modifier}; `slot_words` {position: words of the
    layout's tab string}. The assignment kept is the unique best one in which EVERY pair shares a
    word. A tie, or no assignment where every pair agrees, is UNKNOWN — it is never resolved by
    picking the first, and never by assuming position = page - 1.
    """
    pages, slots = sorted(page_words), sorted(slot_words)
    if len(pages) != len(slots) or not pages:
        return None, "%d page(s) against %d layout tab(s)" % (len(pages), len(slots))
    scored = []
    for perm in itertools.permutations(slots):
        overlaps = [len(page_words[p] & slot_words[s]) for p, s in zip(pages, perm)]
        if min(overlaps) > 0:
            scored.append((sum(overlaps), perm))
    if not scored:
        return None, "no assignment of pages to tabs where every item modifier shares a word with its tab"
    scored.sort(reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None, "%d assignments tie at the best agreement — which tab is which page is UNKNOWN" % (
            sum(1 for sc, _ in scored if sc == scored[0][0]))
    return dict(zip(pages, scored[0][1])), None


def assemble(blobs):
    """blobs {label: bytes|None} -> (tables dict, None) or (None, reason). Pure: pulls and writes nothing."""
    absent = [label for label, _ in SOURCES if blobs.get(label) is None]
    missing = [label for label in REQUIRED if label in absent]
    if missing:
        import affix_lexicon as _A
        return None, ("could not pull %s — extractor %s, install %s. Without them there is no tree, "
                      "so there is no table, not an empty one"
                      % (", ".join(missing), "present" if os.path.exists(_A.EXTRACT) else "MISSING",
                         "present" if os.path.isdir(os.path.join(_A.D2R, "Data")) else "MISSING"))
    strings = {lbl: _strings(blobs.get(lbl)) for lbl in _STRING_SOURCES}
    layout = _loose_json(blobs.get("treelayout"))
    unreadable = [lbl for lbl in _STRING_SOURCES if blobs.get(lbl) is not None and strings[lbl] is None]
    if blobs.get("treelayout") is not None and layout is None:
        unreadable.append("treelayout")
    if unreadable:
        return None, "pulled but would not parse: %s — a corrupt source is not an empty one" % unreadable
    skill_names = strings["skillnames"] or {}
    ui_names = strings["uinames"] or {}
    item_mods = strings["itemmods"] or {}

    skill_rows = _rows(blobs["skills"]) or []
    desc_rows = _rows(blobs["skilldesc"]) or []
    descs = {}
    for d in desc_rows:
        descs.setdefault(d.get("skilldesc") or "", d)
    ids = {}
    for n, r in enumerate(skill_rows):
        star = _int(r.get("*Id"))
        ids.setdefault(r.get("skill") or "", n if star in (None, n) else None)

    # Classes in playerclass row order; the "Expansion" divider has no code and is not a class.
    classes, class_rows = [], {}
    for r in _rows(blobs["playerclass"]) or []:
        code = (r.get("Code") or "").strip()
        if code:
            class_rows[code] = {"cid": len(classes), "key": r.get("Player Class") or ""}
            classes.append(code)
    charstats = {(r.get("class") or ""): r for r in (_rows(blobs.get("charstats")) or [])}
    fields = (layout or {}).get("fields") or {}

    def _slot(arr, cid):
        return arr[cid] if isinstance(arr, list) and 0 <= cid < len(arr) else None

    grid_rows = fields.get("skillRow") if isinstance(fields.get("skillRow"), list) else None
    grid_cols = fields.get("skillColumn") if isinstance(fields.get("skillColumn"), list) else None

    out, owners = {}, {}
    for n, r in enumerate(skill_rows):
        code = r.get("charclass") or ""
        if code:
            owners.setdefault(code, []).append((n, r))
    for code in classes:
        if code not in owners:
            continue
        cid, key = class_rows[code]["cid"], class_rows[code]["key"]
        by_page = {}
        for n, r in owners[code]:
            d = descs.get(r.get("skilldesc") or "")
            page = _int((d or {}).get("SkillPage"))
            prereq_keys = [r.get(k) for k in ("reqskill1", "reqskill2", "reqskill3") if r.get(k)]
            by_page.setdefault(page, []).append({
                "id": ids.get(r.get("skill") or ""),
                "key": r.get("skill") or None,
                "name": skill_names.get((d or {}).get("str name") or "") or None,
                "row": _int((d or {}).get("SkillRow")),
                "col": _int((d or {}).get("SkillColumn")),
                "reqlevel": _int(r.get("reqlevel")),
                "maxlvl": _int(r.get("maxlvl")),
                "iconIndex": _int((d or {}).get("IconCel")),
                "prereqKeys": prereq_keys,
                "prereqs": [ids.get(q) for q in prereq_keys],
            })

        # THE TAB ORDER — derived, never assumed (see the module docstring).
        order, why = None, None
        folder = str(_slot(fields.get("skillButtonFile"), cid) or "").replace("/", "\\").split("\\")
        slot_keys = {i: str(_slot(fields.get("textTab%d" % i), cid) or "").lstrip("@") for i in range(3)}
        cs = charstats.get(key) or {}
        page_keys = {p: cs.get("StrSkillTab%d" % p) or "" for p in by_page if p is not None}
        if layout is None:
            why = "the skill-tree layout was not pulled"
        elif len(folder) < 2 or folder[-2].lower() != key.lower():
            why = "the layout's class slot %d does not name %s (skillButtonFile %r)" % (
                cid, key, _slot(fields.get("skillButtonFile"), cid))
        elif not all(slot_keys.values()) or not all(skill_names.get(k) for k in slot_keys.values()):
            why = "the layout names no readable tab string for %s" % key
        elif not all(item_mods.get(k) for k in page_keys.values()):
            why = "charstats names no readable item modifier for every page of %s" % key
        else:
            order, why = _tab_positions({p: _words(item_mods.get(k)) for p, k in page_keys.items()},
                                        {i: _words(skill_names.get(k)) for i, k in slot_keys.items()})
        tabs = []
        for page in sorted(by_page, key=lambda p: (p is None, p)):
            index = order.get(page) if order else None
            tabs.append({
                "index": index,
                "page": page,
                "name": skill_names.get(slot_keys[index]) if index is not None else None,
                "nameKey": slot_keys[index] if index is not None else None,
                "itemModKey": page_keys.get(page) or None,
                "tabWhy": None if index is not None else why,
                "skills": sorted(by_page[page], key=lambda s: (s["row"] is None, s["row"] or 0,
                                                               s["col"] is None, s["col"] or 0)),
            })
        if all(t["index"] is not None for t in tabs):
            tabs.sort(key=lambda t: t["index"])
        out[code] = {"id": cid, "key": key, "name": ui_names.get(key) or None,
                     "iconFile": _slot(fields.get("skillButtonFile"), cid), "tabs": tabs}

    skills = [s for c in out.values() for t in c["tabs"] for s in t["skills"]]
    tabs_all = [t for c in out.values() for t in c["tabs"]]
    h = hashlib.sha256()
    for label, path in SOURCES:
        b = blobs.get(label)
        h.update(path.encode("utf-8"))
        h.update(b"\x00")
        h.update(hashlib.sha256(b if b is not None else b"<ABSENT>").hexdigest().encode("ascii"))
    return {
        "_comment": "GENERATED from the D2R CASC. Do not hand-edit - run: python3 tv/skill_tables.py --write",
        "sourceHash": h.hexdigest(),
        "sourcesAbsent": absent,
        "grid": {"rows": len(grid_rows) if grid_rows else None,
                 "cols": len(grid_cols) if grid_cols else None,
                 "rowPx": grid_rows, "colPx": grid_cols,
                 "from": "skillstreepanelhd.json skillRow / skillColumn" if grid_rows and grid_cols else None},
        "classOrder": [c for c in classes if c in out],
        # ⚠ SAID, NOT DROPPED: a class the game lists with no skill rows is a different fact from
        # a class nobody looked for.
        "classesWithoutSkills": [c for c in classes if c not in out],
        "counts": {"classes": len(out), "tabs": len(tabs_all), "skills": len(skills),
                   "unnamedSkills": sum(1 for s in skills if s["name"] is None),
                   "unplacedSkills": sum(1 for s in skills if s["row"] is None or s["col"] is None),
                   "untitledTabs": sum(1 for t in tabs_all if t["name"] is None)},
        "classes": out,
    }, None


def build():
    """-> (tables dict, None) or (None, reason). Pulls everything; writes nothing."""
    return assemble({label: _pull(path) for label, path in SOURCES})


_CACHE = [None]


def load(path=None):
    """-> tables dict, or None when never generated / unreadable. NEVER an empty dict."""
    if path is None and _CACHE[0] is not None:
        return _CACHE[0]
    try:
        with io.open(path or STORE, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None           # UNKNOWN, and callers say so
    if not isinstance(d, dict) or not d.get("classes"):
        return None
    if path is None:
        _CACHE[0] = d
    return d


def serialise(t):
    """The exact bytes --write stores. ONE writer, so a freshness check compares like with like."""
    return json.dumps(t, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def verify():
    """-> (code, say). 0 fresh · 1 STALE · 77 cannot tell. ⚠ 77 IS NOT GREEN."""
    have = load()
    if have is None:
        return SKIP, "no skill tables on this machine yet — UNKNOWN, not clean. Run --write."
    fresh, why = build()
    if fresh is None:
        return SKIP, "cannot re-derive here (%s), so freshness is UNKNOWN" % why
    if fresh.get("sourceHash") != have.get("sourceHash"):
        return 1, ("the install has changed since the skill tables were generated: stored %s, now %s"
                   % (str(have.get("sourceHash"))[:12], str(fresh.get("sourceHash"))[:12]))
    if json.loads(serialise(fresh)) != have:
        return 1, "same install, different tables: skill_tables.py changed and --write was not re-run"
    return 0, "skill tables match the install (%s)" % ", ".join(
        "%s %d" % (k, v) for k, v in sorted((have.get("counts") or {}).items()))


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
        from bump_version import atomic_write
        atomic_write(STORE, serialise(t))
        print("   wrote %s" % STORE)
        for k, v in sorted(t["counts"].items()):
            print("      %-15s %d" % (k, v))
        for code in t["classOrder"]:
            c = t["classes"][code]
            print("      %s %-12s %s" % (code, c["name"], " / ".join(str(x["name"]) for x in c["tabs"])))
        return 0
    c, say = verify()
    print(say)
    return c


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
