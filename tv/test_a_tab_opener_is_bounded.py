# -*- coding: utf-8 -*-
"""A TAB OPENER IS BOUNDED — every urlopen in roster_sync carries a deadline, and it really expires.

`fetch_via_cdp` opens a scratch Chrome tab before it can ask bible.html anything:

    req = urllib.request.Request("http://127.0.0.1:%d/json/new?about:blank" % port, method="PUT")
    tgt = json.load(urllib.request.urlopen(req))          # <- NO BOUND
    ws  = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=timeout)

**The socket on the very next line was bounded and this one was not**, with the value already in
scope on the same function's signature. urllib's default is `socket._GLOBAL_DEFAULT_TIMEOUT`, which
means *block*, and nothing in this tree ever calls `socket.setdefaulttimeout` (measured: zero
matches across tv/ and hooks/). So a Chrome that completes the TCP handshake and then never answers
`/json/new` — wedged, mid-shutdown, or a port that belongs to something else entirely — parks the
caller forever with no exception, no log line and no ceiling. That is the worst shape a failure can
take here: not a red gate, a silent one.

**THIS IS THE THIRD SITE OF ONE CLASS.** v3436 fixed `tv/render_check.py:2477` the same way. A
defect that lands three times is not three mistakes, it is a missing law, so the law is written
here rather than the fix being made quietly a third time.

WHAT THIS GATE ASSERTS, AND WHY IT IS SHAPED THIS WAY
────────────────────────────────────────────────────
1. **AST, never grep.** The subject is parsed. A text search for "urlopen" reads the prose in this
    very docstring, and the paragraph above would satisfy any regex written for the law.
    [[source-reading-guard]]
2. **DOTTED names, resolved through the imports.** `request.urlopen` is compared, never the bare
    attribute `urlopen` — `subprocess.run` and `_gq.run` are both called `run`, and a guard that
    matches the leaf admits every namesake. The alias map means `import urllib.request as ur`,
    `from urllib import request` and `from urllib.request import urlopen` are all still the
    subject.
3. **The positional slot comes from `inspect.signature`, not from counting on my fingers.** It is
    tempting to call "the second argument" the timeout. It is not: the signature is
    `urlopen(url, data, timeout, ...)`, so the second positional is **data** and a bound passed
    there would be silently wrong. The gate asks the interpreter where `timeout` lives, and if the
    signature ever stops offering a positional slot it says UNKNOWN rather than guessing.
4. **A zero needs a denominator.** "No unbounded calls" over zero parsed calls is not a pass, it is
    a gate that has lost its subject — so the number of urlopen calls found is asserted to be at
    least one, and printed. [[zero-needs-a-denominator]]
5. **UNKNOWN is its own state.** `timeout=None` is a bound in shape and *forever* in fact, so it is
    counted UNBOUNDED. A call whose arguments arrive through `*args`/`**kwargs` cannot be judged
    from source at all, so it is UNKNOWN and reported as unestablished — never quietly passed.
    [[unknown-stays-unknown]]
6. **The behaviour is DRIVEN, not argued.** A source law proves the bytes say `timeout=`; it cannot
    prove the deadline ever fires. So one case stands up a loopback socket that accepts the
    connection and never answers — the exact failure — and requires `fetch_via_cdp` to come back
    within a ceiling. It proves its own premise first (connect succeeds, read times out), because
    a case that silently failed to reproduce the hang would pass for the wrong reason and could not
    tell a working bound from an unreachable line. [[a-probe-licenses-only-what-it-tested]]
7. **A CASE THAT CANNOT REACH THE LINE IS UNMEASURED, NOT PASSED.** Measured 2026-09-23 (#185):
    `fetch_via_cdp` runs `import websocket` — a THIRD-PARTY module — on the line *before* the
    urlopen. With websocket-client absent, that ImportError satisfies BOTH of the driven case's
    assertions (it raised; it was fast), so the case went **GREEN in 0.75 s over a deliberately
    UNBOUNDED opener** that the very same case failed in 12.78 s with the module installed. It
    proved its SOCKET premise and never its IMPORT premise. So the import premise is asserted
    FIRST, and when it does not hold the case reports **UNMEASURED** and this file exits 77 — the
    gate set's "could not run" code. `test_a_tab_opener_is_bounded` declares `skip_ok=()`, so
    run_gates counts an undeclared skip with the FAILURES rather than printing a tick beside it.
    **"I could not run" must never read the same as "I ran and it was fine."**
    [[unknown-stays-unknown]] [[a-probe-licenses-only-what-it-tested]]
"""
import ast
import inspect
import io
import os
import socket
import sys
import threading
import time
import unittest
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ MUST come after the sys.path insert above — console_safe lives in tv/. This file prints ⚠/✅
# and his Windows console is cp1255, where an emoji raises UnicodeEncodeError WHILE THE GATE IS
# REPORTING — so a clean tree exits non-zero for a reason that has nothing to do with the check.
# The pre-push gate caught this one and named the file and the fix, which is what a good gate does.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SUBJECT = "roster_sync.py"
TARGET = "urllib.request.urlopen"
SKIP_EXIT = 77          # "this could not run" — must match SKIP_EXIT in tv/run_gates.py


