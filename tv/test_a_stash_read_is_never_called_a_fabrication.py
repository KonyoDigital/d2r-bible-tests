# -*- coding: utf-8 -*-
"""REG-1657 — A STASH READ IS NEVER CALLED A FABRICATION FOR WHAT THE BAG BESIDE IT HOLDS.

The vault's free cross-check counts occupied cells with vault_corpus.inventory_lattice - which crops the player's
INVENTORY - and compares them with the names a paid read returned. But the vault reads STASH panels. MEASURED
2026-10-01 across every surveyed reel on his Mac: panel kinds read = stash 2002 · shared 407 · personal 121 ·
materials 41 · runes 12 · gems 4 · inventory 0. Every comparison was between two different panels. While the lattice
was blind (REG-1648) it never ran; working again, reel 82142 - an EMPTY bag beside a stash tooltip naming one real
item - would have shown "the read named 1 item(s) but only 0 square(s) are filled, so at least one name did not come
from this picture" on his board: a fabrication claim about a correct read.

  · DRIVEN: cross_panel_verdict - an over-read on any panel but the inventory (or a panel nobody can tell) is
    "other-panel"; an inventory over-read stays an over-read; agree and under-read are untouched.
  · DRIVEN: "other-panel" is NOT settled - vault_seal_is_definitive refuses it, so no seal loosens and the footage
    stays readable - and why_not_definitive says it as what it is, never "named MORE than the panel can hold".
  · The sweep asks it at the one place a verdict is made, after reconcile_verdict and before the over-read list.

REG-1659 — the same two panels, on the board. A frame whose read named nothing still had its BAG counted, and the
row was named by the screen: "stash · <frame> - N square(s) are visibly full and the read named none of them ... Film
that tab once with the tooltip up". With the lattice re-lit (REG-1648) every such stash frame would ask him to film a
stash tab for squares that are his inventory.
  · The sweep's glimpse row carries the panel that was COUNTED (read from its code: the sweep runs paid reads).
  · DRIVEN in node, the real page code cut by its markers - the helper AND the loop that files it: the row is named
    "your inventory · <frame>", never by the screen; an older payload with no panel is the inventory too (every row
    ever came from that one crop); it never says "the read named none of them" or "Film that tab".
No node on this PC = the page half SKIPS with its reason; a skip is not a pass.

REG-1889 — THE STASH TAB'S OWN GRID (the v3540 cross-family look, finding 1). REG-1657 stopped the bag ACCUSING a
stash read, and said what it left: an agree or an under-read on a stash read still settled on a coincidence with the
bag. vault_corpus.stash_lattice / stash_occupancy now count the stash tab's own 10x10 cells - the measured box, and the
frame's own seams as lines along it, no fitted pitch - and refuse a fixed-slot tab rather than call it 100 full cells.
  · DRIVEN on drawn stash panels at all three of his capture sizes: every cell counted exactly, a dark navy cell is
    still a taken one, a stone panel with no seams and a frame with no panel are refused.
  · DRIVEN on his own frames where they are on this PC (each one counted by eye on 2026-10-07): his personal tab 54,
    his empty shared page 0, his materials tab refused. Absent = SKIP with the reason, never a pass.
  · DRIVEN: _own_panel_cells counts a stash, shared or personal read on the stash grid and falls back to the bag -
    saying so in `counted` - when that grid is not on the frame; cross_panel_verdict keeps an over-read counted on
    the panel the read looked at.
  · The sweep asks _own_panel_cells and hands `counted` to cross_panel_verdict.
RED_PROOF below. [[unknown-stays-unknown]] [[feedback-contradiction-is-the-finding]] [[label-outlived-referent]]
"""
import ast
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()
import fixture_ledgers as _fx_ledgers  # noqa: E402
_fx_ledgers.redirect()

import control_app as ca  # noqa: E402


