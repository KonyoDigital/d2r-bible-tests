/**
 * /console — private CONSOLE-APP dashboard for Konyo (v875).
 *
 * The console twin of /visits: shows every TV DIABLO console (Mac, Windows,
 * cousins) that is ONLINE RIGHT NOW (presence = console:<machine> KV key alive,
 * 10-min TTL fed by the app's beacon) plus the recent boot / ON AIR event log.
 *
 * ACCESS: ?k=<VISITS_KEY> — same secret as /visits; without it the page 404s.
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

  const online = await kv.list({ prefix: 'console:' });
  const now = await Promise.all(online.keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const live = now.filter(Boolean).sort((a, b) => (a.t < b.t ? 1 : -1));

  const logList = await kv.list({ prefix: 'consolelog:', limit: 400 });
  const logRaw = await Promise.all(logList.keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const log = logRaw.filter(Boolean).sort((a, b) => (a.t < b.t ? 1 : -1)).slice(0, 120);

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

  const liveRows = live.map((v) => `<tr>
      <td><b>${esc(v.machine)}</b>${v.user ? ' <span class="muted">(' + esc(v.user) + ')</span>' : ''}</td>
      <td>${esc(v.platform)} · ${esc(v.ver)}</td>
      <td>${modeBadge(v.mode)}</td>
      <td>${v.reads ? esc(v.reads) + ' reads' : '<span class="muted">—</span>'}</td>
      <td>${(flag(v.country) + ' ' + (v.city || v.country || '')).trim()}</td>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
    </tr>`).join('');

  const logRows = log.map((v) => `<tr>
      <td class="t" data-t="${esc(v.t)}">${esc(v.t)}</td>
      <td><b>${esc(v.machine)}</b></td>
      <td>${esc(v.event)}</td>
      <td>${esc(v.platform)} · ${esc(v.ver)}</td>
      <td>${modeBadge(v.mode)}</td>
    </tr>`).join('');

  const html = `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🖥 TV DIABLO — console dashboard</title>
<style>
  :root{color-scheme:dark}
  body{background:#0b0a08;color:#e8ddc8;font:14px/1.5 ui-monospace,Menlo,monospace;margin:24px;max-width:1100px}
  h1{font-size:18px;color:#f0c060} h2{font-size:14px;color:#c9b483;margin-top:28px}
  table{border-collapse:collapse;width:100%;margin-top:10px}
  td,th{padding:6px 10px;border-bottom:1px solid #2a2418;text-align:left;vertical-align:top}
  th{color:#8f7f66;font-weight:normal;font-size:12px;letter-spacing:.08em}
  .muted{color:#6d6353}.mono{font-family:inherit;font-size:12px;color:#9a8d73}
  .b{padding:1px 8px;border-radius:9px;border:1px solid #3a3222;font-size:12px}
  .b.on{color:#ff6a5e;border-color:#7a2e28;background:#2a120f}
  .b.sim{color:#b9a5ff;border-color:#4a3d7a}
  .b.off{color:#8d8370}
  .empty{color:#6d6353;padding:18px 4px}
</style></head><body>
<h1>🖥 TV DIABLO — console dashboard</h1>
<div class="muted">consoles seen in the last 10 minutes are ONLINE · beacon every ~4 min · log keeps 30 days of boots + ON AIR flips</div>
<h2>🟢 online now (${live.length})</h2>
<table><tr><th>machine</th><th>build</th><th>mode</th><th>session</th><th>where</th><th>last beacon</th></tr>
${liveRows || '<tr><td colspan="6" class="empty">no console online right now</td></tr>'}</table>
<h2>📜 recent events</h2>
<table><tr><th>when</th><th>machine</th><th>event</th><th>build</th><th>mode</th></tr>
${logRows || '<tr><td colspan="5" class="empty">no events yet</td></tr>'}</table>
<script>
  document.querySelectorAll('.t').forEach(function(td){
    var d = new Date(td.dataset.t);
    if (!isNaN(d)) td.textContent = d.toLocaleString();
  });
</script>
</body></html>`;
  return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } });
}
