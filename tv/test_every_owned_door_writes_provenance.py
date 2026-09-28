# -*- coding: utf-8 -*-
"""EVERY DOOR INTO `owned` SAYS WHO FILED IT — and the live route files what he HOLDS. Driven on the shipped
board code (cut from bible.html by its markers, run in node), never re-typed.

His words, 2026-09-28: "where is the ledger proof of these two items? i cant find it.. how can i see the evidence
and picture pixels from the session it was extracted from", "its correct btw.. just want to see it and see how its
read so we can surgically fix", "make sure the others have the same logic too", "fix the route so they flow
correctly", and his ruling the same day (HANDOFF §28): a CHRONICLE-PAGE read is found-ever, NOT the vault.

MEASURED on a copy of his store (read-only): owned = [Plague, Grief] with NO d2r_vaultProv row for either — the
trail lived only in d2r_chronicleInboxLog (aic-judge, one session, two frames). The door that owned them
(aicJudgeApply's keep tier) wrote no provenance, and neither did its siblings (22 bare `owned.add(` sites). And the
live register wrote String of Ears — read WORN — only to the found list: kaiChroniclePropose returned from its
"already in the Chronicle" branch before the vault was ever asked.

WHAT THIS LAW HOLDS:
  · THE CENSUS — every `owned.add(` in CODE (a JS scanner: comments, strings, templates and regex literals are
    not code) sits inside the ⟦OWNED PROV⟧ door, except the two NAMED vaultFile sites, each with its reason.
  · THE DOOR — window._ownedAdd writes a kind:'owned' RECEIPT (source, when, session, frame, place, scene, look);
    it never clobbers a filing row (the §24 rebuild's tier / successes / trials stay); a standing receipt only
    fills what it lacks and adds a NEW look to its tally; no source → no row (never invented); a store that will
    not parse is never written over.
  · THE ROUTE — worn / stash / cube / mule files into the dock; a Chronicle page never does, even with a place on
    it; the floor never; inventory alone is holding, not owning (his v2346 ruling); an UNKNOWN place waits.
  · THE BACKFILL — on a fixture store shaped like his: Grief and Plague gain their receipts from their own
    aic-judge rows; String of Ears (worn) is filed with a receipt; the seven Chronicle-page reads, the floor
    read, the unknown one, a dismissed one and one still waiting for his ruling are NOT; a second run is a
    no-op (idempotent); the undo takes back exactly what it did, through the removal door.
  · A RECEIPT IS NEVER A WITNESS — the sorter files nothing on it and the W6 prune keeps no filing on it.
  · THE EVIDENCE PANEL — who / when / session / frame / tally from the store; an item with no provenance says
    so in words; a picture that loads is shown, one that does not is said in words (the console's reason, or
    UNKNOWN) and never drawn as an <img>.
  · THE JOINS — the settled branch of kaiChroniclePropose asks the route before it returns, and aicJudgeApply's
    runeword keep writes its receipt through the door.
RED_PROOF below.
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
if HERE not in sys.path:
    sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

NODE = shutil.which("node")
BIBLE = os.path.join(ROOT, "bible.html")
BEGIN, END = "⟦OWNED PROV BEGIN⟧", "⟦OWNED PROV END⟧"
EV_BEGIN, EV_END = "⟦VAULT EVIDENCE LINE BEGIN⟧", "⟦VAULT EVIDENCE LINE END⟧"
LANES_HEAD = "  window._VAULT_LANES = ["
MAY_HEAD = "  window._vaultMayClaim = function(loc){\n"
REC_FROM = "      var _w0 = (witness && typeof witness === 'object' && !Array.isArray(witness)) ? witness : {};\n"
REC_TO = "      /* v2018 — REG-349: ASK THE PLANNER ABOUT THE ITEM"
SORT_FROM = "    var _pvS = _provAll();\n"
SORT_TO = "    /* the throw-out ADVICE is still computed for the dock"
W6_FROM = "    var _pvW6 = _provAll();\n"
W6_TO = "    // v360 — shared-stash items"
WIT_FROM = "  function _provAsWitness(row){\n"
WIT_TO = "  window._vaultProvAsWitness = _provAsWitness;\n"

#: the ONLY bare `owned.add(` allowed outside the door, each with its reason
NAMED = {
    "try { if (!owned.has(nm)){ owned.add(nm); persistOwned(); } } catch (e) {}":
        (2, "window.vaultFile — the rebuild and the filing branch. The FILING ROW written two lines above IS the "
            "provenance (source, at, frame, looks, gate, tier), and it is richer than any receipt; routing this add "
            "through the door would only stamp an ownedBy note that says the same thing again."),
}


def _src():
    with io.open(BIBLE, encoding="utf-8") as fh:
        return fh.read()


def _marked(s, a, b):
    assert s.count(a) == 1 and s.count(b) == 1, "markers %r / %r are not unique (%d, %d)" % (a, b, s.count(a), s.count(b))
    i = s.rfind("\n", 0, s.index(a)) + 1
    j = s.index("\n", s.index(b)) + 1
    return s[i:j]


def _between(s, a, b, include_b=False):
    assert s.count(a) == 1, "anchor %r matched %d times" % (a[:60], s.count(a))
    i = s.index(a)
    j = s.index(b, i)
    return s[i:j + (len(b) if include_b else 0)]


def owned_prov_region(s=None):
    """The ⟦OWNED PROV⟧ door, cut whole — for every law that drives a door which now calls window._ownedAdd."""
    return _marked(s if s is not None else _src(), BEGIN, END)


def _lanes(s):
    """The ONE vault predicate, cut from the board — the route asks it, so the law must too."""
    head = _between(s, LANES_HEAD, "\n", include_b=True)
    assert s.count(MAY_HEAD) == 1, "the vault predicate is not where this law cuts it"
    i = s.index(MAY_HEAD)
    return head + s[i:s.index("\n  };\n", i) + len("\n  };\n")]


# ── the JS census: which `owned.add(` occurrences are CODE ────────────────────────────────────────────
_REGEX_PREV = set("(,=:[!&|?{};+-*%<>~^")
_REGEX_KW = ("return", "typeof", "case", "in", "of", "delete", "void", "throw", "new", "else", "do")
PAT = re.compile(r"\bowned\s*(?:\.\s*add|\[\s*['\"]add['\"]\s*\])\s*\(")


def code_mask(src, keep_strings=False):
    """For each character: 1 when it is JavaScript CODE inside a <script> block — not a comment, string,
    template text, regex literal or HTML. ⚠ A regex literal with a backtick (/[‘’`]/g — this file has several)
    flipped a naive scanner into template mode for 2,300 lines and hid real sites; the regex and ${ } handling
    below are what make the count honest, and test_the_scanner_sees_every_site_the_old_board_had pins that."""
    mask = bytearray(len(src))
    i, n = 0, len(src)
    in_script, stack, mode, depth, last_sig, last_word = False, [], "code", 0, "", ""
    while i < n:
        if not in_script:
            k = src.find("<script", i)
            if k < 0:
                break
            e = src.find(">", k)
            if e < 0:
                break
            i, in_script = e + 1, True
            mode, stack, depth, last_sig, last_word = "code", [], 0, "", ""
            continue
        if mode == "tmpl":
            c = src[i]
            if c == "\\":
                i += 2
                continue
            if c == "`":
                mode, last_sig = "code", "`"
                i += 1
                continue
            if src.startswith("${", i):
                stack.append(depth)
                depth, mode, last_sig = 0, "code", "{"
                i += 2
                continue
            i += 1
            continue
        if src.startswith("</script", i):
            in_script = False
            i += 1
            continue
        c, two = src[i], src[i:i + 2]
        if two == "/*":
            e = src.find("*/", i + 2)
            i = n if e < 0 else e + 2
            continue
        if two == "//":
            e = src.find("\n", i)
            i = n if e < 0 else e
            continue
        if c in ("'", '"'):
            j = i + 1
            while j < n and src[j] != c and src[j] != "\n":
                j += 2 if src[j] == "\\" else 1
            if keep_strings:
                for q in range(i, min(j + 1, n)):
                    mask[q] = 1
            i, last_sig = j + 1, c
            continue
        if c == "`":
            mode = "tmpl"
            i += 1
            continue
        if c == "/" and (last_sig == "" or last_sig in _REGEX_PREV or last_word in _REGEX_KW):
            j, cls = i + 1, False
            while j < n and src[j] != "\n":
                ch = src[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    cls = True
                elif ch == "]":
                    cls = False
                elif ch == "/" and not cls:
                    break
                j += 1
            i = j + 1
            while i < n and src[i].isalpha():
                i += 1
            last_sig = "/"
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            if depth == 0 and stack:
                depth, mode = stack.pop(), "tmpl"
                i += 1
                continue
            depth -= 1
        mask[i] = 1
        if not c.isspace():
            if c.isalnum() or c in "_$":
                j = i
                while j < n and (src[j].isalnum() or src[j] in "_$"):
                    mask[j] = 1
                    j += 1
                last_word, last_sig, i = src[i:j], "a", j
                continue
            last_sig, last_word = c, ""
        i += 1
    return mask


def code_sites(src):
    mask = code_mask(src)
    out = []
    for m in PAT.finditer(src):
        if mask[m.start()]:
            ls = src.rfind("\n", 0, m.start()) + 1
            out.append((src.count("\n", 0, m.start()) + 1, m.start(), src[ls:src.find("\n", m.start())].strip()))
    return out


HARNESS = r"""
var window = globalThis, STORE = {}, REG = [], RECORDS = [], REMOVED = [], FILED = [], FETCHES = [], LOGS = [];
window.LSR = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(STORE, k) ? STORE[k] : null; },
  setItem: function(k, v){ STORE[k] = String(v); },
  removeItem: function(k){ delete STORE[k]; } };
window.D2R_BUILD = { id: 'vTEST' };
console.info = function(){ LOGS.push(Array.prototype.join.call(arguments, ' ')); };
var owned = new Set();
function esc(t){ return String(t == null ? '' : t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function jsArg(t){ return String(t).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }
function _provAll(){ try { var v = JSON.parse(window.LSR.getItem('d2r_vaultProv') || '{}'); return v || {}; } catch (e) { return {}; } }
%(lanes)s
%(region)s
%(evidence)s
window.tvVaultRegister = function(name, witness){
  REG.push({ name: name, witness: witness });
%(rec)s
  window._ownedAdd(name, _rec);
  return { ok: true, label: name, mode: 'new', filed: false, refused: 'witness', why: 'one look' };
};
window.kaiChronicleRecord = function(r){ RECORDS.push(r); return r; };
window.vaultRemove = function(names, opts){
  REMOVED.push({ names: names.slice(), lane: opts && opts.lane });
  var p = JSON.parse(STORE['d2r_vaultProv'] || '{}');
  names.forEach(function(n){ owned['delete'](n); delete p[n]; });
  STORE['d2r_vaultProv'] = JSON.stringify(p);
  return { removed: names.slice() };
};
function reset(prov, own){ STORE = {}; if (prov !== undefined) STORE['d2r_vaultProv'] = (typeof prov === 'string') ? prov : JSON.stringify(prov);
  owned = new Set(own || []); REG = []; RECORDS = []; REMOVED = []; FILED = []; FETCHES = []; LOGS = []; }
function prov(){ return JSON.parse(STORE['d2r_vaultProv'] || '{}'); }
var OUT = {};
(async function(){
%(script)s
process.stdout.write(JSON.stringify(OUT));
})().catch(function(e){ process.stderr.write('THREW ' + (e && e.stack || e)); process.exit(3); });
"""

SORTER = r"""
function sorter(P, A){
  STORE['d2r_vaultProv'] = JSON.stringify(P);
  var assign = A, n = 0, calls = [];
  function muleById(id){ return (id === 'uni-armor' || id === 'uni-small') ? { id: id } : null; }
  function _log(){ LOGS.push(Array.prototype.slice.call(arguments)); }
  window.vaultFile = function(name, w, o){ calls.push({ name: name, witness: w, opts: o }); return { ok: false, refused: 'witness', why: 'stub' }; };
  window._vaultProvSay = function(){ return ''; };
%(wit)s
%(sort)s
  return calls;
}
function w6(P, A, pool){
  var assign = A;
  function muleById(id){ return (id === 'uni-armor' || id === 'uni-small') ? { id: id } : null; }
  STORE['d2r_vaultProv'] = JSON.stringify(P);
%(w6)s
  return assign;
}
"""

#: game item names only — never his store
CHRONICLE_PAGE = ["Hellfire Torch", "Cranium Basher", "Eye of Etlich", "Nagelring", "Magefist", "Stormshield", "Windforce"]
SESSION = "s_1790543358478_35359"
LOG = ([{"name": "Grief", "status": "in-chronicle", "store": "rwMade", "source": "aic-judge", "tier": "keep",
         "sessionId": SESSION, "frameId": "9_1790543904663", "firstSeenTs": 1790543904663, "loc": None},
        {"name": "Plague", "status": "in-chronicle", "store": "rwMade", "source": "aic-judge", "tier": "keep",
         "sessionId": SESSION, "frameId": "11_1790543968521", "firstSeenTs": 1790543968521, "loc": None},
        {"name": "String of Ears", "status": "in-chronicle", "store": "foundLog", "source": "kai-register",
         "tier": "grail", "sessionId": "s_2", "frameId": "17_1790551926547", "firstSeenTs": 1790551926547,
         "loc": "equipped", "scene": "inventory"}]
       + [{"name": nm, "status": "in-chronicle", "store": "foundLog", "source": "kai-register", "tier": "grail",
           "sessionId": "s_2", "frameId": "%d_1790551%06d" % (20 + i, i), "loc": None, "scene": "chronicle"}
          for i, nm in enumerate(CHRONICLE_PAGE)]
       + [{"name": "Arachnid Mesh", "status": "accepted", "source": "kai-register", "loc": "stash", "scene": "chronicle",
           "sessionId": "s_2", "frameId": "40_1"},
          {"name": "Shako", "status": "in-chronicle", "source": "kai-register", "loc": "floor", "sessionId": "s_2", "frameId": "41_1"},
          {"name": "Gore Rider", "status": "in-chronicle", "source": "kai-register", "loc": None, "sessionId": "s_2", "frameId": "42_1"},
          {"name": "Skin of the Vipermagi", "status": "dismissed", "source": "kai-register", "loc": "equipped", "frameId": "43_1"},
          {"name": "Harlequin Crest", "status": "pending", "source": "kai-register", "loc": "stash", "frameId": "44_1"},
          {"name": "Tal Rasha's Horadric Crest", "status": "in-chronicle", "source": "kai-register", "loc": "inventory", "frameId": "45_1"}])

SCRIPT = r"""
// ── the door ──
reset({}, []);
var r1 = window._ownedAdd('Grief', { source: 'aic-judge', by: 'aicJudgeApply (keep)', sessionId: 's_1', frameId: '9_1790543904663',
                                     ts: 1790543904663, scene: 'stash', readTier: 'keep' });
OUT.receipt = { r: r1, row: prov()['Grief'], owned: Array.from(owned) };
reset({ Shako: { mule: 'uni-armor', source: 'stash', tier: 'PROVEN', successes: 12, trials: 12,
                 looks: [{ id: 's0', frame: 'a.jpg', conf: 0.9 }] } }, []);
window._ownedAdd('Shako', { source: 'kai-register', frameId: 'b.jpg', sessionId: 's9' });
var afterOne = prov()['Shako'];
window._ownedAdd('Shako', { source: 'hand', frameId: 'c.jpg' });
OUT.noClobber = { one: afterOne, two: prov()['Shako'] };
reset({}, []);
window._ownedAdd('String of Ears', { source: 'kai-register', frameId: 'f1', sessionId: 's_2', loc: 'equipped' });
window._ownedAdd('String of Ears', { source: 'kai-register', frameId: 'f2', sessionId: 's_3', scene: 'inventory' });
window._ownedAdd('String of Ears', { source: 'kai-register', frameId: 'f1', sessionId: 's_2' });
OUT.merge = prov()['String of Ears'];
reset({}, []);
var r4 = window._ownedAdd('Nagelring', {});
OUT.noSource = { r: r4, owned: Array.from(owned), prov: prov() };
reset('{broken', []);
var r5 = window._ownedAdd('Nagelring', { source: 'hand' });
OUT.unreadable = { r: r5, raw: STORE['d2r_vaultProv'], owned: Array.from(owned) };

// ── the route ──
var pairs = [['equipped','inventory'],['stash',null],['cube',null],['mule',null],['stash','chronicle'],[null,'chronicle'],
             ['floor',null],[null,'loot'],['inventory',null],[null,'inventory'],[null,null],[null,'stash'],[null,'gameplay'],['EQUIPPED',null]];
OUT.routes = pairs.map(function(p){ var v = window._vaultHoldingRoute(p[0], p[1]); return [p[0], p[1], v.route, v.why]; });
reset({}, []);
var live = window._liveReadRoute({ name: 'String of Ears', loc: 'equipped', scene: 'inventory', sessionId: 's_2',
                                   frameId: '17_1790551926547', source: 'kai-register', tier: 'grail', firstSeenTs: 1790551926547, conf: 0.91 });
var chron = window._liveReadRoute({ name: 'Hellfire Torch', loc: null, scene: 'chronicle', sessionId: 's_2', frameId: '20_1', source: 'kai-register' });
var chronStash = window._liveReadRoute({ name: 'Arachnid Mesh', loc: 'stash', scene: 'chronicle', sessionId: 's_2', frameId: '40_1', source: 'kai-register' });
var unknown = window._liveReadRoute({ name: 'Gore Rider', loc: null, scene: null, source: 'kai-register' });
OUT.live = { live: live, chron: chron, chronStash: chronStash, unknown: unknown, owned: Array.from(owned).sort(),
             row: prov()['String of Ears'], reg: REG };

// ── the backfill ──
reset({}, ['Plague', 'Grief']);
STORE['d2r_chronicleInboxLog'] = JSON.stringify(%(log)s);
var b1 = window._ownedProvBackfill();
var snap = JSON.stringify(STORE), ownSnap = JSON.stringify(Array.from(owned).sort());
var b2 = window._ownedProvBackfill();
OUT.backfill = { b1: b1, b2: b2, idempotent: (JSON.stringify(STORE) === snap && JSON.stringify(Array.from(owned).sort()) === ownSnap),
                 owned: Array.from(owned).sort(), prov: prov(), records: RECORDS };
// ── the evidence panel, on the backfilled store ──
var mG = window._vaultEvidenceOf('Grief'), mS = window._vaultEvidenceOf('String of Ears'), mN = window._vaultEvidenceOf('Nothing Here');
OUT.evidence = { grief: mG, soe: mS, none: mN,
                 griefHtml: window._vaultEvidenceHtml(mG, { state: 'checking', say: 'looking' }),
                 noneHtml: window._vaultEvidenceHtml(mN, { state: 'none', say: '' }),
                 chip: window._vaultEvidenceChip('Grief'), chipNone: window._vaultEvidenceChip('Nothing Here'),
                 line: window._vaultEvidenceLine('Grief') };
// the picture: loads -> shown; does not load -> the console's words; the console silent -> UNKNOWN
window._tvdFrameChain = function(id){ return ['http://bridge/frame?id=' + id, 'tv/frames/hist/' + id + '.jpg']; };
var LOADS = {};
window.Image = function(){ var self = this; Object.defineProperty(self, 'src', { get: function(){ return self._s; },
  set: function(v){ self._s = v; setTimeout(function(){ var f = LOADS[v] ? self.onload : self.onerror; if (f) f.call(self); }, 0); } }); };
var FETCH_IMPL = null;
window.fetch = function(url, opt){ FETCHES.push(url); return FETCH_IMPL(url); };
function pic(id){ return new Promise(function(res){ window._vaultEvidencePicture(id, res); }); }
LOADS['tv/frames/hist/9_1790543904663.jpg'] = 1;
FETCH_IMPL = function(){ return Promise.resolve({ ok: true, json: function(){ return { ok: true, pictures: {
  '17_1790551926547': { present: false, code: 'disk-floor', why: 'the recorder was under its disk floor when this read was taken — the picture was never written' } } }; } }); };
var p1 = await pic('9_1790543904663');
var p2 = await pic('17_1790551926547');
FETCH_IMPL = function(){ return Promise.reject(new Error('refused')); };
var p3 = await pic('17_1790551926547');
var p4 = await pic('');
OUT.pictures = { present: p1, gone: p2, silent: p3, none: p4, fetches: FETCHES,
                 presentHtml: window._vaultEvidencePicHtml(mG, p1), goneHtml: window._vaultEvidencePicHtml(mS, p2),
                 silentHtml: window._vaultEvidencePicHtml(mS, p3) };
// ── the undo ──
var u1 = window._ownedProvBackfillUndo();
var u2 = window._ownedProvBackfillUndo();
OUT.undo = { u1: u1, u2: u2, owned: Array.from(owned).sort(), prov: prov(), removed: REMOVED };
// ── a receipt is never a witness ──
OUT.sorter = sorter({ 'Receipt Only': { kind: 'owned', source: 'hand', at: '2026-09-28T00:00:00Z', where: 'the card' },
                      'Lost Home': { mule: 'uni-armor', source: 'hand', by: 'hand', at: '2026-09-01T00:00:00Z', where: 'the mule window' } }, {})
                 .map(function(c){ return { name: c.name, witnessed: !!c.witness }; });
OUT.w6 = w6({ 'Receipt Only': { kind: 'owned', source: 'hand' }, 'Stash Witness': { mule: 'uni-armor', source: 'stash' } },
            { 'Receipt Only': 'uni-armor', 'Stash Witness': 'uni-armor' }, []);
"""


def _drive():
    s = _src()
    sort_src = SORTER % {"wit": _between(s, WIT_FROM, WIT_TO), "sort": _between(s, SORT_FROM, SORT_TO),
                         "w6": _between(s, W6_FROM, W6_TO)}
    prog = HARNESS % {"lanes": _lanes(s), "region": owned_prov_region(s), "evidence": _marked(s, EV_BEGIN, EV_END),
                      "rec": _between(s, REC_FROM, REC_TO),
                      "script": sort_src + SCRIPT % {"log": json.dumps(LOG)}}
    fd, path = tempfile.mkstemp(prefix=".owned_prov_", suffix=".js", dir=HERE)
    try:
        with io.open(fd, "w", encoding="utf-8") as fh:
            fh.write(prog)
        r = subprocess.run([NODE, path], capture_output=True, text=True, timeout=60)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    if r.returncode != 0:
        raise AssertionError("the owned door would not run — UNKNOWN, not passing: %s" % (r.stderr or r.stdout)[-1500:])
    return json.loads(r.stdout)


_CACHE = {}


def out():
    if "o" not in _CACHE:
        _CACHE["o"] = _drive()
    return _CACHE["o"]


class TheCensus(unittest.TestCase):

    def test_no_bare_owned_add_outside_the_door(self):
        s = _src()
        i = s.index(BEGIN)
        j = s.index(END)
        sites = code_sites(s)
        inside = [x for x in sites if i < x[1] < j]
        outside = [x for x in sites if not (i < x[1] < j)]
        self.assertEqual(1, len(inside), "the door itself should hold exactly one owned.add: %r" % inside)
        named = {}
        for ln, _pos, text in outside:
            if text in NAMED:
                named[text] = named.get(text, 0) + 1
        bare = [(ln, text) for ln, _pos, text in outside if text not in NAMED]
        self.assertEqual([], bare, "a door adds to `owned` without writing provenance — route it through "
                                   "window._ownedAdd(name, {source, ...}): %r" % bare[:6])
        for text, (want, why) in NAMED.items():
            self.assertEqual(want, named.get(text, 0), "a named exception no longer matches the board — prune NAMED: %r" % text)

    def test_the_scanner_sees_every_site_the_old_board_had(self):
        """The instrument, pinned: the board BEFORE this change had 22 bare sites, and a scanner that loses its way
        in a regex literal found 1. Run on a planted fixture holding every shape the file uses."""
        fixture = ("<script>\nvar re = /[‘’`]/g; owned.add(a);\n// owned.add(comment)\n/* owned.add(block) */\n"
                   "var s = 'owned.add(str)'; var t = `x ${owned.add(b)} y`; var u = `owned.add(tmpl)`;\n"
                   "if (x) owned['add'](c); var d = a / b; owned.add(e);\n</script>\n<p>owned.add(html)</p>\n")
        got = [t for _l, _p, t in code_sites(fixture)]
        self.assertEqual(4, len(got), "the census scanner miscounts code sites on a planted fixture: %r" % got)


@unittest.skipIf(NODE is None, "node is absent — the owned door was not driven (a declared skip, never a pass)")
class TheDoorWritesAReceipt(unittest.TestCase):

    def test_a_receipt_names_who_when_and_the_picture(self):
        o = out()["receipt"]
        row = o["row"]
        self.assertIn("Grief", o["owned"])
        self.assertEqual("owned", row["kind"])
        self.assertEqual("aic-judge", row["source"])
        self.assertEqual("s_1", row["sessionId"])
        self.assertEqual("9_1790543904663", row["frameId"])
        self.assertEqual("9_1790543904663", row["looks"][0]["frame"])
        self.assertTrue(str(row["at"]).startswith("2026-09-2"), row["at"])
        self.assertEqual("stash", row["scene"])

    def test_a_filing_row_is_never_clobbered(self):
        o = out()["noClobber"]
        for k in ("one", "two"):
            row = o[k]
            self.assertEqual(("PROVEN", 12, 12, "uni-armor", "stash"),
                             (row.get("tier"), row.get("successes"), row.get("trials"), row.get("mule"), row.get("source")),
                             "%s: the receipt overwrote the richer filing row: %r" % (k, row))
            self.assertNotEqual("owned", row.get("kind"))
        self.assertEqual("kai-register", o["one"]["ownedBy"]["source"], "the filing did not note who first owned it")
        self.assertEqual("kai-register", o["two"]["ownedBy"]["source"], "a second add replaced the ownedBy note")

    def test_a_standing_receipt_only_grows_its_tally(self):
        row = out()["merge"]
        self.assertEqual(["f1", "f2"], [k["frame"] for k in row["looks"]], "a repeat look was counted twice or a new one lost")
        self.assertEqual(2, row["seen"])
        self.assertEqual("equipped", row["loc"])
        self.assertEqual("inventory", row["scene"], "a missing field was not filled from the next read")

    def test_no_source_means_no_row_and_the_item_still_lands(self):
        o = out()["noSource"]
        self.assertIn("Nagelring", o["owned"])
        self.assertEqual({}, o["prov"])
        self.assertFalse(o["r"]["prov"]["ok"])

    def test_an_unreadable_store_is_never_written_over(self):
        o = out()["unreadable"]
        self.assertEqual("{broken", o["raw"])
        self.assertIn("Nagelring", o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the route was not driven")
class TheRouteFilesWhatHeHolds(unittest.TestCase):

    def test_the_route_table(self):
        got = {(a, b): r for a, b, r, _w in out()["routes"]}
        want = {("equipped", "inventory"): "vault", ("stash", None): "vault", ("cube", None): "vault",
                ("mule", None): "vault", ("stash", "chronicle"): "found-only", (None, "chronicle"): "found-only",
                ("floor", None): "not-held", (None, "loot"): "not-held", ("inventory", None): "held",
                (None, "inventory"): "held", (None, None): "wait", (None, "stash"): "wait", (None, "gameplay"): "not-held",
                ("EQUIPPED", None): "vault"}
        self.assertEqual(want, got)
        for a, b, r, why in out()["routes"]:
            self.assertTrue(why, "route %r gave no reason" % ((a, b),))
        waits = [w for a, b, r, w in out()["routes"] if r == "wait"]
        self.assertTrue(all("UNKNOWN" in w or "waits" in w for w in waits), waits)

    def test_a_worn_read_files_into_the_dock_with_its_receipt(self):
        o = out()["live"]
        self.assertEqual("vault", o["live"]["route"])
        self.assertIn("String of Ears", o["owned"])
        row = o["row"]
        self.assertEqual(("owned", "kai-register", "equipped", "inventory", "17_1790551926547", "s_2"),
                         (row["kind"], row["source"], row["loc"], row["scene"], row["frameId"], row["sessionId"]))
        self.assertEqual(1, len(o["reg"]), "the register was asked for something other than the worn read")

    def test_a_chronicle_page_a_floor_and_an_unknown_read_never_file(self):
        o = out()["live"]
        self.assertEqual("found-only", o["chron"]["route"])
        self.assertEqual("found-only", o["chronStash"]["route"], "a Chronicle-page read with a place on it filed")
        self.assertEqual("wait", o["unknown"]["route"])
        for nm in ("Hellfire Torch", "Arachnid Mesh", "Gore Rider"):
            self.assertNotIn(nm, o["owned"])


@unittest.skipIf(NODE is None, "node is absent — the backfill was not driven")
class TheBackfill(unittest.TestCase):

    def test_owned_names_gain_their_receipts_and_the_worn_read_is_filed(self):
        o = out()["backfill"]
        self.assertTrue(o["b1"]["ran"], o["b1"])
        rc = o["b1"]["receipt"]
        self.assertEqual(["Grief", "Plague"], sorted(rc["wrote"]))
        self.assertEqual(["String of Ears"], [f["name"] for f in rc["filed"]])
        g = o["prov"]["Grief"]
        self.assertEqual(("owned", "aic-judge", "9_1790543904663", "s_1790543358478_35359", "backfill"),
                         (g["kind"], g["source"], g["frameId"], g["sessionId"], g["by"]))
        self.assertEqual("11_1790543968521", o["prov"]["Plague"]["frameId"])
        soe = o["prov"]["String of Ears"]
        self.assertEqual(("equipped", "17_1790551926547", "backfill"), (soe["loc"], soe["frameId"], soe["by"]))
        self.assertIn("String of Ears", o["owned"])

    def test_nothing_else_files(self):
        o = out()["backfill"]
        never = CHRONICLE_PAGE + ["Arachnid Mesh", "Shako", "Gore Rider", "Skin of the Vipermagi", "Harlequin Crest",
                                  "Tal Rasha's Horadric Crest"]
        for nm in never:
            self.assertNotIn(nm, o["owned"], "%s was filed by the backfill" % nm)
            self.assertNotIn(nm, o["prov"])
        rc = o["b1"]["receipt"]
        self.assertEqual(8, rc["routes"].get("found-only"), rc["routes"])
        self.assertEqual(1, rc["routes"].get("wait"), rc["routes"])
        self.assertEqual({"dismissed": 1, "pending": 1}, rc["skipped"])

    def test_it_runs_once_and_says_so(self):
        o = out()["backfill"]
        self.assertFalse(o["b2"]["ran"])
        self.assertTrue(o["b2"]["already"])
        self.assertTrue(o["idempotent"], "a second backfill changed the store")

    def test_the_read_keeps_its_own_ledger_status(self):
        recs = out()["backfill"]["records"]
        mine = [r for r in recs if r.get("name") == "String of Ears"]
        self.assertTrue(mine, "the ledger row was never put back after the register spoke over it")
        self.assertEqual(("in-chronicle", "kai-register", "vault"), (mine[-1]["status"], mine[-1]["source"], mine[-1]["vaultRoute"]))

    def test_the_undo_takes_back_exactly_what_it_did(self):
        o = out()["undo"]
        self.assertTrue(o["u1"]["ok"], o["u1"])
        self.assertEqual(["String of Ears"], o["u1"]["removed"])
        self.assertEqual(["Grief", "Plague"], sorted(o["u1"]["dropped"]))
        self.assertEqual(["Grief", "Plague"], o["owned"], "the undo removed a name it never filed")
        self.assertEqual({}, o["prov"])
        self.assertEqual("backfill-undo", o["removed"][0]["lane"], "the undo did not go through the removal door")
        self.assertFalse(o["u2"]["ok"], "a second undo acted again")


@unittest.skipIf(NODE is None, "node is absent — the receipt/witness line was not driven")
class AReceiptIsNeverAWitness(unittest.TestCase):

    def test_the_sorter_files_nothing_on_a_receipt(self):
        calls = out()["sorter"]
        self.assertEqual(["Lost Home"], [c["name"] for c in calls], "the sorter handed a receipt to the mule door")
        self.assertTrue(calls[0]["witnessed"])

    def test_the_prune_keeps_no_filing_on_a_receipt(self):
        a = out()["w6"]
        self.assertNotIn("Receipt Only", a, "a filing stood on a receipt")
        self.assertIn("Stash Witness", a)


@unittest.skipIf(NODE is None, "node is absent — the evidence panel was not driven")
class TheEvidenceIsVisible(unittest.TestCase):

    def test_the_panel_says_who_when_session_frame_and_tally(self):
        e = out()["evidence"]
        g = e["grief"]
        self.assertTrue(g["has"])
        self.assertIn("AI item checker", g["who"])
        self.assertEqual(("s_1790543358478_35359", "9_1790543904663"), (g["session"], g["frame"]))
        self.assertEqual("1 look", g["tallySay"])
        self.assertTrue(g["when"] and "2026" in g["when"], g["when"])
        for bit in ("Filed by", "9_1790543904663", "s_1790543358478_35359", "1 look", "AI item checker"):
            self.assertIn(bit, e["griefHtml"])
        self.assertEqual("worn (equipped) · screen: inventory", e["soe"]["seen"])
        self.assertIn('class="vc-ev"', e["chip"])
        self.assertIn("window._vaultEvidenceOpen(", e["chip"])

    def test_no_provenance_is_said_in_words(self):
        e = out()["evidence"]
        self.assertFalse(e["none"]["has"])
        self.assertIn("No provenance", e["noneHtml"])
        self.assertIn("UNKNOWN", e["noneHtml"])
        self.assertIn("ev-none", e["chipNone"])

    def test_a_picture_is_shown_only_when_it_loads(self):
        p = out()["pictures"]
        self.assertEqual("present", p["present"]["state"])
        self.assertIn("<img", p["presentHtml"])
        self.assertEqual("gone", p["gone"]["state"])
        self.assertIn("picture not on this machine", p["gone"]["say"])
        self.assertIn("disk floor", p["gone"]["say"])
        self.assertEqual("unknown", p["silent"]["state"])
        self.assertIn("UNKNOWN", p["silent"]["say"])
        self.assertEqual("none", p["none"]["state"])
        for k in ("goneHtml", "silentHtml"):
            self.assertNotIn("<img", p[k], "%s drew an image for a picture that did not load" % k)
            self.assertIn("picture not on this machine", p[k])
        self.assertTrue(any("picture_status?ids=17_1790551926547" in u for u in p["fetches"]),
                        "the console was never asked why the picture is gone")


class TheJoins(unittest.TestCase):
    """Structure, read as CODE (comments stripped by the same scanner) — the two doors that route a live read."""

    def _block(self, s, head):
        assert s.count(head) == 1, "anchor %r matched %d times" % (head[:50], s.count(head))
        i = s.index(head) + len(head)
        depth, j = 1, i
        while j < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[j], 0)
            j += 1
        blk = s[i:j]
        m = code_mask(blk.join(["<script>", "</script>"]), keep_strings=True)
        return "".join(ch for k, ch in enumerate(blk) if m[k + len("<script>")] or ch == "\n")

    def test_the_settled_branch_asks_the_route_before_it_returns(self):
        blk = self._block(_src(), "var why = window.kaiChronicleSettledWhy(nm);\n        if (why){")
        self.assertIn("window._liveReadRoute(base)", blk, "the settled branch never asks the route")
        self.assertLess(blk.index("window._liveReadRoute(base)"), blk.index("return;"), "the route is asked after the branch returns")
        self.assertIn("vaultRoute:_svr.route", blk.replace(" ", ""))

    def test_the_judge_keep_writes_its_receipt_through_the_door(self):
        blk = self._block(_src(), "          if (_kwRW){")
        self.assertIn("window._ownedAdd(nm,{source:'aic-judge'", blk.replace(" ", "").replace("\n", ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "a door adds to owned bare again — no receipt, the Grief/Plague defect",
        "file": "bible.html",
        "find": "    else window._ownedAdd(name, (prov && prov.source) ? prov : { source: 'hand', by: 'toggleOwned', where: 'the item card tick' });\n",
        "replace": "    else owned.add(name);\n",
        "matches": 1,
    },
    {
        "why": "the receipt clobbers a filing row (the §24 rebuild's tier/successes/trials are lost)",
        "file": "bible.html",
        "find": "    if (cur && typeof cur === 'object' && !Array.isArray(cur)){\n      if (cur.kind !== 'owned'){\n",
        "replace": "    if (cur && typeof cur === 'object' && !Array.isArray(cur) && cur.kind === 'owned'){\n      if (false){\n",
        "matches": 1,
    },
    {
        "why": "a Chronicle-page read files into the vault again (§28)",
        "file": "bible.html",
        "find": "    if (s === 'chronicle' || l === 'chronicle')\n",
        "replace": "    if (false)\n",
        "matches": 1,
    },
    {
        "why": "an UNKNOWN place files instead of waiting",
        "file": "bible.html",
        "find": "    if (!s) return { route: 'wait', why: 'where it was seen is UNKNOWN",
        "replace": "    if (!s) return { route: 'vault', why: 'where it was seen is UNKNOWN",
        "matches": 1,
    },
    {
        "why": "the settled branch stops asking the route — String of Ears reaches the found list only",
        "file": "bible.html",
        "find": "            try { _svr = window._liveReadRoute(base); } catch(eSR){ _svr = null; }\n",
        "replace": "            _svr = null;\n",
        "matches": 1,
    },
    {
        "why": "the backfill runs on every load (not one-time)",
        "file": "bible.html",
        "find": "    if (done && done.ver >= _BF_VER && !opts.force) return { ran: false, already: true, receipt: done };\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "the sorter hands an owned receipt to the mule door as a witness",
        "file": "bible.html",
        "find": "      if (_row.kind === 'owned') return;          /* 2026-09-28 — an owned RECEIPT is not a witness: it files nothing */\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "a picture that did not load is drawn as a broken image",
        "file": "bible.html",
        "find": "    if (pic.state === 'present' && pic.src){\n",
        "replace": "    if (pic.state !== 'none'){\n",
        "matches": 1,
    },
    {
        "why": "the backfill files a read that is still waiting for his ruling",
        "file": "bible.html",
        "find": "  var _BF_RULED = { 'dismissed': 1, 'blocked-unfound': 1, 'undone': 1, 'pending': 1 };\n",
        "replace": "  var _BF_RULED = { 'dismissed': 1, 'blocked-unfound': 1, 'undone': 1 };\n",
        "matches": 1,
    },
]
