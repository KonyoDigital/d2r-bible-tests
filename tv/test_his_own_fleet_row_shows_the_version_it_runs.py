# -*- coding: utf-8 -*-
"""#246 (REG-2046) - THIS CONSOLE'S OWN FLEET ROW SHOWS THE VERSION IT IS RUNNING, NOT ITS LAST PUBLISHED BEACON.

GrokBot tick 401 (row v3603 beside a Vault chip v3604) and tick 415 (row v3620 beside v3621): the self row carried
what the last beacon PUBLISHED, and a relaunch lands minutes before the next beacon. The running stamp is the drift
loop's own reading (_DRIFT["running"]); the published word is kept as verPublished; an unmeasured stamp changes
nothing; a peer's row is never touched (its version is only knowable through its beacon).
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402


def _fleet():
    return {"online": [{"machine": "me-mac", "ver": "v3620"}, {"machine": "peer", "ver": "v3600"}], "offline": []}


class HisOwnFleetRowShowsTheVersionItRuns(unittest.TestCase):

    def test_his_row_takes_the_running_stamp_and_keeps_the_published_one(self):
        fl = _fleet()
        with mock.patch.dict(ca._DRIFT, {"running": "v3621"}):
            n = ca._fleet_overlay_local_version(fl, "me-mac")
        me, peer = fl["online"]
        self.assertEqual(n, 1)
        self.assertEqual((me["ver"], me.get("verPublished"), me.get("verLive")), ("v3621", "v3620", True), me)
        self.assertEqual(peer, {"machine": "peer", "ver": "v3600"}, "a peer's row was rewritten from this console")

    def test_an_unmeasured_stamp_changes_nothing(self):
        fl = _fleet()
        with mock.patch.dict(ca._DRIFT, {"running": None}):
            self.assertEqual(ca._fleet_overlay_local_version(fl, "me-mac"), 0)
        self.assertEqual(fl, _fleet())

    def test_the_fleet_route_applies_it(self):
        with open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count('                    _fleet_overlay_local_version(_fl, _fl["me"])\n'), 1,
                         "the fleet route no longer overlays his running version")


RED_PROOF = [
    {"why": "REG-2046 - his own fleet row shows its last published beacon again",
     "file": "control_app.py",
     "find": "            if isinstance(row, dict) and str(row.get(\"machine\") or \"\") == str(me) and row.get(\"ver\") != live:\n",
     "replace": "            if False:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
