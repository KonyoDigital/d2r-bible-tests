"""What is a name WORTH, given the lane that read it and the surface it was read off?

Measured against his real journal on 2026-08-31: 5,761 rows, judged against a 567-name roster
(uniques + set pieces + set names). Counted over DISTINCT names, because counting rows lets one
loud frame dominate.

    lane   surface       real   seen   Wilson lower (95%)
    deep   chronicle       38     61       0.4975
    deep   stash            3     25       0.0417
    deep   inventory        1     11       0.0162
    deep   gameplay         0     38       0.0000
    ocr    gameplay         1    366       0.0005
    ocr    (no scene)       0    253       0.0000
    ocr    transition       0     59       0.0000
    ocr    town             0     46       0.0000
    ocr    chronicle        0     33       0.0000
    ocr    stash            0     27       0.0000
    ocr    inventory        0     17       0.0000

TWO FINDINGS, AND THE SECOND ONE INVERTS THE OBVIOUS READING.

**1. The `ocr` lane has produced ONE real item name in 801 sightings** - and that one is
`WIzENDRAW`, a garble that happened to case-fold onto a real name. OCR is worth having for
STRUCTURE (is a stash panel open, which tab is showing) and is worth nothing for NAMES. The lane
design already says ocr is provisional and never reaches the register; this is that design
confirmed by measurement rather than by assertion.

**2. A CHRONICLE PAGE IS THE BEST NAMING SURFACE THERE IS, not the worst.** `deep` on a chronicle
page is 38 real of 61 - an order of magnitude better than anywhere else, because it is a menu of
clean rendered text. What it must never do is imply POSSESSION: it lists items he does not own.
Precision and provenance are ORTHOGONAL questions, and `_vaultMayClaim` answers only the second.
Conflating them is exactly how "chronicles read wrong as vault items" happened, and a gate built
on "chronicle = bad" would have thrown away his best source. [[d2r-vault-routing]]

**3. `deep` on gameplay is 0 of 38.** Those are paid reads spent on frames that structurally
cannot show a legible item name.

⚠ A ZERO FROM FIVE SAMPLES IS NOT A ZERO FROM 366. `deep`/`loot` is 0/5: its Wilson LOWER bound
is 0.0000, identical to a surface measured over hundreds, and it means something entirely
different - nobody has looked. Anything under MIN_SAMPLES answers UNKNOWN and is treated with
caution, never as "proven junk". A gate that cannot tell "measured bad" from "not measured" will
eventually discard a real find and call it precision. [[unknown-stays-unknown]]
"""

MIN_SAMPLES = 30          # below this we have not looked enough to say anything

# (real, seen) keyed by (lane, surface) — the 2026-08-31 corpus. Rebuild with recount().
OBSERVED = {
    ("deep", "chronicle"):  (38, 61),
    ("deep", "stash"):      (3, 25),
    ("deep", "inventory"):  (1, 11),
    ("deep", "gameplay"):   (0, 38),
    ("deep", "loot"):       (0, 5),
    ("ocr", "gameplay"):    (1, 366),
    ("ocr", "transition"):  (0, 59),
    ("ocr", "town"):        (0, 46),
    ("ocr", "chronicle"):   (0, 33),
    ("ocr", "stash"):       (0, 27),
    ("ocr", "inventory"):   (0, 17),
}
CORPUS = {"rows": 5761, "roster": 567, "measured": "2026-08-31"}

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
