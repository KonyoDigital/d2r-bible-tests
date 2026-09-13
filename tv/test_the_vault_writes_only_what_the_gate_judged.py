# -*- coding: utf-8 -*-
"""THE VAULT WRITES ONLY THE ROWS THE GATE ACTUALLY JUDGED — never a second read of the proposal.

FOUND 2026-09-13 by handing `vault_apply` COLD to a different model family and asking it to design
attacks — the same method that found the `unsure` hole in v2641. It returned working payloads and
said it had run them against the live function with the board stubbed:

    class FlipList(list):
        def __iter__(self):              # FIRST pass (the gate): a corroborated decoy
            ...                          # every later pass (the write): the evidence-less row

    class FlipMap(dict):
        def get(self, key, default=None):   # answers "owned" differently on each call
            ...

THE HOLE. The re-gate walked `prop.get(_which)`, collected `_kept` and `_dropped`, refused if
anything dropped — and then THREW `_kept` AWAY. The payload was built from a SECOND read:

    owned  = prop.get("owned")  or []
    unsure = prop.get("unsure") or []
    shaped = _vault_retro().apply_payload(prop)      # a THIRD read

So a container whose later reads differ passed the gate with corroborated rows and delivered
uncorroborated ones. Its verdict: *"Killing this means writing `_kept`, not re-walking `owned`."*

⚠ IN-PROCESS ONLY, SAID PRECISELY: `json.loads` cannot build a lying container, so a POSTed body
could never carry one. This is not a report of an exposure. But this re-gate exists because "the
gate has to hold where the WRITE happens", and a gate whose verdict is discarded one line later
holds nowhere. Same shape as v3063's two-reads-of-one-file, one level up.
[[the-unjoined-end]] [[label-outlived-referent]]
"""
import os
import sys
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

CORROBORATED = {"name": "Decoy Rune", "lane": "stash", "kind": "rune", "count": 3,
                "evidence": [{"session": "s%d" % i, "witness": "s%d#0" % i, "conf": 0.9}
                             for i in range(3)]}
DIRTY = {"name": "Uncorroborated Shako", "lane": "stash", "kind": "item",
         "count": 1, "evidence": []}


class FlipList(list):
    """Answers the gate with a clean row and the write with the real one."""
    def __iter__(self):
        if not getattr(self, "_gated", False):
            self._gated = True
            return iter([CORROBORATED])
        return list.__iter__(self)


class PoisonRow(dict):
    """Attack 3: the ROW lies about its own evidence — snapshotting the row keeps the liar."""
    def get(self, k, default=None):
        if k in ("evidence", "witnesses") and not getattr(self, "_fed", False):
            self._fed = True
            return list(CORROBORATED["evidence"])
        return dict.get(self, k, default)


class FlipMap(dict):
    """The same idea one level up: `get` is not a snapshot."""
    def get(self, key, default=None):
        if key in ("owned",):
            n = getattr(self, "_n", 0) + 1
            self._n = n
            return [CORROBORATED] if n == 1 else [DIRTY]
        return dict.get(self, key, default)


def _drive(proposal):
    """Run vault_apply with the board stubbed. -> (verdict, what reached the board)"""
    import control_app as ca
    sent = {}

    def _fake_ejs(w, js, timeout=8.0):
        sent["js"] = js
        return '{"ok":true,"applied":{}}'

    real_ejs = getattr(ca, "_ejs", None)
    real_win = ca.__dict__.get("_BOARD_WIN")
    real_live = ca.__dict__.get("_WINDOW_LIVE")
    try:
        ca._ejs = _fake_ejs
        ca._BOARD_WIN = object()
        ca._WINDOW_LIVE = True
        v = ca.vault_apply(proposal=proposal)
    finally:
        if real_ejs is not None:
            ca._ejs = real_ejs
        ca._BOARD_WIN = real_win
        ca._WINDOW_LIVE = real_live
    return v, (sent.get("js") or "")


