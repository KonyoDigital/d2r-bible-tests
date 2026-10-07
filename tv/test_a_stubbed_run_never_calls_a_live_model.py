# -*- coding: utf-8 -*-
"""REG-2013 - A STUBBED RUN NEVER CALLS A LIVE MODEL, EVEN WHEN CLAUDE IS THROTTLED. #253, the #231 eye on v3576.

TV_STUB is the TDD seam: the whole agent loop runs on canned reads from the stub manifest with zero vision cost. With the
eyes on BOTH, claude_read returned not-read when Claude was throttled or over budget under TV_STUB - but four readers
(claude_vault_read, claude_chronicle_read, charselect_read, surface_read) took the stub ONLY when the Claude miss was
empty, so a miss skipped the stub and fell through to _oneshot -> _grok_backup: a LIVE Grok read, spending his
subscription, from a run that promised it would spend nothing. Each now returns its own not-read shape, like claude_read.

Drives each REAL reader with TV_STUB=1, the eyes on BOTH and Claude throttled; _oneshot and _grok_backup are replaced
by recorders - a call to either is the defect. The baseline (TV_STUB off) shows the recorder CAN see a call.
"""
import os
import sys
import unittest
import unittest.mock as mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import tv_diablo as T  # noqa: E402

ROOT = os.path.dirname(HERE)
FRAME = os.path.join(ROOT, "fixtures", "pack-stash-001", "reels", "reel_s_1784984019250_fxstash001", "f_1784984191754.jpg")

READERS = (("claude_vault_read", lambda p: T.claude_vault_read(p, "stash")),
           ("claude_chronicle_read", lambda p: T.claude_chronicle_read(p, "uniques")),
           ("charselect_read", lambda p: T.charselect_read(p)),
           ("surface_read", lambda p: T.surface_read(p)))


class AStubbedRunNeverCallsALiveModel(unittest.TestCase):

    def _run(self, call, stub):
        calls = []

        def _rec(*a, **k):
            calls.append(1)
            return None

        env = {"TV_STUB": "1"} if stub else {}
        drop = {k: v for k, v in os.environ.items() if k != "TV_STUB"}
        with mock.patch.dict(os.environ, dict(drop, **env), clear=True), \
                mock.patch.object(T, "_reader_choice", lambda: "both"), \
                mock.patch.object(T, "_is_throttled", lambda: True), \
                mock.patch.object(T, "_sub_budget_check", lambda kind="vision": None), \
                mock.patch.object(T, "_oneshot", _rec), \
                mock.patch.object(T, "_grok_backup", _rec):
            try:
                out = call(FRAME)
            except Exception as e:                       # a reader that raises is not one that stayed offline
                out = {"raised": type(e).__name__}
        return calls, out

    def test_a_throttled_claude_under_the_stub_asks_no_model(self):
        self.assertTrue(os.path.exists(FRAME), "premise: the shipped stash frame is missing")
        for name, call in READERS:
            calls, out = self._run(call, stub=True)
            self.assertEqual(calls, [], "%s called a LIVE model from a stubbed run while Claude was throttled (REG-2013)"
                             % name)
            self.assertNotIn("raised", out if isinstance(out, dict) else {}, "%s raised: %r" % (name, out))

    def test_baseline_without_the_stub_the_recorder_sees_the_backup_path(self):
        """Without TV_STUB the same miss DOES go to the model door - so the case above can tell the two apart."""
        seen = 0
        for name, call in READERS:
            calls, _o = self._run(call, stub=False)
            seen += len(calls)
        self.assertGreater(seen, 0, "premise: the recorder never saw a model call, so the stub case proves nothing")


RED_PROOF = [
    {"why": "REG-2013 - the vault reader under the stub falls through to a LIVE Grok read on a Claude miss",
     "file": "tv/tv_diablo.py",
     "find": '        return {"note": "not read - %s under TV_STUB (vault: a stubbed run never calls a live model)" % _miss}\n',
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2013 - the chronicle reader under the stub falls through to a LIVE Grok read on a Claude miss",
     "file": "tv/tv_diablo.py",
     "find": '        return {"note": "not read - %s under TV_STUB (chronicle: a stubbed run never calls a live model)" % _miss}\n',
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2013 - the charselect reader under the stub falls through to a LIVE Grok read on a Claude miss",
     "file": "tv/tv_diablo.py",
     "find": '        return _panel_note("%s under TV_STUB - not read (charselect: a stubbed run never calls a live model)" % _miss, later=True)\n',
     "replace": "        pass\n",
     "matches": 1},
    {"why": "REG-2013 - the surface reader under the stub falls through to a LIVE Grok read on a Claude miss",
     "file": "tv/tv_diablo.py",
     "find": '        return _panel_note("%s under TV_STUB - not read (surface: a stubbed run never calls a live model)" % _miss, later=True)\n',
     "replace": "        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
