#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE CALL A WRITER MAKES SO ITS STORE CAN NAME WHAT PRODUCED IT — and never guess.

⚠⚠ WHAT THIS IS FOR, MEASURED AND NOT INHERITED. `verdict_provenance.py` is the CENSUS: it asks
every store whether it can say what produced it, and it REPORTS. Run on this tree 2026-09-10:

    44 stores · ANSWERS 6 · PARTIAL 4 · SILENT 16 · REFERENCE 17 · UNKNOWN 1

The census names the gap and refuses to repair it, which is right — back-filling a producer onto
437 rows nobody can now attribute would invent provenance. But a census with no WRITER-SIDE call
is a diagnosis with no medicine: every new store arrives SILENT, because saying what produced you
costs a line of thought nobody has anywhere to put. This module is that place. It is the medicine,
and it is deliberately the only one — [[copy-drift]] §1: name ONE source for a mechanism.

    import provenance as PV
    PV.save_json(path, payload, by="reel_router", ver="v2904")     # stamped + atomic, one replace
    payload, prov = PV.load_json(path)                             # prov.known is False on old files

⚠⚠ THREE REFUSALS, EACH OF WHICH IS THE POINT AND NOT A ROUGH EDGE.

  1. IT NEVER INVENTS A WRITER. `by` is a required argument; there is no default, no stack walk,
     no `__name__` sniffing. A caller that cannot name itself gets `CannotStamp`, not a plausible
     string. And `by="unknown"` is refused BY NAME (see `_PLACEHOLDERS`), because the failure this
     whole territory keeps producing is a word that reads like an answer and is not one.
     [[unknown-stays-unknown]] [[zero-needs-a-denominator]]

  2. ABSENT IS UNKNOWN, NOT "PRODUCED BY NOBODY". `read()` on a store with no `_prov` returns
     `UNKNOWN` — `known=False`, `by=None`, and a `why` sentence saying the store predates the
     stamp. It does not raise, and the payload beside it still loads unchanged. An existing store
     is not corrupt for lacking a field invented after it; treating it that way would turn a
     reporting gap into an outage. [[unknown-stays-unknown]]

  3. A STAMP THAT CANNOT NAME A VERSION SAYS SO, IN THE CENSUS'S OWN VOCABULARY. If `ver` is
     unavailable the block carries `verUnknown: "<why>"` and NO `ver` key — never `ver: null` and
     never `ver: "unknown"`. `classify()` then grades that row PARTIAL (names WHO, not WHAT
     VERSION), which is exactly the distinction `verdict_provenance._verdict` already draws. A
     null version that reads as ANSWERS would be [[the green that lies]] wearing this module's
     clothes. [[label-outlived-referent]]

⚠⚠ THE STAMP RIDES THE SAME `os.replace`, IT IS NOT A SECOND WRITE. `save_json` stamps the payload
IN MEMORY and hands ONE string to `bump_version.atomic_write`, so the file that appears on disk has
its content and its provenance in a single atomic rename. Stamping afterwards would open a window
where the store is live and unattributed — and in this repo that window is not theoretical: v2712
measured 9 torn reads in 188 on the truncate-then-write path, every torn size 0 bytes, on a file
his console EXECS. [[bible-writes-must-be-atomic]] [[open-for-write-truncates-first]]
⚠ It reuses `bump_version.atomic_write` rather than copying it — that function carries the v2795
executable-bit scar and the v2797 pre-chmod window fix, and a second copy would carry neither.

⚠ WHAT IT DOES NOT DO. It does not back-fill, does not walk the tree, does not touch a store
nobody asked it to touch, and it is not wired into any writer by this module. Joining it to the
call sites is a separate, reviewable edit per store — see `CALL_SITES` at the bottom, which is a
LIST, not a loop.

