# -*- coding: utf-8 -*-
"""LEDGER 3.0 - the per-session EXTRACTION RECORD, assembled read-only from the stores that exist.

HIS ORDER 2026-09-28 (#58, handoff §33), his words: "the ledger also needs flagship 3.0 upgrade
architecture and rendering with its own section properly.. like the evidence the proof the tooltips
the sections related the witnesses everything there backend might need to be physically showing too
so it has a dashboard of some sort connected to it so we can see what got tallied.. ... i want to
see the reels n shelf great we have that now the extraction and tallying and counting and proof of
ledgers to all need that same visual rendering so i can see that it was tallied properly and counted
correctly. and where it was seen.."

WHAT ONE RECORD ANSWERS, for ONE reel/session: what did it yield? Which names the live reader read,
on which frames, and WHO read each one (the model that answered, else the lane); which of those names
the chronicle book banked from THIS reel and on how many independent reels besides; which the vault
ledger witnessed in THIS visit, and the tier the item stands on today (visits, never frames); where
each name was seen (the reader's own names_loc); and which way the reader routed it (vault / thrown /
pending / farmed). Beside the names: the film (frames on the shelf, or the tombstone that took it),
the reel's river station, the structural survey, and a side-by-side AGREEMENT of the journal against
the vault ledger - two engines, shown together and never averaged.

BUILT ON THE EXISTING STORES, NEVER A PARALLEL COPY (his Ledger 3.0 rule). This module opens no
file and names no store by its filename: control_app hands it the loaded objects, resolved through
its own path authorities (TV_SESSIONS, TV_CHRON_EVIDENCE, TV_VAULT_LEDGER, TV_HIST), so a fixture
can never reach his tree and a law can drive the whole record over temp stores.
    the journal ring          rows the live reader wrote (sessionId, lane, model, names, names_loc ...)
    the chronicle book        {uniques|sets}[name] -> sightings {reel, frame, lane, conf, witness}
    the vault witness ledger  owned[] rows -> witnesses {session, witness, frame, conf, lane}
    the river stamps          river_stamp.history(reel)  - the reel's station journey
    the structural survey     retro_triage.load()        - panels / frames per reel
    the tombstones            control_app.tombstone_view - a reel that is gone, and why

ONE KEY PER FACT, BORROWED NEVER COPIED [[copy-drift]]:
    a reel     chronicle_retro._reel_key  - "reel_s_X" and "s_X" are ONE reel (trace_spine measured
                                            3,914 of 8,517 sightings as the same row under both)
    a name     item_identity.vault_key then trace_spine.name_key (qualifier kept, glyphs folded)
    a visit    vault_retro.look_id folded by vault_retro._fold_bare_sessions - one trial per VISIT,
               never per frame of a still screen (his ruling 2026-09-28, §34.2)
    a tier     vault_evidence.tier over vault_evidence._measure - the one table
    witnesses  chronicle_retro.witnesses - the one independence verdict

UNKNOWN IS NEVER 0 [[unknown-stays-unknown]]: a side whose store could not be read is None and the
record's `unknown` list says which and why; a session that NO store knows is ok:False with a why,
never an empty record dressed as a quiet night.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

V = 1
#: journal lanes whose rows READ something - they carry `names`. The other lanes (skip, system,
#: kai, intake, deep-owed, known, chronicle) are counted in `lanes` but name nothing themselves.
READ_LANES = ("deep", "ocr", "verify")
#: the reader's own routing lists, one flag each. Measured on his journal: 400 rows carry
#: vault_names / unvault_names, 366 carry farmed / pending / thrown.
ROUTE_LISTS = (("vault", "vault_names"), ("unvault", "unvault_names"), ("farmed", "farmed_names"),
               ("pending", "pending_names"), ("thrown", "thrown_names"))
LEDGERS = ("uniques", "sets")


# ── the borrowed keys ────────────────────────────────────────────────────────────────────────
def reel_key(reel):
    """chronicle_retro's normaliser, called - the ONE spelling of a reel. '' for nothing."""
    import chronicle_retro as _cr
    return _cr._reel_key(str(reel or "").strip())


