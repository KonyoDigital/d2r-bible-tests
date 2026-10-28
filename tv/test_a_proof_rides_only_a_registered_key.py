# -*- coding: utf-8 -*-
"""#186 STEP 3 - A PROOF ONE PC EARNED REACHES ANOTHER PC ON THE SAME COMMIT, AND ONLY UNDER A KEY THE ROSTER TRUSTS.

His ruling, 2026-10-28: "identical bytes saved from the windows alt pc that has already been proved. he doesnt need to
reprove it all". Three parts, each driven here on the real code:

  * functions/api/proofs.js, the REAL handler in node over a stand-in KV, real Ed25519 signatures from roster_sign: an
    unsigned body, a key nobody registered, a signature over other bytes and an export whose manifest names another head
    are refused with NOTHING stored; the registered key stores one record; the same head inside 3 hours writes nothing;
    GET answers who, which head, which platform, and the export itself only on &body=1.
  * tv/proof_carrier.py with fakes for the network and heart2: take() imports a peer's export only when it was carried on
    THIS platform at THIS head (writing exactly the export to the file it hands --import-proved); publish() never posts
    an export it could not sign, and posts exactly the bytes it signed.
  * control_app._proof_carrier_due: the carrier waits wherever the prover would - he is playing, his play state is
    UNKNOWN, memory is under the prover's start floor - runs only on a platform with peers, takes first while laws are
    owed, and does not repeat itself at one HEAD.

The importing side's own rule (re-key every entry on THIS PC's bytes, refuse another HEAD) is REG-2630's law,
test_a_proof_proved_elsewhere_counts_only_under_this_trees_key. RED_PROOF below.
"""
import base64
import io
import json
import os
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
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()
import roster_sign as RS  # noqa: E402
import proof_carrier as PC  # noqa: E402

NODE = shutil.which("node")
PROOFS_JS = os.path.join(ROOT, "functions", "api", "proofs.js")
OWNER = "Konyo · ALT"
HEAD = "a" * 40
OTHER = "b" * 40

_HARNESS = r"""
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const bytes = (s) => new Uint8Array(Buffer.from(s || '', 'base64'));
let store = new Map(Object.entries(CFG.seed || {}).map(([k, v]) => [k, typeof v === 'string' ? v : JSON.stringify(v)]));
let puts = [];
const kv = {
  async get(n, o) { if (!store.has(n)) return null; const v = store.get(n); return (o && o.type === 'json') ? JSON.parse(v) : v; },
  async put(n, v, o) { puts.push({ key: n, ttl: (o && o.expirationTtl) || null }); store.set(n, v); },
};
const mod = await import(pathToFileURL(CFG.file).href);
const out = { steps: [], gets: [] };
for (const step of (CFG.steps || [])) {
  puts = [];
  const realNow = Date.now;
  if (typeof step.now === 'number') Date.now = () => step.now;
  const req = new Request('https://bull-4-u.com/api/proofs', { method: 'POST', body: bytes(step.raw),
    headers: Object.assign({ 'content-type': 'application/json' }, step.headers || {}) });
  const res = await mod.onRequestPost({ request: req, env: { TZ_HISTORY: kv }, waitUntil() {} });
  out.steps.push({ reply: JSON.parse(await res.text()), puts: puts });
  Date.now = realNow;
}
for (const q of (CFG.gets || [])) {
  const res = await mod.onRequestGet({ request: new Request('https://bull-4-u.com/api/proofs?' + q), env: { TZ_HISTORY: kv } });
  out.gets.push(JSON.parse(await res.text()));
}
process.stdout.write(JSON.stringify(out));
"""


