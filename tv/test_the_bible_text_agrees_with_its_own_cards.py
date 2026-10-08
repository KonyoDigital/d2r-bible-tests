# -*- coding: utf-8 -*-
"""REG-2089 - THE BIBLE'S PROSE AGREES WITH ITS OWN CARDS: A TAGLINE'S RESIST FIGURE AND A "NO BOSS CARD" CLAIM.

The #231 code seat, on May's 4275b03a and a78bae20, re-measured at HEAD 2026-10-08:
  * Veil of Steel's tagline read "+60 all res · +140% defense" while its own codex card reads All Resistances +50,
    +60% Enhanced Defense, +140 Defense - the two numbers swapped between the stats. Swept across every tagline that names
    "all res": Veil was the only one off.
  * The Summoner block said "the only Key dropper without its own boss card" - under a link that opens The Summoner's boss
    detail, and with BOSSES[0] being the Summoner.
Both laws are sweeps over the file, so the next tagline or "no card" sentence that disagrees with the data goes red.
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

PAGE = os.path.join(os.path.dirname(HERE), "bible.html")


def _src():
    with io.open(PAGE, encoding="utf-8") as f:
        return f.read()


def _codex(s):
    i = s.find("const ITEM_CODEX = ")
    if i < 0:
        raise AssertionError("ITEM_CODEX is gone - re-point this law")
    return json.loads(s[i + len("const ITEM_CODEX = "):s.find("};\n", i) + 1])


class TheBibleTextAgreesWithItsOwnCards(unittest.TestCase):

    def test_every_all_res_tagline_matches_its_codex(self):
        s = _src()
        codex = _codex(s)
        checked, bad = 0, []
        for m in re.finditer(r'"([^"]{2,60})":"([^"]*?\+(\d+)%? all res[^"]*)"', s):
            name, n = m.group(1), int(m.group(3))
            c = codex.get(name)
            if not c:
                continue
            cr = re.search(r"All Resistances \+(\d+)(?:-(\d+))?", " | ".join(c.get("props") or []))
            if not cr:
                continue
            checked += 1
            lo, hi = int(cr.group(1)), int(cr.group(2) or cr.group(1))
            if not (lo <= n <= hi):
                bad.append("%s: tagline +%d all res, codex %s" % (name, n, cr.group(0)))
        self.assertGreaterEqual(checked, 5, "premise: the sweep reaches the all-res taglines (%d checked)" % checked)
        self.assertEqual(bad, [], "a tagline's resist figure disagrees with its own codex card: %r" % bad)

    def test_every_fcr_tagline_matches_its_codex(self):
        """Swept with the resist law: Suicide Branch +40 (codex 50), Ondal's Wisdom +30 (45), Que-Hegan's Wisdom +30 (20) and
        The Oculus +20 (30) - every one the codex's number was the game's."""
        s = _src()
        codex = _codex(s)
        checked, bad = 0, []
        for m in re.finditer(r'"([^"]{2,60})":"([^"]*?\+(\d+)% FCR[^"]*)"', s):
            name, n = m.group(1), int(m.group(3))
            c = codex.get(name)
            if not c:
                continue
            cr = re.search(r"\+(\d+)(?:-(\d+))?% Faster Cast Rate", " | ".join(c.get("props") or []))
            if not cr:
                continue
            checked += 1
            if not (int(cr.group(1)) <= n <= int(cr.group(2) or cr.group(1))):
                bad.append("%s: tagline +%d%% FCR, codex %s" % (name, n, cr.group(0)))
        self.assertGreaterEqual(checked, 5, "premise: the sweep reaches the FCR taglines (%d checked)" % checked)
        self.assertEqual(bad, [], "a tagline's FCR disagrees with its own codex card: %r" % bad)

    def test_every_codex_note_matches_its_own_props(self):
        """The same two figures inside a codex entry's own `note` - Veil of Steel's note carried the swapped numbers after
        its tagline was fixed, because the note is a second copy of the sentence."""
        codex = _codex(_src())
        bad = []
        for name, c in codex.items():
            note, props = str(c.get("note") or ""), " | ".join(c.get("props") or [])
            for pat, prop in ((r"\+(\d+)%? all res\b", r"All Resistances \+(\d+)(?:-(\d+))?"),
                              (r"\+(\d+)% FCR", r"\+(\d+)(?:-(\d+))?% Faster Cast Rate")):
                n, cr = re.search(pat, note), re.search(prop, props)
                if n and cr and not (int(cr.group(1)) <= int(n.group(1)) <= int(cr.group(2) or cr.group(1))):
                    bad.append("%s: note %s, props %s" % (name, n.group(0), cr.group(0)))
        self.assertEqual(bad, [], "a codex note disagrees with its own props: %r" % bad)

    def test_no_text_says_a_boss_has_no_card_when_it_has_one(self):
        s = _src()
        i = s.find("const BOSSES = ")
        ids = set(re.findall(r'"id":"([a-z0-9_-]+)"', s[i:s.find("];\n", i)]))
        self.assertIn("summoner", ids, "premise: the Summoner is a boss card")
        self.assertEqual(s.count("without its own boss card"), 0,
                         "a sentence says a boss has no card of its own, and BOSSES carries one")


RED_PROOF = [
    {"why": "REG-2089 - Veil of Steel's tagline swaps its resist and defense figures again",
     "file": "bible.html",
     "find": '"Veil of Steel":"+50 all res · +60% ED · +140 defense',
     "replace": '"Veil of Steel":"+60 all res · +140% defense',
     "matches": 1},
    {"why": "REG-2089 - the Summoner is said to have no boss card again",
     "file": "bible.html",
     "find": "Horazon's incarnation · drops the Key of Hate (Hell)</div>",
     "replace": "Horazon's incarnation · the only Key dropper without its own boss card</div>",
     "matches": 1},
    {"why": "REG-2089 - The Oculus's tagline FCR disagrees with its codex again",
     "file": "bible.html",
     "find": "+3 sorc skills · +30% FCR · MF +50% · the all-round sorc orb",
     "replace": "+3 sorc skills · +20% FCR · MF +50% · the all-round sorc orb",
     "matches": 2},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
