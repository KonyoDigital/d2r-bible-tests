# -*- coding: utf-8 -*-
"""EVERY PROBE MUST BE ABLE TO SAY UNKNOWN, AND MUST SAY IT WHEN HANDED NOTHING.

⚠⚠ WHY THIS EXISTS, AND IT IS A PATTERN NOT AN INCIDENT. Four times on 2026-09-04 a fix shipped
the very class of defect it was fixing, one edit away:

    REG-534  two store filenames retyped instead of quoted
    REG-537  a snapshot frozen at import — written ONE LINE BELOW the fix for REG-534
    REG-540  a store path resolved two ways, in the module built to catch dead fields
    REG-541  a wholly unreadable store reporting OK — shipped INSIDE the fix for REG-540's crash,
             by the one module whose entire job is refusing to call the unmeasured clean

The rule was quoted correctly in every one of those commits. What failed was never the rule; it was
that **the NEW code was not re-asked the question the rule exists to ask.** A note cannot fix that.
A law can: every probe on this list is handed nothing, and must answer UNKNOWN rather than a
verdict. It runs against ALL of them, so the next probe added inherits the question automatically.

⚠ IT IS A LAW, NOT A ROSTER. It asserts the BEHAVIOUR (nothing in -> UNKNOWN out) rather than
pinning today's module list to a number, so adding a probe cannot make it stale — but an
ENTRY that stops existing is a refusal, because a probe silently dropped from this list is exactly
how the law stops covering the thing it was written for. [[unknown-stays-unknown]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

def _nothing_for_funnel():
    """⚠ `one_funnel.funnel()` TAKES NO ARGUMENT, so unlike its three siblings its nothing-to-read
    path cannot be driven from outside at all — it always reads the live tree. That is a real
    difference in shape, stated rather than special-cased away: to exercise it, the SOURCE has to
    be emptied. Its own suite already does this, and doing it here keeps the law uniform across
    four probes that are not uniform.
    """
    import one_funnel as OF
    import reel_story as RS
    real = RS.story
    try:
        RS.story = lambda *a, **k: {"reels": []}
        return OF.funnel()
    finally:
        RS.story = real


#: Each entry is a probe that publishes a `state`, and a callable that asks it with NOTHING TO
#: READ. Each is here because a wrong CLEAN from it would be believed.
def _nothing_for_dead_field_state():
    """Point the store resolver at nothing and `state()` has no store to read."""
    import dead_field as DF
    import reel_retention as RR
    real = RR._tombstone_path
    try:
        RR._tombstone_path = lambda *a, **k: os.path.join(HERE, ".no_such_store_ever.json")
        return DF.state()
    finally:
        RR._tombstone_path = real


def _nothing_for_printer():
    """Empty both of the printer's spine owners and it has nothing to walk."""
    import one_start_point as OSP
    import printer as P
    import reel_river as RR
    a, b = OSP.start_points, RR.river
    try:
        OSP.start_points = lambda *x, **k: {"ok": False, "rows": [], "state": "UNKNOWN",
                                            "counts": {}, "why": "x"}
        RR.river = lambda *x, **k: {"ok": False, "rows": [], "gaps": [], "why": "x"}
        return P.stream()
    finally:
        OSP.start_points, RR.river = a, b


def _nothing_for_printer_reach():
    """⚠⚠ THIS ONE FOUND A DEFECT THE DAY IT WAS ADDED (REG-543). `printer_reach.UNREACHABLE` was
    doing two jobs: *"I measured, and the contradiction is structurally impossible on this corpus"*
    — a real finding — and *"I could not read the seal store."* Only the `why` told them apart, so
    a store that failed to open read as the measured verdict. Splitting UNKNOWN out is what lets
    this probe join the law at all."""
    import frame_authority as FA
    import printer_reach as PR
    real = FA.sealed_sessions
    try:
        FA.sealed_sessions = lambda *a, **k: ({}, False)
        return PR.report()
    finally:
        FA.sealed_sessions = real


def _nothing_for_declared_vs_content():
    """Its source is the shelf; empty it and the sample cannot answer."""
    import declared_vs_content as DVC
    import reel_story as RS
    real = getattr(RS, "story", None)
    try:
        if real is not None:
            RS.story = lambda *a, **k: {"reels": []}
        return DVC.report()
    finally:
        if real is not None:
            RS.story = real


