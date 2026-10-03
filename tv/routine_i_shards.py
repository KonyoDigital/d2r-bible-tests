# -*- coding: utf-8 -*-
"""Deal Routine I's fast Playwright specs by measured duration, not by file count.

--shard splits the file list into equal counts. On run 37139166700 that put 40.4 minutes of test
time on shard 6 and 24.9 on shard 2, so the slowest shard was the whole run. This deals largest-first
onto the lightest shard, the same way tv/shard_suite.py deals gate classes.

    python3 tv/routine_i_shards.py --shard 3 --of 6

prints that shard's paths, one per line, heaviest first. A file the table has not seen weighs the
median. An unreadable table still names every fast spec. An empty shard exits 2: Playwright with no
paths runs the whole project, which is the opposite of a shard.

The slow sims stay out. Their names are the chromium project's testIgnore in playwright.config.ts,
read from that file so a second copy cannot drift. Refresh the table from a run's blob zips:

    python3 tv/routine_i_shards.py --from-blobs <zip> [<zip> ...]
"""
import io
import json
import os
import re
import statistics
import sys
import zipfile

from console_safe import enable as _console_safe_enable
_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TABLE = os.path.join(HERE, "routine_i_costs.json")
CONFIG = os.path.join(REPO, "playwright.config.ts")

# Playwright's default testMatch, written out: name.spec.ts and the cjs/mjs/jsx/tsx cousins.
_SPEC = re.compile(r"(?:^|/)[^/]*\.(?:spec|test)\.(?:[cm])?[jt]sx?$")


def chromium_test_ignore(config_text):
    """The chromium project's testIgnore, compiled. None when the config does not say."""
    i = (config_text or "").find("name: 'chromium'")
    if i < 0:
        return None
    m = re.search(r"testIgnore:\s*/(.+)/", config_text[i:i + 4000])
    if not m:
        return None
    try:
        return re.compile(m.group(1))
    except re.error:
        return None


def fast_specs(repo=None):
    """Every fast spec path, repo-relative, sorted. None when the ignore regex cannot be read."""
    repo = repo or REPO
    try:
        with io.open(os.path.join(repo, "playwright.config.ts"), encoding="utf-8") as fh:
            ignore = chromium_test_ignore(fh.read())
    except OSError:
        return None
    if ignore is None:
        return None
    root = os.path.join(repo, "tests")
    out = []
    for dirpath, _dirs, names in os.walk(root):
        for name in names:
            rel = os.path.relpath(os.path.join(dirpath, name), repo).replace("\\", "/")
            if not _SPEC.search("/" + rel):
                continue
            if ignore.search(rel):
                continue
            out.append(rel)
    return sorted(out)


def load_costs(path=None):
    """-> {path: seconds}. {} when the table is absent. None when it exists and will not read."""
    p = path or TABLE
    try:
        with io.open(p, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print("routine_i_shards: %s exists but could not be read (%s) — every fast spec is still "
              "named, and the balance is unmeasured" % (os.path.basename(p), type(e).__name__),
              file=sys.stderr)
        return None
    costs = data.get("costs") if isinstance(data, dict) else None
    if not isinstance(costs, dict):
        print("routine_i_shards: %s has no costs object — balance is unmeasured" % os.path.basename(p),
              file=sys.stderr)
        return None
    return dict((k, float(v)) for k, v in costs.items())


def median_cost(names, costs):
    """The median measured cost of the files being dealt. 1.0 when nothing has been measured."""
    if not costs:
        return 1.0
    known = [float(costs[n]) for n in names if n in costs]
    if not known:
        known = [float(v) for v in costs.values()]
    if not known:
        return 1.0
    return float(statistics.median(known))


def file_weight(name, names, costs):
    """Seconds this file weighs. A file the table has not seen weighs the median, never zero."""
    med = median_cost(names, costs)
    if not costs or name not in costs:
        return float(med)
    v = float(costs[name])
    return v if v else 0.0


def deal(names, k, costs):
    """Largest-first onto the lightest shard. -> k lists (index 0 is shard 1). Empty lists stay,
    so shard K is always index K-1."""
    names = list(names)
    k = max(1, int(k))
    shards = [[] for _ in range(k)]
    load = [0.0] * k
    order = sorted(names, key=lambda n: (-file_weight(n, names, costs), n))
    for n in order:
        i = min(range(k), key=lambda j: (load[j], len(shards[j])))
        shards[i].append(n)
        load[i] += file_weight(n, names, costs)
    return shards


def costs_from_blob_zips(paths):
    """Sum every attempt's duration per spec, from Playwright blob report.jsonl files. -> {path: seconds}"""
    by_id = {}
    totals = {}

    def walk(node, file=None):
        loc = (node.get("location") or {}).get("file")
        if loc:
            file = loc
        if node.get("testId") and file:
            by_id[node["testId"]] = file
        for entry in node.get("entries") or []:
            walk(entry, file)
        for suite in node.get("suites") or []:
            walk(suite, file)

    for path in paths:
        by_id.clear()
        with zipfile.ZipFile(path) as zf:
            with zf.open("report.jsonl") as fh:
                for raw in fh:
                    if not raw.strip():
                        continue
                    event = json.loads(raw)
                    method = event.get("method")
                    if method == "onProject":
                        walk(event["params"]["project"])
                    elif method == "onTestEnd":
                        tid = event["params"]["test"]["testId"]
                        file = by_id.get(tid)
                        if not file:
                            continue
                        rel = file if file.startswith("tests/") else "tests/" + file.replace("\\", "/")
                        totals[rel] = totals.get(rel, 0.0) + float(event["params"]["result"]["duration"])
    return dict((k, round(v / 1000.0, 1)) for k, v in sorted(totals.items()))


def main(argv):
    if argv and argv[0] == "--from-blobs":
        if len(argv) < 2:
            print("usage: routine_i_shards.py --from-blobs <report.zip> [...]")
            return 2
        costs = costs_from_blob_zips(argv[1:])
        if not costs:
            print("no spec durations in %s — nothing written" % (argv[1:],))
            return 2
        rec = {
            "source": "Playwright blob reports, chromium project, sum of every attempt duration",
            "files": len(costs),
            "totalSeconds": round(sum(costs.values()), 1),
            "costs": costs,
        }
        tmp = TABLE + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        os.replace(tmp, TABLE)
        print("wrote %s — %d files, %.0f s" % (TABLE, len(costs), rec["totalSeconds"]))
        return 0
    shard = of = None
    i = 0
    while i < len(argv):
        if argv[i] == "--shard" and i + 1 < len(argv):
            shard = argv[i + 1]
            i += 2
        elif argv[i] == "--of" and i + 1 < len(argv):
            of = argv[i + 1]
            i += 2
        else:
            shard = None
            break
    if shard is None or of is None:
        print("usage: routine_i_shards.py --shard K --of N")
        return 2
    try:
        k = int(shard)
        n = int(of)
    except ValueError:
        print("shard and of must be integers")
        return 2
    if n < 1 or k < 1 or k > n:
        print("shard %s of %s is outside 1..N" % (shard, of))
        return 2
    specs = fast_specs()
    if specs is None:
        print("could not read the chromium testIgnore from playwright.config.ts — refusing to guess a file list")
        return 2
    costs = load_costs()
    chosen = deal(specs, n, costs)[k - 1]
    if not chosen:
        print("shard %s of %s dealt no files" % (shard, of))
        return 2
    for path in chosen:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
