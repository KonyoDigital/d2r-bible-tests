"""v1598 — LAW19 REACHABILITY, as a gate instead of an intention.

The workflow's law says: *every symbol a change adds must have a caller AND a writer.* It has been
enforced by asking an agent to look. Asking works until nobody asks, and this repo has now paid for
that four separate times:

  REG-083/087  a `typeof NAME === 'function'` guard on a name declared NOWHERE — permanently false
  v1576        `chronicle_retro.classifier()` had tests and no production caller, while control_app
               carried an unsafe inline copy: the DEAD code was the SAFE one
  v1593        `RUNES` / `_flat` deleted while the only line referencing them stayed, so an unknown
               zone threw inside the paint and killed the whole Terror Zone panel
  v1598        `#hd-shelf-grid` / `#hd-shelf-pager` — READ in four places, CREATED in none, since
               v910 moved the markup and left the renderer behind. The guard in hdShelf() had been
               permanently true for ~680 versions and everything past it was unreachable

All four are one shape: **a reference to a name nothing produces.** That is mechanically checkable,
so it should not depend on anyone remembering to look.

WHAT THIS GATE CHECKS, and deliberately not more
------------------------------------------------
For every surface, every DOM id READ (`getElementById('x')`, `$('x')`) must be PRODUCED somewhere in
the same document — as static markup (`id="x"`), inside a JS template string (`id=\\'x\\'`), or
assigned at runtime (`el.id = 'x'`). Cross-document reads are real and legitimate (the console
probes the board through an iframe), so those are proven by a `querySelector` on another document
and are listed explicitly rather than pattern-matched — an allowlist you have to justify is the
point; one that grows silently is not.

It is deliberately a STATIC check with no browser: it must be cheap enough to run on every push,
and the failure it catches is a spelling-level fact that needs no runtime to establish.

WHY IT IS NOT A GREP
--------------------
The workflow's own LAW19 text says *prefer execution to grep*, and that is right for "is this
function called". It is wrong here: a DOM id is a string, it cannot be reached indirectly through a
live cross-file reference, and the whole failure mode is that the string exists on one side only.
"""

import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import console_safe  # noqa: F401,E402 — the verdict must survive a non-UTF-8 console

SURFACES = [
    ("tv/control_ui.html", os.path.join(HERE, "control_ui.html")),
    ("bible.html", os.path.join(REPO, "bible.html")),
]

# Ids READ in one document that genuinely LIVE in another. Each needs a reason, and the reason has
# to be checkable by reading the line it names.
CROSS_DOCUMENT = {
    # (surface, id): why it is legitimately absent from this document
}

# Reads that are provably not element lookups — a selector string, a data key, a CSS class.
_READ_PATTERNS = [
    re.compile(r"getElementById\(\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*\)"),
    re.compile(r"(?<![A-Za-z0-9_])\$\(\s*['\"]([A-Za-z0-9_\-]+)['\"]\s*\)"),
]

_WRITE_PATTERNS = [
    re.compile(r"""\bid\s*=\s*["']([A-Za-z0-9_\-]+)["']"""),        # static markup + template strings
    re.compile(r"""\bid\s*=\s*\\+["']([A-Za-z0-9_\-]+)\\*["']"""),  # escaped inside a JS string
    re.compile(r"""\.id\s*=\s*['"]([A-Za-z0-9_\-]+)['"]"""),        # el.id = 'x' at runtime
    re.compile(r"""id:\s*['"]([A-Za-z0-9_\-]+)['"]"""),             # object literal → rendered later
]


def ids_read(src):
    out = {}
    for pat in _READ_PATTERNS:
        for m in pat.finditer(src):
            out.setdefault(m.group(1), src.count("\n", 0, m.start()) + 1)
    return out


def ids_written(src):
    out = set()
    for pat in _WRITE_PATTERNS:
        out.update(m.group(1) for m in pat.finditer(src))
    return out


