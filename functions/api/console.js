/**
 * /api/console — console-app presence beacon (v875, fleet-scan rebuilt v1596).
 *
 * SCOPE — read this before believing what this surface says. It tracks the TV DIABLO
 * console APP checking in from a machine. It does NOT track browser page-views of
 * /d2r/ — those are a separate tracker at /visits (functions/visits.js, fed by
 * recordVisit() in functions/_middleware.js). A machine that only ever opened the
 * bible in a browser will NEVER appear here, by design, and that is not a bug.
 *
 * The control app (Mac + Windows + cousins) POSTs here on boot, on ON AIR / OFF
 * transitions, and every ~4 min as a heartbeat. Storage reuses the TZ_HISTORY KV:
 *   console:<machine>         — CURRENT state, TTL 10 min → key alive ⇔ console online
 *   consolelog:<ts>:<machine> — event log entries (boot/onair/off only, no heartbeats), TTL 30d
 *   lastseen:<machine>        — DURABLE last check-in, TTL 400d, written on EVERY beacon
 *                               INCLUDING heartbeats. One key per machine, so it can never
 *                               fall out of a scan window the way a growing event log can.
 *                               'lastseen:' collides with no other prefix in use here
 *                               ('console:', 'consolelog:', 'visit:').
 *
 * WHY lastseen: EXISTS (the bug it retires) — the offline list used to be reconstructed
 * from `kv.list({ prefix: 'consolelog:', limit: 400 })`. Cloudflare KV returns keys "in
 * lexicographically sorted order according to their UTF-8 bytes" (developers.cloudflare.com
 * /kv/api/list-keys/, verified 2026-08-02), the keys are 'consolelog:<ISO-ts>:<machine>',
 * so ascending == OLDEST FIRST. limit:400 therefore returned the OLDEST 400 events in the
 * 30-day window and never the newest: once the log passed 400 entries every RECENT machine
 * fell outside it and went invisible. Konyo's exact symptom — his cousin ran the console
 * yesterday and did not appear, live GET answered online=[konyo-3], offline=[].
 * Fixed by paginating the FULL cursor (correct under ascending AND descending ordering,
 * which is the point) and by making lastseen: the primary source.
 *
 * REFUTED, DO NOT RE-OPEN — there is no 'console:' / 'consolelog:' prefix collision.
 * `'consolelog:2026-08-01T00:00:00Z:x'.startsWith('console:')` is FALSE (byte 8 is ':'
 * in one and 'l' in the other), so the presence list() below cannot match event-log keys.
 * Investigated and executed 2026-08-02; pinned by a test in tv/test_console_fleet.py.
 * No defensive filter is added for it on purpose: dead code that can never fire reads to
 * the next maintainer as evidence the bug was real.
 *
 * Auth: sits behind the site-wide Basic gate (_middleware) like every /api route.
 * View at /console?k=<VISITS_KEY> — Konyo-only, same key as /visits.
 */

/**
 * List EVERY key under a prefix by following the cursor. KV caps a single list() at 1000
 * keys and signals more via list_complete/cursor; an empty keys array does NOT mean done
 * (expired keys are iterated but not returned), so the loop trusts list_complete only.
 *
 * KEEP THIS BLOCK BYTE-IDENTICAL to the copy in functions/console.js — the two files
 * already shared the oldest-first bug once because they were copy-pasted, and the way to
 * stop that recurring is for the shared part to be obviously, diffably the same.
 */
async function listAll(kv, prefix) {
  const keys = []; let cursor;
  for (let i = 0; i < 50; i++) {                    // hard cap 50 pages x 1000 = 50k keys
    const page = await kv.list({ prefix, limit: 1000, cursor });
    keys.push(...page.keys);
    if (page.list_complete || !page.cursor) break;
    cursor = page.cursor;
  }
  return keys;
}

const PAGE_CAP = 50, PAGE_SIZE = 1000;              // must match listAll's loop bound / limit

/**
 * v1597.1 — READ THE KEY, NOT THE VALUE. This is a HARD Cloudflare limit, not a nicety.
 *
 * Fixing the oldest-400 window meant listing every `consolelog:` key — 2,556 of them on the real
 * store — and the first fix then did one kv.get() per key to learn which machine each event was
 * from. That is 2,556 subrequests in one invocation, and Workers cap subrequests per invocation:
 * `/console` began returning HTTP 500 with "Too many API requests by single Worker invocation"
 * (captured from `wrangler pages deployment tail`, not guessed). The bug fix had a bug.
 *
 * The reads were never necessary. The key IS the record for this purpose:
 *     consolelog:<ISO-timestamp>:<machine>
 * so machine and time parse straight out of the name, at a cost of zero subrequests. Only the
 * machines actually SHOWN need their detail row fetched, and there are a handful of those.
 *
 * Split on the LAST ':' rather than a fixed index — an ISO timestamp contains colons, so
 * `parts[1]` is the hour, not the machine.
 *
 * KEEP BYTE-IDENTICAL with the copy in functions/console.js.
 */
