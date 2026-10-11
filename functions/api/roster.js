/**
 * POST /api/roster — Fleet 3.0 phase 1, the publish only.
 *
 * This is not the presence beacon. functions/api/console.js keeps its own keys
 * (console:, lastseen:) and its own law: no item name crosses that beacon.
 * A roster row is a different route and a different key, `roster:` plus the
 * owner label (Konyo · Mac, Konyo · ALT, Konyo · GrokBot, Dean, Wife PC).
 * An install id, a hostname, or a path is not a key.
 *
 * Presence is already budgeted at 768 of 1,000 KV writes a day. This route
 * adds at most 4 PCs times 25 writes (868 together). Five labels exist so a
 * row can be named; five PCs at this cap would be 893, still under 1,000.
 * One key per owner, rewritten only when the body changed, at most once an
 * hour, plus one boot publish inside that hour. The 26th write of the UTC
 * day is refused out loud. A refusal is HTTP 200 with ok:false, never a 500
 * that looks like the machine went offline.
 *
 * A section that was not in this body stays as it was, or stays absent.
 * It is never stored as an empty list. Pictures and frame bytes are refused
 * and not stored. GET /api/roster reads the five owner keys and writes nothing.
 * No Roster tab, no D1, no R2.
 */

const PRESENCE_WRITES = 768;
const ROSTER_PCS = 4;
const ROSTER_CAP = 25;
const KV_WRITES = 1000;
const HOUR_MS = 3600 * 1000;
const TTL_S = 60 * 60 * 24 * 400;

const OWNERS = ["Konyo · Mac", "Konyo · ALT", "Konyo · GrokBot", "Dean", "Wife PC"];
const SECTIONS = ["characters", "vault", "stash", "owned", "chronicle", "reels"];

const QUOTA_WHY = "roster would not take this publish: quota";
const REFUSAL_HINT = "this is the storage refusing a write, NOT the machine being absent";
const MAX_BODY = 80000;

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

function refuse(why) {
  return json({ ok: false, why: why, hint: REFUSAL_HINT }, 200);
}

function dayOf(ms) {
  return new Date(ms).toISOString().slice(0, 10);
}

