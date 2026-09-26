"""A2 · step 1 — the printer and the reels: can the SWEEP START refuse when it must?

`self_arming.LOCKS` labels `vault.sweep_start` in its own words as *"step 1 — the printer and the
reels"*, and it is the lock his priority names first: the lowest bar (0.510), no prerequisites, and
the one that guards an action that SPENDS MONEY — "starts a paid sweep".

⚠⚠ THIS HARNESS NEVER STARTS A SWEEP. Every attempt is a state in which `chronicle_sweep_start`
MUST refuse, and the only thing counted is whether it did. A harness for a paid door that could
itself open the door would be the most expensive kind of test in this repo. There is no attempt
here whose success path runs.

⚠ AND IT NEVER TOUCHES HIS REAL JOB STATE. `_CHRON_JOB` and the lane list are swapped for the
duration of each attempt and restored in a `finally`, so a crash mid-attempt cannot leave the
console believing a sweep is running. [[feedback-fixtures-never-touch-live-data]]

THE THREE STATES STAY THREE, exactly as hover_wilson keeps them: LEAKS (a wrong input was NOT
refused) is the only failure. UNPROVEN is a measurement nobody has taken. [[unknown-stays-unknown]]
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _attempt_busy(ca, n=8):
    """A sweep is already running. Starting a second one would double-spend."""
    caught = 0
    orig = dict(ca._CHRON_JOB)
    try:
        for _ in range(n):
            ca._CHRON_JOB["running"] = True
            r = ca.chronicle_sweep_start(limit=1)
            # REFUSED is ok:False. Anything that reports started is a leak of a paid door.
            if isinstance(r, dict) and r.get("ok") is False and r.get("busy") is True:
                caught += 1
    finally:
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig)
    return n, caught


def _attempt_no_lane(ca, n=8):
    """No primary lane. A sweep with nothing to read with would spend and learn nothing."""
    caught = 0
    orig = getattr(ca, "_chron_lanes", None)
    if orig is None:
        return 0, 0                      # the accessor moved — UNPROVEN, never a pass
    try:
        ca._chron_lanes = lambda *a, **k: []
        for _ in range(n):
            r = ca.chronicle_sweep_start(limit=1)
            if isinstance(r, dict) and r.get("ok") is False and not r.get("busy"):
                caught += 1
    finally:
        ca._chron_lanes = orig
    return n, caught


def _attempt_bad_limit(ca, n=8):
    """A limit that cannot mean what it says. The runner slices `reel_dirs(hist)[:limit]`, so a
    NEGATIVE limit kept all but the last few — a caller asking for a small bounded sweep got a
    near-maximal paid one — and 0 is falsy, which meant "sweep everything" to someone who asked
    for nothing. Reachable from the route, which passes a negative straight through.

    ⚠ EVERY VALUE HERE MUST BE REFUSED, so this attempt can never open the door. That is the
    same property the two attempts above have and the reason this harness is safe to run at all:
    there is no success path in it. `None` is deliberately NOT tested — it legitimately means ALL.
    """
    caught = 0
    bad = (-5, 0, True, False, "x", 2.5, -1, 0.0)
    for i in range(n):
        r = ca.chronicle_sweep_start(limit=bad[i % len(bad)])
        if isinstance(r, dict) and r.get("ok") is False and not r.get("busy"):
            caught += 1
    return n, caught


def _refused_unstarted(r):
    return (isinstance(r, dict) and r.get("ok") is False and not r.get("busy")
            and not r.get("started"))


def _attempt_hist_file(ca, n=4):
    import tempfile
    caught = 0
    for i in range(n):
        f = tempfile.NamedTemporaryFile(prefix="sweepno_", delete=False)
        f.close()
        r = ca.chronicle_sweep_start(hist_dir=f.name, limit=1)
        if _refused_unstarted(r):
            caught += 1
        try:
            os.remove(f.name)
        except Exception:
            pass
    return n, caught


def _attempt_hist_blank(ca, n=4):
    caught = 0
    for _ in range(n):
        r = ca.chronicle_sweep_start(hist_dir="", limit=1)
        if _refused_unstarted(r):
            caught += 1
    return n, caught


def _attempt_hist_bytes(ca, n=4):
    caught = 0
    for i in range(n):
        r = ca.chronicle_sweep_start(hist_dir=b"/nope/not/a/dir/%d" % i, limit=1)
        if _refused_unstarted(r):
            caught += 1
    return n, caught


def _attempt_limit_list(ca, n=4):
    caught = 0
    for _ in range(n):
        r = ca.chronicle_sweep_start(limit=[])
        if _refused_unstarted(r):
            caught += 1
    return n, caught


def _attempt_limit_dict(ca, n=4):
    caught = 0
    for _ in range(n):
        r = ca.chronicle_sweep_start(limit={"n": 1})
        if _refused_unstarted(r):
            caught += 1
    return n, caught


def _attempt_force(ca, n=4):
    caught = 0
    for _ in range(n):
        r = ca.chronicle_sweep_start(limit=-3, force=True)
        if _refused_unstarted(r):
            caught += 1
    return n, caught


def _attempt_visit_bad_limit(ca, n=4):
    caught = 0
    for _ in range(n):
        r = ca.chronicle_sweep_start(limit=-3, visit=1)
        if _refused_unstarted(r):
            caught += 1
    return n, caught


class _StoppedThread(object):
    """Stands in for threading.Thread so a leak cannot spend a paid read."""
    spawned = []

    def __init__(self, *a, **k):
        _StoppedThread.spawned.append(self)

    def start(self):
        self.started = True


def _guarded(ca, **kw):
    """Call the door with the thread stubbed. -> (response, spawned_count). Restores the job flag."""
    import threading
    real = threading.Thread
    orig = dict(ca._CHRON_JOB)
    _StoppedThread.spawned = []
    threading.Thread = _StoppedThread
    try:
        try:
            r = ca.chronicle_sweep_start(**kw)
        except Exception:
            r = None
        return r, len(_StoppedThread.spawned)
    finally:
        threading.Thread = real
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig)


def _lock_answered(r):
    """The LOCK refused before the door ever read the argument under test.

    ⚠⚠ v3406 — THIS IS EVIDENCE ABOUT THE LOCK, NOT ABOUT THE DOOR, AND IT WAS COUNTED AS A
    REFUSAL. `chronicle_sweep_start` asks `self_arming.may("vault.sweep_start")` BEFORE it reads
    the lane list, and that lock FAILS CLOSED on a stale heart census — which is its state for the
    whole of any session that has touched a gate file. So every attack aimed at a guard sitting
    BELOW the lock got back a perfectly good ok:False, and `_refused_unstarted` said "caught".

    MEASURED 2026-09-22 with the census stale (`the heart census is STALE: the gate files have
    changed since it ran`): reverting the door's OWN lane guard — the isinstance check and the
    try/except that stop an unreadable lane list from starting a sweep — left this harness GREEN,
    exit 0, with lanesnone/lanesraise/lanesstr/lanesdict still reading PROVEN. The revert was real
    and its anchor matched exactly once. The attack simply never arrived.

    A zero needs a denominator and so does a one: `lanesnone 2 of 2 PROVEN` must mean the DOOR
    refused twice, never that the lock answered twice. [[zero-needs-a-denominator]]
    [[gate-blind-to-unexercised-input]] [[the-unjoined-end]]

    ⚠ NOT `_refused_unstarted`, deliberately: `_attempt_lock_shut_does_not_start` and
    `_attempt_lock_raises_does_not_start` REQUIRE the locked shape, and it is their subject.
    """
    return isinstance(r, dict) and "is LOCKED —" in str(r.get("why") or "")


def _tally(results):
    """-> (attempted, caught). An UNREACHED attempt is in NEITHER number.

    Dropping it from `caught` alone would read as a LEAK — an accusation against working code.
    Dropping it from both is the only honest shape, and it lands the claim on UNPROVEN, which
    score() already treats as work to do rather than a defect. [[strictness-that-closes-the-lane]]
    """
    reached = [v for v in results if v is not None]
    return len(reached), sum(1 for v in reached if v)


def _refused_quiet(ca, **kw):
    """-> True the DOOR refused · False it LEAKED · None the door was never REACHED."""
    r, n = _guarded(ca, **kw)
    if _lock_answered(r):
        return None
    return _refused_unstarted(r) and n == 0


def _attempt_hist_int(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir=i + 3, limit=1) for i in range(n))


def _attempt_hist_list(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir=["/tmp"], limit=1) for _ in range(n))


def _attempt_hist_float(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir=1.5, limit=1) for _ in range(n))


def _attempt_hist_space(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="  ", limit=1) for _ in range(n))


def _attempt_hist_newline(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="/nope/\n", limit=1) for _ in range(n))


def _attempt_hist_null(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="/nope/\x00", limit=1) for _ in range(n))


def _attempt_symlink_missing(ca, n=2):
    import tempfile
    seen = []
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="sweeplink_")
        try:
            link = os.path.join(d, "gone")
            os.symlink("/nope/not/here", link)
            seen.append(_refused_quiet(ca, hist_dir=link, limit=1))
        finally:
            shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — 432 sweeplink_* were left in his temp dir
    return _tally(seen)


def _attempt_symlink_file(ca, n=2):
    import tempfile
    seen = []
    for _ in range(n):
        d = tempfile.mkdtemp(prefix="sweeplink_")
        try:
            target = os.path.join(d, "f")
            io_path = open(target, "w")
            io_path.write("x")
            io_path.close()
            link = os.path.join(d, "link")
            os.symlink(target, link)
            seen.append(_refused_quiet(ca, hist_dir=link, limit=1))
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return _tally(seen)


def _attempt_busy_string(ca, n=2):
    caught = 0
    orig = dict(ca._CHRON_JOB)
    try:
        for word in ("yes", 1):
            ca._CHRON_JOB["running"] = word
            r = ca.chronicle_sweep_start(limit=1)
            if isinstance(r, dict) and r.get("ok") is False and r.get("busy") is True and not r.get("started"):
                caught += 1
    finally:
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig)
    return 2, caught


def _attempt_force_missing(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="/nope/force", limit=1, force=True) for _ in range(n))


def _attempt_visit_missing(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="/nope/visit", limit=1, visit=1) for _ in range(n))


def _attempt_reel_bad_limit(ca, n=2):
    return _tally(_refused_quiet(ca, limit=-2, reel_id="reel_x") for _ in range(n))


def _attempt_limit_nan(ca, n=2):
    return _tally(_refused_quiet(ca, limit=v) for v in (float("nan"), float("inf")))


def _attempt_limit_tuple(ca, n=2):
    return _tally(_refused_quiet(ca, limit=v) for v in ((1,), set()))


def _attempt_lanes_none(ca, n=2):
    import tempfile
    d = tempfile.mkdtemp(prefix="sweeplane_")
    real = ca._chron_lanes
    ca._chron_lanes = lambda *a, **k: None
    try:
        return _tally(_refused_quiet(ca, hist_dir=d, limit=1) for _ in range(n))
    finally:
        ca._chron_lanes = real
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_lanes_raise(ca, n=2):
    import tempfile
    d = tempfile.mkdtemp(prefix="sweeplane_")
    real = ca._chron_lanes
    def _boom(*a, **k):
        raise RuntimeError("lanes unreadable")
    ca._chron_lanes = _boom
    try:
        return _tally(_refused_quiet(ca, hist_dir=d, limit=1) for _ in range(n))
    finally:
        ca._chron_lanes = real
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_lock_shut_does_not_start(ca, n=2):
    import tempfile
    import self_arming as SA
    d = tempfile.mkdtemp(prefix="sweeplock_")
    real_may, real_lanes = SA.may, ca._chron_lanes
    SA.may = lambda lock: (False, "sabotage")
    ca._chron_lanes = lambda *a, **k: ["claude"]
    try:
        caught = 0
        for _ in range(n):
            r, spawned = _guarded(ca, hist_dir=d, limit=1)
            if (_refused_unstarted(r) and spawned == 0 and "LOCKED" in str((r or {}).get("why"))):
                caught += 1
        return n, caught
    finally:
        SA.may, ca._chron_lanes = real_may, real_lanes
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_lock_raises_does_not_start(ca, n=2):
    import tempfile
    import self_arming as SA
    d = tempfile.mkdtemp(prefix="sweeplock_")
    real_may, real_lanes = SA.may, ca._chron_lanes
    def _boom(lock):
        raise RuntimeError("unreadable")
    SA.may = _boom
    ca._chron_lanes = lambda *a, **k: ["claude"]
    try:
        caught = 0
        for _ in range(n):
            r, spawned = _guarded(ca, hist_dir=d, limit=1)
            if (_refused_unstarted(r) and spawned == 0
                    and "could not be read" in str((r or {}).get("why"))):
                caught += 1
        return n, caught
    finally:
        SA.may, ca._chron_lanes = real_may, real_lanes
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_a_legal_call_is_not_refused(ca, n=1):
    """The door is not jammed: limit None on a real empty directory is allowed.

    The thread is stubbed, so nothing is paid. Caught means it WOULD have started.
    """
    import tempfile
    import self_arming as SA
    d = tempfile.mkdtemp(prefix="sweepok_")
    real, real_may = ca._chron_lanes, SA.may
    ca._chron_lanes = lambda *a, **k: ["claude"]
    SA.may = lambda lock: (True, "the legal shape is allowed")
    try:
        r, spawned = _guarded(ca, hist_dir=d, limit=None)
    finally:
        ca._chron_lanes, SA.may = real, real_may
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind
    good = isinstance(r, dict) and r.get("ok") is True and r.get("started") is True and spawned == 1
    return 1, (1 if good else 0)


def _attempt_the_second_call_is_busy(ca, n=1):
    import tempfile
    d = tempfile.mkdtemp(prefix="sweepbusy_")
    import threading
    real = threading.Thread
    orig = dict(ca._CHRON_JOB)
    threading.Thread = _StoppedThread
    _StoppedThread.spawned = []
    import self_arming as SA
    real_lanes, real_may = ca._chron_lanes, SA.may
    ca._chron_lanes = lambda *a, **k: ["claude"]
    SA.may = lambda lock: (True, "the legal shape is allowed")
    try:
        first = ca.chronicle_sweep_start(hist_dir=d, limit=1)
        second = ca.chronicle_sweep_start(hist_dir=d, limit=1)
        good = (isinstance(first, dict) and first.get("started") is True
                and isinstance(second, dict) and second.get("ok") is False and second.get("busy") is True)
        return 1, (1 if good else 0)
    finally:
        threading.Thread = real
        ca._chron_lanes = real_lanes
        SA.may = real_may
        ca._CHRON_JOB.clear()
        ca._CHRON_JOB.update(orig)
        shutil.rmtree(d, ignore_errors=True)


def _attempt_lanes_is_a_string(ca, n=2):
    import tempfile
    d = tempfile.mkdtemp(prefix="sweeplane_")
    real = ca._chron_lanes
    ca._chron_lanes = lambda *a, **k: "claude"
    try:
        return _tally(_refused_quiet(ca, hist_dir=d, limit=1) for _ in range(n))
    finally:
        ca._chron_lanes = real
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_lanes_is_a_dict(ca, n=2):
    import tempfile
    d = tempfile.mkdtemp(prefix="sweeplane_")
    real = ca._chron_lanes
    ca._chron_lanes = lambda *a, **k: {"claude": True}
    try:
        return _tally(_refused_quiet(ca, hist_dir=d, limit=1) for _ in range(n))
    finally:
        ca._chron_lanes = real
        shutil.rmtree(d, ignore_errors=True)   # 2026-09-26 — sweeplane/lock/ok dirs were left behind


def _attempt_relative_missing(ca, n=2):
    return _tally(_refused_quiet(ca, hist_dir="no/such/hist", limit=1) for _ in range(n))


def _attempt_no_hist(ca, n=8):
    """A history directory that cannot hold reels. `hist_dir` was never checked at the door — the
    runner resolved it and called reel_dirs() on it — so naming a path that does not exist got
    ok:True, a started thread, and a job that discovered emptiness AFTER the paid door had opened.

    ⚠ Every path here is one that cannot exist, so this attempt has no success path either.
    `None` is deliberately not tested: it means "resolve the default" and is the normal call.
    """
    caught = 0
    for i in range(n):
        r = ca.chronicle_sweep_start(hist_dir="/nope/not/a/real/path/%d" % i)
        if isinstance(r, dict) and r.get("ok") is False and not r.get("busy"):
            caught += 1
    return n, caught


CLAIMS = (
    ("busy", "a second sweep cannot start while one is running — it would double-spend", _attempt_busy),
    ("lane", "a sweep cannot start with no lane to read with — it would spend and learn nothing", _attempt_no_lane),
    ("limit", "a sweep cannot start on a limit that cannot mean what it says — a negative one swept "
              "all but the last few, and 0 swept everything", _attempt_bad_limit),
    ("hist", "a sweep cannot start on a history directory that does not exist — it would open the "
             "paid door and find emptiness afterwards", _attempt_no_hist),
    ("histfile", "a file is not a directory of reels", _attempt_hist_file),
    ("histblank", "an empty path is not a history directory", _attempt_hist_blank),
    ("histbytes", "a bytes path is not a directory", _attempt_hist_bytes),
    ("limitlist", "a list is not a positive limit", _attempt_limit_list),
    ("limitdict", "a dict is not a positive limit", _attempt_limit_dict),
    ("force", "force=True does not override a limit that cannot mean what it says", _attempt_force),
    ("visit", "a visit id does not override a bad limit — the paid thread must not start",
     _attempt_visit_bad_limit),
    ("histint", "an integer is not a directory", _attempt_hist_int),
    ("histlist", "a list is not a directory", _attempt_hist_list),
    ("histfloat", "a float is not a directory", _attempt_hist_float),
    ("histspace", "a blank path is not a directory", _attempt_hist_space),
    ("histnl", "a path with a newline is not a directory", _attempt_hist_newline),
    ("histnull", "a path with a null byte does not start a sweep", _attempt_hist_null),
    ("linkgone", "a symlink to a missing path is not a reel directory", _attempt_symlink_missing),
    ("linkfile", "a symlink to a file is not a reel directory", _attempt_symlink_file),
    ("busyword", "a truthy running flag that is not True is still a sweep already running",
     _attempt_busy_string),
    ("forcemiss", "force=True does not create a directory that is not there", _attempt_force_missing),
    ("visitmiss", "a visit id does not create a directory that is not there", _attempt_visit_missing),
    ("reelbad", "a reel id does not make a negative limit legal", _attempt_reel_bad_limit),
    ("limitnan", "NaN and infinity are not positive limits", _attempt_limit_nan),
    ("limittuple", "a tuple or a set is not a positive limit", _attempt_limit_tuple),
    ("lanesnone", "a lane list of None does not start", _attempt_lanes_none),
    ("lanesraise", "a lane list that raises does not start", _attempt_lanes_raise),
    ("lanesstr", "the word claude in a string is not a lane list", _attempt_lanes_is_a_string),
    ("lanesdict", "a dict of lanes is not a lane list", _attempt_lanes_is_a_dict),
    ("lockshut", "a shut lock on a real empty directory does not start the thread",
     _attempt_lock_shut_does_not_start),
    ("lockraise", "a lock that raises on a real empty directory does not start the thread",
     _attempt_lock_raises_does_not_start),
    ("legal", "limit None on a real directory is allowed — the door is not jammed shut",
     _attempt_a_legal_call_is_not_refused),
    ("second", "the call that started is busy for the next one", _attempt_the_second_call_is_busy),
    ("relative", "a relative missing path is not a directory", _attempt_relative_missing),
)


def score():
    """-> [row]. One row per claim, in hover_wilson's exact shape so the console reads them alike."""
    try:
        import confidence
        import control_app as ca
    except Exception as e:
        return [{"claim": c, "what": w, "attempts": None, "caught": None, "wilson": None,
                 "state": "UNKNOWN",
                 "notes": ["the console module would not import (%s), so nothing was attempted — "
                           "that is UNKNOWN, not a pass" % str(e)[:70]]}
                for c, w, _ in CLAIMS]
    rows = []
    for claim, what, fn in CLAIMS:
        notes = []
        try:
            n, k = fn(ca)
        except Exception as e:
            n, k = None, None
            notes.append("the attempt itself raised (%s) — UNKNOWN, and the guard is unmeasured"
                         % str(e)[:90])
        if not n:
            state, wil = ("UNPROVEN" if n == 0 else "UNKNOWN"), None
            if n == 0:
                notes.append("no attempt could be made against this guard, so there is no evidence "
                             "in either direction")
        elif k < n:
            state = "LEAKS"
            wil = confidence.wilson_lower(k, n)
            notes.append("a state the sweep MUST refuse was accepted %d time(s) of %d — that is a "
                         "paid door opening on a wrong input" % (n - k, n))
        else:
            state, wil = "PROVEN", confidence.wilson_lower(k, n)
        rows.append({"claim": claim, "what": what, "attempts": n, "caught": k,
                     "wilson": wil, "state": state, "notes": notes})
    return rows