function machinesFromLogKeys(keys) {
  const newest = new Map();                          // machine -> ISO timestamp of its latest event
  for (const k of keys) {
    const name = (k && k.name) || '';
    if (!name.startsWith('consolelog:')) continue;
    const rest = name.slice('consolelog:'.length);
    const cut = rest.lastIndexOf(':');
    if (cut <= 0) continue;
    const t = rest.slice(0, cut);
    const machine = rest.slice(cut + 1);
    if (!machine) continue;
    const prev = newest.get(machine);
    if (!prev || prev.t < t) newest.set(machine, { machine, t, key: name });
  }
  return [...newest.values()];
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return json({ ok: false, error: 'storage unavailable' }, 500);

  let body = {};
  try { body = await request.json(); } catch (e) { body = {}; }
  const machine = String(body.machine || 'unknown').slice(0, 40).replace(/[^\w.-]/g, '_');
  const event = String(body.event || 'hb').slice(0, 12);

  const cf = request.cf || {};
  const rec = {
    t: new Date().toISOString(),
    machine,
    platform: String(body.platform || '').slice(0, 12),
    ver: String(body.ver || '').slice(0, 12),
    mode: String(body.mode || '').slice(0, 12),
    event,
    user: String(body.user || '').slice(0, 24),
    // v1496 — the FRIENDLY name Konyo gave this machine in its console ("Konyo's MacBook").
    // The hostname stays as the technical fallback; a nickname is what he actually reads.
    nickname: String(body.nickname || '').slice(0, 40),
    install: String(body.install || '').slice(0, 12),
    reads: Number(body.reads || 0) || 0,
    ip: request.headers.get('CF-Connecting-IP') || '',
    country: cf.country || '',
    city: cf.city || '',
  };

  // v1596 — beacon HONESTY. The client's beacon is fire-and-forget behind a bare
  // `except Exception: pass`, so a machine whose beacon has failed every time for months
  // looks IDENTICAL to a machine nobody ever turned on. The app now reports the PREVIOUS
  // attempt's outcome here; we store it so Konyo can SEE "this machine tried and failed"
  // instead of inferring silence. Absent is normal — older builds do not send it.
  const lastBeacon = coerceLastBeacon(body.lastBeacon);
  if (lastBeacon) rec.lastBeacon = lastBeacon;

  const stored = [];
  // presence: alive key = online console (TTL 10 min ≈ 2 missed heartbeats)
  await kv.put('console:' + machine, JSON.stringify(rec), { expirationTtl: 600 });
  stored.push('console');

  // durable last-seen: EVERY beacon, heartbeats included. This is what makes "when was this
  // machine last here" answerable directly instead of being reconstructed from an event log
  // that was never designed for the question.
  await kv.put('lastseen:' + machine, JSON.stringify(rec), {
    expirationTtl: 60 * 60 * 24 * 400,  // 400 days
  });
  stored.push('lastseen');

  // event log: boots and mode flips only — heartbeats would bloat the KV
  if (event !== 'hb') {
    await kv.put('consolelog:' + rec.t + ':' + machine, JSON.stringify(rec), {
      expirationTtl: 60 * 60 * 24 * 30,   // 30 days of history
    });
    stored.push('consolelog');
  }

  // Echo enough for the client to record a VERIFIED success rather than merely "no exception
  // was thrown". Never the IP, never a secret — the caller already knows its own machine name.
  let fleet = null;
  try { fleet = (await listAll(kv, 'console:')).length; } catch (e) { fleet = null; }
  return json({ ok: true, machine, recorded: rec.t, stored, fleet });
}

/**
 * v1496 — GET /api/console → the fleet as JSON: who is online now and when each machine was last
 * seen. Konyo: "i want to have a tracker for whose logged in and when.. like we have for the
 * website." /console (the HTML page) already answered that in a browser tab behind a key; this
 * lets the console app itself answer it, so the machine he is sitting at can show its own fleet.
 * Same Basic gate as every other /api route (the app already authenticates for the beacon), and
 * strictly read-only.
 *
 * Shape: { ok, now, scope, online[], offline[] (each offline:true), scan{} }.
 */
