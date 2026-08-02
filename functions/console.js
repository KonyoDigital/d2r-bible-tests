/**
 * /console — private CONSOLE-APP dashboard for Konyo (v875 · fleet rebuild v1596).
 *
 * The console twin of /visits. Three layers, newest-first:
 *   1. ONLINE NOW      — presence keys `console:<machine>` (10-min TTL, fed by the app's beacon)
 *   2. THE FLEET       — durable `lastseen:<machine>` keys (~400-day TTL, written on EVERY beacon
 *                        INCLUDING heartbeats) → "when was this machine last here" is answerable
 *                        directly instead of being reconstructed from a log never designed for it.
 *   3. RECENT EVENTS   — `consolelog:<ts>:<machine>` (30 days, boots + ON AIR flips only)
 *
 * WHAT THIS PAGE DOES NOT COVER: website page-views of /d2r/. Those live at /visits. A machine
 * shows up here only if it RAN the console app AND its beacon REACHED the server — which is why
 * the beacon-health column exists: a machine whose beacon has silently failed for months used to
 * look identical to a machine that was never switched on.
 *
 * ACCESS: ?k=<VISITS_KEY> — same secret as /visits; without it (or with the wrong one) the page
 * returns a bare 404, indistinguishably.
 */
export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const provided = url.searchParams.get('k') || '';
  const SECRET = env && env.VISITS_KEY;
  if (!SECRET || provided !== SECRET) {
    return new Response('Not found', { status: 404, headers: { 'content-type': 'text/plain' } });
  }
  const kv = env && env.TZ_HISTORY;
  if (!kv) return new Response('storage unavailable', { status: 500 });

  // v1496 — CI runners used to check in from every test job, so the fleet listed a GitHub VM in
  // Boydton beside Konyo's MacBook. Mirrors the identical filter in /api/console: the answer to
  // "who is here" must only ever contain machines that are his.
  const isRunner = (m) => /^runnervm|^fv-az|^runner-/i.test(String((m && m.machine) || ''));

  // PRESENCE. `prefix:'console:'` does NOT also match `consolelog:` keys — CHECKED BY EXECUTION
  // 2026-08-02: 'consolelog:…'.startsWith('console:') === false, because character 7 is 'l' where
  // the prefix demands ':'. The suspected prefix collision here is REFUTED, not merely unobserved,
  // and a test pins it. Leave this listing alone.
  const online = await kv.list({ prefix: 'console:' });
  const now = await Promise.all(online.keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const live = now.filter(Boolean).filter((v) => !isRunner(v)).sort((a, b) => (a.t < b.t ? 1 : -1));

  // THE BUG THIS REBUILD EXISTS FOR (fixed 2026-08-02, same defect as /api/console:78 — the two
  // files share it by copy-paste, so they are fixed with the IDENTICAL helper and must not drift):
  // this used to list prefix 'consolelog:' with a bare limit of four hundred. KV returns keys in
  // LEXICOGRAPHIC ASCENDING order and the keys are `consolelog:<ISO-ts>:<machine>`, so that bare
  // limit returned the OLDEST four hundred events in the 30-day window. Measured against a 900-event
  // fixture: the old shape saw 400/900 keys, its newest visible event was 21 days stale, and a
  // machine present only in the newest 5 events was INVISIBLE — exactly Konyo's report ("my cousin
  // used it yesterday and i DONT SEE IT"). Cursor pagination is correct under EITHER ordering,
  // which is the whole point; raising the limit would not be.
  //
  // v1597.1 — AND THEN THE FIX HAD A BUG. Listing every key was right; doing a kv.get() per key
  // was not. 2,556 events on the real store meant 2,556 subrequests in one invocation, and Workers
  // cap that: this page started returning HTTP 500 "Too many API requests by single Worker
  // invocation" (read off `wrangler pages deployment tail` — the local stub could never reproduce
  // it, because the limit does not exist off-platform). Machine and timestamp parse straight out
  // of the key name at zero cost; only the newest events we actually RENDER are fetched.
  const logKeys = await listAll(kv, 'consolelog:');
  const logHeads = machinesFromLogKeys(logKeys);                    // newest event per machine, free
  const newestKeys = logKeys
    .map((k) => k.name)
    .filter((n) => n.startsWith('consolelog:'))
    .sort()                                                         // ascending ISO → oldest first
    .slice(-120)                                                    // ...so the TAIL is the newest
    .reverse();
  const logRaw = await Promise.all(newestKeys.map((n) => kv.get(n, 'json').catch(() => null)));
  const logAll = logRaw.filter(Boolean).filter((v) => !isRunner(v)).sort((a, b) => (a.t < b.t ? 1 : -1));
  const log = logAll.slice(0, 120);

  // DURABLE LAST-SEEN. Written by /api/console on every beacon, heartbeats included.
  const seenKeys = await listAll(kv, 'lastseen:');
  const seenRaw = await Promise.all(seenKeys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const lastseen = seenRaw.filter(Boolean).filter((v) => !isRunner(v));

  const nowMs = Date.now();
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const flag = (cc) => {
    if (!cc || cc.length !== 2) return '';
    const A = 0x1f1e6;
    return String.fromCodePoint(A + cc.toUpperCase().charCodeAt(0) - 65, A + cc.toUpperCase().charCodeAt(1) - 65);
  };
  const modeBadge = (m) =>
    m === 'live' ? '<span class="b on">🔴 ON AIR</span>'
    : m === 'sim' ? '<span class="b sim">✦ SIM</span>'
    : m === 'stopping' ? '<span class="b">⏳ sealing</span>'
    : '<span class="b off">○ idle</span>';

  // human relative age — "11 days ago" is what Konyo actually reads; the ISO stamp stays beside it
  const ms = (iso) => { const d = Date.parse(iso); return isNaN(d) ? null : d; };
  const ago = (iso) => {
    const t = ms(iso);
    if (t == null) return 'unknown';
    const s = Math.max(0, Math.round((nowMs - t) / 1000));
    if (s < 90) return s + 's ago';
    const m = Math.round(s / 60);
    if (m < 90) return m + ' min ago';
    const h = Math.round(m / 60);
    if (h < 36) return h + (h === 1 ? ' hour ago' : ' hours ago');
    const d = Math.round(h / 24);
    if (d < 45) return d + (d === 1 ? ' day ago' : ' days ago');
    const mo = Math.round(d / 30);
    return mo + (mo === 1 ? ' month ago' : ' months ago');
  };
  const where = (v) => (flag(v.country) + ' ' + (v.city || v.country || '')).trim();
  const name = (v) => esc(v.nickname || v.machine || 'unknown')
    + (v.nickname && v.machine && v.nickname !== v.machine ? ' <span class="muted">(' + esc(v.machine) + ')</span>' : '');

  // BEACON HONESTY. `lastBeacon` describes that machine's PREVIOUS beacon attempt, reported by
  // tv/control_app.py on the NEXT one. Never render this blank: absent means "old build", which is
  // a different fact from "failing", which is a different fact from "fine".
  const beaconCell = (lb) => {
    if (!lb || typeof lb !== 'object') {
      return '<td class="muted" title="this build predates beacon self-reporting">unknown <span class="mono">(old build)</span></td>';
    }
    if (lb.ok) {
      return '<td><span class="b ok">✓ reached server</span>' + (lb.t ? ' <span class="mono">' + esc(ago(lb.t)) + '</span>' : '') + '</td>';
    }
    const detail = [lb.code ? 'HTTP ' + lb.code : '', lb.err || ''].filter(Boolean).join(' · ') || 'failed, no detail';
    return '<td class="bad"><span class="b err">✗ beacon FAILED</span> <span class="mono">' + esc(detail) + '</span></td>';
  };

  // ── FLEET (layer 2) ────────────────────────────────────────────────────────────────────────
  // Dedupe on EXACT machine name only. A machine that is online right now is marked online here
  // rather than duplicated confusingly.
  const liveNames = new Set(live.map((v) => v.machine));
  const fleetMap = new Map();
  for (const v of lastseen) if (v.machine) fleetMap.set(v.machine, { ...v, src: 'lastseen' });
  // Fallback for the window before /api/console is redeployed (no `lastseen:` keys exist yet):
  // reconstruct the fleet from presence + the event log so the table is never falsely empty. This
  // is clearly labelled below — reconstructed rows only know about boots and ON AIR flips, so their
  // "last seen" is a LOWER BOUND, not the truth.
  //
  // v1597.1 — `logHeads` is what makes this complete. `logAll` is now only the newest 120 EVENTS
  // (the subrequest cap forbids fetching all 2,556), so a machine whose last boot is older than
  // those 120 would be missing from the reconstruction — the original oldest-400 bug wearing a
  // smaller hat. logHeads is derived from ALL key names at zero read cost, so every machine that
  // ever appears in the log is represented. Detailed rows sort first and win the dedupe; the
  // key-derived ones fill in behind them with machine + time and '?' for the rest.
  let reconstructed = 0;
  if (fleetMap.size === 0) {
    for (const v of [...live, ...logAll, ...logHeads]) {
      if (!v.machine || fleetMap.has(v.machine)) continue;
      fleetMap.set(v.machine, { ...v, src: 'reconstructed' });
      reconstructed++;
    }
  }
  const fleet = [...fleetMap.values()].sort((a, b) => (a.t < b.t ? 1 : -1));

  const fleetRows = fleet.map((v) => {
    const on = liveNames.has(v.machine);
    return `<tr>
      <td>${name(v)}</td>
      <td>${on ? '<span class="b live">● ONLINE</span>' : '<span class="b off">○ offline</span>'}</td>
      <td>${esc(v.platform || '?')} · ${esc(v.ver || '?')}</td>
      <td>${esc(where(v)) || '<span class="muted">—</span>'}</td>
      <td><b>${esc(ago(v.t))}</b><br><span class="mono t" data-t="${esc(v.t)}">${esc(v.t)}</span></td>
      ${beaconCell(v.lastBeacon)}
    </tr>`;
  }).join('');

  const liveRows = live.map((v) => `<tr>
      <td><b>${name(v)}</b>${v.user ? ' <span class="muted">(' + esc(v.user) + ')</span>' : ''}</td>
      <td>${esc(v.platform)} · ${esc(v.ver)}</td>
      <td>${modeBadge(v.mode)}</td>
      <td>${v.reads ? esc(v.reads) + ' reads' : '<span class="muted">—</span>'}</td>
      <td>${esc(where(v))}</td>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
    </tr>`).join('');

  const logRows = log.map((v) => `<tr>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
      <td><b>${name(v)}</b></td>
      <td>${esc(v.event)}</td>
      <td>${esc(v.platform)} · ${esc(v.ver)}</td>
      <td>${modeBadge(v.mode)}</td>
    </tr>`).join('');

  // ── FLEET-WIDE FRESHNESS ───────────────────────────────────────────────────────────────────
  // The newest beacon from ANY machine. If even THAT is stale, the beacon PATH is broken — which
  // is a completely different diagnosis from "nobody happens to be online right now", and the one
  // this page previously had no way to say.
  const stamps = [...live, ...fleet, ...logAll].map((v) => ms(v.t)).filter((n) => n != null);
  const newest = stamps.length ? Math.max(...stamps) : null;
  const newestIso = newest == null ? '' : new Date(newest).toISOString();
  const staleMin = newest == null ? null : Math.round((nowMs - newest) / 60000);
  const STALE_AFTER_MIN = 30;
  const isStale = newest == null || staleMin > STALE_AFTER_MIN;
  const freshness = newest == null
    ? `<div class="fresh bad-box"><b>⚠ NO BEACON HAS EVER BEEN RECEIVED.</b> ${fleet.length} machines known.
       Either no machine has run the console app, or every beacon has failed to reach bull-4-u.com.</div>`
    : isStale
      ? `<div class="fresh bad-box"><b>⚠ NEWEST BEACON FROM THE WHOLE FLEET IS ${esc(ago(newestIso))}</b>
         (<span class="t" data-t="${esc(newestIso)}">${esc(newestIso)}</span>) — older than ${STALE_AFTER_MIN} minutes.
         That points at the BEACON PATH being broken (app not running anywhere, network, or the endpoint),
         not merely at nobody being online. ${fleet.length} machines known in total.</div>`
      : `<div class="fresh ok-box"><b>${fleet.length} machines known</b> · newest beacon from any machine
         <b>${esc(ago(newestIso))}</b> (<span class="t" data-t="${esc(newestIso)}">${esc(newestIso)}</span>) — beacon path healthy.</div>`;

  const visitsHref = '/visits?k=' + encodeURIComponent(provided);
  const totalKeys = online.keys.length + logKeys.length + seenKeys.length;
  const PAGE_CAP = 50, PAGE_SIZE = 1000;
  const scanComplete = logKeys.length < PAGE_CAP * PAGE_SIZE && seenKeys.length < PAGE_CAP * PAGE_SIZE;
  const reqEst = (n) => Math.max(1, Math.ceil(n / PAGE_SIZE));

  const emptyWhy = 'The console app was never run there, or its beacon could not reach bull-4-u.com.';

  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🖥 TV DIABLO — console dashboard</title>
<style>
  :root{color-scheme:dark}
  body{background:#0b0a08;color:#e8ddc8;font:14px/1.5 ui-monospace,Menlo,monospace;margin:24px;max-width:1100px}
  @media (max-width:640px){body{margin:12px;font-size:13px}}
  h1{font-size:18px;color:#f0c060} h2{font-size:14px;color:#c9b483;margin-top:28px}
  .wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
  table{border-collapse:collapse;width:100%;margin-top:10px;min-width:560px}
  td,th{padding:6px 10px;border-bottom:1px solid #2a2418;text-align:left;vertical-align:top}
  th{color:#8f7f66;font-weight:normal;font-size:12px;letter-spacing:.08em}
  .muted{color:#6d6353}.mono{font-family:inherit;font-size:12px;color:#9a8d73}
  .b{padding:1px 8px;border-radius:9px;border:1px solid #3a3222;font-size:12px;white-space:nowrap}
  .b.on{color:#ff6a5e;border-color:#7a2e28;background:#2a120f}
  .b.sim{color:#b9a5ff;border-color:#4a3d7a}
  .b.off{color:#8d8370}
  .b.live{color:#6ee08a;border-color:#2c6b3f;background:#0f2416}
  .b.ok{color:#6ee08a;border-color:#2c6b3f}
  .b.err{color:#ff8a7a;border-color:#7a2e28;background:#2a120f}
  td.bad{background:#2a120f}
  .empty{color:#6d6353;padding:18px 4px}
  .scope{border:1px solid #3a3222;background:#141109;border-radius:8px;padding:12px 14px;margin:14px 0;color:#cbbd9e}
  .scope b{color:#f0c060} .scope a{color:#7fc8ff}
  .fresh{border-radius:8px;padding:10px 14px;margin:14px 0}
  .ok-box{border:1px solid #2c6b3f;background:#0f2416;color:#cfe9d5}
  .bad-box{border:1px solid #7a2e28;background:#2a120f;color:#ffd6cf}
  .foot{margin-top:26px;color:#5f5647;font-size:12px}
</style></head><body>
<h1>🖥 TV DIABLO — console dashboard</h1>

<div class="scope">
  <b>What this page tracks:</b> the TV DIABLO console <b>APP</b> checking in from each machine
  (Mac / Windows / cousins running <span class="mono">tv/control_app.py</span>).<br>
  <b>What it does NOT track:</b> website visits to <span class="mono">/d2r/</span> — those are at
  <a href="${esc(visitsHref)}">/visits</a>.<br>
  A machine appears here <b>only</b> if it ran the console app <b>and</b> its beacon reached the server.<br>
  <span class="muted">Retention: presence expires after 10 minutes · the event log keeps 30 days ·
  last-seen keeps ~400 days. The app beacons on boot, on ON AIR / OFF, and every ~4 minutes.</span>
</div>

${freshness}

<h2>🟢 online now (${live.length}) <span class="muted">— beaconed within the last 10 minutes</span></h2>
<div class="wrap"><table><tr><th>machine</th><th>build</th><th>mode</th><th>session</th><th>where</th><th>last beacon</th></tr>
${liveRows || `<tr><td colspan="6" class="empty">We looked and found none online right now. ${esc(emptyWhy)}</td></tr>`}</table></div>

<h2>🛰 the fleet (${fleet.length}) <span class="muted">— every machine ever seen, online or not</span></h2>
${reconstructed ? `<div class="fresh bad-box"><b>Reconstructed from the event log.</b> No
 <span class="mono">lastseen:</span> keys exist yet, which means the <span class="mono">/api/console</span>
 build writing them has not been deployed. These "last seen" times are a LOWER BOUND (boots and ON AIR
 flips only — heartbeats are not in the event log). Redeploy to get true last-seen.</div>` : ''}
<div class="wrap"><table><tr><th>machine</th><th>state</th><th>build</th><th>where</th><th>last seen</th><th>its last beacon attempt</th></tr>
${fleetRows || `<tr><td colspan="6" class="empty">We looked and found no machines at all — not even offline ones. ${esc(emptyWhy)}</td></tr>`}</table></div>

<h2>📜 recent events (${log.length} of ${logAll.length}) <span class="muted">— boots and ON AIR flips, 30-day window</span></h2>
<div class="wrap"><table><tr><th>when</th><th>machine</th><th>event</th><th>build</th><th>mode</th></tr>
${logRows || `<tr><td colspan="5" class="empty">We looked and found no events. ${esc(emptyWhy)}</td></tr>`}</table></div>

<div class="foot">
  scan: ${totalKeys} keys read — presence ${online.keys.length} · events ${logKeys.length} · last-seen ${seenKeys.length}
  · ~${reqEst(logKeys.length) + reqEst(seenKeys.length) + 1} KV list requests (cursor followed to exhaustion, ${PAGE_SIZE}/page, cap ${PAGE_CAP} pages)
  · scan complete: <b>${scanComplete ? 'yes' : 'NO — hit the page cap, some keys were not read'}</b>
</div>
<script>
  document.querySelectorAll('.t').forEach(function(td){
    var d = new Date(td.dataset.t);
    if (!isNaN(d)) td.textContent = d.toLocaleString();
  });
</script>
</body></html>`;
  return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } });
}

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

/**
 * Follow the KV list cursor to exhaustion. KV caps a page at 1000 keys and returns them in
 * LEXICOGRAPHIC ASCENDING order, so a bare `limit: N` over `<prefix>:<ISO-ts>:…` keys silently
 * returns the OLDEST N and hides everything recent. Reading every key is correct under EITHER
 * ordering — that is why this replaces the limit rather than raising it.
 *
 * Byte-identical to the helper in functions/api/console.js ON PURPOSE: those two files already
 * shipped this bug once by copy-paste, and they must not drift again. functions/visits.js carries
 * the same pattern inline. Do not "optimise" a `limit:` back into any of them.
 */
async function listAll(kv, prefix) {
  const keys = []; let cursor;
  for (let i = 0; i < 50; i++) {
    const page = await kv.list({ prefix, limit: 1000, cursor });
    keys.push(...page.keys);
    if (page.list_complete || !page.cursor) break;
    cursor = page.cursor;
  }
  return keys;
}
