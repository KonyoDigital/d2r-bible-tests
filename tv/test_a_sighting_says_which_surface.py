# -*- coding: utf-8 -*-
"""TWO LOOKS AT DIFFERENT SURFACES ARE NOT A CONTRADICTION, AND TWELVE OF HIS WERE ABOUT TO BE.

Konyo's ruling, 2026-09-07: *"chron_evidence — widen it, one confluence store"*.

`chron_evidence.json` holds ~8,300 sightings and every one is chronicle-scene BY CONSTRUCTION —
twice over: `chronicle_kind()` (chronicle_retro.py:857) refuses any page whose read scene is not
"chronicle", and the live-lane converter (:1469) skips non-chronicle rows outright. Meanwhile the
deep reader produces name-carrying sightings across SIX scenes (gameplay 200 · chronicle 154 ·
stash 71 · inventory 39 · loot 6 · town 2) that no corroboration store ever receives.

⚠⚠ THE COLLISION, MEASURED BEFORE THIS GUARD EXISTED. Twelve names sit in `notFound` AND were seen
by the deep reader on a PANEL surface: Goldwrap, Magefist, Wraithstep, Radament's Sphere,
Credendum, Dark Adherent, Rite of Passage, Bramble Mitts, Death Mask, plus the bases Amulet, Grand
Charm, Jewel. `counter_ledger.resolve_contested` joins the two sides BY NAME ONLY with pure
timestamp arithmetic and no surface awareness — so the first widened sweep would have manufactured
twelve contradictions out of twelve pairs that were never in conflict.

And worse than a miscount: the `not-found` verdict says in its own words that *"the found reading
is the suspect one"*. A real stash sighting would have been blamed by a menu page that simply had
not registered the item yet — which is the situation his own "the board and the game do not add up"
panel already reports as normal. [[feedback-contradiction-is-the-finding]]

=== ⚠ IT IS A NO-OP ON THE DAY IT SHIPS, AND THAT IS THE DESIGN ===
`cross-scene` fires ONLY when both sides know their scene and disagree. Absence of `scene` is
UNKNOWN, never a default — the 8,300 rows already on disk carry none and cannot be given one
retroactively. `_stamp_sighting_locs` states the convention this follows: *"a loc is only written
when it is known... None is NEVER stamped. A stored 'unknown' would be indistinguishable from a
stored fact the moment the reel is pruned."* So nothing on his disk is re-graded by a fact nobody
recorded. [[unknown-stays-unknown]]

=== AND IT IS NAMED `scene`, NOT `surface`, DELIBERATELY ===
Two other things already answer to "surface" and NEITHER is this: `loc`/`_sighting_loc` collapses
inventory, chronicle, gameplay, town, loot and transition ALL to None (only "stash" is ever
positive), and `witnesses()`'s `surface_of` callback is wired to that same narrow vocabulary.
`scene` is the deep row's own word for the same six values. reel_segments.py:105: *"two
vocabularies meeting SILENTLY is how a branch stops being reachable without anyone noticing."*
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import counter_ledger as CL  # noqa: E402

RETRO = io.open(os.path.join(HERE, "chronicle_retro.py"), encoding="utf-8").read()


def _code_only(src):
    """Docstrings AND comments stripped — five laws this session were fooled by their own prose."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(node, "body", None) or []
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                b[0].value.value = ""
    out = ast.unparse(tree) if hasattr(ast, "unparse") else src
    out = re.sub(r"(?m)#[^\n]*", "", out)
    # ⚠ ast.unparse NORMALISES QUOTE STYLE: `"scene": "chronicle"` comes back as
    # `'scene': 'chronicle'`, so a literal match on the source spelling finds ZERO and the law
    # reports a defect that does not exist. Normalise both sides rather than guessing which
    # quoting survived. [[feedback-suspect-the-instrument]]
    return out.replace("'", '"')


RETRO_CODE = _code_only(RETRO)


def _s(scene, frame):
    r = {"reel": "r", "frame": frame}
    if scene:
        r["scene"] = scene
    return r


