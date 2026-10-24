# -*- coding: utf-8 -*-
"""REG-2592 — A PROOF THAT ASKS ABOUT HIS VENUE IS ELSEWHERE ON A RUNNER, NEVER A RED THERE.

⚠ WHAT IT IS FOR. The 16-shard CI run at dcff7160 stranded shards on laws whose clean run is red on any host that is
not his Mac, by construction: live_panel_gate and vault_wilson's live-witness door read a running console on 17772;
human_eyes_gate reads his gitignored ledger; reel_demo grades footage on his gitignored shelf; overlap_ratchet compares
against a baseline measured on his platform (font metrics differ). And one REG-2356 proof is BLIND on Linux by
construction (Linux keeps a zombie's group). None of those is a code defect a runner can see - each is a fact about
the venue - so each proof DECLARES what it needs (REG-1686), the runner reads ELSEWHERE, and the Mac proves it
alongside (proof_keys_mac: a need CI_HAS does not name).

⚠ THE DEFECTS THIS GUARDS:
  · a declaration dropped: the proof turns red on every runner again, and its shard owes it forever;
  · a probe that says yes where the venue is missing (a runner proves it and reads UNPROVABLE), or no where it is
    present (his Mac skips a proof it can run - and nobody proves it at all);
  · the probes moved into heart2 by import: browser_gates follows heart2's imports, and overlap_ratchet's closure
    reaches a browser - that one import put 699 gates under the one-browser lock instead of 69.
No console, ledger, shelf or baseline is touched: every probe input is patched. RED_PROOF below.
"""
import ast
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable as _console_safe_enable  # noqa: E402  (it prints non-ASCII)
_console_safe_enable()
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import heart2            # noqa: E402
import proof_keys_mac    # noqa: E402

DECLARED = [("live_panel_gate.py", 0, "live-console"), ("test_gate_banks.py", 3, "live-console"),
            ("human_eyes_gate.py", 0, "human-eyes-ledger"), ("reel_demo.py", 0, "reel-shelf"),
            ("overlap_ratchet.py", 0, "overlap-venue"), ("test_a_killed_run_is_never_a_red.py", 22, "macos")]
VENUES = {"live-console": ("live_panel_gate", "console_here"), "human-eyes-ledger": ("human_eyes_ledger", "ledger_here"),
          "reel-shelf": ("reel_demo", "shelf_here"), "overlap-venue": ("overlap_ratchet", "venue_here")}


