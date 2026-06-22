/**
 * /visits — private visit-log viewer for Konyo.
 *
 * Reads every `visit:` entry from the TZ_HISTORY KV store (written by _middleware's
 * recordVisit) and renders them newest-first as a simple HTML table. Times are
 * converted to the viewer's LOCAL timezone in-browser.
 *
 * ACCESS: requires ?k=<VISITS_KEY> matching the VISITS_KEY Pages secret. Cousins
 * share the site password (so the site-wide gate lets them in) but won't have this
 * URL, so the log stays Konyo-only. If VISITS_KEY isn't set the page is blocked
 * (404) to avoid accidentally exposing the log.
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

  // gather all visit entries (personal site → well under the 1000-key list cap)
  const list = await kv.list({ prefix: 'visit:' });
  const raw = await Promise.all(list.keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const visits = raw.filter(Boolean).sort((a, b) => (a.t < b.t ? 1 : -1)); // newest first

  const flag = (cc) => {
    if (!cc || cc.length !== 2) return '';
    const A = 0x1f1e6;
    return String.fromCodePoint(A + cc.toUpperCase().charCodeAt(0) - 65, A + cc.toUpperCase().charCodeAt(1) - 65);
  };
  const device = (ua) => {
    if (!ua) return 'unknown';
    let os = /Windows/.test(ua) ? 'Windows' : /iPhone|iPad|iOS/.test(ua) ? 'iOS' : /Mac OS X|Macintosh/.test(ua) ? 'Mac' : /Android/.test(ua) ? 'Android' : /Linux/.test(ua) ? 'Linux' : '?';
    let br = /Edg\//.test(ua) ? 'Edge' : /OPR\/|Opera/.test(ua) ? 'Opera' : /Chrome\//.test(ua) ? 'Chrome' : /Firefox\//.test(ua) ? 'Firefox' : /Safari\//.test(ua) ? 'Safari' : '?';
    return os + ' · ' + br;
  };
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  const rows = visits.map((v) => {
    const loc = [v.city, v.region].filter(Boolean).join(', ');
    const place = (flag(v.country) + ' ' + (loc || v.country || '?')).trim();
    return `<tr>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
      <td>${v.user ? esc(v.user) : '<span class="muted">—</span>'}</td>
      <td>${esc(place)}</td>
      <td class="mono">${esc(v.ip)}</td>
      <td>${esc(device(v.ua))}</td>
    </tr>`;
  }).join('');

  const today = visits.filter((v) => v.t.slice(0, 10) === (visits[0] ? visits[0].t.slice(0, 10) : '')).length;

  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Visit log · bull-4-u</title>
<style>
  :root{color-scheme:dark}
  body{margin:0;background:#14110c;color:#e9ddc4;font:15px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
  header{padding:20px 18px 8px;border-bottom:1px solid #3a3122}
  h1{margin:0 0 4px;font-size:20px;color:#d4af37}
  .sub{color:#9c8d6b;font-size:13px}
  .wrap{padding:14px 12px 40px;overflow-x:auto}
  table{border-collapse:collapse;width:100%;min-width:560px}
  th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #2a2418;white-space:nowrap}
  th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#9c8d6b;position:sticky;top:0;background:#1c180f}
  tr:hover td{background:#1f1a10}
  .mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:#c8bb98}
  .muted{color:#6b6149}
  .empty{padding:40px;text-align:center;color:#9c8d6b}
  .t{font-variant-numeric:tabular-nums}
</style></head><body>
<header>
  <h1>👁 Visit log</h1>
  <div class="sub">${visits.length} visit${visits.length === 1 ? '' : 's'} logged${visits.length ? ` · ${today} on the latest day` : ''} · auto-expires after 90 days · times shown in your local zone</div>
</header>
<div class="wrap">
${visits.length ? `<table>
  <thead><tr><th>When (local)</th><th>Login name</th><th>Location</th><th>IP</th><th>Device</th></tr></thead>
  <tbody>${rows}</tbody>
</table>` : '<div class="empty">No visits recorded yet. Load the app once and refresh this page.</div>'}
</div>
<script>
  // convert stored UTC ISO timestamps to the viewer's local time
  for (const el of document.querySelectorAll('td.t')) {
    const d = new Date(el.dataset.t);
    if (!isNaN(d)) el.textContent = d.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
  }
</script>
</body></html>`;

  return new Response(html, {
    headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' },
  });
}
