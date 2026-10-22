#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-2510..REG-2515 (#95, #112) - a roster publish is signed, and a forgery is refused.

His ruling, 2026-10-22: deploy signed roster publishing once the cross-language (Python/JS) signature
test passes; trust-on-first-use; never stop a PC from publishing. THIS FILE IS THAT TEST. Python signs
(both signers: `cryptography` where it is installed, the RFC 8032 signer everywhere) and node runs the
REAL functions/api/roster.js onRequestPost and onRequestGet against a stand-in KV, with the two headers.

What it holds, one acceptance line of the build each:
  * unsigned, no key registered: stored intentVerified:false, so a PC that has not updated still publishes
  * signed, no key registered: the key is registered and the row is stored intentVerified:true
  * after that, unsigned / another key / one flipped bit: each refused, and the KV is byte-identical
  * RFC 8032 section 7.1 vectors pass on both signers, and node verifies them
  * 200 random bodies up to MAX_BODY sign here and verify in node; the two signers agree on every one
  * a string with an emoji no longer reads corrupt (the hash walks UTF-16 units, as the worker does)
  * the key never appears in a response, a receipt, a page, a header or a body
  * a boot publish goes even when nothing changed, so a forged row is healed
  * intentVerified travels with every view, the cache file, the panel's payload and roster_html, and a
    row published before signing reads UNKNOWN
  * the boot sweep of d2jsp scratch (#112) is called exactly once, synchronously, inside a guard

VENUES. Every case that runs roster.js needs node; where node is absent it SKIPS and says so, and its
red-proofs declare needs: node. `cryptography` is needed only for the agreement half; where it is absent
that case SKIPS and says so - never a silent pass. CI's tv-tests job installs it.
"""

import ast
import base64
import html
import io
import json
import os
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import roster_publish as RP  # noqa: E402
import roster_sign as RS  # noqa: E402
from console_safe import enable  # noqa: E402

enable()

NODE = shutil.which("node")
ROSTER_JS = os.path.join(ROOT, *"functions/api/roster.js".split("/"))
APP = os.path.join(HERE, "control_app.py")
DOCTOR = os.path.join(HERE, "console_doctor.py")
OWNER = "Konyo · Mac"
MAX_BODY = 80000
SIGNATURE_HINT = "the key registered for this owner did not sign this publish"
STORAGE_HINT = "this is the storage refusing a write"

#: RFC 8032 section 7.1: TEST 1, TEST 2, TEST 3 and TEST SHA(abc) - secret, public, message, signature.
RFC8032 = (
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
     "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
     "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
    ("c5aa8df43f9f837bedb7442f31dcb7b166d38535076f094b85ce3a2e0b4458f7",
     "fc51cd8e6218a1a38da47ed00230f0580816ed13ba3303ac5deb911548908025",
     "af82",
     "6291d657deec24024827e69c3abe01a30ce548a284743a445e3680d7db5ac3ac18ff9b538d16f290ae67f760984dc6594a7c15e9716ed28dc027beceea1ec40a"),
    ("833fe62409237b9d62ec77587520911e9a759cec1d19755b7da901b96dca3d42",
     "ec172b93ad5e563bf4932c70e1245034c35467ef2efd4d64ebf819683467e2bf",
     "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a"
     "2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
     "dc2a4459e7369633a52b1bf277839a00201009a3efbf3ecb69bea2186c26b58909351fc9ac90b3ecfdfbc7c66431e0303dca179c138ac17ad9bef1177331a704"),
)

# The worker, run as it ships. Each step posts EXACT bytes (base64 here, so nothing re-serialises them)
# with its own headers; `fresh` starts a new store (optionally seeded). Every step reports what it wrote
# and a digest of every KV value before and after, so "nothing was stored" is measured, not assumed.
_HARNESS = r"""
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
const CFG = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const bytes = (s) => new Uint8Array(Buffer.from(s || '', 'base64'));
const digest = (s) => createHash('sha256').update(s).digest('hex');
const seeded = (seed) => new Map(Object.entries(seed || {}).map(([k, v]) => [k, typeof v === 'string' ? v : JSON.stringify(v)]));
let store = seeded(CFG.seed);
let puts = [];
const kv = {
  async get(n) { return store.has(n) ? store.get(n) : null; },
  async put(n, v) { puts.push(n); store.set(n, v); },
};
const snap = () => { const o = {}; for (const [k, v] of store.entries()) o[k] = digest(v); return o; };
const parsed = (v) => { try { return JSON.parse(v); } catch (e) { return v; } };
const mod = await import(pathToFileURL(CFG.file).href);
const out = { steps: [], verify: [], records: null, got: null };
for (const step of (CFG.steps || [])) {
  if (step.fresh) store = seeded(step.seed);
  puts = [];
  const before = snap();
  const req = new Request('https://bull-4-u.com/api/roster', {
    method: 'POST', body: bytes(step.raw),
    headers: Object.assign({ 'content-type': 'application/json' }, step.headers || {}) });
  const res = await mod.onRequestPost({ request: req, env: { TZ_HISTORY: kv }, waitUntil() {} });
  const reply = JSON.parse(await res.text());
  const one = { status: res.status, reply: reply, puts: puts, before: before, after: snap() };
  if (CFG.everyRecord) { one.records = {}; for (const [k, v] of store.entries()) one.records[k] = parsed(v); }
  out.steps.push(one);
}
for (const v of (CFG.verify || [])) {
  let ok = null, err = null;
  try {
    const key = await crypto.subtle.importKey('raw', bytes(v.pub), { name: 'Ed25519' }, false, ['verify']);
    ok = await crypto.subtle.verify({ name: 'Ed25519' }, key, bytes(v.sig), bytes(v.msg));
  } catch (e) { err = String((e && e.name) || e); }
  out.verify.push({ ok: ok, err: err });
}
out.records = {};
for (const [k, v] of store.entries()) out.records[k] = parsed(v);
if (CFG.get) {
  const res = await mod.onRequestGet({ request: new Request('https://bull-4-u.com/api/roster', { method: 'GET' }),
                                       env: { TZ_HISTORY: kv }, waitUntil() {} });
  out.got = { status: res.status, body: JSON.parse(await res.text()) };
}
process.stdout.write(JSON.stringify(out));
"""


def _read(path):
    with io.open(path, encoding="utf-8") as fh:
        return fh.read()


def _need_node(case):
    if not NODE:
        case.skipTest("node is absent - roster.js cannot be run on this PC, so this case is UNMEASURED "
                      "here, not passed")


def _node(cfg, timeout=240):
    cfg = dict(cfg, file=ROSTER_JS)
    with tempfile.TemporaryDirectory(prefix="tvd_roster_sig_") as d:
        harness = os.path.join(d, "h.mjs")
        with io.open(harness, "w", encoding="utf-8") as fh:
            fh.write(_HARNESS)
        conf = os.path.join(d, "cfg.json")
        with io.open(conf, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh)
        r = subprocess.run([NODE, harness, conf], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    if r.returncode != 0:
        raise AssertionError("the roster harness failed rc=%s\n%s" % (r.returncode, r.stderr[-2000:]))
    return json.loads(r.stdout)


def _b64(raw):
    return base64.b64encode(bytes(raw)).decode("ascii")


def _raw(body):
    """The bytes the console posts: _roster_post's own serialiser."""
    return json.dumps(body, ensure_ascii=False).encode("utf-8")


def _body(n=1, boot=True, signed_at=1790000000000, name="Sorceress"):
    return {"owner": OWNER, "boot": boot, "signedAt": signed_at,
            "sections": {"characters": {"asOf": 1000, "counts": n,
                                        "rows": [{"name": name, "cls": "Sorceress", "level": n}]}}}


def _step(raw, headers=None, fresh=False, seed=None):
    one = {"raw": _b64(raw), "headers": dict(headers or {})}
    if fresh:
        one["fresh"] = True
        one["seed"] = seed or {}
    return one


def _flip_one_bit(raw):
    """One bit of one digit of signedAt: a digit XOR 1 is still a digit, so the body is still JSON and
    the only thing a refusal can be about is the signature."""
    at = raw.index(b'"signedAt":') + len(b'"signedAt":')
    while raw[at:at + 1] == b" ":
        at += 1
    at += 3
    if not raw[at:at + 1].isdigit():
        raise AssertionError("the fixture's signedAt is not a 4+ digit number")
    return raw[:at] + bytes([raw[at] ^ 1]) + raw[at + 1:]


def _key(folder):
    """A real key file made by the real code, in a fixture folder. -> (path, seed, pub)"""
    path = RS.key_path_in(folder)
    key, why, made = RS.load_or_create(path)
    if key is None:
        raise AssertionError("no fixture key could be made: %s" % why)
    with io.open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return path, RS.unb64u(data["seed"]), RS.unb64u(data["pub"])


def _registered(pub):
    return {"rosterkey:" + OWNER: {"pub": RS.b64u(pub), "keyId": RS.key_id(pub), "at": 1}}


def _secret_forms(seed):
    """Every spelling of a seed a leak could take."""
    return (RS.b64u(seed), base64.b64encode(seed).decode("ascii"), seed.hex(), seed.hex().upper())


class TheTwoSignersAgree(unittest.TestCase):
    """RFC 8032 is deterministic: two correct signers write the same 64 bytes. That pair is the
    corroborator, and node's crypto.subtle (the worker's own verifier) is the judge."""

    def test_the_rfc8032_vectors_pass_on_the_pure_signer(self):
        for secret, public, message, signature in RFC8032:
            seed, msg = bytes.fromhex(secret), bytes.fromhex(message)
            self.assertEqual(RS.pure_public(seed).hex(), public, "RFC 8032 public key, TEST %s" % public[:8])
            sig = RS.pure_sign(seed, msg)
            self.assertEqual(sig.hex(), signature, "RFC 8032 signature, TEST %s" % public[:8])
            self.assertTrue(RS.pure_verify(bytes.fromhex(public), msg, sig))
            bad = bytearray(sig)
            bad[7] ^= 1
            self.assertFalse(RS.pure_verify(bytes.fromhex(public), msg, bytes(bad)))

    def test_the_rfc8032_vectors_pass_on_cryptography(self):
        if not RS.have_cryptography():
            self.skipTest("cryptography is not installed on this PC - the second signer is UNMEASURED here, "
                          "not passed (CI's tv-tests job installs it)")
        for secret, public, message, signature in RFC8032:
            seed, msg = bytes.fromhex(secret), bytes.fromhex(message)
            self.assertEqual(RS.crypto_public(seed).hex(), public)
            self.assertEqual(RS.crypto_sign(seed, msg).hex(), signature)

    def test_node_verifies_the_rfc8032_vectors(self):
        _need_node(self)
        checks = []
        for _secret, public, message, signature in RFC8032:
            sig = bytes.fromhex(signature)
            checks.append({"pub": _b64(bytes.fromhex(public)), "sig": _b64(sig), "msg": _b64(bytes.fromhex(message))})
            bad = bytearray(sig)
            bad[40] ^= 1
            checks.append({"pub": _b64(bytes.fromhex(public)), "sig": _b64(bytes(bad)),
                           "msg": _b64(bytes.fromhex(message))})
        got = _node({"verify": checks})["verify"]
        self.assertEqual([g["ok"] for g in got], [True, False] * len(RFC8032),
                         "node's crypto.subtle did not accept the RFC 8032 vectors and refuse a flipped bit: %r" % got)

    def test_the_two_signers_agree_on_two_hundred_bodies(self):
        if not RS.have_cryptography():
            self.skipTest("cryptography is not installed on this PC - the agreement half is UNMEASURED here, "
                          "not passed (CI's tv-tests job installs it)")
        got = _sample()
        self.assertEqual(RS.crypto_public(got["seed"]), got["pub"])
        for i, raw in enumerate(got["bodies"]):
            self.assertEqual(RS.crypto_sign(got["seed"], raw), got["sigs"][i],
                             "the two signers wrote different signatures for body %d (%d bytes)" % (i, len(raw)))

    def test_a_pc_without_cryptography_still_signs(self):
        """tv/install-tvd.ps1 and tv/install-tvd.sh do not install cryptography: Dean, ALT and Wife PC
        sign with the RFC 8032 signer, and a cryptography that raises does not stop a publish."""
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path, seed, pub = _key(d)
            key, _why = RS.load_key(path)
            raw = _raw(_body(3))
            real = RS.crypto_sign
            try:
                RS.crypto_sign = lambda s, m: None
                sig, signer, agree = RS.sign(key, raw)
                self.assertEqual((signer, agree), ("pure-python", None))
                self.assertTrue(RS.pure_verify(pub, raw, sig))

                def boom(s, m):
                    raise ValueError("an OpenSSL this cryptography cannot use")
                RS.crypto_sign = boom
                sig2, signer2, _agree = RS.sign(key, raw)
                self.assertIn("cryptography raised ValueError", signer2)
                self.assertEqual(sig2, sig)
            finally:
                RS.crypto_sign = real


def _random_name(rng):
    pool = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -'"
            "éüßñÆØשלום日本語★✓"
            "\U0001f9ff\U0001f525\U0001f48e\U0001f480")
    return "".join(rng.choice(pool) for _ in range(rng.randint(1, 40))).strip() or "Shako"


