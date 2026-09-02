"""A21c — the guard over the chronicle routes and their corroborator.

⚠ EVERY TEST HERE PINS A LAW, NEVER TODAY'S ROSTER. There are three chronicle routes this week and
one of them is DARK; both of those facts should change, and a test that asserts either would go red
for the wrong reason the day the work lands. What must not change is the RULE: a describer is never
a watcher, a stamp is never a check, and a lane a majority carries is flagged on the one that does
not. [[regression-guard]] [[unknown-stays-unknown]]

Each test below was seen RED for its own reason before being trusted — the exact inversion it
guards was restored, the test watched to fail, then the fix restored and watched to pass.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chronicle_routes as CR


def _route(key, **lanes):
    """A synthetic route. The corroborator is a pure function of shape, so it can be exercised
    without a repo — which is the only way to keep these tests off today's defect."""
    base = {ln: {"ok": True, "by": ["x"]} for ln in CR.LANES}
    for k, v in lanes.items():
        base[k] = dict(base[k], **v)
    return {"key": key, "lanes": base}


class TheCorroboratorNamesTheOddOneOut(unittest.TestCase):

    def test_a_lane_the_majority_carries_is_flagged_on_the_one_that_lacks_it(self):
        rows = [_route("a"), _route("b"), _route("c", freshness={"ok": False})]
        flags = CR.corroborate(rows)
        hit = [f for f in flags if f["route"] == "c" and f["lane"] == "freshness"]
        self.assertEqual(len(hit), 1, "the divergent route was not flagged: %r" % flags)
        self.assertEqual(sorted(hit[0]["siblings"]), ["a", "b"],
                         "a flag must NAME the siblings — 'something is different' is not a "
                         "finding anyone can act on")

    def test_one_against_one_is_a_coincidence_and_is_NOT_flagged(self):
        """Two routes disagreeing is not a majority. Flagging here would brand the FIRST route to
        gain a new lane as the broken one — the inverse of what this is for."""
        rows = [_route("a"), _route("b", freshness={"ok": False})]
        self.assertEqual(CR.corroborate(rows), [],
                         "1-vs-1 must stay silent; there is no majority to diverge from")

    def test_a_check_no_gate_runs_is_flagged_separately_from_no_check_at_all(self):
        rows = [_route("a", freshness={"ok": True, "enforced": ["t -> f"]}),
                _route("b", freshness={"ok": True, "enforced": ["t -> f"]}),
                _route("c", freshness={"ok": True, "enforced": []})]
        flags = CR.corroborate(rows)
        self.assertTrue(any(f["lane"] == "freshness/enforced" and f["route"] == "c" for f in flags),
                        "a freshness check nobody runs must be flagged; existing is not running")

    def test_the_corroborator_returns_flags_and_never_a_verdict(self):
        """Standing rule in this console: a lock is a stamp, never a gate. Nothing this returns may
        be shaped like something a caller could enforce."""
        rows = [_route("a"), _route("b"), _route("c", resolver={"ok": False})]
        for f in CR.corroborate(rows):
            self.assertEqual(sorted(f), ["lane", "route", "say", "siblings"],
                             "a flag carries an explanation and nothing that reads as a verdict")


class TheDescriberIsNotAWatcher(unittest.TestCase):

    def test_this_module_never_counts_as_a_freshness_lane_for_anything(self):
        """⚠ THE FALSE GREEN THIS WAS BUILT AFTER. chronicle_routes.py names every roster artifact
        and reads `sourceHash`, so the comparator scan found ITSELF and reported a route as watched
        by the very code whose only job is to say whether anything watches it. Without the
        self-exclusion this module can never report a DARK route at all."""
        comps = CR._comparators()
        mine = [k for k in comps if k.startswith("chronicle_routes.")]
        self.assertEqual(mine, [], "the deriver is vouching for itself: %r" % mine)

    def test_stamping_a_hash_is_not_checking_it(self):
        """A writer that stamps `sourceHash` into the artifact it just built has not verified
        anything. Its siblings' `is_stale` recomputes and compares; that is the lane."""
        comps = CR._comparators()
        self.assertNotIn("build_runeword_roster.build", comps,
                         "a function that only WRITES the stamp was counted as a freshness check")
        self.assertTrue(any(k.endswith(".is_stale") for k in comps),
                        "no comparator found at all — the scan is measuring nothing, which would "
                        "make every route read DARK for the instrument's reason, not the repo's")


class TheRoutesSpeakTheHeartsVocabulary(unittest.TestCase):

    def test_every_route_carries_all_five_lanes_and_one_of_the_four_words(self):
        d = CR.routes()
        self.assertTrue(d.get("ok"), d.get("why"))
        self.assertTrue(d["routes"], "no routes derived — that is UNKNOWN, and it must say so")
        for r in d["routes"]:
            self.assertIn(r["state"], (CR.FLOWING, CR.WATCHED, CR.DARK, CR.UNKNOWN),
                          "a fifth status word defeats the point of one vocabulary")
            for ln in CR.LANES:
                self.assertIn(ln, r["lanes"], "%s is missing the %s lane" % (r["key"], ln))
            self.assertTrue(r["why"], "%s carries a state with no explanation" % r["key"])

    def test_a_route_that_cannot_be_read_is_UNKNOWN_and_never_absent(self):
        """An unparseable roster must not silently drop out of the census — a chronicle that
        vanishes from the list reads as 'there are only two', which is a different and false
        claim than 'one of the three could not be read'."""
        lane = CR._artifact_lane("no_such_roster.json")
        self.assertIs(lane["ok"], False)
        self.assertTrue(lane["why"], "an unreadable artifact must say why")
        self.assertIsNone(lane["count"], "a count nobody could read is None, never 0")


class TheRunewordRouteIsNowWatchedLikeItsSiblings(unittest.TestCase):
    """v2455 — A21c. The gate half of the fix. `is_stale()` existing is not the lane; a gate
    RUNNING it is. Without this class the corroborator would still flag the route, correctly, as
    "a freshness check that no gate runs" — which is the same defect one step further along.
    [[the-unjoined-end]]"""

    def test_the_runeword_roster_still_matches_the_page(self):
        import build_runeword_roster as B
        stale, why = B.is_stale()
        self.assertFalse(stale, "the runeword roster has drifted from bible.html: %s" % why)

    def test_a_hand_edited_roster_is_caught_even_when_the_stamp_matches(self):
        """The stamp proves the SOURCE block; it says nothing about the artifact's own contents.
        A count that disagrees with the page means the file was edited by hand, and that must not
        pass just because the hash still lines up."""
        import json
        import tempfile
        import build_runeword_roster as B
        doc = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "runeword_roster.json")))
        doc["count"] = int(doc["count"]) + 1
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(doc, fh)
        fh.close()
        stale, why = B.is_stale(path=fh.name)
        os.unlink(fh.name)
        self.assertTrue(stale, "a hand-edited count sailed through")
        self.assertIn("hand-edited", why)


if __name__ == "__main__":
    try:                       # cp1255 cannot encode the ⚠ these tests print
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
