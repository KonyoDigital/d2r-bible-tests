# -*- coding: utf-8 -*-
"""#186 STEP 3 - THE CARRIER: A LAW ONE PC PROVED OVER THESE BYTES IS NOT PROVED AGAIN ON ANOTHER PC WITH THE SAME BYTES.

His ruling, 2026-10-28: "identical bytes saved from the windows alt pc that has already been proved. he doesnt need to
reprove it all". Steps 1+2 (REG-2715) made a PC's own census serve what that PC already banked; this carries one PC's
bank to another.

  publish(): this PC writes `heart2 --export-proved` (only the PROVENs ITS clean HEAD's bytes still key) and posts it to
             /api/proofs, signed with its roster key (roster_sign) - the route stores only a body that key signed.
  take():    this PC asks /api/proofs for each same-platform peer's last export; one carried at THIS PC's HEAD goes to a
             scratch file and to `heart2 --import-proved`, which re-keys every entry on THIS PC's bytes and banks only
             what matches (REG-2630). Another HEAD is skipped and said; a refused import changes nothing.

Every network call and every heart2 run is a parameter, so a law drives this with fixtures and never reaches the site,
his verdict cache or his checkout. Nothing here deletes or rewrites a proof he banked: an import only adds. -> receipts
(dicts) that say what happened, UNKNOWN never read as nothing. [[heart-first]] [[unknown-stays-unknown]]
"""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://bull-4-u.com/api/proofs"
#: the site's Basic gate - public, and no longer what lets anything be written (roster.js #95 says why)
AUTH = "Basic " + base64.b64encode(b"app:DeanDiablo").decode()
#: the platforms whose proofs may stand for each other: the same word sys.platform gives
PLATFORM = sys.platform
EXPORT_TIMEOUT_S = 600
IMPORT_TIMEOUT_S = 600


def _tail(text, n=300):
    return " ".join(str(text or "").strip().split())[-n:]


