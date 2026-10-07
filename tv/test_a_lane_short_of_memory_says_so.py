# -*- coding: utf-8 -*-
"""REG-2003 - A VAULT LANE THAT MEMORY KEPT FROM PROVING ITSELF SAYS SO, AND AN IDLE PC FREES ITS VIEW FOR IT.

MEASURED on his ALT 2026-10-07 18:2x, on v3604 (7.9 GB, Boosteroid + the console up): free RAM 403 MB, under the
1024 MB floor below which no secondary worker starts (#83). The shipped canary (REG-1959) asked the OCR worker for one
read and got nothing back in 0.03 s - no worker had started - so every held reel said only "the lane could not be
proven live, so 'no stash here' is UNKNOWN", nothing named memory as the reason, and the idle-PC view release that
REG-1957 built for exactly this shortage was never asked, because it only answered an owed PROOF.

WHAT THIS LAW DRIVES (the real code each time, stubs only at the OS edge):
  * OcrWorker._spawn under the memory floor records WHY (ram_refused), and a spawn that is not refused clears it;
  * LaneCanary.probe on the shipped canary, with that worker refused, fails AND names the reason; with no refusal it
    fails with no invented reason;
  * _vault_lane_free_view asks the SAME pure decision as the proof (view_release_for_proof): a window already sent
    away is freed, naming the vault lane; a PC he is playing on keeps its window;
  * the vault sweep hands the reason to its lane note and to that release (code only, each exactly once).
"""
import io
import os
import sys
import tempfile
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
os.environ.setdefault("TV_GATE_CACHE", os.path.join(tempfile.mkdtemp(prefix="lane_ram_"), "gate_cache.json"))
import control_app as CA  # noqa: E402
import tv_diablo as T  # noqa: E402

RAM_WHY = "free RAM 403 MB is under the 1024 MB floor - no secondary worker until it recovers"


class _Proc(object):
    stdout = iter(())

    def poll(self):
        return None


def _code(src):
    return "\n".join(l.split("#", 1)[0] for l in src.split("\n"))


class ALaneShortOfMemorySaysSo(unittest.TestCase):

    def setUp(self):
        self.w = T.OcrWorker()
        self.addCleanup(lambda: setattr(self.w, "p", None))

    def _spawn(self, ram_ok):
        with mock.patch.object(T, "_ocr_worker_cmd", lambda: ["ocr-worker"]), \
                mock.patch.object(T._child_guard, "secondary_spawn_allowed",
                                  lambda: (True, "") if ram_ok else (False, RAM_WHY)), \
                mock.patch.object(T._child_guard, "spawn", lambda *a, **k: _Proc()), \
                mock.patch.object(T, "ev", lambda *a, **k: None):
            return self.w._spawn()

    def test_a_spawn_refused_for_memory_records_why_and_a_later_spawn_clears_it(self):
        self.assertFalse(self._spawn(ram_ok=False), "premise: the memory floor did not refuse the worker")
        self.assertEqual(self.w.ram_refused, RAM_WHY, "the worker forgot why memory refused it (REG-2003)")
        self.assertTrue(self._spawn(ram_ok=True), "premise: a spawn with memory to spare did not start")
        self.assertEqual(self.w.ram_refused, "", "a worker that started still reports a memory refusal")

    def _probe(self, refused):
        with mock.patch.object(CA, "_gate_cache", lambda: {}), \
                mock.patch.object(CA, "stash_screen_open", lambda path: None), \
                mock.patch.object(T._OCR, "ram_refused", refused):
            cn = CA.LaneCanary()
            ok = cn.probe(cn.known_good_frame())
            return ok, cn.why

    def test_the_canary_names_a_memory_refusal_and_invents_none(self):
        ok, why = self._probe(RAM_WHY)
        self.assertFalse(ok, "premise: a lane whose OCR worker never started was proven live")
        self.assertEqual(why, "the OCR worker was not started (%s)" % RAM_WHY,
                         "the failed probe does not say memory kept the OCR worker from starting (REG-2003)")
        ok, why = self._probe("")
        self.assertFalse(ok)
        self.assertEqual(why, "", "a probe that failed for another reason was blamed on memory")

    def _release(self, playing, mode):
        seen = []

        def _quit(reason="quit-button"):
            seen.append(reason)
            return {"windowDestroyed": True}

        with mock.patch.object(CA, "window_mode_payload", lambda: {"mode": mode}), \
                mock.patch.object(CA, "_sp_playing_here", lambda: playing), \
                mock.patch.object(CA, "_os_input_idle_s", lambda: 0.0), \
                mock.patch.object(CA, "_quit_window_keeps_service", _quit):
            r = CA._vault_lane_free_view("the OCR worker was not started (%s)" % RAM_WHY)
        return r, seen

    def test_an_idle_pc_frees_its_view_for_the_lane_through_the_proofs_own_decision(self):
        r, seen = self._release(playing=False, mode="background")
        self.assertEqual(seen, ["the vault lane cannot prove itself and memory is short"],
                         "the view was not freed for the vault lane, or freed under the proof's reason: %s" % r)
        self.assertTrue(r.get("viewFreed"), r)
        self.assertIn("the vault lane cannot prove itself", r.get("say") or "")

    def test_a_pc_he_is_playing_on_keeps_its_window(self):
        r, seen = self._release(playing=True, mode="front")
        self.assertEqual(seen, [], "the console freed its window while he was playing: %s" % r)
        self.assertEqual(r.get("viewRelease"), "he is playing here")

    def test_the_sweep_hands_the_reason_to_its_note_and_to_the_release(self):
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            code = _code(fh.read())
        self.assertEqual(code.count("_vault_lane_free_view(_cn_why)"), 1,
                         "the vault sweep no longer asks the idle-PC release when memory is the reason")
        self.assertEqual(code.count('+ (" - %s" % _cn_why if _cn_why else ""))'), 1,
                         "the lane note no longer carries the memory reason")


RED_PROOF = [
    {"why": "REG-2003 - the OCR worker forgets why memory refused it, so the canary cannot say so",
     "file": "tv/tv_diablo.py",
     "find": '                self.ram_refused = str(_ram_why or "memory is short")   # REG-2003 - the canary names it\n',
     "replace": "                pass\n",
     "matches": 1},
    {"why": "REG-2003 - a worker that started keeps reporting the old memory refusal",
     "file": "tv/tv_diablo.py",
     "find": '            globals()["_OCR_RAM_SAID"] = False\n            self.ram_refused = ""\n',
     "replace": '            globals()["_OCR_RAM_SAID"] = False\n',
     "matches": 1},
    {"why": "REG-2003 - the failed probe drops the reason: every held reel says only 'could not be proven live'",
     "file": "tv/control_app.py",
     "find": '        self.why = "" if live else _ocr_ram_refusal()\n',
     "replace": '        self.why = ""\n',
     "matches": 1},
    {"why": "REG-2003 - the vault lane never asks the idle-PC release, so a short ALT never drains",
     "file": "tv/control_app.py",
     "find": "                        _vault_lane_free_view(_cn_why)\n",
     "replace": "                        pass\n",
     "matches": 1},
    {"why": "REG-2003 - the view is freed under the proof's reason, so the vault lane's release reads as a proof's",
     "file": "tv/control_app.py",
     "find": "            q = _quit_window_keeps_service(owed)\n",
     "replace": '            q = _quit_window_keeps_service("a proof is owed and memory is short")\n',
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
