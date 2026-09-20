#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v3387 - PRESENCE IS ONE READING, AND IT NAMES THE DOOR IT CAME THROUGH.

Konyo, 2026-09-20: "make sure to join them so there is not mismatch and unsycn between them so
they match and work as a one visual read."

THE DEFECT, AND IT CAUGHT ME BEFORE IT CAUGHT HIM.
This site records presence at two doors and, until now, THE FLEET could see only one:

    lastseen:<machine>   the TV-D console APP beaconing          -> read by /api/console
    visit:<ms>:<rand>    a browser page-view of /d2r/            -> read only by /visits

On 2026-09-19 I read Dean's fleet row as 26 hours and told Konyo he had been gone a day. He
answered: "he was logged in literally 6 hours ago i saw him with my eyes.. something is not
rendering to you properly or fethchin from the right information data".

He was right, and NOTHING WAS BROKEN. Dean's console app really had not beaconed in 26h, and
Dean really had been reading the bible six hours earlier, in a browser. Two true numbers about
one person, and a surface that showed one of them under the words "last seen" with no statement
of what the age was OF. A true number under a label that implies a larger claim misleads exactly
as well as a false one. [[label-outlived-referent]] [[the-unjoined-end]]

⚠ WHY A NEW KEY RATHER THAN READING `visit:`. The login name lives in the visit VALUE, so
grouping page-views by person means reading every one of them - and functions/api/console.js
already carries that scar in its own header: "Reading all 2,556 values blew the per-invocation
subrequest cap and 500'd the page." `webseen:<slug>` is one durable key per web identity, the
same shape `lastseen:` uses against the same problem.

WHAT THIS FILE PINS - behaviour first, and every case runs the REAL Cloudflare handler in node:
  * a page-view writes a durable per-person key, and an anonymous one is KEPT, not dropped
  * that write is throttled, so a reload loop cannot bill a KV write per reload
  * a machine row carries BOTH ages, and says which door produced the newer one
  * a web identity is attached to a row ONLY on an exact identity match - never a guess
  * an unmatched web identity is listed, never silently dropped
  * a machine with no web presence is UNCHANGED (the baseline that lets the case above mean
    something - without it, a handler that stamped every row would pass)
  * ONE normaliser serves both ends of the join
  * the rail renders the joined phrase, not the console beacon alone
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

# ⚠ THE READER HARNESS IS IMPORTED, NOT COPIED. test_console_fleet.py already drives these exact
# handlers in node against a stub KV; a second copy of it here is how the two console files came
# to share one bug in the first place. [[copy-drift]]
from test_console_fleet import run_handler, NODE           # noqa: E402

API = os.path.join(ROOT, "functions", "api", "console.js")
MW = os.path.join(ROOT, "functions", "_middleware.js")
UI = os.path.join(HERE, "control_ui.html")

# The WRITER needs its own harness and that is not drift: run_handler calls onRequestGet /
# onRequestPost, while the recorder lives behind _middleware's onRequest and only runs its KV
# write inside context.waitUntil - which run_handler deliberately stubs to a no-op. A put that is
# never awaited is a put the test cannot see. [[a-gate-can-perturb-what-it-measures]]
_MW_HARNESS = r"""
import { pathToFileURL } from 'node:url';
const CFG = __CFG__;
const store = new Map(Object.entries(CFG.seed || {}).map(([k, v]) => [k, JSON.stringify(v)]));
const puts = [];
const kv = {
  async get(name, type) {
    const v = store.get(name);
    if (v == null) return null;
    return type === 'json' ? JSON.parse(v) : v;
  },
  async put(name, value, opts) { puts.push({ name, value, opts: opts || null }); store.set(name, value); },
  async list() { return { keys: [], list_complete: true }; },
};
const mod = await import(pathToFileURL(CFG.file).href);
const waits = [];
const headers = {};
if (CFG.user != null) headers.Authorization = 'Basic ' + Buffer.from(CFG.user + ':pw').toString('base64');
const request = new Request(CFG.url, { method: CFG.method || 'GET', headers });
await mod.onRequest({
  request,
  env: { TZ_HISTORY: kv },
  next: async () => new Response('ok'),
  waitUntil: (p) => { waits.push(p); },
});
await Promise.all(waits.map((p) => Promise.resolve(p).catch(() => null)));
process.stdout.write(JSON.stringify({ puts }));
"""