def name_key(name):
    """The join key for a NAME across the three stores. '' for nothing.

    item_identity.vault_key keeps the qualifier (Latent / Renewed are different objects) and
    drops the rendering tail; trace_spine.name_key folds the apostrophe glyphs and case - his
    "Saracen's Chance" is straight-quoted in one store and curly in another, measured.
    """
    import item_identity as _ii
    import trace_spine as _ts
    s = str(name or "").strip()
    if not s:
        return ""
    return _ts.name_key(_ii.vault_key(s) or s)


# ── the journal side ─────────────────────────────────────────────────────────────────────────
def _who(row):
    """Who read this row: the model that answered, else the lane. Never blank for a read row."""
    m = str(row.get("model") or "").strip()
    return m if m else "lane:%s" % str(row.get("lane") or "?")


def _journal_side(rows):
    """One session's journal rows -> (side, items). Every count here was measured from rows."""
    lanes, readers = {}, {}
    items = {}
    t0 = t1 = None
    door = ver = None
    owed, answered = set(), set()
    intake_shots = 0
    registered = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        lane = str(r.get("lane") or "")
        lanes[lane] = lanes.get(lane, 0) + 1
        ts = r.get("ts")
        if isinstance(ts, (int, float)) and not isinstance(ts, bool):
            t0 = ts if t0 is None or ts < t0 else t0
            t1 = ts if t1 is None or ts > t1 else t1
        if door is None and r.get("door"):
            door = str(r.get("door"))
        if ver is None and r.get("ver"):
            ver = str(r.get("ver"))
        if lane == "deep-owed" and r.get("frameId"):
            owed.add(str(r.get("frameId")))
        if lane == "deep" and r.get("frameId"):
            answered.add(str(r.get("frameId")))
        if lane == "intake" and isinstance(r.get("intake"), dict):
            intake_shots += 1
        if lane == "kai" and isinstance(r.get("kai"), dict):
            reg = r["kai"].get("register")
            if isinstance(reg, dict):
                for it in reg.get("items") or []:
                    if isinstance(it, dict) and it.get("name"):
                        registered[name_key(it["name"])] = {
                            "name": it["name"], "tier": it.get("tier"), "loc": it.get("loc"),
                            "frameId": it.get("frameId")}
        if lane not in READ_LANES:
            continue
        who = _who(r)
        readers[who] = readers.get(who, 0) + 1
        names = r.get("names")
        if lane == "verify" and isinstance(r.get("verify"), dict):
            # a second look confirms names; its own `names` list is empty by design
            names = list(r["verify"].get("confirm") or [])
        loc = r.get("names_loc") if isinstance(r.get("names_loc"), dict) else {}
        tags = r.get("lifecycle_tags") if isinstance(r.get("lifecycle_tags"), dict) else {}
        for nm in (names or []):
            nm = str(nm or "").strip()
            key = name_key(nm)
            if not key:
                continue
            it = items.get(key)
            if it is None:
                it = items[key] = {"name": nm, "reads": 0, "frames": [], "firstTs": None,
                                   "lastTs": None, "lanes": [], "readBy": [], "loc": None,
                                   "tag": None, "confirmed": False, "provisional": True,
                                   "routed": {}}
            it["reads"] += 1
            # MEASURED on his journal 2026-09-29: the OCR lane journals what it saw as `names`,
            # provisionally ("Your Gamlng Rlg Is Readyl", 4 reads, ocr-mac). A name every read of
            # which was provisional is listed apart and never counted as NAMED; one real read clears it.
            if not r.get("provisional"):
                it["provisional"] = False
            fid = str(r.get("frameId") or "")
            if fid and fid not in it["frames"]:
                it["frames"].append(fid)
            if isinstance(ts, (int, float)) and not isinstance(ts, bool):
                it["firstTs"] = ts if it["firstTs"] is None or ts < it["firstTs"] else it["firstTs"]
                it["lastTs"] = ts if it["lastTs"] is None or ts > it["lastTs"] else it["lastTs"]
            if lane not in it["lanes"]:
                it["lanes"].append(lane)
            if who not in it["readBy"]:
                it["readBy"].append(who)
            if loc.get(nm):
                it["loc"] = str(loc.get(nm))
            if tags.get(nm):
                it["tag"] = str(tags.get(nm))
            if lane == "verify":
                it["confirmed"] = True
        for flag, field in ROUTE_LISTS:
            for nm in (r.get(field) or []):
                key = name_key(nm)
                if key and key in items:
                    items[key]["routed"][flag] = True
    for key, reg in registered.items():
        it = items.get(key)
        if it is None:
            it = items[key] = {"name": reg["name"], "reads": 0, "frames": [], "firstTs": None,
                               "lastTs": None, "lanes": [], "readBy": [], "loc": None,
                               "tag": None, "confirmed": False, "provisional": True,
                               "routed": {}}
        it["registered"] = {"tier": reg.get("tier"), "loc": reg.get("loc"),
                            "frameId": reg.get("frameId")}
        it["provisional"] = False          # the sealed register grounded it against the item database
        if it["loc"] is None and reg.get("loc"):
            it["loc"] = str(reg.get("loc"))
    side = {
        "rows": len(rows), "lanes": lanes,
        "reads": {"answered": sum(lanes.get(l, 0) for l in READ_LANES),
                  "owed": len(owed), "lost": len(owed - answered)},
        "readers": readers, "intakeShots": intake_shots,
        "registered": len(registered),
        "door": door, "ver": ver,
        "span": ({"t0": t0, "t1": t1} if t0 is not None else None),
    }
    return side, items


