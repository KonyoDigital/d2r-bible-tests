# -*- coding: utf-8 -*-
"""Post one priced draft to d2jsp board 268 through the Chrome login on this machine.

The desk in bible.html calls POST /api/d2jsp_send. This module reads the d2jsp
cookies from the local Chrome profile at that moment, loads the compose form,
and submits only when that form is board 268 and the browser is logged in.
The cookie is not stored, not logged, and not returned. A missing login, an
unreadable cookie, or a form this desk does not know returns a status word
and does not claim a post.

Windows has no reader here. A public page has no route. Those stay unposted.
Linux reads the Chrome profile on that machine.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

BOARD = 268
LADDER_BOARD = 271
POST_BOARDS = (BOARD, LADDER_BOARD)
QUOTE_BOARD = 243
COMPOSE_URL = "https://forums.d2jsp.org/post.php?mode=post&f=268"
LOGIN_URL = "https://forums.d2jsp.org/login.php"
_HOST = "forums.d2jsp.org"
_PRICE_LINE = re.compile(r"^\d+(?:\.\d+)? fg$")
_CHROME_EPOCH = 11644473600  # seconds from 1601-01-01 to 1970-01-01


def console_may_post(origin, host, port, sec_fetch_site=None):
    """True only for this console's own page. A foreign Origin never may, and a cross-site request
    with NO Origin never may either.

    REG-2188 — A NO-ORIGIN GET WAS TRUSTED ON HOST ALONE. A browser sends no Origin on a cross-site
    <img>, iframe or window.open GET, but it DOES send the target's Host — so any page he visited
    could reach /api/d2jsp_login and /api/d2jsp_quote (read the keychain, decrypt his cookies, start
    a scratch Chrome, pull his real Chrome to the login page). It could not read the reply, but the
    side effects fired. Sec-Fetch-Site is sent by the browser and cannot be forged by the page: a
    cross-site embed is `cross-site`, a page on another local port is `same-site`, the console's own
    fetch is `same-origin`, and a user typing the URL is `none`. So a no-Origin request is refused
    when it is EXPLICITLY cross-site or same-site, and still allowed when the header is same-origin,
    none or absent — the console's own request is never broken, even on a client that omits it.
    POST is already safe (browsers always send Origin on POST); the arg defaults to None there.
    [[the-unjoined-end]] [[unknown-stays-unknown]]"""
    allowed = {"http://127.0.0.1:%d" % port, "http://localhost:%d" % port}
    if origin:
        return origin in allowed
    if str(sec_fetch_site or "").strip().lower() in {"cross-site", "same-site"}:
        return False
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


def _seal_v10_raw(password, raw, rounds=1003):
    """Encrypt one cookie plaintext. None when the cipher library is absent.

    Mac Chrome derives the key with 1003 rounds. Linux Chrome uses 1 round.
    """
    try:
        from hashlib import pbkdf2_hmac
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except Exception:
        return None
    try:
        pad = 16 - (len(raw) % 16)
        block = bytes(raw) + bytes([pad]) * pad
        key = pbkdf2_hmac("sha1", str(password).encode("utf-8"), b"saltysalt", int(rounds), 16)
        enc = Cipher(algorithms.AES(key), modes.CBC(b" " * 16)).encryptor()
        return b"v10" + enc.update(block) + enc.finalize()
    except Exception:
        return None


def seal_v10(password, text):
    """The inverse of decrypt_v10 for a plain value. None when the cipher library is absent."""
    return _seal_v10_raw(password, str(text).encode("utf-8"))


def _cookie_text(body, host=None):
    """The cookie value inside unpadded Chrome plaintext.

    Database version 24 stores SHA256(host_key) in front of the value. An older
    cookie is the value alone. A digest that is not this host is not the value.
    """
    if host is not None and len(body) > 32:
        digest = hashlib.sha256(str(host).encode("utf-8")).digest()
        if body[:32] == digest:
            body = body[32:]
    text = body.decode("utf-8")
    if not text or any(c in text for c in (";", "\r", "\n")):
        return None
    return text


def decrypt_v10(blob, password, host=None, rounds=1003):
    """Open one Chrome v10 cookie. Any other prefix, or a failed open, is None.

    host is the row host_key. Later Chrome stores bind the value to SHA256 of
    that host. Without the host, only a plain value opens. rounds is 1003 on
    Mac Chrome and 1 on Linux Chrome.
    """
    if not isinstance(blob, (bytes, bytearray)) or blob[:3] != b"v10" or not password:
        return None
    try:
        from hashlib import pbkdf2_hmac
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except Exception:
        return None
    try:
        key = pbkdf2_hmac("sha1", str(password).encode("utf-8"), b"saltysalt", int(rounds), 16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16))
        dec = cipher.decryptor()
        raw = dec.update(bytes(blob[3:])) + dec.finalize()
        pad = raw[-1]
        if not isinstance(pad, int):
            pad = ord(pad)
        if pad < 1 or pad > 16 or raw[-pad:] != bytes([pad]) * pad:
            return None
        text = _cookie_text(raw[:-pad], host)
    except Exception:
        return None
    return text


def cookie_header_from_rows(rows, password, now_utc=None, decrypt=None, rounds=1003):
    """Build a Cookie header from rows whose host is d2jsp. Other hosts are ignored.

    rows are (host_key, name, encrypted_value, expires_utc). An expired row is
    dropped. decrypt defaults to decrypt_v10. -> (header or None, reason)
    reason is ok, need-login, or chrome-unread.
    """
    def open_one(blob, host):
        if decrypt is not None:
            return decrypt(blob)
        return decrypt_v10(blob, password, host, rounds=rounds)

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
        value = open_one(blob, host)
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


def _linux_cookie_dbs():
    """Cookie databases under the Linux Chrome and Chromium profiles. Default first."""
    home = os.path.expanduser("~")
    roots = (
        os.path.join(home, ".config", "google-chrome"),
        os.path.join(home, ".config", "chromium"),
    )
    found = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            names = list(os.listdir(root))
        except OSError:
            continue
        names.sort(key=lambda name: (name != "Default", name))
        for name in names:
            base = os.path.join(root, name)
            for rel in ("Cookies", os.path.join("Network", "Cookies")):
                path = os.path.join(base, rel)
                if os.path.isfile(path):
                    found.append(path)
                    break
    return found


def _linux_chrome_passwords(run=None, tool=None):
    """Keyring secrets for Chrome, then Chrome's own published fallback.

    The fallback word is the one Chromium uses when the keyring has no secret.
    It is not a password this desk chooses. Nothing returned here is logged.
    """
    found = []
    if tool is None:
        tool = shutil.which("secret-tool")
    if tool:
        runner = run or subprocess.run
        for app in ("chrome", "chromium"):
            try:
                proc = runner(
                    [tool, "lookup", "application", app],
                    capture_output=True, timeout=8,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if getattr(proc, "returncode", 1) != 0:
                continue
            text = (getattr(proc, "stdout", b"") or b"").decode("utf-8", "replace").strip("\n")
            if text and text not in found:
                found.append(text)
    if "peanuts" not in found:
        found.append("peanuts")
    return found


def _linux_cookie_header(now_utc=None, paths=None, passwords=None):
    """A d2jsp cookie header from a Linux Chrome profile, or a reason."""
    stores = _linux_cookie_dbs() if paths is None else list(paths)
    if not stores:
        return None, "chrome-unread"
    secrets = _linux_chrome_passwords() if passwords is None else list(passwords)
    saw_fail = False
    saw_rows = False
    for path in stores:
        try:
            rows = _read_rows(path)
        except (OSError, sqlite3.Error):
            continue
        if rows:
            saw_rows = True
        for password in secrets:
            header, reason = cookie_header_from_rows(
                rows, password, now_utc=now_utc, rounds=1,
            )
            if header:
                return header, "ok"
            if reason == "chrome-unread":
                saw_fail = True
    if saw_fail:
        return None, "chrome-unread"
    if saw_rows:
        return None, "need-login"
    return None, "chrome-unread"


def _mac_cookie_header(now_utc=None):
    """The d2jsp cookie header from this Mac's Chrome, or a reason it could not be read."""
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


