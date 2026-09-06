# -*- coding: utf-8 -*-
"""t133/t166 — A FOUND ROW SAID *WHEN*, AND NOTHING ABOUT HOW ANYONE KNOWS.

MEASURED on his real store, 2026-09-06: `d2r_foundLog` is 419 rows of DISPLAY STRINGS —
"Aug 21, 2026 · 14:03" — carrying no reel, no frame and no witness. So no found row can be
re-verified, and t133 ("no per-entry evidence") had nothing to stand on.

=== THE EVIDENCE WAS NEVER MISSING, AND THAT IS THE WHOLE FINDING ===
`wouldAdd.uniques` AND `wouldAdd.sets` rows have carried `witnesses` (the gate's verdict codes)
and `seen[]` ({reel, frame, lane}) since v1864 — ONE dict comprehension over both ledgers at
tv/control_app.py:22378-22385 — and both survive into the browser payload (:11425). The apply
loop already hands the whole row to `_chRecordApplied` (bible.html:44798), which DOES read
`row.witnesses` and `row.seen[0]`.

⚠ IT WRITES `d2r_chronicleInboxLog`, WHICH IS TRIMMED TO THE LAST 400 ROWS (bible.html:49816).
With 419 found names the oldest evidence is already being evicted, and an inbox row is not a
ledger row. Two halves each built correctly, never joined: the found ledger and its proof.
[[the-unjoined-end]]

=== WHAT THIS PINS, AND WHAT IT REFUSES TO PIN ===
`tv/test_a_seal_is_per_session.py` says why: a gate pinned to the BYTES of a fix holds the
spelling of that fix in place and grades nothing about the behaviour. So this file runs the REAL
apply loop, sliced out of bible.html by anchor and executed in node against a synthetic store,
and asks what LANDED. [[regression-guard]]

⚠⚠ THE HARD HALF IS THE ABSENCE. A hand-clicked tick has NO sightings to thread — that is a real
limit of his data, not a defect — and the write has to say so honestly:

    nobody looked          ->  no row at all, `foundEvidenceFor` answers null
    the gate looked and
      corroborated nothing ->  `witnesses: []`  — measured, and measured empty

Collapsing those two is a lie with no author, and the shape it always arrives in is a single
`||` or `??`: `(row.witnesses || [])` turns "nobody looked" into "measured zero" and nothing
downstream can ever tell again. Two laws below exist only to catch that one character.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

⚠ NO NODE = SKIP WITH A DECLARED REASON, NEVER A PASS.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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


def _slice(src, start, end, inclusive=True):
    """Anchored at BOTH ends. Never `src[i:i+N]` — a fixed window past the region reads as
    ABSENT, which is how four false findings were published in this repo. [[source-reading-guard]]
    """
    i = src.find(start)
    if i < 0:
        return None
    j = src.find(end, i + len(start))
    if j < 0:
        return None
    return src[i:j + (len(end) if inclusive else 0)]


def _src():
    return io.open(BIBLE, encoding="utf-8").read()


def _regions(src=None):
    """The five real regions this behaviour lives in. -> dict or None if any is unslicable."""
    src = _src() if src is None else src
    out = {
        "wr": _slice(src, "window._foundEvidenceSet = function(name, row){",
                     "\n  window.foundEvidenceFor = function(name){", inclusive=False),
        "rd": _slice(src, "window.foundEvidenceFor = function(name){",
                     "\n  window._foundEvidenceDrop = function(names){", inclusive=False),
        "dr": _slice(src, "window._foundEvidenceDrop = function(names){",
                     "      return ch;\n    } catch(e){ return false; }\n  };"),
        "uni": _slice(src, "    (add.uniques || []).forEach(function(row){",
                      "\n    (add.sets || []).forEach(function(row){", inclusive=False),
        "sets": _slice(src, "    (add.sets || []).forEach(function(row){",
                       "\n    // v1530 — A SET THE PANEL CALLED COMPLETE.", inclusive=False),
    }
    return out


#: The one line of `toggleOwned` this gate's node stub reproduces. Pinned as its own law below,
#: so the fixture cannot quietly stop resembling the thing it stands in for — the fixture is the
#: usual culprit. [[feedback-fixtures-never-touch-live-data]]
TOGGLE_WRITE = ("else fl[name] = window._grailStamp ? window._grailStamp() : "
                "new Date().toLocaleString();")

HARNESS = r"""
globalThis.window = globalThis;
const STORE = {};
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE,k) ? STORE[k] : null; },
  setItem: function(k,v){ STORE[k] = String(v); },
  removeItem: function(k){ delete STORE[k]; }
};
window._grailStamp = function(){ return 'Sep 6, 2026 \u00b7 12:00'; };

