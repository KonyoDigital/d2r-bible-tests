# -*- coding: utf-8 -*-
"""THE PAGE MUST SAY WHICH DOCUMENT IT IS RENDERING, AND THE DOCTOR MUST COMPARE IT TO DISK.

His console EXECS THE WORKING TREE — every save is a deploy. So the question that decides whether
any UI change reached him is: IS THE PAGE IN FRONT OF HIM THE PAGE ON DISK?

Before v3057 nothing could answer it. The console published FOUR version readings and every one of
them described a FILE, not the rendered document:

    ver       the working tree this process imports
    liveVer   what origin/main last shipped
    bibleVer  bible.html's own D2R_BUILD
    agentVer  the agent disk stamp

⚠⚠ AND THE ABSENCE WAS NOT SILENT — IT WAS ANSWERED WRONG, TWICE. On 2026-09-12 and again on
2026-09-13, `liveVer` trailing the tree was read as "the reload did not take", by me, and repeated
through the eyes queue as a finding. It is nothing of the sort: liveVer lagging disk is CORRECT for
every commit not yet pushed, and `test_live_version_is_not_the_working_tree` exists to keep it that
way. A question with no instrument gets answered by the nearest number that resembles one — which
is [[label-outlived-referent]] arriving as a diagnosis.

This file refuses three rots:
  1. the page stops sending its own build stamp;
  2. the server stops publishing it;
  3. the doctor stops calling a mismatch a mismatch, or starts calling an ABSENT stamp agreement.

[[unknown-stays-unknown]] [[the-unjoined-end]] [[inherited-claim-is-not-evidence]]
"""
import io
import os
import re
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _between(src, start, end):
    """The text between two anchors, or None — never a fixed-size window. [[source-window-shortcut]]"""
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else None


class TestTheWindowSaysWhichDocumentItRenders(unittest.TestCase):

    def test_the_page_sends_its_own_build_stamp_on_the_beat(self):
        """PARSED out of the beat payload, not grepped from the file. [[source-reading-guard]]"""
        body = _between(UI, "fetch('/api/ui_alive'", "})")
        self.assertIsNotNone(body, "the ui_alive beat could not be located at all")
        hits = re.findall(r"\bdocVer:\s*\(\(\s*window\.D2R_BUILD\s*&&\s*window\.D2R_BUILD\.id\s*\)"
                          r"\s*\|\|\s*null\s*\)", body)
        print("build-stamp expressions inside the ui_alive payload: %d" % len(hits))
        self.assertEqual(1, len(hits),
                         "the beat must send the document's OWN D2R_BUILD id under the SAME name the status payload publishes it under, falling back to "
                         "null — never to a guess, and never to a server-side version")

    def test_the_server_publishes_it_raw(self):
        app = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        rec = re.findall(r'_UI_BEAT\["docVer"\]\s*=', app)
        pub = re.findall(r'"docVer":\s*_UI_BEAT\.get\("docVer"\)', app)
        print("beat recorders: %d · status publishers: %d" % (len(rec), len(pub)))
        self.assertEqual(1, len(rec), "the beat must record what the page sent")
        self.assertEqual(1, len(pub), "the status payload must publish it RAW, not as a boolean")

    def test_the_doctor_reads_it_and_the_verdicts_are_right(self):
        """The unit, against fixtures — the only half that can prove the JUDGEMENT."""
        import console_doctor as CD
        fn = CD._check_the_window_runs_the_document_on_disk
        real = CD._get
        cases = [
            ({"ver": "v3057", "uiBeat": {"n": 4, "ageS": 2.0, "docVer": "v3057"}},
             CD.OK, "matching stamps must read OK"),
            ({"ver": "v3057", "uiBeat": {"n": 4, "ageS": 2.0, "docVer": "v3051"}},
             CD.MISSING, "a window rendering an OLDER document than disk is the fault this exists for"),
            ({"ver": "v3057", "uiBeat": {"n": 4, "ageS": 2.0}},
             CD.UNKNOWN, "an ABSENT stamp is UNKNOWN and must never read as agreement"),
            ({"ver": "v3057", "uiBeat": {"n": 4, "ageS": 99999.0, "docVer": "v3057"}},
             CD.UNKNOWN, "a stamp from a beat nobody has heard from is UNKNOWN"),
            ({"ver": "v3057", "uiBeat": {"n": 0, "ageS": 2.0, "docVer": "v3057"}},
             CD.UNKNOWN, "a console that never checked in is headless, not healthy"),
            ({"uiBeat": {"n": 4, "ageS": 2.0, "docVer": "v3057"}},
             CD.UNKNOWN, "no disk version means there is nothing to compare against"),
        ]
        try:
            checked = 0
            for payload, want, msg in cases:
                CD._get = (lambda p, _pl=payload: _pl)
                got, why = fn()
                checked += 1
                self.assertEqual(want, got, "%s (got %s: %s)" % (msg, got, why[:160]))
                self.assertTrue(why and why.strip(), "every verdict must carry a reason")
            print("doctor verdicts exercised: %d" % checked)
            self.assertEqual(6, checked)
        finally:
            CD._get = real

    def test_the_row_is_registered_so_something_actually_asks(self):
        """A check nobody calls is [[the-unjoined-end]]."""
        import console_doctor as CD
        src = io.open(os.path.join(HERE, "console_doctor.py"), encoding="utf-8").read()
        hits = re.findall(r'\(\s*"window runs the document on disk"\s*,\s*'
                          r'_check_the_window_runs_the_document_on_disk\s*\)', src)
        print("registrations of the row: %d" % len(hits))
        self.assertEqual(1, len(hits), "the row must be registered in the doctor's own list")


RED_PROOF = [
    {
        "why": "the page stops sending its own build stamp, so nothing on the wire describes the "
               "rendered document and the question goes back to being unanswerable",
        "file": "control_ui.html",
        "find": "            docVer: ((window.D2R_BUILD && window.D2R_BUILD.id) || null),",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the server stops publishing it, which is the unjoined end: measured on one side, "
               "never reaching the surface a supervisor reads",
        "file": "control_app.py",
        "find": '                   "docVer": _UI_BEAT.get("docVer"),',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the doctor calls an OLDER rendered document OK, which is the whole defect wearing "
               "a green light",
        "file": "console_doctor.py",
        "find": '    if str(doc) == str(disk):',
        "replace": '    if True:',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
