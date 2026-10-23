# -*- coding: utf-8 -*-
"""#143 (REG-2451) - SEED A PUSH WORKTREE WITH THE UNTRACKED STATE ITS GATES READ, IN ONE CALL.

    python3 tv/seed_worktree.py <worktree> [--dry-run]

A fresh worktree made to push from lacks the gitignored files the pre-push gates read, so a push refused one gap at a
time: console-demos needs node_modules; the render gate's heart-stored surfaces need tv/.heart2.json (unseeded, six of
them read 'shrank' - and a data-less panel must never be --blessed); the second-eye gate needed tv/.second_eye.jsonl
until #178 made that ledger one per machine. This joins worktree creation to that state:

  · THE MAIN CHECKOUT IS FOUND FROM THE WORKTREE'S OWN .git POINTER (its gitdir -> commondir -> the common dir, whose
    parent is the main checkout), never from a home path and never by running git (a hook's GIT_DIR would answer for
    whichever tree set it).
  · IT COPIES, NEVER LINKS. A node_modules SYMLINK into another checkout once deleted main's real node_modules (v3525: a
    link is a file, `git add -A` committed it, and checking that commit out in main replaced the directory with it).
    Files are copied; a symlink INSIDE node_modules stays a symlink only when it is relative and lands inside the copy
    (node_modules/.bin's), anything else is copied as what it points at. Each item is built under
    <worktree>/.seed-tmp/node_modules/ (ignored by git at any depth) and moved into place whole, so a killed seed never
    leaves half a node_modules behind under the real name.
  · IT NEVER OVERWRITES. An item already present in the worktree (file, directory or link) is left exactly as it is.
  · tv/.second_eye.jsonl IS ASKED, NOT ASSUMED: it is seeded only while the second_eye_ledger the WORKTREE runs still
    keeps a per-checkout ledger (its module is read; #178 retires the copy, and a branch from before #178 still gets it).
  · IT REFUSES, COPYING NOTHING (exit 2): a destination that is the main checkout itself (its .git is a directory), a
    path that is not a worktree root, a pointer that will not resolve, a common dir with no main checkout beside it, and
    a seed that would leave free disk under his ON AIR floor (FLOOR_GB, the console's own line). TV_SEED_FREE_BYTES is a
    law's seam for the free-space reading.
  · It prints what it seeded, what it left, and the headroom after. Exit 0 = every item is in the worktree; 1 = an item
    could not be seeded (main has none, or a copy failed - named); 2 = refused, nothing copied.
The law: test_a_push_worktree_is_seeded_before_its_gates.
"""
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
#: his ON AIR floor - /api/on refuses to film below it (control_app.ON_AIR_FLOOR_GB, measured there as free / 1e9)
FLOOR_GB = 8.0
ENV_FREE = "TV_SEED_FREE_BYTES"          # a law's seam: the free bytes to assume instead of measuring the disk
STAGE = os.path.join(".seed-tmp", "node_modules")     # under a node_modules/ component: git ignores it at any depth
#: what a push worktree needs and git does not carry: (path relative to the checkout, kind)
ITEMS = (("node_modules", "dir"), (os.path.join("tv", ".heart2.json"), "file"))
SECOND_EYE = os.path.join("tv", ".second_eye.jsonl")


def _gitdir_of(worktree):
    """-> (the checkout's gitdir, None) | (None, why). A linked worktree's .git is a pointer FILE; a main checkout's is
    the directory itself (so a main checkout resolves to itself, and seed() refuses it in one place)."""
    g = os.path.join(worktree, ".git")
    if os.path.isdir(g):
        return g, None
    if not os.path.isfile(g):
        return None, "it has no .git - not a worktree root"
    try:
        with io.open(g, encoding="utf-8") as fh:
            line = fh.read().strip()
    except (OSError, ValueError) as e:
        return None, "its .git pointer would not read (%s)" % type(e).__name__
    if not line.startswith("gitdir:"):
        return None, "its .git file is not a gitdir pointer"
    gd = line.split(":", 1)[1].strip()
    gd = os.path.normpath(gd if os.path.isabs(gd) else os.path.join(worktree, gd))
    if not os.path.isdir(gd):
        return None, "its .git pointer names %s, which is not a directory" % gd
    return gd, None