class TestTheVaultWritesOnlyWhatTheGateJudged(unittest.TestCase):

    def test_a_fliplist_cannot_swap_the_row_after_the_gate(self):
        _v, js = _drive({"ok": True, "owned": FlipList([DIRTY]),
                         "unsure": [], "throwOut": []})
        print("FlipList -> board saw decoy=%s dirty=%s"
              % ("Decoy Rune" in js, DIRTY["name"] in js))
        self.assertNotIn(DIRTY["name"], js,
                         "an uncorroborated row reached the board by answering the gate and the "
                         "write with different objects")

    def test_a_flipmap_cannot_swap_the_row_after_the_gate(self):
        b = FlipMap({"ok": True, "owned": [DIRTY], "unsure": [], "throwOut": []})
        _v, js = _drive(b)
        print("FlipMap  -> board saw decoy=%s dirty=%s"
              % ("Decoy Rune" in js, DIRTY["name"] in js))
        self.assertNotIn(DIRTY["name"], js,
                         "get('owned') is not a snapshot, and the write took the second answer")

    def test_what_the_gate_approved_is_what_is_written(self):
        """The positive half — the fix must not simply drop everything."""
        _v, js = _drive({"ok": True, "owned": [dict(CORROBORATED)],
                         "unsure": [], "throwOut": []})
        print("clean proposal -> board saw decoy=%s" % ("Decoy Rune" in js))
        self.assertIn("Decoy Rune", js,
                      "a corroborated row must still reach the board, or this 'fix' is just a "
                      "refusal wearing a gate's clothes")

    def test_an_uncorroborated_row_is_still_refused_outright(self):
        v, js = _drive({"ok": True, "owned": [dict(DIRTY)], "unsure": [], "throwOut": []})
        ok = isinstance(v, dict) and v.get("ok") is False
        print("plain dirty proposal -> refused=%s board touched=%s" % (ok, bool(js)))
        self.assertTrue(ok, "the original v1595 re-gate must still refuse a plain bad proposal")
        self.assertEqual("", js, "nothing may reach the board when the gate refuses")


    def test_a_row_cannot_lie_about_its_own_evidence(self):
        """Attack 3. v3066 snapshotted the ROW OBJECTS, which keeps a row that lies."""
        v, js = _drive({"ok": True,
                        "owned": [PoisonRow({"name": "Poison Shako", "lane": "stash",
                                             "kind": "item", "count": 1})],
                        "unsure": [], "throwOut": []})
        refused = isinstance(v, dict) and v.get("ok") is False
        print("PoisonRow -> refused=%s leaked=%s" % (refused, "Poison Shako" in js))
        self.assertNotIn("Poison Shako", js,
                         "a row whose .get('evidence') answers the gate once must not reach the "
                         "board — the stored dict carries no witnesses at all")
        self.assertTrue(refused, "and it must be refused, not silently dropped")

    def test_a_non_dict_mapping_cannot_skip_the_gate(self):
        """Attack 4. `isinstance(prop, dict)` was the whole on-switch, and UserDict is not a dict."""
        from collections import UserDict
        v, js = _drive(UserDict({"ok": True, "owned": [dict(DIRTY)],
                                 "unsure": [], "throwOut": []}))
        refused = isinstance(v, dict) and v.get("ok") is False
        print("UserDict  -> refused=%s leaked=%s" % (refused, DIRTY["name"] in js))
        self.assertNotIn(DIRTY["name"], js,
                         "a Mapping that is not a dict subclass skipped the re-gate entirely and "
                         "its row went through ungated")
        self.assertTrue(refused, "the gate must SPEAK for any caller-supplied mapping")

    def test_the_throwout_lane_carries_no_evidence_field(self):
        """Attack 5. Never gated, and it reached the payload.

        ⚠ THE ROW IS NOT REMOVED, AND THAT IS DELIBERATE: a throw-out is a suggestion to DISCARD
        and has no reason to carry three witnesses; requiring them would refuse every honest one.
        What it must not do is carry a field that can be MISTAKEN for corroboration.
        """
        _v, js = _drive({"ok": True, "owned": [dict(CORROBORATED)], "unsure": [],
                         "throwOut": [dict(DIRTY)]})
        import re as _re
        m = _re.search(r'"throwOut":\s*(\[.*?\])', js)
        t = m.group(1) if m else ""
        print("throwOut payload: %s" % t[:110])
        self.assertTrue(t, "the throw-out lane vanished entirely — that is a different defect")
        self.assertNotIn("evidence", t, "a throw-out must not carry an evidence key")
        self.assertNotIn("witnesses", t, "nor a witnesses key")
        self.assertIn(DIRTY["name"], t, "the NAME is the point of a throw-out and must survive")


RED_PROOF = [
    {
        "why": "the caller-supplied proposal is no longer converted to inert data, so a row that "
               "lies about its own evidence, and a Mapping that is not a dict, both get through",
        "file": "control_app.py",
        "find": "    if caller_supplied:\n        proposal = _inert(proposal)",
        "replace": "    if caller_supplied:\n        pass",
        "matches": 1,
    },
    {
        "why": "the throw-out lane carries its evidence keys into the payload again, where they "
               "can be mistaken for corroboration",
        "file": "control_app.py",
        "find": '                _throw.append(dict((k, v) for k, v in (_t or {}).items()\n'
                '                                   if k not in ("evidence", "witnesses")))',
        "replace": "                _throw.append(_t)",
        "matches": 1,
    },
]

# ⚠⚠ THREE SABOTAGES WERE WRITTEN AND WITHDRAWN, and the reason is worth more than the proofs.
#
# Two of them reverted v3066's snapshot — the `_gated` substitution and the shaper's `dict(prop,
# **_gated)`. heart2 returned BLIND on both. It is right: once v3067 converts a caller-supplied
# proposal to INERT DATA at the door, no later read can be answered by code, so undoing the
# snapshot defeats nothing. v3066's fix was correct for the two attacks it was written against
# and was SUPERSEDED by the narrower door a version later. The snapshot stays because it states
# intent and costs nothing, but it is no longer load-bearing and is not claimed as proof.
#
# A THIRD SABOTAGE WAS ALSO WITHDRAWN, AND THAT IS RECORDED RATHER THAN QUIETLY DROPPED.
# It reverted `for _r in list(prop.get(_which) or [])` to the bare `prop.get(...)`, on the theory
# that materialising the walked rows was load-bearing. heart2 returned BLIND — "stayed GREEN
# through its own defeat". It is right: with `_gated` snapshotting the judged rows, the `list()` no
# longer changes the outcome on its own. The call stays because it is cheap and honest about
# intent, but it is NOT claimed as a proof. A sabotage that does not defeat the guard proves
# nothing, and banking it would inflate this lock's evidence with a refusal nobody earned.
# [[sabotage-is-usually-the-wrong-one]] [[regression-guard]]

if __name__ == "__main__":
    unittest.main(verbosity=2)