def run_middleware(url="https://bull-4-u.com/d2r/", user="dean", seed=None, method="GET"):
    cfg = {"file": MW, "url": url, "user": user, "seed": seed or {}, "method": method}
    src = _MW_HARNESS.replace("__CFG__", json.dumps(cfg))
    with tempfile.TemporaryDirectory(prefix="tvd_webseen_") as d:
        p = os.path.join(d, "mw.mjs")
        io.open(p, "w", encoding="utf-8").write(src)
        out = subprocess.run([NODE, p], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise AssertionError("middleware harness failed (rc=%s)\nSTDERR:\n%s"
                             % (out.returncode, out.stderr[-3000:]))
    return json.loads((out.stdout or "").strip().splitlines()[-1])


def _webseen(puts):
    return [p for p in puts if str(p.get("name", "")).startswith("webseen:")]


# The reported case, as data. Dean's console last beaconed 26h ago; Dean was on the site 4h ago.
DEAN_BEACON = "2026-09-19T03:38:36.000Z"
DEAN_VISIT = "2026-09-20T04:10:00.000Z"


def rec(machine, t, **kw):
    d = {"machine": machine, "t": t, "install": "i-" + machine, "ver": "v3386"}
    d.update(kw)
    return d


class APresenceReadingNamesItsDoor(unittest.TestCase):

    # ---------- the writer ----------

    def test_a_page_view_leaves_a_durable_per_person_key(self):
        puts = _webseen(run_middleware(user="dean")["puts"])
        self.assertEqual(len(puts), 1, "a page-view wrote %d webseen keys, expected 1" % len(puts))
        self.assertEqual(puts[0]["name"], "webseen:dean")
        ttl = ((puts[0].get("opts") or {}).get("expirationTtl"))
        self.assertGreaterEqual(int(ttl or 0), 34560000,
                                "the web-presence key expires sooner than lastseen: does (400d), "
                                "so a person the fleet still lists would lose their web half first")
        self.assertEqual(json.loads(puts[0]["value"]).get("t") is not None, True)

    def test_a_visitor_with_no_login_name_is_kept_not_dropped(self):
        """'' is a REAL case: the Basic gate accepts any username and SITE_PASS may be unset.
        Dropping it is how a present person reads as absent. [[unknown-stays-unknown]]"""
        puts = _webseen(run_middleware(user="")["puts"])
        self.assertEqual([p["name"] for p in puts], ["webseen:_anon"],
                         "an unattributable visit vanished instead of landing in its own bucket")

    def test_a_reload_loop_cannot_bill_a_write_per_reload(self):
        """BASELINE PAIR with the case below: throttled must not mean 'never writes again'."""
        import datetime as _dt
        recent = _dt.datetime.now(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
        puts = _webseen(run_middleware(user="dean", seed={
            "webseen:dean": {"user": "dean", "slug": "dean", "t": recent}})["puts"])
        self.assertEqual(puts, [], "a page-view seconds after the last one still cost a KV write")

    def test_but_a_later_visit_does_write_again(self):
        puts = _webseen(run_middleware(user="dean", seed={
            "webseen:dean": {"user": "dean", "slug": "dean", "t": "2026-09-01T00:00:00.000Z"}})["puts"])
        self.assertEqual(len(puts), 1,
                         "the throttle swallowed a visit that was days newer - the key would "
                         "freeze at its first value and the join would go permanently stale")

    def test_an_unreadable_stored_stamp_rewrites_rather_than_suppresses(self):
        """A stored row whose time cannot be parsed must not be able to silence the writer
        forever. `age !== age` is the NaN test; getting it backwards is a silent off switch."""
        puts = _webseen(run_middleware(user="dean", seed={
            "webseen:dean": {"user": "dean", "slug": "dean", "t": "not-a-time"}})["puts"])
        self.assertEqual(len(puts), 1, "an unparseable stored stamp suppressed the write")

    def test_only_the_app_page_is_recorded(self):
        """An art asset or an api call is not a visit; the visit log already draws that line and
        the web-presence key must draw the SAME one or it will read busier than he is."""
        puts = _webseen(run_middleware(url="https://bull-4-u.com/d2r/art/foo.png")["puts"])
        self.assertEqual(puts, [], "a non-page request was recorded as somebody being here")

    # ---------- the join ----------

    def _fleet(self, seed):
        v = run_handler(API, seed=seed)
        return json.loads(v["text"])

    def test_the_reported_case_both_ages_and_which_is_newer(self):
        j = self._fleet({
            "lastseen:dean-pc": rec("dean-pc", DEAN_BEACON, nickname="Dean", user="dean"),
            "webseen:dean": {"user": "dean", "slug": "dean", "t": DEAN_VISIT},
        })
        rows = (j.get("online") or []) + (j.get("offline") or [])
        self.assertEqual(len(rows), 1, "expected exactly Dean's row, got %d" % len(rows))
        r = rows[0]
        self.assertEqual(r.get("t"), DEAN_BEACON, "the console age must survive the join")
        self.assertEqual(r.get("webAt"), DEAN_VISIT,
                         "the browser visit never reached the row - this is the whole defect")
        self.assertEqual(r.get("webVia"), "user", "the row does not record HOW it matched")
        self.assertEqual(r.get("seenAt"), DEAN_VISIT)
        self.assertEqual(r.get("seenVia"), "web",
                         "the newer of the two ages is not attributed to the door it came from")
        self.assertIs(r.get("seenBoth"), True)

    def test_a_machine_with_no_web_presence_is_unchanged(self):
        """THE BASELINE. Without it, a handler that stamped webAt on every row would satisfy the
        case above and this law would be measuring nothing. [[regression-guard]] section 5"""
        j = self._fleet({"lastseen:box-a": rec("box-a", DEAN_BEACON, nickname="Box", user="boxer")})
        r = ((j.get("online") or []) + (j.get("offline") or []))[0]
        self.assertIsNone(r.get("webAt"), "a row with no web identity was given one")
        self.assertIsNone(r.get("webVia"))
        self.assertEqual(r.get("seenVia"), "console")
        self.assertIs(r.get("seenBoth"), False)

    def test_a_web_identity_is_never_attached_to_somebody_elses_row(self):
        """The match is exact or it does not happen. Putting one person's presence on another
        person's row is a worse lie than the silence it replaces."""
        j = self._fleet({
            "lastseen:dean-pc": rec("dean-pc", DEAN_BEACON, nickname="Dean", user="dean"),
            "webseen:deanna": {"user": "deanna", "slug": "deanna", "t": DEAN_VISIT},
        })
        r = ((j.get("online") or []) + (j.get("offline") or []))[0]
        self.assertIsNone(r.get("webAt"),
                          "a DIFFERENT login name was matched onto Dean's row: %r"
                          % (r.get("webVia"),))
        self.assertEqual([w.get("user") for w in (j.get("webOnly") or [])], ["deanna"])

    def test_the_anonymous_bucket_never_claims_a_row(self):
        """A machine that reports no user must not inherit every unattributable visit on the
        site - that would hand one row the presence of everybody who never logged in."""
        j = self._fleet({
            "lastseen:box-a": rec("box-a", DEAN_BEACON, nickname="", user=""),
            "webseen:_anon": {"user": "", "slug": "_anon", "t": DEAN_VISIT},
        })
        r = ((j.get("online") or []) + (j.get("offline") or []))[0]
        self.assertIsNone(r.get("webAt"), "the anonymous web bucket was pinned onto a machine row")

    def test_a_browser_only_person_is_listed_rather_than_dropped(self):
        """A cousin who reads the bible and never runs the console emitted no beacon, so before
        v3387 he was not 'offline' on this panel - he did not exist on it at all."""
        j = self._fleet({
            "lastseen:dean-pc": rec("dean-pc", DEAN_BEACON, nickname="Dean", user="dean"),
            "webseen:cuz": {"user": "cuz", "slug": "cuz", "t": DEAN_VISIT},
        })
        self.assertEqual([w.get("user") for w in (j.get("webOnly") or [])], ["cuz"])
        rows = (j.get("online") or []) + (j.get("offline") or [])
        self.assertEqual(len(rows), 1,
                         "a browser-only identity was pushed into the MACHINE lists, where "
                         "fleet_drop_non_machines() will silently discard it for having no "
                         "install id")

    def test_the_scope_string_no_longer_under_claims(self):
        """Rule 3 of test_console_fleet applied here: the sentence that was true until v3386 is
        now the lie, and it is the sentence I myself read past twice."""
        j = self._fleet({"lastseen:box-a": rec("box-a", DEAN_BEACON)})
        scope = " ".join(str(j.get("scope") or "").split()).lower()
        self.assertNotIn("console app presence only", scope,
                         "the payload still tells its reader it cannot see browser visits")
        self.assertIn("webonly", scope.replace(" ", ""),
                      "the scope does not tell a reader where an unmatched visitor went")

    # ---------- one source, one surface ----------

    def test_both_ends_of_the_join_share_one_normaliser(self):
        src = io.open(API, encoding="utf-8").read()
        self.assertIn("import { webSeenSlug } from '../_middleware.js';", src,
                      "the reader grew its own copy of the slug rule - the two console files "
                      "already shared one bug exactly this way")
        self.assertIn("export function webSeenSlug(", io.open(MW, encoding="utf-8").read(),
                      "the writer no longer exports the normaliser the reader imports")

    def test_the_rail_renders_the_joined_phrase(self):
        """⚠ ANCHORED ON THE CALL, NOT THE NAME. This file and control_ui.html both DISCUSS
        _fleetSince(m.t) in prose; only the live sites carry it wrapped in escC(). Asserting on
        the bare name would be satisfied by the comment explaining the fix. [[source-reading-guard]] 4b"""
        ui = io.open(UI, encoding="utf-8").read()
        self.assertEqual(ui.count("escC(_fleetSeen(m))"), 3,
                         "the three last-seen sites do not all render the joined phrase")
        self.assertEqual(ui.count("escC(_fleetSince(m.t))"), 0,
                         "a row still prints the console beacon's age under the words 'last "
                         "seen', which is the misreading this version exists to end")
        self.assertIn("var _fleetSeen = function (m) {", ui)
        self.assertIn("j.webOnly", ui,
                      "the rail never reads webOnly, so a browser-only person is fetched and "
                      "thrown away - plumbing with no tap")


    # ---------- what the rail actually DRAWS, by running the shipped helper ----------

    def _seen_phrase(self, row):
        """Run the REAL _fleetSeen out of control_ui.html. Asserting on source would prove the
        code is present; this proves what a person READS. Same idiom as v3385's label law -
        the helper is extracted, never re-implemented. [[copy-drift]]"""
        ui = io.open(UI, encoding="utf-8").read()
        start = "  var _fleetSince = function (iso) {"
        end = "  /* v2843 - WHICH SIDE, AND HOW OLD.".replace("-", "\u2014")
        i, j = ui.find(start), ui.find(end)
        self.assertGreaterEqual(i, 0, "_fleetSince is gone from control_ui.html")
        self.assertGreater(j, i, "the region holding both presence helpers cannot be bounded - "
                                 "a fixed-size window here would measure a guess")
        prog = ("%s\nprocess.stdout.write(String(_fleetSeen(%s)));"
                % (ui[i:j], json.dumps(row)))
        fh = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        fh.write(prog)
        fh.close()
        try:
            r = subprocess.run([NODE, fh.name], capture_output=True, text=True, timeout=30)
            self.assertEqual(r.returncode, 0,
                             "the presence phrase helper would not run: %s" % (r.stderr or "")[:300])
            return r.stdout
        finally:
            try:
                os.unlink(fh.name)
            except Exception:
                pass

    def test_the_rail_says_both_ages_and_which_door(self):
        """The sentence that would have stopped me telling him Dean had been gone a day."""
        out = self._seen_phrase({"t": DEAN_BEACON, "webAt": DEAN_VISIT})
        self.assertIn("on the site", out, "the rail still never mentions the browser door: %r" % out)
        self.assertIn("console", out, "the console age vanished instead of being labelled: %r" % out)
        self.assertLess(out.index("on the site"), out.index("console"),
                        "the OLDER door is named first, which buries the answer to 'is he "
                        "around': %r" % out)

    def test_when_the_console_is_the_fresher_door_it_leads(self):
        """BASELINE. Without it, a helper that always printed the browser first would pass above."""
        out = self._seen_phrase({"t": "2026-09-20T10:00:00.000Z", "webAt": DEAN_VISIT})
        self.assertLess(out.index("console"), out.index("on the site"),
                        "the fresher door is not named first: %r" % out)

    def test_a_row_with_one_door_claims_only_that_door(self):
        out = self._seen_phrase({"t": DEAN_BEACON, "webAt": None})
        self.assertIn("console", out)
        self.assertNotIn("on the site", out,
                         "a machine with no browser half was given one on screen: %r" % out)

    def test_a_row_with_no_door_at_all_says_so(self):
        """Not 'never' alone - the reader must know WHICH question came back empty.
        [[zero-needs-a-denominator]]"""
        out = self._seen_phrase({"t": None, "webAt": None})
        self.assertIn("either door", out, "an absent presence does not say what was asked: %r" % out)


RED_PROOF = [
    {
        "why": "the browser visit reaching the row IS the join; without it the rail is back to "
               "reporting console beacons alone and the reported case must go red",
        "file": "functions/api/console.js",
        "find": "    row.webAt = hit ? hit.t : null;",
        "replace": "    row.webAt = null;",
        "matches": 1,
    },
    {
        "why": "skipping the anonymous slug is what stops a machine reporting no user from "
               "inheriting every unattributable visit on the site",
        "file": "functions/api/console.js",
        "find": "      if (s === '_anon') continue;             // an empty field matches the anonymous bucket",
        "replace": "      if (false) continue;",
        "matches": 1,
    },
    {
        "why": "an unmatched visitor must be LISTED; dropping webOnly puts a real person back "
               "into the blind spot this version closes",
        "file": "functions/api/console.js",
        "find": "    webOnly,\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "without the write floor a reload loop bills one KV write per reload",
        "file": "functions/_middleware.js",
        "find": "    if (age === age && age >= 0 && age < WEBSEEN_FLOOR_MS) return;",
        "replace": "    if (false) return;",
        "matches": 1,
    },
    {
        "why": "the floor must not swallow a genuinely newer visit, or the key freezes at its "
               "first value and the join reads permanently stale",
        "file": "functions/_middleware.js",
        "find": "    if (age === age && age >= 0 && age < WEBSEEN_FLOOR_MS) return;",
        "replace": "    if (age === age) return;",
        "matches": 1,
    },
    {
        "why": "reverting one rail site to the console-only age restores the exact sentence that "
               "made me tell him Dean had been gone a day",
        "file": "tv/control_ui.html",
        "find": "                   + ' \\u00b7 last seen ' + escC(_fleetSeen(m));",
        "replace": "                   + ' \\u00b7 last seen ' + escC(_fleetSince(m.t));",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