# ── the chronicle side ───────────────────────────────────────────────────────────────────────
def _chronicle_side(chron, key):
    """The chronicle book's sightings from THIS reel, per name. -> (items, unknown_why|None)"""
    if chron is None:
        return {}, "the chronicle book could not be read, so what it banked from this reel is UNKNOWN"
    if not isinstance(chron, dict):
        return {}, "the chronicle book is not a book (%s), so its side is UNKNOWN" % type(chron).__name__
    try:
        import chronicle_retro as _cr
    except Exception as e:
        return {}, "chronicle_retro could not be read (%s), so the independence verdict is UNKNOWN" % str(e)[:60]
    items = {}
    for led in LEDGERS:
        book = chron.get(led)
        if not isinstance(book, dict):
            continue
        for nm, sightings in book.items():
            if not isinstance(sightings, list):
                continue
            mine, seen = [], set()
            for s in sightings:
                if not isinstance(s, dict) or not s.get("reel"):
                    continue
                if reel_key(s.get("reel")) != key:
                    continue
                # the same sighting under both spellings of the reel is ONE row
                k = (s.get("frame"), s.get("lane"), s.get("conf"))
                if k in seen:
                    continue
                seen.add(k)
                mine.append(s)
            if not mine:
                continue
            frames = []
            lanes = []
            for s in mine:
                if s.get("frame") and s.get("frame") not in frames:
                    frames.append(s.get("frame"))
                ln = str(s.get("lane") or "claude")
                if ln not in lanes:
                    lanes.append(ln)
            all_rows = [s for s in sightings if isinstance(s, dict)]
            reels = {reel_key(s.get("reel")) for s in all_rows if s.get("reel")}
            nk = name_key(nm)
            if not nk:
                continue
            items[nk] = {
                "name": nm, "ledger": led, "sightings": len(mine), "frames": frames,
                "lanes": lanes,
                "witnessTags": list(_cr.witnesses(all_rows)),
                "independentReels": len(reels),
                "hand": any(str(s.get("lane") or "") == "manual" for s in all_rows),
            }
    return items, None


