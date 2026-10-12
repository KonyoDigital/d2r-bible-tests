# -*- coding: utf-8 -*-
"""Post one priced draft to d2jsp board 268 through the Chrome login on this machine.

The desk in bible.html calls POST /api/d2jsp_send. This module reads the d2jsp
cookies from the local Chrome profile at that moment, loads the compose form,
and submits only when that form is board 268 and the browser is logged in.
The cookie is not stored, not logged, and not returned. A missing login, an
unreadable cookie, or a form this desk does not know returns a status word
and does not claim a post.

Windows has no reader here. A public page has no route. Both stay unposted.
"""
from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BOARD = 268
COMPOSE_URL = "https://forums.d2jsp.org/post.php?mode=post&f=268"
LOGIN_URL = "https://forums.d2jsp.org/login.php"
_HOST = "forums.d2jsp.org"
_PRICE_LINE = re.compile(r"^\d+(?:\.\d+)? fg$")
_CHROME_EPOCH = 11644473600  # seconds from 1601-01-01 to 1970-01-01


def console_may_post(origin, host, port):
    """True only for this console's own page. A foreign Origin never may."""
    allowed = {"http://127.0.0.1:%d" % port, "http://localhost:%d" % port}
    if origin:
        return origin in allowed
    bare = (host or "").split(",")[0].strip()
    return bare in {"127.0.0.1:%d" % port, "localhost:%d" % port}


def _d2jsp_host(host):
    h = str(host or "").lstrip(".").lower()
    return h == "d2jsp.org" or h.endswith(".d2jsp.org")


def _chrome_now(now_utc):
    """Chrome stores expiry as microseconds since 1601-01-01."""
    if now_utc is None:
        import time
        now_utc = time.time()
    return int((float(now_utc) + _CHROME_EPOCH) * 1000000)


def seal_v10(password, text):
    """The inverse of decrypt_v10, for the desk law. None when the cipher library is absent."""
    try:
        from hashlib import pbkdf2_hmac
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except Exception:
        return None
    try:
        raw = str(text).encode("utf-8")
        pad = 16 - (len(raw) % 16)
        block = raw + bytes([pad]) * pad
        key = pbkdf2_hmac("sha1", str(password).encode("utf-8"), b"saltysalt", 1003, 16)
        enc = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).encryptor()
        return b"v10" + enc.update(block) + enc.finalize()
    except Exception:
        return None


def decrypt_v10(blob, password):
    """Open one Chrome v10 cookie. Any other prefix, or a failed open, is None."""
    if not isinstance(blob, (bytes, bytearray)) or blob[:3] != b"v10" or not password:
        return None
    try:
        from hashlib import pbkdf2_hmac
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except Exception:
        return None
    try:
        key = pbkdf2_hmac("sha1", str(password).encode("utf-8"), b"saltysalt", 1003, 16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16))
        dec = cipher.decryptor()
        raw = dec.update(bytes(blob[3:])) + dec.finalize()
        pad = raw[-1]
        if not isinstance(pad, int):
            pad = ord(pad)
        if pad < 1 or pad > 16 or raw[-pad:] != bytes([pad]) * pad:
            return None
        text = raw[:-pad].decode("utf-8")
    except Exception:
        return None
    if not text or any(c in text for c in (";", "\r", "\n")):
        return None
    return text


def cookie_header_from_rows(rows, password, now_utc=None, decrypt=None):
    """Build a Cookie header from rows whose host is d2jsp. Other hosts are ignored.

    rows are (host_key, name, encrypted_value, expires_utc). An expired row is
    dropped. decrypt defaults to decrypt_v10. -> (header or None, reason)
    reason is ok, need-login, or chrome-unread.
    """
    open_one = decrypt or (lambda blob: decrypt_v10(blob, password))
    now = _chrome_now(now_utc)
    pairs = []
    saw_host = False
    failed = False
    for host, name, blob, expires in rows:
        if not _d2jsp_host(host):
            continue
        saw_host = True
        try:
            exp = int(expires or 0)
        except (TypeError, ValueError):
            exp = 0
        if exp and exp <= now:
            continue
        value = open_one(blob)
        if not value:
            failed = True
            continue
        nm = str(name or "")
        if not nm or any(c in nm for c in ("=", ";", " ", "\r", "\n")):
            continue
        pairs.append(nm + "=" + value)
    if pairs:
        return "; ".join(pairs), "ok"
    if saw_host and failed:
        return None, "chrome-unread"
    if saw_host:
        return None, "need-login"
    return None, "need-login"


def _cookie_db_path():
    if sys.platform != "darwin":
        return None
    root = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Google", "Chrome", "Default")
    for rel in ("Cookies", os.path.join("Network", "Cookies")):
        path = os.path.join(root, rel)
        if os.path.isfile(path):
            return path
    return None