_SAMPLE = {}


def _sample():
    """200 random bodies up to MAX_BODY, each signed once by the RFC 8032 signer. Built once a run and
    shared, because both the agreement case and the node case need the same 200."""
    if not _SAMPLE:
        rng = random.Random(9501)
        seed = bytes(rng.getrandbits(8) for _ in range(32))
        bodies = [_random_body(rng, rng.randint(64, MAX_BODY)) for _ in range(200)]
        _SAMPLE.update(seed=seed, pub=RS.pure_public(seed), bodies=bodies,
                       sigs=[RS.pure_sign(seed, raw) for raw in bodies])
    return _SAMPLE


def _random_body(rng, target):
    """A roster body the worker accepts, as close under `target` bytes as its rows allow (<= MAX_BODY)."""
    base = {"owner": OWNER, "boot": True, "signedAt": rng.randint(10 ** 12, 2 * 10 ** 12),
            "sections": {"characters": {"asOf": rng.randint(1, 10 ** 12), "counts": 0, "rows": []}}}
    used = len(_raw(base)) + 8
    rows = []
    while True:
        row = {"name": _random_name(rng), "level": rng.randint(1, 99)}
        size = len(_raw(row)) + 2                      # json.dumps writes ", " between rows
        if used + size > target:
            break
        rows.append(row)
        used += size
    if not rows:
        rows.append({"name": "Shako", "level": 1})
    while True:
        base["sections"]["characters"]["rows"] = rows
        base["sections"]["characters"]["counts"] = len(rows)
        raw = _raw(base)
        if len(raw) <= min(target, MAX_BODY) or len(rows) == 1:
            break
        rows = rows[:-1]
    if len(raw) > MAX_BODY:
        raise AssertionError("the fixture built a body over MAX_BODY (%d bytes)" % len(raw))
    return raw