# ── the vault side ───────────────────────────────────────────────────────────────────────────
def _vault_side(vault_doc, key):
    """The vault ledger's witnesses from THIS visit, per name, with the item's tier today.
    -> (items, unknown_why|None). `vault_doc` is the loaded ledger (its `owned` list) or None."""
    if vault_doc is None:
        return {}, "the vault witness ledger could not be read, so what it witnessed in this visit is UNKNOWN"
    owned = vault_doc.get("owned") if isinstance(vault_doc, dict) else None
    if not isinstance(owned, list):
        return {}, "the vault witness ledger has no owned list, so its side is UNKNOWN"
    try:
        import vault_evidence as _ve
        import vault_retro as _vr
        floor = float(_vr.KEEP_CONF_FLOOR)
        fold = _vr._fold_bare_sessions
    except Exception as e:
        return {}, ("vault_evidence or vault_retro could not be read (%s), so the tier is UNKNOWN"
                    % str(e)[:60])
    items = {}
    for nm, rows in _ve._group(owned):
        mine = []
        for row in rows:
            for w in (row.get("witnesses") or []):
                if isinstance(w, dict) and reel_key(w.get("session")) == key:
                    mine.append(w)
        if not mine:
            continue
        # ONE TRIAL PER VISIT, his ruling §34.2 - the same look id and the same fold the gate uses.
        # A still screen held for 102 frames is ONE visit here, as it is in vault_evidence._measure.
        visits = set(fold({_vr.look_id(w) for w in mine if _vr.look_id(w)}))
        won = set(fold({_vr.look_id(w) for w in mine if _vr.look_id(w) and _vr.look_saw_it(w, floor)}))
        frames = []
        for w in mine:
            f = str(w.get("frame") or "").strip()
            if f and f not in frames:
                frames.append(f)
        measured = _ve._measure(rows, floor)
        if measured is None:
            tier = {"tier": None, "bound": None, "successes": None, "trials": None,
                    "why": "a witness row could not be read, so the tier is UNKNOWN"}
            retro = None
        else:
            tier = _ve.tier(measured[0], measured[1])
            flagged = _ve._retro_row(nm, measured)
            retro = flagged.get("flag") if isinstance(flagged, dict) else None
        nk = name_key(nm)
        if not nk:
            continue
        items[nk] = {
            "name": nm, "lane": rows[0].get("lane"), "kind": rows[0].get("kind"),
            "witnessesHere": len(mine), "visitsHere": len(visits), "sawItHere": len(won),
            "frames": frames,
            "tier": tier, "retro": retro,
        }
    return items, None


# ── the film, the station, the survey, the tombstone ─────────────────────────────────────────
def _film(hist, key, tombstone):
    """Frames on the shelf for this reel, or why there are none. Never a 0 for 'did not look'."""
    reel = "reel_" + key
    if not hist:
        return {"frames": None, "onShelf": None, "why": "no shelf was named, so the film is UNKNOWN"}
    rd = os.path.join(hist, reel)
    if os.path.isdir(rd):
        try:
            n = len([f for f in os.listdir(rd) if f.startswith("f_") and f.endswith(".jpg")])
        except Exception as e:
            return {"frames": None, "onShelf": True,
                    "why": "the reel folder is on the shelf but could not be listed (%s)" % type(e).__name__}
        sealed = os.path.isfile(os.path.join(rd, "kai_report.json"))
        return {"frames": n, "onShelf": True, "sealed": sealed,
                "why": "%d film still(s) on the shelf%s" % (n, "" if sealed else " - not sealed yet")}
    if tombstone:
        return {"frames": tombstone.get("frames"), "onShelf": False,
                "why": "released: %s" % str(tombstone.get("why") or "no reason recorded")[:160]}
    return {"frames": None, "onShelf": False,
            "why": "no reel folder on the shelf and no tombstone - whether it was ever filmed is UNKNOWN"}


