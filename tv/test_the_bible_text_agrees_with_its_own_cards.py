# -*- coding: utf-8 -*-
"""REG-2089 - THE BIBLE'S PROSE AGREES WITH ITS OWN CARDS: A TAGLINE'S RESIST FIGURE AND A "NO BOSS CARD" CLAIM.

The #231 code seat, on May's 4275b03a and a78bae20, re-measured at HEAD 2026-10-08:
  * Veil of Steel's tagline read "+60 all res · +140% defense" while its own codex card reads All Resistances +50,
    +60% Enhanced Defense, +140 Defense - the two numbers swapped between the stats. Swept across every tagline that names
    "all res": Veil was the only one off.
  * The Summoner block said "the only Key dropper without its own boss card" - under a link that opens The Summoner's boss
    detail, and with BOSSES[0] being the Summoner.
Both laws are sweeps over the file, so the next tagline or "no card" sentence that disagrees with the data goes red.

REG-2090 - the #231 code seat on May's 0e22e7d2 and 46f0f060, re-measured at the v3630 tip:
  * the P# slider tip and the PLAYERS=8 MYTH card said "up to ~2.3x" for Cows & The Pit while the /p8 table printed x2.41
    and playerMult(cows, hell, 8) is 2.412;
  * the /p8 table's Heavy droppers row printed q 0.28-0.35 beside x1.39-1.52 - the x came from PLAYER_Q (0.27941,
    0.34545), so a reader who multiplied the printed q got x1.53. The q now prints to the precision that round-trips;
  * Blood Raven was "the Den-of-Evil quest archer" in three places (her quest is Sisters' Burial Grounds), and
    Andariel's quest line said "Den-of-Evil + Sisters quest" (hers is Sisters to the Slaughter).
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


def _player_q(s):
    i = s.find("const PLAYER_Q = ")
    if i < 0:
        raise AssertionError("PLAYER_Q is gone - re-point this law")
    return json.loads(s[i + len("const PLAYER_Q = "):s.find(";\n", i)])


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


    def test_the_players_prose_says_the_multiplier_the_formula_gives(self):
        s = _src()
        q = _player_q(s)["cows"]["hell"]
        m = (1 - q ** 5) / (1 - q)                       # playerMult at /players 8: k = 1 + floor(8/2)
        said = re.findall(r"up to (?:<strong>)?~(\d+\.\d+)×(?:</strong>)? for Cows &(?:amp;)? The Pit", s)
        self.assertGreaterEqual(len(said), 2, "premise: the slider tip and the myth card both say it (%d found)" % len(said))
        for x in said:
            self.assertEqual(float(x), round(m, 1),
                             "a sentence says up to ~%s× for Cows & The Pit; playerMult at /p8 is %.3f" % (x, m))

    def test_the_p8_table_rows_round_trip_from_their_printed_q(self):
        s = _src()
        pq = _player_q(s)
        i = s.find("<thead><tr><th>tier</th><th>bosses</th><th>NoDrop q</th><th>×@ /p8</th></tr></thead>")
        self.assertGreater(i, 0, "the /p8 multiplier table is gone - re-point this law")
        body = s[i:s.find("</tbody>", i)]
        rows = re.findall(r"<tr><td class=\"item-name\">[^<]*</td><td>([^<]+)</td><td>([^<]+)</td><td>(.*?)</td></tr>", body)
        self.assertEqual(len(rows), 4, "premise: the four tier rows (%d found)" % len(rows))
        f = lambda v: 1.0 if v == 0 else (1 - v ** 5) / (1 - v)
        bad = []
        for bosses, qs, xs in rows:
            ids = [k for b in bosses.split("·") for k in pq if b.strip().lower().startswith(k)]
            self.assertEqual(len(ids), len(bosses.split("·")), "premise: every boss in %r has a PLAYER_Q row" % bosses)
            real = sorted(pq[k]["hell"] for k in ids)
            printed_q = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", qs)]
            printed_x = [float(v) for v in re.findall(r"\d+\.\d+", xs[xs.find("×"):])]   # "×1.39–1.52" carries one ×
            want_x = sorted({round(f(v), 2) for v in (real[0], real[-1])})
            if [round(v, 2) for v in printed_x] != want_x:
                bad.append("%s: prints ×%s, PLAYER_Q gives ×%s" % (bosses, printed_x, want_x))
            # the eye's check: a reader who multiplies the PRINTED q must land on the printed ×
            from_q = sorted({round(f(v), 2) for v in printed_q})
            if from_q != want_x:
                bad.append("%s: q %s printed, which gives ×%s, beside ×%s" % (bosses, qs, from_q, want_x))
        self.assertEqual(bad, [], "a /p8 table row disagrees with its own q: %r" % bad)

    def test_no_card_gives_a_boss_another_quest(self):
        s = _src()
        self.assertGreaterEqual(s.count("Blood Raven"), 3, "premise: Blood Raven's cards are on the page")
        wrong = re.findall(r"Blood Raven[^\"]{0,120}?Den[- ]of[- ]Evil|Den[- ]of[- ]Evil quest archer", s)
        self.assertEqual(wrong, [], "Blood Raven is given the Den of Evil quest - hers is Sisters' Burial Grounds: %r" % wrong)
        i = s.find("  andariel: {\n    run:")
        self.assertGreater(i, 0, "andariel's tip block is gone - re-point this law")
        q = re.search(r'\n    quest: "([^"]*)"', s[i:s.index("\n  },\n", i)]).group(1)   # andariel's own block
        self.assertIn("Sisters to the Slaughter", q, "Andariel's quest line no longer names her own quest: %r" % q)
        self.assertNotRegex(q, r"Den[- ]of[- ]Evil", "Andariel's quest line names another quest: %r" % q)
    def test_every_rune_use_names_a_runeword_that_holds_the_rune(self):
        """REG-2099 (#231 eye on v43 4decd6cf) - the rune grids' 'used for' column named runewords that do not contain the
        rune: Ohm 'Beast, HotO' (twice), Gul 'Wrath, Bramble', Ist 'Insight', Um 'Smoke, Wealth', Pul 'Spirit, Lionheart',
        Shael 'Spirit', Sur 'Infinity x2' - 13 claims, checked against the file's own RUNEWORDS recipes."""
        s = _src()
        i = s.find("const RUNEWORDS = [")
        self.assertGreater(i, 0, "RUNEWORDS is gone - re-point this law")
        rw = [(re.sub(r"\s*\(.*\)$", "", m.group(1)).lower(), [r.strip() for r in m.group(2).split("+")])
              for m in re.finditer(r'\{n:"([^"]+)", runes:"([^"]+)"', s[i:s.find("\n];", i)])]
        names = {n for n, _ in rw}
        abbrev = {"hoto": "heart of the oak", "cta": "call to arms", "coh": "chains of honor", "botd": "breath of the dying"}

        def norm(u):
            u = re.sub(r"\s*×\s*\d+\s*$", "", u.strip())
            u = re.sub(r"\s+class$", "", u)
            u = re.sub(r"\s+RW\b.*$", "", u)
            return abbrev.get(u.lower(), u.lower())
        checked, bad = 0, []
        for m in re.finditer(r'n:\s*["\']([A-Z][a-z]+) #(\d+)["\'][^}]*?use:\s*["\']([^"\']*)["\']', s):
            rune = m.group(1)
            for part in [p for p in m.group(3).split(",") if p.strip()]:
                nm = norm(part)
                if nm not in names:
                    continue
                checked += 1
                if not any(rune in rs for n, rs in rw if n == nm):
                    bad.append("%s: '%s'" % (rune, part.strip()))
        self.assertGreaterEqual(checked, 25, "premise: the sweep reaches the rune grids (%d checked)" % checked)
        self.assertEqual(bad, [], "a rune's 'used for' names a runeword whose recipe does not hold that rune: %r" % bad)

    def test_no_key_needs_a_players_setting_its_sources_do_not_name(self):
        """REG-2100 (#231 eye on v43 46f0f060, #306) - eleven places said the Pandemonium keys need '/players 3+' ('drops
        require /players 3+', '~1:278 (/p3)', 'Hell /p3+'), under a note citing d2runewizard - which gives the Countess ~8% at
        /players 1 rising to ~9%, and diablowiki the Summoner 8.6% at /p1-2 to 12.8% at /p7-8. Hell only, any /players.
        The one sentence left quoting the old claim is its retraction."""
        s = _src()
        hits = [m.start() for m in re.finditer(r"players 3\+|/p3\+|1:278", s)]
        stray = [s[max(0, h - 60):h + 30] for h in hits if "REG-2100 removed" not in s[max(0, h - 120):h + 10]]
        self.assertEqual(stray, [], "a key is said to need /players 3+ again (or ~1:278): %r" % stray)
        self.assertIn("Keys are <strong>Hell only</strong>, at any /players", s, "premise: the keys card says Hell only")

    def test_the_uber_lead_walks_the_steps_its_own_card_lists(self):
        """REG-2101 (#231 eye on v43 19cdf410) - the Uber Tristram lead said 'Cube the 3 Pandemonium Keys -> red portal ->
        kill all three ubers', skipping the mini-uber portals and the organ cube its own Step 2 and Step 3 describe, and gave
        the torch '+3 to a random class's skill tab' (the torch's +3 is to one class's skills, as ITEM_INFO says)."""
        s = _src()
        self.assertIn("Step 2 — Cube 1 of each key → a random mini-uber portal", s, "premise: the card's own Step 2")
        self.assertIn("Step 3 — Cube 3 organs → Uber Tristram portal", s, "premise: the card's own Step 3")
        self.assertNotIn("Cube the 3 Pandemonium Keys → red portal", s, "the lead skips the organ cube its own steps list")
        self.assertIn("→ cube the 3 organs → Uber Tristram →", s, "the lead no longer walks the organ step")
        self.assertNotIn("skill tab", s[s.find("Hellfire Torch →"):s.find("Click it for the full material card.")],
                         "the torch's +3 is narrowed to one skill tab again")

    def test_a_rate_in_words_is_not_labelled_per_kill(self):
        """REG-2103 (#231 eye on v43 9f39968e) - the material card printed every special-drop rate under 'per-kill rate' and
        footnoted all of them as community per-kill estimates; 'crafted - 1 per full essence set', '100% per recipe' and the
        Colossal Jewel's '1 per character (pinnacle reward)' are how an item comes, not a chance per kill. Drives the SHIPPED
        two-line classifier, cut from materialDetailHtml, over every item rate in SPECIAL_DROPS."""
        import json as _json
        import subprocess as _sp
        from cb_node_harness import NODE
        if NODE is None:
            raise AssertionError("node is not on this machine - this gate does not skip")
        s = _src()
        a = s.find("  const _rateTxt = String(item.rate || '');\n")
        self.assertGreater(a, 0, "the card no longer derives its rate label - re-point this law")
        cut = s[a:s.index("\n", s.index("  const _rateLbl = ", a)) + 1]
        i = s.find("const SPECIAL_DROPS"); j = s.find("\n};", i)
        rates = sorted(set(re.findall(r'rate:\s*"([^"]*)"', s[i:j])))
        self.assertGreaterEqual(len(rates), 10, "premise: the special drops carry their rates (%d)" % len(rates))
        js = "var out = {}; %s.forEach(function(r){ var item = {rate: r};\n%s out[r] = _rateLbl; });\nconsole.log(JSON.stringify(out));" % (
            _json.dumps(rates), cut)
        r = _sp.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[-400:])
        got = _json.loads(r.stdout.strip().splitlines()[-1])
        for rate in ("crafted — 1 per full essence set", "100% per recipe", "1 per character (pinnacle reward)", "common"):
            self.assertEqual(got.get(rate), "how it comes", "a rate in words is labelled %r: %r" % (got.get(rate), rate))
        for rate in ("~1:10 (Hell only)", "~1:500-1500", "100% per kill"):
            self.assertEqual(got.get(rate), "per-kill rate", "a per-kill rate lost its label: %r -> %r" % (rate, got.get(rate)))
        self.assertNotIn("Per-kill figures above are the canonical community estimates", s,
                         "the footer calls every rate a community per-kill estimate again")


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
    {"why": "REG-2090 - the slider tip says ~2.3x for Cows & The Pit again",
     "file": "bible.html",
     "find": "up to ~2.4× for Cows & The Pit",
     "replace": "up to ~2.3× for Cows & The Pit",
     "matches": 1},
    {"why": "REG-2090 - the Heavy droppers row prints a q that does not give its own x",
     "file": "bible.html",
     "find": "<td>0.2794–0.3455</td>",
     "replace": "<td>0.28–0.35</td>",
     "matches": 1},
    {"why": "REG-2090 - Blood Raven is the Den of Evil quest archer again",
     "file": "bible.html",
     "find": "\"The Sisters' Burial Grounds quest archer. Her quest",
     "replace": "\"The Den-of-Evil quest archer. Her quest",
     "matches": 1},
    {"why": "REG-2090 - Andariel's quest line names the Den of Evil again",
     "file": "bible.html",
     "find": "quest: \"Sisters to the Slaughter still open →",
     "replace": "quest: \"Den-of-Evil + Sisters quest still active →",
     "matches": 1},
    {"why": "REG-2099 - Ohm is 'used for' Beast and HotO again, neither of which holds it",
     "file": "bible.html",
     "find": "{n:'Ohm #27', hell:'1:13,754', use:'CtA, Faith, Doom'}",
     "replace": "{n:'Ohm #27', hell:'1:13,754', use:'Beast, HotO'}",
     "matches": 1},
    {"why": "REG-2100 - the keys card says they need /players 3+ to roll again",
     "file": "bible.html",
     "find": "Keys are <strong>Hell only</strong>, at any /players - the chance rises a little at higher /players.",
     "replace": "Keys are <strong>Hell only</strong>, at any /players - the chance rises a little at higher /players. They require /players 3+ to roll.",
     "matches": 1},
    {"why": "REG-2101 - the Uber Tristram lead sends the three keys straight to the trio again, skipping the organ cube",
     "file": "bible.html",
     "find": "Cube 1 of each Pandemonium key → a mini-uber portal (each mini-uber drops one organ) → cube the 3 organs → Uber Tristram → kill all three ubers in one room.",
     "replace": "Cube the 3 Pandemonium Keys → red portal → kill all three ubers in one room.",
     "matches": 1},
    {"why": "REG-2103 - every special-drop rate is labelled per-kill again, '1 per character' included",
     "file": "bible.html",
     "find": "  const _rateLbl = (/(^|[^\\w])1:\\d|\\d\\s*%/.test(_rateTxt) && !/per (recipe|character|full|tristram visit)/i.test(_rateTxt)) ? 'per-kill rate' : 'how it comes';\n",
     "replace": "  const _rateLbl = 'per-kill rate';\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
