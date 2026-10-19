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
# bump. So the tool refuses here what the leak gates would refuse later. Mirrors the home-path ratchet's
# own pattern and guest_profile's machine secrets; adds the IP, hostname and token shapes.
# The home-path ratchet's own pattern (test_no_new_home_path_is_published.HOME). A production module
# may not import a test module (test_the_census_population_is_safe_to_name_by_file), so it is copied
# here and the guard test pins the two patterns equal.
HOME = re.compile(r"/Users/[A-Za-z0-9._-]+/")
_LEAK_IP = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_LEAK_HOST = re.compile(r"\b[A-Za-z0-9-]+\.(?:local|lan|internal|ts\.net)\b", re.I)
_LEAK_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|"
                         r"xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})")


def leak_problem(text):
    """Why this free text may not be published, or None. -> str|None"""
    t = str(text or "")
    if HOME.search(t):  # BUMP-LEAK-HOME
        return "a home path (/Users/<name>/)"
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
