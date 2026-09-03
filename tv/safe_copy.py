#!/usr/bin/env python3
"""Copy this repo somewhere scratch WITHOUT the things that will fill his disk.

⚠⚠ WHY THIS EXISTS, MEASURED. On 2026-09-03 three review agents were each told, in my own workflow
prompt, to "work on COPIES under /tmp if you need to sabotage something". Each ran

    cp -R /Users/konyo/d2r_bible_tests/tv /tmp/skep_<n>/tv

`tv/` holds the reel JPEG store (5.8 GB) and, at the time, a Chrome profile the render gate never
cleaned (1.4 GB). Three copies wrote **20.5 GB in four minutes** onto a volume with about 9 GB
free. It hit ENOSPC, and then every Bash call in the session — mine and every agent's — failed
before it ran, because the harness could not create its own output file. Nobody could even run
`df` to see what had happened, let alone `rm`.

The prompt was the defect. "Copy it to /tmp" is a reasonable instruction that happens to be
catastrophic in a repo carrying gigabytes of footage, and no amount of remembering fixes that.
So: a copier that CANNOT carry the heavy directories, and REFUSES rather than filling the disk.

    python3 tv/safe_copy.py /tmp/my_scratch          # the whole repo, minus the heavy parts
    python3 tv/safe_copy.py /tmp/my_scratch tv       # just tv/, same exclusions

⚠ IT IS NOT A GENERAL COPIER AND MUST NOT BECOME ONE. It has one job: make the copy a sabotage
test needs, which is source and config, never footage.
"""
import argparse
import io
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: Directory NAMES never copied, at any depth. Each is here because it is large and regenerable —
#: a sabotage test reads source, never footage.
HEAVY = (
    "frames",           # the reel JPEG store — 5.8 GB, and it is HIS footage
    ".render_shots",    # render gate output: PNGs plus, until v2476, a 1.4 GB Chrome profile
    ".git",             # a full object store, and no sabotage test needs history
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "test-results",
    "playwright-report",
    "backups",
    "_archive",
)

#: Refuse outright above this. A sabotage copy that needs a gigabyte is not a sabotage copy, it is
#: the accident this file exists to prevent. Deliberately well under any plausible free-space
#: margin: the point is to fail while the machine is still usable, not at the last byte.
MAX_MB = 400

#: And never write a copy that would take the machine below this. Measured the hard way: at zero
#: bytes free, the tool cannot create its own output file, so NOTHING can run — not df, not rm.
#: A guard that only refuses at ENOSPC refuses too late to be fixed.
KEEP_FREE_MB = 4096


def _free_mb(path):
    """Free MB on the volume that will hold `path`. -> int | None

    ⚠⚠ IT MUST CLIMB TO AN EXISTING ANCESTOR, AND THE FIRST VERSION DID NOT. `os.statvfs`
    raises on a directory that does not exist yet, so this returned None for exactly the
    invocation this file's own docstring recounts as the disaster:

        python3 tv/safe_copy.py /tmp/skep_3/tv tv     # /tmp/skep_3 not created yet

    None then skipped the floor entirely (`if free is not None and ...`) while
    `shutil.copytree` happily called `os.makedirs` and wrote anyway. The 4 GB floor — the
    whole reason this file exists — was OFF on the one command shape that caused the
    ENOSPC. `copytree` creates the intermediates, so the volume that matters is the one
    under the nearest ancestor that already exists. Climb to it.
    """
    p = os.path.abspath(path)
    while True:
        try:
            st = os.statvfs(p)
            return (st.f_bavail * st.f_frsize) // (1024 * 1024)
        except Exception:
            parent = os.path.dirname(p)
            if parent == p:       # reached the root and still nothing — genuinely unknown
                return None
            p = parent


