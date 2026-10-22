# -*- coding: utf-8 -*-
"""#62 #68 #69 (REG-2504..REG-2506) - NO CODEX NUMBER CONTRADICTS ITS OWN TABLE.

His ruling of 2026-10-22: an RotW number with no source shows the VANILLA D2R figure, labelled 'vanilla D2R ·
RotW unconfirmed', and contradicting copies are removed; a figure no source gives stays UNKNOWN, never a pick.

What the #231 eye found, swept here rather than pinned one item at a time:
  * Seven chance-to-cast props read "Level 0" (the raw table value; the game computes the level from the item
    level). The page's own hover card (ITEM_TIP, diablo2.io RotW) and the Arreat Summit (vanilla) print the same
    levels: Rising Sun 13-19 Meteor, Snowclash 7-19 Blizzard, Stormrider 13-20 Charged Bolt, Lightsabre 14-20 Chain
    Lightning, Stormspire 20 Charged Bolt, Hellslayer 16-20 Fire Ball, Boneslayer 12-20 Holy Bolt. Every codex
    chance-to-cast level must equal its hover card's.
  * A codex note is a second copy of its own props (and a third in ITEM_INFO / ITEM_INFO_EXTRA). Notes said
    "+30% fire absorb" over a flat or per-level absorb, "4-pc Tal Rasha = +5 sorc skills" over a set table of +3
    full / +1 at two pieces / +2 on Adjudication, and 45 skill-count clauses no table holds. An absorb or a
    skill-count claim in a note must be its own table's figure, in both copies, and the copies must agree.
  * Essences carried three rates (~4% a kill, ~1:25, ~10-15% / ~12%). One source now: silospen's RotW 3.0 drop
    calculator, a non-quest Hell kill at /players 1 - Andariel 13%, Duriel 11%, Mephisto / Diablo / Baal 7% - on
    every surface.
  * The jewel is "Colossal Jewel(s)" in the game; "Colossal Ancient Jewels" stays only as the KEY (his material
    stash, openDrop, data-arttip, the art map, CAT_ART / CAT_ROUTE, ENDGAME_RELICS, UBER_BOSSES.drop).
  * The Summoner's Hell mlvl read 83 on both cards with no source: 80 is the vanilla figure (diablowiki, d2emu,
    silospen's boss entry), labelled. Pindleskin read "TC84/TC85" beside his boss card's TC87: d2emu - TC87,
    never an item above qlvl 86. Bone Ash claimed a Cathedral terror ceiling no zone in the file holds. Uber Duriel
    was "Cold immune" beside a cold resist of 75 (d2emu, Hell: 75 everywhere but physical 50, no immunity).
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable
enable()

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
DOT = " · "

ELEM = {"fire": "Fire", "cold": "Cold", "lightning": "Lightning", "light": "Lightning", "magic": "Magic"}
ABS_NUM = re.compile(r"(\+?\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)(%?) (?:(fire|cold|lightning|light|magic) (?:absorb|abs)\b"
                     r"|absorb (fire|cold|lightning|light|magic)\b)( per clvl)?", re.I)
ABS_BARE = re.compile(r"\b((?:fire|cold|lightning|light|magic)(?:/(?:fire|cold|lightning|light|magic))*) absorb\b"
                      r"|\babsorb ((?:fire|cold|lightning|light|magic)(?:/(?:fire|cold|lightning|light|magic))*)", re.I)
PROP_ABS_A = re.compile(r"\+?(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)(%?) (Fire|Cold|Lightning|Magic) Absorb( \(Based on Character Level\))?")
PROP_ABS_B = re.compile(r"(Fire|Cold|Lightning|Magic) Absorb \+?(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)(%?)")
SKILL = re.compile(r"\+(\d+)(?:-(\d+))? (?:to )?((?:[A-Za-z]+ ){0,2})skills?\b", re.I)
SCOPE = {"all": "All Skills", "ama": "Amazon", "amazon": "Amazon", "sin": "Assassin", "assassin": "Assassin",
         "barb": "Barbarian", "barbarian": "Barbarian", "druid": "Druid", "nec": "Necromancer", "necro": "Necromancer",
         "necromancer": "Necromancer", "pala": "Paladin", "paladin": "Paladin", "sorc": "Sorc", "sorceress": "Sorc",
         "fire": "Fire", "cold": "Cold", "lightning": "Lightning", "light": "Lightning", "poison": "Poison",
         "summon": "Summoning", "summoning": "Summoning", "curse": "Curse", "shadow": "Shadow", "elemental": "Elemental",
         "javelin": "Javelin", "bow": "Bow", "combat": "Combat", "warcry": "Warcries", "shape": "Shape Shifting"}
CTC = re.compile(r"(\d+)% Chance [Tt]o [Cc]ast [Ll]evel \[?(\d+(?:-\d+)?)\]? ([A-Za-z' ]+?) "
                 r"(When Struck|On Striking|On Attack|When You Die|When You Level-Up)", re.I)


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _json_line(src, prefix):
    line = next(ln for ln in src.split("\n") if ln.startswith(prefix))
    body = line[len(prefix):]
    return json.loads(body[:body.rfind("};") + 1])


def _bosses(src):
    line = next(ln for ln in src.split("\n") if ln.startswith("const BOSSES = "))
    body = line[len("const BOSSES = "):]
    return json.loads(body[:body.rindex("];") + 1])


def _info(src):
    """ITEM_INFO and ITEM_INFO_EXTRA, every name -> [its strings] (a name can sit in both tables)."""
    out = {}
    for table in ("ITEM_INFO", "ITEM_INFO_EXTRA"):
        a = src.index("const %s = {" % table)
        body = src[a:src.index("\n};", a)]
        for k, v in re.findall(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$', body, re.M):
            out.setdefault(json.loads('"%s"' % k), []).append(json.loads('"%s"' % v))
    return out


def _table(c):
    lines = list(c.get("props") or []) + list(c.get("setBonuses") or [])
    for s in (c.get("setPartials") or []):
        lines += [p.strip() for p in re.split(r"\s*[·:]\s*", s) if p.strip()]
    for m in (c.get("setMembers") or []):
        lines += list(m.get("affixes") or [])
    return lines


def _absorbs(c):
    out = []
    for p in _table(c):
        m = PROP_ABS_A.search(p)
        if m:
            out.append((m.group(3), m.group(1), bool(m.group(2)), bool(m.group(4))))
            continue
        m = PROP_ABS_B.search(p)
        if m:
            out.append((m.group(1), m.group(2), bool(m.group(3)), False))
    return out


def absorb_problems(note, c):
    bad, have, spans = [], _absorbs(c), []
    for m in ABS_NUM.finditer(note):
        spans.append(m.span())
        want = (ELEM[(m.group(3) or m.group(4)).lower()], m.group(1).lstrip("+"), bool(m.group(2)), bool(m.group(5)))
        if want not in have:
            bad.append(m.group(0))
    for m in ABS_BARE.finditer(note):
        if any(a <= m.start() < b for a, b in spans):
            continue
        for e in (m.group(1) or m.group(2)).lower().split("/"):
            if not any(h[0] == ELEM[e] for h in have):
                bad.append(m.group(0))
                break
    return bad


def skill_problems(note, c):
    bad, lines = [], [l for l in _table(c) if "kill" in l]
    for m in SKILL.finditer(note):
        fig = m.group(1) + ("-" + m.group(2) if m.group(2) else "")
        scopes = [SCOPE[w] for w in m.group(3).lower().split() if w in SCOPE]
        if not scopes:
            continue
        ok = False
        for l in lines:
            mm = re.match(r"\s*\+" + re.escape(fig) + r" (?:to )?(.*)", l)
            if mm and any(s.lower() in mm.group(1).lower() for s in scopes):
                ok = True
                break
        if not ok:
            bad.append(m.group(0))
    return bad


def _uncommented(src):
    """The file with every HTML comment, block comment and whole-line // comment blanked, same length."""
    t = re.sub(r"<!--[\s\S]*?-->", lambda m: " " * len(m.group(0)), src)
    t = re.sub(r"/\*[\s\S]*?\*/", lambda m: " " * len(m.group(0)), t)
    return re.sub(r"(?m)^[ \t]*//[^\n]*", lambda m: " " * len(m.group(0)), t)


