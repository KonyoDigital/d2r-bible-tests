"""v1711 — THE SWEEP MUST NOT SEAL A REEL IT NEVER READ.

`chronicle_swept.json` is the retro sweep's memory: any reel named in it is hidden from every
future sweep via `skip_reels`, because a sealed reel never changes and re-reading one costs a
subscription call per still-run. That optimisation is correct — but only for reels that were
actually read.

The seal loop in control_app carried the comment "remember ONLY the reels this run actually read.
A reel that errored or was skipped must stay unread, or one bad run would permanently hide footage
from every future sweep" — and then excluded exactly two cases (already-swept, unnamed) and sealed
everything else. A reel returning {"classified": 0, "pages": [], "note": "no-index"} — zero work
done — was written into the memory and hidden forever. Recovery costs a `force` run over the whole
history.

The damage lands on the FIRST press: chronicle_swept.json did not exist on this machine, so there
was no prior memory to reveal the behaviour. A countdown, not debt.

These tests exercise the REAL seal rule against real stat shapes from chronicle_retro.
"""
import os
import sys
import textwrap
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable  # noqa: E402 — needs HERE on sys.path first

enable()   # these messages carry em-dashes; a non-UTF-8 console must not crash while REPORTING


def _seal_rule():
    """The seal loop's SOURCE, lifted out of control_app so the tests grade the SHIPPED logic.

    Extracted and EXECUTED rather than reimplemented. A hand-copied predicate keeps passing after
    someone widens the real one — which is exactly how the original comment came to describe an
    intent the code did not implement. Proven by red-proof: deleting the did_read check from
    control_app.py turns these tests red, which a private copy could never do."""
    src = open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
    lines = src.split("\n")
    for i, ln in enumerate(lines):
        if ln.strip() == 'for st in res["reels"]:':
            base = len(ln) - len(ln.lstrip())
            block = [ln]
            for nxt in lines[i + 1:]:
                if nxt.strip() and (len(nxt) - len(nxt.lstrip())) <= base:
                    break
                block.append(nxt)
            return textwrap.dedent("\n".join(block))
    raise AssertionError("the seal loop is gone from control_app.py — this guard is measuring "
                         "nothing and must not report OK")


def run_seal(stats, swept=None, throttled=0, capped=0):
    """Run the REAL loop over `stats` and return the memory it produced.

    v1774 — `throttled` is the count of reads the throttle refused during that sweep. The loop reads
    it, so this harness has to supply it or the extraction stops compiling; passing it also lets the
    throttle case be tested through the SHIPPED code rather than a copy of it."""
    # v1839 — the loop stamps each seal with the READER that made it (v1830), so the namespace has
    # to supply `_tv` or the extraction stops compiling. That is the harness paying its way for
    # running the SHIPPED code instead of a copy: this guard went red the moment the seal gained a
    # field, which is exactly what it is for — and it stayed red for nine versions because
    # run_gates.py runs it and the pre-push hook does not.
    class _TvStub:
        PROMPT_VER = "p-test"
        VERSION = "v-test"

    ns = {"res": {"reels": list(stats)}, "swept": {} if swept is None else swept, "time": time,
          "_throttled": [int(throttled)], "_capped": [int(capped)], "_tv": _TvStub,
          "_tick": lambda **kw: None, "print": lambda *a, **k: None}
    exec(compile(_seal_rule(), "<control_app seal loop>", "exec"), ns)
    return ns["swept"]