class TheWorkerChecksTheBytesItWasSent(unittest.TestCase):
    """roster.js, run as it ships, against signatures made here."""

    def test_two_hundred_random_bodies_sign_here_and_verify_in_node(self):
        _need_node(self)
        got = _sample()
        pub = got["pub"]
        heads = {"X-Roster-Key": RS.b64u(pub)}
        steps, checks, sizes = [], [], []
        for raw, sig in zip(got["bodies"], got["sigs"]):
            sizes.append(len(raw))
            signed = dict(heads, **{"X-Roster-Sig": RS.b64u(sig)})
            steps.append(_step(raw, signed, fresh=True))                                    # no key yet
            steps.append(_step(_flip_one_bit(raw), signed, fresh=True, seed=_registered(pub)))  # key held
            checks.append({"pub": _b64(pub), "sig": _b64(sig), "msg": _b64(raw)})
        self.assertGreater(max(sizes), MAX_BODY - 2000, "the sample never came near MAX_BODY")
        v = _node({"steps": steps, "verify": checks})
        self.assertEqual([c["ok"] for c in v["verify"]], [True] * 200,
                         "node's crypto.subtle refused a signature made here")
        for i in range(200):
            good, bad = v["steps"][2 * i], v["steps"][2 * i + 1]
            self.assertEqual((good["reply"].get("ok"), good["reply"].get("intentVerified"),
                              good["reply"].get("registered")), (True, True, True),
                             "body %d (%d bytes) did not verify through roster.js: %r"
                             % (i, sizes[i], good["reply"]))
            self.assertIs(bad["reply"].get("ok"), False, "a flipped bit in body %d was stored" % i)
            self.assertIn("did not verify", bad["reply"].get("why", ""))
            self.assertEqual(bad["puts"], [], "a refused body %d wrote %r" % (i, bad["puts"]))

    def test_the_acceptance_sequence(self):
        """unsigned -> stored false; signed -> registered, true; then unsigned / another key / one flipped
        bit -> refused with the KV byte-identical; signed again -> true. GET says so."""
        _need_node(self)
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path_a, seed_a, pub_a = _key(os.path.join(d, "a"))
            path_b, seed_b, pub_b = _key(os.path.join(d, "b"))
            raws = [_raw(_body(n, signed_at=1790000000000 + n)) for n in range(1, 7)]
            heads = {n: RS.sign_headers(path_a, raws[n - 1])[0] for n in (2, 5, 6)}
            other, _ = RS.sign_headers(path_b, raws[3])
            steps = [_step(raws[0]),                                  # 0 unsigned, no key
                     _step(raws[1], heads[2]),                        # 1 signed A, no key: TOFU
                     _step(raws[2]),                                  # 2 unsigned after that
                     _step(raws[3], other),                           # 3 another key
                     _step(_flip_one_bit(raws[4]), heads[5]),         # 4 one bit flipped
                     _step(raws[5], heads[6])]                        # 5 signed A again
            v = _node({"steps": steps, "get": True, "everyRecord": True})
        rk, kk = "roster:" + OWNER, "rosterkey:" + OWNER
        s = v["steps"]
        self.assertEqual((s[0]["reply"]["ok"], s[0]["reply"]["stored"], s[0]["reply"]["intentVerified"]),
                         (True, ["roster"], False), "an unsigned first publish must still be stored: %r" % s[0]["reply"])
        self.assertEqual(s[0]["puts"], [rk])
        self.assertNotIn(kk, s[0]["after"], "an unsigned publish registered a key")
        self.assertIs(s[0]["records"][rk]["intentVerified"], False)
        self.assertEqual((s[1]["reply"]["ok"], s[1]["reply"]["intentVerified"], s[1]["reply"].get("registered")),
                         (True, True, True), "the first signed publish did not register its key: %r" % s[1]["reply"])
        self.assertEqual(s[1]["reply"]["keyId"], RS.key_id(pub_a))
        self.assertEqual(s[1]["puts"], [kk, rk])
        self.assertEqual(s[1]["records"][kk]["pub"], RS.b64u(pub_a))
        for i, word in ((2, "not signed"), (3, "different key"), (4, "did not verify")):
            r = s[i]["reply"]
            self.assertEqual(s[i]["status"], 200)
            self.assertIs(r["ok"], False, "step %d was not refused: %r" % (i, r))
            self.assertIn(word, r["why"])
            self.assertIn(SIGNATURE_HINT, r["hint"], "step %d's refusal carried the wrong hint" % i)
            self.assertNotIn(STORAGE_HINT, r["hint"])
            self.assertEqual(s[i]["puts"], [], "a refused step %d wrote %r" % (i, s[i]["puts"]))
            self.assertEqual(s[i]["after"], s[i]["before"], "a refused step %d changed the KV" % i)
        self.assertEqual(s[3]["reply"].get("offered"), RS.key_id(pub_b))
        self.assertEqual(s[3]["reply"].get("keyId"), RS.key_id(pub_a))
        self.assertEqual((s[5]["reply"]["ok"], s[5]["reply"]["intentVerified"], s[5]["reply"]["stored"]),
                         (True, True, ["roster"]))
        self.assertNotIn("registered", s[5]["reply"], "a registered key was registered again")
        rec = v["records"][rk]
        self.assertEqual((rec["intentVerified"], rec["keyId"], rec["signedAt"]),
                         (True, RS.key_id(pub_a), 1790000000006))
        mine = [r for r in v["got"]["body"]["owners"] if r["owner"] == OWNER][0]
        self.assertEqual((mine["corrupt"], mine["intentVerified"], mine["keyId"]), (False, True, RS.key_id(pub_a)))
        view = [r for r in RP.view_of(v["got"]["body"]["owners"], rec["t"]) if r["owner"] == OWNER][0]
        self.assertEqual((view["corrupt"], view["intentVerified"], view["keyId"]), (False, True, RS.key_id(pub_a)))
        # the key never leaves its file: not in a body, a header, a reply, a record or the page
        seen = json.dumps(v, ensure_ascii=False) + json.dumps(heads) + json.dumps(other)
        seen += "".join(r.decode("utf-8") for r in raws)
        seen += RP.roster_html({"ok": True, "fetched": True, "now": rec["t"], "owners": [view]})
        for seed in (seed_a, seed_b):
            for form in _secret_forms(seed):
                self.assertNotIn(form, seen, "a private key reached a body, a header, a reply or a record")

    def test_no_key_and_a_bad_signature_is_stored_unverified_and_registers_nothing(self):
        """Anyone could post that row unsigned, and a signer bug must not stop a PC from publishing - so
        it is stored, said false, and the key is NOT registered. The reply says why."""
        _need_node(self)
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path, _seed, pub = _key(d)
            raw = _raw(_body(2))
            heads, _ = RS.sign_headers(path, raw)
            half = {"X-Roster-Key": heads["X-Roster-Key"]}
            v = _node({"steps": [_step(_flip_one_bit(raw), heads, fresh=True),
                                 _step(raw, half, fresh=True),
                                 _step(raw, half, fresh=True, seed=_registered(pub))]})
        rk, kk = "roster:" + OWNER, "rosterkey:" + OWNER
        for i in (0, 1):
            r = v["steps"][i]["reply"]
            self.assertEqual((r["ok"], r["intentVerified"], r["sig"]), (True, False, "bad"), r)
            self.assertTrue(r.get("sigWhy"), "a bad signature was stored without saying why")
            self.assertNotIn("registered", r)
            self.assertEqual(v["steps"][i]["puts"], [rk], "a bad signature registered a key")
        r = v["steps"][2]["reply"]
        self.assertIs(r["ok"], False, "half a signature was stored for an owner whose key is registered")
        self.assertEqual(v["steps"][2]["puts"], [])
        self.assertNotIn(kk, v["steps"][0]["after"])

    def test_a_key_konyo_put_there_by_hand_is_honoured(self):
        """A key changes only from the Mac: a pre-seeded key - the record this file writes, or the bare
        base64url string - is the owner's from then on, and a key that cannot be read refuses rather than
        letting anyone in."""
        _need_node(self)
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path, _seed, pub = _key(d)
            raw = _raw(_body(3))
            heads, _ = RS.sign_headers(path, raw)
            kk = "rosterkey:" + OWNER
            v = _node({"steps": [_step(raw, heads, fresh=True, seed={kk: RS.b64u(pub)}),
                                 _step(raw, {}, fresh=True, seed={kk: RS.b64u(pub)}),
                                 _step(raw, heads, fresh=True, seed={kk: "not a key"}),
                                 _step(raw, heads, fresh=True, seed={kk: "null"})]})
        hand, bare, junk, empty = (st["reply"] for st in v["steps"])
        self.assertEqual((hand["ok"], hand["intentVerified"]), (True, True), hand)
        self.assertNotIn("registered", hand, "a key Konyo put there was registered over")
        self.assertEqual(v["steps"][0]["puts"], ["roster:" + OWNER])
        self.assertIs(bare["ok"], False, "an unsigned publish got past a hand-placed key")
        self.assertIs(junk["ok"], False, "a key that cannot be read let a publish through")
        self.assertIn("unreadable", junk["why"])
        self.assertEqual(v["steps"][2]["puts"], [])
        self.assertIs(empty["ok"], False, "a key entry holding JSON null was read as no key at all - TOFU reopened")
        self.assertEqual(v["steps"][3]["puts"], [])

    def test_a_row_published_before_signing_reads_unknown(self):
        """A record written before #95 has no intentVerified. GET passes none, and every view shows
        UNKNOWN ('published before signing') - never verified, never unverified."""
        _need_node(self)
        sections = {"characters": {"asOf": 10, "counts": 1, "rows": [{"name": "Sorceress"}]}}
        digest = RP.hash_of(RP.packed(RP.for_hash(sections)))
        seed = {"roster:Dean": {"owner": "Dean", "t": 10, "day": "2000-01-01", "n": 1, "hash": digest,
                                "sections": sections}}
        got = _node({"seed": seed, "get": True})["got"]["body"]
        dean = [r for r in got["owners"] if r["owner"] == "Dean"][0]
        self.assertIs(dean["corrupt"], False)
        self.assertNotIn("intentVerified", dean, "a row published before signing was given a verdict")
        view = [r for r in RP.view_of(got["owners"], 10) if r["owner"] == "Dean"][0]
        self.assertIsNone(view["intentVerified"])
        page = RP.roster_html({"ok": True, "fetched": True, "now": 10, "owners": [view]})
        self.assertIn("signature UNKNOWN: published before signing", page)
        self.assertNotIn("signature verified", page)
        self.assertNotIn("NOT signature-verified", page)

    def test_a_boot_publish_heals_a_forged_row(self):
        """A row someone else wrote in this PC's name (before its key was registered) is overwritten by the
        PC's next boot publish, even though nothing changed on the PC."""
        _need_node(self)
        now = 1790000000000
        mine = RP.sections_from({"characters": {"read": True, "asOf": 1000, "counts": 1,
                                                 "rows": [{"name": "Sorceress", "level": 90}]}})
        state = {"hash": RP.hash_of(RP.packed(RP.for_hash(mine))), "at": now - 60000}
        body, why = RP.due(state, OWNER, mine, now, True)
        self.assertEqual(why, "post")
        forged = _body(99, name="Forged")
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path, _seed, _pub = _key(d)
            raw = _raw(body)
            heads, signing = RS.sign_headers(path, raw)
            self.assertIs(signing["signed"], True)
            v = _node({"steps": [_step(_raw(forged)), _step(raw, heads)]})
        rec = v["records"]["roster:" + OWNER]
        self.assertEqual(rec["sections"]["characters"]["rows"][0]["name"], "Sorceress",
                         "the forged row survived the PC's boot publish")
        self.assertIs(rec["intentVerified"], True)

    def test_an_emoji_round_trips_without_reading_corrupt(self):
        _need_node(self)
        body = _body(1, name="Ber \U0001f9ff rune")
        v = _node({"steps": [_step(_raw(body))], "get": True})
        rec = v["records"]["roster:" + OWNER]
        self.assertEqual(rec["hash"], RP.hash_of(RP.packed(RP.for_hash(rec["sections"]))),
                         "the worker and this file hash the same emoji row differently")
        view = [r for r in RP.view_of(v["got"]["body"]["owners"], rec["t"]) if r["owner"] == OWNER][0]
        self.assertIs(view["corrupt"], False, "an emoji in a row made its owner read CORRUPT (#95)")


