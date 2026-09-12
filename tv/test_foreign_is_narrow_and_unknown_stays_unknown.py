# -*- coding: utf-8 -*-
"""TWO THREADS WERE UNKNOWN FOREVER, AND THE FIX FOR THAT IS THE MOST DANGEROUS KIND.

Measured on his live console, 2026-09-12: `vessels 22 · WATCHED 20 · DARK 0 · UNKNOWN 2`. The two
were `serve_forever` and `wait` — because `census()` reduces `threading.Thread(target=srv.serve_forever)`
to the bare name `serve_forever`, and `classify()` then looks for a `def serve_forever` in
control_app.py, finds none, and answers UNKNOWN. It was right to: UNKNOWN means "I could not look".

But nobody could EVER look, because those names are methods on stdlib objects and no definition of
them exists in this repo at all. "I could not find the body" and "this code is not ours" are
different facts, and only the first is an unknown. So v3034 added the kind FOREIGN.

⚠⚠ AND THAT IS EXACTLY THE CHANGE THAT CAN GO BAD SILENTLY. A classification that turns UNKNOWN
into not-a-vessel is a machine for making a census look complete. Loosened by one condition it
stops describing stdlib methods and starts absolving real lanes — and the result reads as
`UNKNOWN 0`, which is the number a finished job produces. There is no alarm shaped like a census
that got quieter.

So this law does not check that the two known names are FOREIGN. It checks that FOREIGN CANNOT
WIDEN, by asserting the two ways it could:

  · a target with NO receiver stays UNKNOWN, however unresolvable it is;
  · a target whose method IS defined somewhere in this package stays UNKNOWN, even though it is
    reached through a receiver — because that is a lane we own and must judge on its merits.

[[unknown-stays-unknown]] [[regression-guard]] [[feedback-suspect-the-instrument]]
"""
import io
import os
import sys
import unittest

HERE_ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE_)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import lane_census as LC  # noqa: E402


def _kinds(src):
    """-> {fn: kind} for a synthetic source."""
    return dict((r["fn"], r["kind"]) for r in LC.census(src=src))


class TestForeignIsNarrowAndUnknownStaysUnknown(unittest.TestCase):

    def test_a_receiverless_mystery_target_stays_unknown(self):
        """No dot, so nothing was ever reached through another object — UNKNOWN, not FOREIGN."""
        src = "import threading\nthreading.Thread(target=a_name_defined_nowhere_at_all).start()\n"
        k = _kinds(src)
        self.assertIn("a_name_defined_nowhere_at_all", k,
                      "the census did not see the thread at all — the reader is broken, and a "
                      "law that parses nothing passes everything")
        self.assertEqual(
            k["a_name_defined_nowhere_at_all"], "UNKNOWN",
            "a bare unresolvable target was classified %r. FOREIGN requires a RECEIVER; without "
            "one there is no evidence the code lives elsewhere, only that it could not be found."
            % k["a_name_defined_nowhere_at_all"])

    def test_a_method_this_package_defines_stays_unknown_even_through_a_receiver(self):
        """THE LAUNDERING GUARD. `classify` is defined in lane_census.py, so a thread started as
        `x.classify` is OUR lane reached through an object — it must never be waved through."""
        src = "import threading\nthreading.Thread(target=holder.classify).start()\n"
        k = _kinds(src)
        self.assertIn("classify", k, "the census did not see the dotted thread target")
        self.assertNotEqual(
            k["classify"], "FOREIGN",
            "a target whose name IS defined in this package was classified FOREIGN. That is the "
            "failure this law exists for: FOREIGN would then absolve real lanes and the census "
            "would read UNKNOWN 0 while a lane of ours went unwatched.")

    def test_a_stdlib_method_through_a_receiver_is_foreign(self):
        """The capability itself — without this the other two pass trivially on a dead feature."""
        src = "import threading\nthreading.Thread(target=srv.serve_forever).start()\n"
        k = _kinds(src)
        self.assertEqual(k.get("serve_forever"), "FOREIGN",
                         "serve_forever through a receiver should be FOREIGN, got %r — the "
                         "distinction this law guards no longer exists" % k.get("serve_forever"))

    def test_the_live_console_has_no_unclassified_thread(self):
        """His actual console, not a fixture. This is the reading he acts on."""
        rows = LC.census()
        unknown = [r["fn"] for r in rows if r["kind"] == "UNKNOWN"]
        self.assertEqual(unknown, [],
                         "%d thread target(s) in the real console are UNCLASSIFIED: %s. Each is a "
                         "thread nobody has established anything about." % (len(unknown), unknown))
        self.assertGreater(len(rows), 25,
                           "only %d thread target(s) parsed out of the console — the census "
                           "stopped matching the file it reads, so its zero above means nothing"
                           % len(rows))


# ⚠ Each proof deletes ONE of the three conditions that make FOREIGN narrow. A proof that merely
# broke the feature would be satisfied by the capability test alone; these break the NARROWNESS,
# which is what the law is actually for.
RED_PROOF = [
    {
        "why": "drops the receiver requirement, so any unresolvable bare name becomes FOREIGN and "
               "a thread nobody can find is reported as not-our-code",
        "file": "lane_census.py",
        "find": 'if k == "UNKNOWN" and name in dotted and not _defined_anywhere(name):',
        "replace": 'if k == "UNKNOWN" and not _defined_anywhere(name):',
        "matches": 1,
    },
    {
        "why": "drops the defined-anywhere check, so a lane THIS PACKAGE defines, started through "
               "a receiver, is absolved as foreign code",
        "file": "lane_census.py",
        "find": 'if k == "UNKNOWN" and name in dotted and not _defined_anywhere(name):',
        "replace": 'if k == "UNKNOWN" and name in dotted:',
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
