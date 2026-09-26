# -*- coding: utf-8 -*-
"""#246 L1 — FOUND-EVER NEVER FILES TO A MULE. Driven on the SHIPPED board, every trigger pressed.

His words, 2026-09-26: "all those item inside the vault are falsely there ... reverse engineer it all and each
item to see where and why and make sure they dont get routed here again", and "all the items getting vaulted and
vaulted by AI READERS or manually should be to the dedicated mules alone".

THE DEFECT (forensics on a copy of his store, read-only): 173 mule filings, 160 of them from found-ever data with
NO witness of any kind. One writer made all of them — vaultAutoAssign walked ownedPool(), and d2r_owned means
ticked or found-ever, not possession. Six automatic triggers pressed it: chronicleApply's `_landedAny`, two in
vaultAccumApply, the owned_restore and rw_restore post-hooks, and the vault_autosort door — plus _chronAutoAdopt,
which lands a Chronicle sweep every 90 s on his console with nobody watching. On 2026-09-16 a restore became 21
filings at 15:28:34 and 152 at 20:12:49.

WHAT THIS LAW HOLDS, each case DRIVEN in bible.html itself, in its own headless Chrome (never re-typed):
  · THE PREMISE — the page holds a FOUND-EVER world: names in d2r_owned, d2r_foundLog and d2r_setPieces, no
    witness anywhere, an empty mule map. A law that never had a found-ever world to refuse grades nothing.
  · EVERY TRIGGER, PRESSED, LEAVES THE MAP AND THE WITNESS STORE EXACTLY AS SEEDED: the sorter; a ledger
    restore through chronicleApply (the 15:28 shape, set pieces riding the uniques half); _chronAutoAdopt with
    a sweep waiting; vaultAccumApply with a one-look row; the owned_restore, rw_restore and vault_autosort
    scripts the CONSOLE really sends (captured from control_app, then run in the page); the TV registrar with
    no witness; the inbox's auto-accept of one container sighting; the KAI judge's keep tier; Chronicle Accept
    and Accept-All. The failure names the trigger.
  · L3 (board half) — A SET PIECE RESTORED AS A "UNIQUE" GOES TO THE SET DOOR, never into d2r_owned.
  · L5 — CHRONICLE ACCEPT TICKS THE CHRONICLE ONLY by default, and with vault asked for it still needs a
    sighting in a container.
  · THE POSITIVE CONTROL — his hand (a click onto a locker) files, and leaves a provenance row saying so. A door
    that files nothing at all would pass every case above.

⚠ WHAT THIS LAW DOES NOT PRESS: the TV live-pickup loop (it lives inside the live-read handler and needs a
running reader). Its witness is one look, and the door refuses one look — that rule is driven by
test_every_mule_filing_carries_its_witness, and no map write outside the door exists (its source half).
⚠ ITS OWN BROWSER, ON ITS OWN PORT: a free port unless TV_RENDER_PORT is already exported; the Chrome it starts
is killed by the handle it holds and its temp profile goes with it. NO CHROME AT ALL = a declared skip (77),
never a pass; Chrome installed and refusing to start is a FAILURE.
RED_PROOF below.
"""
import io
import json
import os
import socket
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass


def _free_port():
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


# ⚠ BEFORE the import: render_check reads its port once, at import time.
if not os.environ.get("TV_RENDER_PORT"):
    os.environ["TV_RENDER_PORT"] = str(_free_port())
import render_check as RC  # noqa: E402

NO_BROWSER = "no Chrome/Chromium on this machine, so the shipped board was not driven"
BIBLE = os.path.join(ROOT, "bible.html")
READY = ("!!(window.vaultFile&&window.tvVaultRegister&&window.chronicleApply&&window.vaultAccumApply"
         "&&window.vaultAutoAssign&&window.kaiChronicleAccept&&window.LSR&&window._vaultReloadOwned)")

#: game item names only — never his store
UNIQUES = ["Nagelring", "Arachnid Mesh", "Stormshield", "Windforce", "The Stone of Jordan"]
PIECES = ["Aldur's Advance (boots)", "Tal Rasha's Horadric Crest (helm)"]
ONE_LOOK = [{"session": "s_one", "frame": "f_one.jpg", "conf": 0.9}]
TWO_LOOKS = [{"session": "s_a", "frame": "f_a.jpg", "conf": 0.9},
             {"session": "s_b", "frame": "f_b.jpg", "conf": 0.85}]


