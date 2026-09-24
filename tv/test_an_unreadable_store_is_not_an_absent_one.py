# -*- coding: utf-8 -*-
"""v3355 (#108) — AN UNREADABLE STORE IS NOT AN ABSENT ONE, AND THE ERRNO IS THE WHOLE DIFFERENCE.

v3325 was titled *"a store is never written over an unread one"* and it put the rule in three
loaders. All three wrote it as:

    except IOError:   return {}     # absent: nothing marked yet, and that IS a measurement
    except Exception: return None   # malformed/unreadable: UNKNOWN

**In Python 3 `IOError is OSError`** — measured True — and PermissionError, IsADirectoryError and
the EMFILE family are all subclasses. So an EXISTING, GOOD store that merely could not be READ took
the ABSENT arm. The second arm's comment says "malformed/unreadable" and only MALFORMED ever
reached it: a JSON error is a ValueError, an unreadable FILE is an OSError.

MEASURED 2026-09-19 on a real file holding watermarks 179, 180 and 230 at mode 000:

    _marks()                 -> {}
    what `--mark` then wrote -> {"999": 1}
    what it replaced         -> three watermarks, gone

=== ⚠⚠ THE PROSE ABOVE EACH SITE ALREADY DESCRIBED THE DEFECT ===
`_shadow_watch_stored`'s comment, written in v3325, says in as many words: *"ABSENT vs UNREADABLE,
and here it is destructive. `_shadow_watch_note` does `cur = _shadow_watch_stored(); cur.update(kw)`
and writes `cur` back wholesale, so returning {} for a corrupt file REPLACES the store with just
the new keys."* The code directly beneath it did exactly that. A comment stating a rule the
adjacent code does not implement is worse than no comment — it makes the next reader believe the
case is handled. [[measured-true-read-wrong]]

=== THE CLASS WAS SWEPT, AND THE UNSCOPED NUMBER IS ON THE RECORD ===
127 handlers in tv/ catch IOError/OSError broadly. THREE are this defect — the ones where a falsy
value is handed to a caller that writes the whole store back. The rest return None, raise, or say
why. And the right idiom was already in the same file three times: control_app.py:25963, :27390
and :16856 all use `except FileNotFoundError`. [[sweep-dont-ask]] §1

⚠ CI HAD BEEN SHOUTING FOR TEN RUNS. `tv/swallow_census.py --check` (Routine M) reported RANK 1 at
76 against a baseline of 74 on every run since at least v3344, and nothing surfaced it, because the
pre-push derives its gates from CHANGED TEST FILES and never runs the full set. A red nobody reads
is the same as a green. [[regression-guard]] §2
"""
import io
import json
import os
import stat
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()


def _unreadable(payload):
    """A file that EXISTS, holds real data, and cannot be opened. -> path"""
    d = tempfile.mkdtemp()
    p = os.path.join(d, "store.json")
    io.open(p, "w", encoding="utf-8").write(json.dumps(payload))
    os.chmod(p, 0o000)
    return p


def _absent():
    return os.path.join(tempfile.mkdtemp(), "never-written.json")


class ThePremise(unittest.TestCase):
    """⚠ The whole argument rests on one fact about this interpreter. Pin it, or a future Python
    that separates the two would silently make this law reasoning about nothing."""

    def test_IOError_really_is_OSError_here(self):
        self.assertIs(IOError, OSError,
                      "IOError and OSError are distinct on this interpreter, so `except IOError` "
                      "no longer catches PermissionError and this law's premise has changed")
        for cls in (FileNotFoundError, PermissionError, IsADirectoryError):
            self.assertTrue(issubclass(cls, IOError),
                            "%s is not an IOError here" % cls.__name__)

    def test_running_as_root_would_make_every_case_below_vacuous(self):
        """⚠ A skip is not a pass. Root can read a mode-000 file, so the fixtures would not be
        unreadable at all and every assertion would measure nothing. [[regression-guard]] §2"""
        p = _unreadable({"x": 1})
        try:
            io.open(p, encoding="utf-8").read()
            self.fail("a mode-000 file opened successfully — this venue cannot make a file "
                      "unreadable (running as root?), so the cases below prove nothing and must "
                      "not be read as passing")
        except OSError:
            pass


