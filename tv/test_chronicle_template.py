"""v1690 — the Chronicle template, graded by a HAND-READ confusion matrix over his real film.

WHY THIS FILE EXISTS, AND WHY ITS GROUND TRUTH IS NOT THE REEL'S LABELS
----------------------------------------------------------------------
Round 1 of this ship scored FP=30 of 31 "controls" and concluded the detector was broken. It was
not: the control set was. Round 1 and its first replacement both drew controls from
``kai_report.json`` (``classFrames`` / ``missed`` rows with ``cls='tooltip'``) and never opened one.
Those rows are OCR class labels, and in this reel the OCR read the ITEM ROW TEXT *inside* the
Chronicle list ("AmvLET" = AMULET) and stamped the frame 'tooltip'; 36 of those 43 "controls" fall
inside the window spanned by the positives. A 'tooltip' label here is not evidence of a tooltip.
``engineFrames[].scene`` is no better: f_1786385780443 and f_1786385781534 carry scene='chronicle'
and are the ESC MENU — which has a CHRONICLE *button* on it and no panel at all.

So the ground truth below was read off the PIXELS. Every one of the 60 frames named here was
rendered into labelled contact sheets (4x4, 480px thumbs, filename and verdict burned in; the two
tab-refusal frames at 960px) and looked at. A frame is CHRONICLE here iff the panel's own chrome is
visible — the "Chronicle" title band, the Uniques/Sets/Runewords strip, Normal/Exceptional/Elite,
the Armor/Weapons/Accessories rail, the 63% completion bar, VIEW REWARDS — whether or not an item
tooltip is drawn over it. That is his ask exactly: know the page from its own template, with no
tooltip needed.

EXPECTED MAGNITUDE, WRITTEN DOWN BEFORE THE COUNTS WERE READ
------------------------------------------------------------
Stated before grading: FP high (round 1 said 30/31; the third eye predicted a correct detector
would score FP 28-40 against the label-derived controls) and FN near 0. Both were wrong, and the
instrument was the reason both times:

  * FP is 0, on 19 hand-read controls including 13 ESC-menu frames that print the word CHRONICLE.
    The round-1 FP=30 was the CONTROL SET being Chronicle pages, not the detector firing.
  * FN was 7 against the module committed at HEAD, whose ``is_chronicle`` made the close-X a HARD
    requirement: seven Chronicle pages read ``close_x_red == 0.0000`` (every other panel reads
    0.0667) because a tall item tooltip swallows the panel's close-X. Their ``list_midgray`` was
    0.450-0.497 — the evidence was in the detector's hand and not allowed to count. The template
    landing in this ship replaced that hard gate with a 2-of-4 vote, and all seven now read as
    Chronicle with the close-X still measuring exactly 0. Those seven are kept here BY NAME as the
    regression guard against anyone restoring the hard gate.
  * tab=None looked unreachable when graded over 39 sampled positives, and that was the SAMPLE, not
    the code: two frames in the reel (f_1786385870073, f_1786385960931) light two marker windows at
    once (unique 0.0347 vs runewords 0.0345 — a tooltip sitting in the runewords band) and the
    reader refuses rather than coin-flip a Runewords page into his Uniques truth. Both are now
    graded members, so the refusal branch is proven reachable on real film, not on a synthetic.

The tab channel is where a wrong answer costs him grail truth, so it has its own guard: under the
HEAD module f_1786385846705 was named ``runewords`` purely because the Ginther's Rift tooltip lay in
the runewords band. Every graded positive in this reel is on the Unique tab; naming 'sets' or
'runewords' anywhere here is that inversion coming back, and it goes red.

This module is read-only over his film. It opens frames for reading, inventories the reel directory
before and after a full grading pass, and asserts nothing moved. It creates no file under tv/frames:
the round-1 replacement wrote 51 scratch files into his live reel to "prove" the write-free law, so
the write-trap red-proof here fires against a temp dir instead.

PROVENANCE: graded against tv/chronicle_template.py md5 2c319223 (the 2-of-4-vote template of this
ship, as committed at 4469bb4). The counts below are measurements of that module, not aspirations.
The first draft of this line named md5 d1c8b1e3 — a hash no revision of that file has ever had
(``git log`` over tv/chronicle_template.py gives 7cd7455b then 2c319223, and the working tree is
2c319223). The counts were and are true of 2c319223; the LABEL was the thing that was wrong, so it
was corrected rather than the numbers. Re-run ``md5 -q tv/chronicle_template.py`` after any edit to
that module and re-measure before trusting the constants below. Deliberately NOT asserted in a test:
pinning a source hash would go red on every honest edit and teach the next reader to delete it.
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import console_safe  # noqa: F401,E402
import chronicle_template as ct  # noqa: E402

_FRAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "frames", "hist", "reel_s_1786385768689_67392")

# v1711 — THIS SUITE IS PINNED TO ONE REEL OF KONYO'S REAL FOOTAGE, and that footage is
# gitignored (.gitignore:21 `tv/frames/`) — deliberately, because those are his screenshots and
# they must never be committed or published. So the frames exist on his Mac and can never exist on
# a CI runner.
#
# It went unnoticed because CI hand-listed 7 of the 26 gates and this was not among them. The
# moment CI ran the whole set, it failed 6 tests + 1 error on the runner while passing on his Mac:
# not a regression, an absent subject. Every filename below was HAND-READ against the real frames,
# which is exactly why the suite is worth keeping and exactly why it cannot be synthesised — a
# generated fixture would grade the generator, not his footage.
#
# So it SKIPS where its subject cannot exist, and says so. run_gates.py prints every skip loudly
# and the CI job surfaces them, because a check that did not happen is not a check that passed.
# ⚠ The skip is conditioned on the directory being ABSENT, never on CI or platform: on his Mac,
# where the frames are, a real regression must still turn this red.
_HAVE_FOOTAGE = os.path.isdir(_FRAMES_DIR)
_NO_FOOTAGE_WHY = ("the pinned reel %s is not on this machine — this suite grades HAND-READ ground "
                   "truth against Konyo's real frames, which are gitignored and never leave his "
                   "Mac. Absent subject, not a passing test."
                   % os.path.basename(_FRAMES_DIR))


def _f(name):
    return os.path.join(_FRAMES_DIR, name)


# ---------------------------------------------------------------------------
# HAND-READ GROUND TRUTH — every filename below was looked at, not labelled.
# ---------------------------------------------------------------------------

# Chronicle panel open, chrome unobstructed. Sampled every 5th frame across the whole 220s session
# so the set spans the run, not one page.
CHRONICLE_CLEAN = [
    "f_1786385782444.jpg", "f_1786385787469.jpg", "f_1786385792648.jpg", "f_1786385797582.jpg",
    "f_1786385802533.jpg", "f_1786385807514.jpg", "f_1786385828847.jpg", "f_1786385839950.jpg",
    "f_1786385855289.jpg", "f_1786385860808.jpg", "f_1786385867242.jpg", "f_1786385876396.jpg",
    "f_1786385881023.jpg", "f_1786385891508.jpg", "f_1786385898251.jpg", "f_1786385902430.jpg",
    "f_1786385911965.jpg", "f_1786385917282.jpg", "f_1786385922112.jpg", "f_1786385927209.jpg",
    "f_1786385932143.jpg", "f_1786385937435.jpg",
]

# Chronicle panel open WITH an item tooltip over the list — the case his ask names directly ("needs
# to read the NO TOOLTIP ITEM ... not only the tooltip"). Panel chrome visible around the tooltip.
CHRONICLE_UNDER_TOOLTIP = [
    "f_1786385812542.jpg", "f_1786385817510.jpg", "f_1786385823549.jpg", "f_1786385834526.jpg",
    "f_1786385846705.jpg", "f_1786385871546.jpg", "f_1786385886060.jpg", "f_1786385906930.jpg",
    "f_1786385942497.jpg", "f_1786385947600.jpg",
]

# Chronicle panel open, and a TALL tooltip reaches the panel's top-right and swallows the close-X.
# Verified in pixels: left rail, list rows, 63% bar and VIEW REWARDS all visible. These were the 7
# false negatives of the HEAD module. close_x_red is still exactly 0 on every one of them, so they
# are the standing proof that the panel is found WITHOUT its close-X.
CHRONICLE_CLOSE_X_OCCLUDED = [
    "f_1786385822654.jpg", "f_1786385833507.jpg", "f_1786385851146.jpg", "f_1786385851717.jpg",
    "f_1786385852357.jpg", "f_1786385853405.jpg", "f_1786385854155.jpg",
]

# Chronicle panel open, tooltip lying across the Sets/Runewords tabs. Read at 960px: the selected
# tab is visibly Unique in both, and the reader REFUSES to name it because two marker windows are
# lit. Refusal is the right answer here — these exist so that branch is reachable on real film.
CHRONICLE_TAB_REFUSED = [
    "f_1786385870073.jpg", "f_1786385960931.jpg",
]

# NOT Chronicle, and two genuinely different kinds:
#   * outdoor gameplay, no panel at all (the reel opens on a corpse in a lit street)
#   * the ESC main menu — OPTIONS / SAVE AND EXIT / RETURN TO GAME / LOOT FILTER / CHRONICLE. It
#     prints the word CHRONICLE on a button and is the most dangerous non-panel frame in the reel;
#     f_1786385780443 and f_1786385781534 are the two the engine mislabels scene='chronicle'.
# Cross-check worth having: over all 217 frames of the reel the reader calls exactly 19 of them
# non-Chronicle, and they are exactly these 19.
NOT_CHRONICLE = [
    "f_1786385773403.jpg", "f_1786385774657.jpg", "f_1786385775748.jpg", "f_1786385776805.jpg",
    "f_1786385777623.jpg", "f_1786385778600.jpg",
    "f_1786385779530.jpg", "f_1786385780443.jpg", "f_1786385781534.jpg",
    "f_1786385983003.jpg", "f_1786385983879.jpg", "f_1786385984949.jpg", "f_1786385985954.jpg",
    "f_1786385986973.jpg", "f_1786385987968.jpg", "f_1786385989027.jpg", "f_1786385990212.jpg",
    "f_1786385991567.jpg", "f_1786385993061.jpg",
]

POSITIVES = (CHRONICLE_CLEAN + CHRONICLE_UNDER_TOOLTIP + CHRONICLE_CLOSE_X_OCCLUDED
             + CHRONICLE_TAB_REFUSED)  # 41
CONTROLS = NOT_CHRONICLE  # 19

# Measured on md5 2c319223 (see PROVENANCE). Written down so drift shows up as a number, not a mood.
EXPECTED_TP, EXPECTED_FP, EXPECTED_TN, EXPECTED_FN = 41, 0, 19, 0


def _matrix():
    """Grade detect() over the hand-read set. Returns (counts, missed, false_alarms) and asserts
    nothing, so the numbers can be printed whatever they turn out to be."""
    tp = fp = tn = fn = 0
    missed, false_alarms = [], []
    for name in POSITIVES:
        if ct.detect(_f(name))["is_chronicle"]:
            tp += 1
        else:
            fn += 1
            missed.append(name)
    for name in CONTROLS:
        if ct.detect(_f(name))["is_chronicle"]:
            fp += 1
            false_alarms.append(name)
        else:
            tn += 1
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn}, missed, false_alarms


def _fmt(counts, missed, false_alarms):
    return ("\nCONFUSION MATRIX over %d hand-read frames (%d chronicle / %d control)\n"
            "  TP=%d  FP=%d  TN=%d  FN=%d\n"
            "  false alarms: %s\n  missed panels: %s"
            % (len(POSITIVES) + len(CONTROLS), len(POSITIVES), len(CONTROLS),
               counts["TP"], counts["FP"], counts["TN"], counts["FN"],
               false_alarms or "none", missed or "none"))


@unittest.skipUnless(_HAVE_FOOTAGE, _NO_FOOTAGE_WHY)
class TestTheGradedSetIsRealAndNonEmpty(unittest.TestCase):
    """A matrix over an empty or half-missing set proves nothing. Check the film first."""

    def test_every_graded_frame_exists_on_disk(self):
        self.assertEqual(len(POSITIVES), 41)
        self.assertEqual(len(CONTROLS), 19)
        self.assertEqual(len(set(POSITIVES)), len(POSITIVES), "a frame is graded twice")
        self.assertEqual(len(set(POSITIVES) & set(CONTROLS)), 0,
                         "a frame cannot be both chronicle and control")
        for name in POSITIVES + CONTROLS:
            self.assertTrue(os.path.isfile(_f(name)), "graded frame missing from the reel: " + name)
            self.assertGreater(os.path.getsize(_f(name)), 10000, name + " is not a real frame")

    def test_the_controls_are_not_all_one_thing(self):
        """Round 1's controls were 41 tooltip / 1 stash / 1 gameplay — no diversity, and the
        'tooltip' rows were Chronicle pages. This set is 6 outdoor gameplay + 13 ESC menu, and the
        ESC menu is the hard case precisely because CHRONICLE is printed on it."""
        gameplay = [n for n in NOT_CHRONICLE if n <= "f_1786385778600.jpg"]
        esc_menu = [n for n in NOT_CHRONICLE if n >= "f_1786385779530.jpg"]
        self.assertGreaterEqual(len(gameplay), 6, "no plain-gameplay controls")
        self.assertGreaterEqual(len(esc_menu), 13, "no ESC-menu controls — the hard negatives")
        self.assertEqual(len(gameplay) + len(esc_menu), len(NOT_CHRONICLE))


@unittest.skipUnless(_HAVE_FOOTAGE, _NO_FOOTAGE_WHY)
class TestConfusionMatrixOverRealFootage(unittest.TestCase):
    """The point of the ship: counts, printed, against pixels a human actually looked at."""

    def test_no_false_alarms_on_hand_read_controls(self):
        counts, missed, false_alarms = _matrix()
        report = _fmt(counts, missed, false_alarms)
        self.assertEqual(counts["FP"], EXPECTED_FP,
                         "a non-Chronicle frame read as Chronicle — the ESC menu is the likely "
                         "culprit, it prints the word CHRONICLE on a button" + report)
        self.assertEqual(counts["TN"], EXPECTED_TN, report)

    def test_every_hand_read_chronicle_page_is_found(self):
        counts, missed, false_alarms = _matrix()
        report = _fmt(counts, missed, false_alarms)
        self.assertEqual(counts["TP"] + counts["FN"], len(POSITIVES), "set integrity" + report)
        self.assertEqual(counts["FN"], EXPECTED_FN,
                         "a Chronicle page his eye can see was missed" + report)
        self.assertEqual(counts["TP"], EXPECTED_TP, report)

    def test_the_close_x_is_not_a_requirement_for_seeing_the_panel(self):
        """The HEAD module gated is_chronicle on the close-X and lost these seven whole pages. The
        close-X still measures exactly 0 on all seven — that is what makes this guard non-vacuous:
        the reader finds the panel from the other votes, with the close-X genuinely absent."""
        for name in CHRONICLE_CLOSE_X_OCCLUDED:
            sig = ct.geometry_signals(_f(name))
            self.assertIsNotNone(sig, name)
            self.assertLess(sig["close_x_red"], ct._CLOSE_X_RED_THRESH,
                            name + ": the close-X is readable again, so this frame no longer proves "
                                   "anything about occlusion — regrade it")
            self.assertGreaterEqual(sig["list_midgray"], 0.44,
                                    name + ": the panel's stone-gray list interior is the evidence "
                                           "that has to carry the vote")
            r = ct.detect(_f(name))
            self.assertTrue(r["is_chronicle"],
                            name + ": Chronicle page lost because a tooltip covered its close-X — "
                                   "the hard close-X gate is back: " + r["why"])

    def test_a_tooltip_over_the_panel_is_still_read_as_chronicle(self):
        """His ask, literally: read the page even when an item tooltip is drawn across it."""
        for name in CHRONICLE_UNDER_TOOLTIP:
            r = ct.detect(_f(name))
            self.assertTrue(r["is_chronicle"],
                            name + " is a Chronicle page under a tooltip and was missed: " + r["why"])


@unittest.skipUnless(_HAVE_FOOTAGE, _NO_FOOTAGE_WHY)
class TestTabRefusalIsReachable(unittest.TestCase):
    """Round 1 shipped a tab=None branch nothing could reach. Both outcomes must occur on real
    film — a named tab when the strip reads clean, None when two marker windows are lit."""

    def test_tab_none_is_reachable_on_real_frames(self):
        refused = [n for n in POSITIVES if ct.detect(_f(n))["tab"] is None]
        self.assertGreater(len(refused), 0,
                           "tab=None is unreachable — the refusal branch is dead code and a "
                           "Runewords page will be written into his Uniques truth")
        for name in CHRONICLE_TAB_REFUSED:
            r = ct.detect(_f(name))
            self.assertTrue(r["is_chronicle"], name + " is a Chronicle page: " + r["why"])
            self.assertIsNone(r["tab"],
                              name + ": two marker windows are lit here (unique ~0.0347 vs "
                                     "runewords ~0.0345) and the reader guessed instead of "
                                     "refusing: " + r["why"])

    def test_a_named_tab_is_also_reachable_and_is_never_the_tooltip_inversion(self):
        named = [(n, ct.detect(_f(n))["tab"]) for n in POSITIVES]
        named = [(n, t) for n, t in named if t is not None]
        self.assertGreater(len(named), 0, "no tab is ever named — the reader would be useless")
        for n, t in named:
            self.assertEqual(t, "unique",
                             "%s named tab=%s. Every graded page in this reel is the Unique tab; "
                             "the HEAD module called f_1786385846705 'runewords' because a tooltip "
                             "lay in the runewords band. That inversion is back." % (n, t))


@unittest.skipUnless(_HAVE_FOOTAGE, _NO_FOOTAGE_WHY)
class TestPureLaw(unittest.TestCase):
    """No writes, no deletes, no network, no model calls — proven three ways, because each one on
    its own is a proxy: the source text, a runtime trap wider than builtins.open, and an inventory
    of his actual reel directory before and after a full grading pass."""

    def test_source_text_has_no_write_delete_or_call_out(self):
        with open(ct.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertNotRegex(src, r'open\([^)]*["\'][wax]')
        for forbidden in ("os.remove(", "os.rename(", "os.replace(", "os.unlink(", "shutil.",
                          "json.dump(", "requests.", "urllib.", "socket.", ".save(", "subprocess."):
            self.assertNotIn(forbidden, src, forbidden + " has no business in a pure template reader")
        for forbidden in ("anthropic", "openai", "grok", "claude_read", "vision_call"):
            self.assertNotIn(forbidden, src.lower(),
                             forbidden + " would make this a model caller, not a pure reader")

    def test_runtime_trap_sees_no_write_through_any_door(self):
        """builtins.open alone is not the thing — os.open, io.open and PIL's C-level save all
        escape it. Trap every door, then run the real reader through it."""
        with _WriteTrap() as trap:
            for name in (CHRONICLE_CLEAN[0], CHRONICLE_UNDER_TOOLTIP[0], NOT_CHRONICLE[0]):
                ct.detect(_f(name))
        self.assertEqual(trap.attempts, [],
                         "chronicle_template attempted a write: %s" % (trap.attempts,))

    def test_the_trap_itself_catches_a_writer(self):
        """Seen RED on purpose, so the green above means something. The scratch file goes into a
        temp dir — nothing in this file ever writes anywhere near tv/frames."""
        tmp = tempfile.mkdtemp(prefix="chronicle_template_writeproof_")
        try:
            with _WriteTrap() as trap:
                try:
                    open(os.path.join(tmp, "scratch"), "w").close()
                except _WroteSomething:
                    pass
            self.assertEqual(len(trap.attempts), 1,
                             "the write trap did not fire, so it proves nothing about the module")
            self.assertFalse(os.path.exists(os.path.join(tmp, "scratch")),
                             "the trap let the write through")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_his_reel_directory_is_untouched_by_a_full_grading_pass(self):
        """The thing itself: nothing appeared, changed size, or changed mtime in his film."""
        before = _inventory(_FRAMES_DIR)
        _matrix()
        after = _inventory(_FRAMES_DIR)
        self.assertGreater(len(before), 200, "reel inventory looks empty — the check is vacuous")
        self.assertEqual(before, after,
                         "the reel changed during a grading pass: added=%s removed=%s"
                         % (sorted(set(after) - set(before)), sorted(set(before) - set(after))))


def _inventory(d):
    return {n: (os.path.getsize(os.path.join(d, n)), os.stat(os.path.join(d, n)).st_mtime_ns)
            for n in sorted(os.listdir(d))}


class _WroteSomething(IOError):
    pass


class _WriteTrap(object):
    """Blocks and records every write door reachable from python: builtins.open / io.open in a
    writing mode, os.open with a write flag, os.remove/unlink/rename/replace/mkdir/makedirs, and
    PIL's Image.save (which writes at C level, below builtins.open)."""

    _WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC

    def __enter__(self):
        import builtins
        self.attempts = []
        self._saved = {}

        def guard_open(orig, label):
            def wrapper(file, mode="r", *a, **kw):
                if any(c in str(mode) for c in "wax+"):
                    self.attempts.append((label, str(file), str(mode)))
                    raise _WroteSomething("%s(%s, %s)" % (label, file, mode))
                return orig(file, mode, *a, **kw)
            return wrapper

        def guard_os_open(orig):
            def wrapper(path, flags, *a, **kw):
                if flags & self._WRITE_FLAGS:
                    self.attempts.append(("os.open", str(path), oct(flags)))
                    raise _WroteSomething("os.open(%s)" % path)
                return orig(path, flags, *a, **kw)
            return wrapper

        def guard_call(label):
            def wrapper(*a, **kw):
                self.attempts.append((label, str(a[:1]), ""))
                raise _WroteSomething(label)
            return wrapper

        self._saved["builtins.open"] = (builtins, "open", builtins.open)
        builtins.open = guard_open(builtins.open, "builtins.open")
        self._saved["io.open"] = (io, "open", io.open)
        io.open = guard_open(io.open, "io.open")
        self._saved["os.open"] = (os, "open", os.open)
        os.open = guard_os_open(os.open)
        for name in ("remove", "unlink", "rename", "replace", "mkdir", "makedirs"):
            if hasattr(os, name):
                self._saved["os." + name] = (os, name, getattr(os, name))
                setattr(os, name, guard_call("os." + name))
        try:
            from PIL import Image
            self._saved["Image.save"] = (Image.Image, "save", Image.Image.save)
            Image.Image.save = guard_call("PIL.Image.save")
        except ImportError:  # pragma: no cover - PIL is a hard dependency of the module under test
            pass
        return self

    def __exit__(self, *exc):
        for target, attr, orig in self._saved.values():
            setattr(target, attr, orig)
        return False


if __name__ == "__main__":
    unittest.main(verbosity=2)