def live_cookie_header(now_utc=None):
    """The d2jsp cookie header from this machine's Chrome, or a reason it could not be read."""
    if sys.platform == "darwin":
        return _mac_cookie_header(now_utc)
    if sys.platform.startswith("linux"):
        return _linux_cookie_header(now_utc)
    return None, "chrome-unread"


def d2jsp_login_status(now_utc=None):
    """Whether this machine's own Chrome is signed into d2jsp.

    The cookie header is read and dropped. It is not returned, logged, or stored.
    Another console reads the Chrome of the person at that computer.
    """
    _header, reason = live_cookie_header(now_utc)
    if reason == "ok":
        return {
            "ok": True,
            "state": "on",
            "kind": "on",
            "why": "Signed into d2jsp through the Chrome login on this machine.",
        }
    if reason == "need-login":
        return {
            "ok": True,
            "state": "off",
            "kind": "signed-out",
            "needsLogin": True,
            "why": "This machine is not signed into d2jsp. Click the lamp to sign in.",
        }
    return {
        "ok": True,
        "state": "unknown",
        "kind": "unread",
        "why": "This machine could not read the Chrome login.",
    }


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
    # A sale says Selling. WTS remains a sale from a page that has not reloaded.
    head = str(subject or "")
    if not (head.startswith("Selling ") or head.startswith("WTS ")):
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


def _chrome_bin(platform=None, which=None):
    """The Chrome executable on this machine. None when it is not installed."""
    plat = sys.platform if platform is None else platform
    if plat == "darwin":
        path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.isfile(path):
            return path
        return None
    if str(plat).startswith("linux"):
        look = which or shutil.which
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
            found = look(name)
            if found:
                return found
    return None


