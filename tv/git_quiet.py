#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE door for every git spawn in this codebase, so no child ever owns a console.

⚠⚠ v3409 — WHY THIS IS A MODULE AND NOT A SECOND COPY. v3407 put `_git_run` in control_app.py
and routed its 14 git argv sites through it. The cross-family review of v3404 then named a site
that fix could not reach: `console_doctor.py` spawns git too (`git show --name-only`, and
`git rev-list --count HEAD..origin/main` on the eagle tick), and the v3407 gate reads only
control_app.py — so the guard was green while two more console-popping spawns survived in a file
it never opened. Giving console_doctor its own `_git_run` would be [[copy-drift]]: two bodies,
one of which will eventually stop matching. One module, every caller.

THE FAULT IT PREVENTS, measured on the Windows box 2026-09-21: `git.exe` console windows stealing
focus 2-3 in a row, every couple of minutes, while TV DIABLO sat idle. Git for Windows' PATH git
(`Git\\cmd\\git.exe`) is a 46 KB CUI WRAPPER and `pythonw` owns no console, so a CUI child
ALLOCATES one — a real terminal on top of D2R.

⚠ CREATE_NO_WINDOW ON THE WRAPPER IS NOT ENOUGH: it spawns the real git WITHOUT the flag, so the
flag protects the 46 KB stub and nothing else. `headless-git.exe` is no better — a GUI trampoline
that still starts a CUI `git.exe` child (caught live: git.exe -> headless-git.exe -> pythonw) with
Windows Terminal taking the focus. Calling `mingw64\\bin\\git.exe` DIRECTLY is what makes
CREATE_NO_WINDOW + SW_HIDE apply to the binary that actually runs.
"""
import os
import subprocess
import sys

IS_WIN = sys.platform.startswith("win")

# Windows: CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
WIN_CREATE = 0x00000200 | 0x08000000 if IS_WIN else 0

GIT_MINGW = r"C:\Program Files\Git\mingw64\bin\git.exe"


def run(argv, **kw):
    """subprocess.run for git. On Windows the child must not own a console.

    Everything else is passed straight through, so a caller keeps its own cwd, timeout and
    capture settings — this adds the quiet, it does not take the control.
    """
    argv = list(argv)
    if IS_WIN:
        if argv and argv[0] == "git" and os.path.isfile(GIT_MINGW):
            argv[0] = GIT_MINGW
        kw["creationflags"] = kw.get("creationflags", 0) | WIN_CREATE
        env = dict(kw.get("env") or os.environ)
        # ⚠ Git Credential Manager opens a window of its OWN and then sits there until the caller's
        # timeout kills it. A prompt nobody can answer is a stolen screen plus a stalled lane.
        env["GIT_TERMINAL_PROMPT"] = "0"
        kw["env"] = env
        si = kw.get("startupinfo") or subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        kw["startupinfo"] = si
    return subprocess.run(argv, **kw)
