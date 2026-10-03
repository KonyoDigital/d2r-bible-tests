# -*- coding: utf-8 -*-
"""CLAUDE READS EVERY FRAME ON EVERY PC; GROK IS ONLY AN EXTRA LAYER, AND ONLY WHEN IT IS SWITCHED ON.

His ruling, 2026-09-30: "make sure the subscription CLI is using claude and not grok.. grok is just an extra layer if
toggled on.. dean does not use grok.. so it shouldnt need both to work obviously just make sure the coding and logic is
correctly architured too".

MEASURED that morning, before anything changed: his Mac AND his ALT were both on G5 "primary" - Grok read every frame
first and Claude was only its fallback. The Mac's counters: 6,132 Grok calls, 3,150 errors, the last "grok -p timeout
140s" - a failed Grok read held the frame that long before Claude read it. How they got there: ⚡ Authorize on an
already-linked PC called set_mode("primary"), the page's own poll posted {mode: 'primary'} after a login, the switch
offered PRIMARY, and a legacy {"on": true} was read as primary. Both consoles were set to shadow at runtime the same
morning; this law makes the architecture say it:

  1. THE SWITCH - ON is the extra layer (shadow): set_on, a legacy {"on": true}, the environment and a saved or
     requested "primary" all come out as shadow, and a saved primary is SAID (primaryRetired), never silent.
  2. THE READ PATH - the frame reader has no Grok-first branch: every Grok vision read in tv_diablo happens inside a
     shadow job on its own thread, beside the Claude read, never instead of it.
  3. THE CONSOLE - a missing Claude CLI BLOCKS on every PC (it used to soften "when G5 primary covers vision"); a login
     turns Grok on BESIDE Claude; the intake always asks Claude first.
  4. THE PAGE - no Grok-first control and no Grok-first request.
Dean's PC (no Grok at all) is the default path: off, Claude only, nothing else needed.

⚠ #151, HIS RULING OF 2026-10-01, NARROWS THIS LAW AND DOES NOT REPEAL IT: "make the toggle optional to use GROK ONLY no
claude as a secondary at all ... so i can save and when you max out i can use just him". A THIRD position, GROK ONLY,
reads every frame with the Grok CLI and never asks Claude at all - not first, not as a backup. What stays forbidden is
what this law was written for: Grok FIRST with Claude behind it, by any door. So: a saved or requested "primary" is still
read as the extra layer (BOTH), and the only Grok read outside a shadow job is tv_diablo._grok_oneshot - the GROK ONLY
seat, which holds no Claude call of its own. test_his_switch_picks_who_reads.py drives the three positions.
[[the-unjoined-end]] [[unknown-stays-unknown]]
RED_PROOF below.
"""
import ast
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()   # REG-1717 - the switch file below is a scratch dir; contained, it goes with the run (CI's scratch law)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import g5_grok_eyes as g5  # noqa: E402
import control_app as ca  # noqa: E402

# REG-1714 - THIS LAW READ HIS REAL READER SWITCH. The v3555 push proved it in a sandbox copied from his tree, where
# his Mac's EYES switch says GROK ONLY (his choice, 10-02 07:17): there a missing Claude CLI is rightly a warning, not
# a block, and test_a_missing_claude_cli_blocks_even_with_grok_on went red untampered (REG-1709's class, the one law
# that sweep did not reach). Every switch-reading law was then run under a planted GROK ONLY and a planted BOTH: this
# was the only one red. Its switch now lives in its own temp file, whatever position he picks.
g5._STATE_FILE = os.path.join(tempfile.mkdtemp(prefix="claude_reads_switch_"), "g5_grok_eyes.state")

RED_PROOF = [
    {
        "why": "the write guard goes: a request for Grok-first is saved as primary again",
        "file": "g5_grok_eyes.py",
        "find": "    if mode == \"primary\":\n        mode = \"shadow\"                # 2026-09-30: nothing writes Grok-first again\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the read guard goes: a saved primary is read as Grok-first again",
        "file": "g5_grok_eyes.py",
        "find": "        if retired:\n            mode = \"shadow\"            # primary is retired: Claude reads, Grok watches beside it\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the environment can put Grok first again",
        "file": "g5_grok_eyes.py",
        "find": "        return \"shadow\"                # ON is the extra layer; \"primary\" is retired (2026-09-30)\n",
        "replace": "        return \"primary\"\n",
        "matches": 1,
    },
    {
        "why": "the frame reader grows a Grok-first branch again",
        "file": "tv_diablo.py",
        "find": "        _G5 = None\n    # ══ END GROK EYES (G5) ════════════════════════════════════════════════════\n    # #151 HIS SWITCH AT GROK ONLY",
        "replace": "        _G5 = None\n    if _G5 is not None and _G5.is_primary():\n        return _G5.g5_vision_read(ap)\n    # ══ END GROK EYES (G5) ════════════════════════════════════════════════════\n    # #151 HIS SWITCH AT GROK ONLY",
        "matches": 1,
    },
    {
        "why": "a missing Claude CLI softens to a warning again",
        "file": "control_app.py",
        "find": "    checks.append(_chk(\"claude_cli\", bool(exe), \"block\",\n",
        "replace": "    checks.append(_chk(\"claude_cli\", bool(exe), \"warn\",\n",
        "matches": 1,
    },
    {
        "why": "⚡ Authorize makes Grok the reader again",
        "file": "control_app.py",
        "find": "                        _G5.set_mode(\"shadow\")\n",
        "replace": "                        _G5.set_mode(\"primary\")\n",
        "matches": 1,
    },
    {
        "why": "the intake lets a primary mode skip Grok's extra read (or lead with it)",
        "file": "control_app.py",
        "find": "    if mode == \"primary\":\n        mode = \"shadow\"\n    out = []\n",
        "replace": "    out = []\n",
        "matches": 1,
    },
    {
        "why": "the page offers Grok-first again",
        "file": "control_ui.html",
        "find": ">\u2190 BOTH \u2192</button>\n",
        "replace": ">\u2190 BOTH \u2192</button><button type=\"button\" class=\"g5-seg-btn\" data-g5=\"primary\">PRIMARY</button>\n",
        "matches": 1,
    },
]


