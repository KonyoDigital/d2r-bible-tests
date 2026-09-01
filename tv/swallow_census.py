"""WHICH SWALLOWED EXCEPTIONS CAN PUT A CALM NUMBER ON HIS SCREEN.

Konyo, 2026-09-01, on a rule that had called a large finding "noise": "thats not logical.. it
makes a small problem bigger though... and the 238... fix them??" Then: "focus on the 537 here".

He is right that "too many to act on" is not a reason to stop looking. But 537 is also not a
to-do list — most of them are correct. `try: tab.close() except: pass` SHOULD swallow; a teardown
that takes a run down is a worse bug than the one it reports.

So this file exists to turn one big number into a ranked one, repeatably, and to keep the
unscoped total on the record beside the ranked subset. It is a MEASUREMENT, not a linter: it
prints, it never edits, and it has no opinion about any single site.

THE RANKING QUESTION, and it is the only one that matters:

    does this swallow let a number HE ACTS ON keep a calm face?

The shape behind most of this session's scars is a failed read that silently yields {} or 0, so a
screen prints a tidy figure that actually means "nobody could ask". That is worse than a crash,
because a crash gets fixed. [[unknown-stays-unknown]]

    RANK 1  the except body RETURNS or ASSIGNS a falsy default ({} , 0, [], "", None, False)
            after a read/parse/fetch. This is the class. The caller cannot tell the difference
            between "measured zero" and "could not ask".
    RANK 2  a read/parse/fetch is swallowed with a bare `pass`, and the surrounding function has
            a fallible return path. Suspicious; needs a human to say which.
    RANK 3  something else fallible is swallowed. Look eventually.
    OK      the try block only tears something down, or the except body re-raises, logs, or sets
            an explicit UNKNOWN marker.

⚠ THIS TOOL CANNOT TELL YOU A SITE IS WRONG. A rank is a place in a queue, not a verdict — every
fix still needs someone to read the site and decide. Reporting a rank as a defect would make this
the very thing it was written to stop: a confident number nobody measured.
"""

import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# Things whose failure means a FACT was not obtained.
READS = ("open", "load", "loads", "read", "get", "post", "urlopen", "request", "fetch",
         "json", "loadtxt", "execute", "fetchone", "fetchall", "check_output", "run",
         "communicate", "listdir", "glob", "stat", "getmtime", "getsize", "exists")
# Things whose failure means a cleanup did not happen — swallowing is correct.
TEARDOWNS = ("close", "quit", "kill", "terminate", "unlink", "remove", "rmtree", "shutdown",
             "join", "cleanup", "destroy", "release", "disconnect", "stop")

FALSY = ("{}", "[]", "0", "0.0", "''", '""', "None", "False", "()")


def _calls(node):
    """Every dotted call name inside a node, lowercased."""
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                out.append(f.attr.lower())
            elif isinstance(f, ast.Name):
                out.append(f.id.lower())
    return out