/* THE STUB IS THE MEASURED WRITE, NOT AN INVENTION. bible.html:22595 —
   `else fl[name] = window._grailStamp ? window._grailStamp() : new Date().toLocaleString();`
   — reduced to the one line t133 traced. A law above pins that the real line still says this. */
function _tick(name){
  var fl = {};
  try { fl = JSON.parse(window.LSR.getItem('d2r_foundLog') || '{}') || {}; } catch(e){}
  fl[name] = window._grailStamp();
  window.LSR.setItem('d2r_foundLog', JSON.stringify(fl));
}
window.toggleOwned   = function(n){ _tick(n); };
window.toggleSetPiece = function(p){ _tick(p); };

window._gameFoundSet      = function(){ return false; };
window._gameStampToLedger = function(){ return ''; };
window._chRecordApplied   = function(){ return null; };
window._vaultMayClaim     = function(){ return false; };
window.tvVaultRegister    = function(){ return { ok:false, why:'not this law' }; };
window._tvExtraRemember   = function(){};
window._chronSetPieceSet  = function(){ return new Set(%(pieces)s); };

var ALREADY_UNI = %(alreadyUni)s, ALREADY_SET = %(alreadySet)s;
function _chronAlreadyUni(n){ return ALREADY_UNI.indexOf(n) >= 0; }
function _chronAlreadySet(n){ return ALREADY_SET.indexOf(n) >= 0; }
function _chAlreadyVaulted(){ return false; }
var _vaultReport = function(){ return false; };

var res = { uniques: [], sets: [], skipped: [], unknown: [], ts: Date.now() };
var add = %(add)s;

%(wr)s
%(rd)s
%(dr)s
%(uni)s
%(sets)s

%(after)s

