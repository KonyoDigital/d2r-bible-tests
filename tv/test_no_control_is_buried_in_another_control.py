# -*- coding: utf-8 -*-
"""v2770 — A CONTROL INSIDE ANOTHER CONTROL ANNOUNCES ITSELF AS NEITHER.

`#ch-sweep-go` (open Chronicle Sweep) and `#ch-clear-all` (a control Konyo actively uses) were
`role="button" tabindex="0"` spans living INSIDE `<button id="btn-chronicle-inbox">`. HTML forbids
interactive content inside a button, and the price was measurable — Chrome 141 headless, the live
bay put on air, `Accessibility.getPartialAXTree`:

    BEFORE  #btn-chronicle-inbox  role=button  name="📜 Inbox 0 open Chronicle Sweep 🗑 clear all"
    AFTER   #btn-chronicle-inbox  role=button  name="📜 Inbox 0"

The parent button's accessible name had SWALLOWED both chip labels. A screen-reader user heard one
control offering three different actions, with no way to tell which one Enter would run, and the
two chips' own names were said aloud as part of a label belonging to something else.

=== ⚠⚠ WHAT THIS FILE REFUTES, AND WHY THAT IS KEPT ===
The task that produced it was written as "both chips are keyboard-unreachable; calling .focus()
leaves document.activeElement on BODY, so both onkeydown handlers are DEAD CODE". That is WRONG,
and the way it went wrong is the part worth remembering: the probe ran while

    body[data-state="off"] .rail .signal > * { display: none; }

had the whole live bay collapsed off-air. A display:none element is unfocusable for everyone, and
the INBOX BUTTON ITSELF measured focusable:false in the same run — the tell. Re-measured with the
bay on air, on the SHIPPED markup, before any change:

    programmatic .focus()   btn FOCUSABLE · ch-sweep-go FOCUSABLE · ch-clear-all FOCUSABLE
    real Tab from the btn   -> ch-sweep-go -> ch-clear-all
    real Enter on a chip    -> sweepJump   /  clearAll

So the handlers were never dead and Chrome never refused the focus. The defect was the accessible
NAME, not the focus. A zero needs a denominator, and so does a `false`.
[[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]

⚠ WHAT IS STILL UNMEASURED: his console runs in pywebview/WKWebView, not Chrome. Nothing here was
run against WebKit, so "Chrome allowed the focus" is not "every engine allows it". That is one more
reason the nesting had to go rather than be argued about.

=== ⚠ THE MOUSE PATH IS THE THING MOST EASILY BROKEN HERE ===
`.ch-clear` is a control he uses. Each chip stops its click from reaching the inbox modal, and the
old purple pill WAS the button, so a click anywhere in it opened the inbox. Both facts are pinned
below, because the fix moves the pill onto a plain row and would otherwise leave a dead strip that
looks clickable and does nothing. [[the-unjoined-end]] [[visual-regression-detector]]
"""
import io
import os
import re
import sys
import unittest
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()

#: ⚠ A GUARD THAT GREPS SOURCE MUST MATCH EXECUTABLE TEXT. This file's own subject matter is
#: discussed at length in HTML and JS comments right beside the code, and a law satisfied by prose
#: about the fix is a law that passes after the fix is deleted. Five separate guards in this repo
#: have failed exactly that way. The parser below ignores comments by construction; the JS
#: assertions strip them first.
_CODE = re.sub(r"/\*.*?\*/", " ", re.sub(r"<!--.*?-->", " ", UI, flags=re.S), flags=re.S)
_CODE = "\n".join(ln for ln in _CODE.split("\n") if not ln.strip().startswith("//"))


def _is_interactive(tag, attrs):
    """Does this element take focus / act as a control in its own right? -> bool"""
    if tag in ("button", "input", "select", "textarea", "details", "summary"):
        return True
    if tag == "a" and attrs.get("href") is not None:
        return True
    if (attrs.get("role") or "").strip().lower() == "button":
        return True
    ti = attrs.get("tabindex")
    if ti is not None:
        try:
            return int(ti) >= 0
        except ValueError:
            return False
    return False