class TheThreeLoaders(unittest.TestCase):
    """⚠⚠ THE CASE, three times. The three stores v3325 was written about."""

    def _probe(self, loader, point_at, good):
        p = _unreadable(good)
        point_at(p)
        unreadable = loader()
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
        a = _absent()
        point_at(a)
        absent = loader()
        return unreadable, absent

    def _assert_pair(self, name, unreadable, absent):
        self.assertIsNone(
            unreadable, "%s returns %r for a store that EXISTS and cannot be READ. That is "
                        "indistinguishable from 'absent, nothing written yet', and the caller "
                        "writes the whole dict back — so a permissions problem silently destroys "
                        "every key it holds." % (name, unreadable))
        # ⚠ THE BASELINE, or the fix is just "always None" and the three-state design is gone.
        self.assertEqual(
            absent, {}, "%s returns %r for a genuinely ABSENT store. Absent is a MEASUREMENT — "
                        "nothing has been written yet — and turning it into UNKNOWN would make "
                        "the very first write impossible. [[regression-guard]] §5" % (name, absent))

    def test_handoff_marks(self):
        import handoff as H
        old = H.MARKS
        try:
            def point(p):
                H.MARKS = p
            u, a = self._probe(H._marks, point, {"179": 1, "180": 2, "230": 3})
        finally:
            H.MARKS = old
        self._assert_pair("handoff._marks", u, a)

    def test_shadow_watch_stored(self):
        import control_app as CA
        old = CA._shadow_watch_path
        try:
            def point(p):
                CA._shadow_watch_path = lambda _p=p: _p
            u, a = self._probe(CA._shadow_watch_stored, point, {"lookedAt": 123, "starts": 4})
        finally:
            CA._shadow_watch_path = old
        self._assert_pair("control_app._shadow_watch_stored", u, a)

    def test_read_names_feeder(self):
        import control_app as CA
        old = CA._rnf_path
        try:
            def point(p):
                CA._rnf_path = lambda _p=p: _p

            def load():
                CA._RNF_STORE["tried"] = False
                return CA._rnf_load()
            u, a = self._probe(load, point, {"runs": 99, "banked": 5, "lastTs": 1})
        finally:
            CA._rnf_path = old
            CA._RNF_STORE["tried"] = False
        self._assert_pair("control_app._rnf_load", u, a)


class TheWriterActuallyRefuses(unittest.TestCase):
    """⚠ The loader returning None is half of it. The destruction only stops if the WRITER reads
    that None and stands down. Pin the joint, not the end. [[the-unjoined-end]]"""

    def test_rnf_save_refuses_over_an_unreadable_store(self):
        import control_app as CA
        old = CA._rnf_path
        p = _unreadable({"runs": 99, "banked": 5, "lastTs": 1})
        try:
            CA._rnf_path = lambda _p=p: _p
            CA._RNF_STORE["tried"] = False
            saved = CA._rnf_save()
            self.assertIs(
                saved, False,
                "_rnf_save wrote over a store it could not read. It refuses only on None, so the "
                "loader handing back {} for an unreadable file is what re-opened this path.")
        finally:
            os.chmod(p, stat.S_IRUSR | stat.S_IWUSR)
            CA._rnf_path = old
            CA._RNF_STORE["tried"] = False
        # and the bytes are still there
        self.assertEqual(json.load(io.open(p, encoding="utf-8")).get("runs"), 99,
                         "the store was overwritten despite the refusal")


class NoSiteKEEPSTheBrokenShape(unittest.TestCase):
    """[[source-reading-guard]] — grade CODE, never the prose describing it."""

    def test_no_loader_hands_back_a_falsy_container_from_a_bare_IOError(self):
        bad = []
        for fn in ("handoff.py", "control_app.py"):
            src = io.open(os.path.join(HERE, fn), encoding="utf-8").read()
            code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
            lines = code.split("\n")
            for i, ln in enumerate(lines):
                if ln.strip() != "except IOError:":
                    continue
                nxt = "\n".join(lines[i + 1:i + 3])
                if "{}" in nxt or "[]" in nxt or '""' in nxt or "return 0" in nxt:
                    bad.append("%s:%d" % (fn, i + 1))
        self.assertEqual(
            bad, [],
            "%s still answers a bare `except IOError` with an empty container. IOError IS OSError "
            "here, so that arm also catches an existing store that cannot be READ, and the caller "
            "writes the empty value back over it." % ", ".join(bad))


