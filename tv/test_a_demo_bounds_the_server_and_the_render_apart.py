# -*- coding: utf-8 -*-
"""REG-1916 - THE SHELF DEMO BOUNDS THE SERVER AND THE RENDER APART.

j7_shelfStory refused the v3597 and v3601 pushes (and 2 of 13 over 2026-09-27..29) at one 15 s wait that paid for the
console's cold /api/sessions answer AND the shelf's render: measured on his console mid chronicle sweep, 9.2 s cold and
1.1 s warm (663 KB). The journey now asks the server first under its own 60 s bound and prints the time, and the 15 s
bound covers the render alone. The law reads the journey's code (comments stripped) because running it needs his live
console - the pre-push gate is where it runs.
"""
import io
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def _j7():
    s = io.open(os.path.join(HERE, "demo_console.mjs"), encoding="utf-8").read()
    a = s.index("async function j7_shelfStory(page) {")
    b = s.index("\nasync function ", a + 10)
    code = re.sub(r"/\*.{0,4000}?\*/", "", s[a:b], flags=re.S)
    return "\n".join(l for l in code.split("\n") if not l.strip().startswith("//"))


class TheShelfDemoBoundsTheServerAndTheRenderApart(unittest.TestCase):

    def test_the_server_is_asked_first_under_its_own_bound(self):
        c = _j7()
        ask = c.find("fetch('/api/sessions', { cache: 'no-store' })")
        refuse = c.find("if (!warm.ok) throw new Error(")
        click = c.find("await page.click('#btn-shelf');")
        self.assertGreaterEqual(ask, 0, "the journey no longer asks the server before the shelf (REG-1916)")
        self.assertGreaterEqual(refuse, 0, "a server that did not answer is no longer refused by name")
        self.assertGreaterEqual(click, 0, "the shelf click is gone - the law has no subject")
        self.assertLess(ask, click)
        self.assertLess(refuse, click)
        self.assertIn("setTimeout(() => res({ ok: false, why: 'no answer in 60 s' }), 60000)", c)

    def test_the_render_bound_is_unchanged(self):
        c = _j7()
        self.assertEqual(c.count("}, null, { timeout: 15000 });"), 1, "the render bound moved - REG-1916 split it, never widened it")


RED_PROOF = [
    {
        "why": "REG-1916 - a server that never answered is no longer refused by name; the 15 s render wait pays for it again",
        "file": "tv/demo_console.mjs",
        "find": "  if (!warm.ok) throw new Error(`/api/sessions did not answer (${warm.why}, ${warm.ms} ms) - the server half, not the shelf`);\n",
        "replace": "",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
