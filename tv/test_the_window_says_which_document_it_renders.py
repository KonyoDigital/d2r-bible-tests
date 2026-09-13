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

    def test_the_page_sends_the_stamp_the_SERVER_gave_it(self):
        """PARSED out of the beat payload. [[source-reading-guard]]

        ⚠⚠ THIS ASSERTION USED TO NAME THE WRONG GLOBAL AND STILL PASSED. v3057 read
        `window.D2R_BUILD.id` — assigned in bible.html, a DIFFERENT document — so on this page it
        was always undefined and docVer was always null. The test was green because it only asked
        whether the EXPRESSION existed, never whether it could produce a value.
        """
        body = _between(UI, "fetch('/api/ui_alive'", "})")
        self.assertIsNotNone(body, "the ui_alive beat could not be located at all")
        hits = re.findall(r"\bdocVer:\s*\(\s*window\.__DOC_VER__\s*\|\|\s*null\s*\)", body)
        print("served-stamp reads inside the ui_alive payload: %d" % len(hits))
        self.assertEqual(1, len(hits),
                         "the beat must report the stamp THE SERVER GAVE THIS DOCUMENT, falling "
                         "back to null — never a global belonging to another page")
        stray = re.findall(r"D2R_BUILD", re.sub(r"/\*.*?\*/", "", body, flags=re.S))
        print("D2R_BUILD references left in the payload: %d" % len(stray))
        self.assertEqual(0, len(stray),
                         "D2R_BUILD belongs to bible.html and is undefined here — reading it is "
                         "how this field shipped inert")

    def test_the_served_document_actually_carries_the_stamp(self):
        """THE ONE THAT COULD NOT HAVE BEEN FOOLED — it reads the BYTES the server hands out.

        A source-text assertion said the join existed while the value was structurally always
        null. This calls the real serving path and looks for the stamp in what comes back.
        [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]
        """
        import control_app as ca
        sig = ca.doc_signature()
        self.assertTrue(sig, "the console document could not be signed at all")
        body = ca._read_ui()
        self.assertGreater(len(body), 100000, "the served document is implausibly small")
        found = re.findall(rb'window\.__DOC_VER__\s*=\s*"([^"]+)"', body)
        print("stamps found in the SERVED bytes: %d -> %s"
              % (len(found), [f.decode() for f in found]))
        self.assertEqual(1, len(found), "the served document must carry exactly one stamp")
        self.assertEqual(sig, found[0].decode(),
                         "the stamp served must be the signature of the bytes served")
        self.assertEqual(1, body.count(b"<head>"), "injection must not duplicate the head")
        self.assertTrue(body.startswith(b"<!DOCTYPE html>"), "injection must not disturb the doctype")

    def test_the_signature_moves_when_the_document_moves(self):
        """A stamp that never changes cannot detect a stale window. Proven on a real edit."""
        import control_app as ca, tempfile, os as _os, io as _io
        a = ca.doc_signature()
        src = _io.open(ca.UI_PATH, encoding="utf-8").read()
        d = tempfile.mkdtemp(prefix="docsig.")
        try:
            p2 = _os.path.join(d, "control_ui.html")
            _io.open(p2, "w", encoding="utf-8").write(src + "\n<!-- one byte of drift -->\n")
            b = ca.doc_signature(p2)
            print("signature before: %s\nsignature after : %s" % (a, b))
            self.assertTrue(a and b, "both signatures must be readable")
            self.assertNotEqual(a, b, "an edited document MUST sign differently, or a stale "
                                      "window is undetectable")
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_the_server_publishes_it_raw(self):
        app = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        rec = re.findall(r'_UI_BEAT\["docVer"\]\s*=', app)
        pub = re.findall(r'"docVer":\s*_UI_BEAT\.get\("docVer"\)', app)
        print("beat recorders: %d · status publishers: %d" % (len(rec), len(pub)))
        self.assertEqual(1, len(rec), "the beat must record what the page sent")
        self.assertEqual(1, len(pub), "the status payload must publish it RAW, not as a boolean")

    def test_the_doctor_reads_it_and_the_verdicts_are_right(self):
        """The unit, against fixtures — the only half that can prove the JUDGEMENT.

        ⚠ BOTH SIDES ARE STUBBED. The doctor now signs the document ON DISK rather than reading a
        version off the payload, so a fixture that only fakes the payload is comparing a made-up
        stamp against this repo's real one and will fail for the wrong reason.
        """
        import console_doctor as CD
        import control_app as _ca
        fn = CD._check_the_window_runs_the_document_on_disk
        real_get, real_sig = CD._get, _ca.doc_signature
        SIG = "v9999+deadbeefcafe"
        cases = [
            ({"uiBeat": {"n": 4, "ageS": 2.0, "docVer": SIG}}, (lambda p=None: SIG),
             CD.OK, "a window holding the signature this server would serve reads OK"),
            ({"uiBeat": {"n": 4, "ageS": 2.0, "docVer": "v9999+0000feedface"}}, (lambda p=None: SIG),
             CD.MISSING, "a window holding an OLDER signature is the fault this exists for"),
            ({"uiBeat": {"n": 4, "ageS": 2.0, "docVer": "v9999"}}, (lambda p=None: SIG),
             CD.MISSING, "a bare version is NOT the signature — a label must not pass as bytes"),
            ({"uiBeat": {"n": 4, "ageS": 2.0}}, (lambda p=None: SIG),
             CD.UNKNOWN, "an ABSENT stamp is UNKNOWN and must never read as agreement"),
            ({"uiBeat": {"n": 4, "ageS": 99999.0, "docVer": SIG}}, (lambda p=None: SIG),
             CD.UNKNOWN, "a stamp from a beat nobody has heard from is UNKNOWN"),
            ({"uiBeat": {"n": 0, "ageS": 2.0, "docVer": SIG}}, (lambda p=None: SIG),
             CD.UNKNOWN, "a console that never checked in is headless, not healthy"),
            ({"uiBeat": {"n": 4, "ageS": 2.0, "docVer": SIG}}, (lambda p=None: None),
             CD.UNKNOWN, "an unsignable document on disk is UNKNOWN, never agreement"),
        ]
        try:
            checked = 0
            for payload, sig, want, msg in cases:
                CD._get = (lambda p, _pl=payload: _pl)
                _ca.doc_signature = sig
                got, why = fn()
                checked += 1
                self.assertEqual(want, got, "%s (got %s: %s)" % (msg, got, why[:170]))
                self.assertTrue(why and why.strip(), "every verdict must carry a reason")
            print("doctor verdicts exercised: %d" % checked)
            self.assertEqual(7, checked)
        finally:
            CD._get, _ca.doc_signature = real_get, real_sig

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
        "why": "the server stops stamping the document it serves, so every window reports null and "
               "the row can never say anything but UNKNOWN — the exact way v3057 shipped inert",
        "file": "control_app.py",
        "find": '    tag = (\'<script>window.__DOC_VER__=%s;</script>\' % json.dumps(sig)).encode("utf-8")',
        "replace": '    tag = b""',
        "matches": 1,
    },
    {
        "why": "the page stops reading the stamp it was given, which is the same joint broken from "
               "the other end",
        "file": "control_ui.html",
        "find": "            docVer: (window.__DOC_VER__ || null),",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the signature drops the byte hash and becomes a LABEL again, so an unstamped save "
               "to control_ui.html - which bump_version does not stamp - is undetectable",
        "file": "control_app.py",
        "find": '    return "%s+%s" % (_app_ver() or "v?", h[:12])',
        "replace": '    return "%s" % (_app_ver() or "v?")',
        "matches": 1,
    },
    {
        "why": "the doctor calls an older rendered document OK, which is the whole defect wearing "
               "a green light",
        "file": "console_doctor.py",
        "find": '    if str(doc) == str(disk):',
        "replace": '    if True:',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