class TheRatchetCanTellTheTwoApart(unittest.TestCase):
    """⚠⚠ THE RATCHET COULD NOT SEE ITS OWN FIX, WHICH IS WHY THIS SECTION EXISTS.

    `swallow_census` ranked on what a handler RETURNS and never on what it CATCHES, so
    `except FileNotFoundError: return {}` and `except OSError: return {}` were the same rank —
    opposite facts, one number. The three repairs above moved ZERO sites, and a ratchet whose
    count survives the repair of the thing it flagged teaches its reader to re-baseline.
    MEASURED: 6 of 76 rank-1 sites catch absence only, so rank 1 went 76 -> 70.
    """

    def _rank_of(self, snippet):
        import ast
        import swallow_census as SC
        tree = ast.parse(snippet)
        tries = [n for n in ast.walk(tree) if isinstance(n, ast.Try)]
        self.assertEqual(len(tries), 1, "the fixture must contain exactly one try")
        t = tries[0]
        self.assertEqual(len(t.handlers), 1, "the fixture must contain exactly one handler")
        return SC._rank(t, t.handlers[0])[0]

    #: a read the census recognises, handing back an empty dict
    BODY = "def f(p):\n    try:\n        return json.load(open(p))\n    except %s:\n        return {}\n"

    def test_absence_only_is_not_a_lie(self):
        self.assertEqual(
            self._rank_of(self.BODY % "FileNotFoundError"), 2,
            "a handler that catches ABSENCE ONLY is still ranked as a failed read handed back as "
            "data. A store never written and a store written empty are the same fact to a caller, "
            "and ranking them as a lie is what made this ratchet blind to its own repair.")

    def test_a_broad_catch_is_still_a_lie(self):
        """⚠ THE BASELINE. Without it the narrowing is just an off switch. [[regression-guard]] §5"""
        for cls in ("OSError", "IOError", "Exception"):
            self.assertEqual(
                self._rank_of(self.BODY % cls), 1,
                "`except %s: return {}` is no longer ranked as a failed read handed back as data. "
                "That is the exact defect this version repaired in three loaders — IOError IS "
                "OSError here, so it catches an existing store that cannot be opened." % cls)

    def test_a_tuple_carrying_a_wider_class_gets_no_pass(self):
        self.assertEqual(
            self._rank_of(self.BODY % "(FileNotFoundError, PermissionError)"), 1,
            "a tuple that also catches PermissionError is being excused as absence-only. One "
            "wider name in the tuple means the handler catches failures too.")

    def test_a_bare_except_gets_no_pass(self):
        import ast
        import swallow_census as SC
        t = [n for n in ast.walk(ast.parse(
            "def f(p):\n    try:\n        return json.load(open(p))\n    except:\n        return {}\n"
        )) if isinstance(n, ast.Try)][0]
        self.assertEqual(SC._rank(t, t.handlers[0])[0], 1,
                         "a bare `except:` is being read as absence-only")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "putting the handoff loader back on a bare IOError makes an unreadable watermark "
               "store read as absent, and --mark then writes one key over all of them",
        "file": "tv/handoff.py",
        "find": "    except FileNotFoundError:\n        return {}            # absent: nothing marked yet",
        "replace": "    except IOError:\n        return {}            # absent: nothing marked yet",
        "matches": 1,
    },
    {
        "why": "the same regression on the shadow-watch store, whose writer does cur.update(kw) "
               "and writes the whole dict back",
        "file": "tv/control_app.py",
        "find": "    except FileNotFoundError:\n        return {}            # absent: never written yet",
        "replace": "    except IOError:\n        return {}            # absent: never written yet",
        "matches": 1,
    },
    {
        "why": "the same regression on the read-names feeder, where _rnf_save refuses only on None",
        "file": "tv/control_app.py",
        "find": "    except FileNotFoundError:\n        _RNF_STORE[\"readable\"] = {}",
        "replace": "    except IOError:\n        _RNF_STORE[\"readable\"] = {}",
        "matches": 1,
    },
    {
        "why": "widening the census pass back to any exception class makes it excuse the very "
               "defect this version repaired, so its count can never see the repair",
        "file": "tv/swallow_census.py",
        "find": "    return bool(names) and names <= ABSENCE_ONLY",
        "replace": "    return bool(names)",
        "matches": 1,
    },
    {
        "why": "turning the ABSENT arm into UNKNOWN makes the very first write impossible — the "
               "baseline that stops this fix from being 'always refuse'",
        "file": "tv/handoff.py",
        "find": "    except FileNotFoundError:\n        return {}",
        "replace": "    except FileNotFoundError:\n        return None",
        "matches": 1,
    },
]
