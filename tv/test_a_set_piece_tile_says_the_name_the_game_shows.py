"""REG-2145 - a set tile says the name the game shows, and the file index stays the key.

Three codex members are the game file's index: Cow King's Hoofs, Griswolds's Redemption,
Wihtstan's Guard. The string on the item is column 0 of that same row in the generated
sets table. The tile, the member line, the hover title and the set-piece tip print column 0.
data-arttip, artOr, the codex name, MP_TEXT_ALIAS and the art map stay on the index.
A name the table does not index is unchanged. Two shown names for one index stay the index.
"""
import io
import json
import os
import re
import shutil
import subprocess
import unittest

import char_props

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = shutil.which("node")
OPEN = '<script id="v174-char-engine-js">'

# The three the codex actually prints, plus the index the task named that is not a member.
PINNED = {
    "Cow King's Hoofs": "Cow King's Hooves",
    "Griswolds's Redemption": "Griswold's Redemption",
    "Wihtstan's Guard": "Whitstan's Guard",
    "Tal Rasha's Howling Wind": "Tal Rasha's Guardianship",
}


def _src():
    with io.open(os.path.join(ROOT, "bible.html"), encoding="utf-8") as fh:
        return fh.read()


def _once(src, needle):
    n = src.count(needle)
    if n != 1:
        raise AssertionError("%r is in bible.html %d times" % (needle[:80], n))
    return src.index(needle)


def _engine(src):
    i = _once(src, OPEN) + len(OPEN)
    return src[i:src.index("</script>", i)]


def _slice(src, start, end):
    i = _once(src, start)
    j = src.index(end, i)
    return src[i:j]


def _expect_map():
    """column 1 -> column 0, and only when that index has one shown name."""
    out = {}
    rows = {}
    for row in char_props.embedded()["sets"]:
        rows.setdefault(row[1], []).append(row[0])
    for index, shown in rows.items():
        if index and len(set(shown)) == 1 and shown[0]:
            out[index] = shown[0]
    return out


def _drive(src):
    detail = _slice(src, "function _setPieceShownFromRows(rows, name){", "window.setDetailHtml = setDetailHtml;\n")
    detail += "window.setDetailHtml = setDetailHtml;\n"
    card = _slice(src, "function renderCodexCard(name){", "\nfunction renderDetail(")
    codex = src[_once(src, "const ITEM_CODEX = "):]
    codex = codex[:codex.index("\n")]
    js = r"""
var window = {};
function _norm(s){ return String(s == null ? '' : s).toLowerCase().replace(/\s+/g, ' ').trim(); }
function _d2artEsc(s){ return String(s == null ? '' : s); }
function artOr(name){ return '[[ART:' + name + ']]'; }
%s
%s
%s
%s
var table = window._setPieceShownFromGame;
var asked = %s;
var out = { table: {}, tiles: {}, members: {}, pure: {} };
asked.forEach(function(n){ out.table[n] = table(n); });
out.pure.two = _setPieceShownFromRows([['One','K'],['Two','K']], 'K');
out.pure.emptyShown = _setPieceShownFromRows([['','K']], 'K');
out.pure.miss = _setPieceShownFromRows([['Hooves','Hoofs']], 'Shako');
out.pure.one = _setPieceShownFromRows([['Hooves','Hoofs']], 'Hoofs');
Object.keys(ITEM_CODEX).forEach(function(k){
  var c = ITEM_CODEX[k];
  if (!c || c.cat !== 'set' || !c.setMembers || !c.setMembers.length) return;
  out.tiles[k] = setDetailHtml(k);
  out.members[k] = renderCodexCard(k);
  out.table[k + ' ::keys'] = c.setMembers.map(function(m){ return m.name; });
});
process.stdout.write(JSON.stringify(out));
""" % (codex, _engine(src), detail, card, json.dumps(sorted(
        set(list(_expect_map()) + list(PINNED) + ["Shako", "Cow King's Hooves", "Aldur's Rhythm"]))))
    proc = subprocess.run([NODE, "-"], input=js, capture_output=True, text=True, timeout=90)
    if proc.returncode != 0:
        raise AssertionError("the shipped set-name chain would not run: %s" % (proc.stderr or proc.stdout)[:1200])
    return json.loads(proc.stdout)