class TheVerdictKnowsWhichPanelWasCounted(unittest.TestCase):

    def test_a_stash_family_over_read_is_other_panel(self):
        for surface in ("stash", "shared", "personal", "materials", "runes", "gems", "Stash ", None, ""):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface), "other-panel",
                             "a %r read was called a fabrication for what the bag holds" % (surface,))

    def test_an_inventory_over_read_is_still_an_over_read(self):
        for surface in ("inventory", "Inventory", " inventory "):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface), "over-read",
                             "the one real fabrication signal was silenced")

    def test_the_other_verdicts_are_untouched(self):
        for v in ("agree", "under-read"):
            for surface in ("stash", "inventory", None):
                self.assertEqual(ca.cross_panel_verdict(v, surface), v)


class TheVerdictKnowsWhetherTheStashWasCounted(unittest.TestCase):
    """REG-1889 — counted on the stash tab's own grid, an over-read is about the panel the read looked at."""

    def test_a_stash_tab_over_read_counted_on_its_own_grid_stays_an_over_read(self):
        for surface in ("stash", "shared", "Personal "):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface, "stash"), "over-read",
                             "a %r read counted on its own grid lost the one fabrication signal" % surface)

    def test_a_fixed_slot_tab_is_never_judged_by_the_stash_grid(self):
        for surface in ("materials", "runes", "gems", "inventory", None):
            self.assertEqual(ca.cross_panel_verdict("over-read", surface, "stash"), "other-panel")

    def test_a_stash_read_counted_on_the_bag_is_still_other_panel(self):
        self.assertEqual(ca.cross_panel_verdict("over-read", "stash", "inventory"), "other-panel")
        self.assertEqual(ca.cross_panel_verdict("over-read", "stash"), "other-panel")


class _FakeCorpus(object):
    def __init__(self, stash=None, lattice=None, inventory=None):
        self.asked = []
        self._stash, self._lattice, self._inv = stash, lattice, inventory

    def stash_occupancy(self, p):
        self.asked.append("stash")
        return self._stash or {"ok": False, "why": "no stash grid"}

    def inventory_lattice(self, p):
        self.asked.append("lattice")
        return self._lattice or {"ok": False, "why": "no bag"}

    def inventory_occupancy(self, p, lat):
        self.asked.append("inventory")
        return self._inv or {"ok": False, "why": "no bag"}


class TheReadIsCountedOnThePanelItLookedAt(unittest.TestCase):
    """REG-1889 — _own_panel_cells: the stash grid for a stash-tab read, the bag (said so) otherwise."""
    STASH = {"ok": True, "occupied": 0, "free": 100}
    BAG = {"ok": True, "occupied": 14, "free": 26}

    def test_a_stash_tab_read_is_counted_on_the_stash_grid(self):
        for surface in ("stash", "shared", "personal"):
            vc = _FakeCorpus(stash=self.STASH, lattice={"ok": True}, inventory=self.BAG)
            got, counted = ca._own_panel_cells(vc, "f.jpg", surface)
            self.assertEqual(counted, "stash", surface)
            self.assertEqual(got["occupied"], 0, "an empty stash page was counted as the bag's 14")
            self.assertEqual(vc.asked, ["stash"], "the bag was counted beside a stash grid that read")

    def test_a_stash_tab_whose_grid_is_not_on_the_frame_falls_back_to_the_bag_and_says_so(self):
        vc = _FakeCorpus(stash=None, lattice={"ok": True}, inventory=self.BAG)
        got, counted = ca._own_panel_cells(vc, "f.jpg", "stash")
        self.assertEqual(counted, "inventory")
        self.assertEqual(got["occupied"], 14)

    def test_a_fixed_slot_tab_never_asks_the_stash_grid(self):
        for surface in ("materials", "runes", "gems", "inventory", None):
            vc = _FakeCorpus(stash=self.STASH, lattice={"ok": True}, inventory=self.BAG)
            got, counted = ca._own_panel_cells(vc, "f.jpg", surface)
            self.assertEqual(counted, "inventory", surface)
            self.assertNotIn("stash", vc.asked, "a %r read was counted on the stash grid" % (surface,))

    def test_nothing_that_reads_is_nothing_counted(self):
        self.assertEqual(ca._own_panel_cells(_FakeCorpus(), "f.jpg", "stash"), (None, None))


