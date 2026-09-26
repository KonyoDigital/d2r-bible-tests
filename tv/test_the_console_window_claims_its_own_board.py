# -*- coding: utf-8 -*-
"""#239 — THE CONSOLE'S OWN WINDOW CLAIMS ITS BOARD; A MACHINE THAT HELD ONE IS RESTORED, NEVER RESEEDED.

His ruling, 2026-09-25: "this is already architected in a way.. so make sure to check blueprints and wire just
whats needed". Measured before wiring: the console already had a claim door (POST /api/board {claim:true}) that
NOTHING called, and it wrote '*' with NO ledger name - the state v2692 says adopts the owner's seed one find later.

Now one routine claims (window._d2rClaimThisBrowser: the claim + the ledger name, exactly the button's two
writes), and it runs by itself only inside a pywebview window (the console's own - a browser tab never has
window.pywebview) on a store with NO claim, and only when the console says this machine never held a populated
board (no ledger snapshot, no banked tally with have > 0). Anything else leaves the claim bar as it was.

  · DRIVEN (python): own_board_may_autoclaim over a real backup dir and tally - yes only on a clean machine;
    a snapshot, a banked count, or an unreadable record each refuse.
  · DRIVEN (node, the SHIPPED claim script cut from bible.html): the console window claims and names its ledger;
    a refusal, a browser tab, and an existing claim each write nothing; the button uses the same routine.
  · DRIVEN: the "board is claimed" doctor row says what the automatic claim decided.
  · JOINED: the old door no longer writes a claim; the route exists.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import control_app as CA  # noqa: E402
import console_doctor as CD  # noqa: E402

NODE = shutil.which("node")
START = "<script>\n(function(){\n  /* ══ #239 — ONE CLAIM ROUTINE, TWO DOORS"
END = "  } catch(e){}\n})();\n</script>"


def _src(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def _claim_script():
    s = _src("bible.html")
    assert s.count(START) == 1, "the #239 claim script is not where this law looks"
    i = s.index(START) + len("<script>\n")
    j = s.index(END, i) + len("  } catch(e){}\n})();")
    return s[i:j]


class TheGuardRestoresNeverReseeds(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="own-claim-")
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_a_machine_that_never_held_a_board_may_claim(self):
        v = CA.own_board_may_autoclaim(backup_dir=self.d, tally=None)
        self.assertIs(v["may"], True, v)

    def test_a_ledger_snapshot_refuses(self):
        with open(os.path.join(self.d, "ledger_2026-09-25_064945.json"), "w") as fh:
            fh.write("{}")
        v = CA.own_board_may_autoclaim(backup_dir=self.d, tally=None)
        self.assertIs(v["may"], False, "a machine with a ledger backup would be given a new empty world")
        self.assertIn("RESTORED", v["why"])

    def test_a_banked_count_refuses(self):
        v = CA.own_board_may_autoclaim(backup_dir=self.d, tally={"sets": {"have": 2, "total": 135}})
        self.assertIs(v["may"], False)
        self.assertIn("sets 2", v["why"])

    def test_a_banked_zero_is_not_a_board(self):
        v = CA.own_board_may_autoclaim(backup_dir=self.d, tally={"sets": {"have": 0, "total": 135}})
        self.assertIs(v["may"], True, "a measured-empty tally blocked a clean machine")

    def test_an_unreadable_record_refuses(self):
        real = CA.board_tally_load
        CA.board_tally_load = lambda: (_ for _ in ()).throw(OSError("unreadable"))
        try:
            v = CA.own_board_may_autoclaim(backup_dir=self.d)
        finally:
            CA.board_tally_load = real
        self.assertIs(v["may"], False, "UNKNOWN about his past was read as permission")


@unittest.skipIf(NODE is None, "node is absent - this law is UNMEASURED, not passing")
class TheBoardClaimsOnlyInItsOwnWindow(unittest.TestCase):

    def _run(self, pywebview=True, may=True, claim=None, click=False, fire=False):
        store = {"d2r_ownerClaim": claim} if claim else {}
        js = r"""
