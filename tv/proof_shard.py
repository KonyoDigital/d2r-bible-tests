# -*- coding: utf-8 -*-
"""REG-2585 / REG-2586 — ONE PROVE, MANY MACHINES: a proof-level shard plan, and the import that brings shards home.

⚠ WHY. A full `heart2 --prove` is ~3.5 h on his Mac (V1: 4,353 proofs). Per-proof keys cannot shrink the count (Phase 0
and 0b, /workspace notes: no design gets under ~1,900 re-proves), so the lever left is WALL TIME: the same proofs, on
many CI runners at once, banked into the verdict cache, then brought home.

THE PLAN (REG-2585). `heart2 --prove [names] --push --proof-shard K/N` proves only shard K's proofs. Every shard
computes the SAME plan from the same bytes: each gate's proofs are cut into contiguous chunks no costlier than about a
quarter of a shard's fair share (gate_costs.json prices one run of the gate; a chunk pays one clean run plus one run
per proof), and the chunks go, costliest first, to the least-loaded shard (ties to the lowest K). So a 41-proof
browser gate no longer sits on one runner for over an hour, and every (gate, proof) lands in EXACTLY ONE shard - a
proof in none is never proven, a proof in two is paid twice. The plan's digest names gate, index, the proof entry
itself and the shard, so shards cut from different names, bytes or N cannot pass as one set.

THE IMPORT (REG-2586). `heart2 --import-shards FILE...` merges the shards' banked PROVENs into this machine's verdict
cache, through the store's one locked writer, ALL OR NOTHING:
  · every shard 1..N is present exactly once, each FINISHED, all with one N and one plan digest;
  · every shard ran on THIS checkout's HEAD sha, from a clean tree (no tracked file differing from HEAD);
  · an entry is taken only if it is what peek() would serve: a dated, static, fact-free PROVEN - an ELSEWHERE, a
    BLIND, an UNPROVABLE, an undated or a traced entry is never banked;
  · an entry must belong to the shard that carries it (its gate and proof index are in that shard's plan) - a stray
    entry means the file is not what the shard wrote, and the import refuses;
  · the entry's `tree` is KEPT as the runner wrote it, never rewritten: #242's guard (_wave_gate) then still owes this
    tree one clean run of each gate before its imported proofs are reused here;
  · a key this machine already serves is kept as it is (its tree, its age) - an import never displaces a local proof.
Refused means nothing is written. [[unknown-stays-unknown]] [[inherited-claim-is-not-evidence]]
"""
import hashlib
import json
import math
import os
import re

#: a chunk is no costlier than this fraction of one shard's fair share, so the largest gates spread across shards
CHUNKS_PER_SHARD = 4
#: the version of the manifest a shard writes beside its entries; the import refuses any other
MANIFEST_V = 1
#: seconds one tampered run costs beyond the gate's own run (sandbox, tamper, restore, the verdict). MEASURED on the
#: box, 2026-10-23: 24 proofs of sub-second laws took 64 s on one lane; priced at the gate's run alone, a shard of
#: cheap laws looked 5x lighter than it ran
PROOF_OVERHEAD_S = 1.5
_SPEC = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def parse_spec(spec):
    """'K/N' -> (k, n), 1 <= k <= n. Anything else raises ValueError (a shard nobody can read proves nothing)."""
    m = _SPEC.match(str(spec or ""))
    if not m:
        raise ValueError("a proof shard is K/N, e.g. 3/16 - got %r" % (spec,))
    k, n = int(m.group(1)), int(m.group(2))
    if not (1 <= k <= n):
        raise ValueError("a proof shard needs 1 <= K <= N - got %d/%d" % (k, n))
    return k, n


def _proof_key(pr):
    return json.dumps(pr, sort_keys=True, default=str)


def gate_costs(path=None):
    """{gate name: seconds per run} from gate_costs.json (run_gates' measured CI rows). -> dict ({} when unreadable)"""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_costs.json")
    try:
        with open(path, encoding="utf-8") as fh:
            c = json.load(fh).get("costs") or {}
        return dict((str(k), float(v)) for k, v in c.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v >= 0)
    except Exception:
        return {}


