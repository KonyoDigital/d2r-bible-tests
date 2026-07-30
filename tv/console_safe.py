#!/usr/bin/env python3
"""v1480 — one place that makes a script's OUTPUT survive the operator's console.

Why this module exists
----------------------
This has now been the same bug three times:

  REG-044  tv_diablo needed a win32 stdio reconfigure to print its own status lines.
  REG-054  both test suites were only ever green because PYTHONIOENCODING was set by hand
           off-screen; a plain run went red AND corrupted a tracked fixture.
  REG-077  visual_lock_invariant and js_syntax_gate each PASSED their check, reached the success
           branch, and died inside print("✅ …") -> exit 1 on a clean tree.

The machine this ships on has a Hebrew console (cp1255), which cannot encode the check marks,
arrows and box characters the tooling prints everywhere. The failure is always the same shape and
always in the dangerous direction: a correct tree reports FAILURE, which trains people to ignore
the tool, and then the next real failure is ignored too.

A gate that cannot REPORT is a broken gate. Its verdict must depend on the code under test, never
on the shell that happened to launch it.

Usage
-----
    from console_safe import enable
    enable()          # first thing in main(), before anything prints

`errors="replace"` rather than a strict encoder: a character we failed to anticipate should cost a
question mark in the output, never the verdict.
"""
from __future__ import annotations

import sys

__all__ = ["enable"]


def enable(*streams):
    """Make stdout/stderr (or the given streams) encode any text without raising.

    Safe to call more than once, safe on every platform, and never raises — a helper whose job is
    to stop crashes must not become a new source of them. Returns True if every stream is now
    UTF-8 capable, False if any could not be reconfigured (an old file object, a redirect to a
    non-text stream), so a caller that cares can degrade its own output instead of guessing.
    """
    ok = True
    for stream in (streams or (sys.stdout, sys.stderr)):
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Python < 3.7, or a stream that is not a TextIOWrapper (pytest capture, a pipe wrapper,
            # a StringIO under test). Nothing to do and nothing worth crashing over.
            ok = False
    return ok