class Board(object):
    """ONE page of the SHIPPED bible.html in its own headless Chrome. Seeds through the board's own LSR (the world
    prefix is the board's business) and reloads, so every boot-time store is read the way a boot reads it."""

    def __init__(self):
        self.t = None

    def open(self):
        if not RC._chrome_up():
            raise AssertionError("Chrome is INSTALLED at %s and would not start on :%d — a failure on a venue "
                                 "that is supposed to measure" % (RC.CHROME, RC.PORT))
        self.t = RC._Tab("about:blank")
        self.t.send("Page.enable")
        self.t.send("Runtime.enable")
        self.navigate()
        return self

    def navigate(self):
        self.t.send("Page.navigate", url="file://" + BIBLE)
        for _ in range(240):
            time.sleep(0.25)
            try:
                if self.t.ev(READY) is True:
                    time.sleep(0.4)
                    return
            except Exception:
                pass
        raise AssertionError("bible.html never exposed the vault doors in 60 s — UNKNOWN, not passing")

    def run(self, body):
        """Run `body` in the page (async allowed); it fills OUT. -> dict. A throw is a failure with its reason."""
        r = self.t.ev("(async function(){ var OUT = {}; " + body + "\n; return JSON.stringify(OUT); })()")
        if r is None:
            raise AssertionError("the page threw: %s" % (self.t.last_exc,))
        return json.loads(r)

    def seed(self, stores):
        """Write each store through LSR (null removes it), then reload so the boot reads them."""
        self.run("var S = %s; Object.keys(S).forEach(function(k){ if (S[k] === null) window.LSR.removeItem(k);"
                 " else window.LSR.setItem(k, typeof S[k] === 'string' ? S[k] : JSON.stringify(S[k])); });"
                 % json.dumps(stores))
        self.navigate()

    def stores(self):
        return self.run("OUT.map = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                        "OUT.prov = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}');"
                        "OUT.owned = JSON.parse(window.LSR.getItem('d2r_owned') || '[]');"
                        "OUT.setPieces = JSON.parse(window.LSR.getItem('d2r_setPieces') || '[]');"
                        "OUT.foundLog = JSON.parse(window.LSR.getItem('d2r_foundLog') || '{}');")

    def close(self):
        try:
            if self.t is not None:
                self.t.close()
        except Exception:
            pass
        RC._chrome_down()


def found_ever_world(b):
    """The found-ever shape of his board: owned = ticked/found-ever names, a found ledger, set pieces, NO witness,
    an empty map. `owned` is read once at boot and the boot prune may thin it, so after the reload the seeded list
    is put back into the live Set through the board's own re-read door."""
    fl = dict((n, "Aug 1, 2026 · 10:00") for n in UNIQUES + PIECES)
    b.seed({"d2r_owned": UNIQUES, "d2r_foundLog": fl, "d2r_setPieces": PIECES,
            "d2r_muleAssign": {}, "d2r_vaultProv": None, "d2r_laneLock": None,
            "d2r_chronicleInbox": [], "d2r_rwProfile": "fresh"})
    b.run("window.LSR.setItem('d2r_owned', JSON.stringify(%s)); OUT.n = window._vaultReloadOwned();"
          % json.dumps(UNIQUES))


def console_script(door, *args, **kw):
    """The EXACT script a console door sends his board — captured from control_app, never re-typed."""
    import control_app as ca

    class _W(object):
        def __init__(self):
            self.scripts = []

        def evaluate_js(self, js):
            self.scripts.append(js)
            return json.dumps({"ok": True, "applied": False, "added": 0, "written": 0})

    saved = dict((k, getattr(ca, k, None)) for k in ("_BOARD_WIN", "_MAIN_WIN", "_WINDOW_LIVE",
                                                      "board_identity_drift"))
    w = _W()
    try:
        ca._BOARD_WIN, ca._MAIN_WIN, ca._WINDOW_LIVE = w, None, True
        ca.board_identity_drift = lambda *a, **k: {"state": "ok"}
        getattr(ca, door)(*args, **kw)
    finally:
        for k, v in saved.items():
            setattr(ca, k, v)
    assert w.scripts, "%s sent the board nothing — the capture measured nothing" % door
    return w.scripts[-1]


_B = {}


def board():
    if "b" not in _B:
        _B["b"] = Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