def main_checkout_of(worktree):
    """The main checkout a checkout belongs to, read from its .git (a main checkout answers itself). -> (path, None) | (None, why)"""
    worktree = os.path.abspath(worktree)
    gd, why = _gitdir_of(worktree)
    if gd is None:
        return None, why
    common = gd
    cd = os.path.join(gd, "commondir")
    try:
        if os.path.isfile(cd):
            with io.open(cd, encoding="utf-8") as fh:
                rel = fh.read().strip()
            common = os.path.normpath(rel if os.path.isabs(rel) else os.path.join(gd, rel))
        elif os.path.basename(os.path.dirname(gd)) == "worktrees":
            common = os.path.dirname(os.path.dirname(gd))     # git's own layout when the commondir file is missing
    except (OSError, ValueError) as e:
        return None, "its gitdir's commondir would not read (%s)" % type(e).__name__
    if os.path.basename(common) != ".git":
        return None, "its common git dir %s is not a checkout's .git (a bare repository has no main checkout)" % common
    main = os.path.dirname(common)
    if not os.path.isdir(main):
        return None, "the main checkout %s is not a directory" % main
    return main, None


def second_eye_per_checkout(worktree):
    """Will the second_eye_ledger THIS WORKTREE runs keep a per-checkout ledger? -> (bool, why)

    Asked of the module the worktree's own gates will run (its tv/second_eye_ledger.py, parsed - never imported or
    run): a module from before #178 has no machine_ledger() and keeps tv/.second_eye.jsonl, so the copy is still
    needed; one that has it is asked where this worktree's ledger lives. A module that cannot be read is UNKNOWN, and
    the copy is made: a missing ledger refuses a push, an extra copy is only folded in."""
    import ast
    src = os.path.join(worktree, "tv", "second_eye_ledger.py")
    try:
        with io.open(src, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, ValueError) as e:
        return True, ("the worktree's tv/second_eye_ledger.py would not read (%s) - seeded, since a missing ledger "
                      "refuses a push" % type(e).__name__)
    if not any(isinstance(n, ast.FunctionDef) and n.name == "machine_ledger" for n in tree.body):
        return True, "the worktree's second_eye_ledger predates #178 - its ledger is per checkout"
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import second_eye_ledger as SEL
        path, why = SEL.machine_ledger(worktree)
    except Exception as e:
        return True, "where the worktree's ledger lives could not be asked (%s) - seeded" % type(e).__name__
    own = os.path.realpath(path) == os.path.realpath(os.path.join(worktree, SECOND_EYE))
    if why is not None or own:
        return True, "the worktree keeps its own ledger (%s)" % (why or path)
    return False, "the second-eye ledger is one per machine (#178) - nothing to seed"


def _followed_bytes(path, seen):
    """(files, bytes) of `path` with every link FOLLOWED - what shutil.copytree(symlinks=False) / copy2 will write.
    A directory already walked (its real path in `seen`) costs nothing again, so a link cycle ends."""
    try:
        if not os.path.isdir(path):
            return (1, os.path.getsize(path)) if os.path.exists(path) else (0, 0)
    except OSError:
        return 0, 0
    files = total = 0
    for root, dirs, names in os.walk(path, followlinks=True):
        real = os.path.realpath(root)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        for n in names:
            try:
                total += os.path.getsize(os.path.join(root, n))
                files += 1
            except OSError:
                continue                          # a dangling link: copy2 is never reached for it (exists() is False)
    return files, total


