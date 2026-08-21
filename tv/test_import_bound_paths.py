"""THE REGISTRY OF IMPORT-BOUND PATHS — which redirects actually take, named out loud.

WHAT IT COST TO LEARN, 2026-08-21. `_CHRON_EVIDENCE_PATH` is bound from `TV_CHRON_EVIDENCE` when
control_app is first imported. A test set that variable inside a function body, called the real
save, and truncated `tv/chron_evidence.json` from 525,187 bytes to 748 — 767 paid page reads gone.
tv/conftest.py is the CANARY for that: it reports the damage after the fact. This is the MAP: for
every module-level path constant bound from the environment, it says in one place whether a later
`os.environ[...]` is honoured, so a fixture author does not have to guess.

WHY A REGISTRY AND NOT A RULE. The obvious static guard — "no test may assign a live-path env var
inside a function body" — was written first and returned 26 hits, nearly all correct code, because
`TV_HIST` and `TV_SESSIONS` are ALSO read at call time. Measured here, not assumed: control_app has
**11** functions that re-read `TV_HIST` at call time, and **0** that re-read `TV_CHRON_EVIDENCE`.
Same variable name shape, opposite answers. A rule cannot tell them apart; a measured registry can.

THE MEASUREMENT BEHIND EVERY `kind` BELOW (2026-08-21, python3.9, per constant, in a subprocess):
import the module with the variable unset, set it, then ask whether anything moves — plus a count of
functions whose code objects hold the variable name as a constant (`co_consts`, not a text grep —
[[source-reading-guard]]). Zero call-time readers is what makes a constant import-bound; the
attribute itself never moves in either case, so the attribute alone measures nothing.

WHAT THIS GATE ACTUALLY BLOCKS. A tv/*.py that grows a NEW module-level env-bound path constant the
registry does not name. That is the moment the knowledge is cheap; after a fixture has trusted it,
the price is his data. It also pins the two classifications behaviourally, so a constant that
changes sides fails here instead of failing in a fixture.
"""
import ast
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# --- THE REGISTRY ------------------------------------------------------------------------------
# key: "<file>:<CONST>"  ->  (env var, kind, note)
#   kind "import-bound" — a later os.environ[...] is a NO-OP. The only safe redirect is patching the
#                         module attribute: `mock.patch.object(mod, "CONST", tmp)`, and then ASSERT
#                         the redirect took before writing anything.
#   kind "call-time"    — consumers re-read the variable on every call, so os.environ[...] inside a
#                         test genuinely works. These are the 26 false positives a static rule hit.
# Every entry's kind was measured behaviourally; the number in each note is that measurement.
REGISTRY = {
    # ---- control_app: the live-state family. All six default under _fixture_root_for_state(),
    # which honours TV_HIST *at import only* — an isolated harness must set TV_HIST BEFORE import.
    "control_app.py:_CHRON_EVIDENCE_PATH": (
        "TV_CHRON_EVIDENCE", "import-bound",
        "0 call-time readers; writes tv/chron_evidence.json (gitignored, paid for by real model "
        "calls). THE v1920 INCIDENT. Redirect only via mock.patch.object(control_app, "
        "'_CHRON_EVIDENCE_PATH', tmp)."),
    "control_app.py:_CHRON_RESULT_PATH": (
        "TV_CHRON_RESULT", "import-bound",
        "0 call-time readers; writes tv/chron_last_result.json (gitignored; the only backstop the "
        "evidence file had). Patch the attribute."),
    "control_app.py:_CHRON_AUTOREAD_PATH": (
        "TV_CHRON_AUTOREAD", "import-bound",
        "0 call-time readers; writes tv/chron_autoread.json (gitignored). Patch the attribute."),
    "control_app.py:VAULT_LEDGER_PATH": (
        "TV_VAULT_LEDGER", "import-bound",
        "0 call-time readers; writes tv/vault_accum.json. Patch the attribute."),
    "control_app.py:_VAULT_SWEPT_PATH": (
        "TV_VAULT_SWEPT", "import-bound",
        "0 call-time readers; writes tv/vault_swept.json. Patch the attribute."),
    "control_app.py:_VAULT_RESULT_PATH": (
        "TV_VAULT_RESULT", "import-bound",
        "0 call-time readers; writes tv/vault_last_result.json. Patch the attribute."),
    "control_app.py:HIST_DIR": (
        "TV_HIST", "call-time",
        "11 functions re-read TV_HIST at call time (_chron_reads_path, _chron_swept_path, "
        "_chron_sweep_run, ...), so setting it mid-test works. 24 functions still read the constant "
        "directly — patch the attribute TOO when the code under test is one of those."),

    # ---- replay: same variable as control_app._journal_path(), OPPOSITE answer.
    "replay.py:JOURNAL": (
        "TV_SESSIONS", "import-bound",
        "0 call-time readers — control_app resolves TV_SESSIONS per call via _journal_path(), replay "
        "does NOT. read-only consumer (load_journal), so the risk is reading his real "
        "tv/sessions.jsonl while believing the harness is isolated (the v1493 shape)."),

    # ---- tv_diablo
    "tv_diablo.py:FRAMES": (
        "TV_FRAMES_DIR", "import-bound",
        "0 call-time readers, 21 consumers; the WATCH DIR — writable, and every frame path derives "
        "from it. Patch the attribute (and HIST_DIR, which is derived from it at import)."),
    "tv_diablo.py:HIST_DIR": (
        "TV_HIST", "import-bound",
        "derived from FRAMES at import; only 3 functions re-read TV_HIST (_fixture_root, "
        "_journal_path, _sub_budget_path) while 10 read the constant. Treat as import-bound."),
    "tv_diablo.py:_KNOWN_DEAD_FILE": (
        "TV_KNOWN_FRAMES", "import-bound",
        "0 call-time readers; writes known_frames.json under the fixture root. Patch the attribute."),
    "tv_diablo.py:_VISION_CWD": (
        "TV_VISION_CWD", "import-bound",
        "0 call-time readers; a scratch dir under tempfile.gettempdir(), not live state."),
    "tv_diablo.py:OCR_BIN": (
        "TV_OCR_BIN", "call-time",
        "1 call-time reader (_ocr_worker_cmd). A binary that is executed, never written."),

    # ---- extract_ui_icons: an offline art tool, no live state.
    "extract_ui_icons.py:D2R": (
        "D2R_INSTALL", "import-bound",
        "0 call-time readers; the CrossOver game install — READ-ONLY, never a write target."),
    "extract_ui_icons.py:EXTRACT": (
        "CASC_EXTRACT", "import-bound",
        "0 call-time readers; /tmp scratch dir for CASC output, not live state."),
    "extract_ui_icons.py:FRAMEWORK": (
        "CASC_FRAMEWORK", "import-bound",
        "0 call-time readers; /tmp CascLib build dir, not live state."),
}

