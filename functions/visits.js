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
 * ── SCOPE (added after the 2026-08-02 "the tracker is broken" report) ───────────────────────────
 * THIS PAGE COUNTS BROWSER PAGE-VIEWS OF /d2r/ ONLY. Nothing else. There are TWO trackers on this
 * site and they answer DIFFERENT questions:
 *   /visits  (this file)              ← browser page-views, written by recordVisit() in _middleware.js
 *   /console (functions/console.js)   ← TV DIABLO console APP presence, written by the beacon in
 *                                       tv/control_app.py, which POSTs to /api/console and NEVER
 *                                       loads the /d2r/ page.
 * So the console app CAN NEVER APPEAR HERE, BY DESIGN. Konyo went looking for his cousin's console
 * session on this page, correctly did not find it, and concluded the tracker was dead. Half the
 * root cause was not a code bug at all — it was that neither page said what it was. It says so now,
 * loudly, at the top, with a link through to /console carrying the same ?k=.
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
  .empty{padding:44px;text-align:center;color:#9c8d6b}
  .t{font-variant-numeric:tabular-nums}
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
  <h1>👁 Visits &middot; browser page-views of /d2r/</h1>
  <div class="sub">bull-4-u.com/d2r · private · times in your local zone · entries auto-expire after ${ttlDays} days
    · <b>not</b> the 📺 TV DIABLO console app — <a href="${esc(consoleHref)}" style="color:#f0c060">that's here</a></div>
</header>
<div class="wrap">

  <div class="scope">
    <span class="hd">What this page counts &mdash; and what it cannot</span>
    This page counts <b>browser page-views of the bible at /d2r/</b>, and nothing else. Every row here
    is somebody who opened the site in a web browser.
    <br><br>
    It does <b>not</b> and <b>cannot</b> show the <b>📺 TV DIABLO console app</b>. The console talks
    straight to its own endpoint and never loads the /d2r/ page, so it is invisible here <b>by
    design</b> &mdash; that is not a fault in either tracker. <b>A machine missing from this page has
    not necessarily been offline.</b> It may simply have used the console app instead of the website.
    <br><br>
    Console sessions live on their own tracker: <a href="${esc(consoleHref)}">📺 /console &rarr;</a>
  </div>

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

  <h2>Who</h2>
  <div class="tblwrap"><table>
    <thead><tr><th>Person</th><th>Page-views</th><th>Days seen</th><th>Last page-view</th>
      <th>First page-view</th><th>Location</th><th>Device</th></tr></thead>
    <tbody>${peopleRows}</tbody>
  </table></div>
  <div class="note">A &ldquo;person&rdquo; is the login name they typed, or their IP when they left it
    blank. So the same cousin on a phone and a laptop counts twice, and several people behind one
    router with no login name collapse into one. Tell each of them to log in with their own name and
    this column becomes exact.
    <br><br>
    Each count above is <b>web page-views of /d2r/</b>. A row reading &ldquo;1 page-view&rdquo; means
    they opened the <b>website</b> once &mdash; it says <b>nothing</b> about how much they used the
    📺 TV DIABLO console app, which is tracked separately at
    <a href="${esc(consoleHref)}" style="color:#f0c060">/console</a>.</div>

  <h2>Raw log &middot; browser page-views${visits.length > 500 ? ' &middot; newest 500' : ''}</h2>
  <div class="tblwrap"><table>
    <thead><tr><th>When</th><th>Login name</th><th>Location</th><th>IP</th><th>Device</th></tr></thead>
    <tbody>${logRows}</tbody>
  </table></div>
` : `<div class="empty">No <b>browser page-views</b> recorded yet. Load the app in a web browser once
      and refresh this page.<br><br>Remember: 📺 TV DIABLO console sessions never appear here &mdash;
      see <a href="${esc(consoleHref)}" style="color:#f0c060">/console</a>.</div>`}
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