def chrome_user_agent(platform=None, version=None):
    """The installed Chrome's own signature. A clearance cookie is bound to it.

    When the version cannot be read, the header still names Chrome and a
    challenge page stays unread. It is not reported as a post. Mac and Linux
    name themselves, because a cookie from one does not travel as the other.
    """
    plat = sys.platform if platform is None else platform
    if version is None:
        version = "131.0.0.0"
        if plat == "darwin" and plat == sys.platform:
            try:
                proc = subprocess.run(
                    ["defaults", "read",
                     "/Applications/Google Chrome.app/Contents/Info.plist",
                     "CFBundleShortVersionString"],
                    capture_output=True, timeout=5, text=True,
                    encoding="utf-8", errors="replace",
                )
            except OSError:
                proc = None
            if proc is not None and proc.returncode == 0:
                got = (proc.stdout or "").strip()
                if re.fullmatch(r"\d+(?:\.\d+){2,3}", got):
                    version = got
        elif str(plat).startswith("linux") and plat == sys.platform:
            binary = _chrome_bin(platform=plat)
            if binary:
                try:
                    proc = subprocess.run(
                        [binary, "--version"],
                        capture_output=True, timeout=5, text=True,
                        encoding="utf-8", errors="replace",
                    )
                except OSError:
                    proc = None
                if proc is not None and proc.returncode == 0:
                    got = (proc.stdout or "").strip().rsplit(" ", 1)[-1]
                    if re.fullmatch(r"\d+(?:\.\d+){2,3}", got):
                        version = got
    if str(plat).startswith("linux"):
        system = "X11; Linux x86_64"
    else:
        system = "Macintosh; Intel Mac OS X 10_15_7"
    return (
        "Mozilla/5.0 (%s) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36"
    ) % (system, version)


def _open_chrome_login(platform=None, run=None, which=None):
    """Open the forum login in this machine's own Chrome.

    Nothing from a draft is in the URL. The page opens in the Chrome this
    console already reads, not a debug port and not another computer's login.
    """
    plat = sys.platform if platform is None else platform
    runner = run or subprocess.run
    if plat == "darwin":
        argv = ["open", "-a", "Google Chrome", LOGIN_URL]
    elif str(plat).startswith("linux"):
        binary = _chrome_bin(platform=plat, which=which)
        if not binary:
            return False
        argv = [binary, "--no-first-run", LOGIN_URL]
    else:
        return False
    try:
        proc = runner(argv, capture_output=True, timeout=5)
        return getattr(proc, "returncode", 1) == 0
    except Exception:
        return False


def open_d2jsp_login():
    """Open this machine's d2jsp login. The answer says whether the page opened."""
    try:
        opened = bool(_open_chrome_login())
    except Exception:
        opened = False
    if opened:
        return {
            "ok": True,
            "opened": True,
            "why": "The d2jsp login is open in Chrome on this machine.",
        }
    return {
        "ok": False,
        "opened": False,
        "why": "This machine could not open the d2jsp login.",
    }


def _headers(cookie):
    return {
        "User-Agent": chrome_user_agent(),
        "Accept": "text/html",
        "Cookie": cookie,
        "Referer": COMPOSE_URL,
    }


_QUOTE_JS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "functions", "api", "d2jsp_quote.js",
)
quote_login_opened = False
_quote_login_lock = threading.Lock()


def _quote_unknown(item, read_at, reason):
    return {
        "item": str(item or ""),
        "fg": None,
        "low": None,
        "high": None,
        "n": 0,
        "readAt": read_at,
        "reason": reason,
        "board": QUOTE_BOARD,
    }


def _read_quote_parser():
    with open(_QUOTE_JS, encoding="utf-8") as fh:
        src = fh.read()
    mark = "/* ⟦D2JSP QUOTE BEGIN⟧ */\n"
    start = src.index(mark) + len(mark)
    end = src.index("\n/* ⟦D2JSP QUOTE END⟧ */", start)
    return src[start:end]


def _public_fields(parsed, item, read_at):
    if not isinstance(parsed, dict):
        return _quote_unknown(item, read_at, "unread")
    reason = parsed.get("reason")
    if reason not in ("read", "no prices", "need-login", "unread"):
        reason = "unread"
    fg = None
    low = None
    high = None
    n = 0
    if reason == "read":
        try:
            fg = float(parsed.get("fg"))
        except (TypeError, ValueError):
            return _quote_unknown(item, read_at, "unread")
        if fg <= 0:
            return _quote_unknown(item, read_at, "unread")
        if fg == int(fg):
            fg = int(fg)
        low = parsed.get("low")
        high = parsed.get("high")
        try:
            n = int(parsed.get("n"))
        except (TypeError, ValueError):
            return _quote_unknown(item, read_at, "unread")
    return {
        "item": str(item or ""),
        "fg": fg,
        "low": low,
        "high": high,
        "n": n,
        "readAt": parsed.get("readAt") or read_at,
        "reason": reason,
        "board": QUOTE_BOARD,
    }


