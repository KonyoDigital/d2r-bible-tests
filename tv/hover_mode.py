"""MINI(AUTOMATIC) - the join between the plan and the pointer.

WHY THIS FILE EXISTS. v2338 shipped `hover_drive.walk()` (the actuator), v2332 shipped
`slot_identity.hover_targets()` (the plan), and v2338 shipped a readiness lamp on the console.
Nothing joined them. `walk()` had ZERO callers in the tree, so the button he was looking for did
not exist to be found - he asked "i dont see the button rendering anywhere either you said you
shipped this?" and he was right. Both ends were built, correct, and never connected.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

WHAT IT DOES. Hovers each occupied stash/inventory cell in turn so the game renders its TOOLTIP,
and calls back on every dwell so the caller can grab the frame. A stash GRID carries no names;
only the tooltip does. It MOVES ONLY - `hover_drive` contains no click event anywhere, and this
module never adds one.

FOUR WAYS IT STOPS, and he owns three of them: his hand touches the mouse (immediately, and the
pointer is NOT restored in that case because fighting him for it is worse than leaving it), the
stop flag, the step bound, the time bound. A sweep that cannot end is not a feature.
"""

import threading
import time

_LOCK = threading.RLock()
_STATE = {
    "running": False,
    "startedAt": None,
    "container": None,
    "planned": 0,
    "moved": 0,
    "stopped": None,      # why the last run ended; None while running
    "lastStep": None,
    "error": None,
}
_STOP = threading.Event()
_THREAD = None


def status():
    """A snapshot. `running` False with `stopped` None means it has never been run - which is a
    different fact from "it ran and finished", and the UI must be able to tell them apart."""
    with _LOCK:
        s = dict(_STATE)
    if s["startedAt"]:
        s["elapsedS"] = round(time.time() - s["startedAt"], 1)
    return s


def plan(occupied, frame_size, container="stash"):
    """The targets MINI would drive, without driving anything. -> (points, why)

    Separate from `start` on purpose: the plan can be simulated against real frames as often as
    anyone likes before a cursor is ever involved.
    """
    import slot_identity
    fw, fh = frame_size
    box, why = slot_identity.panel_box_for(fw, fh, container=container)
    if not box:
        return [], why or "no panel box for a %dx%d frame" % (fw, fh)
    groups, why2 = slot_identity.hover_targets(occupied, box, container=container)
    if why2:
        return [], why2
    pts = [g["point"] for g in groups if g.get("point")]
    skipped = [g for g in groups if not g.get("point")]
    if not pts:
        return [], ("nothing hoverable: %d group(s), none of them a single rectangle"
                    % len(groups))
    if skipped:
        return pts, ("%d of %d group(s) skipped - not one rectangle, so one point could hover "
                     "either of the items touching there" % (len(skipped), len(groups)))
    return pts, None


def stop():
    """Ask the sweep to end. Returns True if one was running."""
    was = status()["running"]
    _STOP.set()
    return was


def start(occupied, frame_size, capture_rect, container="stash", capture_mode=None,
          on_step=None, _walk=None):
    """Begin a sweep in the background. -> (ok, why)

    Refuses to start a second one: two sweeps fighting for one pointer is not a race anybody
    wins, and the failure would look like a possessed cursor.
    """
    global _THREAD
    with _LOCK:
        if _STATE["running"]:
            return False, "a sweep is already running - stop it first"

    pts, why = plan(occupied, frame_size, container=container)
    if not pts:
        return False, why or "nothing to hover"

    import hover_drive
    ok, pre_why, _facts = hover_drive.preflight()
    if not ok:
        return False, "the pointer cannot be driven right now: %s" % pre_why

    walk = _walk or hover_drive.walk
    _STOP.clear()
    with _LOCK:
        _STATE.update({"running": True, "startedAt": time.time(), "container": container,
                       "planned": len(pts), "moved": 0, "stopped": None, "lastStep": None,
                       "error": None})

    def _step(i, target, screen_xy):
        with _LOCK:
            _STATE["moved"] = i + 1
            _STATE["lastStep"] = {"i": i, "frame": list(target), "screen": list(screen_xy or [])}
        # ⚠⚠ WRITE DOWN WHICH CELL THIS WAS, BECAUSE NOTHING ELSE EVER WILL.
        # `target` is the point slot_identity planned — it IS the true cell, by construction,
        # because mini auto CHOSE it. Until now it updated the status dict above and was dropped,
        # so the one measurement `slot_identity.anchor_from_tooltip_rect` needs could never be
        # made from his own footage: it asks for "a real frame whose true cell is known", and the
        # only thing that knows was throwing the answer away at the moment of hovering.
        #
        # That single missing offset is why the frame door has never said YES, why no seal carries
        # `extracted`, and therefore why not one of his 40 reels can reach the pruning zone.
        # Six stations, one discarded pair. [[the-unjoined-end]] [[plumbing-with-no-tap]]
        #
        # ⚠ IT MAY NEVER STRAND THE POINTER. hover_calibration.record_step swallows its own
        # failures, and this call is outside the lock and before on_step so a slow disk cannot
        # hold the sweep's mutex or pre-empt the caller's own frame grab.
        try:
            import hover_calibration as _hc
            _hc.record_step(i, target, screen_xy, container=container, frame_size=frame_size)
        except Exception:
            pass
        if on_step:
            try:
                on_step(i, target, screen_xy)
            except Exception:
                pass          # a caller that cannot grab a frame must not strand the pointer
        if _STOP.is_set():
            raise _Stopped()

    def _run():
        try:
            rep = walk(pts, frame_size, capture_rect, capture_mode=capture_mode, on_step=_step)
            with _LOCK:
                _STATE["moved"] = rep.get("moved", _STATE["moved"])
                _STATE["stopped"] = rep.get("stopped") or "the sweep finished"
        except _Stopped:
            with _LOCK:
                _STATE["stopped"] = "you stopped it"
        except Exception as exc:
            with _LOCK:
                _STATE["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:160])
                _STATE["stopped"] = "it ended on an error"
        finally:
            with _LOCK:
                _STATE["running"] = False

    _THREAD = threading.Thread(target=_run, name="mini-automatic", daemon=True)
    _THREAD.start()
    return True, "sweeping %d target(s)" % len(pts)


class _Stopped(Exception):
    """His stop, raised out of the dwell callback so the walk unwinds at the next safe point."""
    pass
