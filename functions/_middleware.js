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

  const SECRET = env && env.SITE_PASS;
  if (!SECRET) return next(); // not configured yet → don't lock anyone out

  const header = request.headers.get('Authorization') || '';
  if (header.startsWith('Basic ')) {
    let decoded = '';
    try { decoded = atob(header.slice(6)); } catch (e) { decoded = ''; }
    const pass = decoded.slice(decoded.indexOf(':') + 1); // ignore username, check password only
    if (pass === SECRET) return next();
  }

  return new Response('🔒 Konyo’s D2R Bible — password required.', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Konyo D2R Bible", charset="UTF-8"',
      'content-type': 'text/plain; charset=utf-8',
    },
  });
}
