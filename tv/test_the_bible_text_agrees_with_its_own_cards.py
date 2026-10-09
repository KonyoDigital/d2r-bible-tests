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
        # REG-2105 (the v3627 eye) - the sweep was one spelling wide: "/p3 or higher REQUIRED" and a "/p5 mule trick" survived it
        hits = [m.start() for m in re.finditer(r"players 3\+|/p3\+|1:278|/p\s*3 or higher|p5 mules? trick", s)]
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
        # REG-2105 (the v3627 eye) - the same skip lived in the keys card's subtitle, chip and feeds line and in SPECIAL_DROPS
        for skip in ("cube all 3 \\u2192 red portal", "cube 3 \\u2192 red portal", "3 Terror + 3 Hate + 3 Destruction", "opens 3 red portals"):
            self.assertNotIn(skip, s, "a key line skips the mini-uber step again: %r" % skip)
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
        for rate in ("~8-9% (Hell only)", "~1:500-1500", "100% per kill"):
            self.assertEqual(got.get(rate), "per-kill rate", "a per-kill rate lost its label: %r -> %r" % (rate, got.get(rate)))
        self.assertNotIn("Per-kill figures above are the canonical community estimates", s,
                         "the footer calls every rate a community per-kill estimate again")
        # REG-2107 (the v3628 eye) - "100% per kill" is a guaranteed drop, not an estimate; and a key card's ~1:10 sat beside its
        # own sourced ~8% (the Countess at /players 1)
        self.assertIn("a 100% line is a guaranteed drop", s, "the footer calls the guaranteed organ drops estimates again")
        self.assertNotIn('rate: "~1:10 (Hell only)"', s, "a key card's rate disagrees with the sourced figure beside it again")

    def test_the_rune_card_lists_runewords_from_the_recipe_table(self):
        """REG-2104 (the v3626 second eye, swept) - RUNES[].rw was a hand-written runeword list and 91 of its 132 names did not
        hold the rune (Ber -> Call to Arms, Jah -> Infinity, Ohm -> Beast). The card now lists RUNEWORDS entries whose recipe
        holds the rune, and rw keeps only notes; a runeword NAME back in rw is the hand list returning."""
        s = _src()
        self.assertEqual(s.count('      <div style="font-size:13.5px;line-height:1.6">${_runeRunewordsHtml(r)}</div>'), 1,
                         "the rune card prints a hand-written list again instead of the recipe table's")
        i = s.find("const RUNEWORDS = [")
        names = {re.sub(r"\s*\(.*\)$", "", m.group(1)).lower()
                 for m in re.finditer(r'\{n:"([^"]+)", runes:"', s[i:s.find("\n];", i)])}
        ri = s.find("const RUNES = [")
        rows = re.findall(r'n:"([A-Z][a-z]+)",.*?rw:"([^"]*)"', s[ri:s.find("\n];", ri)])
        self.assertGreaterEqual(len(rows), 30, "premise: the rune table (%d rows)" % len(rows))
        named = [(n, p.strip()) for n, rw in rows for p in rw.split(",") if p.strip().lower() in names]
        self.assertEqual(named, [], "a rune's rw names a runeword again - the card's list comes from the recipe table: %r" % named)

    def test_the_rune_cards_cube_and_level_agree_with_the_cube_section(self):
        """REG-2108 (#231 eye on v43 988f0157) - RUNES[].up, the rune card's 'cube up' line, was a second copy of the cube table
        and every one of its 32 recipes was shifted (El '3 El + Chipped Amethyst', Lo '2 Lo + Perfect Amethyst'), while the page's
        own cube section - Arreat Summit's table, checked - had them right. And Lo / Sur / Ber / Jah wore 61 / 63 / 65 / 67, two
        levels high, so Jah tied Cham. Each card's recipe must equal its cube row; levels rise along the table, tied only where
        the game ties them (El/Eld, Tir/Nef, Eth/Ith)."""
        s = _src()
        rows = re.findall(r'<div class="cube-input">(\d)× ([A-Z][a-z]+)(?: \+ ([^<]+))?</div><div class="cube-arrow">→</div>'
                          r'<div class="cube-output">1× ([A-Z][a-z]+)</div>', s)
        cube = {r[1]: "%s %s%s → %s" % (r[0], r[1], (" + " + r[2]) if r[2] else "", r[3]) for r in rows}
        ri = s.find("const RUNES = [")
        table = re.findall(r'n:"([A-Z][a-z]+)",\s*clvl:(\d+),[^\n]*?up:"([^"]*)"', s[ri:s.find("\n];", ri)])
        self.assertGreaterEqual(len(table), 32, "premise: the rune table (%d rows)" % len(table))
        # REG-2119 (the v3630 second eye) - PRINT THE DENOMINATOR: every rune card with a recipe must have been COMPARED. The
        # first cut kept a rune only when `n in cube`, so a cube section the regex stopped reading made `off` empty and
        # the law green while every recipe drifted.
        unread = [n for n, _cl, _up in table if n not in cube]
        self.assertEqual(unread, [], "rune cards whose cube row was never read - the comparison ran on nothing: %r" % unread)
        off = [(n, up, cube.get(n)) for n, _cl, up in table if up != cube[n]]
        self.assertEqual(off, [], "a rune card's cube recipe disagrees with the page's own cube section: %r" % off)
        # REG-2119 - and the LEVELS are read on their own: Zod carries up:null, so the recipe pattern skipped it and the top
        # rune's level was never checked against Cham's
        levels = re.findall(r'n:"([A-Z][a-z]+)",\s*clvl:(\d+),', s[ri:s.find("\n];", ri)])
        self.assertEqual(len(levels), 33, "premise: all 33 runes carry a level (%d read)" % len(levels))
        lv = [(n, int(cl)) for n, cl in levels if n != "Hel"]
        ties = {("El", "Eld"), ("Tir", "Nef"), ("Eth", "Ith")}
        bad = [(a, b) for (a, x), (b, y) in zip(lv, lv[1:]) if y < x or (y == x and (a, b) not in ties)]
        self.assertEqual(bad, [], "rune level requirements do not rise along the table: %r" % bad)

    def test_the_most_wanted_act_cards_agree_with_their_bosses(self):
        """REG-2111 (#231 eye on v43 5361d57a, #313) - Act 1 promised the Countess "up to Lo" and starred Ber and Jah, which her
        own rune table never lists; Act 2 named Ancient Tunnels over a click that opens Duriel and said "every unique drops";
        Act 3 called Mephisto "high runes + top uniques" against his own TC78-capped plan; a runeword row stayed
        aria-expanded="false" while it opened; Grief's "Eth base = premium" cannot be a Phase Blade."""
        s = _src()
        ci = s.find("const COUNTESS_RUNES = [")
        countess = set(re.findall(r'n:"([A-Z][a-z]+)(?: #\d+)?"', s[ci:s.find("\n];", ci)]))
        ri = s.find("const RUNES = [")
        runes = set(re.findall(r'n:"([A-Z][a-z]+)",\s*clvl:', s[ri:s.find("\n];", ri)]))
        a1 = s.find('label:"Act 1",')
        self.assertGreater(a1, 0, "the Most Wanted Act 1 card is gone - re-point this law")
        wants = re.findall(r'\{n:"([^"]+)",drop:', s[a1:s.find("] },", a1)])
        stray = [w for w in wants if w in runes and w not in countess]
        self.assertEqual(stray, [], "Act 1 stars runes the Countess's own table never drops: %r" % stray)
        a3 = s.find('label:"Act 3",')
        # REG-2125 (the v3631 second eye) - a missing Act 3 card made the next check read an empty slice and pass
        self.assertGreater(a3, 0, "the Most Wanted Act 3 card is gone - re-point this law")
        self.assertNotIn("top uniques", s[a3:s.find("] },", a3)], "Mephisto is promised top uniques over his TC78 cap again")
        # REG-2125 - and EVERY act card's target names the boss its click opens (Act 2 once named Ancient Tunnels over a
        # click that opened Duriel). The boss's own name comes from BOSSES, never from this law.
        cards = re.findall(r'label:"(Act \d)",\s*target:"([^"]*)",\s*boss:"([a-z]+)"', s)
        self.assertGreaterEqual(len(cards), 5, "PRINT THE DENOMINATOR: only %d act cards read" % len(cards))
        off = []
        for act, target, boss in cards:
            b = re.search(r'\{"id":"%s","emoji":"[^"]*","name":"([^"]+)"' % boss, s)
            self.assertIsNotNone(b, "%s opens boss id %r, which BOSSES does not have" % (act, boss))
            head = re.sub(r"^The ", "", b.group(1))
            if head.lower() not in target.split("\u00b7")[0].lower():
                off.append("%s: target %r, click opens %s" % (act, target, b.group(1)))
        self.assertEqual(off, [], "an act card names one place and opens another boss: %r" % off)
        self.assertNotIn("Eth base = premium", s, "Grief's base advice names an ethereal Phase Blade again")
        self.assertIn('row.setAttribute("aria-expanded", _o ? "true" : "false");', s,
                      "a runeword row opens while its aria-expanded stays false")

    def test_every_key_mention_prints_its_own_cards_rate(self):
        """REG-2117 - REG-2107 gave each key card its sourced rate (Terror ~8-9%, Hate ~9-13%, Destruction ~10%) and the sweep
        stopped at the cards: the Uber Step 1 table, the Summoner card and the uber-path nodes still printed ~10% for Terror
        and Hate (5 sites). Every "~N%" printed after a key's name, up to the next key's name, must be that key's card rate."""
        s = _src()
        i = s.find("const SPECIAL_DROPS"); j = s.find("\n};", i)
        card = {m.group(1): m.group(2) for m in re.finditer(
            r'\{n: "(Key of (?:Terror|Hate|Destruction))"[^}]*?rate: "(~[0-9]+(?:-[0-9]+)?%)', s[i:j])}
        self.assertEqual(len(card), 3, "premise: the three key cards carry a sourced rate (%r)" % card)
        key, rate = re.compile(r"Key of (?:Terror|Hate|Destruction)"), re.compile(r"~\s?[0-9]+(?:[-\u2013][0-9]+)?\s?%")
        seen, bad = 0, []
        for ln, line in enumerate(s.split("\n"), 1):
            ms = list(key.finditer(line))
            for a, m in enumerate(ms):
                end = ms[a + 1].start() if a + 1 < len(ms) else len(line)
                for r in rate.finditer(line[m.end():min(end, m.end() + 260)]):
                    seen += 1
                    got = r.group(0).replace(" ", "").replace("\u2013", "-")
                    if got != card[m.group(0)]:
                        bad.append("line %d: %s prints %s, its card says %s" % (ln, m.group(0), got, card[m.group(0)]))
        self.assertGreaterEqual(seen, 12, "PRINT THE DENOMINATOR: only %d key rates were read - re-point this law" % seen)
        self.assertEqual(bad, [], "a key's rate disagrees with its own card:\n  " + "\n  ".join(bad))


    def test_the_colossal_jewel_note_says_what_each_jewel_carries(self):
        """REG-2120 (#309 (4), the #231 eye on v43; sourced 2026-10-09: maxroll + diablobytes) - the aggregate note said EACH of the
        six jewels carries +skill damage and -enemy element resist; the page's own Protector's Stone carries +Enhanced Damage and
        -enemy PHYSICAL resistance and no skill damage. Derived from the six jewels' own stats: one that lacks skill damage must be
        named in the note as the one without it, and no 'Each:' clause may promise skill damage."""
        s = _src()
        jewels = {m.group(1): m.group(2) for m in re.finditer(
            r'"((?:Defender|Protector|Guardian)\'s [A-Z][a-z]+)": \{"rarity":"unique","base":"Colossal Jewel"[^\n]*?"stats":\[([^\]]*)\]', s)}
        self.assertEqual(len(jewels), 6, "premise: the six Colossal Jewels carry their stats (%r)" % sorted(jewels))
        without = sorted(n for n, st in jewels.items() if "Skill Damage" not in st)
        i = s.find('{n: "Colossal Ancient Jewels", from:')
        self.assertGreater(i, 0, "the Colossal Jewels material row is gone - re-point this law")
        note = re.search(r'note: "([^"]*)"', s[i:s.find("\n", i)]).group(1)
        self.assertIsNone(re.search(r"Each:[^.;]*skill", note), "an 'Each:' clause promises skill damage to every jewel: %r" % note)
        for n in without:
            self.assertIn(n, note, "%s carries no skill damage and the note does not say which jewel is the exception" % n)
        self.assertIn("no skill damage", note)

    def test_no_text_gives_an_ancient_one_jewel(self):
        """REG-2120 (#309 (3)) - six jewels, two per Ancient, and the Ancient killed last decides the PAIR (the page's own
        COLOSSAL table lists two per Ancient). Four sentences said 'the jewel matching the Ancient killed last', as if one."""
        s = _src()
        pairs = re.findall(r"drop:'Colossal Ancient Jewels', jewels:\[([^\]]*)\]", s)
        self.assertEqual(len(pairs), 3, "premise: the three Ancients each list their jewels (%d)" % len(pairs))
        self.assertEqual([len(re.findall(r'"([^"]+)"', p)) for p in pairs], [2, 2, 2], "an Ancient no longer lists two jewels")
        singular = re.findall(r"(?:the jewel|the one) matching the Ancient", s)
        self.assertEqual(singular, [], "a sentence gives the last-killed Ancient ONE jewel again: %r" % singular)

    def test_black_cleft_takes_three_shards_wherever_a_recipe_is_told(self):
        """REG-2120 (#309 (5); maxroll sundered-charms + wikiwiki.jp agree) - every Renewed charm takes one Worldstone Shard
        except Black Cleft, which takes three (Southern + Deep + Northern). The category recipe said one for all, the shard blurb
        said each shard upgrades 'a specific' charm (three of them feed two), and Black Cleft's own note read 'Worldstone Shard
        (Northern)s'."""
        s = _src()
        i = s.find("  sunder: {"); j = s.find("  worldstoneShard: {", i); k = s.find("  cowAccess: {", j)
        self.assertTrue(0 < i < j < k, "the sunder / shard material entries moved - re-point this law")
        sunder, shard = s[i:j], s[j:k]
        recipe = re.search(r'\n    recipe: "([^"]*)"', sunder).group(1)
        self.assertIn("Black Cleft takes three", recipe, "the Sunder recipe tells one shard for every charm again: %r" % recipe)
        cleft = re.search(r'\{n: "Black Cleft"[^\n]*', sunder).group(0)
        self.assertIn("three Worldstone Shards (Southern + Deep + Northern)", cleft, "Black Cleft's own recipe lost its three shards")
        self.assertNotIn("Each shard upgrades a specific", shard, "the shard blurb gives every shard one charm again")

    def test_izual_is_not_next_door_to_the_river(self):
        """REG-2121 (#231 eye on v43 0136a656) - the River of Flame card said Izual 'guards the adjacent Plains of Despair'.
        Act 4 runs Outer Steppes, Plains of Despair, City of the Damned, River of Flame: the Plains are two zones back."""
        s = _src()
        i = s.find("Izual is NOT here")
        self.assertGreater(i, 0, "the River of Flame card's Izual line is gone - re-point this law")
        self.assertNotIn("adjacent Plains of Despair", s, "a card calls the Plains of Despair adjacent to the River again")
        self.assertIn("City of the Damned", s[i:s.index(".)", i)], "the Izual line no longer says what lies between")

    def test_every_super_unique_resolves_to_its_own_area(self):
        """REG-2124 (#231 eye on v43 8003b914) - suTzZone matched a substring of a zone's whole roster string, so The Smith
        (Act 1 Barracks) resolved to River of Flame through "the Hellforge smith" in Hephasto's note. Drives the SHIPPED
        suTzZone in node over the page's own TZ_ZONES and SUPER_UNIQUES: every super-unique that resolves must land on a zone
        whose name carries the last word of its own area ('Act 1 · Barracks' -> Barracks)."""
        import json as _json
        import subprocess as _sp
        from cb_node_harness import NODE
        if NODE is None:
            raise AssertionError("node is not on this machine - this gate does not skip")
        s = _src()
        def block(start, end):
            i = s.find(start)
            self.assertGreater(i, 0, "%r is gone - re-point this law" % start)
            return s[i:s.index(end, i) + len(end)]
        js = "%s\n%s\n%s\nconsole.log(JSON.stringify(SUPER_UNIQUES.map(function(su){ var m = suTzZone(su); "\
             "return [su.name, su.act, m ? m.z.name : null]; })));" % (
                 block("const TZ_ZONES = [", "\n];"), block("const SUPER_UNIQUES = [", "\n];"),
                 block("function suTzZone(su){", "\n}\n"))
        r = _sp.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        rows = _json.loads(r.stdout.strip().splitlines()[-1])
        resolved = [(n, a, z) for n, a, z in rows if z]
        self.assertGreaterEqual(len(resolved), 10, "PRINT THE DENOMINATOR: only %d super-uniques resolved" % len(resolved))
        bad = []
        for n, act, z in resolved:
            area = re.sub(r"\s*L\d+$", "", act.split("\u00b7")[-1].strip())
            if area.split()[-1].lower() not in z.lower():
                bad.append("%s (%s) -> %s" % (n, area, z))
        self.assertEqual(bad, [], "a super-unique resolves to a terror zone that is not its own area: %r" % bad)

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
    {"why": "REG-2104 - the rune card prints its hand-written runeword list again",
     "file": "bible.html",
     "find": "      <div style=\"font-size:13.5px;line-height:1.6\">${_runeRunewordsHtml(r)}</div>",
     "replace": "      <div style=\"font-size:13.5px;line-height:1.6\">${r.rw}</div>",
     "matches": 1},
    {"why": "REG-2105 - the special-drops recipe opens three red portals from 3+3+3 keys again",
     "file": "bible.html",
     "find": "recipe: \"1 Terror + 1 Hate + 1 Destruction in the cube (Hell Harrogath) → one random mini-uber portal; a full set per portal, three for all three\",",
     "replace": "recipe: \"3 Terror + 3 Hate + 3 Destruction in cube → opens 3 red portals to Uber bosses\",",
     "matches": 1},
    {"why": "REG-2105 - the special-drops blurb says keys need /p3 or higher again",
     "file": "bible.html",
     "find": "Hell only, at any /players.\",",
     "replace": "Hell only, /p3 or higher REQUIRED for drops.\",",
     "matches": 1},
    {"why": "REG-2105 - the keys card's subtitle skips the mini-uber step again",
     "file": "bible.html",
     "find": "cube 1 of each \\u2192 a mini-uber portal \\u2192 its organ; 3 organs \\u2192 Uber Tristram.",
     "replace": "cube all 3 \\u2192 red portal \\u2192 Pandemonium Run.",
     "matches": 1},
    {"why": "REG-2107 - the Key of Terror card's rate disagrees with the sourced ~8% beside it again",
     "file": "bible.html",
     "find": "rate: \"~8-9% (Hell only)\"",
     "replace": "rate: \"~1:10 (Hell only)\"",
     "matches": 1},
    {"why": "REG-2108 - a rune card's cube recipe drifts from the cube section again",
     "file": "bible.html",
     "find": "up:\"2 Lo + Flawless Topaz → Sur\"",
     "replace": "up:\"2 Lo + Perfect Amethyst → Sur\"",
     "matches": 1},
    {"why": "REG-2111 - the Countess act card stars Ber again",
     "file": "bible.html",
     "find": "    wants:[ {n:\"Lo\",drop:\"Lo\"}, {n:\"Ohm\",drop:\"Ohm\"}, {n:\"Stone of Jordan\",drop:\"The Stone of Jordan\"} ] },",
     "replace": "    wants:[ {n:\"Ber\",drop:\"Ber\"}, {n:\"Ohm\",drop:\"Ohm\"}, {n:\"Stone of Jordan\",drop:\"The Stone of Jordan\"} ] },",
     "matches": 1},
    {"why": "REG-2111 - a runeword row opens with aria-expanded stuck at false again",
     "file": "bible.html",
     "find": "  if (row){ var _o = row.classList.toggle(\"open\"); row.setAttribute(\"aria-expanded\", _o ? \"true\" : \"false\"); }\n",
     "replace": "  if (row) row.classList.toggle(\"open\");\n",
     "matches": 1},
    {"why": "REG-2108 - Jah's level ties Cham's again",
     "file": "bible.html",
     "find": "n:\"Jah\",  clvl:65,",
     "replace": "n:\"Jah\",  clvl:67,",
     "matches": 1},
    {"why": "REG-2117 - the Uber Step 1 table prints the Key of Terror at ~10% again, under its card's ~8-9%",
     "file": "bible.html",
     "find": "<td>~8-9% drop · Hell only",
     "replace": "<td>~10% drop · Hell only",
     "matches": 1},
    {"why": "REG-2119 - one cube row the law can no longer read (the v3630 eye: the comparison silently ran on fewer runes)",
     "file": "bible.html",
     "find": "<div class=\"cube-input\">2× Lo + Flawless Topaz</div><div class=\"cube-arrow\">→</div>",
     "replace": "<div class=\"cube-input\">2× Lo + Flawless Topaz</div> <div class=\"cube-arrow\">→</div>",
     "matches": 1},
    {"why": "REG-2119 - Zod's level falls under Cham's and the level check never sees the top rune",
     "file": "bible.html",
     "find": "n:\"Zod\",  clvl:69,",
     "replace": "n:\"Zod\",  clvl:65,",
     "matches": 1},
    {"why": "REG-2117 - the uber-path node prints the Key of Hate at ~10% again, under its card's ~9-13%",
     "file": "bible.html",
     "find": "'Hell Summoner · Arcane Sanctuary','~9-13% · Hell only'",
     "replace": "'Hell Summoner · Arcane Sanctuary','~10% · Hell only'",
     "matches": 1},
    {"why": "REG-2120 - the Colossal note promises skill damage to every jewel again",
     "file": "bible.html",
     "find": "Each: a 1% chance to cast a spell when struck, +3-5% experience",
     "replace": "Each: a 1% chance to cast a spell when struck, +5-10% to that skill damage, +3-5% experience",
     "matches": 1},
    {"why": "REG-2120 - a sentence gives the last-killed Ancient one jewel again",
     "file": "bible.html",
     "find": "You keep one of the two jewels matching the Ancient killed <strong>last</strong>.</div>",
     "replace": "You keep the jewel matching the Ancient killed <strong>last</strong>.</div>",
     "matches": 1},
    {"why": "REG-2120 - the Sunder recipe tells one shard for Black Cleft too",
     "file": "bible.html",
     "find": "; Black Cleft takes three (Southern + Deep + Northern). Source: Maxroll.",
     "replace": ". Source: Maxroll.",
     "matches": 1},
    {"why": "REG-2121 - the River card calls the Plains of Despair adjacent again",
     "file": "bible.html",
     "find": "he guards the Plains of Despair, two zones back: Plains, City of the Damned, then the River.)",
     "replace": "he guards the adjacent Plains of Despair.)",
     "matches": 1},
    {"why": "REG-2124 - suTzZone matches a substring of the whole roster again, so The Smith lands on River of Flame",
     "file": "bible.html",
     "find": "    if (names.some(function(n){ return word.test(n); })) return {z: TZ_ZONES[i], zi: i};\n",
     "replace": "    if (String(TZ_ZONES[i].unique || '').toLowerCase().includes(needle)) return {z: TZ_ZONES[i], zi: i};\n",
     "matches": 1},
    {"why": "REG-2125 - the Act 2 card names Ancient Tunnels again over a click that opens Duriel",
     "file": "bible.html",
     "find": "label:\"Act 2\",        target:\"Duriel · Tal Rasha's Chamber\",",
     "replace": "label:\"Act 2\",        target:\"Ancient Tunnels · Lost City\",",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