def _station(stamps, key):
    """The reel's river journey, from river_stamp's own history. -> {current, hops, why}"""
    reel = "reel_" + key
    if stamps is None:
        return {"current": None, "hops": None, "why": "the river stamps could not be read - the station is UNKNOWN"}
    try:
        import river_stamp as _rs
    except Exception as e:
        return {"current": None, "hops": None, "why": "river_stamp could not be read (%s)" % str(e)[:60]}
    if isinstance(stamps, dict) and "rows" in stamps:
        rows = [r for r in (stamps.get("rows") or []) if isinstance(r, dict) and str(r.get("reel")) == reel]
        return {"current": (rows[-1].get("station") if rows else None), "hops": len(rows),
                "why": ("never stamped - it has not been walked with a stamper attached" if not rows
                        else "%d hop(s), last by %s" % (len(rows), rows[-1].get("by") or "?"))}
    h = _rs.history(reel, stamps if isinstance(stamps, str) else None)
    if not h.get("ok"):
        return {"current": None, "hops": None, "why": h.get("why") or "UNKNOWN"}
    return {"current": h.get("current"), "hops": h.get("n"),
            "why": h.get("why") or "%d hop(s)" % (h.get("n") or 0)}


def _survey(triage, key):
    """retro_triage's structural verdict for this reel, or None with a why in `unknown`."""
    if triage is None:
        return None, "the structural survey could not be read, so panels/frames are UNKNOWN"
    if not isinstance(triage, dict):
        return None, "the structural survey is not a map, so its side is UNKNOWN"
    row = triage.get("reel_" + key) or triage.get(key)
    if not isinstance(row, dict):
        return None, None          # not surveyed yet is a fact, not an unknown
    return {"panels": row.get("panels"), "frames": row.get("frames"), "full": row.get("full"),
            "ts": row.get("ts")}, None


def _tombstone_of(tombstones, key):
    if not isinstance(tombstones, list):
        return None
    for t in tombstones:
        if not isinstance(t, dict):
            continue
        if reel_key(t.get("reel") or t.get("session")) == key:
            return t
    return None


# ── the record ───────────────────────────────────────────────────────────────────────────────
def session_rows(journal, sid):
    """The journal rows of ONE session, in ts order, or None when the journal cannot be read."""
    if journal is None:
        return None
    key = reel_key(sid)
    mine = [r for r in journal if isinstance(r, dict) and reel_key(r.get("sessionId")) == key]
    mine.sort(key=lambda r: (r.get("ts") or 0))
    return mine