function hashOf(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

function stable(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
  const keys = Object.keys(v).sort();
  return "{" + keys.map((k) => JSON.stringify(k) + ":" + stable(v[k])).join(",") + "}";
}

function dirtyString(s) {
  const low = String(s).toLowerCase();
  if (low.indexOf("data:image") !== -1 || low.indexOf("base64,") !== -1) return true;
  if (/\.(jpg|jpeg|png|gif|webp)(\b|$)/i.test(s)) return true;
  if (s.length > 400) return true;
  return false;
}

function dirty(v) {
  if (typeof v === "string") return dirtyString(v);
  if (Array.isArray(v)) return v.some(dirty);
  if (v && typeof v === "object") {
    return Object.keys(v).some((k) => dirtyString(k) || dirty(v[k]));
  }
  return false;
}

function shapeSection(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  const asOf = raw.asOf;
  if (typeof asOf !== "number" || !Number.isFinite(asOf) || asOf <= 0) return null;
  const out = { asOf: asOf };
  if (typeof raw.counts === "number" && Number.isFinite(raw.counts) && raw.counts >= 0) {
    out.counts = raw.counts;
  } else if (raw.counts && typeof raw.counts === "object" && !Array.isArray(raw.counts)) {
    const counts = {};
    for (const k of Object.keys(raw.counts)) {
      const v = raw.counts[k];
      if (dirtyString(k)) continue;
      if (typeof v === "number" && Number.isFinite(v) && v >= 0) counts[k] = v;
      else if (v && typeof v === "object" && !Array.isArray(v)) {
        const pair = {};
        if (typeof v.have === "number" && v.have >= 0) pair.have = v.have;
        if (typeof v.total === "number" && v.total > 0) pair.total = v.total;
        if (Object.keys(pair).length) counts[k] = pair;
      }
    }
    if (Object.keys(counts).length) out.counts = counts;
  }
  if (Array.isArray(raw.rows) && raw.rows.length) out.rows = raw.rows;
  if (!("counts" in out) && !("rows" in out)) return null;
  return out;
}

function forHash(sections) {
  const o = {};
  for (const name of Object.keys(sections).sort()) {
    const sec = sections[name];
    const c = {};
    for (const k of Object.keys(sec).sort()) {
      if (k === "asOf" || k === "hash") continue;
      c[k] = sec[k];
    }
    o[name] = c;
  }
  return hashOf(stable(o));
}

function priorSections(prev) {
  const out = {};
  const s = prev && prev.sections;
  if (!s || typeof s !== "object" || Array.isArray(s)) return out;
  for (const name of SECTIONS) {
    const sec = s[name];
    if (!sec || typeof sec !== "object" || Array.isArray(sec)) continue;
    const copy = {};
    for (const k of Object.keys(sec)) {
      if (k === "rows" && Array.isArray(sec[k]) && sec[k].length === 0) continue;
      copy[k] = sec[k];
    }
    if (Object.keys(copy).length) out[name] = copy;
  }
  return out;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return refuse("roster would not take this publish: storage unavailable");

  let text = "";
  try { text = await request.text(); } catch (e) { text = ""; }
  if (text.length > MAX_BODY) {
    return refuse("roster would not take this publish: the body is too large to be rows");
  }
  let body;
  try { body = JSON.parse(text || "{}"); } catch (e) {
    return refuse("roster would not take this publish: the body was not JSON");
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return refuse("roster would not take this publish: the body was not a record");
  }

  const owner = body.owner;
  if (OWNERS.indexOf(owner) === -1) {
    return refuse("roster would not take this publish: the key is an owner label, not a machine");
  }
  if (dirty(body)) {
    return refuse("roster would not take this publish: pictures stay on that PC");
  }

  const shaped = {};
  const incoming = (body.sections && typeof body.sections === "object") ? body.sections : {};
  for (const name of SECTIONS) {
    if (!Object.prototype.hasOwnProperty.call(incoming, name)) continue;
    const sec = shapeSection(incoming[name]);
    if (sec) shaped[name] = sec;
  }

  const key = "roster:" + owner;
  let prev = null;
  try {
    const raw = await kv.get(key);
    prev = raw ? JSON.parse(raw) : null;
  } catch (e) { prev = null; }
  if (!prev || typeof prev !== "object" || prev.owner !== owner) prev = null;

  const sections = Object.assign(priorSections(prev), shaped);
  const now = Date.now();
  const hash = forHash(sections);
  const boot = body.boot === true;

  if (!Object.keys(sections).length) {
    return json({ ok: true, owner: owner, stored: [], skipped: ["nothing read"] }, 200);
  }
  if (prev && prev.hash === hash) {
    return json({ ok: true, owner: owner, stored: [], skipped: ["unchanged"] }, 200);
  }
  const age = prev && typeof prev.t === "number" ? (now - prev.t) : HOUR_MS;
  if (prev && age < HOUR_MS && !boot) {
    return json({ ok: true, owner: owner, stored: [], skipped: ["within the hour"] }, 200);
  }

  const today = dayOf(now);
  const n = (prev && prev.day === today && typeof prev.n === "number") ? prev.n : 0;
  if (n >= ROSTER_CAP) {
    return json({ ok: false, why: QUOTA_WHY, hint: REFUSAL_HINT }, 200);
  }

  const rec = { owner: owner, t: now, day: today, n: n + 1, hash: hash, sections: sections };
  try {
    await kv.put(key, JSON.stringify(rec), { expirationTtl: TTL_S });
  } catch (e) {
    return refuse("roster would not take this publish: " + String((e && e.message) || e).slice(0, 140));
  }
  return json({ ok: true, owner: owner, stored: ["roster"], key: key }, 200);
}

export async function onRequestGet(context) {
  const kv = context.env && context.env.TZ_HISTORY;
  if (!kv) return refuse("roster would not take this fetch: storage unavailable");
  const owners = [];
  for (const owner of OWNERS) {
    let raw = null;
    try {
      raw = await kv.get("roster:" + owner);
    } catch (e) {
      return refuse("roster would not take this fetch: " + String((e && e.message) || e).slice(0, 140));
    }
    let prev = null;
    try { prev = raw ? JSON.parse(raw) : null; } catch (e) { prev = null; }
    if (!prev || typeof prev !== "object" || prev.owner !== owner) {
      owners.push({ owner: owner, published: false });
      continue;
    }
    const sections = priorSections(prev);
    const hash = forHash(sections);
    if (prev.hash !== hash) {
      owners.push({ owner: owner, published: true, corrupt: true, t: prev.t });
      continue;
    }
    const row = { owner: owner, published: true, corrupt: false, t: prev.t, hash: hash };
    if (Object.keys(sections).length) row.sections = sections;
    owners.push(row);
  }
  return json({ ok: true, owners: owners }, 200);
}