def _tree_bytes(src):
    """(files, bytes) the copy of `src` that seed() WRITES will take - priced the way _copy_tree / _copy_link copy it.

    REG-2451 round 2 (M2 review): this once priced links as free and a linked top-level directory as its own st_size,
    while the copy walks a linked node_modules whole and materialises every link it does not keep - so a seed passed the
    ON AIR floor short by the whole store. Now: a top-level link is followed (os.walk follows it, so does the copy); a
    link inside the tree costs its target's FOLLOWED bytes - even one kept as a link, because on a PC with no symlink
    privilege (Windows) _copy_link copies it instead, and the floor must hold there too."""
    if not os.path.isdir(src):
        return _followed_bytes(src, set())
    files = total = 0
    for root, dirs, names in os.walk(src):
        for n in list(dirs) + list(names):
            p = os.path.join(root, n)
            if os.path.islink(p):
                f, b = _followed_bytes(p, set())    # per link: two links to one store are two copies
                files += f
                total += b
            elif n in names:
                try:
                    total += os.lstat(p).st_size
                    files += 1
                except OSError:
                    continue
    return files, total


def _inside(root, path):
    r = os.path.realpath(root)
    return os.path.realpath(path) == r or os.path.realpath(path).startswith(r + os.sep)


def _copy_link(s, t, root):
    """A link inside the copied tree: kept as a link only when relative and landing inside the tree, else copied."""
    target = os.readlink(s)
    if not os.path.isabs(target) and _inside(root, os.path.join(os.path.dirname(s), target)):
        try:
            os.symlink(target, t)
            return
        except OSError:
            pass                                  # no symlink privilege (Windows): the copy below stands in
    if os.path.isdir(s):
        shutil.copytree(s, t, symlinks=False)
    elif os.path.exists(s):
        shutil.copy2(s, t)


def _copy_tree(src, dst):
    """A REAL copy of the directory `src` at `dst` (which must not exist): directories made, files copied."""
    os.makedirs(dst)
    for root, dirs, names in os.walk(src):
        rel = os.path.relpath(root, src)
        droot = dst if rel == os.curdir else os.path.join(dst, rel)
        for d in list(dirs):
            s, t = os.path.join(root, d), os.path.join(droot, d)
            if os.path.islink(s):
                _copy_link(s, t, src)             # os.walk does not descend a linked directory
            else:
                os.makedirs(t)
        for n in names:
            s, t = os.path.join(root, n), os.path.join(droot, n)
            if os.path.islink(s):
                _copy_link(s, t, src)
            else:
                shutil.copy2(s, t)


def _install(stage_root, src, final, kind):
    """Copy `src` under the stage, then move it into place whole. Never over an existing path. -> None | why not"""
    staged = os.path.join(stage_root, "%s.%d" % (os.path.basename(final), os.getpid()))
    if os.path.lexists(staged):
        if os.path.isdir(staged) and not os.path.islink(staged):
            shutil.rmtree(staged)
        else:
            os.unlink(staged)
    if kind == "dir":
        _copy_tree(src, staged)
        if os.path.lexists(final):
            shutil.rmtree(staged)
            return "it appeared while the copy ran - left as it is"
        os.rename(staged, final)
        return None
    shutil.copy2(src, staged)
    try:
        os.link(staged, final)                    # refuses an existing path, atomically
    except FileExistsError:
        return "it appeared while the copy ran - left as it is"
    except OSError:
        if os.path.lexists(final):
            return "it appeared while the copy ran - left as it is"
        os.rename(staged, final)                  # a volume with no hard links
        return None
    finally:
        if os.path.lexists(staged):
            os.unlink(staged)
    return None


def _free_bytes(worktree):
    raw = os.environ.get(ENV_FREE)
    if raw is not None and str(raw).strip():
        return int(str(raw).strip()), "%s=%s" % (ENV_FREE, raw)
    return shutil.disk_usage(worktree).free, None


