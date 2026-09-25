# -*- coding: utf-8 -*-
"""A PANEL THAT WAS READ AND HELD NO NAMES IS NOT A PANEL NOBODY READ.

MEASURED 2026-09-13. The river could not drain and `eligible` had NEVER fired once. Eight reels
sat on `panels-never-banked`, and the rule holding them asked only two questions: does the survey
see panels, and is the reel in the durable stores. A reel whose panels carry no readable NAME can
never enter those stores, so the answer was True forever and no future run could change it.

The rule's own comment says it exists for "the state a seal-with-no-rows leaves behind" — and it
never once consulted that seal. [[the-unjoined-end]]

WHY THOSE PANELS ARE UNREADABLE, AND WHY THAT IS CORRECT: one of the eight is a Shared stash page
5/5 carrying ~25 items. It is genuinely full and genuinely unnameable, because a stash GRID prints
no names at all — only the hover tooltip does. The vault reader returning items:[] is RIGHT, which
`vault_seal_is_definitive` already rules a COMPLETE answer rather than a failure.

⚠ THE ASYMMETRY WAS THE DEFECT. `_seal_extracted`'s examined_empty flag was reachable only from
the branch taken when a pass grounded NOTHING. A pass that grounded one row sealed every
non-contributing session with no record of what was looked at. So the same reel, same footage,
same reader released when swept ALONE and was held forever when swept beside one productive
neighbour.

⚠ UNKNOWN STILL KEEPS THE FOOTAGE. Only frame_authority.seal_releases_frames may unlock the hold,
and it says yes for a COVERED seal or an EMPTY one carrying examinedEmpty — never for the default
"nothing was taken". An unreadable seal store holds. There is no un-delete.

⚠ EVERY FIXTURE HERE IS SYNTHETIC. An earlier law in this territory was built on live stages() and
would have gone blind the moment the project succeeded and the held list emptied.
"""
import io
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))

REEL = "reel_s_1700000000000_00001"
SEAL_EXAMINED = {"ts": 1, "rows": 0, "extracted": [],
                 "extractedWhy": "examined and there was nothing to take",
                 "examinedEmpty": True}
SEAL_DEFAULT = {"ts": 1, "rows": 0, "extracted": [], "extractedWhy": "nothing was taken"}


def _between(src, start, end):
    """The region BETWEEN two anchors, or '' when either is missing. -> str

    Both ends anchored on purpose: a fixed-size window past the region reads as ABSENT and has
    invented findings here before. [[source-reading-guard]]
    """
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


