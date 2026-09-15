# -*- coding: utf-8 -*-
"""The fleet card asks again when he comes back to look — and it is an EVENT, never a poll.

Konyo, on a card reading SETS 131/135 while his board held 132: "it didnt sync it and refresh as
fast as it should... it feels stale". It was. Every trigger the card had painted it ONCE:

    _fleetKick        at load
    the v2851 ladder  only AFTER a failed fetch, so never from a good-but-old reading
    the ↻ button      only when he presses it

A number true at load, shown in the present tense. That is REG-815 again — and this card has
already lost a trigger once: it used to refresh when the ADVANCED drawer filled, the card was
moved OUT of that drawer, and its refresh stayed behind. [[stale-reading]] [[the-unjoined-end]]

⚠ AND NOT BY POLLING. His ruling, and the right one: a tighter interval re-asks hundreds of times
to catch a change that happens a few times an evening, and a poll slower than its own interval
saturates the machine. The pair below costs nothing while he is elsewhere and fires exactly when
the card is about to be read — the same idiom the v2348 heartbeat already uses, because WebKit
suspends timers in a hidden window and the event is the only thing that still arrives.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass


def _kick_body():
    """The _fleetKick IIFE, brace-matched. -> str

    ⚠ BOTH ENDS ANCHORED. A fixed slice past the region reads as ABSENT, which would let this law
    report a missing listener that is merely beyond its window. [[source-reading-guard]]
    """
    h = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
    m = re.search(r"\(function _fleetKick\s*\(", h)
    if not m:
        return ""
    i = m.start()
    j = h.find("{", i)
    depth, k = 0, j
    while k < len(h):
        if h[k] == "{":
            depth += 1
        elif h[k] == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    return _code_only(h[i:k + 1])


def _code_only(js):
    """The CODE, with prose removed. -> str

    ⚠⚠ heart2 CAUGHT THIS LAW GOING BLIND TWICE ON ITS FIRST DRILL. The word `visibilitychange`
    also appears in the COMMENT that explains the listener, so deleting the listener left the
    assertion green. Read comments before judging a MEASUREMENT; ignore them when judging CODE.
    [[measured-true-read-wrong]] [[sabotage-is-usually-the-wrong-one]]
    """
    js = re.sub(r"/\*.*?\*/", " ", js, flags=re.S)
    return re.sub(r"(?m)//.*$", " ", js)


class TestTheFleetCardIsAskedAgainWhenHeLooks(unittest.TestCase):

    def setUp(self):
        self.body = _kick_body()
        self.assertTrue(self.body, "_fleetKick is gone — this law reads the wrong thing")

    def test_it_asks_again_when_the_window_becomes_visible(self):
        self.assertIn(
            "visibilitychange", self.body,
            "the card has no visibility trigger. It is painted at load and left standing in the "
            "present tense, which is the whole defect.")

    def test_it_asks_again_when_the_window_takes_focus(self):
        self.assertRegex(
            self.body, r"addEventListener\(\s*['\"]focus['\"]",
            "no focus trigger. visibilitychange alone misses an alt-tab back into an already "
            "visible window, which is how he actually returns to it.")

    def test_the_re_ask_is_throttled(self):
        """focus and visibilitychange BOTH fire on one alt-tab, and a window manager repeats."""
        self.assertRegex(
            self.body, r"now\s*-\s*_lastFleetAsk\s*<\s*\d+\s*\)\s*return",
            "nothing GUARDS the re-ask — a bare `_lastFleetAsk = now` records the time and lets "
            "every call through, so one alt-tab fires it twice and a bouncing window turns a "
            "cheap event into a request storm. The stamp is not the throttle; the early return "
            "is.")

    def test_the_card_is_never_put_on_a_timer(self):
        """His explicit ruling — the fix must not be a shorter poll."""
        for bad in ("setInterval", "setTimeout"):
            self.assertNotIn(
                bad, self.body,
                "the fleet re-ask is on a %s. A tighter interval re-asks hundreds of times to "
                "catch a change that happens a few times an evening, and a poll slower than its "
                "own interval saturates the machine. He ruled this out by name." % bad)


    def test_only_the_newest_ask_may_paint(self):
        """Found by the CODEX eye, a different family from the usual one — which was out of credit
        and recorded an EMPTY SEAT rather than agreement.

        _fleetRefresh is 38k characters with one fetch and two awaits and no abort. Two overlapping
        calls race and whichever resolves LAST paints. Until the focus/visibility triggers landed
        that was almost unreachable; they make it ordinary — an ask stalls, he returns past the
        throttle, the second ask paints CURRENT numbers, then the first resolves and paints OLDER
        ones over them. The stale card, arriving by a new road.

        ⚠ COUNTED, NOT MERELY PRESENT. One guard is not enough: every await is a place the world
        can move on, so a third await added later must come with a third guard or the race is
        silently reopened."""
        h = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        m = re.search(r"window\._fleetRefresh\s*=\s*async function\s*\(", h)
        self.assertIsNotNone(m, "_fleetRefresh is gone — this law reads the wrong thing")
        i = m.start()
        j = h.find("{", i)
        depth, k = 0, j
        while k < len(h):
            if h[k] == "{":
                depth += 1
            elif h[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        body = _code_only(h[i:k + 1])
        self.assertIn("window._fleetGen", body,
                      "no generation stamp — nothing can tell an old response from a new one")
        awaits = len(re.findall(r"\bawait\b", body))
        guards = len(re.findall(r"_gen\s*!==\s*window\._fleetGen", body))
        self.assertGreaterEqual(
            guards, awaits,
            "%d await(s) but only %d generation check(s). Every await is a point where a newer "
            "ask can overtake this one, so an unguarded await lets an older response paint over "
            "fresher numbers." % (awaits, guards))


class TestTheBlurProbeIsOffUnlessAsked(unittest.TestCase):
    """A diagnostic that fires by default is not a diagnostic, it is a shipped design change.

    `#th-shelfov`'s blur is the last untested suspect for the shelf paint void GROKBOT reported on
    two consecutive ticks (API open, scrollTop advancing, painting:true, pixels black until a
    relaunch) and for the ~1.5s repaint lag. Removing it is a VISIBLE change — 5.22% of pixels
    against a 0.71-0.74% same-frame control floor — so it may only happen when someone asks.
    """

    def setUp(self):
        h = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        m = re.search(r"\(function _blurProbe\s*\(", h)
        self.assertIsNotNone(m, "the blur probe is gone — this law reads the wrong thing")
        i = m.start()
        j = h.find("{", i)
        depth, k = 0, j
        while k < len(h):
            if h[k] == "{":
                depth += 1
            elif h[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        self.body = _code_only(h[i:k + 1])

    def test_it_reads_the_flag_before_it_touches_anything(self):
        """The guard must come FIRST. A probe that strips the blur and then checks the flag has
        already changed his console."""
        flag = min(x for x in (self.body.find("noblur=1"), self.body.find("__NOBLUR")) if x > -1)
        touch = self.body.find("backdropFilter")
        self.assertGreater(flag, -1, "the probe no longer looks for its flag at all")
        self.assertGreater(touch, -1, "the probe no longer touches the blur — it does nothing")
        self.assertLess(flag, touch,
                        "the probe touches backdropFilter at %d BEFORE reading its flag at %d, so "
                        "it fires on every load and the blur is gone for good" % (touch, flag))

    def test_it_returns_when_the_flag_is_absent(self):
        head = self.body[:self.body.find("backdropFilter")]
        self.assertRegex(
            head, r"noblur=1[^;]*\)\s*\)\s*return;|if\s*\(![^)]*noblur=1[^)]*\)[^;]*\)\s*return;|return;",
            "nothing returns before the blur is touched, so the flag is read and ignored")

    def test_the_probe_has_a_door_the_measuring_party_can_open(self):
        """GROKBOT is the only party that can measure the live window, and it reported the
        `?noblur=1` door unusable: no in-window URL bar, no evaluate_js HTTP door, and a patched
        launch that produced painting:true with ZERO TV DIABLO windows. A switch only a URL bar can
        reach is plumbing with no tap. The file flag survives the tvd-scan.sh relaunch it already
        performs. [[plumbing-with-no-tap]]"""
        ca = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        # ⚠ THE EMITTED TAG, NOT THE PATH. heart2 caught this BLIND on its first drill: the
        # string ".noblur_probe" survives in the isfile() check and in the comment explaining the
        # door, so deleting the line that actually INJECTS the flag left this green.
        self.assertIn(".noblur_probe", ca, "the server no longer looks for the flag file")
        self.assertIn("window.__NOBLUR=1", ca,
                      "the server looks for the flag and never EMITS anything, so touching the "
                      "file does nothing and the only party who can measure cannot turn it on")
        self.assertIn("__NOBLUR", self.body,
                      "the page no longer honours the server's flag, so touching the file does "
                      "nothing and the door is decorative")

RED_PROOF = [
    {
        'why': 'removes the file-flag door, leaving only a `?noblur=1` URL that the measuring party has already reported it cannot reach — the probe becomes unopenable and the blur theory untestable again',
        'file': 'control_app.py',
        'find': "            tag += b'<script>window.__NOBLUR=1;</script>'",
        'replace': '            pass',
        'matches': 1,
    },
    {
        'why': 'drops the flag guard, so the diagnostic fires on EVERY load and silently ships a visible change to his console — 5.22% of pixels against a 0.71-0.74% control floor — which nobody chose and which was never proven to fix anything',
        'file': 'control_ui.html',
        'find': "      if (!window.__NOBLUR && !/[?&]noblur=1\\b/.test(window.location.search || '')) return;",
        'replace': '      /* removed */',
        'matches': 1,
    },
    {
        'why': 'drops the guard after the json await, so a stalled older ask resolves last and paints OLDER fleet numbers over the fresher ones a newer ask already rendered — the stale card this whole version set out to fix, by a new road',
        'file': 'control_ui.html',
        'find': '      var j = await r.json();\n      if (_gen !== window._fleetGen) return;',
        'replace': '      var j = await r.json();',
        'matches': 1,
    },
    {
        'why': 'drops the visibility trigger, so the card goes back to being painted once at load and left standing in the present tense — the 131-while-the-board-held-132 defect',
        'file': 'control_ui.html',
        'find': "      document.addEventListener('visibilitychange', function () {\n        if (!document.hidden) _fleetAskAgain();\n      });",
        'replace': '      /* removed */',
        'matches': 1,
    },
    {
        'why': 'drops the focus trigger, so an alt-tab back into an already-visible window — how he actually returns to the console — never re-asks',
        'file': 'control_ui.html',
        'find': "      window.addEventListener('focus', _fleetAskAgain);",
        'replace': '      /* removed */',
        'matches': 1,
    },
    {
        'why': 'removes the throttle, so one alt-tab fires the re-ask twice and a bouncing window turns a cheap event into a request storm',
        'file': 'control_ui.html',
        'find': '      if (now - _lastFleetAsk < 10000) return;\n      _lastFleetAsk = now;',
        'replace': '      _lastFleetAsk = now;',
        'matches': 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
