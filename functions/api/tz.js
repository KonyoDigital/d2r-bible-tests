/**
 * /api/tz — live Terror Zone proxy + 48h history recorder for the bible.
 *
 * The bible is a static page; it can't read d2runewizard directly (no CORS) and
 * diablo2.io bot-guards automated reads. So this Pages Function fetches the
 * tokenless d2runewizard JSON server-side and re-serves it same-origin.
 *
 * It also RECORDS each rotation into a Cloudflare KV ring buffer (TZ_HISTORY),
 * deduped by 30-min slot, kept for 48h — so the tab can show a complete history
 * even for slots no browser was watching. Konyo's Telegram alert bot pings this
 * endpoint every 5 min, so the log fills 24/7 regardless of web visits.
 *
 * Returns: { current, next, ts, history:[{slot,zone}, …newest-first] }
 */

const CORS = {
  'Access-Control-Allow-Origin': 'https://bull-4-u.com',   // v697.1 — private tool: origin-locked (was *)
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};
const SRC = 'https://d2runewizard.com/api/trackers/terror-zone';
const SLOT_MS = 30 * 60 * 1000;        // TZ rotates every 30 min
const KEEP_MS = 48 * 60 * 60 * 1000;   // keep 48h
const HKEY = 'history';

function json(body, status = 200, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'public, max-age=30',
      ...CORS,
      ...extra,
    },
  });
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestGet(context) {
  const kv = context.env && context.env.TZ_HISTORY;

  // 1) live current/next from d2runewizard
  let cur = '', nxt = '';
  try {
    const r = await fetch(SRC, {
      headers: {
        'User-Agent': 'KonyoD2RBible/1.0 (+https://bull-4-u.com/d2r/)',
        Accept: 'application/json',
      },
      cf: { cacheTtl: 25, cacheEverything: true },
    });
    if (r.ok) {
      const d = await r.json();
      cur = (typeof d.current === 'string' && d.current) || (d.currentTerrorZone && d.currentTerrorZone.zone) || '';
      nxt = (typeof d.next === 'string' && d.next) || (d.nextTerrorZone && d.nextTerrorZone.zone) || '';
    }
  } catch (e) { /* fall through — history may still serve */ }

  // 2) record + read the 48h history from KV
  let history = [];
  if (kv) {
    try {
      const raw = await kv.get(HKEY);
      history = raw ? JSON.parse(raw) : [];
    } catch (e) { history = []; }

    if (cur) {
      const now = Date.now();
      const slot = Math.floor(now / SLOT_MS) * SLOT_MS;
      const latest = history[0];
      let dirty = false;
      if (!latest || latest.slot !== slot) {
        history.unshift({ slot, zone: cur });
        dirty = true;
      } else if (latest.zone !== cur) {
        latest.zone = cur;     // same slot, corrected zone
        dirty = true;
      }
      if (dirty) {
        history = history
          .filter((h) => h.slot >= now - KEEP_MS)
          .sort((a, b) => b.slot - a.slot)
          .slice(0, 120);
        try { await kv.put(HKEY, JSON.stringify(history)); } catch (e) { /* best effort */ }
      }
    }
  }

  if (!cur && !history.length) return json({ error: 'unavailable' }, 502);
  return json({ current: cur, next: nxt, ts: Date.now(), history });
}
