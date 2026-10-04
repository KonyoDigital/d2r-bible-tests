# -*- coding: utf-8 -*-
"""A tracked file that matches the fetched update is not a local edit.

The running console already treats a file whose bytes match origin/main, CR
ignored, as an update (_matches_fetched_origin). That code runs only inside a
process that has it. The launcher runs first, from the files on disk, and used
to skip the pull whenever git status showed any tracked change. A restart then
left the checkout where it was.

This does not fetch. It reads the origin/main ref already on disk. A blob that
cannot be read is not an update. A history that cannot fast-forward is not
reset. Unknown stays unknown: the caller skips the pull.

Exit codes of --apply: 0 the tree is clean, or the changed files were the
update and now sit on that commit; 2 local work, or not a fast-forward, nothing
was reset; 1 the tree could not be read.
"""
import os
import subprocess
import sys


def bytes_match_ignoring_cr(left, right):
    """Same rule as the console: equal, or equal once CR at end of line is ignored."""
    if left == right:
        return True

    def _norm(raw):
        return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

    return _norm(left) == _norm(right)


def _run(repo, args):
    try:
        r = subprocess.run(
            ["git", "-C", repo] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20,
        )
    except Exception:
        return 1, b"", b""
    return r.returncode, r.stdout or b"", r.stderr or b""


def _safe_rel(name):
    name = str(name or "").replace("\\", "/").strip()
    if not name or name.startswith("/") or name.startswith("~") or name.startswith('"'):
        return None
    if ".." in name.split("/") or ":" in name:
        return None
    return name


def _plain_modification(status):
    """A content change of a tracked file. Adds, deletes and renames block."""
    if len(status) < 2:
        return False
    return status[0] in " M" and status[1] in " M" and status != "  "


def _porcelain(repo):
    """Tracked porcelain rows, or None when git could not be read."""
    rc, out, _err = _run(repo, ["status", "--porcelain", "--untracked-files=no"])
    if rc != 0:
        return None
    rows = []
    for line in out.decode("utf-8", "replace").splitlines():
        if len(line) < 4:
            continue
        status, path = line[:2], line[3:]
        if status == "??":
            continue
        rows.append((status, path))
    return rows


def _matches(repo, rel):
    rc, blob, _err = _run(repo, ["show", "origin/main:" + rel])
    if rc != 0:
        return False
    try:
        with open(os.path.join(repo, rel), "rb") as fh:
            disk = fh.read()
    except Exception:
        return False
    return bytes_match_ignoring_cr(disk, blob)


def _is_ancestor(repo):
    """True when HEAD can fast-forward to origin/main. False when it cannot. None when unknown."""
    rc, _out, _err = _run(repo, ["merge-base", "--is-ancestor", "HEAD", "origin/main"])
    if rc == 0:
        return True
    if rc == 1:
        return False
    return None


def classify(repo):
    """-> {ok, block, update, ancestor}. Does not fetch and does not write."""
    rows = _porcelain(repo)
    if rows is None:
        return {"ok": False, "block": [], "update": [], "ancestor": None}
    block, update = [], []
    for status, path in rows:
        safe = _safe_rel(path)
        if safe is None or not _plain_modification(status) or " -> " in path:
            block.append(path or "?")
            continue
        if _matches(repo, safe):
            update.append(safe)
        else:
            block.append(safe)
    ancestor = _is_ancestor(repo) if update and not block else None
    return {"ok": True, "block": block, "update": update, "ancestor": ancestor}


def apply(repo, speak=False):
    """Put a tree that IS the fetched update onto that commit. Never fetches.

    0 clean, or reset onto the update. 2 local work or not a fast-forward.
    1 could not tell. A reset happens only when every tracked change matches
    origin/main and HEAD is an ancestor of that commit.
    """
    found = classify(repo)
    if not found["ok"]:
        msg = "could not tell whether the changed files are the update"
        code = 1
    elif found["block"]:
        msg = "tracked files modified (local work protected)"
        code = 2
    elif not found["update"]:
        msg = "clean"
        code = 0
    elif found["ancestor"] is not True:
        msg = "the fast-forward was refused; nothing was reset"
        code = 2
    else:
        rc, _out, _err = _run(repo, ["reset", "--hard", "origin/main"])
        if rc != 0:
            msg = "could not tell whether the changed files are the update"
            code = 1
        else:
            msg = "the changed files matched the update"
            code = 0
    if speak:
        print(msg)
    return code


def main(argv):
    repo = "."
    if "--repo" in argv:
        repo = argv[argv.index("--repo") + 1]
    if "--apply" in argv:
        return apply(repo, speak=True)
    found = classify(repo)
    if not found["ok"]:
        print("could not tell whether the changed files are the update")
        return 1
    anc = {True: "yes", False: "no"}.get(found["ancestor"], "unknown")
    print("block=%d update=%d ancestor=%s" % (len(found["block"]), len(found["update"]), anc))
    return 0 if not found["block"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
