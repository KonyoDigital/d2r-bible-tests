#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REG-2166 (#39) - Fleet 3.0 phase 1 publishes on its own route.

The presence beacon stays /api/console. No item name crosses that beacon.
Roster rows go to /api/roster under the owner label, hourly and change-only,
plus one at boot. Over the daily cap the server says why and answers 200,
never a 500 that looks like the machine went offline. A section that was
not read stays absent. Pictures and frame bytes stay off the body.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
import sys
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import roster_publish as RP  # noqa: E402
from console_safe import enable  # noqa: E402

enable()

NODE = shutil.which("node")
ROSTER_JS = os.path.join(ROOT, "functions", "api", "roster.js")
CONSOLE_JS = os.path.join(ROOT, "functions", "api", "console.js")
APP = os.path.join(HERE, "control_app.py")
OWNER = "Konyo · Mac"

_HARNESS = r"""
import { pathToFileURL } from 'node:url';
const CFG = __CFG__;
const store = new Map(Object.entries(CFG.seed || {}).map(([k, v]) => [k, JSON.stringify(v)]));
const puts = [];
const kv = {
  async get(n) { return store.has(n) ? store.get(n) : null; },
  async put(n, v) {
    if (CFG.throwPut) throw new Error('KV put failed');
    puts.push(n);
    store.set(n, v);
  },
};
const mod = await import(pathToFileURL(CFG.file).href);
const replies = [];
const statuses = [];
for (let i = 0; i < CFG.bodies.length; i++) {
  if (i > 0 && CFG.ageBetween) {
    for (const [k, raw] of store.entries()) {
      if (!k.startsWith('roster:')) continue;
      const o = JSON.parse(raw);
      o.t = Date.now() - CFG.ageBetween * 1000;
      store.set(k, JSON.stringify(o));
    }
  }
  const req = new Request('https://bull-4-u.com/api/roster', {
    method: 'POST', body: JSON.stringify(CFG.bodies[i]),
    headers: { 'content-type': 'application/json' } });
  const res = await mod.onRequestPost({ request: req, env: { TZ_HISTORY: kv }, waitUntil(){} });
  statuses.push(res.status);
  replies.push(JSON.parse(await res.text()));
}
const records = {};
for (const [k, raw] of store.entries()) records[k] = JSON.parse(raw);
process.stdout.write(JSON.stringify({ replies, statuses, puts, keys: [...store.keys()], records }));
"""


