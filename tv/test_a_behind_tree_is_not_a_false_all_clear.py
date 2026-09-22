# -*- coding: utf-8 -*-
"""v3416 — A BEHIND TREE IS NOT A FALSE ALL-CLEAR.

Found by the second eye at FULL REACH, and only there: at the shipped 9,000-char cap the same eye
on the same commit answered `cannot-tell` with 0 findings; at 25,074 chars it returned 5, and
three were real. Two of them are this gate's subject, both in v3413's own doctor row:

1. **The proxy.** `_check_the_resume_agrees_with_git_right_now` answered MISSING whenever the file
   said *"Nothing is waiting to be pushed"* and `head != origin`. But `derived()` writes that
   sentence whenever `origin/main..HEAD` is empty — which is ALSO true when HEAD is strictly
   BEHIND origin/main. So a perfectly correct file was called a false all-clear on every behind
   tree, and behind is the ordinary state the moment the Windows box or the other family pushes
   before this machine pulls. The sentence is a claim about UNPUSHED COMMITS; count them.
   [[feedback-verify-not-proxy]]

2. **The blanket exemption.** `if said_head == "UNKNOWN" ... return OK` returned BEFORE the
   all-clear was ever examined, so a file whose fingerprint git could not fill read fine forever
   no matter what else it claimed. UNKNOWN read as fine. [[unknown-stays-unknown]]

⚠ THIS GATE DRIVES THE SHIPPED ROW. It binds `console_doctor.ROOT` to a temp directory holding a
crafted RESUME_HERE.md and injects a fake `git_quiet`, so every verdict comes from the real
function against a state this repo cannot be put into on demand — never from reading its source,
and never from his working tree. [[feedback-fixtures-never-touch-live-data]]
"""
import io
import os
import shutil
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd  # noqa: E402

ROW = dict(cd.CHECKS)["the resume agrees with git"]
ALL_CLEAR = "Nothing is waiting to be pushed"


class _Res(object):
    def __init__(self, out, rc=0):
        self.stdout, self.returncode = out, rc


def _fake_git(head, origin, ahead, rc_head=0, rc_origin=0, rc_ahead=0):
    """A git that answers exactly what a scenario needs, including failing."""
    def run(argv, **kw):
        a = list(argv)
        if "rev-list" in a:
            return _Res(ahead, rc_ahead)
        if a[-1] == "HEAD":
            return _Res(head, rc_head)
        return _Res(origin, rc_origin)
    m = types.ModuleType("git_quiet")
    m.run = run
    return m


