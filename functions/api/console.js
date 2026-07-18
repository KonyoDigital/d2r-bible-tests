/**
 * /api/console — console-app presence beacon (v875).
 *
 * The TV DIABLO control app (Mac + Windows + cousins) POSTs here on boot, on
 * ON AIR / OFF transitions, and every ~4 min as a heartbeat. Storage reuses the
 * TZ_HISTORY KV:
 *   console:<machine>        — CURRENT state, TTL 10 min → key alive ⇔ console online
 *   consolelog:<ts>:<machine> — event log entries (boot/onair/off only, no heartbeats)
 *
 * Auth: sits behind the site-wide Basic gate (_middleware) like every /api route.
 * View at /console?k=<VISITS_KEY> — Konyo-only, same key as /visits.
 */
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
    reads: Number(body.reads || 0) || 0,
    ip: request.headers.get('CF-Connecting-IP') || '',
    country: cf.country || '',
    city: cf.city || '',
  };

  // presence: alive key = online console (TTL 10 min ≈ 2 missed heartbeats)
  await kv.put('console:' + machine, JSON.stringify(rec), { expirationTtl: 600 });

  // event log: boots and mode flips only — heartbeats would bloat the KV
  if (event !== 'hb') {
    await kv.put('consolelog:' + rec.t + ':' + machine, JSON.stringify(rec), {
      expirationTtl: 60 * 60 * 24 * 30,   // 30 days of history
    });
  }
  return json({ ok: true });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}
