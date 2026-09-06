#!/usr/bin/env python3
"""v1489 — stamp a new version across the four surfaces that carry one.

Usage: python bump_version.py v<N> <short name> <note...>   (the leading 'v' is required)

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
import datetime, io, json, os, re, sys

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

    # 2026-08-20 — AND A NOTE MAY NOT NAME A CSS TOKEN IN CALLABLE FORM.
    #
    # v1841 fixed a chip that referenced `var(--fs-tiny)`, a token this file never defines, and then
    # DESCRIBED the fix in the build note using that exact spelling. D2R_BUILD.note is a JS string
    # literal inside bible.html, and v1733's gate strips block comments but not string literals — so
    # it read the sentence about the token as a live reference to it and stayed red. The fix
    # re-created the very defect it fixed, one line further down. [[feedback-comments-vs-code]]
    #
    # Same shape as the apostrophe above: the note is DATA that lands in a parsed file, so what it
    # may contain is a property of the file and not of the prose. Write `--fs-tiny` bare instead.
    if "var(--" in note or "var(--" in name:
        raise SystemExit(
            "the note names a CSS token in callable form (var(--x)). D2R_BUILD.note is a string "
            "literal in bible.html and v1733's token gate cannot tell it from real CSS, so this "
            "would report a token that renders as nothing. Write the token bare: --x")

    # v1613 — REFUSE A VERSION WITHOUT ITS 'v'. Every consumer of these stamps matches `v\d+`:
    # the parity tests, the ship manifest comparison, the badge. Handing this tool a bare "1613"
    # wrote four stamps that all AGREED with each other and none of which any reader could parse —
    # a half-bumped tree by a different route, and worse than a mismatch because the stamps looked
    # internally consistent. It also poisons the next run: `cur` is found by the same `v\d+`
    # pattern, so the tool could no longer find its own previous stamp to replace.
    # v1617 — WHOLE NUMBERS ONLY. Konyo: "we said version go up in whole numbers instead of
    # decimals. so fix that too". Point releases were still being accepted here, so v1616.1 and
    # v1616.2 went out before he caught it. The rule is his and it is easy to keep by hand and easy
    # to forget under momentum, which is exactly the kind of rule that belongs in the tool.
    if not re.match(r"^v\d+$", ver):
        raise SystemExit("version must be a WHOLE number like v1617, not %r — no decimals, and the "
                         "leading 'v' is required (every stamp reader matches it)" % ver)

    # ── v1617 — COMPUTE ALL FOUR, THEN WRITE ALL FOUR ────────────────────────────────────────
    # This used to write each file as it went and raise on the first stamp that did not match. Its
    # own message said "the tree would have been left half-bumped" — but by the time tv_diablo.py
    # failed, bible.html and control_app.py had ALREADY been rewritten, so the sentence described a
    # state the tool had just created rather than one it prevented. (Seen for real stamping v1617
    # over a v1616.1 tree: two files moved, two did not.)
    # Every replacement is now resolved against the ORIGINAL text first; nothing touches disk until
    # all four are known good. The failure mode becomes "nothing happened", which is recoverable.
    today = datetime.date.today().isoformat()
    pending = []          # [(path, new_text)]

    p = os.path.join(REPO, "bible.html")
    s = io.open(p, encoding="utf-8").read()
    a = s.index("  window.D2R_BUILD = { id:'")
    b = s.index("\n", a)
    # STRICT ON WHAT IT WRITES, TOLERANT OF WHAT IT FINDS. The guard above refuses to STAMP a
    # decimal, but the tree may still be HOLDING one (v1616.1 shipped before the rule landed), and a
    # tool that cannot read the version it is replacing cannot replace it.
    _m = re.search(r"id:'(v\d+(?:\.\d+)*)'", s[a:b])
    if not _m:
        raise SystemExit("could not find the current D2R_BUILD id in bible.html — nothing written")
    cur = _m.group(1)
    new_line = ("  window.D2R_BUILD = { id:'%s', name:'%s - %s', date:'%s', note:'%s' };"
                % (ver, ver, name, today, note))
    pending.append((p, s[:a] + new_line + s[b:]))

    p = os.path.join(REPO, "tv", "control_app.py")
    s = io.open(p, encoding="utf-8").read()
    if s.count('"ver": "%s"' % cur) != 1:
        raise SystemExit("control_app.py stamp not found at %s — nothing written" % cur)
    pending.append((p, s.replace('"ver": "%s"' % cur, '"ver": "%s"' % ver)))

    p = os.path.join(REPO, "tv", "tv_diablo.py")
    s = io.open(p, encoding="utf-8").read()
    # tolerant read here too — the trailing comment is free text, and the version may be dotted
    s2, n = re.subn(r'VERSION = "v\d+(?:\.\d+)*"   # .*',
                    'VERSION = "%s"   # %s' % (ver, name), s, count=1)
    if n != 1:
        raise SystemExit("tv_diablo.py VERSION line did not match — nothing written")
    pending.append((p, s2))

    p = os.path.join(REPO, "tv", "WINDOWS_SHIP.json")
    d = json.load(io.open(p, encoding="utf-8"))
    d["ver"] = ver
    d["note"] = "%s: %s" % (ver, note)
    pending.append((p, json.dumps(d, indent=2, ensure_ascii=False) + "\n"))

    for path, text in pending:
        nl = "\n" if path.endswith(".json") else ""
        # ⚠⚠ v2712 — THIS LOOP WAS A TORN-READ GENERATOR, AND HIS CONSOLE IS THE READER.
        # `io.open(path, "w")` TRUNCATES ON OPEN, so between the truncate and the write
        # completing, the file on disk is EMPTY. bible.html is 6 MB and his console EXECS THE
        # WORKING TREE — it re-reads that file per request — so a page load landing in that
        # window parses nothing at all. [[execs-the-working-tree]]
        #
        # MEASURED, not theorised, on a 6,254,422-char copy with a reader polling concurrently:
        #     truncate-then-write   188 reads, 9 TORN (4.8%)   every torn size == 0 bytes
        #     tmp + os.replace      203 reads, 0 TORN (0.0%)
        # The torn reads were not partial parses — they were an EMPTY FILE, which is exactly the
        # symptom he described: "a panel that renders NOTHING and says nothing", unreproducible
        # afterwards because the settled tree is fine.
        #
        # os.replace() is atomic on the same filesystem, so a concurrent reader sees either the
        # whole old file or the whole new one and never a half. The repo already does this in 93
        # places; the four version stamps — the write that runs on EVERY ship — were not among
        # them. [[open-for-write-truncates-first]] [[stale-render]]
        atomic_write(path, text, nl)

    _drop_stale_bytecode([p for p, _t in pending])

    print("%s -> %s  (%s)" % (cur, ver, name))


def atomic_write(path, text, nl=""):
    """Write `text` to `path` so a CONCURRENT READER never sees a partial file.

    ⚠⚠ v2712 — THE FOUR-STAMP WRITE WAS A TORN-READ GENERATOR, AND HIS CONSOLE IS THE READER.
    This was `io.open(path, "w", ...).write(text)`, which TRUNCATES ON OPEN. Between the truncate
    and the write completing, the file on disk is EMPTY. bible.html is 6 MB, his console EXECS THE
    WORKING TREE and re-reads it per request, so a page load landing in that window parses nothing
    at all. [[execs-the-working-tree]]

    MEASURED on a 6,254,422-char copy with a reader polling concurrently — not theorised:

        truncate-then-write    188 reads,  9 TORN  (4.8%)   every torn size == 0 bytes
        tmp + os.replace       203 reads,  0 TORN  (0.0%)

    The torn reads were not partial parses. They were an EMPTY FILE, which is precisely the symptom
    he reported: "a panel that renders NOTHING and says nothing", unreproducible afterwards because
    the settled tree is fine. Every attempt to reproduce it on a settled tree was measuring the
    wrong moment. [[feedback-blind-fixture-green-gate]]

    os.replace() is atomic on the same filesystem: a reader sees the whole old file or the whole
    new one, never a half. The repo already did this in 93 places — the one write that runs on
    EVERY ship was not among them. [[open-for-write-truncates-first]] [[stale-render]]

    ⚠ THIS IS PER-FILE, NOT ACROSS THE FOUR. A crash between two stamps still leaves the set
    disagreeing; that is a different defect and this does not fix it. Saying otherwise would be
    the overclaim this repo keeps carving. [[unknown-stays-unknown]]
    """
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8", newline=nl) as fh:
        fh.write(text)
    os.replace(tmp, path)


def _drop_stale_bytecode(paths):
    """Delete the cached .pyc for every source this bump just edited.

    ⚠ THIS BUMP'S EDITS ARE INHERENTLY LENGTH-PRESERVING. "v2366" -> "v2367" is the same byte
    count, and Python decides a .pyc is fresh from the source's mtime AND SIZE. Edit twice inside
    one filesystem-timestamp tick and the interpreter keeps running the OLD compiled constants
    against correct source - silently.

    It bit three times on 2026-09-01 alone. The worst was `_app_ver()`, which deliberately reads
    the version out of `status_payload.__code__.co_consts` so it reports what this process is
    RUNNING rather than what is on disk (v2155). With a stale .pyc it answered v2366 while the
    file said v2367, `test_app_ver_equals_ship_version` went red on a correct tree, and a push
    was blocked twice for a defect that did not exist.

    ⚠ AND THE CACHE IS NOT IN __pycache__ ON THIS MAC. `sys.pycache_prefix` relocates it to
    ~/Library/Caches/com.apple.python/<absolute source path>, so anyone deleting __pycache__ and
    concluding "cleared" has cleared nothing. Both locations are removed here.
    [[python-pycache-prefix-mac]]
    """
    import sys as _sys
    removed = []
    for src in paths:
        if not src.endswith(".py"):
            continue
        stem = os.path.basename(src)[:-3]
        cands = []
        prefix = getattr(_sys, "pycache_prefix", None)
        if prefix:
            cands.append(os.path.join(prefix + os.path.dirname(os.path.abspath(src))))
        cands.append(os.path.join(os.path.dirname(os.path.abspath(src)), "__pycache__"))
        for d in cands:
            try:
                if not os.path.isdir(d):
                    continue
                for f in os.listdir(d):
                    if f.startswith(stem + ".") and f.endswith(".pyc"):
                        os.remove(os.path.join(d, f))
                        removed.append(f)
            except Exception:
                pass          # a cache we cannot clear is a warning, never a failed bump
    if removed:
        print("   cleared %d stale .pyc: %s" % (len(removed), ", ".join(sorted(set(removed))[:4])))
    return removed


if __name__ == "__main__":
    bump(sys.argv[1], sys.argv[2], " ".join(sys.argv[3:]))
