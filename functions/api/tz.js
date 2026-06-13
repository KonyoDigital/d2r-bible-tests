/**
 * /api/tz — live Terror Zone proxy for the bible's TZ TRACKER tab.
 *
 * The bible is a static page; it cannot read d2runewizard directly (that API
 * sends no CORS headers), and diablo2.io bot-guards automated reads. So this
 * Pages Function fetches the tokenless d2runewizard JSON server-side (same
 * region-wide D2R rotation) and re-serves it same-origin with CORS + a short
 * cache. Returns: { current, next, ts }  (zone name strings + fetch epoch ms).
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const SRC = 'https://d2runewizard.com/api/trackers/terror-zone';

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'public, max-age=60',
      ...CORS,
      ...extra,
    },
  });
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestGet(context) {
  try {
    const r = await fetch(SRC, {
      headers: {
        'User-Agent': 'KonyoD2RBible/1.0 (+https://bull-4-u.com/d2r/)',
        Accept: 'application/json',
      },
      // edge-cache the upstream so we never hammer d2runewizard
      cf: { cacheTtl: 30, cacheEverything: true },
    });
    if (!r.ok) return json({ error: 'upstream', status: r.status }, 502);
    const d = await r.json();
    const cur =
      (typeof d.current === 'string' && d.current) ||
      (d.currentTerrorZone && d.currentTerrorZone.zone) ||
      '';
    const nxt =
      (typeof d.next === 'string' && d.next) ||
      (d.nextTerrorZone && d.nextTerrorZone.zone) ||
      '';
    return json({ current: cur, next: nxt, ts: Date.now() });
  } catch (e) {
    return json({ error: 'fetch', detail: String(e).slice(0, 200) }, 502);
  }
}