def plan(src):
    """-> (files, bytes, skipped_dirs). Walks once, counting what WOULD be copied."""
    files, total, skipped = 0, 0, []
    for root, dirs, names in os.walk(src):
        drop = [d for d in dirs if d in HEAVY]
        for d in drop:
            skipped.append(os.path.relpath(os.path.join(root, d), src))
        dirs[:] = [d for d in dirs if d not in HEAVY]
        for n in names:
            p = os.path.join(root, n)
            try:
                if os.path.islink(p):
                    continue          # a symlink is copied as a link; it carries no bytes
                total += os.path.getsize(p)
                files += 1
            except Exception:
                pass
    return files, total, sorted(skipped)


def copy(src, dst, force=False, say=print):
    """-> exit code. Refuses before writing anything if the plan is too big."""
    src = os.path.abspath(src)
    dst = os.path.abspath(dst)
    if not os.path.isdir(src):
        say("no such source: %s" % src)
        return 2
    if dst.startswith(REPO + os.sep) or dst == REPO:
        say("REFUSED — the destination is inside the repo (%s). A scratch copy belongs outside it, "
            "or the next walk copies the copy." % dst)
        return 2

    files, total, skipped = plan(src)
    mb = total / (1024.0 * 1024.0)
    free = _free_mb(os.path.dirname(dst) or "/")
    say("plan: %d file(s), %.1f MB, skipping %d heavy director%s"
        % (files, mb, len(skipped), "y" if len(skipped) == 1 else "ies"))
    for s in skipped[:8]:
        say("   skipped: %s" % s)
    if len(skipped) > 8:
        say("   ... and %d more" % (len(skipped) - 8))

    if mb > MAX_MB and not force:
        say("REFUSED — %.1f MB is over the %d MB ceiling. This copier is for source, not data. "
            "If you really mean it, pass --force, and check `df` first." % (mb, MAX_MB))
        return 1
    # ⚠ AND UNKNOWN IS NOT PERMISSION. If the free space could not be established at all,
    # refuse — a floor that abstains whenever it cannot measure is not a floor. Reaching
    # here means statvfs failed on every ancestor up to the root, which is not a normal
    # state and is not a reason to write gigabytes. [[unknown-stays-unknown]]
    if free is None:
        say("REFUSED — could not establish free space for %s (statvfs failed on every "
            "ancestor up to the root). That is UNKNOWN, not enough room." % dst)
        return 1
    if (free - mb) < KEEP_FREE_MB:
        say("REFUSED — the volume has %d MB free and this would leave %d MB, under the %d MB "
            "floor. At zero bytes nothing can run at all, not even the command that would clean "
            "up: on 2026-09-03 every shell in the session died at spawn."
            % (free, int(free - mb), KEEP_FREE_MB))
        return 1

    def _ignore(_d, names):
        return {n for n in names if n in HEAVY}

    if os.path.exists(dst):
        say("REFUSED — %s already exists. Remove it yourself, deliberately." % dst)
        return 2
    shutil.copytree(src, dst, ignore=_ignore, symlinks=True)
    say("copied %d file(s), %.1f MB -> %s" % (files, mb, dst))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Copy the repo to scratch without the heavy parts.")
    ap.add_argument("dest")
    ap.add_argument("subdir", nargs="?", default="",
                    help="copy only this subdirectory of the repo (e.g. tv)")
    ap.add_argument("--force", action="store_true",
                    help="ignore the size ceiling (never ignores the free-space floor)")
    ap.add_argument("--plan", action="store_true", help="say what it would copy and stop")
    a = ap.parse_args(argv)

    src = os.path.join(REPO, a.subdir) if a.subdir else REPO
    if a.plan:
        files, total, skipped = plan(src)
        print("would copy %d file(s), %.1f MB" % (files, total / (1024.0 * 1024.0)))
        for s in skipped:
            print("   skipping %s" % s)
        return 0
    # ⚠ `force` was parsed and dropped here, so the refusal message advised a flag that did
    # nothing: over the ceiling, `--force` printed the identical refusal and exited 1.
    return copy(src, a.dest, force=a.force)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main())
