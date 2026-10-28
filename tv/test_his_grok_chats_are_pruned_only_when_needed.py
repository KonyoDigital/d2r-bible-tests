# -*- coding: utf-8 -*-
"""#151 (REG-2743, his ruling 2026-10-28) - HIS GROK CHATS ARE PRUNED ON THEIR OWN, AND ONLY WHEN THEY HAVE TO BE.

"pruning your own Grok chats ... architecure and build and design something so fix it and prune automatically if needed."
grok_chat_prune runs after each disk-sign measurement: when the sessions folder is over its budget, or the disk is under
the ON AIR floor, it removes whole conversation folders oldest first - never a session Grok lists as open, never one
written in the last hour, never one younger than 7 days (1 day when the disk is under the critical floor), never anything
outside the sessions root - and writes a receipt. Not needed -> nothing is touched.

Every case builds its own sessions tree in a temp dir and removes for real there; his ~/.grok is never read.
[[feedback-fixtures-never-touch-live-data]] RED_PROOF below.
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
import fixture_tmp as _fx  # noqa: E402
_fx.contain()                 # every temp tree below lives in this run's own scratch, listed only through list_own
import grok_chat_prune as G  # noqa: E402

GB = 1000 ** 3
MB = 1000 ** 2


class HisGrokChatsArePrunedOnlyWhenNeeded(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="grok_prune_law_")
        self.root = os.path.join(self.d, "sessions")
        os.makedirs(self.root)
        self.now = time.time()
        self.registry = os.path.join(self.d, "active_sessions.json")
        self.receipt = os.path.join(self.d, "receipt.jsonl")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def chat(self, sid, size, age_days, cwd="%2FUsers%2Fhim"):
        p = os.path.join(self.root, cwd, sid)
        os.makedirs(p, exist_ok=True)
        f = os.path.join(p, "chat.jsonl")
        with open(f, "wb") as fh:
            fh.truncate(int(size))          # sparse: the law is about the arithmetic, not his disk
        t = self.now - age_days * 86400
        os.utime(f, (t, t))
        os.utime(p, (t, t))
        return p

    def live(self, *ids):
        with open(self.registry, "w", encoding="utf-8") as fh:
            json.dump([{"session_id": i, "pid": 1} for i in ids], fh)

    def run_once(self, free=50 * GB, floor=8 * GB, critical=6 * GB):
        return G.run(root=self.root, registry=self.registry, free_bytes=free, floor_bytes=floor, critical_bytes=critical,
                     receipt_path=self.receipt, now_s=self.now)

    def left(self):
        """The conversation folders still on the fixture tree; a link is never one. -> [id]"""
        out = []
        for c in _fx.list_own(self.root):
            cp = os.path.join(self.root, c)
            if not os.path.isdir(cp) or os.path.islink(cp):
                continue
            for e in _fx.list_own(cp):
                ep = os.path.join(cp, e)
                if os.path.isdir(ep) and not os.path.islink(ep):
                    out.append(e)
        return sorted(out)

    # ---- the baseline: nothing is needed, nothing goes -----------------------------------------------------------

    def test_BASELINE_not_needed_touches_nothing_however_old(self):
        self.chat("ancient", 300 * MB, 400)
        r = self.run_once()
        self.assertIsNone(r["need"], r)
        self.assertEqual(self.left(), ["ancient"], "a chat was pruned when nothing called for it")
        self.assertFalse(os.path.exists(self.receipt), "a receipt was written for a pass that removed nothing")

    # ---- over the budget -------------------------------------------------------------------------------------------

    def test_over_budget_prunes_oldest_first_down_to_the_target_and_keeps_live_and_young(self):
        self.chat("old30", 900 * MB, 30)
        self.chat("old20", 700 * MB, 20)
        self.chat("live40", 600 * MB, 40)
        self.chat("young2", 500 * MB, 2, cwd="%2Ftmp%2Fx")
        with open(os.path.join(self.root, "%2FUsers%2Fhim", "prompt_history.jsonl"), "w") as fh:
            fh.write("{}\n")
        self.live("live40")
        r = self.run_once()
        self.assertEqual(r["need"], "over-budget", r)
        self.assertEqual(self.left(), ["live40", "young2"], r["say"])
        self.assertLessEqual(r["after"], G.TARGET_BYTES)
        self.assertTrue(os.path.exists(os.path.join(self.root, "%2FUsers%2Fhim", "prompt_history.jsonl")),
                        "the prompt history beside the chats was removed")
        rows = [json.loads(l) for l in open(self.receipt, encoding="utf-8")]
        self.assertEqual([x["id"] for x in rows[-1]["removed"]], ["old30", "old20"], "the receipt does not say what went")

    def test_it_stops_at_the_target_and_takes_no_more(self):
        self.chat("a", 900 * MB, 60)
        self.chat("b", 900 * MB, 50)
        self.chat("c", 400 * MB, 40)
        r = self.run_once()
        self.assertEqual(self.left(), ["b", "c"], "it pruned past the target: %s" % r["say"])

    # ---- a short disk ----------------------------------------------------------------------------------------------

    def test_a_short_disk_prunes_until_the_floor_plus_margin(self):
        self.chat("a", 600 * MB, 60)
        self.chat("b", 600 * MB, 50)
        self.chat("c", 600 * MB, 40)
        # 7.9 GB free under an 8 GB floor: it needs floor + margin - free = 1.1 GB back, so a and b (1.2 GB) and no more
        r = self.run_once(free=7900 * MB, floor=8 * GB)
        self.assertEqual(r["need"], "disk-short", r)
        self.assertEqual(self.left(), ["c"], r["say"])

    def test_a_critical_disk_may_take_a_two_day_old_chat_but_never_one_written_this_hour(self):
        self.chat("two_days", 500 * MB, 2)
        self.chat("this_hour", 500 * MB, 0.01)
        r = self.run_once(free=3 * GB, floor=8 * GB, critical=6 * GB)
        self.assertEqual(self.left(), ["this_hour"], r["say"])

    def test_a_short_but_not_critical_disk_keeps_a_week(self):
        self.chat("two_days", 500 * MB, 2)
        r = self.run_once(free=7 * GB, floor=8 * GB, critical=6 * GB)
        self.assertEqual(self.left(), ["two_days"], r["say"])
        self.assertIn("younger than 7 day", r["say"])

    def test_an_unknown_disk_never_triggers_on_its_own(self):
        self.chat("old", 300 * MB, 90)
        r = self.run_once(free=None)
        self.assertIsNone(r["need"], r)
        self.assertEqual(self.left(), ["old"])

    # ---- what it must never do -------------------------------------------------------------------------------------

    def test_an_unreadable_live_registry_prunes_nothing(self):
        self.chat("old", 2500 * MB, 90)
        with open(self.registry, "w") as fh:
            fh.write("{not json")
        r = self.run_once()
        self.assertEqual(self.left(), ["old"], "it pruned while it could not tell which session is his live one")
        self.assertIn("could not be read", r["say"])

    def test_a_link_out_of_the_root_is_never_counted_or_followed(self):
        """A link inside the sessions root that points outside it is not his chat: its bytes never count toward the
        budget (or a big file elsewhere would get his real chats pruned), and the walk never enters it."""
        outside = tempfile.mkdtemp(prefix="grok_prune_outside_")
        try:
            big = os.path.join(outside, "his_big_file")
            with open(big, "wb") as fh:
                fh.truncate(2500 * MB)
            self.chat("old", 300 * MB, 90)
            os.symlink(outside, os.path.join(self.root, "%2FUsers%2Fhim", "linked"))
            r = self.run_once()
            self.assertIsNone(r["need"], "bytes behind a link out of the root were counted: %s" % r["say"])
            self.assertEqual(self.left(), ["old"], r["say"])
            self.assertTrue(os.path.exists(big))
        finally:
            shutil.rmtree(outside, ignore_errors=True)

RED_PROOF = [
    {"why": "REG-2743 - the live session is pruned like any old chat",
     "file": "grok_chat_prune.py",
     "find": "              if r[\"id\"] not in live and now_s - r[\"newest\"] >= max(LIVE_S, keep_s)]",
     "replace": "              if now_s - r[\"newest\"] >= max(LIVE_S, keep_s)]",
     "matches": 1},
    {"why": "REG-2743 - it prunes when nothing calls for it",
     "file": "grok_chat_prune.py",
     "find": "    need = \"both\" if (over and short) else \"over-budget\" if over else \"disk-short\" if short else None",
     "replace": "    need = \"over-budget\"",
     "matches": 1},
    {"why": "REG-2743 - the week of young chats is not kept",
     "file": "grok_chat_prune.py",
     "find": "    keep_s = (KEEP_DAYS_CRITICAL if critical else KEEP_DAYS) * 86400",
     "replace": "    keep_s = KEEP_DAYS_CRITICAL * 86400",
     "matches": 1},
    {"why": "REG-2743 - it does not stop at the target",
     "file": "grok_chat_prune.py",
     "find": "        if (not over or under_target) and disk_ok:\n            break\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2743 - an unreadable registry is read as no live session",
     "file": "grok_chat_prune.py",
     "find": "    except Exception:\n        return None\n    if not isinstance(rows, list):",
     "replace": "    except Exception:\n        return set()\n    if not isinstance(rows, list):",
     "matches": 1},
    {"why": "REG-2743 - the walk follows a link out of the root and counts what is behind it",
     "file": "grok_chat_prune.py",
     "find": "                        if not k.is_dir(follow_symlinks=False):\n                            continue\n",
     "replace": "                        if not k.is_dir():\n                            continue\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
