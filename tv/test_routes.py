#!/usr/bin/env python3
# 🧪 T1 — ROUTE MATRIX · ~1400-ITEM DB SWEEP · FUNNEL DRY-RUN.
# Konyo: "a full test system checking and verifying all routes and funneled coding, against the
# ~1400-item database." Standalone, deterministic, NO AI calls, NO internet — only localhost file
# reads + an ephemeral Handler on 127.0.0.1. Follows tv/test_control.py conventions (unittest, no
# pytest; every test isolates HERE/HIST_DIR/JOURNAL into a tempdir and restores globals in tearDown
# so nothing ever touches the real frames or the real sessions.jsonl).
import contextlib
import inspect
import io
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import control_app as ca  # noqa: E402
import replay as rp  # noqa: E402
import tv_diablo as tvd  # noqa: E402

BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")


# ─────────────────────────────────────────────────────────────────────────────
# DB harvest — the ~1400-item name list, pulled from the SAME name:'…' / n:'…'
# literals ca._kai_vocab() harvests, but kept as FULL names (not tokenized). Built
# once at import; the tests below sweep KAI recognition + the OCR filter over it.
# ─────────────────────────────────────────────────────────────────────────────
def _harvest_db_names():
    """Keep full names (not tokens). Mirrors control_app._kai_vocab sources so the sweep
    and the live lexicon stay one system — v939.1 also pulls openDrop + Title-Case JSON keys
    and Latent/Renewed bare forms (Black Cleft from Latent Black Cleft)."""
    names = set()
    with open(BIBLE, encoding="utf-8", errors="replace") as f:
        txt = f.read()

    def _add(v):
        v = (v or "").strip()
        # drop JS template garbage harvested from name: '${…}' / "n": "`+r+`"
        if not v or "${" in v or "`" in v or v.startswith("' +") or "\\" in v:
            return
        if 3 <= len(v) <= 48:
            names.add(v)
            bare = re.sub(r"^(Latent|Renewed|PreCrafted)\s+", "", v, flags=re.I).strip()
            if bare and bare != v and 3 <= len(bare) <= 48:
                names.add(bare)

    for pat in (r"""(?<![\w"])(?:name|n)\s*:\s*(['"])(.*?)\1""",
                r""""(?:name|n)"\s*:\s*(['"])(.*?)\1"""):
        for m in re.finditer(pat, txt):
            _add(m.group(2))
    for m in re.finditer(r"""openDrop\(\s*(['"])(.*?)\1""", txt):
        _add(m.group(2))
    for m in re.finditer(r'"([A-Z][^"]{2,46})"\s*:', txt):
        key = m.group(1)
        if key.isupper() and " " not in key:
            continue
        if re.fullmatch(r"[A-Za-z0-9_./+-]+", key) and " " not in key and len(key) < 6:
            continue
        if " " not in key and not re.match(r"^[A-Z][a-z]", key):
            continue
        _add(key)
    return sorted(names)


DB_NAMES = _harvest_db_names()


# ═════════════════════════════════════════════════════════════════════════════
# PART A — ROUTE MATRIX (synthetic sessions, no live app)
# ═════════════════════════════════════════════════════════════════════════════
class TestKaiFrameCls(unittest.TestCase):
    """ca._kai_frame_cls(lines, itemish) — funnel routing metadata: which KIND of frame held
    the OCR text. Full matrix: a stash panel word + a tally-tab word → the sub-class; inventory;
    a floating item name → tooltip; nothing item-ish → gameplay."""

    def test_full_matrix(self):
        cases = [
            (["Personal Stash", "Runes"], False, "stash-runes"),
            (["Shared Stash", "Gems"], False, "stash-gems"),
            (["Shared Stash", "Materials"], False, "stash-materials"),
            (["Stash"], False, "stash"),                       # panel open, no tab word
            (["Inventory"], False, "inventory"),
            (["Windforce"], True, "tooltip"),                  # item floats, no panel word
            (["Blood Moor"], False, "gameplay"),               # no item signal at all
            ([], False, "gameplay"),                           # empty → gameplay
        ]
        for lines, itemish, expect in cases:
            self.assertEqual(ca._kai_frame_cls(lines, itemish), expect,
                             "%r (itemish=%s) → %s" % (lines, itemish, expect))

    def test_multi_tally_words_stay_generic_stash(self):
        # v947 — full chrome lists ALL tabs; do not force materials/runes from multi-hit.
        self.assertEqual(ca._kai_frame_cls(["Personal", "Shared", "Gems", "Materials", "Runes"], False), "stash")
        self.assertEqual(ca._kai_frame_cls(["Personal Stash", "Runes Gems"], False), "stash")

    def test_itemish_ignored_once_a_panel_is_open(self):
        # a stash panel word wins even when an item name also floats (itemish=True).
        self.assertEqual(ca._kai_frame_cls(["Shared Stash", "Windforce"], True), "stash")


