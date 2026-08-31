"""What is a name WORTH, given the lane that read it and the surface it was read off?

⚠ REG-439 RETRACTED v2354's FIGURES, AND THAT RETRACTION WAS ITSELF WRONG. v2354 measured the
journal when `sessions.jsonl` held ~5,761 rows. By the time I "re-derived" it the file had
ROTATED to 860 rows while `sessions.1.jsonl` quietly held 7,103 - and `_journal_path()` returns
only the current generation. So the smaller table was not a correction, it was the same query
run against a fifth of the evidence. REG-440.

Measured 2026-08-31 over the WHOLE RING (7,980 rows; 1,359 name-sightings placed on a segment),
judged against 672 roster names (uniques + set pieces + set names + the 105 runewords that had no
roster at all until v2361). Five of v2354's entries reproduce EXACTLY - deep/inventory 1/11,
deep/gameplay 0/38, ocr/stash 0/27, ocr/inventory 0/17, deep/loot 0/5 - and the rest have simply
grown, because he has been playing:

    lane   surface       real   seen   Wilson lower (95%)
    deep   chronicle       45     74       0.4942
    deep   stash            4     25       0.0640
    deep   inventory        1     11       0.0162
    deep   gameplay         0     38       0.0000
    ocr    gameplay         1    583       0.0003
    ocr    (no scene)       0    359       0.0000
    ocr    transition       0     64       0.0000
    ocr    town             0     49       0.0000
    ocr    chronicle        0     37       0.0000
    ocr    stash            0     27       0.0000
    ocr    inventory        0     17       0.0000
    deep   loot             0      5       0.0000

TWO FINDINGS, AND THE SECOND INVERTS THE OBVIOUS READING.

**1. The `ocr` lane has produced ONE real item name in 1,136 placed sightings** - `WIzENDRAW`, a
garble that case-folded onto a real name. OCR earns its keep on STRUCTURE (is a panel open, which
tab) and nothing at all on NAMES. The lane design already held that ocr is provisional and never
reaches the register; this is that design confirmed by measurement rather than assertion.

**2. A CHRONICLE PAGE IS THE BEST NAMING SURFACE THERE IS, not the worst** - 45 real of 74, an
order of magnitude better than anywhere else, because it is a menu of clean rendered text. What
it must never do is imply POSSESSION: it lists items he does not own. Precision and provenance
are ORTHOGONAL, `_vaultMayClaim` answers only the second, and a gate built on "chronicle = bad"
would have discarded his best source. [[d2r-vault-routing]]

⚠ A ZERO FROM FIVE SAMPLES IS NOT A ZERO FROM 583. Anything under MIN_SAMPLES answers None and is
still READ - a gate that refuses to pay for what it has not measured can never measure it.
[[unknown-stays-unknown]]

⚠ AND EVERY MEASUREMENT OVER HIS JOURNAL MUST READ THE RING. Three separate "contradictions"
during this arc were one cause: a query answered differently before and after a rotation.
"""

MIN_SAMPLES = 30          # below this we have not looked enough to say anything

# (real, seen) keyed by (lane, surface) — the 2026-08-31 corpus. Rebuild with recount().
OBSERVED = {
    # ⚠ v2362 — MEASURED OVER THE WHOLE JOURNAL RING. v2354's figures were CORRECT and the
    # REG-439 retraction of them was itself wrong: it re-measured only `sessions.jsonl`, which
    # had rotated from 5,761 rows to 860 while `sessions.1.jsonl` held 7,103. Five of v2354's
    # entries reproduce EXACTLY over the ring (deep/inventory 1/11, deep/gameplay 0/38,
    # ocr/stash 0/27, ocr/inventory 0/17, deep/loot 0/5); the rest have simply grown, because he
    # has been playing. REG-440.
    #
    # 7,980 rows across the ring; 1,359 name-sightings placed on a segment. Judged against 672
    # roster names (uniques + set pieces + set names + the 105 runewords added in v2361).
    ("deep", "chronicle"):  (45, 74),
    ("deep", "stash"):      (4, 25),
    ("deep", "inventory"):  (1, 11),
    ("deep", "gameplay"):   (0, 38),
    ("deep", "loot"):       (0, 5),
    ("ocr", "gameplay"):    (1, 583),
    ("ocr", "no-scene"):    (0, 359),
    ("ocr", "transition"):  (0, 64),
    ("ocr", "town"):        (0, 49),
    ("ocr", "chronicle"):   (0, 37),
    ("ocr", "stash"):       (0, 27),
    ("ocr", "inventory"):   (0, 17),
}
CORPUS = {"rows": 7980, "roster": 672, "placed": 1359,
          "measured": "2026-08-31 over the whole journal RING (REG-440)"}

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