def bank_live(port=17772, timeout=4.0):
    """Ask the RUNNING console to start a sweep with a limit of -1.

    The route passes that limit through. The door must refuse and must not report started.
    An unreachable console banks nothing.
    """
    import json as _json
    import urllib.request as _u
    body = _json.dumps({"limit": -1}).encode("utf-8")
    try:
        req = _u.Request("http://127.0.0.1:%d/api/chronicle_sweep" % port, data=body,
                         headers={"Content-Type": "application/json"})
        r = _json.loads(_u.urlopen(req, timeout=timeout).read().decode("utf-8", "replace"))
    except Exception as e:
        return ("live NOT banked: the console on :%d did not answer (%s) — UNKNOWN, not a pass"
                % (port, type(e).__name__))
    if not (isinstance(r, dict) and r.get("ok") is False and not r.get("started")):
        return "live NOT banked: the running console did not refuse limit -1: %r" % (r,)
    import self_arming as SA
    SA.bank("vault.sweep_start", "live", "sweep_live", n=1, k=1, attacks=1,
            ref="live-bad-limit",
            note="the running console refused to start a sweep on limit -1")
    return "banked LIVE vault.sweep_start"


def bank_into_proof_queue(rows):
    """Bank each claim's aggregate under vault.sweep_start. -> {"banked", "skipped"}"""
    import self_arming as _sa
    banked, skipped = [], []
    for r in rows:
        n, k = r.get("attempts"), r.get("caught")
        if n is None or k is None:
            skipped.append("%s (%s — the probe could not answer, so it banks nothing)"
                           % (r.get("claim"), r.get("state")))
            continue
        # ⚠ v3406 — 0 of 0 IS NOT EVIDENCE, AND IT USED TO BANK AS attacks=1. A claim whose
        # every attempt was answered by the lock reaches here with n == 0, and banking it would
        # add a DISTINCT ATTACK to vault.sweep_start's confluence for an attack that never
        # arrived — the lock raising its own score on refusals it issued itself.
        if n == 0:
            skipped.append("%s (UNPROVEN — 0 attempts REACHED the door, so there is no attack "
                           "to bank; a lock that answers its own attackers must not be scored "
                           "by them)" % (r.get("claim"),))
            continue
        try:
            _sa.bank("vault.sweep_start", "sabotage", "sweep_wilson", n=n, k=k,
                     attacks=1,   # ⚠ ONE ROW = ONE ATTACK FUNCTION; `n` is how many times it was
                     # applied. Summing these across rows gives the DISTINCT attack count,
                     # which is what stops a Wilson score being bought by looping one idea
                     # over many inputs. See self_arming.bank() and REG-598.
                     ref=str(r.get("claim")), note=str(r.get("what") or "")[:200])
            banked.append("%s %d/%d" % (r.get("claim"), k, n))
        except ValueError as e:
            skipped.append("%s REFUSED: %s" % (r.get("claim"), str(e)[:120]))
    return {"banked": banked, "skipped": skipped}


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    rows = score()
    # ⚠⚠ v2940 (#75) — BANKING IS NOW DELIBERATE, BECAUSE AN AUDIT THAT WRITES EVIDENCE IS NOT AN
    # AUDIT. MEASURED 2026-09-11: all four wilson harnesses called bank_into_proof_queue()
    # unconditionally from main(), and all four are REGISTERED GATES (hover_wilson appears 8 times
    # in run_gates.py). So every `git push` wrote rows into his self-arming ledger as a SIDE EFFECT
    # of grading the tree — 333 rows across 18 axes, and roughly twenty of this session's pushes
    # contributed. Evidence must be banked because someone decided to, never because a gate ran.
    # ⚠ The FOLD was never the problem: `_fold` keys on (lock, kind, src, ref) and score() folds
    # before scoring, so repetition never inflated n — measured on console.pixel_rescue,
    # n == attacks == 16 and wilson == wilsonByAttack. Only the door was open.
    b = bank_into_proof_queue(rows) if "--bank" in argv else {"banked": [], "skipped": ["not banked: pass --bank to write evidence. An audit that writes is not an audit."]}
    live_note = bank_live() if "--bank" in argv else "live not asked — pass --bank"
    print("SWEEP WILSON — can the paid sweep refuse when it must?\n")
    print("  %-8s %9s %8s %8s  %s" % ("claim", "sabotages", "caught", "wilson", "state"))
    print("  " + "-" * 58)
    for r in rows:
        print("  %-8s %9s %8s %8s  %s" % (
            r["claim"], "?" if r["attempts"] is None else r["attempts"],
            "?" if r["caught"] is None else r["caught"],
            "—" if r["wilson"] is None else ("%.3f" % r["wilson"]), r["state"]))
    print()
    print("  " + live_note)
    if b["banked"]:
        print("  banked -> vault.sweep_start: " + ", ".join(b["banked"]))
    for sk in b["skipped"]:
        print("  NOT banked: " + sk)
    for r in rows:
        for n in (r["notes"] or []):
            print("  %-8s %s" % (r["claim"], n))
    print("\n  ⚠ no sweep was started. Every attempt is a state the door MUST refuse.")
    # ⚠ v3406 — SAY IT, never leave it to be inferred from a small number. A claim whose
    # attempts were all answered by the lock is UNPROVEN, and UNPROVEN read as PROVEN is the
    # whole defect this version exists for.
    _unreached = [r for r in rows if r.get("attempts") == 0]
    if _unreached:
        print("  ⚠ %d claim(s) never REACHED the door — vault.sweep_start answered first, so "
              "they are UNPROVEN, not passed: %s"
              % (len(_unreached), ", ".join(str(r.get("claim")) for r in _unreached)))
        print("    (that lock fails closed on a stale heart census — `python3 tv/heart2.py "
              "--prove` is what lets these attacks arrive)")
    # ⚠⚠ v2888 — WAS `return 0`, UNCONDITIONALLY. heart2 named this one of three gates that could
    # never go red however bad the answer got: it scored every sabotage and then discarded the
    # verdict. Its sibling hover-wilson already exits 1 on a LEAKS row, so this makes a law that
    # exists elsewhere apply here too rather than inventing one. MEASURED BEFORE ARMING, 2026-09-10:
    # 2 claims, 8 of 8 sabotages caught on each, 0 LEAKS — so arming blocks nothing today and catches the
    # first sabotage that ever gets through. An UNPROVEN claim still PASSES, loudly: nobody having
    # tried to break it yet is work to do, not a defect. [[the-unjoined-end]] [[regression-guard]]
    _leaks = [r for r in rows if r.get("state") == "LEAKS"]
    if _leaks:
        print("")
        print("LEAK - a deliberately WRONG input was NOT caught:")
        for _r in _leaks:
            print("   %s (%s): caught %s of %s sabotages"
                  % (_r.get("claim"), _r.get("what"), _r.get("caught"), _r.get("attempts")))
        return 1
    return 0