class ASightingSaysWhichSurface(unittest.TestCase):

    # ── every mint site declares it ───────────────────────────────────────────────────────────
    def test_all_THREE_mint_sites_stamp_the_scene(self):
        """⚠ Three, not one. Stamping the found sighting and leaving the notFound RECEIPT bare
        would make every pair look half-known — and the receipt is the OTHER side of the very
        comparison this exists to guard."""
        n = RETRO_CODE.count('"scene": "chronicle"')
        self.assertEqual(3, n,
                         "expected the found sighting, the notFoundSeen receipt and the "
                         "completeSets sighting each to declare their scene; found %d in code" % n)

    def test_it_is_a_CONSTANT_here_and_that_is_correct(self):
        """`normalize_page`'s return carries eighteen keys and `scene` is not among them
        (chronicle_hunt.py:176). This pipeline is chronicle-only by construction, so the constant
        is the measured truth — not a shortcut. A `resp.get("scene")` here would silently write
        None on every row."""
        self.assertNotIn('resp.get("scene")', RETRO_CODE,   # quotes normalised by _code_only
                         "a mint site reads scene off resp, which never carries it — every row "
                         "would be stamped None")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_different_surfaces_do_NOT_contradict(self):
        v = CL.resolve_contested([_s("stash", "f_1788000000000")],
                                 [_s("chronicle", "f_1788999999999")])
        self.assertEqual("cross-scene", v["verdict"],
                         "a stash sighting and a chronicle absence were treated as a "
                         "contradiction — and `not-found` calls the found reading 'the suspect "
                         "one', so his real stash sighting would be blamed by a menu page")
        self.assertEqual("stash", v.get("foundScene"))
        self.assertEqual("chronicle", v.get("notFoundScene"))

    def test_the_SAME_surface_still_contradicts(self):
        """The other direction. Two Chronicle readings that disagree are a genuine contradiction
        and must stay one — this guard must not become a blanket excuse."""
        v = CL.resolve_contested([_s("chronicle", "f_1788000000000")],
                                 [_s("chronicle", "f_1788999999999")])
        self.assertEqual("not-found", v["verdict"], "a real same-surface contradiction was excused")

    # ── ⚠ NO-OP ON EVERYTHING ALREADY ON DISK ─────────────────────────────────────────────────
    def test_an_UNKNOWN_scene_changes_nothing(self):
        """His 8,300 existing sightings carry no scene. If absence triggered the guard, every one
        of them would silently stop contradicting — a mass re-grade on a fact nobody recorded."""
        for a, b in ((None, None), ("chronicle", None), (None, "chronicle")):
            v = CL.resolve_contested([_s(a, "f_1788000000000")], [_s(b, "f_1788999999999")])
            self.assertEqual("not-found", v["verdict"],
                             "an unknown scene (%r vs %r) changed the verdict — this must be a "
                             "no-op until scenes are actually recorded" % (a, b))

    def test_a_MIXED_side_is_unknown_not_a_pick(self):
        """If a name was read on two surfaces there is no single scene for that side. Choosing one
        would invent the fact this guard exists to respect."""
        v = CL.resolve_contested(
            [_s("stash", "f_1788000000000"), _s("inventory", "f_1788000000001")],
            [_s("chronicle", "f_1788999999999")])
        self.assertNotEqual("cross-scene", v["verdict"],
                            "a side with TWO scenes was given one, so a mixed reading silently "
                            "became a single-surface claim")

    # ── the allowlist must know it ────────────────────────────────────────────────────────────
    def test_the_verdict_is_in_the_KNOWN_allowlist(self):
        """⚠ test_counter_ledger's KNOWN set guards against invented verdicts, and its own comment
        says an allowlist "must be derived from that module, or stated with the reason each member
        is there". A new verdict absent from it fails the moment his data produces one."""
        # ⚠ THE **SET**, NOT THE FILE. This first asserted the string appeared anywhere in
        # test_counter_ledger.py — and my own exercise-test in that same file contains it, so
        # deleting it from the allowlist still passed. Sixth law this session fooled by text it
        # put there itself. Parse the literal and test MEMBERSHIP. [[source-reading-guard]]
        import ast as _ast
        t = io.open(os.path.join(HERE, "test_counter_ledger.py"), encoding="utf-8").read()
        found = None
        for node in _ast.walk(_ast.parse(t)):
            if isinstance(node, _ast.Assign) and any(
                    getattr(x, "id", None) == "KNOWN" for x in node.targets):
                try:
                    found = {e.value for e in node.value.elts
                             if isinstance(e, _ast.Constant)}
                except Exception:
                    found = None
                break
        self.assertIsNotNone(found, "the KNOWN allowlist literal could not be parsed — fix this "
                                    "guard before trusting a green from it")
        self.assertIn("cross-scene", found,
                      "the counter_ledger allowlist does not contain cross-scene, so it fires the "
                      "day the first deep row lands. It knows: %s" % sorted(found))

    def test_it_still_parses(self):
        ast.parse(RETRO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