class TheHashWalksWhatTheWorkerWalks(unittest.TestCase):

    def test_an_emoji_hashes_as_the_worker_hashes_it(self):
        """REG-2511 - measured in node: roster.js hashOf('Ber 🧿 rune') is 83534eb3. Walking code points
        gave a8b9dc5d, so view_one called every viewer's copy of that owner CORRUPT."""
        self.assertEqual(RP.hash_of("Ber \U0001f9ff rune"), "83534eb3")
        self.assertEqual(RP.hash_of("abc"), "1a47e90b", "an ASCII digest moved")
        self.assertEqual(RP.hash_of("Tal Rune ★"), "b51575f1", "a BMP digest moved")
        sections = {"characters": {"asOf": 5, "counts": 1, "rows": [{"name": "Ber \U0001f9ff rune"}]}}
        row = {"owner": "Dean", "published": True, "corrupt": False, "t": 5,
               "hash": RP.hash_of(RP.packed(RP.for_hash(sections))), "sections": sections}
        self.assertIs(RP.view_one("Dean", row, 5)["corrupt"], False)


class TheBootPublishGoesEvenWhenUnchanged(unittest.TestCase):

    def test_boot_posts_an_unchanged_body_and_a_tick_does_not(self):
        now = 1_000_000
        sections = RP.sections_from({"characters": {"read": True, "asOf": 1000, "counts": 1,
                                                     "rows": [{"name": "Sorceress", "level": 1}]}})
        state = {"hash": RP.hash_of(RP.packed(RP.for_hash(sections))), "at": now}
        body, why = RP.due(state, OWNER, sections, now + 1000, True)
        self.assertEqual(why, "post", "REG-2512: an unchanged boot did not post, so a forged row is never healed")
        self.assertEqual((body["boot"], body["signedAt"]), (True, now + 1000))
        quiet, why = RP.due(state, OWNER, sections, now + 1000, False)
        self.assertIsNone(quiet)
        self.assertEqual(why, "unchanged")
        refused = dict(state, refuseAt=now, why="roster would not take this publish: quota")
        held, why = RP.due(refused, OWNER, sections, now + 1000, True)
        self.assertIsNone(held, "a refusal was retried inside the hour")
        self.assertIn("quota", why)


