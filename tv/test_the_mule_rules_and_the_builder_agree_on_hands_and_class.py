# -*- coding: utf-8 -*-
"""#41 rank 15 (2026-09-29) — THE MULE WINDOW'S RULES AND THE BUILDER'S DATABASE AGREE ON HANDS AND CLASS FOR EVERY
BASE, AND THE DOCTOR WATCHES THE MULE'S BLOCKS UNATTENDED.

The heart audit (#256, ranked 26 gaps) found the mule window's slot, hands and class rules (the MULE_BASE_SLOT /
MULE_NAMED_BASE / MULE_BASE_RULES blocks tv/mule_slot_map.py writes into bible.html) checked by NOTHING unattended:
console_doctor.py had 0 references to mule_slot_map, the only caller of its check() was a gate that skips without an
install, and no test read both CB_DB and MULE_BASE_RULES. After a game patch they would drift silently while 'builder
item data' went red on its sibling block.

WHAT THIS LAW DRIVES (the real code, never a grep of it):
  · THE TWO GENERATORS AGREE, with no install: for EVERY base in the builder's CB_DB block (tv/char_builder_db.py: b[14]
    hands 2 / 12 / 1, ty[t][2] the class lock) the mule's MULE_BASE_RULES block (tv/mule_slot_map.py, read through its
    own embedded()) says the same hands and the same class - measured 2026-09-29: 692 bases, 0 mismatches, every rule
    name present in CB_DB. The denominator is printed and must stay whole: a rule name absent from CB_DB would make the
    compare a sample, so that is red too.
    ⚠ WHAT THIS IS: one install read through two generators - a transform bug in either shows. It is NOT a second
    witness to what the game wears where; the corroborator's registry says so (NO_JOINT_YET).
  · THE DOCTOR ROW 'mule slot rules' (console_doctor._check_the_mule_slot_rules_match_the_install) with
    mule_slot_map.check stubbed: 0 is OK, 1 is MISSING carrying the generator's own sentence and the action, 77 (no
    install) is UNKNOWN - never OK - and a check that raises is UNKNOWN; it is in CHECKS, PERIODIC (it pulls from the
    install, like its siblings), WATCHES, and explained in corroborate.NO_JOINT_YET.
RED_PROOF below: every sabotage turns this law red for its own reason.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import console_doctor as CD  # noqa: E402
import corroborate as C  # noqa: E402
import mule_slot_map as MS  # noqa: E402
import test_the_character_builder_is_their_builder as CB  # noqa: E402  the CB_DB block, cut by the builder's own law

ROW = "mule slot rules"
HANDS = {12: "12", 2: "2"}


def compare():
    """-> {compared, mismatches: [(what, name, code, cbdb, rules)], absent: [rule names not in CB_DB]}"""
    slots, nb, ru = MS.embedded()
    d = CB._db()
    B, TY, CLS = d["b"], d["ty"], d["cls"]
    names = set(b[0] for b in B.values())
    h2, h12 = set(ru["hands"].get("2") or []), set(ru["hands"].get("12") or [])
    cls_of = {}
    for cname, ns in (ru.get("class") or {}).items():
        for n in ns:
            cls_of[n] = cname
    absent = sorted(n for n in (h2 | h12 | set(cls_of)) if n not in names)
    bad, n = [], 0
    for code, b in B.items():
        name, t = b[0], b[1]
        ci = (TY.get(t) or [None, None, -1])[2]
        cname = CLS[ci]["n"] if isinstance(ci, int) and ci >= 0 else None
        want_h = "12" if name in h12 else ("2" if name in h2 else "1")
        got_h = HANDS.get(b[14], "1")
        if b[21] == "w" and want_h != got_h:
            bad.append(("hands", name, code, got_h, want_h))
        if cls_of.get(name) != cname:
            bad.append(("class", name, code, cname, cls_of.get(name)))
        n += 1
    return {"compared": n, "mismatches": bad, "absent": absent, "rules": (len(h2), len(h12), len(cls_of))}


class TheTwoGeneratorsAgree(unittest.TestCase):

    def test_every_base_says_the_same_hands_and_class_in_both_blocks(self):
        got = compare()
        self.assertGreaterEqual(got["compared"], 600, "PRINT THE DENOMINATOR: only %d bases compared" % got["compared"])
        self.assertGreater(got["rules"][0], 50, "the rules block names %d two-handed bases - the block is not what the install wrote" % got["rules"][0])
        self.assertGreater(got["rules"][1], 5, "the rules block names %d one-or-two-handed bases" % got["rules"][1])
        self.assertGreater(got["rules"][2], 50, "the rules block class-locks %d bases" % got["rules"][2])
        self.assertEqual(got["absent"], [], "rule names the builder's database does not carry - the compare would be a "
                                            "sample: %s" % got["absent"][:8])
        self.assertEqual(got["mismatches"], [],
                         "%d of %d bases disagree between CB_DB and MULE_BASE_RULES (what, name, code, builder, mule): %s"
                         % (len(got["mismatches"]), got["compared"], got["mismatches"][:8]))


class TheDoctorRow(unittest.TestCase):

    def _with(self, answer):
        real = MS.check
        MS.check = answer
        try:
            return CD._check_the_mule_slot_rules_match_the_install()
        finally:
            MS.check = real

    def test_the_three_states_and_a_raise(self):
        st, why = self._with(lambda: (0, "the doll-slot map matches the install (helm 41)"))
        self.assertEqual(st, CD.OK, why)
        self.assertIn("matches the install", why)
        st, why = self._with(lambda: (1, "the install disagrees with the block in bible.html: hands: the block says {} - run --write"))
        self.assertEqual(st, CD.MISSING, why)
        self.assertIn("run --write", why)
        self.assertIn("last patch's", why, "a stale block must say what he is looking at: %s" % why)
        st, why = self._with(lambda: (MS.SKIP, "cannot re-derive here (no install), so whether the block matches the install is UNKNOWN"))
        self.assertEqual(st, CD.UNKNOWN, "no install read %s - never OK: %s" % (st, why))
        self.assertIn("UNKNOWN", why)

        def boom():
            raise RuntimeError("casc gone")
        st, why = self._with(boom)
        self.assertEqual(st, CD.UNKNOWN, why)
        self.assertIn("raised", why)

    def test_the_row_is_registered_periodic_declared_and_explained(self):
        names = [n for n, _fn in CD.CHECKS]
        self.assertIn(ROW, names, "the doctor never asks the row")
        self.assertIs(dict(CD.CHECKS)[ROW], CD._check_the_mule_slot_rules_match_the_install)
        self.assertIn(ROW, CD.PERIODIC, "the row pulls from the install every tick - its siblings are PERIODIC")
        self.assertIn(ROW, CD.WATCHES, "the row is not declared in WATCHES")
        self.assertIn(ROW, C.NO_JOINT_YET, "no registry line says why the row has no corroborator")
        self.assertIn("one install", C.NO_JOINT_YET[ROW])
        cov = C.coverage()
        self.assertTrue(cov.get("ok"), cov)
        self.assertIn(ROW, cov["uncovered"])
        self.assertNotIn(ROW, cov["unexplained"])


RED_PROOF = [
    {
        "why": "#41 rank 15 - a base leaves the mule's one-or-two-handed list while the builder still says 12 (Balrog Blade)",
        "file": "bible.html",
        "find": '    "hands": {"12": "Balrog Blade|',
        "replace": '    "hands": {"12": "',
        "matches": 1,
    },
    {
        "why": "#41 rank 15 - the mule block's reader drops every class lock (the gate reads through embedded())",
        "file": "mule_slot_map.py",
        "find": '    ru = dict((k, dict((v, [x for x in ns.split("|") if x]) for v, ns in (rd.get(k) or {}).items())) for k in RULE_KEYS)\n',
        "replace": '    ru = dict((k, dict((v, [x for x in ns.split("|") if x]) for v, ns in ((rd.get(k) if k != "class" else None) or {}).items())) for k in RULE_KEYS)\n',
        "matches": 1,
    },
    {
        "why": "#41 rank 15 - no install reads as OK",
        "file": "console_doctor.py",
        "find": "    if code == getattr(MS, \"SKIP\", 77):\n        return UNKNOWN, say\n    if code != 0:\n        return MISSING, say + \" - the mule picker's slots, hands and class locks are last patch's\"\n",
        "replace": "    if code == getattr(MS, \"SKIP\", 77):\n        return OK, say\n    if code != 0:\n        return MISSING, say + \" - the mule picker's slots, hands and class locks are last patch's\"\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 15 - the doctor never asks the row (dropped from CHECKS)",
        "file": "console_doctor.py",
        "find": "    (\"mule slot rules\", _check_the_mule_slot_rules_match_the_install),\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 15 - the row leaves PERIODIC (an install pull on every eagle tick)",
        "file": "console_doctor.py",
        "find": "            \"mule slot rules\",         # #41 rank 15 — its sibling: 4 tables + itemtypes.txt from the same install\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#41 rank 15 - the corroborator's registry no longer says why the row has no joint",
        "file": "corroborate.py",
        "find": "    'mule slot rules': 'the row re-derives the MULE_BASE_* blocks from the install through ONE generator '\n",
        "replace": "    'mule slot rules ': 'the row re-derives the MULE_BASE_* blocks from the install through ONE generator '\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