class TestEveryIdReadIsAlsoWritten(unittest.TestCase):
    """The whole gate. One test per surface so a failure names the file without hunting."""

    def _check(self, label, path):
        if not os.path.isfile(path):
            self.skipTest("%s not present" % label)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        read, written = ids_read(src), ids_written(src)
        orphans = {i: ln for i, ln in read.items()
                   if i not in written and (label, i) not in CROSS_DOCUMENT}
        if orphans:
            lines = "\n".join(
                "    %s:%d  reads #%s — nothing in this document ever creates it"
                % (label, ln, i) for i, ln in sorted(orphans.items(), key=lambda kv: kv[1]))
            self.fail(
                "%d DOM id(s) are READ but never WRITTEN in %s.\n%s\n\n"
                "Every guard on these is permanently false and every write to them is unreachable "
                "— that is the v1598 shelf bug, the v1593 Terror Zone crash and REG-083/087, which "
                "are all the same defect. Either create the element, delete the dead reference, or "
                "— if the id genuinely belongs to ANOTHER document (the console probing the board "
                "through its iframe is the real case) — add it to CROSS_DOCUMENT with the reason."
                % (len(orphans), label, lines))

    def test_console_ui(self):
        self._check(*SURFACES[0])

    def test_board(self):
        self._check(*SURFACES[1])


class TestTheGateCanActuallyFail(unittest.TestCase):
    """A gate nobody has seen fail is a gate nobody knows works. This proves the detector fires on
    the exact shape it exists to catch, using a synthetic document rather than the real one."""

    def test_it_flags_a_read_with_no_writer(self):
        src = "<div id=\"real\"></div><script>var a=document.getElementById('real');" \
              "var b=document.getElementById('phantom');</script>"
        read, written = ids_read(src), ids_written(src)
        self.assertIn("phantom", read)
        self.assertNotIn("phantom", written)
        self.assertIn("real", written)

    def test_it_accepts_a_runtime_assigned_id(self):
        """ov.id = 'x' is how the console builds its overlays — a real writer, not markup."""
        src = "<script>var ov=document.createElement('div');ov.id='tly-ov';" \
              "document.getElementById('tly-ov');</script>"
        self.assertIn("tly-ov", ids_written(src))

    def test_it_accepts_an_id_emitted_inside_a_template_string(self):
        src = """<script>el.innerHTML = '<button id="hd-prev">x</button>';
                 document.getElementById('hd-prev');</script>"""
        self.assertIn("hd-prev", ids_written(src))



# ── LAW19, second half: SYMBOLS ────────────────────────────────────────────────────────────────
# The id check above catches `getElementById('phantom')`. This catches its twin:
#     if (typeof renderAll === 'function') renderAll();
# ...where `renderAll` is declared NOWHERE, so the guard is permanently false. v1599 found five of
# those by hand — and they were not merely dead, they were five ownership changes that never
# repainted the surfaces showing ownership. Doing that by hand once is fine; relying on doing it
# again is not.
#
# WHY THIS SCANS LINE-WISE INSTEAD OF STRIPPING COMMENTS — learned the expensive way, twice:
#
#   1. NOT stripping means a comment can MASK the truth. My first sweep reported `renderAll` dead
#      long after it was fixed, because the comment explaining the fix quotes the dead guard.
#   2. Stripping NAIVELY is worse: `re.sub(r"/\*.*?\*/", "", src, flags=S)` on a 39k-line document
#      that contains regex literals and strings holding "/*" swallowed real spans of code, and the
#      sweep then reported THREE healthy functions (_aicIsGrailName, _chIsJunkName, refreshOpenCard)
#      as undeclared. A gate that invents findings gets ignored, which is worse than no gate —
#      refreshOpenCard is called bare in four places and would throw on load if that were true.
#
# So: read line by line, SKIP lines that are comments, and never rewrite the source. Conservative in
# the safe direction — a fake declaration hidden in a trailing comment on a code line would be
# missed, and missing one is survivable in a way that fabricating three is not.
_DECL_PATTERNS = [re.compile(p) for p in (
    r"function\s+([A-Za-z_$][\w$]*)\s*\(",
    r"(?:var|let|const)\s+([A-Za-z_$][\w$]*)\s*=",
    r"window\.([A-Za-z_$][\w$]*)\s*=",
    r"([A-Za-z_$][\w$]*)\s*[:=]\s*(?:async\s+)?function",
    r"([A-Za-z_$][\w$]*)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
)]
_GUARD_PATTERNS = [
    re.compile(r"typeof\s+([A-Za-z_$][\w$]*)\s*===?\s*['\"]function['\"]"),
    re.compile(r"typeof\s+window\.([A-Za-z_$][\w$]*)\s*===?\s*['\"]function['\"]"),
    # v1626 — THE OTHER HALF OF THE SAME GUARD. `typeof X !== 'undefined'` is the same promise in
    # the same shape, and it was not covered. That gap cost real time: a v1625 follow-up reported
    # the "last found" inline colour as permanently dead because `_Q_HEX is not in that closure's
    # scope` — untrue (it is a top-level var, so a window property), and there was no gate to
    # refute it, so it had to be disproved by rendering the bar on both tabs. 89 symbols in
    # bible.html use this shape; exactly two resolve nowhere, and both are browser features being
    # detected on purpose (see BROWSER_GLOBALS).
    re.compile(r"typeof\s+([A-Za-z_$][\w$]*)\s*!==?\s*['\"]undefined['\"]"),
    re.compile(r"typeof\s+window\.([A-Za-z_$][\w$]*)\s*!==?\s*['\"]undefined['\"]"),
]

