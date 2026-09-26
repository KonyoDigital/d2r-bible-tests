# -*- coding: utf-8 -*-
"""THE OPERATOR DOORS KEEP THEIR CONTRACT — and this law is their NAMED OWNER.

Routine I's v1550 audit ("every /api route in the console has a consumer, or a named owner") has been
red on four routes that no page calls BY DESIGN: they are doors a person or the GrokBot seat walks
through by hand, after something went wrong.

    /api/owned_restore      put owned names back          (writes his world - confirm required)
    /api/rw_restore         put made runewords back       (writes his world - confirm required)
    /api/vault_autosort     press the board's Auto-Sort   (writes his world - confirm required)
    /api/vault_route_probe  why is each item unsorted     (reads only)

Deleting them would delete the repair path; an allowlist entry with nothing behind it would excuse a
real orphan. So each gets an owner that DRIVES it.

  · DRIVEN through the REAL Handler on an ephemeral port, the board window replaced by a recorder:
    without `confirm`, no write door sends the board a single store write (setItem) and each answers
    applied:false; the probe never writes at all.
  · PREMISE: with `confirm`, every write door DOES send its write - so each no-confirm case can fail.

#246 L4 — AND NO DOOR FILES A MULE FROM A POSSESSION RECORD. On 2026-09-16 a confirmed restore became 152 mule
filings with no witness behind any of them (20:12:49): owned_restore wrote a backup's found-ever owned list and
its v3222 post-hook pressed the sorter, and ledger_restore_apply called owned_restore(confirm=True) from inside a
restore he had confirmed for the CHRONICLE. Held here, each DRIVEN:
  · a CONFIRMED owned_restore / rw_restore sends the board no script that presses the sorter;
  · a confirmed ledger restore never reaches the owned door (ledger_restore.py's own contract: owned is
    "BACKED UP but NOT restorable here"), still drives the runeword door, and says the owned half was skipped;
  · the register button's {} path re-gates the STORED sweep under TODAY's gate, row by row: a row the per-look
    rule now refuses (Magefist's frameless conf-0.0 second look) is held back and NAMED, the rest go through.
RED_PROOF below.
"""
import json
import os
import sys
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402

WRITE_DOORS = {
    "/api/owned_restore": {"names": ["Shako"]},
    "/api/rw_restore": {"entries": {"Enigma": "2026-01-01"}},
    "/api/vault_autosort": {},
}
READ_DOORS = {"/api/vault_route_probe": {}}


class _Board(object):
    """Stands in for his board window: records every script, answers like a board that obeyed."""

    def __init__(self):
        self.scripts = []

    def evaluate_js(self, js):
        self.scripts.append(js)
        return json.dumps({"ok": True, "applied": False, "preview": {"moves": 0}, "pool": 0,
                           "assigned": 0, "added": 0, "written": 0})

    def writes(self):
        # a store write, or the press of Auto-Sort itself (its preview only asks `typeof`)
        return [s for s in self.scripts if "setItem(" in s or "window.vaultAutoAssign();" in s]


