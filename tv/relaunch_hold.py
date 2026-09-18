# -*- coding: utf-8 -*-
"""v3301 — THE RELAUNCH INTERLOCK: hold it while a sweep runs, GREEN-LIGHT it when the sweep ends.

Konyo, 2026-09-17, ruling on task #38:

    "make sure to safegaurd the sweep so it cant relaunch until it does happen then a green light
     switch turns it on to relaunch when needed.. a safegaurd for this so sweeps run and relaunch
     doesnt kill them and they go through the river to get extracted and tallied and filtered and
     then deleted eventually"

⚠⚠ THE HOLD ALREADY EXISTED. THE GREEN LIGHT DID NOT — AND THAT IS THE WHOLE DEFECT.
`_exec_relaunch_soon` reads, in its own words: *"⛔ ABANDON, do not queue."* So a relaunch refused
because a sweep was reading is **dropped on the floor**. Nothing re-fires it when the sweep ends.
The console then keeps running the build it already had until some INDEPENDENT decision happens to
come round again — which, for the rescue path, is at least one escalation period later and may
never come at all. A safeguard that throws the request away is a refusal, not an interlock.

MEASURED, 2026-09-18, from the GrokBot seat's own `GB-L-LOOKED · NATIVE ... (mandatory relaunch)`
rows: **8 relaunches in one day**, gaps of 84 / 42 / 30 / 21 / 28 / 14 / 40 minutes — median ~30.
A chronicle sweep runs 60-110 minutes. **At that cadence a relaunch lands inside essentially every
sweep**, so "abandon on conflict" is not a rare corner; it is the normal path.

THREE THINGS HIS RULING REQUIRES, AND EACH FAILS DIFFERENTLY IF OMITTED:

  1. THE GREEN LIGHT — when the last in-flight thing finishes, the held relaunch FIRES BY ITSELF.
     Without it he has to notice and press again, which is the "waiting forever for a human" shape
     the watchdog rule exists to forbid. [[heart-first]]

  2. AN EXPIRY, MEASURED FROM THE FIRST ASK — a hold with no expiry is a recorded scar in this
     repo. ⚠ AND THE SUBTLE HALF: a repeat ask must NOT refresh the deadline. If pressing the
     button re-stamps `askedTs`, then pressing it every 30 minutes keeps the hold alive forever
     and the expiry is decorative. The deadline belongs to the FIRST ask; later asks only update
     the REASON. This is the no-expiry scar wearing a new coat.

  3. A VISIBLE HELD REASON — `held: true` with no sentence is a state nobody can act on. Every
     hold carries the in-flight sentence that caused it, and every drop carries how long it waited.

⚠ UNKNOWN IS A THIRD STATE AND IT MUST NOT FIRE. `release()` takes `ok` as True / False / **None**.
None means "nobody could tell what is in flight" — and an interlock that fires on UNKNOWN is an
interlock that relaunches into a sweep it simply failed to see. Not measuring is not idle.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

PURE FUNCTIONS OVER A PLAIN DICT, ON PURPOSE. control_app owns the dict; every rule lives here.
That is what lets the law run on a GitHub runner instead of needing his Mac — importing
control_app pulls in pywebview, the reel store and a live port. [[test-venue]] [[regression-guard]]
"""
import time

#: How long a held relaunch may wait before it is DROPPED. A chronicle sweep is 60-110 minutes
#: (measured), so this must clear the longest sweep with margin — and must not be unbounded.
#: ⚠ Derive from this constant in tests; never hardcode 7200. [[regression-guard]] §4
HOLD_TTL_S = 7200.0

#: Who may ask. Recorded so a fired relaunch can say what asked for it, weeks later.
ASKERS = ("button", "rescue", "drift")


def new_state():
    """A fresh register. -> dict. Every field explicit, so no reader guesses a missing key."""
    return {
        "held": False,
        "why": "",           # the in-flight sentence that caused the hold
        "asked": "",         # one of ASKERS
        "askedTs": 0.0,      # FIRST ask. The deadline is measured from here and never moved.
        "reasks": 0,         # how many times it was asked again while already held
        "expiresTs": 0.0,
        "firedTs": 0.0,      # last time the green light fired
        "droppedTs": 0.0,    # last time a hold expired UNFIRED
        "fired": 0,          # lifetime. ⚠ lifetime, not per-process — "has this EVER worked"
        "dropped": 0,
        "lastSay": "no relaunch has been held yet",
    }


def hold(state, why, asked, now=None):
    """Record that a relaunch was refused because something is in flight. -> the say string.

    ⚠ A RE-ASK DOES NOT MOVE THE DEADLINE. It updates the reason and counts itself, and that is
    all. See the docstring above: refreshing the expiry on every press is how a bounded hold
    silently becomes an unbounded one.
    """
    now = time.time() if now is None else float(now)
    why = str(why or "something is in flight")
    asked = str(asked or "?")
    if state.get("held"):
        state["reasks"] = int(state.get("reasks") or 0) + 1
        state["why"] = why                      # the reason may have changed; the deadline may not
        waited = now - float(state.get("askedTs") or now)
        state["lastSay"] = ("a relaunch has been held %ds (asked %d more time(s) since) — %s"
                            % (int(waited), int(state["reasks"]), why))
        return state["lastSay"]
    state.update({
        "held": True, "why": why, "asked": asked, "askedTs": now, "reasks": 0,
        "expiresTs": now + HOLD_TTL_S,
    })
    state["lastSay"] = ("a relaunch is HELD until the work in flight finishes — %s "
                        "(it will fire by itself; giving up after %dm)"
                        % (why, int(HOLD_TTL_S / 60)))
    return state["lastSay"]


