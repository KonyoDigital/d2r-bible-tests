# -*- coding: utf-8 -*-
"""#227 — A FRESH MACHINE ESTABLISHES ITS TREE AT BOOT, ON EVERY PLATFORM.

MEASURED 2026-09-24: the one boot-shaped machine_tree.establish() lived inside _prewarm_seal_cache,
which returns at once on Windows and otherwise runs only after a capture session STOPS. So a fresh
machine established nothing until it filmed, and 'this console tree is established' read MISSING for
as long as that took — forever on a machine that never records.

  · DRIVEN: _establish_tree_at_boot() calls the writers' door with IS_WIN True (no platform skip).
  · DRIVEN: a scratch console (render gate, test launcher) establishes NOTHING — without TV_HIST it
    would provision the runner's real home.
  · COMPILER: main() starts it (co_names), so it runs at boot, not after a session.
RED_PROOF below.
"""
import os
import sys
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import control_app as ca  # noqa: E402


class _Stubs(unittest.TestCase):
    scratch = False

    def setUp(self):
        self._mods = {k: sys.modules.get(k) for k in ("machine_tree", "win_relaunch")}
        self._win = ca.IS_WIN
        self.calls = []
        mt = types.ModuleType("machine_tree")
        mt.UNUSABLE, mt.FAILED, mt.REFUSED = "unusable", "failed", "refused"
        mt.establish = lambda: self.calls.append("establish") or [
            {"root": "ledger backups", "state": "created", "why": "made and a write proven"}]
        mt.say = lambda rows: "stub"
        wr = types.ModuleType("win_relaunch")
        wr.scratch_console = lambda: self.scratch
        sys.modules["machine_tree"], sys.modules["win_relaunch"] = mt, wr

    def tearDown(self):
        ca.IS_WIN = self._win
        for k, v in self._mods.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


class HisOwnConsoleEstablishesAtBoot(_Stubs):

    def test_it_establishes_on_windows(self):
        ca.IS_WIN = True
        rows = ca._establish_tree_at_boot()
        self.assertEqual(self.calls, ["establish"], "a Windows console established nothing at boot")
        self.assertEqual(rows[0]["state"], "created")

    def test_it_establishes_on_the_mac(self):
        ca.IS_WIN = False
        ca._establish_tree_at_boot()
        self.assertEqual(self.calls, ["establish"])


class AScratchConsoleEstablishesNothing(_Stubs):
    scratch = True

    def test_a_scratch_console_never_provisions(self):
        ca.IS_WIN = True
        self.assertIsNone(ca._establish_tree_at_boot())
        self.assertEqual(self.calls, [], "a scratch console provisioned this machine's tree")


class TheBootStartsIt(unittest.TestCase):

    def test_main_starts_the_establish_at_boot(self):
        self.assertIn("_establish_tree_at_boot", ca.main.__code__.co_names,
                      "main() no longer starts the tree establish, so a fresh machine waits for a film")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#227 - main() no longer establishes the tree at boot: a fresh machine reads MISSING until it films",
        "file": "control_app.py",
        "find": "    threading.Thread(target=_establish_tree_at_boot, daemon=True, name=\"tvd-tree\").start()\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "#227 - the boot establish is skipped on Windows again (the _prewarm_seal_cache shape)",
        "file": "control_app.py",
        "find": "        import win_relaunch as _wr\n        if _wr.scratch_console():\n            return None\n    except Exception:\n        return None\n    try:\n        import machine_tree as _mt\n        rows = _mt.establish() or []\n",
        "replace": "        import win_relaunch as _wr\n        if _wr.scratch_console():\n            return None\n    except Exception:\n        return None\n    if IS_WIN:\n        return None\n    try:\n        import machine_tree as _mt\n        rows = _mt.establish() or []\n",
        "matches": 1,
    },
    {
        "why": "#227 - a scratch console provisions this machine's real tree at boot",
        "file": "control_app.py",
        "find": "        import win_relaunch as _wr\n        if _wr.scratch_console():\n            return None\n    except Exception:\n        return None\n    try:\n        import machine_tree as _mt\n",
        "replace": "        import win_relaunch as _wr\n    except Exception:\n        return None\n    try:\n        import machine_tree as _mt\n",
        "matches": 1,
    },
]
