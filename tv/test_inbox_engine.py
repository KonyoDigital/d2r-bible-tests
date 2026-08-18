"""v1794 — THE BOARD'S FOLD AND THIS FILE'S FOLD MUST BE THE SAME FOLD.

`chronicle_resolve.py` repairs a reader's OCR slip against the roster before the gate counts
witnesses. The board needed the same repair — it is a `file://` page and a phone he opens mid-game,
so it can never call this Python — and v1789's own note says exactly what makes that dangerous:

    "writing a second, differently-behaved matcher on the board is how two answers to one question
     start disagreeing quietly."

The load-bearing word is DIFFERENTLY. Two runtimes are forced by the deployment; two BEHAVIOURS are
a choice, and this file is how that choice is refused. It extracts the marked block out of
bible.html — the real shipped source, not a copy kept beside it — runs it in node, and fails on the
first name where the two disagree.

WHY IT EXTRACTS RATHER THAN IMPORTS. A vendored copy of the JS would be one more artifact to sync,
and a gate that reads the copy would go green while the page shipped something else. That is
`copy-drift` in its purest form, and it is the exact failure this gate exists to prevent — so the
bytes under test are the bytes between INBOX_ENGINE_BEGIN and INBOX_ENGINE_END in bible.html.

WHAT THE CORPUS IS MADE OF, and why each part is there:
  · every roster name            — an exact match must never go anywhere near the near-match path
  · his five real OCR slips      — the measured cases: Battlecage, Naglring, Heart Garver,
                                   Twitchthrow, Gravepalms (read off his ledger by hand 2026-08-18)
  · his real reader debris       — base names and truncations that must fold onto NOTHING
  · single-character mutations   — deletion, insertion and substitution on 160 roster names, which
                                   is where the cutoff and the ambiguity gap actually get exercised.
                                   A corpus of only the known cases proves the known cases; the
                                   mutations are what would catch a ratio implemented almost right.

The mutation seed is FIXED. A random corpus that fails once and passes on re-run teaches nothing and
gets ignored — the same reason `--shard` splitting by file count is called out in the gate notes.
"""

import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIBLE = os.path.join(REPO, "bible.html")

# This file's failure messages quote HIS item names and the em dashes in its own prose. On a
# non-UTF-8 console that crashes while REPORTING, so a clean tree exits non-zero for a reason that
# has nothing to do with the code. test_control.py enforces this on every tv/test_*.py.
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

BEGIN = "INBOX_ENGINE_BEGIN"
END = "INBOX_ENGINE_END"

# read off his own ledger by hand on 2026-08-18 — the six that were the same row read twice
REAL_SLIPS = {
    "Battlecage": "Rattlecage",
    "Naglring": "Nagelring",
    "Heart Garver": "Heart Carver",
    "Twitchthrow": "Twitchthroe",
    "Gravepalms": "Gravepalm",
}

# reader debris from the same read — every one of these must fold onto NOTHING, because each is
# either the game naming a row he has NOT found or the reader quoting its own damage
REAL_DEBRIS = [
    "Bone Visage", "Templar Coat", "Wrist Sword", "Ancient Sword", "Basinet", "Thunder Maul",
    "Firel...", "Natalya's...", "Heavas (partially obscured)",
    "Chronicle of Items", "Horadric Cube", "Sort by", "the dragon",
]


def _extract_block(path=BIBLE):
    """The shipped source between the two markers. Refuses on anything but exactly one pair."""
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    if src.count(BEGIN) != 1 or src.count(END) != 1:
        raise AssertionError(
            "expected exactly one %s/%s pair in bible.html, found %d/%d — the gate reads the SHIPPED "
            "source, so a duplicated or deleted marker is a real failure, not a test bug"
            % (BEGIN, END, src.count(BEGIN), src.count(END)))
    m = re.search(r"/\* " + BEGIN + r".*?\*/(.*?)/\* " + END + r" \*/", src, re.S)
    if not m:
        raise AssertionError("markers present but the block would not extract — check the comment form")
    return m.group(1)


