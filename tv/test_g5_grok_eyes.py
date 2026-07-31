#!/usr/bin/env python3
"""G5 Grok Eyes — subscription CLI lane safety tests (no API keys)."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import g5_grok_eyes as g5  # noqa: E402


class TestG5OffByDefault(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()
        for k in ("TV_G5_GROK_EYES", "XAI_API_KEY", "G5_XAI_KEY", "G4_XAI_KEY"):
            os.environ.pop(k, None)
        self._td = tempfile.mkdtemp()
        self._p_state = mock.patch.object(g5, "_STATE_FILE", os.path.join(self._td, "g5.state"))
        self._p_budget = mock.patch.object(g5, "_BUDGET_PATH", os.path.join(self._td, "budget.json"))
        self._p_state.start()
        self._p_budget.start()
        g5._CALL_LOG.clear()
        g5._STATS.update({
            "calls": 0, "ok": 0, "errors": 0, "skipped_budget": 0,
            "shadow": 0, "primary": 0, "last": None, "last_error": None,
            "lane": "subscription-cli",
        })

    def tearDown(self):
        self._p_state.stop()
        self._p_budget.stop()
        os.environ.clear()
        os.environ.update(self._env)

    def test_default_mode_off(self):
        self.assertEqual(g5.mode_intent(), "off")
        self.assertFalse(g5.is_primary())

    def test_vision_noop_when_off(self):
        with mock.patch.object(g5, "has_subscription", return_value=True):
            with mock.patch.object(g5, "subprocess") as sp:
                self.assertIsNone(g5.g5_vision_read("/nope.jpg"))
                sp.run.assert_not_called()
        self.assertEqual(g5._STATS["calls"], 0)

    def test_no_subscription_forces_effective_off(self):
        g5.set_mode("primary")
        with mock.patch.object(g5, "has_subscription", return_value=False):
            self.assertEqual(g5.mode_intent(), "primary")
            self.assertEqual(g5.mode(), "off")
            self.assertFalse(g5.is_on())

    def test_status_lane_is_subscription_not_api(self):
        st = g5.status()
        self.assertEqual(st.get("lane"), "subscription-cli")
        power = (st.get("power") or "").lower()
        self.assertTrue("grok -p" in power or "oidc" in power or "supergrok" in power)
        self.assertIn("no api", power)
        self.assertNotIn("api.x.ai", power)
        self.assertNotIn("bearer", power)

    def test_api_keys_stripped_from_env(self):
        os.environ["XAI_API_KEY"] = "should-never-be-used"
        os.environ["G5_XAI_KEY"] = "nope"
        env, stripped = g5._grok_env()
        self.assertNotIn("XAI_API_KEY", env)
        self.assertNotIn("G5_XAI_KEY", env)
        self.assertIn("XAI_API_KEY", stripped)
        self.assertIn("G5_XAI_KEY", stripped)

    def test_loose_parse(self):
        j = g5._loose_parse('noise {"names":["Shako"],"scene":"loot","conf":0.9} tail')
        self.assertIsNotNone(j)
        self.assertEqual(j["names"], ["Shako"])

    def test_set_mode_persists(self):
        g5.set_mode("shadow")
        with open(os.path.join(self._td, "g5.state"), encoding="utf-8") as fh:
            d = json.load(fh)
        self.assertEqual(d.get("mode"), "shadow")
        self.assertEqual(d.get("lane"), "subscription-cli")


class TestV1381GrokAuthorize(unittest.TestCase):
    """v1381.2 — ⚡ Authorize: no-spam login spawn; installer/CLI gates."""

    def test_status_exposes_auth_fields(self):
        st = g5.status()
        for k in ("cliInstalled", "authorized", "needsLogin", "needsInstall", "loginInflight"):
            self.assertIn(k, st)

    def test_start_login_no_cli_short_circuits(self):
        with mock.patch.object(g5, "_grok_bin", return_value=""):
            out = g5.start_login()
        self.assertFalse(out.get("ok"))
        self.assertEqual(out.get("reason"), "no-cli")
        self.assertFalse(out.get("started"))

    def test_start_login_already_authorized_no_spawn(self):
        with mock.patch.object(g5, "_grok_bin", return_value="/fake/grok"):
            with mock.patch.object(g5, "_subscription_logged_in", return_value=True):
                with mock.patch.object(g5.subprocess, "Popen") as pop:
                    out = g5.start_login()
        self.assertTrue(out.get("ok"))
        self.assertEqual(out.get("reason"), "already-authorized")
        self.assertFalse(out.get("started"))
        pop.assert_not_called()

    def test_needs_login_when_cli_without_auth(self):
        with mock.patch.object(g5, "_grok_bin", return_value="/fake/grok"):
            with mock.patch.object(g5, "_subscription_logged_in", return_value=False):
                st = g5.status()
        self.assertTrue(st.get("cliInstalled"))
        self.assertTrue(st.get("needsLogin"))
        self.assertFalse(st.get("authorized"))


class TestG5CliCall(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()
        os.environ.pop("TV_G5_GROK_EYES", None)
        self._td = tempfile.mkdtemp()
        self._p_state = mock.patch.object(g5, "_STATE_FILE", os.path.join(self._td, "s.state"))
        self._p_budget = mock.patch.object(g5, "_BUDGET_PATH", os.path.join(self._td, "b.json"))
        self._p_state.start()
        self._p_budget.start()
        # tiny fake image file
        self._img = os.path.join(self._td, "f.jpg")
        with open(self._img, "wb") as fh:
            fh.write(b"\xff\xd8\xff\xd9")

    def tearDown(self):
        self._p_state.stop()
        self._p_budget.stop()
        os.environ.clear()
        os.environ.update(self._env)

    def test_force_uses_grok_p_not_http(self):
        class R:
            returncode = 0
            stdout = '{"names":["Test"],"scene":"loot","conf":0.8,"area":"","tz":[]}'
            stderr = ""

        with mock.patch.object(g5, "has_subscription", return_value=True):
            with mock.patch.object(g5, "_grok_bin", return_value="/fake/grok"):
                with mock.patch.object(g5.subprocess, "run", return_value=R()) as run:
                    out = g5.g5_vision_read(self._img, force=True)
        self.assertIsNotNone(out)
        self.assertEqual(out["names"], ["Test"])
        self.assertEqual(out.get("_lane"), "subscription-cli")
        argv = run.call_args[0][0]
        self.assertEqual(argv[0], "/fake/grok")
        self.assertIn("-p", argv)
        # must not have been an HTTP call — no urllib
        env = run.call_args[1].get("env") or {}
        self.assertNotIn("XAI_API_KEY", env)


class TestDualIntakeReceivers(unittest.TestCase):
    """v1380.1 — /api/intake dual receiver order by G5 mode (subscription CLIs only)."""

    def setUp(self):
        self._td = tempfile.mkdtemp()
        # minimal dual files so path.isfile is true
        open(os.path.join(self._td, "intake_local.mjs"), "w").close()
        open(os.path.join(self._td, "intake_grok_sub.mjs"), "w").close()
        # import helper from control_app without starting the server
        import control_app as ca  # noqa: E402
        self.ca = ca

    def test_off_claude_only(self):
        labs = [l for l, _ in self.ca._intake_dual_runners(self._td, "off")]
        self.assertEqual(labs, ["subscription"])

    def test_shadow_claude_then_grok(self):
        labs = [l for l, _ in self.ca._intake_dual_runners(self._td, "shadow")]
        self.assertEqual(labs, ["subscription", "grok-subscription"])

    def test_primary_grok_then_claude(self):
        labs = [l for l, _ in self.ca._intake_dual_runners(self._td, "primary")]
        self.assertEqual(labs, ["grok-subscription", "subscription"])

    def test_local_off_empty(self):
        self.assertEqual(self.ca._intake_dual_runners(self._td, "primary", local_on=False), [])

    def test_primary_without_grok_file_falls_to_empty_not_wrong_lane(self):
        os.unlink(os.path.join(self._td, "intake_grok_sub.mjs"))
        # no grok file → primary cannot lead with grok; helper returns [] for primary branch
        # (mode==primary and not isfile(grok) skips the primary block, lands in else → claude)
        labs = [l for l, _ in self.ca._intake_dual_runners(self._td, "primary")]
        self.assertEqual(labs, ["subscription"])


class TestG5ChronicleLane(unittest.TestCase):
    """v1514 — the second eye on the Chronicle.

    Konyo wants Grok reading the SAME thing "identically". Identically is both the requirement and
    the trap: the two lanes must answer the same question in the same SHAPE or their answers cannot
    be compared — but they must not share prompt WORDING, or they inherit the same blind spots and
    the independent second opinion is theatre."""

    def _read(self, raw, kind="chronicle-uniques"):
        with mock.patch.object(g5, "g5_vision_read", return_value=raw):
            return g5.g5_chronicle_read("/tmp/f.jpg", kind)

    def test_it_answers_in_the_SAME_SHAPE_as_the_primary_lane(self):
        r = self._read({"found": ["Windforce"], "notFound": ["Shako"], "conf": 0.8})
        for field in ("ledger", "found", "notFound", "sets", "witness", "printed", "read", "conf"):
            self.assertIn(field, r, field + " is part of the v1510 contract both lanes must speak")
        self.assertEqual(r["lane"], "grok")

    def test_the_prompt_is_its_OWN_words_not_a_copy_of_claudes(self):
        # ★ shared wording ⇒ shared blind spots ⇒ a second opinion that is theatre. The two prompts
        # must state the same CONTRACT while sharing no long stretch of phrasing.
        worker = os.path.join(os.path.dirname(HERE), "functions", "api", "intake.js")
        with open(worker, encoding="utf-8") as fh:
            claude_side = fh.read()
        mine = g5.CHRONICLE_VISION_PROMPT
        # the contract IS shared — same fields, same refusals
        for shared in ("stateVisible", "wrongTab", "printedFound", "notFound"):
            self.assertIn(shared, mine)
            self.assertIn(shared, claude_side)
        # ...the sentences are not. Any 12-word run copied verbatim means one blind spot, not two eyes.
        words = [w for w in mine.replace("\\n", " ").split() if w]
        runs = [" ".join(words[i:i + 12]) for i in range(0, max(0, len(words) - 12))]
        copied = [r for r in runs if r in claude_side]
        self.assertEqual(copied, [], "verbatim phrasing shared with the primary lane: " + str(copied[:1]))

    def test_a_dead_lane_returns_NONE_not_an_empty_page(self):
        # ★ "grok didn't run" and "grok saw nothing" must stay different facts, or a dead second
        # lane reads as silent agreement
        with mock.patch.object(g5, "g5_vision_read", return_value=None):
            self.assertIsNone(g5.g5_chronicle_read("/tmp/f.jpg", "chronicle-uniques"))

    def test_it_makes_the_SAME_refusals(self):
        r = self._read({"found": ["Windforce"], "stateVisible": False})
        self.assertEqual(r["found"], [])
        self.assertEqual(r["note"], "no-found-state")
        r2 = self._read({"found": ["Windforce"], "wrongTab": True})
        self.assertEqual(r2["found"], [])
        self.assertEqual(r2["note"], "wrong-ledger")

    def test_the_ledger_it_was_ASKED_for_is_the_ledger_it_reports(self):
        self.assertEqual(self._read({"found": []}, "chronicle-sets")["ledger"], "sets")
        self.assertEqual(self._read({"found": []}, "chronicle-uniques")["ledger"], "uniques")

    def test_the_printed_witness_means_the_same_thing_in_both_lanes(self):
        agree = self._read({"found": ["A", "B"], "notFound": ["C"], "printedFound": 2, "printedTotal": 3})
        self.assertEqual(agree["witness"], "agree")
        partial = self._read({"found": ["A", "B"], "notFound": [], "printedFound": 2, "printedTotal": 403})
        self.assertEqual(partial["witness"], "none", "a partial page can never claim a witness")

    def test_the_prompt_carries_the_unattended_danger_and_the_ledger_slot(self):
        self.assertIn("unattended", g5.CHRONICLE_VISION_PROMPT)
        self.assertIn("{ledger}", g5.CHRONICLE_VISION_PROMPT)
        self.assertIn("wrongTab", g5.CHRONICLE_VISION_PROMPT)


if __name__ == "__main__":
    unittest.main()
