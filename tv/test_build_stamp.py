"""v2466 — the build stamp may drop its decoration, but never half a word.

⚠ THE DEFECT, AND WHY IT COUNTS DESPITE BEING DELIBERATE. v1691.1 capped this badge at 180px and
ruled "id + date must survive; the name is the decoration that clips". That rule is right and this
guard does not touch it. What went wrong underneath it: the version NAMES grew to 45 characters in
a box that fits about 24, so the decoration was ALWAYS cut mid-word — measured on the shipped
stamp, 259px of 437 hidden, rendering "v2465 · 2026-09-03 · THE ...".

TWO INDEPENDENT COLD CROSS-FAMILY READS called that fragment an unintended cut-off. The second one
matters most: on the same screenshots it correctly identified a genuinely deliberate overlay
elsewhere as "intentional UI behaviour, not a rendering error", reversing its own earlier call that
I had refuted by measurement. It distinguishes deliberate from broken, and it called this broken.

THE LAW PINNED HERE IS NOT "the name must show". It is: **whatever the stamp renders, it renders
whole.** Dropping the decoration is allowed. Ending mid-word is not.

⚠ It SKIPS, never passes, without headless Chrome — an unmeasured stamp is UNKNOWN.
"""
import json
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
BIBLE = "file://" + os.path.join(os.path.dirname(HERE), "bible.html")

_PROBE = r"""(function(){
  var all = document.querySelectorAll('body > div'), hit = null;
  for (var i = 0; i < all.length; i++){
    if (/^v\d+ · 20\d\d-/.test((all[i].textContent || '').trim())) { hit = all[i]; break; }
  }
  if (!hit) return JSON.stringify({found:false});
  return JSON.stringify({found:true, txt:(hit.textContent||'').trim(),
    scrollW:hit.scrollWidth, clientW:hit.clientWidth,
    hasTitle:!!hit.getAttribute('title'),
    title:(hit.getAttribute('title')||'').slice(0,60)});
})()"""


def _read():
    import render_check as rc
    if not rc._chrome_up():
        return None
    try:
        tab = rc._Tab(BIBLE)
        time.sleep(9)
        raw = tab.ev(_PROBE)
        tab.close()
        return json.loads(raw) if raw else None
    finally:
        rc._chrome_down()


class TheStampRendersWhole(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = _read()

    def setUp(self):
        if not self.d:
            self.skipTest("no headless Chrome — the stamp is UNMEASURED, which is UNKNOWN not a pass")
        if not self.d.get("found"):
            self.skipTest("no build stamp found on the page — UNKNOWN, never a pass")

    def test_the_stamp_is_not_clipped(self):
        d = self.d
        self.assertLessEqual(
            d["scrollW"], d["clientW"] + 1,
            "the build stamp renders %dpx of text in %dpx and ends mid-word: %r. v1691.1 allows the "
            "NAME to be dropped — it does not allow half of it to be shown. Two independent cold "
            "reads called this exact fragment a rendering bug."
            % (d["scrollW"], d["clientW"], d["txt"]))

    def test_the_id_and_date_always_survive(self):
        """v1691.1's actual rule, which this guard protects rather than replaces: whatever else
        goes, the answer to 'is this tab stale?' must stay on screen."""
        import re
        self.assertRegex(self.d["txt"], r"^v\d+ · 20\d\d-\d\d-\d\d",
                         "the stamp no longer leads with id and date, which is the one thing "
                         "v1691.1 said must survive: %r" % self.d["txt"])

    def test_the_full_note_is_still_recoverable(self):
        """Dropping the decoration is only honest because the whole thing is one hover away."""
        self.assertTrue(self.d["hasTitle"],
                        "the stamp drops its name and offers no title — the text would be gone "
                        "with no way back, which is worse than the truncation it replaced")


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