def parse_public_quote(html, item, read_at, node_run=None):
    """Run the quote parser in functions/api/d2jsp_quote.js. No number is filled in here."""
    if node_run is None:
        node = shutil.which("node")
        if not node:
            return _quote_unknown(item, read_at, "unread")

        def node_run(prog, page):
            return subprocess.run(
                [node, "-e", prog],
                input=page,
                capture_output=True,
                timeout=20,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
    try:
        parser = _read_quote_parser()
    except (OSError, ValueError):
        return _quote_unknown(item, read_at, "unread")
    prog = (
        parser
        + "\nprocess.stdout.write(JSON.stringify(d2jspRead("
        + "require('fs').readFileSync(0,'utf8'),"
        + json.dumps(str(item or "")) + ","
        + json.dumps(str(read_at or ""))
        + ")));\n"
    )
    try:
        proc = node_run(prog, str(html or ""))
    except OSError:
        return _quote_unknown(item, read_at, "unread")
    if getattr(proc, "returncode", 1) != 0:
        return _quote_unknown(item, read_at, "unread")
    try:
        parsed = json.loads(getattr(proc, "stdout", "") or "")
    except (TypeError, ValueError):
        return _quote_unknown(item, read_at, "unread")
    return _public_fields(parsed, item, read_at)


def _search_keywords(item):
    return re.sub(r"['’ʼ`]", "", str(item or ""))


def _search_url(item):
    """The forum's own post search for the Switch Ladder board."""
    return "https://forums.d2jsp.org/search.php?c=7&f=%d&t=0" % QUOTE_BOARD


def _search_body(item):
    return urllib.parse.urlencode({"stext": _search_keywords(item)}).encode("utf-8")


def _challenge_page(page):
    text = str(page or "")
    if not text.strip():
        return True
    if re.search(r"Just a moment", text, re.I):
        return True
    return "cf-browser-verification" in text


def _cdp_call(ws, ident, method, params=None, wait=15):
    ws.send(json.dumps({"id": ident, "method": method, "params": params or {}}))
    end = time_now() + wait
    while time_now() < end:
        msg = json.loads(ws.recv())
        if msg.get("id") == ident:
            return msg
    raise OSError(method)


def time_now():
    import time
    return time.time()


_SCRATCH_PREFIXES = ("d2jsp-quote-", "d2jsp-post-")
_SCRATCH_STALE_S = 300  # 5 min — far beyond a normal op (<30s), so an in-flight profile is never swept


def _sweep_stale_scratch(now=None, tmp=None):
    """REG-2190 — SWEEP SCRATCH CHROMES A CRASHED CONSOLE LEFT HOLDING HIS COOKIES. -> count removed.

    Each op mkdtemps a d2jsp-quote-* / d2jsp-post-* profile and cleans it in its `finally`. But a
    console killed mid-op (kill -9, a relaunch) never reaches that finally, so the headless Chrome —
    which holds his decrypted d2jsp session — keeps running and its profile stays on disk, and
    nothing came back for them (process-port-discipline: everything I start, I own until it is dead).
    This runs at the top of each op: it removes any d2jsp scratch profile older than _SCRATCH_STALE_S
    (seconds-old in-flight ones are left alone) and SIGKILLs a Chrome still holding one — matched by
    its exact --user-data-dir, never by name, so his real Chrome can never be a target."""
    import glob as _glob
    import time as _time
    now = _time.time() if now is None else now
    root = tmp if tmp is not None else tempfile.gettempdir()
    removed = 0
    for pref in _SCRATCH_PREFIXES:
        for d in _glob.glob(os.path.join(root, pref + "*")):
            try:
                if now - os.path.getmtime(d) < _SCRATCH_STALE_S:
                    continue
            except OSError:
                continue
            try:
                _out = subprocess.run(["pgrep", "-f", "--user-data-dir=" + d],
                                      capture_output=True, text=True, timeout=5).stdout
                for _pid in _out.split():
                    try:
                        os.kill(int(_pid), signal.SIGKILL)
                    except Exception:
                        pass
            except Exception:
                pass
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    return removed


def _chrome_search(item, cookie):
    """Load the Switch Ladder search in a scratch Chrome. The cookie is not logged.

    The forum answers a scripted request with a challenge page. A separate Chrome,
    on its own profile and its own port, can submit the board's own search form.
    His open Chrome is not the one this starts. Raises OSError when that load fails.
    """
    import time
    import websocket
    keywords = _search_keywords(item)
    _sweep_stale_scratch()
    prof = tempfile.mkdtemp(prefix="d2jsp-quote-")
    sock = __import__("socket").socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    browser = _chrome_bin()
    if not browser:
        raise OSError("chrome")
    proc = subprocess.Popen(
        [browser, "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-blink-features=AutomationControlled",
         "--remote-debugging-port=%d" % port, "--user-data-dir=%s" % prof,
         "--remote-allow-origins=*", "--window-size=1100,800", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    base = "http://127.0.0.1:%d" % port
    ws = None
    try:
        deadline = time.time() + 12
        while time.time() < deadline:
            try:
                urllib.request.urlopen(base + "/json/version", timeout=2)
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise OSError("chrome")
        tab = json.loads(urllib.request.urlopen(
            urllib.request.Request(base + "/json/new?about:blank", method="PUT"),
            timeout=10,
        ).read().decode("utf-8", "replace"))
        ws = websocket.create_connection(
            tab["webSocketDebuggerUrl"], timeout=20, origin=base,
        )
        _cdp_call(ws, 1, "Network.enable")
        _cdp_call(ws, 2, "Network.setUserAgentOverride", {"userAgent": chrome_user_agent()})
        ident = 10
        for part in str(cookie or "").split(";"):
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            name = name.strip()
            if not name:
                continue
            _cdp_call(ws, ident, "Network.setCookie", {
                "name": name,
                "value": value,
                "url": "https://forums.d2jsp.org/",
                "domain": ".d2jsp.org",
                "path": "/",
                "secure": True,
            })
            ident += 1
        _cdp_call(ws, 50, "Page.enable")
        _cdp_call(ws, 51, "Page.navigate", {
            "url": "https://forums.d2jsp.org/forum.php?f=%d" % QUOTE_BOARD,
        })
        submit = (
            "(function(){var f=document.querySelector('form[action*=\"search.php\"]');"
            "if(!f||!f.stext)return 'no-form';f.stext.value=%s;f.submit();return 'sent';})()"
        ) % json.dumps(keywords)
        sent = False
        html = ""
        deadline = time.time() + 20
        while time.time() < deadline:
            time.sleep(0.8)
            try:
                got = _cdp_call(ws, 60, "Runtime.evaluate", {
                    "expression": "document.documentElement.outerHTML",
                    "returnByValue": True,
                }, wait=8)
            except Exception:
                continue
            html = ((got.get("result") or {}).get("result") or {}).get("value") or ""
            if not sent and "search.php" in html and "stext" in html:
                try:
                    _cdp_call(ws, 61, "Runtime.evaluate", {
                        "expression": submit,
                        "returnByValue": True,
                    }, wait=8)
                    sent = True
                except Exception:
                    continue
            if sent and "Search Results" in html and not _challenge_page(html):
                return html
        if sent and html and not _challenge_page(html):
            return html
        raise OSError("search")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        shutil.rmtree(prof, ignore_errors=True)


def _chrome_edit(topic, subject, text, cookie):
    """Replace the saved topic through its own Edit link.

    The link has to say Edit and open post.php. Anything else returns no-edit
    and does not start a new trade. A title longer than 50 characters is not
    sent. The cookie is not logged. His open Chrome is not the one this starts.
    """
    import time
    import websocket
    _sweep_stale_scratch()
    prof = tempfile.mkdtemp(prefix="d2jsp-post-")
    sock = __import__("socket").socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    browser = _chrome_bin()
    if not browser:
        raise OSError("chrome")
    proc = subprocess.Popen(
        [browser, "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-blink-features=AutomationControlled",
         "--remote-debugging-port=%d" % port, "--user-data-dir=%s" % prof,
         "--remote-allow-origins=*", "--window-size=1100,800", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    base = "http://127.0.0.1:%d" % port
    ws = None
    try:
        deadline = time.time() + 12
        while time.time() < deadline:
            try:
                urllib.request.urlopen(base + "/json/version", timeout=2)
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise OSError("chrome")
        tab = json.loads(urllib.request.urlopen(
            urllib.request.Request(base + "/json/new?about:blank", method="PUT"),
            timeout=10,
        ).read().decode("utf-8", "replace"))
        ws = websocket.create_connection(
            tab["webSocketDebuggerUrl"], timeout=20, origin=base,
        )
        _cdp_call(ws, 1, "Network.enable")
        _cdp_call(ws, 2, "Network.setUserAgentOverride", {"userAgent": chrome_user_agent()})
        ident = 10
        for part in str(cookie or "").split(";"):
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            name = name.strip()
            if not name:
                continue
            _cdp_call(ws, ident, "Network.setCookie", {
                "name": name,
                "value": value,
                "url": "https://forums.d2jsp.org/",
                "domain": ".d2jsp.org",
                "path": "/",
                "secure": True,
            })
            ident += 1
        _cdp_call(ws, 50, "Page.enable")
        _cdp_call(ws, 51, "Page.navigate", {"url": str(topic or "")})
        open_edit = (
            "(function(){var as=document.querySelectorAll('a');"
            "for(var i=0;i<as.length;i++){"
            "var label=(as[i].textContent||'').replace(/\\s+/g,' ').trim();"
            "if(label!=='Edit')continue;"
            "var href=as[i].href||'';"
            "if(href.indexOf('/post.php')<0)continue;"
            "location.href=href;return 'opened';}"
            "return 'no-edit';})()"
        )
        fill = (
            "(function(){var box=document.querySelector("
            + json.dumps('textarea[name="Post"]') + ");"
            "var title=document.querySelector("
            + json.dumps('input[name="ttitle"]') + ");"
            "if(!box||!title||!box.form)return 'no-form';"
            "var subject=" + json.dumps(str(subject or "")) + ";"
            "if(subject.length>50)return 'title';"
            "title.value=subject;box.value=" + json.dumps(str(text or "")) + ";"
            "var picked=false;var labs=document.querySelectorAll('label');"
            "for(var i=0;i<labs.length;i++){"
            "if((labs[i].textContent||'').indexOf('Selling Item')<0)continue;"
            "var input=document.getElementById(labs[i].htmlFor||'');"
            "if(input&&input.name==='sType'){input.checked=true;picked=true;}}"
            "if(!picked)return 'no-sell';"
            "var paid=['sItalic','sBold','sRed'];"
            "for(var p=0;p<paid.length;p++){"
            "var extra=box.form.querySelector('input[name=\"'+paid[p]+'\"]');"
            "if(extra)extra.checked=false;}"
            "var btn=box.form.querySelector("
            + json.dumps('input[name="submit"]') + ");"
            "if(!btn)return 'no-submit';"
            "btn.click();return 'clicked';})()"
        )
        opened = False
        sent = False
        href = ""
        saw_page = False
        deadline = time.time() + 25
        while time.time() < deadline:
            time.sleep(0.8)
            try:
                got = _cdp_call(ws, 60, "Runtime.evaluate", {
                    "expression": "JSON.stringify({href:location.href,html:document.documentElement?document.documentElement.outerHTML:''})",
                    "returnByValue": True,
                }, wait=8)
            except Exception:
                continue
            raw = ((got.get("result") or {}).get("result") or {}).get("value") or ""
            try:
                snap = json.loads(raw)
            except Exception:
                continue
            href = str(snap.get("href") or "")
            html = str(snap.get("html") or "")
            if href and _on_forum(href) and "login" in href.lower():
                return href
            if html and not _challenge_page(html):
                saw_page = True
            if sent and _topic(href) and not _challenge_page(html):
                return href
            if (not opened) and saw_page:
                try:
                    opened_msg = _cdp_call(ws, 61, "Runtime.evaluate", {
                        "expression": open_edit,
                        "returnByValue": True,
                    }, wait=8)
                    opened_word = ((opened_msg.get("result") or {}).get("result") or {}).get("value") or ""
                    if opened_word == "opened":
                        opened = True
                except Exception:
                    continue
            if opened and (not sent) and (not _challenge_page(html)) and ('name="Post"' in html):
                try:
                    filled = _cdp_call(ws, 62, "Runtime.evaluate", {
                        "expression": fill,
                        "returnByValue": True,
                    }, wait=8)
                    word = ((filled.get("result") or {}).get("result") or {}).get("value") or ""
                    if word == "title":
                        return href
                    if word == "clicked":
                        sent = True
                except Exception:
                    continue
        if sent and href:
            return href
        if saw_page:
            return "no-edit"
        raise OSError("post")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        shutil.rmtree(prof, ignore_errors=True)


def _chrome_post(subject, text, cookie, forum=None):
    """Submit a board 268 trade from the forum's own New Trade link.

    The trading board does not open on the old compose address. That address
    answers Invalid Action. The form that does open names the title ttitle, the
    message Post, and the button submit. A title longer than 50 characters
    is the board's own limit, and this function does not send it.
    Returns the URL the browser landed on. Raises OSError when that browser
    does not finish. The cookie is not logged. His open Chrome is not the one
    this starts.
    """
    import time
    import websocket
    _sweep_stale_scratch()
    prof = tempfile.mkdtemp(prefix="d2jsp-post-")
    sock = __import__("socket").socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    browser = _chrome_bin()
    if not browser:
        raise OSError("chrome")
    proc = subprocess.Popen(
        [browser, "--headless=new", "--disable-gpu", "--no-first-run",
         "--no-default-browser-check", "--disable-blink-features=AutomationControlled",
         "--remote-debugging-port=%d" % port, "--user-data-dir=%s" % prof,
         "--remote-allow-origins=*", "--window-size=1100,800", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    base = "http://127.0.0.1:%d" % port
    ws = None
    try:
        deadline = time.time() + 12
        while time.time() < deadline:
            try:
                urllib.request.urlopen(base + "/json/version", timeout=2)
                break
            except Exception:
                time.sleep(0.2)
        else:
            raise OSError("chrome")
        tab = json.loads(urllib.request.urlopen(
            urllib.request.Request(base + "/json/new?about:blank", method="PUT"),
            timeout=10,
        ).read().decode("utf-8", "replace"))
        ws = websocket.create_connection(
            tab["webSocketDebuggerUrl"], timeout=20, origin=base,
        )
        _cdp_call(ws, 1, "Network.enable")
        _cdp_call(ws, 2, "Network.setUserAgentOverride", {"userAgent": chrome_user_agent()})
        ident = 10
        for part in str(cookie or "").split(";"):
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            name = name.strip()
            if not name:
                continue
            _cdp_call(ws, ident, "Network.setCookie", {
                "name": name,
                "value": value,
                "url": "https://forums.d2jsp.org/",
                "domain": ".d2jsp.org",
                "path": "/",
                "secure": True,
            })
            ident += 1
        board = _post_board(forum) or BOARD
        _cdp_call(ws, 50, "Page.enable")
        _cdp_call(ws, 51, "Page.navigate", {
            "url": "https://forums.d2jsp.org/forum.php?f=%d" % board,
        })
        open_trade = (
            "(function(){var as=document.querySelectorAll('a');"
            "for(var i=0;i<as.length;i++){"
            "var label=(as[i].textContent||'').replace(/\\s+/g,' ').trim();"
            "if(label!=='New Trade')continue;"
            "var href=as[i].href||'';"
            "if(href.indexOf('/post.php')<0)continue;"
            "location.href=href;return 'opened';}"
            "return 'no-trade';})()"
        )
        fill = (
            "(function(){var box=document.querySelector("
            + json.dumps('textarea[name="Post"]') + ");"
            "var title=document.querySelector("
            + json.dumps('input[name="ttitle"]') + ");"
            "if(!box||!title||!box.form)return 'no-form';"
            "var subject=" + json.dumps(str(subject or "")) + ";"
            "if(subject.length>50)return 'title';"
            "title.value=subject;box.value=" + json.dumps(str(text or "")) + ";"
            "var picked=false;var labs=document.querySelectorAll('label');"
            "for(var i=0;i<labs.length;i++){"
            "if((labs[i].textContent||'').indexOf('Selling Item')<0)continue;"
            "var input=document.getElementById(labs[i].htmlFor||'');"
            "if(input&&input.name==='sType'){input.checked=true;picked=true;}}"
            "if(!picked)return 'no-sell';"
            "var paid=['sItalic','sBold','sRed'];"
            "for(var p=0;p<paid.length;p++){"
            "var extra=box.form.querySelector('input[name=\"'+paid[p]+'\"]');"
            "if(extra)extra.checked=false;}"
            "var btn=box.form.querySelector("
            + json.dumps('input[name="submit"]') + ");"
            "if(!btn)return 'no-submit';"
            "btn.click();return 'clicked';})()"
        )
        opened = False
        sent = False
        href = ""
        deadline = time.time() + 25
        while time.time() < deadline:
            time.sleep(0.8)
            try:
                got = _cdp_call(ws, 60, "Runtime.evaluate", {
                    "expression": "JSON.stringify({href:location.href,html:document.documentElement?document.documentElement.outerHTML:''})",
                    "returnByValue": True,
                }, wait=8)
            except Exception:
                continue
            raw = ((got.get("result") or {}).get("result") or {}).get("value") or ""
            try:
                snap = json.loads(raw)
            except Exception:
                continue
            href = str(snap.get("href") or "")
            html = str(snap.get("html") or "")
            if _topic(href) and not _challenge_page(html):
                return href
            if (not opened) and (not _challenge_page(html)) and ("New Trade" in html):
                try:
                    opened_msg = _cdp_call(ws, 61, "Runtime.evaluate", {
                        "expression": open_trade,
                        "returnByValue": True,
                    }, wait=8)
                    opened_word = ((opened_msg.get("result") or {}).get("result") or {}).get("value") or ""
                    if opened_word == "opened":
                        opened = True
                except Exception:
                    continue
            if opened and (not sent) and (not _challenge_page(html)) and ('name="Post"' in html):
                try:
                    filled = _cdp_call(ws, 62, "Runtime.evaluate", {
                        "expression": fill,
                        "returnByValue": True,
                    }, wait=8)
                    word = ((filled.get("result") or {}).get("result") or {}).get("value") or ""
                    if word == "title":
                        return href
                    if word == "clicked":
                        sent = True
                except Exception:
                    continue
        if href:
            return href
        raise OSError("post")
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        shutil.rmtree(prof, ignore_errors=True)


def d2jsp_quote(item, origin, host, port, cookie_get=None, transport=None, node_run=None, chrome_fetch=None, sec_fetch_site=None):
    """Read one item's fg range from the Switch Ladder search. -> (http code, dict)

    The dict is the reading. It never carries the cookie or the page.
    No login, a challenge page, or no fg on a line that names the item stays unknown.
    """
    import datetime
    read_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    item = str(item or "").strip()[:80]
    if not console_may_post(origin, host, port, sec_fetch_site):
        return 403, _quote_unknown(item, read_at, "origin")
    if not item:
        return 200, _quote_unknown(item, read_at, "no item")
    get_cookie = cookie_get or live_cookie_header
    try:
        cookie, cookie_reason = get_cookie()
    except Exception:
        cookie, cookie_reason = None, "chrome-unread"
    if not cookie:
        return 200, _quote_unknown(item, read_at, cookie_reason or "need-login")
    fetch = transport or _transport
    headers = _headers(cookie)
    headers["Referer"] = "https://forums.d2jsp.org/forum.php?f=%d" % QUOTE_BOARD
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        status, hdrs, raw = fetch("POST", _search_url(item), headers, _search_body(item))
    except Exception:
        return 200, _quote_unknown(item, read_at, "unread")
    if status in (301, 302, 303, 307, 308):
        loc = ""
        if isinstance(hdrs, dict):
            loc = hdrs.get("Location") or hdrs.get("location") or ""
        if "login" in str(loc).lower():
            return 200, _quote_unknown(item, read_at, "need-login")
        return 200, _quote_unknown(item, read_at, "unread")
    if isinstance(raw, (bytes, bytearray)):
        page = raw.decode("utf-8", "replace")
    else:
        page = str(raw or "")
    if _challenge_page(page) and chrome_fetch is not False:
        opener = chrome_fetch or _chrome_search
        try:
            opened = opener(item, cookie)
        except Exception:
            opened = page
        if isinstance(opened, str) and opened and not _challenge_page(opened):
            page = opened
    return 200, parse_public_quote(page, item, read_at, node_run=node_run)


def open_quote_login_once():
    """Open the Chrome login at most once per process. The price stays unknown either way."""
    global quote_login_opened
    with _quote_login_lock:
        if quote_login_opened:
            return False
        quote_login_opened = True
    try:
        return bool(_open_chrome_login())
    except Exception:
        return None


def _post_board(forum):
    """268 is RotW softcore. 271 is RotW softcore ladder. Anything else is refused."""
    try:
        n = int(forum)
    except (TypeError, ValueError):
        return None
    return n if n in POST_BOARDS else None


def _topic_on_board(url, forum):
    """A saved topic is edited only when it is the board this post is for.

    A topic with no f= belongs to board 268, which is the only board a post
    could have saved before the ladder board existed. A 268 topic is not
    edited as a 271 trade.
    """
    public = _public_topic(url)
    if not public:
        return False
    try:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(public).query)
        raw = (query.get("f") or [None])[0]
        found = int(raw) if raw is not None else None
    except (TypeError, ValueError):
        found = None
    if found is None:
        return int(forum) == BOARD
    return found == int(forum)


def _public_topic(url):
    """A topic URL that is safe to show. Anything else is empty."""
    if not _topic(url):
        return ""
    raw = str(url or "").strip()
    if raw.startswith("/") and not raw.startswith("//"):
        raw = "https://%s%s" % (_HOST, raw.split("#", 1)[0])
    try:
        parts = urllib.parse.urlparse(raw)
    except Exception:
        return ""
    if parts.scheme != "https" or parts.netloc != _HOST:
        return ""
    if "topic.php" not in (parts.path or ""):
        return ""
    return urllib.parse.urlunparse(("https", _HOST, parts.path, "", parts.query, ""))


def _send_edit(subject, text, cookie, topic, edit_post, open_login):
    """Update one saved topic. A missing Edit door does not start a new trade."""
    opener = edit_post or _chrome_edit
    landed = None
    try:
        landed = opener(topic, subject, text, cookie)
    except OSError as stuck:
        landed = stuck
    if isinstance(landed, OSError) or not landed or landed == "no-edit":
        if landed == "no-edit":
            return 200, {"ok": False, "reason": "not-posted"}
        return 200, {"ok": False, "reason": "unread"}
    landed = str(landed)
    public = _public_topic(landed)
    if public:
        return 200, {"ok": True, "reason": "submitted", "topic": public}
    if _on_forum(landed) and "login" in landed.lower():
        door = open_login or _open_chrome_login
        opened = False
        try:
            opened = bool(door())
        except Exception:
            opened = False
        return 200, {"ok": False, "reason": "need-login", "opened": opened}
    return 200, {"ok": False, "reason": "not-posted"}


def _send_through_chrome(subject, text, cookie, chrome_post, open_login, forum=None):
    """One scratch-Chrome submit. A topic URL is the only submitted receipt."""
    opener = chrome_post or _chrome_post
    board = _post_board(forum) or BOARD
    landed = None
    try:
        if opener is _chrome_post:
            landed = opener(subject, text, cookie, board)
        else:
            landed = opener(subject, text, cookie)
    except OSError as stuck:
        landed = stuck
    if isinstance(landed, OSError) or not landed:
        return 200, {"ok": False, "reason": "unread"}
    landed = str(landed)
    public = _public_topic(landed)
    if public:
        return 200, {"ok": True, "reason": "submitted", "topic": public}
    if _on_forum(landed) and "login" in landed.lower():
        door = open_login or _open_chrome_login
        opened = False
        try:
            opened = bool(door())
        except Exception:
            opened = False
        return 200, {"ok": False, "reason": "need-login", "opened": opened}
    return 200, {"ok": False, "reason": "not-posted"}


def d2jsp_send(body, origin, host, port, cookie_get=None, transport=None, open_login=None, chrome_post=None, edit_post=None, sec_fetch_site=None):
    """Post one desk draft. -> (http code, {ok, reason, opened?})

    The dict never carries the cookie, the page, or the draft.
    """
    if not console_may_post(origin, host, port, sec_fetch_site):
        return 403, {"ok": False, "reason": "origin"}
    body = body if isinstance(body, dict) else {}
    try:
        forum = int(body.get("forum"))
    except (TypeError, ValueError):
        forum = 0
    if _post_board(forum) is None:
        return 200, {"ok": False, "reason": "wrong-board"}
    subject = str(body.get("subject") or "").strip()
    text = str(body.get("body") or "").strip()
    if len(text) > 4000:
        return 200, {"ok": False, "reason": "long"}
    if not _priced(subject, text):
        return 200, {"ok": False, "reason": "no-price"}
    if len(subject) > 50:
        return 200, {"ok": False, "reason": "title"}
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
    topic = _public_topic(str(body.get("topic") or ""))
    if topic and not _topic_on_board(topic, forum):
        topic = ""
    if topic:
        opener = edit_post
        if opener is None and chrome_post is False:
            opener = lambda *args: "no-edit"
        return _send_edit(subject, text, cookie, topic, opener, open_login)
    if transport is None and chrome_post is not False:
        return _send_through_chrome(subject, text, cookie, chrome_post, open_login, forum)
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
    raw_text = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw or "")
    if _challenge_page(raw_text) and chrome_post is not False:
        return _send_through_chrome(subject, text, cookie, chrome_post, open_login, forum)
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
    post_text = raw.decode("utf-8", "replace") if isinstance(raw, (bytes, bytearray)) else str(raw or "")
    if _challenge_page(post_text) and chrome_post is not False:
        return _send_through_chrome(subject, text, cookie, chrome_post, open_login, forum)
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
