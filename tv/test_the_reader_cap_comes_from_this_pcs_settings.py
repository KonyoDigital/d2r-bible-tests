# -*- coding: utf-8 -*-
"""REG-2382 / REG-2383 / REG-2384 — THE READER'S CAP IS THIS PC'S, SAYS WHERE IT CAME FROM, AND A CAP HIT IS A 429.

MEASURED 2026-10-21 on his Mac: the live console (launched through Terminal, TVD_VIA_TERMINAL=1) carried no
TV_INTAKE_* variable at all - neither the LaunchAgent plist nor `launchctl setenv` reaches a Terminal-launched console -
so tv/intake_local.mjs capped at its code default while the caps were believed raised: his live ledger held 20 reads in
the last hour, and the 21st was refused as `subscription hourly cap hit (20/20)` with nothing saying which limit that
was or where it came from.

READ FROM THE CODE, not measured: the refusal left the lane as `200 {"error":"worker-exception"}` (intake.js catches the
throw), and on /api/ask the runner exited 1, so the handler fell through to the website proxy, which reads on the site's
API key - pinned with stub runners in test_a_capped_read_is_answered_429. And `TV_INTAKE_*_MAX=0`, the documented off
switch, never switched anything off: `parseInt('0') || 20` is 20.

THE LAW, DRIVEN through the real runner (`node tv/intake_local.mjs` + the locked functions/api pipeline) on a fixture
ledger (TV_SUB_BUDGET) and a fixture settings file (TV_PC_SETTINGS) - his ledger and his settings are never read or
written, and the claude CLI is a path that does not exist, so no case can spend a read:
  · one rule on every PC: env TV_INTAKE_*_MAX (the override) > this PC's gitignored tv/pc_settings.json > the default;
  · the refusal names the active limit and its source, and a layer holding an unusable value is said, not skipped;
  · a cap hit - intake or ask - answers status 429 with {error, window, used, limit, source, retry_s}, and never
    reaches the CLI; 0 opens the circuit;
  · REG-2390 - with both windows full the refusal is the one that BINDS (the latest retry, an unknown one latest of
    all), with that window's own limit, source and retry_s, and says the other is full too; both 0 switches are named.
That the settings file is ignored by git is test_this_pcs_settings_file_never_travels; that the console hands the
runner's 429 to the board is test_a_capped_runner_reaches_the_board_as_429.

EVERY CASE HERE NEEDS NODE, ON PURPOSE. A PC without node (Dean's: tv/install-tvd.ps1 installs none) skips this law
whole. On this heart2 such a tamper is still filed BLIND there; it is ELSEWHERE once REG-2354 lands, which files
ELSEWHERE only a tamper EVERY case skipped. When two node-free git cases lived here they ran there, so every node-only
proof stayed green "with 2 laws run" - BLIND under either rule, and one BLIND shuts every lock on a PC.
The ledger cases need a POSIX host too (a stand-in CLI script cannot be spawned without a shell on Windows): they
skip on the question heart2's "posix" capability asks, and the three proofs only they catch declare it, so a Windows
PC with node files those three ELSEWHERE, never BLIND.
[[unknown-stays-unknown]] [[the-unjoined-end]]  RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
RUNNER = os.path.join(HERE, "intake_local.mjs")
READER = os.path.join(HERE, "pc_settings.mjs")
LIVE_LEDGER = os.path.join(HERE, ".subscription_budget.json")
LIVE_SETTINGS = os.path.join(HERE, "pc_settings.json")
#: the locked pipeline the runner drives - part of this law's verdict, so part of its proof key
PROOF_NEEDS = ["../functions/api/intake.js", "../functions/api/ask.js"]

LOCATE = {"image": "aGk=", "media_type": "image/jpeg", "kind": "locate"}
SEAMS = ("TV_INTAKE_HOURLY_MAX", "TV_INTAKE_DAILY_MAX", "TV_PC_SETTINGS", "TV_SUB_BUDGET", "TVD_CLAUDE_BIN",
         "TV_INTAKE_MODEL")


def _snap(p):
    try:
        with open(p, "rb") as fh:
            return fh.read()
    except OSError:
        return None


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class _Runner(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="reader-cap-")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.ledger = os.path.join(self.d, "ledger.json")
        self.settings = os.path.join(self.d, "pc_settings.json")
        self.live = (_snap(LIVE_LEDGER), _snap(LIVE_SETTINGS))
        self.addCleanup(self._his_files_untouched)

    def _his_files_untouched(self):
        self.assertEqual((_snap(LIVE_LEDGER), _snap(LIVE_SETTINGS)), self.live,
                         "a case wrote his live tv/.subscription_budget.json or tv/pc_settings.json")

    def calls(self, n, age_s=60.0):
        """n intake calls in the fixture ledger, the newest `age_s` old and one a minute apart (milliseconds, the
        unit this lane writes)."""
        now = time.time() * 1000.0
        rows = [now - (age_s + 60.0 * i) * 1000.0 for i in range(n)]
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            json.dump({"calls": rows}, fh)
        return rows

    def settle(self, values, raw=None):
        with io.open(self.settings, "w", encoding="utf-8") as fh:
            fh.write(raw if raw is not None else json.dumps(values))

    def ask(self, path="/api/intake", body=None, env=None, runner=None, settings=True):
        e = {k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k not in SEAMS}
        e["TV_SUB_BUDGET"] = self.ledger
        if settings:
            e["TV_PC_SETTINGS"] = self.settings
        e["TVD_CLAUDE_BIN"] = os.path.join(self.d, "no-such-claude")   # a cap that fails open spends nothing
        e.update(env or {})
        # node writes UTF-8 to a pipe on every OS; text=True alone decodes with the locale's code page (cp1255 or
        # cp1252 on a Windows PC without UTF-8 mode), which turned the refusal's em dash into mojibake there
        p = subprocess.run([NODE, runner or RUNNER], input=json.dumps({"path": path, "body": body or LOCATE}),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=e,
                           cwd=self.d)
        self.assertEqual(p.returncode, 0, "the runner died: %s" % (p.stderr or "")[-400:])
        out = json.loads(p.stdout)
        try:
            out["json"] = json.loads(out.get("body") or "{}")
        except ValueError:
            out["json"] = {}
        return out

    def assertCapped(self, out, window, used, limit, source):
        self.assertEqual(out.get("status"), 429, "a cap hit answered %r: %r" % (out.get("status"), out.get("body")))
        j = out["json"]
        self.assertEqual(j.get("error"), "subscription-cap")
        self.assertEqual((j.get("window"), j.get("used"), j.get("limit"), j.get("source")),
                         (window, used, limit, source), j.get("message"))
        self.assertIn("limit from " + source, j.get("message", ""), "the refusal does not name the limit's source")
        return j

    def assertAdmitted(self, out):
        """The cap let the call through: it reached the claude CLI, which (by design here) does not exist."""
        self.assertNotEqual(out.get("status"), 429, "refused at the cap: %r" % out.get("body"))
        self.assertIn("claude CLI gave no JSON", out.get("body") or "",
                      "premise: an admitted call did not reach the CLI: %r" % out.get("body"))


class OneRuleOnEveryPC(_Runner):

    def test_without_a_settings_file_the_code_default_caps_and_says_so(self):
        self.calls(20)
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        self.assertIn("(20/20", j["message"])

    def test_this_pcs_settings_file_raises_the_cap(self):
        self.calls(20)
        self.settle({"TV_INTAKE_HOURLY_MAX": 50, "TV_INTAKE_DAILY_MAX": 300})
        self.assertAdmitted(self.ask())

    def test_a_cap_from_the_settings_file_names_the_file(self):
        self.calls(5)
        self.settle({"TV_INTAKE_HOURLY_MAX": 5})
        self.assertCapped(self.ask(), "hour", 5, 5, "the TV_PC_SETTINGS file")

    def test_the_environment_overrides_the_file(self):
        self.calls(20)
        self.settle({"TV_INTAKE_HOURLY_MAX": 50})
        self.assertCapped(self.ask(env={"TV_INTAKE_HOURLY_MAX": "20"}), "hour", 20, 20, "env TV_INTAKE_HOURLY_MAX")
        self.assertAdmitted(self.ask(env={"TV_INTAKE_HOURLY_MAX": "21"}))

    def test_the_daily_cap_reads_the_same_rule(self):
        self.calls(30)
        self.settle({"TV_INTAKE_HOURLY_MAX": 500, "TV_INTAKE_DAILY_MAX": 30})
        self.assertCapped(self.ask(), "day", 30, 30, "the TV_PC_SETTINGS file")

    def test_the_default_file_is_tv_pc_settings_json_beside_the_reader(self):
        """No TV_PC_SETTINGS: a copy of the runner, its reader and the pipeline reads <tv>/pc_settings.json."""
        tv = os.path.join(self.d, "tree", "tv")
        api = os.path.join(self.d, "tree", "functions", "api")
        os.makedirs(tv)
        os.makedirs(api)
        for src in (RUNNER, READER):
            shutil.copy2(src, tv)
        for n in ("intake.js", "ask.js"):
            shutil.copy2(os.path.join(ROOT, "functions", "api", n), api)
        with io.open(os.path.join(tv, "pc_settings.json"), "w", encoding="utf-8") as fh:
            json.dump({"TV_INTAKE_HOURLY_MAX": 3}, fh)
        self.calls(3)
        out = self.ask(runner=os.path.join(tv, "intake_local.mjs"), settings=False)
        self.assertCapped(out, "hour", 3, 3, "tv/pc_settings.json")


class ARefusalIsSaidAndNeverSpends(_Runner):

    def test_zero_opens_the_circuit(self):
        self.calls(0)
        j = self.assertCapped(self.ask(env={"TV_INTAKE_DAILY_MAX": "0"}), "circuit", None, 0,
                              "env TV_INTAKE_DAILY_MAX")
        self.assertIn("circuit open", j["message"])

    def test_an_ask_at_the_cap_is_a_429_too(self):
        """ask.js does not catch the shim's throw: the runner used to exit 1 and the console fell to the website."""
        self.calls(20)
        self.assertCapped(self.ask(path="/api/ask", body={"question": "what can I make?"}),
                          "hour", 20, 20, "the code default")

    def test_retry_names_when_the_oldest_call_ages_out(self):
        rows = self.calls(20, age_s=600.0)                 # the oldest is 600 + 19*60 = 1740 s old
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        want = 3600.0 - (time.time() * 1000.0 - min(rows)) / 1000.0
        self.assertLessEqual(abs(j.get("retry_s") - want), 5, "retry_s %r, expected about %d" % (j.get("retry_s"), want))

    def test_a_layer_holding_nonsense_is_said_and_passed_over(self):
        self.calls(20)
        self.settle({"TV_INTAKE_HOURLY_MAX": "fifty"})
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        self.assertIn("is not a whole number - ignored", j["message"])
        self.settle(None, raw="{not json")
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        self.assertIn("is unreadable", j["message"])

    def test_a_settings_file_saved_with_a_bom_is_read(self):
        """Notepad on Windows saves UTF-8 with a byte-order mark; JSON.parse refuses it raw."""
        self.calls(3)
        self.settle(None, raw="﻿" + json.dumps({"TV_INTAKE_HOURLY_MAX": 3}))
        self.assertCapped(self.ask(), "hour", 3, 3, "the TV_PC_SETTINGS file")