class ASetPieceTileSaysTheNameTheGameShows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = _src()
        cls.expect = _expect_map()
        cls.out = _drive(cls.src) if NODE else None

    def test_the_game_table_names_the_index(self):
        if NODE is None:
            self.skipTest("node is absent - this law is UNMEASURED, not passing")
        got = self.out["table"]
        for index, shown in PINNED.items():
            self.assertEqual(got[index], shown, index)
        self.assertEqual(got["Shako"], "Shako")
        self.assertEqual(got["Cow King's Hooves"], "Cow King's Hooves",
                         "the shown name was looked up as if it were the index")
        self.assertEqual(got["Aldur's Rhythm"], "Aldur's Rhythm")
        for index, shown in self.expect.items():
            self.assertEqual(got.get(index, index), shown, index)
        self.assertEqual(self.out["pure"],
                         {"two": "K", "emptyShown": "K", "miss": "Shako", "one": "Hooves"})

    def test_the_tile_and_the_member_line_say_the_shown_name_and_keep_the_index(self):
        if NODE is None:
            self.skipTest("node is absent - this law is UNMEASURED, not passing")
        expect = self.expect
        seen = set()
        for key, html in self.out["tiles"].items():
            names = self.out["table"][key + " ::keys"]
            tiles = re.findall(
                r'data-arttip="([^"]*)".*?\[\[ART:([^\]]*)\]\].*?ct-name">([^<]*)<',
                html)
            self.assertEqual(len(tiles), len(names), key)
            for tip, art, label in tiles:
                self.assertEqual(tip, art, "the art key left the index")
                self.assertIn(tip, names, key)
                self.assertEqual(label, expect.get(tip, tip), tip)
                if tip in PINNED:
                    self.assertNotEqual(label, tip)
                    seen.add(tip)
        self.assertEqual(seen, set(PINNED) - {"Tal Rasha's Howling Wind"})
        seen_members = set()
        for key, html in self.out["members"].items():
            names = self.out["table"][key + " ::keys"]
            rows = re.findall(
                r'class="cx-member">.*?\[\[ART:([^\]]*)\]\].*?class="cx-member-nm">([^<]*)<',
                html)
            self.assertEqual([art for art, _label in rows], names, key)
            for art, label in rows:
                self.assertEqual(label, expect.get(art, art), art)
                if art in PINNED:
                    seen_members.add(art)
        self.assertEqual(seen_members, set(PINNED) - {"Tal Rasha's Howling Wind"})

    def test_the_hover_and_the_tip_ask_the_same_helper_and_the_alias_keeps_the_index(self):
        src = self.src
        self.assertEqual(src.count("lab.textContent = (typeof _setPieceShown==='function') ? _setPieceShown(wn) : wn"), 2)
        self.assertEqual(src.count("lab.textContent = (typeof _setPieceShown==='function') ? _setPieceShown(nm) : nm"), 1)
        self.assertNotIn("lab.textContent = wn;", src)
        self.assertNotIn("lab.textContent = nm;", src)
        self.assertIn("var _shownPiece = _setPieceShown(sp.base);", src)
        self.assertIn('data-arttip="\'+_d2artEsc(m.name)+\'"', src)
        self.assertIn("artOr(m.name,", src)
        self.assertIn('"cow king\'s hooves": "Cow King\'s Hoofs"', src)
        self.assertIn('"Cow King\'s Hoofs": "art/heavyboots_graphic.png"', src)
        self.assertIn("window._setPieceShownFromGame = function(name){", src)


RED_PROOF = [
    {"why": "REG-2145 - the set tile prints the file index again",
     "file": "bible.html",
     "find": "      + '<div class=\"ct-body\"><div class=\"ct-name\">'+shown+'</div>'+sub+aff+'</div></div>';\n",
     "replace": "      + '<div class=\"ct-body\"><div class=\"ct-name\">'+m.name+'</div>'+sub+aff+'</div></div>';\n",
     "matches": 1},
    {"why": "REG-2145 - the string-table lookup hands back the index for every name",
     "file": "bible.html",
     "find": "  return hit || raw;\n",
     "replace": "  return raw;\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
