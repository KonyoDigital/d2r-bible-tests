#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""#95 - this PC's roster signing key, and the two Ed25519 signers that must agree.

His ruling, 2026-10-22: deploy signed roster publishing once the Python/JS signature test passes,
trust-on-first-use, and never stop a PC from publishing.

WHAT IS SIGNED. The exact bytes POST /api/roster receives. Neither side re-serialises before the
check, so Python's and JavaScript's JSON writers never have to agree on a byte. functions/api/roster.js
verifies those same bytes with crypto.subtle before it parses them.

THE KEY. One Ed25519 keypair per PC, in <log root>/.roster_key.json. control_app passes that path, so it
follows TV_HIST and a fixture never touches the real key. The file is mode 0600 and holds
{v, seed, pub, created}. The seed never leaves the file: it is not logged, returned or posted. The public
half may be public. The server keeps one per owner (rosterkey:<owner>) and registers it on the first
signed publish. An existing key file is never replaced, even when it cannot be read: a PC that lost its
key is refused until Konyo resets that owner's key from the Mac (functions/api/roster.js says how).

TWO SIGNERS. `cryptography` when it imports. Otherwise a pure-Python RFC 8032 signer, because
tv/install-tvd.ps1 installs pywebview, Pillow, numpy and websocket-client and tv/install-tvd.sh installs
only pywebview: without the fallback Dean, ALT and Wife PC would never sign. Ed25519 is deterministic, so
the two produce byte-identical signatures. That pair is the corroborator, and it is asked on every
signature this PC makes while both are present.
"""

import base64
import hashlib
import json
import os
import time

KEY_FILE = ".roster_key.json"
KEY_VERSION = 1
PUBLIC_LEN = 32
SIG_LEN = 64

# ── RFC 8032 section 5.1, the reference arithmetic (extended twisted Edwards coordinates) ────────────
_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493


def _inv(x):
    return pow(x, _P - 2, _P)


_D = (-121665 * _inv(121666)) % _P
_SQRT_M1 = pow(2, (_P - 1) // 4, _P)


def _recover_x(y, sign):
    if y >= _P:
        return None
    x2 = (y * y - 1) * _inv(_D * y * y + 1) % _P
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P != 0:
        x = x * _SQRT_M1 % _P
    if (x * x - x2) % _P != 0:
        return None
    if (x & 1) != sign:
        x = _P - x
    return x


_GY = 4 * _inv(5) % _P
_GX = _recover_x(_GY, 0)
_G = (_GX, _GY, 1, _GX * _GY % _P)


def _add(a, b):
    pa = (a[1] - a[0]) * (b[1] - b[0]) % _P
    pb = (a[1] + a[0]) * (b[1] + b[0]) % _P
    pc = 2 * a[3] * b[3] * _D % _P
    pd = 2 * a[2] * b[2] % _P
    e, f, g, h = pb - pa, pd - pc, pd + pc, pb + pa
    return (e * f % _P, g * h % _P, f * g % _P, e * h % _P)


def _mul(s, pt):
    acc = (0, 1, 1, 0)
    while s > 0:
        if s & 1:
            acc = _add(acc, pt)
        pt = _add(pt, pt)
        s >>= 1
    return acc


def _same_point(a, b):
    return ((a[0] * b[2] - b[0] * a[2]) % _P == 0
            and (a[1] * b[2] - b[1] * a[2]) % _P == 0)


def _compress(pt):
    zi = _inv(pt[2])
    x = pt[0] * zi % _P
    y = pt[1] * zi % _P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _decompress(raw):
    if not isinstance(raw, (bytes, bytearray)) or len(raw) != 32:
        return None
    y = int.from_bytes(raw, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _recover_x(y, sign)
    if x is None:
        return None
    return (x, y, 1, x * y % _P)


def _expand(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return a, h[32:]


def _seed_ok(seed):
    return isinstance(seed, (bytes, bytearray)) and len(seed) == 32


def pure_public(seed):
    """The public key of a 32-byte seed, by the RFC 8032 arithmetic alone."""
    if not _seed_ok(seed):
        raise ValueError("a seed is 32 bytes")
    a, _prefix = _expand(bytes(seed))
    return _compress(_mul(a, _G))


def pure_sign(seed, msg):
    """RFC 8032 section 5.1.6. No import beyond hashlib, so every PC can sign."""
    if not _seed_ok(seed):
        raise ValueError("a seed is 32 bytes")
    msg = bytes(msg)
    a, prefix = _expand(bytes(seed))
    pub = _compress(_mul(a, _G))
    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little") % _L
    big_r = _compress(_mul(r, _G))
    k = int.from_bytes(hashlib.sha512(big_r + pub + msg).digest(), "little") % _L
    s = (r + k * a) % _L
    return big_r + s.to_bytes(32, "little")


def pure_verify(pub, msg, sig):
    """RFC 8032 section 5.1.7, cofactorless. -> bool. The laws use it; the server uses crypto.subtle."""
    if not isinstance(pub, (bytes, bytearray)) or len(pub) != PUBLIC_LEN:
        return False
    if not isinstance(sig, (bytes, bytearray)) or len(sig) != SIG_LEN:
        return False
    big_a = _decompress(bytes(pub))
    big_r = _decompress(bytes(sig[:32]))
    if big_a is None or big_r is None:
        return False
    s = int.from_bytes(bytes(sig[32:]), "little")
    if s >= _L:
        return False
    k = int.from_bytes(hashlib.sha512(bytes(sig[:32]) + bytes(pub) + bytes(msg)).digest(), "little") % _L
    return _same_point(_mul(s, _G), _add(big_r, _mul(k, big_a)))


# ── the second signer ────────────────────────────────────────────────────────────────────────────────
def have_cryptography():
    """-> bool. Asked at call time and imported nowhere at module level: CI's runner and the PCs
    the installers set up may not have it, and this module must load on all of them."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: F401
    except Exception:
        return False
    return True


