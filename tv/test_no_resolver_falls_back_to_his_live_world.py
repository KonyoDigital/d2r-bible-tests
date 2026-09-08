# -*- coding: utf-8 -*-
"""v2788 — THREE RESOLVERS FELL BACK TO HIS LIVE DIRECTORY WHEN ISOLATION HAD BEEN ASKED FOR.

v2783 fixed one: `_fixture_root_for_state()` in control_app had
`except Exception: return HERE`, so ANY failure inside the resolver silently handed the caller his
real data directory — the exact harm the function exists to prevent. v2785 then made it agree with
the canonical rule. **Neither swept to the copies.** A parallel read-only sweep found three more:

    tv/control_app.py       `_log_root()`            binds LOG_PATH, which is APPENDED to on every
                                                     line of console output and TRUNCATED at 2 MB
    tv/chronicle_routes.py  `_routes_cache_root()`   WRITES
    tv/frame_authority.py   inline `_croot`          WRITES .fixture_reels_cache.json

`_log_root`'s own docstring already records the harm happening once from a milder cause: gate runs
wrote `control start … mode=sim` banners into his live log and I read them as Konyo at his keyboard.
And frame_authority's v2778 comment MEASURED these very files being left dirty in his live `tv/` —
the comment was written, the except-arm was not fixed.

=== ⚠⚠ THIS LAW IS A CENSUS, NOT A LIST OF THREE ===
Naming the three would be green the day a fourth appears — and a fourth is exactly how three
appeared, one copy at a time. It PARSES every module in tv/ and fails on any except-handler that
resolves to HERE without consulting TV_HIST. [[copy-drift]] [[the-unjoined-end]] [[regression-guard]]

⚠ AST, NOT GREP. Every one of these fixes quotes the defective arm in a comment to explain it, so a
substring search would go red on the explanation. [[source-reading-guard]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: A handler may legitimately fall back to HERE when nothing could ever have asked for isolation.
#: Each entry needs a REASON, exactly like render_check's truncation_ok — an unexplained exemption
#: is how a census becomes a list.
ALLOWED = {
    # "module.py:function": "why falling back to HERE is correct here",
    "control_app.py:_chron_hunt_mem_path":
        "DELIBERATE, and the code already tried the 'fix' and rejected it. It honours "
        "TV_CHRON_HUNT_MEM first, then a patched global, then DERIVES from _chron_swept_path() — "
        "the file that has carried every isolation override since v1858. Its own v2175.2 comment "
        "records the attempt: *'My first cut walked TV_HIST itself and STILL wrote his live tree "
        "during a full suite run, because the callers that reach here do not all set TV_HIST — I "
        "had rebuilt half of an isolation that already existed, and got the half wrong.'* Forcing "
        "the census's shape onto it would re-introduce that bug. [[copy-drift]]",
}


#: ⚠⚠ THE DISCRIMINATOR, AND THE CODE TAUGHT IT TO ME. The first cut of this census flagged
#: `shadow_ledger._ledger_path` and `retro_gate._ledger_path`, and BOTH ARE CORRECT — they catch
#: `ImportError` ONLY, and their comments say exactly why: *"If the root rule is broken that must
#: surface, not resolve to his tree."* An ImportError means tv_diablo genuinely is not importable,
#: and HERE is then the honest answer. A BLANKET `except Exception` is the defect, because it also
#: swallows a runtime failure OF THE RULE ITSELF and answers as if nobody had asked for isolation.
#: A census that cannot tell those apart would train us to skim its output. [[unknown-stays-unknown]]
_NARROW = {"ImportError", "ModuleNotFoundError"}


def _catches_broadly(handler):
    """Does this except-arm swallow a runtime failure of the rule, not just a missing module?"""
    t = handler.type
    if t is None:                                   # bare `except:` — the widest of all
        return True
    names = set()
    for n in ast.walk(t):
        if isinstance(n, ast.Name):
            names.add(n.id)
        elif isinstance(n, ast.Attribute):
            names.add(n.attr)
    return not names or bool(names - _NARROW)


def _handlers_resolving_to_here(tree):
    """Every BROAD except-handler that yields HERE. -> [(func, lineno, consults_tv_hist)]

    ⚠ Deduped by line number. The first cut walked Module AND each FunctionDef, so every site was
    reported twice — six real sites read as twelve, which is a count nobody can act on.
    """
    seen, out = set(), []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(fn):
            if not isinstance(node, ast.Try):
                continue
            for h in node.handlers:
                if h.lineno in seen:
                    continue
                if not any(isinstance(n, ast.Name) and n.id == "HERE" for n in ast.walk(h)):
                    continue
                if not _catches_broadly(h):
                    continue                        # narrow ImportError-only is CORRECT
                seen.add(h.lineno)
                consults = any(isinstance(n, ast.Constant) and n.value == "TV_HIST"
                               for n in ast.walk(h))
                out.append((fn.name, h.lineno, consults))
    return out


class NoResolverFallsBackToHisLiveWorld(unittest.TestCase):

    def test_the_census_finds_something_to_inspect(self):
        """⚠ THE DENOMINATOR. If the walk ever returns nothing at all, the law below passes over an
        empty set and reads exactly like clean. [[zero-needs-a-denominator]]"""
        seen = 0
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py"):
                continue
            try:
                tree = ast.parse(io.open(os.path.join(HERE, name), encoding="utf-8").read())
            except Exception:
                continue
            seen += len(_handlers_resolving_to_here(tree))
        self.assertGreater(seen, 0,
                           "the census inspected ZERO except-handlers — it is measuring nothing, "
                           "not finding nothing")

    # ── ⚠⚠ THE LAW ──────────────────────────────────────────────────────────────────────────
    def test_NO_except_arm_resolves_to_HERE_while_ignoring_TV_HIST(self):
        """★★★ A request for isolation that cannot be honoured must not degrade to NO isolation.

        Falling back to HERE is not a degraded answer — it is the wrong one, and on `_log_root` it
        would have appended to (and at 2 MB truncated) his real console log from inside a gate run.

        The census parses every module in tv/. Anything it finds must either consult TV_HIST in the
        handler or carry a REASON in ALLOWED."""
        bad = []
        for name in sorted(os.listdir(HERE)):
            if not name.endswith(".py") or name.startswith("test_"):
                continue
            path = os.path.join(HERE, name)
            try:
                tree = ast.parse(io.open(path, encoding="utf-8").read())
            except Exception:
                continue
            for fname, lineno, consults in _handlers_resolving_to_here(tree):
                if consults:
                    continue
                key = "%s:%s" % (name, fname)
                if key in ALLOWED:
                    continue
                bad.append("%s:%d in %s()" % (name, lineno, fname))
        self.assertEqual(bad, [],
                         "%d except-handler(s) resolve to his LIVE directory without consulting "
                         "TV_HIST, so a resolver failure inside an isolated run writes into his "
                         "real data: %s" % (len(bad), ", ".join(bad)))

    def test_every_exemption_carries_a_REASON(self):
        """⚠ An unexplained exemption is how a census quietly becomes a list of the ones somebody
        got round to. Same rule render_check applies to truncation_ok."""
        empty = [k for k, v in ALLOWED.items() if not str(v).strip()]
        self.assertEqual(empty, [], "exemptions with no reason: %s" % empty)

    # ── ⛔ AND HIS OWN CONSOLE MUST BE UNCHANGED ─────────────────────────────────────────────
    def test_his_console_still_writes_where_he_expects(self):
        """⛔ THE OTHER HALF. With nothing asking for a fixture world, every one of these must
        still resolve to his live tree — a fix that quietly moved his console log somewhere he
        cannot find it would be far worse than the bug."""
        import control_app as CA
        self.assertTrue(str(CA.LOG_PATH).startswith(CA.HERE + os.sep),
                        "his console log no longer resolves into his own tree: %s" % CA.LOG_PATH)
        import chronicle_routes as CR
        self.assertEqual(CR._routes_cache_root(), CR.HERE,
                         "the routes cache no longer resolves to his tree in ordinary use")

    def test_log_root_DELEGATES_rather_than_repeating_the_rule(self):
        """⚠ Two copies drifted; three would drift again, and the next fix would land on whichever
        one the author happened to open. `_log_root` must quote the owner, not restate it."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        tree = ast.parse(src)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_log_root"), None)
        self.assertIsNotNone(fn, "_log_root is gone")
        calls = {getattr(c.func, "id", None) or getattr(c.func, "attr", None)
                 for c in ast.walk(fn) if isinstance(c, ast.Call)}
        self.assertIn("_fixture_root_for_state", calls,
                      "_log_root has its own copy of the rule again instead of delegating")


if __name__ == "__main__":
    unittest.main(verbosity=2)
