# -*- coding: utf-8 -*-
"""#223 — A RESIZE CALLBACK DEFERS ITS LAYOUT, SO THE BOARD NEVER THROWS A RESIZEOBSERVER LOOP.

MEASURED 2026-09-24: the render gate's `inbox` target went red three runs straight with one uncaught
page error — "ResizeObserver loop completed with undelivered notifications" — and was red on
v3493's page too, so the loop was old and only the timing (load ~4) was new. `_inboxSync` toggles a
class on the element it observes and publishes --inbox-top, which that element's own max-height
reads: run synchronously from the observer, it re-sizes what is being observed inside the delivery
loop. Every observer in bible.html now defers its work one animation frame, coalesced (`_roDefer`).
A push gate that goes red on machine load is a gate people learn to re-run until green.

  · STRUCTURAL: every `new ResizeObserver(` in the page's code hands it a deferred callback.
  · DRIVEN: `_roDefer` itself, executed in node — three synchronous calls run the work ONCE, and
    not before the frame.
RED_PROOF below.
"""
import io
import json
import os
import sys
import re
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


def _code():
    src = io.open(BIBLE, encoding="utf-8").read()
    src = re.sub(r"/\*.{0,6000}?\*/", " ", src, flags=re.S)       # bounded ([[source-reading-guard]])
    return "\n".join(l.split("//", 1)[0] if l.lstrip().startswith("//") else l for l in src.split("\n"))


class AResizeCallbackDefersItsLayout(unittest.TestCase):

    def test_every_observer_gets_a_deferred_callback(self):
        code = _code()
        total = code.count("new ResizeObserver(")
        deferred = code.count("new ResizeObserver(_roDefer(")
        print("   ResizeObservers in bible.html: %d, deferred: %d" % (total, deferred))
        self.assertGreaterEqual(total, 5, "premise: measured 5 observers on 2026-09-24 — re-measure")
        self.assertEqual(deferred, total, "%d observer(s) run their layout inside the delivery loop"
                                          % (total - deferred))

    def test_the_defer_runs_the_work_once_after_the_frame(self):
        src = io.open(BIBLE, encoding="utf-8").read()
        i = src.find("  var _roDefer = function(fn){")
        j = src.find("\n  };\n", i)
        self.assertTrue(i >= 0 and j > i, "_roDefer moved — this law is grading nothing")
        fn = src[i:j + len("\n  };\n")]
        js = ("var frames = [];\n"
              "var window = { requestAnimationFrame: function(f){ frames.push(f); return frames.length; } };\n"
              + fn +
              "var runs = 0; var d = _roDefer(function(){ runs++; });\n"
              "d(); d(); d();\n"
              "var before = runs; frames.splice(0).forEach(function(f){ f(); });\n"
              "var after = runs; d(); frames.splice(0).forEach(function(f){ f(); });\n"
              "console.log(JSON.stringify({before: before, after: after, again: runs}));\n")
        d = tempfile.mkdtemp(prefix="rodefer-")
        self.addCleanup(shutil.rmtree, d, True)
        f = os.path.join(d, "t.js")
        io.open(f, "w", encoding="utf-8").write(js)
        r = subprocess.run(["node", f], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr[:300])
        got = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(got["before"], 0, "the work ran inside the observer's delivery, not after the frame")
        self.assertEqual(got["after"], 1, "three calls in one frame ran the work %d time(s), not once" % got["after"])
        self.assertEqual(got["again"], 2, "a later frame's call was swallowed")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "#223 - the inbox observer runs its layout inside the delivery loop again (the ResizeObserver loop error that turned the render gate red under load)",
        "file": "bible.html",
        "find": "new ResizeObserver(_roDefer(_inboxSync)).observe(_ibxEl)",
        "replace": "new ResizeObserver(_inboxSync).observe(_ibxEl)",
        "matches": 1,
    },
    {
        "why": "#223 - the defer no longer coalesces: every observation in a frame queues its own layout pass",
        "file": "bible.html",
        "find": "      if (queued) return;\n      queued = true;\n",
        "replace": "",
        "matches": 1,
    },
]
