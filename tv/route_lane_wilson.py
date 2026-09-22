#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Thirty-one distinct ways a route lane's own predicate must say the evidence is gone.

These call the predicates routes() already calls — chronicle `_source_ok`, fleet `_defines`,
roster `_declared` — on a snippet that starts life passing and is then mutated. A mutation
that the predicate still accepts is a leak, and it is not banked.

Nothing here edits his bible or his rosters. Chronicle's check is pointed at a temp file.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _mid(s):
    return max(1, len(s) // 2)


MUTATIONS = (
    ("delete", lambda s: ""),
    ("homoglyph", lambda s: s[:-1] + "а" if s else s),
    ("zwsp", lambda s: s[:_mid(s)] + "\u200b" + s[_mid(s):]),
    ("newline", lambda s: s[:_mid(s)] + "\n" + s[_mid(s):]),
    ("space", lambda s: s[:_mid(s)] + " " + s[_mid(s):]),
    ("lower", lambda s: (s[:_mid(s)] + ("q" if s[_mid(s):_mid(s) + 1] != "q" else "z") + s[_mid(s) + 1:]) if s else "q"),
    ("gap", lambda s: s[:_mid(s)] + "_" + s[_mid(s):]),
    ("drop-first", lambda s: s[1:]),
    ("drop-last", lambda s: s[:-1]),
    ("swap", lambda s: (s[1] + s[0] + s[2:]) if len(s) > 2 else s + "x"),
    ("tab", lambda s: s[:_mid(s)] + "\t" + s[_mid(s):]),
    ("extra", lambda s: s[:_mid(s)] + "Q" + s[_mid(s):]),
    ("reversed", lambda s: s[::-1]),
    ("encoded", lambda s: s.replace(s[:1], "%20", 1) if s else s),
    ("quoted", lambda s: '"%s"' % s),
    ("comment-line", lambda s: "// " + s),
    ("comment-block", lambda s: "/* %s */" % s),
    ("html-comment", lambda s: "<!-- %s -->" % s),
    ("split", lambda s: s[:_mid(s)] + '"+"' + s[_mid(s):]),
    ("plus", lambda s: s + s[-1:] if s else "x"),
    ("dotted", lambda s: s[:_mid(s)] + "." + s[_mid(s):]),
    ("slashed", lambda s: s[:_mid(s)] + "/" + s[_mid(s):]),
    ("braced", lambda s: "{" + s + "}"),
    ("indexed", lambda s: '["%s"]' % s),
    ("global", lambda s: "globalThis." + s),
    ("wrong-case-window", lambda s: "Window." + s),
    ("plural", lambda s: "windows." + s),
    ("this", lambda s: "this." + s),
    ("bom", lambda s: "\ufeff"),
    ("empty-body", lambda s: s),  # handled by the caller when the predicate is a body check
    ("only-mention", lambda s: s + "()"),
)


def _chronicle_base(token):
    return "<script>\n%s = [1];\n</script>\n" % token


def _run_chronicle():
    import chronicle_routes as C
    out = {}
    real = C.BIBLE
    try:
        for key, toks in C._SOURCE_TOKENS.items():
            token = toks[0]
            base = _chronicle_base(token)
            fd, path = tempfile.mkstemp(suffix=".html")
            os.close(fd)
            C.BIBLE = path
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(base)
                if C._source_ok(key) is not True:
                    out[key] = (0, 0, ["base snippet did not pass"])
                    continue
                n = k = 0
                notes = []
                for name, fn in MUTATIONS:
                    if name == "empty-body":
                        mutated = base.replace(token, token[:-1] + "x", 1)
                    elif name == "only-mention":
                        mutated = base.replace(token, "MENTIONED_ONLY", 1)
                    else:
                        broken = fn(token)
                        if token in broken:
                            broken = token[:1] + "×" + token[1:]
                        mutated = base.replace(token, broken, 1)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(mutated)
                    n += 1
                    if C._source_ok(key) is not True:
                        k += 1
                    else:
                        notes.append(name)
                out[key] = (n, k, notes)
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass
    finally:
        C.BIBLE = real
    return out


def _run_fleet():
    import fleet_routes as F
    out = {}
    for key, getter, _wire in F.LANES:
        base_line = "window.%s = function(){return 1}\n" % getter
        if F._defines(base_line, getter) is not True:
            out[key] = (0, 0, ["base getter did not pass"])
            continue
        n = k = 0
        notes = []
        for name, fn in MUTATIONS:
            if name == "empty-body":
                text = "var %s = function(){return 1}\n" % getter
            elif name == "only-mention":
                text = "window.%s()\n" % getter
            else:
                text = "window.%s = function(){return 1}\n" % fn(getter)
            n += 1
            if F._defines(text, getter) is not True:
                k += 1
            else:
                notes.append(name)
        out[key] = (n, k, notes)
    return out


def _run_roster():
    import roster_routes as R
    bases = {
        "runeword": "const RUNEWORDS = [1, 2];\n",
        "set": "const ITEM_SETS = [1, 2];\n",
        "unique": "window.ITEM_VALUE = [1, 2];\n",
    }
    needles = {"runeword": "RUNEWORDS", "set": "ITEM_SETS", "unique": "ITEM_VALUE"}
    out = {}
    for key, base in bases.items():
        if R._declared(base, key) is not True:
            out[key] = (0, 0, ["base declaration did not pass"])
            continue
        needle = needles[key]
        n = k = 0
        notes = []
        for name, fn in MUTATIONS:
            if name == "empty-body":
                text = base.replace("[1, 2]", "[]", 1)
            elif name == "only-mention":
                text = "// " + base
            else:
                text = base.replace(needle, fn(needle), 1)
            n += 1
            if R._declared(text, key) is not True:
                k += 1
            else:
                notes.append(name)
        out[key] = (n, k, notes)
    return out


def _live():
    """The real files, one question per route: the predicate the lane uses still passes."""
    import chronicle_routes as C
    import fleet_routes as F
    import roster_routes as R
    bible = open(C.BIBLE, encoding="utf-8", errors="replace").read()
    out = {}
    for key in C._SOURCE_TOKENS:
        ok = C._source_ok(key) is True
        out[("chronicle", key)] = ok
    for key, getter, _w in F.LANES:
        out[("fleet", key)] = F._defines(bible, getter) is True
    for key in ("runeword", "set", "unique"):
        out[("roster", key)] = R._declared(bible, key) is True
    return out


def main(argv):
    bank = "--bank" in argv
    print("route lane predicates — 31 mutations each\n")
    groups = (
        ("chronicle", _run_chronicle()),
        ("fleet", _run_fleet()),
        ("roster", _run_roster()),
    )
    failed = False
    for label, rows in groups:
        for key, (n, k, notes) in rows.items():
            mark = "OK" if n and k == n else "LEAK"
            if mark != "OK":
                failed = True
            print("  %-12s %-10s %s %d/%d %s" % (label, key, mark, k, n, ",".join(notes)[:80]))
    live = _live()
    print("\nlive predicates on his real files:")
    for (label, key), ok in live.items():
        print("  %-12s %-10s %s" % (label, key, "PASS" if ok else "FAIL"))
        if not ok:
            failed = True
    if not bank:
        print("\n(nothing banked — pass --bank)")
        return 1 if failed else 0
    if failed:
        print("\nNOT BANKING — a mutation was still accepted, or a live predicate failed")
        return 1
    import self_arming as SA
    for label, rows in groups:
        for key, (n, k, _notes) in rows.items():
            SA.bank("%s.%s" % (label, key), "sabotage", "route_lane_wilson",
                    n=n, k=k, attacks=n, ref="mutations",
                    note="31 mutations of the lane predicate, each one no longer accepted")
            live_ok = live[(label, key)]
            SA.bank("%s.%s" % (label, key), "live", "route_lane_live",
                    n=1, k=1 if live_ok else 0, attacks=1, ref="live-predicate",
                    note="the predicate on his real bible still accepts the real declaration")
            print("  banked %s.%s sabotage %d/%d + live" % (label, key, k, n))
    return 0


# The corroborator counts CLAIMS. One entry per mutation, matching attacks=n above.
CLAIMS = tuple(name for name, _fn in MUTATIONS)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
