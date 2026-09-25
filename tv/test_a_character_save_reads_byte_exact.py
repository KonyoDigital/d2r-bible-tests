# -*- coding: utf-8 -*-
"""A CHARACTER SAVE READS BYTE-EXACT, OR THE READER SAYS WHERE IT STOPPED.

`tv/d2s_read.py` turns a D2R .d2s (format 105) into items. The item bitstream carries no per-item
length: one bit read wrong and every later item is still item-SHAPED garbage — plausible codes,
plausible names, a confident list that is wrong from that point on. The file offers exactly one
witness: after the declared number of top-level items the next two bytes are the corpse section's
`JM`. So this law is about that witness, and about never reporting a partial list as complete.

WHY A SYNTHETIC SAVE. His saves must not enter this repo (it is PUBLIC), so the fixture is built
here by a small bit-writer that knows the format independently of the reader — its own Huffman
codes, its own checksum, its own copy of the two format-105 bits. It encodes one unique armour with
a socketed magic jewel, a 2-rune runeword staff, a potion in the belt and a quest item in the stash,
and the reader must hand every field back and end exactly on the corpse tag.

THE TWO FORMAT-105 BITS (measured on three of his saves, 144 top-level items, no sniffing):
  · ONE BIT after the type-specific block of every extended item — without it Jalal's Mane and its
    Colossal Jewel derail.
  · ONE BIT after the LAST property list, then byte-align. The study decoder had recorded this as
    two quirks — 8 zero bits after a runeword list, and a 0x00 "pad" sniffed before an item — and
    every one of them is an item whose last list ends EXACTLY on a byte boundary. The fixture
    reproduces both shapes: the runeword's list and the quest item's list are made to land on a
    boundary, the unique's is made not to.

  · DRIVEN: the synthetic save decodes field-for-field and ends on the corpse tag.
  · DRIVEN: a short item count, a missing format bit, a truncated file and a bad checksum all come
    back ok=False with the byte where it stopped — never a partial list called complete.
  · DRIVEN: a runeword past runes.txt row 79 is UNKNOWN with both candidates, never guessed.
  · MEASURED when present: his TESTCLAUDE.d2s — 49 top-level items, Jalal's Mane on the head — and
    his BLANK.d2s — 28 top-level items, none equipped, the study's sniffed "pad" at 0x490 read as
    Mephisto's Brain's trailing bit.
RED_PROOF below.
"""
import io
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402  #171 — this run's scratch dirs leave with it
_fx_tmp.contain()

import d2s_read as R  # noqa: E402
import item_tables as I  # noqa: E402

T = I.load()
REAL = os.environ.get("D2S_REAL_SAVE") or os.path.join(os.path.expanduser("~"), "Desktop", "TESTCLAUDE.d2s")
BLANK = os.environ.get("D2S_BLANK_SAVE") or os.path.join(os.path.expanduser("~"), "Desktop", "BLANK.d2s")
LAST_PLAYED = 1790326379

#: The D2R item-code Huffman table, written out here rather than derived from the reader's tree, so a
#: damaged tree cannot encode and decode its own mistake into agreement.
HUFF = {" ": "10", "0": "11111011", "1": "1111100", "2": "001100", "3": "1101101", "4": "11111010",
        "5": "00010110", "6": "1101111", "7": "01111", "8": "000100", "9": "01110", "a": "11110",
        "b": "0101", "c": "01000", "d": "110001", "e": "110000", "f": "010011", "g": "11010",
        "h": "00011", "i": "1111110", "j": "000101110", "k": "010010", "l": "11101", "m": "01101",
        "n": "001101", "o": "1111111", "p": "11001", "q": "11011001", "r": "11100", "s": "0010",
        "t": "01100", "u": "00001", "v": "1101110", "w": "00000", "x": "00111", "y": "0001010",
        "z": "11011000"}
GROUPED = {17: 2, 48: 2, 50: 2, 52: 2, 54: 3, 57: 3}


