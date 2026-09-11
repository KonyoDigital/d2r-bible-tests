# -*- coding: utf-8 -*-
"""v2985 — A ROW MUST NAME THE STORE IT IS ACTUALLY IN.

HIS RULING, 2026-09-12: *"leave the keys alone, just fix the store label"*.

THE DEFECT. `kaiChronicleSettledWhy` asked `_gFound(nm)` and, on a hit, stamped
`store: 'foundLog'`. But `_gFound` is a UNION — its first line is `if (owned.has(n)) return true;`
and only then does it consult `d2r_foundLog`. The comment directly above the call says so in its
own words: *"live _gFound (includes legacy owned)"*. So a name living in `d2r_owned` and NOT in
`d2r_foundLog` was filed under a store it is not in, and `DEST` rendered it "→ chronicle".

MEASURED on his newest ledger backup: of 360 routing rows carrying a `store`, 11 name a store whose
contents lack that name. One — Atma’s Scarab — was an apostrophe artefact of the AUDIT SCRIPT, not
a defect in his data. The other 10 are real, and 8 are exactly this branch:
    Lionheart · Enlightenment · Heart of the Oak · Myth · Death Mask · Black Cleft ·
    Crescent Moon (amulet) · Athena's Wrath (set piece)
⚠ ALL 10 ARE REGISTERED IN SOME STORE. Nothing is lost; the LABEL is wrong. That distinction is the
whole reason no repair here may ever remove a name. [[label-outlived-referent]]

⚠⚠ WHY THE FOLD IS COPIED FROM `_gFound` AND `_chMapHas` IS NOT USED — this is the part a future
simplification will get wrong. `_chMapHas` resolves through `_chNameKeys`, which yields only
{exact, lowercase, bare-of-" Rune"}. It does NOT fold the apostrophe. Using it here mislabels the
four curly-apostrophe names whenever his ledger key is straight. MEASURED against his real stores:
`Atma’s Scarab` is NOT a key in d2r_foundLog, but `Atma's Scarab` IS — so the folded branch answers
'foundLog' (right) and a `_chMapHas` branch answers 'owned' (wrong). v1779 paid for this lesson in
this same function: *"_gFound(curly)=false, _gFound(straight)=true"*.

⚠ HIS KEYS ARE UNTOUCHED, and that is a standing ruling, not a shortcut — v1779: *"The ledger is
NOT rewritten — his keys are his; the read folds instead"*; v2762 made the same call for art rather
than change roster bytes, because `unique_roster.json` and `set_roster.json` share one `sourceHash`
and rewriting it makes every machine's fleet mask undecodable until it republishes. No count moves
here; only the provenance word changes.

⚠ THE NODE TEST IS THE REAL ONE. The source checks below can only see shapes I thought of; only
executing the shipped branch proves what it answers.
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIBLE = io.open(os.path.join(REPO, "bible.html"), encoding="utf-8").read()


def _branch():
    """The shipped branch body, anchored at BOTH ends — never a fixed-size window.

    A `src[i:i+N]` read past the region reports ABSENT for something present, which has cost this
    repo four findings in one session. [[source-reading-guard]]
    """
    a = BIBLE.find("if (typeof _gFound === 'function' && _gFound(nm))")
    if a < 0:
        return None
    # ⚠ END ON THE BRANCH'S OWN CLOSING BRACE, not on the next statement. The first cut anchored
    # the end at `var found = _chLsGet(...)`, which sits AFTER the enclosing try's `} catch(e){}` —
    # so the slice carried a stray closer, and every node run died with an unbalanced wrapper
    # before it could answer anything. An over-reaching end anchor fails LOUDLY here; the same
    # mistake in a law that only counts matches fails SILENTLY. [[source-reading-guard]]
    ret = BIBLE.find("why: 'you already had this one' };", a)
    if ret < 0:
        return None
    b = BIBLE.find("}", ret + len("why: 'you already had this one' };"))
    return BIBLE[a:b + 1] if b > a else None


def _run_node(js):
    if not js:
        return None
    d = tempfile.mkdtemp(prefix="settled_")
    f = os.path.join(d, "t.js")
    io.open(f, "w", encoding="utf-8").write(js)
    try:
        r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
    except Exception:
        return None
    if r.returncode != 0:
        return {"__err": (r.stderr or "")[:400]}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return {"__err": "unparseable: %r" % r.stdout[:300]}


class TheSettledRowNamesTheStoreItIsIn(unittest.TestCase):

    def test_the_branch_is_still_findable(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertIsNotNone(_branch(),
                             "the _gFound branch of kaiChronicleSettledWhy moved or was renamed — "
                             "this law has no subject and is measuring nothing")

    def test_the_store_is_not_hardcoded_to_foundLog(self):
        b = _branch()
        self.assertNotIn("return { store: 'foundLog', why: 'you already had this one' };", b,
                         "the branch stamps 'foundLog' unconditionally again, so every name that "
                         "is only in d2r_owned is filed under a store it is not in")

    def test_it_does_not_use_the_helper_that_cannot_fold(self):
        b = _branch()
        self.assertNotIn("_chMapHas", b,
                         "_chMapHas resolves through _chNameKeys, which does not fold the "
                         "apostrophe — using it here mislabels the four curly names whenever his "
                         "ledger key is straight (measured: Atma’s Scarab)")

    # ── THE REAL ONE: execute the shipped branch ──────────────────────────────────────────────
    def _ask(self, nm, owned, foundlog):
        b = _branch()
        js = """
        var OWNED = new Set(%s), FL = %s;
        var nm = %s;
        function _chLsGet(k, d){ return k === 'd2r_foundLog' ? FL : d; }
        function _gFound(n){
          if (OWNED.has(n)) return true;
          for (var k of [n, n.replace(/\\u2019/g,"'"), n.replace(/'/g,'\\u2019')])
            if (FL[k] != null) return true;
          return false;
        }
        var window = { d2rResolveItem: null };
        function ask(){ %s
          return { store: null, why: 'not settled here' }; }
        console.log(JSON.stringify(ask()));
        """ % (json.dumps(sorted(owned)), json.dumps(foundlog), json.dumps(nm), b)
        return _run_node(js)

    def test_a_name_only_in_owned_is_labelled_owned(self):
        got = self._ask("Lionheart", {"Lionheart"}, {})
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass and nothing here is established")
        self.assertNotIn("__err", got, "the branch would not execute: %s" % got.get("__err"))
        self.assertEqual(got.get("store"), "owned",
                         "a name present only in d2r_owned is still filed as 'foundLog'")

    def test_a_name_in_foundlog_is_labelled_foundLog(self):
        got = self._ask("Shako", set(), {"Shako": 1})
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertEqual(got.get("store"), "foundLog",
                         "a genuine foundLog name lost its correct label")

    def test_a_curly_name_whose_ledger_key_is_STRAIGHT_is_still_foundLog(self):
        """THE REGRESSION THAT A `_chMapHas` REWRITE WOULD REINTRODUCE, on his real spelling."""
        got = self._ask(u"Atma’s Scarab", set(), {u"Atma's Scarab": 1})
        if got is None:
            self.skipTest("node unavailable — a skip is NOT a pass")
        self.assertEqual(got.get("store"), "foundLog",
                         "the curly name did not fold onto his straight ledger key, so an item he "
                         "found months ago is filed as merely 'owned' — v1779's defect, one layer "
                         "over")


RED_PROOF = [
    {
        "why": "hardcoding 'foundLog' again is the original defect: every owned-only name is filed "
               "under a store it is not in",
        "file": "bible.html",
        "find": "return { store: (_inFL ? 'foundLog' : 'owned'), why: 'you already had this one' };",
        "replace": "return { store: 'foundLog', why: 'you already had this one' };",
        "matches": 1,
    },
    {
        "why": "dropping the curly->straight fold reintroduces v1779's split on his real ledger key",
        "file": "bible.html",
        "find": "          if (!_inFL && _fl[String(nm).replace(/\\u2019/g, \"'\")] != null) _inFL = true;",
        "replace": "          if (false) _inFL = true;",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