def _node(cfg):
    cfg = dict(cfg, file=PROOFS_JS)
    d = tempfile.mkdtemp(prefix="tvd_proofs_js_")
    try:
        h, c = os.path.join(d, "h.mjs"), os.path.join(d, "cfg.json")
        with io.open(h, "w", encoding="utf-8") as fh:
            fh.write(_HARNESS)
        with io.open(c, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        r = subprocess.run([NODE, h, c], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    finally:
        shutil.rmtree(d, True)
    if r.returncode != 0:
        raise AssertionError("the proofs harness failed rc=%s\n%s" % (r.returncode, r.stderr[-2000:]))
    return json.loads(r.stdout)


def _export(head=HEAD, n=3):
    return {"format": 2, "entries": dict(("k%d" % i, {"gate": "g%d" % i, "proof": i, "verdict": "PROVEN"}) for i in range(n)),
            "export": {"head": head, "dirty": False, "n": n, "at": 1}}


def _raw(head=HEAD, manifest_head=None, platform="win32"):
    body = {"owner": OWNER, "platform": platform, "head": head, "export": _export(manifest_head or head)}
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _key():
    d = tempfile.mkdtemp(prefix="tvd_proofs_key_")
    path = RS.key_path_in(d)
    key, why, _made = RS.load_or_create(path)
    if key is None:
        raise AssertionError("no fixture key: %s" % why)
    return path, key.pub


def _signed(path, raw):
    headers, signing = RS.sign_headers(path, raw)
    assert signing.get("signed"), signing
    return headers


def _step(raw, headers=None, now=None):
    one = {"raw": base64.b64encode(raw).decode("ascii"), "headers": dict(headers or {})}
    if now is not None:
        one["now"] = now
    return one


def _seed(pub):
    return {"rosterkey:" + OWNER: {"pub": RS.b64u(pub), "keyId": RS.key_id(pub), "at": 1}}


@unittest.skipUnless(NODE, "node is absent - proofs.js cannot be run here, so these cases are UNMEASURED, not passed")
class TheRouteTakesOnlyARegisteredKey(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.path, cls.pub = _key()
        cls.other_path, _p = _key()

    def test_the_registered_key_stores_one_record_and_get_answers_it(self):
        raw = _raw()
        o = _node({"seed": _seed(self.pub), "steps": [_step(raw, _signed(self.path, raw), now=1000000)],
                   "gets": ["owner=" + OWNER, "owner=" + OWNER + "&body=1", "owner=Dean"]})
        r = o["steps"][0]
        self.assertTrue(r["reply"].get("stored"), "the registered key's export was not stored: %r" % r["reply"])
        self.assertEqual([p["key"] for p in r["puts"]], ["proofs:" + OWNER])
        self.assertEqual(r["puts"][0]["ttl"], 7 * 24 * 3600, "the export does not expire")
        meta, full, none = o["gets"]
        self.assertEqual((meta["head"], meta["platform"], meta["count"]), (HEAD, "win32", 3))
        self.assertNotIn("export", meta, "the bare GET hands the whole export")
        self.assertEqual(full["export"]["entries"], _export()["entries"])
        self.assertEqual((none.get("ok"), none.get("have")), (True, False))

    def test_the_same_head_again_writes_nothing(self):
        raw = _raw()
        h = _signed(self.path, raw)
        o = _node({"seed": _seed(self.pub), "steps": [_step(raw, h, now=1000000), _step(raw, h, now=1000000 + 3600000)]})
        second = o["steps"][1]
        self.assertEqual((second["reply"].get("stored"), second["puts"]), (False, []),
                         "the same head an hour later spent a KV write: %r" % second)

    def test_nothing_unsigned_unregistered_forged_or_mismatched_is_stored(self):
        raw = _raw()
        forged = bytearray(raw)
        forged[forged.index(b'"verdict":"PROVEN"') + 12] ^= 1          # one byte of an entry, after signing
        bad_head = _raw(manifest_head=OTHER)
        steps = [_step(raw),                                              # unsigned
                 _step(raw, _signed(self.other_path, raw)),               # a key that is not the registered one
                 _step(bytes(forged), _signed(self.path, raw)),           # a signature over other bytes
                 _step(bad_head, _signed(self.path, bad_head))]           # the manifest names another head
        o = _node({"seed": _seed(self.pub), "steps": steps})
        for i, s in enumerate(o["steps"]):
            self.assertIs(s["reply"].get("ok"), False, "case %d was taken: %r" % (i, s["reply"]))
            self.assertEqual(s["puts"], [], "case %d wrote to KV: %r" % (i, s))
        o2 = _node({"seed": {}, "steps": [_step(raw, _signed(self.path, raw))]})
        self.assertIn("no registered key", o2["steps"][0]["reply"].get("why", ""),
                      "a key nobody registered carried proofs: %r" % o2["steps"][0]["reply"])
        self.assertEqual(o2["steps"][0]["puts"], [], "proofs registered a key on first use")


class TheCarrierTakesOnlyThisPlatformAtThisHead(unittest.TestCase):

    def _get(self, metas):
        def get(url):
            owner = url.split("owner=", 1)[1].split("&", 1)[0]
            m = metas.get(urlparse_unquote(owner), {"ok": True, "have": False})
            if url.endswith("&body=1"):
                return dict(m, export=_export(m.get("head")))
            return m
        return get

    def test_only_a_same_platform_export_at_this_head_is_imported(self):
        seen = []

        def run(args, timeout):
            with io.open(args[1], encoding="utf-8") as fh:
                seen.append((args[0], json.load(fh)))
            return 0, "IMPORTED"
        metas = {"Konyo · ALT": {"ok": True, "have": True, "platform": "win32", "head": HEAD, "count": 3, "at": 1},
                 "Konyo · Mac": {"ok": True, "have": True, "platform": "darwin", "head": HEAD, "count": 9, "at": 1},
                 "Wife PC": {"ok": True, "have": True, "platform": "win32", "head": OTHER, "count": 2, "at": 1}}
        out = PC.take(["Konyo · ALT", "Konyo · Mac", "Wife PC", "Dean"], HEAD, platform="win32",
                      get=self._get(metas), run=run)
        self.assertEqual([r["owner"] for r in out["imported"]], ["Konyo · ALT"])
        self.assertEqual(seen, [("--import-proved", _export(HEAD))], "the file handed to the import is not the export")
        why = dict((s["owner"], s["why"]) for s in out["skipped"])
        self.assertIn("darwin", why["Konyo · Mac"])
        self.assertIn("carried at", why["Wife PC"])
        self.assertEqual(why["Dean"], "no export carried")

    def test_an_unknown_head_asks_nobody(self):
        asked = []
        out = PC.take(["Konyo · ALT"], None, get=lambda u: asked.append(u) or {}, run=None)
        self.assertEqual(asked, [])
        self.assertIn("UNKNOWN", out["why"])


def urlparse_unquote(s):
    import urllib.parse
    return urllib.parse.unquote(s)


class ThePublishPostsOnlyWhatItSigned(unittest.TestCase):

    def _run(self, head=HEAD):
        def run(args, timeout):
            d = args[1]
            with io.open(os.path.join(d, ".heart2_cache.json"), "w", encoding="utf-8") as fh:
                json.dump(_export(head), fh)
            return 0, "EXPORTED"
        return run

    def test_an_unsigned_export_is_not_sent(self):
        posted = []
        out = PC.publish(OWNER, "k", run=self._run(), post=lambda *a: posted.append(a) or {"ok": True},
                         sign=lambda path, raw: ({}, {"signed": False, "why": "no key"}))
        self.assertEqual(posted, [], "an export no key signed was posted")
        self.assertIn("could not be signed", out["why"])

    def test_the_bytes_posted_are_the_bytes_signed(self):
        signed, posted = [], []

        def sign(path, raw):
            signed.append(raw)
            return {"X-Roster-Key": "k", "X-Roster-Sig": "s"}, {"signed": True, "keyId": "abc"}
        out = PC.publish(OWNER, "k", platform="win32", run=self._run(),
                         post=lambda url, raw, headers: posted.append((raw, headers)) or {"ok": True, "stored": True},
                         sign=sign)
        self.assertTrue(out.get("stored"))
        self.assertEqual(posted[0][0], signed[0], "the posted bytes are not the signed bytes")
        body = json.loads(posted[0][0].decode("utf-8"))
        self.assertEqual((body["owner"], body["platform"], body["head"]), (OWNER, "win32", HEAD))

    def test_a_refused_export_is_not_sent(self):
        posted = []
        out = PC.publish(OWNER, "k", run=lambda a, t: (2, "EXPORT REFUSED: dirty"), post=lambda *a: posted.append(a),
                         sign=lambda p, r: ({}, {"signed": True}))
        self.assertEqual(posted, [])
        self.assertIn("refused", out["why"])


class TheCarrierWaitsWhereTheProverWould(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import control_app as CA
        cls.CA = CA

    def due(self, sp, state=None, head=HEAD, now=10000, platform="win32"):
        return self.CA._proof_carrier_due(sp, state or {"take": {}, "publish": {}}, head, now, platform)[0]

    def test_it_waits_while_he_plays_or_nobody_knows_or_memory_is_short(self):
        ok = {"playing": False, "freeMb": 4000, "owed": 3}
        self.assertEqual(self.due(ok), "take")
        self.assertIsNone(self.due(dict(ok, playing=True)), "the carrier ran beside his game")
        self.assertIsNone(self.due(dict(ok, playing=None)), "an UNKNOWN play state was read as permission")
        self.assertIsNone(self.due(dict(ok, freeMb=500)), "the carrier ran under the prover's memory floor")
        self.assertIsNone(self.due(ok, platform="darwin"), "a PC with no same-platform peer carried proofs")
        self.assertIsNone(self.due(ok, head=None))
        self.assertIsNone(self.due(ok, state={"running": True, "take": {}, "publish": {}}))

    def test_it_takes_first_and_does_not_repeat_itself_at_one_head(self):
        sp = {"playing": False, "freeMb": 4000, "owed": 3}
        self.assertEqual(self.due(sp, {"take": {HEAD: 10000 - 60}, "publish": {}}), "publish",
                         "a take a minute ago was taken again")
        self.assertIsNone(self.due(sp, {"take": {HEAD: 10000 - 60}, "publish": {HEAD: 10000 - 60}}))
        self.assertEqual(self.due(dict(sp, owed=0)), "publish", "with nothing owed it does not post its own")


RED_PROOF = [
    {"why": "#186 step 3 - proofs ride a key nobody registered (trust on first use)",
     "file": "functions/api/proofs.js",
     "find": "  if (registered === null) return refuse(owner + \" has no registered key - proofs ride only a key the roster already trusts\");\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "#186 step 3 - a body the key did not sign is stored",
     "file": "functions/api/proofs.js",
     "find": "  if (!intent.verified) return refuse(intent.refused || \"the signature did not verify\");\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "#186 step 3 - an export whose manifest names another head is stored",
     "file": "functions/api/proofs.js",
     "find": "      || !ex.export || typeof ex.export !== \"object\" || ex.export.head !== head) {\n",
     "replace": "      || !ex.export || typeof ex.export !== \"object\") {\n",
     "matches": 1, "needs": "node"},
    {"why": "#186 step 3 - the same head spends a KV write every time it is carried",
     "file": "functions/api/proofs.js",
     "find": "  if (prev && prev.head === head && typeof prev.at === \"number\" && now - prev.at < SAME_HEAD_GAP_MS) {\n",
     "replace": "  if (false) {\n",
     "matches": 1, "needs": "node"},
    {"why": "#186 step 3 - another platform's proofs are imported",
     "file": "tv/proof_carrier.py",
     "find": "        if meta.get(\"platform\") != platform:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "#186 step 3 - an export carried at another HEAD is imported",
     "file": "tv/proof_carrier.py",
     "find": "        if meta.get(\"head\") != head:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "#186 step 3 - an export no key signed is posted",
     "file": "tv/proof_carrier.py",
     "find": "    if not (isinstance(signing, dict) and signing.get(\"signed\")):\n",
     "replace": "    if False:\n",
     "matches": 1},
    {"why": "#186 step 3 - the carrier runs beside his game, or when nobody knows whether he plays",
     "file": "tv/control_app.py",
     "find": "    if sp.get(\"playing\") is not False:\n        return None, \"he is playing",
     "replace": "    if sp.get(\"playing\") is True:\n        return None, \"he is playing",
     "matches": 1},
    {"why": "#186 step 3 - the carrier runs under the prover's memory floor",
     "file": "tv/control_app.py",
     "find": "    if not isinstance(free, (int, float)) or isinstance(free, bool) or free < floor:\n",
     "replace": "    if False:\n",
     "matches": 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
