# -*- coding: utf-8 -*-
"""v2740 — ONE ROUTER, OR ONE PERSON'S LEDGER READ FROM INSIDE ANOTHER PERSON'S WORLD.

Konyo: *"to each profile its individual ledgers and datas logic feedings the architecture and
routes already built .. same as reels and local storage these are all local anyways .. just needs a
unified logic it already is im pretty sure .. if not it should be"*.

HE IS RIGHT, AND IT IS MEASURED. `window.LSR` is that unified logic — every `d2r_*` key is read and
written through one namespace router (owner-main bare, owner-ladder `L·`, guest `I·<id8>·`,
guest-ladder `IL·<id8>·`, cousin `W·`). Counted in bible.html:

    routed through window.LSR                                     249
    bare, but ROUTING POINTERS (they DECIDE the namespace, so
      routing them would be circular: ownerClaim, installId,
      activeMachine, ledgerName, lsrRoute, the profile pointer)     20
    bare, but explicit-prefix MIGRATION code ('L·d2r_foundLog'
      and friends — moving rows BETWEEN namespaces on purpose)     ~64
    bare with a written `raw-ok` waiver                             12

So the architecture already is what he described. What did NOT exist is anything keeping it that
way: a new `localStorage.getItem('d2r_foundLog')` anywhere in this file would compile, run, pass
every existing gate, and — inside a guest world — read the OWNER's key. That is the Dean defect
with a different door.

=== WHY A BARE ACCESS IS THE EXACT SHAPE OF THAT BUG ===
`LSR.key(k)` prefixes a key only when it is in a fork set. A BARE call skips that entirely, so it
always lands on the owner's namespace whatever world is active. One line is enough to make a guest
console read, or overwrite, Konyo's chronicle. [[copy-drift]] [[the-unjoined-end]]

⚠ THIS IS A RATCHET, NOT A BAN. The 84 unwaived bare accesses that exist today are real and mostly
legitimate (pointers and migration), and rewriting them is not this gate's job. The count may
SHRINK freely and may never GROW — the same shape the visual-lock uses on raw font sizes, and for
the same reason: a debt you can see and cannot add to.
"""
import io
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

BIBLE = os.path.join(ROOT, "bible.html")
DEBT = os.path.join(HERE, "store_routing_debt.json")

VERBS = ("getItem(", "setItem(", "removeItem(")

#: Keys that MUST be bare: they decide which namespace everything else lands in, so routing them
#: through the router would be circular. This list is the same one `_collectProgress` refuses to
#: export, plus the two the resolver itself reads.
POINTERS = {
    "d2r_ownerClaim", "d2r_installId", "d2r_installIdCache", "d2r_activeProfile",
    "d2r_activeProfileWin", "d2r_activeMachine", "d2r_machineSource", "d2r_profile",
    "d2r_lsrRoute", "d2r_ledgerName", "d2r_testGuest",
}


def _scan():
    """-> (routed, bare_waived, bare_unwaived, [(line, keys, text), ...])"""
    routed = waived = 0
    unwaived = []
    for i, line in enumerate(io.open(BIBLE, encoding="utf-8"), 1):
        if "localStorage." not in line and "LSR." not in line:
            continue
        for v in VERBS:
            routed += line.count("LSR." + v)
        stripped = line
        for v in VERBS:
            stripped = stripped.replace("LSR." + v, "")
        n = sum(stripped.count("localStorage." + v) for v in VERBS)
        if not n:
            continue
        if "raw-ok" in line:
            waived += n
            continue
        keys = set(re.findall(r"['\"](d2r_[A-Za-z0-9_]+)['\"]", line))
        unwaived.append((i, sorted(keys), line.strip()))
    return routed, waived, sum(1 for _ in unwaived), unwaived


