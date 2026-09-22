#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record a Claude look against the locks that already cleared their attack bar.

The kind `cross-family` is a different model family trying to break the real code.
This file does not invent that look. It reads a verdict Claude wrote, and it banks
`attacks=1` only for a surface whose answer says the claim held. A seat that is
signed out, over quota, or silent banks nothing.

`--wait` retries from now until 20:00 local. That is the window after the 19:00 renewal.
"""
import datetime
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

REPO = os.path.dirname(HERE)
SURFACES = (
    "frame.release",
    "printer.stream",
    "vault.sweep_start",
    "chronicle",
    "fleet",
    "roster",
)
ROUTES_FOR = {
    "frame.release": ("frame.release",),
    "printer.stream": ("printer.stream",),
    "vault.sweep_start": ("vault.sweep_start",),
    "chronicle": ("chronicle.runeword", "chronicle.set", "chronicle.unique"),
    "fleet": ("fleet.runewords", "fleet.sets", "fleet.uniques"),
    "roster": ("roster.runeword", "roster.set", "roster.unique"),
}
DEAD_SEAT = (
    "not logged in",
    "please run /login",
    "auth_required",
    "usage limit",
    "hit your usage",
    "overloaded",
    "api key has expired",
)

PROMPT = """You are reviewing code you did not write. Read the files. Try to REFUTE each claim. Do not edit anything.

Claim frame.release — tv/frame_authority.py seal_releases_frames releases only when extracted covers name, location and provenance, or when examinedEmpty is exactly True, extracted is an empty list, and rows is the integer 0. False, 0.0, the string "0", and a missing count must not release.

Claim printer.stream — tv/printer.py stream never invents a station answer. An owner that raises leaves that station UNKNOWN with a why. A tombstone that is not a record is reels None, not 0. A bool reel id is not walked under the name True.

Claim vault.sweep_start — tv/control_app.py chronicle_sweep_start does not start a thread when limit is negative, a bool, a list, NaN, or when hist_dir is not a directory. A lane list that is not a list, or that raises, does not start. force=True does not override a bad limit.

Claim chronicle — tv/chronicle_routes.py _source_ok is true only while bible.html still contains that route's source token.

Claim fleet — tv/fleet_routes.py _defines is true only for an assignment window.NAME =, not for a mention.

Claim roster — tv/roster_routes.py _declared is false for an emptied body and for a declaration that survives only in a comment.

Return one JSON object and nothing else. Keys: frame.release, printer.stream, vault.sweep_start, chronicle, fleet, roster. Each value is {"holds": true or false, "attack": "the input that breaks it, or empty", "why": "one sentence"}.
"""


def seat_is_dead(text):
    low = (text or "").lower()
    return any(s in low for s in DEAD_SEAT)


def parse_verdict(text):
    """-> dict | None. None means this text is not a review."""
    if not text or seat_is_dead(text):
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        doc = json.loads(text[start:end + 1])
    except Exception:
        return None
    if not isinstance(doc, dict):
        return None
    return doc


def ask_claude(timeout_s=420):
    """-> (text, returncode). A dead seat comes back as text plus a non-zero code."""
    try:
        proc = subprocess.run(
            ["claude", "-p", "--allowedTools", "Read", "--max-turns", "12", PROMPT],
            cwd=REPO, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or "") + "\n" + (e.stderr or "")).strip()
        return out or "timeout", 124
    except OSError as e:
        return "claude could not be started: %s" % e, 127
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return text, proc.returncode


def bank_held(doc, verdict_path):
    """Bank attacks=1 for each surface Claude said held. -> (banked, held_back)."""
    import self_arming as SA
    banked, held_back = [], []
    head = json.dumps(doc, ensure_ascii=False)[:140]
    for surface in SURFACES:
        cell = doc.get(surface)
        locks = ROUTES_FOR[surface]
        if not isinstance(cell, dict) or cell.get("holds") is not True:
            held_back.append((surface, cell))
            continue
        why = str(cell.get("why") or "").strip()
        if not why:
            held_back.append((surface, cell))
            continue
        note = "Claude reviewed %s and the claim held: %s" % (surface, why[:220])
        for lock in locks:
            SA.bank(lock, "cross-family", "crossfamily_claude",
                    n=1, k=1, attacks=1, ref=surface,
                    note=note[:400])
            banked.append(lock)
    return banked, held_back


def wait_and_review(log_path, verdict_path, status_path, until_hour=20):
    """Retry Claude until `until_hour` local. Write one status line."""
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    deadline = datetime.datetime.now().replace(hour=until_hour, minute=0, second=0, microsecond=0)
    last = ""
    while True:
        text, code = ask_claude()
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write("\n--- %s code=%s ---\n%s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), code, text[:4000]))
        doc = parse_verdict(text) if code == 0 else None
        if doc:
            with open(verdict_path, "w", encoding="utf-8") as fh:
                fh.write(text)
            banked, held_back = bank_held(doc, verdict_path)
            line = "DONE: banked %d — %s — held back %s" % (
                len(banked), ", ".join(banked),
                ",".join(s for s, _c in held_back) or "none")
            with open(status_path, "w", encoding="utf-8") as fh:
                fh.write(line + "\n")
            print(line)
            return 0 if not held_back else 2
        last = (text or "")[:180].replace("\n", " ")
        if datetime.datetime.now() >= deadline:
            line = "FAILED: Claude never gave a verdict by %02d:00 (%s)" % (until_hour, last)
            with open(status_path, "w", encoding="utf-8") as fh:
                fh.write(line + "\n")
            print(line)
            return 1
        time.sleep(120)


def main(argv):
    log_path = os.path.expanduser("~/.grok/long-running-background-tasks/claude_xfam_1900.log")
    verdict_path = os.path.expanduser("~/.grok/long-running-background-tasks/claude_xfam_1900_verdict.txt")
    status_path = os.path.expanduser("~/.grok/long-running-background-tasks/claude_xfam_1900.status")
    if "--self-test" in argv:
        assert parse_verdict("Not logged in · Please run /login") is None
        assert parse_verdict("") is None
        doc = parse_verdict('noise {"frame.release": {"holds": true, "attack": "", "why": "rows False stays shut"}}')
        assert doc and doc["frame.release"]["holds"] is True
        assert seat_is_dead("You've hit your usage limit")
        print("self-test ok")
        return 0
    if "--wait" in argv:
        return wait_and_review(log_path, verdict_path, status_path)
    print("pass --wait to ask Claude, or --self-test")
    return 2


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
