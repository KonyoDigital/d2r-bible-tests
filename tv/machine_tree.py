# -*- coding: utf-8 -*-
"""v3393 — A MACHINE ESTABLISHES ITS OWN TREE.

HIS RULING, 2026-09-20: *"something needs to be synced to their own individual PCS and not my
addresses... the console needs to scan their own individual pc and fetch the information needed...
make sure its joined properly and architected with everything else and not a side job"* and
*"don't fix 'the Windows PC'. Fix 'any machine establishes its own tree'... Then Dean's PC is fixed
by pulling, with nobody touching Dean's PC."*

MEASURED on his Windows ALT box (read live over its own loopback, 2026-09-20, identity minted that
morning — a genuine first run):
    EXISTS  <repo>\\tv                    756 entries
    MISSING <repo>\\tv\\frames · frames\\hist · reels
    EXISTS  <home>\\d2r_ledger_backups    3 files, written that day
So the machine PROVISIONS AND WRITES correctly — the ledger writer creates its own directory. It is
the FRAME/REEL writers that establish nothing: control_app.py has 15 scattered makedirs,
frame_authority.py has 0, reel_retention.py has 0. Provisioning is a side effect of whichever code
path happens to run first, which is exactly the "side job" he refused.

⚠⚠ THE WORST OUTCOME IS NOT "CREATES NOTHING" — IT IS "CREATES THE TREE IN THE WRONG PLACE".
A third eye (grok-4-1-fast-reasoning) reviewed this design before a line was written and ranked that
first: if a root resolves under a redirected profile, OneDrive, or a build-agent workspace, ensure()
returns created, THE HEART TURNS GREEN, every later read succeeds against the wrong location, and the
empty panels vanish while the data goes somewhere nobody looks. The fault becomes INVISIBLE, which is
the thing this module exists to prevent. Hence: every root RECORDS WHICH ANCHOR WON, and an anchor
that cannot be established REFUSES instead of guessing. [[unknown-stays-unknown]]

⚠ EACH ROOT DECLARES ITS OWN ANCHOR KIND. The eye argued home should win precedence since it is the
only stable per-user anchor. Measured, that is wrong here: <repo>\\tv\\frames is repo-relative BY
DESIGN while <home>\\d2r_ledger_backups is home-relative AND ALREADY WORKS on that machine. A blanket
"prefer home" would relocate the one writer that is not broken. So the kind is a property of the
ROOT, never a global precedence.

⚠ NO EMOJI, NO UNSANITISED PATH, IN ANY MESSAGE. That console is cp1255: printing one non-ASCII
character crashes the process mid-report. A PATH CAN CARRY ONE — the eye caught that I had only
planned for emoji. Every path passes through _ascii() before it enters any string a caller may print.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# on / worked / lastTs vocabulary is the heart's; these are the states a ROOT can be in.
CREATED = "created"      # it did not exist; we made it AND proved a write
FOUND = "found"          # it existed AND we proved a write
UNUSABLE = "unusable"    # it exists but a write does not land (not a dir, read-only, ACLs)
FAILED = "failed"        # it does not exist and could not be made
REFUSED = "refused"      # its anchor could not be established — we will NOT guess a location


def _ascii(s):
    """Any path, safe to put in a message on a cp1255 console.

    ⚠ NOT COSMETIC. A user profile can contain a non-ASCII character; printing that path inside an
    error message kills the process on Windows BEFORE the caller ever sees the error. The third eye
    ranked this second of five risks and it is the one I had not planned for.
    """
    try:
        return str(s).encode("ascii", "replace").decode("ascii")
    except Exception:
        return "<unprintable path>"


def _frozen():
    """A packaged app has no meaningful repo-relative root.

    ⚠ pywebview apps are often frozen; deriving a repo root from __file__ then points INSIDE the
    executable or a temp dir, and the tree we build there vanishes on next run — an ephemeral tree
    that looks provisioned and is not. Third eye, risk 5.
    """
    return bool(getattr(sys, "frozen", False))


def anchors():
    """Where this machine's roots may hang, each with WHY it resolved that way.

    Returns {kind: (path_or_None, why)}. A None path is a REFUSAL, never a fallback.
    """
    out = {}

    env = os.environ.get("D2R_HOME") or ""
    out["env"] = ((env or None),
                  "D2R_HOME is set" if env else "D2R_HOME is not set")

    if _frozen():
        out["repo"] = (None, "this build is frozen, so a repo-relative root would live inside the "
                             "executable or a temp dir and would not survive a restart")
    else:
        out["repo"] = (os.path.dirname(HERE), "derived from this module location")

    home = os.path.expanduser("~")
    out["home"] = ((home if home and home != "~" else None),
                   "the user profile" if home and home != "~"
                   else "the home directory could not be expanded")
    return out


# Each root names its OWN anchor kind. This is the property the third eye's "prefer home"
# suggestion would have flattened, relocating the ledger writer that already works.
ROOTS = (
    ("tv",              "repo", ("tv",)),
    ("frames",          "repo", ("tv", "frames")),
    ("frames/hist",     "repo", ("tv", "frames", "hist")),
    # ⚠ NO "reels" ROOT. I invented one from my own probe list and the discoverer caught me:
    # it reported FAILED on THIS Mac, where frames and frames/hist are both established with
    # proven writes. A root absent on the machine that WORKS is not a root. Reels live INSIDE
    # hist (chronicle_calibrate.py joins them onto it), so creating tv/reels would have made an
    # empty directory on every machine that nothing ever reads - the third eye's risk 1,
    # "creates the tree in the wrong place", committed by the author of the warning.
    ("ledger backups",  "home", ("d2r_ledger_backups",)),
    ("board backups",   "home", ("d2r_board_backups",)),
)


def _prove_write(path):
    """A directory that EXISTS is not a directory that WORKS.

    ⚠ Third eye, risk 3: a path can exist yet not be a directory, be a symlink onto a read-only
    volume, or carry ACLs that fail the FIRST REAL WRITE — and a caller would see all-green while
    the tree is unusable. So `found` requires a proven write, not mere existence.
    """
    if not os.path.isdir(path):
        return False, "it exists but is not a directory"
    probe = os.path.join(path, ".__tree_probe__")
    try:
        with io.open(probe, "w", encoding="utf-8") as fh:
            fh.write("x")
    except Exception as e:
        return False, "a write does not land here (%s)" % e.__class__.__name__
    try:
        os.remove(probe)
    except Exception:
        pass          # the write is what we were proving; a stuck probe is not a failure
    return True, ""


def resolve():
    """This machine's roots, each carrying the anchor that produced it. Creates nothing."""
    anc = anchors()
    rows = []
    for name, kind, parts in ROOTS:
        base, why = anc.get(kind, (None, "unknown anchor kind"))
        if not base:
            rows.append({"root": name, "anchor": kind, "path": None, "state": REFUSED,
                         "why": "the %s anchor could not be established: %s" % (kind, why)})
            continue
        rows.append({"root": name, "anchor": kind, "path": os.path.join(base, *parts),
                     "state": None, "why": why})
    return rows