def crypto_public(seed):
    """The public key by `cryptography`. -> bytes, or None when it is not installed here."""
    if not have_cryptography():
        return None
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519
    priv = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(seed))
    return priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def crypto_sign(seed, msg):
    """A signature by `cryptography`. -> bytes, or None when it is not installed here."""
    if not have_cryptography():
        return None
    from cryptography.hazmat.primitives.asymmetric import ed25519
    return ed25519.Ed25519PrivateKey.from_private_bytes(bytes(seed)).sign(bytes(msg))


# ── encodings ────────────────────────────────────────────────────────────────────────────────────────
_B64U = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")


def b64u(raw):
    """base64url with no padding: the form the X-Roster-Key and X-Roster-Sig headers carry."""
    return base64.urlsafe_b64encode(bytes(raw)).rstrip(b"=").decode("ascii")


def unb64u(text):
    """-> bytes, or None for anything that is not base64url."""
    if not isinstance(text, str):
        return None
    t = text.strip().rstrip("=")
    if not t or any(c not in _B64U for c in t) or len(t) % 4 == 1:
        return None
    return base64.urlsafe_b64decode(t + "=" * (-len(t) % 4))


def key_id(pub):
    """A short public name for a key: the first 12 hex of SHA-256 over its 32 raw bytes. roster.js
    computes the same thing, so a row's keyId and this PC's own can be compared."""
    return hashlib.sha256(bytes(pub)).hexdigest()[:12]


def key_path_in(root):
    """Where this PC keeps its key, inside the root control_app hands over (TV_HIST-aware)."""
    if not isinstance(root, str) or not root:
        return None
    return os.path.join(root, KEY_FILE)


class RosterKey(object):
    """One PC's keypair. Its repr and its view never carry the seed."""

    __slots__ = ("_seed", "pub", "created")

    def __init__(self, seed, pub, created):
        self._seed = bytes(seed)
        self.pub = bytes(pub)
        self.created = created

    def __repr__(self):
        return "RosterKey(%s)" % key_id(self.pub)

    __str__ = __repr__

    def view(self):
        return {"pub": b64u(self.pub), "keyId": key_id(self.pub), "created": self.created}


def _tighten(path):
    """0600 on a POSIX filesystem. Windows keeps its own ACLs and this is a no-op there."""
    if os.name != "posix":
        return
    try:
        if os.stat(path).st_mode & 0o077:
            os.chmod(path, 0o600)
    except OSError as e:
        return "its mode could not be narrowed (%s)" % type(e).__name__
    return None