class _Nesting(HTMLParser):
    """Walks the real element tree and records every control buried inside another one.

    ⚠ A PARSER, NOT A REGEX. The claim is about STRUCTURE — "is this element a descendant of a
    button" — and a regex over 23k lines cannot answer that. It also gets comment-stripping for
    free: HTMLParser routes `<!-- ... -->` to handle_comment, which this class does not implement,
    so prose about nested chips can never satisfy the law. [[source-reading-guard]]
    """

    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
            "param", "source", "track", "wbr"}

    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.stack = []          # [(tag, id, is_host)]
        self.buried = []         # [(child_id_or_tag, host_id_or_tag)]
        self.parent_of = {}      # id -> parent id/tag, for the sibling law
        self.attrs_of = {}       # id -> {attr: value}; laws read ATTRIBUTES, never text windows
        self.opened = 0

    @staticmethod
    def _is_host(tag, a):
        """Can this element swallow a descendant control's accessible name? -> bool

        ⚠ ROLE COUNTS, NOT ONLY THE TAG. My first cut asked `tag in ("button", "a")`, and a
        sabotage that turned the wrapper row into `role="button"` — re-burying all three controls
        one level higher — sailed straight through. A guard aimed at one spelling of a defect
        measures that spelling and nothing else.
        """
        return tag in ("button", "a") or (a.get("role") or "").strip().lower() in ("button", "link")

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        self.opened += 1
        ident = a.get("id") or (tag + "." + a.get("class", "").split(" ")[0])
        if self.stack:
            self.parent_of[ident] = self.stack[-1][1]
        if a.get("id"):
            self.attrs_of[a["id"]] = a
        if _is_interactive(tag, a):
            host = next((s for s in reversed(self.stack) if s[2]), None)
            if host is not None:
                self.buried.append((ident, host[1]))
        if tag not in self.VOID:
            self.stack.append((tag, ident, self._is_host(tag, a) and _is_interactive(tag, a)))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                return


def _parse():
    p = _Nesting()
    p.feed(UI)
    return p


def _between(src, a, b, what):
    """Anchored at BOTH ends. `src[i:i+N]` past a region reads as ABSENT, and this file's own
    subject has been mis-measured that way four times in one session."""
    i = src.find(a)
    if i < 0:
        raise AssertionError("the opening anchor for %s is gone: %r" % (what, a))
    j = src.find(b, i + len(a))
    if j < 0:
        raise AssertionError("the closing anchor for %s is gone: %r" % (what, b))
    return src[i:j]