def plan(have, n, costs=None):
    """The shard every proof belongs to. -> {(gate, index): k} covering every proof of `have` exactly once (pure).

    have   [(name, filename, proofs)] as heart2.prove() holds them
    n      how many shards
    costs  {gate: seconds per run}; a gate it does not price costs the median of those it does (1.0 when none)"""
    n = int(n)
    if n < 1:
        raise ValueError("a plan needs at least one shard")
    costs = dict(costs or {})
    known = sorted(v for v in costs.values() if v > 0)
    default = known[len(known) // 2] if known else 1.0
    gates = []
    for name, _f, proofs in have:
        p = len(proofs or [])
        if p:
            c = costs.get(str(name))
            gates.append((str(name), p, c if (c is not None and c > 0) else default))
    oh = PROOF_OVERHEAD_S
    total = sum((c + oh) * p + c for _n, p, c in gates)        # every proof's run, and the gate's one clean run
    target = total / float(n * CHUNKS_PER_SHARD) if total > 0 else 1.0
    chunks = []
    for name, p, c in gates:
        k = max(1, min(p, int(math.ceil((c + oh) * p / target)) if target > 0 else 1))
        base, extra = divmod(p, k)
        start = 0
        for j in range(k):
            size = base + (1 if j < extra else 0)
            idx = list(range(start, start + size))
            start += size
            chunks.append(((c + oh) * size + c, name, idx))
    chunks.sort(key=lambda t: (-t[0], t[1], t[2][0]))
    load = [0.0] * n
    out = {}
    for cost, name, idx in chunks:
        k = min(range(n), key=lambda s: (load[s], s))
        load[k] += cost
        for i in idx:
            out[(name, i)] = k + 1
    return out


def plan_digest(have, n, assignment):
    """sha256 of every (gate, index, proof entry, shard) and N: shards from different plans never pass as one set."""
    rows = []
    for name, _f, proofs in have:
        for i, pr in enumerate(proofs or []):
            rows.append([str(name), i, _proof_key(pr), assignment.get((str(name), i))])
    rows.sort(key=lambda r: (r[0], r[1]))
    return hashlib.sha256(json.dumps({"n": int(n), "rows": rows}, sort_keys=True).encode("utf-8")).hexdigest()


def mine(assignment, k):
    """{gate: set(index)} - the proofs shard k proves."""
    out = {}
    for (name, i), s in assignment.items():
        if s == k:
            out.setdefault(name, set()).add(i)
    return out


def restrict_order(order, gates, own):
    """A push run's order cut down to one shard. -> (order, gates) with every gate that has no proof here dropped."""
    order2 = dict((g, [i for i in (order.get(g) or []) if i in own.get(g, ())]) for g in gates)
    gates2 = [g for g in gates if order2.get(g)]
    return dict((g, order2[g]) for g in gates2), gates2


def manifest(k, n, head, dirty, digest, own, names, stopped, at_ms):
    """What a shard writes beside its entries when it FINISHES (an unfinished shard writes none)."""
    return {"v": MANIFEST_V, "k": int(k), "n": int(n), "head": str(head or ""), "dirty": bool(dirty),
            "plan": str(digest), "finished": True, "names": sorted(names) if names else None,
            "stopped": list(stopped) if stopped else None, "at": int(at_ms),
            "assigned": sorted([g, i] for g, idx in own.items() for i in idx)}


def servable(e):
    """THE SAME PREDICATE heart2._VerdictCache.peek() asks: a dated, static, fact-free PROVEN. -> bool"""
    if not isinstance(e, dict):
        return False
    t = e.get("provedAt")
    if not (isinstance(t, (int, float)) and not isinstance(t, bool)):
        return False
    if e.get("kind", "static") != "static" or "facts" in e or "factsRef" in e:
        return False
    return e.get("verdict") == "PROVEN"


def check_shards(bodies, head):
    """Is this a complete, consistent set of finished shards of HEAD? -> (ok, why | None, [(k, entries, assigned)])

    bodies  [(label, body | None, why-unreadable | None)] - each shard file as read
    head    this checkout's HEAD sha"""
    shards, ns, plans, owner = {}, set(), set(), {}
    for label, body, why in bodies:
        if body is None:
            return False, "%s is unreadable (%s)" % (label, why), []
        m = body.get("shard") if isinstance(body, dict) else None
        if not isinstance(m, dict) or m.get("v") != MANIFEST_V:
            return False, "%s carries no shard manifest - it is not a finished shard's file" % label, []
        if m.get("finished") is not True:
            return False, "%s is a shard that never finished" % label, []
        if not head or m.get("head") != head:
            return False, "%s ran on %s, not this checkout's HEAD %s" % (label, str(m.get("head"))[:12],
                                                                      str(head)[:12] or "UNKNOWN"), []
        if m.get("dirty") is not False:
            return False, "%s ran on a tree whose tracked files differed from its HEAD" % label, []
        k, n = m.get("k"), m.get("n")
        if not all(isinstance(x, int) and not isinstance(x, bool) for x in (k, n)) or not 1 <= k <= n:
            return False, "%s names no readable shard number" % label, []
        if k in shards:
            return False, "shard %d/%d is given twice" % (k, n), []
        ns.add(n)
        plans.add(m.get("plan"))
        assigned = set()
        for row in m.get("assigned") or []:
            if isinstance(row, list) and len(row) == 2:
                assigned.add((str(row[0]), row[1]))
        ent = body.get("entries")
        if not isinstance(ent, dict):
            return False, "%s has no 'entries' map" % label, []
        for row in assigned:
            if row in owner:
                return False, "%s[%s] is assigned to shards %d and %d - one plan gives a proof one shard" % (
                    row[0], row[1], owner[row], k), []
            owner[row] = k
        shards[k] = (ent, assigned)
    if not shards:
        return False, "no shard was given", []
    if len(ns) != 1:
        return False, "the shards disagree on N (%s)" % ", ".join(str(x) for x in sorted(ns)), []
    n = ns.pop()
    if len(plans) != 1:
        return False, "the shards were cut from different plans (other names, bytes or N)", []
    missing = sorted(set(range(1, n + 1)) - set(shards))
    if missing:
        return False, "shard(s) %s of %d are missing - a partial set is never imported" % (
            ", ".join(str(x) for x in missing), n), []
    if set(shards) - set(range(1, n + 1)):
        return False, "a shard number lies outside 1..%d" % n, []
    return True, None, [(k, shards[k][0], shards[k][1]) for k in sorted(shards)]


def select(shards, keyer=None):
    """The entries an import may bank. -> (ok, why | None, {key: entry}, skipped count)

    An entry outside its shard's plan refuses the whole import; one that is not servable is skipped (counted).
    keyer   (gate, proof index) -> the key THIS checkout's bytes give that proof (None: unkeyable here). A servable entry
            filed under any other key refuses the import: the shard's key is a claim, this tree's key is the fact."""
    take, skipped = {}, 0
    for k, ent, assigned in shards:
        for key, e in ent.items():
            if not isinstance(e, dict):
                skipped += 1
                continue
            if (str(e.get("gate")), e.get("proof")) not in assigned:
                return False, "shard %d holds %s[%s], a proof its plan never gave it" % (
                    k, e.get("gate"), e.get("proof")), {}, 0
            if not servable(e):
                skipped += 1                # ELSEWHERE, BLIND, UNPROVABLE, undated, traced: never banked
                continue
            if keyer is not None and keyer(str(e.get("gate")), e.get("proof")) != key:
                return False, "shard %d files %s[%s] under a key this checkout's bytes do not give it" % (
                    k, e.get("gate"), e.get("proof")), {}, 0
            take[key] = e                   # KEPT as the shard wrote it - its tree above all
    return True, None, take, skipped


def merge_into(disk_entries, take):
    """This machine's entries plus the imported ones; a key this machine already SERVES is kept. -> (entries, added)"""
    out = dict((k, v) for k, v in (disk_entries or {}).items() if isinstance(v, dict))
    added = 0
    for key, e in take.items():
        if servable(out.get(key)):
            continue
        out[key] = e
        added += 1
    return out, added
