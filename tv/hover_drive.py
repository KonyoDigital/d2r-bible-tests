#!/usr/bin/env python3
"""MINI(AUTOMATIC) — the half that moves his cursor. HOVER ONLY, BY CONSTRUCTION.

slot_identity.py answers WHERE to look: item_groups() finds the items, next_target() picks the
next unexplained one, screen_point() turns a point in a captured frame into a point on his screen.
All of that is arithmetic and moves nothing. This module is the actuator, and it is the only file
in the tree that touches his pointer.

★ THERE IS NO CLICK IN THIS FILE, AND THAT IS THE DESIGN, NOT A SETTING.

    The only event it can build is kCGEventMouseMoved. It never constructs a mouse-down or a
    mouse-up, so no flag, no argument and no future caller can make it press anything. In D2R a
    left click on an occupied cell PICKS THE ITEM UP; a stray one during an automatic sweep would
    scatter his stash, and "it was disabled" is not the same guarantee as "it does not exist".
    A page-turn click is a separate job for a separate file, with its own refusal that the point
    is outside the grid. It is deliberately not here yet.

★ IT IS HIS SCREEN, AND HE IS PROBABLY USING IT. [[borrowed-surface]]

    The pointer is a shared surface. If he moves the mouse while this is walking, this stops —
    immediately, on the next step, by noticing the pointer is not where it was left. It does not
    fight him for it, and it does not resume by itself. It also puts the pointer back where it
    found it, so a sweep leaves no trace.

★ THREE REFUSALS BEFORE IT MOVES ANYTHING, and each returns a REASON rather than a bare False,
  because "it did not run" and "it ran and found nothing" are different facts nothing downstream
  can reconstruct. [[unknown-stays-unknown]]
"""

import time

# How far the pointer may drift from where we left it before we conclude HE moved it. A few px
# of slop, because a trackpad resting under a palm can jitter one or two and calling that "he
# took over" would abort every sweep on a laptop.
HAND_ON_MOUSE_PX = 6.0

# Nothing here runs unbounded. An automatic sweep that cannot end is the shape that held a core
# on this machine for 28 hours. [[unbounded-search-orphans]]
MAX_STEPS = 400
MAX_SECONDS = 900.0
DWELL_S = 0.42          # measured: D2R paints an item tooltip well inside 400ms
SETTLE_S = 0.06         # after the move, before the frame — the compositor needs a beat


def _quartz():
    """The Quartz bits, or (None, why). Import failure is a REASON, never a silent False."""
    try:
        from Quartz import (
            CGEventCreateMouseEvent, CGEventPost, CGEventCreate, CGEventGetLocation,
            kCGEventMouseMoved, kCGMouseButtonLeft, kCGHIDEventTap,
            CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID,
        )
    except Exception as e:
        return None, "quartz-import: %s" % str(e)[:90]
    return {
        "mk": CGEventCreateMouseEvent, "post": CGEventPost, "new": CGEventCreate,
        "loc": CGEventGetLocation, "moved": kCGEventMouseMoved,
        "lbtn": kCGMouseButtonLeft, "tap": kCGHIDEventTap,
        "winlist": CGWindowListCopyWindowInfo, "allwin": kCGWindowListOptionAll,
        "nullwin": kCGNullWindowID,
    }, None


def cursor_pos():
    """Where the pointer is now, in global display points, or (None, why)."""
    q, why = _quartz()
    if q is None:
        return None, why
    try:
        p = q["loc"](q["new"](None))
        return (float(p.x), float(p.y)), None
    except Exception as e:
        return None, "cursor-read: %s" % str(e)[:90]


def d2r_window_rect():
    """The screen rect of the SAME window tv_diablo captures, as (x, y, w, h), or (None, why).

    ⚠ IT MUST BE THE SAME WINDOW, not "a D2R-looking window". screen_point() maps a frame point
    through the capture's rect; if this returned a different window the arithmetic would be
    perfectly correct about the wrong rectangle and the pointer would land somewhere plausible
    and wrong. So the pick is delegated to tv_diablo.find_d2r_window_mac() and this only looks up
    the bounds of the id it returns. One chooser, one window.
    """
    q, why = _quartz()
    if q is None:
        return None, why
    try:
        import tv_diablo
        hit = tv_diablo.find_d2r_window_mac()
    except Exception as e:
        return None, "window-pick: %s" % str(e)[:90]
    if not hit:
        # v2351b — CARRY THE CHOOSER\'S OWN REASON. "no D2R game window is on screen" was a dead
        # end while the game WAS on screen: it named the verdict and not the cause, so the same
        # sentence covered "the game is shut", "the title was redacted", "Quartz refused" and
        # "the layer filter ate it" - four different faults with four different fixes.
        why = ""
        try:
            why = str(getattr(tv_diablo, "_PICK_WHY", "") or "")
        except Exception:
            why = ""
        return None, ("no D2R game window is on screen" + (" (%s)" % why[:160] if why else
                      " (the chooser gave no reason)"))
    wid = hit[0]
    try:
        wins = q["winlist"](q["allwin"], q["nullwin"]) or []
    except Exception as e:
        return None, "winlist: %s" % str(e)[:90]
    for w in wins:
        try:
            if int(w.get("kCGWindowNumber") or 0) != int(wid):
                continue
            b = w.get("kCGWindowBounds") or {}
            r = (float(b.get("X") or 0), float(b.get("Y") or 0),
                 float(b.get("Width") or 0), float(b.get("Height") or 0))
            if r[2] < 2 or r[3] < 2:
                return None, "the window reports a %gx%g rect, which is not a window" % (r[2], r[3])
            return r, None
        except Exception:
            continue
    return None, "the chosen window id %s is no longer in the window list" % wid