class TestWatchdog(unittest.TestCase):
    """ca._watchdog_check(sid, sess_rows) — the hardcoded D2R safeguards. It APPENDS violation
    rows to os.path.join(HERE, 'sessions.jsonl'), so HERE is repointed at a tempdir for every
    test (restored in tearDown) — the real journal is never touched, and we assert on the returned
    violation rows AND on the isolated file."""

    def setUp(self):
        self._old_here = ca.HERE
        self.tmp = tempfile.mkdtemp(prefix="tvd-wd-")
        ca.HERE = self.tmp
        open(os.path.join(self.tmp, "sessions.jsonl"), "w").close()

    def tearDown(self):
        ca.HERE = self._old_here
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def _deep(**kw):
        row = {"lane": "deep", "scene": "loot", "names": [], "ts": 1_700_000_000_000}
        row.update(kw)
        return row

    @staticmethod
    def _rules(out):
        return sorted(v["watchdog"]["rule"] for v in out)

    def _journaled_rules(self):
        rules = []
        with open(os.path.join(self.tmp, "sessions.jsonl"), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    r = json.loads(ln)
                    if r.get("lane") == "watchdog":
                        rules.append(r["watchdog"]["rule"])
        return rules

    # ── rule 1: tally-tab-visited-needs-receipt ──────────────────────────────
    def test_visited_no_receipt_each_tab(self):
        for tab in ("runes", "gems", "materials"):
            out = ca._watchdog_check("s_%s" % tab, [self._deep(stashTab=tab)])
            self.assertEqual(self._rules(out), ["tally-tab-visited-needs-receipt"], tab)
            self.assertEqual(out[0]["watchdog"]["tab"], tab)

    def test_visited_with_receipt_is_clean(self):
        rows = [self._deep(stashTab="runes"),
                {"lane": "intake", "intake": {"tab": "runes"}, "ts": 1_700_000_000_100}]
        out = ca._watchdog_check("s_ok", rows)
        self.assertEqual(out, [])

    # ── rule 2: stash-open-no-tab-reads ──────────────────────────────────────
    def test_stash_open_no_tab_reads(self):
        out = ca._watchdog_check("s_st", [self._deep(scene="stash", stashTab="")])
        self.assertEqual(self._rules(out), ["stash-open-no-tab-reads"])

    def test_stash_open_with_a_tab_read_is_clean(self):
        # stash opened but a tab WAS read AND receipted → no violation of either rule.
        rows = [self._deep(scene="stash", stashTab="gems"),
                {"lane": "intake", "intake": {"tab": "gems"}, "ts": 1_700_000_000_100}]
        out = ca._watchdog_check("s_st2", rows)
        self.assertEqual(out, [])

    # ── rule 3: text-eye-silent-all-session ──────────────────────────────────
    def test_text_eye_silent_fires_on_busy_named_session(self):
        rows = [self._deep(scene="loot", names=(["Shako"] if i == 0 else []))
                for i in range(6)]                              # 6 deep reads, >=1 named, no text-eye
        out = ca._watchdog_check("s_te", rows)
        self.assertEqual(self._rules(out), ["text-eye-silent-all-session"])

    def test_quiet_session_no_named_reads_no_violation(self):
        # 6 deep reads but NONE named → the text eye legitimately had nothing to trigger on.
        rows = [self._deep(scene="loot") for _ in range(6)]
        out = ca._watchdog_check("s_quiet", rows)
        self.assertEqual(out, [])

    def test_text_eye_beat_present_silences_the_rule(self):
        rows = [self._deep(scene="loot", names=(["Shako"] if i == 0 else [])) for i in range(6)]
        rows.append({"why": "text-eye", "ts": 1_700_000_000_200})   # a real trigger beat landed
        out = ca._watchdog_check("s_te_ok", rows)
        self.assertEqual(out, [])

    def test_below_six_deep_reads_never_fires_text_eye(self):
        rows = [self._deep(scene="loot", names=["Shako"]) for _ in range(5)]
        out = ca._watchdog_check("s_five", rows)
        self.assertEqual(out, [])

    # ── isolation + multi-violation ──────────────────────────────────────────
    def test_multiple_violations_and_journaled_to_isolated_file(self):
        # 6 named deep reads on an OPEN stash where no tab was ever read → stash-open fires AND
        # the text eye never triggered → text-eye-silent fires. (A tally-visit can't co-fire with
        # stash-open: setting a stashTab to be "visited" also makes any_tab_read True.)
        rows = [self._deep(scene="stash", stashTab="", names=(["Shako"] if i == 0 else []))
                for i in range(6)]
        out = ca._watchdog_check("s_multi", rows)
        self.assertEqual(self._rules(out),
                         ["stash-open-no-tab-reads", "text-eye-silent-all-session"])
        # the rows landed in the TEMPDIR journal, proving HERE isolation held.
        self.assertEqual(sorted(self._journaled_rules()),
                         ["stash-open-no-tab-reads", "text-eye-silent-all-session"])


class TestFunnelGapGrouping(unittest.TestCase):
    """v937 KAI FUNNEL slice-1 gap detection. The escalation stage is inline in _kai_closer_loop
    (not a callable), so this replicates its pure set/grouping math EXACTLY and asserts the
    contract: gaps = tally tabs VISITED-but-not-RECEIPTED, and per gap the funnel picks the LAST
    missed frame of that class (most recent view wins). The class strings come from the REAL
    ca._kai_frame_cls, tying the replica to production."""

    @staticmethod
    def _gaps_and_targets(sess_rows, missed):
        # ── copied verbatim from _kai_closer_loop's funnel stage ──
        visited, receipted = set(), set()
        for r2 in sess_rows:
            if r2.get("lane") == "deep":
                t2 = str(r2.get("stashTab") or "").lower()
                if t2 in ("runes", "gems", "materials"):
                    visited.add(t2)
            ik2 = r2.get("intake")
            if isinstance(ik2, dict) and str(ik2.get("tab") or "").lower():
                receipted.add(str(ik2.get("tab") or "").lower())
        gaps = [t for t in ("runes", "gems", "materials") if t in visited and t not in receipted]
        by_tab = {}
        for mrec in missed:
            c2 = str(mrec.get("cls") or "")
            if c2.startswith("stash-") and c2[6:] in gaps:
                by_tab[c2[6:]] = mrec   # last wins = most recent view of that tab
        return gaps, by_tab

    def test_gap_is_visited_minus_receipted(self):
        rows = [{"lane": "deep", "stashTab": "runes"},
                {"lane": "deep", "stashTab": "gems"},
                {"lane": "intake", "intake": {"tab": "gems"}}]   # gems receipted, runes not
        gaps, _ = self._gaps_and_targets(rows, [])
        self.assertEqual(gaps, ["runes"])

    def test_grouping_picks_last_missed_frame_per_tab(self):
        # two runes-class misses; the funnel must chauffeur the LAST (most recent) one.
        cls = ca._kai_frame_cls(["Personal Stash", "Runes"], False)   # == "stash-runes"
        self.assertEqual(cls, "stash-runes")
        rows = [{"lane": "deep", "stashTab": "runes"}]
        missed = [{"f": "early.jpg", "ts": 10, "cls": cls},
                  {"f": "late.jpg", "ts": 20, "cls": cls}]
        gaps, by_tab = self._gaps_and_targets(rows, missed)
        self.assertEqual(gaps, ["runes"])
        self.assertEqual(by_tab["runes"]["f"], "late.jpg")

    def test_receipted_tab_produces_no_funnel_target(self):
        rows = [{"lane": "deep", "stashTab": "runes"},
                {"lane": "intake", "intake": {"tab": "runes"}}]
        missed = [{"f": "x.jpg", "ts": 5, "cls": "stash-runes"}]
        gaps, by_tab = self._gaps_and_targets(rows, missed)
        self.assertEqual(gaps, [])
        self.assertEqual(by_tab, {})


class TestIntakeReceiptDedupe(unittest.TestCase):
    """v935.11 R3 — the /intake_result receipt route (control outlives the dying agent bridge).
    Driven through a REAL ephemeral Handler on 127.0.0.1 with HERE repointed at a tempdir. The
    exact-triple dedupe: same (frameId, tab, counts, ok/total/errors) within 5min = dup; different
    counts = a genuine correction that journals; an EMPTY frameId carries no identity so it always
    journals (never collapses two anonymous shots)."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self._old_here = ca.HERE
        self.tmp = tempfile.mkdtemp(prefix="tvd-intake-")
        ca.HERE = self.tmp
        open(os.path.join(self.tmp, "sessions.jsonl"), "w").close()

    def tearDown(self):
        ca.HERE = self._old_here
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _post(self, payload):
        req = urllib.request.Request(
            "http://127.0.0.1:%d/intake_result" % self.port,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())

    def _intake_rows(self):
        rows = []
        with open(os.path.join(self.tmp, "sessions.jsonl"), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln and json.loads(ln).get("lane") == "intake":
                    rows.append(json.loads(ln))
        return rows

    def test_exact_duplicate_collapses(self):
        # v938.7 — REG-036 fixed: both sides of the dedupe compare now build the SAME
        # 4-element sig ([counts, ok, total, errors], sort_keys). An exact duplicate within
        # ±5min collapses to one journal row; the second POST answers dup:true.
        rec = {"frameId": "f1", "tab": "runes", "counts": {"El": 2}, "total": 2, "errors": 0, "ok": True}
        s1, b1 = self._post(rec)
        s2, b2 = self._post(dict(rec))
        self.assertEqual((s1, s2), (200, 200))
        self.assertNotIn("dup", b1)
        self.assertTrue(b2.get("dup"), "exact duplicate must collapse (REG-036)")
        self.assertEqual(len(self._intake_rows()), 1)

    def test_different_counts_journal_separately(self):
        self._post({"frameId": "f1", "tab": "runes", "counts": {"El": 2}})
        self._post({"frameId": "f1", "tab": "runes", "counts": {"El": 3}})   # a re-tally correction
        self.assertEqual(len(self._intake_rows()), 2)

    def test_empty_frame_id_always_journals(self):
        rec = {"frameId": "", "tab": "runes", "counts": {"El": 2}}
        self._post(dict(rec))
        self._post(dict(rec))
        self.assertEqual(len(self._intake_rows()), 2)          # anonymous shots never collapse

    def test_captureTs_derived_from_frame_id_not_receipt_time(self):
        # A0 fix (2026-07-21, arch panel Q5 blocker): the client stamps `ts` with Date.now() at
        # receipt-landing time — auto-intake (screenshot+tally) takes SECONDS, so `ts` floats
        # seconds right of the frame it describes. captureTs must instead be the frame's own
        # capture ms, decoded from frameId ("{n}_{captureMs}"), so the retro scrub (which joins
        # on captureTs, never ts) lands the receipt on the photo it actually describes.
        cap_ms = 1_753_000_000_000
        receipt_ts = cap_ms + 4_500          # receipt lands 4.5s after the frame was captured
        self._post({"frameId": "7_%d" % cap_ms, "tab": "runes",
                     "counts": {"El": 2}, "ts": receipt_ts})
        rows = self._intake_rows()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("captureTs"), cap_ms,
                          "captureTs must be the FRAME's capture ms, not the receipt-landing ts")
        self.assertEqual(row.get("ts"), receipt_ts,
                          "ts stays the receipt-landing time — ts and captureTs are DIFFERENT")
        self.assertNotEqual(row.get("captureTs"), row.get("ts"))
        self.assertEqual(row.get("capSrc"), "frame")

    def test_captureTs_falls_back_honestly_with_no_frame_id(self):
        # No frameId → can't derive a true captureTs, so it falls back to receipt time — but
        # capSrc must flag that honestly so retro readers know this row isn't frame-anchored.
        receipt_ts = 1_753_000_005_000
        self._post({"frameId": "", "tab": "runes", "counts": {"El": 9}, "ts": receipt_ts})
        rows = self._intake_rows()
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.get("captureTs"), receipt_ts)
        self.assertEqual(row.get("capSrc"), "receipt-fallback")


class TestFunnelSetWrapperMath(unittest.TestCase):
    """v937 SET wrapper: a whole-stash photo must never double-count on top of the live store. The
    JS snapshots prev counts, then for every key the intake REPORTED subtracts the PRIOR amount —
    and only for keys that were previously present. This mirrors that math in Python."""

    @staticmethod
    def _adjust_calls(prev, added):
        # mirror of: Object.keys(res.added).forEach(k => { was=prev[k]||0; if(was>0) ADJ(k,-was) })
        calls = []
        for k in added:                       # dict preserves insertion order like Object.keys
            was = prev.get(k, 0) or 0
            if was > 0:
                calls.append((k, -was))
        return calls

    def test_subtracts_only_prior_reported_keys(self):
        prev = {"El": 5}
        added = {"El": 7, "Ral": 2}           # El was already 5; Ral is brand new
        self.assertEqual(self._adjust_calls(prev, added), [("El", -5)])

    def test_no_prior_no_adjust(self):
        self.assertEqual(self._adjust_calls({}, {"El": 7, "Ral": 2}), [])

    def test_prior_key_not_reported_is_left_alone(self):
        # a rune already in the store but NOT in this photo's added set is never touched.
        self.assertEqual(self._adjust_calls({"Vex": 3}, {"El": 1}), [])


# ═════════════════════════════════════════════════════════════════════════════
# PART B — ~1400-ITEM DB SWEEP (recognition + OCR filter against the real DB)
# ═════════════════════════════════════════════════════════════════════════════
class TestDbSweep(unittest.TestCase):
    """The full item-DB gauntlet. Harvest guarded first (>=800), then KAI recognition, the OCR
    line filter, and name normalization are swept over every harvested name. Miss/drop lists are
    PRINTED — Konyo wants to SEE exactly what the vocab does not know."""

    def test_harvest_is_guarded(self):
        self.assertGreaterEqual(len(DB_NAMES), 800,
                                "DB harvest collapsed — only %d names" % len(DB_NAMES))

    def test_kai_recognition_pass_rate(self):
        misses = [n for n in DB_NAMES if not ca._kai_itemish(n)]
        rate = 100.0 * (len(DB_NAMES) - len(misses)) / len(DB_NAMES)
        print("\n[DB SWEEP] KAI recognition: %.2f%% (%d/%d) — %d misses"
              % (rate, len(DB_NAMES) - len(misses), len(DB_NAMES), len(misses)))
        for m in misses:
            print("   KAI-miss:", repr(m))
        self.assertGreaterEqual(rate, 97.0,
                                "KAI vocab recognition dropped below 97%%: %.2f%%" % rate)

    def test_ocr_filter_keep_rate(self):
        kept, dropped = 0, []
        for i in range(0, len(DB_NAMES), 10):
            chunk = DB_NAMES[i:i + 10]
            keptset = {o.lower() for o in tvd.filter_ocr_lines(chunk)}
            for c in chunk:
                if c.lower() in keptset:
                    kept += 1
                else:
                    dropped.append(c)
        rate = 100.0 * kept / len(DB_NAMES)
        print("\n[DB SWEEP] OCR filter keep: %.2f%% (%d/%d) — %d dropped"
              % (rate, kept, len(DB_NAMES), len(dropped)))
        for d in dropped:
            print("   OCR-dropped:", repr(d))
        self.assertGreaterEqual(rate, 95.0,
                                "OCR filter dropped >5%% of real item names: %.2f%%" % rate)

    def test_norm_name_never_empty(self):
        bad = [n for n in DB_NAMES if not tvd._norm_name(n)]
        for b in bad:
            print("   NORM-empty:", repr(b))
        self.assertEqual(bad, [], "_norm_name returned empty for real names")


# ═════════════════════════════════════════════════════════════════════════════
# PART C — FUNNEL JS DRY-RUN (extract the real template, syntax + return-0 path)
# ═════════════════════════════════════════════════════════════════════════════
class TestFunnelJsDryRun(unittest.TestCase):
    """Extract the funnel's injected JS template from control_app.py source, format it exactly like
    the code does, then (1) syntax-check via `new Function`, and (2) eval it under a stub document
    whose getElementById returns null — the IIFE must take its early return-0 path with no
    SyntaxError and no ReferenceError."""

    def _template(self):
        src = inspect.getsource(ca._kai_closer_loop)
        m = re.search(r"_js = \((.*?)\) % \(", src, re.DOTALL)
        self.assertIsNotNone(m, "could not locate the `_js = (` funnel template block")
        return eval("(" + m.group(1) + ")")   # concatenated string literals → the template

    def test_template_has_nine_placeholders(self):
        # v948.17 (Grok P0-1/P0-2) — was 6: added PREV (never-zero write guard) plus a
        # tab/frameId pair for the honest-error receipt in the outer .catch.
        self.assertEqual(self._template().count("%s"), 9)

    def test_node_dry_run_syntax_and_return_zero(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not on PATH")
        tmpl = self._template()
        import json as _j
        js = tmpl % (_j.dumps("runes"), _j.dumps("runes"), _j.dumps("runes"), _j.dumps(0),
                     _j.dumps("/hist/reel_x/f.jpg"), _j.dumps("runes"), _j.dumps("reel_x/f"),
                     _j.dumps("runes"), _j.dumps("reel_x/f"))
        jf = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False)
        jf.write(js)
        jf.close()
        try:
            p = ca.subprocess.run(
                [node, "-e",
                 "global.document={getElementById:()=>null};"
                 "const fs=require('fs');const js=fs.readFileSync(process.argv[1],'utf8');"
                 "new Function(js);"                       # pure syntax check
                 "const r=eval(js);"                       # run under the stub doc
                 "if(typeof r!=='number'){console.error('non-numeric return',r);process.exit(3);}"
                 "process.stdout.write(String(r));",
                 jf.name],
                capture_output=True, text=True, timeout=20)
        finally:
            os.unlink(jf.name)
        self.assertEqual(p.returncode, 0, "node dry-run failed: " + (p.stderr or "")[:300])
        self.assertEqual(p.stdout.strip(), "0", "funnel IIFE did not take the null-frame return-0 path")


# ═════════════════════════════════════════════════════════════════════════════
# PART D — v943 WAVE (register ledger · grail-gate split · engine self-heal · dossier)
# Pins the whole v943 arc so it can never silently regress. All pure-logic against the
# real ca._ functions (fullnames read the real bible.html); no live app, no journal writes.
# ═════════════════════════════════════════════════════════════════════════════
class TestV943Register(unittest.TestCase):
    """ca._kai_compile_register — the post-seal EVIDENCE ledger. Union of deep-read names +
    KAI judge verdicts (grail/keep/border), filtered to real DB items minus anchors/junk.
    One record per unique name, earliest sighting wins, tier from the judge if judged."""

    def test_ledger_keeps_db_items_drops_anchor_and_junk(self):
        sess = [
            {"lane": "deep", "ts": 1000, "frameId": "1_1000",
             "names": ["Windforce", "Horadric Cube"],
             "names_loc": {"Windforce": "stash", "Horadric Cube": "inventory"}},
            {"lane": "deep", "ts": 2000, "frameId": "2_2000",
             "names": ["Beast Noose", "665 Gold"],
             "names_loc": {"Beast Noose": "ground"}},
            {"lane": "kai", "ts": 1500, "frameId": "reel_s/f_1500",
             "kai": {"judge": {"name": "Windforce", "tier": "grail", "score": 9}}},
        ]
        reg = ca._kai_compile_register(sess)
        by = {r["name"]: r for r in reg}
        # exactly the unique + the rare survive; anchor (cube) + junk (gold) are gone
        self.assertEqual(set(by), {"Windforce", "Beast Noose"})
        # the unique: earliest sighting (the deep read at 1000) wins ts/frame/loc; tier from judge
        w = by["Windforce"]
        self.assertEqual((w["firstSeenTs"], w["frameId"], w["loc"], w["tier"]),
                         (1000, "1_1000", "stash", "grail"))
        # the rare: sighted only by the deep read, never judged → tier stays None
        r = by["Beast Noose"]
        self.assertEqual((r["firstSeenTs"], r["frameId"], r["loc"], r["tier"]),
                         (2000, "2_2000", "ground", None))

    def test_anchor_and_junk_filters_directly(self):
        self.assertTrue(ca._register_is_anchor("horadric cube"))
        self.assertTrue(ca._register_is_anchor("tome of town portal"))
        self.assertTrue(ca._register_is_junk("665 gold"))
        self.assertTrue(ca._register_is_junk("gold"))
        self.assertFalse(ca._register_is_anchor("windforce"))
        self.assertFalse(ca._register_is_junk("beast noose"))

    def test_only_grail_keep_border_judge_tiers_register(self):
        # a TOSS judge verdict (name not otherwise read) must NOT enter the ledger.
        sess = [{"lane": "kai", "ts": 10, "frameId": "reel_s/f_10",
                 "kai": {"judge": {"name": "Windforce", "tier": "toss", "score": 0}}}]
        self.assertEqual(ca._kai_compile_register(sess), [])


class TestV943GrailGate(unittest.TestCase):
    """The /kai_verdict GRAIL GATE split (v943.2): a name promotes toss/border → grail only if
    it's a known DB item AND NOT in the generated rare/crafted combo space. Replicates the exact
    route condition so the two consumers of _kai_fullnames stay correctly divergent.

    v948.19 — extended to replicate the RUNEWORD branch added to fix the 'Spirit' grail/toss
    split-brain (Grok forensic #6, 2026-07-21 21:05 fast run): a runeword name is real forged
    gear (never toss/border) but is NOT a grail item (grail = unique/set only).

    v1250 — RW check is FIRST and independent of fullnames membership, so glued-base reads
    ('Spirit Monarch') that are NOT in _kai_fullnames() still force keep (never grail/toss).
    _gate() mirrors control_app.py /kai_verdict exactly via _kai_is_runeword_name."""

    @staticmethod
    def _gate(name, tier):
        # Mirrors control_app.py /kai_verdict v1250 gate (pure decision, no journal).
        if name and ca._kai_is_runeword_name(name):
            if tier in ("toss", "border", "grail"):
                return "keep"
        elif (name and name.lower() in ca._kai_fullnames()
              and name.lower() not in ca._kai_rarenames()
              and tier in ("toss", "border")):
            return "grail"
        return tier

    def test_unique_promotes_to_grail(self):
        self.assertEqual(self._gate("Windforce", "toss"), "grail")
        self.assertEqual(self._gate("Hellfire Torch", "border"), "grail")

    def test_rare_combo_stays_tossable(self):
        self.assertEqual(self._gate("Beast Noose", "toss"), "toss")
        self.assertEqual(self._gate("Plague Wing", "border"), "border")

    def test_crafted_name_stays_tossable(self):
        self.assertEqual(self._gate("Bone Winding", "toss"), "toss")

    def test_non_toss_tier_is_never_touched(self):
        self.assertEqual(self._gate("Windforce", "keep"), "keep")

    def test_rarenames_is_subset_of_fullnames(self):
        self.assertTrue(ca._kai_rarenames() <= ca._kai_fullnames())

    def test_spirit_runeword_never_grail_never_toss(self):
        """THE BUG (Grok forensic #6): 'Spirit' journaled tier='grail' on the /kai_verdict
        server path (bare runeword name caught by the old broad fullnames-minus-rarenames
        gate) while bible.html's client-side aicJudgeApply applied 'toss' (score 0) — same
        read, two disagreeing verdicts. THE FIX: a runeword forces 'keep' on both toss AND
        border, on NEITHER path does it become 'grail' (grail tracking is unique/set only —
        runewords have their own 100-word Chronicle). This pin proves the server side; the
        mirrored client fix lives in bible.html aicJudgeApply (_rwResolve/findRuneword)."""
        self.assertEqual(self._gate("Spirit", "toss"), "keep")
        self.assertEqual(self._gate("Spirit", "border"), "keep")
        self.assertEqual(self._gate("Spirit", "keep"), "keep")  # untouched, already keep
        self.assertEqual(self._gate("Spirit", "grail"), "keep")  # demote false grail
        # a handful of other real runewords must never grail-promote either
        self.assertEqual(self._gate("Enigma", "toss"), "keep")
        self.assertEqual(self._gate("Insight", "border"), "keep")
        # true uniques/sets are UNCHANGED by the runeword branch — still grail-promote
        self.assertEqual(self._gate("Windforce", "toss"), "grail")

    def test_spirit_monarch_glued_base_is_keep_not_grail(self):
        """v1250 residual of forensic #6: live deep read 'Spirit Monarch' (RW + base glue).
        Not in _kai_fullnames() (only bare 'Spirit' is), so the v948.19 fullnames-gated
        branch skipped it entirely — left whatever the judge said (often toss) uncorrected.
        Gate must force keep for glued-base forms the same as bare Spirit."""
        self.assertFalse("spirit monarch" in ca._kai_fullnames())  # the trap
        self.assertTrue(ca._kai_is_runeword_name("Spirit Monarch"))
        self.assertEqual(self._gate("Spirit Monarch", "toss"), "keep")
        self.assertEqual(self._gate("Spirit Monarch", "grail"), "keep")
        self.assertEqual(self._gate("Insight Thresher", "border"), "keep")
        self.assertEqual(self._gate("Chains of Honor Dusk Shroud", "toss"), "keep")
        self.assertEqual(self._gate("Call to Arms Phase Blade", "grail"), "keep")
        # rare that starts with a RW first-token must NOT false-match
        self.assertFalse(ca._kai_is_runeword_name("Beast Noose"))
        self.assertEqual(self._gate("Beast Noose", "toss"), "toss")

    def test_reconcile_applied_matches_authoritative_tier(self):
        """v1250 — journal applied must not lag a server tier upgrade (Theatre KEEP→toss)."""
        self.assertEqual(ca._kai_reconcile_applied("keep", "toss"), "keep")
        self.assertEqual(ca._kai_reconcile_applied("keep", "border"), "keep")
        self.assertEqual(ca._kai_reconcile_applied("grail", "toss"), "grail")
        self.assertEqual(ca._kai_reconcile_applied("grail", "keep"), "grail")
        self.assertEqual(ca._kai_reconcile_applied("keep", "keep"), "keep")
        self.assertEqual(ca._kai_reconcile_applied("toss", "toss"), "toss")  # no upgrade
        self.assertEqual(ca._kai_reconcile_applied("keep", ""), "")  # no applied → leave empty

    def test_register_canonicalizes_glued_runeword_names(self):
        """v1250 — deep 'Spirit Monarch' must enter the register as bare 'Spirit' (keep),
        not be dropped because the glued form isn't in _kai_fullnames()."""
        rows = [
            {"lane": "deep", "ts": 10, "frameId": "2_10", "sessionId": "s",
             "names": ["Spirit Monarch"], "names_new": ["Spirit Monarch"],
             "scene": "stash", "stashTab": "personal"},
            {"lane": "kai", "mode": "kai-judge", "ts": 11, "frameId": "2_10",
             "kai": {"judge": {"name": "Spirit Monarch", "tier": "keep", "score": 0}}},
        ]
        reg = ca._kai_compile_register(rows)
        names = {r["name"].lower(): r for r in reg}
        self.assertIn("spirit", names)
        self.assertEqual(names["spirit"]["tier"], "keep")
        # glued form itself must not appear as a second register row
        self.assertNotIn("spirit monarch", names)

    def test_runewordnames_is_subset_of_fullnames_and_disjoint_from_rarenames(self):
        rw = ca._kai_runewordnames()
        self.assertTrue(rw <= ca._kai_fullnames())
        self.assertTrue(len(rw) >= 90)   # ~100-runeword Chronicle
        self.assertIn("spirit", rw)
        self.assertIn("enigma", rw)
        self.assertFalse(rw & ca._kai_rarenames())


class TestV943EngineSelfHeal(unittest.TestCase):
    """ca._engine_selfheal(alive, w) — consecutive dead-probe streak → iframe revive → hard-dead.
    Pure counter logic driven with w=None (skips the JS kick). Globals reset each test."""

    _G = ("_ENG_FAILS", "_ENG_REVIVES", "_ENGINE_DEAD_HARD", "_EJS_STUCK")

    def setUp(self):
        for k in self._G:
            ca.__dict__.pop(k, None)

    def tearDown(self):
        for k in self._G:
            ca.__dict__.pop(k, None)

    @staticmethod
    def _dead():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ca._engine_selfheal(False, None)
        return buf.getvalue().strip()

    @staticmethod
    def _live():
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ca._engine_selfheal(True, None)
        return buf.getvalue().strip()

    def test_no_revive_before_threshold(self):
        for _ in range(ca._ENGINE_REVIVE_AT - 1):
            self.assertEqual(self._dead(), "")
        self.assertEqual(ca._ENG_FAILS, ca._ENGINE_REVIVE_AT - 1)
        self.assertIsNone(ca.__dict__.get("_ENG_REVIVES"))

    def test_revive_at_threshold_then_halfway_reset(self):
        for _ in range(ca._ENGINE_REVIVE_AT - 1):
            self._dead()
        self.assertEqual(self._dead(), "🔌 engine revive attempted")
        self.assertEqual(ca._ENG_REVIVES, 1)
        self.assertEqual(ca._ENG_FAILS, ca._ENGINE_REVIVE_AT // 2)   # half-way settle

    def test_live_probe_resets_streak(self):
        for _ in range(3):
            self._dead()
        self._live()
        self.assertEqual(ca._ENG_FAILS, 0)

    def test_caps_at_max_revives_then_hard_dead_once(self):
        revive_msgs = dead_msgs = 0
        # plenty of dead probes to burn through every revive and reach hard-dead
        for _ in range(ca._ENGINE_REVIVE_AT * (ca._ENGINE_REVIVE_MAX + 2)):
            out = self._dead()
            revive_msgs += (out == "🔌 engine revive attempted")
            dead_msgs += (out == "🔌 engine DEAD — restart the app")
        self.assertEqual(revive_msgs, ca._ENGINE_REVIVE_MAX)
        self.assertEqual(dead_msgs, 1)                              # shouted exactly once
        self.assertEqual(ca._ENG_REVIVES, ca._ENGINE_REVIVE_MAX)   # capped
        self.assertTrue(ca._ENGINE_DEAD_HARD)
        # further dead probes stay silent (no repeat shout)
        self.assertEqual("".join(self._dead() for _ in range(10)), "")


class TestV943Dossier(unittest.TestCase):
    """ca._build_dossier_maps + ca._beat_dossier — the three-eye join. A read beat (frameId
    'N_ts') joins its verify row (base '#v' stripped) + the tally receipt for its stashTab; a
    footage beat (frameId 'reel_<sid>/f_<ms>') joins its KAI frame class."""

    def setUp(self):
        self.sess = [
            {"lane": "deep", "ts": 500, "captureTs": 500, "frameId": "2_500",
             "stashTab": "runes", "names": ["El"]},
            {"lane": "verify", "ts": 600, "frameId": "2_500#v",
             "verify": {"confirm": ["El"], "missed": [], "not_present": [], "conf": 0.9}},
            {"lane": "intake", "ts": 520,
             "intake": {"tab": "runes", "kind": "tally", "ok": True, "total": 3,
                        "counts": {"El": 2, "Eld": 1}}},
            {"lane": "kai", "ts": 700, "frameId": "reel_s/f_700",
             "kai": {"cls": "stash-runes", "texts": ["Runes"]}},
        ]
        self.maps = ca._build_dossier_maps(self.sess)

    def test_read_beat_joins_verify_and_tally(self):
        d = ca._beat_dossier(self.maps,
                             {"frameId": "2_500", "captureTs": 500, "stashTab": "runes", "lane": "deep"})
        # 🔵 verify by frameId base (strip '#v') — v947.2 enriched with *which* names (not just counts)
        v = d["verify"]
        self.assertEqual(v["conf"], 0.9)
        self.assertEqual((v["confirm"], v["corrected"], v["missed"]), (1, 0, 0))
        self.assertEqual(v["confirmNames"], ["El"])      # the enrichment: name lists, not bare counts
        self.assertEqual(v["missedNames"], [])
        self.assertEqual(v["correctedNames"], [])
        # 📸 tally by tab, counts top-pairs largest first
        self.assertEqual(d["tally"]["tab"], "runes")
        self.assertEqual(d["tally"]["total"], 3)
        self.assertTrue(d["tally"]["ok"])
        self.assertEqual(d["tally"]["counts"], [["El", 2], ["Eld", 1]])
        # a read frameId never matches a reel KAI key
        self.assertIsNone(d["kai"])

    def test_footage_beat_joins_kai_class(self):
        d = ca._beat_dossier(self.maps,
                             {"frameId": "reel_s/f_700", "captureTs": 700, "footage": True})
        self.assertIsNotNone(d["kai"])
        self.assertEqual(d["kai"]["cls"], "stash-runes")
        # footage carries no read frameId → no verify join
        self.assertIsNone(d["verify"])

    def test_maps_shapes(self):
        self.assertIn("2_500", self.maps["verify"])            # verify keyed by stripped base
        self.assertIn("reel_s/f_700", self.maps["kai"])        # kai keyed by exact reel frameId
        self.assertEqual(self.maps["tab_ts"]["runes"], [520])  # receipts bucketed + sorted per tab

    # ── v944.5 — NEVER-ZERO: a 0/error shot never wins over a real read of the same tab ──
    def test_zero_read_superseded_by_real_count(self):
        # Konyo's rule: "I don't want anything read 0 — read it according to the updated picture."
        # A runes session with a real 404 read AND a later errored 0 shot: the frame nearest the 0
        # must STILL report the real 404 (superseded), never a MISS.
        sess = [
            {"lane": "intake", "ts": 1000,
             "intake": {"tab": "runes", "kind": "tally", "ok": True, "total": 404,
                        "counts": {"El": 200, "Eld": 204}}},
            {"lane": "intake", "ts": 5000,   # a later errored shot on the SAME tab
             "intake": {"tab": "runes", "kind": "tally", "ok": False, "total": 0, "counts": {}}},
        ]
        maps = ca._build_dossier_maps(sess)
        self.assertEqual(int(maps["tab_best"]["runes"]["total"]), 404)   # best receipt = the real read
        # a footage frame sitting right on the errored 0-shot moment:
        d = ca._beat_dossier(maps, {"frameId": "reel_s/f_5000", "captureTs": 5000,
                                    "footage": True, "label": "stash-runes"})
        rs = d["readStatus"]
        self.assertEqual(rs["kind"], "read")        # NOT 'miss'
        self.assertEqual(rs["counted"], 404)        # the updated/real picture, never 0
        self.assertTrue(rs["superseded"])           # flagged: the nearby 0 was overridden
        self.assertEqual(int(d["tally"]["total"]), 404)   # tally itself supersedes to the real one

    def test_true_miss_still_reports_miss(self):
        # a stash tab the router labeled but that NEVER got a real read anywhere = an honest miss.
        sess = [{"lane": "intake", "ts": 5000,
                 "intake": {"tab": "gems", "kind": "tally", "ok": False, "total": 0, "counts": {}}}]
        maps = ca._build_dossier_maps(sess)
        self.assertNotIn("gems", maps["tab_best"])
        d = ca._beat_dossier(maps, {"frameId": "reel_s/f_5000", "captureTs": 5000,
                                    "footage": True, "label": "stash-gems"})
        self.assertEqual(d["readStatus"]["kind"], "miss")
        self.assertEqual(d["readStatus"]["counted"], 0)


class TestNeverZeroRefire(unittest.TestCase):
    """v944.6 — empty/error intake is a failure signal: driver re-fires the freshest frame
    for that tab (up to 3 tries). Pure helpers pin the decision so the theatre never settles
    on a 0 as the final answer when a re-read is still possible."""

    def test_intake_is_real(self):
        self.assertTrue(ca._intake_is_real({"ok": True, "total": 404}))
        self.assertFalse(ca._intake_is_real({"ok": True, "total": 0}))
        self.assertFalse(ca._intake_is_real({"ok": False, "total": 0}))
        self.assertFalse(ca._intake_is_real({"ok": False, "total": 12}))
        self.assertFalse(ca._intake_is_real(None))
        self.assertFalse(ca._intake_is_real({}))

    def test_freshest_tab_fid_picks_newest(self):
        reads = [
            {"lane": "deep", "scene": "stash", "stashTab": "runes", "ts": 1000, "frameId": "1_1000"},
            {"lane": "deep", "scene": "stash", "stashTab": "runes", "ts": 5000, "frameId": "9_5000"},
            {"lane": "deep", "scene": "stash", "stashTab": "gems", "ts": 9000, "frameId": "g_9000"},
        ]
        self.assertEqual(ca._drv_freshest_tab_fid("runes", reads=reads, fallback="old"), "9_5000")
        self.assertEqual(ca._drv_freshest_tab_fid("gems", reads=reads), "g_9000")
        self.assertEqual(ca._drv_freshest_tab_fid("materials", reads=reads, fallback="fb"), "fb")

    def test_empty_refire_plan_tally(self):
        job = {"key": "runes", "tab": "runes", "fid": "1_1000", "tries": 0, "fired_ms": 1}
        act, nxt = ca._drv_empty_refire_plan(job, {"ok": False, "total": 0}, "9_5000")
        self.assertEqual(act, "refire")
        self.assertEqual(nxt["fid"], "9_5000")
        self.assertEqual(nxt["tries"], 1)
        # real count → done
        act2, _ = ca._drv_empty_refire_plan(job, {"ok": True, "total": 404}, "9_5000")
        self.assertEqual(act2, "done")
        # third empty → giveup
        job3 = dict(job); job3["tries"] = 2
        act3, _ = ca._drv_empty_refire_plan(job3, {"ok": True, "total": 0}, "9_5000")
        self.assertEqual(act3, "giveup")

    def test_vault_empty_is_done_not_refire(self):
        # vault personal/shared can legitimately total 0 (empty tab) — an OK read of an empty
        # tab is DONE, never re-fired (re-firing an empty tab would loop forever).
        job = {"key": "vault_personal", "tab": "personal", "fid": "v1", "tries": 0}
        act, _ = ca._drv_empty_refire_plan(job, {"ok": True, "total": 0}, "v2")
        self.assertEqual(act, "done")

    def test_vault_error_refires(self):
        # v946.3 — vault ERROR with tooltip names re-fires. v946.7 — grid (no names) gives up.
        job = {"key": "vault_shared", "tab": "shared", "fid": "v1", "tries": 0, "has_names": True}
        act, nxt = ca._drv_empty_refire_plan(job, {"ok": False, "total": 0}, "v9")
        self.assertEqual(act, "refire")
        self.assertEqual(nxt["fid"], "v9")           # re-reads the freshest frame
        # exhausts to giveup, never loops forever
        job3 = {"key": "vault_shared", "tab": "shared", "fid": "v1", "tries": 2, "has_names": True}
        act3, _ = ca._drv_empty_refire_plan(job3, {"ok": False, "total": 0}, "v9")
        self.assertEqual(act3, "giveup")
        # grid error: no thrash
        job_g = {"key": "vault_personal", "tab": "personal", "fid": "g1", "tries": 0, "has_names": False}
        self.assertEqual(ca._drv_empty_refire_plan(job_g, {"ok": False, "total": 0}, "g2")[0], "giveup")


class TestRouterLedger(unittest.TestCase):
    """v944 🚦 THE KAI ROUTER — Stage 1 label table. ca._kai_route_for_label maps a label to the
    funnel that WOULD take it; ca._kai_build_routing derives per-frame {sources, confidence, route,
    routed, skipReason} from the scan + session rows + journal. Pure — no firing, no I/O."""

    def test_route_for_label(self):
        self.assertEqual(ca._kai_route_for_label("stash-runes"), "tally:runes")
        self.assertEqual(ca._kai_route_for_label("stash-gems"), "tally:gems")
        self.assertEqual(ca._kai_route_for_label("stash-materials"), "tally:materials")
        self.assertEqual(ca._kai_route_for_label("tooltip"), "judge")
        self.assertEqual(ca._kai_route_for_label("stash"), "vault")
        self.assertEqual(ca._kai_route_for_label("inventory"), "vault")
        self.assertIsNone(ca._kai_route_for_label("gameplay"))
        self.assertIsNone(ca._kai_route_for_label(None))

    def setUp(self):
        # v944.1 — each brain carries its own vote (ocrLabel/journalLabel). Legacy rows
        # with only ocr/journal booleans + label still work via the builder fallback.
        self.scan = [
            {"f": "f_100.jpg", "ts": 100000, "ocr": True,  "ocrLabel": "stash-runes",
             "journal": True,  "journalLabel": "stash-runes", "label": "stash-runes"},
            {"f": "f_200.jpg", "ts": 200000, "ocr": True,  "ocrLabel": "tooltip",
             "journal": False, "label": "tooltip"},
            {"f": "f_300.jpg", "ts": 300000, "ocr": False, "journal": False, "label": "gameplay"},
            {"f": "f_400.jpg", "ts": 400000, "ocr": True,  "ocrLabel": "stash-gems",
             "journal": False, "label": "stash-gems"},
            {"f": "f_500.jpg", "ts": 500000, "ocr": True,  "ocrLabel": "stash-materials",
             "journal": True,  "journalLabel": "stash-materials", "label": "stash-materials"},
            {"f": "f_600.jpg", "ts": 600000, "ocr": True,  "ocrLabel": "inventory",
             "journal": True,  "journalLabel": "inventory", "label": "inventory"},
        ]
        self.sess = [
            {"lane": "deep", "ts": 100000, "names": ["El"]},                        # named read → 'read' near 100k
            {"lane": "intake", "frameId": "reel_S/f_100",
             "intake": {"tab": "runes", "ok": True, "kind": "kai-funnel", "total": 12}},  # funnel fired on f_100
            {"lane": "intake", "frameId": "",
             "intake": {"tab": "materials", "ok": True, "kind": "tally", "total": 7}},    # materials receipted (real)
        ]
        self.journal = self.sess + [
            {"lane": "kai", "mode": "kai-judge", "frameId": "reel_S/f_200",
             "kai": {"judge": {"name": "Windforce", "tier": "toss"}}},              # judge verdict on f_200
        ]
        self.led = {r["f"]: r for r in ca._kai_build_routing(self.scan, self.sess, "S", self.journal)}

    def test_funnel_routed_frame(self):
        # v944.1 — a near named deep-read votes 'tooltip', not stash-runes. Honest quorum:
        # only journal+ocr agree on stash-runes (conf 2). 'read' does NOT inflate stash quorum.
        r = self.led["f_100.jpg"]
        self.assertEqual(sorted(r["sources"]), ["journal", "ocr"])
        self.assertEqual(r["confidence"], 2)
        self.assertEqual(r["route"], "tally:runes")
        self.assertEqual(r["routed"], "kai-funnel")
        self.assertIsNone(r["skipReason"])

    def test_judge_routed_frame(self):
        r = self.led["f_200.jpg"]
        self.assertEqual(sorted(r["sources"]), ["judge", "ocr"])            # both vote tooltip
        self.assertEqual(r["route"], "judge")
        self.assertEqual(r["routed"], "kai-judge")
        self.assertIsNone(r["skipReason"])

    def test_low_confidence_and_no_route_skips(self):
        # gameplay: no sources, no route → confidence<2 (checked before no-route)
        g = self.led["f_300.jpg"]
        self.assertEqual((g["confidence"], g["route"], g["routed"], g["skipReason"]),
                         (0, None, None, "confidence<2"))
        # single-source stash-gems → confidence<2 even though a route exists
        gm = self.led["f_400.jpg"]
        self.assertEqual((gm["confidence"], gm["route"], gm["skipReason"]),
                         (1, "tally:gems", "confidence<2"))

    def test_quorum_but_no_gap_and_vault_skips(self):
        # materials had a normal receipt → a 2-source materials frame is 'no-gap'
        m = self.led["f_500.jpg"]
        self.assertEqual((m["confidence"], m["route"], m["routed"], m["skipReason"]),
                         (2, "tally:materials", None, "no-gap"))
        # inventory routes to vault — v946 fireable (not-selected) for Stage 3 vault lane
        v = self.led["f_600.jpg"]
        self.assertEqual((v["route"], v["routed"], v["skipReason"]),
                         ("vault", None, "not-selected"))

    def test_routed_count_and_shape(self):
        led = ca._kai_build_routing(self.scan, self.sess, "S", self.journal)
        self.assertEqual(len(led), 6)
        self.assertEqual(sum(1 for r in led if r["routed"]), 2)             # f_100 + f_200 fired
        # every row carries the full contract, no missing keys (v949 adds the gate fields)
        for r in led:
            self.assertEqual(set(r), {"f", "ts", "label", "sources", "confidence",
                                      "voteCount", "route", "routed", "skipReason",
                                      "gatePass", "gateReason", "gateSources"})

    def test_dedupe_run_routing_only_film_intact(self):
        # a visual run of 3 identical-sig frames: FIRST routable, next 2 dup-chained — but ALL
        # 3 stay in the ledger (dedupe is routing-only; the film/replay is never trimmed).
        sig = (4096, b"IDENTICAL-FRAME-BYTES")
        scan = [
            {"f": "f_1.jpg", "ts": 1000, "ocr": True, "journal": True, "label": "stash-runes", "sig": sig},
            {"f": "f_2.jpg", "ts": 1100, "ocr": True, "journal": True, "label": "stash-runes", "sig": sig},
            {"f": "f_3.jpg", "ts": 1200, "ocr": True, "journal": True, "label": "stash-runes", "sig": sig},
        ]
        led = ca._kai_build_routing(scan, [], "S", [])
        self.assertEqual([r["f"] for r in led], ["f_1.jpg", "f_2.jpg", "f_3.jpg"])   # all 3 present
        # first frame keeps its label + route (the one routable head of the run)
        self.assertEqual(led[0]["route"], "tally:runes")
        self.assertNotEqual(led[0]["skipReason"], "dup-of:f_1.jpg")
        # both duplicates: label unchanged, route/routed nulled, chained to the run head
        for dup in led[1:]:
            self.assertEqual(dup["label"], "stash-runes")     # label unchanged
            self.assertIsNone(dup["route"])
            self.assertIsNone(dup["routed"])
            self.assertEqual(dup["skipReason"], "dup-of:f_1.jpg")
        # exactly 1 routable + 2 dup-chained
        self.assertEqual(sum(1 for r in led if r["route"]), 1)
        self.assertEqual(sum(1 for r in led if str(r["skipReason"] or "").startswith("dup-of:")), 2)

    def test_sig_change_breaks_the_run(self):
        # a differing sig starts a fresh run — not chained to the prior frame.
        # ts of c is >3s past a so label+time near-dup does not also collapse it.
        scan = [
            {"f": "a.jpg", "ts": 1000, "ocr": True, "journal": True, "label": "stash",
             "ocrLabel": "stash", "journalLabel": "stash", "sig": (1, b"A")},
            {"f": "b.jpg", "ts": 1100, "ocr": True, "journal": True, "label": "stash",
             "ocrLabel": "stash", "journalLabel": "stash", "sig": (1, b"A")},
            {"f": "c.jpg", "ts": 5000, "ocr": True, "journal": True, "label": "stash",
             "ocrLabel": "stash", "journalLabel": "stash", "sig": (2, b"B")},
        ]
        led = ca._kai_build_routing(scan, [], "S", [])
        self.assertEqual(led[1]["skipReason"], "dup-of:a.jpg")   # b is a dup of a
        self.assertNotIn("dup-of", str(led[2]["skipReason"]))    # c starts a new run
        self.assertNotIn("near-dup", str(led[2]["skipReason"] or ""))
        self.assertEqual(led[2]["route"], "vault")               # c keeps its route

    def test_label_time_near_dup_collapses_routing(self):
        # v944.6 — different JPEG sigs (cursor/glow) but same label within 3s = one logical event.
        # Film keeps all frames; only the cluster head stays routable.
        scan = [
            {"f": "r1.jpg", "ts": 10000, "ocr": True, "journal": True, "label": "stash-runes",
             "ocrLabel": "stash-runes", "journalLabel": "stash-runes", "sig": (1, b"A")},
            {"f": "r2.jpg", "ts": 11500, "ocr": True, "journal": True, "label": "stash-runes",
             "ocrLabel": "stash-runes", "journalLabel": "stash-runes", "sig": (2, b"B")},  # different sig
            {"f": "r3.jpg", "ts": 12500, "ocr": True, "journal": True, "label": "stash-runes",
             "ocrLabel": "stash-runes", "journalLabel": "stash-runes", "sig": (3, b"C")},
            # outside the 3s window → fresh cluster head
            {"f": "r4.jpg", "ts": 16000, "ocr": True, "journal": True, "label": "stash-runes",
             "ocrLabel": "stash-runes", "journalLabel": "stash-runes", "sig": (4, b"D")},
        ]
        led = ca._kai_build_routing(scan, [], "S", [])
        self.assertEqual(len(led), 4)                            # film never trimmed
        self.assertEqual(led[0]["route"], "tally:runes")
        self.assertEqual(led[1]["skipReason"], "near-dup-of:r1.jpg")
        self.assertIsNone(led[1]["route"])
        self.assertEqual(led[2]["skipReason"], "near-dup-of:r1.jpg")
        self.assertEqual(led[3]["route"], "tally:runes")         # new head after window
        self.assertFalse(str(led[3].get("skipReason") or "").startswith("near-dup"))
        # actual funnel receipt on a near-dup frame is preserved (not erased by near-dup)
        j = [{"lane": "intake", "frameId": "reel_S/r2",
              "intake": {"tab": "runes", "ok": True, "kind": "kai-funnel", "total": 10}}]
        led2 = ca._kai_build_routing(scan, [], "S", j)
        self.assertEqual(led2[1]["routed"], "kai-funnel")

    # ── v944.1 Stage 2 — QUORUM + DISAGREEMENT POLICY ─────────────────────────
    def test_journal_panel_wins_over_ocr_tooltip(self):
        # stash screens are OCR-dark: journal time-map overrides a conflicting OCR tooltip.
        # Both brains vote → journal wins label; only journal agrees with the final label?
        # Actually ocr voted tooltip, journal voted stash-runes → final stash-runes, sources=[journal]
        # confidence 1 → confidence<2 (no fire). That's correct: OCR did NOT agree.
        scan = [{"f": "x.jpg", "ts": 1000, "ocr": True, "ocrLabel": "tooltip",
                 "journal": True, "journalLabel": "stash-runes", "label": "stash-runes"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertEqual(r["label"], "stash-runes")
        self.assertEqual(r["sources"], ["journal"])
        self.assertEqual(r["confidence"], 1)
        self.assertEqual(r["skipReason"], "confidence<2")

    def test_disagreement_two_brains_no_winner(self):
        # ocr says tooltip, read says tooltip → agreement on tooltip with 2 sources.
        # Force true disagreement: ocr=tooltip vs journal=inventory (no stash-* priority path)
        # wait — journal inventory is still journal priority only for stash-*. inventory loses to majority.
        # ocr=tooltip, journal=inventory → two distinct, each 1 vote → disagreement
        scan = [{"f": "d.jpg", "ts": 2000, "ocr": True, "ocrLabel": "tooltip",
                 "journal": True, "journalLabel": "inventory", "label": "tooltip"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertEqual(r["skipReason"], "disagreement")
        self.assertIsNone(r["route"])
        self.assertEqual(r["confidence"], 0)
        self.assertEqual(r["sources"], [])

    def test_quorum_two_agree_routes(self):
        # ocr + journal both stash-gems → confidence 2, route tally:gems
        scan = [{"f": "g.jpg", "ts": 3000, "ocr": True, "ocrLabel": "stash-gems",
                 "journal": True, "journalLabel": "stash-gems", "label": "stash-gems"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertEqual(sorted(r["sources"]), ["journal", "ocr"])
        self.assertEqual(r["confidence"], 2)
        self.assertEqual(r["route"], "tally:gems")
        self.assertEqual(r["skipReason"], "not-selected")  # no receipt, no fire yet

    # ── v944.2 Stage 2 hardening — SOURCE INDEPENDENCE ────────────────────────
    def test_read_and_judge_are_one_content_class(self):
        # a tooltip that a deep read NAMED and a judge then VERDICTED is ONE tooltip
        # witnessed twice — NOT two independent brains. With no pixel/time brain on it,
        # confidence must be 1 (content), not 2, so it does NOT clear the quorum gate
        # on its own. voteCount stays honest at 2 (both brains did vote).
        scan = [{"f": "t.jpg", "ts": 5000, "ocr": False, "journal": False, "label": "tooltip"}]
        sess = [{"lane": "deep", "ts": 5000, "names": ["Windforce"]}]           # read → 'read'
        journal = sess + [{"lane": "kai", "mode": "kai-judge", "frameId": "reel_S/f_t",
                           "kai": {"judge": {"name": "Windforce"}}}]
        # frameId must match reel_S/f_t → but our f is 't.jpg'; judge keys on reel_S/t
        journal[-1]["frameId"] = "reel_S/t"
        r = ca._kai_build_routing(scan, sess, "S", journal)[0]
        self.assertEqual(sorted(r["sources"]), ["judge", "read"])
        self.assertEqual(r["voteCount"], 2)          # both voted (honest)
        self.assertEqual(r["confidence"], 1)         # but ONE independent class (content)
        self.assertEqual(r["routed"], "kai-judge")   # judge already fired → routed
        self.assertIsNone(r["skipReason"])           # routed frame is not gated
        # the independent-class helper itself
        self.assertEqual(ca._router_conf(["read", "judge"]), 1)          # same class collapses
        self.assertEqual(ca._router_conf(["ocr", "read"]), 2)            # pixel + content
        self.assertEqual(ca._router_conf(["ocr", "journal", "read"]), 3)  # all distinct

    def test_content_needs_independent_brain_to_route(self):
        # a tooltip read-only (no judge, no ocr, no journal) is content=1 → gated confidence<2,
        # exactly as a single stash brain is. It routes only when a pixel/time brain corroborates.
        scan = [{"f": "u.jpg", "ts": 6000, "ocr": False, "journal": False, "label": "tooltip"}]
        sess = [{"lane": "deep", "ts": 6000, "names": ["El"]}]
        r = ca._kai_build_routing(scan, sess, "S", sess)[0]
        self.assertEqual(r["sources"], ["read"])
        self.assertEqual(r["confidence"], 1)
        self.assertEqual(r["skipReason"], "confidence<2")

    def test_quorum_label_helper(self):
        # pure helper pins
        lb, src, d = ca._kai_quorum_label({"ocr": "tooltip", "journal": "stash-runes"})
        self.assertEqual((lb, src, d), ("stash-runes", ["journal"], None))
        lb, src, d = ca._kai_quorum_label({"ocr": "tooltip", "read": "tooltip"})
        self.assertEqual(lb, "tooltip")
        self.assertEqual(sorted(src), ["ocr", "read"])
        self.assertIsNone(d)
        lb, src, d = ca._kai_quorum_label({"ocr": "tooltip", "journal": "inventory"})
        self.assertEqual(d, "disagreement")
        self.assertEqual(src, [])

    # ── v944.6 Stage 3 — lanes OBEY the ledger ────────────────────────────────
    def test_stage3_select_funnel_and_judge(self):
        # fireable: conf≥2 + route + skip not-selected|cap; one funnel job per tab (newest);
        # vault / conf<2 / already-routed / disagreement NEVER selected.
        routing = [
            {"f": "r_old.jpg", "ts": 1000, "label": "stash-runes", "confidence": 2,
             "route": "tally:runes", "routed": None, "skipReason": "not-selected"},
            {"f": "r_new.jpg", "ts": 2000, "label": "stash-runes", "confidence": 2,
             "route": "tally:runes", "routed": None, "skipReason": "not-selected"},
            {"f": "g1.jpg", "ts": 1500, "label": "stash-gems", "confidence": 2,
             "route": "tally:gems", "routed": None, "skipReason": "not-selected"},
            {"f": "g_done.jpg", "ts": 1600, "label": "stash-gems", "confidence": 2,
             "route": "tally:gems", "routed": "kai-funnel", "skipReason": None},  # already fired
            {"f": "low.jpg", "ts": 1700, "label": "stash-materials", "confidence": 1,
             "route": "tally:materials", "routed": None, "skipReason": "confidence<2"},
            {"f": "tip1.jpg", "ts": 3000, "label": "tooltip", "confidence": 2,
             "route": "judge", "routed": None, "skipReason": "cap"},
            {"f": "tip0.jpg", "ts": 2500, "label": "tooltip", "confidence": 2,
             "route": "judge", "routed": None, "skipReason": "cap"},
            {"f": "inv.jpg", "ts": 4000, "label": "inventory", "confidence": 2,
             "route": "vault", "routed": None, "skipReason": "no-vault-fire"},
            {"f": "fight.jpg", "ts": 5000, "label": "tooltip", "confidence": 0,
             "route": None, "routed": None, "skipReason": "disagreement"},
        ]
        funnel, judge, vault = ca._kai_stage3_select(routing)
        tabs = {j["tab"]: j for j in funnel}
        self.assertEqual(set(tabs), {"runes", "gems"})          # materials gated conf<2
        self.assertEqual(tabs["runes"]["f"], "r_new.jpg")       # newest runes frame
        self.assertEqual(tabs["gems"]["f"], "g1.jpg")           # g_done already routed → skipped
        self.assertEqual([j["f"] for j in judge], ["tip0.jpg", "tip1.jpg"])  # ts order
        # vault fireable (v946) · disagreement never appears
        self.assertEqual(len(vault), 1)
        self.assertEqual(vault[0]["f"], "inv.jpg")
        self.assertTrue(all(j["f"] != "fight.jpg" for j in judge))

    def test_stage3_empty_when_no_fireable(self):
        funnel, judge, vault = ca._kai_stage3_select([
            {"f": "a.jpg", "ts": 1, "confidence": 1, "route": "tally:runes",
             "routed": None, "skipReason": "confidence<2"},
            {"f": "b.jpg", "ts": 2, "confidence": 1, "route": "vault",
             "routed": None, "skipReason": "confidence<2"},
        ])
        self.assertEqual(funnel, [])
        self.assertEqual(judge, [])
        self.assertEqual(vault, [])

    def test_stage3_receipt_writes_routed_back(self):
        # after a funnel receipt lands, the rebuilt ledger marks that frame routed=kai-funnel
        # and drops it from Stage 3 re-selection (loop closed).
        scan = [{"f": "r.jpg", "ts": 9000, "ocr": True, "ocrLabel": "stash-runes",
                 "journal": True, "journalLabel": "stash-runes", "label": "stash-runes"}]
        pre = ca._kai_build_routing(scan, [], "S", [])
        self.assertEqual(pre[0]["skipReason"], "not-selected")
        f0, j0, v0 = ca._kai_stage3_select(pre)
        self.assertEqual(len(f0), 1)
        self.assertEqual(f0[0]["tab"], "runes")
        journal = [{"lane": "intake", "frameId": "reel_S/r",
                    "intake": {"tab": "runes", "ok": True, "kind": "kai-funnel", "total": 44}}]
        post = ca._kai_build_routing(scan, [], "S", journal)
        self.assertEqual(post[0]["routed"], "kai-funnel")
        self.assertIsNone(post[0]["skipReason"])
        f1, j1, v1 = ca._kai_stage3_select(post)
        self.assertEqual(f1, [])   # already routed → not re-selected


class TestAccuracyGate(unittest.TestCase):
    """v949 🚦🛡 THE ACCURACY GATE (§3.5, ENGINE_ARCHITECTURE.md) — the ping-pong verification
    mesh between the router (_kai_build_routing) and the funnels (Stage 3). ca._kai_gate_check
    is the pure three-check decision; ca._kai_gate_pingpong is the bounded re-read/honest-miss
    contract; ca._kai_gate_name_hit is the hardcoded ~1400-item DB name check."""

    # ── check 1: hardcoded filter ─────────────────────────────────────────────
    def test_filter_rejects_journal_only_tally_label(self):
        # journal (time-map) ALONE never clears the tally hard-signal — this is the exact
        # class that produced the vault-0 / materials false-positive bugs.
        g = ca._kai_gate_check("stash-materials", ["journal"], 2, "tally:materials")
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "no-hard-signal")

    def test_filter_passes_with_ocr_or_grid_or_tabstrip(self):
        for src in (["journal", "ocr"], ["journal", "grid"], ["journal", "tabstrip"]):
            g = ca._kai_gate_check("stash-runes", src, 2, "tally:runes")
            self.assertTrue(g["pass"], src)

    def test_filter_rejects_garbage_ocr_tooltip_no_db_name(self):
        # "IA Lla" / "Ii" style garble matches no name in the ~1400-item DB → dies here,
        # zero AI cost, even though sources otherwise look fine.
        g = ca._kai_gate_check("tooltip", ["ocr", "read"], 2, "judge", name_hit=False)
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "name-not-in-db")

    def test_filter_tooltip_no_name_evidence_is_fail_open(self):
        # no name evidence supplied at all (name_hit=None) — the gate can't assert anything
        # about the DB match, so it doesn't invent a false rejection.
        g = ca._kai_gate_check("tooltip", ["ocr", "read"], 2, "judge", name_hit=None)
        self.assertTrue(g["pass"])

    def test_gate_name_hit_real_vs_garbage(self):
        fn = {"windforce", "hellfire torch"}
        self.assertTrue(ca._kai_gate_name_hit(["Windforce"], fullnames=fn))
        self.assertTrue(ca._kai_gate_name_hit(["ia lla", "Hellfire Torch"], fullnames=fn))
        self.assertFalse(ca._kai_gate_name_hit(["IA Lla", "Ii"], fullnames=fn))
        self.assertFalse(ca._kai_gate_name_hit([], fullnames=fn))

    # ── check 2: brain quorum (build on the router, don't duplicate) ───────────
    def test_quorum_needs_at_least_two(self):
        g = ca._kai_gate_check("stash-gems", ["ocr"], 1, "tally:gems")
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "quorum<2")

    def test_quorum_two_clears_when_filter_and_cell_ok(self):
        g = ca._kai_gate_check("stash-gems", ["ocr", "grid"], 2, "tally:gems")
        self.assertTrue(g["pass"])
        self.assertIsNone(g["reason"])

    def test_disagreement_collapses_to_quorum_fail(self):
        # a disagreement row already has confidence 0 / empty sources from the router —
        # the gate does not need a separate branch, it's caught by the quorum<2 check.
        g = ca._kai_gate_check("tooltip", [], 0, None)
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "quorum<2")

    # ── check 3: cell-correctness ───────────────────────────────────────────────
    def test_wrong_cell_route_mismatch_rejected(self):
        # label says runes but the route passed in points at gems — must never fire.
        g = ca._kai_gate_check("stash-runes", ["ocr", "grid"], 2, "tally:gems")
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "wrong-cell")

    def test_wrong_cell_chrome_dissent_vetoes_even_with_quorum(self):
        # tabstrip agrees with the final label (materials) but grid dissents to runes — a lone
        # chrome witness disagreeing is the wrong-tab->wrong-cell class; veto even though the
        # majority label otherwise cleared quorum.
        g = ca._kai_gate_check("stash-materials", ["ocr", "tabstrip"], 2, "tally:materials",
                                chrome_votes={"tabstrip": "stash-materials", "grid": "stash-runes"})
        self.assertFalse(g["pass"])
        self.assertEqual(g["reason"], "wrong-cell")

    def test_no_label_and_unroutable_label_rejected(self):
        self.assertEqual(ca._kai_gate_check("", [], 0, None)["reason"], "no-label")
        self.assertEqual(ca._kai_gate_check("gameplay", [], 0, None)["reason"], "no-label")
        self.assertEqual(ca._kai_gate_check("mystery", ["ocr", "grid"], 2, None)["reason"],
                         "no-hard-signal")

    def test_full_pass(self):
        g = ca._kai_gate_check("stash-runes", ["ocr", "grid"], 2, "tally:runes")
        self.assertEqual(g, {"pass": True, "reason": None})

    # ── ping-pong: bounded re-read → proven or honest miss ──────────────────────
    def test_pingpong_done_when_gate_passed(self):
        self.assertEqual(ca._kai_gate_pingpong(0, True), ("done", None))

    def test_pingpong_retries_then_honest_miss(self):
        act, tries = ca._kai_gate_pingpong(0, False, max_tries=3)
        self.assertEqual((act, tries), ("pingpong", 1))
        act, tries = ca._kai_gate_pingpong(1, False, max_tries=3)
        self.assertEqual((act, tries), ("pingpong", 2))
        act, tries = ca._kai_gate_pingpong(2, False, max_tries=3)
        self.assertEqual((act, tries), ("honest-miss", None))   # never routes a guess

    # ── ping-pong wired live: _kai_gate_pingpong_plan over a routing ledger ─────
    def test_pingpong_plan_retries_gate_held_judge_row(self):
        routing = [{"f": "tip.jpg", "ts": 1000, "route": "judge", "skipReason": "gate:name-not-in-db"}]
        retry, pinned, tries = ca._kai_gate_pingpong_plan(routing, {})
        self.assertEqual([r["f"] for r in retry], ["tip.jpg"])
        self.assertEqual(pinned, [])
        self.assertEqual(tries, {"tip.jpg": 1})

    def test_pingpong_plan_ignores_non_judge_and_non_gate_rows(self):
        routing = [
            {"f": "a.jpg", "ts": 1, "route": "tally:runes", "skipReason": "gate:no-hard-signal"},
            {"f": "b.jpg", "ts": 2, "route": "vault", "skipReason": "gate:wrong-cell"},
            {"f": "c.jpg", "ts": 3, "route": "judge", "skipReason": "not-selected"},
            {"f": "d.jpg", "ts": 4, "route": "judge", "skipReason": "cap"},
        ]
        retry, pinned, tries = ca._kai_gate_pingpong_plan(routing, {})
        self.assertEqual(retry, [])
        self.assertEqual(pinned, [])
        self.assertEqual(tries, {})

    def test_pingpong_plan_pins_after_max_tries(self):
        routing = [{"f": "tip.jpg", "ts": 1000, "route": "judge", "skipReason": "gate:quorum<2"}]
        # simulate the prior two passes already having retried
        retry, pinned, tries = ca._kai_gate_pingpong_plan(routing, {"tip.jpg": 2}, max_tries=3)
        self.assertEqual(retry, [])
        self.assertEqual(pinned, ["tip.jpg"])
        self.assertEqual(tries, {"tip.jpg": 3})

    def test_pingpong_plan_already_pinned_stays_pinned(self):
        # a frame already maxed out on a prior pass never re-enters the retry pool.
        routing = [{"f": "tip.jpg", "ts": 1000, "route": "judge", "skipReason": "gate:quorum<2"}]
        retry, pinned, tries = ca._kai_gate_pingpong_plan(routing, {"tip.jpg": 3}, max_tries=3)
        self.assertEqual(retry, [])
        self.assertEqual(pinned, ["tip.jpg"])
        self.assertEqual(tries, {"tip.jpg": 3})

    def test_pingpong_plan_persists_independent_tries_per_frame(self):
        routing = [
            {"f": "a.jpg", "ts": 1, "route": "judge", "skipReason": "gate:name-not-in-db"},
            {"f": "b.jpg", "ts": 2, "route": "judge", "skipReason": "gate:no-hard-signal"},
        ]
        retry, pinned, tries = ca._kai_gate_pingpong_plan(routing, {"a.jpg": 2}, max_tries=3)
        self.assertEqual(sorted(r["f"] for r in retry), ["b.jpg"])
        self.assertEqual(pinned, ["a.jpg"])
        self.assertEqual(tries, {"a.jpg": 3, "b.jpg": 1})

    # ── integration: wired into _kai_build_routing's ledger ────────────────────
    def test_ledger_gate_fields_present_journal_only_already_gated_by_router(self):
        # journal-only materials sticky (no chrome witness) never even clears router quorum
        # (confidence 1: 'read'/'judge' always vote 'tooltip', so only ocr/tabstrip/grid can
        # ever be journal's SECOND agreeing vote on a stash-* label) — the router's own
        # 'confidence<2' already wins the skipReason message. The gate fields are still
        # attached and correctly say why: no chrome/OCR witness backs this label.
        scan = [{"f": "m.jpg", "ts": 1000, "journal": True, "journalLabel": "stash-materials",
                 "label": "stash-materials"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertIn("gatePass", r)
        self.assertIn("gateReason", r)
        self.assertIn("gateSources", r)
        self.assertEqual(r["confidence"], 1)
        self.assertEqual(r["skipReason"], "confidence<2")
        self.assertFalse(r["gatePass"])
        self.assertEqual(r["gateReason"], "no-hard-signal")

    def test_ledger_gate_vetoes_lone_chrome_dissenter_wrong_cell(self):
        # THE wrong-tab->wrong-cell class (vault-0 / materials false-positive): journal +
        # tabstrip both say materials (quorum clears at conf 2, router says 'not-selected' —
        # fireable) but grid — a real chrome witness — says runes. The router's majority vote
        # outvotes grid, but the gate refuses to let a dissenting chrome brain be silenced.
        scan = [{"f": "m2.jpg", "ts": 2000,
                 "journal": True, "journalLabel": "stash-materials",
                 "tabstrip": True, "tabstripLabel": "stash-materials",
                 "grid": True, "gridLabel": "stash-runes",
                 "label": "stash-materials"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertEqual(sorted(r["sources"]), ["journal", "tabstrip"])
        self.assertEqual(r["confidence"], 2)
        self.assertEqual(r["route"], None)              # veto clears the route
        self.assertFalse(r["gatePass"])
        self.assertEqual(r["gateReason"], "wrong-cell")
        self.assertEqual(r["skipReason"], "gate:wrong-cell")
        funnel, _, _ = ca._kai_stage3_select([r])
        self.assertEqual(funnel, [])                    # Stage 3 can never select it

    def test_ledger_gate_passes_grid_confirmed_materials(self):
        scan = [{"f": "m3.jpg", "ts": 3000, "journal": True, "journalLabel": "stash-materials",
                 "grid": True, "gridLabel": "stash-materials", "label": "stash-materials"}]
        r = ca._kai_build_routing(scan, [], "S", [])[0]
        self.assertEqual(r["confidence"], 2)
        self.assertTrue(r["gatePass"])
        self.assertEqual(r["skipReason"], "not-selected")   # fireable — Stage 3 will pick it up
        funnel, _, _ = ca._kai_stage3_select([r])
        self.assertEqual(len(funnel), 1)
        self.assertEqual(funnel[0]["tab"], "materials")


class TestSuperAnalyzeKai(unittest.TestCase):
    """v949.x 🧠🔬 SUPER-ANALYZE KAI — Phase B, THE 4TH ORGAN (ENGINE_ARCHITECTURE.md "MASTER
    BRAIN" layer 4 / ARCH_PINGPONG §Q1-hybrid). The closer's gate (§3.5) only PROVES a frame is
    real content; this organ is the deep INDEPENDENT re-read for frames the gate proved but no
    eye ever named a real item on — the fix for "film complete but only 3 registered". Pure
    selection (ca._kai_super_already_named / ca._kai_super_select); firing lives in the closer
    and is not unit-tested here (real vision call)."""

    FN = {"windforce", "hellfire torch", "shael rune"}

    # ── _kai_super_already_named ────────────────────────────────────────────────
    def test_already_named_true_for_nearby_real_deep_read(self):
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Windforce"]}]
        self.assertTrue(ca._kai_super_already_named(sess, 1500, fullnames=self.FN, window_ms=4000))

    def test_already_named_false_for_garbage_nearby_read(self):
        # a deep read landed nearby but named nothing DB-real ("IA Lla" garble) — still a
        # candidate for super-analyze.
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["IA Lla"]}]
        self.assertFalse(ca._kai_super_already_named(sess, 1500, fullnames=self.FN, window_ms=4000))

    def test_already_named_true_for_nearby_real_judge_verdict(self):
        sess = [{"lane": "kai", "ts": 2000,
                  "kai": {"judge": {"name": "Hellfire Torch", "tier": "grail"}}}]
        self.assertTrue(ca._kai_super_already_named(sess, 2200, fullnames=self.FN, window_ms=4000))

    def test_already_named_ignores_judge_verdict_outside_grail_keep_border(self):
        sess = [{"lane": "kai", "ts": 2000,
                  "kai": {"judge": {"name": "Hellfire Torch", "tier": "unreadable"}}}]
        self.assertFalse(ca._kai_super_already_named(sess, 2200, fullnames=self.FN, window_ms=4000))

    def test_already_named_false_when_out_of_window(self):
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Windforce"]}]
        self.assertFalse(ca._kai_super_already_named(sess, 9000, fullnames=self.FN, window_ms=4000))

    def test_already_named_false_with_no_rows(self):
        self.assertFalse(ca._kai_super_already_named([], 1000, fullnames=self.FN))

    # ── _kai_super_select ───────────────────────────────────────────────────────
    def test_select_requires_gate_pass_true(self):
        routing = [
            {"f": "a.jpg", "ts": 1, "label": "tooltip", "gatePass": True, "confidence": 2},
            {"f": "b.jpg", "ts": 2, "label": "tooltip", "gatePass": False, "confidence": 2},
            {"f": "c.jpg", "ts": 3, "label": "tooltip", "gatePass": None, "confidence": 2},
        ]
        cands = ca._kai_super_select(routing, [], fullnames=self.FN)
        self.assertEqual([r["f"] for r in cands], ["a.jpg"])

    def test_select_only_tooltip_or_stash_dash_labels_never_gameplay_or_plain_stash(self):
        routing = [
            {"f": "gp.jpg", "ts": 1, "label": "gameplay", "gatePass": True, "confidence": 2},
            {"f": "st.jpg", "ts": 2, "label": "stash", "gatePass": True, "confidence": 2},
            {"f": "inv.jpg", "ts": 3, "label": "inventory", "gatePass": True, "confidence": 2},
            {"f": "tip.jpg", "ts": 4, "label": "tooltip", "gatePass": True, "confidence": 2},
            {"f": "sr.jpg", "ts": 5, "label": "stash-runes", "gatePass": True, "confidence": 2},
        ]
        cands = ca._kai_super_select(routing, [], fullnames=self.FN)
        self.assertEqual(sorted(r["f"] for r in cands), ["sr.jpg", "tip.jpg"])

    def test_select_excludes_frames_already_named_a_real_item(self):
        routing = [{"f": "tip.jpg", "ts": 1000, "label": "tooltip", "gatePass": True, "confidence": 2}]
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Windforce"]}]
        cands = ca._kai_super_select(routing, sess, fullnames=self.FN)
        self.assertEqual(cands, [])

    def test_select_includes_frame_whose_nearby_read_was_garbage(self):
        # THE CORE BUG THIS ORGAN FIXES: live+OCR both garbled ("IA Lla") — still a candidate.
        routing = [{"f": "tip.jpg", "ts": 1000, "label": "tooltip", "gatePass": True, "confidence": 2}]
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["IA Lla"]}]
        cands = ca._kai_super_select(routing, sess, fullnames=self.FN)
        self.assertEqual([r["f"] for r in cands], ["tip.jpg"])

    def test_select_orders_tooltip_before_stash_then_confidence_then_ts(self):
        routing = [
            {"f": "sr1.jpg", "ts": 100, "label": "stash-runes", "gatePass": True, "confidence": 3},
            {"f": "tip2.jpg", "ts": 300, "label": "tooltip", "gatePass": True, "confidence": 2},
            {"f": "tip1.jpg", "ts": 200, "label": "tooltip", "gatePass": True, "confidence": 3},
        ]
        cands = ca._kai_super_select(routing, [], fullnames=self.FN)
        # tooltip frames first (higher confidence first among them), stash-* last
        self.assertEqual([r["f"] for r in cands], ["tip1.jpg", "tip2.jpg", "sr1.jpg"])

    def test_select_respects_explicit_cap(self):
        routing = [{"f": "t%d.jpg" % i, "ts": i, "label": "tooltip", "gatePass": True, "confidence": 2}
                   for i in range(5)]
        cands = ca._kai_super_select(routing, [], fullnames=self.FN, cap=2)
        self.assertEqual(len(cands), 2)

    def test_select_default_cap_from_env_is_8_to_12_budget(self):
        # never a runaway — the default env cap must sit in the documented 8-12 budget.
        old = os.environ.get("TV_KAI_SUPER_MAX")
        try:
            os.environ.pop("TV_KAI_SUPER_MAX", None)
            routing = [{"f": "t%d.jpg" % i, "ts": i, "label": "tooltip", "gatePass": True, "confidence": 2}
                       for i in range(20)]
            cands = ca._kai_super_select(routing, [], fullnames=self.FN)
            self.assertGreaterEqual(len(cands), 8)
            self.assertLessEqual(len(cands), 12)
        finally:
            if old is None:
                os.environ.pop("TV_KAI_SUPER_MAX", None)
            else:
                os.environ["TV_KAI_SUPER_MAX"] = old

    def test_select_env_cap_override_respected(self):
        old = os.environ.get("TV_KAI_SUPER_MAX")
        try:
            os.environ["TV_KAI_SUPER_MAX"] = "3"
            routing = [{"f": "t%d.jpg" % i, "ts": i, "label": "tooltip", "gatePass": True, "confidence": 2}
                       for i in range(10)]
            cands = ca._kai_super_select(routing, [], fullnames=self.FN)
            self.assertEqual(len(cands), 3)
        finally:
            if old is None:
                os.environ.pop("TV_KAI_SUPER_MAX", None)
            else:
                os.environ["TV_KAI_SUPER_MAX"] = old

    def test_select_never_reads_gameplay_even_with_gate_pass_somehow_true(self):
        # LAW: only gate-proved tooltip/stash-* frames — gameplay/boot never qualifies even in
        # a hypothetical bad-data case where gatePass got set True on a gameplay-labelled row.
        routing = [{"f": "gp.jpg", "ts": 1, "label": "gameplay", "gatePass": True, "confidence": 3}]
        cands = ca._kai_super_select(routing, [], fullnames=self.FN)
        self.assertEqual(cands, [])

    # ── _fire_aic_judge_js tag plumbing ─────────────────────────────────────────
    def test_fire_aic_judge_js_embeds_tag_when_given(self):
        js = ca._fire_aic_judge_js("/hist/x.jpg", "S", "reel_S/x", 1000, live=False, tag="super")
        self.assertIn('res.tag="super"', js.replace("'", '"').replace(" ", ""))

    def test_fire_aic_judge_js_omits_tag_field_when_absent(self):
        js = ca._fire_aic_judge_js("/hist/x.jpg", "S", "reel_S/x", 1000, live=False)
        self.assertNotIn("res.tag=", js)


class TestKaiVerdictSuperTag(unittest.TestCase):
    """v949.x — /kai_verdict journals the SUPER-ANALYZE provenance tag (kai.judge.tag) so the
    closer can distinguish its own deep re-reads from the ordinary live/post-seal judge lane
    without a second endpoint — same handler, one extra breadcrumb field. Driven through a REAL
    ephemeral Handler, matching TestIntakeReceiptDedupe's harness."""

    @classmethod
    def setUpClass(cls):
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), ca.Handler)
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        self._old_here = ca.HERE
        self.tmp = tempfile.mkdtemp(prefix="tvd-super-")
        ca.HERE = self.tmp
        open(os.path.join(self.tmp, "sessions.jsonl"), "w").close()

    def tearDown(self):
        ca.HERE = self._old_here
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _post(self, payload):
        req = urllib.request.Request(
            "http://127.0.0.1:%d/kai_verdict" % self.port,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())

    def _judge_rows(self):
        rows = []
        with open(os.path.join(self.tmp, "sessions.jsonl"), encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    row = json.loads(ln)
                    if row.get("lane") == "kai" and row.get("mode") == "kai-judge":
                        rows.append(row)
        return rows

    def test_super_tag_journaled_on_kai_judge_row(self):
        self._post({"fts": 1000, "name": "Vex Rune", "verdict": {"tier": "keep", "score": 5},
                    "ok": True, "sid": "S", "frameId": "reel_S/x", "tag": "super"})
        rows = self._judge_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kai"]["judge"]["tag"], "super")
        self.assertIn("super-judge", rows[0]["note"])

    def test_no_tag_leaves_tag_field_none(self):
        self._post({"fts": 1000, "name": "Vex Rune", "verdict": {"tier": "keep", "score": 5},
                    "ok": True, "sid": "S", "frameId": "reel_S/y"})
        rows = self._judge_rows()
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["kai"]["judge"]["tag"])
        self.assertNotIn("super-judge", rows[0]["note"])

    def test_live_tag_takes_precedence_over_super_note_wording(self):
        # live=True always wins the note's "live-" prefix regardless of tag (mid-session live
        # judge fires never carry tag='super' in practice, but the note wording must stay
        # unambiguous if it ever happened).
        self._post({"fts": 1000, "name": "Vex Rune", "verdict": {"tier": "keep", "score": 5},
                    "ok": True, "sid": "S", "frameId": "reel_S/z", "live": True, "tag": "super"})
        rows = self._judge_rows()
        self.assertEqual(rows[0]["kai"]["judge"]["tag"], "super")
        self.assertIn("live-judge", rows[0]["note"])
        self.assertNotIn("super-judge", rows[0]["note"])


class TestLiveJudgeQueue(unittest.TestCase):
    """v948.2 — live mid-session Item Checker gates (pure, no vision)."""

    def test_queue_new_names_not_echo(self):
        rd = {
            "lane": "deep", "frameId": "10_100", "scene": "inventory",
            "names_new": ["Beast Noose"], "names_echo": ["Horadric Cube"],
            "names_moved": [], "names": ["Beast Noose", "Horadric Cube"],
        }
        self.assertTrue(ca._live_judge_should_queue(rd))
        self.assertEqual(ca._live_judge_interesting_names(rd), ["Beast Noose"])

    def test_skip_pure_echo_and_anchors(self):
        rd = {
            "lane": "deep", "frameId": "10_101", "scene": "stash",
            "stashTab": "personal",
            "names_new": [], "names_echo": ["Horadric Cube", "Tome of Town Portal"],
            "names_moved": [], "names": ["Horadric Cube"],
        }
        self.assertFalse(ca._live_judge_should_queue(rd))
        self.assertEqual(ca._live_judge_interesting_names(rd), [])

    def test_skip_tally_tabs(self):
        rd = {
            "lane": "deep", "frameId": "10_102", "scene": "stash", "stashTab": "gems",
            "names_new": ["Chipped Ruby"], "names_echo": [], "names_moved": [],
            "names": ["Chipped Ruby"],
        }
        self.assertFalse(ca._live_judge_should_queue(rd))

    def test_skip_when_live_env_off(self):
        rd = {
            "lane": "deep", "frameId": "10_103",
            "names_new": ["Steel Ring"], "names_echo": [], "names_moved": [],
        }
        old = os.environ.get("TV_KAI_JUDGE_LIVE")
        try:
            os.environ["TV_KAI_JUDGE_LIVE"] = "0"
            self.assertFalse(ca._live_judge_should_queue(rd))
        finally:
            if old is None:
                os.environ.pop("TV_KAI_JUDGE_LIVE", None)
            else:
                os.environ["TV_KAI_JUDGE_LIVE"] = old

    def test_judge_already_near_dedupes_live_vs_stage3(self):
        rows = [
            {"lane": "kai", "mode": "kai-judge", "ts": 100000,
             "kai": {"judge": {"name": "X", "tier": "keep", "live": True}}},
        ]
        self.assertTrue(ca._judge_already_near(rows, 103000, window_ms=6000))
        self.assertFalse(ca._judge_already_near(rows, 120000, window_ms=6000))

    def test_moved_names_qualify(self):
        rd = {
            "lane": "deep", "frameId": "10_104", "scene": "stash", "stashTab": "personal",
            "names_new": [], "names_echo": ["Cube"], "names_moved": ["Ars Dul'Mephistos"],
            "names": ["Ars Dul'Mephistos"],
        }
        self.assertTrue(ca._live_judge_should_queue(rd))
        self.assertIn("Ars Dul'Mephistos", ca._live_judge_interesting_names(rd))

    def test_fire_js_marks_live(self):
        js = ca._fire_aic_judge_js("/hist/x.jpg", "sid1", "fid1", 99, live=True)
        self.assertIn("aicJudge", js)
        self.assertIn("aicJudgeApply", js)
        self.assertIn("res.live=true", js)
        js2 = ca._fire_aic_judge_js("/hist/x.jpg", "sid1", "fid1", 99, live=False)
        self.assertIn("res.live=false", js2)


class TestKaiNameishRecal(unittest.TestCase):
    """v944.7 (Fable forensic recalibration) — the KAI missed ledger counts unread ITEM NAMES,
    not unread flavor/stat lines. Proven against the real reel: Hellfire Torch flagged missed
    (false positive, its name WAS registered — flavor lines triggered it) vs Jade Jewel (true
    miss, a hovered magic jewel never registered)."""

    def test_names_pass(self):
        for nm in ("Jade Jewel", "Hellfire Torch", "Ars Dul'Mephistos", "The Stone of Jordan"):
            self.assertTrue(ca._kai_nameish(nm), nm)

    def test_flavor_and_stat_lines_rejected(self):
        for flavor in ("Required Level: 75", "Poison Resist +23%", "Level 30 Hydra (420 Charges)",
                       "Keep in Inventory to Gain Bonus", "Ctrl + Left Click to Move to Inventory",
                       "+3 to Warlock Skills", "All Resistances +12",
                       "Can be Inserted into Socketed Items", "128% Extra Gold from Monsters"):
            self.assertFalse(ca._kai_nameish(flavor), flavor)

    def test_bare_ui_words_rejected(self):
        for ui in ("Stash", "Inventory", "Runes", "Gems", "Materials", "Shared", "Personal"):
            self.assertFalse(ca._kai_nameish(ui), ui)


class TestIntakeLease(unittest.TestCase):
    """v945.6 — exactly one owner fires a given tab at a time."""

    def setUp(self):
        ca._INTAKE_LEASES.clear()

    def tearDown(self):
        ca._INTAKE_LEASES.clear()

    def test_claim_blocks_second_owner(self):
        a = ca._intake_lease_claim("runes", "engine-driver", now_ms=1_000_000)
        self.assertTrue(a["ok"])
        b = ca._intake_lease_claim("runes", "board", now_ms=1_000_100)
        self.assertFalse(b["ok"])
        self.assertEqual(b["why"], "held")
        self.assertEqual(b["holder"], "engine-driver")

    def test_same_owner_renews(self):
        a = ca._intake_lease_claim("gems", "board", ttl_ms=60_000, now_ms=2_000_000)
        self.assertTrue(a["ok"])
        b = ca._intake_lease_claim("gems", "board", ttl_ms=60_000, now_ms=2_010_000)
        self.assertTrue(b["ok"])
        self.assertEqual(b["owner"], "board")

    def test_release_then_other_may_claim(self):
        ca._intake_lease_claim("materials", "engine-driver", now_ms=3_000_000)
        r = ca._intake_lease_release("materials", "engine-driver")
        self.assertTrue(r["released"])
        c = ca._intake_lease_claim("materials", "board", now_ms=3_000_100)
        self.assertTrue(c["ok"])

    def test_expired_lease_allows_new_owner(self):
        # v1202 — expiry is monotonic (untilMono), not wall-clock. Advancing only now_ms
        # leaves the lease held forever in a same-process test. Drive both clocks past TTL.
        # floor TTL is 5s — advance past until.
        ca._intake_lease_claim("runes", "board", ttl_ms=5_000,
                              now_ms=4_000_000, now_mono_ms=4_000_000)
        c = ca._intake_lease_claim("runes", "engine-driver", ttl_ms=60_000,
                                 now_ms=4_006_000, now_mono_ms=4_006_000)
        self.assertTrue(c["ok"])
        self.assertEqual(c["owner"], "engine-driver")

    def test_vault_key_scheme_cross_blocks(self):
        # v945.7 (Fable review) — the board claims vault as 'vault_<tab>'. If the driver claimed
        # the bare tab ('personal') the two keys would never collide and the lease would be a no-op
        # for vault dual-fire. A same-key cross-owner claim MUST block.
        a = ca._intake_lease_claim("vault_personal", "board", now_ms=5_000_000)
        self.assertTrue(a["ok"])
        b = ca._intake_lease_claim("vault_personal", "engine-driver", now_ms=5_000_100)
        self.assertFalse(b["ok"], "vault_personal must cross-block (same key, diff owner)")
        # and the bare tab is a DIFFERENT lease — proving why the driver must use the key
        c = ca._intake_lease_claim("personal", "engine-driver", now_ms=5_000_200)
        self.assertTrue(c["ok"], "'personal' != 'vault_personal' — mismatched keys don't block")

    def test_driver_claims_by_key_not_tab(self):
        # source-pin the fix: the engine-driver's lease claim must use job['key'] (which is
        # 'vault_personal' / 'runes' — the board's scheme), not the bare job['tab'].
        import inspect
        src = inspect.getsource(ca)
        self.assertIn('_intake_lease_claim(job.get("key") or job.get("tab")', src)
        # every driver release uses the key too (claim/release keys must match or the lease leaks)
        self.assertNotIn('_intake_lease_release(inflight.get("tab")', src)
        self.assertNotIn('_intake_lease_release(job.get("tab")', src)


class TestSessionHealth(unittest.TestCase):
    """v946 — one-glance session health from journal rows."""

    def test_tabs_and_verdict(self):
        rows = [
            {"lane": "intake", "intake": {"tab": "runes", "ok": True, "total": 404}},
            {"lane": "intake", "intake": {"tab": "gems", "ok": False, "total": 0}},
            {"lane": "deep", "stashTab": "runes", "names": ["El"]},
            {"lane": "kai", "kai": {"missedFrames": 3}},
        ]
        h = ca._session_health_from_rows(rows, leases={"runes": {"owner": "engine-driver"}},
                                         driver={"fired": 2, "refire": 1})
        self.assertEqual(h["tabs"]["runes"]["total"], 404)
        self.assertTrue(h["tabs"]["runes"]["ok"])
        self.assertFalse(h["tabs"]["gems"]["ok"])
        self.assertEqual(h["verdict"], "partial")
        self.assertEqual(h["refires"], 1)
        self.assertIn("KAI closed · 3 missed-text", h["story"])

    def test_idle_when_empty(self):
        h = ca._session_health_from_rows([])
        self.assertEqual(h["verdict"], "idle")


class TestFilmCompleteness(unittest.TestCase):
    """v948.13 — FILM ↔ REGISTRATION COMPLETENESS (ENGINE_ARCHITECTURE.md target #2).
    ca._session_completeness cross-references reel frames (film, ground truth) against
    deep reads: 'unread' = KAI's retro sweep saw item text no read ever claimed (honest,
    already caught — a reel frame backs it by construction); 'read-no-film' = a read
    landed but no reel frame exists near it (a REAL capture drop)."""

    def test_full_coverage_no_gaps(self):
        # a read at ts=1000 with a reel frame at ts=1000 (or within tolerance) → no drop.
        sess_rows = [{"lane": "deep", "names": ["Windforce"], "captureTs": 1000, "ts": 1000,
                      "frameId": "reel_S/1_1000"}]
        reel_frames = [{"f": "f_1000.jpg", "ts": 1000}, {"f": "f_2000.jpg", "ts": 2000}]
        c = ca._session_completeness(sess_rows, reel_frames)
        self.assertEqual(c["reads"], 1)
        self.assertEqual(c["reel_frames"], 2)
        self.assertEqual(c["unread"], 0)
        self.assertEqual(c["dropped"], 0)
        self.assertEqual(c["gaps"], [])
        self.assertEqual(c["hovers_estimated"], 1)
        self.assertEqual(c["coveragePct"], 100.0)

    def test_read_with_no_nearby_reel_frame_is_a_drop(self):
        # a read at ts=50000 but the nearest reel frame is 5s away (tol default 1500ms)
        # → the film thread skipped archiving near that moment: a real drop.
        sess_rows = [{"lane": "deep", "names": ["Shako"], "captureTs": 50000, "ts": 50000,
                      "frameId": "reel_S/1_50000"}]
        reel_frames = [{"f": "f_1000.jpg", "ts": 1000}, {"f": "f_45000.jpg", "ts": 45000}]
        c = ca._session_completeness(sess_rows, reel_frames)
        self.assertEqual(c["dropped"], 1)
        kinds = [g["kind"] for g in c["gaps"]]
        self.assertIn("read-no-film", kinds)

    def test_kai_unread_rows_are_honest_not_drops(self):
        # KAI's retro sweep found item text no read claimed — a reel frame backs it by
        # construction (KAI only scans real reel frames); this is NOT a capture drop.
        sess_rows = [
            {"lane": "kai", "frameId": "reel_S/f_9000", "kai": {"texts": ["Harlequin Crest"]},
             "ts": 9000},
            {"lane": "kai", "frameId": "", "kai": {"missedFrames": 1}},   # summary row, no frameId
        ]
        reel_frames = [{"f": "f_9000.jpg", "ts": 9000}]
        c = ca._session_completeness(sess_rows, reel_frames)
        self.assertEqual(c["reads"], 0)
        self.assertEqual(c["unread"], 1)          # only the per-item row counts, not the summary
        self.assertEqual(c["dropped"], 0)          # never miscounted as a film drop
        self.assertEqual(c["gaps"][0]["kind"], "unread")
        self.assertEqual(c["hovers_estimated"], 1)
        self.assertEqual(c["coveragePct"], 0.0)

    def test_empty_session_is_fully_covered(self):
        c = ca._session_completeness([], [])
        self.assertEqual(c, {"hovers_estimated": 0, "reads": 0, "reel_frames": 0, "gaps": [],
                             "unread": 0, "dropped": 0, "coveragePct": 100.0})

    def test_gaps_sorted_by_ts(self):
        sess_rows = [
            {"lane": "kai", "frameId": "reel_S/f_5000", "kai": {"texts": ["b"]}, "ts": 5000},
            {"lane": "deep", "names": ["a"], "captureTs": 90000, "ts": 90000, "frameId": "x"},
            {"lane": "kai", "frameId": "reel_S/f_1000", "kai": {"texts": ["c"]}, "ts": 1000},
        ]
        c = ca._session_completeness(sess_rows, [{"f": "f_5000.jpg", "ts": 5000}])
        self.assertEqual([g["ts"] for g in c["gaps"]], sorted(g["ts"] for g in c["gaps"]))

    def test_custom_tolerance_widens_or_narrows_drops(self):
        sess_rows = [{"lane": "deep", "names": ["Item"], "captureTs": 2000, "ts": 2000,
                      "frameId": "x"}]
        reel_frames = [{"f": "f_0.jpg", "ts": 0}]
        # 2000ms gap: fails default 1500ms tolerance, passes a wider 3000ms tolerance
        self.assertEqual(ca._session_completeness(sess_rows, reel_frames)["dropped"], 1)
        self.assertEqual(
            ca._session_completeness(sess_rows, reel_frames, tol_ms=3000)["dropped"], 0)


class TestVaultGridAutoGate(unittest.TestCase):
    """v946.7 — vaultIntake is tooltip-identity, not icon-grid. Auto-fire only with real names."""

    def test_names_worth_auto(self):
        self.assertFalse(ca._vault_names_worth_auto([]))
        self.assertFalse(ca._vault_names_worth_auto(["'Ii'"]))
        self.assertFalse(ca._vault_names_worth_auto(["IA Lla", "Ii"]))
        self.assertTrue(ca._vault_names_worth_auto(["Gheed's Fortune Grand Charm"]))
        self.assertTrue(ca._vault_names_worth_auto(["War Traveler"]))

    def test_vault_identity_grid_error_no_refire(self):
        job = {"key": "vault_personal", "tab": "personal", "fid": "2_1", "tries": 0, "has_names": False}
        act, _ = ca._drv_empty_refire_plan(job, {"ok": False, "total": 0}, "3_1")
        self.assertEqual(act, "giveup")

    def test_vault_tooltip_error_refires(self):
        job = {"key": "vault_shared", "tab": "shared", "fid": "4_1", "tries": 0, "has_names": True}
        act, nxt = ca._drv_empty_refire_plan(job, {"ok": False, "total": 0}, "5_1")
        self.assertEqual(act, "refire")
        self.assertEqual(nxt["fid"], "5_1")

    def test_vaultcount_zero_refires(self):
        # COUNT path: total=0 is a failed count → re-fire (like tally)
        job = {"key": "vaultcount_personal", "tab": "personal", "fid": "2_1", "tries": 0}
        act, nxt = ca._drv_empty_refire_plan(job, {"ok": True, "total": 0}, "3_1")
        self.assertEqual(act, "refire")
        self.assertEqual(nxt["fid"], "3_1")
        act2, _ = ca._drv_empty_refire_plan(job, {"ok": True, "total": 27}, "3_1")
        self.assertEqual(act2, "done")


class TestStashTabIdentity(unittest.TestCase):
    """v946.1 — gems/materials must not vanish into generic stash."""

    def test_tab_from_ocr_lines(self):
        # single-tab lines → that tab
        self.assertEqual(ca._tab_from_ocr_lines(["MATERIALS"]), "materials")
        self.assertEqual(ca._tab_from_ocr_lines(["Runes", "El", "Eld"]), "runes")
        self.assertEqual(ca._tab_from_ocr_lines(["Shared"]), "shared")
        self.assertEqual(ca._tab_from_ocr_lines(["Gems"]), "gems")
        self.assertEqual(ca._tab_from_ocr_lines(["Fortune"]), "")  # no false rune in fortune
        # v947 — full chrome prints every tab name → ambiguous (grid fingerprint decides)
        self.assertEqual(ca._tab_from_ocr_lines(
            ["Personal", "Shared", "Gems", "Materials", "Runes"]), "")
        self.assertEqual(ca._tab_from_ocr_lines(["Shared Stash", "Gems"]), "")  # two canons

    def test_frame_cls_tally_words(self):
        self.assertEqual(ca._kai_frame_cls(["Gems", "Chipped Diamond"], []), "stash-gems")
        self.assertEqual(ca._kai_frame_cls(["Materials", "Key"], []), "stash-materials")
        self.assertEqual(ca._kai_frame_cls(["Runes"], []), "stash-runes")

    def test_sticky_tab_holds_between_deeps(self):
        # deep at t=1000 runes, deep at t=10000 gems — frame at 5000 inherits runes
        times = [(1000, "runes"), (10000, "gems")]
        self.assertEqual(ca._kai_sticky_tab(5000, times), "runes")
        self.assertEqual(ca._kai_sticky_tab(10050, times), "gems")
        self.assertEqual(ca._kai_sticky_tab(100, [(20000, "runes")]), None)  # far before first deep
        # near future deep within 4s (frame before deep stamp lands)
        self.assertEqual(ca._kai_sticky_tab(900, [(1000, "materials")]), "materials")

    def test_stash_eye_fuse_and_grid(self):
        """v947 — intake-mimic eyes fuse without calling intake."""
        import stash_eye as se
        tab, src = se.fuse_tab_signals(ocr_tab="gems", grid_label="stash-gems",
                                       journal_tab="shared", model_tab="")
        self.assertEqual(tab, "gems")
        self.assertIn("ocr", src)
        self.assertIn("grid", src)
        # OCR tally beats sticky shared (the farm miss that started this work)
        tab2, _ = se.fuse_tab_signals(ocr_tab="", grid_label="stash-materials",
                                      journal_tab="shared", model_tab="shared")
        self.assertEqual(tab2, "materials")
        # multi-chrome OCR empty → journal sticky still works
        tab3, src3 = se.fuse_tab_signals(ocr_tab="", grid_label="stash",
                                         journal_tab="runes", model_tab="")
        self.assertEqual(tab3, "runes")
        self.assertIn("journal", src3)

    def test_grid_solo_materials_kai_retro(self):
        """v948.7 — KAI retro: film stills promote materials without live deep sticky."""
        import stash_eye as se
        # live path still blocks inventing materials on empty corroboration
        tab_live, src_live = se.fuse_tab_signals(
            ocr_tab="", grid_label="stash-materials", journal_tab="", model_tab="",
            allow_grid_solo=False)
        self.assertEqual(tab_live, "")
        # KAI retro path allows grid solo when panel is already stash-*
        tab_kai, src_kai = se.fuse_tab_signals(
            ocr_tab="", grid_label="stash-materials", journal_tab="", model_tab="",
            allow_grid_solo=True)
        self.assertEqual(tab_kai, "materials")
        self.assertIn("grid", src_kai)
        self.assertIn("solo", src_kai)

    def test_boot_screen_guard(self):
        """v948.8 — the D2R title/reconnect splash ('Press Any Key to Begin' /
        'Connecting to Battle.net') is ~92% black + a burning-logo chroma sliver,
        same signature classify_stash_grid's materials branch looks for. Caught
        auditing reel s_1784636825977_40909: 11 boot-screen frames grid-fingerprinted
        as stash-materials and the KAI retro funnel wasted its one materials shot
        on one (materialIntake correctly came back total=0 — there was nothing
        there — but the ledger lied about tab state). Full-frame OCR (noisy —
        'PRESS ANY KfY T& BEGIN') still catches it; word-level match, not phrase."""
        import stash_eye as se
        self.assertTrue(se.is_boot_screen(["PRESS ANY KfY T& BEGIN"]))
        self.assertTrue(se.is_boot_screen(["CONNECTING TO BATTLE.NET"]))
        self.assertTrue(se.is_boot_screen(["DIABLO", "RESURRECTED"]))
        self.assertFalse(se.is_boot_screen(["Key of Terror", "Essence of Suffering"]))
        self.assertFalse(se.is_boot_screen([]))
        # analyze_frame short-circuits to gameplay before grid/OCR fusion can
        # mistake the splash for a tally tab (allow_grid_solo=True == KAI retro)
        p = os.path.join(HERE, "frames", "hist",
                          "reel_s_1784636825977_40909", "f_1784636855259.jpg")
        if os.path.isfile(p):
            out = se.analyze_frame(p, ocr_lines=["PRESS ANY KfY T& BEGIN"],
                                    allow_grid_solo=True)
            self.assertEqual(out["cls"], "gameplay")
            self.assertEqual(out["tab"], "")
            self.assertIn("boot-screen-guard", out["sources"])

    def test_materials_grid_detects_real_receipted_frame(self):
        """v948.19 — Grok forensic #5 (2026-07-21 21:05 fast run, 'materials 0 classes').

        THE MATERIALS VERDICT for reel s_1784657116450_14249: honest-zero — the player
        never opened the Materials tab this run (0 OCR-chrome hits across all 153 frames'
        routing rows, and visual review of the reel confirms Personal -> Shared -> Runes
        only). This pin proves the OTHER half of Grok's question: does classify_stash_grid
        actually detect a real materials frame when one exists? Before v948.19 the answer
        was NO — this exact frame is ground truth (a real, receipted materialIntake fired
        on it in sessions.jsonl: sessionId s_1784561805354_94817, frameId
        'reel_s_1784561282553_86929/f_1784561356596', total=184, ok=True) and the OLD
        materials band (fd>=0.42, fc 0.04-0.10) MISSED it (fd=0.3839, fc=0.0308 — both
        outside the old floors). The recalibrated band in stash_eye.py now catches it."""
        import stash_eye as se
        p = os.path.join(HERE, "frames", "hist",
                          "reel_s_1784561282553_86929", "f_1784561356596.jpg")
        if os.path.isfile(p):
            label, detail = se.classify_stash_grid(p)
            self.assertEqual(label, "stash-materials")
            self.assertEqual(detail.get("pick"), "materials")
        # second receipted-real materials frame (different session, same law) —
        # sessionId s_1784563564997_15694, total=210
        p2 = os.path.join(HERE, "frames", "hist",
                           "reel_s_1784561832500_95271", "f_1784561874907.jpg")
        if os.path.isfile(p2):
            label2, _ = se.classify_stash_grid(p2)
            self.assertEqual(label2, "stash-materials")

    def test_materials_grid_rejects_dark_gameplay_false_positive(self):
        """v948.19 — the false-positive twin of the under-detection bug above: the OLD
        materials band (fd>=0.42, fc 0.04-0.10) also happily matched a plain GAMEPLAY
        combat frame (Catacombs fight, fire-lit, no stash panel open at all) because dark
        floor + fire chroma looks like 'empty materials slots + essence icons' in pure
        pixel terms. Found auditing reel s_1784647619282_26240 while calibrating the
        fix above. The recalibrated band (upper-bounded fd<=0.55, tighter fc) rejects it —
        same law as the is_boot_screen guard, extended to non-splash dark scenes."""
        import stash_eye as se
        p = os.path.join(HERE, "frames", "hist",
                          "reel_s_1784647619282_26240", "f_1784647734875.jpg")
        if os.path.isfile(p):
            label, detail = se.classify_stash_grid(p)
            self.assertNotEqual(label, "stash-materials")
            self.assertGreater(detail.get("frac_dark", 0), 0.55)  # confirms why: too dark

    def test_retro_promote_and_gap_funnel(self):
        """v948.7 — cluster promote + gap funnel from reel labels."""
        scan = [
            {"f": "f_1.jpg", "ts": 1000, "label": "stash", "gridLabel": "stash-materials",
             "tabstripLabel": None, "confidence": 2},
            {"f": "f_2.jpg", "ts": 2000, "label": "stash", "gridLabel": "stash-materials",
             "tabstripLabel": "stash-materials", "confidence": 2},
            {"f": "f_3.jpg", "ts": 3000, "label": "stash", "gridLabel": "stash",
             "confidence": 2},
            {"f": "f_4.jpg", "ts": 4000, "label": "gameplay", "confidence": 0},
        ]
        out = ca._kai_retro_promote_tally([dict(x) for x in scan])
        self.assertEqual(out[0]["label"], "stash-materials")
        self.assertEqual(out[1]["label"], "stash-materials")
        # plan-like rows for gap funnel
        plan = [
            {"f": "f_2.jpg", "ts": 2000, "label": "stash-materials", "confidence": 2,
             "route": "tally:materials", "routed": None, "skipReason": "not-selected",
             "gridLabel": "stash-materials"},
            {"f": "f_9.jpg", "ts": 9000, "label": "stash-gems", "confidence": 1,
             "gridLabel": "stash-gems", "route": None, "routed": None},
        ]
        # gems already receipted → only materials gap
        sess = [{"lane": "intake", "intake": {"tab": "gems", "ok": True, "total": 50, "kind": "kai-funnel"}}]
        gaps = ca._kai_stage3_gap_funnels(plan, sess)
        tabs = {g["tab"] for g in gaps}
        self.assertIn("materials", tabs)
        self.assertNotIn("gems", tabs)


class TestMasterBrainReconciler(unittest.TestCase):
    """v949.x 🥷🧠 Phase C — THE MASTER-BRAIN RECONCILER (ENGINE_ARCHITECTURE.md 'MASTER
    BRAIN'; ARCH_PINGPONG_NINJA_ENGINE_ROOM.md §4 + §6-Q1/Q2 SETTLED). ca._kai_reconcile is
    the ONE pure fn; ca._kai_build_engine_frames materializes it (+ router/gate/funnel/
    second/kai layer detail) into the EngineFrame shape kai_report.json carries at seal;
    ca._kai_engine_frame_effective enforces the sealed-always-wins-over-live law."""

    # ── priority order: super > live named > kai-retro named > OCR-only ────────────
    def test_priority_super_beats_live_named_on_the_same_frame(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["read"],
                    "super": {"reread": True, "deepNames": ["Windforce"], "tier": "grail"}}]
        register = [{"name": "Windforce", "tier": "grail"}]
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Shael Rune"]}]
        out = ca._kai_reconcile(routing, register, sess)
        self.assertEqual(out[0]["owner"], "super")
        self.assertEqual(out[0]["verdict"], "grail")
        self.assertIn("Windforce", out[0]["why"])

    def test_priority_live_named_beats_kai_retro_named(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["read"]}]
        register = [{"name": "Windforce", "tier": None}]
        sess = [
            {"lane": "deep", "captureTs": 1000, "names": ["Windforce"]},
            {"lane": "kai", "frameId": "reel_S/a", "mode": "kai-judge",
             "kai": {"judge": {"name": "Windforce", "tier": "grail", "live": False, "tag": None}}},
        ]
        out = ca._kai_reconcile(routing, register, sess)
        self.assertEqual(out[0]["owner"], "live")

    def test_priority_kai_retro_named_beats_ocr_only(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["ocr"]}]
        register = [{"name": "Windforce", "tier": "grail"}]
        sess = [{"lane": "kai", "frameId": "reel_S/a", "mode": "kai-judge",
                 "kai": {"judge": {"name": "Windforce", "tier": "grail", "live": False, "tag": None}}}]
        out = ca._kai_reconcile(routing, register, sess)
        self.assertEqual(out[0]["owner"], "kai")
        self.assertEqual(out[0]["verdict"], "grail")

    def test_ocr_only_when_no_reader_named_anything(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["ocr"]}]
        out = ca._kai_reconcile(routing, [], [])
        self.assertEqual(out[0]["owner"], "ocr")
        self.assertEqual(out[0]["verdict"], "miss")

    def test_super_tag_judge_never_counted_as_kai_retro(self):
        # a super-analyze judge verdict (tag='super') landed in the journal but the row's
        # OWN .super field was (hypothetically) never stamped — must NOT be picked up as
        # a plain kai-retro named read; the layers are provenance-distinct.
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["judge"]}]
        register = [{"name": "Windforce", "tier": "grail"}]
        sess = [{"lane": "kai", "frameId": "reel_S/a", "mode": "kai-judge",
                 "kai": {"judge": {"name": "Windforce", "tier": "grail", "live": False, "tag": "super"}}}]
        out = ca._kai_reconcile(routing, register, sess)
        self.assertNotEqual(out[0]["owner"], "kai")   # never mistaken for a plain kai-retro read
        self.assertEqual(out[0]["verdict"], "miss")   # no owning layer named it — honest miss

    # ── DB-verification: live named requires a DB-verified name when register is real ──
    def test_live_named_requires_db_verification_when_register_present(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["read"]}]
        register = [{"name": "Windforce", "tier": None}]   # 'IA Lla' never made the register
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["IA Lla"]}]
        out = ca._kai_reconcile(routing, register, sess)
        self.assertNotEqual(out[0]["owner"], "live")

    def test_live_named_trusts_raw_name_when_register_empty_provisional_mode(self):
        # the _engine_driver live call never has a compiled register (too slow for a 2s
        # poll) — a nearby deep-read name is trusted as a GUESS, not gated on DB membership.
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["read"]}]
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Windforce"]}]
        out = ca._kai_reconcile(routing, [], sess)
        self.assertEqual(out[0]["owner"], "live")

    # ── never let a captured item die unread (tooltip frame, nothing owns it) ──────
    def test_tooltip_frame_with_zero_evidence_is_owner_none_verdict_miss(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": []}]
        out = ca._kai_reconcile(routing, [], [])
        self.assertIsNone(out[0]["owner"])
        self.assertEqual(out[0]["verdict"], "miss")

    # ── non-item frames (gameplay etc.) never carry a verdict ───────────────────────
    def test_gameplay_frame_owner_and_verdict_both_none(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "gameplay", "sources": []}]
        out = ca._kai_reconcile(routing, [], [])
        self.assertIsNone(out[0]["owner"])
        self.assertIsNone(out[0]["verdict"])

    # ── never let a thin funnel clobber a good tally (stash-* frames) ──────────────
    def test_stash_frame_owner_is_funnel_when_a_receipt_landed(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "stash-materials", "sources": ["grid"],
                    "routed": "kai-funnel"}]
        out = ca._kai_reconcile(routing, [], [])
        self.assertEqual(out[0]["owner"], "funnel")
        self.assertIsNone(out[0]["verdict"])   # a receipt landing is not a quality verdict

    def test_stash_frame_with_evidence_but_no_receipt_is_ocr_miss_not_a_fabricated_count(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "stash-runes", "sources": ["grid"],
                    "routed": None}]
        out = ca._kai_reconcile(routing, [], [])
        self.assertEqual(out[0]["owner"], "ocr")
        self.assertEqual(out[0]["verdict"], "miss")   # never-zero: a signal to re-fire

    # ── _kai_engine_frame_effective — the sealed-wins law ───────────────────────────
    def test_sealed_frame_always_wins_over_a_matching_live_guess(self):
        sealed = [{"f": "a.jpg", "owner": "kai", "verdict": "grail"}]
        live = [{"f": "a.jpg", "owner": "live", "verdict": None}]   # stale guess, same frame
        out = ca._kai_engine_frame_effective(sealed, live, kai_ver=3)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["owner"], "kai")
        self.assertTrue(out[0]["sealed"])

    def test_live_only_frame_kept_when_sealed_hasnt_covered_it_yet(self):
        sealed = [{"f": "a.jpg", "owner": "kai", "verdict": "grail"}]
        live = [{"f": "a.jpg", "owner": "live"}, {"f": "b.jpg", "owner": "live"}]
        out = ca._kai_engine_frame_effective(sealed, live, kai_ver=3)
        fs = {r["f"]: r for r in out}
        self.assertEqual(len(out), 2)
        self.assertFalse(fs["b.jpg"]["sealed"])

    def test_sealed_frames_discarded_entirely_below_kaiver_3(self):
        sealed = [{"f": "a.jpg", "owner": "kai", "verdict": "grail"}]
        live = [{"f": "a.jpg", "owner": "live"}]
        out = ca._kai_engine_frame_effective(sealed, live, kai_ver=2)
        self.assertEqual(len(out), 1)
        self.assertFalse(out[0]["sealed"])

    # ── _kai_build_engine_frames — the materialized EngineFrame shape ──────────────
    def test_build_engine_frames_shape_has_all_seven_layers_plus_owner_verdict(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": ["read", "ocr"],
                    "confidence": 2, "gatePass": True, "gateReason": "ok",
                    "gateSources": ["ocr", "read"], "routed": None, "route": None}]
        register = [{"name": "Windforce", "tier": None}]
        sess = [{"lane": "deep", "captureTs": 1000, "names": ["Windforce"]}]
        maps = ca._kai_engine_frame_maps(routing, register, sess)
        frames = ca._kai_build_engine_frames(routing, register, {}, maps)
        self.assertEqual(len(frames), 1)
        fr = frames[0]
        for key in ("live", "second", "kai", "super", "router", "gate", "funnel"):
            self.assertIn(key, fr["layers"])
        self.assertEqual(fr["owner"], "live")
        self.assertEqual(fr["layers"]["live"]["names"], ["Windforce"])
        self.assertEqual(fr["layers"]["gate"]["gatePass"], True)

    def test_build_engine_frames_never_materializes_presentation_strings(self):
        # LAW (Q1-hybrid): only semantic reconciliation is written at seal; no rendered
        # HTML/label text — layers carry raw names/flags/reasons only.
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": []}]
        frames = ca._kai_build_engine_frames(routing, [], {}, {})
        fr = frames[0]
        self.assertNotIn("html", fr)
        self.assertNotIn("presentation", fr)
        self.assertIsInstance(fr["layers"]["router"], dict)

    def test_build_engine_frames_super_layer_prefers_super_reads_arg_over_row_stamp(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": [],
                    "super": {"reread": True, "deepNames": ["stale"], "tier": None}}]
        super_reads = {"a.jpg": {"reread": True, "deepNames": ["Windforce"], "tier": "grail"}}
        frames = ca._kai_build_engine_frames(routing, [], super_reads, {})
        self.assertEqual(frames[0]["layers"]["super"]["deepNames"], ["Windforce"])

    def test_build_engine_frames_super_layer_falls_back_to_row_stamp(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": [],
                    "super": {"reread": True, "deepNames": ["Windforce"], "tier": "grail"}}]
        frames = ca._kai_build_engine_frames(routing, [], {}, {})   # empty super_reads dict
        self.assertEqual(frames[0]["layers"]["super"]["deepNames"], ["Windforce"])
        self.assertEqual(frames[0]["layers"]["super"]["state"], "reread")

    def test_build_engine_frames_kai_state_always_swept_post_seal(self):
        routing = [{"f": "a.jpg", "ts": 1000, "label": "tooltip", "sources": []}]
        frames = ca._kai_build_engine_frames(routing, [], {}, {})
        self.assertEqual(frames[0]["layers"]["kai"]["state"], "swept")

    # ── _kai_live_routing_row — the cheap live shape ────────────────────────────────
    def test_live_routing_row_tooltip_when_names_present(self):
        row = ca._kai_live_routing_row({"names": ["Windforce"], "scene": "ground",
                                        "captureTs": 5000, "frameId": "reel_S/f_5"})
        self.assertEqual(row["label"], "tooltip")
        self.assertEqual(row["ts"], 5000)
        self.assertEqual(row["f"], "f_5.jpg")

    def test_live_routing_row_stash_tally_tab(self):
        row = ca._kai_live_routing_row({"names": [], "scene": "stash", "stashTab": "runes",
                                        "captureTs": 5000, "frameId": "reel_S/f_5"})
        self.assertEqual(row["label"], "stash-runes")

    def test_live_routing_row_gameplay_when_nothing(self):
        row = ca._kai_live_routing_row({"names": [], "scene": "", "captureTs": 5000})
        self.assertEqual(row["label"], "gameplay")

    # ── the reconciler feeding straight off a live-shaped row (integration of the two
    #    pieces the provisional _engine_driver call actually chains together) ─────────
    def test_live_row_plus_reconcile_names_a_frame_end_to_end(self):
        rd = {"names": ["Windforce"], "scene": "ground", "captureTs": 5000,
              "frameId": "reel_S/f_5", "lane": "deep"}
        row = ca._kai_live_routing_row(rd)
        out = ca._kai_reconcile([row], [], [rd])
        self.assertEqual(out[0]["owner"], "live")

    # ── v948.26 🥷🧠 Phase D — the live-ring DEQUE ENTRY shape (what _engine_driver's 2s
    #    loop appends) surfaces owner/verdict/why to the NOW-CURSOR, never marked sealed ──
    def test_live_ring_deque_entry_carries_owner_verdict_and_is_never_sealed(self):
        # mirror the append _engine_driver does: live routing row → reconcile → ring entry
        rd = {"names": ["Windforce"], "scene": "ground", "captureTs": 5000,
              "frameId": "reel_S/f_5", "lane": "deep"}
        row = ca._kai_live_routing_row(rd)
        rec = {r["f"]: r for r in ca._kai_reconcile([row], [], [rd])}[row["f"]]
        entry = {"f": row["f"], "ts": row["ts"], "label": row["label"],
                 "owner": rec.get("owner"), "verdict": rec.get("verdict"),
                 "why": rec.get("why"), "sealed": False}
        self.assertEqual(entry["owner"], "live")
        self.assertFalse(entry["sealed"])       # provisional guess — sealed reel wins in retro
        self.assertIn("f_5.jpg", entry["f"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