def _is_falsy_const(node):
    if isinstance(node, ast.Constant):
        return not node.value or node.value == 0
    if isinstance(node, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
        return not (getattr(node, "keys", None) or getattr(node, "elts", None))
    return False


def _hands_back(handler):
    """EXACTLY what the except body hands back, because the difference decides everything.

    ⚠ THE FIRST CUT OF THIS TOOL GOT THIS WRONG AND WOULD HAVE PRODUCED A 262-ITEM QUEUE THAT WAS
    MOSTLY FINE. It treated every falsy default as the lying shape. But `return None` is usually
    the HONEST answer — None IS "I could not tell", and a caller that checks `is None` gets the
    truth. Measured over this tree: of 262 sites, 168 hand back None or False and 94 hand back
    something that reads as DATA. Only the 94 are the class where "could not ask" wears the
    costume of "measured zero". Ranking them together would have buried the real ones under
    correct code — the exact way a real finding gets ignored. [[unknown-stays-unknown]]
    """
    for st in handler.body:
        v = st.value if isinstance(st, (ast.Return, ast.Assign)) else None
        if isinstance(st, ast.Return) and v is None:
            return "None"
        if v is None:
            continue
        if isinstance(v, ast.Constant):
            if v.value is None:  return "None"
            if v.value is False: return "False"
            if v.value == 0:     return "ZERO"
            if v.value == "":    return "EMPTY-STR"
        if isinstance(v, ast.Dict) and not v.keys:            return "EMPTY-DICT"
        if isinstance(v, (ast.List, ast.Set)) and not v.elts: return "EMPTY-LIST"
        if isinstance(v, ast.Tuple) and v.elts and all(_is_falsy_const(e) for e in v.elts):
            return "EMPTY-TUPLE"
    return "other"


# The shapes that a caller cannot distinguish from a real measurement.
LIES_AS_DATA = ("ZERO", "EMPTY-DICT", "EMPTY-LIST", "EMPTY-STR", "EMPTY-TUPLE")


def _body_shape(handler):
    """What the except body DOES. -> ('pass'|'return-falsy'|'assign-falsy'|'speaks'|'other')"""
    body = handler.body
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return "pass"
    for st in body:
        if isinstance(st, ast.Raise):
            return "speaks"
        # a print / log / a call carrying the word warn|error|unknown counts as speaking up
        for c in _calls(st):
            if c in ("print", "warning", "warn", "error", "exception", "critical", "log"):
                return "speaks"
    for st in body:
        if isinstance(st, ast.Return) and st.value is not None and _is_falsy_const(st.value):
            return "return-falsy"
        if isinstance(st, ast.Return) and st.value is None:
            return "return-falsy"
        if isinstance(st, ast.Assign) and _is_falsy_const(st.value):
            return "assign-falsy"
        if isinstance(st, ast.Assign) and isinstance(st.value, ast.Tuple) \
                and all(_is_falsy_const(e) for e in st.value.elts):
            return "assign-falsy"
    return "other"


def _rank(try_node, handler):
    calls = _calls(ast.Module(body=list(try_node.body), type_ignores=[]))
    reads = [c for c in calls if c in READS]
    tears = [c for c in calls if c in TEARDOWNS]
    shape = _body_shape(handler)

    if shape == "speaks":
        return 0, "the except body reports it"
    if tears and not reads:
        return 0, "teardown only — swallowing is correct here"
    if reads and shape in ("return-falsy", "assign-falsy"):
        hb = _hands_back(handler)
        if hb in LIES_AS_DATA:
            return 1, "a failed %s becomes %s — 'could not ask' is indistinguishable from a real " \
                      "measurement" % (reads[0], hb)
        # None/False after a failed read is the honest unknown. Still worth an eye — a CALLER that
        # does `x or 0` re-creates the lie one frame up — but it is not the same defect.
        return 2, "a failed %s returns %s (honest unknown; check the CALLER does not coerce it)" \
                  % (reads[0], hb)
    if reads and shape == "pass":
        return 2, "a failed %s is swallowed silently" % reads[0]
    if reads:
        return 2, "a failed %s is swallowed" % reads[0]
    return 3, "something fallible is swallowed"


def scan(root=None):
    root = root or REPO
    rows, unreadable = [], []
    state = {"skippedDirs": []}
    for dp, dns, fns in os.walk(root):
        # ⚠ `backups/` IS A RESTORE SNAPSHOT, NOT SHIPPING CODE — a frozen copy of tv/ from
        # 2026-07-16. Counting it would put four sites at the top of the queue that no running
        # process can reach. It is SKIPPED AND COUNTED, never silently dropped: a census that
        # quietly narrows its own scope is the thing this file exists to stop. [[no-silent-caps]]
        skipped = [d for d in dns if d in ("backups",)]
        for d in skipped:
            state["skippedDirs"].append(os.path.relpath(os.path.join(dp, d), root))
        dns[:] = [d for d in dns if d not in (".git", "node_modules", "__pycache__",
                                              ".render_shots", "frames", "backups")]
        for fn in sorted(fns):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dp, fn)
            try:
                src = io.open(p, encoding="utf-8").read()
                tree = ast.parse(src)
            except Exception as e:
                # ⚠ A FILE THIS TOOL COULD NOT PARSE IS NOT A FILE WITH NO SWALLOWS. Naming it is
                # the whole difference between a census and a comforting number.
                unreadable.append((os.path.relpath(p, root), str(e)[:60]))
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Try):
                    continue
                for h in node.handlers:
                    r, why = _rank(node, h)
                    rows.append({
                        "file": os.path.relpath(p, root),
                        "line": h.lineno,
                        "rank": r,
                        "why": why,
                        "shape": _body_shape(h),
                    })
    return {"rows": rows, "unreadable": unreadable, "root": root,
            "skippedDirs": sorted(set(state["skippedDirs"]))}


def main(argv=None):
    try:
        import console_safe
        console_safe.enable()
    except Exception:
        pass
    argv = list(argv or [])
    out = scan()
    rows = out["rows"]
    by = {}
    for r in rows:
        by.setdefault(r["rank"], []).append(r)

    print("\nSWALLOWED EXCEPTIONS in %s" % out["root"])
    print("  %d handlers examined across the tree" % len(rows))
    if out.get("skippedDirs"):
        print("  (skipped, and not represented above: %s — a restore snapshot, not shipping code)"
              % ", ".join(out["skippedDirs"]))
    if out["unreadable"]:
        # never let an unparsed file read as a clean one
        print("  ⚠ %d file(s) COULD NOT BE PARSED and are not represented below:"
              % len(out["unreadable"]))
        for f, e in out["unreadable"][:5]:
            print("       %s — %s" % (f, e))
    print()
    LABEL = {1: "RANK 1  a failed read becomes DATA (0 / {} / [] / '')  ← the class that lies",
             2: "RANK 2  a failed read is swallowed silently",
             3: "RANK 3  something else fallible is swallowed",
             0: "OK      teardown, or the body speaks up"}
    for r in (1, 2, 3, 0):
        print("  %-64s %4d" % (LABEL[r], len(by.get(r) or [])))

    top = sorted(by.get(1) or [], key=lambda r: (r["file"], r["line"]))
    if top:
        n = 25 if "--all" not in argv else len(top)
        print("\n  RANK 1 sites%s:" % ("" if n >= len(top) else " (first %d of %d — --all for the rest)"
                                       % (n, len(top))))
        for r in top[:n]:
            print("     %-38s :%-6d %s" % (r["file"], r["line"], r["why"]))
        if n < len(top):
            # no silent caps: say what was dropped
            print("     … %d more not printed" % (len(top) - n))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
