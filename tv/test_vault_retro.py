"""v1595 — THE VAULT ACCUMULATOR'S LAWS, proven rather than asserted.

Konyo: *"the vault manager is synced to also slowly analyze and remember especially between and
among sessions ... and slowly also feed the vault manager for throwing out or muling the items read
at the time."*

Accumulating a picture of what he owns ACROSS sessions is a different risk profile from a single
read, and every test here exists because of one specific way it could quietly ruin his stash:

  MERGE-MAX — a later read that sees FEWER items must never subtract. An obstructed or half-scrolled
  stash frame is a NORMAL event, not evidence he threw something away. Get this wrong and the
  accumulator slowly eats his own inventory, one bad frame at a time, while looking like it is
  working.

  THROW-OUT NEEDS MORE EVIDENCE THAN KEEP — there is no un-throw in Diablo. It is the only
  irreversible action in the whole app, so it carries a higher bar and stays a SUGGESTION.

  ORDER MUST NOT MATTER — sessions arrive in whatever order the sweep happens to read reels. If
  merge(a,b) and merge(b,a) can disagree, the ledger depends on disk order, which is not a fact
  about his stash.

  MISSING IS NOT ZERO — a count nobody could read stays unknown, with a reason. An invented zero is
  indistinguishable from "he has none of these", and that is what drives a throw-out.

The workflow that built vault_retro.py left this file unwritten and said so; its own ad-hoc poke
used rows with no `name`/`lane`, which `_rows_of` correctly drops, and it read the empty result as
possible breakage rather than a malformed probe. These tests use the real row shape.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402 — non-ASCII in the failure messages must survive a
                     # non-UTF-8 console; a test that cannot report is not a test.
import vault_retro as v  # noqa: E402
import chronicle_retro as cr  # noqa: E402

LANE = "stash"


def row(name, count=1, lane=LANE, **kw):
    r = {"name": name, "lane": lane, "count": count}
    r.update(kw)
    return r


def count_of(res, name):
    for r in res["owned"]:
        if r["name"] == name:
            return r.get("count")
    return None


class TestV1786TheReGateCanActuallyGate(unittest.TestCase):
    """v1786 — THE RE-GATE REFUSED EVERY GENUINE PROPOSAL AND BLAMED THE READER.

    control_app re-checks a caller-supplied proposal at the WRITE, feeding each row's provenance
    back into gate(). gate() reads conf; _witness_rows emitted {session, frame, lane} and nothing
    else. So bestConf was 0.0 and a real proposal — two sessions at 0.97 and 0.95 — came back "the
    reader itself was unsure (0.00 < 0.55)": refused on a field the provenance never carried.

    It was fail-CLOSED only by accident (the console posts an empty body today). The moment anything
    posted the engine's own proposal back, apply would refuse everything — and a HAND-MADE body
    carrying conf would sail through, which is the wrong way round. Found by an adversarial review."""

    def test_a_genuine_proposal_clears_its_own_re_gate(self):
        # v2073 — as many looks as the LAW asks for, not the two this was written with. His ruling
        # moved KEEP_MIN_WITNESSES to 3 and this case is about whether a genuine proposal clears its
        # own re-gate, not about any particular number.
        ev = [{"session": "s_%d" % i, "frame": "f%d" % i, "lane": "stash", "conf": 0.97 - 0.01 * i}
              for i in range(v.KEEP_MIN_WITNESSES)]
        row = v._owned_row(("Ist Rune", "stash"), ev)
        wit = row.get("witnesses") or row.get("evidence") or []
        self.assertTrue(wit, "the row carries no provenance at all")
        self.assertIsNotNone(wit[0].get("conf"),
                             "witness rows still carry no conf — the re-gate cannot judge them")
        # NB: this file imports vault_retro as `v`, so the verdict cannot also be called v
        verdict = v.gate(wit, v.KEEP_CONF_FLOOR, v.KEEP_MIN_WITNESSES)
        self.assertTrue(verdict.get("pass"),
                        "the engine's own proposal fails its own gate: %s" % verdict.get("why"))

    def test_a_weak_single_sighting_is_still_refused(self):
        """Non-vacuity: the fix must not turn the gate into a rubber stamp."""
        weak = [{"session": "s_1", "frame": "f1", "lane": "stash", "conf": 0.20}]
        self.assertFalse(v.gate(weak, v.KEEP_CONF_FLOOR, v.KEEP_MIN_WITNESSES).get("pass"))


class TestMergeMax(unittest.TestCase):
    """Law 1, and the one that can silently destroy his ledger."""

    def test_a_smaller_later_read_never_subtracts(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 3)])
        self.assertEqual(count_of(res, "Ral Rune"), 9,
                         "a later read seeing 3 must NOT lower a held count of 9 — a half-scrolled "
                         "stash frame is normal, not evidence he threw six runes away")

    def test_the_shortfall_is_reported_not_swallowed(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 3)])
        held = [h if isinstance(h, str) else h.get("name") for h in res["held"]]
        self.assertIn("Ral Rune", held,
                      "refusing to subtract is right; refusing SILENTLY is not — the shortfall has "
                      "to be visible or a genuine loss looks identical to an obstructed frame")

    def test_a_larger_later_read_does_raise(self):
        res = v.merge_vault([row("Ral Rune", 9)], [row("Ral Rune", 14)])
        self.assertEqual(count_of(res, "Ral Rune"), 14)
        raised = [x if isinstance(x, str) else x.get("name") for x in res["raised"]]
        self.assertIn("Ral Rune", raised)

    def test_an_item_missing_from_a_later_read_survives(self):
        """Absence is not a claim. He did not throw the Shako away by walking to another tab."""
        res = v.merge_vault([row("Shako", 1), row("Ral Rune", 9)], [row("Ral Rune", 9)])
        self.assertEqual(count_of(res, "Shako"), 1,
                         "an item the second read never saw must survive — absence of evidence is "
                         "not evidence of absence, and this is the exact shape of a scroll position")

    def test_order_cannot_change_the_answer(self):
        a = [row("Ral Rune", 9), row("Shako", 1)]
        b = [row("Ral Rune", 3), row("Ist Rune", 2)]
        one = {r["name"]: r.get("count") for r in v.merge_vault(a, b)["owned"]}
        two = {r["name"]: r.get("count") for r in v.merge_vault(b, a)["owned"]}
        self.assertEqual(one, two,
                         "sessions arrive in whatever order the sweep reads reels; if the fold is "
                         "not order-independent the ledger describes the disk, not his stash")

    def test_lanes_do_not_bleed_into_each_other(self):
        """stash / inventory / equipment are different places. The same item in two of them is two
        rows, not one — merging them would invent items he does not have."""
        res = v.merge_vault([row("Ral Rune", 9, lane="stash")],
                            [row("Ral Rune", 2, lane="inventory")])
        got = sorted((r["name"], r["lane"], r.get("count")) for r in res["owned"])
        self.assertEqual(len(got), 2, "same name in two lanes must stay two rows: %r" % (got,))


class TestThrowOutIsHarderThanKeep(unittest.TestCase):
    """Law 4. There is no un-throw in Diablo."""

    def test_the_throw_bar_is_strictly_higher_than_the_keep_bar(self):
        self.assertGreater(v.THROWOUT_CONF_FLOOR, v.KEEP_CONF_FLOOR,
                           "advising a throw-out must need MORE confidence than advising a keep")
        self.assertGreater(v.THROWOUT_MIN_WITNESSES, v.KEEP_MIN_WITNESSES,
                           "and more witnesses")

    def test_the_keep_bar_is_the_chronicle_bar(self):
        """One calibrated number, not two that drift. The chronicle's floor was tuned on his own
        footage; a second copy would be a second thing to re-tune and only one would get it."""
        self.assertEqual(v.KEEP_CONF_FLOOR, cr.CONF_FLOOR)

    def test_a_throw_out_is_never_automatic(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "vault_retro.py"), encoding="utf-8").read()
        self.assertIn("automatic", src)
        self.assertNotIn("automatic\": True", src.replace("'", '"'),
                         "nothing may mark a throw-out automatic — it is a suggestion, always")


class TestHonestAbsence(unittest.TestCase):
    """Law 5. An invented zero is what drives a wrong throw-out."""

    def test_a_sweep_with_no_reader_refuses_instead_of_returning_empty(self):
        out = v.sweep(["/nonexistent/reel"])
        self.assertFalse(out.get("ok"),
                         "no reader supplied is a REFUSAL, not an empty vault — an empty result "
                         "here reads as 'he owns nothing', which is the input to a throw-out")
        self.assertTrue(str(out.get("why") or "").strip(), "and it must say why")

    def test_rows_without_a_name_or_lane_contribute_nothing(self):
        """The shape that fooled the build agent: a bare {key: {count}} map has no name and no lane,
        so it is not a row and must not become one."""
        res = v.merge_vault({"ral": {"count": 9}}, {"ral": {"count": 3}})
        self.assertEqual(res["owned"], [],
                         "a malformed row must be dropped, never guessed into existence")


class TestReuseNotReimplementation(unittest.TestCase):
    """The accumulator is the chronicle sweep pointed at a different target. Two copies of a
    threshold calibrated on his footage is two things that drift apart, and only one gets re-tuned."""

    def test_it_imports_the_chronicle_primitives_rather_than_copying_them(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "vault_retro.py"), encoding="utf-8").read()
        self.assertIn("chronicle_retro", src)
        for prim in ("still_runs", "jpeg_sig"):
            self.assertNotIn("def %s(" % prim, src,
                             "%s must be IMPORTED from chronicle_retro, not redefined here" % prim)


class TestMiniReelIsFoundable(unittest.TestCase):
    """v1595 — the agent now stamps `mini` into the reel index. Before that, is_mini_reel() could
    never return True on a real reel and the mini-first ordering was unreachable code."""

    def test_a_stamped_index_is_recognised(self):
        self.assertTrue(v.is_mini_reel({"mini": True}),
                        "the stamp the agent writes must be the stamp the sweep looks for")

    def test_an_unstamped_reel_is_not_mini(self):
        self.assertFalse(v.is_mini_reel({"sessionId": "s1", "n": 40}))

    def test_the_agent_actually_writes_that_stamp(self):
        """The other half. A reader that recognises a stamp nobody writes is the dead-seam class."""
        agent = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "tv_diablo.py"), encoding="utf-8").read()
        # v1608 — MATCH THE FACT, NOT THE VARIABLE NAME. This asserted the literal
        # `_idx["mini"] = True`, and when the seal was restructured (the index is now written
        # before the blank pass) the dict was renamed _idx -> _ixdoc. The stamp was still written,
        # byte-identical in meaning, and this test went red on a rename — a false alarm on a
        # healthy change, which is the failure mode that teaches people to delete tests.
        # The dead-seam protection is "something writes a mini flag into the reel index"; that is
        # what is checked now, independent of what the local variable happens to be called.
        import re as _re
        self.assertTrue(_re.search(r'\[\s*["\']mini["\']\s*\]\s*=\s*True', agent),
                        "tv_diablo must stamp the reel with a mini flag, or is_mini_reel can "
                        "never fire on real footage")
        self.assertTrue(_re.search(r'\[\s*["\']focus["\']\s*\]\s*=\s*MINI_FOCUS', agent),
                        "and the FOCUS must be stamped too — v1603's sweep trusts it in place of "
                        "a classify call, so a reel without it silently loses that whole benefit")
        self.assertIn("MINI_MODE", agent)


class TestADeclaredFocusIsTrusted(unittest.TestCase):
    """v1603 — Konyo: "is this finally focused and understanding of the fact that it is reading
    stash/runes/gems/materials and to look out specifically for this".

    Before this, no: `focus` was stamped on the reel and used ONLY to sweep mini reels first
    (is_mini_reel's docstring: "being wrong here costs ordering, never correctness"). Every run
    still paid a classify call to rediscover a fact already on disk — and could still get it wrong,
    which is worse than the cost: a rune tab misread as "inventory" files his runes in the wrong
    lane, and merge-max then makes that permanent.

    Trusting it is the SAME trade chronicle_retro.sweep_frames() has made for the live lane since
    v1527. Cheaper and more accurate at once, because the call it removes is the one that could lie.
    """

    def test_an_ownership_focus_is_taken_from_the_stamp(self):
        self.assertEqual(v._declared_surface({"focus": "runes"}), "runes")
        self.assertEqual(v._declared_surface({"focus": "STASH"}), "stash")

    def test_a_chronicle_focus_is_NOT_this_sweep_s_business(self):
        """chronicle-uniques/sets are real mini focuses, but the chronicle sweep owns them. Claiming
        one here would file grail pages into the vault as though they were a stash tab."""
        self.assertIsNone(v._declared_surface({"focus": "chronicle-uniques"}))
        self.assertIsNone(v._declared_surface({"focus": "chronicle-sets"}))

    def test_an_unknown_focus_is_never_trusted(self):
        """The stamp replaces a paid read, so anything not in the vocabulary must fall through to
        the classifier rather than becoming a lane by assertion."""
        for junk in ("", None, "cube", "belt", "../stash", 7, {"a": 1}):
            self.assertIsNone(v._declared_surface({"focus": junk}), repr(junk))

    def test_a_reel_with_no_focus_behaves_exactly_as_before(self):
        self.assertIsNone(v._declared_surface({}))
        self.assertIsNone(v._declared_surface(None))


class TestApplyPayloadIsTheProductionSHAPE(unittest.TestCase):
    """v1998 — the function that shapes EVERY payload the board receives had never been executed.

    Measured before this class existed: `apply_payload` appears in ZERO test files. It owns the
    contract between this module and the board, and it is where REG-341 lived — it emitted
    `"witnesses": len(...)`, turning the list `_witness_rows` builds into an int. Every reader on
    the board treats it as an ARRAY (`witnesses[0].session`, `witnesses.length`), so a JS loop over
    a number simply never ran, and the 3-session equipment lock could not fire on a real apply. It
    locked fine against hand-made arrays in the tests that existed, because none of them went
    through this function.

    Grok's read of the same gap, 2026-08-23: "No committed test asserts apply_payload items have
    list witnesses… Without this, REG-341 is a comment."
    """

    @staticmethod
    def _prop(**kw):
        import vault_retro as vr
        ev = lambda s, f, lane, c: {"session": s, "frame": f, "lane": lane, "conf": c,
                                    "kind": "item", "count": None, "ts": 1787242458369}
        row = vr._owned_row(("Harlequin Crest", "equipment"),
                            [ev("s_A", "f1", "equipment", 0.97),
                             ev("s_B", "f2", "equipment", 0.95),
                             ev("s_C", "f3", "equipment", 0.96)])
        base = {"ok": True, "owned": [row], "generatedTs": 1787242458369,
                "sessionsRead": ["s_A", "s_B", "s_C"]}
        base.update(kw)
        return base

    def test_witnesses_ship_as_ROWS_and_the_count_rides_beside_them(self):
        import vault_retro as vr
        it = vr.apply_payload(self._prop())["items"][0]
        self.assertIsInstance(it["witnesses"], list,
                              "witnesses collapsed to a scalar — the board loops over it and a loop "
                              "over a number never runs, which is REG-341 exactly")
        self.assertEqual(len(it["witnesses"]), 3)
        self.assertEqual(it["witnessCount"], 3, "the count must survive as its own field")
        self.assertNotIsInstance(it["witnesses"], int)

    def test_the_board_can_count_DISTINCT_sessions_the_way_the_lane_lock_does(self):
        """The lock needs 3 DISTINCT sessions. That is only possible if the rows carry `session`."""
        import vault_retro as vr
        w = vr.apply_payload(self._prop())["items"][0]["witnesses"]
        self.assertEqual(sorted({r["session"] for r in w}), ["s_A", "s_B", "s_C"])
        for r in w:
            self.assertTrue(r.get("frame"), "provenance lost: reel/frame live on these rows and nowhere else")
            self.assertEqual(r.get("lane"), "equipment")
            self.assertIsNotNone(r.get("conf"), "conf is re-gated from these rows by control_app")

    def test_non_dict_witnesses_are_dropped_rather_than_shipped(self):
        import vault_retro as vr
        p = self._prop()
        p["owned"][0]["witnesses"] = [{"session": "s_A", "frame": "f1", "lane": "stash", "conf": 0.9},
                                      "not-a-row", None, 7]
        it = vr.apply_payload(p)["items"][0]
        self.assertEqual(len(it["witnesses"]), 1, "a junk witness reached the board")
        self.assertEqual(it["witnessCount"], 4,
                         "witnessCount counts what the sweep SAW, not what survived the filter — "
                         "collapsing those two hides that something was dropped")

    def test_the_free_pixel_evidence_is_carried_through(self):
        """v1996 — glimpsed/reconciled/overRead were computed and then dropped HERE, so the board
        could not render them however much it wanted to."""
        import vault_retro as vr
        pl = vr.apply_payload(self._prop(
            glimpsed=[{"frame": "f_a.jpg", "surface": "personal", "occupied": 22, "free": 18}],
            reconciled=[{"frame": "f_b.jpg", "named": 27, "occupied": 22, "verdict": "over-read"}],
            overRead=[{"frame": "f_b.jpg", "named": 27, "occupied": 22}]))
        self.assertEqual(len(pl["glimpsed"]), 1)
        self.assertEqual(len(pl["reconciled"]), 1)
        self.assertEqual(pl["overRead"][0]["named"], 27)

    def test_a_refused_proposal_returns_empty_lists_and_never_None(self):
        """`None` and `[]` mean different things and the board branches on both."""
        import vault_retro as vr
        out = vr.apply_payload({"ok": False, "why": "nothing to propose"})
        self.assertFalse(out["ok"])
        self.assertEqual(out["items"], [])
        self.assertEqual(out["suggestions"], [])
        self.assertIn("nothing to propose", out["why"])

    def test_it_writes_nothing(self):
        """The law the whole arc rests on: this module may never write."""
        import vault_retro as vr
        p = self._prop()
        before = json.dumps(p, sort_keys=True, default=str)
        vr.apply_payload(p)
        self.assertEqual(json.dumps(p, sort_keys=True, default=str), before,
                         "apply_payload mutated the proposal it was handed")


class TestApplyPayloadCannotSilentlyDropAField(unittest.TestCase):
    """apply_payload names the fields it ships, so a field added to _owned_row simply does not
    arrive and nothing fails. That has happened FOUR times — v1986, v1996, v2004, v2006 — and
    v1986's cost REG-339's 3-session equipment lock on the only path that actually runs, while the
    tests kept passing against hand-made arrays.

    This is the fifth-time guard: every field an owned row carries must either SHIP or be named in
    vault_retro.APPLY_NOT_SHIPPED with a reason. Neither is a failure."""

    def _row(self):
        ev = [{"session": "s_%d" % i, "witness": "s_%d#0" % i, "frame": "f%d.jpg" % i,
               "lane": "stash", "conf": 0.9, "count": 3 + i, "kind": "item",
               "ts": 1787600000000 + i} for i in range(v.KEEP_MIN_WITNESSES)]
        return v._owned_row(("Shako", "stash"), ev), ev

    def test_every_owned_field_either_ships_or_is_declared_unshipped(self):
        row, _ = self._row()
        pay = v.apply_payload({"ok": True, "owned": [row], "throwOut": [], "generatedTs": 1})
        self.assertTrue(pay.get("items"), "apply_payload shipped no items at all")
        shipped = set(pay["items"][0])
        declared = set(getattr(v, "APPLY_NOT_SHIPPED", {}))
        missing = set(row) - shipped - declared
        self.assertEqual(missing, set(),
                         "apply_payload silently drops %s — a board reader asking for it gets "
                         "undefined and nothing fails. Ship it, or name it in APPLY_NOT_SHIPPED "
                         "with a reason." % sorted(missing))

    def test_the_declared_list_cannot_hide_a_field_that_is_actually_gone(self):
        """A declaration is a decision, not a dumping ground: every name in APPLY_NOT_SHIPPED must
        really be a field an owned row carries, or it is stale and hiding nothing."""
        row, _ = self._row()
        stale = set(getattr(v, "APPLY_NOT_SHIPPED", {})) - set(row)
        self.assertEqual(stale, set(),
                         "APPLY_NOT_SHIPPED names %s, which an owned row no longer carries — a "
                         "stale exemption silently covers whatever takes that name next" % sorted(stale))

    def test_witnesses_ship_as_ROWS_not_as_a_count(self):
        """v1986, pinned. `witnesses` as an int made every board loop over it a no-op."""
        row, ev = self._row()
        pay = v.apply_payload({"ok": True, "owned": [row], "throwOut": [], "generatedTs": 1})
        w = pay["items"][0].get("witnesses")
        self.assertIsInstance(w, list, "witnesses shipped as %s — a board `for (i<w.length)` over a "
                                       "number never runs" % type(w).__name__)
        self.assertEqual(len(w), len(ev))
        self.assertTrue(all(isinstance(x, dict) for x in w))
        self.assertEqual(pay["items"][0].get("witnessCount"), len(ev),
                         "the count that replaced the int is gone too")

    def test_provenance_survives_the_shaping(self):
        """reel and frame live on the witness dicts and NOWHERE else in `items`. Losing the rows
        loses the only pointer back to the pixels."""
        row, _ = self._row()
        pay = v.apply_payload({"ok": True, "owned": [row], "throwOut": [], "generatedTs": 1})
        w = pay["items"][0]["witnesses"]
        self.assertTrue(any(x.get("frame") for x in w),
                        "no witness carries a frame — the row can no longer be traced to what it "
                        "was read from")
        self.assertTrue(any(x.get("session") for x in w), "no witness carries a session")


if __name__ == "__main__":
    unittest.main(verbosity=2)