def websocket_premise():
    """Can the `import websocket` that runs BEFORE the urlopen actually succeed? -> (bool, str)

    `fetch_via_cdp` opens with three imports and the third is third-party:

        import time
        import urllib.request
        import websocket          # <- roster_sync.py:132, ABOVE the urlopen this gate judges

    So an absent websocket-client raises ImportError from a line the subject reaches FIRST, and to
    a case that asserts only "it raised, and it was quick" that raise is indistinguishable from the
    deadline it exists to measure. Asked of the interpreter, never assumed: a gate may not decide
    it has a dependency. [[a-probe-licenses-only-what-it-tested]]
    """
    try:
        import websocket
    except BaseException as exc:            # noqa: BLE001 — any failure to import is absence
        return False, "`import websocket` raised %s: %s" % (type(exc).__name__, exc)
    # ⚠ AND THAT IS THE WHOLE PREMISE — deliberately NOT "is this really websocket-client".
    # The first cut also demanded `create_connection`, and that is a guard that cries wolf: a
    # NAMESAKE module (the name is taken by other packages) leaves `import websocket` succeeding,
    # so the subject reaches the urlopen and this case measures it perfectly well. MEASURED with a
    # stub module bound to the name: against an UNBOUNDED source the case still failed in 12.775s,
    # and against the bounded one it passed in 1.77s. Refusing that run as UNMEASURED would have
    # been a red gate over a working measurement, and a row that cries wolf gets silenced.
    # The premise this case needs is exactly "the import above the urlopen does not raise".
    return True, "importable: %s %s" % (getattr(websocket, "__name__", "websocket"),
                                        getattr(websocket, "__file__", "?"))


