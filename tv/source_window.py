#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One anchored source window, for every law that reads code as text.

⚠⚠ WHY THIS FILE EXISTS, TWICE OVER.

**1. A FIXED-SIZE WINDOW MEASURES THE AUTHOR'S GUESS, NOT THE FILE.** `src[i:i+400]` asks "is the
defect within 400 characters of here?" and answers a question nobody asked. When the region moves
past the bound, the text simply is not there — and under a NEGATIVE assertion (`assertNotIn`,
`assertFalse`) absence is exactly what makes the test pass. The law goes green because it could not
see, which is indistinguishable from green because there is nothing to see. Measured in this tree:
**68 fixed windows, 25 of them inside a function that also carries a negative assertion.**

**2. THE FIX ITSELF WAS COPY-DRIFTING.** `_between` had already been written FIVE separate times —
in test_coldread_empty_is_not_broken, test_the_river_is_wired_to_the_console,
test_a_dead_fill_keeps_its_content, test_no_control_is_buried_in_another_control and
test_a_seal_is_per_session — with three different signatures (`whence`, `what`, neither). Five
copies of a helper is five chances for one of them to grow a subtly different idea of what a
missing anchor means. [[copy-drift]]

★ THE RULE THAT MAKES THIS SAFE: **a missing end anchor RAISES.** Falling back to "the rest of the
file" or "as much as I could get" would reintroduce the whole defect one level up — a window that
quietly returns less than it promised is the thing being fixed. If the anchor is gone, the law's
subject has moved and the law must go red and say so, not read a shorter region and call it clean.
"""

__all__ = ["between", "after", "block", "WindowError"]


class WindowError(AssertionError):
    """An anchor was not found. AssertionError so unittest reports it as a failure, not an error —
    a law whose subject has moved has FAILED, and that is a finding, not a crash."""


def _need(hay, needle, start, what, which):
    i = hay.find(needle, start)
    if i < 0:
        raise WindowError(
            "the %s anchor %r was not found%s while reading %s. The region this law is about has "
            "MOVED or been renamed — that is a real finding and the law must go red for it, "
            "rather than reading a shorter window and reporting clean."
            % (which, needle, ("" if start == 0 else " after offset %d" % start), what))
    return i


def between(src, start, end, what="the region", include_end=False):
    """The text from `start` to `end`, both ANCHORED to real markers. -> str

    Neither end is a length. `end` is searched for AFTER `start`, so a marker that also appears
    earlier cannot collapse the window to nothing.
    """
    src = src or ""
    a = _need(src, start, 0, what, "start")
    b = _need(src, end, a + len(start), what, "end")
    return src[a:(b + len(end)) if include_end else b]


def after(src, start, *ends, **kw):
    """From `start` to whichever of `ends` comes FIRST. -> str

    For the common shape "this block, up to whatever structurally follows it" — the next `def`,
    the next `return`, a closing brace — where several are plausible and the nearest is correct.
    ⚠ If NONE of them is found it raises, for the same reason `between` does.
    """
    what = kw.pop("what", "the region")
    if kw:
        raise TypeError("after() got unexpected keyword(s): %s" % sorted(kw))
    src = src or ""
    a = _need(src, start, 0, what, "start")
    hits = [src.find(e, a + len(start)) for e in ends]
    hits = [h for h in hits if h >= 0]
    if not hits:
        raise WindowError(
            "none of the end anchors %r were found after %r while reading %s. Returning the rest "
            "of the file instead would be a fixed-size window with no number on it — the same "
            "defect wearing a different shape." % (list(ends), start, what))
    return src[a:min(hits)]


def block(src, start, what="the block", opener="{", closer="}"):
    """From `start` through its MATCHING closing brace. -> str

    The only honest window for a brace-delimited body. A character count cannot express "this
    block" — measured in this tree, guesses ran from 9,000 against a 10,475-char function to 400
    against a branch nobody had counted — and a textual end marker cannot either, because the same
    closer appears at every nesting depth inside.

    ⚠ It counts braces inside STRINGS and COMMENTS too, which is a real limitation and is stated
    rather than hidden: for the JS this repo greps it has been correct, and a body whose string
    literals carry unbalanced braces would need a parser, not a counter. Raising on an unbalanced
    run is the safe half — it can be wrong by refusing, never by silently returning less.
    """
    src = src or ""
    a = _need(src, start, 0, what, "start")
    o = src.find(opener, a)
    if o < 0:
        raise WindowError("no %r after %r while reading %s" % (opener, start, what))
    depth, i = 0, o
    while i < len(src):
        c = src[i]
        if c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return src[a:i + 1]
        i += 1
    raise WindowError(
        "the block opened at %r never closes while reading %s — returning what was scanned would "
        "be a fixed-size window with no number on it." % (start, what))