class _W(object):
    """LSB-first bit writer — the mirror of the reader's _Bits."""

    def __init__(self):
        self.bits = []

    @property
    def p(self):
        return len(self.bits)

    def w(self, v, n):
        for i in range(n):
            self.bits.append((v >> i) & 1)

    def align(self):
        while len(self.bits) % 8:
            self.bits.append(0)

    def data(self):
        assert len(self.bits) % 8 == 0, "unaligned stream"
        out = bytearray(len(self.bits) // 8)
        for i, bit in enumerate(self.bits):
            if bit:
                out[i >> 3] |= 1 << (i & 7)
        return bytes(out)


def _sid(name):
    return next(int(k) for k, v in T["stats"].items() if v["name"] == name)


def _st(sid):
    return T["stats"][str(sid)]


def _filler(residue):
    """A plain item stat whose id+value is `residue` bits mod 8 — to steer where a list ends."""
    taken = {s + k for s, n in GROUPED.items() for k in range(n)}
    for sid in sorted(int(k) for k in T["stats"]):
        s = _st(sid)
        if (sid not in taken and s["name"].startswith("item_") and s["saveBits"]
                and not s["saveParamBits"] and (9 + s["saveBits"]) % 8 == residue):
            return sid
    raise AssertionError("no filler stat with residue %d — the fixture cannot steer this list" % residue)


def encode_props(w, props, land=None):
    """Write [(stat name, param, value)] + 0x1FF. land=True: the list ENDS on a byte boundary;
    land=False: it does not; None: wherever it falls. -> the list the reader must hand back."""
    out = []
    for name, param, value in props:
        sid = _sid(name)
        s = _st(sid)
        w.w(sid, 9)
        if s["saveParamBits"]:
            w.w(param, s["saveParamBits"])
        w.w(value + s["saveAdd"], s["saveBits"])
        out.append({"stat": name, "param": param if s["saveParamBits"] else None, "value": value})
    if land is not None and ((w.p + 9) % 8 == 0) != land:
        need = (-(w.p + 9)) % 8 if land else 1
        sid = _filler(need)
        s = _st(sid)
        w.w(sid, 9)
        w.w(1, s["saveBits"])
        out.append({"stat": s["name"], "param": None, "value": 1 - s["saveAdd"]})
    w.w(0x1FF, 9)
    if land is not None:
        assert (w.p % 8 == 0) == land, "the fixture failed to steer its own list"
    return out


def encode_item(w, it, v105=True, trailing=True):
    """One item (and its socketed children) in format 105. -> the fields the reader must return."""
    kids = it.get("children") or []
    simple = bool(it.get("simple"))
    flags = (1 << 4) | (1 << 23)
    flags |= (1 << 11) if "sockets" in it else 0
    flags |= (1 << 21) if simple else 0
    flags |= (1 << 22) if it.get("ethereal") else 0
    flags |= (1 << 26) if "rw" in it else 0
    start = w.p
    w.w(flags, 32)
    w.w(5, 3)
    for v, n in ((it["loc"], 3), (it.get("slot", 0), 4), (it.get("x", 0), 4), (it.get("y", 0), 4),
                 (it.get("panel", 0), 3)):
        w.w(v, n)
    for ch in (it["code"] + "    ")[:4]:
        for c in HUFF[ch]:
            w.w(int(c), 1)
    w.w(len(kids), 1 if simple else 3)
    exp = {"code": it["code"], "location": R.LOCATIONS[it["loc"]], "simple": simple,
           "ethereal": bool(it.get("ethereal")), "x": it.get("x", 0), "y": it.get("y", 0)}
    if it["loc"] == 1:
        exp["slot"] = R.SLOTS[it["slot"]]
    if it["loc"] == 0:
        exp["panel"] = R.PANELS[it["panel"]]
    if not simple:
        q = it["q"]
        w.w(0x5EED0000 + start, 32)
        w.w(it["ilvl"], 7)
        w.w(q, 4)
        w.w(0, 1)
        w.w(0, 1)
        if q in (1, 3):
            w.w(0, 3)
        elif q == 4:
            w.w(it["prefix"], 11)
            w.w(it["suffix"], 11)
            exp.update(magicPrefix=it["prefix"], magicSuffix=it["suffix"])
        elif q == 7:
            w.w(it["uid"], 12)
            exp["uniqueId"] = it["uid"]
        exp.update(quality=R.QUALITIES[q], ilvl=it["ilvl"])
        if "rw" in it:
            w.w(it["rw"], 12)
            w.w(5, 4)
            exp["runewordId"] = it["rw"]
        w.w(0, 1)                                           # timestamp
        kind = T["items"][it["code"]]["kind"]
        if kind == "armor":
            w.w(it["defense"] + _st(31)["saveAdd"], _st(31)["saveBits"])
            exp["defense"] = it["defense"]
        if kind in ("armor", "weapon"):
            w.w(it["maxdur"], _st(73)["saveBits"])
            if it["maxdur"]:
                w.w(it["dur"], _st(72)["saveBits"])
            exp["durability"] = {"current": it["dur"] if it["maxdur"] else None, "max": it["maxdur"]}
        if v105:
            w.w(0, 1)                                       # FORMAT 105: after the type block
        if "sockets" in it:
            w.w(it["sockets"], 4)
            exp["sockets"] = it["sockets"]
        last = "rwprops" if "rw" in it else "props"
        exp["props"] = encode_props(w, it.get("props") or [], it.get("land") if last == "props" else None)
        if "rw" in it:
            exp["runewordProps"] = encode_props(w, it["rwprops"], it.get("land"))
        exp["_lastListEnd"] = w.p
        if trailing:
            w.w(0, 1)                                       # FORMAT 105: after the last list
    w.align()
    exp["_start"], exp["_end"] = start, w.p
    exp["socketed"] = [encode_item(w, k, v105, trailing) for k in kids]
    return exp


def _checksum(b):
    c = 0
    for i, x in enumerate(bytearray(b)):
        c = (((c << 1) & 0xFFFFFFFF) + (0 if 12 <= i < 16 else x) + (c >> 31)) & 0xFFFFFFFF
    return c


STATS = [("strength", 25), ("energy", 15), ("dexterity", 20), ("vitality", 30), ("statpts", 5),
         ("hitpoints", 500 * 256), ("maxhp", 512 * 256), ("level", 42), ("experience", 12345678),
         ("gold", 4321)]
SKILLS = list(range(30))


def encode_save(items, count=None, v105=True, trailing=True, version=105):
    """-> (bytes, meta). A whole format-105 file around the given top-level items."""
    hdr = bytearray(R.QUESTS_AT)
    struct.pack_into("<II", hdr, 0, 0xAA55AA55, version)
    hdr[0x14], hdr[0x15], hdr[0x18], hdr[0x1B] = 0x20, 15, 5, 42
    struct.pack_into("<I", hdr, 0x20, LAST_PLAYED)
    hdr[0x12B:0x12B + 5] = b"SYNTH"
    quests = b"Woo!" + struct.pack("<IH", 6, 298) + bytes(298 - 10)
    ws = b"WS" + struct.pack("<IH", 1, 80) + bytes(80 - 8) + b"\x01"     # the measured extra byte
    w4 = b"w4" + bytes(49)
    g = _W()
    for name, val in STATS:
        sid = _sid(name)
        g.w(sid, 9)
        g.w(val, _st(sid)["csvBits"])
    g.w(0x1FF, 9)
    g.align()
    head = bytes(hdr) + quests + ws + w4 + b"gf" + g.data() + b"if" + bytes(SKILLS)
    w = _W()
    exp = [encode_item(w, it, v105, trailing) for it in items]
    body = b"JM" + struct.pack("<H", len(items) if count is None else count) + w.data()
    tail = b"JM\x00\x00" + b"jf" + b"kf\x00" + b"\x01\x00" + b"lf\x00\x00"
    blob = bytearray(head + body + tail)
    struct.pack_into("<I", blob, 8, len(blob))
    struct.pack_into("<I", blob, 12, _checksum(blob))
    return bytes(blob), {"items": exp, "itemsAt": len(head) + 4, "corpseAt": len(head + body)}


#: The fixture. Real codes and ids from his install's tables, never from his saves.
HARLEQUIN = {"code": "uap", "loc": 1, "slot": 1, "q": 7, "ilvl": 87, "uid": 248, "defense": 141,
             "maxdur": 12, "dur": 10, "sockets": 1, "land": False,
             "props": [("item_allskills", None, 2), ("item_magicbonus", None, 50), ("maxhp", None, 98)],
             "children": [{"code": "jew", "loc": 6, "q": 4, "ilvl": 80, "prefix": 101, "suffix": 202,
                           "props": [("item_fastercastrate", None, 15), ("fireresist", None, 30)]}]}
LEAF = {"code": "sst", "loc": 1, "slot": 4, "q": 3, "ilvl": 30, "rw": 98, "maxdur": 20, "dur": 20,
        "sockets": 2, "land": True,
        "props": [("item_maxdurability_percent", None, 10)],
        "rwprops": [("item_singleskill", 36, 3), ("item_addclassskills", 1, 3), ("fireresist", None, 33)],
        "children": [{"code": "r03", "loc": 6, "simple": True}, {"code": "r08", "loc": 6, "x": 1, "simple": True}]}
POTION = {"code": "hp5", "loc": 2, "x": 3, "simple": True}
BRAIN = {"code": "mbr", "loc": 0, "panel": 5, "x": 2, "y": 6, "q": 2, "ilvl": 1, "land": True, "props": []}
ITEMS = [HARLEQUIN, LEAF, POTION, BRAIN]


def _same(tc, exp, got, where):
    for k, v in exp.items():
        if k.startswith("_"):
            continue
        if k == "socketed":
            tc.assertEqual(len(got["socketed"]), len(v), "%s: socketed children" % where)
            for i, (e, g) in enumerate(zip(v, got["socketed"])):
                _same(tc, e, g, "%s/socket%d %s" % (where, i, e["code"]))
        elif k in ("props", "runewordProps"):
            tc.assertEqual([{"stat": p["stat"], "param": p["param"], "value": p["value"]} for p in got[k]], v,
                           "%s: %s" % (where, k))
        else:
            tc.assertEqual(got.get(k), v, "%s: %s" % (where, k))


@unittest.skipIf(T is None, "tv/item_tables.json is absent — it is GENERATED and COMMITTED, so this is a "
                            "broken checkout, and every law below is UNMEASURED, not passing")
class TheSyntheticSaveReadsBack(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.blob, cls.meta = encode_save(ITEMS)
        cls.res = R.read(cls.blob)

    def test_it_ends_exactly_on_the_corpse_tag(self):
        v = self.res["verify"]
        self.assertTrue(self.res["ok"], self.res["why"])
        self.assertTrue(v["endsOnCorpseTag"])
        self.assertEqual(v["bytesConsumed"], self.meta["corpseAt"], "the decode ended somewhere else")
        self.assertEqual((v["itemCount"], v["declaredItemCount"]), (4, 4),
                         "the JM count is TOP-LEVEL items; the 3 socketed children ride inside")
        self.assertTrue(v["checksumOk"] and v["sizeMatches"] and v["statsEndOnSkillsTag"])

    def test_every_item_field_reads_back(self):
        for i, (e, g) in enumerate(zip(self.meta["items"], self.res["items"])):
            _same(self, e, g, "item %d %s" % (i, e["code"]))

    def test_the_names_come_from_his_install(self):
        head, staff, pot, brain = self.res["items"]
        self.assertEqual((head["uniqueName"], head["name"], head["slot"]), ("Harlequin Crest", "Shako", "head"))
        self.assertEqual(head["socketed"][0]["name"], "Jewel")
        self.assertEqual((staff["runewordName"], staff["slot"]), ("Leaf", "right hand"))
        self.assertEqual([k["name"] for k in staff["socketed"]], ["Tir Rune", "Ral Rune"])
        self.assertEqual((pot["name"], pot["location"]), ("Super Healing Potion", "belt"))
        self.assertEqual((brain["name"], brain["panel"], brain["quality"]), ("Mephisto's Brain", "stash", "normal"))

    def test_the_fixture_exercises_both_format_105_bits(self):
        """The premise, checked: a law about a boundary that the fixture never reaches is blind."""
        head, staff, _pot, brain = self.meta["items"]
        self.assertNotEqual(head["_lastListEnd"] % 8, 0, "the unique's list was meant to end OFF a boundary")
        for it in (staff, brain):
            self.assertEqual(it["_lastListEnd"] % 8, 0, "%s was meant to end ON a boundary" % it["code"])
            self.assertEqual(it["_end"] - it["_lastListEnd"], 8,
                             "%s: the trailing bit must cost a whole byte here — the shape the study "
                             "decoder called '8 runeword bits' and 'a 0x00 pad'" % it["code"])
        at = self.meta["itemsAt"] + brain["_end"] // 8 - 1
        self.assertEqual(self.blob[at:at + 1], b"\x00", "the byte the study sniffed as a pad is not there")

    def test_the_header_stats_and_skills_read_back(self):
        h = self.res["header"]
        self.assertEqual((h["name"], h["className"], h["level"], h["version"], h["progression"]),
                         ("SYNTH", "Druid", 42, 105, 15))
        self.assertEqual((h["expansion"], h["hardcore"], h["lastPlayed"]), (True, False, LAST_PLAYED))
        want = {n: (v / 256.0 if n in R.FIXED_POINT else v) for n, v in STATS}
        self.assertEqual(self.res["stats"], want, "the stats block is read with CSvBits, not Save Bits")
        self.assertEqual(self.res["skills"], SKILLS)
        self.assertEqual(self.res["merc"]["hired"], False)
        self.assertEqual(self.res["golem"], {"present": False})

    def test_a_path_reads_the_same_as_bytes(self):
        p = os.path.join(tempfile.mkdtemp(), "synth.d2s")
        with io.open(p, "wb") as fh:
            fh.write(self.blob)
        res = R.read(p)
        self.assertTrue(res["ok"], res["why"])
        self.assertEqual(res["items"], self.res["items"])


@unittest.skipIf(T is None, "tv/item_tables.json is absent — UNMEASURED, not passing")
class ADecodeThatDerailsSaysSo(unittest.TestCase):

    def _refused(self, res, what):
        self.assertFalse(res["ok"], "%s was reported ok: %d item(s) handed back as the whole list"
                         % (what, len(res["items"])))
        self.assertTrue(res["why"], "%s: ok=False with no reason" % what)
        return res

    def test_a_short_count_does_not_end_on_the_corpse_tag(self):
        blob, meta = encode_save(ITEMS, count=3)
        res = self._refused(R.read(blob), "a list one item short")
        self.assertFalse(res["verify"]["endsOnCorpseTag"])
        self.assertEqual(res["verify"]["stoppedAt"], meta["itemsAt"] + meta["items"][3]["_start"] // 8,
                         "the byte where it stopped is not reported")
        self.assertIn("0x%X" % res["verify"]["stoppedAt"], res["why"])

    def test_a_save_without_the_type_block_bit_is_refused(self):
        blob, _ = encode_save(ITEMS, v105=False)
        self._refused(R.read(blob), "a save missing the format-105 type-block bit")

    def test_a_save_without_the_trailing_bit_is_refused(self):
        blob, _ = encode_save(ITEMS, trailing=False)
        self._refused(R.read(blob), "a save missing the format-105 trailing bit")

    def test_a_truncated_file_is_refused_never_raised(self):
        blob, meta = encode_save(ITEMS)
        for cut in (meta["itemsAt"] + 20, meta["corpseAt"] - 3, 100):
            res = self._refused(R.read(blob[:cut]), "a file cut at byte %d" % cut)
            self.assertFalse(res["verify"]["endsOnCorpseTag"])

    def test_a_missing_file_is_refused_never_raised(self):
        res = self._refused(R.read(os.path.join(tempfile.mkdtemp(), "absent.d2s")), "a file that is not there")
        self.assertIn("could not open", res["why"])

    def test_a_bad_checksum_is_not_ok(self):
        blob, _ = encode_save(ITEMS)
        bad = bytearray(blob)
        bad[12] ^= 0xFF
        res = self._refused(R.read(bytes(bad)), "a save whose checksum does not match")
        self.assertFalse(res["verify"]["checksumOk"])
        self.assertTrue(res["verify"]["endsOnCorpseTag"], "the items still decode; only the file is bad")

    def test_no_tables_is_unknown_not_a_crash(self):
        blob, _ = encode_save(ITEMS)
        res = self._refused(R.read(blob, tables={}), "a read with no tables")
        self.assertIn("UNKNOWN", res["why"])
        self.assertEqual(res["items"], [])

    def test_another_format_is_unmeasured(self):
        blob, _ = encode_save(ITEMS, version=97)
        self.assertIn("UNMEASURED", self._refused(R.read(blob), "a format-97 save")["why"])


@unittest.skipIf(T is None, "tv/item_tables.json is absent — UNMEASURED, not passing")
class ARunewordNameIsNeverGuessed(unittest.TestCase):

    def test_a_runeword_past_row_79_is_unknown(self):
        """id 159: runes.txt row 133 is Steel, key Runeword133 is Stealth. No save on hand says which."""
        steel = {"code": "crs", "loc": 0, "panel": 1, "q": 2, "ilvl": 20, "rw": 159, "maxdur": 30,
                 "dur": 30, "sockets": 2, "land": True, "rwprops": [("item_magicbonus", None, 10)],
                 "children": [{"code": "r03", "loc": 6, "simple": True},
                              {"code": "r01", "loc": 6, "x": 1, "simple": True}]}
        res = R.read(encode_save([steel])[0])
        self.assertTrue(res["ok"], "the DECODE is fine — only the name is unknown: %s" % res["why"])
        it = res["items"][0]
        self.assertIsNone(it["runewordName"], "a runeword was named by one of two readings that disagree")
        self.assertIn("Steel", it["runewordWhy"])
        self.assertIn("Stealth", it["runewordWhy"])

    def test_a_runeword_both_readings_agree_on_is_named(self):
        self.assertEqual(R._runeword(T, 37), ("Breath of the Dying", None))
        self.assertEqual(R._runeword(T, 67), ("Fortitude", None))


@unittest.skipUnless(os.path.isfile(REAL) and T is not None,
                     "UNMEASURED: his real save %s is not on this machine (or the tables are absent) — "
                     "the synthetic law still runs, the byte-exact claim about HIS save does not" % REAL)
class HisRealSave(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.res = R.read(REAL)

    def test_his_save_decodes_byte_exact(self):
        v = self.res["verify"]
        self.assertTrue(self.res["ok"], self.res["why"])
        self.assertTrue(v["endsOnCorpseTag"] and v["checksumOk"] and v["sizeMatches"])
        self.assertEqual((v["itemCount"], v["declaredItemCount"]), (49, 49))
        print("   his save: %d top-level items, ends on the corpse tag at byte 0x%X"
              % (v["itemCount"], v["bytesConsumed"]))

    def test_jalals_mane_is_on_his_head(self):
        head = [it for it in self.res["items"] if it.get("slot") == "head"]
        self.assertEqual(len(head), 1)
        self.assertEqual((head[0]["uniqueName"], head[0]["code"]), ("Jalal's Mane", "dra"))
        self.assertEqual([k["code"] for k in head[0]["socketed"]], ["cjw"])

    def test_his_runewords_carry_their_runes(self):
        rw = {it["runewordName"]: [k["code"] for k in it["socketed"]]
              for it in self.res["items"] if it.get("isRuneword")}
        self.assertEqual(rw, {"Breath of the Dying": ["r26", "r15", "r01", "r02", "r33", "r05"],
                              "Fortitude": ["r01", "r12", "r14", "r28"]})


@unittest.skipUnless(os.path.isfile(BLANK) and T is not None,
                     "UNMEASURED: his blank planner save %s is not on this machine (or the tables are absent)"
                     % BLANK)
class HisBlankSave(unittest.TestCase):
    """A second real save: a blank planner Druid, belt potions and stash keys/organs/shards/cube only.
    The study decoder had to SNIFF a 0x00 'pad' at 0x490 here, before Token of Absolution — the same
    boundary as in TESTCLAUDE. It is the last byte of Mephisto's Brain, whose list ends exactly on a
    byte boundary, so the trailing format-105 bit costs a whole byte. No sniff reads it."""

    @classmethod
    def setUpClass(cls):
        cls.res = R.read(BLANK)
        with io.open(BLANK, "rb") as fh:
            cls.blob = fh.read()

    def test_it_decodes_byte_exact_with_nothing_equipped(self):
        v = self.res["verify"]
        self.assertTrue(self.res["ok"], self.res["why"])
        self.assertTrue(v["endsOnCorpseTag"] and v["checksumOk"] and v["sizeMatches"])
        self.assertEqual((v["itemCount"], v["declaredItemCount"], v["bytesConsumed"]), (28, 28, 0x55D))
        self.assertEqual([it["code"] for it in self.res["items"] if it["location"] == "equipped"], [])
        print("   his blank save: 28 top-level items, none equipped, ends on the corpse tag at 0x55D")

    def test_the_sniffed_pad_is_the_brain_s_trailing_bit(self):
        codes = [it["code"] for it in self.res["items"]]
        brain = self.res["items"][codes.index("mbr")]
        token = self.res["items"][codes.index("toa")]
        end = (brain["bitStart"] + brain["bits"]) // 8
        self.assertEqual(self.blob[0x490:0x491], b"\x00", "the byte the study sniffed as a pad is not at 0x490")
        self.assertEqual((brain["bitStart"] // 8, end), (0x480, 0x491),
                         "Mephisto's Brain no longer owns the 0x00 at 0x490")
        self.assertEqual(token["bitStart"] // 8, 0x491, "Token of Absolution does not start right after it")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "the format-105 bit after the type-specific block is dropped - the unique and its jewel derail",
        "file": "tv/d2s_read.py",
        "find": "        r.r(1)\n        if row[\"stackable\"]:\n",
        "replace": "        if row[\"stackable\"]:\n",
        "matches": 1,
    },
    {
        "why": "the format-105 bit after the last list is dropped - every list ending on a byte boundary "
               "(the runeword's, the quest item's) loses a byte: the study's '8 bits' and 'pad' both return",
        "file": "tv/d2s_read.py",
        "find": "        # FORMAT 105 — ONE BIT after the LAST property list, then align. Not a pad, not 8 runeword bits.\n"
                "        r.r(1)\n",
        "replace": "        # FORMAT 105 — ONE BIT after the LAST property list, then align. Not a pad, not 8 runeword bits.\n",
        "matches": 1,
    },
    {
        "why": "the study's runeword rule comes back in place of the trailing bit (8 bits after a runeword "
               "list, nothing elsewhere, no sniff) - the quest item whose list ends on a boundary derails",
        "file": "tv/d2s_read.py",
        "find": "        # FORMAT 105 — ONE BIT after the LAST property list, then align. Not a pad, not 8 runeword bits.\n"
                "        r.r(1)\n",
        "replace": "        if it[\"isRuneword\"]:\n            r.r(8)\n",
        "matches": 1,
    },
    {
        "why": "socketed children are no longer read inside their parent, so the TOP-LEVEL count stops early",
        "file": "tv/d2s_read.py",
        "find": "    it[\"socketed\"] = [_item(r, T) for _ in range(n_children)]\n",
        "replace": "    it[\"socketed\"] = []\n",
        "matches": 1,
    },
    {
        "why": "the corpse-tag witness is faked: a decode that ended in the wrong place reports a complete list",
        "file": "tv/d2s_read.py",
        "find": "    v[\"endsOnCorpseTag\"] = b[end:end + 2] == CORPSE_TAG\n",
        "replace": "    v[\"endsOnCorpseTag\"] = True\n",
        "matches": 1,
    },
    {
        "why": "a runeword is named by its row alone - Steel/Stealth is guessed instead of UNKNOWN",
        "file": "tv/d2s_read.py",
        "find": "    if by_row and by_key is by_row:\n",
        "replace": "    if by_row:\n",
        "matches": 1,
    },
    {
        "why": "the stats block is read with the ITEM width (Save Bits) instead of CSvBits - strength is 8 "
               "bits there and 10 here, and the block no longer ends on the 'if' tag",
        "file": "tv/d2s_read.py",
        "find": "            val = r.r(s[\"csvBits\"])\n",
        "replace": "            val = r.r(s[\"saveBits\"] or s[\"csvBits\"])\n",
        "matches": 1,
    },
]