class FoundEverNeverFilesToAMule(unittest.TestCase):

    def test_1_the_premise_is_a_found_ever_world_with_an_empty_map(self):
        b = board()
        found_ever_world(b)
        s = b.stores()
        for n in UNIQUES:
            self.assertIn(n, s["owned"], "premise: %s is not in d2r_owned — there is no found-ever world to refuse" % n)
        for p in PIECES:
            self.assertIn(p, s["setPieces"], "premise: the set piece %s is not ticked" % p)
        self.assertEqual({}, s["map"], "premise: the map is not empty before any trigger")
        self.assertEqual({}, s["prov"], "premise: a witness row exists before any trigger")

    def test_2_every_trigger_leaves_the_map_as_seeded(self):
        b = board()
        found_ever_world(b)
        owned_js = console_script("owned_restore", UNIQUES + ["Hellfire Torch"], confirm=True)
        rw_js = console_script("rw_restore", {"Enigma": "Jul 1, 2026 · 10:00"}, confirm=True)
        sort_js = console_script("vault_autosort", confirm=True)
        body = r"""
          var T = [];
          function snap(name){
            var m = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');
            var p = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}');
            T.push({ trigger: name, filed: Object.keys(m), prov: Object.keys(p) });
          }
          function wait(ms){ return new Promise(function(r){ setTimeout(r, ms); }); }
          var U = %(uni)s, P = %(pieces)s, ONE = %(one)s;
          window.vaultAutoAssign(); snap('the sorter (vaultAutoAssign)');
          window.chronicleApply({ wouldAdd: { uniques: U.concat(P).map(function(n){ return { name: n }; }),
                                              sets: P.map(function(n){ return { name: n }; }) } });
          await wait(150); snap('a ledger restore through chronicleApply');
          window.chronicleApply({ wouldAdd: { uniques: ['Hellfire Torch'], sets: [] } });
          await wait(150); snap('a fresh unique tick through chronicleApply');
          window._chronAdoptGate = function(){ return { ok: true }; };
          window.chronicleFetchProposal = function(){ return Promise.resolve({ ok: true,
            proposal: { startedTs: 'law-' + Date.now(), wouldAdd: { uniques: [{ name: 'Harlequin Crest' }], sets: [] } } }); };
          await window._chronAutoAdopt(); await wait(150); snap('_chronAutoAdopt with a sweep waiting');
          window.vaultAccumApply({ items: [{ name: 'Windforce', lane: 'stash', kind: 'item', conf: 0.9,
                                             witnesses: ONE, witnessCount: 1 }] });
          await wait(150); snap('vaultAccumApply with a one-look row');
          eval(%(owned_js)s); await wait(400); snap('the console owned_restore script');
          eval(%(rw_js)s); await wait(400); snap('the console rw_restore script');
          eval(%(sort_js)s); await wait(200); snap('the console vault_autosort script');
          window.tvVaultRegister('Stormshield'); snap('the TV registrar with no witness');
          try { window.kaiChroniclePropose([{ name: 'Nagelring', tier: 'grail', loc: 'stash', frameId: 'f_one.jpg',
                                              sessionId: 's_one', source: 'law' }]); } catch (e) {}
          snap('the inbox auto-accept of one container sighting');
          try { window.aicJudgeApply({ ok: true, verdict: { tier: 'keep', score: 80 }, name: 'Arachnid Mesh',
                                       q: 'unique', base: 'Spiderweb Sash', mods: [] },
                                     { frameId: 'f_j.jpg', sid: 's_j' }); } catch (e) {}
          snap('the KAI judge keep tier');
          window.kaiChronicleAccept('Windforce'); snap('Chronicle Accept (default)');
          try { window.kaiChronicleAcceptAll(); } catch (e) {}
          snap('Chronicle Accept-All');
          OUT.T = T;
        """ % {"uni": json.dumps(UNIQUES), "pieces": json.dumps(PIECES), "one": json.dumps(ONE_LOOK),
               "owned_js": json.dumps(owned_js), "rw_js": json.dumps(rw_js), "sort_js": json.dumps(sort_js)}
        out = b.run(body)
        self.assertGreaterEqual(len(out["T"]), 13, "premise: not every trigger was pressed: %r" % out["T"])
        bad = [r for r in out["T"] if r["filed"] or r["prov"]]
        self.assertEqual([], bad, "A FOUND-EVER NAME REACHED A MULE — first trigger that filed: %s -> %s"
                         % ((bad[0]["trigger"], bad[0]["filed"][:6]) if bad else ("", "")))

    def test_3_a_set_piece_restored_as_a_unique_goes_to_the_set_door(self):
        """L3 (board half). The 15:28:34 shape: every foundLog key sent as a unique, set pieces included."""
        b = board()
        b.seed({"d2r_owned": [], "d2r_setPieces": [], "d2r_foundLog": {}, "d2r_muleAssign": {},
                "d2r_vaultProv": None})
        out = b.run("var r = window.chronicleApply({ wouldAdd: { uniques: %s.map(function(n){ return { name: n }; }),"
                    " sets: [] } }); OUT.sets = r.sets; OUT.uniques = r.uniques;"
                    "OUT.owned = JSON.parse(window.LSR.getItem('d2r_owned') || '[]');"
                    "OUT.setPieces = JSON.parse(window.LSR.getItem('d2r_setPieces') || '[]');"
                    "OUT.map = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');" % json.dumps(PIECES))
        for p in PIECES:
            self.assertNotIn(p, out["owned"], "the set piece %s fell into d2r_owned through toggleOwned — the "
                                              "found-ever refill of Event A" % p)
            self.assertIn(p, out["sets"], "the set piece %s was not routed to the set door: %r" % (p, out))
            self.assertIn(p, out["setPieces"], "the set piece %s was not ticked as a set piece" % p)
        self.assertEqual({}, out["map"], "a restored set piece was filed to a mule")

    def test_4_chronicle_accept_ticks_the_chronicle_only(self):
        """L5. "tick it" is the Chronicle; the vault needs his ruling AND a container sighting."""
        b = board()
        b.seed({"d2r_owned": [], "d2r_muleAssign": {}, "d2r_vaultProv": None, "d2r_chronicleInbox": []})
        out = b.run("OUT.a = window.kaiChronicleAccept('Nagelring');"
                    "OUT.b = window.kaiChronicleAccept('Arachnid Mesh', { vault: true });"
                    "OUT.map = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');")
        self.assertTrue(out["a"]["ok"], "the accept failed outright: %r" % out["a"])
        self.assertEqual("skipped", out["a"]["vault"], "Chronicle Accept touched the Vault by default: %r" % out["a"])
        self.assertNotEqual("filed", out["b"]["vault"], "a vault-accept with no container sighting filed: %r" % out["b"])
        self.assertIn("container", str(out["b"].get("vaultWhy") or out["b"].get("say") or ""),
                      "the refusal does not say it needs a container sighting: %r" % out["b"])
        self.assertEqual({}, out["map"], "a Chronicle accept became a mule filing")

    def test_5_his_hand_files_and_leaves_its_row(self):
        """THE POSITIVE CONTROL: the door is not simply shut. A click onto a locker is his declaration."""
        b = board()
        found_ever_world(b)
        out = b.run("window.vaultAssign('Nagelring', 'uni-small');"
                    "OUT.map = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                    "OUT.prov = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}');")
        self.assertEqual("uni-small", out["map"].get("Nagelring"), "his hand did not file: %r" % out["map"])
        row = out["prov"].get("Nagelring") or {}
        self.assertEqual("hand", row.get("source"), "his filing left no hand provenance: %r" % row)
        self.assertEqual("uni-small", row.get("mule"))


