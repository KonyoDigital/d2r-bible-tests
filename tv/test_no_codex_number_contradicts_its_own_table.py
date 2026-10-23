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
  * THE FIX ROUND (the adversarial review): the skill reader read a claim only when it ended in the word "skills"
    after at most two letter-only words, so "+1-2 cold sorc" (Frostburn, no skill line), "+1 fire sorc" (Bane Ash:
    +5 Fire Bolt, +2 Warmth), "+1-3 fire/light skills" (Eschuta's Temper: +1-3 Sorceress), "+2 paladin auras"
    (Seraph's Hymn: +2 All Skills, +1 Masteries) and "+1 nec auras" (Homunculus) all passed green. And the sweep
    stopped at absorb and skill counts: 136 of 312 notes still carried a number their own table does not hold
    (Crow Caw "40% IAS · +25 DEX · open wounds 50%" over 15 / 15 / 35; Atma's Wail "+8-10% LL" with no leech;
    Gheed's Fortune with its gold and MF figures swapped). Every note with a figure was rewritten from its own
    table, clause by clause, or the clause removed (his ruling: a contradicting copy is removed). Read here three
    ways, over every copy - the codex note, its ITEM_INFO / ITEM_INFO_EXTRA duplicates, and the ITEM_INFO note the
    runtime uniques (_NEWUNI) show:
      - every NUMBER a note prints is one its own table prints (a rune reads the rune table, RUNES); a note with no
        table prints no number;
      - a STAT a note names with a figure (IAS, FCR, FHR, FRW, MF, gold, LL, ML, CB, deadly strike, open wounds, the
        four attributes, the resists, ED / def, AR, life, mana, block, DR, thorns, pierce, mana and life regen)
        carries that table line's figure - so a swap whose numbers both exist still goes red;
      - a SKILL count, '+N[-M] <class or tree words> skills | sorc | auras | ...' with the slash forms, is the figure
        of a table line that names that class or tree.
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
# '+N[-M] <class or tree words> skills | sorc | auras | ...', the slash forms ('fire/light skills') included
SKILL = re.compile(r"\+(\d+)(?:-(\d+))?\s(?:to\s)?((?:[A-Za-z]+(?:/[A-Za-z]+)*\s){0,4})"
                   r"(skills?|sorc|sorceress|nec|necro|necromancer|pala|paladin|ama|amazon|sin|assassin|barb|barbarian|"
                   r"druid|auras?|curses?|masteries|warcries)\b", re.I)
CLASS = {"sorc": "sorc", "sorceress": "sorc", "nec": "necro", "necro": "necro", "necromancer": "necro",
         "pala": "paladin", "paladin": "paladin", "ama": "amazon", "amazon": "amazon", "zon": "amazon", "sin": "assassin",
         "assassin": "assassin", "barb": "barbarian", "barbarian": "barbarian", "druid": "druid"}
TREE = {"fire": "fire", "cold": "cold", "light": "lightning", "lightning": "lightning", "poison": "poison",
        "bone": "bone", "curse": "curses", "curses": "curses", "summon": "summoning", "summoning": "summoning",
        "shape": "shape shifting", "elemental": "elemental", "combat": "combat", "masteries": "masteries",
        "warcries": "warcries", "warcry": "warcries", "javelin": "javelin", "bow": "bow", "passive": "passive",
        "shadow": "shadow", "martial": "martial", "traps": "traps", "trap": "traps", "aura": "auras", "auras": "auras",
        "offensive": "offensive auras", "defensive": "defensive auras"}
NUM = re.compile(r"\d+(?:\.\d+)?")
FIG = r"([+-]?\d+(?:\.\d+)?(?:\s?-\s?\d+(?:\.\d+)?)?)(\s?%)?"
# a stat a note names (its words) -> what its table line says (None: decided by the item, see _stat_lines)
STATS = [
    (r"IAS|attack speed", r"Increased Attack Speed"),
    (r"FCR|cast rate", r"Faster Cast Rate"),
    (r"FHR|hit recovery", r"Faster Hit Recovery"),
    (r"FRW|run/walk|run walk", r"Faster Run/Walk"),
    (r"FBR|block rate", r"Faster Block Rate"),
    (r"MF|magic find", r"Better Chance of Getting Magic Items"),
    (r"ELG|EG|extra gold|gold find|GF|to gold|gold", r"Extra Gold"),
    (r"LL|life leech|life steal|life stolen", r"Life Stolen"),
    (r"ML|mana leech|mana steal|mana stolen", r"Mana Stolen"),
    (r"CB|crushing blow", r"Crushing Blow"),
    (r"DS|deadly strike", r"Deadly Strike"),
    (r"OW|open wounds", r"Open Wounds"),
    (r"STR|strength", r"to Strength"),
    (r"DEX|dexterity", r"to Dexterity"),
    (r"VIT|vitality", r"to Vitality"),
    (r"ENE|ENG|energy", r"to Energy"),
    (r"all res|all resist(?:ances?)?|res all", r"All Resistances"),
    (r"fire res(?:ist)?", r"Fire Resist"),
    (r"cold res(?:ist)?", r"Cold Resist"),
    (r"light(?:ning)? res(?:ist)?", r"Lightning Resist"),
    (r"poison res(?:ist)?|psn res", r"Poison Resist"),
    (r"ED", None),
    (r"def|defense|defence", None),
    (r"AR|attack rating", r"Attack Rating"),
    (r"life", r"to Life|Maximum Life|Life after each"),
    (r"mana", r"to Mana|Maximum Mana|Mana after each"),
    (r"block|chance to block", r"Chance of Blocking|Chance to Block"),
    (r"DR|damage reduced|dmg reduced|damage reduce", r"Damage Reduced"),
    (r"thorns", r"Attacker Takes"),
    (r"pierce|piercing", r"Piercing Attack"),
    (r"mana regen|regen mana|regenerate mana", r"Regenerate Mana"),
    (r"replenish life|life regen|regen life", r"Replenish Life"),
]
_STAT_RE = []
for _words, _line in STATS:
    _flags = re.I if _words.lower() == _words else 0
    _STAT_RE.append((re.compile(FIG + r"\s?(?:to\s+|more\s+|bonus\s+)?(?:" + _words + r")\b", _flags),
                     re.compile(r"\b(?:" + _words + r")\s?(?:by\s+|of\s+)?" + FIG, _flags)))
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
        # M6 T2 review: ITEM_INFO holds lines with SEVERAL entries ("Tarnhelm":"..","Stealskull":"..",..). A reader anchored
        # on one entry per line never read them, so the copies the page shows went unchecked. Every pair on a line is read,
        # and a line the reader cannot account for in full is an error, never a skip.
        for ln in body.split("\n")[1:]:
            t = ln.strip()
            if not t or t.startswith("//"):
                continue
            pairs = list(_INFO_PAIR.finditer(t))
            rest = _INFO_PAIR.sub("", t).replace(",", "").strip()
            assert pairs and not rest, "%s: a line the reader cannot read in full: %r" % (table, t[:120])
            for m in pairs:
                out.setdefault(json.loads('"%s"' % m.group(1)), []).append(json.loads('"%s"' % m.group(2)))
    return out


_INFO_PAIR = re.compile(r'"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"')


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


def skill_claims(note):
    """(figure, the class or tree words it names, text) for every skill-count claim in a note"""
    out = []
    for m in SKILL.finditer(note):
        fig = m.group(1) + ("-" + m.group(2) if m.group(2) else "")
        words = [w for part in m.group(3).lower().split() for w in part.split("/")] + [m.group(4).lower()]
        if "all" in words:
            out.append((fig, ["all skills"], m.group(0)))
            continue
        trees = [TREE[w] for w in words if w in TREE]
        classes = [CLASS[w] for w in words if w in CLASS]
        if trees or classes:
            out.append((fig, trees or classes, m.group(0)))
    return out


def skill_problems(note, c):
    """a skill count must be the figure of a table line that names every class or tree the claim names"""
    lines = [l for l in _table(c) if l.strip().startswith("+")]
    bad = []
    for fig, scopes, text in skill_claims(note):
        for sc in scopes:
            if not any((lambda mm: mm and sc in mm.group(1).lower())(re.match(r"\s*\+" + re.escape(fig) + r" (?:to )?(.*)", l))
                       for l in lines):
                bad.append(text)
                break
    return bad


def _figs(line):
    """every figure a table line prints: '+160-200% Enhanced Defense' -> {'160-200', '160'}"""
    out = set()
    for m in re.finditer(r"\[?([+-]?\d+(?:\.\d+)?)\]?(?:\s?-\s?\[?(\d+(?:\.\d+)?)\]?)?", line):
        a = m.group(1).lstrip("+")
        out.add(a + ("-" + m.group(2) if m.group(2) else ""))
        out.add(a)
    return out


def stat_claims(clause):
    """(figure, has %, stat index, text) for every '<figure> <stat>' / '<stat> <figure>'; a claim inside a longer
    claim is the longer one's (3-6% life steal is a leech claim, not a life one)"""
    found = []
    for i, (pa, pb) in enumerate(_STAT_RE):
        for p in (pa, pb):
            for m in p.finditer(clause):
                found.append((m.group(1).replace(" ", "").lstrip("+"), bool((m.group(2) or "").strip()), i,
                              m.group(0), m.span()))
    return [a for a in found
            if not any(b is not a and b[4][0] <= a[4][0] and a[4][1] <= b[4][1] and b[4][1] - b[4][0] > a[4][1] - a[4][0]
                       for b in found)]


def stat_problems(note, c):
    lines, bad = _table(c), []
    for clause in re.split(r"\s*·\s*", note):
        for fig, pct, i, text, _span in stat_claims(clause):
            words, want = STATS[i]
            if want is None:
                if words == "ED":
                    want = r"Enhanced Damage" if any("Enhanced Damage" in l for l in lines) else r"Enhanced Defense"
                else:
                    want = r"Enhanced Defense" if pct else r"^\+?[\d.]+(?:-[\d.]+)? Defense\b"
            cand = [l for l in lines if re.search(want, l)]
            if not cand or not any(fig in _figs(l) for l in cand):
                bad.append("%s (table: %s)" % (text, " / ".join(cand) or "no such line"))
    return bad


def number_problems(note, lines, c=None):
    """every number a note prints must be one its own table prints (and its sockets / level / tc fields)"""
    ok = set(NUM.findall(" | ".join(lines)))
    for k in ("sockets", "reqLvl", "qlvl", "tc", "reqStr", "reqDex"):
        if c is not None and c.get(k) is not None:
            ok.add(str(c[k]))
    return [x for x in NUM.findall(note) if x not in ok]


def _runes(src):
    """the rune table's weapon / armor / shield lines, by rune name"""
    out = {}
    for m in re.finditer(r'\{num:\d+, n:"(\w+)",[^\n]*?w:"([^"]*)", a:"([^"]*)", s:"([^"]*)"', src):
        out[m.group(1)] = [m.group(2), m.group(3), m.group(4)]
    return out


def _newuni(src):
    i = src.index("var _NEWUNI = {")
    j = src.index("\n", i)
    return json.loads(src[i + len("var _NEWUNI = "):j].rstrip().rstrip(";"))


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
        cls.newuni = _newuni(cls.src)
        cls.runes = _runes(cls.src)

    def _copies(self):
        """(name, entry, where, note): every codex note, every ITEM_INFO copy of it, and the ITEM_INFO note a runtime
        unique (_NEWUNI) shows on its card"""
        for name, c in self.codex.items():
            yield name, c, "codex", str(c.get("note") or "")
            for v in self.info.get(name, []):
                yield name, c, "info", v
        for name, c in self.newuni.items():
            for v in self.info.get(name, []):
                yield name, c, "runtime unique", v

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
        for name, c, where, note in self._copies():
            if not note:
                continue
            checked += len(ABS_NUM.findall(note)) + len(ABS_BARE.findall(note)) + len(skill_claims(note))
            for b in absorb_problems(note, c) + skill_problems(note, c):
                bad.append("%s (%s): %r" % (name, where, b))
        self.assertGreaterEqual(checked, 100, "PRINT THE DENOMINATOR: only %d absorb / skill claims read" % checked)
        self.assertEqual(bad, [], "a note claims an absorb or a skill count its own table does not hold")

    def test_the_skill_reader_reads_every_shape_the_review_named(self):
        """the old reader needed the word 'skills' after at most two letter-only words, so these read as nothing"""
        for note, scopes in (("+1-2 cold sorc", ["cold"]), ("+1 fire sorc", ["fire"]),
                             ("+1-3 fire/light skills", ["fire", "lightning"]), ("+2 paladin auras", ["auras"]),
                             ("+1 nec auras", ["auras"]), ("+2 poison and bone skills", ["poison", "bone"]),
                             ("+3 sorc skills", ["sorc"]), ("+2 ALL skills", ["all skills"])):
            got = skill_claims(note)
            self.assertEqual([g[1] for g in got], [scopes], "the skill reader reads %r as %r" % (note, got))

    def test_every_number_in_a_note_is_its_own_tables(self):
        """acceptance #4: every number a note prints exists in its own table - in every copy of the note"""
        read, bad, bare = 0, [], []
        for name, c, where, note in self._copies():
            if not note:
                continue
            lines = _table(c)
            if not lines and where == "codex" and name.endswith(" rune"):
                lines = [l for r in re.split(r"[/ ]", name[:-len(" rune")]) for l in self.runes.get(r, [])]
                self.assertTrue(lines, "premise: the rune table holds %s" % name)
            if not lines:
                if where == "codex" and NUM.search(note):
                    bare.append("%s: %r" % (name, note))
                continue
            read += len(NUM.findall(note))
            for x in number_problems(note, lines, c):
                bad.append("%s (%s): %s in %r" % (name, where, x, note))
        self.assertGreaterEqual(read, 1200, "PRINT THE DENOMINATOR: only %d note numbers read" % read)
        self.assertEqual(bare, [], "a note with no table to read prints a number")
        self.assertEqual(bad, [], "a note prints a number its own table does not hold:\n  " + "\n  ".join(bad))

    def test_every_named_stat_carries_its_table_figure(self):
        """a number that exists is not enough: Gheed's Fortune printed its gold figure as MF and its MF as gold"""
        read, bad = 0, []
        for name, c, where, note in self._copies():
            if not note or not _table(c):
                continue
            read += sum(len(stat_claims(cl)) for cl in re.split(r"\s*·\s*", note))
            for b in stat_problems(note, c):
                bad.append("%s (%s): %s" % (name, where, b))
        self.assertGreaterEqual(read, 800, "PRINT THE DENOMINATOR: only %d stat claims read" % read)
        self.assertEqual(bad, [], "a note names a stat with a figure its table line does not print:\n  " + "\n  ".join(bad))

    def test_the_reviewed_notes_say_their_tables(self):
        s = self.src
        for stale in ("+1-2 cold sorc", "+1 fire sorc", "+1-3 fire/light skills", "+2 paladin auras", "+1 nec auras",
                      "+8-10% LL · ML", "+15 STR · 8% LL", "+200% ED · 25% CB", "+20-40% cold res", "+15-20 LL",
                      "40% IAS · +25 DEX", "+20-40 ELG · +80-160% MF", "+100% MF vs demons", "+20% fcr"):
            self.assertNotIn(stale, s, "a contradicted note is back: %r" % stale)

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
    {"why": "#62 review - Frostburn's note gives +1-2 cold sorc skills again, which no line of its table holds",
     "file": "bible.html",
     "find": "+40% max mana · adds 1-6 cold dmg · caster gloves",
     "replace": "+40% max mana · +1-2 cold sorc · caster gloves",
     "matches": 2},
    {"why": "#62 review - Seraph's Hymn's note gives +2 paladin auras again over +2 All Skills / +1 Masteries",
     "file": "bible.html",
     "find": "+2 ALL skills · +1 masteries · +25-50% damage to demons and undead",
     "replace": "+2 paladin auras · +1 masteries · +25-50% damage to demons and undead",
     "matches": 2},
    {"why": "#62 review - Eschuta's Temper's slash form '+1-3 fire/light skills' is back over +1-3 Sorceress",
     "file": "bible.html",
     "find": "+1-3 sorc skills · +40% FCR",
     "replace": "+1-3 fire/light skills · +40% FCR",
     "matches": 2},
    {"why": "#62 review - Homunculus's note gives +1 nec auras again",
     "file": "bible.html",
     "find": "+2 nec skills · +2 poison and bone skills · +40 all res",
     "replace": "+2 nec skills · +1 nec auras · +40 all res",
     "matches": 2},
    {"why": "#62 review - Gheed's Fortune swaps its gold and MF figures again (both numbers exist, only the stat reader sees it)",
     "file": "bible.html",
     "find": "+80-160% extra gold · +20-40% MF",
     "replace": "+20-40% extra gold · +80-160% MF",
     "matches": 2},
    {"why": "#62 review - Crow Caw's note prints an IAS figure its table does not hold again",
     "file": "bible.html",
     "find": "15% IAS · +15 DEX · 35% open wounds",
     "replace": "40% IAS · +15 DEX · 35% open wounds",
     "matches": 2},
    {"why": "#62 review - a rune note prints a figure the rune table does not hold",
     "file": "bible.html",
     "find": "Ber: 20% Crushing Blow (weapon)",
     "replace": "Ber: 25% Crushing Blow (weapon)",
     "matches": 1},
    {"why": "#62 review - a note with no table to read prints a number again (the keys' '3 keys')",
     "file": "bible.html",
     "find": "One of the three Pandemonium keys; cube one of each in Hell Harrogath for a mini-uber portal.",
     "replace": "One of the 3 keys used to open Uber Tristram.",
     "matches": 2},
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
    {"why": "M6 T2 review - a shown ITEM_INFO copy that shares its line with another entry contradicts its table again "
            "(Stealskull's stale +5-10% LL/ML, +25-50% MF beside Tarnhelm's entry)",
     "file": "bible.html",
     "find": '  "Tarnhelm":"+1 ALL skills · +25-50% MF · low-lvl MF helm",\n  "Stealskull":"+10% IAS · 5% LL/ML · +30-50% MF · MF helm",\n',
     "replace": '  "Tarnhelm":"+1 ALL skills · +25-50% MF · low-lvl MF helm","Stealskull":"+10% IAS · +5-10% LL/ML · +25-50% MF · MF helm",\n',
     "matches": 1},
    {"why": "M6 T2 review - Boneflame's shown copy, on a line with Wizardspike's, is a Phoenix-base blurb again, not its note",
     "file": "bible.html",
     "find": '  "Boneflame":"+2-3 nec skills · +20-30 all res · +20% FRW · CTC Terror · necro shield",\n  "Wizardspike":',
     "replace": '  "Boneflame":"4 sockets · necro Phoenix base","Wizardspike":',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