class TheRefusalNamesTheWindowThatBinds(_Runner):
    """REG-2390 - WITH BOTH WINDOWS FULL, THE HOUR WAS ASKED FIRST AND ANSWERED ALONE. 80 reads today, 20 of them this
    hour, at the default caps: the refusal said `(20/20, limit from the code default) — intake paused this hour` with
    retry_s 120 (a read promised two minutes on) while the day cap refused for 20 hours more, and it named the
    hour's source when the day's limit came from another layer. The refusal is the window whose retry is LATEST - its
    own limit, source and retry_s - and its message says the other window is full too. Node only, like every case here:
    nothing in this class needs a shell or a stand-in CLI, so a Windows PC with node runs all of it - read from the
    source, not run on Windows; ask() decodes the runner's UTF-8 itself, and with the pipe decoded as cp1255 or cp1252
    (a Windows code page without UTF-8 mode) the em dash these cases assert became mojibake there."""

    def write(self, rows):
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            json.dump({"calls": rows}, fh)
        return rows

    def test_a_full_day_binds_over_a_full_hour(self):
        now = time.time() * 1000.0
        rows = self.write([now - (60.0 + 180.0 * i) * 1000.0 for i in range(80)])   # 20 in each of the last 4 hours
        j = self.assertCapped(self.ask(), "day", 80, 80, "the code default")
        want = 86400.0 - (time.time() * 1000.0 - min(rows)) / 1000.0                 # the day's oldest read ages out
        self.assertLessEqual(abs(j.get("retry_s") - want), 5,
                             "retry_s %r is not the day's, about %d - the hour's was 120" % (j.get("retry_s"), want))
        self.assertTrue(j["message"].startswith(
            "subscription daily cap hit (80/80, limit from the code default) — intake paused today;"), j["message"])
        self.assertIn("; the hourly cap is full too (20/20, limit from the code default)", j["message"])
        self.assertNotIn("paused this hour", j["message"], "an hour's pause promised while the day cap refuses")

    def test_the_binding_window_names_its_own_source(self):
        now = time.time() * 1000.0
        self.write([now - (60.0 + 180.0 * i) * 1000.0 for i in range(80)])
        self.settle({"TV_INTAKE_DAILY_MAX": 80})
        j = self.assertCapped(self.ask(env={"TV_INTAKE_HOURLY_MAX": "20"}), "day", 80, 80, "the TV_PC_SETTINGS file")
        self.assertTrue(j["message"].startswith(
            "subscription daily cap hit (80/80, limit from the TV_PC_SETTINGS file) — intake paused today;"),
            j["message"])
        self.assertIn("; the hourly cap is full too (20/20, limit from env TV_INTAKE_HOURLY_MAX)", j["message"])

    def test_an_hour_that_frees_last_binds_over_a_full_day(self):
        """The rule is the LATEST retry, not 'the day wins': the day's oldest read ages out in 10 minutes and the
        hour's in half an hour, so the hour binds - and says the day is full too."""
        now = time.time() * 1000.0
        hour = [now - (60.0 + 90.0 * i) * 1000.0 for i in range(20)]                 # the oldest 1770 s old
        older = [now - (7200.0 + 1000.0 * k) * 1000.0 for k in range(59)] + [now - 85800.0 * 1000.0]
        self.write(hour + older)
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        want = 3600.0 - (time.time() * 1000.0 - min(hour)) / 1000.0
        self.assertLessEqual(abs(j.get("retry_s") - want), 5,
                             "retry_s %r is not the hour's, about %d - the day's was 600" % (j.get("retry_s"), want))
        self.assertTrue(j["message"].startswith(
            "subscription hourly cap hit (20/20, limit from the code default) — intake paused this hour;"),
            j["message"])
        self.assertIn("; the daily cap is full too (80/80, limit from the code default)", j["message"])

    def test_an_unknown_retry_is_never_a_promise(self):
        """A row the window cannot age - a number saved as a string, as a hand edit leaves it - is counted, and its
        window's retry is unknown (_retryS never guesses). Another window's known retry must not stand in for it: no
        retry_s, and no 'paused this hour' while the day is full too."""
        now = time.time() * 1000.0
        hour = [str(int(now - (60.0 + 90.0 * i) * 1000.0)) for i in range(20)]
        older = [now - (7200.0 + 1000.0 * k) * 1000.0 for k in range(60)]
        self.write(hour + older)
        j = self.assertCapped(self.ask(), "hour", 20, 20, "the code default")
        self.assertIsNone(j.get("retry_s"), "a time was promised while the hour's own retry cannot be known")
        self.assertIn("; the daily cap is full too (80/80, limit from the code default)", j["message"])
        self.assertNotIn("paused this hour", j["message"])

    def test_when_no_full_window_can_say_when_the_day_is_named(self):
        """Both retries unknown is a tie, and a tie goes to the day - the longer window - with no time and no pause
        length promised."""
        now = time.time() * 1000.0
        hour = [str(int(now - (60.0 + 90.0 * i) * 1000.0)) for i in range(20)]
        older = [str(int(now - (7200.0 + 1000.0 * k) * 1000.0)) for k in range(60)]
        self.write(hour + older)
        j = self.assertCapped(self.ask(), "day", 80, 80, "the code default")
        self.assertIsNone(j.get("retry_s"))
        self.assertTrue(j["message"].startswith(
            "subscription daily cap hit (80/80, limit from the code default) — intake paused;"), j["message"])
        self.assertIn("; the hourly cap is full too (20/20, limit from the code default)", j["message"])

    def test_both_switches_at_zero_are_both_named(self):
        self.calls(0)
        self.settle({"TV_INTAKE_DAILY_MAX": 0})
        j = self.assertCapped(self.ask(env={"TV_INTAKE_HOURLY_MAX": "0"}), "circuit", None, 0,
                              "env TV_INTAKE_HOURLY_MAX")
        self.assertIn("TV_INTAKE_HOURLY_MAX=0, limit from env TV_INTAKE_HOURLY_MAX", j["message"])
        self.assertIn("TV_INTAKE_DAILY_MAX=0, limit from the TV_PC_SETTINGS file", j["message"],
                      "raising the hourly switch would still leave intake off, and the refusal does not say why")


