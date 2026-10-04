#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE CHARACTER BUILDER'S NODE STAND-IN — one DOM harness, cut from bible.html, run in node.

⚠ MOVED HERE VERBATIM from tv/test_the_character_builder_is_their_builder.py (#41 rank 16, REG-1561), because a
PRODUCTION lane now needs it: tooltip_oracle_lane runs the SHIPPED tooltip composition over their planner's oracle
on the console's own cadence, and a lane in his console must not import a test module to do its work. The builder
law and its nine sibling laws keep importing these names through that module (`import
test_the_character_builder_is_their_builder as CB` -> CB.NODE, CB._run, CB._src, CB._between, CB._db ...), which
re-exports them from here - ONE stand-in, never a copy. [[copy-drift]]

WHAT IT IS. `HARNESS` is a localStorage + document stand-in with spies on the vault and the mules; `_stage` cuts
the board pieces the builder stands on (the forked-name sets, the LSR door, CHARS, the backup collector) and
`_builder_js` / `_db_json` cut the ⟦CHARACTER BUILDER JS⟧ block and the generated ⟦CB_DB⟧ block, each between
its own anchors (`_between` refuses an anchor that is not unique). `_run(body)` runs all of it in ONE node
process and returns the JSON the body put in OUT.

⚠ NODE IS RESOLVED BY ENV, PATH, THEN THE KNOWN INSTALL LOCATIONS - not PATH alone. His console runs under
launchd with a bare PATH (the G5 lane sat dark for weeks on `shutil.which` for exactly that reason - see
tv/g5_grok_eyes.py), so a PATH-only lookup would read "node absent" on a Mac that has node. `NODE` is None when no
candidate is an executable file, and every caller treats None as UNKNOWN (a declared skip, never a pass).
"""
import io
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: where node lives on machines with a bare launchd/service PATH. Order: env override, PATH, then these.
NODE_KNOWN = (
    "/usr/local/bin/node", "/opt/homebrew/bin/node", "/opt/local/bin/node",
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "nodejs", "node.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "nodejs", "node.exe"),
)


def node_path(env=None):
    """The node binary, or None. -> str | None

    env override (TV_NODE) -> PATH (`node`, `nodejs`) -> NODE_KNOWN. A candidate counts only when it is an
    executable FILE; a directory or a dangling symlink is not node. None is the honest answer and the callers say
    "node absent" as UNKNOWN - never 0 rows, never a pass.
    """
    env = os.environ if env is None else env
    cands = []
    ov = str(env.get("TV_NODE") or "").strip()
    if ov:
        cands.append(ov)
    for n in ("node", "nodejs"):
        w = shutil.which(n, path=env.get("PATH"))
        if w:
            cands.append(w)
    cands.extend(NODE_KNOWN)
    for c in cands:
        try:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        except Exception:
            continue
    return None


NODE = node_path()
BIBLE = os.path.join(ROOT, "bible.html")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _between(s, start, end):
    assert s.count(start) == 1, "the cut start %r is not unique (%d) — the anchor moved" % (start[:60], s.count(start))
    i = s.index(start) + len(start)
    j = s.index(end, i)
    return s[i:j]


def _builder_js(s):
    return _between(s, '<script id="cb-builder-js">', "\n</script>")


def _stash_tab_js(s):
    """The one tab-row function. It lives in the vault span, which this harness does not load.
    The page assigns window._stabHtml after window exists; the same order is required here,
    because a var window later in the harness would hide an earlier assignment."""
    return _between(s, "/* ⟦STASH TABS⟧ */", "/* ⟦/STASH TABS⟧ */")


def _builder_css(s):
    return _between(s, '<style id="cb-builder-css">', "\n</style>")


def _db_json(s):
    return _between(s, '<script type="application/json" id="cb-db">', "</script>")


def _stage(s):
    """the board pieces the builder stands on, each cut between its own boundaries"""
    lp = "window._LP_FORKED = new Set([" + _between(s, "window._LP_FORKED = new Set([", "]);") + "]);\n"
    # the statement ends at its own ']));' (a comment follows on the line) - the old ');\n' marker ran on into LSR
    # and parsed by luck until LSR gained a '});' (v3525), which ended the cut mid-function
    wp = "window._WP_FORKED = new Set(" + _between(s, "window._WP_FORKED = new Set(", "]));") + "]));\n"
    lsr = "window.LSR = (function(){" + _between(s, "window.LSR = (function(){", "\n})();") + "\n})();\n"
    chars = "const CHARS = {" + _between(s, "const CHARS = {", "\n};\n") + "\n};\n"
    backup = "function _collectProgress(){" + _between(s, "function _collectProgress(){", "\nfunction _progressSnapshot(){") + "\n"
    return lp, wp, lsr, chars, backup


HARNESS = r"""
var RAW = {}, READS = [], CALLS = [], LISTEN = [];
var localStorage = {
  getItem: function(k){ READS.push(k); return Object.prototype.hasOwnProperty.call(RAW, k) ? RAW[k] : null; },
  setItem: function(k, v){ RAW[k] = String(v); }, removeItem: function(k){ delete RAW[k]; },
  key: function(i){ return Object.keys(RAW)[i] == null ? null : Object.keys(RAW)[i]; }
};
Object.defineProperty(localStorage, 'length', { get: function(){ return Object.keys(RAW).length; } });
var window = globalThis;
window.localStorage = localStorage;
window._D2R_OWNER = true; window.D2R_PROFILE = 'main'; window._D2R_LPFX = 'L·'; window._D2R_PFX = 'W·';
window._D2R_INSTALL = 'test';
/* the vault and the mules, as spies: the builder must never touch them */
['vaultAssign', 'openMuleCard', 'tvVaultRegister', '_muleLoad', 'vaultCloseCard', 'muleById'].forEach(function(n){
  window[n] = function(){ CALLS.push(n); };
});
/* his real stores are there, full: reading any of them is the defect */
RAW['d2r_muleAssign'] = '{"Harlequin Crest (Shako)":"m1"}'; RAW['d2r_owned'] = '["Harlequin Crest"]';
RAW['d2r_muleEquip'] = '{}'; RAW['d2r_muleRoster'] = '[]'; RAW['d2r_foundLog'] = '[]';
function Cls(){ var c = {}; return { add: function(x){ c[x] = 1; }, remove: function(x){ delete c[x]; },
  contains: function(x){ return !!c[x]; }, toggle: function(x, on){ if (on === undefined) on = !c[x]; if (on) c[x] = 1; else delete c[x]; return on; } }; }
function El(id){ this.id = id || ''; this.hidden = false; this.attrs = {}; this._html = ''; this.style = {}; this.classList = Cls();
  this.scrollTop = 0; this.children = []; this.textContent = ''; }
El.prototype.setAttribute = function(k, v){ this.attrs[k] = String(v); if (k === 'id') this.id = String(v); };
El.prototype.getAttribute = function(k){ return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; };
El.prototype.querySelector = function(){ return null; };
El.prototype.querySelectorAll = function(){ return []; };
El.prototype.getBoundingClientRect = function(){ return { left: 0, top: 0, width: 100, height: 40, right: 100, bottom: 40 }; };
El.prototype.appendChild = function(c){ this.children.push(c); if (c.id) ELS[c.id] = c; return c; };
El.prototype.focus = function(){};
Object.defineProperty(El.prototype, 'innerHTML', { get: function(){ return this._html; }, set: function(v){ this._html = String(v); } });
var ELS = {}, MODAL = new El('cb-modal');
var DBEL = new El('cb-db'); DBEL.textContent = __DB__;
var document = {
  body: new El('body'), documentElement: new El('html'), activeElement: null,
  getElementById: function(id){
    if (id === 'cb-db') return DBEL;
    if (id === 'cb-modal') return (ELS['cb-win'] && ELS['cb-win']._html.indexOf('id="cb-modal"') >= 0) ? MODAL : null;
    return ELS[id] || null;
  },
  createElement: function(){ return new El(''); },
  querySelector: function(){ return null; }, querySelectorAll: function(){ return []; },
  addEventListener: function(t, f, cap){ LISTEN.push([t, f, !!cap]); }
};
document.body.appendChild = function(c){ if (c.id) ELS[c.id] = c; return c; };
window.document = document;
window.addEventListener = function(){};
window.innerWidth = 2000; window.innerHeight = 1300;
function artOr(n){ return '<span class="d2art-wrap">' + n + '</span>'; }
function key(k){ var fired = []; LISTEN.forEach(function(l){ if (l[0] === 'keydown' && l[2]) l[1]({ key: k, preventDefault: function(){}, stopImmediatePropagation: function(){ fired.push('stopped'); } }); }); return fired; }
function slots(){ var b = JSON.parse(RAW['d2r_charBuilds'] || '{}'); var k = Object.keys(b)[0]; return k ? b[k] : null; }
"""


def _run(body, db=None):
    s = _src()
    lp, wp, lsr, chars, backup = _stage(s)
    prog = (HARNESS.replace("__DB__", json.dumps(db if db is not None else _db_json(s)))
            + _stash_tab_js(s)
            + lp + wp + lsr + chars + backup + _builder_js(s) + "\n;(function(){ var OUT = {};\n" + body
            + "\nprocess.stdout.write(JSON.stringify(OUT)); })();\n")
    r = subprocess.run([NODE, "-"], input=prog, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    if r.returncode != 0:
        raise AssertionError("node failed: " + (r.stderr or r.stdout)[-2000:])
    return json.loads(r.stdout)


def _db():
    return json.loads(_db_json(_src()))