# Guards on names this document does NOT own. Each needs a reason a reader can check.
EXTERNAL_SYMBOLS = {
    # (surface, symbol): why it legitimately lives elsewhere
    #
    # v1626 — BROWSER APIs, feature-detected on purpose. These are the ONLY two of the 89
    # typeof-guarded symbols in bible.html that resolve to no declaration, and that is correct:
    # the whole point of guarding them is that an older engine may not provide them. Allowlisting
    # them is what keeps the new typeof-undefined coverage honest — a gate that cries wolf on
    # legitimate feature detection is a gate people learn to skip.
    ("bible.html", "AbortController"): "browser API — feature-detected, not ours to declare",
    ("bible.html", "ResizeObserver"): "browser API — feature-detected, not ours to declare",
    # v1695 — the third of the same kind, and it had been failing this gate as a standing red.
    # Verified at the source rather than waved through by category: bible.html:39053 guards
    # `typeof MutationObserver === 'function'` and constructs `new MutationObserver(...)` on the
    # line below to re-stamp art on nodes added later. That is feature detection doing its job.
    # Leaving it red was the real cost — a gate with a permanent known failure stops being read,
    # and this suite's whole value is that a NEW entry in it means something broke.
    ("bible.html", "MutationObserver"): "browser API — feature-detected, not ours to declare",
}


def scan_symbols(path):
    """-> (declared:set, guarded:{name: first_line}). Skips comment lines; never rewrites source."""
    declared, guarded = set(), {}
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            t = line.lstrip()
            if t.startswith("//") or t.startswith("*") or t.startswith("/*"):
                continue
            for p in _DECL_PATTERNS:
                declared.update(m.group(1) for m in p.finditer(line))
            for p in _GUARD_PATTERNS:
                for m in p.finditer(line):
                    guarded.setdefault(m.group(1), n)
    return declared, guarded


