# -*- coding: utf-8 -*-
"""REG-2006 - "GROK STEPPED IN" COUNTS ONLY A FRAME GROK WAS ASKED. The #231 eye on v3576, confirmed on v3605's tree.

note_backup's own contract: "One frame asked Grok because Claude did not read ... Counted even when the backup itself
fails: how often Grok had to step in includes the frames where it was asked and could not answer." _grok_backup called
it FIRST, before the install, sign-in and one-Grok-gate checks, so on a PC with no Grok (Dean's) or a signed-out one the
heart's "Grok stepped in N" climbed for frames nobody asked - and the console paints that line from backupReads > 0.

Drives the REAL tv_diablo._grok_backup with the OS edge stubbed (the binary lookup, the sign-in check, the gate, the
read): refused before an ask -> the count does not move; asked (even when the read answers nothing) -> exactly +1.
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
import g5_grok_eyes as G5  # noqa: E402
import tv_diablo as T  # noqa: E402


class _Gate(object):
    def __init__(self, free):
        self.free = free

    def acquire(self, timeout=None):
        return self.free

    def release(self):
        pass


class ABackupCountsOnlyAnAsk(unittest.TestCase):

    def _count(self, installed=True, signed_in=True, gate_free=True):
        calls = []
        with mock.patch.dict(G5._STATS, {"backup_reads": 0, "backup_why": ""}), \
                mock.patch.object(G5, "_stats_flush", lambda *a, **k: None), \
                mock.patch.object(G5, "_grok_bin", lambda: "/bin/grok" if installed else None), \
                mock.patch.object(G5, "has_subscription", lambda: signed_in), \
                mock.patch.object(G5, "g5_vision_read", lambda *a, **k: calls.append(1)), \
                mock.patch.object(T, "_GROK_ONLY_GATE", _Gate(gate_free)), \
                mock.patch.object(T, "journal_skip", lambda *a, **k: None):
            T._grok_backup("/nowhere/f_1.jpg", "claude timed out")
            return int(G5._STATS.get("backup_reads") or 0), len(calls)

    def test_a_frame_refused_before_any_ask_is_not_counted(self):
        for kw, what in ((dict(installed=False), "Grok is not installed"),
                         (dict(signed_in=False), "Grok is not signed in"),
                         (dict(gate_free=False), "the one-Grok gate stayed busy")):
            n, asked = self._count(**kw)
            self.assertEqual(asked, 0, "premise: %s, yet Grok was asked" % what)
            self.assertEqual(n, 0, "'Grok stepped in' counted a frame nobody asked (%s) - REG-2006" % what)

    def test_a_frame_grok_was_asked_is_counted_once_even_when_it_answers_nothing(self):
        n, asked = self._count()
        self.assertEqual(asked, 1, "premise: an installed, signed-in, free Grok was not asked")
        self.assertEqual(n, 1, "an ask that answered nothing was not counted - note_backup's own contract")


RED_PROOF = [
    {"why": "REG-2006 - the backup is counted again before the install and sign-in checks, so a PC with no Grok "
            "shows 'Grok stepped in N'",
     "file": "tv/tv_diablo.py",
     "find": "        import g5_grok_eyes as _G5b\n    except Exception as e:\n",
     "replace": "        import g5_grok_eyes as _G5b\n        _G5b.note_backup(label)\n    except Exception as e:\n",
     "matches": 1},
    {"why": "REG-2006 - the ask is never counted, so 'Grok stepped in' stays 0 while Grok reads",
     "file": "tv/tv_diablo.py",
     "find": "        _G5b.note_backup(label)\n    except Exception:\n        pass\n",
     "replace": "        pass\n    except Exception:\n        pass\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