var store = %s, reloads = 0, fetched = 0, listeners = {};
var ls = { getItem: function(k){ return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
           setItem: function(k, v){ store[k] = String(v); } };
var btn = { disabled: false, textContent: '', onclick: null };
var bar = { hidden: true };
var window = { localStorage: ls, _D2R_INSTALL: 'abcdef0123456789', _D2R_OWNER: false,
               addEventListener: function(n, f){ listeners[n] = f; } };
if (%s) window.pywebview = {};
var document = { getElementById: function(id){ return id === 'claim-btn' ? btn : (id === 'claim-bar' ? bar : null); },
                 body: { classList: { add: function(){} } } };
var location = { protocol: 'http:', reload: function(){ reloads++; } };
function setTimeout(f){ f(); }
var pending = [];
function fetch(u){ fetched++; var body = %s;
  return { then: function(f){ var r = f({ json: function(){ return body; } });
    return { then: function(g){ g(r); return { catch: function(){} }; } }; } }; }
%s
if (%s && listeners.pywebviewready) listeners.pywebviewready();
if (%s && btn.onclick) btn.onclick();
console.log(JSON.stringify({ store: store, reloads: reloads, fetched: fetched }));
""" % (json.dumps(store), "true" if pywebview else "false",
       json.dumps({"ok": True, "may": may, "why": "test"}), _claim_script(), "true" if fire else "false",
       "true" if click else "false")
        r = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise AssertionError("the shipped claim script would not run - UNKNOWN, not passing: %s" % r.stderr[:400])
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_console_window_claims_and_names_its_ledger(self):
        out = self._run(pywebview=True, may=True)
        self.assertEqual(out["store"].get("d2r_ownerClaim"), "abcdef0123456789")
        self.assertEqual(out["store"].get("d2r_ledgerName"), "Ledger-abcdef01",
                         "a claim without a ledger name adopts the owner's seed one find later (v2692)")
        self.assertEqual(out["reloads"], 1)

    def test_a_refusal_writes_nothing(self):
        out = self._run(pywebview=True, may=False)
        self.assertNotIn("d2r_ownerClaim", out["store"], "a machine that held a board was given a new world")
        self.assertEqual(out["reloads"], 0)

    def test_a_browser_tab_never_asks(self):
        """⚠ THE EVENT IS FIRED. Any page script can dispatch `pywebviewready`; only the bridge object
        proves the window. Without firing it, the guard inside was never exercised (seen BLIND)."""
        out = self._run(pywebview=False, may=True, fire=True)
        self.assertEqual(out["fetched"], 0, "a page that is not the console's window asked to be claimed")
        self.assertNotIn("d2r_ownerClaim", out["store"])

    def test_an_existing_claim_is_left_alone(self):
        out = self._run(pywebview=True, may=True, claim="someone-else")
        self.assertEqual(out["store"].get("d2r_ownerClaim"), "someone-else")
        self.assertEqual(out["fetched"], 0)

    def test_the_button_uses_the_same_routine(self):
        out = self._run(pywebview=False, may=False, click=True)
        self.assertEqual(out["store"].get("d2r_ownerClaim"), "abcdef0123456789")
        self.assertEqual(out["store"].get("d2r_ledgerName"), "Ledger-abcdef01")


class TheDoctorAndTheDoor(unittest.TestCase):

    def test_the_doctor_says_what_the_automatic_claim_decided(self):
        real_read, real_may = CD._board_read, CA.own_board_may_autoclaim
        CD._board_read = lambda: {"ok": True, "boardLoaded": True, "owner": False, "pfx": "I-abc-",
                                  "counts": {"foundLog": 3, "owned": 0, "setPieces": 0}}
        CA.own_board_may_autoclaim = lambda: {"ok": True, "may": False, "why": "held a board before - RESTORED"}
        try:
            st, why = CD._check_the_board_world_is_claimed()
        finally:
            CD._board_read, CA.own_board_may_autoclaim = real_read, real_may
        self.assertEqual(st, CD.MISSING)
        self.assertIn("did NOT claim it by itself", why)
        self.assertIn("RESTORED", why)

    def test_the_old_door_writes_no_claim_and_the_route_exists(self):
        app = _src("tv/control_app.py")
        self.assertNotIn("localStorage.setItem('d2r_ownerClaim','*')", app,
                         "the console writes a nameless '*' claim again")
        self.assertEqual(app.count('if path == "/api/own_board_claim":'), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#239 - a machine that held a board is given a fresh empty world (the 2026-09-08 night)",
        "file": "tv/control_app.py",
        "find": "    if snaps or had:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
    {
        "why": "#239 - a browser tab on the console's address claims itself as the console's board",
        "file": "bible.html",
        "find": "        if (!window.pywebview) return;\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#239 - the board claims even when the console refused",
        "file": "bible.html",
        "find": "          if (!j || j.may !== true) return;\n",
        "replace": "          if (!j) return;\n",
        "matches": 1,
    },
    {
        "why": "#239 - the claim routine stops naming the ledger, so a new board adopts the owner's seed (v2692)",
        "file": "bible.html",
        "find": "          window.localStorage.setItem('d2r_ledgerName',\n",
        "replace": "          window.localStorage.setItem('d2r_ledgerName_gone',\n",
        "matches": 1,
    },
    {
        "why": "#239 - the doctor tells him to press the button without saying the console refused and why",
        "file": "tv/console_doctor.py",
        "find": '        if isinstance(_v, dict) and _v.get("may") is False:\n',
        "replace": "        if False:\n",
        "matches": 1,
    },
]