class TestAnExaminedPanelIsNotAnUnreadOne(unittest.TestCase):

    def _ask(self, seal, sealed_ok=True, panels=4):
        """Run _panels_never_banked against a synthetic survey and a synthetic seal. -> bool"""
        import reel_retention as RR
        import retro_triage as RT
        import frame_authority as FA

        store = {REEL: {"full": True, "panels": panels, "frames": panels}}
        # ⚠ #123 — the cache key was built from HIS retro_triage.json (`getmtime` of the real store):
        # on CI there is no such file, so all four cases ERRORED in 0.1 s before judging anything, and
        # here the key depended on his live store. A throwaway store file makes the key real on every
        # machine; the triage store path is pointed at it and restored. [[feedback-fixtures-never-touch-live-data]]
        import tempfile as _tempfile
        _fd, _tmp_store = _tempfile.mkstemp(prefix="examined_panel_", suffix=".json")
        with os.fdopen(_fd, "w") as _fh:
            _fh.write("{}")
        self.addCleanup(lambda: os.path.exists(_tmp_store) and os.remove(_tmp_store))
        old_store_path = RT._store_path
        RT._store_path = lambda *a, **k: _tmp_store
        key = (RT._store_path(), os.path.getmtime(RT._store_path()))
        old_cache = dict(RR._TRIAGE_CACHE)
        old_dur = RR._DURABLE
        old_sealed = FA.sealed_sessions
        try:
            RR._TRIAGE_CACHE["store"] = store
            RR._TRIAGE_CACHE["at"] = key
            RR._DURABLE = set()                      # nothing banked -> only the seal can release
            FA.sealed_sessions = lambda root=None: (({REEL: seal} if seal else {}), sealed_ok)
            return RR._panels_never_banked(REEL)
        finally:
            RR._TRIAGE_CACHE.clear()
            RR._TRIAGE_CACHE.update(old_cache)
            RR._DURABLE = old_dur
            FA.sealed_sessions = old_sealed
            RT._store_path = old_store_path

    def test_an_examined_empty_seal_releases_the_reel(self):
        held = self._ask(SEAL_EXAMINED)
        print("examined-empty seal -> held=%s (expected False)" % held)
        self.assertFalse(held,
                         "a seal that read every panel and cross-checked them, finding no name to "
                         "be had, is a COMPLETE answer — holding it is a hold no run can lift")

    def test_a_default_seal_still_holds_the_reel(self):
        held = self._ask(SEAL_DEFAULT)
        print("default 'nothing was taken' seal -> held=%s (expected True)" % held)
        self.assertTrue(held,
                        "'nothing was taken' is _seal_extracted's DEFAULT for rows==0 and records "
                        "no examination — it must never be read as one")

    def test_an_unreadable_seal_store_keeps_the_footage(self):
        self.assertTrue(self._ask(SEAL_EXAMINED, sealed_ok=False),
                        "an unreadable seal store is UNKNOWN, and UNKNOWN keeps the reel")
        self.assertTrue(self._ask(None),
                        "a reel with no seal at all was never examined — it must hold")

    def test_a_reel_with_no_panels_is_untouched_by_this_path(self):
        self.assertFalse(self._ask(SEAL_DEFAULT, panels=0),
                         "no panels means nothing to bank; that answer predates this rule and "
                         "must not change")

    def test_the_seal_authority_is_frame_authoritys_and_not_a_second_opinion(self):
        import frame_authority as FA
        self.assertTrue(FA.seal_releases_frames(SEAL_EXAMINED)[0])
        self.assertFalse(FA.seal_releases_frames(SEAL_DEFAULT)[0])
        with io.open(os.path.join(HERE, "reel_retention.py"), encoding="utf-8") as _fh:
            src = _fh.read()
        region = _between(src, "def _panels_never_banked", "\ndef ")
        # ⚠ JUDGE THE CODE, NOT THE PROSE. The first cut of this assertion matched the word inside
        # the comment explaining the fix and failed on documentation. Comments are read when
        # judging a MEASUREMENT and ignored when judging CODE. [[measured-true-read-wrong]]
        code = "\n".join(ln.split("#", 1)[0] for ln in region.splitlines())
        self.assertIn("seal_releases_frames", code,
                      "the rule must ask frame_authority rather than re-deciding what a seal means")
        self.assertNotIn("examinedEmpty", code,
                         "reading the flag directly forks the authority — ask seal_releases_frames")

    def test_a_non_contributing_session_records_what_was_examined(self):
        """The WRITER half. Without it the flag above could never appear on a new seal."""
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as _fh:
            src = _fh.read()
        region = _between(src,
                          "                _srows = int(_rows_by_sess.get(str(sess), 0))",
                          "            _seal_pending = True")
        self.assertTrue(region, "could not locate the per-session seal writer")
        self.assertIn("examined_empty=_examined", region,
                      "the non-contributing session must be sealed with its examination recorded")
        # ⚠ PIN THE COMPUTATION, NOT ONLY THE CALL SITE. The first cut asserted just that
        # `examined_empty=_examined` was passed, and heart2 proved it BLIND: setting
        # `_examined = False` defeats the whole writer while leaving that call untouched, so the
        # flag could never be written and this gate stayed green through its own defeat.
        _bind = [ln.strip() for ln in region.splitlines()
                 if ln.split("#", 1)[0].strip().startswith("_examined =")]
        print("_examined binding(s) found: %d -> %s" % (len(_bind), _bind))
        self.assertEqual(len(_bind), 1, "_examined must be bound exactly once")
        self.assertIn("_srows == 0", _bind[0],
                      "the flag may only be set for a session that contributed NOTHING")
        self.assertIn("_definitive", _bind[0],
                      "and only when the pass was definitive — that is the clause refusing a "
                      "failed read, a pixel error, an over-read, or a verdict outside "
                      "under-read/agree. Without it this releases his footage on no evidence")
        self.assertIn('_rec["examinedEmpty"] = True', region,
                      "seal_releases_frames reads examinedEmpty off the seal row itself")
        self.assertIn("_definitive", region,
                      "only vault_seal_is_definitive may unlock this — it is what refuses a failed "
                      "read, a pixel error, an over-read, or a verdict outside under-read/agree")
        hoist = _between(src, "        _definitive = vault_seal_is_definitive", "        if _rows:")
        self.assertTrue(hoist,
                        "_definitive must be computed ABOVE the _rows split; inside the else it "
                        "can only ever answer for a pass that grounded nothing")
        print("writer half present: examined_empty= + examinedEmpty + hoisted _definitive")


RED_PROOF = [
    {
        "why": "the rule stops consulting the seal, so a panel that was read and held no names "
               "reads exactly like one nobody ever opened — a hold no future run can lift, which "
               "is what pinned 8 of his reels and kept `eligible` at zero forever",
        "file": "reel_retention.py",
        "find": "                if _releases:\n                    return False",
        "replace": "                if False:\n                    return False",
        "matches": 1,
    },
    {
        "why": "the writer stops recording the examination, so no new seal can ever carry the "
               "flag and the join above goes permanently inert",
        "file": "control_app.py",
        "find": "                _examined = bool(_srows == 0 and _definitive)",
        "replace": "                _examined = False",
        "matches": 1,
    },
    {
        "why": "_definitive falls back inside the else branch, restoring the asymmetry where a "
               "reel's fate depends on which neighbour it was swept beside",
        "file": "control_app.py",
        "find": "        _definitive = vault_seal_is_definitive(_read_ok[0], _reconciled, _over_read, _pix_err)",
        "replace": "        _definitive = False",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
