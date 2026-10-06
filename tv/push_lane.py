# -*- coding: utf-8 -*-
"""#182 (his go 2026-10-06) - WHICH LANE A PUSH TAKES: the full Mac gate, or CI only.

hooks/pre-push hands this the ref lines git gives the hook on stdin
(`<local_ref> <local_sha> <remote_ref> <remote_sha>`) and prints ONE word:

    ci-only   every ref that ships is refs/heads/ci/<name>  -> the hook skips its Mac stages; GitHub grades it
    full      anything else                                 -> the whole gate, exactly as before

WHY IT EXISTS. 63 Grok commits sat unpushed for two days (10-04..10-06) because any push - a branch
included - paid the full Mac gate, so no CI ever saw them and four HIGH defects stacked. A ci/* branch
never deploys (publish.yml runs on main only) and the tv/ and browser workflows run on any branch, so a
ci/* push can be graded on GitHub at no cost to his Mac.

THE ASYMMETRY IS DELIBERATE - it fails toward the FULL gate:
  * the decision reads the refs being PUSHED, never the branch the shell stands on (v2143.1: `git push
    origin wip:main` publishes to main while HEAD says wip);
  * one ref that is not ci/* - main, a tag, any other branch - makes the whole push `full`;
  * a ref naming main makes it `full` even when it is a DELETION;
  * no ref that ships, an unreadable line, or this script failing -> `full` (the hook defaults to full).
Law: test_a_ci_push_skips_the_mac_and_never_main.py
"""
import sys

CI_PREFIX = "refs/heads/ci/"
MAIN = "refs/heads/main"


def _zero(sha):
    s = str(sha or "")
    return bool(s) and set(s) == {"0"}


def lane(text):
    """The lane for these ref lines. -> ("ci-only" | "full", why)"""
    ships = []
    for ln in str(text or "").splitlines():
        parts = ln.split()
        if not parts:
            continue
        if len(parts) != 4:
            return "full", "a ref line did not read as four fields: %r" % ln[:120]
        _lr, ls, rr, _rs = parts
        if rr == MAIN:
            return "full", "this push names %s" % MAIN
        if _zero(ls):
            continue                      # a deletion ships nothing
        ships.append(rr)
    if not ships:
        return "full", "no ref in this push ships anything"
    other = [r for r in ships if not (r.startswith(CI_PREFIX) and len(r) > len(CI_PREFIX))]
    if other:
        return "full", "not a ci/* ref: %s" % ", ".join(other)
    return "ci-only", "every ref that ships is ci/*: %s" % ", ".join(ships)


def main():
    try:
        word, why = lane(sys.stdin.read())
    except Exception as e:                  # unreadable is FULL, never a skip
        word, why = "full", "the lane could not be decided (%s)" % type(e).__name__
    print(word)
    print(why, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
