#!/usr/bin/env python3
"""A7 — who ACTUALLY writes a reel store, witnessed at runtime instead of guessed statically.

A7's claim is that no reel gets a second implementation. Scoping it needs a count of who WRITES
each store, and I could not get one:

    a filename-adjacency grep        0 writers, all four stores
    an AST walk resolving constants  0 writers, all four stores

Neither follows a path bound in a helper (`TOMBSTONE_PATH = _tombstone_path()`) and threaded through
arguments. **Two zeros in a row measured MY INSTRUMENTS, not the code** (v2507), and a third static
detector would have been the same mistake with more effort. v2507 shipped a DECLARED-owner registry
instead and said plainly that it reports COUPLING, not writes.

This is the other half: a witness that watches the writes happen.

⚠⚠ IT ONLY EVER OBSERVES. It patches `open` and `os.replace` to RECORD, and calls straight through
to the originals — it never redirects, blocks, or fabricates a write. A tool that watches the one
door with no undo must not be able to move it.

⚠ AND IT PROVES NOTHING UNTIL SOMETHING RUNS. Enabling it does not gather evidence; a sweep has to
happen while it is on. This ships as the INSTRUMENT with its own proof, and the real per-store
answer is a measurement nobody has taken yet — which is a different fact from "one writer", and is
said here rather than implied. [[unknown-stays-unknown]]

    with write_witness.watching() as w:
        ...                      # anything
    w.writers("vault_swept.json")     -> ["frame_authority", ...]
"""
import io
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))

#: The stores A7 cares about. Named, not guessed — a witness that reports every file the process
#: touches drowns the answer in noise.
WATCHED = ("retro_triage.json", "reel_tombstones.json", "vault_accum.json", "vault_swept.json",
           "chron_evidence.json")

_WRITE_MODES = ("w", "a", "x", "+")


class Witness(object):
    """What was written, and by whom. Observation only."""

    def __init__(self, watched=WATCHED):
        self.watched = tuple(watched)
        self.events = []          # [{"store", "by", "mode", "where"}]

    # ── attribution ──────────────────────────────────────────────────────────────────────
    def _blame(self):
        """The nearest frame OUTSIDE this module that lives in the tree. -> (module, where)

        ⚠ NOT `sys._getframe(2)`. The write may be several helpers deep — the whole reason the
        static walks failed is that these paths are threaded through helpers — so a fixed depth
        would attribute every write to whichever utility happened to call `open`. Walk out until
        the frame is not this file, and report the first one that belongs to the tree.
        """
        try:
            stack = traceback.extract_stack()
        except Exception:
            return None, ""
        for fr in reversed(stack):
            fn = os.path.abspath(fr.filename or "")
            if fn == os.path.abspath(__file__):
                continue
            if not fn.startswith(HERE + os.sep):
                continue
            # ⚠⚠ A FRAME IS NOT ALWAYS A FILE, AND abspath MAKES ONE LOOK LIKE A LOCAL ONE.
            # `os.path.abspath("<stdin>")` is HERE + "/<stdin>", so an interactive or exec'd frame
            # passed the tree test above — and the blind `[:-3]` then reported the writer as
            # `<std`. A witness naming a module that does not exist is worse than one naming
            # nobody: the first is believed. Require a real .py file on disk.
            base = os.path.basename(fn)
            if not base.endswith(".py") or not os.path.isfile(fn):
                continue
            return base[:-3], "%s:%d" % (base, fr.lineno)
        return None, ""

    def _note(self, path, mode):
        try:
            base = os.path.basename(str(path or ""))
        except Exception:
            return
        if base not in self.watched:
            return
        by, where = self._blame()
        self.events.append({"store": base, "by": by, "mode": str(mode), "where": where})

    # ── the answer ───────────────────────────────────────────────────────────────────────
    def writers(self, store):
        """-> sorted module names that wrote this store while watching, or None if UNWATCHED.

        ⚠ None means the witness was not asked to watch it. An empty LIST means it watched and
        saw nothing — which is only evidence if something that should have written actually ran.
        """
        if store not in self.watched:
            return None
        return sorted({e["by"] for e in self.events if e["store"] == store and e["by"]})

    def report(self):
        return {"watched": list(self.watched), "events": list(self.events),
                "writers": {s: self.writers(s) for s in self.watched},
                "why": ("%d write(s) witnessed. An empty list is 'watched and saw nothing', which "
                        "is evidence only if something that should have written actually ran."
                        % len(self.events))}


class watching(object):
    """Context manager. Patches `open` and `os.replace` to RECORD and calls through."""

    def __init__(self, watched=WATCHED):
        self.w = Witness(watched)
        self._open = None
        self._replace = None

    def __enter__(self):
        import builtins
        # ⚠⚠ `io.open` IS A SEPARATE ATTRIBUTE AND THIS CODEBASE USES IT EVERYWHERE. Patching only
        # `builtins.open` left the witness blind: its own demo wrote a watched store and reported
        # ZERO writers — which would have been the THIRD instrument in this task returning a zero
        # that measured itself. Caught by the demo before it shipped, which is the only reason a
        # module whose whole job is counting writers did not ship unable to count.
        self._open, self._replace = builtins.open, os.replace
        self._io_open = io.open
        w = self.w

        def _open(file, mode="r", *a, **k):
            if any(c in str(mode) for c in _WRITE_MODES):
                w._note(file, mode)
            return self._open(file, mode, *a, **k)

        def _replace(src, dst, *a, **k):
            # ⚠ THE ATOMIC WRITE IS THE ONE THAT MATTERS AND IT IS NOT AN `open` OF THE STORE.
            # These stores are written to `<name>.tmp` and moved into place, so a witness that
            # watched only `open` would see the tmp file and NEVER the store — and report zero
            # writers for a store being written on every sweep. That is exactly the shape of the
            # two static failures this replaces.
            w._note(dst, "replace")
            return self._replace(src, dst, *a, **k)

        builtins.open = _open
        io.open = _open
        os.replace = _replace
        return w

    def __exit__(self, *exc):
        import builtins
        builtins.open = self._open
        io.open = self._io_open
        os.replace = self._replace
        return False


def main(argv):
    import json
    print("\nWRITE WITNESS — who actually writes a reel store\n")
    print("  watched: %s" % ", ".join(WATCHED))
    print()
    print("  ⚠ This is an INSTRUMENT, not a measurement. Enabling it gathers nothing; a sweep has")
    print("     to run while it is on. The per-store answer is a measurement NOBODY HAS TAKEN,")
    print("     which is a different fact from 'one writer'.")
    if "--demo" in argv:
        import tempfile
        with watching() as w:
            p = os.path.join(tempfile.mkdtemp(), "vault_swept.json")
            with io.open(p, "w", encoding="utf-8") as fh:
                fh.write("{}")
        print("\n  demo (this module writing one store): %s" % json.dumps(w.report()["writers"]))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