def _numpy_or_skip(case):
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except Exception as e:
        case.skipTest("UNMEASURED here, not passing: the pixel lane needs numpy and PIL (%s)" % e)


def _draw(path, W, H, filled, dark=(), stone=False, panel=True):
    """A frame with a stash panel drawn where slot_identity measured it. `filled` cells carry an item (navy backing
    and a bright blob of art), `dark` cells a navy backing darker than any empty cell's grey, the rest are empty."""
    import numpy as np
    from PIL import Image
    import slot_identity as si
    A = np.full((H, W, 3), 35, dtype=np.uint8)
    if panel:
        x, y, w, h = si.panel_box_for(W, H, container="stash")[0]
        pc, pr = w / 10.0, h / 10.0
        if stone:
            rng = np.random.RandomState(5)
            A[int(y):int(y + h), int(x):int(x + w)] = rng.randint(40, 90, (int(y + h) - int(y), int(x + w) - int(x), 1))
        else:
            for j in range(10):
                for i in range(10):
                    c0, c1, r0, r1 = int(x + i * pc), int(x + (i + 1) * pc), int(y + j * pr), int(y + (j + 1) * pr)
                    if (i, j) in filled:
                        A[r0:r1, c0:c1] = (20, 22, 60)
                        m = int(pc * 0.3)
                        A[r0 + m:r1 - m, c0 + m:c1 - m] = (190, 150, 90)
                    elif (i, j) in dark:
                        A[r0:r1, c0:c1] = (10, 12, 42)
                    else:
                        A[r0:r1, c0:c1] = (18, 19, 19)
            t = max(1, int(round(2 * H / 1912.0)))
            for i in range(11):
                X = int(round(x + i * pc))
                A[int(y):int(y + h), max(0, X - t // 2):X + t - t // 2] = (75, 72, 66)
            for j in range(11):
                Y = int(round(y + j * pr))
                A[max(0, Y - t // 2):Y + t - t // 2, int(x):int(x + w)] = (75, 72, 66)
    Image.fromarray(A).save(path, quality=95)


class TheStashTabIsCountedOnItsOwnGrid(unittest.TestCase):
    """REG-1889 — the stash tab's own 10x10 cells, at every size his Mac has captured."""
    SIZES = ((2940, 1912), (1440, 936), (1440, 904))
    FILLED = {(0, 0), (1, 0), (0, 1), (1, 1), (5, 3), (9, 9), (4, 6), (4, 7), (4, 8)}

    def setUp(self):
        _numpy_or_skip(self)
        self.tmp = tempfile.mkdtemp(prefix="stash1889_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        import vault_corpus as vc
        self.vc = vc

    def _frame(self, name, W, H, **kw):
        p = os.path.join(self.tmp, "%s_%dx%d.jpg" % (name, W, H))
        _draw(p, W, H, **kw)
        return p

    def test_every_cell_is_counted_at_every_capture_size(self):
        for W, H in self.SIZES:
            with self.subTest(size="%dx%d" % (W, H)):
                got = self.vc.stash_occupancy(self._frame("grid", W, H, filled=self.FILLED))
                self.assertTrue(got.get("ok"), got)
                self.assertEqual(got["panel"], "stash")
                self.assertEqual((got["occupied"], got["free"]), (len(self.FILLED), 100 - len(self.FILLED)))
                taken = {(i, j) for j, line in enumerate(got["grid"]) for i, t in enumerate(line) if t}
                self.assertEqual(taken, self.FILLED, "the right count from the wrong cells is not a count")

    def test_an_empty_stash_page_is_zero_not_refused(self):
        for W, H in self.SIZES:
            with self.subTest(size="%dx%d" % (W, H)):
                got = self.vc.stash_occupancy(self._frame("empty", W, H, filled=set()))
                self.assertTrue(got.get("ok"), got)
                self.assertEqual(got["occupied"], 0)

    def test_a_dark_navy_cell_is_still_a_taken_one(self):
        """An item's navy backing can read darker than an empty cell's grey; its COLOUR is what separates them."""
        got = self.vc.stash_occupancy(self._frame("dark", 1440, 936, filled=set(), dark={(3, 3), (6, 2)}))
        self.assertTrue(got.get("ok"), got)
        self.assertEqual(got["occupied"], 2, "a navy cell with no art was counted as an empty one")

    def test_a_panel_with_no_seams_is_refused_not_counted_full(self):
        for W, H in self.SIZES:
            with self.subTest(size="%dx%d" % (W, H)):
                got = self.vc.stash_occupancy(self._frame("stone", W, H, filled=set(), stone=True))
                self.assertFalse(got.get("ok"), "a fixed-slot tab was counted as %r full cells" % got.get("occupied"))
                self.assertIn("10x10 grid is not on this frame", got.get("why") or "")

    def test_a_frame_with_no_panel_is_refused(self):
        got = self.vc.stash_occupancy(self._frame("none", 1440, 936, filled=set(), panel=False))
        self.assertFalse(got.get("ok"), got)


class HisOwnFramesAreCountedAsHeCountsThem(unittest.TestCase):
    """REG-1889 — his frames, each counted by eye on 2026-10-07. Not on this PC = SKIP with the reason.
    Only BLESSED fixture reels may be named here (REG-1027: a reel id in test code makes retention hold that footage);
    the 1440x936 size is covered by the drawn panels above, not by naming another of his reels."""
    HIST = os.path.join(HERE, "frames", "hist")
    CASES = (
        ("reel_s_1784984019250_95276/f_1784984235886.jpg", 54, "his personal tab, 2940x1912"),
        ("reel_s_1788190210097_78660/f_1788190274830.jpg", None, "his MATERIALS tab - fixed slots, refused"),
    )

    def test_his_frames(self):
        _numpy_or_skip(self)
        import vault_corpus as vc
        seen = 0
        for rel, want, what in self.CASES:
            p = os.path.join(self.HIST, rel)
            if not os.path.isfile(p):
                continue
            seen += 1
            with self.subTest(what):
                got = vc.stash_occupancy(p)
                if want is None:
                    self.assertFalse(got.get("ok"), "%s was counted: %r" % (what, got.get("occupied")))
                else:
                    self.assertTrue(got.get("ok"), "%s: %r" % (what, got.get("why")))
                    self.assertEqual(got["occupied"], want, what)
        if not seen:
            self.skipTest("UNMEASURED here, not passing: none of his counted frames is on this PC")


class OtherPanelIsSaidButNotSettled(unittest.TestCase):
    REC = [{"frame": "f_1.jpg", "surface": "stash", "named": 1, "occupied": 0, "verdict": "other-panel"}]

    def test_it_does_not_loosen_a_seal(self):
        self.assertFalse(ca.vault_seal_is_definitive(1, self.REC, [], []),
                         "a cross-panel read was taken as settled - a seal loosened on a comparison of two panels")

    def test_it_is_said_as_what_it_is(self):
        why = " · ".join(ca.why_not_definitive(1, self.REC, [], []))
        self.assertIn("a panel the pixel layer does not count (stash)", why)
        self.assertNotIn("named MORE than the panel can hold", why, "the explanation accuses: %r" % why)

    def test_the_explanation_agrees_with_the_verdict(self):
        for rec in (self.REC, [dict(self.REC[0], verdict="agree")], [dict(self.REC[0], verdict="under-read")]):
            definitive = ca.vault_seal_is_definitive(1, rec, [], [])
            why = ca.why_not_definitive(1, rec, [], [])
            self.assertEqual(definitive, not why, "verdict %s and explanation %r disagree for %r"
                             % (definitive, why, rec[0]["verdict"]))


class TheSweepAsksIt(unittest.TestCase):
    """_vault_sweep_run is ~600 lines and runs paid reads; the join is read from its code, in order."""

    def test_after_the_reconcile_and_before_the_over_read_list(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        calls = {}
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) \
                    and isinstance(node.value.func, ast.Name) and node.value.func.id in ("reconcile_verdict",
                                                                                       "cross_panel_verdict"):
                calls.setdefault(node.value.func.id, []).append(node.lineno)
            if isinstance(node, ast.If) and isinstance(node.test, ast.Compare) \
                    and isinstance(node.test.left, ast.Name) and node.test.left.id == "_verdict":
                calls.setdefault("over-read-check", []).append(node.lineno)
        self.assertEqual(len(calls.get("cross_panel_verdict", [])), 1, "the sweep never asks which panel was counted")
        self.assertLess(min(calls["reconcile_verdict"]), calls["cross_panel_verdict"][0])
        self.assertLess(calls["cross_panel_verdict"][0], min(calls["over-read-check"]),
                        "the over-read list is filled before the panel is asked about")

    def test_it_counts_the_panel_the_read_looked_at_and_says_which(self):
        """REG-1889 — the cells come from _own_panel_cells, and the panel they came from reaches the verdict."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        own = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "_own_panel_cells"]
        self.assertEqual(len(own), 1, "the sweep does not ask which panel's cells to count")
        cpv = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
               and n.func.id == "cross_panel_verdict"]
        self.assertEqual(len(cpv), 1)
        self.assertEqual(len(cpv[0].args), 3, "the verdict is not told which panel was counted")
        self.assertTrue(isinstance(cpv[0].args[2], ast.Name) and cpv[0].args[2].id == "_counted")
        rv = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
              and n.func.id == "reconcile_verdict"]
        self.assertLess(own[0].lineno, min(r.lineno for r in rv), "the count is taken after the verdict")


class TheIncompleteReasonIsThePureFunctions(unittest.TestCase):
    """REG-1661 — the sweep's INCOMPLETE reason (what a retirement quotes) is why_not_definitive's own words."""

    def test_the_reason_a_retirement_quotes_comes_from_the_pure_function(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        assigns = [n for n in ast.walk(fn) if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_whynot" for t in n.targets)]
        self.assertEqual(len(assigns), 1, "PREMISE: the sweep builds its incomplete reason once")
        # the reason quotes `_nd` - the ONE answer the sweep got from the pure function (test_a_read_reel_says_why_
        # it_cannot_seal pins that it is asked once) - and never re-derives a condition by hand
        uses = [n for n in ast.walk(assigns[0].value) if isinstance(n, ast.Name) and n.id == "_nd"]
        self.assertTrue(uses, "the incomplete reason re-derives the conditions instead of quoting the pure "
                              "function - an other-panel read retires as '0 of 28 never cross-checked'")
        nd = [n for n in ast.walk(fn) if isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "_nd" for t in n.targets)]
        self.assertEqual(len(nd), 1, "PREMISE: the sweep binds the pure function's answer once")
        self.assertTrue(isinstance(nd[0].value, ast.Call) and isinstance(nd[0].value.func, ast.Name)
                        and nd[0].value.func.id == "why_not_definitive", "`_nd` is not the pure function's answer")
        text = ast.get_source_segment(io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read(),
                                      assigns[0]) or ""
        self.assertNotIn("were never cross-checked", text, "a hand-written copy of a condition is back")

    def test_the_other_panel_case_says_what_it_is(self):
        rec = [dict(frame="f_%d.jpg" % i, surface="stash", named=0, occupied=3, verdict="under-read") for i in range(27)]
        rec.append(dict(frame="f_x.jpg", surface="stash", named=1, occupied=0, verdict="other-panel"))
        why = "; ".join(ca.why_not_definitive(28, rec, [], []))
        self.assertIn("a panel the pixel layer does not count (stash)", why)
        self.assertNotIn("never cross-checked", why)


class TheGlimpseNamesThePanelItCounted(unittest.TestCase):
    """REG-1659 — the board's glimpse row says where the full squares ARE."""

    def test_the_sweep_records_the_counted_panel(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run"), None)
        self.assertIsNotNone(fn, "_vault_sweep_run is gone - re-point this law")
        rows = [c.args[0] for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                and c.func.attr == "append" and isinstance(c.func.value, ast.Name) and c.func.value.id == "_glimpsed"
                and c.args and isinstance(c.args[0], ast.Dict)]
        self.assertEqual(len(rows), 1, "PREMISE: the sweep builds exactly one glimpse row")
        got = {k.value: v for k, v in zip(rows[0].keys, rows[0].values) if isinstance(k, ast.Constant)}
        self.assertIn("panel", got, "the glimpse row does not say which panel its squares were counted on")
        self.assertTrue(isinstance(got["panel"], ast.Name) and got["panel"].id == "_LATTICE_PANEL",
                        "the glimpse row's panel is not the lattice's own panel")

    NODE = shutil.which("node")

    def _drive(self, glimpsed):
        if not self.NODE:
            self.skipTest("no node on this PC - the page half is UNMEASURED here, not passing")
        with io.open(os.path.join(os.path.dirname(HERE), "bible.html"), encoding="utf-8") as fh:
            src = fh.read()
        a = src.index("/* \u27e6GLIMPSE ROW BEGIN\u27e7 */")
        b = src.index("/* \u27e6GLIMPSE ROW END\u27e7 */", a)
        script = ("var recs = [];\nvar _rec = function(name, status, why, frame){ recs.push({name: name, status: status, "
                  "why: why, frame: frame}); };\nvar out = {};\nvar payload = " + json.dumps({"glimpsed": glimpsed})
                  + ";\n" + src[a:b] + "\nprocess.stdout.write(JSON.stringify({recs: recs, out: out}));\n")
        r = subprocess.run([self.NODE, "-"], input=script, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        if r.returncode != 0:
            raise AssertionError("the page code did not run - UNKNOWN, not passing: %s" % r.stderr[-400:])
        return json.loads(r.stdout)

    def test_a_stash_frame_files_its_squares_under_the_inventory(self):
        got = self._drive([{"frame": "f_1.jpg", "surface": "stash", "panel": "inventory", "occupied": 33, "free": 7},
                           {"frame": "f_2.jpg", "surface": "shared", "panel": "inventory", "occupied": 0, "free": 40}])
        self.assertEqual(len(got["recs"]), 1, "an empty bag filed a row, or a full one filed none: %r" % got)
        rec = got["recs"][0]
        self.assertEqual(rec["name"], "your inventory · f_1.jpg", "the row is named by the screen: %r" % rec["name"])
        self.assertEqual(rec["status"], "glimpsed")
        self.assertIn("33 square(s) in your inventory", rec["why"])
        for wrong in ("the read named none", "Film that tab", "stash"):
            self.assertNotIn(wrong, rec["why"], "the row still points at the stash: %r" % rec["why"])
        self.assertEqual(got["out"].get("glimpsedTotal"), 33)

    def test_an_older_payload_is_the_inventory_too(self):
        got = self._drive([{"frame": "f_3.jpg", "surface": "personal", "occupied": 22, "free": 18}])
        self.assertEqual(got["recs"][0]["name"], "your inventory · f_3.jpg",
                         "a row from before the panel was recorded was named by its screen")

    def test_a_panel_it_does_not_know_is_said_as_itself(self):
        got = self._drive([{"frame": "f_4.jpg", "surface": "stash", "panel": "stash", "occupied": 2, "free": 98}])
        self.assertEqual(got["recs"][0]["name"], "the stash · f_4.jpg")


RED_PROOF = [
    {"why": "REG-1657 - a stash read is called a fabrication again for what the bag beside it holds",
     "file": "control_app.py",
     # REG-1889 — re-anchored: the function now asks which panel was counted, and this is its last word
     "find": "    if counted == _LATTICE_PANEL and s == _LATTICE_PANEL:\n"
             "        return verdict\n"
             "    return \"other-panel\"\n",
     "replace": "    return verdict\n",
     "matches": 1},
    {"why": "REG-1657 - the sweep stops asking which panel was counted",
     "file": "control_app.py",
     "find": "                            _verdict = cross_panel_verdict(_verdict, surface, _counted)   # REG-1657 · REG-1889\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1889 - a stash-tab read counted on its own grid loses the one fabrication signal again",
     "file": "control_app.py",
     "find": "    if counted == \"stash\" and s in _STASH_GRID_SURFACES:\n        return verdict\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1889 - a stash-tab read is counted on the bag again, never on the panel it read",
     "file": "control_app.py",
     "find": "    if str(surface or \"\").strip().lower() in _STASH_GRID_SURFACES:\n"
             "        so = vc.stash_occupancy(frame_path)\n",
     "replace": "    if False:\n"
                "        so = vc.stash_occupancy(frame_path)\n",
     "matches": 1},
    {"why": "REG-1889 - the sweep stops asking which panel's cells to count",
     "file": "control_app.py",
     "find": "                        _oc2, _counted = _own_panel_cells(_vc2, p, surface) if _vc2 else (None, None)\n",
     "replace": "                        _oc2, _counted = (None, None)\n",
     "matches": 1},
    {"why": "REG-1889 - a fixed-slot tab with no seams is counted as 100 full cells",
     "file": "vault_corpus.py",
     "find": "    if seam < _STASH_SEAM_MIN or cover < _STASH_SEAM_COVER or seam < _STASH_SEAM_RATIO * mid:\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "REG-1889 - a dark navy cell an item covers is counted as an empty one",
     "file": "vault_corpus.py",
     "find": "                     and abs(tint) < _STASH_EMPTY_TINT)\n",
     "replace": "                     )\n",
     "matches": 1},
    {"why": "REG-1657 - a cross-panel read is taken as settled: a seal loosens on a comparison of two panels",
     "file": "control_app.py",
     "find": "    return all(str(r.get(\"verdict\") or \"\") in (\"under-read\", \"agree\") for r in rec)\n",
     "replace": "    return all(str(r.get(\"verdict\") or \"\") in (\"under-read\", \"agree\", \"other-panel\") for r in rec)\n",
     "matches": 1},
    {"why": "REG-1657 - a cross-panel read goes unexplained",
     "file": "control_app.py",
     "find": "    other = [r for r in rec if str(r.get(\"verdict\") or \"\") == \"other-panel\"]\n",
     "replace": "    other = []\n",
     "matches": 1},
    {"why": "REG-1659 - the sweep's glimpse row forgets which panel its squares were counted on",
     "file": "control_app.py",
     "find": "                                        \"panel\": _LATTICE_PANEL,\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-1659 - the board names the glimpse row by the screen again: his bag reads as a stash tab",
     "file": "bible.html",
     "find": "          var p = String((g && g.panel) || 'inventory').trim().toLowerCase();\n"
             "          var where = (p === 'inventory') ? 'your inventory' : ('the ' + p);\n",
     "replace": "          var where = (g && g.surface) || 'stash';\n",
     "matches": 1},
    {"why": "REG-1659 - the loop files the row under the screen, not the helper's name (the join is cut)",
     "file": "bible.html",
     "find": "          _rec(row.name, 'glimpsed', row.why, g.frame);\n",
     "replace": "          _rec((g.surface || 'stash') + ' · ' + (g.frame || '?'), 'glimpsed', row.why, g.frame);\n",
     "matches": 1},
    {"why": "REG-1661 - the incomplete reason re-derives the conditions again and drifts from the pure function",
     "file": "control_app.py",
     "find": "                           else (\"; \".join(_nd) if (not _definitive and _nd)       # the pure function's answer, asked ONCE\n",
     "replace": "                           else (\"%d of %d read frame(s) were never cross-checked\" % (_read_ok[0] - len(_reconciled), _read_ok[0]) if _read_ok[0]\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
