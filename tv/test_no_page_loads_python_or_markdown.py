# -*- coding: utf-8 -*-
"""REG-2444 (#147 R1) - NO PAGE LOADS A .py OR A .md FILE.

A browser law's Chrome reads files no audit hook sees (REG-2443: its run is attested, C, never traced). A key for such a
run can name the pages it loads only if the pages load nothing but the web files themselves: if a page could
`fetch('notes.md')` or `<script src="tv/x.py">`, a python or markdown edit would change what the browser rendered while
no key of the run moved. So no TRACKED .html / .htm / .js / .mjs / .cjs / .css file names a .py or a .md in
  src= (any element), <link href=> whose rel loads it (stylesheet, preload, modulepreload, import, prefetch, icon,
  apple-touch-icon, manifest), url(), import() and a static import,
  @import, new Worker() / new SharedWorker(), importScripts(), navigator.serviceWorker.register(), or fetch().
A query string or a fragment does not hide one (x.py?v=2). A link a person clicks (<a href="README.md">) is not a load.
FLOOR, said: a path the page BUILDS at run time (fetch(base + name)) is not a literal and is not read here.

THE LIST IS THE LAW'S OWN BYTES (PAGES), never a listing made while it runs: a law that lists a directory cannot be
keyed (heart2 law_inputs), and a tracked-file list fetched by a subprocess is invisible to the key, so the key would be
under-wide. PAGES is held to `git ls-files` instead: a new tracked page that is not in PAGES fails here, naming the line
to add - and adding it changes this file, which moves the key. In a tree git cannot answer for, that one case is
UNKNOWN and says so; the scanner's own cases run everywhere.
RED_PROOF below.
"""
import io
import os
import re
import shutil
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

#: every tracked web file, by name. A new one is added HERE (the completeness case names it).
PAGES = (
    "H_sweep.js", "J_screens.js", "K_perf.js", "L_integrity.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/bible.bffef6a30c.css",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-00.2d09d09364.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-01.4140e03834.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-02.1a35fb99a2.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-03.32ebcfb130.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-04.4115e8d20f.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-05.a49fdddcba.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-06.9441b6ec1f.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-07.03b7098427.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-08.6a31198505.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-09.e3450adba5.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-10.c19e2319e1.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-11.26d3b7e0af.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-12.7b3419df11.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-13.8ebe87076a.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-14.88f61c087a.js",
    "_archive/phase_z_20260715/assets/z/3527b03a86/chunk-15.0c3e734f86.js",
    "_archive/phase_z_20260715/assets/z/sw.js", "_archive/phase_z_20260715/bible.monolith.html",
    "_archive/phase_z_20260715/sw.js", "_archive/v44_orphan_20260714/sw.js",
    "_archive/v44_orphan_20260714/v44-upgrade.css", "_archive/v44_orphan_20260714/v44-upgrade.js",
    "backups/bible_pre_richtip_20260608_224721.html",
    "backups/desktop_wip_binds_restructure_PLUS_v172_2026-06-11.html", "bible.html", "bible_routes.html",
    "end_to_end_audit.js", "functions/_middleware.js", "functions/api/ask.js", "functions/api/console.js",
    "functions/api/d2jsp_quote.js", "functions/api/hello.js", "functions/api/intake.js", "functions/api/roster.js",
    "functions/api/tz.js", "functions/console.js", "functions/d2r/api/d2jsp_quote.js", "functions/d2r/api/tz.js",
    "functions/visits.js", "offline1735.mjs", "routine_status.js", "tv/control_ui.html",
    "tv/debug/tz_rotation_probe.mjs", "tv/demo_console.mjs", "tv/gate_trace/node_trace.cjs",
    "tv/intake_grok_sub.mjs", "tv/intake_local.mjs", "tv/pc_settings.mjs", "v32_init_timing.js", "v32_replicate_audit.js", "v32_smoke.js",
    "v32_smoke2.js", "v33_smoke.js", "v34_debug.js", "v34_smoke.js", "v35_apostrophe_test.js", "v35_full.js",
    "v35_smoke.js", "v36_test.js", "v38_picks_check.js", "v39_dom_probe.js", "v39_polish_check.js",
    "v39_polish_check2.js", "v39_pulse_debug.js", "v40_content_check.js", "v40_debug.js",
    "v40_uniqueness_recheck.js", "v41_polish_check.js", "v41_quick_recheck.js", "v41_widget_verify.js",
)
#: what makes a tracked file a web file
WEB_SPECS = ("*.html", "*.htm", "*.js", "*.mjs", "*.cjs", "*.css")