class EachProofSaysWhatItNeeds(unittest.TestCase):

    def test_each_venue_proof_declares_its_need(self):
        for f, i, need in DECLARED:
            got = (heart2.red_proofs_in(f) or [])[i].get("needs")
            self.assertEqual(got, need, "%s RED_PROOF[%d] no longer declares %r - a runner reads it red" % (f, i, need))

    def test_each_need_names_its_gates_own_probe(self):
        for need, (mod, fn) in VENUES.items():
            self.assertEqual(heart2.PROOF_NEEDS_HOST[need][:2], (mod, fn), need)

    def test_macos_is_asked_of_the_platform(self):
        self.assertIs(heart2.host_lacks("macos")[0], sys.platform != "darwin",
                      "the zombie proof's need is not asked: Linux judges a proof that is BLIND there")

    def test_the_mac_proves_each_alongside(self):
        for need in list(VENUES) + ["macos"]:
            self.assertNotIn(need, proof_keys_mac.CI_HAS, "%s is read as one CI has: nobody proves it" % need)

    def test_heart2_imports_no_gate_module(self):
        with open(os.path.join(HERE, "heart2.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module.split(".")[0])
        hit = names & set(m for m, _f in VENUES.values())
        self.assertFalse(hit, "heart2 imports %s: browser_gates now locks every gate that imports heart2" % sorted(hit))


class HostLacksAsksTheProbe(unittest.TestCase):

    def test_a_missing_venue_is_ELSEWHERE_and_a_present_one_is_judged(self):
        for need, (mod, fn) in VENUES.items():
            m = __import__(mod)
            with mock.patch.object(m, fn, lambda: False):
                self.assertIs(heart2.host_lacks(need)[0], True, need)
            with mock.patch.object(m, fn, lambda: True):
                self.assertIs(heart2.host_lacks(need)[0], False, need)


class EachProbeAsksItsOwnQuestion(unittest.TestCase):

    def test_the_console(self):
        import live_panel_gate as G
        for port, want in ((True, True), (False, False), (None, False)):
            with mock.patch.object(G, "_port_open", lambda *a, **k: port):
                self.assertIs(G.console_here(), want, "port %r" % (port,))

    def test_the_ledger(self):
        import human_eyes_ledger as L
        tmp = tempfile.mkdtemp(prefix="venue-")
        self.addCleanup(shutil.rmtree, tmp, True)
        p = os.path.join(tmp, "ledger.jsonl")
        with mock.patch.object(L, "LEDGER_PATH", p):
            self.assertIs(L.ledger_here(), False)
            open(p, "w").close()
            self.assertIs(L.ledger_here(), True)

    def test_the_shelf(self):
        import reel_demo as R
        for state, want in (("absent", False), ("empty", False), ("present", True), ("broken", True)):
            with mock.patch.object(R, "_shelf", lambda: (state, "why")):
                self.assertIs(R.shelf_here(), want, state)

    def test_the_overlap_baseline(self):
        import overlap_ratchet as O
        for was in (None, {}, [], {"x": 1}):
            with mock.patch.object(O, "_baseline", lambda: (was, "missing")):
                self.assertIs(O.venue_here(), True, "baseline %r is a broken gate - judged everywhere, never "
                                                    "ELSEWHERE everywhere" % (was,))
        for match, want in ((True, True), (False, False)):
            with mock.patch.object(O, "_baseline", lambda: ({"_venue": "x"}, None)), \
                    mock.patch.object(O, "_venue_matches", lambda was: (match, "why")):
                self.assertIs(O.venue_here(), want, match)


class AVenueTheSandboxNeverCarriesIsElsewhere(unittest.TestCase):
    """REG-2660 - MEASURED on his Mac at 27b9a028: reel_demo PASSED 12 of 12 over 70 reels in his tree, yet heart2 filed it
    ALREADY RED, because the host probe said "shelf here" and the proof ran in a sandbox safe_copy builds without
    tv/frames. The need is asked of the sandbox too, and a sandbox without footage is ELSEWHERE, never red."""

    def test_footage_is_entries_on_the_shelf(self):
        import reel_demo as R
        import tv_diablo as TD
        tmp = tempfile.mkdtemp(prefix="venue-shelf-")
        self.addCleanup(shutil.rmtree, tmp, True)
        hist = os.path.join(tmp, "hist")
        with mock.patch.object(TD, "HIST_DIR", hist):
            self.assertIs(R.footage_here(), False, "absent")
            os.mkdir(hist)
            self.assertIs(R.footage_here(), False, "an established empty shelf")
            open(os.path.join(hist, ".probe"), "w").close()
            self.assertIs(R.footage_here(), False, "a dot-probe is not footage")
            os.mkdir(os.path.join(hist, "reel_s_1_2"))
            self.assertIs(R.footage_here(), True, "a reel")

    def _tree(self, body):
        tmp = tempfile.mkdtemp(prefix="venue-sbx-")
        self.addCleanup(shutil.rmtree, tmp, True)
        with open(os.path.join(tmp, "reel_demo.py"), "w") as fh:
            fh.write("def footage_here():\n    %s\n" % body)
        return tmp

    def test_the_sandbox_is_asked_in_the_sandbox(self):
        self.assertIs(heart2._sandbox_lacks(self._tree("return False"), "reel-shelf"), True)
        self.assertIs(heart2._sandbox_lacks(self._tree("return True"), "reel-shelf"), False)
        self.assertIsNone(heart2._sandbox_lacks(self._tree("raise RuntimeError('x')"), "reel-shelf"),
                          "a probe that cannot answer is UNKNOWN - judged as usual, never ELSEWHERE")
        self.assertIsNone(heart2._sandbox_lacks(self._tree("return False"), "macos"), "only declared sandbox venues")

    def test_host_has_it_sandbox_lacks_it_is_elsewhere_not_red(self):
        said = []
        with mock.patch.object(heart2, "host_lacks", lambda n: (False, "footage")), \
                mock.patch.object(heart2, "_sandbox_lacks", lambda s, n: True):
            got = heart2._prove_one(tempfile.gettempdir(), "reel_demo", "reel_demo.py",
                                    {"file": "reel_demo.py", "find": "x", "replace": "y", "needs": "reel-shelf"},
                                    0, said.append, dry=True)
        self.assertEqual(got, heart2.ELSEWHERE, said)


RED_PROOF = [
    {"why": "REG-2660 - the sandbox is no longer asked: a green reel_demo is filed ALREADY RED on his Mac",
     "file": "heart2.py",
     "find": "if _sandbox_lacks(sandbox, _need) is True:",
     "replace": "if False:",
     "matches": 1},
    {"why": "REG-2592 - live-panel's proof no longer declares the console: every runner reads it red",
     "file": "live_panel_gate.py",
     "find": "'matches': 2, 'needs': 'live-console',",
     "replace": "'matches': 2,",
     "matches": 1},
    {"why": "REG-2592 - vault_wilson's live-witness proof no longer declares the console",
     "file": "test_gate_banks.py",
     "find": "\"matches\": 1, \"needs\": \"live-console\",",
     "replace": "\"matches\": 1,",
     "matches": 1},
    {"why": "REG-2592 - human-eyes' proof no longer declares the ledger",
     "file": "human_eyes_gate.py",
     "find": "'matches': 1, 'needs': 'human-eyes-ledger',",
     "replace": "'matches': 1,",
     "matches": 1},
    {"why": "REG-2592 - reel_demo's proof no longer declares the shelf",
     "file": "reel_demo.py",
     "find": "\"matches\": 2, \"needs\": \"reel-shelf\",",
     "replace": "\"matches\": 2,",
     "matches": 1},
    {"why": "REG-2592 - overlap_ratchet's proof no longer declares its venue",
     "file": "overlap_ratchet.py",
     "find": "'matches': 1, 'needs': 'overlap-venue',",
     "replace": "'matches': 1,",
     "matches": 1},
    {"why": "REG-2592 - the Linux-BLIND zombie proof no longer declares macOS",
     "file": "test_a_killed_run_is_never_a_red.py",
     "find": "ELSEWHERE on Linux and Windows, never BLIND there.\n     \"matches\": 1, \"needs\": \"macos\"},",
     "replace": "ELSEWHERE on Linux and Windows, never BLIND there.\n     \"matches\": 1},",
     "matches": 1},
    {"why": "REG-2592 - an unparseable console address reads as a console",
     "file": "live_panel_gate.py",
     "find": "    return _port_open() is True\n",
     "replace": "    return _port_open() is not False\n",
     "matches": 1},
    {"why": "REG-2592 - every PC claims his ledger",
     "file": "human_eyes_ledger.py",
     "find": "    return os.path.exists(LEDGER_PATH)\n",
     "replace": "    return True\n",
     "matches": 1},
    {"why": "REG-2592 - an empty shelf reads as footage",
     "file": "reel_demo.py",
     "find": "    return _shelf()[0] not in (\"absent\", \"empty\")\n",
     "replace": "    return _shelf()[0] not in (\"absent\",)\n",
     "matches": 1},
    {"why": "REG-2592 - a baseline of another platform reads as this one's",
     "file": "overlap_ratchet.py",
     "find": "    return _venue_matches(was)[0]\n",
     "replace": "    return True\n",
     "matches": 1},
    {"why": "REG-2592 - an unstamped or empty baseline is excused as a venue gap: ELSEWHERE on every host, never proved",
     "file": "overlap_ratchet.py",
     "find": "    if not isinstance(was, dict) or not was.get(\"_venue\"):\n        return True\n",
     "replace": "    if was is None:\n        return True\n",
     "matches": 1},
    {"why": "REG-2592 - heart2 asks a probe that is not the gate's own",
     "file": "heart2.py",
     "find": "    \"live-console\": (\"live_panel_gate\", \"console_here\",\n",
     "replace": "    \"live-console\": (\"live_panel_gate\", \"_port_open\",\n",
     "matches": 1},
    {"why": "REG-2592 - heart2 imports a gate module: its browser closure reaches every gate",
     "file": "heart2.py",
     "find": "def host_lacks(need):\n",
     "replace": "def host_lacks(need):\n    import overlap_ratchet  # noqa: F401\n",
     "matches": 1},
    {"why": "REG-2592 - a venue need is read as one CI has: nobody proves it",
     "file": "proof_keys_mac.py",
     "find": "CI_HAS = frozenset((\"posix\", \"posix-signals\", \"bash\", \"node\", \"numpy\", \"dir-link\"))",
     "replace": "CI_HAS = frozenset((\"posix\", \"posix-signals\", \"bash\", \"node\", \"numpy\", \"dir-link\", \"reel-shelf\"))",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
