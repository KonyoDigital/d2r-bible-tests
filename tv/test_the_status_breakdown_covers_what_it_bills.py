# -*- coding: utf-8 -*-
"""#28 — EVERY PRODUCER IN status_payload IS TIMED, OR IT IS EXEMPT BY NAME WITH A REASON.

MEASURED 2026-09-09 on his live console (947 requests since boot, 6 slow):

    totalMs 36.4 · sections sum 2.7 · unattributedMs 33.7   ->  93% of the request UNEXPLAINED

Thirteen producers were wrapped in `_t()` and thirty-one were not, so the breakdown billed 7% of
the time it was measuring. #28's own next step was "reproduce with a live recording session and
read the per-section breakdown" — and that reproduction would have returned a breakdown saying
96% UNKNOWN, because even every instrumented section at its worst-since-boot sums to 2,192 ms
against a 52,360 ms event. **An instrument that explains 4% of the thing it exists to explain
sends the reader looking in the wrong place.** [[zero-needs-a-denominator]]

After wrapping sixteen more: totalMs 1141.5 · attributed 1104.0 (**97%**) · unattributedMs 37.5.
And the top cost was one of the invisible ones — `fleetOrigin` at **619.3 ms, 54% of the
request**, with `screenRecOk` at 79.8 ms behind it. Neither had ever appeared in a breakdown.

★ THE LAW IS AST, NOT TEXT. A grep for `_t(` is satisfied by a comment mentioning it, and this
repo has been fooled that way more than once. This walks the parsed function, marks every node
inside a `_t(...)` call as covered, and requires every remaining producer call to be named in
`EXEMPT` with a reason. A producer added later is RED until somebody decides which it is.
[[source-reading-guard]] [[the-unjoined-end]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

#: Builtins and str/dict methods — not producers, and timing them would be noise.
_TRIVIAL = frozenset("""
_t get str int float bool list dict len round max min sorted isinstance getattr sum abs any all
time globals append join keys items values strip lower upper split replace format setdefault
reversed enumerate range set tuple hasattr type
""".split())

#: Producers that stay UNTIMED, each with the reason. ⚠ An exemption with no reason is how a real
#: cost gets waved through, so the test asserts every entry carries one.
EXEMPT = {
    "_journal_path":            "returns a path string; no I/O",
    "_read_pid":                "one small file read, already covered by the `pid` section",
    "_pid_alive":               "a kill(pid, 0) syscall — microseconds",
    "ui_beat_age":              "arithmetic over an in-memory timestamp",
    "_windows_ship":            "reads a small JSON only on Windows; on his Mac the branch is dead",
    "_status_timing_payload":   "this is the breakdown itself — timing it would time the meter",
    "_diablo_scene_label":      "a string lookup over a value already in hand",
    "_session_health_from_rows": "pure function over rows already read",
    "_newest_gate_count":       "pure function over rows already read",
    "_newest_completeness":     "pure function over rows already read",
    "_kai_journal_rows":        "reads the journal tail already loaded for this request",
    "_intake_lease_status":     "in-memory lease dict",
    "getsize":                  "a single os.path.getsize stat() call, microseconds",
    "isfile":                   "a single os.path.isfile stat() call, microseconds",
    # ⚠ v2956 — MEASURED BEFORE EXEMPTING, NOT ASSUMED. Walked its AST: the only calls it makes
    # are get/isinstance/max/round/str/time — no open(), no json.load, no subprocess. It reshapes
    # `_UI_BEAT["pixelBlank"]`, a dict already in memory, into the shape an outside reader needs.
    # This gate was RED ON ORIGIN for two stamps (CI run 34592434138, agent-suite) and my local
    # pre-push never ran it, so "green here" said nothing about it. [[test-venue]]
    "pixel_witness_public":     "reshapes an in-memory _UI_BEAT dict; no I/O of any kind",
    # ⚠ v2844 — EXEMPT FOR A REASON THAT IS TRUE, NOT BECAUSE THEY ARE FREE. Both touch disk.
    # They are exempt because they run in the timing EPILOGUE, after `_total` has already been
    # taken, so their cost cannot land in this request's `unattributedMs` — which is the only
    # thing this law is protecting. Each is also guarded: the load runs at most once per boot
    # (`_STATUS_TIMING["worstRequest"] or ...`), the save only when a NEW worst is recorded.
    # ⚠⚠ THE COST IS NOT ZERO, IT IS DEFERRED — it lands on the NEXT request's total, where it is
    # attributed like any other work. Writing "free" here would have been the convenient lie.
    "_status_worst_load":       "epilogue-only, after _total is taken; at most once per boot",
    "_status_worst_save":       "epilogue-only, after _total is taken; only on a new worst",
}


def _status_payload_node():
    src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
    fns = [n for n in ast.walk(ast.parse(src))
           if isinstance(n, ast.FunctionDef) and n.name == "status_payload"]
    assert len(fns) == 1, "status_payload is not a single top-level function"
    return fns[0]


def _timed_and_untimed():
    fn = _status_payload_node()
    covered = set()
    timed = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_t":
            if n.args and isinstance(n.args[0], ast.Constant):
                timed.append(n.args[0].value)
            for sub in ast.walk(n):
                covered.add(id(sub))
    untimed = {}
    for n in ast.walk(fn):
        if isinstance(n, ast.Call) and id(n) not in covered:
            f = n.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm and nm not in _TRIVIAL:
                untimed.setdefault(nm, []).append(n.lineno)
    return timed, untimed


class EveryProducerIsTimedOrExempt(unittest.TestCase):

    def test_no_producer_is_silently_untimed(self):
        _timed, untimed = _timed_and_untimed()
        stray = {k: v for k, v in untimed.items() if k not in EXEMPT}
        self.assertEqual(
            {}, stray,
            "these producers run inside status_payload and appear in NO section, so their cost "
            "lands in `unattributedMs` where nobody can act on it. Wrap each in `_t(\"name\", fn)` "
            "or add it to EXEMPT with the reason it is free: %s"
            % ", ".join("%s (line %d)" % (k, v[0]) for k, v in sorted(stray.items())))

    def test_the_instrument_actually_covers_most_of_the_function(self):
        """A census that passes with two sections is not a breakdown."""
        timed, _u = _timed_and_untimed()
        self.assertGreaterEqual(
            len(timed), 25,
            "only %d producers are timed. It was 13 when the breakdown billed 7%% of the request "
            "it measured; falling back toward that makes `unattributedMs` the answer again."
            % len(timed))

    def test_every_exemption_carries_a_reason(self):
        for name, why in EXEMPT.items():
            self.assertGreater(len(str(why)), 15,
                               "%r is exempted from the breakdown with no reason worth the name — "
                               "an unexplained exemption is how a real cost is waved through" % name)

    def test_the_exemption_list_has_no_ghosts(self):
        """An exemption for a call that no longer exists hides the fact that nothing checked it."""
        _timed, untimed = _timed_and_untimed()
        ghosts = sorted(set(EXEMPT) - set(untimed))
        self.assertEqual([], ghosts,
                         "EXEMPT names %s, which status_payload no longer calls untimed — a stale "
                         "exemption makes this list read as more considered than it is" % ghosts)

    def test_section_names_are_unique(self):
        """`_t` ACCUMULATES into one key, so a duplicated name silently merges two costs."""
        timed, _u = _timed_and_untimed()
        dupes = sorted({n for n in timed if timed.count(n) > 1})
        self.assertEqual([], dupes,
                         "section name(s) %s are used twice. `_t` adds into the existing key, so "
                         "two different producers would be reported as one line and neither could "
                         "be found from it." % dupes)


class TheBreakdownIsHonestAboutItself(unittest.TestCase):

    def test_the_gap_is_published_unclamped(self):
        """A negative gap means the sections double-counted; hiding it hides the breakage.

        ⚠⚠ THE FIRST VERSION OF THIS LAW READ THE WRONG LINE AND HEART 2.0 SAID SO. It did
        `src.find('"unattributedMs"')` — and the FIRST occurrence in control_app.py is
        `_status_timing_payload`'s UNKNOWN branch (`"unattributedMs": None`), four hundred lines
        above the epilogue that actually computes the gap. So the tamper clamped the real line and
        this inspected a different one: BLIND, green through its own defeat. A first-match search
        is a guess about which occurrence matters. [[source-window-shortcut]]
        """
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        # the COMPUTED one — the only occurrence that subtracts. Anchored on both ends.
        # ⚠⚠ v2844 — COMMENT LINES ARE NOT CODE, AND THIS LAW COUNTED THEM. A comment added
        # directly above the assignment — explaining this very rule, and naming
        # `"unattributedMs"`, `_total` and `_sum` in one sentence to do so — was counted as a
        # SECOND computing line, and the gate went red on prose. A law that reads source text must
        # decide what is source: judge CODE by code and ignore what the comments say about it.
        # [[feedback-comments-vs-code]] [[source-reading-guard]]
        lines = [l for l in src.split("\n")
                 if '"unattributedMs"' in l and "_total" in l and "_sum" in l
                 and not l.lstrip().startswith("#")]
        self.assertEqual(1, len(lines),
                         "expected exactly one line that COMPUTES unattributedMs, found %d — this "
                         "law has lost its target and would inspect the wrong one: %s"
                         % (len(lines), [l.strip()[:80] for l in lines]))
        line = lines[0]
        for clamp in ("max(0", "max(0.0", "abs("):
            self.assertNotIn(clamp, line,
                             "unattributedMs is clamped with %r — an instrument that cannot report "
                             "its own contradiction is worse than none: %s" % (clamp, line.strip()))

    def test_the_first_request_since_boot_is_unknown_not_zero(self):
        """`timing` describes the PREVIOUS request. Before one exists it must say so."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find("def _status_timing_payload")
        self.assertGreater(i, 0)
        j = src.find("\ndef ", i + 10)
        blk = src[i:j]
        self.assertIn('"state": "UNKNOWN"', blk,
                      "with no completed request the breakdown does not report UNKNOWN, so an "
                      "un-measured console is indistinguishable from a fast one")
        # ⚠⚠ COUNT, DO NOT MEMBERSHIP-TEST. There are TWO unknown returns in this function — the
        # no-request-yet branch and the exception branch — and both carry the same literal. A bare
        # `assertIn` was satisfied by whichever one the tamper had NOT touched, so it stayed green
        # through its own defeat: heart2 reported it BLIND. Both branches must say None, because a
        # 0 from either of them reads as an instant console. [[regression-guard]]
        self.assertEqual(2, blk.count('"totalMs": None'),
                         "expected BOTH unknown returns (no-request-yet, and the exception path) "
                         "to report totalMs None; found %d. A 0 from either reads as instant."
                         % blk.count('"totalMs": None'))


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "un-timing the single most expensive producer is the defect verbatim: fleetOrigin "
               "was 619ms of a 1141ms request and appeared in no section at all",
        "file": "control_app.py",
        "find": '    _fleet = _t("fleetOrigin", lambda: fleet_origin_status(force_fetch=False))',
        "replace": '    _fleet = fleet_origin_status(force_fetch=False)',
        "matches": 1,
    },
    {
        "why": "clamping the gap to zero lets the sections double-count without the instrument "
               "ever admitting it",
        "file": "control_app.py",
        "find": '            "unattributedMs": round(_total - _sum, 1),',
        "replace": '            "unattributedMs": max(0.0, round(_total - _sum, 1)),',
        "matches": 1,
    },
    {
        "why": "returning 0 instead of None before any request has completed makes an unmeasured "
               "console read as an instant one",
        "file": "control_app.py",
        "find": '                    "totalMs": None, "sections": None, "unattributedMs": None}\n'
                '        return {',
        "replace": '                    "totalMs": 0, "sections": None, "unattributedMs": None}\n'
                   '        return {',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
