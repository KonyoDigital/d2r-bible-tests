# -*- coding: utf-8 -*-
"""#273 (REG-2034) - THE PERF SWEEP CLOSES ITS BROWSER WHEN A RUN THROWS, AND SAYS WHICH RUN FAILED.

K_perf.js (CI Routine K) measures bible.html three times and keeps the best. The #231 eye on a May commit found
browser.close() only on the success path: the loop catches a throw and goes on, so every failed pass left a
Chromium running, and the catch said nothing - three failed runs read as 'all runs failed' with no reason.
Pure text, stdlib only: the close lives in a finally, and the loop's catch writes the failure to stderr (stdout is the
JSON line the workflow parses).
"""
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "K_perf.js")


def _code():
    with open(SRC, encoding="utf-8") as f:
        return "\n".join(l.split("//", 1)[0] for l in f.read().split("\n"))


class ThePerfSweepClosesItsBrowser(unittest.TestCase):

    def test_the_close_is_in_a_finally_after_the_launch(self):
        code = _code()
        self.assertEqual(code.count("chromium.launch()"), 1, "the sweep launches a browser in more than one place now")
        m = re.search(r"chromium\.launch\(\);\s*try \{(.*?)\} finally \{\s*await browser\.close\(\);\s*\}", code, re.S)
        self.assertIsNotNone(m, "browser.close() is not in a finally that follows the launch")
        self.assertNotIn("browser.close()", m.group(1), "a second close sits on the success path")

    def test_a_failed_run_is_reported_not_swallowed(self):
        m = re.search(r"try \{ runs\.push\(await measure\(\)\); \} catch \(e\) \{([^}]*)\}", _code())
        self.assertIsNotNone(m, "the run loop moved")
        self.assertIn("console.error(", m.group(1), "a failed run is swallowed again")


RED_PROOF = [
    {"why": "REG-2034 - the perf sweep closes its browser only on the success path again",
     "file": "K_perf.js",
     "find": "  } finally {\n",
     "replace": "    await browser.close();\n  } catch (e) { throw e; } {\n",
     "matches": 1},
    {"why": "REG-2034 - a failed perf run is swallowed again",
     "file": "K_perf.js",
     "find": "catch (e) { console.error('K_perf: run '",
     "replace": "catch (e) { void ('K_perf: run '",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
