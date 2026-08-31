"""What is a name WORTH, given the lane that read it and the surface it was read off?

⚠ THE v2354 TABLE IS RETRACTED. It claimed denominators - deep/chronicle 61, ocr/gameplay 366,
deep/stash 25 - that a careful re-measurement on the same journal CANNOT REPRODUCE. Asked twice,
by two independently written expressions, deep/chronicle comes back as 10, not 61. I could not
reconstruct how the larger numbers arose, so they are withdrawn rather than defended. REG-439.

RE-DERIVED 2026-08-31 over 5,761 journal rows, judged against 672 roster names (uniques + set
pieces + set names + the 105 RUNEWORDS that had no roster at all until v2361 and so scored zero
by construction). Counted over DISTINCT names; 275 sightings placed on a segment, 98 unplaceable:

    lane   surface       real   seen   Wilson lower (95%)
    deep   chronicle        7     10       0.3968
    ocr    gameplay         0    201       0.0000
    ocr    (no scene)       0     93       0.0000
    ocr    chronicle        0      5       0.0000
    ocr    town             0      1       0.0000

WHAT SURVIVES THE CORRECTION, and it is the actionable half: **the `ocr` lane has produced zero
real item names across 300 placed sightings.** OCR earns its keep on STRUCTURE - is a panel open,
which tab - and nothing at all on NAMES. The lane design already held that ocr is provisional and
never reaches the register; this is that design confirmed by measurement.

WHAT DOES NOT SURVIVE: any claim about stash, inventory or the deep lane on gameplay. There is
not enough placed evidence to say anything about them, and `MIN_SAMPLES` now correctly answers
NOT ESTABLISHED for every one - which means `witnesses_required` returns the cautious default of
2 almost everywhere. That is the honest state of this measurement, not a failure of it.

⚠ A ZERO FROM FIVE SAMPLES IS NOT A ZERO FROM 201. Anything under MIN_SAMPLES answers None and is
still READ - a gate that refuses to pay for what it has not measured can never measure it.
[[unknown-stays-unknown]]
"""

MIN_SAMPLES = 30          # below this we have not looked enough to say anything

# (real, seen) keyed by (lane, surface) — the 2026-08-31 corpus. Rebuild with recount().
OBSERVED = {
    # ⚠ v2361 — RE-DERIVED, AND SMALLER THAN WHAT v2354 SHIPPED. The v2354 table claimed
    # denominators (deep/chronicle 61, ocr/gameplay 366, deep/stash 25 ...) that a careful
    # re-measurement on the same journal CANNOT REPRODUCE: the same query, run twice by two
    # different expressions, returns deep/chronicle = 10, not 61. I could not reconstruct how the
    # larger figures arose, so they are retracted rather than defended. See REG-439.
    #
    # Derivation, so this is checkable rather than asserted: every journal row carrying `items`
    # or `names`, timestamp parsed from `frameId` (both the bare `<n>_<ms>` and the
    # `<reel>/f_<ms>` path form), placed with reel_segments.activity_at, counted over DISTINCT
    # names, judged against uniques + set pieces + set names + RUNEWORDS (105 names that had no
    # roster at all before v2361 and therefore scored zero by construction).
    #
    # 275 name-sightings placed on a segment; 98 could not be placed.
    ("deep", "chronicle"):  (7, 10),
    ("ocr", "gameplay"):    (0, 201),
    ("ocr", "no-scene"):    (0, 93),
    ("ocr", "chronicle"):   (0, 5),
    ("ocr", "town"):        (0, 1),
}
CORPUS = {"rows": 5761, "roster": 672, "placed": 275, "unplaced": 98,
          "measured": "2026-08-31 (re-derived; v2354's figures retracted, REG-439)"}

GOOD = 0.20        # Wilson lower at or above this: believable on its own
WEAK = 0.01        # between WEAK and GOOD: needs corroboration


def _key(lane, surface):
    return (str(lane or "").strip().lower(), str(surface or "").strip().lower())


def _wilson(k, n):
    try:
        from confidence import wilson_lower
        return wilson_lower(k, n)
    except Exception:
        return 0.0


