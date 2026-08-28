#!/usr/bin/env python3
"""RUN THE SUITE AS A CI RUNNER SEES IT — no board, no footage, none of his history.

⚠ WHY THIS EXISTS. On 2026-08-28 the agent-tests workflow was found RED FOR TEN CONSECUTIVE RUNS,
since v2200, over a day and roughly thirty-five versions. Every one of those ships was green on his
Mac. Two tests in TestV2080TheExtractPruneCycleIsClosed asserted that the retention cycle DELETES,
and v2167 had made the deleter refuse on any board world that is not CONFIRMED. His board has been
recorded; a GitHub runner's never has. So the refusal was correct, the tests were wrong, and the
signal was invisible from here.

A gate that is always red carries exactly as much information as one that is always green, and both
train you to stop reading it. That is the failure this file is against.

WHAT IT DOES: neutralises the things a runner does not have, then runs the suite and reports which
tests depend on his machine. It does NOT modify any test — it only reveals.

⚠ IT IS NOT A REPLACEMENT FOR CI. It stubs the host dependencies we KNOW about. A test that leans on
something not listed in HOST_STUBS will still pass here and fail there — so a green run of this is
"none of the KNOWN host traps", never "CI will pass". Saying otherwise would make this the very kind
of over-claiming gate it exists to catch. [[unknown-stays-unknown]]
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

# Each entry: (module, attribute, value a RUNNER would really see, why).
# Add to this list whenever CI disagrees with this Mac — the list IS the record of what his machine
# silently provides.
HOST_STUBS = (
    ("control_app", "board_identity_drift",
     lambda: {"state": "unknown", "why": "the board's world has never been recorded"},
     "a runner has never opened his board, so no world can be confirmed (v2167 refuses on this)"),
)


def apply_stubs(verbose=True):
    """Bind every host stub. -> [(name, ok, why)]"""
    sys.path.insert(0, HERE)
    out = []
    for mod_name, attr, val, why in HOST_STUBS:
        try:
            mod = __import__(mod_name)
        except Exception as e:
            out.append((("%s.%s" % (mod_name, attr)), False,
                        "module did not import: %s" % str(e)[:70]))
            continue
        if not hasattr(mod, attr):
            # ⚠ A STUB WITH NO TARGET IS A GATE MEASURING NOTHING. If the attribute is renamed this
            # must be loud, or the simulation silently stops simulating.
            out.append((("%s.%s" % (mod_name, attr)), False,
                        "attribute no longer exists — this stub is inert and the simulation is "
                        "weaker than it claims"))
            continue
        setattr(mod, attr, val)
        out.append((("%s.%s" % (mod_name, attr)), True, why))
    if verbose:
        for name, ok, why in out:
            print("  %s %-38s %s" % ("✓" if ok else "✗", name, why[:88]))
    return out



def _without_tests_of(suite, stubbed, module):
    """Drop tests whose own body calls a stubbed name. -> (suite, [dropped names])

    Read from the SOURCE of each test, not from its name — a name is a guess about what a test does
    and this decides whether it runs at all.
    """
    import inspect
    import re as _re
    keep, dropped = [], []

    def walk(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                walk(t)
                continue
            try:
                src = inspect.getsource(getattr(t, t._testMethodName))
            except Exception:
                src = ""
            # ⚠ TWO FIXES BROKE EACH OTHER, AND THIS IS THE JOIN. Mentioning a stubbed name is not
            # the same as depending on the stub:
            #
            #   a test that ASSERTS what board_identity_drift returns  -> its subject is gone, drop it
            #   a test that PATCHES board_identity_drift for a scenario -> its own patch wins over
            #                                                             mine, so the stub is inert
            #                                                             and it MUST still run
            #
            # The first cut dropped both. Adding the patch to the two tests whose CI failure started
            # all of this therefore made the simulator stop checking exactly those two — coverage
            # shrinking precisely where the defect had been. [[two-fixes-broke-each-other]]
            mentions = [a for a in stubbed if _re.search(r"\b%s\b" % _re.escape(a), src)]
            patches = [a for a in mentions
                       if _re.search(r"patch\.object\([^)]*\b%s\b" % _re.escape(a), src)
                       or _re.search(r"patch\([^)]*\b%s\b" % _re.escape(a), src)]
            if mentions and not patches:
                dropped.append(t._testMethodName)
            else:
                keep.append(t)

    walk(suite)
    out = unittest.TestSuite()
    for t in keep:
        out.addTest(t)
    return out, dropped


def main(argv=None):
    argv = list(argv or [])
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    print("CI SIMULATION — the suite as a runner sees it\n")
    stubs = apply_stubs()
    inert = [n for n, ok, _w in stubs if not ok]
    if inert:
        print("\n\U0001f534 %d stub(s) could not bind, so this run simulates LESS than it says: %s"
              % (len(inert), ", ".join(inert)))
        return 2
    os.chdir(HERE)
    sys.path.insert(0, ".")
    import test_control
    which = argv[0] if argv else None
    loader = unittest.TestLoader()
    suite = (loader.loadTestsFromName(which, test_control) if which
             else loader.loadTestsFromModule(test_control))
    # ⚠ A TEST OF THE STUBBED FUNCTION IS NOT A TEST THAT DEPENDS ON HIS MACHINE, and the first cut
    # of this file reported four of them as host-dependent. They call `board_identity_drift`
    # directly to assert what it returns; replacing it removes their subject, so they fail for a
    # reason that has nothing to do with CI. A simulator that cries wolf gets ignored exactly like
    # the permanently-red gate it exists to replace — which would make this file the defect it was
    # written against. Drop them from the run and SAY how many, because silently excluding tests is
    # how a sample turns into a verdict. [[regression-guard]]
    stubbed = {attr for _m, attr, _v, _w in HOST_STUBS}
    suite, dropped = _without_tests_of(suite, stubbed, test_control)
    if dropped:
        print("  \u2139 %d test(s) excluded because they TEST a stubbed function rather than "
              "depend on it:" % len(dropped))
        for d in sorted(dropped)[:8]:
            print("      %s" % d)
    print()
    r = unittest.TextTestRunner(verbosity=1).run(suite)
    bad = [t.id().split(".")[-1] for t, _ in list(r.failures) + list(r.errors)]
    print()
    if bad:
        print("\U0001f534 %d test(s) depend on something only HIS machine has:" % len(bad))
        for b in bad[:20]:
            print("     %s" % b)
        return 1
    print("\U0001f7e2 no KNOWN host dependency in %d test(s)." % r.testsRun)
    print("   That is not the same as \"CI will pass\" — only the stubs above were neutralised.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
