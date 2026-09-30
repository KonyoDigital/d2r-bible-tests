#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#41 rank 16 (REG-1560) — THEIR TOOLTIP ROWS ARE OURS: the shipped composition, run on the console's own
cadence, receipted PER ROW, and corroborated against their planner's oracle.

WHY. The #41 heart audit (rank 16, verified) found that the character builder's tooltip composition had no
runtime invariant and no doctor row: the one independent engine — their planner's in-game tooltip, MEASURED on
headless Chrome and frozen as text in tv/the_tooltip_oracle.json (203 rows over 6 runewords) — was compared only by
a gate, in node, at push time. His console could ship a composition that stopped being theirs and nothing on the
eagle would say so until the next push. This module is the runtime joint the audit asked for.

THE TWO ENGINES, and they are genuinely independent:
  THEIRS   the oracle file: the words and numbers THEIR planner printed, hovered row by row (tv/the_tooltip_oracle.json)
  OURS     the SHIPPED composition — window._cbTipEntry + window.d2Tip and the generated ⟦CB_DB⟧ block, cut from the
           bible.html ON DISK and run in node through the builder law's own stand-in (tv/cb_node_harness.py,
           imported, never re-typed)
`measure()` runs ours ONCE over every oracle row and `judge()` says, per row, whether ours is theirs — the same
three declared differences the gate test_the_tooltip_is_the_games_tooltip asserts (a sword's class line, a blunt
base's +50% undead said UNKNOWN, an untyped rolled attack speed across two bands). The gate calls THIS measure(),
so the gate and the lane share one composition run and one judge. [[copy-drift]]

THE RECEIPT is PER ROW, never a summary: {runeword, base, agree, why, kinds} for every oracle row, plus the
bible.html it measured ({id, size, mtimeNs, sha1}), the oracle's limit, the node it ran, and the lane's LIFETIME
counters (runs, runsMeasured, firstTs). A summary ("203 of 203") cannot answer "which row?", and the next reader
would have to re-run node to find out. [[heart-first]] §6

THREE THINGS STAY UNKNOWN, NEVER 0 OR OK:
  · NODE ABSENT — no node by env (TV_NODE), PATH or the known install locations (a PC without node: the Windows
    box's node is UNKNOWN today): the receipt says `node absent`, rows is None, the doctor row and the corroborate
    invariant read UNKNOWN. Not 0 rows, not "all agree".
  · STALE — the receipt measured bytes of bible.html that are no longer the bytes on disk (sha1 differs): the
    agreement it records is about a page that has since moved, so it is UNKNOWN until the lane re-measures (within
    EVERY_S). A reading carries the age of the thing it measured. [[stale-reading]]
  · NO RECEIPT / UNREADABLE — the lane has not measured, or its receipt cannot be read: UNKNOWN, naming which.

THE LIMIT, stated wherever a verdict is printed: the oracle is 203 rows over SIX runewords (Breath of the Dying,
Grief, Spirit, Insight, Call to Arms, Heart of the Oak) measured once on 2026-09-26 for a level 99 Sorceress. A
green here says those rows are theirs — nothing about a runeword, a class or a level the oracle never held.

    python3 tv/tooltip_oracle_lane.py            the verdict and the lane contract off the receipt on disk
    python3 tv/tooltip_oracle_lane.py --once     one lane tick (measure if owed, write the receipt)
    python3 tv/tooltip_oracle_lane.py --force    measure now whatever the receipt says
"""
import hashlib
import io
import json
import os
import re
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ORACLE = os.path.join(HERE, "the_tooltip_oracle.json")
LANE = "tvd-tooltip-oracle"
#: the loop's period (control_app._tooltip_oracle_loop sleeps this between ticks)
EVERY_S = 900.0
#: a fresh receipt is re-earned after this long even when bible.html did not move
REMEASURE_S = 6 * 3600.0
#: the receipt file, in the lane's world (his tree, or a fixture's when TV_HIST names one)
RECEIPT_NAME = ".tooltip_oracle_receipt.json"

OK, MISSING, UNKNOWN = "ok", "missing", "unknown"


def _world():
    """Whose world the receipt describes: his tree, or a fixture's when TV_HIST is one (lane_trace's rule,
    called, not copied)."""
    try:
        import tv_diablo as _tvd
        return _tvd._fixture_root(HERE)
    except Exception:
        _h = (os.environ.get("TV_HIST") or "").strip()
        return _h if (_h and os.path.isabs(_h)) else HERE


def receipt_path():
    return os.path.join(_world(), RECEIPT_NAME)


def _bible_path():
    return os.path.join(ROOT, "bible.html")


# ── THEIRS: the oracle ───────────────────────────────────────────────────────────────────────────────────────
def oracle(path=None):
    """The oracle fixture. Raises when it cannot be read — a caller says UNKNOWN, never 0 rows."""
    with io.open(path or ORACLE, encoding="utf-8") as fh:
        fx = json.load(fh)
    if not isinstance(fx, dict) or not isinstance(fx.get("runewords"), dict):
        raise ValueError("the oracle is not the expected shape")
    return fx


def oracle_rows(fx=None):
    """[(runeword, base, their lines)] - head + the runeword's props, or the base's own props."""
    fx = oracle() if fx is None else fx
    out = []
    for rw, v in fx["runewords"].items():
        for base, e in v["bases"].items():
            out.append((rw, base, list(e["head"]) + list(e.get("props") or v["props"])))
    return out


def oracle_limit(fx=None):
    """What the oracle can vouch for, and nothing more. -> {rows, runewords, names, build, measuredOn}"""
    fx = oracle() if fx is None else fx
    rw = fx.get("runewords") or {}
    m = re.search(r"\d{4}-\d{2}-\d{2}", str(fx.get("about") or ""))
    return {"rows": sum(len((v or {}).get("bases") or {}) for v in rw.values()),
            "runewords": len(rw), "names": sorted(rw), "build": fx.get("build"),
            "measuredOn": m.group(0) if m else None}


def _norm(s):
    return re.sub(r"\s+", " ", s.replace(u"–", "-")).strip()


# ── OURS: the shipped composition, in node ──────────────────────────────────────────────────────────────────
#: helpers the composition run and every tooltip law share: the tooltip of a named item on a named base, as
#: [class, text] rows
HELP = r"""
window.openCharBuilder();
var d = window._cbDb();
function baseCode(n){ var h = null; Object.keys(d.b).forEach(function(c){ if (!h && d.b[c][0] === n && d.b[c][20]) h = c; }); return h; }
function rows(h){ var out = [], re = /<div class="([^"]+)"[^>]*>([\s\S]*?)<\/div>/g, m;
  while ((m = re.exec(h))) out.push([m[1], m[2].replace(/<[^>]+>/g, '').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>')]);
  return out; }
function entry(name, base, o){
  o = o || {}; var it = d.byName[name.toLowerCase()]; if (!it) return null;
  var e = window._cbEntryFor(it); if (base){ var bc = baseCode(base); if (!bc) return null; e.base = bc; }
  if (o.rolls) e.rolls = o.rolls;
  var t = window._cbTipEntry(e, it, o.lvl == null ? 99 : o.lvl, o.slot || 'rarm', o.cls === undefined ? 'Sorceress' : o.cls);
  if (o.attrs) t.attrs = o.attrs;
  return { it: it, e: e, t: t };
}
function tip(name, base, o){ var x = entry(name, base, o); return x ? rows(window.d2Tip(x.t)) : null; }
/* the roll key and the top of the item's own Increased Attack Speed line, when it is a range */
function iasRoll(name){ var it = d.byName[name.toLowerCase()], sid = d.tip.st.item_fasterattackrate, hit = null;
  (it[6] || []).forEach(function(l){ var r = l[1] && l[1][0]; if (!hit && d.TK[l[0]][2] === sid && r && r[0] !== r[1]) hit = [r[2], Math.max(r[0], r[1])]; });
  return hit; }
"""


def compose(cases, run=None):
    """ONE node process over every [runeword, base] pair. -> [{rows, sword, blunt} | {err}] in case order.

    `run` is the builder stand-in's runner (cb_node_harness._run); a law may hand in its own.
    """
    if run is None:
        import cb_node_harness as H
        run = H._run
    return run(HELP + r"""
      var CASES = %s;
      OUT.r = CASES.map(function(c){
        var x = entry(c[0], c[1]);
        if (!x) return { err: 'no item or base ' + c[0] + ' / ' + c[1] };
        var bt = d.b[x.e.base][1], anc = d.anc[bt] || {};
        return { rows: rows(window.d2Tip(x.t)), sword: !!anc.swor, blunt: !!anc.blun };
      });
    """ % json.dumps(cases))["r"]


def judge(rw, base, theirs, got):
    """Is OUR composed tooltip THEIR text, line for line? -> (agree, why, kinds)

    `kinds` names the declared differences this row needed ([] when it is theirs exactly): 'sword' (theirs prints
    no class line on a sword, ours the game's), 'blunt' (theirs '+50% Damage to Undead', ours the same place said
    UNKNOWN - the number is the game's code), 'speed' (an untyped rolled attack speed whose two ends fall in two
    bands: theirs the top roll's word, ours both). A row that disagrees says WHERE, so a reader never re-runs node
    to find out.
    """
    if not isinstance(got, dict):
        return False, "no composition came back for this row", None
    if "err" in got:
        return False, str(got["err"]), None
    kinds = []
    notes = [t for c, t in got["rows"] if c == "d2t-note"]
    for n in notes:
        if not n.startswith("strength / dexterity: UNKNOWN until the character has attributes"):
            return False, "an unexpected note %r" % n, None
    ours = [(c, _norm(t)) for c, t in got["rows"] if c != "d2t-note"]
    th = [_norm(x) for x in theirs]
    ot = [t for _, t in ours]
    if ot == th:
        return True, "theirs line for line (%d lines)" % len(th), kinds
    # (a) SWORD: ours has the game's sword class line where theirs has none - on a sword, and only there
    if got.get("sword"):
        k = [i for i, t in enumerate(ot) if t.startswith("Sword Class - ")]
        if len(k) != 1 or [t for t in th if " Class - " in t]:
            return False, "a sword must print exactly one 'Sword Class - ' line (theirs none): %s" % k, None
        if not (ot[k[0] - 1].startswith("Required Level: ") and (re.search(r" Attack Speed$", ot[k[0]])
                                                                 or "attack speed UNKNOWN" in ot[k[0]])):
            return False, "the sword's class line is out of place or not the game's form: %r" % ot[k[0]], None
        del ot[k[0]]
        del ours[k[0]]
        kinds.append("sword")
    # (b) BLUNT: theirs "+50% Damage to Undead" before Socketed; ours the UNKNOWN in the same place
    if got.get("blunt") and "+50% Damage to Undead" in th:
        i = th.index("+50% Damage to Undead")
        if i >= len(ours) or ours[i][0] != "d2t-unk" or not ours[i][1].startswith("Damage to Undead: UNKNOWN"):
            return False, "the blunt bonus is not said UNKNOWN in its place: %r" % ours[i:i + 1], None
        if any("Damage to Undead" in t and not t.startswith("Damage to Undead: UNKNOWN") for t in ot):
            return False, "a blunt base with its own undead stat must not say the bonus", None
        ot[i] = th[i]
        kinds.append("blunt")
    # (c) an untyped rolled IAS whose ends fall in two bands: ours "(A-B) Attack Speed", theirs B (the top roll)
    for i, (a, b) in enumerate(zip(th, ot)):
        m = re.match(r"^(\w+ Class - )\((.+)-(.+)\) Attack Speed$", b)
        if a != b and m and a == m.group(1) + m.group(3) + " Attack Speed":
            ot[i] = a
            kinds.append("speed")
    if ot != th:
        at = next((i for i, (a, b) in enumerate(zip(th, ot)) if a != b), min(len(th), len(ot)))
        return False, ("line %d differs - theirs %r, ours %r (theirs %d lines, ours %d); theirs %s / ours %s"
                       % (at + 1, th[at] if at < len(th) else None, ot[at] if at < len(ot) else None,
                          len(th), len(ot), th, ot)), None
    return True, "theirs after the declared difference(s): %s" % ", ".join(kinds), kinds


def bible_stamp(path=None):
    """The bible.html the composition is cut from, identified by its BYTES. -> {id, size, mtimeNs, sha1} | None

    None when it cannot be read - UNKNOWN, and every reader treats it so. The sha1 is what freshness() compares:
    a receipt is fresh only about the exact bytes it measured, whatever the clock says.
    """
    p = path or _bible_path()
    try:
        st = os.stat(p)
        with io.open(p, "rb") as fh:
            data = fh.read()
        m = re.search(rb"window\.D2R_BUILD = \{ id:'([^']*)'", data)
        return {"id": (m.group(1).decode("utf-8", "replace") if m else None), "size": int(st.st_size),
                "mtimeNs": int(st.st_mtime_ns), "sha1": hashlib.sha1(data).hexdigest()}
    except Exception:
        return None


def measure(fx=None, run=None, now_ms=None):
    """Run the SHIPPED composition over every oracle row, ONCE, and judge each. -> the report (a receipt body)

    rows is a LIST of per-row verdicts, or None when nothing was judged (node absent, the oracle unreadable,
    bible.html unstampable, node failed) - and then `why` says which, `ok` is False, and no count is 0.
    """
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    out = {"lane": LANE, "measuredTs": now, "ok": False, "why": "", "node": None, "rows": None,
           "agreed": None, "measured": None, "oracleRows": None, "limit": None, "bible": None, "kinds": None}
    try:
        fx = oracle() if fx is None else fx
        rows = oracle_rows(fx)
        out["oracleRows"] = len(rows)
        out["limit"] = oracle_limit(fx)
    except Exception as e:
        out["why"] = "the oracle could not be read: %s %s" % (type(e).__name__, str(e)[:80])
        return out
    if not rows:
        out["why"] = "the oracle holds no rows - nothing to compare, which is UNKNOWN, not agreement"
        return out
    out["bible"] = bible_stamp()
    if out["bible"] is None:
        out["why"] = "bible.html could not be read, so there is nothing to compose from"
        return out
    if run is None:
        import cb_node_harness as H
        if not H.NODE:
            out["why"] = ("node absent: no node binary by env (TV_NODE), PATH or the known install locations - "
                          "the composition was NOT run, so every row is UNKNOWN (not 0, not agreed)")
            return out
        out["node"] = H.NODE
        run = H._run
    else:
        out["node"] = "caller-supplied runner"
    try:
        got = compose([[rw, b] for rw, b, _ in rows], run=run)
    except Exception as e:
        out["why"] = "the composition did not run: %s %s" % (type(e).__name__, str(e)[:160])
        return out
    if not isinstance(got, list) or len(got) != len(rows):
        out["why"] = ("node answered %s verdict(s) for %d rows - the run is not a measurement of every row"
                      % (len(got) if isinstance(got, list) else "no", len(rows)))
        return out
    rrows, kinds = [], {"equal": 0, "sword": 0, "blunt": 0, "speed": 0}
    for (rw, b, th), g in zip(rows, got):
        agree, why, ks = judge(rw, b, th, g)
        rrows.append({"runeword": rw, "base": b, "agree": bool(agree), "why": why, "kinds": ks})
        if agree and not ks:
            kinds["equal"] += 1
        for k in (ks or []):
            kinds[k] += 1
    out["rows"] = rrows
    out["measured"] = len(rrows)
    out["agreed"] = sum(1 for r in rrows if r["agree"] is True)
    out["kinds"] = kinds
    out["ok"] = (out["agreed"] == out["measured"] == out["oracleRows"])
    bad = [r for r in rrows if not r["agree"]]
    out["why"] = ("%d of %d rows are theirs (build %s)" % (out["agreed"], out["measured"], out["bible"].get("id"))
                  + ("" if not bad else " - NOT theirs: " + "; ".join(
                      "%s / %s: %s" % (r["runeword"], r["base"], r["why"][:80]) for r in bad[:3])
                     + (" ..." if len(bad) > 3 else "")))
    return out


# ── THE RECEIPT ─────────────────────────────────────────────────────────────────────────────────────────────
def read_receipt(path=None):
    """-> (receipt, why). None = absent or unreadable, and `why` says which - never an empty receipt."""
    p = path or receipt_path()
    try:
        with io.open(p, encoding="utf-8") as fh:
            rec = json.load(fh)
    except FileNotFoundError:
        return None, "no receipt yet at %s" % os.path.basename(p)
    except Exception as e:
        return None, "the receipt is unreadable: %s" % type(e).__name__
    if not isinstance(rec, dict):
        return None, "the receipt is not a record"
    return rec, ""


def write_receipt(rep, path=None):
    """Persist a report as THE receipt, carrying the lifetime counters forward. tmp + os.replace. -> bool

    runs         ticks that measured (attempted), lifetime
    runsMeasured ticks whose composition actually ran and judged every row, lifetime
    firstTs      when this lane first wrote
    A previous receipt that exists but cannot be read is NOT silently restarted at zero: the counters are carried
    as UNKNOWN (None) with `countersWhy`, so a reader sees the history was lost rather than a young lane.
    """
    p = path or receipt_path()
    prev, pwhy = read_receipt(p)
    rec = dict(rep)
    if prev is None and os.path.exists(p):
        rec["runs"] = rec["runsMeasured"] = rec["firstTs"] = None
        rec["countersWhy"] = ("the previous receipt was unreadable (%s), so the lifetime counters could not be "
                              "carried and are UNKNOWN" % pwhy)
    else:
        prev = prev or {}

        def _n(k):
            v = prev.get(k)
            return v if (isinstance(v, int) and not isinstance(v, bool)) else None
        if prev.get("countersWhy"):
            # ⚠ 2026-09-30 — UNKNOWN + 1 IS STILL UNKNOWN. The write after a loss stored None, and the NEXT write read
            # that None through `_n(...) or 0` and restarted the counters at 1, with firstTs = today: contract() then
            # reported worked 1, a young lane, under a countersWhy that says the history was lost (#231 5908899891,
            # reproduced before this changed). Once lost, the lifetime counters stay UNKNOWN; lastTs still moves, so a
            # lane that stops measuring after a loss still reads stale.
            rec["runs"] = rec["runsMeasured"] = rec["firstTs"] = None
            rec["countersWhy"] = prev["countersWhy"]     # the history was lost once; say so for ever
        else:
            rec["runs"] = (_n("runs") or 0) + 1
            rec["runsMeasured"] = (_n("runsMeasured") or 0) + (1 if isinstance(rep.get("rows"), list) else 0)
            rec["firstTs"] = prev.get("firstTs") or rep.get("measuredTs")
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".tor.", dir=d or None)
        try:
            with io.open(fd, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True))
            os.replace(tmp, p)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return True
    except Exception:
        return False


def freshness(rec, stamp=None):
    """Did the receipt measure the bible.html on disk NOW? -> (True | False | None, why)

    None when it cannot be told (no stamp in the receipt, or bible.html unreadable now). False is STALE: the bytes
    moved since the measurement, so the agreement it records is about a page that no longer exists.
    """
    if not isinstance(rec, dict):
        return None, "no receipt"
    had = rec.get("bible")
    if not isinstance(had, dict) or not had.get("sha1"):
        return None, "the receipt carries no bible.html stamp, so what it measured cannot be told"
    stamp = bible_stamp() if stamp is None else stamp
    if not isinstance(stamp, dict) or not stamp.get("sha1"):
        return None, "bible.html cannot be read now, so whether the receipt is about it cannot be told"
    if had["sha1"] == stamp["sha1"]:
        return True, "measured these exact bytes of bible.html (build %s)" % had.get("id")
    try:
        moved = (int(stamp.get("mtimeNs") or 0) // 1000000) - int(rec.get("measuredTs") or 0)
        moved = "%d min after" % (moved // 60000) if moved >= 0 else "%d min BEFORE" % (-moved // 60000)
    except Exception:
        moved = "an UNKNOWN time from"
    return False, ("STALE: the receipt measured build %s (sha %s) and bible.html on disk is build %s (sha %s), "
                   "modified %s the measurement" % (had.get("id"), str(had.get("sha1"))[:10], stamp.get("id"),
                                                    str(stamp.get("sha1"))[:10], moved))


def _age_say(ms, now_ms=None):
    try:
        import unknown_age as _ua
        return _ua.age_say(ms, now_ms)
    except Exception:
        return "UNKNOWN"


def _limit_say(rec):
    lim = rec.get("limit") if isinstance(rec, dict) else None
    lim = lim if isinstance(lim, dict) else {}
    return ("the oracle's limit: their planner's %s rows over %s runewords (%s), measured once%s for a level %s %s"
            % (lim.get("rows", "?"), lim.get("runewords", "?"), ", ".join(lim.get("names") or []) or "?",
               (" on %s" % lim["measuredOn"]) if lim.get("measuredOn") else "",
               (lim.get("build") or {}).get("level", "?"), (lim.get("build") or {}).get("class", "?")))


def verdict(path=None, stamp=None, live_rows=None, now_ms=None):
    """The doctor-facing verdict off the receipt on disk. -> (OK | MISSING | UNKNOWN, why)

    UNKNOWN: no receipt, an unreadable one, node absent (rows None), a summary in place of rows, a receipt the
    page has moved from, or an oracle that cannot be read now. MISSING: a row never judged, or a row that is not
    theirs - named. OK: every oracle row judged and theirs, with the build, the age and the oracle's limit.
    """
    rec, rwhy = read_receipt(path)
    if rec is None:
        return UNKNOWN, ("%s - the %s lane has not measured yet, or could not; its rows are UNKNOWN, not 0"
                         % (rwhy, LANE))
    rows = rec.get("rows")
    if rows is None:
        return UNKNOWN, ("the lane could not run the composition (%s): %s"
                         % (_age_say(rec.get("measuredTs"), now_ms) + " ago", rec.get("why") or "no reason recorded"))
    if not isinstance(rows, list):
        return UNKNOWN, ("the receipt carries a summary, not rows (%s) - a summary cannot say which row disagrees,"
                         " so nothing here is known per row" % type(rows).__name__)
    fresh, fwhy = freshness(rec, stamp)
    if fresh is None:
        return UNKNOWN, fwhy
    if fresh is False:
        return UNKNOWN, "%s - the %s lane re-measures within %d min" % (fwhy, LANE, int(EVERY_S // 60))
    try:
        live = len(oracle_rows()) if live_rows is None else int(live_rows)
    except Exception as e:
        return UNKNOWN, ("the oracle cannot be read now (%s), so whether every row was judged is UNKNOWN"
                         % type(e).__name__)
    judged = len(rows)
    bad = [r for r in rows if not (isinstance(r, dict) and r.get("agree") is True)]
    if judged != live:
        return MISSING, ("%d of %d oracle rows were judged - %d row(s) never reached the composition; %s"
                         % (judged, live, abs(live - judged), _limit_say(rec)))
    if bad:
        return MISSING, ("%d of %d rows are NOT theirs: %s%s - measured %s ago on build %s; %s"
                         % (len(bad), judged,
                            "; ".join("%s / %s: %s" % (r.get("runeword"), r.get("base"), str(r.get("why"))[:90])
                                      for r in bad[:3] if isinstance(r, dict)),
                            " ..." if len(bad) > 3 else "", _age_say(rec.get("measuredTs"), now_ms),
                            (rec.get("bible") or {}).get("id"), _limit_say(rec)))
    return OK, ("%d of %d rows are theirs line for line - measured %s ago on build %s; %s"
                % (judged, live, _age_say(rec.get("measuredTs"), now_ms), (rec.get("bible") or {}).get("id"),
                   _limit_say(rec)))


def contract(path=None, stamp=None):
    """The lane in the SHARED supervision vocabulary. -> {on, worked, lastTs, owed, say}

    on      True - this lane has no switch (it reads the page and writes its own receipt; nothing to switch off)
    worked  LIFETIME ticks whose composition judged every row (runsMeasured), from the receipt; None = UNKNOWN
    lastTs  when it last measured (attempted); None = never / unreadable
    owed    rows the FRESH receipt says are not theirs; None when the receipt is absent, stale, node absent or a
            summary - UNKNOWN, never 0 [[heart-first]] §2 §3 §7
    """
    rec, rwhy = read_receipt(path)
    out = {"on": True, "worked": None, "lastTs": None, "owed": None, "say": ""}
    if rec is None:
        out["say"] = "%s - worked / lastTs / owed are UNKNOWN, not 0" % rwhy
        return out
    w = rec.get("runsMeasured")
    out["worked"] = w if (isinstance(w, int) and not isinstance(w, bool)) else None
    t = rec.get("measuredTs")
    out["lastTs"] = t if (isinstance(t, int) and not isinstance(t, bool)) else None
    rows = rec.get("rows")
    if not isinstance(rows, list):
        out["say"] = "owed UNKNOWN: %s" % (rec.get("why") if rows is None else "the receipt carries a summary")
        return out
    fresh, fwhy = freshness(rec, stamp)
    if fresh is not True:
        out["say"] = "owed UNKNOWN: %s" % fwhy
        return out
    out["owed"] = sum(1 for r in rows if not (isinstance(r, dict) and r.get("agree") is True))
    out["say"] = "%d row(s) owed a fix; %d judged; %s" % (out["owed"], len(rows), fwhy)
    return out


def run_once(path=None, force=False, now_ms=None):
    """ONE lane tick: measure when the receipt is absent, could not judge, is stale, or is older than REMEASURE_S;
    else leave it. -> {measured, wrote, ok, why, agreed, owed, node}"""
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    p = path or receipt_path()
    rec, rwhy = read_receipt(p)
    stamp = bible_stamp()
    if not force and rec is not None and isinstance(rec.get("rows"), list):
        fresh, fwhy = freshness(rec, stamp)
        t = rec.get("measuredTs")
        young = isinstance(t, int) and 0 <= (now - t) < REMEASURE_S * 1000
        if fresh is True and young:
            c = contract(p, stamp)
            return {"measured": False, "wrote": False, "ok": rec.get("ok"), "agreed": rec.get("agreed"),
                    "owed": c["owed"], "node": rec.get("node"),
                    "why": "nothing to re-measure: %s, %s ago" % (fwhy, _age_say(t, now))}
    rep = measure(now_ms=now)
    wrote = write_receipt(rep, p)
    c = contract(p, stamp) if wrote else {"owed": None}
    return {"measured": True, "wrote": wrote, "ok": rep.get("ok"), "agreed": rep.get("agreed"),
            "owed": c.get("owed"), "node": rep.get("node"),
            "why": rep.get("why") + ("" if wrote else " - AND THE RECEIPT COULD NOT BE WRITTEN")}


def main(argv):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    if "--once" in argv or "--force" in argv:
        r = run_once(force="--force" in argv)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r.get("ok") else (2 if r.get("agreed") is None else 1)
    st, why = verdict()
    c = contract()
    print("%s %s" % ({OK: "\U0001f7e2", MISSING: "\U0001f534", UNKNOWN: "⚪"}.get(st, "?"), why))
    print("lane %s: on %s · worked %s · lastTs %s · owed %s - %s"
          % (LANE, c["on"], c["worked"], c["lastTs"], c["owed"], c["say"]))
    return 0 if st == OK else (2 if st == UNKNOWN else 1)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
