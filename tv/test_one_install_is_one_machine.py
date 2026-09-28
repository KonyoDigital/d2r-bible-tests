# -*- coding: utf-8 -*-
"""2026-09-28 — ONE INSTALL IS ONE MACHINE, WHATEVER ITS HOST IS CALLED.

HIS WORDS, pointing at his fleet panel: "BUT IT FLEET i see another grok bot fix it if it doesnt really exits".

MEASURED on his /api/fleet: two GrokBot rows carrying the SAME install id (1bba07477e40) - machine
"grok-bot-vm-..." live on v3521, and machine "cursor" last seen 2026-09-20 on v3377. The worker keys its records
by MACHINE NAME (console:<machine>, lastseen:<machine>, a 400-day TTL), so a renamed host keeps a row of its own:
a ghost PC with 8-day-old counts and a "differs" chip that no real machine owns.

DRIVEN through the real /api/fleet route (Handler.do_GET) on real-shaped rows: one install reported under two
machine names reads as ONE row - the newest - with the older name kept as `formerMachines` and stated in
`mergedInstalls`; two different installs never merge; the stale "last good" roster the panel falls back to is
merged the same way. RED_PROOF below.
"""
import json
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402

GHOST = {"machine": "cursor", "install": "1bba07477e40", "nickname": "GrokBot", "ver": "v3377",
         "t": "2026-09-20T03:37:45.409Z", "seenAt": "2026-09-20T03:37:45.409Z", "offline": True}
LIVE = {"machine": "grok-bot-vm-346371813", "install": "1bba07477e40", "nickname": "GrokBot", "ver": "v3521",
        "t": "2026-09-28T10:13:36.284Z", "seenAt": "2026-09-28T10:13:36.284Z"}
DEAN = {"machine": "LAPTOP-QNFL860M", "install": "f8ceea724d93", "nickname": "Dean", "ver": "v3520",
        "t": "2026-09-27T23:48:33.076Z", "seenAt": "2026-09-27T23:48:33.076Z", "offline": True}
WIFE = {"machine": "AdiJusid", "install": "6ee926f9d70d", "nickname": "Wife PC", "ver": "v2101",
        "t": "2026-09-01T18:24:45.281Z", "seenAt": "2026-09-01T18:24:45.281Z", "offline": True}


def _copy(x):
    return json.loads(json.dumps(x))


class OneInstallIsOneMachine(unittest.TestCase):

    def _fleet(self, online, offline, last_good=None):
        """/api/fleet, driven through the route, on a fixture roster."""
        h = ca.Handler.__new__(ca.Handler)
        h.path = "/api/fleet"
        out = []
        h._json = lambda code, obj: out.append(obj)
        fl = {"ok": True, "online": online, "offline": offline}
        with mock.patch.object(ca, "fleet_presence", lambda force=False: _copy(fl)), \
                mock.patch.object(ca, "fleet_origin_status", lambda *a, **k: {"ahead": None, "publishedVer": None}), \
                mock.patch.object(ca, "board_tally_load", lambda: None), \
                mock.patch.object(ca, "fleet_presence_last_good", lambda: (_copy(last_good), 60) if last_good else (None, None)):
            h.do_GET()
        self.assertEqual(len(out), 1, "PREMISE: the route did not answer once")
        return out[0]

    @staticmethod
    def _rows(payload):
        return (payload.get("online") or []) + (payload.get("offline") or [])

    def test_a_renamed_host_is_one_row_and_keeps_its_old_name(self):
        got = self._fleet([_copy(LIVE)], [_copy(GHOST), _copy(DEAN), _copy(WIFE)])
        grok = [r for r in self._rows(got) if r.get("install") == "1bba07477e40"]
        self.assertEqual([r["machine"] for r in grok], ["grok-bot-vm-346371813"],
                         "one GrokBot install still reads as %d machine rows: %r" % (len(grok), [r["machine"] for r in grok]))
        self.assertEqual([f["machine"] for f in grok[0].get("formerMachines") or []], ["cursor"],
                         "the older host name was dropped instead of kept on the row")
        self.assertEqual([m["machine"] for m in got.get("mergedInstalls") or []], ["cursor"],
                         "the merge was silent - nothing states that 'cursor' was folded")

    def test_the_newest_row_wins_whichever_bucket_it_sits_in(self):
        older_online = dict(_copy(LIVE), t="2026-09-01T00:00:00Z", seenAt="2026-09-01T00:00:00Z")
        newer_offline = dict(_copy(GHOST), t="2026-09-28T12:00:00Z", seenAt="2026-09-28T12:00:00Z")
        got = self._fleet([older_online], [newer_offline])
        grok = [r for r in self._rows(got) if r.get("install") == "1bba07477e40"]
        self.assertEqual([r["machine"] for r in grok], ["cursor"], "the OLDER report won the merge")

    def test_two_installs_never_merge(self):
        got = self._fleet([_copy(LIVE)], [_copy(DEAN), _copy(WIFE)])
        self.assertEqual(sorted(r["machine"] for r in self._rows(got)),
                         sorted(["grok-bot-vm-346371813", "LAPTOP-QNFL860M", "AdiJusid"]),
                         "real, different machines were merged or lost")
        self.assertEqual(got.get("mergedInstalls"), [], "a merge was reported where there was nothing to merge")

    def test_the_stale_roster_the_panel_falls_back_to_is_merged_too(self):
        lg = {"ok": True, "online": [_copy(LIVE)], "offline": [_copy(GHOST), _copy(DEAN)]}
        got = self._fleet([_copy(LIVE)], [_copy(DEAN)], last_good=lg)
        stale = got.get("lastGood") or {}
        grok = [r for r in (stale.get("online") or []) + (stale.get("offline") or [])
                if r.get("install") == "1bba07477e40"]
        self.assertEqual(len(grok), 1, "the ghost comes back through the stale roster: %r" % [r["machine"] for r in grok])


RED_PROOF = [
    {
        "why": "2026-09-28 - /api/fleet stops merging one install's rows: the renamed host is a ghost PC again",
        "file": "control_app.py",
        "find": "                    _fl = fleet_merge_same_install(_fl)  # 2026-09-28 — a renamed host is not a second PC\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the merge keeps the OLDEST report instead of the newest",
        "file": "control_app.py",
        "find": "        if inst not in newest or _when(m) > _when(newest[inst][1]):\n",
        "replace": "        if inst not in newest or _when(m) < _when(newest[inst][1]):\n",
        "matches": 1,
    },
    {
        "why": "2026-09-28 - the stale roster is shown raw: the ghost returns whenever the fleet cannot be reached",
        "file": "control_app.py",
        "find": "                        _lg = fleet_merge_same_install(fleet_drop_non_machines(_lg))\n",
        "replace": "                        pass\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