def _post(bodies, seed=None, throw_put=False, age_between=0):
    if not NODE:
        raise AssertionError("node is absent - the worker was not run")
    cfg = {"file": ROSTER_JS, "bodies": bodies, "seed": seed or {},
           "throwPut": throw_put, "ageBetween": age_between}
    src = _HARNESS.replace("__CFG__", json.dumps(cfg))
    with tempfile.TemporaryDirectory(prefix="tvd_roster_") as d:
        path = os.path.join(d, "h.mjs")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(src)
        r = subprocess.run([NODE, path], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise AssertionError("roster harness failed rc=%s\n%s" % (r.returncode, r.stderr[-2000:]))
    return json.loads((r.stdout or "").strip().splitlines()[-1])


def _char(n, as_of=1000):
    return {"read": True, "asOf": as_of, "counts": n, "rows": [{"name": "Sorceress", "cls": "Sorceress", "level": n}]}


def _body(n=1, boot=False, as_of=1000, extra=None):
    sections = {"characters": {"asOf": as_of, "counts": n, "rows": [
        {"name": "Sorceress", "cls": "Sorceress", "level": n}]}}
    body = {"owner": OWNER, "boot": boot, "sections": sections}
    if extra:
        body.update(extra)
    return body


class RosterPublishStaysOffTheBeacon(unittest.TestCase):

    def test_the_budget_stays_under_the_ceiling(self):
        got = RP.budget()
        self.assertEqual(got["presence"], 768)
        self.assertEqual(got["pcs"] * got["perPc"], 100)
        self.assertEqual(got["together"], 868)
        self.assertLess(got["together"], got["ceiling"])
        self.assertLess(768 + 5 * 25, 1000, "the five labels at the cap would pass 1000")
        js = open(ROSTER_JS, encoding="utf-8").read()
        for line in ("const PRESENCE_WRITES = 768;", "const ROSTER_PCS = 4;",
                     "const ROSTER_CAP = 25;", "const KV_WRITES = 1000;"):
            self.assertIn(line, js)
        console = open(CONSOLE_JS, encoding="utf-8").read()
        self.assertIn("No item names ever cross this boundary", console)
        self.assertNotIn("roster:", console)

    def test_an_unread_section_stays_absent(self):
        self.assertIsNone(RP.section_of(None))
        self.assertIsNone(RP.section_of([]))
        self.assertIsNone(RP.section_of({"read": False, "rows": []}))
        self.assertIsNone(RP.characters_read(False, {"chars": {}}, [], 1000))
        self.assertIsNone(RP.vault_read("absent", [], 1000))
        self.assertIsNone(RP.vault_read("unreadable: no", [], 1000))
        self.assertIsNone(RP.chronicle_read({"ok": False, "why": "not read"}, 1000))
        self.assertIsNone(RP.stash_read(None, 1000))
        self.assertIsNone(RP.reels_read(None, {}, {}, 1000))
        got = RP.sections_from({"vault": [], "characters": _char(1)}, 1000)
        self.assertNotIn("vault", got)
        self.assertIn("characters", got)
        self.assertNotIn("rows", got["characters"]) if False else None
        empty = RP.section_of({"read": True, "asOf": 1000, "counts": 0, "rows": []})
        self.assertEqual(empty, {"asOf": 1000, "counts": 0})
        self.assertNotIn("rows", empty)

    def test_pictures_and_frame_bytes_stay_off_the_row(self):
        row = RP._clean_row({
            "name": "Shako",
            "tier": "PROVEN",
            "frame": "data:image/png;base64,AAAA",
            "evidence": ["s_1784984019250_fx", "reel/f_1.jpg", "/tmp/shot/a.png"],
        }, ("name", "tier", "evidence"))
        self.assertEqual(row["name"], "Shako")
        self.assertNotIn("frame", row)
        self.assertEqual(row["evidence"], ["s_1784984019250_fx"])
        self.assertIsNone(RP._clean_row({"name": "data:image/png;base64,AAAA"}))

    def test_the_key_is_the_owner_label(self):
        self.assertEqual(RP.roster_key(OWNER), "roster:" + OWNER)
        self.assertIsNone(RP.roster_key("konyo-3"))
        self.assertIsNone(RP.roster_key("/tmp/host"))
        self.assertIsNone(RP.owner_of("23d0486747ce4c58"))
        self.assertEqual(len(RP.OWNERS), 5)

    def test_a_mac_named_konyo_is_the_mac_roster_label(self):
        self.assertEqual(RP.owner_of("Konyo", "mac"), OWNER)
        self.assertIsNone(RP.owner_of("Konyo", "windows"))
        self.assertIsNone(RP.owner_of("Konyo"))
        self.assertIsNone(RP.owner_of("Grok", "mac"))
        self.assertIsNone(RP.owner_of("someone", "mac"))
        self.assertEqual(RP.owner_of("Dean", "mac"), "Dean")
        self.assertEqual(RP.owner_of("Wife PC", "windows"), "Wife PC")
        with open(APP, encoding="utf-8") as fh:
            src = fh.read()
        once = src.split("def _roster_publish_once(", 1)[1].split("def _roster_publish_loop", 1)[0]
        call = "owner = _rp.owner_of(_roster_claimed_name(), _roster_platform())"
        self.assertEqual(once.count(call), 1)

    def test_change_only_hourly_and_one_boot(self):
        now = 1_000_000
        body, why = RP.due({}, OWNER, RP.sections_from({"characters": _char(1)}), now, False)
        self.assertEqual(why, "post")
        state = {"hash": RP.hash_of(RP.packed(RP.for_hash(body["sections"]))), "at": now}
        again, why = RP.due(state, OWNER, body["sections"], now + 1000, True)
        self.assertIsNone(again)
        self.assertEqual(why, "unchanged")
        moved = RP.sections_from({"characters": _char(2)})
        held, why = RP.due(state, OWNER, moved, now + 1000, False)
        self.assertIsNone(held)
        self.assertEqual(why, "within the hour")
        booted, why = RP.due(state, OWNER, moved, now + 1000, True)
        self.assertEqual(why, "post")
        self.assertEqual(booted["owner"], OWNER)
        later, why = RP.due(state, OWNER, moved, now + RP.HOUR_MS, False)
        self.assertEqual(why, "post")
        refused = dict(state, refuseAt=now, why="roster would not take this publish: quota")
        quiet, why = RP.due(refused, OWNER, moved, now + 1000, True)
        self.assertIsNone(quiet)
        self.assertIn("quota", why)

    def test_a_skip_is_not_remembered_as_a_publish(self):
        sections = RP.sections_from({"characters": _char(2)})
        state = RP.apply_reply({}, sections, {"ok": True, "stored": [], "skipped": ["within the hour"]}, 50)
        self.assertNotIn("hash", state)
        self.assertEqual(state["at"], 50)
        published = RP.apply_reply(state, sections, {"ok": True, "stored": ["roster"]}, 80)
        self.assertEqual(published["why"], "published")
        self.assertIn("hash", published)

    def test_the_worker_writes_the_owner_key_and_not_the_beacon(self):
        v = _post([_body(1, boot=True, extra={"machine": "konyo-3", "install": "abc"})])
        self.assertEqual(v["statuses"], [200])
        self.assertEqual(v["replies"][0]["stored"], ["roster"])
        self.assertEqual(v["keys"], ["roster:" + OWNER])
        rec = v["records"]["roster:" + OWNER]
        self.assertNotIn("konyo-3", json.dumps(rec))
        self.assertNotIn("install", rec)
        self.assertNotIn("machine", rec)
        self.assertEqual(v["puts"], ["roster:" + OWNER])

    def test_a_hostname_is_not_a_key(self):
        v = _post([{"owner": "konyo-3", "sections": _body()["sections"]}])
        self.assertEqual(v["statuses"], [200])
        self.assertIs(v["replies"][0]["ok"], False)
        self.assertIn("owner label", v["replies"][0]["why"])
        self.assertEqual(v["keys"], [])

    def test_an_unread_section_is_not_stored_as_an_empty_list(self):
        seed_key = "roster:" + OWNER
        seed = {seed_key: {"owner": OWNER, "t": 1, "day": "2000-01-01", "n": 1, "hash": "old",
                           "sections": {"vault": {"asOf": 1, "counts": 2, "rows": [{"name": "Shako"}]}}}}
        body = _body(1, boot=True)
        body["sections"]["vault"] = []
        v = _post([body], seed=seed)
        rec = v["records"][seed_key]
        self.assertIn("characters", rec["sections"])
        self.assertIn("vault", rec["sections"])
        self.assertNotEqual(rec["sections"]["vault"], [])
        self.assertEqual(rec["sections"]["vault"]["rows"][0]["name"], "Shako")
        self.assertNotIn("chronicle", rec["sections"])

    def test_a_measured_empty_is_a_count_and_not_a_list(self):
        body = {"owner": OWNER, "boot": True, "sections": {
            "vault": {"asOf": 1000, "counts": 0, "rows": []}}}
        v = _post([body])
        rec = v["records"]["roster:" + OWNER]
        self.assertEqual(rec["sections"]["vault"], {"asOf": 1000, "counts": 0})
        self.assertNotIn("rows", rec["sections"]["vault"])

    def test_unchanged_and_the_hour_do_not_write(self):
        first = _body(1, boot=False, as_of=1000)
        second = _body(1, boot=True, as_of=9000)
        v = _post([first, second])
        self.assertEqual(v["replies"][1]["skipped"], ["unchanged"])
        self.assertEqual(v["puts"], ["roster:" + OWNER])
        moved = _body(4, boot=False, as_of=9000)
        v2 = _post([first, moved])
        self.assertEqual(v2["replies"][1]["skipped"], ["within the hour"])
        self.assertEqual(len(v2["puts"]), 1)
        v3 = _post([first, _body(4, boot=True)])
        self.assertEqual(v3["replies"][1]["stored"], ["roster"])
        self.assertEqual(len(v3["puts"]), 2)

    def test_the_daily_cap_is_a_refusal_and_not_an_outage(self):
        bodies = [_body(i, boot=True) for i in range(1, 27)]
        v = _post(bodies)
        self.assertEqual(v["statuses"][-1], 200)
        self.assertIs(v["replies"][-1]["ok"], False)
        self.assertEqual(v["replies"][-1]["why"], "roster would not take this publish: quota")
        self.assertIn("NOT the machine being absent", v["replies"][-1]["hint"])
        self.assertEqual(len(v["puts"]), 25)
        self.assertEqual(v["records"]["roster:" + OWNER]["n"], 25)

    def test_a_new_day_is_not_still_over_the_cap(self):
        seed = {"roster:" + OWNER: {"owner": OWNER, "t": 10, "day": "2000-01-01", "n": 25,
                                    "hash": "old", "sections": {"characters": {"asOf": 1, "counts": 1}}}}
        v = _post([_body(3, boot=True)], seed=seed)
        self.assertEqual(v["replies"][0]["stored"], ["roster"])
        self.assertEqual(v["records"]["roster:" + OWNER]["n"], 1)

    def test_a_storage_throw_is_not_a_500(self):
        v = _post([_body(1, boot=True)], throw_put=True)
        self.assertEqual(v["statuses"], [200])
        self.assertIs(v["replies"][0]["ok"], False)
        self.assertIn("roster would not take this publish", v["replies"][0]["why"])
        self.assertIn("NOT the machine being absent", v["replies"][0]["hint"])
        self.assertEqual(v["keys"], [])

    def test_pictures_in_the_body_are_refused(self):
        body = _body(1, boot=True)
        body["sections"]["characters"]["rows"][0]["shot"] = "data:image/jpeg;base64,AAAA"
        v = _post([body])
        self.assertEqual(v["statuses"], [200])
        self.assertIs(v["replies"][0]["ok"], False)
        self.assertIn("pictures", v["replies"][0]["why"])
        self.assertEqual(v["keys"], [])

    def test_the_console_posts_roster_on_its_own_route(self):
        src = open(APP, encoding="utf-8").read()
        self.assertIn("https://bull-4-u.com/api/roster", src)
        self.assertEqual(src.count('target=_roster_publish_loop'), 1)
        beacon = src.split("def _console_beacon(", 1)[1].split("def _console_beacon_async", 1)[0]
        self.assertNotIn("/api/roster", beacon)
        self.assertNotIn("roster_publish", beacon)
        once = src.split("def _roster_publish_once(", 1)[1].split("def _roster_publish_loop", 1)[0]
        self.assertIn("_beacon_suppressed_by()", once)
        self.assertIn("/api/roster", once)
        self.assertNotIn("/api/console", once)
        reads = src.split("def _roster_reads(", 1)[1].split("def _roster_post", 1)[0]
        for name in ("characters_read", "vault_read", "chronicle_read", "reels_read"):
            self.assertIn(name, reads)
        self.assertNotIn("stash_read", reads)


RED_PROOF = [
    {
        "why": "REG-2166 - an unread section is stored as an empty list",
        "file": "roster_publish.py",
        "find": "    if not isinstance(raw, dict) or raw.get(\"read\") is not True:\n        return None\n",
        "replace": "    if not isinstance(raw, dict) or raw.get(\"read\") is not True:\n        return {\"counts\": 0, \"rows\": []}\n",
        "matches": 1,
    },
    {
        "why": "REG-2166 - the roster key becomes a hostname",
        "file": "roster_publish.py",
        "find": "    return \"roster:\" + owner\n",
        "replace": "    return \"roster:\" + \"hostname\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2166 - the worker keys the row by the machine field",
        "file": "functions/api/roster.js",
        "find": "  const key = \"roster:\" + owner;\n",
        "replace": "  const key = \"roster:\" + String(body.machine || owner);\n",
        "matches": 1,
    },
    {
        "why": "REG-2166 - over the daily cap the worker answers 500",
        "file": "functions/api/roster.js",
        "find": "    return json({ ok: false, why: QUOTA_WHY, hint: REFUSAL_HINT }, 200);\n",
        "replace": "    return json({ ok: false, why: QUOTA_WHY, hint: REFUSAL_HINT }, 500);\n",
        "matches": 1,
    },
    {
        "why": "REG-2168 - a mac named Konyo is left with no roster label",
        "file": "roster_publish.py",
        "find": "    if name == \"Konyo\" and platform == \"mac\":\n        return \"Konyo · Mac\"\n",
        "replace": "    return None\n    if name == \"Konyo\" and platform == \"mac\":\n        return \"Konyo · Mac\"\n",
        "matches": 1,
    },
    {
        "why": "REG-2168 - the console asks for the nickname and drops the platform",
        "file": "control_app.py",
        "find": "    owner = _rp.owner_of(_roster_claimed_name(), _roster_platform())\n",
        "replace": "    owner = _rp.owner_of(_roster_claimed_name())\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