# ── the analyser ─────────────────────────────────────────────────────────────────────────────
def _dotted(node):
    """The full dotted spelling of a call target, or None if it is not a plain name/attribute."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def alias_map(tree):
    """Every name this module binds to a module or function, mapped to its canonical dotted path.

    Function-local imports count — `fetch_via_cdp` imports `urllib.request` inside its own body,
    which a module-header-only reader would miss entirely. Relative imports are skipped: they can
    never name urllib.
    """
    m = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    m[a.asname] = a.name                      # import urllib.request as ur
                else:
                    head = a.name.split(".")[0]               # import urllib.request  -> "urllib"
                    m[head] = head
        elif isinstance(node, ast.ImportFrom):
            if node.level:                                    # relative — not urllib
                continue
            base = node.module or ""
            for a in node.names:
                m[a.asname or a.name] = (base + "." + a.name) if base else a.name
    return m


def resolve(dotted, aliases):
    """`request.urlopen` + the import map -> `urllib.request.urlopen`. -> str|None"""
    if not dotted:
        return None
    head, _, rest = dotted.partition(".")
    base = aliases.get(head)
    if base is None:
        return None
    return base + ("." + rest if rest else "")


def timeout_position():
    """Where `timeout` sits positionally in urlopen's REAL signature. -> int|None (None = UNKNOWN)

    Asked of the interpreter rather than hardcoded, because the obvious guess is wrong: `timeout`
    is the THIRD parameter (index 2); the second is `data`. Measured on this interpreter at run
    time, so a stdlib that moves it cannot leave the law quietly pointing at the wrong slot.
    """
    try:
        params = list(inspect.signature(urllib.request.urlopen).parameters.items())
    except (TypeError, ValueError):
        return None
    for i, (name, p) in enumerate(params):
        if name == "timeout":
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD):
                return i
            return None                                        # keyword-only: no positional slot
    return None


def classify(call, tpos):
    """BOUND | UNBOUNDED | UNKNOWN for one urlopen call node."""
    for kw in call.keywords:
        if kw.arg == "timeout":
            if isinstance(kw.value, ast.Constant) and kw.value.value is None:
                return "UNBOUNDED"          # `timeout=None` is spelled like a bound and is not one
            return "BOUND"
    if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None
                                                                 for k in call.keywords):
        return "UNKNOWN"                    # *args/**kwargs: nobody can say from source
    if tpos is None:
        return "UNKNOWN" if call.args[1:] else "UNBOUNDED"
    if len(call.args) > tpos:
        a = call.args[tpos]
        if isinstance(a, ast.Constant) and a.value is None:
            return "UNBOUNDED"
        return "BOUND"
    return "UNBOUNDED"


def urlopen_calls(src, filename="<src>"):
    """Every urllib.request.urlopen call in `src`. -> [(lineno, state, source-ish)]"""
    tree = ast.parse(src, filename=filename)
    aliases = alias_map(tree)
    tpos = timeout_position()
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if resolve(_dotted(node.func), aliases) != TARGET:
            continue
        out.append((node.lineno, classify(node, tpos), _dotted(node.func)))
    return out


def _subject_src():
    with io.open(os.path.join(HERE, SUBJECT), encoding="utf-8", errors="replace") as fh:
        return fh.read()


class TestATabOpenerIsBounded(unittest.TestCase):

    # ── the analyser can say NO — otherwise every green below is vacuous ─────────────────────
    def test_BASELINE_the_analyser_actually_distinguishes_bound_from_unbounded(self):
        """A law whose instrument answers BOUND to everything is a law that never fires.

        Six sabotages in one day were green because the SABOTAGE was inert, not because the guard
        was blind; the cheapest defence is making the instrument prove, on synthetic source, that
        its output varies at all. [[sabotage-is-usually-the-wrong-one]]
        """
        cases = [
            ("import urllib.request\nurllib.request.urlopen(r)\n", "UNBOUNDED"),
            ("import urllib.request\nurllib.request.urlopen(r, timeout=5)\n", "BOUND"),
            ("import urllib.request\nurllib.request.urlopen(r, timeout=None)\n", "UNBOUNDED"),
            ("import urllib.request as ur\nur.urlopen(r)\n", "UNBOUNDED"),
            ("from urllib import request\nrequest.urlopen(r)\n", "UNBOUNDED"),
            ("from urllib.request import urlopen\nurlopen(r)\n", "UNBOUNDED"),
            ("from urllib.request import urlopen as uo\nuo(r, timeout=2)\n", "BOUND"),
            ("import urllib.request\nurllib.request.urlopen(r, None, 9)\n", "BOUND"),
            ("import urllib.request\nurllib.request.urlopen(r, **kw)\n", "UNKNOWN"),
        ]
        for src, want in cases:
            found = urlopen_calls(src)
            self.assertEqual(len(found), 1, "the analyser did not find the one call in %r" % src)
            self.assertEqual(found[0][1], want,
                             "analyser said %s, expected %s, for: %r" % (found[0][1], want, src))

    def test_BASELINE_a_namesake_urlopen_is_NOT_mistaken_for_urllibs(self):
        """[[a-widened-guard-admits-what-it-bans]] — compare the dotted name, never the leaf."""
        src = ("import requests_shim as rs\nrs.urlopen(r)\n"
               "class C:\n    def urlopen(self, u):\n        pass\nC().urlopen(r)\n")
        self.assertEqual(urlopen_calls(src), [],
                         "a foreign `urlopen` was claimed as urllib's — the guard is matching the "
                         "bare attribute, so it would also demand a timeout from things that have "
                         "no such argument")

    def test_BASELINE_the_positional_timeout_slot_is_the_one_the_stdlib_really_has(self):
        """If this ever reads 1, the law would accept `urlopen(req, 5)` — which sets **data**."""
        tpos = timeout_position()
        self.assertIsNotNone(tpos, "urlopen no longer offers `timeout` positionally on this "
                                   "interpreter; positional bounds are now UNKNOWN, and any call "
                                   "relying on one must be re-read by hand")
        self.assertEqual(tpos, 2, "timeout moved to positional slot %r — the law follows the "
                                  "signature, but a move this big wants a human look" % (tpos,))

    # ── the law ──────────────────────────────────────────────────────────────────────────────
    def test_the_subject_really_contains_urlopen_calls_to_judge(self):
        """THE DENOMINATOR. Zero calls parsed is a lost subject, not a clean bill of health."""
        found = urlopen_calls(_subject_src(), SUBJECT)
        print("\n  %s: %d urllib.request.urlopen call(s) parsed -> %s"
              % (SUBJECT, len(found), ", ".join("L%d %s" % (l, s) for l, s, _ in found) or "none"))
        self.assertGreaterEqual(len(found), 1,
                                "no urllib.request.urlopen call was parsed out of %s at all — "
                                "either the file stopped opening tabs (then retire this gate) or "
                                "the analyser has gone blind and 'no unbounded calls' below means "
                                "nothing" % SUBJECT)

    def test_EVERY_urlopen_in_the_subject_CARRIES_A_BOUND(self):
        found = urlopen_calls(_subject_src(), SUBJECT)
        bad = ["%s:%d (%s)" % (SUBJECT, ln, name) for ln, st, name in found if st == "UNBOUNDED"]
        self.assertEqual(bad, [], "unbounded urllib.request.urlopen call(s): %s — urllib blocks "
                                  "FOREVER by default and nothing here calls "
                                  "socket.setdefaulttimeout, so a Chrome that accepts the "
                                  "connection and never answers wedges the caller with no "
                                  "message. Pass the `timeout` already in scope." % ", ".join(bad))

    def test_an_unjudgeable_urlopen_is_reported_UNKNOWN_not_passed(self):
        """0 is measured-and-zero; a call nobody can read is not the same thing."""
        found = urlopen_calls(_subject_src(), SUBJECT)
        unknown = ["%s:%d" % (SUBJECT, ln) for ln, st, _ in found if st == "UNKNOWN"]
        self.assertEqual(unknown, [], "urlopen call(s) at %s pass their arguments through "
                                      "*args/**kwargs, so whether they carry a deadline CANNOT be "
                                      "established from source. That is unknown, not fine — read "
                                      "them by hand and either pin the bound at the call site or "
                                      "give this gate a way to see it." % ", ".join(unknown))

    # ── and the deadline really expires ──────────────────────────────────────────────────────
    def test_the_opener_GIVES_UP_on_a_socket_that_accepts_and_never_answers(self):
        """DRIVEN, not asserted about. [[a-law-about-a-row-must-drive-the-row]]

        A listening socket that never `accept()`s still completes the handshake out of the backlog,
        so the client connects, sends its PUT, and waits on a reply that never comes — the exact
        wedged-Chrome shape. `fetch_via_cdp` must raise inside its own timeout instead of parking.

        The hang is run on a daemon thread on purpose: without a bound, the call never returns, and
        a case that waited for it would BE the defect. The ceiling is what fails.
        """
        # ── PREMISE 1 OF 2 — THE IMPORT. Without it, every assertion below is vacuous ──────
        # fetch_via_cdp runs `import websocket` on the line ABOVE the urlopen. With the module
        # absent that ImportError satisfies "raised" AND "fast" — the two assertions at the foot
        # of this case — so an UNBOUNDED opener passed here in 0.75s while the identical source
        # failed in 12.78s with the module installed (measured, #185). A skip is not a pass, so
        # this gets its OWN state: UNMEASURED, and the runner below turns it into exit 77.
        ws_ok, ws_detail = websocket_premise()
        print("\n  import premise: %s — %s" % ("OK" if ws_ok else "UNMEASURED", ws_detail))
        if not ws_ok:
            why = ("UNMEASURED: websocket-client is not importable, so fetch_via_cdp raises "
                   "ImportError at roster_sync.py:132 — the line BEFORE the urlopen under test — "
                   "and this case cannot reach the call it is supposed to judge. Its own "
                   "assertions would be satisfied by that ImportError, i.e. it would go green "
                   "over an unbounded opener. [%s] Fix: pip install websocket-client (CI installs "
                   "it in .github/workflows/tv-tests.yml). THIS IS NOT A PASS — the file exits %d."
                   % (ws_detail, SKIP_EXIT))
            print("  \u26a0 " + why)
            self.skipTest(why)

        import roster_sync

        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(16)                       # room for the premise probe AND the subject
        port = srv.getsockname()[1]
        try:
            # ── prove the premise, or this case is measuring nothing ──────────────────────
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            probe.settimeout(3.0)
            try:
                probe.connect(("127.0.0.1", port))
                probe.sendall(b"PUT /json/new HTTP/1.1\r\nHost: x\r\n\r\n")
                probe.settimeout(0.75)
                with self.assertRaises(socket.timeout, msg=(
                        "the fixture is NOT the failure under test: this socket answered (or "
                        "refused) instead of accepting-and-going-silent, so a pass below would "
                        "say nothing about whether the opener is bounded")):
                    probe.recv(1)
            finally:
                probe.close()

            # ── now the subject, with a 1s deadline and a 12s ceiling ─────────────────────
            box = {}

            def run():
                t0 = time.time()
                try:
                    roster_sync.fetch_via_cdp(port=port, timeout=1.0)
                    box["outcome"] = ("returned", None)
                except BaseException as exc:                      # noqa: BLE001 — any raise is fine
                    box["exc_type"] = type(exc)
                    box["outcome"] = ("raised", "%s: %s" % (type(exc).__name__, exc))
                box["secs"] = time.time() - t0

            th = threading.Thread(target=run, daemon=True, name="tvd-bounded-opener-probe")
            t0 = time.time()
            th.start()
            th.join(12.0)
            waited = time.time() - t0

            self.assertIn("outcome", box,
                          "fetch_via_cdp was still inside the tab-open after %.1fs against a "
                          "Chrome that accepts the connection and never answers. That is the "
                          "unbounded urlopen: no exception, no log line, no ceiling — the caller "
                          "is simply gone." % waited)
            kind, detail = box["outcome"]
            # The same vacuity from the other side, and INDEPENDENT of the premise check above on
            # purpose — one of the two is allowed to be wrong. An ImportError coming back here can
            # only have come from the `import websocket` ABOVE the urlopen, so the call under test
            # never ran and "it raised, quickly" is a statement about nothing.
            if kind == "raised" and box.get("exc_type") is not None and issubclass(
                    box["exc_type"], ImportError):
                self.fail("fetch_via_cdp raised %s, which comes from the import block ABOVE the "
                          "urlopen (roster_sync.py:130-132) — the call under test was never "
                          "reached, so this case measured NOTHING about the bound and must not "
                          "read as a pass. Install websocket-client and run it again. (%s)"
                          % (box["exc_type"].__name__, detail))
            self.assertEqual(kind, "raised",
                             "fetch_via_cdp RETURNED from a socket that never sent a byte — the "
                             "premise of this case is broken, not the bound")
            self.assertLess(box["secs"], 10.0,
                            "the opener gave up only after %.1fs with timeout=1.0 — the deadline "
                            "reached something, but not the call that hangs (%s)"
                            % (box["secs"], detail))
        finally:
            srv.close()


RED_PROOF = [
    {
        "why": "THE UNBOUNDED TAB OPENER, RESTORED. urllib.request.urlopen with no timeout blocks "
               "FOREVER - the default is socket._GLOBAL_DEFAULT_TIMEOUT and nothing in tv/ calls "
               "socket.setdefaulttimeout - so a Chrome that completes the TCP handshake and never "
               "answers /json/new wedges fetch_via_cdp with no exception and no ceiling, while "
               "the websocket on the NEXT line was bounded all along. Third site of the class; "
               "v3436 fixed tv/render_check.py:2477 the same way.",
        "file": "roster_sync.py",
        "find": "    tgt = json.load(urllib.request.urlopen(req, timeout=timeout))",
        "replace": "    tgt = json.load(urllib.request.urlopen(req))",
        "matches": 1,
    },
    {
        "why": "A BOUND THAT IS NOT ONE. `timeout=None` is spelled exactly like a deadline and "
               "means block forever; a guard that only looks for the WORD timeout accepts it.",
        "file": "roster_sync.py",
        "find": "    tgt = json.load(urllib.request.urlopen(req, timeout=timeout))",
        "replace": "    tgt = json.load(urllib.request.urlopen(req, timeout=None))",
        "matches": 1,
    },
    {
        "why": "THE BOUND IN THE WRONG SLOT. urlopen(url, data, timeout) - the second positional "
               "is DATA, so `urlopen(req, timeout)` sets a request body and leaves the read "
               "unbounded. A law that accepted 'a positional second arg' would call this fixed.",
        "file": "roster_sync.py",
        "find": "    tgt = json.load(urllib.request.urlopen(req, timeout=timeout))",
        "replace": "    tgt = json.load(urllib.request.urlopen(req, timeout))",
        "matches": 1,
    },
]

if __name__ == "__main__":
    # THE EXIT CODE IS THE VERDICT, AND IT HAS THREE STATES. `unittest.main()` exits 0 on a run
    # whose only non-pass was a SKIP, which is precisely how "I could not measure the law" becomes
    # a green gate — the lie this file's docstring point 7 exists to forbid. 77 is the gate set's
    # "could not run" (SKIP_EXIT in tv/run_gates.py); this gate is registered with `skip_ok=()`,
    # so run_gates shows SKIP and counts it with the FAILURES rather than printing a tick.
    _res = unittest.main(verbosity=2, exit=False).result
    if not _res.wasSuccessful():
        sys.exit(1)
    if _res.skipped:
        print("\n\u26a0 UNMEASURED - %d case(s) did not run, so this gate certifies NOTHING "
              "about them. Exiting %d, never 0." % (len(_res.skipped), SKIP_EXIT))
        for _t, _why in _res.skipped:
            print("    - %s\n      %s" % (_t, _why))
        sys.exit(SKIP_EXIT)
    sys.exit(0)
