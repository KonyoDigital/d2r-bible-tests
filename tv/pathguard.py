#!/usr/bin/env python3
"""redirect_module_path — the API every path-redirecting test must use.

⚠ WHY THIS IS NOT IN conftest.py. It was, and that broke CI for nine consecutive runs.

`tv/run_gates.py` runs each suite as a PLAIN SCRIPT (`python3 tv/test_x.py`), and the agent-tests
workflow installs only `pillow` — **there is no pytest on the runner**. A test that did
`from conftest import redirect_module_path` therefore pulled in conftest's module-level
`import pytest` and died with ModuleNotFoundError, as an ERROR rather than a failure, on a runner
where every local signal was green.

The helper itself needs nothing from pytest. It lives here so a script-run suite can use it, and
conftest re-exports it so `from conftest import redirect_module_path` keeps working.

[[test-venue]] — the host is part of the fixture, and so is the RUNNER.
"""
import contextlib
import os

# The tv/ directory. Lives here rather than being inherited from conftest: moving the
# function out without its dependency is exactly how this file first shipped, and the
# NameError only appeared when a suite RAN it — a module-level name resolves at call time.
HERE = os.path.dirname(os.path.abspath(__file__))


@contextlib.contextmanager
def redirect_module_path(module, attr, tmp_path):
    """Point `module.attr` at `tmp_path` for the duration of the block, then restore it.

    THE API EVERY PATH-REDIRECTING TEST MUST USE. Import it: `from conftest import
    redirect_module_path` (pytest puts this directory on sys.path), then:

        with redirect_module_path(control_app, "_CHRON_EVIDENCE_PATH", tmp_path / "ev.json"):
            control_app._save_chron_evidence(...)

    WHY IT EXISTS, 2026-08-21. A test redirected the evidence store with
    `os.environ["TV_CHRON_EVIDENCE"] = <tmp>` and then called the real save.
    `control_app._CHRON_EVIDENCE_PATH` is a module-level constant bound from that variable
    **when control_app is first imported** — which, inside a suite, has already happened. The
    assignment was a no-op, the write landed on his real banked evidence, and
    `tv/chron_evidence.json` went from 525,187 bytes to 748: 298 proposed uniques and 86 set
    pieces across 767 page reads, each paid for by a real model call, replaced by a two-item
    fixture. It was recovered only because `chron_last_result.json` happened to hold the same
    object.

    Three assertions, because the defect was never "the wrong value" — it was an isolation
    that was never checked:
      1. the attribute must ALREADY EXIST (a typo'd name patches nothing and reads as safety),
      2. the new path must NOT be inside this tv/ directory (redirecting onto live data is the
         incident with extra steps),
      3. after patching, `getattr(module, attr)` must equal the new path — the redirect TOOK.

    Returns the redirected path as a str, so callers can read back what was written.
    """
    new = str(tmp_path)
    if not hasattr(module, attr):
        raise AttributeError(
            "redirect_module_path: %s has no attribute %r — patching a name that does not "
            "exist isolates NOTHING and the real path stays bound. Check the spelling against "
            "the module." % (getattr(module, "__name__", module), attr))
    real = os.path.realpath(new)
    if real == HERE or real.startswith(HERE + os.sep):
        raise AssertionError(
            "redirect_module_path: refusing to redirect %s.%s at %s — that is inside the live "
            "tv/ directory. Redirect to tmp_path." % (
                getattr(module, "__name__", module), attr, real))
    original = getattr(module, attr)
    setattr(module, attr, new)
    got = getattr(module, attr)
    if got != new:
        setattr(module, attr, original)
        raise AssertionError(
            "redirect_module_path: THE REDIRECT DID NOT TAKE. %s.%s is %r, not %r. Do not run "
            "the write." % (getattr(module, "__name__", module), attr, got, new))
    try:
        yield new
    finally:
        setattr(module, attr, original)
