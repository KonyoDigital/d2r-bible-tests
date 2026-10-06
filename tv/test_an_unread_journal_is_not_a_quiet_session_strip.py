# -*- coding: utf-8 -*-
"""REG-1805 — AN UNREAD JOURNAL IS NOT A QUIET SESSION STRIP.

The session-health strip treats an empty tally list as a night with no
tallies yet, an empty lease map as free, and a missing re-fire count as
zero. While the console is on, that is what it paints. An unread journal
is that same empty strip: the poll already says verdict unknown. The
strip said "no tallies yet", "free", and "0 re-fires".

A measured empty night still says those three. A landed tally is still a
tally. A held lease is still held. A counted re-fire is still that count.
The verdict word already falls through to unknown. An unread walk says
the journal was not read.

Nothing here reads his journal. RED_PROOF below. [[unknown-stays-unknown]]
"""
import json
import os
import subprocess
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

_NOT_READ = "the journal was not read"
_ZERO_REFIRES = "0 re-fires \u00b7 fired 0"


def _strip(on=True, verdict="idle", tab_summary=None, leases=None,
           refires=0, fired=0, omit_counts=False, omit_health=False):
    with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
        ui = fh.read()
    start = ui.find("    // v946 — SESSION HEALTH strip\n")
    end = ui.find("    } catch (eH) {}", start)
    if start < 0 or end < 0:
        raise AssertionError("the session-health strip is not in control_ui.html")
    fn = ui[start:end + len("    } catch (eH) {}")]
    if "\x00" in fn:
        raise AssertionError("the strip slice crossed the null byte")
    if omit_health:
        st = {}
    else:
        sh = {}
        if verdict is not None:
            sh["verdict"] = verdict
        if tab_summary is not None:
            sh["tabSummary"] = tab_summary
        if leases is not None:
            sh["leases"] = leases
        if not omit_counts:
            sh["refires"] = refires
            sh["driverFired"] = fired
        st = {"sessionHealth": sh}
    js = (
        "var window = {};\n"
        "function paintStrip(st, on){\n"
        "  var els = {};\n"
        "  function make(){\n"
        "    var classes = {};\n"
        "    return {textContent:'', classList:{\n"
        "      remove:function(){for (var i=0;i<arguments.length;i++) delete classes[arguments[i]];},\n"
        "      add:function(c){classes[c]=true;}\n"
        "    }, classes:classes};\n"
        "  }\n"
        "  ['sess-health','sh-tabs','sh-lease','sh-refire','sh-verdict'].forEach(function(id){els[id]=make();});\n"
        "  function $(id){return els[id];}\n"
        + fn
        + "\n  return {tabs:els['sh-tabs'].textContent, lease:els['sh-lease'].textContent,\n"
        "    refire:els['sh-refire'].textContent, verdict:els['sh-verdict'].textContent};\n"
        "}\n"
        "process.stdout.write(JSON.stringify(paintStrip("
        + json.dumps(st) + ", " + ("true" if on else "false") + ")));\n"
    )
    got = subprocess.run(
        ["node", "-"], input=js.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if got.returncode != 0:
        raise AssertionError(got.stderr.decode("utf-8", "replace")[:600])
    return json.loads(got.stdout.decode("utf-8"))


class AnUnreadJournalIsNotAQuietSessionStrip(unittest.TestCase):

    def test_a_measured_empty_night_on_air_still_says_no_tallies(self):
        row = _strip(on=True, verdict="idle", tab_summary={}, leases={},
                     refires=0, fired=0)
        self.assertEqual(row["tabs"], "no tallies yet")
        self.assertEqual(row["lease"], "free")
        self.assertEqual(row["refire"], _ZERO_REFIRES)
        self.assertEqual(row["verdict"], "idle")
        self.assertNotIn("was not read", row["tabs"])
        self.assertNotIn("was not read", row["lease"])
        self.assertNotIn("was not read", row["refire"])

    def test_a_measured_empty_night_off_air_stays_the_dash(self):
        row = _strip(on=False, verdict="idle", tab_summary={}, leases={},
                     refires=0, fired=0)
        self.assertEqual(row["tabs"], "\u2014")
        self.assertEqual(row["lease"], "free")
        self.assertEqual(row["refire"], _ZERO_REFIRES)
        self.assertEqual(row["verdict"], "idle")
        self.assertNotIn("was not read", row["tabs"])

    def test_an_unread_journal_on_air_is_not_a_quiet_strip(self):
        row = _strip(on=True, verdict="unknown", tab_summary={}, leases={},
                     omit_counts=True)
        self.assertEqual(row["tabs"], _NOT_READ)
        self.assertEqual(row["lease"], _NOT_READ)
        self.assertEqual(row["refire"], _NOT_READ)
        self.assertEqual(row["verdict"], "unknown")
        self.assertNotIn("no tallies", row["tabs"])
        self.assertNotEqual(row["lease"], "free")
        self.assertNotIn("0 re-fires", row["refire"])
        self.assertNotIn("fired 0", row["refire"])

    def test_an_unread_journal_off_air_is_not_free(self):
        row = _strip(on=False, verdict="unknown", tab_summary={}, leases={},
                     omit_counts=True)
        self.assertEqual(row["tabs"], _NOT_READ)
        self.assertEqual(row["lease"], _NOT_READ)
        self.assertEqual(row["refire"], _NOT_READ)
        self.assertNotEqual(row["tabs"], "\u2014")
        self.assertNotEqual(row["lease"], "free")
        self.assertNotIn("0 re-fires", row["refire"])
        self.assertEqual(row["verdict"], "unknown")

    def test_an_unread_zero_is_still_not_a_count(self):
        row = _strip(on=True, verdict="unknown", tab_summary={}, leases={},
                     refires=0, fired=0)
        self.assertEqual(row["tabs"], _NOT_READ)
        self.assertEqual(row["lease"], _NOT_READ)
        self.assertEqual(row["refire"], _NOT_READ)
        self.assertNotEqual(row["refire"], _ZERO_REFIRES)
        self.assertEqual(row["verdict"], "unknown")

    def test_a_landed_tally_is_still_a_tally(self):
        row = _strip(
            on=True, verdict="ok",
            tab_summary={"gems": "\u00d73"},
            leases={"runes": {"owner": "engine-driver"}},
            refires=2, fired=5)
        self.assertEqual(row["tabs"], "gems \u00d73")
        self.assertEqual(row["lease"], "runes\u2192engine-driver")
        self.assertEqual(row["refire"], "2 re-fires \u00b7 fired 5")
        self.assertEqual(row["verdict"], "session ok")
        self.assertNotIn("was not read", row["tabs"])
        self.assertNotIn("was not read", row["lease"])
        self.assertNotIn("was not read", row["refire"])

    def test_two_tallies_still_join(self):
        row = _strip(
            on=True, verdict="ok",
            tab_summary={"gems": "\u00d73", "runes": "\u00d71"},
            refires=1, fired=1)
        self.assertIn("gems \u00d73", row["tabs"])
        self.assertIn("runes \u00d71", row["tabs"])
        self.assertIn(" \u00b7 ", row["tabs"])
        self.assertNotIn("was not read", row["tabs"])

    def test_a_miss_is_still_a_miss(self):
        row = _strip(on=True, verdict="miss", tab_summary={"gems": "MISS"},
                     refires=0, fired=0)
        self.assertEqual(row["tabs"], "gems MISS")
        self.assertEqual(row["verdict"], "miss \u00b7 needs re-read")
        self.assertNotIn("was not read", row["tabs"])
        self.assertNotIn("was not read", row["verdict"])

    def test_a_partial_is_still_partial(self):
        row = _strip(on=True, verdict="partial",
                     tab_summary={"gems": "\u00d72", "runes": "MISS"},
                     refires=0, fired=1)
        self.assertEqual(row["verdict"], "partial \u00b7 some MISS")
        self.assertIn("gems \u00d72", row["tabs"])
        self.assertIn("runes MISS", row["tabs"])
        self.assertNotIn("was not read", row["tabs"])
        self.assertEqual(row["refire"], "0 re-fires \u00b7 fired 1")

    def test_an_unread_walk_still_shows_a_tally_it_has(self):
        row = _strip(
            on=True, verdict="unknown",
            tab_summary={"gems": "\u00d73"},
            leases={"runes": {"owner": "engine-driver"}},
            refires=4, fired=4)
        self.assertEqual(row["tabs"], "gems \u00d73")
        self.assertEqual(row["lease"], "runes\u2192engine-driver")
        self.assertEqual(row["refire"], _NOT_READ)
        self.assertNotIn("no tallies", row["tabs"])
        self.assertNotEqual(row["lease"], "free")
        self.assertNotIn("4 re-fires", row["refire"])
        self.assertEqual(row["verdict"], "unknown")

    def test_a_missing_session_health_is_still_the_quiet_strip(self):
        row = _strip(on=True, omit_health=True)
        self.assertEqual(row["tabs"], "no tallies yet")
        self.assertEqual(row["lease"], "free")
        self.assertEqual(row["refire"], _ZERO_REFIRES)
        self.assertEqual(row["verdict"], "idle")
        self.assertNotIn("was not read", row["tabs"])

    def test_the_strip_asks_this_look(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            ui = fh.read()
        self.assertIn("var shUnread = (sh.verdict === 'unknown');", ui)
        self.assertIn(
            ": (shUnread ? 'the journal was not read' : (on ? 'no tallies yet' : '\u2014'));",
            ui)
        self.assertIn(": (shUnread ? 'the journal was not read' : 'free');", ui)
        self.assertIn("if (rf) rf.textContent = shUnread", ui)
        self.assertNotIn(
            "if (rf) rf.textContent = (sh.refires || 0) + ' re-fires",
            ui)


RED_PROOF = [
    {
        "why": "REG-1805 - an unread journal is painted as a quiet session strip",
        "file": "control_ui.html",
        "find": "      var shUnread = (sh.verdict === 'unknown');\n",
        "replace": "      var shUnread = false;\n",
        "matches": 1,
    },
    {
        "why": "REG-1805 - a measured empty night is painted as a journal that was not read",
        "file": "control_ui.html",
        "find": "      var shUnread = (sh.verdict === 'unknown');\n",
        "replace": "      var shUnread = (tabKeys.length === 0);\n",
        "matches": 1,
    },
    {
        "why": "REG-1805 - the screen calls an unread journal a night with no tallies yet",
        "file": "control_ui.html",
        "find": "        : (shUnread ? 'the journal was not read' : (on ? 'no tallies yet' : '\u2014'));\n",
        "replace": "        : (on ? 'no tallies yet' : '\u2014');\n",
        "matches": 1,
    },
    {
        "why": "REG-1805 - the screen calls an unread journal a free lease",
        "file": "control_ui.html",
        "find": "        : (shUnread ? 'the journal was not read' : 'free');\n",
        "replace": "        : 'free';\n",
        "matches": 1,
    },
    {
        "why": "REG-1805 - the screen calls an unread journal zero re-fires",
        "file": "control_ui.html",
        "find": "      if (rf) rf.textContent = shUnread\n"
                "        ? 'the journal was not read'\n"
                "        : ((sh.refires || 0) + ' re-fires \u00b7 fired ' + (sh.driverFired || 0));\n",
        "replace": "      if (rf) rf.textContent = (sh.refires || 0) + ' re-fires \u00b7 fired ' + (sh.driverFired || 0);\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