class IntentVerifiedTravelsWithEveryView(unittest.TestCase):

    def _row(self, owner, extra):
        sections = {"characters": {"asOf": 7, "counts": 1, "rows": [{"name": "Shako"}]}}
        row = {"owner": owner, "published": True, "corrupt": False, "t": 7, "sections": sections,
               "hash": RP.hash_of(RP.packed(RP.for_hash(sections)))}
        row.update(extra)
        return row

    def test_view_cache_and_page_carry_each_verdict(self):
        rows = [self._row("Konyo · Mac", {"intentVerified": True, "keyId": "0123456789ab"}),
                self._row("Dean", {"intentVerified": False}),
                self._row("Wife PC", {}),
                self._row("Konyo · ALT", {"intentVerified": "true"})]
        views = RP.view_of(rows, 7)
        by = {v["owner"]: v for v in views}
        self.assertEqual((by["Konyo · Mac"]["intentVerified"], by["Konyo · Mac"]["keyId"]), (True, "0123456789ab"))
        self.assertIs(by["Dean"]["intentVerified"], False)
        self.assertIsNone(by["Wife PC"]["intentVerified"], "a row with no verdict was given one")
        self.assertIsNone(by["Konyo · ALT"]["intentVerified"], "a string was read as a verdict")
        with tempfile.TemporaryDirectory(prefix="tvd_roster_cache_") as d:
            folder = os.path.join(d, "roster_cache")
            bare = dict(by["Konyo · Mac"])
            del bare["intentVerified"]
            RP.write_cache(folder, [bare, by["Dean"], by["Wife PC"]])
            with io.open(os.path.join(folder, RP.cache_file_name("Konyo · Mac")), encoding="utf-8") as fh:
                written = json.load(fh)
            self.assertIn("intentVerified", written, "the cache file left the verdict out, so a reader must guess")
            self.assertIsNone(written["intentVerified"])
            RP.write_cache(folder, views)
            back = {r["owner"]: r for r in RP.read_cache(folder, 7)["owners"]}
        self.assertIs(back["Konyo · Mac"]["intentVerified"], True)
        self.assertEqual(back["Konyo · Mac"]["keyId"], "0123456789ab")
        self.assertIs(back["Dean"]["intentVerified"], False)
        self.assertIsNone(back["Wife PC"]["intentVerified"])
        page = RP.roster_html({"ok": True, "fetched": True, "now": 7, "owners": list(back.values())})
        self.assertIn("signature verified (key 0123456789ab)", page)
        self.assertIn("NOT signature-verified", page)
        self.assertIn("signature UNKNOWN: published before signing", page)


