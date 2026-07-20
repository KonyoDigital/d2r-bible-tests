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

    def test_tab_word_precedence_runes_over_gems(self):
        # blob carries a stash word + both tab words → runes is checked first.
        self.assertEqual(ca._kai_frame_cls(["Personal Stash", "Runes Gems"], False), "stash-runes")

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

    def test_template_has_six_placeholders(self):
        self.assertEqual(self._template().count("%s"), 6)

    def test_node_dry_run_syntax_and_return_zero(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not on PATH")
        tmpl = self._template()
        import json as _j
        js = tmpl % (_j.dumps("runes"), _j.dumps("runes"), _j.dumps("runes"),
                     _j.dumps("/hist/reel_x/f.jpg"), _j.dumps("runes"), _j.dumps("reel_x/f"))
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
    route condition so the two consumers of _kai_fullnames stay correctly divergent."""

    @staticmethod
    def _gate(name, tier):
        low = name.lower()
        if name and low in ca._kai_fullnames() and low not in ca._kai_rarenames() \
                and tier in ("toss", "border"):
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
        # 🔵 verify by frameId base (strip '#v')
        self.assertEqual(d["verify"], {"conf": 0.9, "confirm": 1, "corrected": 0, "missed": 0})
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
        self.scan = [
            {"f": "f_100.jpg", "ts": 100000, "ocr": True,  "journal": True,  "label": "stash-runes"},
            {"f": "f_200.jpg", "ts": 200000, "ocr": True,  "journal": False, "label": "tooltip"},
            {"f": "f_300.jpg", "ts": 300000, "ocr": False, "journal": False, "label": "gameplay"},
            {"f": "f_400.jpg", "ts": 400000, "ocr": True,  "journal": False, "label": "stash-gems"},
            {"f": "f_500.jpg", "ts": 500000, "ocr": True,  "journal": True,  "label": "stash-materials"},
            {"f": "f_600.jpg", "ts": 600000, "ocr": True,  "journal": True,  "label": "inventory"},
        ]
        self.sess = [
            {"lane": "deep", "ts": 100000, "names": ["El"]},                        # named read → 'read' near 100k
            {"lane": "intake", "frameId": "reel_S/f_100",
             "intake": {"tab": "runes", "ok": True, "kind": "kai-funnel"}},         # funnel fired on f_100
            {"lane": "intake", "frameId": "",
             "intake": {"tab": "materials", "ok": True, "kind": "tally"}},          # materials receipted normally
        ]
        self.journal = self.sess + [
            {"lane": "kai", "mode": "kai-judge", "frameId": "reel_S/f_200",
             "kai": {"judge": {"name": "Windforce", "tier": "toss"}}},              # judge verdict on f_200
        ]
        self.led = {r["f"]: r for r in ca._kai_build_routing(self.scan, self.sess, "S", self.journal)}

    def test_funnel_routed_frame(self):
        r = self.led["f_100.jpg"]
        self.assertEqual(sorted(r["sources"]), ["journal", "ocr", "read"])   # 3 brains agree
        self.assertEqual(r["confidence"], 3)
        self.assertEqual(r["route"], "tally:runes")
        self.assertEqual(r["routed"], "kai-funnel")
        self.assertIsNone(r["skipReason"])

    def test_judge_routed_frame(self):
        r = self.led["f_200.jpg"]
        self.assertEqual(sorted(r["sources"]), ["judge", "ocr"])            # read is >4s away
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
        # inventory routes to vault, which the closer never fires this stage
        v = self.led["f_600.jpg"]
        self.assertEqual((v["route"], v["routed"], v["skipReason"]),
                         ("vault", None, "no-vault-fire"))

    def test_routed_count_and_shape(self):
        led = ca._kai_build_routing(self.scan, self.sess, "S", self.journal)
        self.assertEqual(len(led), 6)
        self.assertEqual(sum(1 for r in led if r["routed"]), 2)             # f_100 + f_200 fired
        # every row carries the full contract, no missing keys
        for r in led:
            self.assertEqual(set(r), {"f", "ts", "label", "sources", "confidence",
                                      "route", "routed", "skipReason"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
