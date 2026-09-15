# -*- coding: utf-8 -*-
"""Find BUILT-BUT-UNJOINED ends: functions that compute a verdict nobody consumes."""
import ast, io, os, re, collections

HERE = "tv"
SKIP_PREFIX = ("test_",)
py = [f for f in sorted(os.listdir(HERE))
      if f.endswith(".py") and not f.startswith(SKIP_PREFIX)]

defs = {}      # name -> (file, lineno, doc first line)
for f in py:
    try:
        src = io.open(os.path.join(HERE, f), encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:
        continue
    for n in tree.body:                      # module-level defs only
        if isinstance(n, ast.FunctionDef) and not n.name.startswith("__"):
            doc = (ast.get_docstring(n) or "").strip().split("\n")[0][:80]
            defs.setdefault(n.name, []).append((f, n.lineno, doc))

# count call sites across ALL non-test source
calls = collections.Counter()
for f in py:
    try:
        src = io.open(os.path.join(HERE, f), encoding="utf-8").read()
        tree = ast.parse(src)
    except Exception:
        continue
    for n in ast.walk(tree):
        # ⚠ REFERENCES, NOT JUST CALLS. console_doctor registers every _check_* in a CHECKS
        # table as a VALUE; counting only ast.Call flagged all 30 of them as orphans. A registry
        # entry IS a join. [[feedback-suspect-the-instrument]]
        if isinstance(n, ast.Call):
            fn = n.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
            if nm: calls[nm] += 1
        elif isinstance(n, ast.Name):
            calls[n.id] += 1
        elif isinstance(n, ast.Attribute):
            calls[n.attr] += 1

# a def whose only "call" is its own definition site is unconsumed
orphan = []
for name, places in defs.items():
    if calls[name] <= 0 and len(places) == 1:
        f, ln, doc = places[0]
        orphan.append((f, ln, name, doc))

# rank: the interesting ones sound like verdicts / readers / joins
KEY = ("verdict","report","state","check","audit","why","reason","decide","judge",
       "rank","route","owed","witness","confluence","receipt","trace","bank","gate")
hot = [o for o in orphan if any(k in o[2].lower() or k in (o[3] or "").lower() for k in KEY)]

print("  module-level defs scanned : %d" % len(defs))
print("  never called anywhere     : %d" % len(orphan))
print("  ...of those, verdict-shaped: %d\n" % len(hot))
for f, ln, name, doc in sorted(hot)[:26]:
    print("  %-26s %s:%-5d %s" % (name[:26], f, ln, (doc or "")[:62]))

