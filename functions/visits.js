/**
 * /visits — Konyo's private analytics dashboard for the D2R Bible.
 *
 * Reads every `visit:` entry from the TZ_HISTORY KV store (written by _middleware's recordVisit)
 * and renders who is using the site, how often, from where, and on what.
 *
 * ACCESS: requires ?k=<VISITS_KEY> matching the VISITS_KEY Pages secret. Cousins share the SITE
 * password (so the site-wide gate lets them in) but not this key, so the log stays Konyo-only. If
 * VISITS_KEY isn't set the page 404s rather than opening — and a WRONG key 404s identically, so
 * probing cannot distinguish "no key configured" from "wrong key".
 *
 * v1596 — WAS A FLAT TABLE, IS NOW A DASHBOARD. Konyo asked for "a tracker ... like a website style
 * one, only for me as an admin style", not knowing this endpoint already existed and had been
 * logging since 2026-06-22. A reverse-chronological list of every hit answers "what happened last"
 * and none of the questions he actually has: how many people use this, who are they, are they
 * coming back. So the raw rows stay at the bottom — they are the evidence — and above them sit:
 *
 *   HOW MANY      visits, people, today, last 7 days
 *   WHEN          a 30-day bar chart — the SHAPE of usage, which no single number carries
 *   WHO           one row per person, newest first, with return counts
 *   WHAT HAPPENED the raw log, unchanged
 *
 * A PERSON is the login name when one was typed, otherwise the IP. That is a real limitation and it
 * is printed on the page rather than hidden behind a confident "unique visitors" figure that would
 * be quietly wrong: one cousin on a phone and a laptop counts twice, and several people behind one
 * router with no login name collapse into one.
 *
 * ── SCOPE (2026-08-02, REWRITTEN v1687 — the old text below it was true and is no longer) ───────
 * This page carries TWO kinds of record, measured in DIFFERENT UNITS and never added together:
 *   PAGE-VIEWS      browser loads of /d2r/, from `visit:` keys written by recordVisit()
 *                   in _middleware.js. Every count, card and chart on the page is these.
 *   CONSOLE MACHINES machines running the TV DIABLO app, from `console:` (10-min presence) and
 *                   `lastseen:` (durable) keys written by /api/console, beaconed by
 *                   tv/control_app.py. Its own section, its own units, in NO total above it.
 *
 * ── NAMED VISITORS (v1694) — joining the two half-trackers ─────────────────────────────────────
 * Before v1694, `visit:` rows can see every browser page-view but cannot name who (the "Who"
 * table below falls back to IP, so one cousin on two devices counts twice and several people
 * behind one router collapse into one), while the console's `lastseen:` scheme HAS real identity
 * but never sees a browser. bible.html now beacons its own stable identity to POST /api/hello
 * once per page-load (see that file for the exact contract), which writes it under a THIRD
 * prefix so neither existing scheme is touched:
 *   `hvisitor:<id>`      — DURABLE, ONE KEY PER PERSON (like `lastseen:`), read-modify-written on
 *                          every beacon: { id, name, code, machine, ver, first_seen, last_seen,
 *                          count, country, city }. `count`/`first_seen`/`last_seen` are already
 *                          authoritative totals — this file does not recompute them.
 *   `hhit:<ISO-ts>:<rand>:<id>`
 *                        — per-hit log, TTL 30 days — the ONLY source for day-by-day shape
 *                          (7d/30d/sparkline), because the durable record above is a single
 *                          overwritten row and cannot carry history by itself. Read from the KEY
 *                          NAME ALONE: the name already encodes both fields the value holds, so
 *                          this file never fetches the value and spends ONE subrequest for the
 *                          whole log instead of one per page-load ever recorded.
 * If nothing has beaconed yet (old cached build, JS blocked, or /api/hello unreachable), both
 * lists come back empty and this section says so honestly — it does not fall back to guessing
 * identity from IP, and it does not hide itself. The two prefixes are read in SEPARATE try/catch
 * blocks and a failed read is printed as UNKNOWN, never as an empty population.
 *
 * ⚠ THIS SECTION RENDERS OUTSIDE THE `visit:` GATE, DELIBERATELY. `visit:` rows expire after 90
 * days (_middleware.js) while `hvisitor:` lives 400 (hello.js), so an empty page-view store is a
 * perfectly ordinary state in which named identities still exist. Nesting the named table inside
 * `visits.length ? …` would have hidden the new population behind the old one's count — the exact
 * coupling this ship exists to break, inverted. Keep it ungated.
 *
 * ⚠ NO TRUE "ONLINE NOW" SIGNAL EXISTS FOR THIS SCHEME. Unlike `console:<machine>` (a short-TTL
 * presence key refreshed by a running app's heartbeat), the browser beacon fires ONCE per
 * page-load and then falls silent — there is no heartbeat to hold a presence key alive, so
 * claiming "online now" here would be a guess dressed as a fact. This file shows relative
 * "last seen" instead and says why, rather than inventing a second presence mechanism.
 *
 * ⚠ TWO POPULATIONS, NEVER ONE NUMBER. The named-visitor table below and the IP-inferred "Who"
 * table measure DIFFERENT SETS of people: anyone on a stale cached build, or with JS blocked, or
 * who never typed a name/code into the beacon (no identity ⇒ /api/hello silently skips the
 * write), still lands in the IP-inferred numbers and never in the named table. Neither table is
 * corrected by the other, both stay on the page, and the gap between their totals is printed
 * rather than reconciled into a single "visitors" figure — that single-figure merge is exactly
 * the defect class this project keeps finding.
 *
 * WHY THEY ARE BOTH HERE NOW. The console app never loads /d2r/, so it cannot produce a page-view
 * — true then, true now. Konyo went looking for his cousin's console session on this page twice
 * (2026-08-02 and 2026-08-09), correctly did not find it, and both times concluded the tracker was
 * dead. Both times the answer was a LINK to /console, and v1602 made that link the loudest element
 * on the page. He read past it again. A POINTER IS NOT A TRACKER: a person hunting a machine opens
 * the dashboard, not the signpost. So the machines are ON this page — while the page-view numbers
 * stay exactly what they always measured, because merging them would fix the navigation by
 * corrupting the data. /console remains the deep page: per-event history and beacon health.
 *
 * Two more honesty surfaces added at the same time, both for the same reason (an empty tracker and a
 * healthy-but-quiet tracker used to look identical):
 *   FRESHNESS   — timestamp of the newest page-view, absolute + relative, warning-coloured past 48h.
 *   DATA WINDOW — how far back these numbers can reach (TTL read off the recordVisit() write, not
 *                 guessed), how many records were scanned, and whether that scan was truncated.
 */
