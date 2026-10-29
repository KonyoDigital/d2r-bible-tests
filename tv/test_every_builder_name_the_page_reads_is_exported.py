# -*- coding: utf-8 -*-
"""#83 (REG-3093, GrokBot 06:36) - EVERY BUILDER FUNCTION THE PAGE READS OFF window IS PUT ON window.

GrokBot on the D2JSP desk: every filed card said "Base not recorded", even for fixed-base uniques - Hellfire Torch is a Large
Charm, Gheed's Fortune a Grand Charm - so the draft post carried no base. catalogBase() asks window._cbItemsNamed for the
item's database row; _cbItemsNamed is a function of the character builder and was never put on window, so the fallback
returned '' for every name. Swept: one more name the page reads off window and nobody exported - window._cbBase, read by
_mpIsGenericCopy ("a magic or rare still named its base's own name"), which therefore only ever matched the b: id path.
The other 152 window._cb* names the page calls have their export. Both are now exported beside their definitions, the way
window._cbDb = _cbDb sits beside _cbDb.

Driven: (1) the sweep, over bible.html's code with its comments stripped - every window._cb* name read has an export;
(2) the real catalogBase and _mpIsGenericCopy cut out of bible.html and run in node over the real _cbItemsNamed and _cbBase
plus exactly the export statements the page carries, against a stand-in item database. RED_PROOF below.
"""
import io
import json
import os
import re
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
with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as _fh:
    PAGE = _fh.read()


def _code(src):
    """bible.html's script, comments out: bounded block comments (an unbounded one ran a third of the file away once) and
    // line comments that are not a URL's ://."""
    src = re.sub(r"/\*.{0,4000}?\*/", " ", src, flags=re.S)
    return re.sub(r"(?<![:'\"\\])//[^\n]*", "", src)


def _cut(sig):
    if PAGE.count(sig) != 1:
        raise AssertionError("%r occurs %d times - this law cannot see its subject" % (sig, PAGE.count(sig)))
    i = PAGE.index(sig)
    depth = 0
    for j in range(PAGE.index("{", i), len(PAGE)):
        if PAGE[j] == "{":
            depth += 1
        elif PAGE[j] == "}":
            depth -= 1
            if depth == 0:
                return PAGE[i:j + 1]
    raise AssertionError("%r never closed - harness fault, not a pass" % sig)


def _exports(name):
    """Every statement in the page's code that puts `name` on window - run as the page runs them, or not at all."""
    return re.findall(r"window\.%s\s*=\s*%s\s*;" % (name, name), _code(PAGE))


class EveryBuilderNameThePageReadsIsExported(unittest.TestCase):

    def test_every_window_cb_name_read_has_an_export(self):
        code = _code(PAGE)
        read = set(re.findall(r"window\.(_cb[A-Za-z0-9_]+)", code))
        put = set(re.findall(r"window\.(_cb[A-Za-z0-9_]+)\s*=(?!=)", code))
        for m in re.finditer(r"Object\.assign\(window,\s*\{([^}]*)\}", code):
            put |= set(re.findall(r"(_cb[A-Za-z0-9_]+)\s*:", m.group(1)))
        self.assertGreater(len(read), 100, "premise: the sweep read %d window._cb* names - it is blind" % len(read))
        self.assertIn("_cbItemsNamed", read, "premise: catalogBase no longer reads window._cbItemsNamed")
        self.assertEqual(sorted(read - put), [], "the page reads these off window and nothing puts them there")


HARNESS = r"""
const C = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
const window = {};
const DB = { it: [['u1', 'Hellfire Torch', 'u', 'cm2'], ['u2', "Gheed's Fortune", 'u', 'cm3'],
                  ['b1', 'Grand Charm', 'b', 'cm3']],
             b: { cm2: ['Large Charm'], cm3: ['Grand Charm'] } };
function _cbDb() { return DB; }
window._cbDb = _cbDb;
const run = new Function('window', '_cbDb', C.code + '\nreturn { catalogBase: catalogBase, generic: _mpIsGenericCopy };');
const f = run(window, _cbDb);
console.log(JSON.stringify({
  torch: f.catalogBase('Hellfire Torch'), gheed: f.catalogBase("Gheed's Fortune"), plain: f.catalogBase('Grand Charm'),
  genericBare: f.generic({ q: 'm', base: 'cm3', name: 'Grand Charm' }),
  genericNamed: f.generic({ q: 'm', base: 'cm3', name: 'Grand Charm of Vita' })
}));
"""


class TheDeskAndThePlannerReadTheBuildersRows(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not NODE:
            raise AssertionError("node is not on this machine - this law does not skip")
        code = "\n".join([_cut("  function _cbItemsNamed(name){"),
                          _cut("  function _cbBase(code){"),
                          _cut("  function catalogBase(name){"),
                          _cut("  function _mpIsGenericCopy(e){")]
                         + _exports("_cbItemsNamed") + _exports("_cbBase"))
        import tempfile
        d = tempfile.mkdtemp(prefix="cb_exports_")
        try:
            h, c = os.path.join(d, "h.js"), os.path.join(d, "c.json")
            with io.open(h, "w", encoding="utf-8") as fh:
                fh.write(HARNESS)
            with io.open(c, "w", encoding="utf-8") as fh:
                fh.write(json.dumps({"code": code}))
            r = subprocess.run([NODE, h, c], capture_output=True, text=True, timeout=60)
        finally:
            shutil.rmtree(d, True)
        if r.returncode != 0:
            raise AssertionError("node failed: %s" % r.stderr[-900:])
        cls.o = json.loads(r.stdout.strip().splitlines()[-1])

    def test_a_fixed_base_unique_names_its_base(self):
        self.assertEqual((self.o["torch"], self.o["gheed"]), ("Large Charm", "Grand Charm"),
                         "the D2JSP card's base fallback found no base: %r" % self.o)

    def test_a_base_is_not_named_as_its_own_base(self):
        self.assertEqual(self.o["plain"], "")

    def test_a_magic_item_still_named_its_base_is_a_generic_copy(self):
        self.assertIs(self.o["genericBare"], True, "a magic Grand Charm named 'Grand Charm' was not read as a generic copy")
        self.assertIs(self.o["genericNamed"], False)


RED_PROOF = [
    {"why": "REG-3093 - _cbItemsNamed is not put on window again (every D2JSP card: Base not recorded)",
     "file": "bible.html",
     "find": "  window._cbItemsNamed = _cbItemsNamed;\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-3093 - _cbBase is not put on window again (a magic item named its base is never a generic copy)",
     "file": "bible.html",
     "find": "  window._cbBase = _cbBase;\n",
     "replace": "",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
