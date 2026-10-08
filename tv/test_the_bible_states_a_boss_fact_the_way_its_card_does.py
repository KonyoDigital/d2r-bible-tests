# -*- coding: utf-8 -*-
"""#272 (REG-2033) - THE BIBLE STATES A BOSS OR ITEM FACT THE WAY ITS OWN CARD DOES.

The #231 second eye read the May commits (v42/v43) and found game facts on his live site that the page's
OWN data contradicts. MEASURED in bible.html at 2c1ae533:

  * the Pandemonium table said Uber Mephisto 'Cold + Lit immune', Uber Diablo 'Fire + Lit immune', Uber Baal
    'None' - while the uber ID cards below it (with their resist numbers) say Lightning + Poison, Fire + Cold,
    Fire + Cold;
  * three Hellfire Torch lines said '+20 stats' while the drop data says '+10-20 attr';
  * two lines sent him to Anya with a Standard of Heroes for the Torch, while the Torch's own card says the
    Uber Tristram trio is the only source and it drops beside the Standard.

One fact written in two places drifts; this law makes the copy answer to the card. Pure text, stdlib only.
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(os.path.dirname(HERE), "bible.html")

_ELEMENTS = ("fire", "cold", "lightning", "poison", "magic", "physical")


def _src():
    with open(PAGE, encoding="utf-8") as f:
        return f.read()


def _elements(text):
    t = re.sub(r"\blit\b", "lightning", text.lower())
    return {e for e in _ELEMENTS if e in t}


def _plain(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def uber_cards(src):
    """{card id: the elements its `immune:` field names} for the three Uber Tristram cards."""
    out = {}
    for m in re.finditer(r"\{ id:'(uber-(?:mephisto|diablo|baal))'", src):
        end = src.find("{ id:'", m.end())
        block = src[m.end():end if end > 0 else m.end() + 4000]
        im = re.search(r"\bimmune:'([^']*)'", block)
        out[m.group(1)] = _elements(im.group(1)) if im else None
    return out


def pandemonium_rows(src):
    """{card id: the elements the Pandemonium table's immunity cell names}, one <tr> at a time."""
    out = {}
    for m in re.finditer(r"onclick=\"jumpToUberBoss\('(uber-(?:mephisto|diablo|baal))'\)\"", src):
        row_end = src.find("</tr>", m.end())
        cells = re.findall(r"<td>([^<]*)</td>", src[m.end():row_end])
        out[m.group(1)] = _elements(cells[0]) if cells else None
    return out


def torch_attr_range(src):
    m = re.search(r'n: "Hellfire Torch", from: \[[^\]]*\], rate: "[^"]*", note: "([^"]*)"', src)
    if not m:
        return None
    r = re.search(r"\+(\d+-\d+) attr", m.group(1))
    return r.group(1) if r else None


def torch_stat_claims(src):
    """Every '+N stats' figure stated in the same sentence as the Hellfire Torch, on the rendered text."""
    text = _plain(src)
    return re.findall(r"Hellfire Torch[^.;]{0,160}?\+(\d+(?:-\d+)?) stats", text)


def torch_anya_sentences(src):
    text = _plain(src)
    return [s for s in re.split(r"(?<=[.!?])\s", text)
            if "Hellfire Torch" in s and re.search(r"\bAnya\b", s)]


class TheBibleStatesABossFactTheWayItsCardDoes(unittest.TestCase):

    def test_the_pandemonium_table_names_the_immunities_its_uber_cards_name(self):
        src = _src()
        cards, rows = uber_cards(src), pandemonium_rows(src)
        self.assertEqual(sorted(cards), ["uber-baal", "uber-diablo", "uber-mephisto"], cards)
        self.assertEqual(sorted(rows), sorted(cards), "the Pandemonium table lost a row: %r" % rows)
        for uid in cards:
            self.assertTrue(cards[uid], "%s's card names no immunity - nothing to compare" % uid)
            self.assertEqual(rows[uid], cards[uid],
                             "%s: the table says %r, its card says %r" % (uid, rows[uid], cards[uid]))

    def test_every_hellfire_torch_stat_line_matches_its_drop_data(self):
        src = _src()
        want = torch_attr_range(src)
        self.assertEqual(want, "10-20", "the Torch's drop data no longer states its attribute range")
        claims = torch_stat_claims(src)
        self.assertGreaterEqual(len(claims), 3, "the Torch stat lines moved - this law reads %r" % claims)
        self.assertEqual(sorted(set(claims)), [want], "a Torch line states %r, its data says +%s" % (claims, want))

    def test_no_line_sends_him_to_anya_for_the_torch(self):
        self.assertEqual(torch_anya_sentences(_src()), [])


RED_PROOF = [
    {"why": "REG-2033 - the Pandemonium table names an immunity its Uber Mephisto card does not",
     "file": "bible.html",
     "find": "<td>Lightning + Poison immune</td>",
     "replace": "<td>Cold + Lit immune</td>",
     "matches": 1},
    {"why": "REG-2033 - a Hellfire Torch line states +20 stats again",
     "file": "bible.html",
     "find": "+3 skills tab · +10-20 stats · +10-20 all res) — no turn-in",
     "replace": "+3 skills tab · +20 stats · +10-20 all res) — no turn-in",
     "matches": 1},
    {"why": "REG-2033 - a line sends him to Anya for the Hellfire Torch again",
     "file": "bible.html",
     "find": "The trio drops the",
     "replace": "Talk to Anya · receive",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