export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const provided = url.searchParams.get('k') || '';
  const SECRET = env && env.VISITS_KEY;

  // No key configured, or wrong/missing key → look like the page doesn't exist.
  if (!SECRET || provided !== SECRET) {
    return new Response('Not found', { status: 404, headers: { 'content-type': 'text/plain' } });
  }

  const kv = env && env.TZ_HISTORY;
  if (!kv) return new Response('storage unavailable', { status: 500 });

  // KV list() caps at 1000 keys per call, so follow the cursor. Without this the dashboard would
  // one day silently describe only the newest 1000 visits as though they were all of them — every
  // total on the page would just quietly stop growing.
  //
  // VERIFIED 2026-08-02: this listing is CORRECT and was deliberately left alone. It passes NO
  // `limit:` and it follows the cursor to exhaustion, so it reads EVERY `visit:` key whatever order
  // KV hands them back in. That matters because the sibling console endpoints had the opposite
  // shape — a bare `limit:400` over lexicographically-ordered timestamped keys, which returns the
  // OLDEST 400 and hides everything recent. This loop is the reference pattern they are being fixed
  // to copy; do not "optimise" a limit back into it.
  let keys = [];
  let cursor;
  let truncated = false;                             // ran out of loop budget before KV ran out of keys
  for (let i = 0; i < 20; i++) {
    const page = await kv.list({ prefix: 'visit:', cursor });
    keys = keys.concat(page.keys || []);
    if (page.list_complete || !page.cursor) break;
    cursor = page.cursor;
    if (i === 19) truncated = true;                  // 20 pages × 1000 keys = 20,000 scanned, more remain
  }
  const raw = await Promise.all(keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const visits = raw.filter((v) => v && v.t).sort((a, b) => (a.t < b.t ? 1 : -1)); // newest first

  // ── CONSOLE APP SESSIONS (v1687) ───────────────────────────────────────────────────────────────
  // Konyo, TWICE — 2026-08-02 and 2026-08-09: "my cousin logged in to the console, i dont see it
  // tracked here." Both times the data was on /console, correct and current, and both times the fix
  // was a LINK from this page. v1602 made that link the loudest element under the title and he read
  // past it again, because a person looking for a machine opens the tracker, not the signpost.
  // A POINTER IS NOT A TRACKER. The third fix puts the machines on the page he actually opens.
  //
  // ⚠ AND THEY ARE NEVER FOLDED INTO A PAGE-VIEW COUNT. A beacon is "an app is running"; a
  // page-view is "a browser loaded /d2r/". Adding them would make every number above a claim about
  // something it does not measure — the failure this dashboard has already had once, in the
  // opposite direction. Own section, own units, stated on the page.
  //
  // Reads ONLY `console:` (10-min presence) and `lastseen:` (durable, ONE key per machine, written
  // on every beacon including heartbeats). It deliberately does NOT read `consolelog:`: that
  // prefix carries the lexicographic-ordering trap documented in functions/console.js and pinned by
  // tv/test_console_fleet.py, and a third copy of that helper is exactly how a fix lands in two
  // files out of three. For per-event history and beacon health, /console remains the deep page.
  // ('console:' cannot match a 'consolelog:' key — byte 8 is 'l' where the prefix demands ':'.
  // REFUTED and pinned; see the same note in functions/console.js.)
  const listPrefix = async (prefix) => {
    let out = [];
    let cur;
    for (let i = 0; i < 5; i++) {                    // one key per machine; 5 pages is 5,000 of them
      const page = await kv.list({ prefix, cursor: cur });
      out = out.concat(page.keys || []);
      if (page.list_complete || !page.cursor) break;
      cur = page.cursor;
    }
    return out;
  };
  // CI runners used to beacon from every test job — the same filter /console applies, for the same
  // reason: "who is here" must only ever contain machines that are his.
  const isRunner = (m) => /^runnervm|^fv-az|^runner-/i.test(String((m && m.machine) || ''));
  let machines = [];
  try {
    const [liveKeys, seenKeys] = await Promise.all([listPrefix('console:'), listPrefix('lastseen:')]);
    const onlineNames = new Set(liveKeys.map((k) => k.name.slice('console:'.length)));
    const seenRaw = await Promise.all(seenKeys.map((k) => kv.get(k.name, 'json').catch(() => null)));
    machines = seenRaw
      .filter((m) => m && m.t)
      .filter((m) => !isRunner(m))
      .map((m) => Object.assign({}, m, { online: onlineNames.has(m.machine) }))
      .sort((a, b) => (a.t < b.t ? 1 : -1));         // newest beacon first
  } catch (e) {
    machines = [];                                    // the console block is additive: never let it
  }                                                   // take down the page-view dashboard

  // ── NAMED VISITORS (v1694) — real contract, see functions/api/hello.js ─────────────────────────
  // `hvisitor:` is durable/one-per-person like `lastseen:`, so it reuses `listPrefix` above
  // unmodified (the exact "reuse the idea, don't invent a second one" the brief asked for).
  // `hhit:` is a growing per-hit log (30d TTL), so it gets the same paginated-cursor shape as the
  // `visit:` loop at the top of this function. Additive only: any failure here must never take
  // down the page-view or console sections above.
  // ⚠ TWO INDEPENDENT try/catch BLOCKS, ON PURPOSE — do not merge them back into one. A single
  // catch around both prefixes lets a failed `hhit:` scan zero out the perfectly readable
  // `hvisitor:` records, and the page then prints "No beaconed visitor identity yet" over
  // identities that exist and were readable: a false statement on the one dashboard whose entire
  // job is being honest about what it cannot know. Each prefix now fails alone, and a failure is
  // reported AS a failure rather than rendered as an empty population.
  let namedRecords = [];
  let namedFailed = false;
  try {
    const idKeys = await listPrefix('hvisitor:');
    const idRaw = await Promise.all(idKeys.map((k) => kv.get(k.name, 'json').catch(() => null)));
    // Read defensively — a record missing a field renders that field unknown, never guessed.
    namedRecords = idRaw.filter((v) => v && v.id && v.last_seen);
  } catch (e) {
    namedRecords = [];                                  // additive: never breaks the rest of the page
    namedFailed = true;                                 // but NEVER reported as "nobody has beaconed"
  }

  // The hit log is read from the KEY NAMES ALONE. `hhit:<ISO-ts>:<id>` already encodes both fields
  // (`t`, `id`) that the JSON value carries, so fetching each value would spend one subrequest per
  // page-load ever recorded (30 days × 20 loads/day ≈ 600) against a Pages Functions subrequest
  // ceiling of 50 free / 1000 paid — and because each get was individually .catch(()=>null),
  // tripping that ceiling would have surfaced as SILENTLY SMALLER numbers, not as an error.
  // Listing is paginated and cheap; parsing a key is free. The id charset is fixed by hello.js
  // (`[a-z0-9-]`, ≤40 chars, so it can contain no colon), which is what makes the split safe.
  let hitRecords = [];
  let hitTruncated = false;
  let hitFailed = false;
  let hitUnparsed = 0;
  // v1694 fix: hello.js writes FOUR segments — `hhit:<ISO>:<rand>:<id>` — because a random
  // segment is what stops two loads in the same millisecond from overwriting one another. The
  // first cut of this regex only allowed THREE, so every key the real writer produced was
  // rejected and every day column read 0. The middle group is optional so the 3-segment shape
  // named in this file's header still parses; it can never swallow the id, because `<rand>` is
  // base36 (`[a-z0-9]+`) and must be followed by a colon, and an id can contain no colon at all.
  const HHIT_KEY = /^hhit:(\d{4}-\d{2}-\d{2}T[\d:.]+Z):(?:[a-z0-9]+:)?([a-z0-9-]+)$/;
  try {
    let hitKeys = [];
    let hcursor;
    for (let i = 0; i < 20; i++) {
      const page = await kv.list({ prefix: 'hhit:', cursor: hcursor });
      hitKeys = hitKeys.concat(page.keys || []);
      if (page.list_complete || !page.cursor) break;
      hcursor = page.cursor;
      if (i === 19) hitTruncated = true;
    }
    for (const k of hitKeys) {
      const m = HHIT_KEY.exec(k.name);
      if (!m) { hitUnparsed++; continue; }               // counted and printed, never guessed at
      hitRecords.push({ t: m[1], id: m[2] });
    }
  } catch (e) {
    hitRecords = [];
    hitFailed = true;                                    // day-by-day unknown ≠ day-by-day zero
  }

  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const flag = (cc) => {
    if (!cc || cc.length !== 2) return '';
    const A = 0x1f1e6;
    return String.fromCodePoint(A + cc.toUpperCase().charCodeAt(0) - 65,
                                A + cc.toUpperCase().charCodeAt(1) - 65);
  };
  const device = (ua) => {
    if (!ua) return 'unknown';
    const os = /Windows/.test(ua) ? 'Windows' : /iPhone|iPad|iOS/.test(ua) ? 'iOS'
      : /Mac OS X|Macintosh/.test(ua) ? 'Mac' : /Android/.test(ua) ? 'Android'
      : /Linux/.test(ua) ? 'Linux' : '?';
    const br = /Edg\//.test(ua) ? 'Edge' : /OPR\/|Opera/.test(ua) ? 'Opera'
      : /Chrome\//.test(ua) ? 'Chrome' : /Firefox\//.test(ua) ? 'Firefox'
      : /Safari\//.test(ua) ? 'Safari' : '?';
    return os + ' · ' + br;
  };
  const placeOf = (v) => {
    const loc = [v.city, v.region].filter(Boolean).join(', ');
    return (flag(v.country) + ' ' + (loc || v.country || '?')).trim();
  };
  // WHO: a typed login name wins; the IP is the fallback identity.
  const whoOf = (v) => (v.user && v.user.trim()) || v.ip || 'unknown';

  const day = (iso) => String(iso || '').slice(0, 10);
  const todayUTC = new Date().toISOString().slice(0, 10);

  // ── how far back these numbers can possibly reach ───────────────────────────
  // NOT a guess: read straight off the write in functions/_middleware.js recordVisit() —
  //   kv.put(key, ..., { expirationTtl: 7776000 })
  // If that TTL is ever changed, change this constant with it; nothing here can detect it.
  const VISIT_TTL_S = 7776000;                       // 90 days
  const ttlDays = Math.round(VISIT_TTL_S / 86400);
  const horizon = new Date(Date.now() - VISIT_TTL_S * 1000).toISOString().slice(0, 10);

  // ── freshness: is this tracker quiet, or is it dead? ────────────────────────
  // Without this line an empty tracker and a working tracker with no traffic look identical, which
  // is exactly how "nothing after 2 Aug 01:58" got read as "the tracker is broken".
  const newest = visits.length ? visits[0].t : null;  // visits are already sorted newest-first
  const newestMs = newest ? Date.parse(newest) : NaN;
  const ageMs = isFinite(newestMs) ? Date.now() - newestMs : Infinity;
  const STALE_MS = 48 * 3600e3;
  const rel = (ms) => {
    if (!isFinite(ms)) return 'never';
    if (ms < 0) return 'just now';
    const mins = Math.round(ms / 6e4);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + ' minute' + (mins === 1 ? '' : 's') + ' ago';
    const hrs = Math.round(mins / 60);
    if (hrs < 48) return hrs + ' hour' + (hrs === 1 ? '' : 's') + ' ago';
    const d = Math.round(hrs / 24);
    return d + ' day' + (d === 1 ? '' : 's') + ' ago';
  };
  const stale = ageMs > STALE_MS;
  const consoleHref = '/console?k=' + encodeURIComponent(provided);

  // ── the four headline numbers ───────────────────────────────────────────────
  const people = new Map();
  for (const v of visits) {                        // visits are newest-first
    const k = whoOf(v);
    const p = people.get(k);
    if (!p) {
      people.set(k, { who: k, named: !!(v.user && v.user.trim()), n: 1, last: v.t, first: v.t,
                      place: placeOf(v), dev: device(v.ua), days: new Set([day(v.t)]) });
    } else {
      p.n += 1;
      p.first = v.t;                               // keep walking back to the earliest
      p.days.add(day(v.t));
    }
  }
  const sevenAgo = new Date(Date.now() - 7 * 864e5).toISOString().slice(0, 10);
  const nToday = visits.filter((v) => day(v.t) === todayUTC).length;
  const n7 = visits.filter((v) => day(v.t) >= sevenAgo).length;

  // ── 30-day shape ────────────────────────────────────────────────────────────
  const byDay = new Map();
  for (const v of visits) byDay.set(day(v.t), (byDay.get(day(v.t)) || 0) + 1);
  const days = [];
  for (let i = 29; i >= 0; i--) {
    const d = new Date(Date.now() - i * 864e5).toISOString().slice(0, 10);
    days.push({ d, n: byDay.get(d) || 0 });
  }
  const peak = Math.max(1, ...days.map((x) => x.n));
  const bars = days.map((x) => {
    const h = Math.round((x.n / peak) * 100);
    return `<div class="bar${x.n ? '' : ' zero'}${x.d === todayUTC ? ' today' : ''}" title="${esc(x.d)} — ${x.n} page-view${x.n === 1 ? '' : 's'}"><i style="height:${Math.max(x.n ? 4 : 1, h)}%"></i></div>`;
  }).join('');

  // ── named visitors: join durable identity (hvisitor:) with day-by-day hits (hhit:) ────────────
  const thirtyAgo = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
  const namedVisitors = new Map();
  for (const rec of namedRecords) {
    namedVisitors.set(rec.id, {
      id: rec.id,
      sigil: (rec.code || rec.name || '').trim() || null,   // code preferred, matches hello.js
      count: Number(rec.count) || 0,                        // authoritative total from the durable record
      last: rec.last_seen,
      first: rec.first_seen,
      machine: rec.machine || null,
      place: (flag(rec.country) + ' ' + [rec.city, rec.country].filter(Boolean).join(', ')).trim() || null,
      byDay: new Map(),
      days: new Set(),
    });
  }
  // hhit: only carries 30 days — it can only ever refine the last-30-day shape of a record whose
  // durable totals (count/first_seen/last_seen) already came from hvisitor: above. A hit for an id
  // with no hvisitor: record (theoretically possible if one expired before the other) is dropped
  // rather than fabricating a person around a bare id.
  for (const h of hitRecords) {
    const nv = namedVisitors.get(h.id);
    if (!nv) continue;
    const d = day(h.t);
    nv.days.add(d);
    nv.byDay.set(d, (nv.byDay.get(d) || 0) + 1);
  }
  const nVisits7 = (nv) => [...nv.byDay.entries()].filter(([d]) => d >= sevenAgo)
    .reduce((s, [, n]) => s + n, 0);
  const nVisits30 = (nv) => [...nv.byDay.entries()].filter(([d]) => d >= thirtyAgo)
    .reduce((s, [, n]) => s + n, 0);
  const sparkline = (nv) => {
    const cells = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date(Date.now() - i * 864e5).toISOString().slice(0, 10);
      cells.push(nv.byDay.get(d) || 0);
    }
    const peakN = Math.max(1, ...cells);
    // v1694 fix — EXPLICIT PIXEL heights, never percentages. The bars used to live directly in the
    // `<td class="spark">` and carry `height:<pct>%`; a percentage height cannot resolve against a
    // table cell (a td's height is a minimum, not a definite size), so every "full height" bar
    // computed to 3-4px in a 22px track and the whole column read as a dim dash. The bars now sit
    // in a plain <div class="sparkbox"> with a definite 22px height, and each bar states its own
    // height in px, which is correct whatever the containing box turns out to be.
    const TRACK = 22;
    const bars = cells.map((n) => {
      const h = n ? Math.max(5, Math.round((n / peakN) * TRACK)) : 2;
      return `<i style="height:${h}px${n ? '' : ';background:#2f2818'}" title="${n} hit${n === 1 ? '' : 's'} in the last 30d window"></i>`;
    }).join('');
    return `<div class="sparkbox">${bars}</div>`;
  };
  // When the `hhit:` scan itself failed, every day-shaped column is UNKNOWN, not zero — printing
  // "0 visits in the last 7 days" for a person who may well have visited daily is exactly the
  // wrong-number-under-a-true-looking-label defect. The durable totals are unaffected and still show.
  const unk = '<span class="muted" title="the 30-day hit log could not be read — unknown, not zero">?</span>';
  const namedRows = [...namedVisitors.values()].sort((a, b) => (a.last < b.last ? 1 : -1)).map((nv) => {
    const lastMs = Date.parse(nv.last);
    return `<tr>
      <td><b>${nv.sigil ? esc(nv.sigil) : '<span class="muted">UNKNOWN</span>'}</b>${
        nv.id ? ` <span class="mono muted">${esc(nv.id)}</span>` : ''}${
        nv.machine ? `<br><span class="mono muted">${esc(nv.machine)}</span>` : ''}</td>
      <td>${isFinite(lastMs) ? esc(rel(Date.now() - lastMs)) : '<span class="muted">unknown</span>'}</td>
      <td class="num">${nv.count} <span class="muted">visit${nv.count === 1 ? '' : 's'}</span></td>
      <td class="num">${hitFailed ? unk : (nv.days.size ? nv.days.size : '<span class="muted">—</span>')}</td>
      <td class="num">${hitFailed ? unk : nVisits7(nv)}</td>
      <td class="num">${hitFailed ? unk : nVisits30(nv)}</td>
      <td class="t" data-t="${esc(nv.last)}">${esc(nv.last)}</td>
      <td class="t" data-t="${esc(nv.first)}">${esc(nv.first)}</td>
      <td>${nv.place ? esc(nv.place) : '<span class="muted">?</span>'}</td>
      <td class="spark">${hitFailed ? unk : sparkline(nv)}</td>
    </tr>`;
  }).join('');

  const peopleRows = [...people.values()].sort((a, b) => (a.last < b.last ? 1 : -1)).map((p) => `
    <tr>
      <td><b>${esc(p.who)}</b>${p.named ? '' : ' <span class="muted">(no login name — shown by IP)</span>'}</td>
      <td class="num">${p.n} <span class="muted">page-view${p.n === 1 ? '' : 's'}</span></td>
      <td class="num">${p.days.size} <span class="muted">day${p.days.size === 1 ? '' : 's'}</span></td>
      <td class="t" data-t="${esc(p.last)}">${esc(p.last)}</td>
      <td class="t" data-t="${esc(p.first)}">${esc(p.first)}</td>
      <td>${esc(p.place)}</td>
      <td>${esc(p.dev)}</td>
    </tr>`).join('');

  const logRows = visits.slice(0, 500).map((v) => `<tr>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
      <td>${v.user ? esc(v.user) : '<span class="muted">—</span>'}</td>
      <td>${esc(placeOf(v))}</td>
      <td class="mono">${esc(v.ip)}</td>
      <td>${esc(device(v.ua))}</td>
    </tr>`).join('');

  // ONE ROW PER MACHINE, newest beacon first. `online` is presence (a `console:` key alive inside
  // its 10-minute TTL), not an inference from how recent the timestamp looks.
  const nOnline = machines.filter((m) => m.online).length;
  const machineRows = machines.map((m) => {
    const place = [m.city, m.country].filter(Boolean).join(', ');
    const beaconMs = Date.parse(m.t);
    return `<tr>
      <td>${esc(m.nickname || m.machine || 'unknown')}${
        m.nickname && m.machine ? ` <span class="mono muted">${esc(m.machine)}</span>` : ''}</td>
      <td>${m.online ? '<b class="on-now">● online now</b>' : '<span class="muted">○ offline</span>'}</td>
      <td class="mono">${esc([m.platform, m.ver].filter(Boolean).join(' · ')) || '<span class="muted">—</span>'}</td>
      <td>${flag(m.country)} ${esc(place) || '<span class="muted">—</span>'}</td>
      <td>${isFinite(beaconMs) ? esc(rel(Date.now() - beaconMs)) : '—'}
        <span class="t mono muted" data-t="${esc(m.t)}">${esc(m.t)}</span></td>
    </tr>`;
  }).join('');

  // v1694 — the two population sizes, named ONCE here so the heading badge and the prose under
  // each table can never drift apart. They are deliberately NOT summed anywhere in this file.
  const beaconTotal = [...namedVisitors.values()].reduce((s, nv) => s + nv.count, 0);

  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Visits · bull-4-u</title>
