# -*- coding: utf-8 -*-
"""v3774 (REG-2295) — WHAT A VERSION STAMP MAY NOT CARRY.

The build name and note land in bible.html (twice), WINDOWS_SHIP.json and TASKS.md of a PUBLIC repo.
bump_version.py refuses a leaking name or note before writing, and gate_ledger.py runs the same check
on every ADDED stamp line before it lets a coherent bump carry the content gates, so a note pasted by
hand past the tool still reruns them. One definition, two callers.
"""
import re

# THE NAME AND NOTE ARE PUBLISHED FREE TEXT. They land in bible.html (twice),
# WINDOWS_SHIP.json and TASKS.md of a PUBLIC repo, and gate memory skips content gates over a coherent
# bump. So the tool refuses here what the leak gates would refuse later. Reuses the home-path ratchet's
# own counter and guest_profile's machine secrets; adds the IP, hostname and token shapes.
_LEAK_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_LEAK_HOST = re.compile(r"\b[A-Za-z0-9-]+\.(?:local|lan|internal|ts\.net)\b", re.I)
_LEAK_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|"
                         r"xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")


def leak_problem(text):
    """Why this free text may not be published, or None. -> str|None"""
    t = str(text or "")
    try:
        import test_no_new_home_path_is_published as _hp
        if _hp.count(t):  # BUMP-LEAK-HOME
            return "a home path (/Users/<name>/)"
    except Exception as exc:
        return "the home-path counter could not be loaded (%s) — UNKNOWN is not clean" % type(exc).__name__
    if "/home/" in t or "C:\\Users\\" in t:
        return "a home path"
    if _LEAK_IP.search(t):  # BUMP-LEAK-IP
        return "an IP address"
    if _LEAK_HOST.search(t):  # BUMP-LEAK-HOST
        return "a hostname"
    if _LEAK_TOKEN.search(t):  # BUMP-LEAK-TOKEN
        return "a token"
    try:
        import guest_profile as _gp
        for secret, _repl in _gp._secrets():
            if secret == "Konyo" or len(secret) < 4:
                continue  # the public nickname is not a secret
            if secret in t:  # BUMP-LEAK-MACHINE
                return "this machine's identity (home or user name)"
    except Exception:
        pass
    return None