_Q = r"""(?:"([^"]*)"|'([^']*)'|`([^`]*)`)"""
_ATTR = r"""\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))"""
_SRC = re.compile(r"\bsrc" + _ATTR, re.I)
_LINK = re.compile(r"<link\b[^>]*>", re.I)
_REL = re.compile(r"\brel" + _ATTR, re.I)
_HREF = re.compile(r"\bhref" + _ATTR, re.I)
_LOAD_RELS = ("stylesheet", "preload", "modulepreload", "import", "prefetch", "icon", "apple-touch-icon", "manifest")
_CALL = re.compile(r"\b(url|import|fetch|importScripts)\s*\(\s*(?:" + _Q[3:-1] + r"|([^)'\"`\s]+))", re.I)
_WORKER = re.compile(r"\bnew\s+(?:Shared)?Worker\s*\(\s*" + _Q)
_CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?" + _Q, re.I)
_STATIC_IMPORT = re.compile(r"(?<![@.\w])import\s+(?:[\w*{}\s,$]+?\s+from\s+)?" + _Q)  # not CSS @import
_SERVICE_WORKER = re.compile(r"serviceWorker\.register\s*\(\s*" + _Q)
_PY_OR_MD = re.compile(r"\.(py|md)$", re.I)


def _first(m, start=0):
    return next((g for g in m.groups()[start:] if g is not None), "")


def _names_py_or_md(ref):
    """A reference names a .py or a .md file, whatever query string or fragment follows it. -> bool"""
    return bool(_PY_OR_MD.search(ref.split("?")[0].split("#")[0].strip()))


def loads(text):
    """Every way `text` makes a browser load a .py or a .md. -> [(how, reference)]"""
    found = []
    for m in _SRC.finditer(text):
        found.append(("src=", _first(m)))
    for tag in _LINK.finditer(text):
        rel, href = _REL.search(tag.group(0)), _HREF.search(tag.group(0))
        if rel and href and any(r in _first(rel).lower().split() for r in _LOAD_RELS):
            found.append(("<link rel=%s>" % _first(rel), _first(href)))
    for m in _CALL.finditer(text):
        found.append(("%s()" % m.group(1), _first(m, 1)))
    for m in _WORKER.finditer(text):
        found.append(("new Worker()", _first(m)))
    for m in _CSS_IMPORT.finditer(text):
        found.append(("@import", _first(m)))
    for m in _STATIC_IMPORT.finditer(text):
        found.append(("import", _first(m)))
    for m in _SERVICE_WORKER.finditer(text):
        found.append(("serviceWorker.register()", _first(m)))
    return [(how, ref) for how, ref in found if _names_py_or_md(ref)]


def missing_from(pages, tracked):
    """(tracked web files PAGES lacks, PAGES entries git does not track). -> (sorted list, sorted list)"""
    return sorted(set(tracked) - set(pages)), sorted(set(pages) - set(tracked))


def tracked_pages():
    """The tracked web files, by git's index (GIT_* removed: a hook's GIT_DIR names another tree). -> list | None"""
    if not shutil.which("git"):
        return None
    env = dict((k, v) for k, v in os.environ.items() if not str(k).upper().startswith("GIT_"))
    try:
        proc = subprocess.run(["git", "-C", REPO, "ls-files", "-z", "--"] + list(WEB_SPECS), env=env,
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]


class TheScannerFindsEveryWayAPageLoadsAFile(unittest.TestCase):
    def _found(self, text):
        return [ref for _how, ref in loads(text)]

    def test_a_script_src_is_found(self):
        self.assertEqual(self._found('<script src="tv/x.py"></script>'), ["tv/x.py"])
        self.assertEqual(self._found("<img src='notes.md'>"), ["notes.md"])

    def test_a_stylesheet_preload_or_import_link_is_found(self):
        self.assertEqual(self._found('<link rel="stylesheet" href="a.md">'), ["a.md"])
        self.assertEqual(self._found('<link href="b.py" rel="preload" as="script">'), ["b.py"])
        self.assertEqual(self._found("<link rel=modulepreload href=c.py>"), ["c.py"])
        self.assertEqual(self._found('<link rel="import" href="d.md">'), ["d.md"])
        self.assertEqual(self._found('<link rel="shortcut icon" href="favicon.py">'), ["favicon.py"])

    def test_url_import_fetch_and_workers_are_found(self):
        self.assertEqual(self._found(".x { background: url('e.md') }"), ["e.md"])
        self.assertEqual(self._found(".y { background: url(f.py) }"), ["f.py"])
        self.assertEqual(self._found("const m = await import('./g.py');"), ["./g.py"])
        self.assertEqual(self._found("import h from './h.md';"), ["./h.md"])
        self.assertEqual(self._found('@import "i.md";'), ["i.md"])
        self.assertEqual(self._found("fetch(`/j.md`).then(r => r.text())"), ["/j.md"])
        self.assertEqual(self._found("new Worker('k.py')"), ["k.py"])
        self.assertEqual(self._found("importScripts('l.py')"), ["l.py"])
        self.assertEqual(self._found("navigator.serviceWorker.register('m.py')"), ["m.py"])

    def test_a_query_string_or_a_fragment_does_not_hide_one(self):
        self.assertEqual(self._found('<script src="x.py?v=3"></script>'), ["x.py?v=3"])
        self.assertEqual(self._found("fetch('notes.md#top')"), ["notes.md#top"])

    def test_what_is_not_a_load_is_not_found(self):
        self.assertEqual(self._found('<a href="README.md">the readme</a>'), [], "a link a person clicks is a load")
        self.assertEqual(self._found('<link rel="help" href="README.md"><link rel="canonical" href="x.md">'), [],
                         "a <link> whose rel loads nothing is a load")
        self.assertEqual(self._found('<script src="app.js"></script> <img src="x.png">'), [])
        self.assertEqual(self._found("fetch('/api/x'); // see tv/heart2.py"), [], "prose that names a .py is a load")