class _State(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.mkdtemp(prefix="claude_reads_")
        self.addCleanup(shutil.rmtree, self.td, True)
        self.state = os.path.join(self.td, "g5.state")
        p = mock.patch.object(g5, "_STATE_FILE", self.state)
        p.start()
        self.addCleanup(p.stop)
        saved = os.environ.pop("TV_G5_GROK_EYES", None)
        if saved is not None:
            self.addCleanup(os.environ.__setitem__, "TV_G5_GROK_EYES", saved)

    def _write(self, d):
        with io.open(self.state, "w", encoding="utf-8") as fh:
            json.dump(d, fh)

    def _saved_mode(self):
        with io.open(self.state, encoding="utf-8") as fh:
            return json.load(fh).get("mode")


# ══ 1 — THE SWITCH ═══════════════════════════════════════════════════════════════════════════════════════════════
class TheSwitchNeverPutsGrokFirst(_State):

    def test_dean_s_pc_is_claude_only_with_nothing_else(self):
        self.assertEqual(g5.mode_intent(), "off", "no choice made must mean Claude only")
        with mock.patch.object(g5, "has_subscription", return_value=False):
            self.assertEqual(g5.mode(), "off")
            self.assertFalse(g5.is_on())

    def test_on_is_the_extra_layer(self):
        g5.set_on(True)
        self.assertEqual(self._saved_mode(), "shadow")
        with mock.patch.object(g5, "has_subscription", return_value=True):
            self.assertEqual(g5.mode(), "shadow")
            self.assertFalse(g5.is_primary())

    def test_a_request_for_grok_first_is_saved_as_the_extra_layer(self):
        g5.set_mode("primary")
        self.assertEqual(self._saved_mode(), "shadow", "a Grok-first request reached the switch file")

    def test_a_saved_grok_first_reads_as_the_extra_layer_and_says_so(self):
        self._write({"on": True, "mode": "primary"})
        self.assertEqual(g5.mode_intent(), "shadow")
        st = g5.status()
        # #151 - the extra layer is now named for what it is: BOTH (Claude reads every frame, Grok beside it)
        self.assertEqual(st.get("reader"), "both")
        self.assertTrue(str(st.get("readerRule") or "").startswith("Claude reads every frame"), st.get("readerRule"))
        self.assertIn("retired", st.get("primaryRetired") or "", "a saved Grok-first choice was mapped silently")
        self._write({"on": True, "mode": "off"})
        self.assertEqual(g5.mode_intent(), "shadow", "a legacy on:true read as Grok-first")

    def test_the_environment_cannot_put_grok_first(self):
        for v in ("1", "on", "true", "yes", "primary", "pri"):
            with mock.patch.dict(os.environ, {"TV_G5_GROK_EYES": v}):
                self.assertEqual(g5.mode_intent(), "shadow", "TV_G5_GROK_EYES=%s put Grok first" % v)


# ══ 2 — THE READ PATH ════════════════════════════════════════════════════════════════════════════════════════════
class TheFrameReaderHasNoGrokFirstBranch(unittest.TestCase):

    def test_every_grok_read_sits_in_a_named_seat(self):
        """Walked by the parser: every g5_vision_read call in tv_diablo sits inside _grok_oneshot
        (GROK ONLY) or _grok_backup (a frame Claude did not read). A function with "shadow" in its
        name is not a home, and nothing asks is_primary. [[source-reading-guard]]"""
        with io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        bad = []
        homes = []

        def walk(node, fn):
            for ch in ast.iter_child_nodes(node):
                nfn = ch.name if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)) else fn
                if isinstance(ch, ast.Call) and isinstance(ch.func, ast.Attribute):
                    if ch.func.attr == "is_primary":
                        bad.append("is_primary asked in %s (line %d)" % (fn, ch.lineno))
                    if ch.func.attr == "g5_vision_read":
                        homes.append(nfn)
                        if nfn not in ("_grok_oneshot", "_grok_backup"):
                            bad.append("a Grok read outside the two seats, in %s (line %d)" % (nfn, ch.lineno))
                walk(ch, nfn)
        walk(tree, None)
        self.assertEqual(sorted(homes), ["_grok_backup", "_grok_oneshot"],
                         "premise: the scanner saw the two seats (%s)" % homes)
        self.assertEqual(bad, [], "the frame reader can still put Grok first or beside Claude: %s" % bad)

    def test_the_grok_only_seat_has_no_claude_behind_it(self):
        """#151 - _grok_oneshot is Grok ALONE: no warm Claude reader, no Claude one-shot, no budget-gated Claude path
        inside it, so it can never become Grok-first-then-Claude. [[source-reading-guard]]"""
        with io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_grok_oneshot"]
        self.assertEqual(len(fns), 1, "the GROK ONLY seat is not one function")
        called = set()
        for n in ast.walk(fns[0]):
            if isinstance(n, ast.Call):
                f = n.func
                called.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
        self.assertIn("g5_vision_read", called, "premise: the seat reads with Grok")
        self.assertEqual(called & {"ask", "_oneshot", "_oneshot_inner", "claude_read", "_maybe_genius"}, set(),
                         "the GROK ONLY seat reaches a Claude reader")