⚠ LIST-SHAPED STORES CANNOT CARRY THIS AND ARE REFUSED. `known_frames.json` is a JSON array; there
is no key to hang `_prov` on without changing the shape its readers parse. `CannotStamp` says so by
name rather than silently wrapping it in an object. That store stays UNKNOWN until someone decides
its shape, which is the honest state. [[unknown-stays-unknown]]
"""
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The one key. A single nested block rather than three flat fields, so a payload's own namespace
#: is touched exactly once and `payload()` can hand a reader back precisely what it always saw.
PROV_KEY = "_prov"

#: Values that LOOK like an answer and are not. Refused as `by` outright: the defect this repo
#: keeps shipping is a word standing where a measurement belongs, and "unknown" is that word.
_PLACEHOLDERS = ("", "?", "-", "n/a", "na", "none", "null", "unknown", "unspecified", "tbd",
                 "todo", "somebody", "someone", "nobody", "anonymous")

#: `at` is EPOCH MILLISECONDS, the unit every store in this tree already uses (board_tally.json
#: carries at=1789067205463). A caller handing it epoch SECONDS is off by a factor of 1000 and
#: would date every row to 1970 — the same unit collision that has already been carved once here.
#: 1e11 ms is 1973 and 1e11 s is the year 5138, so the floor separates them with room to spare.
_MS_FLOOR = 10 ** 11

_VERSION_RE = re.compile(r"D2R_BUILD\s*=\s*\{\s*id:'(v\d+(?:\.\d+)*)'")


class CannotStamp(Exception):
    """The caller asked for a stamp this module refuses to write."""


class Prov(object):
    """What a store says about its own producer — or why it says nothing.

    ⚠ `known` is the only truth test. `bool(prov)` is `known`, so `if prov:` reads correctly, and
    an UNKNOWN one is falsey with `by is None` — there is no string on it that could be printed
    beside a real writer's name and pass for one.
    """

    __slots__ = ("known", "by", "ver", "at", "verWhy", "extra", "why")

    def __init__(self, known, by=None, ver=None, at=None, verWhy=None, extra=None, why=""):
        self.known, self.by, self.ver, self.at = known, by, ver, at
        self.verWhy, self.extra, self.why = verWhy, dict(extra or {}), why

    def __bool__(self):
        return bool(self.known)

    __nonzero__ = __bool__          # py2-shaped callers in this tree still exist

    def describe(self):
        """One sentence a surface can print. -> str

        ⚠ THE UNKNOWN SENTENCE NEVER CONTAINS A NAME-SHAPED WORD. "produced by unknown" and
        "produced by nobody" both read as an attribution; "cannot say" reads as a gap, which is
        what it is. [[unknown-stays-unknown]]
        """
        if not self.known:
            return "provenance UNKNOWN — %s" % (self.why or "no %s block" % PROV_KEY)
        v = self.ver or ("version UNKNOWN (%s)" % (self.verWhy or "not recorded"))
        return "written by %s at %s, %s" % (self.by, self.at if self.at is not None
                                            else "an unrecorded time", v)

    def __repr__(self):
        return "<Prov %s>" % self.describe()

    def to_dict(self):
        return {"known": self.known, "by": self.by, "ver": self.ver, "at": self.at,
                "verWhy": self.verWhy, "extra": dict(self.extra), "why": self.why}


#: The single UNKNOWN answer for a store that never carried a block. Deliberately a FACTORY and not
#: a shared singleton, so no caller can mutate the one everybody else reads.
def _unknown(why):
    return Prov(False, why=why)


UNKNOWN_WHY_ABSENT = ("no %s block — this store predates the stamp, or its writer does not call "
                      "provenance.stamp()" % PROV_KEY)


# ── reading the version, or admitting it cannot ──────────────────────────────────────────────
_VER_CACHE = []          # [(ver|None, why)] — one entry once resolved


def repo_version(_repo=None):
    """The build this tree is stamped at. -> (ver|None, why)

    ⚠⚠ IT READS THE WHOLE FILE, ON PURPOSE, AND ONLY ONCE PER PROCESS. `coldread.py` already
    carved this: a 400 KB head read returned None because `D2R_BUILD` sits ~1.1 MB into a 5.8 MB
    bible.html, and a version that cannot be found is indistinguishable from one that is absent.
    A bounded window here would measure my guess about the file's layout rather than the file.
    [[source-window-shortcut]]

    ⚠ NEVER RAISES AND NEVER GUESSES. Unreadable returns `(None, why)`, and `stamp()` turns that
    into `verUnknown` rather than a plausible number.
    """
    if _repo is None and _VER_CACHE:
        return _VER_CACHE[0]
    root = _repo or os.path.dirname(HERE)
    p = os.path.join(root, "bible.html")
    try:
        with io.open(p, encoding="utf-8", errors="replace") as fh:
            s = fh.read()
    except Exception as exc:
        out = (None, "bible.html could not be read (%s)" % type(exc).__name__)
    else:
        m = _VERSION_RE.search(s)
        out = (m.group(1), "") if m else (None, "no D2R_BUILD id found in bible.html")
    if _repo is None:
        _VER_CACHE.append(out)
    return out


# ── the stamp ────────────────────────────────────────────────────────────────────────────────
_MISSING = object()


def _check_by(by):
    if not isinstance(by, str):
        raise CannotStamp("`by` must be a string naming the producing module, got %s. There is no "
                          "default: a stamp that cannot name its writer is worse than no stamp, "
                          "because it looks like one" % type(by).__name__)
    b = by.strip()
    if b.lower() in _PLACEHOLDERS:
        raise CannotStamp("`by`=%r is a placeholder, not a writer. Absent provenance is UNKNOWN; "
                          "a word that reads like an answer is the defect this module exists to "
                          "refuse" % by)
    return b


def _check_at(at):
    if at is None:
        return int(time.time() * 1000)
    if isinstance(at, bool) or not isinstance(at, (int, float)):
        raise CannotStamp("`at` must be epoch MILLISECONDS as a number, got %s"
                          % type(at).__name__)
    at = int(at)
    if at < _MS_FLOOR:
        raise CannotStamp("`at`=%d looks like epoch SECONDS, not milliseconds — every store in "
                          "this tree records ms, and a 1000x unit error dates the row to 1970 "
                          "while still parsing as a valid time" % at)
    return at


def stamp(payload, by, ver=_MISSING, at=None, extra=None):
    """A COPY of `payload` carrying its producer. -> dict

    `payload` must be a dict. `by` names the producing module and is required. `ver` defaults to
    the tree's build; pass it explicitly when the caller already knows its own version, and pass
    `None` to say deliberately that there is none to record.

    ⚠ IT RETURNS A NEW DICT AND DOES NOT MUTATE THE CALLER'S. A writer that builds its payload
    once and saves it twice must not accumulate the first save's timestamp.

    ⚠ `_prov` IS INSERTED FIRST. Key order is insertion order in JSON, and the census samples
    `list(blob)[:25]` — a block that lands as the 40th key of a wide store is a block the census
    never looks at. Being first is not cosmetic here. [[the-unjoined-end]]
    """
    if isinstance(payload, list):
        raise CannotStamp(
            "this store is a JSON array, and there is no key to hang %s on without changing the "
            "shape its readers parse. Wrapping it in an object silently would be a migration "
            "disguised as a stamp. Decide the shape first; until then the store is UNKNOWN, which "
            "is the honest state" % PROV_KEY)
    if not isinstance(payload, dict):
        raise CannotStamp("payload must be a dict, got %s" % type(payload).__name__)

    b = _check_by(by)
    block = {"by": b, "at": _check_at(at)}
    if ver is _MISSING:
        v, vwhy = repo_version()
    else:
        v, vwhy = (ver, "the writer passed ver=None deliberately") if ver is None else (ver, "")
    if v is None:
        # ⚠ NO `ver` KEY AT ALL, rather than a null one. `classify()` reads this as PARTIAL — it
        # names WHO and not WHAT VERSION — which is a true statement. `ver: null` would satisfy a
        # key-presence check and lie. [[zero-needs-a-denominator]]
        block["verUnknown"] = vwhy or "the version could not be established"
    else:
        if not isinstance(v, str) or v.strip().lower() in _PLACEHOLDERS:
            raise CannotStamp("`ver`=%r is a placeholder, not a version. Pass ver=None to record "
                              "honestly that there is none" % (v,))
        block["ver"] = v.strip()

    for k, val in (extra or {}).items():
        k = str(k)
        if k in ("by", "ver", "at", "verUnknown"):
            raise CannotStamp("extra key %r would overwrite a core provenance field — pass it as "
                              "the field itself instead of smuggling it in" % k)
        if not isinstance(val, (str, int, float, bool)) and val is not None:
            raise CannotStamp("extra[%r] must be a JSON scalar, got %s" % (k, type(val).__name__))
        block[k] = val

    out = {PROV_KEY: block}
    for k, val in payload.items():
        if k == PROV_KEY:
            continue          # re-stamping REPLACES; a store carries one producer, the last one
        out[k] = val
    return out


def stamp_row(row, by, ver=_MISSING, at=None, extra=None):
    """The same block, for ONE `.jsonl` record. -> dict

    ⚠ IDENTICAL SHAPE ON PURPOSE. A jsonl row and a json store answer the same question, and two
    shapes for one fact is how a reader ends up written twice and one of them forgotten.
    [[copy-drift]]
    """
    return stamp(row, by, ver=ver, at=at, extra=extra)


# ── reading it back, without inventing anything ──────────────────────────────────────────────
def read(obj):
    """What this dict says about its producer. -> Prov

    ⚠ A MALFORMED BLOCK IS ITS OWN ANSWER, distinct from an absent one. "somebody wrote a block
    and got it wrong" and "this store predates the stamp" are different facts about the tree, and
    collapsing them would hide a broken writer behind the legitimate backlog.
    """
    if not isinstance(obj, dict):
        return _unknown("not a JSON object — %s carries no fields" % type(obj).__name__)
    if PROV_KEY not in obj:
        return _unknown(UNKNOWN_WHY_ABSENT)
    blk = obj[PROV_KEY]
    if not isinstance(blk, dict):
        return _unknown("%s is a %s, not an object — a malformed block, not an absent one"
                        % (PROV_KEY, type(blk).__name__))
    by = blk.get("by")
    if not isinstance(by, str) or by.strip().lower() in _PLACEHOLDERS:
        return _unknown("%s carries no usable `by` (%r) — a block that cannot name its writer is "
                        "UNKNOWN, not an attribution" % (PROV_KEY, by))
    ver = blk.get("ver")
    if ver is not None and not isinstance(ver, str):
        ver = None
    extra = dict((k, v) for k, v in blk.items()
                 if k not in ("by", "ver", "at", "verUnknown"))
    return Prov(True, by=by.strip(), ver=ver, at=blk.get("at"),
                verWhy=blk.get("verUnknown"), extra=extra)


def payload(obj):
    """`obj` as its readers have always seen it — the block removed. -> dict

    ⚠ ADDITIVE MEANS BOTH DIRECTIONS. A reader that iterates the store's keys must not suddenly
    find a `_prov` entry among its data rows, or adding provenance to `chronicle_swept.json`
    invents a 402nd reel. This is the half of "additive" that is easy to forget.
    """
    if not isinstance(obj, dict):
        return obj
    return dict((k, v) for k, v in obj.items() if k != PROV_KEY)


def read_file(path):
    """-> Prov, for a `.json` store or the LAST row of a `.jsonl` one.

    ⚠ Absent, unreadable and unparseable each get their OWN `why`. A missing file and a corrupt
    one are different problems and a single "no" hides which. [[zero-needs-a-denominator]]
    """
    if not os.path.exists(path):
        return _unknown("no file at %s" % os.path.basename(path))
    try:
        if path.endswith(".jsonl"):
            last = None
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if ln.strip():
                        last = ln
            if last is None:
                return _unknown("no rows yet — the shape is UNKNOWN, not stamp-less")
            return read(json.loads(last))
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            return read(json.load(fh))
    except Exception as exc:
        return _unknown("would not parse (%s)" % type(exc).__name__)


# ── the join to the census ───────────────────────────────────────────────────────────────────
def classify(row):
    """The census's verdict for a row carrying this block. -> "ANSWERS" | "PARTIAL" | None

    `None` means "this module has nothing to say about this row" — `verdict_provenance._verdict`
    then falls through to its own field vocabulary exactly as before, so the patch that calls this
    can never make an already-ANSWERS store worse.

    ⚠⚠ WHY THIS FUNCTION EXISTS AT ALL, AND WHY THE ALTERNATIVE IS A TRAP. Today, unpatched, a
    `.json` store stamped by this module ALREADY reads as ANSWERS — but by accident. The census's
    `_sample_row` merges a store's sub-dicts, `_prov` is a sub-dict, and the merged row therefore
    contains a bare `ver` key, which is in `PRODUCER_FIELDS`. MEASURED, not assumed (see
    `test_the_accidental_merge_is_not_the_join`). Two reasons that accident must not be the join:

        · IT DOES NOT HOLD FOR `.jsonl`. The census reads the LAST LINE's TOP-LEVEL keys and does
          no merging, so a stamped jsonl row shows `_prov` — not a producer field — and grades
          SILENT. `disk_history.jsonl` and `ui_faults.jsonl` are two of the sixteen SILENT stores.
        · IT DEPENDS ON A KEY NAME NOBODY DECLARED. Rename the block's inner `ver` and the census
          silently stops recognising every stamped store, with no test failing anywhere.

    One definition of "what a provenance block is" lives here, and the census asks. [[copy-drift]]
    """
    p = read(row)
    if not p.known:
        return None
    return "ANSWERS" if p.ver else "PARTIAL"


# ── writing it, in one atomic step ───────────────────────────────────────────────────────────
def _atomic_write(path, text):
    """The repo's atomic write, reused rather than re-implemented. -> None

    ⚠ `bump_version.atomic_write` carries two scars a fresh copy would not: v2795 (os.replace moves
    the temp inode, so every executable it touched came out 0644 and the pre-push hook was skipped
    entirely) and v2797 (the chmod must precede the replace or a push landing in the window still
    sees a non-executable hook). Copying those 40 lines here would be [[copy-drift]] with the
    safety routine as the duplicated part, which is the dangerous case.
    """
    from bump_version import atomic_write
    atomic_write(path, text)


def save_json(path, obj, by, ver=_MISSING, at=None, extra=None, indent=2, sort_keys=False):
    """Stamp `obj` and write it atomically. -> Prov (the block that landed)

    ⚠⚠ ONE WRITE, NOT TWO. The stamp is applied in memory and the whole document goes through a
    single `os.replace`, so there is no instant at which the store is live and unattributed. A
    "write then stamp" version of this function would create exactly the window this module exists
    to close, and would look correct in every test that reads the settled file.
    """
    doc = stamp(obj, by, ver=ver, at=at, extra=extra)
    _atomic_write(path, json.dumps(doc, indent=indent, sort_keys=sort_keys, ensure_ascii=False))
    return read(doc)


def load_json(path, default=None):
    """-> (payload, Prov)

    ⚠ AN UNSTAMPED STORE LOADS NORMALLY. That is requirement one: provenance is additive, so a
    file written before this module existed returns its payload untouched beside an UNKNOWN Prov.
    It is never an error, never a raise, and never a reason to treat the store as corrupt.
    """
    if not os.path.exists(path):
        return (default, _unknown("no file at %s" % os.path.basename(path)))
    try:
        with io.open(path, encoding="utf-8", errors="replace") as fh:
            blob = json.load(fh)
    except Exception as exc:
        return (default, _unknown("would not parse (%s)" % type(exc).__name__))
    return (payload(blob), read(blob))


def append_jsonl(path, row, by, ver=_MISSING, at=None, extra=None):
    """Stamp one record and append it. -> Prov

    ⚠ APPEND, NOT REPLACE, AND THAT IS DELIBERATE. A jsonl store is grown a line at a time; going
    through a temp-file replace would rewrite megabytes per row and — worse — two writers doing it
    concurrently would lose each other's rows. `open(..., "a")` with one `write()` of a single
    line under PIPE_BUF is the shape this tree already uses. This function does NOT claim
    atomicity across processes; it claims the row is stamped before it is written.
    [[unknown-stays-unknown]]
    """
    doc = stamp(row, by, ver=ver, at=at, extra=extra)
    line = json.dumps(doc, ensure_ascii=False)
    if "\n" in line:
        raise CannotStamp("a jsonl row serialised with a newline in it — the store would gain a "
                          "half row that parses as two")
    with io.open(path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    return read(doc)


# ── the call sites this is FOR, named rather than looped over ────────────────────────────────
#: ⚠⚠ A LIST, NOT A MIGRATION. Each entry is one reviewable edit in a file this module does not
#: own. Applying them is a decision per store — a loop that stamped all sixteen would be exactly
#: the back-fill `verdict_provenance.py` refuses, one layer up. The census measures whether they
#: landed; this list only says where they go. [[unknown-stays-unknown]]
#:
#: The SILENT sixteen, measured 2026-09-10 by `python3 tv/verdict_provenance.py --census-only -v`:
#:   auto_relaunch · capture_doors · chron_evidence · chron_hunt_memory · chron_last_result ·
#:   disk_history.jsonl · ledger_peaks · main_character · reel_tombstones · retro_gate ·
#:   retro_triage · shadow_ai · shadow_watch · ui_faults.jsonl · vault_last_result · vault_seen
#: and the PARTIAL four (they name a lane, never a version):
#:   g5_shadow.jsonl · g5_stats · river_stamp.jsonl · sessions.jsonl
CALL_SITES = "see tv/test_provenance.py's report and the task #69 hand-back for the per-store patch"

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    v, why = repo_version()
    print("provenance.py — block key %s" % PROV_KEY)
    print("  tree version: %s" % (v or "UNKNOWN (%s)" % why))
    print("  %s" % read({}).describe())
    print("  %s" % read(stamp({"a": 1}, by="provenance.__main__")).describe())