class EveryStoreReadIsRouted(unittest.TestCase):

    def test_the_scanner_can_see_the_router_AT_ALL(self):
        """⚠ A gate that finds nothing to grade passes having examined ZERO candidates."""
        routed, _, _, _ = _scan()
        self.assertGreater(routed, 150,
                           "only %d routed accesses found — the scanner or the router is gone, and "
                           "a low count here would make every law below vacuous" % routed)
        # ⚠ NOT a fixed-size head read. `window.LSR` is declared ~line 4078, well past 256KB, so
        # a bounded read reported it ABSENT and then dumped the whole slice into the failure
        # message. A bound chosen once is a bound that goes stale. [[source-reading-guard]]
        src = io.open(BIBLE, encoding="utf-8").read()
        self.assertIn("window.LSR = (function(){", src,
                      "the router is not declared any more — every law below assumes it exists")

    # ── ⚠⚠ THE RATCHET ───────────────────────────────────────────────────────────────────────
    def test_bare_store_access_never_GROWS(self):
        """A new bare `localStorage.getItem('d2r_foundLog')` compiles, runs, passes every other
        gate, and inside a guest world reads the OWNER's key. One line is the whole bug.

        The count may shrink freely and may never grow — the same shape the visual-lock uses on raw
        font sizes, and for the same reason: a debt you can see and cannot add to.
        """
        _, _, unwaived, rows = _scan()
        try:
            base = json.load(io.open(DEBT, encoding="utf-8"))
        except Exception as e:
            self.fail("store_routing_debt.json could not be read (%s) — that is UNKNOWN, not a "
                      "clean surface. Regenerate with --snapshot and review the diff." % e)
        was = int(base.get("unwaivedBare", -1))
        self.assertGreaterEqual(
            was, 0, "the debt file carries no baseline, so this ratchet is measuring nothing")
        self.assertLessEqual(
            unwaived, was,
            "bare localStorage access grew from %d to %d line(s). Every one of them lands on the "
            "OWNER's namespace whatever world is active, so a single new line can make a guest "
            "console read — or overwrite — his chronicle. Route it through window.LSR, or if it "
            "genuinely must be bare (a routing POINTER, or a deliberate cross-namespace "
            "migration), say `raw-ok` on the line with the reason.\\nNew or moved:\\n%s"
            % (was, unwaived,
               "\\n".join("  L%s %s" % (ln, txt[:96]) for ln, _k, txt in rows[-4:])))
        if unwaived < was:
            print("   ℹ store-routing debt PAID: %d -> %d. Rerun with --snapshot to tighten."
                  % (was, unwaived))

    # ── the pointers are allowed to be bare, and nothing else is allowed to look like one ────
    def test_a_LEDGER_key_is_never_read_bare_without_a_waiver(self):
        """⚠ THE LOAD-BEARING ONE. The ratchet above counts lines; this names the ones that would
        actually cross a profile. A pointer being bare is by design. `d2r_foundLog`, `d2r_owned`,
        `d2r_setPieces`, `d2r_rwMade` and `d2r_grailUnfound` being bare is the Dean defect.
        """
        LEDGERS = {"d2r_foundLog", "d2r_owned", "d2r_setPieces", "d2r_rwMade",
                   "d2r_gameFound", "d2r_grailUnfound", "d2r_tally"}
        _, _, _, rows = _scan()
        bad = []
        for ln, keys, txt in rows:
            hit = LEDGERS & set(keys)
            # an explicitly-prefixed key ('L·d2r_foundLog') is migration code addressing a
            # namespace on purpose — it is not a routing bypass, it IS the routing
            if hit and not re.search(r"['\"](?:L|W|WL|I|IL)·", txt):
                bad.append((ln, sorted(hit), txt[:92]))
        self.assertEqual(
            [], bad,
            "a LEDGER store is read or written bare, with no `raw-ok` reason. Bare means the "
            "OWNER's namespace whatever world is active, so this line reads his chronicle from "
            "inside somebody else's console:\\n%s"
            % "\\n".join("  L%s %s -> %s" % (ln, k, t) for ln, k, t in bad))

    def test_the_pointer_list_here_matches_the_one_the_exporter_refuses(self):
        """Two lists of "keys that must not travel" that can drift apart is one list too many.
        `_collectProgress`'s PTRS is the other one. [[copy-drift]]"""
        src = io.open(BIBLE, encoding="utf-8").read()
        blk = src[src.find("const PTRS = {"):]
        blk = blk[:blk.find("}")]
        exporter = set(re.findall(r"'(d2r_[A-Za-z0-9_]+)'", blk))
        self.assertTrue(exporter, "could not read _collectProgress's PTRS list")
        missing = sorted(exporter - POINTERS)
        self.assertEqual([], missing,
                         "the exporter refuses to export %s, and this file does not treat them as "
                         "routing pointers. One of the two lists is wrong." % missing)


if __name__ == "__main__":
    if "--snapshot" in sys.argv:
        r, w, u, _ = _scan()
        io.open(DEBT, "w", encoding="utf-8").write(json.dumps(
            {"routed": r, "waivedBare": w, "unwaivedBare": u}, indent=1) + "\n")
        print("snapshot: routed=%d waived=%d unwaived=%d" % (r, w, u))
        sys.exit(0)
    unittest.main(verbosity=2)
