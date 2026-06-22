/**
 * Site-wide HTTP Basic Auth gate (Konyo + cousins, private personal tool).
 *
 * Runs on EVERY request to the Pages project. Only the PASSWORD matters — any
 * username is accepted — so there's a single secret to share. The password lives
 * in the Cloudflare env var SITE_PASS (a secret, never in the repo); if it's not
 * set the gate is OPEN (fail-safe so a missing secret never locks the site out).
 *
 * EXCEPTION: /api/tz is left open so the Telegram alert bot's 5-min recorder ping
 * (which sends no credentials) keeps the 48h history filling 24/7, and the public
 * TZ data stays reachable. Everything else — the bible, art, /api/intake — is gated.
 * The bible page calls /api/intake same-origin, so the browser auto-sends the
 * logged-in credentials; only outside visitors are blocked.
 *
 * VISIT LOG (2026-06-22): every authenticated load of the app page is recorded to
 * the TZ_HISTORY KV store under a `visit:` key (time, IP, city/country, device,
 * login name). View it at /visits?k=<VISITS_KEY>. Logging is best-effort and fully
 * wrapped — it can never delay or block a response (see recordVisit()).
 */
export async function onRequest(context) {
  const { request, env, next } = context;
  const url = new URL(request.url);

  // the app lives under /d2r/ — send the bare domain (and /index.html) there so a
  // bookmark of the plain host lands on the app instead of a blank 404.
  if (url.pathname === '/' || url.pathname === '/index.html') {
    return Response.redirect(url.origin + '/d2r/', 308);
  }

  // bot recorder + public TZ endpoint: always open
  if (url.pathname === '/api/tz') return next();

  // decode the Basic Auth username — ignored for AUTH, but recorded so Konyo can
  // label who's who (tell a cousin to log in as e.g. "cuz" and visits show it).
  let user = '';
  const header = request.headers.get('Authorization') || '';
  if (header.startsWith('Basic ')) {
    try { const d = atob(header.slice(6)); user = d.slice(0, d.indexOf(':')); } catch (e) { /* ignore */ }
  }

  const SECRET = env && env.SITE_PASS;
  if (!SECRET) {                       // not configured yet → don't lock anyone out
    recordVisit(context, url, user);
    return next();
  }

  if (header.startsWith('Basic ')) {
    let decoded = '';
    try { decoded = atob(header.slice(6)); } catch (e) { decoded = ''; }
    const pass = decoded.slice(decoded.indexOf(':') + 1); // ignore username, check password only
    if (pass === SECRET) {
      recordVisit(context, url, user);
      return next();
    }
  }

  return new Response('🔒 Konyo’s D2R Bible — password required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Konyo D2R Bible", charset="UTF-8"',
      'content-type': 'text/plain; charset=utf-8',
    },
  });
}

/**
 * Best-effort visit recorder. Logs ONLY real loads of the app page (not every art
 * asset / api call), GET only. Any failure is swallowed; the KV write runs in
 * waitUntil so it never adds latency to the user's response.
 */
function recordVisit(context, url, user) {
  try {
    const { request, env } = context;
    if (request.method !== 'GET') return;
    const p = url.pathname;
    if (p !== '/d2r/' && p !== '/d2r/index.html') return; // one log per app page-view
    const kv = env && env.TZ_HISTORY;
    if (!kv) return;

    const cf = request.cf || {};
    const entry = {
      t: new Date().toISOString(),
      user: user || '',
      ip: request.headers.get('CF-Connecting-IP') || '',
      country: cf.country || request.headers.get('CF-IPCountry') || '',
      city: cf.city || '',
      region: cf.region || '',
      ua: request.headers.get('User-Agent') || '',
      ref: request.headers.get('Referer') || '',
    };
    const key = 'visit:' + Date.now() + ':' + Math.random().toString(36).slice(2, 8);
    // keep 90 days, then auto-expire so the log can't grow unbounded
    context.waitUntil(kv.put(key, JSON.stringify(entry), { expirationTtl: 7776000 }).catch(() => {}));
  } catch (e) { /* never let logging break the gate */ }
}
