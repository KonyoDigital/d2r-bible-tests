# -*- coding: utf-8 -*-
"""REG-1632 — THE BASH A LAW MEANS IS A POSIX BASH, NOT WHATEVER `bash` NAMES ON THIS PC.

MEASURED on the ALT 2026-09-30 (its own heart census, then the law run by hand): `bash` on its PATH is
C:\\Windows\\System32\\bash.exe - the WSL launcher, which with no distribution installed prints "Windows Subsystem for
Linux has no installed distributions" in UTF-16 and runs nothing. So every law that drives a shell snippet
(`subprocess.run(["bash", "-c", ...])`) read ALREADY RED on that PC - test_the_gate_never_adopts_a_browser_it_did_not_start
failed 4 of 6 with "the hook's port snippet did not run". The PC HAS a real bash: Git for Windows ships one beside the git
it pulls with, and run by hand it chose the port correctly (bash's own /dev/tcp, no lsof needed).

One resolver, so every law asks the same question the same way: `bash()` -> the path of a real POSIX bash, or None when
this PC has none (a law then says UNKNOWN - it never guesses a pass). Never the WSL launcher. Windows paths are handled
with ntpath whatever the host, so the law that drives this runs the Windows case on his Mac and on CI too.
"""
import ntpath
import os
import shutil
import sys


def _is_wsl_launcher(path, sysroot=None, P=ntpath):
    """Is `path` under the Windows directory (System32 / SysWOW64 / Sysnative), where only the WSL launcher lives? -> bool"""
    root = sysroot or r"C:\Windows"
    try:
        p = P.normcase(P.abspath(path))
        r = P.normcase(P.abspath(root)).rstrip("\\/")
    except Exception:
        return False
    return p.startswith(r + "\\")


def _git_bash_candidates(git_path, env, P=ntpath):
    out = []
    if git_path:
        # <Git>\cmd\git.exe, <Git>\bin\git.exe, <Git>\mingw64\bin\git.exe - walk up to the install root
        d = P.dirname(P.abspath(git_path))
        for _ in range(3):
            d = P.dirname(d)
            out += [P.join(d, "bin", "bash.exe"), P.join(d, "usr", "bin", "bash.exe")]
    for base in (env.get("ProgramFiles"), env.get("ProgramW6432"), env.get("ProgramFiles(x86)")):
        if base:
            out.append(P.join(base, "Git", "bin", "bash.exe"))
    if env.get("LOCALAPPDATA"):
        out.append(P.join(env["LOCALAPPDATA"], "Programs", "Git", "bin", "bash.exe"))
    return out


def bash(which=None, isfile=None, platform=None, env=None):
    """-> the path of a real POSIX bash on this PC, or None. Never the WSL launcher. Never raises."""
    which = which or shutil.which
    isfile = isfile or os.path.isfile
    plat = platform or sys.platform
    env = os.environ if env is None else env
    try:
        found = which("bash")
        if not plat.startswith("win"):
            return found
        if found and not _is_wsl_launcher(found, env.get("SystemRoot") or env.get("windir")):
            return found
        for c in _git_bash_candidates(which("git"), env):
            if isfile(c):
                return c
    except Exception:
        return None
    return None