def move_cursor(x, y):
    """Move the pointer. Returns (True, None) or (False, why).

    ★ kCGEventMouseMoved AND NOTHING ELSE. No button event is constructed anywhere in this file.
    """
    q, why = _quartz()
    if q is None:
        return False, why
    try:
        x = float(x); y = float(y)
    except (TypeError, ValueError) as e:
        return False, "not a point: %s" % str(e)[:70]
    if x != x or y != y or x in (float("inf"), float("-inf")) or y in (float("inf"), float("-inf")):
        # NaN/Inf pass every range test ever written; screen_point learned this at v2335.
        return False, "the target is not a finite point (%r, %r)" % (x, y)
    try:
        ev = q["mk"](None, q["moved"], (x, y), q["lbtn"])
        if ev is None:
            return False, "the move event could not be built — is Accessibility granted?"
        q["post"](q["tap"], ev)
        return True, None
    except Exception as e:
        return False, "move: %s" % str(e)[:90]


def hand_is_on_the_mouse(expected, slop=HAND_ON_MOUSE_PX, _pos=None):
    """Did HE move the pointer since we put it at `expected`? -> (bool_or_None, why)

    None means we could not tell, which is NOT the same as no. A sweep that cannot read the
    pointer must stop, because the one thing it may never do is keep driving a surface it has
    stopped being able to observe. [[unknown-stays-unknown]] [[borrowed-surface]]
    """
    if expected is None:
        return None, "nothing was expected yet"
    # ⚠ THROUGH THE SEAM, NOT AROUND IT. This called cursor_pos() directly, so walk()'s injected
    # pointer was consulted for the MOVES and ignored for the CHECK — the clean-walk case aborted
    # on step 2 announcing "that is his hand" about a pointer nobody had touched. A seam that
    # only half the code goes through is not a seam; it is a way to test a path that does not
    # exist. Caught by driving the walk, which is the only reason those seams are here.
    # [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
    here, why = (_pos or cursor_pos)()
    if here is None:
        return None, why
    dx = abs(here[0] - expected[0]); dy = abs(here[1] - expected[1])
    if dx > slop or dy > slop:
        return True, "the pointer moved %.0f,%.0f px from where it was left — that is his hand" % (dx, dy)
    return False, None


def can_actually_move():
    """PROVE the pointer obeys, by moving it 1px and reading it back. -> (True, None)|(False, why)

    ⚠ READING THE CURSOR IS NOT PERMISSION TO MOVE IT. CGEventGetLocation works for any process;
    CGEventPost needs Accessibility, and WITHOUT IT IT FAILS SILENTLY — no exception, no return
    code, the pointer simply does not move. So a preflight built on "can I read the cursor and
    find the window" answers READY and then moves nothing, for ever, with every lamp green. That
    is the same shape as a second eye that is installed, authorised, and has never been asked:
    ready, authorised and ACTUALLY WORKING are three different questions and only the third one
    matters. [[grok-second-eye]] [[unknown-stays-unknown]]

    The receipt is a 1px twitch, immediately undone. It is the smallest thing that cannot be
    faked by a permission dialog nobody answered.
    """
    before, why = cursor_pos()
    if before is None:
        return False, "the pointer cannot be read (%s)" % why
    ok, why = move_cursor(before[0] + 1.0, before[1])
    if not ok:
        return False, why
    after, why2 = cursor_pos()
    move_cursor(before[0], before[1])          # put it back either way
    if after is None:
        return False, "the pointer could not be read back (%s)" % why2
    if abs(after[0] - (before[0] + 1.0)) > 2.0 or abs(after[1] - before[1]) > 2.0:
        return False, ("the move was posted and the pointer did not follow — macOS is dropping "
                       "the event, which is what Accessibility being ungranted looks like "
                       "(System Settings > Privacy & Security > Accessibility)")
    return True, None