# where "Colossal Ancient Jewels" is a KEY, by what stands right before it
KEY_BEFORE = re.compile(r"(?:data-arttip=\"|data-art-logo=\"|openDrop\(\\?'|materialDetailHtml\('|\{n: \"|^\s*\"|drop:'|drop:\""
                        r"|colossalJewel:'|'Annihilus','|MAT_SHOWN = \{ ')$")


class NoCodexNumberContradictsItsOwnTable(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = _src()
        cls.codex = _json_line(cls.src, "const ITEM_CODEX = ")
        cls.tip = _json_line(cls.src, "const ITEM_TIP = ")
        cls.info = _info(cls.src)

    def test_no_proc_is_level_0_and_every_level_is_its_hover_cards(self):
        level0 = [(n, p) for n, c in self.codex.items() for p in (c.get("props") or []) if re.search(r"\bLevel 0\b", p)]
        self.assertEqual(level0, [], "a chance-to-cast still reads Level 0")
        compared, bad = 0, []
        norm = lambda s: s.lower().replace("fireball", "fire ball").strip()
        for name, c in self.codex.items():
            t = self.tip.get(name)
            if not t:
                continue
            tl = {(m.group(1), norm(m.group(3)), m.group(4).lower()): m.group(2) for m in CTC.finditer(" | ".join(t["l"]))}
            for p in c.get("props") or []:
                m = CTC.search(p)
                if not m:
                    continue
                key = (m.group(1), norm(m.group(3)), m.group(4).lower())
                if key in tl:
                    compared += 1
                    if tl[key] != m.group(2):
                        bad.append("%s: codex %r, hover card level %s" % (name, p, tl[key]))
        self.assertGreaterEqual(compared, 60, "PRINT THE DENOMINATOR: only %d chance-to-cast lines compared" % compared)
        self.assertEqual(bad, [], "a codex chance-to-cast level is not its hover card's")

    def test_every_absorb_and_skill_count_claim_is_its_own_table(self):
        checked, bad = 0, []
        for name, c in self.codex.items():
            notes = [("codex", str(c.get("note") or ""))] + [("info", v) for v in self.info.get(name, [])]
            for where, note in notes:
                if not note:
                    continue
                checked += len(ABS_NUM.findall(note)) + len(ABS_BARE.findall(note)) + len(SKILL.findall(note))
                for b in absorb_problems(note, c) + skill_problems(note, c):
                    bad.append("%s (%s): %r" % (name, where, b))
        self.assertGreaterEqual(checked, 60, "PRINT THE DENOMINATOR: only %d absorb / skill claims read" % checked)
        self.assertEqual(bad, [], "a note claims an absorb or a skill count its own table does not hold")

    def test_the_three_named_notes_say_their_tables(self):
        s = self.src
        for stale in ("+30% fire absorb", "+12-25 fire res", "+5 sorc skills", "+65% FCR · +120-200 mana",
                      "4-pc Tal Rasha"):
            self.assertNotIn(stale, s, "a contradicted note is back: %r" % stale)
        nums = lambda t: set(re.findall(r"\d+(?:\.\d+)?", t))
        for name in ("The Rising Sun", "Steel Shade", "Tal Rasha set (any piece)"):
            c = self.codex[name]
            table = nums(" | ".join(_table(c)))
            for note in [c["note"]] + self.info.get(name, []):
                stray = sorted(nums(note) - table)
                self.assertEqual(stray, [], "%s: the note carries numbers its table does not: %r in %r" % (name, stray, note))

    def test_each_note_and_its_duplicate_agree(self):
        drift = []
        for name, c in self.codex.items():
            if not c.get("note") or not (c.get("props") or c.get("setBonuses")):
                continue
            for v in self.info.get(name, []):
                if v.strip().lower() != str(c["note"]).strip().lower():
                    drift.append("%s: codex %r / info %r" % (name, c["note"], v))
        self.assertEqual(drift, [], "a codex note and its ITEM_INFO copy say different things")

    def test_essences_state_one_sourced_rate(self):
        s = self.src
        a = s.index("  essence: {")
        rows = dict(re.findall(r'\{n: "(Essence of \w+)", from: \[[^\]]*\], rate: "([^"]*)"', s[a:s.index("  token: {", a)]))
        self.assertEqual(rows, {"Essence of Suffering": "~13% Andariel · ~11% Duriel (Hell)",
                                "Essence of Hatred": "~7% (Hell)", "Essence of Terror": "~7% (Hell)",
                                "Essence of Destruction": "~7% (Hell)"})
        h = s.index("const ESSENCES_HUB = [")
        hub = dict(re.findall(r"open:'(Essence of \w+)',\s*from:'[^']*',\s*rate:'([^']*)'", s[h:s.index("];", h)]))
        self.assertEqual(hub, {"Essence of Suffering": "~13% / ~11%", "Essence of Hatred": "~7%",
                               "Essence of Terror": "~7%", "Essence of Destruction": "~7%"},
                         "the hub tiles and the material rows give an essence two rates")
        card = s[s.index("function essencesDetailHtml(embedded){"):s.index("window.essencesDetailHtml = essencesDetailHtml;")]
        self.assertIn("${e.rate}", card, "the hub tiles print a rate of their own again")
        self.assertIn("silospen's RotW 3.0", card, "the essence card no longer names its source")
        for stale in ("~4% per kill", "~1:25", "~10-15%", "12% per essence", "\\u00b7 ~12% \\u00b7"):
            self.assertNotIn(stale, s, "a second essence rate is back: %r" % stale)

    def test_no_shown_text_says_colossal_ancient_jewels(self):
        t = _uncommented(self.src)
        shown = []
        for m in re.finditer(r"Colossal Ancient Jewel", t):
            line_start = t.rfind("\n", 0, m.start()) + 1
            before = t[max(line_start, m.start() - 60):m.start()]
            after = t[m.end():m.end() + 2]
            if not after.startswith("s") or not KEY_BEFORE.search(before):
                shown.append(t[max(0, m.start() - 50):m.end() + 20].replace("\n", " "))
        self.assertEqual(shown, [], "shown text names the jewel the way the game does not")
        self.assertIn("const MAT_SHOWN = { 'Colossal Ancient Jewels': 'Colossal Jewels' };", self.src)
        self.assertIn('{n: "Colossal Ancient Jewels", from:', self.src, "the material key moved, so his stash count is lost")
        self.assertIn('"Colossal Ancient Jewels": "art/colossal_jewel1_graphic.png"', self.src, "the art map lost the key")
        self.assertIn("<h2 class=\"gic-name\">${_matShown(item.n)}", self.src)
        self.assertIn("label: \"Colossal Jewels\",", self.src)

    def test_the_super_unique_and_uber_cards_agree_with_their_sources(self):
        s = self.src
        summ = [b for b in _bosses(s) if b["id"] == "summoner"][0]
        hell = [d for d in summ["diffs"] if d["label"] == "HELL"][0]
        su = re.search(r'\{emoji:"[^"]*",name:"The Summoner",[^\n]*?mlvl:(\d+),[^\n]*?drops:"([^"]*)"\}', s)
        self.assertEqual((hell["mlvl"], int(su.group(1))), (80, 80), "the Summoner has two Hell levels, or not the vanilla 80")
        self.assertIn("vanilla D2R · RotW unconfirmed", hell["tc"])
        self.assertIn("vanilla D2R · RotW unconfirmed", su.group(2))
        pin = re.search(r'name:"Pindleskin",[^\n]*?drops:"([^"]*)"', s).group(1)
        self.assertIn("TC87", pin)
        self.assertIn("qlvl 86", pin)
        self.assertNotRegex(pin, r"TC8[45]", "Pindleskin's card names a lower ceiling than his boss card")
        pind = [b for b in _bosses(s) if b["id"] == "pindle"][0]
        self.assertIn("TC87", pind["why"])
        bone = re.search(r'name:"Bone Ash",[^\n]*?drops:"([^"]*)"', s).group(1)
        self.assertNotRegex(bone, r"TC\d", "Bone Ash claims a terror ceiling no zone in the file holds")
        u = s[s.index("{ id:'uber-duriel'"):s.index("{ id:'uber-mephisto'")]
        self.assertIn("immune:'none'", u)
        self.assertNotIn("Cold immune", u)
        self.assertNotIn("Cold-immune", u)
        self.assertIn("(d2emu, Hell", u)
        self.assertIn("type:'Act 2 Demon Superunique", u)
        self.assertNotIn("Uber Duriel's uber ID card\"><strong>Uber Duriel</strong> →</span></td><td>The Lord of Pain's uber form · cold-immune", s)


RED_PROOF = [
    {"why": "#62 - The Rising Sun's Meteor reads Level 0 again",
     "file": "bible.html",
     "find": "2% Chance to Cast Level 13-19 Meteor When Struck",
     "replace": "2% Chance to Cast Level 0 Meteor When Struck",
     "matches": 1},
    {"why": "#62 - The Rising Sun's note claims +30% fire absorb over a per-level absorb again",
     "file": "bible.html",
     "find": "+0.75 fire absorb per clvl · +2 fire skills · fire-sorc amulet",
     "replace": "+30% fire absorb · +2 fire skills · fire-sorc amulet",
     "matches": 2},
    {"why": "#62 - Tal Rasha's note gives the set +5 sorc skills again",
     "file": "bible.html",
     "find": "full set +3 sorc skills · 2-piece bonus",
     "replace": "full set +5 sorc skills · 2-piece bonus",
     "matches": 2},
    {"why": "#62 - the ITEM_INFO copy of Steel Shade's note drifts from the codex note again",
     "file": "bible.html",
     "find": "\"Steel Shade\":\"+5-11 fire absorb",
     "replace": "\"Steel Shade\":\"+30% fire absorb",
     "matches": 1},
    {"why": "#69 - the essence rows go back to ~1:25",
     "file": "bible.html",
     "find": "rate: \"~7% (Hell)\",",
     "replace": "rate: \"~1:25\",",
     "matches": 3},
    {"why": "#69 - the essence hub tiles print their own ~12% again",
     "file": "bible.html",
     "find": "from ${e.from} \\u00b7 ${e.rate} \\u00b7 Hell",
     "replace": "from ${e.from} \\u00b7 ~12% \\u00b7 Hell",
     "matches": 1},
    {"why": "#69 - a link shows Colossal Ancient Jewels again",
     "file": "bible.html",
     "find": "onclick=\"window.openDrop('Colossal Ancient Jewels')\">Colossal Jewels →</span>",
     "replace": "onclick=\"window.openDrop('Colossal Ancient Jewels')\">Colossal Ancient Jewels →</span>",
     "matches": 1},
    {"why": "#69 - the display map loses the jewel, so the material card shows its key",
     "file": "bible.html",
     "find": "const MAT_SHOWN = { 'Colossal Ancient Jewels': 'Colossal Jewels' };",
     "replace": "const MAT_SHOWN = {};",
     "matches": 1},
    {"why": "#68 - the Summoner's super-unique card goes back to Hell mlvl 83",
     "file": "bible.html",
     "find": "name:\"The Summoner\",act:\"Act 2 · Arcane Sanctuary\",mlvl:80,",
     "replace": "name:\"The Summoner\",act:\"Act 2 · Arcane Sanctuary\",mlvl:83,",
     "matches": 1},
    {"why": "#68 - Pindleskin's card names the TC84/TC85 pool again beside his boss card's TC87",
     "file": "bible.html",
     "find": "mlvl 86 reaches TC87 every kill",
     "replace": "mlvl 86 reaches the TC84/TC85 unique pool every kill",
     "matches": 1},
    {"why": "#68 - Bone Ash claims a Cathedral terror ceiling again",
     "file": "bible.html",
     "find": "so no terror ceiling is claimed for him.",
     "replace": "Cathedral terrors to mlvl 96 / TC85.",
     "matches": 1},
    {"why": "#68 - Uber Duriel is called Cold immune again beside a cold resist of 75",
     "file": "bible.html",
     "find": "block:'50%', immune:'none',",
     "replace": "block:'50%', immune:'Cold',",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