def precision(lane, surface, observed=None):
    """-> (wilson_lower|None, seen, why). None means NOT ESTABLISHED - never 0.0."""
    obs = observed if observed is not None else OBSERVED
    row = obs.get(_key(lane, surface))
    if not row:
        return None, 0, "no measurement exists for lane=%s surface=%s" % (lane, surface)
    k, n = row
    if n < MIN_SAMPLES:
        return None, n, ("only %d sample(s), below the %d needed to say anything - a zero here "
                         "means nobody has looked, not that it is bad" % (n, MIN_SAMPLES))
    return _wilson(k, n), n, "%d real of %d seen" % (k, n)


def witnesses_required(lane, surface, observed=None):
    """How many independent witnesses before a name from here may be believed? -> (n, why)

    ONE for a combination measured good, TWO for measured-weak, TWO for NOT MEASURED (the honest
    answer to "we do not know" is caution, not a veto and not a free pass), THREE for a
    combination measured to produce essentially nothing.
    """
    w, n, why = precision(lane, surface, observed=observed)
    if w is None:
        return 2, "not established (%s) - treated cautiously" % why
    if w >= GOOD:
        return 1, "%s (Wilson lower %.4f)" % (why, w)
    if w >= WEAK:
        return 2, "%s (Wilson lower %.4f) - corroboration required" % (why, w)
    return 3, ("%s (Wilson lower %.4f) - this lane/surface has produced almost nothing real"
               % (why, w))


def worth_paying_to_read(lane, surface, observed=None):
    """Should a PAID read be spent on this frame at all? -> (bool, why)

    Refused only where a combination has been MEASURED over a real sample to produce nothing.
    Unmeasured combinations are still read - that is how they become measured, and a gate that
    starves its own evidence can never improve.
    """
    w, n, why = precision(lane, surface, observed=observed)
    if w is None:
        return True, "unmeasured (%s) - read it, that is how it gets measured" % why
    if w <= 0.001 and n >= MIN_SAMPLES:
        return False, "%s (Wilson lower %.4f over %d) - measured to yield nothing" % (why, w, n)
    return True, "%s (Wilson lower %.4f)" % (why, w)


def recount(rows, roster, segments_for):
    """Rebuild OBSERVED from a journal, so the table cannot quietly rot as his corpus grows.

    `rows` journal dicts · `roster` a set of lowercased real names · `segments_for(sid)` the
    session's segments. Returns {(lane, surface): (real, seen)} over DISTINCT names.
    """
    import collections
    try:
        import reel_segments as rs
    except Exception:
        return {}
    buckets = collections.defaultdict(lambda: {"real": set(), "junk": set()})
    for r in rows or []:
        items = r.get("items") or r.get("names") or []
        if not items:
            continue
        sid = str(r.get("sessionId") or "")
        frame = str(r.get("frame") or r.get("frameId") or "")
        ts = None
        for chunk in reversed(frame.replace(".", "_").split("_")):
            if chunk.isdigit() and 12 <= len(chunk) <= 14:
                ts = int(chunk)
                break
        if not sid or not ts:
            continue
        act = rs.activity_at(segments_for(sid) or [], sid, ts)
        if isinstance(act, (tuple, list)):
            act = act[0]
        if not act:
            continue
        lane = str(r.get("lane") or "?").strip().lower()
        for it in items:
            nm = it.get("name") if isinstance(it, dict) else it
            if not isinstance(nm, str) or not nm.strip():
                continue
            key = "real" if nm.strip().lower() in roster else "junk"
            buckets[(lane, act)][key].add(nm.strip())
    return {k: (len(v["real"]), len(v["real"]) + len(v["junk"])) for k, v in buckets.items()}


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    print("measured %s over %d rows against %d roster names\n"
          % (CORPUS["measured"], CORPUS["rows"], CORPUS["roster"]))
    print("%-6s %-11s %9s %10s  %s" % ("lane", "surface", "wilson", "witnesses", "paid read?"))
    for k in sorted(OBSERVED, key=lambda x: -(OBSERVED[x][0] / float(OBSERVED[x][1] or 1))):
        w, n, _ = precision(*k)
        need, _why = witnesses_required(*k)
        pay, paywhy = worth_paying_to_read(*k)
        print("  %-4s %-11s %9s %10d  %s"
              % (k[0], k[1], ("%.4f" % w) if w is not None else "n/a", need,
                 "yes" if pay else "NO - " + paywhy[:44]))
