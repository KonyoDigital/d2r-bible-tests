# -*- coding: utf-8 -*-
"""The restore's two halves are joined by a MEASUREMENT, not by a comment.

`ledger_restore.proposal_from()` builds what a restore would put back, and the board's
`window.chronicleApply` is the only door it may travel through — the console never writes the
grail itself. Between them sat one sentence in a test:

    "the board reads proposal.wouldAdd and nothing else"

That is a belief about another file, asserted nowhere. The existing law checks the proposal's shape
against that sentence, so renaming the key on EITHER side leaves it green while the restore
silently applies nothing — and `ledger_restore_apply` would report the board's own `ok` for a
payload the board read as empty. [[the-unjoined-end]] [[plumbing-with-no-tap]]

⚠ WHY THIS AND NOT AN END-TO-END APPLY. `chronicle_apply` calls into the live board WINDOW; it
cannot be sandboxed in Python. And the board is currently whole — the live plan reports
missingTotal 0 against 446 in backup and 446 on board — so there is nothing to put back. Proving
an apply for real would mean DELETING one of his finds to manufacture a gap. This joins the two
halves without writing a byte to his ledger; the end-to-end apply stays honestly UNPROVEN.
"""
import io
import os
import re
import sys
import tempfile
import json
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import ledger_restore as LR  # noqa: E402

ROUTE = {"id": "abc", "p": "main", "m": "owner", "pfx": ""}