@unittest.skipIf(shutil.which("node") is None, "node not installed — see js_syntax_gate for the same dependency")
class TestInboxEngineMatchesChronicleResolve(unittest.TestCase):
    """The board's fold and chronicle_resolve.py answer identically, name for name."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, HERE)
        import chronicle_resolve as res
        cls.res = res
        cls.roster = res.load_roster()
        cls.names = sorted(set(cls.roster.values()))
        cls.block = _extract_block()
        cls.corpus = cls._build_corpus(cls.names)
        cls.js = cls._run_node(cls.block, cls.names, cls.corpus)

    @staticmethod
    def _build_corpus(names):
        corpus = list(names)
        corpus += list(REAL_SLIPS)
        corpus += REAL_DEBRIS
        corpus += ["", "   ", "xq", "Latent Black Cleft", "Black Cleft",
                   "Bone Break", "Latent Bone Break", "The Dragon Chang(?)"]
        rnd = random.Random(1794)          # fixed: a corpus that differs per run cannot be argued with
        alpha = "abcdefghijklmnopqrstuvwxyz"
        for n in names[:160]:
            if len(n) < 4:
                continue
            i = rnd.randrange(len(n))
            corpus.append(n[:i] + n[i + 1:])                      # deletion
            corpus.append(n[:i] + rnd.choice(alpha) + n[i:])      # insertion
            corpus.append(n[:i] + rnd.choice(alpha) + n[i + 1:])  # substitution
        return corpus

    @staticmethod
    def _run_node(block, names, corpus):
        harness = block + """
