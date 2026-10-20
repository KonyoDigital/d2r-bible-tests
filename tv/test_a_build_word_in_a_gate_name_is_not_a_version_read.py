# -*- coding: utf-8 -*-
"""v3775 (REG-2296) — A GENERIC WORD IN A GATE'S NAME IS NOT A READ OF THE VERSION.

On a coherent bump a gate still reruns when its NAME speaks of the version. The rule matched
build|title|status|fresh as well, so test_the_item_edit_tab_builds_magic_and_rare_items,
test_a_fresh_install_is_not_a_lost_store, test_a_title_is_not_an_owner and 19 more reran on every
bump although their scripts never name the version. The name rule keeps version|stamp|bump|ship|resume
(case-insensitive). A gate whose script speaks of the version still reruns through the script rule,
and a module that only reads the version still reruns through the reader rule.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import gate_ledger as GL  # noqa: E402

_QUIET = "import sys\nprint('ok')\nsys.exit(0)\n"
_LOUD = "import sys\nVERSION = 'x'\nsys.exit(0)\n"


class AGenericNameWordIsNotAVersionRead(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="vername.")
        self.addCleanup(shutil.rmtree, self.root, True)
        os.makedirs(os.path.join(self.root, "tv"))
        for name, text in (("quiet.py", _QUIET), ("loud.py", _LOUD)):
            with io.open(os.path.join(self.root, "tv", name), "w", encoding="utf-8") as fh:
                fh.write(text)
        self.led = GL.Ledger(path=os.path.join(self.root, "none.json"), probes={"python": "3"})

    def _reads(self, name, script="tv/quiet.py", inputs=()):
        return self.led.reads_version({"script": script, "inputs": list(inputs)}, self.root, name)

    def test_build_title_status_fresh_names_carry(self):
        for name in ("test_the_item_edit_tab_builds_magic_and_rare_items", "test_a_title_is_not_an_owner",
                     "test_the_status_breakdown_names_its_blind_spot", "test_a_fresh_install_is_not_a_lost_store"):
            self.assertFalse(self._reads(name), "%s reruns on its name alone" % name)

    def test_the_version_words_still_rerun(self):
        for word in ("version", "stamp", "bump", "ship", "resume"):
            name = "test_a_%s_gate" % word
            self.assertTrue(self._reads(name), "%s no longer reruns on a bump" % name)

    def test_the_name_rule_ignores_case(self):
        self.assertTrue(self._reads("test_a_Version_gate"))

    def test_a_script_that_names_the_version_still_reruns(self):
        self.assertTrue(self._reads("test_a_build_gate", script="tv/loud.py"))

    def test_a_reader_module_still_reruns(self):
        self.assertTrue(self._reads("test_a_build_gate", inputs=("tv/version_stamp_gate.py",)))

    def test_wilson_of_these_attacks_meets_the_bar(self):
        import confidence
        self.assertGreaterEqual(len(RED_PROOF), 10)
        self.assertGreaterEqual(confidence.wilson_lower(len(RED_PROOF), len(RED_PROOF)), 0.722)


RED_PROOF = [
    {"why": 'build in a name reruns again', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume|build", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'title in a name reruns again', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume|title", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'status in a name reruns again', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume|status", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'fresh in a name reruns again', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume|fresh", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'a version name carries', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'a stamp name carries', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'a bump name carries', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|ship|resume", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'a ship name carries', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|resume", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'a resume name carries', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship", re.I)  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": 'the name rule is case-sensitive', "file": "gate_ledger.py",
     "find": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume", re.I)  # STAMP-NAME-NARROW\n',
     "replace": '_VERSION_NAME = re.compile(r"version|stamp|bump|ship|resume")  # STAMP-NAME-NARROW\n', "matches": 1},
    {"why": "the name rule is off", "file": "gate_ledger.py",
     "find": "        if _VERSION_NAME.search(str(name or \"\")):  # STAMP-VERSION-NAME\n",
     "replace": "        if False:  # STAMP-VERSION-NAME\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