def _board_apply_body():
    """The board's own chronicleApply, brace-matched. -> str

    ⚠ BOTH ENDS ANCHORED. A fixed-size slice past the region reads as ABSENT and would make this
    law report a missing key that is simply beyond the window. [[source-reading-guard]]
    """
    h = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
    m = re.search(r"window\.chronicleApply\s*=\s*function\s*\(", h)
    if not m:
        return ""
    i = m.start()
    j = h.find("{", i)
    depth = 0
    k = j
    while k < len(h):
        if h[k] == "{":
            depth += 1
        elif h[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return h[i:k + 1]


def _code_only(js):
    """The CODE, with prose stripped. A half named only in a COMMENT is not a half the board
    spends. [[measured-true-read-wrong]]"""
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    return re.sub(r"(?m)//.*$", " ", js)


def _board_apply_inner():
    """Where the apply ACTUALLY reads the proposal. -> str (code only)

    ⚠⚠ THE OUTER FUNCTION SPENDS NOTHING. `chronicleApply` unwraps `proposal.wouldAdd` into `add`,
    declares its RESULT shape `{uniques: [], sets: [], skipped: []}` and delegates to
    `_chronicleApplyInner(proposal, add, res)`. The half names therefore appear in the outer body
    because of the RESULT object — so a law asserting "the half is named in chronicleApply" passes
    whatever the board does with `add`, which is green for the wrong reason. Found by the Codex
    eye on the shipped v3153. [[the-unjoined-end]]"""
    h = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()
    m = re.search(r"window\._chronicleApplyInner\s*=\s*function\s*\(", h)
    if not m:
        return ""
    i = m.start()
    j = h.find("{", i)
    depth, k = 0, j
    while k < len(h):
        if h[k] == "{":
            depth += 1
        elif h[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return _code_only(h[i:k + 1])


class TestTheRestoreProposalReachesTheBoard(unittest.TestCase):

    def setUp(self):
        d = tempfile.mkdtemp()
        io.open(os.path.join(d, "ledger_x.json"), "w", encoding="utf-8").write(
            json.dumps({"route": ROUTE,
                        "ledger": {"foundLog": {"Lost": "d"}, "setPieces": ["SetLost"]}}))
        self.prop = LR.proposal_from(LR.plan(ROUTE, {"foundLog": {}, "setPieces": []}, d))
        self.body = _board_apply_body()

    def test_the_board_really_defines_the_door_this_restore_posts_through(self):
        self.assertTrue(self.body,
                        "window.chronicleApply was not found in bible.html at all — the restore "
                        "posts through a door that does not exist, and every shape assertion "
                        "about it is about nothing")

    def test_the_key_the_restore_writes_is_the_key_the_board_reads(self):
        """The join. Rename it on either side and the restore applies nothing, quietly."""
        self.assertIn("wouldAdd", self.prop,
                      "the proposal no longer carries `wouldAdd`: %s" % sorted(self.prop))
        self.assertRegex(
            self.body, r"proposal\s*&&\s*proposal\.wouldAdd",
            "the board no longer reads `proposal.wouldAdd`, but the restore still writes it. The "
            "apply would post a payload the board reads as empty and report the board's own ok.")

    def test_every_half_the_restore_fills_is_a_half_the_board_spends(self):
        """`wouldAdd` holding a key the board never looks at is a silently dropped store."""
        halves = sorted(self.prop.get("wouldAdd") or {})
        self.assertTrue(halves, "the proposal fills no halves at all")
        # ⚠ THE OUTER BODY IS NOT THE TEST. It names every half in its RESULT object, so asking it
        # whether a half is "spent" answers yes whatever the board does with `add`.
        inner = _board_apply_inner()
        self.assertTrue(inner, "window._chronicleApplyInner is gone — the apply delegates nowhere")
        self.assertIn("_chronicleApplyInner", _code_only(self.body),
                      "chronicleApply no longer delegates, so the half it reads is somewhere this "
                      "law does not follow")
        # ⚠ A WORD BOUNDARY, NOT A SUBSTRING. `"add.uniques" in inner` is satisfied by
        # `add.uniquesX` — heart2 caught this proof BLIND on its first drill, tampering the real
        # read and watching the assertion sail through its own defeat.
        # ⚠ AND `add` MUST STILL COME FROM `wouldAdd`. Found by the Codex eye on v3161: rename the
        # key in the OUTER function and `add` becomes {}, so every restore is dropped — while this
        # test stays green, because `add.uniques` is still written in the inner body and the
        # delegation still stands. The file's other law catches that rename, so the GATE goes red
        # either way; this assertion is what makes THIS test true on its own rather than true
        # because of its neighbour. [[the-unjoined-end]]
        self.assertRegex(
            _code_only(self.body), r"add\s*=\s*\(\s*proposal\s*&&\s*proposal\.wouldAdd",
            "`add` is no longer bound from proposal.wouldAdd, so every half below is read from an "
            "empty object and the restore is dropped in silence")
        unread = [h for h in halves
                  if not re.search(r"add\.%s\b" % re.escape(h), inner)]
        self.assertEqual(
            unread, [],
            "the restore fills %r and the apply never READS add.%s — those names would be handed "
            "over and dropped without a word." % (halves, ", add.".join(unread) if unread else ""))


RED_PROOF = [
    {
        'why': "renames the key the restore writes, so the board's `proposal.wouldAdd` reads undefined and the apply puts back NOTHING while reporting the board's own ok",
        'file': 'ledger_restore.py',
        'find': 'return {"wouldAdd": add, "source": "ledger_restore", "file": plan_out.get("file")}',
        'replace': 'return {"toAdd": add, "source": "ledger_restore", "file": plan_out.get("file")}',
        'matches': 1,
    },
    {
        'why': 'renames the key the BOARD reads, the same break from the other side — the half this law exists to catch, because no python test can see it',
        'file': '../bible.html',
        'find': 'var add = (proposal && proposal.wouldAdd) || {};',
        'replace': 'var add = (proposal && proposal.toAdd) || {};',
        'matches': 1,
    },
    {
        'why': 'stops the apply READING add.uniques, so a restore hands the names over and the board drops them — while the outer chronicleApply still NAMES uniques in its result object, which is what made the old assertion green for the wrong reason',
        'file': '../bible.html',
        'find': '    (add.uniques || []).forEach(function(row){',
        'replace': '    (add.uniquesX || []).forEach(function(row){',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