def seed(worktree, say=print, dry=False, second_eye=None):
    """Seed `worktree` from its main checkout. -> exit code (0 seeded/present, 1 an item could not be seeded, 2 refused)

    `second_eye` (bool) overrides asking second_eye_ledger whether its ledger is still per checkout - a law's seam."""
    worktree = os.path.abspath(worktree)
    if not os.path.isdir(worktree):
        say("seed: REFUSED - %s is not a directory" % worktree)
        return 2
    main, why = main_checkout_of(worktree)
    if main is None:
        say("seed: REFUSED - %s: %s. Nothing was copied." % (worktree, why))
        return 2
    if os.path.realpath(main) == os.path.realpath(worktree):
        say("seed: REFUSED - %s is the main checkout itself, never a seed destination. Nothing was copied." % worktree)
        return 2
    items = list(ITEMS)
    if second_eye is None:
        second_eye, se_why = second_eye_per_checkout(worktree)
    else:
        se_why = "told by the caller"
    if second_eye:
        items.append((SECOND_EYE, "file"))
    say("seed: worktree %s" % worktree)
    say("seed: main checkout %s (from the worktree's own .git pointer)" % main)
    plan, need, rc = [], 0, 0
    for rel, kind in items:
        src, dst = os.path.join(main, rel), os.path.join(worktree, rel)
        if os.path.lexists(dst):
            say("seed:   %-22s already present - left exactly as it is" % rel)
            continue
        if not os.path.exists(src) or (kind == "dir") != os.path.isdir(src):
            say("seed:   %-22s ⚠ NOT SEEDED - the main checkout has no %s %s" % (rel, kind, rel))
            rc = 1
            continue
        n, b = _tree_bytes(src)
        plan.append((rel, kind, src, dst, n, b))
        need += b
    if not second_eye:
        say("seed:   %-22s not seeded - %s" % (SECOND_EYE, se_why))
    else:
        say("seed:   %-22s wanted - %s" % (SECOND_EYE, se_why))
    try:
        free, seam = _free_bytes(worktree)
    except Exception as e:
        say("seed: REFUSED - free disk could not be read (%s), so the %.0f GB floor cannot be kept. Nothing was copied."
            % (type(e).__name__, FLOOR_GB))
        return 2
    floor = int(FLOOR_GB * 1e9)
    if free - need < floor:
        say("seed: REFUSED - %.2f GB free%s, and the seed takes %.1f MB: that leaves %.2f GB, under his %.0f GB ON AIR "
            "floor. Nothing was copied." % (free / 1e9, (" (%s)" % seam) if seam else "", need / 1e6,
                                            (free - need) / 1e9, FLOOR_GB))
        return 2
    if dry:
        for rel, _k, _s, _d, n, b in plan:
            say("seed:   %-22s would be copied (%.1f MB, %d file(s))" % (rel, b / 1e6, n))
        say("seed: headroom %.2f GB free after the seed (floor %.0f GB) - dry run, nothing copied"
            % ((free - need) / 1e9, FLOOR_GB))
        return rc
    stage_root = os.path.join(worktree, STAGE)
    if plan:
        os.makedirs(stage_root, exist_ok=True)
    try:
        for rel, kind, src, dst, n, b in plan:
            parent = os.path.dirname(dst)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            try:
                why_not = _install(stage_root, src, dst, kind)
            except Exception as e:
                say("seed:   %-22s ⚠ NOT SEEDED - the copy failed (%s: %s)" % (rel, type(e).__name__, str(e)[:120]))
                rc = 1
                continue
            if why_not:
                say("seed:   %-22s %s" % (rel, why_not))
            else:
                say("seed:   %-22s copied (%.1f MB, %d file(s))" % (rel, b / 1e6, n))
    finally:
        top = os.path.join(worktree, ".seed-tmp")
        if os.path.isdir(top) and not os.path.islink(top):
            shutil.rmtree(top, ignore_errors=True)
    try:
        after, _seam = _free_bytes(worktree)
        if _seam:
            after = free - need
    except Exception:
        after = free - need
    say("seed: headroom %.2f GB free after the seed (floor %.0f GB)" % (after / 1e9, FLOOR_GB))
    return rc


def main(argv):
    try:
        for stream in (sys.stdout, sys.stderr):
            stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print("usage: python3 tv/seed_worktree.py <worktree> [--dry-run]")
        return 2
    return seed(args[0], dry="--dry-run" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