def session_record(sid, stores):
    """The per-session extraction record for `sid`. -> dict

    `stores` is {journal: rows|None, chron: book|None, vault: doc|None, hist: path|None,
                 stamps: river_stamp.rows()|path|None, triage: dict|None, tombstones: list|None,
                 unknown: [why...]} - loaded by the caller through its own path authorities.
    """
    key = reel_key(sid)
    if not key:
        return {"ok": False, "v": V, "why": "no session id was named"}
    unknown = list(stores.get("unknown") or [])
    journal = stores.get("journal")
    rows = session_rows(journal, key)
    if journal is None:
        unknown.append("the journal could not be read, so the reader's trail for this reel is UNKNOWN")
    tomb = _tombstone_of(stores.get("tombstones"), key)
    film = _film(stores.get("hist"), key, tomb)
    if rows:
        jside, jitems = _journal_side(rows)
    else:
        jside, jitems = None, {}
        if journal is not None:
            unknown.append("no journal row carries this session - its rows rotated out of the ring, "
                           "or it was never journalled; the reader's trail is UNKNOWN, not empty")
    citems, cwhy = _chronicle_side(stores.get("chron"), key)
    if cwhy:
        unknown.append(cwhy)
    vitems, vwhy = _vault_side(stores.get("vault"), key)
    if vwhy:
        unknown.append(vwhy)
    survey, swhy = _survey(stores.get("triage"), key)
    if swhy:
        unknown.append(swhy)
    station = _station(stores.get("stamps"), key)
    if station.get("hops") is None:
        unknown.append(station.get("why") or "the river stamps could not be read - the station is UNKNOWN")

    known_by = [k for k, v in (("journal", bool(rows)), ("chronicle", bool(citems)),
                               ("vault", bool(vitems)), ("shelf", film.get("onShelf") is True),
                               ("tombstone", tomb is not None),
                               ("river", station.get("hops") not in (None, 0)),
                               ("survey", survey is not None)) if v]
    if not known_by:
        return {"ok": False, "v": V, "session": key, "reel": "reel_" + key,
                "why": "no store knows this session - not the journal, the chronicle book, the vault "
                       "ledger, the shelf, the tombstones, the river or the survey",
                "unknown": unknown}

    # the union of names, one row per name, each side present or None
    keys = []
    for src in (jitems, citems, vitems):
        for k in src:
            if k not in keys:
                keys.append(k)
    items = []
    for k in keys:
        j, c, v = jitems.get(k), citems.get(k), vitems.get(k)
        name = (j or c or v)["name"]
        items.append({"key": k, "name": name,
                      "journal": j, "chronicle": c,
                      "vault": v if vitems or stores.get("vault") is not None else None})
    items.sort(key=lambda it: ((it["journal"] or {}).get("firstTs") or 0, it["name"].lower()))

    # AGREEMENT - two engines side by side, never averaged: the live reader's journal against the
    # vault sweep's ledger, for the names each one has for this reel. UNKNOWN when either side is.
    # Provisional (OCR-only) names are left out of the reader's side and said so - junk the OCR
    # lane saw once is not a name the vault sweep failed to witness.
    named_keys = {k for k, it in jitems.items() if not it.get("provisional")}
    if rows and stores.get("vault") is not None:
        jk, vk = named_keys, set(vitems)
        agreement = {"both": sorted(jk & vk), "journalOnly": sorted(jk - vk), "vaultOnly": sorted(vk - jk),
                     "why": ("%d name(s) on both sides, %d only in the reader's journal, %d only in the "
                             "vault ledger (%d provisional OCR-only name(s) left out)"
                             % (len(jk & vk), len(jk - vk), len(vk - jk), len(jitems) - len(named_keys)))}
    else:
        agreement = None

    yield_ = {
        "named": len(named_keys), "provisional": len(jitems) - len(named_keys),
        "registered": (jside or {}).get("registered"),
        "chronicle": len(citems) if cwhy is None else None,
        "vault": len(vitems) if vwhy is None else None,
        "routedVault": sum(1 for it in jitems.values() if it["routed"].get("vault")),
        "thrown": sum(1 for it in jitems.values() if it["routed"].get("thrown")),
        "pending": sum(1 for it in jitems.values() if it["routed"].get("pending")),
        "confirmed": sum(1 for it in jitems.values() if it.get("confirmed")),
    }
    frames = {
        "journal": len({f for it in jitems.values() for f in it["frames"]}),
        "chronicle": len({f for it in citems.values() for f in it["frames"]}) if cwhy is None else None,
        "vault": len({f for it in vitems.values() for f in it["frames"]}) if vwhy is None else None,
    }
    return {
        "ok": True, "v": V,
        "session": key, "reel": "reel_" + key,
        "door": (jside or {}).get("door"), "ver": (jside or {}).get("ver"),
        "span": (jside or {}).get("span"),
        "journal": jside,
        "readers": (jside or {}).get("readers"),
        "film": film, "station": station, "survey": survey, "tombstone": tomb,
        "items": items, "yield": yield_, "evidenceFrames": frames,
        "agreement": agreement,
        "knownBy": known_by, "unknown": unknown,
    }