def preflight():
    """Everything that must be true before the pointer moves. -> (ok, why, facts)

    Reported as one dict so a caller can SAY which condition failed rather than "it did not
    start". Every "no" here is a sentence a person can act on.
    """
    facts = {}
    q, why = _quartz()
    if q is None:
        return False, why, facts
    pos, why = cursor_pos()
    if pos is None:
        return False, "the pointer cannot be read (%s) — Accessibility is probably not granted" % why, facts
    facts["cursor"] = pos
    moves, why = can_actually_move()
    facts["pointerObeys"] = bool(moves)
    if not moves:
        return False, why, facts
    rect, why = d2r_window_rect()
    if rect is None:
        return False, why, facts
    facts["window"] = rect
    return True, None, facts


def walk(targets, frame_size, capture_rect, capture_mode=None, on_step=None,
         dwell_s=DWELL_S, max_steps=MAX_STEPS, max_seconds=MAX_SECONDS, _sleep=None,
         _move=None, _pos=None):
    """Hover each target in turn. Returns a report dict. MOVES ONLY; NEVER CLICKS.

    `targets` are points in FRAME space (what slot_identity hands out). They are converted here,
    one at a time, through screen_point() — not in a batch beforehand — because the window can be
    dragged mid-sweep and a batch of coordinates computed against an old rect would keep landing
    confidently in the wrong place. [[stale-reading]]

    `on_step(i, target, screen_xy)` is called after the dwell, and is where the caller grabs its
    frame. It is not given any way to click.

    The injection seams (_sleep/_move/_pos) exist so the whole walk can be driven in a test with
    no pointer and no window. A route this consequential that can only be exercised by actually
    moving his mouse is a route that will only ever be tested by accident.
    """
    import slot_identity

    sleep = _sleep or time.sleep
    move = _move or move_cursor
    getpos = _pos or cursor_pos

    rep = {"moved": 0, "stopped": None, "steps": [], "restored": False}
    started = time.time()

    home, why = getpos()
    if home is None:
        rep["stopped"] = "the pointer cannot be read (%s)" % why
        return rep

    expected = None
    for i, t in enumerate(targets or []):
        if i >= max_steps:
            rep["stopped"] = "the step bound (%d) — a sweep must be able to end" % max_steps
            break
        if (time.time() - started) > max_seconds:
            rep["stopped"] = "the time bound (%.0fs)" % max_seconds
            break

        # ── HIS HAND WINS, ALWAYS AND IMMEDIATELY ──────────────────────────────────────────
        took_over, why = hand_is_on_the_mouse(expected, _pos=getpos)
        if took_over is None and expected is not None:
            rep["stopped"] = "could not tell where the pointer is (%s) — stopping rather than " \
                             "driving a surface it cannot see" % why
            break
        if took_over:
            rep["stopped"] = why
            break

        # ⚠ (value, why), NOT a bare point. Every answering function in slot_identity returns a
        # pair — the `why` is how a refusal explains itself instead of arriving as a None nobody
        # can account for. The first cut of this loop treated the pair as the point and pushed a
        # tuple straight into the mover; it surfaced immediately because the walk is driveable
        # without a pointer, which is the whole reason those seams exist. [[the-unjoined-end]]
        sxy, why = slot_identity.screen_point(t, frame_size, capture_rect,
                                              capture_mode=capture_mode)
        if sxy is None:
            rep["steps"].append({"i": i, "target": t, "skipped": why or "outside the capture region"})
            continue

        ok, why = move(sxy[0], sxy[1])
        if not ok:
            rep["stopped"] = "the pointer would not move: %s" % why
            break
        expected = (float(sxy[0]), float(sxy[1]))
        rep["moved"] += 1
        sleep(SETTLE_S)
        sleep(dwell_s)
        rep["steps"].append({"i": i, "target": t, "screen": expected})
        if on_step is not None:
            try:
                on_step(i, t, expected)
            except Exception as e:
                rep["stopped"] = "the caller's on_step raised: %s" % str(e)[:90]
                break

    # ── PUT IT BACK. A sweep that leaves his pointer parked over a stash cell has changed his
    #    screen, and the whole point is that it does not. Attempted even after a stop, EXCEPT
    #    when the reason for stopping was that his hand is on it — moving it then would be
    #    yanking the pointer out from under him. [[borrowed-surface]]
    if not (rep["stopped"] and "his hand" in rep["stopped"]):
        ok, _ = move(home[0], home[1])
        rep["restored"] = bool(ok)
    return rep


if __name__ == "__main__":
    ok, why, facts = preflight()
    print("preflight: %s" % ("READY" if ok else "NO — " + str(why)))
    for k, v in sorted(facts.items()):
        print("   %-8s %s" % (k, v))
