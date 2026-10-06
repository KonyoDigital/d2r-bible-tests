# -*- coding: utf-8 -*-
"""#144 — each heart2 prove lane hands a port base. A suite derives its ports from it.

A lone run of a suite (no TV_LANE_PORT_BASE) keeps the port that suite has always used, so
`python3 tv/test_control.py` still stays off his live console. Two prove lanes therefore cannot
both land on 17971 / 17972.

The bind itself deletes nothing. What deletes a tracked file is a request from the OTHER sandbox
that arrives on the shared listener and runs inside this one. The file-watcher law records that
unlink, and records that the same request on a lane's own port leaves the neighbour's file in place.
"""
import os

ENV = "TV_LANE_PORT_BASE"
# His console, the agent default, Kai, the predicter, Chrome, and the ports a lone suite pins.
FORBIDDEN = frozenset({17771, 17772, 17781, 8848, 9222, 9223, 17971, 17972, 17973, 17994})
# shard_suite owns 17981 upward. Lanes start clear of that and of the pinned suite ports.
BASE0 = 21001
STRIDE = 4          # agent, control, render (TV_LAW_PORT), spare — lanes do not overlap


def base_for_lane(lane):
    """Port base for prove lane n (1-based). -> int. Adjacent lanes do not share a port."""
    n = int(lane)
    if n < 1:
        n = 1
    b = BASE0 + (n - 1) * STRIDE
    if any((b + i) in FORBIDDEN or not (1024 <= (b + i) <= 65535) for i in range(3)):
        raise ValueError("lane %s port base %s collides with a reserved port" % (lane, b))
    return b


def _parse(raw):
    raw = ("" if raw is None else str(raw)).strip()
    if not raw.isdigit():
        return None
    b = int(raw)
    if any((b + i) in FORBIDDEN or not (1024 <= (b + i) <= 65535) for i in (0, 1)):
        return None
    return b


def current_base():
    """The lane base in this process, or None when nobody handed one (or it is not safe)."""
    return _parse(os.environ.get(ENV, ""))


def agent_port(default):
    b = current_base()
    return str(b if b is not None else int(default))


def control_port(default):
    b = current_base()
    return str((b + 1) if b is not None else int(default))


def adopt(agent_default, control_default, keep=False):
    """Set TV_PORT and TV_CONTROL_PORT. A lane base wins over a value already in the environment.

    keep=True is the old setdefault: with no lane base, a port the caller already chose stays.
    """
    if current_base() is None and keep:
        os.environ.setdefault("TV_PORT", agent_port(agent_default))
        os.environ.setdefault("TV_CONTROL_PORT", control_port(control_default))
        return
    os.environ["TV_PORT"] = agent_port(agent_default)
    os.environ["TV_CONTROL_PORT"] = control_port(control_default)


def adopt_agent(default):
    """Set TV_PORT only. A lane base wins; otherwise `default` (the suite's historical port)."""
    os.environ["TV_PORT"] = agent_port(default)


def adopt_control(default):
    """Set TV_CONTROL_PORT only. A lane base's control port wins; otherwise `default`."""
    os.environ["TV_CONTROL_PORT"] = control_port(default)


def stamp(env, lane):
    """The ports one prove lane's gate runs with. Mutates `env` and returns it.

    REG-1820 - a TV_CONTROL_PORT already in `env` (run_gates.law_env's reserved dead port, or one the caller chose) SURVIVES:
    it was overwritten with base+1, a live port of this lane, and the law's ask reached a stranger again. Only an unset or
    his-console (17772) value takes the lane's own control port."""
    b = base_for_lane(lane)
    prev = _parse(env.get(ENV, ""))
    env[ENV] = str(b)
    env["TV_PORT"] = str(b)
    # REG-1857 - re-stamping one env for another lane moves the control port the PREVIOUS stamp gave it (that lane's
    # base+1), or it would sit beside this lane's other ports; a reserved dead port or a caller's choice is never moved.
    if env.get("TV_CONTROL_PORT", "") in ("", "17772") or (prev is not None and env.get("TV_CONTROL_PORT") == str(prev + 1)):
        env["TV_CONTROL_PORT"] = str(b + 1)
    env["TV_LAW_PORT"] = str(b + 2)
    return env
