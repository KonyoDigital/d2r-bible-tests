# -*- coding: utf-8 -*-
"""v3428 (#37) — THE BOARD'S BUILD ID COMES FROM THE LIVE WINDOW OR IT COMES BACK UNKNOWN.

#37 has been BLOCKED for weeks on one value, and the GrokBot seat finally said why, three ticks
running: *"live typeof window.D2R_BUILD / .id / Object.keys(D2R*) NOT EVALABLE — no evaluate_js
HTTP door on pywebview seat (probed /api/eval* → 404)"*. It could only read the board's SERVED
HTML, which is the file, not the window.

⚠ AND I REPORTED THAT BLOCKER AS LIFTED ONCE, WRONGLY. An earlier pack answered `v3419` via
`/board?app=1&engine=1` and I read it as a live evaluation; the seat then labelled the same read
**SOURCE-ONLY**. Its refusals were right and my reading of them was not. A value that agrees with
the live one is still not a live read. [[a-probe-licenses-only-what-it-tested]]

⚠⚠ THE LAW THIS FILE EXISTS FOR: the door must NEVER substitute the banner or `/api/status`. That
substitution IS the defect #37 bans — one banner, one sentence, one writer — and the seat has been
correctly refusing it as "not a substitute for contentWindow" on every single pack. Four distinct
refusals (window shut, timeout, raise, non-JSON) and one MEASURED absence must stay
distinguishable, because "I could not look" and "it is not there" are opposite facts.
[[unknown-stays-unknown]]
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA  # noqa: E402

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8", errors="replace").read()

GOOD = json.dumps({"typeofBuild": "object", "id": "v3419", "profile": "MAIN+LADDER",
                   "machine": "LINUX", "keys": ["D2R_BUILD", "D2R_PFX"], "hopped": True})


class TestALiveBuildReadIsNeverTheBanner(unittest.TestCase):

    def _drive(self, ejs, live=True, win=object()):
        """Run board_build() against a fake window and a fake evaluator."""
        g = CA.__dict__
        old = (g.get("_BOARD_WIN"), g.get("_MAIN_WIN"), g.get("_WINDOW_LIVE"), g.get("_ejs"))
        try:
            g["_BOARD_WIN"], g["_MAIN_WIN"], g["_WINDOW_LIVE"] = win, None, live
            g["_ejs"] = ejs
            return CA.board_build()
        finally:
            (g["_BOARD_WIN"], g["_MAIN_WIN"], g["_WINDOW_LIVE"], g["_ejs"]) = old

    # ---- the one good answer ------------------------------------------------------------

    def test_a_live_window_answers_with_its_own_id(self):
        out = self._drive(lambda w, code, t=4.0: GOOD)
        self.assertTrue(out["ok"])
        self.assertEqual(out["id"], "v3419")
        self.assertEqual(out["profile"], "MAIN+LADDER")
        self.assertEqual(out["machine"], "LINUX")
        self.assertTrue(out["hopped"], "the reader does not say WHICH context answered")

    # ---- four refusals, each distinguishable -------------------------------------------

    def test_a_SHUT_window_is_a_refusal_with_no_id(self):
        out = self._drive(lambda *a, **k: GOOD, live=False)
        self.assertFalse(out["ok"])
        self.assertIsNone(out["id"], "it invented an id with no window to read")
        self.assertIn("not open", out["why"])

    def test_a_TIMEOUT_is_UNKNOWN_and_never_an_absence(self):
        """⚠ `_ejs` returns None when the WKWebView did not answer inside its bound. Calling that
        'no build id' reports a BUSY window as an UNSTAMPED one — the exact collapse this door
        exists to avoid."""
        out = self._drive(lambda *a, **k: None)
        self.assertFalse(out["ok"])
        self.assertIsNone(out["id"])
        self.assertIn("did not answer", out["why"])
        self.assertNotIn("carries no", out["why"],
                         "a timeout was worded as a measured absence")

    def test_a_RAISING_window_names_the_failure(self):
        def boom(*a, **k):
            raise RuntimeError("dead webview")
        out = self._drive(boom)
        self.assertFalse(out["ok"])
        self.assertIsNone(out["id"])
        self.assertIn("refused the read", out["why"])

    def test_a_NON_JSON_answer_is_a_refusal(self):
        out = self._drive(lambda *a, **k: "<html>not json</html>")
        self.assertFalse(out["ok"])
        self.assertIsNone(out["id"])

    def test_a_window_that_RAISED_IN_JS_reports_that(self):
        out = self._drive(lambda *a, **k: json.dumps({"err": "D2R_BUILD is not defined"}))
        self.assertFalse(out["ok"])
        self.assertIn("raised", out["why"])

    # ---- the measured absence, which is NOT a refusal -----------------------------------

    def test_a_window_with_NO_build_id_is_a_MEASURED_absence(self):
        """⚠ THE STATE THE SEAT HAS BEEN REPORTING. It reads differently from every refusal above,
        and the why must say so or a reader cannot tell 'the board has no stamp' from 'I could not
        ask'."""
        out = self._drive(lambda *a, **k: json.dumps(
            {"typeofBuild": "undefined", "id": None, "keys": [], "hopped": False}))
        self.assertFalse(out["ok"])
        self.assertIsNone(out["id"])
        self.assertIn("measured, not a failure to look", out["why"])

    # ---- the substitution this whole task bans ------------------------------------------

    def test_the_door_never_reaches_for_the_banner_or_api_status(self):
        """#37: ONE banner, ONE sentence, ONE writer. A live-window door that quietly falls back to
        the served stamp would report agreement it never measured — and the seat has spent weeks
        correctly refusing exactly that substitution."""
        # ⚠⚠ THE DOCSTRING IS STRIPPED, AND THE FIRST CUT OF THIS CASE FAILED BECAUSE IT WAS NOT.
        # board_build's own docstring contains the sentence "IT NEVER FALLS BACK TO THE BANNER OR
        # /api/status" — so a scanner that reads prose flagged the EXPLANATION of the ban as a
        # violation of it. Stripping `#` comments was not enough; a docstring is prose too.
        # [[sweep-dont-ask]] — "a scanner that reads its own documentation sits red forever
        # pointing at itself". [[source-reading-guard]] §4b
        import ast as _ast
        fn = [n for n in _ast.walk(_ast.parse(SRC))
              if isinstance(n, _ast.FunctionDef) and n.name == "board_build"]
        self.assertTrue(fn, "board_build is gone")
        stripped = _ast.get_docstring(fn[0]) is not None
        nodes = fn[0].body[1:] if stripped else fn[0].body
        self.assertTrue(nodes, "board_build has a docstring and nothing else")
        code = "\n".join(_ast.get_source_segment(SRC, n) or "" for n in nodes)
        code = "\n".join(l.split("#", 1)[0] for l in code.split("\n"))
        for banned in ("/api/status", "BUILD_ID", "_VERSION", "banner"):
            self.assertNotIn(banned, code,
                             "board_build reaches for %r — a value from another source dressed as "
                             "a live window read is the defect #37 bans" % banned)

    def test_it_is_a_FIXED_expression_not_a_caller_supplied_eval(self):
        """⚠ The seat asked for an eval route and that is the one thing this must not become: a
        caller-supplied-code endpoint on the console he is looking at is a hazard, and a second
        write path into his board."""
        i = SRC.find("def board_build(")
        j = SRC.find("\ndef ", i + 1)
        body = SRC[i:j if j > 0 else len(SRC)]
        self.assertNotIn("def board_build(code", body, "the door takes caller-supplied code")
        sig = body.split("\n", 1)[0]
        self.assertEqual(sig.strip(), "def board_build():",
                         "board_build grew a parameter — it must take nothing, so there is nothing "
                         "to inject: %r" % sig)


RED_PROOF = [
    {
        "why": "v3428 - THE TIMEOUT COLLAPSED INTO AN ABSENCE. _ejs returns None when the window "
               "did not answer inside its bound; wording that as 'carries no D2R_BUILD.id' reports "
               "a BUSY window as an UNSTAMPED one, which is the collapse this door exists to stop.",
        "file": "control_app.py",
        "find": "                \"why\": \"the board window did not answer within 4s — UNKNOWN, not absent\"}",
        "replace": "                \"why\": \"the board window carries no D2R_BUILD.id\"}",
        "matches": 1,
    },
    {
        "why": "v3428 - A MEASURED ABSENCE DRESSED AS SUCCESS. Reporting ok:True when the window "
               "answered with no id hands every reader a None that looks like a verdict.",
        "file": "control_app.py",
        "find": "    out = {\"ok\": bool(got.get(\"id\")), \"id\": got.get(\"id\"),",
        "replace": "    out = {\"ok\": True, \"id\": got.get(\"id\"),",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
