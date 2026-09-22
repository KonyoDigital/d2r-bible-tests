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


def footage_frames():
    """Where THIS machine's frames root lives. None means the repo anchor was refused.

    TV_FRAMES_DIR wins, because a harness that set it owns a scratch tree and must not
    be redirected onto the live one. [[feedback-fixtures-never-touch-live-data]]
    """
    env = os.environ.get("TV_FRAMES_DIR") or ""
    if env:
        return env
    for r in resolve():
        if r["root"] == "frames":
            return r["path"]
    return None


def footage_hist():
    """Where THIS machine's hist lives. Same rule as footage_frames: env first, then the door."""
    env = os.environ.get("TV_HIST") or ""
    if env:
        return env
    for r in resolve():
        if r["root"] == "frames/hist":
            return r["path"]
    return None


def establish():
    """The door the WRITERS walk through. Looking uses ensure(create=False).

    ⚠ A harness that set TV_HIST / TV_FRAMES_DIR owns a scratch tree. Creating THIS
    machine's live roots from inside that harness would plant the tree in his real
    directory while the test thought it was isolated — the third eye's risk 1,
    arriving as a writer instead of a discoverer.
    ⚠ Looking never provisions. Writing does. frame_authority and reel_retention
    PLAN; they call footage_hist() and never this.
    """
    hist = os.environ.get("TV_HIST") or ""
    frames = os.environ.get("TV_FRAMES_DIR") or ""
    if hist or frames:
        rows = []
        # ⚠⚠ v3410 — HALF A HARNESS IS NOT HALF A TREE, AND `continue` MADE THE MISSING HALF
        # LOOK ESTABLISHED. With TV_FRAMES_DIR set and TV_HIST unset — which is exactly
        # replay.py:217 spawning a tv_diablo child — this loop skipped the hist root and
        # returned rows saying the one it DID make was created. Meanwhile tv_diablo.py:2345
        # still computes `HIST_DIR = TV_HIST or join(FRAMES, "hist")`, so the writer aims at a
        # directory the door never made. MEASURED: makedirs ['/tmp/SAND/frames'] only,
        # HIST_DIR created False — then every _archive_footage_copy dies on
        # shutil.disk_usage(HIST_DIR), is swallowed at tv_diablo.py:1840, and _FOOTAGE_WHY
        # still reads 'grab', so the console shows no reason and no disk-full. Silent from boot.
        #
        # ⚠ THE TWO HALVES ARE NOT SYMMETRIC, AND THAT ASYMMETRY IS THE WHOLE CARE HERE.
        #   frames set, hist empty -> DERIVE join(frames, "hist"). That is literally the
        #     arithmetic tv_diablo.py:2345 does, and it stays INSIDE the harness's own scratch
        #     tree, so it cannot reach his real footage.
        #   hist set, frames empty -> the partner CANNOT be derived: frames would be the LIVE
        #     tree, and provisioning that from inside an isolated harness is this module's
        #     risk 1, arriving as a writer. So it is REFUSED and NAMED, never skipped.
        # [[unknown-stays-unknown]] — a root nobody established must not read as one that was.
        # ⚠⚠ v3412 — DERIVE THE PATH, NEVER THE VERDICT. v3410 appended a FOUND/CREATED row for
        # the derived hist root BEFORE the attempt ran, and the loop below then appended a SECOND
        # row for the same root when the write failed. REPRODUCED: with TV_FRAMES_DIR set and
        # <frames>/hist existing at mode 0555, establish() returned
        #   root=frames/hist state=found      why=derived from TV_FRAMES_DIR...
        #   root=frames/hist state=unusable   why=a write does not land here (PermissionError)
        # — two states for one root, and a reader taking the first hit archives into a directory
        # whose write had just failed. Named by the cross-family review of v3410, on code one
        # hour old. The provenance is carried in a FLAG and spent in the ONE row the loop writes.
        # [[unknown-stays-unknown]] — a root has exactly one state, and it is the measured one.
        derived_hist = False
        if frames and not hist:
            hist = os.path.join(frames, "hist")
            derived_hist = True
        for name, p in (("frames", frames), ("frames/hist", hist)):
            if not p:
                rows.append({"root": name, "anchor": "env", "path": None, "state": REFUSED,
                             "why": ("TV_HIST names a scratch tree but TV_FRAMES_DIR does not, "
                                     "and this root cannot be derived from it without pointing "
                                     "at the live tree — set both or neither")})
                continue
            existed = os.path.isdir(p)
            try:
                os.makedirs(p, exist_ok=True)
            except Exception as e:
                rows.append({"root": name, "anchor": "env", "path": p, "state": FAILED,
                             "why": "could not be created (%s) at %s"
                                    % (e.__class__.__name__, _ascii(p))})
                continue
            ok, why = _prove_write(p)
            if not ok:
                rows.append({"root": name, "anchor": "env", "path": p,
                             "state": UNUSABLE, "why": why})
            else:
                rows.append({"root": name, "anchor": "env", "path": p,
                             "state": CREATED if not existed else FOUND,
                             "why": ("derived from TV_FRAMES_DIR, inside the harness's own tree"
                                     if (derived_hist and name == "frames/hist")
                                     else "scratch tree for an isolated harness")})
        return rows
    return ensure(create=True)


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