class TestABehindTreeIsNotAFalseAllClear(unittest.TestCase):

    def setUp(self):
        self._dir = tempfile.mkdtemp(prefix="resume_row_")
        self._root = cd.ROOT
        cd.ROOT = self._dir
        self._gq = sys.modules.get("git_quiet")

    def tearDown(self):
        cd.ROOT = self._root
        if self._gq is not None:
            sys.modules["git_quiet"] = self._gq
        else:
            sys.modules.pop("git_quiet", None)
        shutil.rmtree(self._dir, ignore_errors=True)

    def _ask(self, said_head, said_origin, head, origin, ahead, clear=True, **rc):
        body = "<!-- fp: head=%s origin=%s ver=v9999 -->\n" % (said_head, said_origin)
        if clear:
            body += "\n✅ %s — as of the fetch above.\n" % ALL_CLEAR
        io.open(os.path.join(self._dir, "RESUME_HERE.md"), "w",
                encoding="utf-8").write(body)
        sys.modules["git_quiet"] = _fake_git(head, origin, ahead, **rc)
        return ROW()

    # ---- the baseline: the law must still fire on the thing it was written for -------------

    def test_BASELINE_an_ahead_tree_claiming_all_clear_is_still_caught(self):
        st, why = self._ask("aaa", "bbb", "aaa", "bbb", "2")
        self.assertEqual(st, cd.MISSING,
                         "the false all-clear is no longer caught at all — every case below "
                         "would then pass for the wrong reason")
        self.assertIn("2 unpushed", why)

    # ---- the defect ------------------------------------------------------------------------

    def test_a_BEHIND_tree_claiming_all_clear_is_CORRECT(self):
        """HEAD an ancestor of origin: 0 unpushed, hashes differ, the sentence is TRUE."""
        st, why = self._ask("aaa", "bbb", "aaa", "bbb", "0")
        self.assertNotEqual(st, cd.MISSING,
                            "a tree that is merely BEHIND origin was called a false all-clear — "
                            "the sentence is a claim about unpushed commits and there are none. "
                            "This is the v3416 defect: hash-equality used as a proxy for a count")

    def test_an_UNKNOWN_fingerprint_does_not_exempt_the_sentence(self):
        st, why = self._ask("UNKNOWN", "bbb", "aaa", "bbb", "3")
        self.assertEqual(st, cd.MISSING,
                         "an UNKNOWN fingerprint waved the all-clear through unexamined — honest "
                         "about the fingerprint, silent about the false sentence beside it")
        self.assertIn("3 unpushed", why)

    def test_an_UNKNOWN_fingerprint_with_a_TRUE_sentence_is_OK_and_says_it_checked(self):
        st, why = self._ask("UNKNOWN", "UNKNOWN", "aaa", "bbb", "0")
        self.assertEqual(st, cd.OK)
        self.assertIn("checked anyway", why,
                      "the UNKNOWN arm does not say that it examined the sentence, so a reader "
                      "cannot tell an exemption from an inspection")

    # ---- a count that cannot be read is UNKNOWN, never zero --------------------------------

    def test_a_failed_count_is_UNKNOWN(self):
        st, _ = self._ask("aaa", "bbb", "aaa", "bbb", "", rc_ahead=1)
        self.assertEqual(st, cd.UNKNOWN)

    def test_a_count_that_is_not_a_number_is_UNKNOWN(self):
        st, why = self._ask("aaa", "bbb", "aaa", "bbb", "fatal: bad revision")
        self.assertEqual(st, cd.UNKNOWN,
                         "git answered prose where a count was expected and the row treated it "
                         "as a number")
        self.assertIn("not a count", why)

    def test_a_failed_hash_read_is_still_UNKNOWN(self):
        st, _ = self._ask("aaa", "bbb", "", "bbb", "0", rc_head=1)
        self.assertEqual(st, cd.UNKNOWN)

    # ---- and the ordinary states still answer as before ------------------------------------

    def test_an_exact_match_is_OK(self):
        st, why = self._ask("aaa", "bbb", "aaa", "bbb", "0", clear=False)
        self.assertEqual(st, cd.OK)

    def test_a_fingerprint_behind_the_repo_is_UNMEASURED_not_a_fault(self):
        st, why = self._ask("old", "bbb", "aaa", "bbb", "0", clear=False)
        self.assertEqual(st, cd.UNMEASURED,
                         "a resume derived one commit ago is normal between a commit and the "
                         "next bump, and must not read as a fault")

    def test_no_fingerprint_at_all_is_UNKNOWN(self):
        io.open(os.path.join(self._dir, "RESUME_HERE.md"), "w",
                encoding="utf-8").write("no derived block here\n")
        sys.modules["git_quiet"] = _fake_git("aaa", "bbb", "0")
        st, _ = ROW()
        self.assertEqual(st, cd.UNKNOWN)

    def test_a_missing_resume_is_UNKNOWN(self):
        sys.modules["git_quiet"] = _fake_git("aaa", "bbb", "0")
        st, _ = ROW()
        self.assertEqual(st, cd.UNKNOWN)


RED_PROOF = [
    {
        "why": "v3416 - THE PROXY, RESTORED. Judging the all-clear by hash inequality is exactly "
               "the pre-fix behaviour: it calls a tree that is merely BEHIND origin a false "
               "all-clear, which is the ordinary state whenever another machine pushes first.",
        "file": "console_doctor.py",
        "find": "    if claims_clear and ahead > 0:",
        "replace": "    if claims_clear and head != origin:",
        "matches": 1,
    },
    {
        "why": "v3416 - THE BLANKET EXEMPTION, RESTORED. Returning OK the moment the fingerprint "
               "carries UNKNOWN skips the all-clear sentence entirely, so a file git could not "
               "fingerprint reads fine no matter what else it claims.",
        "file": "console_doctor.py",
        "find": '    fp_unknown = (said_head == "UNKNOWN" or said_origin == "UNKNOWN")\n',
        "replace": '    fp_unknown = (said_head == "UNKNOWN" or said_origin == "UNKNOWN")\n'
                   '    if fp_unknown:\n'
                   '        return OK, ("exempt")\n',
        "matches": 1,
    },
    {
        "why": "v3416 - A BAD COUNT READ AS ZERO. Treating an unparseable rev-list answer as 0 "
               "makes every all-clear look true, which is the quiet direction and the one nobody "
               "notices.",
        "file": "console_doctor.py",
        # ⚠ v3416 — THIS TAMPER IS DELIBERATELY PARSE-SAFE. The first cut sliced the head off a
        # multi-line call and left its continuation lines dangling, so heart2 answered INVALID:
        # a gate reddened by a SyntaxError proves nothing about the law. This one is a complete,
        # compiling statement that changes only the BEHAVIOUR under test.
        "find": '        ahead = int((_a.stdout or "").strip())',
        "replace": '        ahead = int((_a.stdout or "").strip()) if (_a.stdout or "").strip().isdigit() else 0',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