export async function onRequestGet(context) {
  const { env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return json({ ok: false, error: 'storage unavailable' }, 500);

  // v1496 — CI runners used to check in from every test job, so the fleet listed a GitHub VM in
  // Boydton beside Konyo's MacBook. The beacon no longer sends from CI, but entries already in KV
  // (and any older build still running) are filtered here too — belt and braces, because the answer
  // to "who is online" must only ever contain machines that are his. Applied to presence, lastseen
  // and consolelog alike.
  const isRunner = (m) => /^runnervm|^fv-az|^runner-/i.test(String((m && m.machine) || ''));
  const readAll = async (keys) => (await Promise.all(
    keys.map((k) => Promise.resolve(kv.get(k.name, 'json')).catch(() => null)),
  )).filter(Boolean).filter((m) => m && m.machine).filter((m) => !isRunner(m)).sort(newestFirst);

  // presence — 'console:' cannot match a 'consolelog:' key (see REFUTED note in the header).
  const presenceKeys = await listAll(kv, 'console:');
  const machines = await readAll(presenceKeys);

  // `seen` is seeded from ONLINE: an online machine's own history is deliberately suppressed,
  // because it is already reported above with a live record. Dedupe is strict string equality
  // on l.machine — never a prefix or normalised name, or one machine would eat another's row.
  const seen = new Set(machines.map((m) => m.machine));
  const offline = [];
  const take = (list) => {
    for (const l of list) {
      if (seen.has(l.machine)) continue;
      seen.add(l.machine);
      offline.push({ ...l, offline: true });
    }
  };

  // PRIMARY offline source: the durable last-seen keys. One key per machine, 400-day TTL —
  // there is no window for a recent machine to fall out of.
  const lastseenKeys = await listAll(kv, 'lastseen:');
  take(await readAll(lastseenKeys));

  // SECONDARY backfill: the event log, for machines that last beaconed BEFORE lastseen: shipped
  // and therefore have no durable key yet. Full cursor pagination — the old limit:400 here read
  // the OLDEST 400 events and is what made recent machines invisible.
  //
  // v1597.1 — machine + time come from the KEY NAME (see machinesFromLogKeys). Reading all 2,556
  // values blew the per-invocation subrequest cap and 500'd the page. Only the newest event of
  // each machine we are actually going to SHOW gets fetched, which is a handful of reads.
  const logKeys = await listAll(kv, 'consolelog:');
  const logMachines = machinesFromLogKeys(logKeys)
    .filter((m) => !seen.has(m.machine))
    .filter((m) => !isRunner(m))
    .sort(newestFirst)
    .slice(0, 40);                                   // a bounded, stated cap — not a silent one
  const logDetail = (await Promise.all(logMachines.map((m) =>
    Promise.resolve(kv.get(m.key, 'json')).catch(() => null))))
    .map((rec, i) => (rec && rec.machine ? rec : logMachines[i]));   // fall back to key-derived
  take(logDetail.filter(Boolean).filter((m) => !isRunner(m)));

  offline.sort(newestFirst);

  // v1596 — SCAN DIAGNOSTICS. offline:[] used to be unreadable: it could mean "nobody has been
  // here" or "the scan is broken", and those look the same. These counts separate them.
  // pages/complete are derived from key counts because listAll is kept byte-identical across
  // the two console files; complete goes false if the 50-page hard cap could have truncated.
  const pagesFor = (n) => Math.max(1, Math.ceil(n / PAGE_SIZE));
  const scan = {
    logKeys: logKeys.length,
    lastseenKeys: lastseenKeys.length,
    presenceKeys: presenceKeys.length,
    pages: pagesFor(presenceKeys.length) + pagesFor(lastseenKeys.length) + pagesFor(logKeys.length),
    complete: presenceKeys.length < PAGE_CAP * PAGE_SIZE
      && lastseenKeys.length < PAGE_CAP * PAGE_SIZE
      && logKeys.length < PAGE_CAP * PAGE_SIZE,
  };

  return json({
    ok: true,
    now: new Date().toISOString(),
    scope: 'TV-D console APP presence only (beacons from the control app). NOT browser page-views of /d2r/ — those are a separate tracker at /visits.',
    online: machines,
    offline,
    scan,
  });
}

function newestFirst(a, b) {
  return String((a && a.t) || '') < String((b && b.t) || '') ? 1 : -1;
}

/**
 * Defensive coercion of the client-reported PREVIOUS beacon result. Anything unexpected is
 * dropped rather than thrown on — a malformed health report must never cost us the beacon.
 */
function coerceLastBeacon(v) {
  try {
    if (!v || typeof v !== 'object' || Array.isArray(v)) return null;
    const out = {};
    if (v.ok !== undefined && v.ok !== null) out.ok = !!v.ok;
    if (v.code !== undefined && v.code !== null && Number.isFinite(Number(v.code))) out.code = Number(v.code);
    if (v.err !== undefined && v.err !== null) out.err = String(v.err).slice(0, 120);
    if (v.t !== undefined && v.t !== null) out.t = String(v.t).slice(0, 40);
    return Object.keys(out).length ? out : null;
  } catch (e) { return null; }
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}
