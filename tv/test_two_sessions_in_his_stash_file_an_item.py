# -*- coding: utf-8 -*-
"""REG-2022 - TWO SESSIONS SEEING IT IN HIS STASH FILE AN ITEM, WITH NO CONFIDENCE NEEDED WHEN THE READER GIVES NONE.

His words: "it should be doing this automatically regardless. as it gets intaked. eventually routed to the mule
related..". MEASURED on a copy of his board store (2026-10-07): the live reader records NO confidence - 400 of 400 ledger
rows and all 96 vault receipts carry conf null - so the door's "each look with its own conf >= 0.55" could never pass,
and nothing ever filed itself. And each live read hands the register ONE look, so a second session was judged alone
again. Asked, his call (#267): "2 sessions, no conf" - when not one look carries a confidence, a look counts on its own
frame and session, and two DISTINCT sessions in a place he keeps things file it.

Held here, on the SHIPPED page in a scratch Chrome:
  - the witness: two conf-less stash looks from two sessions pass; one session (even two frames of it) does not; a
    mixed witness (one look with a confidence) still drops the conf-less look, so an unsure read never files;
  - intake: a stash read in a new session files an item whose receipt already holds a stash look from another session;
  - the automatic sorter (vaultAutoAssign, which sweeps and applies call with nobody at the screen) files a receipt with
    two stash sessions on THAT witness - never as his hand - and files nothing for one look, MAIN-only looks, a discard
    suggestion, or an item his MAIN wore after the stash looks.
NO CHROME AT ALL = a declared skip, never a pass.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import test_a_sweep_never_reticks_what_he_unticked as H  # noqa: E402  (its Board drives the shipped page)

_B = {}


def board():
    if "b" not in _B:
        _B["b"] = H.Board().open()
    return _B["b"]


def tearDownModule():
    b = _B.pop("b", None)
    if b is not None:
        b.close()


def _look(sid, frame, at, loc):
    return {"id": sid, "frame": frame, "conf": None, "at": at, "loc": loc, "scene": "stash"}


def _receipt(looks):
    return {"kind": "owned", "source": "kai-register", "by": "law", "at": "2026-10-07T08:00:00.000Z", "looks": looks,
            "seen": len(looks)}


RECEIPTS = {
    "Nokozan Relic": [_look("s_1", "1_1", "2026-10-07T08:01:00.000Z", "stash"), _look("s_2", "2_1", "2026-10-07T09:01:00.000Z", "stash")],
    "Obedience": [_look("s_1", "3_1", "2026-10-07T08:02:00.000Z", "stash")],
    "Magefist": [_look("s_1", "4_1", "2026-10-07T08:03:00.000Z", "stash"), _look("s_1", "4_2", "2026-10-07T08:04:00.000Z", "stash")],
    "Arachnid Mesh": [_look("s_1", "5_1", "2026-10-07T08:05:00.000Z", "equipped"), _look("s_2", "5_2", "2026-10-07T09:05:00.000Z", "equipped")],
    "Isenhart's Case (armor)": [_look("s_1", "6_1", "2026-10-07T08:06:00.000Z", "stash"), _look("s_2", "6_2", "2026-10-07T09:06:00.000Z", "stash")],
    "Vampire Gaze": [_look("s_1", "7_1", "2026-10-07T08:07:00.000Z", "stash"), _look("s_2", "7_2", "2026-10-07T09:07:00.000Z", "stash"),
                     _look("s_3", "7_3", "2026-10-07T10:07:00.000Z", "equipped")],
    # one stash look + an OLDER inventory look from another session: only the stash look may count (the inventory look is
    # his MAIN's), and the newest placed look is the stash one, so the MAIN rule does not hide a wrong gather
    # (the stash look FIRST: a gather that took every look would then call the whole witness a stash one - the order the
    #  heart2 proof showed the case needs, or the wrong gather is refused as "inventory" for the wrong reason)
    "Gloom": [_look("s_1", "8_1", "2026-10-07T08:08:00.000Z", "stash"), _look("s_2", "8_0", "2026-10-07T07:08:00.000Z", "inventory")],
}


def _seed():
    board().seed({"d2r_owned": sorted(RECEIPTS), "d2r_vaultProv": {n: _receipt(l) for n, l in RECEIPTS.items()},
                  "d2r_muleAssign": {}})


@unittest.skipUnless(os.path.exists(H.RC.CHROME), "no Chrome/Chromium on this machine - UNMEASURED here, not passing")
class TwoSessionsInHisStashFileAnItem(unittest.TestCase):

    def test_the_witness_counts_conf_less_looks_only_when_the_reader_gives_none(self):
        o = board().run("""
          var C = window._vaultWitnessCheck;
          OUT.two = C({ lane: 'stash', sessions: [{ session: 's_a', frame: 'f_a' }, { session: 's_b', frame: 'f_b' }] });
          OUT.one = C({ lane: 'stash', sessions: [{ session: 's_a', frame: 'f_a' }] });
          OUT.sameSession = C({ lane: 'stash', sessions: [{ session: 's_a', frame: 'f_a' }, { session: 's_a', frame: 'f_a2' }] });
          OUT.mixed = C({ lane: 'stash', sessions: [{ session: 's_a', frame: 'f_a', conf: 0.9 }, { session: 's_b', frame: 'f_b' }] });
          OUT.noFrame = C({ lane: 'stash', sessions: [{ session: 's_a', frame: 'f_a' }, { session: 's_b', frame: null }] });""")
        self.assertTrue(o["two"].get("ok"), "two conf-less stash looks from two sessions were refused (his #267 ruling): %r" % o["two"])
        self.assertFalse(o["one"].get("ok"), "ONE session filed an item")
        self.assertFalse(o["sameSession"].get("ok"), "two frames of ONE session counted as two witnesses")
        self.assertFalse(o["mixed"].get("ok"), "a reader that DOES give confidences had its conf-less look counted")
        self.assertFalse(o["noFrame"].get("ok"), "a look with no frame counted")

    def test_the_automatic_sorter_files_two_stash_sessions_and_nothing_else(self):
        _seed()
        o = board().run("window.vaultAutoAssign(); OUT.a = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');"
                        "OUT.pv = (JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}')['Nokozan Relic']) || null;")
        a, pv = o["a"], o["pv"] or {}
        self.assertEqual(a.get("Nokozan Relic"), "uni-small", "two stash sessions did not file the item automatically: %r" % a)
        self.assertEqual(pv.get("source"), "stash", "the automatic filing does not say it stands on the stash looks: %r" % pv)
        self.assertNotEqual(pv.get("by"), "hand", "an automatic filing was stamped as his hand")
        for n, why in (("Obedience", "one look"), ("Magefist", "two frames of ONE session"),
                       ("Arachnid Mesh", "looks only on his MAIN"), ("Isenhart's Case (armor)", "a discard suggestion"),
                       ("Vampire Gaze", "worn by his MAIN after the stash looks"), ("Gloom", "one stash look - its inventory look is his MAIN's")):
            self.assertNotIn(n, a, "the automatic sorter filed %s - %s" % (n, why))

    def test_a_second_sessions_stash_read_files_it_at_intake(self):
        _seed()
        o = board().run("OUT.r = window.tvVaultRegister('Obedience', { lane: 'stash', by: 'kai-register',"
                        " sessions: [{ session: 's_9', frame: '9_1', conf: null }] });"
                        "OUT.a = JSON.parse(window.LSR.getItem('d2r_muleAssign') || '{}');")
        self.assertEqual(o["a"].get("Obedience"), "runewords",
                         "a stash read in a second session did not file an item its receipt already saw in another: %r" % o)


RED_PROOF = [
    {"why": "REG-2022 - a conf-less look never counts again, so nothing files itself at intake (400 of 400 reads have no conf)",
     "file": "bible.html",
     "find": "      if (!id || !fr || (c == null && _anyConf) || (c != null && c < VAULT_WITNESS_FLOOR)){ dropped++; return; }\n",
     "replace": "      if (!id || !fr || c == null || c < VAULT_WITNESS_FLOOR){ dropped++; return; }\n",
     "matches": 1},
    {"why": "REG-2022 - a mixed witness counts its conf-less look, so an unsure reader's look files",
     "file": "bible.html",
     "find": "      if (!id || !fr || (c == null && _anyConf) || (c != null && c < VAULT_WITNESS_FLOOR)){ dropped++; return; }\n",
     "replace": "      if (!id || !fr || (c != null && c < VAULT_WITNESS_FLOOR)){ dropped++; return; }\n",
     "matches": 1},
    {"why": "REG-2022 - the register judges a second session's read alone again, so the 2-session bar is never met at intake",
     "file": "bible.html",
     "find": "        _vf = witness ? window.vaultFile(name, _wG || witness, { mule: sg.id })\n",
     "replace": "        _vf = witness ? window.vaultFile(name, witness, { mule: sg.id })\n",
     "matches": 1},
    {"why": "REG-2022 - the automatic sorter makes an automatic discard / keep-on-MAIN decision",
     "file": "bible.html",
     "find": "        if (!_sgR || !_sgR.id || _sgR.id.charAt(0) === '_' || !muleById(_sgR.id)) return;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2022 - the automatic sorter files what his MAIN wore after the stash looks",
     "file": "bible.html",
     "find": "        if (window._vaultLastSeenOnMain && window._vaultLastSeenOnMain(name)) return;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2022 - a receipt's MAIN looks are gathered as stash looks",
     "file": "bible.html",
     "find": "    mine.filter(function(k){ return k && _WIT_STASH[String(k.loc || '').toLowerCase()]; })\n",
     "replace": "    mine.filter(function(k){ return !!k; })\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