const roster = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const corpus = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));
const idx = D2R_INBOX_FOLD.index(roster);
console.log(JSON.stringify({
  cutoff: D2R_INBOX_FOLD.NEAR_CUTOFF,
  gap: D2R_INBOX_FOLD.AMBIGUITY_GAP,
  fold: corpus.map(n => D2R_INBOX_FOLD.fold(n, idx).canonical),
  norm: corpus.map(n => D2R_INBOX_FOLD.norm(n)),
}));
"""
        d = tempfile.mkdtemp(prefix="inbox-engine-gate-")
        try:
            hp = os.path.join(d, "harness.js")
            rp = os.path.join(d, "roster.json")
            cp = os.path.join(d, "corpus.json")
            for p, data in ((hp, harness), (rp, json.dumps(names)), (cp, json.dumps(corpus))):
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(data)
            out = subprocess.run([shutil.which("node"), hp, rp, cp],
                                 capture_output=True, text=True, timeout=180)
            if out.returncode:
                raise AssertionError("the extracted block would not run in node:\n%s" % out.stderr[:3000])
            return json.loads(out.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_two_constants_are_the_same_two_constants(self):
        # Calibrated in chronicle_resolve.py against HIS ledger. A board that folded at a looser
        # cutoff would write finds he never made, and nothing else in the tree would notice.
        self.assertEqual(self.js["cutoff"], self.res.NEAR_CUTOFF)
        self.assertEqual(self.js["gap"], self.res.AMBIGUITY_GAP)

    def test_norm_agrees_character_for_character(self):
        # The fold key is upstream of every other answer: two implementations that normalise
        # differently are comparing different strings before either has matched anything.
        bad = [(n, self.res._norm(n), j)
               for n, j in zip(self.corpus, self.js["norm"]) if self.res._norm(n) != j]
        self.assertEqual(bad[:10], [], "%d of %d names normalise differently" % (len(bad), len(self.corpus)))

    def test_every_name_in_the_corpus_folds_the_same_way(self):
        bad = []
        for name, j in zip(self.corpus, self.js["fold"]):
            p = self.res.canonical(name, self.roster)
            if p != j:
                bad.append({"name": name, "python": p, "js": j})
        self.assertEqual(bad[:10], [],
                         "%d of %d names disagree between bible.html and chronicle_resolve.py"
                         % (len(bad), len(self.corpus)))

    def test_his_five_real_ocr_slips_still_fold(self):
        # The gate above proves AGREEMENT; this proves the agreed answer is the RIGHT one. Two
        # implementations can agree perfectly on being broken.
        got = dict(zip(self.corpus, self.js["fold"]))
        for slip, want in REAL_SLIPS.items():
            self.assertEqual(got.get(slip), want, "%r no longer folds onto %r" % (slip, want))

    def test_real_reader_debris_folds_onto_nothing(self):
        # The safety boundary, from the other side: a base name or a torn read that folded onto a
        # roster item would write a find he never made. "the dragon" -> "The Dragon Chang" is the
        # measured case that fixed NEAR_CUTOFF at 0.86 rather than 0.80.
        got = dict(zip(self.corpus, self.js["fold"]))
        for name in REAL_DEBRIS:
            self.assertIsNone(got.get(name), "%r folded onto %r — it must fold onto nothing"
                              % (name, got.get(name)))

    def test_every_roster_name_folds_onto_itself(self):
        got = dict(zip(self.corpus, self.js["fold"]))
        bad = [n for n in self.names if got.get(n) != n]
        self.assertEqual(bad[:10], [], "%d roster names do not fold onto themselves" % len(bad))

    def test_the_six_latent_pairs_stay_twelve_items(self):
        """The near-twin pairs the roster deliberately holds must never merge.

        chronicle_resolve.py's own comment records how close this came: "Latent Cold Rupture" LOOKS
        like a quality roll prefixed onto "Cold Rupture", and the first cut of that file stripped the
        prefix. The roster carries BOTH forms as separate grail entries — all six pairs, TWELVE slots.
        Merging each pair would have credited him with an item he had not found AND deleted the other
        from his hunt list, in a ledger where there is no unfind.

        This asserts the pairs from the roster rather than from a hand-list, so a seventh pair added
        to the game is covered the day it appears."""
        got = dict(zip(self.corpus, self.js["fold"]))
        pairs = [(n, n[len("Latent "):]) for n in self.names
                 if n.startswith("Latent ") and n[len("Latent "):] in set(self.names)]
        self.assertGreaterEqual(len(pairs), 6, "expected at least the six known Latent pairs, got %r" % pairs)
        for latent, bare in pairs:
            self.assertEqual(got.get(latent), latent, "%r folded onto %r" % (latent, got.get(latent)))
            self.assertEqual(got.get(bare), bare, "%r folded onto %r" % (bare, got.get(bare)))

    def test_the_real_roster_has_no_fold_collisions(self):
        """load_roster() RAISES when two DISTINCT roster names normalise to one key, because silently
        picking a winner credits him with an item he never found. That guard is only meaningful if the
        roster it guards is actually clean — and if it ever stops being clean, this says so here rather
        than by taking the console down mid-sweep."""
        keys = {}
        for n in self.names:
            keys.setdefault(self.res._norm(n), []).append(n)
        collisions = {k: v for k, v in keys.items() if len(v) > 1}
        self.assertEqual(collisions, {}, "distinct roster names share a fold key")

    def test_the_board_refuses_a_collided_key_instead_of_crashing(self):
        """The one place the two implementations may legitimately DIFFER, and it is a difference in
        failure mode rather than in verdict. Python raises; a browser may not take the whole board
        down over one bad key, so the JS poisons that key and refuses to fold it. Same answer for the
        name in question — no fold — without the crash. Asserted explicitly so nobody later 'fixes'
        it into picking a winner."""
        harness = self.block + """
const idx = D2R_INBOX_FOLD.index(['Foo Bar', 'FooBar', 'Clean Name']);
console.log(JSON.stringify({
  collided: D2R_INBOX_FOLD.fold('Foo Bar', idx),
  clean: D2R_INBOX_FOLD.fold('Clean Name', idx),
}));
"""
        d = tempfile.mkdtemp(prefix="inbox-engine-collide-")
        try:
            hp = os.path.join(d, "h.js")
            with open(hp, "w", encoding="utf-8") as fh:
                fh.write(harness)
            out = subprocess.run([shutil.which("node"), hp], capture_output=True, text=True, timeout=60)
            self.assertEqual(out.returncode, 0, out.stderr[:2000])
            got = json.loads(out.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        self.assertIsNone(got["collided"]["canonical"])
        self.assertEqual(got["collided"]["why"], "roster-collision")
        self.assertEqual(got["clean"]["canonical"], "Clean Name")


if __name__ == "__main__":
    unittest.main(verbosity=2)
