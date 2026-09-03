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
    // ══ v2257 — THE FOURTH, FIFTH AND SIXTH JOINT OF THE SAME DEFECT, and I made all three ══
    //
    // v2254 added `diskVer`, v2255 `relaunch`, v2256 `pull` — each posted faithfully by the
    // console, each dropped HERE, because `rec` is a fixed key list and none of them was on it.
    // Three versions of work that could not reach his screen no matter how correct the console
    // was, and the comment on `tally` directly below already describes this exact failure:
    // "built on both ends, never joined, and silent by construction."
    //
    // ⚠ THE TELL WAS ON HIS OWN ROW. His console reported `run v2256` — a build that sends all
    // three — beside `disk (none)` and `pull —`. A machine cannot be running code that emits a
    // field and be silent about it; that contradiction was the whole finding.
    // [[plumbing-with-no-tap]] [[the-unjoined-end]]
    //
    // Shaped here rather than trusted, the same standard the tally uses: strings are clamped,
    // booleans are booleans, and anything unrecognised becomes null so "we could not tell" can
    // never read as an answer.
    diskVer: String(body.diskVer || '').slice(0, 12) || null,
    relaunch: (function (r) {
      if (!r || typeof r !== 'object') return null;
      const tri = (v) => (v === true ? true : v === false ? false : null);
      return { armed: tri(r.armed), may: tri(r.may),
               why: String(r.why == null ? '' : r.why).slice(0, 160) };
    })(body.relaunch),
    pull: (function (p) {
      if (!p || typeof p !== 'object') return null;
      const behind = Number(p.behind);
      return { can: (p.can === true ? true : p.can === false ? false : null),
               behind: Number.isFinite(behind) && behind >= 0 ? Math.min(behind, 100000) : null,
               why: String(p.why == null ? '' : p.why).slice(0, 160) };
    })(body.pull),
    // v2163 — WHAT THIS MACHINE HAS, so the fleet roster can show each person's progress on
    // hover of their name. Konyo asked for his cousin's and his wife's live chronicle numbers.
    //
    // ⚠ THE CLIENT SHIPPED THIS FIELD IN v2157 AND NOTHING HERE STORED IT. A cross-family review
    // found it: the beacon posted `tally`, this worker built `rec` from a fixed key list, and the
    // field was dropped on arrival — so the tooltip could never have had data no matter how well
    // the console computed it. Built on both ends, never joined, and silent by construction.
    // [[plumbing-with-no-tap]]
    //
    // COUNTS ONLY, and shaped here rather than trusted: numbers are clamped and anything that is
    // not a number becomes null. No item names ever cross this boundary — a roster says how many,
    // never which. The client already omits the field entirely when its board was unreadable, so
    // absent means "not reported", never zero.
    tally: (function (t) {
      if (!t || typeof t !== 'object') return null;
      const pair = (p) => {
        if (!p || typeof p !== 'object') return null;
        const have = Number(p.have);
        const total = Number(p.total);
        if (!Number.isFinite(have) || have < 0) return null;
        return { have: Math.min(have, 100000),
                 total: (Number.isFinite(total) && total > 0) ? Math.min(total, 100000) : null };
      };
      const at = Number(t.at);
      // ⚠ v2168 — CARRY `ok`. The tooltip reads `if (!t || !t.ok)` and renders "no counts
      // reported yet", so a record stored WITHOUT that field failed the test and the feature
      // stayed invisible even though the numbers had arrived intact. Third joint of the same
      // feature to be built on both ends and not joined; found by a review lens.
      // ⚠ v2188 — AND CARRY THE REFUSAL. `ok: true` was hardcoded and a tally with no pairs
      // returned null, so a machine that CANNOT count was indistinguishable from one that never
      // reported — and the tooltip is built to render `t.why`. That is the FOURTH joint of this
      // one feature built on both ends and not joined (this comment said "third"). A refusal
      // carries no item data: a short reason string and nulls. [[the-unjoined-end]]
      const out = { ok: t.ok === true,
                    sets: pair(t.sets), uniques: pair(t.uniques), runewords: pair(t.runewords),
                    at: Number.isFinite(at) ? at : null };
      if (!out.ok) {
        const why = (typeof t.why === 'string') ? t.why.replace(/\s+/g, ' ').trim() : '';
        return why ? { ok: false, why: why.slice(0, 160), at: out.at } : null;
      }
      return (out.sets || out.uniques || out.runewords) ? out : null;
    })(body.tally),
    // v2213 — WHICH set pieces each machine holds, as BITS over a roster both machines already
    // have. Konyo asked THE FLEET to cross-reference him against his cousin — "show me what he has
    // that i dont" — and counts cannot answer that: 116 does not subtract from 120 to produce
    // names.
    //
    // ⚠ THE BOUNDARY THIS FILE DECLARES IS KEPT. Four lines above, `tally` says "No item names
    // ever cross this boundary — a roster says how many, never which." A mask honours that: this
    // worker stores an OPAQUE base64url string, never decodes it, and cannot name a single item
    // from it. The roster that gives the bits meaning lives on his machines, and the subtraction
    // happens there.
    //
    // Shape is validated, never trusted: a fingerprint, a length, and a body whose size must match
    // that length. Anything else is dropped whole rather than stored half-understood — a mask
    // decoded against the wrong roster names real items that are simply the wrong ones, and that
    // failure is silent.
    // 167 — is this machine's capture eye live. Boolean + age only; no paths, no reel ids.
    // Absent means the client did not report it. live:false is measured-dark, not missing.
    eye: (function (e) {
      if (!e || typeof e !== 'object') return null;
      const age = Number(e.ageMs);
      return {
        live: e.live === true,
        ageMs: (Number.isFinite(age) && age >= 0) ? Math.min(age, 86400000) : null,
      };
    })(body.eye),
    masks: (function (m) {
      if (!m || typeof m !== 'object') return null;
      const one = (x) => {
        if (!x || typeof x !== 'object') return null;
        const v = String(x.v || '').slice(0, 32);
        const n = Number(x.n);
        const b = String(x.b || '');
        if (!v || !Number.isInteger(n) || n <= 0 || n > 4096) return null;
        if (!b || b.length > 4096 || !/^[A-Za-z0-9_-]+$/.test(b)) return null;
        // base64url of ceil(n/8) bytes, unpadded — a body that does not match its own declared
        // length is a partial read, and a partial read of a bitmask is a wrong answer
        if (b.length > Math.ceil((Math.ceil(n / 8) + 2) / 3) * 4) return null;
        const out = { v: v, n: n, b: b };
        const have = Number(x.have);
        if (Number.isInteger(have) && have >= 0 && have <= n) out.have = have;
        return out;
      };
      /* ⚠⚠ v2460 — THIS STORED ONLY `sets`, AND THAT IS THE OTHER HALF OF REG-357.
         Grok measured that no machine on the fleet has ever published a uniques mask and I
         confirmed it from the live record. Both of us were looking at the board. THIS LINE would
         have thrown a uniques mask away on arrival even if a board had published one — the
         validator above is already ledger-agnostic and the caller (`_masks_for_wire`) has said
         "every ledger this machine can build, not a hardcoded one" since v2329. One end was
         generalised and the other was left naming a single ledger, so the uniques cross-reference
         could never have worked end to end no matter what the boards did.
         The allow-list stays an allow-list — a client cannot invent ledgers — it is just no
         longer one entry long. [[the-unjoined-end]] [[copy-drift]] */
      const LEDGERS = ['sets', 'uniques'];
      const out = {};
      for (const k of LEDGERS) {
        const v = one(m[k]);
        if (v) out[k] = v;
      }
      return Object.keys(out).length ? out : null;
    })(body.masks),
    /* N-3 (Grok) — WHICH LINK GAVE UP, for a ledger that was omitted. He built the producer in
       control_app and nothing here stored it, so it vanished on arrival and every surface
       downstream stayed silent however correct the console was. The reachability gate refused the
       push for exactly this, which is the gate doing its job on a joint built at one end.
       Values are short strings the console writes about ITSELF — never an item name. */
    maskWhy: (function (w) {
      if (!w || typeof w !== 'object') return null;
      const out = {};
      for (const k of ['sets', 'uniques']) {
        const v = w[k];
        if (typeof v === 'string' && v) out[k] = v.slice(0, 160);
      }
      return Object.keys(out).length ? out : null;
    })(body.maskWhy),
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
  const skipped = [];

  /* ══ v2283 — THE ROSTER WAS DYING EVERY DAY AT A DIFFERENT HOUR ═══════════════════════════════
     Konyo: "i dont see anyone online in fleet. and all three consoles are definitely live right
     now. it say slast seen 2h".

     They were all live. This function was returning HTTP 500 (Cloudflare 1101 — the Worker
     throwing) on every POST while GET answered 200, so all three machines froze at the same
     instant and the panel called them offline.

     ROOT CAUSE, MEASURED, NOT GUESSED. Each heartbeat did TWO kv.put calls, every ~4 minutes, per
     machine: 3 x 15/hr x 2 = ~2,160 writes/day against Cloudflare KV's free-tier ceiling of 1,000
     writes/day. Once spent, kv.put throws and the whole request 500s. Reads are on a far larger
     limit, which is exactly why GET kept working.
     PROVEN by a falsifiable prediction: a POST at 2026-08-29T23:58:52Z returned 500 and the same
     POST at 00:01:29Z — ninety seconds after the UTC quota reset — returned 200.

     TWO CHANGES, and the second matters more than the first:
     1. WRITE LESS. Presence is refreshed at most every REFRESH_S, with the TTL widened to cover
        two missed refreshes, and the durable last-seen is rewritten only when something about the
        machine ACTUALLY CHANGED. A heartbeat that says exactly what the last one said is not news
        and does not need to be spent on. Worst case now ~540 writes/day for three machines.
     2. FAIL HONESTLY. A quota refusal is no longer allowed to become a 500. It answers ok:false
        with a reason the console can render, because "the roster would not take my beacon" and
        "that machine is gone" are opposite facts and the panel had been printing the second one
        for the first. [[unknown-stays-unknown]] */
  /* ⚠ THESE TWO NUMBERS ARE A BUDGET, NOT A TASTE. My first cut used 480s and the guard that
     computes the worst case rejected it: 3 machines x (3600/480) x 24 x 2 keys = 1,080 writes/day,
     still over the 1,000/day ceiling. The optimistic figure (lastseen only on change) is about
     half that — but a budget must be sized on the worst case, or it fails on the one day
     everything changes at once. At 900s with room for a FOURTH machine:
       4 x (3600/900) x 24 x 2 = 768 writes/day, comfortably under 1,000.
     Presence is then accurate to within 15 minutes, which is the right trade: a fleet panel that
     is coarse beats a roster that dies at a different hour every day. */
  const REFRESH_S = 900;          // rewrite presence at most every 15 minutes
  const PRESENCE_TTL = 2400;      // ...and let it live 40, so two missed refreshes do not evict

  let prevRaw = null;
  try { prevRaw = await kv.get('console:' + machine); } catch (e) { prevRaw = null; }
  let prev = null;
  try { prev = prevRaw ? JSON.parse(prevRaw) : null; } catch (e) { prev = null; }

  const ageS = (prev && prev.t) ? ((Date.now() - Date.parse(prev.t)) / 1000) : 1e9;
  // ⚠ MATERIAL means "a thing he reads on the panel". Two heartbeats that differ only in their
  // timestamp are the same news, and news is what a write is for.
  const material = !prev
    || prev.ver !== rec.ver || prev.mode !== rec.mode || prev.event !== rec.event
    || prev.diskVer !== rec.diskVer
    || JSON.stringify(prev.tally || null) !== JSON.stringify(rec.tally || null)
    || JSON.stringify(prev.masks || null) !== JSON.stringify(rec.masks || null)
    || JSON.stringify(prev.pull || null) !== JSON.stringify(rec.pull || null)
    || !!(prev.eye && prev.eye.live) !== !!(rec.eye && rec.eye.live);

  try {
    if (material || ageS >= REFRESH_S) {
      await kv.put('console:' + machine, JSON.stringify(rec), { expirationTtl: PRESENCE_TTL });
      stored.push('console');
    } else {
      skipped.push('console (unchanged, refreshed ' + Math.round(ageS) + 's ago)');
    }

    // durable last-seen: only when something changed. Presence answers "is it here now"; this
    // answers "what was it last time", and an identical rewrite answers neither question anew.
    if (material) {
      await kv.put('lastseen:' + machine, JSON.stringify(rec), {
        expirationTtl: 60 * 60 * 24 * 400,  // 400 days
      });
      stored.push('lastseen');
    } else {
      skipped.push('lastseen (nothing changed)');
    }
  } catch (e) {
    /* ⚠ THE WHOLE POINT. A storage refusal must reach him as a REFUSAL, not as a machine that
       vanished. 200 with ok:false so the console can parse it and say UNKNOWN; a 500 here is what
       made three live machines read as offline for two hours. */
    return json({
      ok: false, machine,
      why: 'the roster could not store this beacon — ' + String((e && e.message) || e).slice(0, 140),
      hint: 'this is the storage refusing a write, NOT the machine being absent',
      stored, skipped,
    }, 200);
  }

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