def _read_rows(db_path):
    """Copy the cookie database, then read it. Chrome keeps the live file locked."""
    uri = "file:" + urllib.parse.quote(db_path, safe="/") + "?immutable=1"
    src = sqlite3.connect(uri, uri=True)
    try:
        tmp = tempfile.NamedTemporaryFile(prefix="d2jsp-cookies-", suffix=".db", delete=False)
        tmp.close()
        dst = sqlite3.connect(tmp.name)
        try:
            src.backup(dst)
            rows = list(dst.execute(
                "select host_key, name, encrypted_value, expires_utc from cookies"
            ))
        finally:
            dst.close()
            try:
                os.remove(tmp.name)
            except OSError:
                pass
    finally:
        src.close()
    return rows


def live_cookie_header(now_utc=None):
    """The d2jsp cookie header from this Mac's Chrome, or a reason it could not be read."""
    if sys.platform != "darwin":
        return None, "chrome-unread"
    path = _cookie_db_path()
    if not path:
        return None, "chrome-unread"
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-w", "-s", "Chrome Safe Storage", "-a", "Chrome"],
            capture_output=True, timeout=60,
        )
    except Exception:
        return None, "chrome-unread"
    if proc.returncode != 0:
        return None, "chrome-unread"
    password = proc.stdout.decode("utf-8", "replace").strip()
    if not password:
        return None, "chrome-unread"
    try:
        rows = _read_rows(path)
    except Exception:
        return None, "chrome-unread"
    return cookie_header_from_rows(rows, password, now_utc=now_utc)


class _Compose(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.has_logout = False
        self.has_subject = False
        self.has_message = False
        self.has_post = False
        self.post_value = "Post"

    def handle_starttag(self, tag, attrs):
        d = {}
        for key, val in attrs:
            d[key] = val or ""
        if tag == "a" and "mode=logout" in d.get("href", ""):
            self.has_logout = True
        if tag == "input":
            name = d.get("name", "")
            if name == "subject":
                self.has_subject = True
            if name == "post":
                self.has_post = True
                if d.get("value"):
                    self.post_value = d["value"]
            if name and d.get("type", "text") == "hidden" and len(self.hidden) < 30:
                self.hidden.append((name, d.get("value", "")))
        if tag == "textarea" and d.get("name") == "message":
            self.has_message = True
        if tag == "button" and d.get("name") == "post":
            self.has_post = True
            if d.get("value"):
                self.post_value = d["value"]


def parse_compose(html):
    """The compose page. -> {reason, fields?, post_value?}

    reason is unread, need-login, form-unknown, or ready.
    """
    if isinstance(html, (bytes, bytearray)):
        text = html.decode("utf-8", "replace")
    else:
        text = str(html or "")
    low = text.lower()
    if (not text) or ("just a moment" in low) or ("cf-browser-verification" in low):
        return {"reason": "unread"}
    if "not currently logged in" in low:
        return {"reason": "need-login"}
    form = _Compose()
    try:
        form.feed(text)
    except Exception:
        return {"reason": "form-unknown"}
    if not form.has_logout:
        return {"reason": "need-login"}
    if not (form.has_subject and form.has_message and form.has_post):
        return {"reason": "form-unknown"}
    return {"reason": "ready", "fields": form.hidden, "post_value": form.post_value}


def _priced(subject, body):
    if not str(subject or "").startswith("WTS "):
        return False
    if len(subject) > 140 or len(body) > 4000:
        return False
    lines = [ln.strip() for ln in str(body or "").splitlines() if ln.strip()]
    if not lines or not _PRICE_LINE.match(lines[-1]):
        return False
    try:
        return float(lines[-1].split()[0]) > 0
    except ValueError:
        return False


def _on_forum(url):
    if not url:
        return False
    if url.startswith("/") and not url.startswith("//"):
        return True
    try:
        parts = urllib.parse.urlparse(url)
    except Exception:
        return False
    return parts.scheme in ("https", "") and parts.netloc in (_HOST, "")


def _topic(url):
    if not _on_forum(url):
        return False
    path = url
    try:
        path = urllib.parse.urlparse(url).path or url
    except Exception:
        path = url
    return "topic.php" in path


def _transport(method, url, headers, data):
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, hdrs, newurl):
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=25) as resp:
            return resp.status, {k: v for k, v in resp.headers.items()}, resp.read(200000)
    except urllib.error.HTTPError as exc:
        # None is "this header was not read". An empty page is not a receipt.
        loc = None
        try:
            loc = exc.headers.get("Location")
        except Exception:
            loc = None
        raw = None
        try:
            raw = exc.read(200000)
        except Exception:
            raw = None
        return exc.code, {"Location": loc or ""}, raw or b""