class TheSealOnlyRemembersWhatWasRead(unittest.TestCase):
    def setUp(self):
        self.body = _seal_rule()

    def _seal(self, st):
        """Did the SHIPPED loop seal this reel?"""
        return ("reel_" + str(st.get("reel"))) in run_seal([st])

    def test_a_CAPPED_sweep_seals_NOTHING_either(self):
        """v1778 — the same loss through the other door, found by code review of v1777.

        _classify_one ticks classified=1 whatever happens, and this loop reads "classified > 0 with
        pages == 0" as "the classifier looked and correctly found no Chronicle page". A subscription
        cap counterfeits that shape exactly: the classifier was never asked. v1774 guarded the
        throttle and the cap had nothing, so a cap opening mid-sweep sealed every remaining reel at
        full price having read nothing - and a sealed reel is never looked at again."""
        st = {"reel": "s_capped", "runs": 3, "candidates": 3, "classified": 3, "pages": 0,
              "note": None}
        self.assertIn("reel_s_capped", run_seal([st]),
                      "a clean classifier-only run must still seal")
        self.assertEqual(run_seal([st], capped=1), {},
                         "a sweep the subscription cap refused sealed a reel it never read")

    def test_a_throttled_sweep_seals_NOTHING(self):
        """v1774 — the seal rule reasons that "classified > 0 with pages == 0 IS a legitimate seal:
        the cheap classifier looked at every frame and correctly found no Chronicle page". A throttle
        counterfeits exactly that shape — the classifier was never asked, the reader answered
        scene='gameplay' with no names, and the run finished clean. Measured on his console: a page
        that had read chronicle/uniques with 6 names came back gameplay/0 while "throttle cascade
        detected" printed, and a full sweep returned 105 classifies, 4 pages, 0 names.

        Sealing on that is how footage is lost at full price, and his recordings cannot be re-made."""
        st = {"reel": "s_throttled", "runs": 3, "candidates": 3, "classified": 3, "pages": 0,
              "note": None}
        self.assertIn("reel_s_throttled", run_seal([st], throttled=0),
                      "a clean classifier-only run must still seal, or nothing ever gets cheaper")
        self.assertEqual(run_seal([st], throttled=1), {},
                         "a sweep that hit the throttle sealed a reel it never actually read")

    def test_the_shipped_loop_actually_checks_that_something_was_read(self):
        # guards the predicate above against drifting from the code it claims to mirror
        self.assertIn("did_read", self.body,
                      "the seal loop no longer tests whether the reel was read — the comment above "
                      "it would be describing an intent the code does not implement, again")
        self.assertIn("no-index", self.body)

    def test_a_reel_that_read_NOTHING_is_never_sealed(self):
        # chronicle_retro.py:433 — the exact shape a reel with an unloadable index returns
        st = {"reel": "s_1", "runs": 0, "candidates": 0, "classified": 0, "pages": 0,
              "note": "no-index"}
        self.assertFalse(self._seal(st), "a reel nothing was read from was hidden from every "
                                         "future sweep; only a full `force` run could recover it")

    def test_a_zero_work_reel_with_no_note_is_also_not_sealed(self):
        self.assertFalse(self._seal({"reel": "s_2", "classified": 0, "pages": 0}))

    def test_a_classifier_that_found_no_pages_IS_sealed(self):
        # the legitimate seal: every frame was looked at and honestly held no Chronicle page.
        # Paying the classifier again returns the same answer, so this must NOT be re-read.
        self.assertTrue(self._seal({"reel": "s_3", "classified": 7, "pages": 0}),
                        "refusing this seal would make the memory useless and re-bill every run")

    def test_a_reel_that_read_pages_is_sealed(self):
        self.assertTrue(self._seal({"reel": "s_4", "classified": 3, "pages": 2}))

    def test_an_already_swept_reel_is_not_re_recorded(self):
        self.assertFalse(self._seal({"reel": "s_5", "classified": 0, "pages": 0,
                                     "note": "already-swept"}))

    def test_the_key_written_is_the_key_skip_reels_looks_up(self):
        """The memory only works if the key it writes equals the basename sweep_hist compares.

        control_app writes "reel_" + st["reel"]; sweep_hist tests os.path.basename(reel_dir)
        against the skip set. st["reel"] is the index's sessionId (chronicle_retro.py:434), and
        reel dirs are named reel_<sessionId>, so the two agree — but only while sessionId is
        present. A mismatch would be invisible: every reel would simply be re-read at full price
        forever, looking exactly like a memory that was never populated."""
        import chronicle_retro as cr
        hist = os.path.join(HERE, "frames", "hist")
        if not os.path.isdir(hist):
            self.skipTest("no hist dir on this machine")
        reels = cr.reel_dirs(hist)
        if not reels:
            self.skipTest("no sealed reels on this machine")
        checked = 0
        for p in reels:
            idx = cr.load_index(p) or {}
            sid = idx.get("sessionId")
            if not sid:
                continue                     # the latent case: a rebuilt index carries no sessionId
            self.assertEqual("reel_" + str(sid), os.path.basename(p),
                             "the sweep would write a key skip_reels can never match, so every "
                             "reel would be re-read at full price on every run")
            checked += 1
        self.assertGreater(checked, 0, "no reel carried a sessionId — the key agreement above is "
                                       "unproven rather than passing")


if __name__ == "__main__":
    unittest.main()