# ══ 3 — THE CONSOLE ══════════════════════════════════════════════════════════════════════════════════════════════
class TheConsoleNeedsClaudeOnEveryPc(unittest.TestCase):

    def test_a_missing_claude_cli_blocks_even_with_grok_on(self):
        class _PR:
            returncode = 0
            stdout = b"ok"
            stderr = b""
        env_saved = os.environ.pop("TV_CLAUDE_BIN", None)
        try:
            with mock.patch.object(ca.subprocess, "run", lambda *a, **k: _PR()), \
                    mock.patch.object(ca.shutil, "which", lambda *a, **k: None), \
                    mock.patch.object(ca, "_find_claude_bin", lambda *a, **k: None), \
                    mock.patch.object(g5, "mode", lambda: "shadow"):
                j = ca.farmgate_payload()
        finally:
            if env_saved is not None:
                os.environ["TV_CLAUDE_BIN"] = env_saved
        row = next(c for c in j["checks"] if c["id"] == "claude_cli")
        self.assertFalse(row["ok"], row)
        self.assertEqual(row["severity"], "block", "a PC without Claude was let through: %r" % row)

    def _login(self, body):
        calls = []
        h = ca.Handler.__new__(ca.Handler)
        h.path = "/api/g5_login"
        raw = json.dumps(body).encode("utf-8")
        h.headers = {"Content-Length": str(len(raw)), "Content-Type": "application/json"}
        h.rfile = io.BytesIO(raw)
        out = []
        h._json = lambda code, obj: out.append((code, obj))
        with mock.patch.object(ca._G5, "start_login",
                               lambda prefer_oauth=True: {"ok": True, "reason": "already-authorized",
                                                          "hasSubscription": True}), \
                mock.patch.object(ca._G5, "set_mode", lambda m, on=None: calls.append(m)), \
                mock.patch.object(ca, "_g5_status", lambda: {"mode": "shadow"}):
            h.do_POST()
        self.assertEqual(len(out), 1, "the route answered %d times" % len(out))
        return calls

    def test_a_login_turns_grok_on_beside_claude_never_first(self):
        self.assertEqual(self._login({"oauth": True, "setOn": True}), ["shadow"])
        self.assertEqual(self._login({"oauth": True, "setPrimary": True}), ["shadow"],
                         "an older page's setPrimary made Grok the reader")

    def test_the_intake_asks_claude_first_whatever_the_mode_says(self):
        td = tempfile.mkdtemp(prefix="intake_order_")
        self.addCleanup(shutil.rmtree, td, True)
        for f in ("intake_local.mjs", "intake_grok_sub.mjs"):
            io.open(os.path.join(td, f), "w").close()
        for m in ("primary", "shadow"):
            labs = [l for l, _p in ca._intake_dual_runners(td, m)]
            self.assertEqual(labs, ["subscription", "grok-subscription"], "mode %s: %r" % (m, labs))
        self.assertEqual([l for l, _p in ca._intake_dual_runners(td, "off")], ["subscription"])


# ══ 4 — THE PAGE ═════════════════════════════════════════════════════════════════════════════════════════════════
class ThePageOffersNoGrokFirst(unittest.TestCase):

    def test_no_grok_first_control_and_no_grok_first_request(self):
        with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotIn('data-g5="primary"', src, "the EYES switch offers Grok-first")
        for req in ("mode: 'primary'", 'mode:"primary"', "setPrimary: true"):
            self.assertNotIn(req, src, "the page still asks for Grok-first: %s" % req)
        self.assertIn('data-g5="shadow"', src, "premise: the + GROK position exists")


if __name__ == "__main__":
    unittest.main(verbosity=2)
