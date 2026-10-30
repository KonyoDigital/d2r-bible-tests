# -*- coding: utf-8 -*-
"""v3847 FAST GATE - the gate set a push runs: the CORE set + every gate whose law reads a changed file.

Elad 2026-10-30 15:29: changed-file gates + a core set; a change to a SHARED file (bible.html,
control_ui.html, control_app.py, the gate machinery itself) runs EVERY gate; a nightly full run; never
skip the hook. CI still runs the whole set sharded on every push - the fast set decides the local push,
it never decides the release alone.

Selection is static and over-inclusive on purpose: a gate is picked when its law file changed, or when
its law names a changed file by basename or module stem (an import is a name). The import closure is NOT followed:
735 laws import control_app.py, which imports most of tv/, so it would pick ~650 gates for any tv/ change.
"""
import functools, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SHARED = ("bible.html", "control_ui.html", "tv/control_app.py", "tv/run_gates.py", "tv/fast_gates.py",
          "tv/gate_ledger.py", "hooks/pre-push", "tv/fast_core.txt")
CORE_FILE = os.path.join(HERE, "fast_core.txt")


def core():
    with open(CORE_FILE) as f:
        return [l.split("#")[0].strip() for l in f if l.split("#")[0].strip()]


def changed(base="origin/main"):
    out = subprocess.run(["git", "diff", "--name-only", "%s...HEAD" % base], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l.strip()]


def _imports(path, cache={}):
    if path in cache:
        return cache[path]
    cache[path] = set()
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return cache[path]
    mods = set(re.findall(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", src, re.M))
    for m in mods:
        p = os.path.join(HERE, m + ".py")
        if os.path.exists(p):
            cache[path] |= {p} | _imports(p)
    return cache[path]


@functools.lru_cache(maxsize=None)
def _text(path):
    try:
        return open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return ""


def _outside_registry(src):
    """run_gates.py with the GATES = [ ... ] list cut out, and the gate names that list holds."""
    a = src.find("\nGATES = [\n"); b = src.find("\n]\n", a)
    if a < 0 or b < 0:
        return src, set()
    return src[:a] + src[b:], set(re.findall(r'^    Gate\("([^"]+)"', src[a:b], re.M))


def registry_change(old, new):
    """-> the gate names whose registry entry was ADDED or EDITED, when nothing outside GATES = [ ... ] moved and no
    entry vanished; None otherwise (then every gate runs)."""
    (o_rest, o_names), (n_rest, n_names) = _outside_registry(old), _outside_registry(new)
    if not old or not o_names or o_rest != n_rest or not o_names <= n_names:
        return None

    def entries(src):
        return {m.group(2): m.group(1) for m in
                re.finditer(r'^(    Gate\("([^"]+)".*?)(?=^    Gate\(|^\]$)', src, re.M | re.S)}
    oe, ne = entries(old), entries(new)
    return {n for n in ne if oe.get(n) != ne[n]}


def registry_only(base="origin/main"):
    old = subprocess.run(["git", "show", "%s:tv/run_gates.py" % base], cwd=REPO, capture_output=True, text=True).stdout
    return registry_change(old, _text(os.path.join(HERE, "run_gates.py")))


def select(gates, files, base="origin/main"):
    """-> (names | None for FULL, reason). None means every gate runs."""
    added = set()
    if "tv/run_gates.py" in files:
        added = registry_only(base)
        if added is None:
            return None, "tv/run_gates.py changed outside the gate registry - every gate runs"
        files = [f for f in files if f != "tv/run_gates.py"]
    hit = [f for f in files if f in SHARED]
    if hit:
        return None, "shared file(s) changed: %s - every gate runs" % ", ".join(hit)
    known = {g.name for g in gates}
    pick = [n for n in core() if n in known] + sorted(added - set(core()))
    keys = set()
    for f in files:
        b = os.path.basename(f); keys.add(b)
        stem = os.path.splitext(b)[0]
        if len(stem) >= 5:
            keys.add(stem)
    absch = {os.path.join(REPO, f) for f in files}
    rx = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(k) for k in sorted(keys))) if keys else None
    seen = {}

    def names_one(p):
        if p not in seen:
            seen[p] = bool(rx and rx.search(_text(p)))
        return seen[p]
    for g in gates:
        law = next((str(a) for a in g.argv if str(a).endswith(".py") and "/tv/" in str(a)), None)
        if not law:
            if g.name not in pick:
                pick.append(g.name)   # a gate with no law file cannot be mapped: run it
            continue
        # the law itself: its own file, or its own text naming the changed file / module stem (which covers its
        # direct imports). NOT the import closure: 735 laws import control_app.py, which imports most of tv/, so
        # the closure picks ~650 gates for any tv/ change. The whole set still runs in CI and nightly.
        if law in absch or names_one(law):
            if g.name not in pick:
                pick.append(g.name)
    return pick, "%d core + changed-file gates for %d changed file(s)" % (len(core()), len(files))


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    import run_gates
    b = (sys.argv[1:2] or ["origin/main"])[0]
    names, why = select(run_gates.GATES, changed(b), b)
    print(why)
    print("FULL" if names is None else "\n".join(names))
