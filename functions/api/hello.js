/**
 * /api/hello — browser identity beacon (v1694).
 *
 * SCOPE — this is the OTHER half of the visit story. `functions/visits.js` (fed by
 * `recordVisit()` in `functions/_middleware.js`) sees every authenticated page-view of
 * /d2r/ but cannot say WHO — the Basic Auth username is decoded there yet ignored for
 * auth (any password-holder gets in on any username), so "one cousin on a phone and a
 * laptop counts twice, and several people behind one IP count as one" (that file's own
 * header). `functions/api/console.js` has REAL identity (`lastseen:<machine>`, 400d TTL)
 * but only ever hears from the TV DIABLO desktop app, never a browser.
 *
 * This endpoint is the board's browser-side beacon: bible.html calls it once per
 * page-load with a self-reported name/code (the same kind of "log in as 'cuz'" label the
 * middleware comment already invites), and it writes DURABLE per-person identity into the
 * same TZ_HISTORY KV the rest of the site uses — mirroring console.js's key discipline:
 *
 *   hvisitor:<id>          — DURABLE per-person record, TTL 400d, read-modify-write on
 *                            every beacon (first_seen kept, last_seen/count updated).
 *                            One key per PERSON — not per device — so the dashboard's
 *                            identity list can never fall out of a KV list() window the
 *                            way a growing per-hit log could; same reasoning as
 *                            console.js's `lastseen:`. 'hvisitor:' collides with no
 *                            existing prefix ('visit:', 'console:', 'consolelog:',
 *                            'lastseen:').
 *   hhit:<ISO-ts>:<rand>:<id>
 *                          — ONE ENTRY PER BEACON (i.e. per page-load), TTL 30d, read by
 *                            the dashboard only to draw the day-by-day shape of the last
 *                            30 days. There is deliberately NO rate limiting: at family
 *                            scale (~tens of loads a day) this is ~1k keys at steady
 *                            state, and `visits.js` walks `hhit:` with a paginated cursor
 *                            (20 pages) for exactly that reason, so it is never bounded by
 *                            KV's 1000-key-per-list() cap. The `<rand>` segment exists
 *                            because two loads inside the same millisecond would otherwise
 *                            overwrite each other — the same reason `visits.js` appends
 *                            `Math.random().toString(36).slice(2,8)` to its `visit:` keys.
 *
 * READ BY — `functions/visits.js` (the /visits?k=… dashboard) lists `hvisitor:` for the
 * per-person table and `hhit:` for each person's day bars. Its filters are
 * `v && v.id && v.last_seen` (identity) and `v && v.t && v.id` (hits); every field below
 * is written to satisfy them. If either prefix or either field name changes here, that
 * table silently renders EMPTY — it degrades rather than throwing — so the two files must
 * be changed together.
 *
 * ⚠ TWO DIFFERENT POPULATIONS — do not let a dashboard add these to one number. `visit:`
 * entries are IP/UA-inferred and count EVERY authenticated page-load, including people who
 * never typed a name. `hvisitor:`/`hhit:` entries only exist for people whose browser
 * actually beaconed here with a self-reported identity — a strict, usually smaller,
 * differently-biased subset. Label them separately wherever both are shown.
 *
 * ⚠ `count` IS A BEST-EFFORT LOWER BOUND, NOT A LEDGER. Workers KV has no atomic increment
 * and no read-your-writes guarantee (reads are edge-cached ~60s), so two page-loads close
 * together can both read the same prior value and both write prior+1 — an undercount, never
 * an overcount. It is the right number for "roughly how often does my cousin open this",
 * and the wrong number for anything that must balance. The per-day `hhit:` entries are
 * independent of it (unique keys, no read-modify-write) and are the more trustworthy signal
 * inside the 30-day window.
 *
 * AUTH — this route is NOT in the `_middleware.js` unauthenticated allowlist (that's only
 * `/api/tz` and the two TV-D installer scripts), so it sits behind the same site-wide HTTP
 * Basic gate as every other /api route. It is not a public write endpoint: an anonymous
 * caller on the internet gets a 401 from the gate before this code ever runs. bible.html
 * calls it same-origin, so the browser auto-sends the already-entered credentials, same as
 * /api/intake does today. CAVEAT, pre-existing and site-wide (not this ship's doing): that
 * gate is FAIL-OPEN — `_middleware.js` returns `next()` when `SITE_PASS` is unset — so the
 * protection holds only while that secret is configured, which it is today.
 */

