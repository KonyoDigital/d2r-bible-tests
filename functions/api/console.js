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
    // v1496 — the FRIENDLY name Konyo gave this machine in its console ("Konyo's MacBook").
    // The hostname stays as the technical fallback; a nickname is what he actually reads.
    nickname: String(body.nickname || '').slice(0, 40),
    install: String(body.install || '').slice(0, 12),
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

/**
 * v1496 — GET /api/console → the fleet as JSON: who is online now and when each machine was last
 * seen. Konyo: "i want to have a tracker for whose logged in and when.. like we have for the
 * website." /console (the HTML page) already answered that in a browser tab behind a key; this
 * lets the console app itself answer it, so the machine he is sitting at can show its own fleet.
 * Same Basic gate as every other /api route (the app already authenticates for the beacon), and
 * strictly read-only.
 */
export async function onRequestGet(context) {
  const { env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return json({ ok: false, error: 'storage unavailable' }, 500);

  // v1496 — CI runners used to check in from every test job, so the fleet listed a GitHub VM in
  // Boydton beside Konyo's MacBook. The beacon no longer sends from CI, but entries already in KV
  // (and any older build still running) are filtered here too — belt and braces, because the answer
  // to "who is online" must only ever contain machines that are his.
  const isRunner = (m) => /^runnervm|^fv-az|^runner-/i.test(String((m && m.machine) || ''));
  const live = await kv.list({ prefix: 'console:' });
  const recs = await Promise.all(live.keys.map((k) => kv.get(k.name, 'json').catch(() => null)));
  const machines = recs.filter(Boolean).filter((m) => !isRunner(m)).sort((a, b) => (a.t < b.t ? 1 : -1));

  // last-seen for machines whose presence key has EXPIRED (offline) — read from the event log,
  // so a machine that has been off for a week still says when it was last here instead of vanishing.
  const logList = await kv.list({ prefix: 'consolelog:', limit: 400 });
  const logs = (await Promise.all(logList.keys.map((k) => kv.get(k.name, 'json').catch(() => null))))
    .filter(Boolean)
    .sort((a, b) => (a.t < b.t ? 1 : -1));
  const seen = new Set(machines.map((m) => m.machine));
  const offline = [];
  for (const l of logs) {
    if (isRunner(l)) continue;
    if (seen.has(l.machine)) continue;
    seen.add(l.machine);
    offline.push({ ...l, offline: true });
  }
  return json({ ok: true, now: new Date().toISOString(), online: machines, offline });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}
