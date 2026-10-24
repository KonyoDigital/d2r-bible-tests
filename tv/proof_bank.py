# -*- coding: utf-8 -*-
"""REG-2633 - PUBLISH ONE COMMIT'S PROOF BANK TO origin/proof-bank, OR FAIL THE RUN. NEVER A QUIET NOTHING.

The PCs (Dean's, the ALT) read `origin/proof-bank:<HEAD>.<class>.json` (self_prove.fetch_bank, REG-2632). Two CI
producers write it: the Linux census fan-in (proof-keys-shards.yml, job `bank`) writes `<sha>.linux.json`, and the
Windows census (proof-bank-windows.yml) writes `<sha>.windows.json` - a Windows PC keys raw CRLF bytes under the
"windows" class, so only a bank proved on Windows can ever serve it.

  python3 tv/proof_bank.py --check FILE --head SHA --class CLS
      the export `heart2 --export-proved` wrote is readable, is THIS commit's (manifest head == SHA, not dirty), holds
      at least one entry, was keyed on CLS (this runner's heart2.PLATFORM_CLASS), and names no machine path.
  python3 tv/proof_bank.py --publish FILE --head SHA --class CLS [--remote origin] [--branch proof-bank] [--keep 60]
      --check, then commits FILE as <SHA>.<CLS>.json on BRANCH (an orphan branch the first time), keeps the newest
      KEEP banks, pushes (rebasing over a racing producer, a few tries), and READS IT BACK from the remote: the run
      passes only when origin serves the same bytes.
Every refusal prints "PROOF BANK REFUSED: <why>" and exits 1; a missing file is a refusal, never a skip.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BRANCH = "proof-bank"
KEEP = 60
PUSH_TRIES = 4
CLASSES = ("linux", "windows", "darwin")
#: what a published bank must never carry (the export blanks its tree to "exported:<hash>", REG-2632)
PRIVATE = (re.compile(r"/Users/"), re.compile(r"/home/"), re.compile(r"[A-Za-z]:\\\\Users\\\\"),
           re.compile(r"[A-Za-z]:/Users/"), re.compile(r"/runner/work/"), re.compile(r"\\\\runner\\\\"))
NAME = re.compile(r"^([0-9a-f]{40})\.(linux|windows|darwin)\.json$")


class Refused(Exception):
    pass


def bank_name(head, cls):
    return "%s.%s.json" % (head, cls)


def check(path, head, cls, platform_class=None):
    """-> (body_text, n_entries); raises Refused with the reason."""
    if platform_class is None:
        import heart2 as _h2
        platform_class = _h2.PLATFORM_CLASS
    if not re.match(r"^[0-9a-f]{40}$", head or ""):
        raise Refused("head %r is not a full commit sha" % (head,))
    if cls not in CLASSES:
        raise Refused("class %r is not one of %s" % (cls, ", ".join(CLASSES)))
    if platform_class != cls:
        raise Refused("this runner keys proofs as %r, not %r - its bank would never meet a %s key"
                      % (platform_class, cls, cls))
    if not path or not os.path.isfile(path):
        raise Refused("the export %r does not exist (heart2 --export-proved wrote nothing)" % (path,))
    try:
        with io.open(path, encoding="utf-8") as fh:
            text = fh.read()
        body = json.loads(text)
    except (OSError, ValueError) as e:
        raise Refused("the export %r is unreadable (%s)" % (path, type(e).__name__))
    m = body.get("export") if isinstance(body, dict) else None
    ent = body.get("entries") if isinstance(body, dict) else None
    if not isinstance(m, dict) or not isinstance(ent, dict):
        raise Refused("the export has no export manifest or no entries map")
    if m.get("head") != head:
        raise Refused("the export is of %r, not this commit %s" % (m.get("head"), head[:12]))
    if m.get("dirty") is not False:
        raise Refused("the export was keyed on a tree that differed from its HEAD")
    if len(ent) < 1 or m.get("entries") != len(ent):
        raise Refused("the export holds %d entr(ies) (manifest says %r) - an empty bank serves nothing"
                      % (len(ent), m.get("entries")))
    for rx in PRIVATE:
        if rx.search(text):
            raise Refused("the export names a machine path (%s)" % rx.pattern)
    return text, len(ent)


def _run(args, cwd, env=None):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def _git(cwd, *a):
    return _run(["git"] + list(a), cwd)


def _must(cwd, *a):
    rc, out = _git(cwd, *a)
    if rc != 0:
        raise Refused("git %s failed (%d): %s" % (" ".join(a[:2]), rc, out.strip()[-300:]))
    return out


def prune(names, keep):
    """The bank files to delete so the newest `keep` commits stay (by the order git lists them newest-first is not
    known here, so by the commit order given). -> [name]"""
    seen, out = [], []
    for n in names:
        m = NAME.match(n)
        if not m:
            continue
        if m.group(1) not in seen:
            seen.append(m.group(1))
        if seen.index(m.group(1)) >= keep:
            out.append(n)
    return out


def publish(path, head, cls, remote="origin", branch=BRANCH, keep=KEEP, repo=".", platform_class=None, say=print):
    text, n = check(path, head, cls, platform_class)
    url = _must(repo, "remote", "get-url", remote).strip()
    name = bank_name(head, cls)
    work = tempfile.mkdtemp(prefix="proof-bank.")
    try:
        _must(work, "init", "-q")
        _must(work, "config", "user.name", "proof-bank")
        _must(work, "config", "user.email", "proof-bank@users.noreply.github.com")
        _must(work, "config", "core.autocrlf", "false")
        _must(work, "remote", "add", "origin", url)
        pushed = False
        for attempt in range(1, PUSH_TRIES + 1):
            rc, out = _git(work, "fetch", "-q", "origin", "+refs/heads/%s:refs/remotes/origin/%s" % (branch, branch))
            has = _git(work, "rev-parse", "-q", "--verify", "refs/remotes/origin/%s" % branch)[0] == 0
            if rc != 0 and has:
                raise Refused("fetching %s failed: %s" % (branch, out.strip()[-300:]))
            if has:
                _must(work, "checkout", "-q", "-B", branch, "refs/remotes/origin/%s" % branch)
            else:
                _must(work, "checkout", "-q", "--orphan", branch)
            with io.open(os.path.join(work, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            # newest first: the commit order of each bank's last touch
            listed = [l for l in _must(work, "log", "--format=", "--name-only", "--diff-filter=A").splitlines() if l] \
                if has else []
            order = [name] + [l for l in listed if l != name]
            for old in prune(order, keep):
                if os.path.exists(os.path.join(work, old)):
                    _must(work, "rm", "-q", old)
            _must(work, "add", name)
            _must(work, "commit", "-q", "--allow-empty", "-m", "proof bank %s %s (%d entries)" % (cls, head[:12], n))
            rc, out = _git(work, "push", "-q", "origin", "HEAD:refs/heads/%s" % branch)
            if rc == 0:
                pushed = True
                break
            say("  proof bank push %d/%d did not land (%s) - refetching" % (attempt, PUSH_TRIES, out.strip()[-200:]))
        if not pushed:
            raise Refused("the bank could not be pushed to %s after %d tries" % (branch, PUSH_TRIES))
        _must(work, "fetch", "-q", "origin", "+refs/heads/%s:refs/remotes/origin/%s" % (branch, branch))
        rc, back = _git(work, "show", "refs/remotes/origin/%s:%s" % (branch, name))
        if rc != 0 or back != text:
            raise Refused("origin/%s does not serve %s back byte for byte after the push" % (branch, name))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    say("  ✓ REG-2633 PROOF BANK PUBLISHED: %s (%d entr(ies)) on %s/%s, read back" % (name, n, remote, branch))
    return name


def main(argv=None):
    ap = argparse.ArgumentParser(prog="proof_bank.py")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="FILE")
    g.add_argument("--publish", metavar="FILE")
    ap.add_argument("--head", required=True)
    ap.add_argument("--class", dest="cls", required=True)
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default=BRANCH)
    ap.add_argument("--keep", type=int, default=KEEP)
    a = ap.parse_args(argv)
    try:
        if a.check:
            _t, n = check(a.check, a.head, a.cls)
            print("  ✓ REG-2633 proof bank %s holds %d entr(ies)" % (bank_name(a.head, a.cls), n))
        else:
            if a.keep < 1:
                raise Refused("--keep must be at least 1")
            publish(a.publish, a.head, a.cls, a.remote, a.branch, a.keep)
    except Refused as e:
        print("  ✗ PROOF BANK REFUSED: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