PROBES = (
    ("one_start_point.start_points",
     lambda: __import__("one_start_point").start_points(os.path.join(HERE, ".no_such_shelf_ever"))),
    ("one_funnel.funnel", _nothing_for_funnel),
    ("per_reel_routes.routes", lambda: __import__("per_reel_routes").routes([])),
    ("dead_field.dead_fields", lambda: __import__("dead_field").dead_fields(None)),
    ("dead_field.state", _nothing_for_dead_field_state),
    ("printer_reach.report", _nothing_for_printer_reach),
    ("printer.stream", _nothing_for_printer),
)

#: Each probe, and how to ask it with a REAL shelf. Used only by the shape law below — a reading's
#: key set must not depend on its verdict.
FULL = (
    ("one_start_point.start_points", lambda: __import__("one_start_point").start_points()),
    ("one_funnel.funnel", lambda: __import__("one_funnel").funnel()),
    ("per_reel_routes.routes", lambda: __import__("per_reel_routes").routes()),
    ("dead_field.dead_fields",
     lambda: __import__("dead_field").dead_fields([{"a": 1, "z": None} for _ in range(40)])),
    ("printer_reach.report", lambda: __import__("printer_reach").report()),
    ("printer.stream", lambda: __import__("printer").stream()),
    # ⚠ REG-553 — `dead_fields` takes rows in memory, so the unreadable-source law never touched a
    # filesystem for it. `state()` is the entry point that actually READS, and it is the one a
    # consumer calls. Both are covered now.
    ("dead_field.state", lambda: __import__("dead_field").state()),
)

#: ⚠ Probes whose FULL entry is handed data IN MEMORY and never touches a filesystem. The
#: unreadable-source law cannot ask them anything — breaking `open` changes nothing about a list
#: that is already in hand — so requiring UNKNOWN of them would be requiring a wrong answer. Named
#: with the reason rather than silently skipped, because an exemption nobody can see is how a law
#: quietly stops covering things. `dead_field.state` IS covered: it is the entry point that reads.
IN_MEMORY = ("dead_field.dead_fields",)

#: ⚠ NOT ON THE LIST, WITH THE REASON — because a probe missing silently is the failure this file
#: exists to prevent, and a probe missing with a REASON is a decision anyone can re-open:
#:
#:   declared_vs_content.report — its no-data path could not be driven from outside in the time
#:       this was written: emptying reel_story leaves its own reel-dir walk untouched, so the stub
#:       does not reach it. It is UNTESTABLE-aware (that IS its live verdict), so the question it
#:       would be asked here is one it already answers — but "already answers" is a claim I did not
#:       prove, and an unproven claim does not earn a line above. Open.
#:   store_owners.audit — publishes `ok`/`rows`/`why` and NO `state` at all. It is a different
#:       shape, not a probe that forgot to say UNKNOWN, and widening the law to cover it would
#:       change what the law means. Left out deliberately.
NOT_COVERED = ("declared_vs_content.report", "store_owners.audit")

#: ⚠⚠ WHICH PROBES THE PER-PROBE UNREADABLE-SOURCE LAW REACHES, AND WHICH IT DOES NOT — because
#: its first cut covered THREE of six and nothing said so, which is how a law quietly means less
#: than its name. `per_reel_routes` and `printer.stream` read nothing themselves: their source is
#: other probes' modules, and breaking those is what the OWNERS' own cases already do. That is a
#: reason, not an excuse, and it is written down so the next reader can disagree with it.
OWN_SOURCE_UNTESTED = ("per_reel_routes.routes", "printer.stream")


