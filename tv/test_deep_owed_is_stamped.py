# -*- coding: utf-8 -*-
"""v2724 — AN ABSENT DEEP READ MEANT TWO DIFFERENT THINGS AND NOTHING COULD TELL THEM APART.

14 of his 40 reels resolve to zone UNKNOWN with 0 segments, and the correlation is perfect:
zone UNKNOWN == segments 0 == never deep-read. Their lane mix is
kai 169 · intake 43 · system 13 · ocr 8 · skip 6 · DEEP **0**.

But an absent `deep` row is consistent with two histories:
    (a) the frame was never dispatched to the reader
    (b) it WAS dispatched and the answer was thrown away

(b) is real and lives in `_vision_job`: `if _POOL_STOPPING: return` drops a COMPLETED read on
shutdown. That is correct — applying a stale read after close corrupts the session — but it leaves
no trace a read was ever owed. So the two histories were indistinguishable, and the row could only
say "never deep-read" without being able to say why. [[unknown-stays-unknown]]

=== WHAT THIS PINS ===
The stamp is written at the moment of COMMITMENT — before the network call — so a read lost to the
shutdown guard or to an exception still leaves `deep-owed` behind. `deep-owed` beside `deep` then
separates "never asked" from "asked and lost".

⚠⚠ AND THE FIRST CUT WOULD HAVE RECORDED NOTHING, FOREVER. It named the frame `fid_this`, which has
ZERO bindings in `_vision_job` — verified by PARSING the function, not by reading it. Inside the
stamp's own `try/except Exception: pass`, that NameError would have been swallowed silently. It is
the identical defect fixed one hour earlier in the /board Doctor hookup (`path="/board"` making the
recorder open a file that could not exist), repeated by the same hand on the same day. A write that
cannot run is worse than no write, because the absence reads as "nothing happened".
[[feedback-suspect-the-instrument]] [[join-gate-heart]]

⚠ IT CANNOT BE BACKFILLED for the existing 14, and must not be. Nothing recorded at the time
distinguishes (a) from (b) for them, so they stay UNKNOWN — the same rule `door` states one file
over: "absent door = absent key, never a guessed default".
"""
import ast
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

SRC = os.path.join(HERE, "tv_diablo.py")


def _src():
    return io.open(SRC, encoding="utf-8").read()


def _vision_job():
    """-> (ast node, source). The function that dispatches deep reads."""
    src = _src()
    tree = ast.parse(src)
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "_vision_job":
            return n, src
    raise AssertionError("GUARD CANNOT GRADE: _vision_job is gone or renamed — fix this test "
                         "before trusting any verdict it prints")


class DeepOwedIsStamped(unittest.TestCase):

    def test_the_stamp_exists_at_all(self):
        self.assertIn('"lane": "deep-owed"', _src(),
                      "nothing records that a deep read was OWED, so 'never dispatched' and "
                      "'dispatched and lost' remain the same absence")

    def test_it_is_written_BEFORE_the_read_not_after(self):
        """The whole point. After the call, a discarded read leaves no trace."""
        src = _src()
        stamp = src.index('"lane": "deep-owed"')
        call = src.index("rd = claude_read(snap_path")
        self.assertLess(stamp, call,
                        "the owing is stamped AFTER the reader is called. A read dropped by the "
                        "_POOL_STOPPING guard, or lost to an exception, would then leave nothing "
                        "behind — which is the exact case this exists to measure")

    def test_every_name_it_uses_is_actually_IN_SCOPE(self):
        """⚠⚠ THE LAW THAT WOULD HAVE CAUGHT MY FIRST CUT.

        The stamp lives inside `try/except Exception: pass`, so a NameError is SILENT: the row is
        never written and the absence reads as 'no deep read was owed'. The first cut used
        `fid_this`, which is never bound in this function. Verified by parsing, because reading it
        looked fine."""
        fn, src = _vision_job()
        target = next(i for i, l in enumerate(src.splitlines(), 1)
                      if '"lane": "deep-owed"' in l)
        # names the stamp block LOADS
        lines = src.splitlines()
        block = "\n".join(lines[target - 3:target + 8])
        used = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?![\w\s]*=[^=])", block))
        used &= {"snap_path", "SESSION_ID", "_journal", "os", "fid_this", "frame_id", "job", "rid"}
        tree = ast.parse(src)
        module_level = {t.id for n in tree.body if isinstance(n, ast.Assign)
                        for t in n.targets if isinstance(t, ast.Name)}
        module_level |= {n.name for n in tree.body
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        module_level |= {a.asname or a.name.split(".")[0]
                         for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        bound_anywhere = {n.id for n in ast.walk(tree)
                          if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        for name in sorted(used):
            self.assertTrue(
                name in module_level or name in bound_anywhere,
                "the stamp references %r, which is bound NOWHERE. Inside its own try/except that "
                "is a silent NameError: the row is never written and the absence reads as 'no deep "
                "read was owed'." % name)

    def test_it_does_NOT_use_the_name_that_was_never_bound(self):
        """Pin the specific mistake, so it cannot come back by copy."""
        fn, src = _vision_job()
        body = src[src.index("def _vision_job"):]
        body = body[:body.index("\n            def ") if "\n            def " in body else len(body)]
        stamp_i = body.index('"lane": "deep-owed"')
        block = body[stamp_i - 200:stamp_i + 400]
        binds = {n.id for n in ast.walk(fn)
                 if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        self.assertNotIn("fid_this", block.split("#")[0] if "#" in block else block,
                         "the stamp uses `fid_this`, which has %d bindings in _vision_job. It "
                         "would raise NameError, be swallowed, and record nothing forever."
                         % len([b for b in binds if b == "fid_this"]))

    def test_it_is_a_LANE_not_a_flag_on_the_deep_row(self):
        """The deep row is exactly what does not exist in the case being measured."""
        src = _src()
        self.assertIn('"lane": "deep-owed"', src)
        self.assertNotIn('"deepOwed": True', src,
                         "the owing is a flag on a row that, in the case this measures, is never "
                         "written at all")

    def test_the_segmenter_still_ignores_it(self):
        """⚠ It says a read was OWED, never that one happened. reel_segments filters lane=='deep',
        so a `deep-owed` row must never be mistaken for a read."""
        seg = io.open(os.path.join(HERE, "reel_segments.py"), encoding="utf-8").read()
        seg = re.sub(r"#.*$", " ", seg, flags=re.M)
        self.assertRegex(seg, r'lane["\']?\)?\s*!=\s*["\']deep["\']',
                         "reel_segments no longer filters strictly on lane == 'deep', so a "
                         "deep-owed row could be counted as an actual read")


if __name__ == "__main__":
    unittest.main(verbosity=2)