def chrome_user_agent():
    """The installed Chrome's own signature. A clearance cookie is bound to it.

    When the version cannot be read, the header still names Chrome and a
    challenge page stays unread. It is not reported as a post.
    """
    version = "131.0.0.0"
    if sys.platform == "darwin":
        try:
            proc = subprocess.run(
                ["defaults", "read",
                 "/Applications/Google Chrome.app/Contents/Info.plist",
                 "CFBundleShortVersionString"],
                capture_output=True, timeout=5, text=True,
            )
        except OSError:
            proc = None
        if proc is not None and proc.returncode == 0:
            got = (proc.stdout or "").strip()
            if re.fullmatch(r"\d+(?:\.\d+){2,3}", got):
                version = got
    return (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36"
    ) % version


def _open_chrome_login():
    """Open the fixed login page in the Chrome that is already running. Nothing from the draft is in the URL."""
    if sys.platform != "darwin":
        return False
    try:
        proc = subprocess.run(
            ["open", "-a", "Google Chrome", LOGIN_URL],
            capture_output=True, timeout=5,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _headers(cookie):
    return {
        "User-Agent": chrome_user_agent(),
        "Accept": "text/html",
        "Cookie": cookie,
        "Referer": COMPOSE_URL,
    }


def d2jsp_send(body, origin, host, port, cookie_get=None, transport=None, open_login=None):
    """Post one desk draft. -> (http code, {ok, reason, opened?})

    The dict never carries the cookie, the page, or the draft.
    """
    if not console_may_post(origin, host, port):
        return 403, {"ok": False, "reason": "origin"}
    body = body if isinstance(body, dict) else {}
    try:
        forum = int(body.get("forum"))
    except (TypeError, ValueError):
        forum = 0
    if forum != BOARD:
        return 200, {"ok": False, "reason": "wrong-board"}
    subject = str(body.get("subject") or "").strip()
    text = str(body.get("body") or "").strip()
    if not _priced(subject, text):
        return 200, {"ok": False, "reason": "no-price"}
    get_cookie = cookie_get or live_cookie_header
    try:
        cookie, cookie_reason = get_cookie()
    except Exception:
        cookie, cookie_reason = None, "chrome-unread"
    if not cookie:
        out = {"ok": False, "reason": cookie_reason or "chrome-unread"}
        if out["reason"] == "need-login":
            opener = open_login or _open_chrome_login
            try:
                out["opened"] = bool(opener())
            except Exception:
                out["opened"] = False
        return 200, out
    fetch = transport or _transport
    try:
        status, hdrs, raw = fetch("GET", COMPOSE_URL, _headers(cookie), None)
    except Exception:
        return 200, {"ok": False, "reason": "unread"}
    if status in (301, 302, 303, 307, 308):
        loc = ""
        if isinstance(hdrs, dict):
            loc = hdrs.get("Location") or hdrs.get("location") or ""
        if _on_forum(loc) and "login" in loc.lower():
            opener = open_login or _open_chrome_login
            opened = False
            try:
                opened = bool(opener())
            except Exception:
                opened = False
            return 200, {"ok": False, "reason": "need-login", "opened": opened}
        return 200, {"ok": False, "reason": "form-unknown"}
    parsed = parse_compose(raw)
    if parsed["reason"] != "ready":
        out = {"ok": False, "reason": parsed["reason"]}
        if parsed["reason"] == "need-login":
            opener = open_login or _open_chrome_login
            try:
                out["opened"] = bool(opener())
            except Exception:
                out["opened"] = False
        return 200, out
    fields = list(parsed["fields"])
    fields.append(("subject", subject))
    fields.append(("message", text))
    fields.append(("post", parsed.get("post_value") or "Post"))
    encoded = urllib.parse.urlencode(fields).encode("utf-8")
    sent_headers = _headers(cookie)
    sent_headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        status, hdrs, raw = fetch("POST", COMPOSE_URL, sent_headers, encoded)
    except Exception:
        return 200, {"ok": False, "reason": "unread"}
    loc = ""
    if isinstance(hdrs, dict):
        loc = hdrs.get("Location") or hdrs.get("location") or ""
    if status in (301, 302, 303, 307, 308) and _topic(loc):
        return 200, {"ok": True, "reason": "submitted"}
    if status in (301, 302, 303, 307, 308) and _on_forum(loc) and "login" in loc.lower():
        opener = open_login or _open_chrome_login
        opened = False
        try:
            opened = bool(opener())
        except Exception:
            opened = False
        return 200, {"ok": False, "reason": "need-login", "opened": opened}
    came_back = parse_compose(raw)
    if came_back["reason"] == "need-login":
        opener = open_login or _open_chrome_login
        opened = False
        try:
            opened = bool(opener())
        except Exception:
            opened = False
        return 200, {"ok": False, "reason": "need-login", "opened": opened}
    # A 200 that is not a redirect onto topic.php did not confirm a post.
    # Saying submitted here would claim a send the board did not receipt.
    return 200, {"ok": False, "reason": "not-posted"}
