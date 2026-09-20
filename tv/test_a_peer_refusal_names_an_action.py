#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3384 — A REFUSAL THAT NAMES NO ACTION IS A REFUSAL THE READER CANNOT USE.

Konyo, looking at THE FLEET: *"fleet still not working"*.

MEASURED on his live console the same hour, and the panel was not lying — the peer was:
    machine LAPTOP-QNFL860M · OFFLINE · last reported 2026-09-19T03:38:36Z (~26h)
    ver v3342 · sets 131/135 · uniques 0/403 · maskWhy "no board window"
so "THEY HAVE - YOU DO NOT" drew the sentence "not published - no board window" and no names.

⚠ EVERY WORD OF THAT WAS TRUE AND NONE OF IT WAS ACTIONABLE. He cannot tell from it whether to
wait, to ask that machine to open its board, or to do nothing at all — which is exactly what his
#35 ruling forbids a surface to do.

⚠⚠ AND THE FIX FOR THE WORDING WAS ALREADY SHIPPED, ON THE WRONG SIDE OF THE WIRE. v3359 (#112)
made the give-up name WHICH state instead of one unactionable "no board window". But `maskWhy` is
written by the OTHER machine and arrives verbatim, so a peer that never updates keeps sending the
old sentence for ever and NO fix on this side can reach it. That is [[the-unjoined-end]] across a
machine boundary: both halves correct, the join never made.

WHAT CLOSES IT is that the capability is VERSIONED. v3379 taught the console to mint a mask from
the board's banked hand-over, so a machine on v3379+ can publish names with no board window open
at all. The reader already holds the peer's version in the SAME roster row it reads `maskWhy`
from — it was simply not looking at it.

WHAT THIS FILE PINS:
  * a peer below v3379 is told it cannot publish until it updates, naming BOTH versions
  * a peer at or above v3379 is not accused of anything
  * a peer whose version is absent or unparseable is UNKNOWN — never "too old"
  * fleet_compare actually FORWARDS the version and the verdict (the join)
  * the panel PREFERS the actionable reason and still falls back to the peer's own sentence
"""

import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

import control_app as CA

APP = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _js_code_only(src):
    """JS with /* ... */ comments blanked, line count preserved.

    ⚠ MY OWN EXPLANATION NAMES THE THING IT EXPLAINS. Every law in this repo that grepped a UI
    for a symbol it had just documented has passed on its own prose at least once.
    [[source-reading-guard]] section 4
    """
    def _blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    return re.sub(r"/\*.{0,4000}?\*/", _blank, src, flags=re.S)


class APeerRefusalNamesAnAction(unittest.TestCase):

    # ---------- behaviour ----------

    def test_a_peer_below_the_capability_is_told_what_to_do(self):
        can, why = CA.peer_can_publish_names("v3342")
        self.assertIs(can, False, "a v3342 peer cannot publish names and must be reported so")
        self.assertIn("v3342", why, "the reason does not name the peer's own version")
        self.assertIn("v%d" % CA.MASK_WITHOUT_BOARD_SINCE, why,
                      "the reason does not name the version the capability arrived in, so the "
                      "reader cannot tell what would fix it")
        self.assertIn("update", why.lower(), "the reason names no action")

    def test_the_boundary_version_can_publish(self):
        """OFF-BY-ONE IS THE WHOLE RISK: v3379 IS the version that gained it."""
        can, why = CA.peer_can_publish_names("v%d" % CA.MASK_WITHOUT_BOARD_SINCE)
        self.assertIs(can, True, "the version that INTRODUCED the capability is being accused")
        self.assertEqual(why, "", "a capable peer carries no accusation")

    def test_one_below_the_boundary_cannot(self):
        can, _ = CA.peer_can_publish_names("v%d" % (CA.MASK_WITHOUT_BOARD_SINCE - 1))
        self.assertIs(can, False)

    def test_a_current_peer_is_not_accused(self):
        can, why = CA.peer_can_publish_names("v3383")
        self.assertIs(can, True)
        self.assertEqual(why, "")

    def test_an_absent_version_is_UNKNOWN_never_too_old(self):
        """A missing field is not evidence. [[unknown-stays-unknown]]"""
        for bad in (None, "", "   "):
            can, why = CA.peer_can_publish_names(bad)
            self.assertIsNone(can, "%r was resolved to %r instead of UNKNOWN" % (bad, can))
            self.assertEqual(why, "", "an UNKNOWN peer must carry no accusation")

    def test_an_unparseable_version_is_UNKNOWN(self):
        """⚠ THE PADDED FORMS CAME FROM THE CROSS-FAMILY EYE on v3384. `^v(\\d+)$` accepted
        "v03379" and int() turned it into 3379, so a MALFORMED version was parsed with confidence
        and its owner declared capable. Every version this project stamps is unpadded, so
        refusing the padded form costs nothing real. [[unknown-stays-unknown]]"""
        for bad in ("3342", "v3342-dirty", "vNNNN", "latest", "v03379", "v0003379", "v007"):
            can, _ = CA.peer_can_publish_names(bad)
            self.assertIsNone(can, "%r was resolved to %r instead of UNKNOWN" % (bad, can))

    # ---------- the join ----------

    def test_fleet_compare_forwards_the_version_and_the_verdict(self):
        """A helper nobody calls is documentation. [[the-unjoined-end]]"""
        tree = ast.parse(APP)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "fleet_compare"), None)
        self.assertIsNotNone(fn, "fleet_compare is gone")
        seg = "\n".join(APP.split("\n")[fn.lineno - 1:(fn.end_lineno or fn.lineno)])
        seg = "\n".join(l.split("#", 1)[0] for l in seg.split("\n"))
        # ⚠ v3384 — ASK WHERE THE VALUE COMES FROM, NOT WHETHER THE NAME APPEARS. The first cut
        # asserted `out["theirVer"]` was present, and heart2 proved it BLIND: the tamper
        # `out["theirVer"] = None` still contains that string, so the law passed over its own
        # defeat. A forward is only a forward if it reads the peer's row. [[source-reading-guard]]
        self.assertIn('out["theirVer"] = str(them.get("ver")', seg,
                      "fleet_compare no longer takes the version FROM the peer's roster row, so "
                      "the panel is back to echoing a sentence the peer wrote and cannot revise")
        self.assertIn("peer_can_publish_names(", seg,
                      "fleet_compare no longer asks whether the peer CAN publish")
        self.assertIn('out["theirCanPublishWhy"]', seg,
                      "the actionable sentence is computed and never leaves the function")

    def test_the_panel_prefers_the_actionable_reason(self):
        code = _js_code_only(UI)
        self.assertIn("jj.theirCanPublish === false && jj.theirCanPublishWhy", code,
                      "the panel no longer prefers the reason the reader can act on, so a peer "
                      "that is merely OUT OF DATE is reported as though its board were shut")

    def test_the_panel_still_falls_back_to_the_peers_own_sentence(self):
        """The capability reason REPLACES nothing when it is absent — a peer on a new enough
        version that still cannot publish for its own reason must keep saying so."""
        code = _js_code_only(UI)
        self.assertIn("jj.maskWhy", code,
                      "the fallback to the peer's own reason was removed, so a CAPABLE peer that "
                      "still cannot publish now says nothing at all")


RED_PROOF = [
    {
        "why": "resolving an ABSENT version to False accuses a machine of being out of date on a "
               "missing field, which is the confident-zero this whole file exists to prevent",
        "file": "control_app.py",
        "find": '    if not raw:\n        return None, ""',
        "replace": '    if not raw:\n        return False, "too old"',
        "matches": 1,
    },
    {
        "why": "widening the comparison to accept every version means a v3342 peer reads as "
               "capable and the reader is told nothing at all",
        "file": "control_app.py",
        "find": "    if n >= MASK_WITHOUT_BOARD_SINCE:",
        "replace": "    if n >= 0:",
        "matches": 1,
    },
    {
        "why": "cutting the forward in fleet_compare restores the exact unjoined end: the verdict "
               "is computed and never reaches the panel",
        "file": "control_app.py",
        "find": '    out["theirVer"] = str(them.get("ver") or "").strip() or None',
        "replace": '    out["theirVer"] = None',
        "matches": 1,
    },
    {
        "why": "removing the panel's preference sends the reader back to the peer's own "
               "unactionable sentence, which is what he was looking at when he said it was not "
               "working",
        "file": "control_ui.html",
        "find": "      if (jj && jj.theirCanPublish === false && jj.theirCanPublishWhy) {",
        "replace": "      if (false) {",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
