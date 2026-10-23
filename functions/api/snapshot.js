// Shadow mode - one console's account stores, uploaded so another console can show them read only.
//
// POST: the body {owner, boot, signedAt, hash, stores} that tv/console_snapshot.py builds, signed with the
// key already registered for that owner by a roster publish (X-Roster-Key / X-Roster-Sig over these exact
// bytes). This endpoint never registers a key: an owner without one, an unsigned body, or another key is
// refused before any write. Change-only, at most once per MIN_GAP_MS unless it is the boot post, and at most
// DAY_CAP writes per owner per day: 4 PCs x 20 = 80, beside presence 768 + roster 100 = 948 of the 1000 KV
// writes a day. Refusals are HTTP 200 {ok:false, why}, as roster's are.
//
// GET ?owner=: that owner's last upload, read only. The stores' hash is checked on the way out; a record
// that does not match its own hash is served as corrupt, never as stores.

import { OWNERS, hashOf, stable, signatureOf, intentOf } from "./roster.js";

const MAX_BODY = 200000;
const DAY_CAP = 20;
const MIN_GAP_MS = 30 * 60 * 1000;
const TTL_S = 60 * 60 * 24 * 400;
const KEY_PREFIX = "rosterkey:";
const STORE_NAME = /^d2r_[A-Za-z0-9_]{1,60}$/;
const HINT = "this is the storage refusing a write, NOT the machine being absent";

function json(obj) {
  return new Response(JSON.stringify(obj), {
    status: 200,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function refuse(why, extra) {
  return json(Object.assign({ ok: false, why: "snapshot would not take this upload: " + why, hint: HINT }, extra || {}));
}

function dayOf(ms) {
  return new Date(ms).toISOString().slice(0, 10);
}

export function storesOk(stores) {
  if (!stores || typeof stores !== "object" || Array.isArray(stores)) return false;
  const names = Object.keys(stores);
  if (!names.length) return false;
  return names.every((k) => STORE_NAME.test(k) && typeof stores[k] === "string");
}

export function hashOfStores(stores) {
  return hashOf(stable(stores));
}

async function registeredOf(kv, owner) {
  const held = await kv.get(KEY_PREFIX + owner);
  if (!held) return null;
  let registered;
  try { registered = JSON.parse(held); } catch (e) { registered = { pub: String(held).trim() }; }
  if (typeof registered === "string") registered = { pub: registered };
  if (!registered || typeof registered !== "object") registered = { pub: null };
  return registered;
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return refuse("storage unavailable");
  let bytes = new Uint8Array(0);
  try { bytes = new Uint8Array(await request.arrayBuffer()); } catch (e) { bytes = new Uint8Array(0); }
  if (bytes.byteLength > MAX_BODY) return refuse("the body is larger than " + MAX_BODY + " bytes");
  const sig = await signatureOf(request, bytes);
  let body;
  try { body = JSON.parse(new TextDecoder("utf-8").decode(bytes) || "{}"); } catch (e) {
    return refuse("the body was not JSON");
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) return refuse("the body was not a record");
  const owner = body.owner;
  if (OWNERS.indexOf(owner) === -1) return refuse("the key is an owner label, not a machine");

  let registered;
  try { registered = await registeredOf(kv, owner); } catch (e) {
    return refuse("the key registered for this owner could not be read");
  }
  // A snapshot never registers a key: the roster publish is the one place trust is first given.
  if (registered === null) return refuse(owner + " has no registered roster key yet; a signed roster publish registers it");
  const intent = intentOf(owner, registered, sig);
  if (intent.refused || intent.verified !== true || intent.register) {
    const out = { sig: sig.state };
    if (intent.registeredKeyId) out.keyId = intent.registeredKeyId;
    if (sig.keyId) out.offered = sig.keyId;
    return refuse(intent.refused || "this upload was not signed by " + owner + "'s registered key", out);
  }

  const stores = body.stores;
  if (!storesOk(stores)) return refuse("stores must be d2r_ names holding strings");
  const low = JSON.stringify(stores).toLowerCase();
  if (low.indexOf("data:image") !== -1 || low.indexOf("base64,") !== -1) return refuse("pictures stay on that PC");
  const hash = hashOfStores(stores);
  if (body.hash !== hash) return refuse("the stores do not match the hash that was signed");

  const key = "snapshot:" + owner;
  let prev = null;
  try {
    const raw = await kv.get(key);
    prev = raw ? JSON.parse(raw) : null;
  } catch (e) { prev = null; }
  if (!prev || typeof prev !== "object" || prev.owner !== owner) prev = null;

  const now = Date.now();
  const said = { intentVerified: true, sig: sig.state, keyId: intent.keyId };
  const samePub = !!prev && prev.pub === sig.pub;
  if (prev && prev.hash === hash && samePub) {
    return json(Object.assign({ ok: true, owner: owner, stored: [], skipped: ["unchanged"] }, said));
  }
  const age = prev && typeof prev.t === "number" ? now - prev.t : MIN_GAP_MS;
  if (prev && samePub && age < MIN_GAP_MS && body.boot !== true) {
    return json(Object.assign({ ok: true, owner: owner, stored: [], skipped: ["within 30 min"] }, said));
  }
  const today = dayOf(now);
  const n = prev && prev.day === today && typeof prev.n === "number" ? prev.n : 0;
  if (n >= DAY_CAP) return refuse("quota: " + DAY_CAP + " uploads a day for " + owner);
  const rec = { owner: owner, t: now, day: today, n: n + 1, hash: hash, stores: stores,
                intentVerified: true, keyId: intent.keyId, pub: sig.pub };
  if (typeof body.signedAt === "number" && Number.isFinite(body.signedAt)) rec.signedAt = body.signedAt;
  try {
    await kv.put(key, JSON.stringify(rec), { expirationTtl: TTL_S });
  } catch (e) {
    return refuse(String((e && e.message) || e).slice(0, 140));
  }
  return json(Object.assign({ ok: true, owner: owner, stored: ["snapshot"], key: key }, said));
}

export async function onRequestGet(context) {
  const kv = context.env && context.env.TZ_HISTORY;
  if (!kv) return json({ ok: false, why: "snapshot could not be read: storage unavailable" });
  let owner = null;
  try { owner = new URL(context.request.url).searchParams.get("owner"); } catch (e) { owner = null; }
  if (OWNERS.indexOf(owner) === -1) return json({ ok: false, why: "ask for one of the five owner labels" });
  let prev = null;
  try {
    const raw = await kv.get("snapshot:" + owner);
    prev = raw ? JSON.parse(raw) : null;
  } catch (e) {
    return json({ ok: false, why: "snapshot could not be read: " + String((e && e.message) || e).slice(0, 140) });
  }
  if (!prev || typeof prev !== "object" || prev.owner !== owner) {
    return json({ ok: true, owner: owner, published: false });
  }
  if (!storesOk(prev.stores) || prev.hash !== hashOfStores(prev.stores)) {
    return json({ ok: true, owner: owner, published: true, corrupt: true, t: prev.t });
  }
  const out = { ok: true, owner: owner, published: true, corrupt: false, t: prev.t, hash: prev.hash,
                stores: prev.stores, intentVerified: prev.intentVerified === true };
  if (typeof prev.keyId === "string" && /^[0-9a-f]{12}$/.test(prev.keyId)) out.keyId = prev.keyId;
  return json(out);
}