def release(state, ok, why="", now=None):
    """Ask whether the held relaunch may go now. -> (fire, say).

    `ok` is the THREE-STATE answer from nothing_in_flight:
        True  -> nothing in flight     -> GREEN LIGHT
        False -> something in flight   -> keep holding (until the deadline)
        None  -> could not tell        -> keep holding. UNKNOWN NEVER FIRES.

    ⚠ THE EXPIRY IS CHECKED BEFORE `ok`, DELIBERATELY. A hold that has outlived its deadline is
    dropped whatever the world is doing — otherwise a permanently-stuck sweep (the exact thing
    `sweep_past_its_ceiling` exists for) would keep a hold alive past its own bound.
    """
    now = time.time() if now is None else float(now)
    if not state.get("held"):
        return False, "nothing is held"

    waited = now - float(state.get("askedTs") or now)
    if now >= float(state.get("expiresTs") or 0.0):
        state.update({"held": False, "droppedTs": now,
                      "dropped": int(state.get("dropped") or 0) + 1})
        state["lastSay"] = ("the held relaunch EXPIRED after %dm and was DROPPED, never fired — "
                            "the last thing holding it was: %s"
                            % (int(waited / 60), state.get("why") or "unknown"))
        return False, state["lastSay"]

    if ok is None:
        state["lastSay"] = ("still held after %ds — could not tell what is in flight%s, and "
                            "UNKNOWN does not open the door"
                            % (int(waited), (" (%s)" % why) if why else ""))
        return False, state["lastSay"]
    if not ok:
        state["why"] = str(why or state.get("why") or "something is in flight")
        state["lastSay"] = "still held after %ds — %s" % (int(waited), state["why"])
        return False, state["lastSay"]

    state.update({"held": False, "firedTs": now, "fired": int(state.get("fired") or 0) + 1})
    state["lastSay"] = ("GREEN LIGHT after %ds — the work that held it has finished, so the "
                        "relaunch asked for by the %s is going now"
                        % (int(waited), state.get("asked") or "?"))
    return True, state["lastSay"]


def contract(state, now=None):
    """The lane's answer in THE SHARED SUPERVISION VOCABULARY. -> dict.

    on / worked / lastTs / owed, so one supervisor can ask sixteen lanes one question. `owed` is
    1 while a relaunch is waiting and 0 when none is — a MEASURED zero, never a stand-in for
    "nobody asked". [[heart-first]] §3
    """
    now = time.time() if now is None else float(now)
    held = bool(state.get("held"))
    last = max(float(state.get("firedTs") or 0.0), float(state.get("droppedTs") or 0.0))
    return {
        "on": True,                       # the interlock is not switchable; it is a safeguard
        "worked": int(state.get("fired") or 0),
        "lastTs": int(last * 1000) if last else None,
        "owed": 1 if held else 0,
        "held": held,
        "heldFor": int(now - float(state.get("askedTs") or now)) if held else 0,
        "expiresIn": (int(float(state.get("expiresTs") or 0.0) - now) if held else None),
        "dropped": int(state.get("dropped") or 0),
        "why": state.get("why") or "",
        "say": state.get("lastSay") or "",
    }


def stuck(state, in_flight_ok, now=None, grace_s=90.0):
    """CORROBORATOR — two INDEPENDENT sides: the REGISTER vs THE WORLD. -> (bad, say).

    Side A is our own book: "a relaunch is held".
    Side B is `nothing_in_flight()`: "something is actually in flight".

    They are independent because B is computed by control_app from the sweep/mini/agent state and
    knows nothing about this register. If A says HELD while B has said CLEAR for longer than one
    tick window, then the green light is NOT WIRED — the release path is not being called, and the
    hold will sit there until its deadline and be dropped. That is precisely the failure this
    module was written to end, so it must be detectable rather than assumed. [[heart-first]] §1

    ⚠ `in_flight_ok is None` is NOT a fault here. Unknown means the world could not be read, which
    is a different complaint and belongs to whatever reads it.
    """
    now = time.time() if now is None else float(now)
    if not state.get("held"):
        return False, "nothing is held, so nothing can be stuck"
    if in_flight_ok is not True:
        return False, "held, and something is genuinely in flight — that is the interlock working"
    waited = now - float(state.get("clearSinceTs") or now)
    if waited < float(grace_s):
        return False, ("held while clear for %ds — inside the %ds grace, the green light gets a "
                       "tick to fire" % (int(waited), int(grace_s)))
    return True, ("a relaunch has been HELD for %ds while NOTHING has been in flight for %ds. "
                  "The green light is not firing — the release path is not being called, so this "
                  "hold will sit until it expires and be dropped."
                  % (int(now - float(state.get("askedTs") or now)), int(waited)))


def note_clear(state, in_flight_ok, now=None):
    """Stamp when the world last became CLEAR, so `stuck()` has a denominator. -> None."""
    now = time.time() if now is None else float(now)
    if in_flight_ok is True:
        if not state.get("clearSinceTs"):
            state["clearSinceTs"] = now
    else:
        state["clearSinceTs"] = 0.0
