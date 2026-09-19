# -*- coding: utf-8 -*-
"""A QUIT MUST SAY WHO ASKED, BECAUSE HIS CONSOLE DIED AND NOBODY COULD NAME THE CAUSE.

★ Grok Bot, driving the native seat as a user and ranking four traps worst-first:

    "Mule 2->3 arrow -> native window closed (`window gone (api-quit)` in log). No Esc sent."

His console was killed by clicking a UI arrow, and the log line was the same one a deliberate
exit writes. I could NOT reproduce it: `/api/quit` has exactly ONE caller in the page (the Escape
empty-stack handler) and the board iframe has none. So either an Escape reached that handler by a
path neither of us can see, or something POSTed the route directly.

⚠ IT CANNOT BE FIXED BLIND, SO IT IS MADE DIAGNOSABLE. Every quit now carries the name of whoever
asked; an unnamed one is recorded as UNATTRIBUTED. Since the Escape handler is the only page
caller, an UNATTRIBUTED line in his log is itself the finding — it means something else killed the
console, and the next occurrence carries its own evidence instead of being a mystery.

A cause nobody can name is a cause nobody can fix. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

APP = os.path.join(HERE, "control_app.py")
UI = os.path.join(HERE, "control_ui.html")


def _py_code():
    """control_app.py with `#` comment lines out — prose must not satisfy a law here."""
    with io.open(APP, encoding="utf-8", errors="replace") as f:
        src = f.read()
    return re.sub(r"(?m)^\s*#.*$", " ", src)


def _js_code():
    with io.open(UI, encoding="utf-8", errors="replace") as f:
        src = f.read()
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


class AQuitNamesWhoAsked(unittest.TestCase):

    @staticmethod
    def _branch(text, anchor):
        """-> the PYTHON block introduced by `anchor`, bounded by its own indentation, or "".

        ⚠ v3352 — a byte count is a guess about where a block ends; indentation is not. This walks
        from the anchor line to the first later non-blank line indented no further than it, which
        is exactly where the block closes. No braces are involved, so the string/regex hazard that
        forced two JS bounds back onto byte windows in this same version cannot arise here.

        ⚠ Returns "" when the anchor is absent, and callers must FAIL on that rather than assert
        over it — an empty string satisfies assertNotIn for anything at all.
        """
        i = text.find(anchor)
        if i < 0:
            return ""
        start = text.rfind("\n", 0, i) + 1
        ind = len(text[start:i]) - len(text[start:i].lstrip())
        lines = text[start:].split("\n")
        out, off = [lines[0]], len(lines[0]) + 1
        for ln in lines[1:]:
            if ln.strip():
                cur = len(ln) - len(ln.lstrip())
                if cur <= ind:
                    break
            out.append(ln)
            off += len(ln) + 1
        return "\n".join(out)

    def _route(self):
        src = _py_code()
        i = src.find('if path == "/api/quit":')
        self.assertGreater(i, -1, "the /api/quit route is gone — re-anchor this law")
        # ⚠ /api/quit is the LAST route in the file, so there is no following `if path == "` to
        # anchor against. The first cut asserted there was one and aborted every law with
        # "could not find the end of the route" — a law that refuses to read is not a strict law,
        # it is a broken one. Bounded by the next route OR the end of the file, whichever comes
        # first, so the slice is still both-ends anchored. [[source-reading-guard]]
        j = src.find('if path == "', i + 10)
        if j < 0:
            j = len(src)
        return src[i:j]

    def test_the_route_reads_an_attribution(self):
        blk = self._route()
        self.assertIn('"from"', blk,
                      "/api/quit does not read WHO asked, so a console death is indistinguishable "
                      "from a deliberate exit after the fact — which is why Grok Bot could only "
                      "report it as a mystery")

    def test_an_unnamed_quit_is_recorded_as_UNATTRIBUTED(self):
        """⚠ NOT a default that reads like a cause. 'api-quit' alone looked like an explanation and
        explained nothing; UNATTRIBUTED says plainly that nobody claimed it. [[unknown-stays-unknown]]"""
        blk = self._route()
        self.assertIn("UNATTRIBUTED", blk,
                      "an unnamed quit falls back to something that reads like a cause. The whole "
                      "point is that an unclaimed quit must ANNOUNCE that it is unclaimed")

    def test_the_attribution_reaches_the_thing_that_PRINTS(self):
        """★ THE JOINT. Reading `from` and then discarding it would be a fix that ships and
        attributes nothing — the shape this session has hit four times."""
        blk = self._route()
        self.assertIn("_request_console_exit(_qwho", blk,
                      "the attribution is read and then NOT passed to the exit path, so the line "
                      "in his log still says nothing about who asked")
        self.assertNotIn('_request_console_exit("api-quit"', blk,
                         "the exit is still requested with the old fixed string, so the "
                         "attribution never reaches the log")

    def test_an_UNATTRIBUTED_quit_is_REFUSED_and_the_console_stays_up(self):
        """★ v3280 — THE WORST-RANKED TRAP STOPS BEING AN OBSERVATION AND BECOMES A REFUSAL.

        Grok Bot, driving the native seat as a user: *"Mule 2->3 arrow -> native window closed
        (`window gone (api-quit)` in log). No Esc sent."* — ranked WORST of four traps. His
        console died from a vault arrow click.

        v3262 made it DIAGNOSABLE — every quit names who asked, an unnamed one records as
        UNATTRIBUTED. That was right while the cause was unknown, and it has been waiting for a
        recurrence ever since: an observation, not a fix.

        MEASURED, and it is what makes refusing safe rather than reckless:

            page callers of /api/quit      bible.html 0 · control_ui.html 1
            that one caller                names itself `escape-empty-stack`
            script / shell / python        ZERO across the whole repo
            the ✕ and webview-return       go through _request_console_exit DIRECTLY, never
                                           over HTTP — untouched by this

        So every legitimate HTTP quit that exists already names itself, and an unattributed one is
        by construction something nobody wrote. Performing it kills his console on the word of a
        caller that will not say who it is.
        """
        r = self._route()
        self.assertIn("if not _qfrom:", r,
                      "an unattributed quit is still PERFORMED — the console can still be killed "
                      "by a caller that will not name itself")
        i = r.find("if not _qfrom:")
        branch = self._branch(r, "if not _qfrom:")
        self.assertTrue(branch, "could not bound the refusal branch")
        self.assertIn('"refused": True', branch, "the refusal does not say it refused")
        # ⚠⚠ v3352 — ADDED BECAUSE A RED-PROOF CAME BACK BLIND WITH A CORRECT MATCH COUNT OF 1.
        # Silencing the stdout line changed a real byte and this law stayed GREEN, which by the
        # standing rule means the LAW is weak rather than the sabotage wrong. It asserted the JSON
        # answer and nothing else — but the JSON goes to whoever called, while the PRINT is how he
        # sees that his console refused to die. The route's own comment says the point is that "a
        # human with curl is told the remedy rather than left guessing"; that human reads stdout.
        self.assertIn("/api/quit REFUSED", branch,
                      "the refusal is silent on stdout, so a console that declined to close looks "
                      "exactly like one that ignored the request")
        self.assertIn("return", branch, "the refusal falls through and quits anyway")
        # and it must refuse BEFORE the thing that actually exits
        self.assertLess(i, r.find("_request_console_exit"),
                        "the refusal is checked AFTER the exit has already been requested")

    def test_a_WHITESPACE_name_does_not_defeat_the_refusal(self):
        """★ v3281 — found by the cross-family eye on v3280, and real.

        `str(body.get("from") or "")` treats `"   "` as truthy, so `{"from": "   "}` satisfies
        `not _qfrom` and walks straight past the refusal. **A guard that a space defeats is not a
        guard**, and whitespace is exactly what a sloppy caller or a fuzzer sends.

        ⚠ No known trigger today — the one real caller sends a string literal — but the entire
        point of the refusal is callers nobody has written yet.
        """
        r = self._route()
        i = r.find('.get("from")')
        self.assertGreater(i, -1, "the attribution is no longer read from the body")
        self.assertIn(".strip()", r[i:i + 200],
                      "a whitespace-only `from` still counts as naming yourself, so the refusal "
                      "is defeated by a single space")

    def test_the_refusal_TELLS_HIM_HOW_to_quit_on_purpose(self):
        """⚠ IT IS A REFUSAL, NOT A LOCK. Any caller may still quit by saying who it is — one
        field. A guard that blocks an action without naming the remedy turns a bug into a
        mystery, which is the shape this whole ticket started as."""
        r = self._route()
        branch = self._branch(r, "if not _qfrom:")
        self.assertTrue(branch, "could not bound the refusal branch")
        self.assertIn("from", branch, "the refusal never names the field that would allow it")
        self.assertIn("still running", branch,
                      "the refusal does not say the console survived, so a caller cannot tell a "
                      "refusal from a failed exit")

    def test_the_only_page_caller_still_NAMES_itself_or_the_refusal_locks_him_out(self):
        """⚠⚠ THE GUARD ON THE WHOLE CHANGE. Refusing unattributed quits is only safe while the
        ONE real caller attributes itself. If that ever stops, Escape-to-quit silently dies and
        this law is the thing that says why."""
        js = _js_code()
        self.assertIn("'/api/quit'", js, "the page no longer calls the quit route at all")
        i = js.find("'/api/quit'")
        self.assertIn("escape-empty-stack", js[i:i + 400],
                      "the page's quit no longer names itself, so v3280's refusal would block "
                      "the one legitimate exit")

    def test_the_only_page_caller_NAMES_itself(self):
        """If the one legitimate caller did not name itself, every quit would read UNATTRIBUTED
        and the signal would be worthless — a flag that is always on."""
        js = _js_code()
        i = js.find("'/api/quit'")
        self.assertGreater(i, -1, "the page no longer calls /api/quit — re-anchor this law")
        self.assertIn("escape-empty-stack", js[i:i + 400],
                      "the Escape handler does not name itself, so a legitimate exit is also "
                      "recorded as UNATTRIBUTED and the signal cannot distinguish anything")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "removing the attribution guard lets an unnamed caller kill his console again — the "
               "whole defect this law was written for. The branch then cannot be bound either, so "
               "both the presence assertion and every assertion about its contents go red.",
        "file": "tv/control_app.py",
        "find": "            if not _qfrom:",
        "replace": "            if False:",
        "matches": 1,
    },
    {
        "why": "silencing the refusal line leaves a caller with a console that did not close and "
               "nothing on stdout saying why — a refusal nobody can see is the shape this law "
               "exists to refuse.",
        "file": "tv/control_app.py",
        "find": '"\\U0001F6D1 /api/quit REFUSED — unattributed. The console was NOT closed."',
        "replace": '"quit"',
        "matches": 1,
    },
]