RED_PROOF = [
    {
        "why": "#246 W0 - the sorter walks the found-ever pool again: every owned name is filed",
        "file": "bible.html",
        "find": "    var _pvS = _provAll();\n",
        "replace": "    var _pvS = {}; ownedPool().forEach(function(n){ _pvS[n] = { source: 'hand', where: 'the found-ever pool' }; });\n",
        "matches": 1,
    },
    {
        "why": "#246 W1 - the TV registrar files with no witness again (the v2193 door that filed 112 Chronicle names)",
        "file": "bible.html",
        "find": "        _vf = witness ? window.vaultFile(name, witness, { mule: sg.id })\n",
        "replace": "        _vf = window.vaultFile(name, witness || { by: 'hand', where: 'no witness' }, { mule: sg.id });\n        if (false) _vf = witness ? window.vaultFile(name, witness, { mule: sg.id })\n",
        "matches": 1,
    },
    {
        "why": "#246 W0c - a set piece restored as a 'unique' falls into d2r_owned through toggleOwned again",
        "file": "bible.html",
        "find": "        if (_spn){ (res._setsFromUniques = res._setsFromUniques || []).push(",
        "replace": "        if (false && _spn){ (res._setsFromUniques = res._setsFromUniques || []).push(",
        "matches": 1,
    },
    {
        "why": "#246 W0e - Chronicle Accept files to the vault by default again",
        "file": "bible.html",
        "find": "    var _wantVault = !!(opts && opts.vault === true);\n",
        "replace": "    var _wantVault = !(opts && opts.vault === false);\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    # A class-level skip would print OK (skipped=N) and exit 0, which run_gates reads as a PASS. With no browser
    # binary at all this is a DECLARED skip (77); everything else runs and can fail.
    if not os.path.exists(RC.CHROME):
        sys.stderr.write("⚪ SKIP — %s. UNMEASURED, declared as a skip (77), never a pass.\n" % NO_BROWSER)
        raise SystemExit(77)
    unittest.main(verbosity=2)
