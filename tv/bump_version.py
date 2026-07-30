#!/usr/bin/env python3
"""v1489 — stamp a new version across the four surfaces that carry one.

Usage: python bump_version.py <ver> <short name> <note...>

The version lives in four places: the board's `D2R_BUILD`, `control_app.py`'s `/api/status`,
`tv_diablo.py`'s `VERSION`, and `tv/WINDOWS_SHIP.json`. Bumping them by hand is four chances to
miss one, and a half-bumped tree is not cosmetic — `test_button_matrix` compares the LIVE app's
version to the ship manifest, so a missed stamp surfaces as "the running app is a different build
than the tree you are testing" and sends the next person hunting a phantom.

The board note is a SINGLE-QUOTED JS literal. Writing one by hand during v1478 put an apostrophe in
"someone else's chronicle", which terminated the string early and threw a SyntaxError that blanks
the entire 37k-line page. The syntax gate caught it — but the right place to stop that class is
before it is written, so this refuses an apostrophe outright rather than relying on the gate to
notice afterwards.

Each stamp is verified after writing: a silent no-op replace would leave the tree half-bumped,
which is the exact failure this tool exists to prevent.
"""
import io, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# v1489 — this tool prints, so it must survive the operator's console (REG-044/054/077/078).
# Caught by TestToolsCanReportTheirVerdict on its first run, which is the gate doing its job.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass


def bump(ver, name, note):
    if "'" in note or "'" in name:
        raise SystemExit("apostrophe in note/name would break the single-quoted D2R_BUILD literal")

    p = os.path.join(REPO, "bible.html")
    s = io.open(p, encoding="utf-8").read()
    a = s.index("  window.D2R_BUILD = { id:'")
    b = s.index("\n", a)
    cur = re.search(r"id:'(v\d+)'", s[a:b]).group(1)
    new = ("  window.D2R_BUILD = { id:'%s', name:'%s - %s', date:'2026-07-31', note:'%s' };"
           % (ver, ver, name, note))
    io.open(p, "w", encoding="utf-8", newline="").write(s[:a] + new + s[b:])

    p = os.path.join(REPO, "tv", "control_app.py")
    s = io.open(p, encoding="utf-8").read()
    assert s.count('"ver": "%s"' % cur) == 1, "control_app stamp not found at %s" % cur
    io.open(p, "w", encoding="utf-8", newline="").write(
        s.replace('"ver": "%s"' % cur, '"ver": "%s"' % ver))

    p = os.path.join(REPO, "tv", "tv_diablo.py")
    s = io.open(p, encoding="utf-8").read()
    # re.sub silently returns the input unchanged when nothing matches, which would leave the tree
    # half-bumped — precisely the failure this tool exists to prevent. Count the substitutions.
    s, n = re.subn(r'VERSION = "v\d+"   # .*', 'VERSION = "%s"   # %s' % (ver, name), s, count=1)
    if n != 1:
        raise SystemExit("tv_diablo.py VERSION line did not match — stamp NOT written; the tree "
                         "would have been left half-bumped")
    io.open(p, "w", encoding="utf-8", newline="").write(s)

    p = os.path.join(REPO, "tv", "WINDOWS_SHIP.json")
    d = json.load(io.open(p, encoding="utf-8"))
    d["ver"] = ver
    d["note"] = "%s: %s" % (ver, note)
    io.open(p, "w", encoding="utf-8", newline="\n").write(
        json.dumps(d, indent=2, ensure_ascii=False) + "\n")

    print("%s -> %s  (%s)" % (cur, ver, name))


if __name__ == "__main__":
    bump(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