class TestEveryGuardedSymbolExists(unittest.TestCase):
    """`typeof X === 'function'` is only defensive if X exists somewhere. Otherwise it is a promise
    nobody kept — and it hides forever, because the surrounding code still works."""

    def _check(self, label, path):
        if not os.path.isfile(path):
            self.skipTest("%s not present" % label)
        declared, guarded = scan_symbols(path)
        dead = {g: ln for g, ln in guarded.items()
                if g not in declared and (label, g) not in EXTERNAL_SYMBOLS}
        if dead:
            lines = "\n".join("    %s:%d  guards `typeof %s === 'function'` — declared nowhere"
                               % (label, ln, g) for g, ln in sorted(dead.items(), key=lambda kv: kv[1]))
            self.fail(
                "%d guard(s) in %s test a symbol that does not exist.\n%s\n\n"
                "Every one of these is permanently false, so the branch behind it never runs. That "
                "is REG-083/087 and REG-096: five `renderAll` guards meant five ownership changes "
                "that never repainted the grail meter. Either write the function, delete the dead "
                "branch, or — if it genuinely lives in another file — add it to EXTERNAL_SYMBOLS "
                "with the reason." % (len(dead), label, lines))

    def test_console_ui(self):
        self._check(*SURFACES[0])

    def test_board(self):
        self._check(*SURFACES[1])