_KINDS = ("import-bound", "call-time")

# Strings that look like a path but are not one. A URL contains "/" and must not drag _TZ_UPSTREAM
# into the registry; a bare model name or flag never reaches _path_shaped at all.
_URL_PREFIXES = ("http://", "https://", "ws://", "wss://")
_PATH_SUFFIXES = (".json", ".jsonl", ".txt", ".log", ".db", ".png", ".jpg", ".html", ".csv")
_PATH_CALLS = ("join", "expanduser", "abspath", "dirname", "gettempdir", "realpath", "mkdtemp")


def _reads_env(node):
    """True when evaluating this expression consults the environment."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute) and f.attr in ("get", "pop"):
                inner = f.value
                if isinstance(inner, ast.Attribute) and inner.attr == "environ":
                    return True
            if isinstance(f, ast.Attribute) and f.attr == "getenv":
                return True
            if isinstance(f, ast.Name) and f.id == "getenv":
                return True
        if isinstance(n, ast.Subscript):
            v = n.value
            if isinstance(v, ast.Attribute) and v.attr == "environ":
                return True
    return False


def _path_shaped(node):
    """True when the expression builds a filesystem path — an os.path/tempfile call, or a literal
    that looks like one. Deliberately NOT 'contains a slash': that swallows every URL."""
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in _PATH_CALLS:
            return True
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            s = n.value
            if s.startswith(_URL_PREFIXES):
                continue
            if s.startswith("/") or s.startswith("~/") or s.endswith(_PATH_SUFFIXES):
                return True
    return False


def _import_time_body(body):
    """Statements that run at import: the module body, and anything nested in a module-level if /
    try / with. A constant hidden inside `try:` is bound just as hard as one at column 0."""
    for st in body:
        yield st
        for attr in ("body", "orelse", "finalbody"):
            inner = getattr(st, attr, None)
            if isinstance(inner, list) and isinstance(st, (ast.If, ast.Try, ast.With)):
                for sub in _import_time_body(inner):
                    yield sub


def scan_module_env_path_constants(path):
    """-> sorted list of constant names in `path` bound from the environment to a path at import."""
    with open(path, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    found = []
    for node in _import_time_body(tree.body):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names or not _reads_env(value) or not _path_shaped(value):
            continue
        found.extend(names)
    return sorted(set(found))


def scan_tree(root=HERE):
    """-> {"<file>:<CONST>": path} for every tv/*.py. Test files included: a fixture module that
    binds a live path at import is the same defect wearing a test's name."""
    out = {}
    for name in sorted(os.listdir(root)):
        if not name.endswith(".py"):
            continue
        full = os.path.join(root, name)
        for const in scan_module_env_path_constants(full):
            out["%s:%s" % (name, const)] = full
    return out


class TestImportBoundPathRegistry(unittest.TestCase):
    """Same shape as run_gates.py's TestNoOrphanSuite: the tree and the registry must agree."""

    def test_scanner_is_not_blind(self):
        """THE COUNT IS THE TELL. A scanner that finds nothing passes everything."""
        found = scan_tree()
        self.assertGreaterEqual(
            len(found), 10,
            "the scanner found only %d env-bound path constants across tv/*.py — it was finding 16 "
            "on 2026-08-21. Suspect the instrument before the code." % len(found))
        self.assertIn("control_app.py:_CHRON_EVIDENCE_PATH", found,
                      "the scanner no longer sees the constant that caused the incident this file "
                      "exists for — the scan is broken, not the code.")

    def test_no_unregistered_env_bound_path(self):
        found = scan_tree()
        missing = sorted(k for k in found if k not in REGISTRY)
        self.assertEqual(
            [], missing,
            "NEW module-level env-bound PATH constant(s) with no registry entry:\n  "
            + "\n  ".join("%s  (%s)" % (k, found[k]) for k in missing)
            + "\n\nA constant like this is bound ONCE at import. Measure it — does any function "
              "re-read the variable at call time? — then add it to REGISTRY in "
              "tv/test_import_bound_paths.py as 'import-bound' or 'call-time'. If it is "
              "import-bound and names a writable path, the only safe redirect in a fixture is "
              "mock.patch.object(module, 'CONST', tmp), asserted after patching.")

    def test_registry_has_no_stale_entries(self):
        found = scan_tree()
        stale = sorted(k for k in REGISTRY if k not in found)
        self.assertEqual(
            [], stale,
            "REGISTRY names constant(s) tv/*.py no longer binds from the environment: %s. Either "
            "the constant was renamed/removed (drop the entry) or it stopped reading the "
            "environment (drop it) — a note describing code that is gone is worse than no note."
            % ", ".join(stale))

    def test_every_entry_is_classified(self):
        for key, entry in sorted(REGISTRY.items()):
            self.assertEqual(3, len(entry), "%s: expected (env var, kind, note)" % key)
            var, kind, note = entry
            self.assertIn(kind, _KINDS, "%s: kind %r must be one of %s" % (key, kind, _KINDS))
            self.assertTrue(var and var.isupper(), "%s: %r is not an env var name" % (key, var))
            self.assertGreater(len(note), 30, "%s: the note must say what it costs to get wrong" % key)

    def test_registry_env_var_matches_the_source(self):
        """A note is only worth its accuracy: the variable named here must be the one the line
        actually reads. Cheap to drift, silent when it does."""
        for key, (var, _kind, _note) in sorted(REGISTRY.items()):
            fname, const = key.split(":", 1)
            full = os.path.join(HERE, fname)
            with open(full, "r", encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=full)
            hit = None
            for node in _import_time_body(tree.body):
                targets = node.targets if isinstance(node, ast.Assign) else (
                    [node.target] if isinstance(node, ast.AnnAssign) and node.value else [])
                if any(isinstance(t, ast.Name) and t.id == const for t in targets):
                    hit = node.value
                    break
            self.assertIsNotNone(hit, "%s: not found at module level in %s" % (key, fname))
            names = {n.value for n in ast.walk(hit)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str)}
            self.assertIn(var, names,
                          "%s: registry says it reads %s, the source does not name that variable "
                          "(it names %s)" % (key, var, sorted(n for n in names if n.isupper())))


class TestClassificationStillHolds(unittest.TestCase):
    """The registry's two kinds, pinned behaviourally. If a constant changes sides, this goes red
    here — where it is cheap — instead of inside a fixture that has already written to live data."""

    @staticmethod
    def _with_env(var, value, fn):
        old = os.environ.get(var)
        os.environ[var] = value
        try:
            return fn()
        finally:
            if old is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = old

    def test_import_bound_constant_ignores_a_later_env_change(self):
        import control_app
        before = control_app._CHRON_EVIDENCE_PATH
        after = self._with_env("TV_CHRON_EVIDENCE", "/tmp/should-never-be-used.json",
                               lambda: control_app._CHRON_EVIDENCE_PATH)
        self.assertEqual(
            before, after,
            "_CHRON_EVIDENCE_PATH now moves with TV_CHRON_EVIDENCE. If that is deliberate, "
            "reclassify it 'call-time' in REGISTRY — the fixture advice changes with it.")

    def test_patching_the_attribute_is_the_redirect_that_takes(self):
        """The remedy the conftest canary prescribes, proven to work — an instruction nobody has
        run is a rumour."""
        import control_app
        tmp = "/tmp/evidence-redirect-proof.json"
        with mock.patch.object(control_app, "_CHRON_EVIDENCE_PATH", tmp):
            self.assertEqual(tmp, control_app._CHRON_EVIDENCE_PATH)
        self.assertNotEqual(tmp, control_app._CHRON_EVIDENCE_PATH, "the patch leaked")

    def test_call_time_resolver_honours_a_later_env_change(self):
        """control_app resolves TV_SESSIONS per call — this is why the blanket static rule was
        wrong, and it must keep being true or half the suite's isolation is a no-op."""
        import control_app
        before = control_app._journal_path()
        moved = self._with_env("TV_SESSIONS", "/tmp/journal-redirect-proof.jsonl",
                               control_app._journal_path)
        self.assertEqual("/tmp/journal-redirect-proof.jsonl", moved,
                         "_journal_path() stopped honouring TV_SESSIONS")
        self.assertEqual(before, control_app._journal_path(), "TV_SESSIONS leaked out of the test")

    def test_replay_journal_is_the_opposite_answer_for_the_same_variable(self):
        """Same variable, other module, other answer. This asymmetry is the trap the registry
        exists to publish: TV_SESSIONS works mid-test for control_app and is a NO-OP for replay."""
        import replay
        before = replay.JOURNAL
        after = self._with_env("TV_SESSIONS", "/tmp/replay-journal-proof.jsonl",
                               lambda: replay.JOURNAL)
        self.assertEqual(before, after,
                         "replay.JOURNAL now moves with TV_SESSIONS — reclassify it 'call-time'.")


if __name__ == "__main__":
    unittest.main()
