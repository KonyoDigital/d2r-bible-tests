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
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe_enable   # it prints non-ASCII; a cp1255 console must not crash
    _console_safe_enable()
except ImportError:                 # second eye: only a missing module is tolerated - a broken one is not hidden
    pass

#: a chunk is no costlier than this fraction of one shard's fair share, so the largest gates spread across shards
CHUNKS_PER_SHARD = 4
#: the version of the manifest a shard writes beside its entries; the import refuses any other
MANIFEST_V = 1
#: seconds one tampered run costs beyond the gate's own run (sandbox, tamper, restore, the verdict). MEASURED on the
#: box, 2026-10-23: 24 proofs of sub-second laws took 64 s on one lane; priced at the gate's run alone, a shard of
#: cheap laws looked 5x lighter than it ran
PROOF_OVERHEAD_S = 1.5
#: REG-2593 - what a proof costs ON A RUNNER, over what gate_costs + PROOF_OVERHEAD_S says. MEASURED on the 16-shard run
#: at dcff7160 (421 gates priced from their own provedAt gaps): median 0.42 (p10 0.11, p90 0.91) - a gate this file has
#: no measured row for is priced at that ratio, not at a desk guess
PROOF_COST_FACTOR = 0.42
#: REG-2593 - the lanes one runner proves on (2 cores). A shard's wall is the larger of its work over its lanes and its
#: BROWSER work, which runs one gate at a time (#42 ONE BROWSER AT A TIME) - the old plan balanced only the first, and
#: its slowest shard ran 2.1x the mean
RUNNER_LANES = 2
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


def proof_costs(path=None):
    """REG-2593 - {gate: seconds per proof ON A RUNNER} from proof_costs.json (measure_costs' rows). -> dict ({} when
    unreadable: the plan then prices every gate from gate_costs, as it did)"""
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "proof_costs.json")
    try:
        with open(path, encoding="utf-8") as fh:
            c = json.load(fh).get("perProof") or {}
        return dict((str(k), float(v)) for k, v in c.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0)
    except Exception:
        return {}


def measure_costs(bodies):
    """REG-2593 - seconds per proof per gate, MEASURED from finished shard caches: within one shard a gate's proofs run
    back to back on one lane, so the gap between consecutive provedAt stamps is one proof's cost (its clean run is shared).
    Median over every gap of every shard. A gate with no gap (one proof per shard) is left out - priced by the factor.
    bodies: [cache body]. -> {gate: seconds}"""
    gaps = {}
    for body in bodies:
        per = {}
        for e in ((body or {}).get("entries") or {}).values():
            t = e.get("provedAt") if isinstance(e, dict) else None
            if isinstance(t, (int, float)) and not isinstance(t, bool) and e.get("gate"):
                per.setdefault(str(e["gate"]), []).append(t)
        for g, ts in per.items():
            ts.sort()
            gaps.setdefault(g, []).extend((b - a) / 1000.0 for a, b in zip(ts, ts[1:]))
    out = {}
    for g, v in gaps.items():
        if v:
            v = sorted(v)
            m = len(v) // 2
            out[g] = round(v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2.0, 3)
    return out