<style>
  :root{color-scheme:dark}
  *{box-sizing:border-box}
  body{margin:0;background:#14110c;color:#e9ddc4;
       font:15px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
  header{padding:22px 20px 14px;border-bottom:1px solid #3a3122}
  h1{margin:0 0 3px;font-size:21px;color:#d4af37;letter-spacing:.01em}
  .sub{color:#9c8d6b;font-size:13px}
  h2{margin:26px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:.13em;
     color:#9c8d6b;font-weight:700}
  /* v1694 — the two people-tables count DIFFERENT populations, and the prose saying so sat in
     small grey text UNDER each table while the two headings were styled identically. A reader
     who only skims the headings could add the two totals. Each population now carries a badge
     ON its heading, in its own colour, with "never added" said in the badge itself. */
  .pop{display:inline-block;vertical-align:middle;margin-left:9px;padding:3px 9px;border-radius:999px;
       font-size:11px;letter-spacing:.04em;text-transform:none;font-weight:700;border:1px solid}
  .pop.beacon{background:#16240f;border-color:#4d7a2e;color:#a8d47a}
  .pop.ipinf{background:#101c26;border-color:#2e5c7a;color:#7ab6d4}
  .pop .sep{opacity:.55;font-weight:400;padding:0 2px}
  .pop .nadd{font-weight:400;opacity:.85}
  .wrap{padding:6px 20px 48px;max-width:1100px;margin:0 auto}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:18px}
  .card{background:#1c180f;border:1px solid #3a3122;border-radius:10px;padding:13px 15px}
  .card b{display:block;font-size:27px;line-height:1.1;color:#f0c060;font-variant-numeric:tabular-nums}
  .card i{display:block;font-style:normal;margin-top:3px;font-size:12px;color:#9c8d6b;
          letter-spacing:.05em;text-transform:uppercase}
  .chart{display:flex;align-items:flex-end;gap:3px;height:110px;padding:10px 12px;
         background:#1c180f;border:1px solid #3a3122;border-radius:10px}
  .bar{flex:1 1 0;height:100%;display:flex;align-items:flex-end;min-width:0}
  .bar i{display:block;width:100%;background:linear-gradient(180deg,#f0c060,#96702a);
         border-radius:2px 2px 0 0}
  .bar.zero i{background:#2f2818}
  .bar.today i{background:linear-gradient(180deg,#8fe6a0,#3f8a56)}
  .chart-x{display:flex;justify-content:space-between;margin-top:5px;font-size:11px;color:#6b6149}
  /* v1694 — per-person sparkline: 14 tiny bars inside one table cell, same colour language as the
     30-day chart above (gold = activity, dim = zero) so the two read as one visual system. */
     The bars are NOT laid out by the <td> itself — a td is a table cell, its height is a minimum
     rather than a definite size, so a child's percentage height has nothing to resolve against.
     The flex track is a plain <div class="sparkbox"> with a real 22px height inside the cell, and
     every bar states its height in px. */
  .spark{width:110px}
  .sparkbox{display:flex;align-items:flex-end;gap:1px;height:22px;width:84px}
  .sparkbox i{display:block;flex:1 1 0;min-width:4px;border-radius:1px 1px 0 0;
           background:linear-gradient(180deg,#f0c060,#96702a)}
  .tblwrap{overflow-x:auto;border:1px solid #2a2418;border-radius:10px}
  table{border-collapse:collapse;width:100%;min-width:640px}
  th,td{text-align:left;padding:9px 13px;border-bottom:1px solid #2a2418;white-space:nowrap}
  th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#9c8d6b;
     position:sticky;top:0;background:#1c180f}
  tr:last-child td{border-bottom:0}
  tr:hover td{background:#1f1a10}
  .num{font-variant-numeric:tabular-nums;color:#f0c060;font-weight:700}
  .mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:#c8bb98}
  .muted{color:#6b6149;font-weight:400}
  /* v1687 — presence green. STATUS-OK green, deliberately not an item-quality colour:
     on this page it means "beaconing right now", nothing about rarity. */
  .on-now{color:#66ff88}
  .empty{padding:44px;text-align:center;color:#9c8d6b}
  .t{font-variant-numeric:tabular-nums}
  /* v1602 — the crossover door to /console. Deliberately the loudest thing under the title:
     the failure it fixes was a correct sentence that got read past. */
  .xover{display:flex;align-items:center;gap:13px;margin:13px 0 2px;padding:12px 15px;
    background:linear-gradient(180deg,rgba(240,192,96,.10),rgba(240,192,96,.04));
    border:1px solid rgba(240,192,96,.42);border-radius:10px;text-decoration:none;color:inherit}
  .xover:hover{border-color:#f0c060;background:rgba(240,192,96,.14)}
  .xo-ic{font-size:22px;flex:none}
  .xo-txt{font-size:13px;line-height:1.5;color:#d9cbab}
  .xo-txt b{display:block;color:#f0c060;font-size:14px;margin-bottom:2px}
  .xo-go{margin-left:auto;flex:none;white-space:nowrap;font-size:13px;font-weight:700;color:#f0c060;
    border:1px solid rgba(240,192,96,.5);border-radius:999px;padding:7px 13px}
  @media (max-width:640px){.xover{flex-wrap:wrap}.xo-go{margin-left:0}}
  .note{margin-top:9px;font-size:12px;color:#6b6149;line-height:1.6}
  .scope{margin-top:18px;background:#1c180f;border:1px solid #3a3122;border-left:3px solid #d4af37;
         border-radius:10px;padding:13px 16px;font-size:13px;line-height:1.65;color:#c8bb98}
  .scope b{color:#e9ddc4}
  .scope .hd{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.13em;
             color:#d4af37;font-weight:700;margin-bottom:5px}
  .scope a{color:#f0c060}
  .fresh{margin-top:12px;background:#1c180f;border:1px solid #3a3122;border-left:3px solid #3f8a56;
         border-radius:10px;padding:12px 16px;font-size:14px;color:#e9ddc4}
  .fresh .big{font-size:17px;font-weight:700;color:#8fe6a0}
  .fresh .sub2{display:block;margin-top:4px;font-size:12px;color:#9c8d6b;line-height:1.6}
  .fresh.warn{border-left-color:#e0803a}
  .fresh.warn .big{color:#f0a050}
</style></head><body>
<header>
  <h1>👁 Visits &middot; page-views of /d2r/ + console-app machines</h1>
  <div class="sub">bull-4-u.com/d2r · private · times in your local zone · entries auto-expire after ${ttlDays} days</div>
  <!-- v1602 — A DOOR, NOT A FOOTNOTE. This used to be six words at the end of the subtitle
       ("...not the console app — that's here"), with the link text "that's here". Konyo went looking
       for his cousin's activity, read past it, and reported the tracker as not tracking him at all —
       while /console had been listing that exact machine (LAPTOP-QNFL860M, "Dean", Monroe US) the
       whole time. The data was never missing; the DOOR was. A correct sentence nobody reads is not
       documentation, it is decoration. -->
  <a class="xover" href="${esc(consoleHref)}">
    <span class="xo-ic">📺</span>
    <span class="xo-txt"><b>Console-app machines are on this page now &mdash; scroll to
      &ldquo;Console app&rdquo;.</b>
      ${machines.length
        ? `${machines.length} machine${machines.length === 1 ? '' : 's'} tracked${
            nOnline ? `, <b>${nOnline} online right now</b>` : ''}.`
        : 'None have checked in yet.'}
      /console has the per-event history and beacon health.</span>
    <span class="xo-go">open /console &rarr;</span>
  </a>
</header>
<div class="wrap">

  <div class="scope">
    <span class="hd">What this page counts &mdash; and what it cannot</span>
    This page counts <b>browser page-views of the bible at /d2r/</b>, and nothing else. Every row here
    is somebody who opened the site in a web browser.
    <br><br>
    The <b>📺 TV DIABLO console app</b> is a different thing and is counted separately, in its own
    section below. The console talks straight to its own endpoint and <b>never loads the /d2r/
    page</b>, so it can never appear in the page-view numbers &mdash; that is not a fault in either
    tracker, it is what the two are measuring. <b>A machine absent from the page-view tables has not
    necessarily been offline:</b> it may have used the app instead of the website, and the machines
    section below is where that shows.
    <br><br>
    <b>v1694 &mdash; a third source, also below:</b> when the board itself beacons a stable identity,
    it lands in the <b>Named visitors</b> table with a real WHO, not a guess. That table and the
    older IP-inferred <b>Who</b> table are <b>two different populations, kept as two numbers</b>
    &mdash; a visitor with no beacon shows up only in the IP-inferred one, never merged into a named
    row and never quietly dropped.
    <br><br>
    Per-session history, boot events and beacon health stay on the deep page:
    <a href="${esc(consoleHref)}">📺 /console &rarr;</a>
  </div>

  <h2>📺 Console app &middot; machines running TV DIABLO${
    machines.length ? ` &middot; ${nOnline} online now` : ''}</h2>
${machines.length ? `
  <div class="tblwrap"><table>
    <thead><tr><th>Machine</th><th>State</th><th>Build</th><th>Where</th><th>Last beacon</th></tr></thead>
    <tbody>${machineRows}</tbody>
  </table></div>
  <div class="note">These are <b>app sessions, not page-views</b>, and they are <b>not added to any
    number above</b> &mdash; a beacon means the console app is running, a page-view means a browser
    opened the site. One machine can do both, neither, or either. <b>&ldquo;Online now&rdquo;</b>
    means it checked in within the last 10 minutes.
    <br><br>
    This is the summary. Boot events, ON AIR flips and beacon health &mdash; including a machine
    whose beacon has been silently failing &mdash; are on
    <a href="${esc(consoleHref)}" style="color:#f0c060">📺 /console</a>.</div>
` : `  <div class="empty">No console-app machines have checked in. If someone is running TV DIABLO
      right now, its beacon is not reaching the server &mdash;
      <a href="${esc(consoleHref)}" style="color:#f0c060">📺 /console</a> shows the last attempt each
      machine made.</div>`}

  <div class="fresh${stale ? ' warn' : ''}">
    ${newest
      ? `<span class="big">Last page-view ${esc(rel(ageMs))}</span>
         <span class="sub2">at <span class="t" data-t="${esc(newest)}">${esc(newest)}</span> ${
           stale
             ? '&mdash; <b>no page-views recorded recently &mdash; this may be normal, or recording may have stopped.</b> Load bull-4-u.com/d2r once in a browser and refresh this page: if the number above does not move, recording really has stopped.'
             : '&mdash; recording is live.'}</span>`
      : `<span class="big">No page-views have ever been recorded</span>
         <span class="sub2"><b>No page-views recorded recently &mdash; this may be normal, or recording may have stopped.</b> Load bull-4-u.com/d2r once in a browser and refresh this page.</span>`}
  </div>

  <div class="note">
    <b>Data window:</b> each page-view record auto-expires ${ttlDays} days after it is written
    (<span class="mono">expirationTtl: ${VISIT_TTL_S}</span> in <span class="mono">recordVisit()</span>,
    functions/_middleware.js), so these numbers can reach back to <b>${esc(horizon)}</b> at the very
    furthest &mdash; anything older is gone and its absence here means nothing.
    Scanned <b>${keys.length}</b> stored record${keys.length === 1 ? '' : 's'},
    of which <b>${visits.length}</b> parsed as usable page-views.
    ${truncated
      ? '<b style="color:#f0a050">The scan hit its 20,000-record ceiling and was TRUNCATED &mdash; the totals below are a floor, not a total.</b>'
      : 'The scan was complete &mdash; not truncated.'}
  </div>

${visits.length ? `
  <div class="cards">
    <div class="card"><b>${visits.length}</b><i>page-views logged</i></div>
    <div class="card"><b>${people.size}</b><i>people</i></div>
    <div class="card"><b>${nToday}</b><i>page-views today</i></div>
    <div class="card"><b>${n7}</b><i>page-views, last 7 days</i></div>
  </div>

  <h2>Last 30 days</h2>
  <div class="chart">${bars}</div>
  <div class="chart-x"><span>30 days ago</span><span>today</span></div>
` : ''}

  <h2>Named visitors &middot; identified by beacon${
    namedFailed ? ' <span class="pop beacon" style="color:#f0a050;border-color:#8a5a20;background:#241a0f">POPULATION A &middot; size UNKNOWN &mdash; identity scan FAILED</span>'
    : namedVisitors.size ? ` <span class="pop beacon">POPULATION A<span class="sep">&middot;</span>${
        namedVisitors.size} identit${namedVisitors.size === 1 ? 'y' : 'ies'}<span class="sep">&middot;</span>${
        beaconTotal} beaconed visit${beaconTotal === 1 ? '' : 's'}<span class="sep">&middot;</span><span class="nadd">never added to population B</span></span>`
    : ''}</h2>
${namedFailed ? `  <div class="empty"><b style="color:#f0a050">The identity scan failed &mdash; this is
      not a statement that nobody has visited.</b> Reading the <span class="mono">hvisitor:</span>
      keys threw, so how many named people there are is <b>UNKNOWN</b>, not zero. Refresh; if it
      persists the KV binding is the thing to look at. The IP-inferred numbers below are read
      separately and are unaffected.</div>`
  : namedVisitors.size ? `
  <div class="tblwrap"><table>
    <thead><tr><th>Person</th><th>Last seen</th><th>Visits</th><th>Days active <span class="mono muted">(30d)</span></th>
      <th>Last 7d</th><th>Last 30d</th><th>Last visit</th><th>First visit</th><th>Location</th>
      <th>Last 14 days</th></tr></thead>
    <tbody>${namedRows}</tbody>
  </table></div>
  <div class="note"><b>This table is built from the board's own identity beacon</b>
    (<span class="mono">hvisitor:</span>/<span class="mono">hhit:</span>, written by
    <span class="mono">/api/hello</span>), not from IP guessing &mdash; so the same person on a
    phone and a laptop stays two rows under two self-typed names, never merged, and a record with
    no name/code renders as <b>UNKNOWN</b> rather than being silently dropped.
    <b>No true &ldquo;online now&rdquo; signal exists for this scheme</b> &mdash; the beacon fires
    once per page-load and holds no heartbeat, unlike the console app's TTL'd presence key above
    &mdash; so this column shows <b>last seen</b>, not presence. Visits/first/last come straight
    from the durable record; days-active/7d/30d/sparkline can only see the last 30 days because
    that is all <span class="mono">hhit:</span> retains.${hitFailed
      ? ` <b style="color:#f0a050">The 30-day hit log could not be read on this request, so every
        day-shaped column shows <span class="mono">?</span> &mdash; UNKNOWN, not zero. The visit
        totals, first and last seen come from a separate read and still stand.</b>`
      : ''}
    <br><br>
    <b>It is not the same population as the &ldquo;Who&rdquo; table below.</b> Anyone on a stale
    cached build, with JS blocked, or who never typed a name/code, never beacons and so never
    appears here &mdash; they still land in the IP-inferred numbers below. Named identities:
    <b>${namedVisitors.size}</b>, totalling <b>${beaconTotal}</b>
    beaconed visit${beaconTotal === 1 ? '' : 's'} (<b>population A</b>, green badge above).
    IP-inferred page-views: <b>${visits.length}</b> across <b>${people.size}</b> IP/login bucket${
      people.size === 1 ? '' : 's'} (<b>population B</b>, blue badge below). These two totals are <b>never added together</b> &mdash; they
    measure different, overlapping-but-not-identical populations.${hitTruncated
      ? ' <b style="color:#f0a050">The 30-day hit scan hit its 20,000-record ceiling and was TRUNCATED.</b>'
      : ''}${hitUnparsed
      ? ` <b style="color:#f0a050">${hitUnparsed} hit key${hitUnparsed === 1 ? '' : 's'} did not match
          the expected <span class="mono">hhit:&lt;ISO&gt;:&lt;rand&gt;:&lt;id&gt;</span> shape and ${
          hitUnparsed === 1 ? 'was' : 'were'} left out of the day columns rather than guessed at.</b>`
      : ''}</div>
` : `  <div class="empty">No beaconed visitor identity yet &mdash; and this really is a read that
      succeeded and found nothing, not a failed read. Either nobody has loaded a build that beacons
      it, or nobody has typed a name/code for the beacon to send &mdash; <span class="mono">
      /api/hello</span> silently skips writing an anonymous beacon rather than fabricating an
      identity. The IP-inferred section below still has what it has always had.</div>`}

${visits.length ? `
  <h2>Who &middot; IP-inferred (no beacon identity) <span class="pop ipinf">POPULATION B<span class="sep">&middot;</span>${
    people.size} IP/login bucket${people.size === 1 ? '' : 's'}<span class="sep">&middot;</span>${
    visits.length} page-view${visits.length === 1 ? '' : 's'}<span class="sep">&middot;</span><span class="nadd">never added to population A</span></span></h2>
  <div class="tblwrap"><table>
    <thead><tr><th>Person</th><th>Page-views</th><th>Days seen</th><th>Last page-view</th>
      <th>First page-view</th><th>Location</th><th>Device</th></tr></thead>
    <tbody>${peopleRows}</tbody>
  </table></div>
  <div class="note">A &ldquo;person&rdquo; here is the login name they typed, or their IP when they
    left it blank &mdash; <b>this table has no beacon identity, only IP-inference.</b> So the same
    cousin on a phone and a laptop counts twice, and several people behind one router with no login
    name collapse into one. This is a <b>different population</b> from the Named Visitors table
    above: it is a floor for &ldquo;at least this many people&rdquo;, not a headcount.
    <br><br>
    Each count above is <b>web page-views of /d2r/</b>. A row reading &ldquo;1 page-view&rdquo; means
    they opened the <b>website</b> once &mdash; it says <b>nothing</b> about how much they used the
    📺 TV DIABLO console app. That is the separate section above, counted in its own units.</div>

  <h2>Raw log &middot; browser page-views${visits.length > 500 ? ' &middot; newest 500' : ''}</h2>
  <div class="tblwrap"><table>
    <thead><tr><th>When</th><th>Login name</th><th>Location</th><th>IP</th><th>Device</th></tr></thead>
    <tbody>${logRows}</tbody>
  </table></div>
` : `<div class="empty">No <b>IP-inferred page-view records</b> (<span class="mono">visit:</span>,
      written by functions/_middleware.js) are in the store right now. Load the app in a web browser
      once and refresh this page.<br><br>This says nothing about the 📺 console app &mdash; its
      machines are in their own section above &mdash; and <b>nothing about the Named visitors table
      above either</b>: those records live 400 days while these expire after ${ttlDays}, so a quiet
      stretch empties this section while named identities are still perfectly readable. Two
      populations, two independent reads.</div>`}
</div>
<script>
  // stored timestamps are UTC ISO — show them in the viewer's own zone
  // td.t = table cells; span.t = the freshness line's absolute timestamp
  for (const el of document.querySelectorAll('td.t, span.t')) {
    const d = new Date(el.dataset.t);
    if (!isNaN(d)) el.textContent = d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }
</script>
</body></html>`;

  return new Response(html, {
    headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' },
  });
}