def load_key(path, tighten=True):
    """-> (RosterKey | None, why). why "absent" means there is no file at all. The only write it may
    make is narrowing the file's mode to 0600, and a reader that must write nothing passes tighten=False."""
    if not isinstance(path, str) or not path:
        return None, "no key path was given"
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return None, "absent"
    except Exception as e:
        return None, "the key file is unreadable (%s); it was left as it is" % type(e).__name__
    if not isinstance(data, dict) or data.get("v") != KEY_VERSION:
        return None, "the key file is not a version-%d key; it was left as it is" % KEY_VERSION
    seed = unb64u(data.get("seed"))
    pub = unb64u(data.get("pub"))
    if seed is None or len(seed) != 32 or pub is None or len(pub) != PUBLIC_LEN:
        return None, "the key file does not hold a 32-byte seed and a 32-byte public key; it was left as it is"
    if pure_public(seed) != pub:
        return None, "the key file's public half does not match its seed; it was left as it is"
    created = data.get("created")
    if isinstance(created, bool) or not isinstance(created, int):
        created = None
    if tighten:
        _tighten(path)
    return RosterKey(seed, pub, created), None


def load_or_create(path, now_ms=None):
    """-> (RosterKey | None, why, made). Makes a key only where no file exists at all.

    An existing file that cannot be read is left alone and reported: replacing it would mint a key the
    server has never seen, and an owner whose first key is registered would then be refused anyway,
    with the evidence gone."""
    key, why = load_key(path)
    if key is not None:
        return key, None, False
    if why != "absent":
        return None, why, False
    seed = os.urandom(32)
    pub = pure_public(seed)
    made_at = now_ms if isinstance(now_ms, int) and not isinstance(now_ms, bool) else int(time.time() * 1000)
    body = {"v": KEY_VERSION, "seed": b64u(seed), "pub": b64u(pub), "created": made_at}
    tmp = path + ".tmp"
    try:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        try:
            os.remove(tmp)                    # a dead writer's partner file: never reuse its mode
        except FileNotFoundError:
            pass
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(body, fh)
            fh.flush()
            os.fsync(fh.fileno())
        if os.path.exists(path):              # another writer finished first: its key stands
            os.remove(tmp)
            key, why = load_key(path)
            return key, why, False
        os.replace(tmp, path)
    except Exception as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return None, "the key could not be written (%s)" % type(e).__name__, False
    _tighten(path)
    return RosterKey(seed, pub, made_at), None, True


def sign(key, raw):
    """-> (signature, signer, agree). agree is None when only one signer exists on this PC, and
    False when the two disagree (the doctor shows that; cryptography's signature is the one sent).
    A `cryptography` that is installed and raises is named in the signer, and the RFC 8032 signer's
    signature goes instead: a broken library must not stop a PC from publishing."""
    own = pure_sign(key._seed, raw)
    try:
        other = crypto_sign(key._seed, raw)
    except Exception as e:
        return own, "pure-python (cryptography raised %s)" % type(e).__name__, None
    if other is None:
        return own, "pure-python", None
    return other, "cryptography", other == own


def sign_headers(key_path, raw, now_ms=None):
    """The headers that sign exactly `raw`, and what happened. -> (headers, signing)

    headers is {} when this publish goes unsigned, and then signing says why. Neither ever holds the seed."""
    if not isinstance(raw, (bytes, bytearray)):
        return {}, {"signed": False, "why": "the body to sign was not bytes"}
    key, why, made = load_or_create(key_path, now_ms)
    if key is None:
        return {}, {"signed": False, "why": why or "no key"}
    kid = key_id(key.pub)
    try:
        sig, signer, agree = sign(key, bytes(raw))
    except Exception as e:
        return {}, {"signed": False, "why": "signing raised %s" % type(e).__name__, "keyId": kid}
    if len(sig) != SIG_LEN:
        return {}, {"signed": False, "why": "the signer returned %d bytes, not 64" % len(sig), "keyId": kid}
    headers = {"X-Roster-Key": b64u(key.pub), "X-Roster-Sig": b64u(sig)}
    return headers, {"signed": True, "keyId": kid, "signer": signer, "agree": agree, "made": made}


def public_view(key_path):
    """This PC's key as the doctor may show it, read-only. -> (view | None, why)"""
    key, why = load_key(key_path, tighten=False)
    if key is None:
        return None, why
    return key.view(), None
