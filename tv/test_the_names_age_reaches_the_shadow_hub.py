# -*- coding: utf-8 -*-
"""#200 (REG-3036, GrokBot v3836 glass pass, #230 6485132266) - THE NAMES' AGE REACHES THE SHADOW'S HUB, END TO END.

GrokBot: in the ALT shadow's Sessions tab no "names read N min ago" text appeared anywhere. Measured 03:49, read only:
the site's ALT row carried chronicle.rowsAsOf (03:00:26), the Mac's roster cache kept it, and the real join run in node -
_shadowRosterStores -> _shadowMergeStores -> _paintChronicle, on the site's real ALT profile stores and that cached row -
painted "Runewords 0/99 · Sets 4/135 · Uniques 56/403 · names read 51 min ago" into #hd-chron-counts, the FORGE QUESTS
head. That head is `text-transform: uppercase` (.hd-h, inherited by .hd-sub), so on glass and in innerText the clause reads
"NAMES READ ..." - a case-sensitive search for "names read" finds nothing. No code defect was found in the join.

What was missing is a law over the JOIN. REG-2745's law drove the shapers and _chronicleCounts on a hand-built progress;
nothing ran the three steps between the row and the line, so breaking the stamp in _shadowRosterStores, the merge's keep
for a listed lane, or the shadow's read of its own progress would all stay green. This drives them together on the ALT's
shape: a profile snapshot that already holds the names (the merge keeps the row's progress only because the lane is
listed), a snapshot without them, and a row from before REG-2745 (no rowsAsOf: no clause, never a guessed age).

Driven: the seven functions cut out of control_ui.html and run in node over a mock document, with a fixed clock; fixture
row and stores, never his. RED_PROOF below.
"""
import io
import json
import os
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
NODE = shutil.which("node")
with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as _fh:
    UI = _fh.read()

FNS = ["  function _listCount(raw) {", "  function _chronicleCounts(summary, progress, lists) {",
       "  function _paintChronicle(summary) {", "  window._shadowRosterStores = function (row, fleet, owner) {",
       "  window._shadowStoreEmpty = function (raw) {", "  window._shadowBuildsEmpty = function (stores) {",
       "  window._shadowMergeStores = function (snapStores, builtStores) {"]
NOW = 1793236380000
NAMES_AT = NOW - 13 * 60000
OWNER = "Konyo · ALT"


def _cut(sig):
    if UI.count(sig) != 1:
        raise AssertionError("%r occurs %d times - this law cannot see its subject" % (sig, UI.count(sig)))
    i = UI.index(sig)
    depth = 0
    for j in range(UI.index("{", i), len(UI)):
        if UI[j] == "{":
            depth += 1
        elif UI[j] == "}":
            depth -= 1
            if depth == 0:
                return UI[i:j + 1] + (";" if sig.lstrip().startswith("window.") else "")
    raise AssertionError("%r never closed - harness fault, not a pass" % sig)


def _row(rows_as_of=NAMES_AT):
    chron = {"asOf": NOW - 13 * 60000 - 26000,
             "counts": {"sets": {"have": 4, "total": 135}, "uniques": {"have": 56, "total": 403},
                        "runewords": {"have": 0, "total": 99}, "uniquesNamed": 3, "setsNamed": 1},
             "rows": [{"lane": "uniques", "name": "Harlequin Crest"}, {"lane": "uniques", "name": "Arachnid Mesh"},
                      {"lane": "uniques", "name": "Mara's Kaleidoscope"}, {"lane": "sets", "name": "Tal Rasha's Lidless Eye"}]}
    if rows_as_of is not None:
        chron["rowsAsOf"] = rows_as_of
    return {"owner": OWNER, "published": True, "t": NOW - 13 * 60000, "sections": {"chronicle": chron}}


def _snap(with_names=True):
    s = {"d2r_forgeSummary": json.dumps({"grail": {"found": 56, "total": 403}, "sets": {"found": 4, "total": 135},
                                         "chron": {"made": 0, "total": 99}}),
         "d2r_rwMade": "{}", "d2r_charBuilds": "{}"}
    if with_names:
        s["d2r_foundLog"] = json.dumps({"Harlequin Crest": "", "Arachnid Mesh": "", "Mara's Kaleidoscope": ""})
        s["d2r_setPieces"] = json.dumps(["Tal Rasha's Lidless Eye"])
    else:
        s["d2r_foundLog"] = "{}"
        s["d2r_setPieces"] = "[]"
    return s