def session_summary(sid, rows):
    """The cheap row for the sessions list - journal-only, no store joins. -> dict"""
    key = reel_key(sid)
    side, items = _journal_side(rows or [])
    return {
        "session": key, "reel": "reel_" + key, "door": side["door"], "ver": side["ver"],
        "span": side["span"], "rows": side["rows"], "lanes": side["lanes"],
        "reads": side["reads"], "readers": side["readers"],
        "named": sum(1 for it in items.values() if not it.get("provisional")),
        "provisional": sum(1 for it in items.values() if it.get("provisional")),
        "registered": side["registered"], "intakeShots": side["intakeShots"],
        "routedVault": sum(1 for it in items.values() if it["routed"].get("vault")),
        "thrown": sum(1 for it in items.values() if it["routed"].get("thrown")),
    }


def sessions(journal, limit=200):
    """Every journalled session, newest first, as cheap rows. -> dict

    `total` is every session the ring holds; `shown` is what this answer carries. A journal that
    cannot be read is ok:False, never an empty list.
    """
    if journal is None:
        return {"ok": False, "v": V, "sessions": [], "total": None, "shown": 0,
                "why": "the journal could not be read, so the session list is UNKNOWN - not empty"}
    import replay as _rp
    groups = _rp.split_sessions(journal)
    out = []
    for grp in groups:
        sid = next((r.get("sessionId") for r in grp if isinstance(r, dict) and r.get("sessionId")), "")
        if not sid:
            continue         # pre-v780 rows with nothing to key on: not a reel
        out.append(session_summary(sid, grp))
    try:
        lim = int(limit)
    except (TypeError, ValueError):
        lim = 200
    lim = max(1, lim)
    return {"ok": True, "v": V, "sessions": out[:lim], "total": len(out), "shown": min(len(out), lim),
            "why": ("%d session(s) in the ring, newest first%s"
                    % (len(out), "" if len(out) <= lim else " - %d shown, ?limit= for more" % lim))}


def census(stores, limit=32):
    """The heart's view: for the newest reels, can a record be drawn, and what disagrees.

    -> {ok, trails, noTrail: [reels on the shelf with a sealed report and NO journal rows],
        unknown: [...], agreement: {both, journalOnly, vaultOnly}, why}
    A sealed reel on the shelf whose journal rows are gone is a trail that cannot be drawn for
    footage he still has - that is the lost link this row names.
    """
    journal = stores.get("journal")
    hist = stores.get("hist")
    if journal is None:
        return {"ok": False, "trails": None, "noTrail": None,
                "why": "the journal could not be read, so no trail can be drawn - UNKNOWN, not 0"}
    if not hist or not os.path.isdir(hist):
        return {"ok": False, "trails": None, "noTrail": None,
                "why": "the shelf could not be opened, so which reels have a trail is UNKNOWN"}
    try:
        reels = sorted((d for d in os.listdir(hist) if d.startswith("reel_")), reverse=True)
    except Exception as e:
        return {"ok": False, "trails": None, "noTrail": None,
                "why": "the shelf could not be listed (%s)" % type(e).__name__}
    have = {reel_key(r.get("sessionId")) for r in journal if isinstance(r, dict) and r.get("sessionId")}
    trails, no_trail, both, jo, vo = 0, [], 0, 0, 0
    for reel in reels[:max(1, int(limit))]:
        key = reel_key(reel)
        sealed = os.path.isfile(os.path.join(hist, reel, "kai_report.json"))
        if key in have:
            trails += 1
            rec = session_record(key, stores)
            ag = rec.get("agreement") if rec.get("ok") else None
            if ag:
                both += len(ag["both"])
                jo += len(ag["journalOnly"])
                vo += len(ag["vaultOnly"])
        elif sealed:
            no_trail.append(reel)
    return {"ok": True, "trails": trails, "noTrail": no_trail, "reels": len(reels[:max(1, int(limit))]),
            "agreement": {"both": both, "journalOnly": jo, "vaultOnly": vo},
            "unknown": list(stores.get("unknown") or []),
            "why": ("%d reel(s) on the shelf, %d with a trail; %d sealed with NO trail" %
                    (len(reels[:max(1, int(limit))]), trails, len(no_trail)))}
