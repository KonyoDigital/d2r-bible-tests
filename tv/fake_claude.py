#!/usr/bin/env python3
# 📺 TV DIABLO — fake claude binary for worker TDD (v713). Speaks just enough
# stream-json: each user line gets one {"type":"result"} with a canned read.
# TV_FAKE_MODE: ok (default) · slow (never answers — timeout path) · junk (non-JSON result)
import json, os, sys, time

mode = os.environ.get("TV_FAKE_MODE", "ok")
if "--input-format" not in sys.argv:
    # one-shot form: claude -p <prompt> --output-format text
    if mode == "ok":
        print(json.dumps({"area": "Oneshot Plains", "scene": "loot", "names": ["Ist Rune"], "tz": []}))
    sys.exit(0)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    if mode == "slow":
        time.sleep(9999)
    if mode == "junk":
        print(json.dumps({"type": "result", "result": "sorry, here is prose with no json"}), flush=True)
        continue
    print(json.dumps({"type": "system", "subtype": "init"}), flush=True)
    print(json.dumps({"type": "result", "result": json.dumps(
        {"area": "Worker Keep", "scene": "loot", "names": ["Vex Rune"], "tz": ["Spider Forest"]})}), flush=True)
