"""Regenerate `unique_roster.json` FROM bible.html — the one source of the roster.

The roster rule ("ITEM_VALUE ∪ _UNI_EXTRA, minus every set piece in bare or suffixed form") is
already written, once, in bible.html's `_roster()`. Writing it a second time in Python would put
two authorities on one fact and let them drift apart quietly — so this script does not re-derive
it. It loads the real page in headless Chrome and asks `window._gUniqueRoster()`.

It also stamps `sourceHash`: the sha256 of the five bible.html lines the roster is built from
(ITEM_VALUE, _UNI_EXTRA, ITEM_SETS, SET_PIECES_EXTRA, SET_PIECES_EXTRA2). A test compares that
hash WITHOUT launching a browser, so a roster that has gone stale fails on his Mac in
milliseconds instead of going unnoticed until a name refuses to tick.

    python3 tv/roster_sync.py            # verify only — exits 1 if stale
    python3 tv/roster_sync.py --write    # regenerate (needs Chrome on :9224+)

Chrome rules per `chrome-cdp-mac`: never :9222 (his Chrome) or :9223 (TradingView), always a
scratch --user-data-dir, always --remote-allow-origins.
"""

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BIBLE = os.path.join(REPO, "bible.html")
OUT = os.path.join(HERE, "unique_roster.json")

# Each roster input is declared on ONE line in bible.html; hashing the declarations catches an item
# added, renamed or removed without reading the whole 43k-line file.
SOURCE_DECLS = (
    r"window\.ITEM_VALUE\s*=",
    r"const\s+_UNI_EXTRA\s*=",
    r"(?:const|var)\s+ITEM_SETS\s*=",
    r"(?:const|var)\s+SET_PIECES_EXTRA\s*=",
    r"(?:const|var)\s+SET_PIECES_EXTRA2\s*=",
)


def source_hash(bible_path=BIBLE):
    """sha256 over the roster's source declarations, in a fixed order.

    A declaration that is ABSENT is recorded as absent rather than skipped: if `SET_PIECES_EXTRA2`
    is ever renamed, the hash must move. Silently omitting a missing input would make the guard
    weaker exactly when the file changed most."""
    with open(bible_path, "r", encoding="utf-8", errors="ignore") as fh:
        lines = fh.read().splitlines()
    h = hashlib.sha256()
    for pat in SOURCE_DECLS:
        rx = re.compile(pat)
        hit = next((ln for ln in lines if rx.search(ln)), None)
        h.update((pat + "\x00" + (hit if hit is not None else "<ABSENT>") + "\n").encode("utf-8"))
    return h.hexdigest()


def load(path=OUT):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def is_stale(path=OUT, bible_path=BIBLE):
    """-> (stale: bool, why: str). Missing artifact counts as stale, never as fine."""
    if not os.path.exists(path):
        return True, "unique_roster.json does not exist"
    try:
        doc = load(path)
    except Exception as exc:
        return True, "unique_roster.json is unreadable: %s" % exc
    if not (doc.get("names") or []):
        return True, "unique_roster.json holds no names"
    want = source_hash(bible_path)
    got = doc.get("sourceHash")
    if got != want:
        return True, "bible.html roster sources changed (%s -> %s); run: python3 tv/roster_sync.py --write" % (
            str(got)[:12], want[:12])
    return False, "in sync (%d names)" % len(doc["names"])


def fetch_via_cdp(port=9224, timeout=180):
    """Ask the real page. Returns the roster list."""
    import time
    import urllib.request
    import websocket  # noqa: F401  — only needed on the --write path

    req = urllib.request.Request("http://127.0.0.1:%d/json/new?about:blank" % port, method="PUT")
    tgt = json.load(urllib.request.urlopen(req))
    ws = websocket.create_connection(tgt["webSocketDebuggerUrl"], timeout=timeout)
    n = [0]

    def send(method, **params):
        n[0] += 1
        ws.send(json.dumps({"id": n[0], "method": method, "params": params}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == n[0]:
                return msg

    send("Page.enable")
    send("Page.navigate", url="file://" + BIBLE)
    time.sleep(10)
    res = send("Runtime.evaluate",
               expression="JSON.stringify((window._gUniqueRoster&&window._gUniqueRoster())||[])",
               returnByValue=True)
    raw = (res.get("result", {}).get("result") or {}).get("value")
    if not raw:
        raise RuntimeError("the page returned no roster — it did not finish loading, or "
                           "_gUniqueRoster is gone: %s" % json.dumps(res)[:300])
    names = json.loads(raw)
    if len(names) < 300:
        # Never overwrite a good artifact with a half-loaded page. 398 measured 2026-08-18.
        raise RuntimeError("roster came back with only %d names; refusing to write a short roster"
                           % len(names))
    return names


def main(argv):
    import console_safe  # noqa: F401  — this prints an em dash; a non-UTF-8 console must not crash
    console_safe.enable()
    write = "--write" in argv
    if write:
        port = 9224
        for i, a in enumerate(argv):
            if a == "--port" and i + 1 < len(argv):
                port = int(argv[i + 1])
        names = fetch_via_cdp(port=port)
        doc = {
            "_comment": "GENERATED from bible.html window._gUniqueRoster(). Do not hand-edit — "
                        "run: python3 tv/roster_sync.py --write",
            "sourceHash": source_hash(),
            "count": len(names),
            "names": sorted(names),
        }
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print("wrote %s — %d names, sourceHash %s" % (OUT, len(names), doc["sourceHash"][:12]))
        return 0
    stale, why = is_stale()
    print(("STALE: " if stale else "OK: ") + why)
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