class ThisPCSaysItsOwnLastPublish(unittest.TestCase):

    def test_each_outcome_is_named_with_its_why(self):
        sections = {"characters": {"asOf": 1, "counts": 1}}
        signed = {"signed": True, "keyId": "aaaaaaaaaaaa", "signer": "pure-python", "agree": None}
        cases = [
            ({"ok": True, "stored": ["roster"], "intentVerified": True, "keyId": "aaaaaaaaaaaa", "signing": signed},
             "signed", None),
            ({"ok": False, "why": "roster would not take this publish: Dean has a registered key and this "
                                  "publish was not signed", "hint": "nothing was stored",
              "signing": {"signed": False, "why": "the key file is unreadable (ValueError); it was left as it is"}},
             "refused", "registered key"),
            ({"ok": True, "stored": ["roster"], "intentVerified": False,
              "signing": {"signed": False, "why": "the key could not be written (PermissionError)"}},
             "unsigned", "PermissionError"),
            ({"ok": True, "stored": ["roster"], "intentVerified": False, "sig": "bad",
              "sigWhy": "the signature does not match these bytes", "signing": signed},
             "unverified", "does not match"),
            ({"ok": False, "why": "URLError", "code": None, "signing": signed}, "unreached", "URLError"),
        ]
        for reply, want, words in cases:
            state = RP.apply_reply({}, sections, reply, 50)
            out = RP.publish_outcome(state, 50 + 120000)
            self.assertEqual(out["state"], want, "%r read as %r" % (reply, out))
            if words:
                self.assertIn(words, out["why"])
            page = html.unescape(RP.roster_html({"ok": True, "fetched": False, "owners": [], "me": out}))
            self.assertIn("this PC's last publish", page)
            self.assertIn("this PC has not fetched a roster yet", page)
        self.assertEqual(RP.publish_outcome({"why": "unchanged"}, 1)["state"], "unknown",
                         "a receipt written before signing read as a signed publish")
        self.assertEqual(RP.publish_outcome(None, 1)["state"], "unknown")
        refused = RP.publish_outcome(RP.apply_reply({}, sections, cases[1][0], 50), 50)
        self.assertIn("REFUSED", html.unescape(RP.roster_html({"ok": True, "fetched": False, "me": refused})))
        unsigned = RP.publish_outcome(RP.apply_reply({}, sections, cases[2][0], 50), 50)
        self.assertIn("went UNSIGNED", html.unescape(RP.roster_html({"ok": True, "fetched": False, "me": unsigned})))

    def test_the_panel_route_hands_over_this_pcs_receipt(self):
        src = _read(APP)
        self.assertEqual(src.count('if path == "/api/roster-cache":'), 1)
        at = src.index('if path == "/api/roster-cache":')
        door = src[at:src.index("return\n", at)]
        me = 'data["me"] = _rp.publish_outcome(_roster_state_load(), int(time.time() * 1000))'
        self.assertIn(me, door, "the roster panel no longer carries this PC's own last publish")
        self.assertLess(door.index(me), door.index("roster_html(data)"),
                        "this PC's outcome is added after the page was drawn, so the page cannot show it")


class TheConsoleSignsTheBytesItPosts(unittest.TestCase):
    """_roster_post, cut from control_app.py as it ships and run against a stand-in urllib: what it
    sends is what it signed, and a key it cannot use posts unsigned and says why."""

    @staticmethod
    def _post_fn(sent, answer=b'{"ok": true, "stored": ["roster"]}', fail=None):
        src = _read(APP)
        if src.count("\ndef _roster_post(") != 1:
            raise AssertionError("_roster_post is defined %d times - re-point this law" % src.count("\ndef _roster_post("))
        start = src.index("\ndef _roster_post(") + 1
        code = src[start:src.index("\ndef ", start)]

        class Req(object):
            def __init__(self, url, data=None, headers=None, method=None):
                sent.append({"url": url, "data": data, "headers": dict(headers or {}), "method": method})

        class Resp(object):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read(self):
                return answer

        def urlopen(req, timeout=None):
            if fail:
                raise fail
            return Resp()

        request = types.SimpleNamespace(Request=Req, urlopen=urlopen)
        ns = {"json": json, "urllib": types.SimpleNamespace(request=request)}
        exec(compile(code, APP, "exec"), ns)
        return ns["_roster_post"]

    def test_the_exact_bytes_posted_are_the_bytes_signed(self):
        sent = []
        body = _body(4, name="Ber \U0001f9ff rune")
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path = RS.key_path_in(d)
            reply = self._post_fn(sent)("https://bull-4-u.com/api/roster", body, path)
            _p, seed, pub = _key(d)
        self.assertEqual(len(sent), 1)
        data, heads = sent[0]["data"], sent[0]["headers"]
        self.assertEqual(data, _raw(body), "the console posted bytes other than its own serialisation")
        self.assertIn("X-Roster-Sig", heads, "the console posted unsigned with a usable key (#95)")
        self.assertEqual(RS.unb64u(heads["X-Roster-Key"]), pub)
        self.assertTrue(RS.pure_verify(pub, data, RS.unb64u(heads["X-Roster-Sig"])),
                        "the signature does not cover the bytes that were posted")
        self.assertEqual((reply["signing"]["signed"], reply["signing"]["keyId"]), (True, RS.key_id(pub)))
        state = RP.apply_reply({}, body["sections"], reply, 1)
        out = RP.publish_outcome(state, 1)
        seen = json.dumps([heads, reply, state, out], ensure_ascii=False) + data.decode("utf-8")
        for form in _secret_forms(seed):
            self.assertNotIn(form, seen, "the private key left its file")
        if NODE:
            v = _node({"steps": [_step(data, heads)]})
            self.assertIs(v["steps"][0]["reply"]["intentVerified"], True,
                          "roster.js did not verify what the console sent: %r" % v["steps"][0]["reply"])

    def test_a_key_it_cannot_use_posts_unsigned_and_says_why(self):
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path = RS.key_path_in(d)
            with io.open(path, "w", encoding="utf-8") as fh:
                fh.write("{not a key")
            sent = []
            reply = self._post_fn(sent)("https://bull-4-u.com/api/roster", _body(1), path)
            with io.open(path, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), "{not a key", "an unreadable key file was replaced")
        self.assertNotIn("X-Roster-Sig", sent[0]["headers"])
        self.assertIs(reply["signing"]["signed"], False)
        self.assertIn("unreadable", reply["signing"]["why"])
        sent = []
        none = self._post_fn(sent)("https://bull-4-u.com/api/roster", _body(1))
        self.assertEqual((none["signing"]["signed"], none["signing"]["why"]), (False, "no key path was given"))
        failed = self._post_fn([], fail=OSError("down"))("https://bull-4-u.com/api/roster", _body(1), None)
        self.assertIs(failed["ok"], False)
        self.assertIn("signing", failed, "a failed post lost what the signing did")

    def test_the_publish_loop_hands_over_this_pcs_key_path(self):
        """The path is spelled out in control_app so test_every_decision_file_is_ignored asks git's own
        matcher about it; this pins that spelling to roster_sign.KEY_FILE, which the doctor reads."""
        src = _read(APP)
        once = src.split("def _roster_publish_once(", 1)[1].split("def _roster_publish_loop", 1)[0]
        call = 'reply = _roster_post("https://bull-4-u.com/api/roster", body, os.path.join(_log_root(), "%s"))'
        self.assertEqual(once.count(call % RS.KEY_FILE), 1,
                         "the publish loop no longer hands this PC's key path (roster_sign.KEY_FILE) to the post")
        self.assertEqual(RS.key_path_in("root"), os.path.join("root", RS.KEY_FILE))

    def test_the_key_file_is_never_committed(self):
        """This repo is PUBLIC: a committed seed lets anyone sign as that PC for good."""
        lines = [ln.strip() for ln in _read(os.path.join(ROOT, ".gitignore")).splitlines()]
        for name in ("tv/" + RS.KEY_FILE, "tv/" + RS.KEY_FILE + ".tmp"):
            self.assertIn(name, lines, "%s is not ignored - one `git add -A` publishes a private key" % name)
            self.assertNotIn("!" + name, lines)