@unittest.skipUnless(os.name == "posix", "a stand-in claude CLI cannot be spawned without a shell on Windows - "
                                         "UNMEASURED there (its proofs declare needs: posix)")
class TheLedgerKeepsTheOtherLanesRows(_Runner):
    """REG-2385 - tv/.subscription_budget.json is ALSO tv_diablo's vision meter (SECONDS, _sub_budget_record). Recording
    an intake call kept only rows younger than a day in MILLISECONDS - none of the vision lane's - so every intake read
    erased the vision meter. A stand-in CLI that answers like claude lets a call be ADMITTED and RECORDED here."""

    def setUp(self):
        super().setUp()
        self.cli = os.path.join(self.d, "claude-stand-in")
        with io.open(self.cli, "w", encoding="utf-8") as fh:
            fh.write("#!/usr/bin/env node\nprocess.stdout.write('{\"found\":false,\"x0\":0,\"y0\":0,\"x1\":0,\"y1\":0}');\n")
        os.chmod(self.cli, 0o755)

    def rows(self):
        with io.open(self.ledger, encoding="utf-8") as fh:
            return json.load(fh)["calls"]

    def test_a_recorded_intake_call_keeps_the_vision_lanes_rows(self):
        now = time.time()
        vision = [now - 300.0, now - 200.0, now - 100.0]            # what tv_diablo writes: seconds
        mine = [(now - 50.0) * 1000.0, (now - 40.0) * 1000.0]       # what this lane writes: milliseconds
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            json.dump({"calls": vision + mine}, fh)
        ino = os.stat(self.ledger).st_ino
        out = self.ask(env={"TVD_CLAUDE_BIN": self.cli})
        self.assertEqual(out.get("status"), 200, "premise: the stand-in call was not admitted: %r" % out.get("body"))
        after = self.rows()
        self.assertEqual([r for r in after if r < 1e11], vision, "an intake read erased the vision lane's rows")
        self.assertEqual(len([r for r in after if r >= 1e11]), 3, "this lane's own call was not recorded")
        self.assertNotEqual(os.stat(self.ledger).st_ino, ino,
                            "the ledger was rewritten in place - a torn write resets both lanes' caps")

    def test_the_vision_lanes_rows_do_not_count_against_the_intake_cap(self):
        """The rule today, kept: this lane's cap counts the reads THIS lane made. 25 vision reads in the hour must not
        refuse an intake read at a cap of 20 (whether they should is a ruling nobody has made)."""
        now = time.time()
        with io.open(self.ledger, "w", encoding="utf-8") as fh:
            json.dump({"calls": [now - 60.0 * (i + 1) for i in range(25)]}, fh)
        out = self.ask(env={"TVD_CLAUDE_BIN": self.cli})
        self.assertEqual(out.get("status"), 200, "vision reads refused an intake read: %r" % out.get("body"))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-2382 - the reader never opens this PC's settings file: the caps are env-or-default again",
        "file": "pc_settings.mjs",
        "find": "    if (!existsSync(path)) return { label, values: {}, error: null };\n",
        "replace": "    return { label, values: {}, error: null };\n",
        "matches": 1,
    },
    {
        "why": "REG-2382 - the settings file outranks the environment: an explicit override stops overriding",
        "file": "pc_settings.mjs",
        "find": "    if (n !== null) return { value: n, source: 'env ' + name, notes };\n",
        "replace": "    if (n !== null && !Object.prototype.hasOwnProperty.call(settings.values, name)) return { value: n, source: 'env ' + name, notes };\n",
        "matches": 1,
    },
    {
        "why": "REG-2382 - the default file is not beside the reader: no PC finds its tv/pc_settings.json",
        "file": "pc_settings.mjs",
        "find": "export const SETTINGS_FILE = 'pc_settings.json';\n",
        "replace": "export const SETTINGS_FILE = '.pc_settings.json';\n",
        "matches": 1,
    },
    {
        "why": "REG-2382 - the refusal stops naming where its limit came from",
        "file": "intake_local.mjs",
        "find": "  return 'limit from ' + limit.source + (limit.notes.length ? '; ' + limit.notes.join('; ') : '');\n",
        "replace": "  return 'limit ' + limit.value;\n",
        "matches": 1,
    },
    {
        "why": "REG-2382 - an unusable layer is passed over in silence",
        "file": "pc_settings.mjs",
        "find": "    notes.push(settings.label + ' is unreadable (' + settings.error + ') - ignored');\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2382 - a settings file Notepad saved (UTF-8 with a BOM) is unreadable on Windows",
        "file": "pc_settings.mjs",
        "find": "    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-2383 - a cap hit is answered 200 with an error body again (intake) and kills the runner (ask)",
        "file": "intake_local.mjs",
        "find": "if (CAP_HIT) {\n  process.stdout.write(JSON.stringify({\n    status: 429,\n",
        "replace": "if (CAP_HIT && false) {\n  process.stdout.write(JSON.stringify({\n    status: 429,\n",
        "matches": 1,
    },
    {
        "why": "REG-2383 - an ask at the cap rejects past the runner again: exit 1, and the console falls to the website",
        "file": "intake_local.mjs",
        "find": "  if (!CAP_HIT) throw e;",
        "replace": "  throw e;",
        "matches": 1,
    },
    {
        "why": "REG-2383 - the refusal no longer says when a call will be allowed again",
        "file": "intake_local.mjs",
        "find": "  const t = sorted[used - max];\n",
        "replace": "  const t = sorted[sorted.length - 1];\n",
        "matches": 1,
    },
    {
        "why": "REG-2384 - TV_INTAKE_*_MAX=0 no longer opens the circuit (the old parseInt(...) || 20 read it as 20)",
        "file": "pc_settings.mjs",
        "find": "  if (typeof raw === 'number') return Number.isInteger(raw) && raw >= 0 ? raw : null;\n  const s = String(raw == null ? '' : raw).trim();\n  return /^\\d+$/.test(s) ? parseInt(s, 10) : null;\n",
        "replace": "  if (typeof raw === 'number') return Number.isInteger(raw) && raw > 0 ? raw : null;\n  const s = String(raw == null ? '' : raw).trim();\n  return /^\\d+$/.test(s) && parseInt(s, 10) > 0 ? parseInt(s, 10) : null;\n",
        "matches": 1,
    },
    {
        "why": "REG-2385 - recording an intake call erases the vision lane's seconds rows from the shared ledger again",
        "file": "intake_local.mjs",
        "find": "    if (n >= MS_FLOOR) return now - n < DAY_MS;\n    const age = now / 1000 - n;\n    return age >= -60 && age < 86400;\n",
        "replace": "    return now - n < DAY_MS;\n",
        "matches": 1,
        "needs": "posix",
    },
    {
        "why": "REG-2385 - the intake cap starts counting the vision lane's reads (a rule change nobody ruled on)",
        "file": "intake_local.mjs",
        "find": "  const calls = (state.calls || []).filter((t) => now - t < DAY_MS);\n",
        "replace": "  const calls = (state.calls || []).map((t) => (t < 1e11 ? t * 1000 : t)).filter((t) => now - t < DAY_MS);\n",
        "matches": 1,
        "needs": "posix",
    },
    {
        "why": "REG-2385 - the ledger is rewritten in place again: a torn write reads as {} and resets both lanes' caps",
        "file": "intake_local.mjs",
        "find": "    renameSync(tmp, BUDGET_PATH);\n    return;\n",
        "replace": "    throw new Error('written in place');\n",
        "matches": 1,
        "needs": "posix",
    },
    {
        "why": "REG-2390 - the hour is asked first and answered alone again: with both windows full the refusal names the "
               "hour and its two-minute retry while the day cap refuses for 20 hours more",
        "file": "intake_local.mjs",
        "find": "  const bind = full.reduce((a, b) => (_late(b) >= _late(a) ? b : a));\n",
        "replace": "  const bind = full[0];\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - the day always wins when both windows are full: an hour that frees last is said as the day, "
               "with a retry ten minutes away while the hour refuses for half an hour",
        "file": "intake_local.mjs",
        "find": "  const bind = full.reduce((a, b) => (_late(b) >= _late(a) ? b : a));\n",
        "replace": "  const bind = full[full.length - 1];\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - the other full window goes unsaid: the refusal reads as if only one cap were in the way",
        "file": "intake_local.mjs",
        "find": "  const others = full.filter((w) => w !== bind);\n",
        "replace": "  const others = [];\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - a known retry outranks an unknown one: the refusal promises a time while a full window's own "
               "retry cannot be known",
        "file": "intake_local.mjs",
        "find": "  return w.retryS === null ? Infinity : w.retryS;\n",
        "replace": "  return w.retryS === null ? -1 : w.retryS;\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - with a window's retry unknown and the day full too, the refusal still says 'paused this hour'",
        "file": "intake_local.mjs",
        "find": "  const pause = bind.retryS === null && others.length ? 'intake paused' : 'intake paused ' + bind.words[1];\n",
        "replace": "  const pause = 'intake paused ' + bind.words[1];\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - with both switches at 0 the circuit names only the hourly one: raising it leaves intake off, "
               "and nothing says why",
        "file": "intake_local.mjs",
        "find": ".filter(([, l]) => l.value <= 0);\n",
        "replace": ".filter(([, l]) => l.value <= 0).slice(0, 1);\n",
        "matches": 1,
    },
    {
        "why": "REG-2390 - a tie goes to the hour: with neither full window able to say when, the shorter one is named",
        "file": "intake_local.mjs",
        "find": "  const bind = full.reduce((a, b) => (_late(b) >= _late(a) ? b : a));\n",
        "replace": "  const bind = full.reduce((a, b) => (_late(b) > _late(a) ? b : a));\n",
        "matches": 1,
    },
]
