# -*- coding: utf-8 -*-
"""THE PACKS NOW SHIP IN A PUBLIC REPO — SO THEY MUST NEVER STOP SAYING THEY ARE STAGED.

Konyo, 2026-09-16, choosing the road for the guest fixtures:
    "make it so they are uploaded with my reels."  /  "make it public no problem."

I raised that the repo is public and permanent; he reaffirmed. So `fixtures/` came out of
`.gitignore` and his recorded runs now travel with the code — which is what finally lets Grok
Bot's Linux box render a real SHELF, because a box with a clone and nothing else can stage them.

⚠⚠ THAT DECISION MOVES WHERE THE RISK LIVES. Before, a pack was a local artefact and a mistake
cost a rebuild. Now a pack is a published artefact and the mistake that matters is different:
a staged session that STOPS SAYING IT IS STAGED. `guest_fixture_pack` already puts `fixture:true`
and `fixturePack` on every record, and the whole guest seat exists to tell the truth about his
console — an eyes-loop reporting a finding about staged footage as though it were his live
footage is a wrong number that looks exactly like a right one. [[unknown-stays-unknown]]

⚠ AND A PUBLISHED PACK CANNOT BE UNPUBLISHED. The leak audit that ran before the first commit
(0 hits across every text byte of all five packs) is not a property of the code — it is a
property of THOSE BYTES on THAT DAY. This law re-runs the same audit on whatever is in the tree
now, so the next pack anyone adds is held to the bar the first five cleared.

MEASURED at the time of shipping: 5 packs, 72 frames, ~13 MB, every session `fixture: true`,
loaded into a scratch mirror exactly as the box would -> 5 sessions, 5 reels, 77 files staged.
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

FIXTURES = os.path.join(REPO, "fixtures")

# the same patterns the pre-commit audit used. CLAUDE.md §4: never put install ids, hostnames,
# tokens or home paths in anything this repo publishes.
LEAK_PATTERNS = (
    ("home path", re.compile(r"/Users/[A-Za-z0-9._-]+")),
    ("windows path", re.compile(r"[A-Z]:\\Users\\", re.I)),
    ("his name", re.compile(r"\bkonyo\b", re.I)),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("token", re.compile(r"\b(?:ghp_|sk-|xai-)[A-Za-z0-9_-]{8,}")),
    ("install id", re.compile(r"\binstallId\b", re.I)),
)
_IMG = (".jpg", ".jpeg", ".png", ".webp")


def _packs():
    if not os.path.isdir(FIXTURES):
        return []
    return sorted(d for d in os.listdir(FIXTURES)
                  if os.path.isfile(os.path.join(FIXTURES, d, "pack.json")))


class TheShippedPacksAreStagedNotHisLiveFootage(unittest.TestCase):

    def test_there_are_packs_to_ship_at_all(self):
        """[[zero-needs-a-denominator]] -- every assertion below is vacuously true on an empty
        directory, so an empty fixtures/ would make this whole file a green light over nothing."""
        n = len(_packs())
        print("   packs in the tree: %d" % n)
        self.assertGreater(n, 0,
                           "fixtures/ holds no packs, so every other law in this file passes "
                           "while proving nothing -- and Grok Bot's shelf renders empty")

    def test_every_session_says_it_is_a_fixture(self):
        for p in _packs():
            sj = os.path.join(FIXTURES, p, "sessions.json")
            self.assertTrue(os.path.isfile(sj), "%s carries no sessions.json" % p)
            sess = json.load(io.open(sj, encoding="utf-8")).get("sessions") or []
            self.assertTrue(sess, "%s stages no sessions" % p)
            for s in sess:
                self.assertIs(s.get("fixture"), True,
                              "%s stages a session that does not say fixture:true -- on the guest "
                              "it is indistinguishable from his live footage, and the first thing "
                              "that happens is a finding about staged data reported as his" % p)
                self.assertTrue(s.get("fixturePack"),
                                "%s stages a session with no fixturePack, so nothing can say "
                                "WHICH pack it came from" % p)

    def test_no_pack_leaks_anything_into_the_public_repo(self):
        """re-runs the pre-commit audit on whatever is in the tree now."""
        hits = []
        scanned = 0
        for p in _packs():
            for dirpath, _dn, fns in os.walk(os.path.join(FIXTURES, p)):
                for fn in fns:
                    if fn.lower().endswith(_IMG):
                        continue
                    fp = os.path.join(dirpath, fn)
                    scanned += 1
                    txt = io.open(fp, encoding="utf-8", errors="replace").read()
                    for name, rx in LEAK_PATTERNS:
                        m = rx.search(txt)
                        if m:
                            hits.append((name, os.path.relpath(fp, REPO), m.group(0)[:40]))
        print("   text files scanned: %d  leak hits: %d" % (scanned, len(hits)))
        self.assertGreater(scanned, 0, "nothing was scanned, so 0 hits means nobody looked")
        self.assertEqual([], hits, "a pack carries something that must not be published: %r"
                         % (hits[:4],))

    def test_a_pack_stays_small_enough_to_live_in_a_repo(self):
        """one reel is ~196 MB; a pack is a SUBSET and the whole reason packs exist. A pack that
        grew back toward its source would put gigabytes of footage in a public git history, and
        git history does not forget."""
        for p in _packs():
            mb = sum(os.path.getsize(os.path.join(dp, fn))
                     for dp, _dn, fns in os.walk(os.path.join(FIXTURES, p)) for fn in fns) / 1e6
            print("   %-16s %5.1f MB" % (p, mb))
            self.assertLess(mb, 25.0,
                            "%s is %.1f MB -- a pack is meant to be a representative subset, and "
                            "this one is heading back toward the size of the reel it came from"
                            % (p, mb))

    def test_the_pack_names_the_reel_it_came_from_and_is_NOT_that_reel(self):
        """a fixture session id must be namespaced, or a staged session collides with the real
        one it was cut from and the shelf shows one where the other belongs."""
        for p in _packs():
            pj = json.load(io.open(os.path.join(FIXTURES, p, "pack.json"), encoding="utf-8"))
            src = (pj.get("source") or {}).get("sessionId")
            fix = pj.get("fixtureSessionId")
            self.assertTrue(src, "%s does not record which reel it was cut from" % p)
            self.assertTrue(fix, "%s has no namespaced fixture session id" % p)
            self.assertNotEqual(src, fix,
                                "%s stages under the SAME id as his real session -- a staged "
                                "session and his own footage cannot share an id" % p)

    def test_the_loader_still_refuses_to_write_into_his_live_footage(self):
        """the packs being public does not loosen where they may be loaded."""
        import guest_fixture_pack as fx
        self.assertTrue(getattr(fx, "FORBIDDEN_DESTS", None),
                        "the loader no longer names any forbidden destination")
        joined = " ".join(fx.FORBIDDEN_DESTS)
        self.assertIn(os.path.join("tv", "frames"), joined,
                      "the live frames tree is no longer refused as a load destination -- a "
                      "staged scenario could become real footage, and footage has no un-delete")


RED_PROOF = [
    # the tamper targets the real thing each assertion is about
    ("guest_fixture_pack.py", "FORBIDDEN_DESTS = (", "FORBIDDEN_DESTS_DISABLED = (",
     "test_the_loader_still_refuses_to_write_into_his_live_footage"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