def plan(have, n, costs=None, browser=None, per_proof=None, lanes=RUNNER_LANES):
    """The shard every proof belongs to. -> {(gate, index): k} covering every proof of `have` exactly once (pure).

    have       [(name, filename, proofs)] as heart2.prove() holds them
    n          how many shards
    costs      {gate: seconds per run}; a gate it does not price costs the median of those it does (1.0 when none)
    browser    REG-2593: the gates proved one at a time (they start a browser). None: the pre-REG-2593 plan exactly
    per_proof  REG-2593: {gate: MEASURED seconds per proof on a runner}; a gate it lacks costs PROOF_COST_FACTOR x
               (its run + PROOF_OVERHEAD_S). A chunk of `size` proofs then costs per_proof x (size + 2): the proofs and
               the gate's two clean runs (the wave's and the closing one)
    lanes      a runner's lanes: a shard's wall is max(its work / lanes, its browser work)"""
    n = int(n)
    if n < 1:
        raise ValueError("a plan needs at least one shard")
    costs = dict(costs or {})
    known = sorted(v for v in costs.values() if v > 0)
    default = known[len(known) // 2] if known else 1.0
    oh = PROOF_OVERHEAD_S
    pp = dict(per_proof or {})
    gates = []
    for name, _f, proofs in sorted(have, key=lambda t: str(t[0])):     # one order, whatever order the names came in
        p = len(proofs or [])
        if p:
            c = costs.get(str(name))
            c = c if (c is not None and c > 0) else default
            if per_proof is None:
                unit, fixed = c + oh, c                                 # every proof's run, and the gate's clean run
            else:
                u = pp.get(str(name))
                unit = u if u is not None else PROOF_COST_FACTOR * (c + oh)
                fixed = 2 * unit
            gates.append((str(name), p, unit, fixed, browser is not None and str(name) in browser))
    total = sum(u * p + f for _n, p, u, f, _b in gates)
    target = total / float(n * CHUNKS_PER_SHARD) if total > 0 else 1.0
    # REG-2593, MODELLED on the measured costs: cutting browser gates finer made N=16 SLOWER (max 1675s vs 1349s): each
    # chunk pays its gate's two clean runs again. One target for every gate; the wall-aware placement below spreads them
    chunks = []
    for name, p, u, f, b in gates:
        k = max(1, min(p, int(math.ceil(u * p / target)) if target > 0 else 1))
        base, extra = divmod(p, k)
        start = 0
        for j in range(k):
            size = base + (1 if j < extra else 0)
            idx = list(range(start, start + size))
            start += size
            chunks.append((u * size + f, b, name, idx))
    chunks.sort(key=lambda t: (-t[0], t[2], t[3][0]))
    tot = [0.0] * n
    brw = [0.0] * n
    lanes = max(1, int(lanes))
    out = {}
    for cost, b, name, idx in chunks:
        if browser is None:
            k = min(range(n), key=lambda s: (tot[s], s))
        else:   # REG-2593: the shard whose WALL grows least - its work over its lanes, or its browser queue
            k = min(range(n), key=lambda s: (max((tot[s] + cost) / lanes, brw[s] + (cost if b else 0.0)), tot[s], s))
        tot[k] += cost
        if b:
            brw[k] += cost
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


def manifest(k, n, head, dirty, digest, own, names, stopped, at_ms, owed=None):
    """What a shard writes beside its entries when it FINISHES (an unfinished shard writes none). `owed` (REG-2591): every
    failure a shard that KEPT GOING found, [gate, index, verdict, reason] each."""
    return {"v": MANIFEST_V, "k": int(k), "n": int(n), "head": str(head or ""), "dirty": bool(dirty),
            "plan": str(digest), "finished": True, "names": sorted(names) if names else None,
            "stopped": list(stopped) if stopped else None, "at": int(at_ms),
            "owed": [list(f) for f in (owed or [])],
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


def unbanked(shards, take):
    """REG-2586 - per shard, how many of its ASSIGNED proofs the import banks none for. -> {k: (unbanked, assigned)}

    A shard that stopped on a failure never ran what came after it; an assigned proof with no servable entry (never run,
    ELSEWHERE, BLIND...) is a proof the next push still pays for here."""
    out = {}
    for k, ent, assigned in shards:
        got = set((str(e.get("gate")), e.get("proof")) for key, e in (ent or {}).items()
                  if take.get(key) is e)
        out[k] = (len(set(assigned) - got), len(assigned))
    return out


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


STORE_NAME = ".heart2_cache.json"          # the basename heart2's store writer accepts (heart2._StoreFile)


def fan_in(root, n, head, say=print):
    """REG-2588 — CI's fan-in: are the N shard artifacts under `root` (one dir per artifact, each holding the shard's
    STORE_NAME) one complete, importable set of HEAD? The SAME rules the import applies (check_shards, select), so a set
    the fan-in passes is a set `heart2 --import-shards` takes, and one it refuses is refused here first, on CI, where the
    log names the shard. -> exit code: 0 a whole set, 2 refused"""
    bodies, empty = [], []
    for d in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        path = os.path.join(root, d, STORE_NAME)
        if not os.path.isfile(path):
            empty.append(d)
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                body = json.load(fh)
            bodies.append((d, body if isinstance(body, dict) else None, None if isinstance(body, dict) else "not a map"))
        except (OSError, ValueError) as e:
            bodies.append((d, None, "%s: %s" % (type(e).__name__, str(e)[:80])))
    for d in empty:
        say("  ⚠ %s carries no %s - that shard banked nothing it could hand on" % (d, STORE_NAME))
    ok, why, shards = check_shards(bodies, head)
    if ok and empty:                                     # second eye: a dir with no store is not a shard of the set
        ok, why = False, "%d artifact dir(s) carry no %s (%s)" % (len(empty), STORE_NAME, ", ".join(empty[:4]))
    if ok:
        got = set(b["shard"].get("n") for _l, b, _w in bodies)
        if got != {n} or len(shards) != n:
            ok, why = False, "the workflow runs %d shards but the files name N=%s (%d given)" % (
                n, ",".join(str(x) for x in sorted(got, key=str)), len(shards))
    if ok:
        ok, why, take, skipped = select(shards)
    if not ok:
        say("  ✗ REG-2588 FAN-IN REFUSED: %s. This set would be refused by `heart2 --import-shards` too." % why)
        return 2
    owed = unbanked(shards, take)
    stops = dict((b["shard"]["k"], b["shard"].get("stopped")) for _l, b, _w in bodies if b["shard"].get("stopped"))
    fails = dict((b["shard"]["k"], b["shard"].get("owed")) for _l, b, _w in bodies if b["shard"].get("owed"))
    for k, _ent, assigned in shards:
        st = stops.get(k)
        say("    shard %2d/%d: %4d assigned, %4d banked%s%s" % (
            k, n, len(assigned), len(assigned) - owed[k][0],
            (", STOPPED at %s" % ("%s[%s] %s" % tuple(st[:3]) if isinstance(st, list) and len(st) >= 3 else st))
            if st else "",
            (", OWES %s" % ", ".join("%s[%s] %s" % tuple(f[:3]) for f in fails[k] if isinstance(f, list) and len(f) >= 3))
            if fails.get(k) else ""))
    _n_owed = sum(len(v) for v in fails.values())
    _n_unb = sum(u for u, _a in owed.values())
    say("  ✓ REG-2588 FAN-IN: all %d shards of %s finished on one plan; %d PROVEN entr(ies) to import, %d not servable%s%s."
        % (n, str(head)[:12], len(take), skipped,
           (" - %d shard(s) STOPPED on a failure, owed a fix" % len(stops)) if stops else "",
           (" - REG-2591: %d failure(s) OWED a fix in %d shard(s)" % (_n_owed, len(fails))) if fails else ""))
    # REG-2594 - said out loud, never left to a reader to add up: what this set does NOT bank. Which of those the Mac
    # proves itself (ELSEWHERE here) only the Mac driver knows; it reports FULL or PARTIAL after its import
    say("  REG-2594: %d of %d assigned proof(s) bank nothing from this set (ELSEWHERE on a runner, owed, or never run)"
        % (_n_unb, sum(a for _u, a in owed.values())))
    return 0


def main(argv=None):
    import argparse
    import subprocess
    ap = argparse.ArgumentParser(description="REG-2588 - the CI fan-in check over N proof-shard artifacts")
    ap.add_argument("--fan-in", dest="root", default=None, help="dir holding one sub-dir per shard artifact")
    ap.add_argument("--shards", type=int, default=None, help="N, the workflow's shard count")
    ap.add_argument("--head", default=None, help="the sha the shards must have run on (default: git rev-parse HEAD)")
    ap.add_argument("--measure-costs", dest="measure", default=None,
                    help="REG-2593: dir of finished shard artifacts -> write proof_costs.json (seconds per proof)")
    a = ap.parse_args(argv)
    if a.measure:
        bodies = []
        for d in sorted(os.listdir(a.measure)):
            f = os.path.join(a.measure, d, STORE_NAME)
            if os.path.isfile(f):
                with open(f, encoding="utf-8") as fh:
                    bodies.append(json.load(fh))
        got = measure_costs(bodies)
        if not got:                     # second eye: an empty or wrong dir never blanks the table the plan reads
            print("  ✗ REG-2593: no shard cache under that dir priced any gate - proof_costs.json is left as it was")
            return 2
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proof_costs.json")
        heads = sorted(set(str(((b or {}).get("shard") or {}).get("head") or "")[:12] for b in bodies))
        with open(out + ".tmp", "w", encoding="utf-8") as fh:
            json.dump({"v": 1, "measuredOn": "a GitHub runner, %d shard(s) at %s" % (len(bodies), ",".join(heads)),
                       "perProof": dict(sorted(got.items()))}, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(out + ".tmp", out)
        print("  REG-2593: %d gate(s) priced from %d shard cache(s) -> tv/proof_costs.json" % (len(got), len(bodies)))
        return 0
    if not a.root or a.shards is None:
        ap.error("--fan-in DIR and --shards N are required (or --measure-costs DIR)")
    head = a.head
    if head is None:
        p = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        head = p.stdout.strip() if p.returncode == 0 else ""
    return fan_in(a.root, a.shards, head)


if __name__ == "__main__":
    raise SystemExit(main())
