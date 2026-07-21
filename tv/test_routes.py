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
        # vault personal/shared can legitimately total 0 — never-zero applies to tally tabs only
        job = {"key": "vault_personal", "tab": "personal", "fid": "v1", "tries": 0}
        act, _ = ca._drv_empty_refire_plan(job, {"ok": True, "total": 0}, "v2")
        self.assertEqual(act, "done")


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
        # every row carries the full contract, no missing keys
        for r in led:
            self.assertEqual(set(r), {"f", "ts", "label", "sources", "confidence",
                                      "voteCount", "route", "routed", "skipReason"})

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
        # floor TTL is 5s — advance past until
        ca._intake_lease_claim("runes", "board", ttl_ms=5_000, now_ms=4_000_000)
        c = ca._intake_lease_claim("runes", "engine-driver", ttl_ms=60_000, now_ms=4_006_000)
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