class OperatorDoorsKeepTheirContract(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.board = _Board()
        self._saved = dict((k, getattr(ca, k, None)) for k in
                           ("_BOARD_WIN", "_MAIN_WIN", "_WINDOW_LIVE", "board_identity_drift"))
        ca._BOARD_WIN = self.board
        ca._MAIN_WIN = None
        ca._WINDOW_LIVE = True
        ca.board_identity_drift = lambda *a, **k: {"state": "ok"}

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(ca, k, v)

    def _post(self, route, body):
        req = urllib.request.Request("http://127.0.0.1:%d%s" % (self.port, route),
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))

    def test_premise_every_confirmed_door_does_write(self):
        for route, body in WRITE_DOORS.items():
            self.board.scripts[:] = []
            out = self._post(route, dict(body, confirm=True))
            self.assertTrue(self.board.writes(), "premise: CONFIRMED %s sent no write - its no-confirm "
                            "case below would pass for the wrong reason (%r)" % (route, out))

    def test_no_write_door_writes_without_confirm(self):
        for route, body in WRITE_DOORS.items():
            self.board.scripts[:] = []
            out = self._post(route, body)
            self.assertIsNot(out.get("applied"), True, "%s applied without confirm: %r" % (route, out))
            self.assertEqual(self.board.writes(), [], "%s sent the board a WRITE without confirm" % route)

    def test_a_possession_door_never_presses_the_sorter(self):
        """#246 L4 — a restored possession record waits in the dock; it is never filed on its own word."""
        for route, body in (("/api/owned_restore", {"names": ["Shako", "Nagelring"]}),
                            ("/api/rw_restore", {"entries": {"Enigma": "2026-01-01"}})):
            self.board.scripts[:] = []
            self._post(route, dict(body, confirm=True))
            self.assertTrue(self.board.scripts, "premise: %s sent the board nothing" % route)
            self.assertEqual([], [s for s in self.board.scripts if "vaultAutoAssign" in s],
                             "%s presses the sorter after writing a possession record — the 20:12:49 refill" % route)

    def test_the_chronicle_restore_never_reaches_the_owned_door(self):
        import ledger_restore as LR
        calls = {"owned": 0, "rw": 0}
        saved = dict((k, getattr(ca, k)) for k in ("ledger_restore_plan", "chronicle_apply", "owned_restore", "rw_restore"))
        saved_lr = dict((k, getattr(LR, k)) for k in ("proposal_from", "backed_up_only_from"))
        try:
            ca.ledger_restore_plan = lambda: {"ok": True, "file": "ledger_law.json", "missingTotal": 1, "why": "law"}
            ca.chronicle_apply = lambda proposal=None: {"ok": True}
            ca.owned_restore = lambda *a, **k: calls.__setitem__("owned", calls["owned"] + 1) or {"ok": True}
            ca.rw_restore = lambda *a, **k: calls.__setitem__("rw", calls["rw"] + 1) or {"ok": True}
            LR.proposal_from = lambda plan: {"wouldAdd": {"uniques": [{"name": "Nagelring"}]}}
            LR.backed_up_only_from = lambda plan, d=None: ({"owned": ["Shako"], "rwMade": {"Enigma": "d"}}, "")
            out = ca.ledger_restore_apply(confirm=True)
        finally:
            for k, v in saved.items():
                setattr(ca, k, v)
            for k, v in saved_lr.items():
                setattr(LR, k, v)
        self.assertEqual(0, calls["owned"], "a CHRONICLE restore called owned_restore — a found-ever owned list comes "
                                            "back as possession and the sorter files it")
        self.assertEqual(1, calls["rw"], "premise: the runeword door must still be driven")
        self.assertTrue(((out.get("alsoRestored") or {}).get("owned") or {}).get("skipped"),
                        "the receipt does not say the owned half was skipped: %r" % out)

    def test_the_register_button_regates_the_stored_sweep(self):
        good = {"name": "Nagelring", "lane": "stash", "kind": "item", "count": 1,
                "witnesses": [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9},
                              {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85}]}
        mage = {"name": "Magefist", "lane": "stash", "kind": "item", "count": 1,
                "witnesses": [{"session": "s_1", "frame": None, "conf": 0.0},
                              {"session": "s_2", "frame": "f_2.jpg", "conf": 0.85}]}
        real = ca.vault_sweep_state
        try:
            ca.vault_sweep_state = lambda: {"result": {"ok": True, "owned": [good, mage], "unsure": [], "throwOut": []}}
            self.board.scripts[:] = []
            out = ca.vault_apply(None)
        finally:
            ca.vault_sweep_state = real
        sent = "".join(self.board.scripts)
        self.assertIn("Nagelring", sent, "premise: the row that clears today's gate did not reach the board")
        self.assertNotIn("Magefist", sent, "a stored row today's gate refuses was registered from the {} path")
        self.assertIn("Magefist", json.dumps(out.get("regatedOut") or []),
                      "the held-back row is not NAMED beside the answer: %r" % out)

    def test_the_probe_only_reads(self):
        for route, body in READ_DOORS.items():
            self.board.scripts[:] = []
            self._post(route, body)
            self.assertTrue(self.board.scripts, "premise: %s never asked the board anything" % route)
            self.assertEqual([s for s in self.board.scripts if "setItem(" in s], [],
                             "%s wrote to the board - it is a read-only door" % route)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#246 L4 - owned_restore presses the sorter again after writing a possession record (the 20:12:49 refill)",
        "file": "control_app.py",
        "find": "          \"try{var _rr=(typeof window._vaultReloadOwned==='function')?window._vaultReloadOwned():null;\"\n          \"if(_rr===null){setTimeout(function(){try{window.location.reload();}catch(_r){}},150);}\"\n",
        "replace": "          \"try{var _rr=(typeof window._vaultReloadOwned==='function')?window._vaultReloadOwned():null;\"\n          \"if(_rr===null){setTimeout(function(){try{window.location.reload();}catch(_r){}},150);}\"\n          \"else if(typeof window.vaultAutoAssign==='function'){setTimeout(function(){try{window.vaultAutoAssign();}catch(_s){}},60);}\"\n",
        "matches": 1,
    },
    {
        "why": "#246 L4 - a chronicle restore reaches the owned door again (owned is BACKED UP, not restorable here)",
        "file": "control_app.py",
        "find": "        _also[\"owned\"] = {\"ok\": False, \"applied\": False, \"skipped\": True,\n",
        "replace": "        _also[\"owned\"] = owned_restore(_extra[\"owned\"], confirm=True) and {\"ok\": False, \"applied\": False, \"skipped\": True,\n",
        "matches": 1,
    },
    {
        "why": "#246 W3 - the register button's {} path stops re-gating the stored sweep",
        "file": "control_app.py",
        "find": "    if _gated is None and isinstance(prop, dict):\n",
        "replace": "    if False and _gated is None and isinstance(prop, dict):\n",
        "matches": 1,
    },
    {
        "why": "owned_restore writes without confirm again - a hand-typed restore lands in his world unasked",
        "file": "control_app.py",
        "find": "            self._json(200, owned_restore(body.get(\"names\"), confirm=_confirmed(body.get(\"confirm\"))))\n",
        "replace": "            self._json(200, owned_restore(body.get(\"names\"), confirm=True))\n",
        "matches": 1,
    },
    {
        "why": "vault_autosort presses Auto-Sort without confirm again",
        "file": "control_app.py",
        "find": "            self._json(200, vault_autosort(confirm=_confirmed(body.get(\"confirm\"))))\n",
        "replace": "            self._json(200, vault_autosort(confirm=True))\n",
        "matches": 1,
    },
]
