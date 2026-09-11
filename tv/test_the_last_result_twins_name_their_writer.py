# -*- coding: utf-8 -*-
"""#69 — THE TWO LAST-RESULT STORES MUST NAME WHAT PRODUCED THEM.

MEASURED 2026-09-11 by `verdict_provenance.py`: 44 stores · ANSWERS 6 · PARTIAL 4 · SILENT 16 ·
REFERENCE 17 · UNKNOWN 1. `chron_last_result.json` and `vault_last_result.json` were both SILENT.

These two are DELIBERATE TWINS — `_vault_result_save` says in its own docstring that it "mirrors
_chron_result_save deliberately" — so they are stamped together. Fixing one and leaving its
declared mirror for a later sweep is this repo's most repeated shape. [[sweep-dont-ask]]

⚠ THE PAYLOAD IS FLAT — `{result, [proposal,] savedTs}` — and every reader takes a NAMED field, so
the stamp belongs on the BLOB. A reel-keyed store needs it INSIDE each row instead, or it gains a
phantom row (REG-972). Same helper, opposite right answer, decided by the shape. This law pins the
shape as well as the presence.

⚠ THE STAMP MUST BE SWALLOWED. Both saves are already best-effort because "losing the cache must
never take down the sweep that produced it" — and a LABEL must never become the thing that loses it.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()


def _body(case, start, end, what):
    """The slice between two ANCHORS — never a fixed window. [[source-window-shortcut]]"""
    i = SRC.find(start)
    case.assertGreater(i, 0, "anchor %r is gone — this law lost its target (%s)" % (start, what))
    j = SRC.find(end, i + len(start))
    case.assertGreater(j, i, "closing anchor %r not found (%s)" % (end, what))
    return SRC[i:j]


class BothTwinsStampTheirPayload(unittest.TestCase):

    CASES = (("chron_last_result", "def _chron_result_save():", "os.replace(tmp, _CHRON_RESULT_PATH)"),
             ("vault_last_result", "def _vault_result_save():", "_VAULT_RESULT_PATH)"))

    def test_each_twin_stamps_the_blob_it_writes(self):
        for store, start, end in self.CASES:
            body = _body(self, start, end, store)
            m = re.search(r"payload\s*=\s*_PV\.stamp\(\s*payload\s*,\s*by\s*=\s*[\"']([\w.]+)[\"']",
                          body)
            self.assertIsNotNone(
                m, "%s is written without a provenance stamp, so a result persisted by an older "
                   "sweep cannot be told from today's" % store)
            self.assertTrue(m.group(1),
                            "%s stamps an empty producer" % store)

    def test_each_twin_names_ITS_OWN_store(self):
        """A shared `extra` would make both rows claim the same origin, and would also collapse the
        two red-proof anchors into one. [[label-outlived-referent]]"""
        seen = {}
        for store, start, end in self.CASES:
            body = _body(self, start, end, store)
            m = re.search(r'extra\s*=\s*\{\s*["\']store["\']\s*:\s*["\']([\w.]+)["\']', body)
            self.assertIsNotNone(m, "%s does not tag which store its stamp is for" % store)
            self.assertEqual(store, m.group(1),
                             "%s tags its stamp as %r" % (store, m.group(1)))
            self.assertNotIn(m.group(1), seen,
                             "%s and %s tag the SAME store name" % (store, seen.get(m.group(1))))
            seen[m.group(1)] = store

    def test_the_stamp_cannot_cost_the_result(self):
        """A best-effort save must not acquire a way to fail. [[unknown-stays-unknown]]"""
        for store, start, end in self.CASES:
            body = _body(self, start, end, store)
            i = body.find("_PV.stamp(")
            self.assertGreater(i, 0)
            head = body[:i]
            self.assertIn("try:", head,
                          "%s stamps outside a try, so a failure in the LABEL would lose the "
                          "sweep's result — the expensive thing this store exists to keep" % store)

    def test_the_stamp_goes_on_the_blob_not_a_row(self):
        """These payloads are FLAT. A per-row stamp here would be the mirror mistake of REG-972."""
        for store, start, end in self.CASES:
            body = _body(self, start, end, store)
            self.assertNotIn("stamp_row(", body,
                             "%s uses the per-ROW stamp on a flat payload — the readers take "
                             "named fields, so the block belongs on the blob" % store)


RED_PROOF = [
    {
        "why": "un-stamping the chronicle's last result puts it back to SILENT: a proposal "
               "persisted by an older sweep reads exactly like one from today's",
        "file": "control_app.py",
        "find": '            payload = _PV.stamp(payload, by="control_app", extra={"store": "chron_last_result"})\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "un-stamping the vault's last result puts its declared TWIN back to SILENT — the "
               "sibling-left-behind shape this sweep exists to prevent",
        "file": "control_app.py",
        "find": '            payload = _PV.stamp(payload, by="control_app", extra={"store": "vault_last_result"})\n',
        "replace": "",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