class NoControlIsBuriedInAnotherControl(unittest.TestCase):

    # ── ⚠⚠ THE STRUCTURE ────────────────────────────────────────────────────────────────────
    def test_no_NEW_control_is_buried_inside_another_one(self):
        """★ THE LAW, AS A RATCHET. `document.querySelectorAll('button [role=button], button
        button, a [role=button]')` returned 2 on the shipped page and the task called the defect
        "contained". IT WAS NOT — that selector only asks about a native `<button>`/`<a>` host, and
        widening it to any element carrying role=button found two more, both real and both
        measured in the accessibility tree:

            #hd-hist-head  role=button  name="🗂 HISTORY EVERY RECORDED RUN see all →"
            #mind-tag      role=button  name="🧾 AI READS · LIVE 🔬"

        Their labels are fixed (see the aria-label law below); their NESTING is still there,
        because undoing it means splitting two headers into rows and giving each its own pixel
        pass. So the set is recorded here and may only ever SHRINK: a new one fails, and a fixed
        one that stays listed fails too, so the debt cannot quietly become permanent.
        [[sweep-dont-ask]] [[regression-guard]]
        """
        known = {("hd-hist-all", "hd-hist-head"), ("fx-open", "mind-tag")}
        p = _parse()
        self.assertGreater(p.opened, 500,
                           "only %d elements were parsed — the parser fell over long before the "
                           "console's markup, so a clean result here means nothing" % p.opened)
        got = set(p.buried)
        new = got - known
        self.assertEqual(set(), new,
                         "these controls are newly buried inside another control: %s. A control "
                         "may not contain interactive content — the host's accessible name "
                         "absorbs the child's label, and a screen reader then announces one "
                         "control offering several actions." % sorted(new))
        fixed = known - got
        self.assertEqual(set(), fixed,
                         "%s no longer nested — good, now delete it from `known` above so the "
                         "ratchet stays tight. A debt list that outlives the debt stops meaning "
                         "anything." % sorted(fixed))

    def test_every_remaining_host_says_its_own_name_out_loud(self):
        """★ THE HARM, PINNED SEPARATELY FROM THE STRUCTURE. An element with an explicit
        `aria-label` takes its name from that label instead of from its contents, so the buried
        control's text stops being read out as part of something else's name. Measured after:

            #hd-hist-head  name="HISTORY — tap to expand your run history"   (was ... "see all →")
            #mind-tag      name="AI READS — click to cycle reads · ..."      (was ... "🔬")

        While a nesting is allowed to exist at all, this is the thing that must not regress.
        """
        p = _parse()
        for _child, host in p.buried:
            a = p.attrs_of.get(host)
            self.assertIsNotNone(a, "the host %r has no id, so nothing can pin its name" % host)
            self.assertTrue((a.get("aria-label") or "").strip(),
                            "%r contains another control and has no aria-label, so its accessible "
                            "name is built from its contents — including the buried control's "
                            "label." % host)

    def test_the_two_chips_are_siblings_of_the_inbox_button(self):
        """The specific shape the law above was written for, pinned by name so a future edit that
        re-parents one chip fails HERE with the reason rather than only in the general sweep."""
        p = _parse()
        for chip in ("ch-sweep-go", "ch-clear-all"):
            self.assertIn(chip, p.parent_of, "%s is gone from the markup" % chip)
            self.assertEqual("ch-inbox-row", p.parent_of[chip],
                             "%s hangs off %r instead of the shared row — if that is the inbox "
                             "button again, its label is being swallowed" % (chip, p.parent_of[chip]))
        self.assertEqual("ch-inbox-row", p.parent_of.get("btn-chronicle-inbox"),
                         "the inbox button left the row it shares with the chips")

    # ── ⚠⚠ THE THINGS THE FIX COULD HAVE QUIETLY BROKEN ─────────────────────────────────────
    def test_the_pill_hides_and_shows_AS_ONE(self):
        """The purple box moved from the button to the row. If only the button keeps being hidden,
        an empty pill stays on screen with a lone `clear all` floating in it."""
        blk = _between(_CODE, "function paintChronicleInbox(){", "function _chInboxAgo(",
                       what="the inbox painter")
        self.assertIn("ch-inbox-row", blk,
                      "the painter never touches the row, so the pill that draws the border and "
                      "background is never hidden — the inbox 'disappears' as an empty box")
        self.assertRegex(blk, r"hidden\s*=\s*btn\.hidden",
                         "the row's visibility is derived independently of the button's. One "
                         "condition, computed once: two copies of the same expression drift, and "
                         "that already cost a permanently dead chip here (v2767).")

    def test_the_dead_strip_in_the_middle_still_opens_the_inbox(self):
        """The whole pill used to BE the button, so a click anywhere in it opened the modal. The
        button is only its left half now. Without the forwarder the gap between `📜 Inbox 0` and
        the chips looks clickable and does nothing — a control that silently stopped working."""
        self.assertIn("_chRow.onclick", _CODE,
                      "nothing forwards a click on the row's own padding to the inbox button, so "
                      "part of the pill is now decorative and looks live")
        fwd = _between(_CODE, "_chRow.onclick", "\n", what="the row click forwarder")
        self.assertIn("e.target === _chRow", fwd,
                      "the forwarder fires on ANY bubbled click, not only one that landed on the "
                      "row itself — every click on the button would open the inbox twice")
        self.assertIn("_chBtn.click()", fwd, "the forwarder does not actually reach the button")

    def test_each_chip_still_stops_its_click_reaching_the_inbox_modal(self):
        """★ `.ch-clear` is a control he uses. Measured after the change: a click on either chip
        fires ONLY its own handler — clearAll / sweepJump — and never the inbox modal.

        ⚠ THE ASSERTION IS ON THE `onclick` ATTRIBUTE, NOT ON THE TAG. Asking whether the tag
        anywhere contains `event.stopPropagation()` was satisfied by the chip's OTHER handler:
        deleting it from `onclick` left it in `onkeydown` and the law stayed green through a
        sabotage that genuinely broke the mouse path. [[sabotage-is-usually-the-wrong-one]]
        """
        p = _parse()
        for chip, call in (("ch-clear-all", "_chClearAll"), ("ch-sweep-go", "_chronWaitingJump")):
            a = p.attrs_of.get(chip)
            self.assertIsNotNone(a, "%s is gone from the markup" % chip)
            click = a.get("onclick", "")
            self.assertIn("stopPropagation", click,
                          "%s's onclick no longer stops the click, so clicking it also opens the "
                          "inbox modal on top of the action it just ran. onclick=%r"
                          % (chip, click))
            self.assertIn(call, click, "%s's onclick lost its handler: %r" % (chip, click))

    def test_each_chip_is_still_operable_from_the_keyboard(self):
        """Enter and Space, measured live: a real Enter on the focused chip fired sweepJump /
        clearAll. A chip with role=button and no key handler is a mouse-only control wearing a
        button's clothes."""
        p = _parse()
        for chip in ("ch-clear-all", "ch-sweep-go"):
            a = p.attrs_of.get(chip)
            self.assertIsNotNone(a, "%s is gone from the markup" % chip)
            self.assertEqual("0", a.get("tabindex"),
                             "%s cannot be reached by Tab any more" % chip)
            keys = a.get("onkeydown", "")
            self.assertIn("'Enter'", keys, "%s no longer answers Enter: onkeydown=%r" % (chip, keys))
            self.assertIn("' '", keys, "%s no longer answers Space: onkeydown=%r" % (chip, keys))

    def test_the_row_does_not_pretend_to_be_a_control_itself(self):
        """⚠ The wrapper must stay a plain box. Giving it role=button would recreate the exact
        defect one level up — a control containing three controls."""
        p = _parse()
        a = p.attrs_of.get("ch-inbox-row")
        self.assertIsNotNone(a, "the shared row is gone")
        self.assertIsNone(a.get("role"),
                          "the row took role=%r, so the three controls inside it are buried "
                          "again — one level higher and harder to see" % a.get("role"))
        self.assertIsNone(a.get("tabindex"),
                          "the row is focusable, which puts a stop in the tab order that does "
                          "nothing and announces nothing")


if __name__ == "__main__":
    unittest.main(verbosity=2)
