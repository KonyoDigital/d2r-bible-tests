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
        unread = [h for h in halves if h not in self.body]
        self.assertEqual(
            unread, [],
            "the restore fills %r and the board's apply never names %r — those names would be "
            "handed over and dropped without a word." % (halves, unread))


RED_PROOF = [
    {
        "why": "renames the key the restore writes, so the board's `proposal.wouldAdd` reads "
               "undefined and the apply puts back NOTHING while reporting the board's own ok",
        "file": "ledger_restore.py",
        "find": 'return {"wouldAdd": add, "source": "ledger_restore", "file": plan_out.get("file")}',
        "replace": 'return {"toAdd": add, "source": "ledger_restore", "file": plan_out.get("file")}',
        "matches": 1,
    },
    {
        "why": "renames the key the BOARD reads, the same break from the other side — the half "
               "this law exists to catch, because no python test can see it",
        "file": "../bible.html",
        "find": "var add = (proposal && proposal.wouldAdd) || {};",
        "replace": "var add = (proposal && proposal.toAdd) || {};",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