class TestTheSymbolDetectorCanFail(unittest.TestCase):
    def test_it_flags_a_guard_with_no_declaration(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
            fh.write("<script>function real(){}\n"
                     "if (typeof real === 'function') real();\n"
                     "if (typeof ghost === 'function') ghost();</script>\n")
            p = fh.name
        try:
            declared, guarded = scan_symbols(p)
            self.assertIn("real", declared)
            self.assertIn("ghost", guarded)
            self.assertNotIn("ghost", declared)
        finally:
            os.unlink(p)

    def test_a_guard_inside_a_COMMENT_is_not_counted(self):
        """The exact false positive that made the first sweep report an already-fixed bug."""
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
            fh.write("<script>\n// was: if (typeof renderAll === 'function') renderAll();\n"
                     "var ok = 1;</script>\n")
            p = fh.name
        try:
            _declared, guarded = scan_symbols(p)
            self.assertNotIn("renderAll", guarded,
                             "a guard quoted in a comment is documentation, not code")
        finally:
            os.unlink(p)

class TestTheKnownOffendersStayFixed(unittest.TestCase):
    """Named regressions. These are cheap and they name the bug, so a reintroduction is obvious
    rather than being one line in a list of orphans."""

    def setUp(self):
        with open(os.path.join(HERE, "control_ui.html"), encoding="utf-8") as fh:
            raw = fh.read()
        # STRIP COMMENTS FIRST. The v1598 removal left a comment explaining what was deleted and
        # naming the dead calls verbatim — so the first version of this test failed on its own
        # documentation. A "did this code come back" check has to read CODE; prose that mentions
        # the bug is the opposite of the bug.
        no_line = re.sub(r"^\s*//.*$", "", raw, flags=re.M)
        self.ui = re.sub(r"/\*.*?\*/", "", no_line, flags=re.S)

    def test_the_phantom_shelf_grid_stays_gone(self):
        for dead in ("$('hd-shelf-grid')", "$('hd-shelf-pager')", "hdShelfRender("):
            self.assertNotIn(dead, self.ui,
                             "%s is back. Its element is created nowhere, so everything it guards "
                             "is unreachable — that was ~680 versions of dead render code." % dead)

    def test_the_board_lightbox_is_only_probed_through_the_iframe(self):
        """#tvd-frame-lb belongs to bible.html. A console-side getElementById for it is always null."""
        self.assertNotIn("getElementById('tvd-frame-lb')", self.ui)
        self.assertIn("#tvd-frame-lb:not([hidden])", self.ui,
                      "the iframe probe is the one that WORKS — if it goes, Esc stops reaching a "
                      "board overlay and the console closes out from under an open lightbox")


class TestLaw19ForPythonToo(unittest.TestCase):
    """v2005 — LAW19 says "every symbol a change adds must have a caller AND a writer", and this
    file has enforced it for DOM ids and `typeof` guards only. The SAME shape in Python was
    unguarded, and it cost this repo six times in one night (2026-08-22/23), four of them mine:

      lane_lock.py        declared "AT MOST ONE LANE IS EVER UNLOCKED" with zero production callers
                          — only tests imported it (REG-359)
      vault_corpus.py     space_map worked on his film and NOTHING called it (REG-364)
      control_app.py      prop["glimpsed"] / ["overRead"] written, read by no surface (REG-355)
      control_app.py      prop["pixelLaneError"] the same, three versions later (REG-364)

    Every one looked wired from its own end. That is the defining property, and it is mechanically
    checkable, so it must not depend on anyone remembering to look.

    THE ALLOWLIST IS THE POINT. An entry has to carry a REASON, and "we might need it later" is not
    one — the four above all had that reason. Blocked-on-evidence is: infer_transfer cannot be
    joined until a reel exists that films the inventory and then the stash with items moved between,
    and no reel of his does.
    """

    # symbol -> why it is allowed to have no production caller TODAY
    ALLOWED = {
        "vault_corpus.py:infer_transfer":
            "blocked on FOOTAGE, not on code: every one of his 31 reels was scanned and not one "
            "shows the panel changing, because none captured him stashing. Joining it now would be "
            "a gate that can never fire. Delete this line the day such a reel exists.",
        "lane_lock.py:may_write":
            "a thin wrapper over lane_for(), which IS joined (chronicle_retro.chronicle_kind, "
            "v1999). Calling it from there would compare the chronicle tab against itself — "
            "tautological wiring is worse than none. Kept because it is the documented public API "
            "of the law; delete it rather than fake a caller.",
        "stash_eye.py:prep_stash_grid":
            "PRE-EXISTING, not introduced by this arc. Pure image prep mirroring _tallyPrepImage; "
            "listed here so it is visible rather than silently tolerated.",
        "counter_ledger.py:missing_names":
            "PRE-EXISTING. A set-difference helper beside owned_by_subtraction, which IS used. "
            "Listed so the next reader sees it rather than rediscovering it.",
    }

    WATCH = ("vault_corpus.py", "vault_retro.py", "lane_lock.py", "reel_retention.py",
             "stash_eye.py", "counter_ledger.py")

    def _orphans(self):
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        prod = [f for f in os.listdir(here)
                if f.endswith(".py") and not f.startswith("test_")]
        text = {}
        for f in prod:
            try:
                with open(os.path.join(here, f), encoding="utf-8") as fh:
                    text[f] = fh.read()
            except OSError:
                pass
        for extra, rel in (("bible.html", os.path.join(here, "..", "bible.html")),
                           ("control_ui.html", os.path.join(here, "control_ui.html"))):
            try:
                with open(rel, encoding="utf-8") as fh:
                    text[extra] = fh.read()
            except OSError:
                pass
        found = []
        for f in self.WATCH:
            if f not in text:
                continue
            for node in ast.parse(text[f]).body:
                if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                    continue
                calls = 0
                for g, t in text.items():
                    pat = r"(?<!def )\b%s\s*\(" % node.name if g == f else r"\b%s\s*\(" % node.name
                    calls += len(re.findall(pat, t))
                if calls == 0:
                    found.append("%s:%s" % (f, node.name))
        return found

    def test_every_public_helper_has_a_caller_or_a_justified_reason(self):
        orphans = self._orphans()
        new = [o for o in orphans if o not in self.ALLOWED]
        self.assertEqual(
            new, [],
            "these public functions have NO production caller and no reason on record: %s. "
            "Join them, delete them, or add them to ALLOWED with a reason that is not "
            "'we might need it later'." % ", ".join(new))

    def test_the_allowlist_does_not_outlive_its_entries(self):
        """An allowlist that keeps names nobody has needed for years is how it stops being read."""
        orphans = set(self._orphans())
        stale = [k for k in self.ALLOWED if k not in orphans]
        self.assertEqual(
            stale, [],
            "these are on the allowlist but are NOT orphans any more — they were joined or "
            "deleted, so remove the excuse: %s" % ", ".join(stale))

    def test_every_reason_is_a_real_one(self):
        for k, why in self.ALLOWED.items():
            self.assertGreater(len(why), 60, "%s has a token reason, not a real one" % k)
            self.assertNotIn("might need it later", why.lower(),
                             "%s: that is the reason all four defects already had" % k)


class TestLaw19ForThePayloadContract(unittest.TestCase):
    """v2005 — the OTHER half of the same class, and the one that bit hardest.

    apply_payload's returned dict IS the contract with the board. A key added there and read by no
    surface is computed, carried, and thrown away — and it looks perfectly wired from the writing
    end. It happened five times in one arc:

      glimpsed / overRead   computed v1989/v1994, rendered nowhere until v1996 (REG-355)
      room / pixelLaneError computed v1995/v1998, rendered nowhere until v2004 (REG-364)
      witnessCount          added v1986 "for any surface that wants a number" — none ever did

    Same allowlist discipline: a key may be unread only with a REASON.
    """

    ALLOWED = {
        "generatedTs":
            "metadata, not a signal: the moment the proposal was built. The board shows reel and "
            "frame provenance from the witness rows instead, which is what he can actually open.",
        "readOnlyUntilApply":
            "a CONTRACT MARKER asserting vault_retro wrote nothing — it is for a reader auditing "
            "the payload's honesty, not for a pixel. Rendering it would say nothing he can act on.",
    }

    @staticmethod
    def _strip_comments(text):
        """v2005 — A GUARD THAT READS ITS OWN DOCUMENTATION IS BLIND.

        Caught by sabotage: unjoining `witnessCount` left the guard GREEN, because the comment
        explaining why witnessCount matters contains the word witnessCount. Exactly the scar already
        on record — an explanatory comment blinding a guard that grepped for a module name.

        ⚠ AND THE STRIP ITSELF HAS A SCAR: an unbounded /*…*/ regex once ate 16.9% of bible.html,
        because a `/*` inside a STRING started a comment that ran to the next one anywhere in the
        file. So the block pattern is NON-GREEDY and the result is size-checked by the caller: a
        strip that removes most of the file is a broken instrument, not a clean bill of health.
        [[feedback-comments-vs-code]] [[source-reading-guard]]
        """
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)      # non-greedy block comments
        text = re.sub(r"(?m)^\s*//.*$", " ", text)                # whole-line // comments only
        text = re.sub(r"(?s)<!--.*?-->", " ", text)                # html comments
        return text

    def _unread(self):
        import ast
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "vault_retro.py"), encoding="utf-8") as fh:
            vr = fh.read()
        surfaces = ""
        for rel in (os.path.join(here, "..", "bible.html"), os.path.join(here, "control_ui.html")):
            try:
                with open(rel, encoding="utf-8") as fh:
                    surfaces += self._strip_comments(fh.read())
            except OSError:
                pass
        self.assertGreater(len(surfaces), 2_000_000,
                           "comment-stripping removed most of the surfaces (%d bytes left) — the "
                           "instrument is broken, and a broken instrument passes everything"
                           % len(surfaces))
        fn = None
        for n in ast.parse(vr).body:
            if isinstance(n, ast.FunctionDef) and n.name == "apply_payload":
                fn = n
        assert fn is not None, "apply_payload moved — this guard is measuring nothing"
        keys = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Dict):
                for k in node.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, str):
                        keys.add(k.value)
        return sorted(k for k in keys
                      if not re.search(r"\b%s\b" % re.escape(k), surfaces))

    def test_every_payload_key_reaches_a_surface_or_says_why_not(self):
        unread = self._unread()
        new = [k for k in unread if k not in self.ALLOWED]
        self.assertEqual(
            new, [],
            "apply_payload emits these and NO surface reads them: %s. Render them, drop them, or "
            "add them to ALLOWED with a reason. A key carried and never read is the shape that cost "
            "five versions in one arc." % ", ".join(new))

    def test_the_allowlist_does_not_outlive_its_entries(self):
        unread = set(self._unread())
        stale = [k for k in self.ALLOWED if k not in unread]
        self.assertEqual(stale, [],
                         "these are allowlisted but ARE read now — remove the excuse: %s"
                         % ", ".join(stale))


if __name__ == "__main__":
    unittest.main(verbosity=2)