var _ev = {};
try { _ev = JSON.parse(window.LSR.getItem('d2r_foundEvidence') || '{}') || {}; } catch(e){}
console.log(JSON.stringify({
  foundLog: JSON.parse(window.LSR.getItem('d2r_foundLog') || '{}'),
  evidenceRaw: _ev,
  evidenceKeys: Object.keys(_ev),
  reads: %(reads)s.map(function(n){
    var v = window.foundEvidenceFor(n);
    return { name: n, isNull: v === null, value: v };
  }),
  res: res
}));
"""


def _run(add, reads, already_uni=(), already_set=(), pieces=(), after=""):
    """Execute the REAL loop against a synthetic store. -> (result, why_not)"""
    r = _regions()
    missing = [k for k, v in r.items() if v is None]
    if missing:
        return None, "regions unslicable from bible.html: %s" % ", ".join(sorted(missing))
    js = HARNESS % {
        "add": json.dumps(add, ensure_ascii=False),
        "reads": json.dumps(list(reads), ensure_ascii=False),
        "alreadyUni": json.dumps(list(already_uni), ensure_ascii=False),
        "alreadySet": json.dumps(list(already_set), ensure_ascii=False),
        "pieces": json.dumps(list(pieces), ensure_ascii=False),
        "after": after,
        "wr": r["wr"], "rd": r["rd"], "dr": r["dr"], "uni": r["uni"], "sets": r["sets"],
    }
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.cjs")
    io.open(p, "w", encoding="utf-8").write(js)
    try:
        out = subprocess.check_output(["node", p], stderr=subprocess.STDOUT, timeout=60)
        return json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1]), ""
    except subprocess.CalledProcessError as e:
        return None, "node refused: %s" % e.output.decode("utf-8", "replace")[-600:]
    finally:
        shutil.rmtree(d, ignore_errors=True)


#: The payload shape control_app.py:22378-22385 actually emits, for both ledgers.
SWEPT = {"name": "Harlequin Crest",
         "why": "seen in two separate Chronicle visits",
         "witnesses": ["cross-reel", "cross-lane"],
         "seen": [{"reel": "s_1787495295689_1483", "frame": "f_0041", "lane": "claude"},
                  {"reel": "s_1785078127173_28278", "frame": "f_0112", "lane": "ocr"}]}

#: The gate LOOKED at this one and could corroborate nothing. `[]` is a measurement.
LOOKED_EMPTY = {"name": "Black Cleft", "why": "one uncorroborated read",
                "witnesses": [], "seen": []}

#: A row from a producer that never emits either key. NOBODY LOOKED.
BARE = {"name": "Death Mask"}


@unittest.skipIf(shutil.which("node") is None,
                 "node is absent — this gate runs REAL bible.html javascript, and without an "
                 "engine it is a SKIP with a declared reason, never a pass")
class AFoundRowCarriesItsEvidence(unittest.TestCase):

    # ── ⚠ FIRST, THE SUBJECT. A law that cannot find what it grades passes having examined
    #    nothing, which is the most convincing green there is. ───────────────────────────────
    def test_the_subject_EXISTS_in_bible_html(self):
        r = _regions()
        missing = sorted(k for k, v in r.items() if v is None)
        self.assertEqual(
            [], missing,
            "these regions could not be sliced out of bible.html: %s — the evidence writer or "
            "the apply loop was renamed or removed, and every law below would have passed "
            "having graded ZERO lines. Fix this guard before trusting a green from it."
            % ", ".join(missing))
        self.assertIn("_foundEvidenceSet", r["uni"],
                      "the accepted-uniques loop no longer threads the row's evidence — this is "
                      "the exact defect t133 traced: the loop reads row.date and row.gameFound, "
                      "calls toggleOwned(n) with the bare name, and the sightings the payload "
                      "carried are dropped on the floor")

    def test_the_node_stub_still_matches_the_REAL_toggleOwned_write(self):
        """The fixture is the usual culprit. If toggleOwned stops writing a bare display string,
        this gate is grading a write that no longer happens. [[feedback-blind-fixture-green-gate]]
        """
        src = _src()
        self.assertIn(TOGGLE_WRITE, src,
                      "toggleOwned's foundLog write has changed shape. The node stub in this file "
                      "reproduces it verbatim; update BOTH or this gate measures a fiction.")

    def test_the_reason_this_store_exists_STILL_HOLDS(self):
        """The evidence already reaches `d2r_chronicleInboxLog` — and that ring is TRIMMED. If the
        cap ever goes away the premise of this whole fix changes, and a stale premise is how a
        gate outlives its subject. [[stale-reading]]"""
        src = _src()
        self.assertIn("_chLsSet(_CH_LOG_KEY, (log || []).slice(-400));", src,
                      "the inbox ring is no longer trimmed to 400. Re-read whether a separate "
                      "durable evidence store is still the right answer before trusting this file.")

    # ── LAW 1 — a swept row lands with its proof ────────────────────────────────────────────
    def test_a_swept_unique_lands_with_the_reel_and_frame_the_payload_CARRIED(self):
        got, why = _run({"uniques": [SWEPT], "sets": []}, reads=["Harlequin Crest"])
        self.assertIsNotNone(got, why)
        self.assertIn("Harlequin Crest", got["foundLog"],
                      "the apply did not even tick it — this law is measuring nothing")
        ev = got["evidenceRaw"].get("Harlequin Crest")
        self.assertIsNotNone(
            ev, "the row carried 2 witnesses and 2 sightings and the found ledger got a DATE ONLY. "
                "That is t166's 419 display strings, one row at a time.")
        self.assertEqual(["cross-reel", "cross-lane"], ev["witnesses"])
        self.assertEqual("s_1787495295689_1483", ev["sightings"][0]["reel"])
        self.assertEqual("f_0041", ev["sightings"][0]["frame"])
        self.assertEqual("claude", ev["sightings"][0]["lane"])

    # ── LAW 2 — a hand tick has nothing to thread, and says so ──────────────────────────────
    def test_a_HAND_TICK_gets_no_evidence_row_and_reads_back_NULL(self):
        """⚠ THE DIRECTION THAT IS EASIEST TO GET WRONG AND HARDEST TO NOTICE. Most of his 419
        rows were ticked by hand. There is no testimony to record, and the honest answer is that
        nobody looked — not an empty record that reads as "checked, found nothing"."""
        got, why = _run({"uniques": [], "sets": []}, reads=["Griffon's Eye"],
                        after='window.toggleOwned("Griffon\'s Eye");')
        self.assertIsNotNone(got, why)
        self.assertIn("Griffon's Eye", got["foundLog"], "the hand tick did not land")
        self.assertEqual([], got["evidenceKeys"],
                         "a hand tick invented an evidence row: %s" % got["evidenceKeys"])
        self.assertTrue(got["reads"][0]["isNull"],
                        "foundEvidenceFor answered %r for a name nobody ever looked at. `null` is "
                        "'nobody looked'; anything else is a measurement that was never taken."
                        % (got["reads"][0]["value"],))

    # ── LAW 3 — [] and null are DIFFERENT ANSWERS, in both directions ───────────────────────
    def test_a_gate_that_LOOKED_and_found_nothing_records_an_EMPTY_LIST_not_null(self):
        got, why = _run({"uniques": [LOOKED_EMPTY], "sets": []}, reads=["Black Cleft"])
        self.assertIsNotNone(got, why)
        ev = got["evidenceRaw"].get("Black Cleft")
        self.assertIsNotNone(ev, "the gate looked at this row and its answer was discarded")
        self.assertEqual([], ev["witnesses"],
                         "witnesses came back %r. The gate LOOKED and corroborated nothing — that "
                         "is a measurement, and it must survive as []." % (ev["witnesses"],))
        self.assertEqual([], ev["sightings"],
                         "sightings came back %r for a row carrying seen: []"
                         % (ev["sightings"],))

    def test_a_row_that_carries_NEITHER_key_is_recorded_as_null_NOT_as_empty(self):
        """The `(row.witnesses || [])` character. One `||` and 'nobody looked' becomes 'measured
        zero' forever, with nothing downstream able to tell again. [[unknown-stays-unknown]]"""
        got, why = _run({"uniques": [BARE], "sets": []}, reads=["Death Mask"])
        self.assertIsNotNone(got, why)
        self.assertIn("Death Mask", got["foundLog"], "the apply did not tick it")
        ev = got["evidenceRaw"].get("Death Mask")
        if ev is not None:
            self.assertIsNone(ev["witnesses"],
                              "a row with NO witnesses key recorded %r — an empty list here is a "
                              "measurement nobody took" % (ev["witnesses"],))
            self.assertIsNone(ev["sightings"],
                              "a row with NO seen key recorded %r" % (ev["sightings"],))
        else:
            self.assertTrue(got["reads"][0]["isNull"],
                            "no record was written, which is honest — but the reader answered "
                            "%r instead of null" % (got["reads"][0]["value"],))

    # ── LAW 4 — nothing is invented ─────────────────────────────────────────────────────────
    def test_no_sighting_is_INVENTED_for_a_name_that_carried_none(self):
        got, why = _run({"uniques": [SWEPT, BARE], "sets": []},
                        reads=["Harlequin Crest", "Death Mask"])
        self.assertIsNotNone(got, why)
        # ⚠ THE DENOMINATOR. With nothing recorded at all this law finds no borrowed reel and
        # reports clean, having examined an empty store. [[zero-needs-a-denominator]]
        self.assertIsNotNone(got["evidenceRaw"].get("Harlequin Crest"),
                             "the evidenced row in this batch was not recorded, so there was "
                             "nothing for the bare row to borrow and this law graded nothing")
        bare = got["evidenceRaw"].get("Death Mask")
        borrowed = json.dumps(bare or {})
        self.assertNotIn("s_1787495295689_1483", borrowed,
                         "a sighting from ANOTHER row in the same batch attached itself to a name "
                         "that carried none — one read counted twice, which is the shape v1963 "
                         "found on his real board")

    # ── LAW 5 — a SET piece is a found row too ──────────────────────────────────────────────
    def test_a_swept_SET_PIECE_lands_with_its_evidence_as_well(self):
        """toggleSetPiece writes every piece into d2r_foundLog on purpose (v644), and the payload
        builds uniques and sets from ONE dict comprehension — so a sets row carries the same
        `witnesses` and `seen[]`. Threading one ledger and not the other is half a fix."""
        row = dict(SWEPT, name="Immortal King's Will")
        got, why = _run({"uniques": [], "sets": [row]}, reads=["Immortal King's Will"],
                        pieces=["Immortal King's Will"])
        self.assertIsNotNone(got, why)
        self.assertIn("Immortal King's Will", got["foundLog"], "the set piece was not ticked")
        ev = got["evidenceRaw"].get("Immortal King's Will")
        self.assertIsNotNone(
            ev, "the sets branch drops its evidence. Same payload, same ledger, same law.")
        self.assertEqual("s_1787495295689_1483", ev["sightings"][0]["reel"])

    # ── LAW 6 — the retraction reaches every door that already retracts the game date ───────
    def test_an_UN_TICK_retracts_the_evidence_at_EVERY_door(self):
        """v1891 closed the game-date retraction on ONE door; v1963 had to reopen it for the
        others — "a rule implemented at half its entrances is a rule that holds until he uses the
        other half". A stale reel id left behind re-attaches as corroboration to a name he ticks
        by hand later. Same rule, same doors. [[the-unjoined-end]]"""
        src = _src()
        doors = {
            "toggleOwned": _slice(
                src, "try { var _gfU = JSON.parse(window.LSR.getItem('d2r_gameFound')",
                "\n      }   // un-tick also clears any legacy vault entry", inclusive=False),
            "toggleSetPiece": _slice(
                src, "try { var _gfP = JSON.parse(window.LSR.getItem('d2r_gameFound')",
                "\n    } else if (!Object.prototype.hasOwnProperty.call(fl, piece)",
                inclusive=False),
            "setRepair": _slice(
                src, "var _gfR = JSON.parse(window.LSR.getItem('d2r_gameFound')",
                "\n      /* stamp the reading this repair acted on", inclusive=False),
        }
        unfindable = sorted(k for k, v in doors.items() if v is None)
        self.assertEqual([], unfindable,
                         "these retraction doors could not be located, so this law graded nothing: "
                         "%s" % ", ".join(unfindable))
        blind = sorted(k for k, v in doors.items() if "_foundEvidenceDrop" not in v)
        self.assertEqual(
            [], blind,
            "these doors retract the game date and LEAVE THE SIGHTINGS STANDING: %s. The reel id "
            "re-attaches itself the moment he ticks that name by hand later — a claim sourced "
            "from a read he threw away." % ", ".join(blind))

    def test_the_retractor_actually_REMOVES_the_row(self):
        got, why = _run({"uniques": [SWEPT], "sets": []}, reads=["Harlequin Crest"],
                        after="window._foundEvidenceDrop('Harlequin Crest');")
        self.assertIsNotNone(got, why)
        self.assertEqual([], got["evidenceKeys"],
                         "the drop left %s behind" % got["evidenceKeys"])
        self.assertTrue(got["reads"][0]["isNull"],
                        "after a retraction the reader answered %r instead of null"
                        % (got["reads"][0]["value"],))

    # ── LAW 7 — the new store is routed, like every other ledger ────────────────────────────
    def test_the_evidence_store_is_never_read_or_written_BARE(self):
        """Bare `localStorage` means the OWNER's namespace whatever world is active, so one bare
        line lets a guest console read — or overwrite — his chronicle's proof."""
        bad = []
        seen = 0
        for i, line in enumerate(io.open(BIBLE, encoding="utf-8"), 1):
            if "d2r_foundEvidence" not in line or "raw-ok" in line:
                continue
            seen += 1
            stripped = line
            for v in ("getItem(", "setItem(", "removeItem("):
                stripped = stripped.replace("LSR." + v, "")
            if re.search(r"localStorage\.(getItem|setItem|removeItem)\(", stripped):
                bad.append((i, line.strip()[:100]))
        # ⚠ A ZERO NEEDS A DENOMINATOR. With no `d2r_foundEvidence` line anywhere this law returns
        # a clean-looking 0 having examined nothing. [[zero-needs-a-denominator]]
        self.assertGreater(seen, 0,
                           "no d2r_foundEvidence access exists at all — this law graded ZERO "
                           "lines, which is UNKNOWN and not a clean surface")
        self.assertEqual([], bad,
                         "d2r_foundEvidence is accessed bare (%d access line(s) examined):\n%s"
                         % (seen, "\n".join("  L%s %s" % b for b in bad)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