class NothingInMustGiveUnknownOut(unittest.TestCase):

    def test_every_probe_answers_UNKNOWN_when_handed_nothing(self):
        for name, ask in PROBES:
            r = ask()
            self.assertIsInstance(r, dict, "%s did not return a reading" % name)
            state = r.get("state") or r.get("ladder")   # one_funnel publishes two readings
            self.assertEqual(
                state, "UNKNOWN",
                "%s was handed nothing and answered %r. Nothing-to-read is not a clean verdict — "
                "it is the ABSENCE of one, and a probe that rounds it up is the defect every probe "
                "on this list was written to prevent. why=%r"
                % (name, state, str(r.get("why"))[:160]))

    def test_the_reason_is_carried_not_just_the_word(self):
        """⚠ UNKNOWN with no reason is a shrug. A reader has to be able to tell 'the shelf is
        empty' from 'the shelf could not be read' — opposite facts about his footage."""
        for name, ask in PROBES:
            why = str((ask() or {}).get("why") or "").strip()
            self.assertTrue(why, "%s said UNKNOWN and gave no reason at all" % name)
            self.assertGreater(len(why), 20,
                               "%s's reason is too short to distinguish anything: %r" % (name, why))

    def test_the_law_still_covers_four_probes(self):
        """⚠ It asserts BEHAVIOUR, not a roster — but a probe silently dropped from PROBES is
        exactly how a law stops covering the thing it was written for, and that deletion looks
        identical to a passing run. The count is the only thing that catches it."""
        self.assertGreaterEqual(
            len(PROBES), 5,
            "a probe was removed from this law. Adding one is free; removing one needs a reason "
            "written down, because the run stays green either way.")

    def test_the_per_probe_law_says_which_probes_it_does_NOT_reach(self):
        """⚠⚠ Its first cut reached THREE of six and nothing said so. A law that covers half its
        subjects while carrying a name that implies all of them is the same defect as a probe that
        rounds UNKNOWN up — it claims more than it measured. Every probe in FULL must either have
        an own-source case or be named, with a reason, in OWN_SOURCE_UNTESTED."""
        import inspect
        src = inspect.getsource(type(self).test_no_probe_CRASHES_ON_ITS_OWN_UNREADABLE_SOURCE)
        for name, _ in FULL:
            if name in IN_MEMORY or name in OWN_SOURCE_UNTESTED:
                continue
            self.assertIn('"%s"' % name, src,
                          "%s has no own-source case and is not named in OWN_SOURCE_UNTESTED, so "
                          "nobody can tell whether this law reaches it" % name)

    def test_OK_means_the_same_thing_in_every_probe(self):
        """⚠⚠ REG-556, from the cold look at v2554. `dead_field.state()` returned `ok: True` while
        its state was UNKNOWN; `one_start_point` and `per_reel_routes` return `ok: False` for
        exactly that state. **A consumer branching on `ok` got opposite answers from probes meant
        to be uniform** — the copy-drift defect applied to a MEANING rather than a filename, which
        no filename check could ever have caught.

        The rule, once: `ok` is False when nothing was established. Asked of every probe that
        publishes one, in both directions — UNKNOWN must be `ok: False`, and a real verdict must
        be `ok: True`, or the field would just be a second name for the state.
        """
        for name, ask in PROBES:
            r = ask()
            if "ok" not in r:
                continue
            st = r.get("state") or r.get("ladder")
            if st != "UNKNOWN":
                continue
            self.assertIs(r["ok"], False,
                          "%s says ok=%r while nothing was established. Its siblings say False, "
                          "and a consumer branching on `ok` gets opposite answers from probes that "
                          "are meant to be uniform." % (name, r["ok"]))
        for name, ask in FULL:
            r = ask()
            if "ok" not in r:
                continue
            st = r.get("state") or r.get("ladder")
            if st == "UNKNOWN":
                continue
            self.assertIs(r["ok"], True,
                          "%s reached the verdict %r and still says ok=%r, so `ok` is not "
                          "reporting whether anything was established" % (name, st, r["ok"]))

    def test_every_IN_MEMORY_exemption_is_real(self):
        """⚠ An exemption is a hole in a law, so it has to be checkable. Each name in IN_MEMORY
        must actually be in FULL (or it is a stale entry silently exempting nothing) and must NOT
        be the filesystem-reading sibling — `dead_field.state` reads and is covered; only
        `dead_field.dead_fields`, handed rows in memory, is exempt."""
        names = [n for n, _ in FULL]
        for n in IN_MEMORY:
            self.assertIn(n, names, "%s is exempted but is not in FULL — a stale exemption "
                                    "silently covers nothing" % n)
        self.assertIn("dead_field.state", names,
                      "the filesystem-reading entry point is not in the law, so the exemption for "
                      "its in-memory sibling leaves that module unasked entirely")

    def test_every_probe_left_OUT_carries_a_reason(self):
        """⚠⚠ A probe missing from PROBES silently is the exact failure this file exists to
        prevent, and the count check above cannot see one that was never added. So the ones left
        out are NAMED, and this pins that the list of exclusions is not empty — an empty
        NOT_COVERED would mean either everything is covered (say so by adding them) or somebody
        deleted the reasons."""
        self.assertTrue(NOT_COVERED,
                        "no probe is recorded as deliberately left out. If everything is covered, "
                        "add it to PROBES; if something is not, it needs a reason here.")
        for name in NOT_COVERED:
            self.assertNotIn(name, [n for n, _ in PROBES],
                             "%s is both covered and listed as not covered" % name)

    def test_printer_reach_tells_UNKNOWN_apart_from_UNREACHABLE(self):
        """⚠⚠ REG-543, and it is why this probe could join the law at all. `UNREACHABLE` meant
        BOTH *"I measured, and the contradiction is structurally impossible"* — a real finding —
        AND *"I could not read the seal store."* Only the `why` told them apart, so a consumer
        branching on `state` could not, and an unopenable store read as the measured verdict."""
        import printer_reach as PR
        self.assertEqual(_nothing_for_printer_reach().get("state"), "UNKNOWN")
        live = PR.report().get("state")
        self.assertNotEqual(
            live, "UNKNOWN",
            "the live tree now reports UNKNOWN too, so the split collapsed the other way and the "
            "real measured finding has been lost")

    def test_a_readings_SHAPE_does_not_depend_on_its_VERDICT(self):
        """⚠⚠ REG-546, and it is the FIFTH instance of one pattern in a day — a fix shipping the
        class it was fixing. REG-544 caught `dead_fields` omitting `judged`/`skipped` on its
        UNKNOWN paths; the SAME defect shipped in the SAME batch inside `printer.stream`, whose
        UNKNOWN return dropped `walked`, `unknownStations`, `stations` and `owners`. **A consumer
        reading those raised KeyError on exactly the path that means nothing was established — the
        reading breaks in the state it exists to report.**

        The word-level law above could not see it, because both readings said UNKNOWN correctly.
        So the shape is checked mechanically too: ask each probe with NOTHING and with a REAL
        shelf, and the key sets must match. This is what would have caught the fifth instance
        without anyone remembering.
        """
        empty = dict(PROBES)
        full = dict(FULL)
        # ⚠⚠ REG-548, from the cold look at v2546 — THE LOOP ITERATES `FULL`, so a probe in PROBES
        # and NOT in FULL is never fetched and never shaped, silently. Adding a probe to one list
        # and forgetting the other leaves it unguarded while the run stays green, which is the
        # failure this whole file exists to prevent, one level up.
        self.assertEqual(
            sorted(set(empty) - set(full)), [],
            "these probes are asked with NOTHING but never shaped against a real dataset, so "
            "their key sets are unguarded and the run stays green: %s"
            % sorted(set(empty) - set(full)))
        for name, ask_full in FULL:
            ask_empty = empty.get(name)
            self.assertTrue(ask_empty, "%s is in FULL but not in PROBES" % name)
            a, b = ask_empty(), ask_full()
            # ⚠⚠ REG-548 — AND A PROBE WHOSE TWO CALLS RETURN THE SAME THING PASSES VACUOUSLY.
            # `set(b) - set(a)` is empty when a IS b, so a probe whose "empty" stub does not
            # actually empty anything would be compared against itself and prove nothing. The two
            # calls must reach DIFFERENT states, or the fixture is the defect, not the subject.
            # [[feedback-blind-fixture-green-gate]]
            sa = a.get("state") or a.get("ladder")
            sb = b.get("state") or b.get("ladder")
            self.assertNotEqual(
                sb, sa,
                "%s answered %r to BOTH the empty ask and the real one, so the two calls are not "
                "distinguishing anything and its shape was compared against itself. The stub is "
                "not emptying what this probe reads." % (name, sa))
            self.assertIsInstance(a, dict, "%s empty reading is not a dict" % name)
            self.assertIsInstance(b, dict, "%s full reading is not a dict" % name)
            missing = sorted(set(b) - set(a))
            self.assertEqual(
                missing, [],
                "%s drops %s when it has nothing to report, so a caller reading them breaks on "
                "exactly the path that means NOTHING WAS ESTABLISHED. A shape that changes with "
                "the verdict is not a shape." % (name, missing))

    def test_every_ROW_in_a_reading_agrees_with_its_siblings_on_shape(self):
        """⚠⚠ REG-549, and it closes the mesh one level down from REG-547.

        The reading-level law compares TOP-LEVEL key sets. REG-547 was a shape defect nested two
        levels below that, and I fixed it by hand in one file — which leaves every OTHER nested
        reading unguarded. This asks it generically: within one reading, every row must carry the
        same keys, because a row that drops a key on its refusal path breaks a consumer walking
        the list on exactly the rows that went wrong.

        ⚠⚠ AND THE FIRST DEFECT IT FOUND WAS LATENT. `one_start_point` dropped `frames` and
        `blankFlagged` on its two refusal rows — and **his shelf has no reel with a missing or
        unparseable index**, so every LIVE reading showed one uniform shape and nothing would ever
        have revealed it. It took a CONSTRUCTED tree. *All rows agree today* is a fact about his
        corpus, not about the function, so this law is driven by BOTH.
        """
        for name, ask in FULL:
            r = ask()
            for key in ("rows", "stores"):
                rows = [x for x in (r.get(key) or []) if isinstance(x, dict)]
                if len(rows) < 2:
                    continue
                shapes = set(frozenset(x) for x in rows)
                if len(shapes) > 1:
                    u = set().union(*[set(x) for x in shapes])
                    i = set.intersection(*[set(x) for x in shapes])
                    self.fail("%s.%s has %d different row shapes; %s are missing from some rows. "
                              "A consumer walking the list breaks on exactly the rows that went "
                              "wrong." % (name, key, len(shapes), sorted(u - i)))

    def test_a_CONSTRUCTED_refusal_row_keeps_the_full_shape(self):
        """⚠ The law above runs on HIS shelf, which exercises only the happy path — so the refusal
        rows are built here on purpose. This is the case that found REG-549."""
        import json
        import shutil
        import tempfile
        import one_start_point as OSP
        d = tempfile.mkdtemp(prefix="probe_shape_")
        self.addCleanup(shutil.rmtree, d, True)
        for nm, idx in (("reel_s_1", {"sessionId": "s_1", "n": 1,
                                      "frames": [{"f": "a.jpg", "ts": 1}]}),
                        ("reel_s_2", None),
                        ("reel_s_3", "{ not json")):
            os.makedirs(os.path.join(d, nm))
            if idx is not None:
                with open(os.path.join(d, nm, "index.json"), "w") as fh:
                    fh.write(idx if isinstance(idx, str) else json.dumps(idx))
        rows = OSP.start_points(d)["rows"]
        self.assertEqual(len(rows), 3, "the constructed tree was not walked: %s" % rows)
        doors = sorted(r["door"] for r in rows)
        self.assertEqual(doors, ["UNKNOWN", "UNREADABLE", "recorder"],
                         "BASELINE: the three refusal paths were not all reached: %s" % doors)
        shapes = set(frozenset(r) for r in rows)
        self.assertEqual(len(shapes), 1,
                         "a reel whose birth could not be read gets a THINNER row than one that "
                         "could: %s" % [sorted(x) for x in shapes])

    def test_no_probe_CRASHES_ON_ITS_OWN_UNREADABLE_SOURCE(self):
        """⚠⚠ REG-554 — THE FIRST VERSION OF THIS LAW PASSED FOR THE WRONG REASON, and a cold
        review's unrelated question is what exposed it.

        It patched `os.listdir`, `builtins.open` and `io.open` globally and required UNKNOWN.
        Measured with a sentinel in the exception message: **only 1 of 6 probes ever reported the
        blocked read.** The rest answered UNKNOWN because the patch broke the IMPORT MACHINERY —
        `one_start_point` said *"the recorder would not import"* — so they never reached their own
        read at all. The law claimed to prove *a probe survives an unreadable source* and actually
        proved *a probe survives a process where nothing can be opened, including imports*. Every
        one of them passed, and five passed vacuously.

        So each probe's OWN source is broken instead of the world's: a path that exists and cannot
        be read as what the probe expects. And the reading must NAME the failure — a probe that
        answers UNKNOWN for an unrelated reason is exactly the vacuous pass this replaces.
        """
        import shutil
        import tempfile
        d = tempfile.mkdtemp(prefix="unreadable_")
        self.addCleanup(shutil.rmtree, d, True)
        # a DIRECTORY where each probe expects a FILE — a real read error at the real read site,
        # reached through the probe's own code rather than through a broken interpreter.
        trap = os.path.join(d, "trap.json")
        os.makedirs(trap)

        import reel_retention as RR

        cases = (
            ("one_start_point.start_points",
             lambda: __import__("one_start_point").start_points(os.path.join(d, "no_shelf")),
             "state"),
            ("dead_field.state", self._with(RR, "_tombstone_path", lambda *a, **k: trap,
                                            lambda: __import__("dead_field").state()),
             "state"),
            # ⚠ MY FIRST CUT PATCHED THE WRONG THING AND THE LAW BLAMED THE PROBE. I swapped
            # `retro_triage.STORE`, assuming printer_reach quoted it; it reads its own module
            # constant `TRIAGE`. The probe answered its real measured verdict and the law called
            # that a defect. Suspect the instrument first — it was the instrument.
            ("printer_reach.report",
             self._with(__import__("printer_reach"), "TRIAGE", trap,
                        lambda: __import__("printer_reach").report()),
             "state"),
            # ⚠ REG-555 — one_funnel was NOT in this law's first cut, and asking it found a real
            # defect: with both waypoint stores unreadable it reported the passage UNRECORDED, a
            # claim about his pipeline made over evidence nobody gathered.
            # ⚠⚠ AND THIS ONE PUBLISHES TWO READINGS. `one_funnel` answers a LADDER and a
            # PASSAGE; breaking its waypoint stores blinds the passage and leaves the ladder
            # legitimately readable, because the ladder comes from reel_story. The law's first cut
            # demanded UNKNOWN of the whole reading and FAILED a probe that was answering
            # correctly — the same coarse-mesh mistake in a new place. A case names WHICH reading
            # its broken source feeds.
            ("one_funnel.funnel", self._two_stores_unreadable(trap), "passage"),
        )
        for name, ask, key in cases:
            try:
                r = ask()
            except Exception as e:
                self.fail("%s RAISED %s on its OWN unreadable source. A probe that crashes goes "
                          "silent exactly when things are unusual: %s"
                          % (name, type(e).__name__, str(e)[:90]))
            st = r.get(key) if key in r else (r.get("state") or r.get("ladder"))
            self.assertEqual(st, "UNKNOWN",
                             "%s answered %r for %r over a source it could not read. why=%r"
                             % (name, st, key, str(r.get("why"))[:140]))

    def _two_stores_unreadable(self, trap):
        """one_funnel reads through TWO owners, so both have to break for its passage to be blind."""
        def _run():
            import frame_authority as FA
            import one_funnel as OF
            import retro_triage as RT
            rt, fa = RT.STORE, FA.SEAL_STORE
            try:
                RT.STORE = FA.SEAL_STORE = os.path.basename(trap)
                return OF.funnel()
            finally:
                RT.STORE, FA.SEAL_STORE = rt, fa
        return _run

    def _with(self, mod, attr, value, fn):
        """Run `fn` with `mod.attr` replaced, restoring it afterwards. -> callable"""
        def _run():
            real = getattr(mod, attr)
            try:
                setattr(mod, attr, value)
                return fn()
            finally:
                setattr(mod, attr, real)
        return _run

    def test_the_GLOBAL_patch_reaches_at_least_one_probes_read(self):
        """⚠ BASELINE that the OLD law lacked. Patching the world is still worth doing — it is how
        `printer_reach` was shown to handle a read failure — but it must be shown to reach a READ
        rather than an import, or it proves nothing. This asserts the sentinel actually appears in
        at least one probe's reason."""
        import builtins
        rl, ro, ri = os.listdir, builtins.open, io.open

        def _boom(*a, **k):
            raise PermissionError("BLOCKED-SENTINEL")

        seen = []
        for name, ask in FULL:
            if name in IN_MEMORY:
                continue
            try:
                os.listdir, builtins.open, io.open = _boom, _boom, _boom
                try:
                    r = ask()
                except Exception:
                    r = {}
            finally:
                os.listdir, builtins.open, io.open = rl, ro, ri
            if "BLOCKED-SENTINEL" in str(r.get("why") or ""):
                seen.append(name)
        self.assertTrue(
            seen,
            "the global patch reached NO probe's actual read — every UNKNOWN it produces would be "
            "an import failure wearing the right word, which is a law passing for the wrong reason")

    def test_no_probe_CRASHES_when_the_whole_process_cannot_open_anything(self):
        """⚠⚠ REG-552 EXPOSED A HOLE IN THIS LAW ITSELF. Every case above asks a probe with a
        source that is MISSING or EMPTY — and `one_start_point` handled those and **raised** on a
        source that EXISTS and cannot be READ, because `os.listdir` propagated a PermissionError.
        A probe that crashes goes silent exactly when the filesystem is unusual, which is when you
        need it most.

        Missing and unreadable are different failures and only one of them was being asked. This
        breaks `os.listdir` and `io.open` under every probe and requires an ANSWER — any answer,
        UNKNOWN or otherwise — rather than an exception.
        """
        import builtins
        real_listdir, real_open, real_io = os.listdir, builtins.open, io.open

        def _boom(*a, **k):
            raise PermissionError("denied")

        for name, ask in FULL:
            try:
                os.listdir, builtins.open, io.open = _boom, _boom, _boom
                try:
                    r = ask()
                except Exception as e:
                    self.fail("%s RAISED %s when its source could not be read. A probe that "
                              "crashes goes silent exactly when things are unusual: %s"
                              % (name, type(e).__name__, str(e)[:80]))
            finally:
                os.listdir, builtins.open, io.open = real_listdir, real_open, real_io
            self.assertIsInstance(r, dict, "%s did not return a reading" % name)
            # ⚠⚠ REG-553 — REQUIRING A DICT WAS NOT ENOUGH. A probe that swallows everything and
            # answers OK on an unreadable filesystem would have PASSED this law — the
            # unmeasured-reads-as-clean defect, inside the law written to prevent it. Found by
            # measuring what the probes actually SAY under a broken filesystem rather than
            # assuming the law covered it.
            if name in IN_MEMORY:
                continue          # nothing on disk to break; see IN_MEMORY
            st = r.get("state") or r.get("ladder")
            self.assertEqual(
                st, "UNKNOWN",
                "%s answered %r when NOTHING on the filesystem could be read. Nothing established "
                "is UNKNOWN; any other word is a verdict over evidence that was never gathered. "
                "why=%r" % (name, st, str(r.get("why"))[:140]))

    def test_BASELINE_these_probes_can_reach_a_real_verdict(self):
        """⚠⚠ Or the law above passes on four functions that answer UNKNOWN to everything, which
        would be a guard proving the opposite of what it claims. Each is handed real input and must
        NOT say UNKNOWN."""
        import dead_field as DF
        import one_funnel as OF
        import per_reel_routes as PRR
        rows = [{"reel": "reel_%d" % i, "deletedTs": 1, "z": None} for i in range(40)]
        self.assertNotEqual(DF.dead_fields(rows).get("state"), "UNKNOWN",
                            "dead_fields cannot reach a verdict at all")
        self.assertNotEqual(
            PRR.routes([{"reel": "reel_a", "tag": "zero-pages", "stage": "swept"}]).get("state"),
            "UNKNOWN", "per_reel_routes cannot reach a verdict at all")
        got = OF.funnel()          # against the live tree, which has reels
        self.assertNotEqual(got.get("ladder"), "UNKNOWN",
                            "one_funnel cannot reach a verdict at all: %s" % got.get("why"))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