const ID_TTL = 60 * 60 * 24 * 400;   // 400 days — match console.js's lastseen: durability
const HIT_TTL = 60 * 60 * 24 * 30;   // 30 days — match console.js's consolelog: window

// A password-holder could otherwise mint unlimited 400-day identity keys just by typing a
// new label. Creating a NEW identity is the only path that checks this (one extra list()
// on first sight of a label, never on a returning visitor), so the steady-state beacon
// still costs exactly one get + two puts.
const MAX_IDENTITIES = 64;

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return json({ ok: false, error: 'storage unavailable' }, 500);

  // Never trust the body's declared or actual length — cap what we read before parsing.
  let raw = '';
  try { raw = await request.text(); } catch (e) { raw = ''; }
  if (raw.length > 4096) raw = raw.slice(0, 4096);

  let body = {};
  try { body = JSON.parse(raw || '{}'); } catch (e) { body = {}; }
  if (!body || typeof body !== 'object' || Array.isArray(body)) body = {};

  const name = String(body.name || '').slice(0, 40).trim();
  const code = String(body.code || '').slice(0, 24).trim();
  const machine = String(body.machine || '').slice(0, 40).replace(/[^\w.-]/g, '_');
  // bible.html's `window._D2R_INSTALL` UUID. NOT the storage key (that is the person, so a
  // phone and a laptop collapse into one row — the whole complaint this ship answers), but
  // kept on the record so a row can still be joined back to a specific install, and to
  // console.js's `lastseen:<machine>`, later.
  const install = String(body.id || '').slice(0, 64).replace(/[^\w-]/g, '');
  const ver = String(body.ver || '').slice(0, 12);

  // Identity = whatever the person actually typed (code preferred, then name), never the
  // IP or UA — that is the entire point of this endpoint. No identity, no write: silently
  // acking an anonymous beacon would let it masquerade as a durable person record.
  const label = (code || name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  if (!label) return json({ ok: true, skipped: 'no identity' });
  const id = label.slice(0, 40);

  const cf = request.cf || {};
  const now = new Date().toISOString();

  const idKey = 'hvisitor:' + id;
  let prior = null;
  try { prior = await kv.get(idKey, 'json'); } catch (e) { prior = null; }

  if (!prior) {
    let known = 0;
    try {
      const page = await kv.list({ prefix: 'hvisitor:', limit: MAX_IDENTITIES + 1 });
      known = ((page && page.keys) || []).length;
    } catch (e) { known = 0; }
    if (known >= MAX_IDENTITIES) return json({ ok: true, skipped: 'identity cap' });
  }

  const rec = {
    id,
    name: name || (prior && prior.name) || '',
    code: code || (prior && prior.code) || '',
    machine: machine || (prior && prior.machine) || '',
    install: install || (prior && prior.install) || '',
    ver: ver || (prior && prior.ver) || '',
    first_seen: (prior && prior.first_seen) || now,
    last_seen: now,
    count: ((prior && Number(prior.count)) || 0) + 1,   // best-effort lower bound, see header
    country: cf.country || (prior && prior.country) || '',
    city: cf.city || (prior && prior.city) || '',
  };

  await kv.put(idKey, JSON.stringify(rec), { expirationTtl: ID_TTL });

  // Per-hit entry for day-by-day aggregation — deliberately tiny (no UA/IP duplication, the
  // durable record above already has the person's shape). 'hhit:' cannot collide with
  // 'hvisitor:' (different literal prefixes), and the random segment keeps two loads in the
  // same millisecond from overwriting one another.
  const rand = Math.random().toString(36).slice(2, 8);
  await kv.put('hhit:' + now + ':' + rand + ':' + id, JSON.stringify({ t: now, id }), {
    expirationTtl: HIT_TTL,
  });

  return json({ ok: true, id, first_seen: rec.first_seen, count: rec.count });
}

// A GET writes NOTHING. It exists so the endpoint can be proved reachable from a browser
// (behind the same Basic gate) without minting an identity or inflating anyone's count.
export async function onRequestGet(context) {
  const kv = context && context.env && context.env.TZ_HISTORY;
  return json({ ok: true, endpoint: 'hello', writes: 'POST only', storage: kv ? 'ready' : 'unavailable' });
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}
