# -*- coding: utf-8 -*-
"""v2738 — HIS EXPORT CARRIED OTHER PEOPLE'S WORLDS, AND A GUEST'S OWN EXPORT COULD NOT COME HOME.

Konyo: *"and for dean same logic make sure his is relative individually saving his consoles data to
his own ledgers and repair and everything all related to separately and individually"*.

`_collectProgress` computes a BARE name for every raw key and exports it only when
`LSR.key(bare) === rk` — "the active account's view only; the other namespaces never leave", in its
own comment. v684 taught it the MACHINE fork (`L·` `W·` `WL·`). v1499 then added the INSTALL fork
(`I·<id8>·` for a guest world, `IL·<id8>·` for its ladder) and **this line was never swept with
it** — `_D2R_PFX` is built at bible.html:3930 as `'I·' + install8 + '·'`, so the prefix is
VARIABLE-LENGTH and no fixed slice removes it. bible.html:4263 already handled all five prefixes,
so the knowledge was in the file and simply not on that line.
[[sweep-dont-ask]] [[feedback-comments-vs-code]]

MEASURED on his real backup, and it was wrong in BOTH directions:
  OWNER export  carried `I·77f64154·d2r_foundLog` and `I·c5c2c92d·d2r_foundLog` — two other
                worlds' chronicles inside his own snapshot.
  GUEST export  a guest's own rows came out under `I·<id8>·d2r_foundLog` instead of the bare name.
                `_applyProgress` restores through `LS.setItem`, which re-applies the ACTIVE world's
                prefix, so a namespaced key can never route home: Dean restoring into a reinstalled
                browser (new install id) would get NOTHING back — and his file also carried a second
                guest's chronicle.

⚠⚠ THIS GATE RUNS THE REAL JAVASCRIPT, IT DOES NOT GREP FOR IT. The regions are sliced out of
bible.html by anchor and executed in node against a synthetic store. A source grep would pin the
spelling of a fix; this pins the BEHAVIOUR, which is the thing that was wrong.
⚠ NO NODE = SKIP WITH A REASON, NEVER A PASS. [[regression-guard]]
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
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")


def _slice(src, start, end, inclusive=True):
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    if j < 0:
        return None
    return src[i:j + (len(end) if inclusive else 0)]


def _regions():
    """The four real regions this behaviour lives in. -> dict or None"""
    src = io.open(BIBLE, encoding="utf-8").read()
    out = {
        # ⚠ BOTH ENDS ANCHORED, never a slice to the first newline — `_LP_FORKED` spans several
        # lines and cutting at "\n" produced a truncated literal that node refused with a
        # SyntaxError pointing at the NEXT statement. [[source-reading-guard]]
        "lp": _slice(src, "window._LP_FORKED = new Set(", "window._WP_FORKED", inclusive=False),
        "wp": _slice(src, "window._WP_FORKED = new Set(", "\ntry {", inclusive=False),
        "lsr": _slice(src, "window.LSR = (function(){", "\n})();"),
        "collect": _slice(src, "function _collectProgress(){", "\nfunction _progressSnapshot()",
                          inclusive=False),
    }
    return None if any(v is None for v in out.values()) else out


HARNESS = r"""
const RAW_STORE = %(store)s;
const RAW = {
  get length(){ return Object.keys(RAW_STORE).length; },
  key: function(i){ return Object.keys(RAW_STORE)[i]; },
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(RAW_STORE,k) ? RAW_STORE[k] : null; },
  setItem: function(k,v){ RAW_STORE[k] = String(v); },
  removeItem: function(k){ delete RAW_STORE[k]; }
};
globalThis.window = globalThis;
window.localStorage = RAW;
window._D2R_OWNER   = %(owner)s;
window._D2R_INSTALL = "%(install)s";
window.D2R_PROFILE  = "main";
window._D2R_PFX  = window._D2R_OWNER ? '' : ('I·'  + String(window._D2R_INSTALL).slice(0,8) + '·');
window._D2R_LPFX = window._D2R_OWNER ? 'L·' : ('IL·' + String(window._D2R_INSTALL).slice(0,8) + '·');
%(lp)s
%(wp)s
%(lsr)s
%(collect)s
console.log(JSON.stringify(_collectProgress()));
"""


def _run(owner, install, store):
    r = _regions()
    if r is None:
        return None, "the regions could not be sliced out of bible.html"
    js = HARNESS % {"store": json.dumps(store, ensure_ascii=False),
                    "owner": "true" if owner else "false", "install": install,
                    "lp": r["lp"], "wp": r["wp"], "lsr": r["lsr"], "collect": r["collect"]}
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.cjs")
    io.open(p, "w", encoding="utf-8").write(js)
    try:
        out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=30)
        return json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1]), ""
    except subprocess.CalledProcessError as e:
        return None, "node refused: %s" % e.output.decode("utf-8", "replace")[-400:]
    finally:
        shutil.rmtree(d, ignore_errors=True)


#: two guest worlds and an owner world in one store, which is the shape his real store is in
STORE = {
    "d2r_foundLog": '{"Owner Item":"d"}',
    "d2r_setPieces": '["Owner Piece"]',
    "d2r_activeTab": '"uniques"',
    "d2r_installId": '"77f64154aaaa"',
    "I·77f64154·d2r_foundLog": '{"Guest A Item":"d"}',
    "I·77f64154·d2r_craftMade": '{"Guest A Craft":1}',
    "I·c5c2c92d·d2r_foundLog": '{"Guest B Item":"d"}',
}


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — this gate runs REAL bible.html javascript, and without an "
                 "engine it is a SKIP with a declared reason, never a pass")
class TheExportCarriesExactlyOneWorld(unittest.TestCase):

    def test_the_regions_can_be_sliced_AT_ALL(self):
        """⚠ A gate that cannot find its subject passes having examined nothing."""
        r = _regions()
        self.assertIsNotNone(r, "bible.html no longer yields _LP_FORKED / _WP_FORKED / LSR / "
                                "_collectProgress by anchor — fix the slicing before trusting green")
        self.assertIn("_D2R_PFX", r["lsr"], "the sliced LSR block does not contain the guest prefix")
        self.assertIn("RAW.key(i)", r["collect"], "the sliced exporter does not walk the raw store")

    # ── ⚠⚠ THE OWNER DIRECTION ────────────────────────────────────────────────────────────────
    def test_an_OWNER_export_carries_no_guest_world(self):
        got, why = _run(True, "77f64154aaaa", STORE)
        self.assertIsNotNone(got, why)
        leaked = sorted(k for k in got if k.startswith(("I·", "IL·", "W·", "L·")))
        self.assertEqual(
            [], leaked,
            "his snapshot carried %s — other people's chronicles inside his own export. The line's "
            "own comment says 'the other namespaces never leave'." % leaked)
        self.assertIn("d2r_foundLog", got, "his own chronicle is missing from his own export")
        self.assertEqual('{"Owner Item":"d"}', got["d2r_foundLog"],
                         "the exported chronicle is not the OWNER's rows")

    # ── ⚠⚠ THE GUEST DIRECTION — the half that decides whether Dean can ever restore ──────────
    def test_a_GUEST_exports_its_own_rows_under_BARE_names(self):
        got, why = _run(False, "77f64154aaaa", STORE)
        self.assertIsNotNone(got, why)
        self.assertIn(
            "d2r_foundLog", got,
            "a guest's chronicle did not export under its BARE name. _applyProgress restores "
            "through LS.setItem, which re-applies the ACTIVE world's prefix — so a namespaced key "
            "can never route home, and Dean restoring into a reinstalled browser (new install id) "
            "would get nothing back.")
        self.assertEqual('{"Guest A Item":"d"}', got["d2r_foundLog"],
                         "the guest exported somebody else's chronicle under his own bare name")

    def test_a_GUEST_export_carries_no_OTHER_guest(self):
        got, why = _run(False, "77f64154aaaa", STORE)
        self.assertIsNotNone(got, why)
        for k, v in got.items():
            self.assertNotIn("Guest B", str(v),
                             "guest A's export carried guest B's rows under %r" % k)
        leaked = sorted(k for k in got if k.startswith(("I·", "IL·")))
        self.assertEqual([], leaked, "namespaced keys leaked into a guest export: %s" % leaked)

    # ── the property v1499 added, which must survive the fix ──────────────────────────────────
    def test_the_identity_pointers_never_travel(self):
        """v1499: importing a MacBook backup onto another PC would otherwise hand that browser his
        claim, and importing an older snapshot onto his own could REVOKE it."""
        for owner in (True, False):
            got, why = _run(owner, "77f64154aaaa", STORE)
            self.assertIsNotNone(got, why)
            self.assertNotIn("d2r_installId", got,
                             "an identity pointer travelled in a %s export"
                             % ("owner" if owner else "guest"))

    # ── ⚠⚠ THE SIBLING — THE HALF THAT WRITES ─────────────────────────────────────────────────
    def test_the_RESTORE_side_refuses_a_guest_world_too(self):
        """v636 refused `L·`, v684 added `W·`, and v1499's install fork was swept into NEITHER
        line. Every snapshot taken before v2738 can carry namespaced guest keys — his real one
        carried two worlds' — and `LS.setItem('I·<id8>·d2r_foundLog', …)` is left untouched by
        LSR.key (fork sets hold BARE names), so it lands as a RAW write into that guest's world.

        ⚠ FIXING THE EXPORT ALONE DOES NOT CLOSE THIS: the old files already exist on his disk.
        [[sweep-dont-ask]]
        """
        src = io.open(BIBLE, encoding="utf-8").read()
        blk = _slice(src, "function _applyProgress(", "\n}", inclusive=False)
        self.assertIsNotNone(blk, "could not read _applyProgress")
        guard = [ln for ln in blk.splitlines() if "keys.forEach" in ln]
        self.assertTrue(guard, "the restore guard line is gone")
        for pfx in ("'L\u00b7'", "'W\u00b7'", "'I\u00b7'", "'IL\u00b7'"):
            self.assertIn(pfx, guard[0],
                          "the restore does not refuse %s keys, so an old snapshot carrying them "
                          "would be written straight into another world" % pfx)

    def test_UI_state_still_travels_in_both_worlds(self):
        """Keys in no fork set are bare in every world, so every world looks identical and bare-key
        presence can never be read as ownership. The fix must not narrow that."""
        for owner in (True, False):
            got, why = _run(owner, "77f64154aaaa", STORE)
            self.assertIsNotNone(got, why)
            self.assertIn("d2r_activeTab", got,
                          "unforked UI state stopped exporting in the %s world"
                          % ("owner" if owner else "guest"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