class TheKeyStaysOnThisPC(unittest.TestCase):

    def test_a_key_is_made_once_kept_private_and_never_replaced(self):
        with tempfile.TemporaryDirectory(prefix="tvd_roster_key_") as d:
            path = RS.key_path_in(d)
            key, why, made = RS.load_or_create(path, 123)
            self.assertIsNotNone(key, why)
            self.assertTrue(made)
            again, _why, made2 = RS.load_or_create(path)
            self.assertFalse(made2, "a second load made a second key")
            self.assertEqual(again.pub, key.pub)
            with io.open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(sorted(data), ["created", "pub", "seed", "v"])
            self.assertEqual(data["created"], 123)
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600, "the key file is readable by others")
            seed = RS.unb64u(data["seed"])
            shown = repr(key) + str(key) + json.dumps(key.view()) + json.dumps(RS.public_view(path)[0])
            for form in _secret_forms(seed):
                self.assertNotIn(form, shown, "the key's own repr or view carries its seed")
            self.assertFalse(os.path.exists(path + ".tmp"), "the atomic-write partner was left behind")
            with io.open(path, "w", encoding="utf-8") as fh:
                json.dump(dict(data, pub=RS.b64u(b"\x01" * 32)), fh)
            broken, why, made3 = RS.load_or_create(path)
            self.assertIsNone(broken)
            self.assertFalse(made3)
            self.assertIn("does not match its seed", why)
            with io.open(path, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["pub"], RS.b64u(b"\x01" * 32),
                                 "a key file that does not add up was replaced - a registered owner would "
                                 "then be refused with the evidence gone")


class TheDoctorAsksIt(unittest.TestCase):

    def test_the_verdict_names_what_is_wrong(self):
        ok_me = {"state": "signed", "intentVerified": True, "keyId": "aaaaaaaaaaaa", "agree": True}
        fetched = {"ok": True, "fetched": True, "owners": [
            {"owner": OWNER, "published": True, "corrupt": False, "intentVerified": True, "keyId": "aaaaaaaaaaaa"},
            {"owner": "Dean", "published": True, "corrupt": False, "intentVerified": True, "keyId": "bbbbbbbbbbbb"},
            {"owner": "Wife PC", "published": False}]}
        st, why = RP.signing_verdict(fetched, ok_me, OWNER, "aaaaaaaaaaaa")
        self.assertEqual(st, "ok", why)
        unsigned = json.loads(json.dumps(fetched))
        unsigned["owners"][1]["intentVerified"] = False
        st, why = RP.signing_verdict(unsigned, ok_me, OWNER, "aaaaaaaaaaaa")
        self.assertEqual(st, "missing")
        self.assertIn("Dean", why)
        before = json.loads(json.dumps(fetched))
        del before["owners"][1]["intentVerified"]
        self.assertEqual(RP.signing_verdict(before, ok_me, OWNER, "aaaaaaaaaaaa")[0], "unknown",
                         "a row published before signing read as verified")
        st, why = RP.signing_verdict(fetched, dict(ok_me, state="refused", why="no"), OWNER, "aaaaaaaaaaaa")
        self.assertEqual(st, "missing")
        self.assertIn("REFUSED", why)
        st, why = RP.signing_verdict(fetched, ok_me, OWNER, "cccccccccccc")
        self.assertEqual(st, "missing")
        self.assertIn("resets that owner's key", why)
        self.assertEqual(RP.signing_verdict({"ok": True, "fetched": False}, ok_me, OWNER, None)[0], "unknown")
        self.assertEqual(RP.signing_verdict(fetched, dict(ok_me, agree=False), OWNER, "aaaaaaaaaaaa")[0], "missing")
        self.assertEqual(RP.signing_verdict(fetched, {"state": "unknown"}, None, None)[0], "ok",
                         "a PC with no roster label publishes nothing and is asked only about the others")

    def test_the_doctor_row_reads_this_pcs_own_stores(self):
        with tempfile.TemporaryDirectory(prefix="tvd_roster_doctor_") as d:
            key_path, _seed, pub = _key(d)
            kid = RS.key_id(pub)
            receipt = RP.apply_reply({}, {}, {"ok": True, "stored": ["roster"], "intentVerified": True, "keyId": kid,
                                              "signing": {"signed": True, "keyId": kid, "agree": True}}, 5)
            views = RP.view_of([{"owner": OWNER, "published": True, "corrupt": False, "t": 5,
                                 "hash": RP.hash_of(RP.packed(RP.for_hash({}))), "intentVerified": True,
                                 "keyId": kid}], 5)
            RP.write_cache(os.path.join(d, "roster_cache"), views)
            ca = types.SimpleNamespace(
                _roster_state_load=lambda: receipt,
                _roster_cache_payload=lambda: RP.read_cache(os.path.join(d, "roster_cache"), 5),
                _roster_claimed_name=lambda: "Konyo", _roster_platform=lambda: "mac", _log_root=lambda: d)
            self.assertEqual(RP.doctor_row(ca, 5)[0], "ok")
            refused = RP.apply_reply(receipt, {}, {"ok": False, "why": "roster would not take this publish: x",
                                                   "hint": "nothing was stored", "signing": {"signed": True}}, 6)
            ca._roster_state_load = lambda: refused
            st, why = RP.doctor_row(ca, 6)
            self.assertEqual(st, "missing")
            self.assertIn("REFUSED", why)
            self.assertFalse(os.path.exists(key_path + ".tmp"))
        doctor = _read(DOCTOR)
        self.assertEqual(doctor.count('    ("every roster publish is signed", _check_every_roster_publish_is_signed),\n'), 1,
                         "the doctor no longer asks whether every roster publish is signed")
        fn = doctor[doctor.index("def _check_every_roster_publish_is_signed("):]
        fn = fn[:fn.index("\ndef ")]
        self.assertIn("_rp.doctor_row(_serving_console(_ca)", fn)