def run_heart2(args, timeout):
    """`python heart2.py <args>` in this checkout. -> (exit code or None, its last words)"""
    try:
        p = subprocess.run([sys.executable, os.path.join(HERE, "heart2.py")] + list(args), cwd=HERE,
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        return None, "heart2 did not finish in %d s" % timeout
    except Exception as e:
        return None, "heart2 could not be started (%s)" % type(e).__name__
    return p.returncode, _tail((p.stdout or "") + " " + (p.stderr or ""))


def http_get(url, timeout=20):
    """GET one /api/proofs answer. -> dict, or {ok: False, why} - never raises"""
    try:
        req = urllib.request.Request(url, headers={"Authorization": AUTH, "User-Agent": "TVD-Console/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            got = json.loads(r.read().decode("utf-8", "replace"))
        return got if isinstance(got, dict) else {"ok": False, "why": "the answer was not a record"}
    except Exception as e:
        return {"ok": False, "why": "the proofs route could not be read (%s)" % type(e).__name__}


def http_post(url, raw, headers, timeout=60):
    """POST one signed export. -> dict, or {ok: False, why} - never raises"""
    try:
        h = {"Content-Type": "application/json", "User-Agent": "TVD-Console/1.0", "Authorization": AUTH}
        h.update(headers or {})
        req = urllib.request.Request(url, data=raw, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            got = json.loads(r.read().decode("utf-8", "replace"))
        return got if isinstance(got, dict) else {"ok": False, "why": "the answer was not a record"}
    except Exception as e:
        return {"ok": False, "why": "the proofs route could not be reached (%s)" % type(e).__name__}


def export_payload(owner, platform=PLATFORM, run=run_heart2):
    """This PC's export, wrapped for /api/proofs. -> (bytes, None) | (None, why)"""
    d = tempfile.mkdtemp(prefix="proofs_out_")
    try:
        rc, said = run(["--export-proved", d], EXPORT_TIMEOUT_S)
        if rc != 0:
            return None, "the export was refused or failed (%s): %s" % (rc, said)
        try:
            with open(os.path.join(d, ".heart2_cache.json"), encoding="utf-8") as fh:
                ex = json.load(fh)
        except Exception as e:
            return None, "the export file could not be read (%s)" % type(e).__name__
        head = ((ex or {}).get("export") or {}).get("head") if isinstance(ex, dict) else None
        if not head:
            return None, "the export carries no HEAD in its manifest"
        payload = {"owner": owner, "platform": platform, "head": head, "export": ex}
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def publish(owner, key_path, platform=PLATFORM, run=run_heart2, post=http_post, sign=None):
    """Export this PC's proofs and post them signed. -> receipt {ok, stored?, head?, count?, why?}"""
    raw, why = export_payload(owner, platform, run)
    if raw is None:
        return {"ok": False, "why": why}
    if sign is None:
        import roster_sign as _rs
        sign = _rs.sign_headers
    try:
        headers, signing = sign(key_path, raw)
    except Exception as e:
        return {"ok": False, "why": "the signer raised %s" % type(e).__name__}
    if not (isinstance(signing, dict) and signing.get("signed")):
        # a roster row may post unsigned; a proof may not - the route would refuse it, so it is not sent
        return {"ok": False, "why": "not sent: the export could not be signed (%s)" % (signing or {}).get("why")}
    got = post(URL, raw, headers)
    return dict(got, signing=signing)


def head_of(run_git=None):
    """This checkout's HEAD. -> 40-hex, or None (UNKNOWN)"""
    try:
        if run_git is not None:
            out = run_git()
        else:
            out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=20).stdout
        out = str(out or "").strip()
        return out if len(out) == 40 else None
    except Exception:
        return None


def take(peers, head, platform=PLATFORM, get=http_get, run=run_heart2):
    """Bank each same-platform peer's export carried at THIS head. -> receipt {imported: [...], skipped: [...]}

    head None is UNKNOWN: nothing is fetched (an import into an unknown HEAD would be refused anyway)."""
    out = {"head": head, "imported": [], "skipped": []}
    if not head:
        out["why"] = "this checkout's HEAD is UNKNOWN - nothing was asked"
        return out
    for owner in peers or []:
        q = URL + "?owner=" + urllib.parse.quote(owner)
        meta = get(q)
        if not meta.get("ok"):
            out["skipped"].append({"owner": owner, "why": meta.get("why") or "the route said no"})
            continue
        if not meta.get("have"):
            out["skipped"].append({"owner": owner, "why": "no export carried"})
            continue
        if meta.get("platform") != platform:
            out["skipped"].append({"owner": owner, "why": "carried on %s, this PC is %s" % (meta.get("platform"), platform)})
            continue
        if meta.get("head") != head:
            out["skipped"].append({"owner": owner, "why": "carried at %s, this PC is at %s"
                                   % (str(meta.get("head"))[:12], head[:12])})
            continue
        full = get(q + "&body=1")
        ex = full.get("export") if full.get("ok") else None
        if not isinstance(ex, dict):
            out["skipped"].append({"owner": owner, "why": full.get("why") or "the export itself did not come back"})
            continue
        d = tempfile.mkdtemp(prefix="proofs_in_")
        try:
            path = os.path.join(d, ".heart2_cache.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(ex, fh)
            # REG-3045 - a CARRIED import: heart2 refuses it whole unless its runtime matches this PC's, and marks every
            # entry it banks with who carried it, under which key
            args = ["--import-proved", path, "--carried-by", owner]
            if meta.get("keyId"):
                args += ["--carried-key", str(meta.get("keyId"))]
            rc, said = run(args, IMPORT_TIMEOUT_S)
        finally:
            shutil.rmtree(d, ignore_errors=True)
        _b = re.search(r"REG-3045 CARRIED from .*?: (\d+) banked", str(said or ""))
        row = {"owner": owner, "count": meta.get("count"), "at": meta.get("at"), "rc": rc, "said": said,
               "banked": int(_b.group(1)) if _b else None}      # None: heart2 did not say (UNKNOWN, never 0)
        (out["imported"] if rc == 0 else out["skipped"]).append(row if rc == 0 else dict(row, why="the import refused it"))
    return out
