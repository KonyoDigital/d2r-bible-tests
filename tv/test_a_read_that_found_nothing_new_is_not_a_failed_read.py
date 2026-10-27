# -*- coding: utf-8 -*-
"""#158.2 (GrokBot, the vault on his real frames) - A READ THAT FOUND NOTHING NEW IS NOT A FAILED READ.

vaultIntake answered ok: (new items) > 0. A frame read cleanly that showed only items he already owns was posted as
ok:false, so the receipt ledger counted every such re-read as an error - "0 of 39 real reads" - beside the server's own
sentence for it ("read fine - nothing on this screen to count"). ok is whether the READ worked now (no screenshot failed,
no AI-service error); total stays the new items, `read` is everything read, and `why` says which kind of nothing it was;
the TV path posts the reason a failed read carries, so its receipt says it.

Driven on the whole page in node (window._vaultIntakeVerdict), and on the two places that hand it out. RED_PROOF below.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import vault_page_node as VPN  # noqa: E402

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
BODY = r"""
(function(){
var V = window._vaultIntakeVerdict;
OUT.known = V(0, 3, 0, '');
OUT.fresh = V(2, 3, 0, '');
OUT.empty = V(0, 0, 0, '');
OUT.failed = V(0, 0, 1, '');
OUT.ai = V(0, 0, 0, 'AI service unreachable - HTTP 503');
})();
"""


@unittest.skipUnless(VPN.NODE, "node is absent on this machine - UNMEASURED here, never a pass")
class AReadThatFoundNothingNewIsNotAFailedRead(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.o = VPN.run(BODY, timeout=300)

    def test_the_page_booted(self):
        self.assertEqual(self.o["__boot"]["errors"], [], self.o["__boot"])

    def test_nothing_new_is_ok_and_says_so(self):
        k = self.o["known"]
        self.assertTrue(k["ok"], "a clean read of items he already owns was posted as a failure (#158.2): %r" % k)
        self.assertEqual((k["total"], k["read"]), (0, 3))
        self.assertEqual(k["why"], "read 3 items, none new")
        self.assertEqual(self.o["fresh"], {"ok": True, "total": 2, "read": 3, "why": ""})
        self.assertTrue(self.o["empty"]["ok"])
        self.assertIn("nothing on this screen", self.o["empty"]["why"])

    def test_a_failed_read_is_a_failure_with_its_reason(self):
        self.assertFalse(self.o["failed"]["ok"])
        self.assertEqual(self.o["failed"]["why"], "1 screenshot failed to read")
        self.assertFalse(self.o["ai"]["ok"])
        self.assertIn("HTTP 503", self.o["ai"]["why"])

    def test_both_doors_hand_the_verdict_out(self):
        with open(BIBLE, encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count("    return Object.assign(_vaultIntakeVerdict((typeof _newThis !== 'undefined' ? _newThis : logged.length),\n"), 1,
                         "vaultIntake no longer answers through the one verdict")
        self.assertEqual(src.count("                                 err: (_vr && !_vr.ok && _vr.why) || undefined,   /* #158.2 - the receipt says why */\n"), 1,
                         "the TV path's receipt no longer carries why a read failed")


RED_PROOF = [
    {"why": "#158.2 - a clean read that found nothing new is a failure again",
     "file": "bible.html",
     "find": "    return { ok: true, total: n, read: r,\n",
     "replace": "    return { ok: n > 0, total: n, read: r,\n",
     "matches": 1, "needs": "node"},
    {"why": "#158.2 - a failed screenshot reads as a clean read again",
     "file": "bible.html",
     "find": "    if (e || aiErr)\n      return { ok: false, total: n, read: r,\n",
     "replace": "    if (aiErr)\n      return { ok: false, total: n, read: r,\n",
     "matches": 1, "needs": "node"},
    {"why": "#158.2 - the TV receipt drops why the read failed",
     "file": "bible.html",
     "find": "                                 err: (_vr && !_vr.ok && _vr.why) || undefined,   /* #158.2 - the receipt says why */\n",
     "replace": "",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