class TheBootSweepsD2jspScratch(unittest.TestCase):
    """#112 - a console killed mid d2jsp op leaves a scratch Chrome holding his session. main() calls the
    existing d2jsp_chrome._sweep_stale_scratch() once, synchronously, inside a guard that never raises."""

    def test_the_sweep_is_called_once_and_guarded(self):
        src = _read(APP)
        self.assertEqual(src.count("_sweep_stale_scratch("), 1, "the boot sweep is called more or less than once")
        self.assertEqual(src.count("\ndef main("), 1)
        start = src.index("\ndef main(") + 1
        main = ast.parse(src[start:src.index('\nif __name__ == "__main__":', start)]).body[0]
        hits = []
        for st in main.body:
            for node in ast.walk(st):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "_sweep_stale_scratch"):
                    hits.append(st)
        self.assertEqual(len(hits), 1, "main() does not call the sweep exactly once at its own level")
        guard = hits[0]
        self.assertIsInstance(guard, ast.Try, "the boot sweep is not inside a try: a failure would stop the boot")
        self.assertTrue(any(isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "_sweep_stale_scratch"
                            for b in guard.body for n in ast.walk(b)))
        catches = [h for h in guard.handlers if isinstance(h.type, ast.Name) and h.type.id == "Exception"]
        self.assertTrue(catches, "the guard does not catch Exception")
        for h in catches:
            self.assertFalse(any(isinstance(n, ast.Raise) for n in ast.walk(h)), "the guard re-raises")
            self.assertTrue(any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print"
                                for n in ast.walk(h)), "a failed sweep is not recorded")
        index_sweep = src.index('_reel_sweep_indexes(why="console boot")')
        self.assertLess(index_sweep, src.index("_sweep_stale_scratch("))
        self.assertLess(src.index("_sweep_stale_scratch("), src.index("target=_roster_publish_loop"),
                        "the sweep runs after the lanes have started")


RED_PROOF = [
    {"why": "REG-2510 (#95): roster.js takes a signature that does not match the bytes as valid, so a flipped bit "
            "is stored for a registered owner and registers a key for an unregistered one",
     "file": "functions/api/roster.js",
     "find": "  if (ok !== true) return { state: \"bad\", keyId: keyId, why: \"the signature does not match these bytes\" };\n",
     "replace": "",
     "matches": 1, "needs": "node"},
    {"why": "REG-2510 (#95): a refused publish still writes the row before it answers ok:false",
     "file": "functions/api/roster.js",
     "find": "  if (intent.refused) return refuseSignature(intent, sig);\n",
     "replace": "  if (intent.refused) { await kv.put(key, JSON.stringify({ owner: owner, t: Date.now(), day: \"2000-01-01\", "
                "n: 1, hash: \"forged\", sections: shaped }), { expirationTtl: TTL_S }); return refuseSignature(intent, sig); }\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2510 (#95): the registered-key check is skipped, so a publish signed by another key overwrites the owner's row",
     "file": "functions/api/roster.js",
     "find": "    if (sig.pub !== b64uOfBytes(regPub)) {\n",
     "replace": "    if (false) {\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2510 (#95): GET calls a row published before signing unverified instead of passing no verdict (UNKNOWN)",
     "file": "functions/api/roster.js",
     "find": "    if (typeof prev.intentVerified === \"boolean\") row.intentVerified = prev.intentVerified;\n",
     "replace": "    row.intentVerified = prev.intentVerified === true;\n",
     "matches": 1, "needs": "node"},
    {"why": "REG-2513 (#95): view_one drops intentVerified, so no viewer can show whether a row was its owner's",
     "file": "roster_publish.py",
     "find": "    out[\"intentVerified\"] = verified_of(row)\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2511 (#95): hash_of walks code points again, so an emoji row reads CORRUPT for every viewer",
     "file": "roster_publish.py",
     "find": "    data = text.encode(\"utf-16-le\", \"surrogatepass\")\n    for i in range(0, len(data), 2):\n"
             "        h ^= data[i] | (data[i + 1] << 8)\n",
     "replace": "    for ch in text:\n        h ^= ord(ch)\n",
     "matches": 1},
    {"why": "REG-2512 (#95): due() answers 'unchanged' before it looks at boot, so a forged row is never healed",
     "file": "roster_publish.py",
     "find": "    if state.get(\"hash\") == digest and not boot:\n",
     "replace": "    if state.get(\"hash\") == digest:\n",
     "matches": 1},
    {"why": "REG-2510 (#95): the console builds the signature headers and posts without them",
     "file": "control_app.py",
     "find": "            headers.update(signed)\n",
     "replace": "",
     "matches": 1},
    {"why": "REG-2510 (#95): a key file that cannot be read is replaced by a new key, so a registered owner is refused "
            "with the evidence gone",
     "file": "roster_sign.py",
     "find": "    if why != \"absent\":\n        return None, why, False\n",
     "replace": "    if why != \"absent\":\n        os.remove(path)\n",
     "matches": 1},
    {"why": "REG-2515 (#112): the boot sweep of d2jsp scratch loses its guard, so one failure stops the console booting",
     "file": "control_app.py",
     "find": "    try:\n        import d2jsp_chrome as _d2jsp_boot\n",
     "replace": "    import d2jsp_chrome as _d2jsp_boot\n    _d2jsp_boot._sweep_stale_scratch()\n    try:\n",
     "matches": 1},
    {"why": "REG-2514 (#95): the doctor stops asking whether every roster publish is signed",
     "file": "console_doctor.py",
     "find": "    (\"every roster publish is signed\", _check_every_roster_publish_is_signed),\n",
     "replace": "",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