class NoTrackedPageLoadsPythonOrMarkdown(unittest.TestCase):
    def test_no_page_names_a_py_or_md_load(self):
        offenders, scanned = [], 0
        for rel in PAGES:
            full = os.path.join(REPO, *rel.split("/"))
            if not os.path.isfile(full):
                continue  # a partial copy of the tree (a heart2 sandbox carries tv/ and bible.html): absent, not clean
            scanned += 1
            with io.open(full, encoding="utf-8", errors="replace") as fh:
                for how, ref in loads(fh.read()):
                    offenders.append("%s: %s %s" % (rel, how, ref))
        self.assertGreater(scanned, 0, "no page was scanned at all - a law that reads nothing is not a pass")
        self.assertEqual(offenders, [], "a page loads a .py or a .md - a browser key cannot name it:\n  "
                         + "\n  ".join(offenders))

    def test_pages_is_every_tracked_page(self):
        tracked = tracked_pages()
        if tracked is None:
            self.skipTest("git could not list the tracked pages here - whether PAGES is complete is UNKNOWN, "
                          "not complete")
        lacks, extra = missing_from(PAGES, tracked)
        self.assertEqual(lacks, [], "tracked web file(s) missing from PAGES in tv/test_no_page_loads_python_or_"
                                    "markdown.py - add them there (the key reads that list): %s" % lacks)
        self.assertEqual(extra, [], "PAGES names file(s) git no longer tracks - remove them: %s" % extra)

    def test_the_completeness_rule_names_both_directions(self):
        self.assertEqual(missing_from(("a.js",), ["a.js", "b.css"]), (["b.css"], []))
        self.assertEqual(missing_from(("a.js", "gone.js"), ["a.js"]), ([], ["gone.js"]))


RED_PROOF = [
    {"why": "the scanner skips src=", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "_SRC = re.compile(r\"\\bsrc\" + _ATTR, re.I)\n",
     "replace": "_SRC = re.compile(r\"(?!x)x\" + _ATTR, re.I)\n", "matches": 1},
    {"why": "the scanner skips a stylesheet link", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "_LOAD_RELS = (\"stylesheet\", \"preload\", \"modulepreload\", \"import\", \"prefetch\", \"icon\", "
             "\"apple-touch-icon\", \"manifest\")\n",
     "replace": "_LOAD_RELS = (\"preload\", \"modulepreload\", \"import\", \"prefetch\", \"icon\", "
                "\"apple-touch-icon\", \"manifest\")\n", "matches": 1},
    {"why": "the scanner skips url()", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "_CALL = re.compile(r\"\\b(url|import|fetch|importScripts)\\s*\\(",
     "replace": "_CALL = re.compile(r\"\\b(import|fetch|importScripts)\\s*\\(", "matches": 1},
    {"why": "the scanner skips fetch()", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "_CALL = re.compile(r\"\\b(url|import|fetch|importScripts)\\s*\\(",
     "replace": "_CALL = re.compile(r\"\\b(url|import|importScripts)\\s*\\(", "matches": 1},
    {"why": "the scanner skips new Worker()", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "_WORKER = re.compile(r\"\\bnew\\s+(?:Shared)?Worker\\s*\\(\\s*\" + _Q)\n",
     "replace": "_WORKER = re.compile(r\"(?!x)x\" + _Q)\n", "matches": 1},
    {"why": "a query string hides a load", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "    return bool(_PY_OR_MD.search(ref.split(\"?\")[0].split(\"#\")[0].strip()))\n",
     "replace": "    return bool(_PY_OR_MD.search(ref.strip()))\n", "matches": 1},
    {"why": "a <link> whose rel loads nothing is read as a load", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "        if rel and href and any(r in _first(rel).lower().split() for r in _LOAD_RELS):\n",
     "replace": "        if href:\n", "matches": 1},
    {"why": "the completeness rule forgets a new tracked page", "file": "test_no_page_loads_python_or_markdown.py",
     "find": "    return sorted(set(tracked) - set(pages)), sorted(set(pages) - set(tracked))\n",
     "replace": "    return [], sorted(set(pages) - set(tracked))\n", "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=1)
