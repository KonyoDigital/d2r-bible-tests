"""THE LIVE-DATA CANARY — the suite must not be able to destroy what it is testing.

WHAT IT COST TO LEARN, 2026-08-21. A test written to prove that a not-found receipt survives the
chronicle chain redirected the evidence store with `os.environ["TV_CHRON_EVIDENCE"] = <tmp>` and
then called the real save. **`_CHRON_EVIDENCE_PATH` is a module-level constant bound from that
variable when control_app is first imported** — which, inside a suite, has already happened. The
environment assignment was a no-op. The write landed on his real banked evidence and truncated
`tv/chron_evidence.json` from **525,187 bytes to 748**: 298 proposed uniques and 86 set pieces
across 767 page reads that were each paid for by a real model call, replaced by a two-item fixture.

It was recovered in full, and only by luck: `chron_last_result.json` happens to hold the same
proposal object. Had it not, the only way back would have been re-reading his entire reel history at
full price.

WHY THIS AND NOT A STATIC CHECK. The obvious guard — "no test may assign a live-path env var inside
a function body" — was written first and returned **26 hits, nearly all correct code**: `TV_HIST` and
`TV_SESSIONS` are read at call time as well as at import, so redirecting them mid-test genuinely
works. A guard with 26 false positives is a guard nobody reads. This one has none, because it does
not reason about mechanism at all — it asks the only question that matters: *did the bytes change?*

EVERY FILE BELOW IS GITIGNORED. There is no git recovery for any of them. That is the whole reason
this exists.

⚠ IT IS A CANARY, NOT A LOCK. It reports damage after the fact; it cannot prevent it. The rule it
enforces is the one the incident actually violated: **patch the module ATTRIBUTE, then assert the
redirect took.** Setting up an isolation and never checking it took is the defect — the fixture
looked isolated and was not. [[feedback-fixtures-never-touch-live-data]]
"""
import hashlib
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))

# The irreplaceable ones: banked reads, the sweep result, the journal, the visit ledgers. Anything
# whose bytes were paid for by a real model call or by him actually playing belongs here.
LIVE_FILES = (
    "chron_evidence.json",      # banked page reads — the most expensive bytes the console holds
    "chron_last_result.json",   # the last proposal; also the only backstop the incident above had
    "chron_reads.json",
    "chron_autoread.json",
    "chronicle_swept.json",
    "state.json",
    "sessions.jsonl",           # his play journal
    "vault_ledger.json",
)


def _fingerprint(path):
    """(size, sha1) or None when absent. Absence is recorded too: a suite that CREATES one of these
    has also touched live state, and 'it did not exist before' must not read as 'nothing happened'."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        return None
    except OSError:
        return "unreadable"
    return (len(data), hashlib.sha1(data).hexdigest())


@pytest.fixture(scope="session", autouse=True)
def live_data_is_not_collateral():
    before = {n: _fingerprint(os.path.join(HERE, n)) for n in LIVE_FILES}
    yield
    damaged = []
    for n in LIVE_FILES:
        after = _fingerprint(os.path.join(HERE, n))
        if after == before[n]:
            continue
        b, a = before[n], after
        if b is None:
            damaged.append("%s was CREATED by the suite (%s bytes)"
                           % (n, a[0] if isinstance(a, tuple) else a))
        elif a is None:
            damaged.append("%s was DELETED by the suite (was %s bytes)"
                           % (n, b[0] if isinstance(b, tuple) else b))
        else:
            bs = b[0] if isinstance(b, tuple) else "?"
            as_ = a[0] if isinstance(a, tuple) else "?"
            damaged.append("%s changed: %s bytes -> %s bytes" % (n, bs, as_))
    if damaged:
        pytest.fail(
            "A TEST WROTE TO LIVE DATA. These files are gitignored — there is no git recovery:\n  "
            + "\n  ".join(damaged)
            + "\n\nAlmost certainly a fixture redirected a path with os.environ[...] instead of "
              "patching the module attribute. Path constants like control_app._CHRON_EVIDENCE_PATH "
              "are bound ONCE at import, so setting the env var inside a test changes nothing and "
              "the write lands on his real files. Patch the attribute, then ASSERT the redirect "
              "took before writing anything.",
            pytrace=False)