def ensure(create=True):
    """Establish this machine's tree and SAY WHAT IT DID.

    ⚠ created / found / unusable / failed / refused are FIVE DIFFERENT FACTS. A caller never sees a
    single boolean: "we made it", "it was already right", "it is there and does not work", "we could
    not make it", and "we refuse to guess where it goes" demand different responses.
    """
    rows = resolve()
    for r in rows:
        if r["state"] == REFUSED:
            continue
        p = r["path"]
        existed = os.path.isdir(p)
        if not existed:
            if not create:
                r["state"], r["why"] = FAILED, "it does not exist and creation was not requested"
                continue
            try:
                os.makedirs(p)
            except Exception as e:
                r["state"] = FAILED
                r["why"] = "could not be created (%s) at %s" % (e.__class__.__name__, _ascii(p))
                continue
        ok, why = _prove_write(p)
        if not ok:
            r["state"], r["why"] = UNUSABLE, why
        else:
            r["state"] = CREATED if not existed else FOUND
            r["why"] = "made and a write was proven" if not existed else "a write was proven"
    return rows


def say(rows):
    """One ASCII line a human can act on. Never a bare count."""
    n = {}
    for r in rows:
        n[r["state"]] = n.get(r["state"], 0) + 1
    bad = [r for r in rows if r["state"] in (UNUSABLE, FAILED, REFUSED)]
    head = "%d root(s): %s" % (len(rows),
                               ", ".join("%d %s" % (v, k) for k, v in sorted(n.items())))
    if not bad:
        return head + " - every root is established and a write was proven at each"
    return head + " - NOT established: " + "; ".join(
        "%s (%s) %s" % (b["root"], b["state"], b["why"]) for b in bad[:4])


if __name__ == "__main__":
    try:
        from console_safe import enable as _e
        _e()
    except Exception:
        pass
    _rows = ensure(create=False)      # report-only by default: never provision by being looked at
    for _r in _rows:
        print("  %-16s %-8s %-9s %s" % (_r["root"], _r["anchor"], _r["state"],
                                        _ascii(_r["path"])))
    print(say(_rows))