HARNESS = r"""
const C = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
Date.now = () => C.now;
const out = {};
for (const sc of C.scenes) {
  const el = { textContent: '' };
  const window = {};
  const document = { body: { classList: { contains: (c) => c === 'shadow-hub' } },
                     getElementById: (id) => id === 'hd-chron-counts' ? el : null };
  /* this PC's own board answers too, with a progress of its own: a shadow must never read it */
  const lsHub = (k) => k === 'd2r_shadowProgress'
    ? JSON.stringify({ uniques: { have: 1, total: 403, listed: true, rowsAsOf: C.now - 600 * 60000 } }) : null;
  const paint = new Function('window', 'document', 'lsHub', C.code + '\nreturn _paintChronicle;')(window, document, lsHub);
  const built = window._shadowRosterStores(sc.row, null, sc.row.owner);
  const stores = window._shadowMergeStores(sc.snap, built && built.stores);
  window._tvdShadowSnap = { owner: sc.row.owner, t: 0, stores: stores };
  let summary = null; try { summary = JSON.parse(stores.d2r_forgeSummary); } catch (e) {}
  paint(summary);
  out[sc.name] = { line: el.textContent, progress: stores.d2r_shadowProgress || null };
}
console.log(JSON.stringify(out));
"""


def _drive():
    if not NODE:
        raise AssertionError("node is not on this machine - this law does not skip")
    import tempfile
    d = tempfile.mkdtemp(prefix="names_age_hub_")
    try:
        h, c = os.path.join(d, "h.js"), os.path.join(d, "c.json")
        with io.open(h, "w", encoding="utf-8") as fh:
            fh.write(HARNESS)
        scenes = [{"name": "named", "row": _row(), "snap": _snap(True)},
                  {"name": "unnamed", "row": _row(), "snap": _snap(False)},
                  {"name": "old", "row": _row(None), "snap": _snap(True)}]
        with io.open(c, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"code": "\n".join(_cut(f) for f in FNS), "now": NOW, "scenes": scenes}))
        r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
                           env=dict(os.environ, TZ="UTC"))
    finally:
        shutil.rmtree(d, True)
    if r.returncode != 0:
        raise AssertionError("node failed: %s" % r.stderr[-900:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TheNamesAgeReachesTheShadowHub(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = _drive()

    def test_a_snapshot_that_holds_the_names_still_says_when_they_were_read(self):
        self.assertEqual(self.o["named"]["line"], "Runewords 0/99 · Sets 4/135 · Uniques 56/403 · names read 13 min ago",
                         self.o["named"])

    def test_a_snapshot_without_the_names_says_it_too(self):
        self.assertTrue(self.o["unnamed"]["line"].endswith(" · names read 13 min ago"), self.o["unnamed"])

    def test_a_row_from_before_the_stamp_says_no_age_never_a_guess(self):
        self.assertNotIn("names read", self.o["old"]["line"], self.o["old"])
        self.assertTrue(self.o["old"]["line"].startswith("Runewords 0/99 · Sets 4/135 · Uniques 56/403"), self.o["old"])

    def test_the_clause_rides_in_the_head_that_draws_it_uppercase(self):
        # the FORGE QUESTS head transforms its text: the clause on glass is "NAMES READ ..." - search it case-blind
        head = UI[UI.index('<div class="hd-col" id="hd-forge">'):]
        head = head[:head.index("</div>")]
        self.assertIn('id="hd-chron-counts"', head)
        self.assertIn("text-transform: uppercase", UI[UI.index("  .hd-h { font: var(--fw-semibold)"):][:300])


RED_PROOF = [
    {"why": "REG-3036 - the shadow's row stores never carry when the names were read",
     "file": "tv/control_ui.html",
     "find": "      if (list.length && whole(chron.rowsAsOf, 1)) pair.rowsAsOf = chron.rowsAsOf;\n",
     "replace": "", "matches": 1, "needs": "node"},
    {"why": "REG-3036 - a snapshot that holds the names drops the row's listed progress",
     "file": "tv/control_ui.html",
     "find": "if (window._shadowStoreEmpty(stores[pair[1]]) || row.listed === true) keep[pair[0]] = row;",
     "replace": "if (window._shadowStoreEmpty(stores[pair[1]])) keep[pair[0]] = row;", "matches": 1, "needs": "node"},
    {"why": "REG-3036 - the shadow's hub reads this PC's own progress",
     "file": "tv/control_ui.html",
     "find": "try { progress = JSON.parse((shadow ? readHub('d2r_shadowProgress') : lsHub('d2r_shadowProgress')) || 'null'); }",
     "replace": "try { progress = JSON.parse(lsHub('d2r_shadowProgress') || 'null'); }", "matches": 1, "needs": "node"},
    {"why": "REG-3036 - a row with no stamp gets an age anyway",
     "file": "tv/control_ui.html",
     "find": "      if (r && r.listed === true && whole(r.rowsAsOf, 1) && r.rowsAsOf > namesAt) namesAt = r.rowsAsOf;\n",
     "replace": "      if (r && r.listed === true) namesAt = Math.max(namesAt, whole(r.rowsAsOf, 1) ? r.rowsAsOf : Date.now() - 60000);\n",
     "matches": 1, "needs": "node"},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
