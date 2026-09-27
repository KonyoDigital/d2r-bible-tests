# -*- coding: utf-8 -*-
"""A cited picture stays when its reel is released, and the evidence line opens it.

His ruling 2026-09-27: the standing line (PROVEN 12/12 · N sessions) is clickable and opens the
existing lightbox on that item's looks. A frame those looks cite is kept when the reel goes. An
uncited frame of the same reel goes. The tombstone says what it kept and why. A picture that
cannot be served says so — never a blank.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

import frame_authority as FA
import reel_retention as RR
import vault_evidence as VE

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")
BEGIN = "⟦VAULT EVIDENCE LINE BEGIN⟧"
END = "⟦VAULT EVIDENCE LINE END⟧"
TILE = "window._vaultEvidenceBtn(p.n)"

HARNESS = r"""
var window = globalThis, STORE = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
  setItem: function(k, v){ STORE[k] = String(v); } };
function _provAll(){
  try { var v = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}'); return v || {}; }
  catch (e) { return {}; } }
function jsArg(t){ return String(t).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
function esc(t){ return String(t == null ? '' : t); }
var OPENED = [];
window._tvdOpenFrame = function(id, meta){
  OPENED.push({ id: id, title: meta && meta.title, src: meta && meta.src }); };
"""

BODY = r"""
STORE['d2r_vaultProv'] = JSON.stringify({
  Shako: {
    tier: 'PROVEN', successes: 12, trials: 12, sessions: ['s0', 's1', 's2'],
    source: 'stash', by: 'evidence', at: '2026-09-27T12:00:00Z',
    looks: [
      { id: 's0', frame: 'cited.jpg', conf: 0.91, cell: { tab: 'personal', x: 3, y: 4 }, at: '2026-09-27T12:00:00Z' },
      { id: 's1', frame: 'second.jpg', conf: 0.88, cell: { tab: 'personal', x: 3, y: 4 } },
      { id: 's2', frame: null, conf: 0.4 }
    ]
  },
  Gone: {
    tier: 'PROVEN', successes: 2, trials: 2, sessions: ['g0'],
    looks: [{ id: 'g0', frame: 'gone.jpg', conf: 0.9, released: true, crop: 'crops/gone.jpg' }]
  }
});
var line = window._vaultEvidenceLine('Shako');
var first = window._vaultOpenEvidence('Shako', 0);
var second = window._vaultEvidenceStep(1);
var missing = window._vaultEvidenceStep(1);
var released = window._vaultOpenEvidence('Gone', 0);
var btn = window._vaultEvidenceBtn('Shako');
process.stdout.write(JSON.stringify({
  line: line, first: first, second: second, missing: missing, released: released,
  opened: OPENED, btn: btn
}));
"""


def _cut():
    with io.open(BIBLE, encoding="utf-8") as fh:
        src = fh.read()
    assert src.count(BEGIN) == 1 and src.count(END) == 1
    i = src.index(BEGIN)
    j = src.index(END, i) + len(END)
    return src[src.rfind("\n", 0, i) + 1:src.index("\n", j) + 1]


def _drive():
    prog = HARNESS + _cut() + BODY
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AssertionError("the evidence line would not run — UNKNOWN, not passing: %s"
                             % (r.stderr or r.stdout)[-800:])
    return json.loads(r.stdout)


def _look(frame, miss=False):
    row = {"session": "s-" + frame, "frame": frame, "conf": 0.91, "lane": "stash"}
    if miss:
        row["saw"] = "empty"
    return row


class ACitedFrameStaysAndTheLineOpensIt(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cited-frame-")
        self.hist = os.path.join(self.tmp, "hist")
        self.reel = os.path.join(self.hist, "reel_s_9_1")
        os.makedirs(self.reel)
        for name in ("cited.jpg", "miss.jpg", "other.jpg"):
            with io.open(os.path.join(self.reel, name), "w", encoding="utf-8") as fh:
                fh.write(name)
        self.ledger = os.path.join(self.tmp, "vault_accum.json")
        doc = {"owned": [{"name": "Shako", "lane": "stash", "kind": "item", "witnesses": [
            _look("cited.jpg"), _look("miss.jpg", miss=True)]}]}
        self.before = json.dumps(doc).encode("utf-8")
        with io.open(self.ledger, "wb") as fh:
            fh.write(self.before)
        self.his = os.path.join(HERE, "reel_tombstones.json")
        self.his_stat = os.stat(self.his) if os.path.isfile(self.his) else None

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _wit(self, frames):
        return {"ok": True, "haveIndex": True, "frames": set(), "cited": set(frames)}

    def _seal(self):
        return {"s_9_1": {"extracted": [], "rows": 0, "examinedEmpty": True}}

    def test_a_cited_frame_stays_and_an_uncited_one_goes(self):
        got = VE.cited_frames(self.ledger)
        self.assertTrue(got["ok"], got)
        self.assertEqual(["cited.jpg"], got["frames"])
        self.assertNotIn("miss.jpg", got["frames"])
        with io.open(self.ledger, "rb") as fh:
            self.assertEqual(self.before, fh.read(), "citing frames wrote the witness ledger")
        note = FA.keep_cited(self.reel, self._seal(), self._wit(got["frames"]))
        self.assertTrue(note["ok"], note)
        self.assertTrue(os.path.isfile(os.path.join(self.reel, "cited.jpg")))
        self.assertFalse(os.path.isfile(os.path.join(self.reel, "other.jpg")))
        self.assertFalse(os.path.isfile(os.path.join(self.reel, "miss.jpg")))
        self.assertEqual(["cited.jpg"], [k["frame"] for k in note["kept"]])
        self.assertIn("cited as vault evidence", note["kept"][0]["why"])
        self.assertEqual(["miss.jpg", "other.jpg"], note["gone"])
        rows = RR._tombstone(self.hist, [{
            "reel": "reel_s_9_1", "mb": 0.1, "pages": 1, "why": "released",
            "kept": note["kept"]}])
        self.assertEqual(["cited.jpg"], [k["frame"] for k in rows[0]["kept"]])
        self.assertIn("cited as vault evidence", rows[0]["kept"][0]["why"])
        stone = os.path.join(self.tmp, "reel_tombstones.json")
        self.assertTrue(os.path.isfile(stone), "the tombstone was not written beside the temp reel")
        with io.open(stone, encoding="utf-8") as fh:
            saved = json.load(fh)
        self.assertEqual("cited.jpg", saved["reels"][0]["kept"][0]["frame"])
        if self.his_stat is not None:
            now = os.stat(self.his)
            self.assertEqual(self.his_stat.st_mtime, now.st_mtime)
            self.assertEqual(self.his_stat.st_size, now.st_size)

    def test_an_unreadable_ledger_releases_nothing(self):
        with io.open(self.ledger, "wb") as fh:
            fh.write(b"{")
        got = VE.cited_frames(self.ledger)
        self.assertFalse(got["ok"])
        self.assertIsNone(got["frames"])
        note = FA.keep_cited(self.reel, self._seal(),
                             {"ok": True, "haveIndex": True, "frames": set(), "cited": None})
        self.assertFalse(note["ok"])
        self.assertIsNone(note["gone"])
        for name in ("cited.jpg", "miss.jpg", "other.jpg"):
            self.assertTrue(os.path.isfile(os.path.join(self.reel, name)))

    def test_a_missing_ledger_cites_nothing_and_is_not_unknown(self):
        got = VE.cited_frames(os.path.join(self.tmp, "no-such.json"))
        self.assertTrue(got["ok"])
        self.assertEqual([], got["frames"])
        idx = FA.witness_index(os.path.join(self.tmp, "empty-root"))
        os.makedirs(os.path.join(self.tmp, "empty-root"), exist_ok=True)
        idx = FA.witness_index(os.path.join(self.tmp, "empty-root"))
        self.assertTrue(idx["ok"])
        self.assertEqual(set(), idx["cited"])

    @unittest.skipIf(NODE is None, "node is absent — the evidence line was not driven")
    def test_the_evidence_line_opens_the_right_frames(self):
        with io.open(BIBLE, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(1, src.count(TILE), "the vault tile does not open the evidence line")
        out = _drive()
        self.assertEqual("PROVEN 12/12 · 3 sessions", out["line"])
        self.assertEqual("cited.jpg", out["first"]["frame"])
        self.assertEqual("second.jpg", out["second"]["frame"])
        self.assertIn("personal 3,4", out["first"]["title"])
        self.assertIn("conf 0.91", out["first"]["title"])
        self.assertEqual(["cited.jpg", "second.jpg"], [o["id"] for o in out["opened"][:2]])
        self.assertEqual("picture missing: UNKNOWN", out["missing"]["say"])
        self.assertIsNone(out["missing"]["frame"])
        self.assertNotIn("", [o["id"] for o in out["opened"]])
        self.assertEqual("frame released — crop kept", out["released"]["say"])
        self.assertEqual("crops/gone.jpg", out["released"]["frame"])
        self.assertIn("PROVEN 12/12", out["btn"])
        self.assertIn("window._vaultOpenEvidence", out["btn"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a cited frame is released with the rest of its reel",
        "file": "frame_authority.py",
        "find": "    if os.path.basename(frame_path) in set(_cited or ()):\n",
        "replace": "    if False and os.path.basename(frame_path) in set(_cited or ()):\n",
        "matches": 1,
    },
    {
        "why": "a miss is cited, so a frame that did not see the item is kept",
        "file": "vault_evidence.py",
        "find": "        for shot in shots:\n",
        "replace": ("        for shot in [e for row in rows for e in "
                    "(row.get('witnesses') if isinstance(row.get('witnesses'), list) else [])]:\n"),
        "matches": 1,
    },
    {
        "why": "a picture that cannot be served opens blank instead of saying UNKNOWN",
        "file": "bible.html",
        "find": "    if (!look.frame) return { ok: false, frame: null, say: 'picture missing: UNKNOWN', title: 'picture missing: UNKNOWN · ' + title, ids: looks.map(function(k){ return k.frame || null; }) };\n",
        "replace": "    if (!look.frame) return { ok: false, frame: null, say: '', title: '', ids: looks.map(function(k){ return k.frame || null; }) };\n",
        "matches": 1,
    },
    {
        "why": "the tombstone forgets which frames it kept",
        "file": "reel_retention.py",
        "find": "            rec[\"kept\"] = c[\"kept\"]\n",
        "replace": "            rec[\"why\"] = c.get(\"why\")\n",
        "matches": 1,
    },
]