RED_PROOF = [
    {
        "why": "v3038 — the LIMIT refusal is mislabelled as contention. ⚠ DELIBERATELY NOT the "
               "guard itself, for the same reason the busy proof below gives: defeating the guard "
               "would let a real sweep START, and a heart2 sandbox does not set TV_HIST, so it "
               "could reach his real reels. This tamper leaves the door SHUT and spends nothing — "
               "it only makes the refusal claim `busy`, which `_attempt_bad_limit` requires to be "
               "absent. A caller then cannot tell a nonsense limit from a second sweep.",
        "file": "control_app.py",
        "find": '            return {"ok": False, "why": "a sweep needs a positive limit or none at all',
        "replace": '            return {"ok": False, "busy": True, "why": "a sweep needs a positive limit or none at all',
        "matches": 1,
    },
    {
        "why": "v3038 — the same for the HISTORY DIRECTORY refusal, and for the same safety reason: "
               "the door stays shut, nothing is spent, and the only thing broken is the caller's "
               "ability to tell 'that path cannot hold reels' from 'a sweep is already running'.",
        "file": "control_app.py",
        "find": '            return {"ok": False, "why": "there is no history directory at',
        "replace": '            return {"ok": False, "busy": True, "why": "there is no history directory at',
        "matches": 1,
    },
    {
        "why": "v2889 — the tamper drops the STRUCTURED `busy` flag while the refusal itself REMAINS, "
               "so a caller can no longer tell contention from any other refusal. That is v2206's "
               "documented failure in its own words: a cross-family review of v2204 \"refused the "
               "read as a lock and retried forever\". ⚠ DELIBERATELY NOT the busy GUARD: defeating "
               "that would let a real sweep START, and a heart2 sandbox does not set TV_HIST, so it "
               "could reach his real reels. This tamper spends nothing. ⚠ ANCHORED ON TWO LINES "
               "carrying `\"state\": dict(_CHRON_JOB)}` because the one-line form occurs THREE times "
               "— in chronicle_autoread_tick, chronicle_autoreel_tick AND chronicle_sweep_start — and "
               "a three-site tamper would redden for a broader reason than the one claimed. MEASURED "
               "against a shadowed control_app: busy LEAKS, sabotages=8 caught=0, exit 1, `lane` "
               "still PROVEN 8/8. [[sabotage-is-usually-the-wrong-one]] [[unknown-stays-unknown]]",
        "file": 'control_app.py',
        "find": '            return {"ok": False, "busy": True, "why": "a sweep is already running",\n                    "state": dict(_CHRON_JOB)}\n',
        "replace": '            return {"ok": False, "why": "a sweep is already running",\n                    "state": dict(_CHRON_JOB)}\n',
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main())
