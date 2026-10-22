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
 * #95 (REG-2516): a signed, verified write keeps a section it did not send only
 * when the stored row was written under the very same key. Anything else the row
 * held - planted unsigned, written before signing, another key's - is dropped, never
 * carried in under this key's "verified".
 * It is never stored as an empty list. Pictures and frame bytes are refused
 * and not stored. GET /api/roster reads the five owner keys and writes nothing.
 * No Roster tab, no D1, no R2.
 *
 * #95 SIGNED PUBLISHING (his ruling 2026-10-22: deploy once the Python/JS signature
 * test passes, trust-on-first-use, never stop a PC from publishing).
 * The site's Basic password is public (the console sends it from a public repo), so
 * it is no longer what lets a row be written. Each PC holds an Ed25519 key
 * (tv/roster_sign.py) and sends X-Roster-Key and X-Roster-Sig (base64url) over the
 * EXACT bytes it posts. Those bytes are verified here with crypto.subtle before they
 * are parsed and before any KV write. Nothing is re-serialised on either side.
 *
 *   no key registered + valid signature  -> the key is registered (rosterkey:<owner>)
 *                                           and the row is stored intentVerified:true
 *   no key registered + unsigned         -> stored intentVerified:false, so a PC that
 *                                           has not updated keeps publishing
 *   no key registered + bad signature    -> stored intentVerified:false and NOT
 *                                           registered: anyone could post that row
 *                                           unsigned, and a signer bug must not stop
 *                                           a PC from publishing. The reply says why.
 *   registered + same key + valid        -> stored intentVerified:true
 *   registered + unsigned, another key,
 *   or a bad signature                   -> refused (200, ok:false) with its own why
 *                                           and hint. Nothing is stored.
 *
 * A key changes only when Konyo deletes rosterkey:<owner> from the Mac. Nothing here
 * changes one by itself. The next signed publish then registers that PC's key:
 *   npx wrangler kv namespace list          (the id of the namespace bound as TZ_HISTORY)
 *   npx wrangler kv key delete "rosterkey:<owner>" --namespace-id=<that id> --remote
 * A key can also be put there before a PC's first publish (pre-seeded):
 *   npx wrangler kv key put "rosterkey:<owner>" '{"pub":"<base64url>","keyId":"<12 hex>","at":0}' --namespace-id=<that id> --remote
 * A row stored before signing has no intentVerified. GET passes the field only when
 * the record holds a boolean, so a viewer shows that row UNKNOWN, never verified.
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
const KEY_PREFIX = "rosterkey:";
const SIGNATURE_HINT = "nothing was stored: the key registered for this owner did not sign this publish. " +
  "A PC that lost its key stays refused until Konyo resets the owner's key from the Mac; a key never changes by itself";

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

function bytesOfB64u(text) {
  if (typeof text !== "string") return null;
  const t = text.trim().replace(/=+$/, "");
  if (!t || !/^[A-Za-z0-9_-]+$/.test(t) || t.length % 4 === 1) return null;
  let bin = "";
  try { bin = atob(t.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((t.length + 3) % 4)); } catch (e) {
    return null;
  }
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function b64uOfBytes(bytes) {
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

// The short public name of a key: the first 12 hex of SHA-256 over its 32 raw bytes.
// tv/roster_sign.py key_id() computes the same, so a PC can compare its own key with a row's.
async function keyIdOf(pub) {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", pub));
  let hex = "";
  for (let i = 0; i < 6; i++) hex += (d[i] < 16 ? "0" : "") + d[i].toString(16);
  return hex;
}

// #95 - what the two headers prove about these exact bytes. -> {state: none | valid | bad, ...}
async function signatureOf(request, bytes) {
  const keyText = request.headers.get("x-roster-key");
  const sigText = request.headers.get("x-roster-sig");
  if (!keyText && !sigText) return { state: "none" };
  if (!keyText || !sigText) return { state: "bad", why: "one signature header came without the other" };
  const pub = bytesOfB64u(keyText);
  const sig = bytesOfB64u(sigText);
  if (!pub || pub.length !== 32) return { state: "bad", why: "the public key is not 32 bytes of base64url" };
  if (!sig || sig.length !== 64) return { state: "bad", why: "the signature is not 64 bytes of base64url" };
  const keyId = await keyIdOf(pub);
  let ok = false;
  try {
    const verifier = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    ok = await crypto.subtle.verify({ name: "Ed25519" }, verifier, sig, bytes);
  } catch (e) {
    return { state: "bad", keyId: keyId, why: "the signature could not be checked: " + String((e && e.name) || e).slice(0, 60) };
  }
  if (ok !== true) return { state: "bad", keyId: keyId, why: "the signature does not match these bytes" };
  return { state: "valid", pub: b64uOfBytes(pub), keyId: keyId };
}

// #95 - may this owner's row be written by this publish, and is it the owner's intent?
// -> {refused: why, registeredKeyId} | {verified, keyId, register}
function intentOf(owner, registered, sig) {
  if (registered !== null) {
    const regPub = registered && typeof registered === "object" ? bytesOfB64u(registered.pub) : null;
    if (!regPub || regPub.length !== 32) {
      return { refused: "the key registered for " + owner + " is unreadable (not 32 bytes of base64url)" };
    }
    const regId = typeof registered.keyId === "string" ? registered.keyId.slice(0, 16) : null;
    if (sig.state === "none") {
      return { refused: owner + " has a registered key and this publish was not signed", registeredKeyId: regId };
    }
    if (sig.state !== "valid") {
      return { refused: "the signature did not verify (" + sig.why + ")", registeredKeyId: regId };
    }
    if (sig.pub !== b64uOfBytes(regPub)) {
      return { refused: "this publish was signed by a different key than the one registered for " + owner, registeredKeyId: regId };
    }
    return { verified: true, keyId: sig.keyId, register: false };
  }
  if (sig.state === "valid") return { verified: true, keyId: sig.keyId, register: true };
  return { verified: false, keyId: null, register: false };
}

function refuseSignature(intent, sig) {
  const out = { ok: false, why: "roster would not take this publish: " + intent.refused, hint: SIGNATURE_HINT, sig: sig.state };
  if (intent.registeredKeyId) out.keyId = intent.registeredKeyId;
  if (sig.keyId) out.offered = sig.keyId;
  return json(out, 200);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return refuse("roster would not take this publish: storage unavailable");

  let bytes = new Uint8Array(0);
  try { bytes = new Uint8Array(await request.arrayBuffer()); } catch (e) { bytes = new Uint8Array(0); }
  if (bytes.byteLength > MAX_BODY) {
    return refuse("roster would not take this publish: the body is too large to be rows");
  }
  // #95 - the signature is checked over the bytes as they arrived, before JSON.parse and before any write.
  const sig = await signatureOf(request, bytes);
  let text = "";
  try { text = new TextDecoder("utf-8").decode(bytes); } catch (e) { text = ""; }
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
  const keyName = KEY_PREFIX + owner;
  let held = null;
  try { held = await kv.get(keyName); } catch (e) {
    return refuse("roster would not take this publish: the key registered for this owner could not be read");
  }
  // A key Konyo put there by hand may be the bare base64url string rather than the record this file writes.
  // Anything else stored under the name still counts as a registered key, unreadable: it fails closed.
  let registered = null;
  if (held) {
    try { registered = JSON.parse(held); } catch (e) { registered = { pub: String(held).trim() }; }
    if (typeof registered === "string") registered = { pub: registered };
    if (!registered || typeof registered !== "object") registered = { pub: null };
  }
  const intent = intentOf(owner, registered, sig);
  if (intent.refused) return refuseSignature(intent, sig);

  let prev = null;
  try {
    const raw = await kv.get(key);
    prev = raw ? JSON.parse(raw) : null;
  } catch (e) { prev = null; }
  if (!prev || typeof prev !== "object" || prev.owner !== owner) prev = null;

  const now = Date.now();
  const boot = body.boot === true;
  const verified = intent.verified === true;
  const keyId = verified ? intent.keyId : null;
  // The whole public key a verified row was written under. keyId is 48 bits of it, a name for people to
  // compare; two keys can share one, so "the same key" is asked of the key itself.
  const pub = verified ? sig.pub : null;
  const prevPub = prev && prev.intentVerified === true && typeof prev.pub === "string" ? prev.pub : null;
  const sameIntent = !!prev && prev.intentVerified === verified && prevPub === pub && (prev.keyId || null) === keyId;
  // REG-2516 - a verified row holds only what its own key signed. A section is carried over from the stored
  // row only when that row was written under this very key. Merging every prior section into a signed write
  // stamped rows this key never signed - planted unsigned before the key was registered, written before
  // signing, or another key's - "signature verified (key ...)" for good, because a PC never re-sends a section
  // it does not read (no PC sends `owned`). An unsigned write still merges: it is stored NOT verified, and says so.
  const inherit = !verified || sameIntent;
  const sections = Object.assign(inherit ? priorSections(prev) : {}, shaped);
  const hash = forHash(sections);
  // What this publish's signature proved, said on every answer so the PC can record it.
  const said = { intentVerified: verified, sig: sig.state };
  if (keyId) said.keyId = keyId;
  if (sig.state === "bad") said.sigWhy = sig.why;
  // A row that becomes verified, changes key, or registers its key is written even when unchanged
  // and inside the hour: that is the owner's key arriving, not a churn of rows. The daily cap holds.
  const upgrade = verified && (!sameIntent || intent.register === true);

  if (!Object.keys(sections).length) {
    return json(Object.assign({ ok: true, owner: owner, stored: [], skipped: ["nothing read"] }, said), 200);
  }
  if (prev && prev.hash === hash && sameIntent && !upgrade) {
    return json(Object.assign({ ok: true, owner: owner, stored: [], skipped: ["unchanged"] }, said), 200);
  }
  const age = prev && typeof prev.t === "number" ? (now - prev.t) : HOUR_MS;
  if (prev && age < HOUR_MS && !boot && !upgrade) {
    return json(Object.assign({ ok: true, owner: owner, stored: [], skipped: ["within the hour"] }, said), 200);
  }

  const today = dayOf(now);
  const n = (prev && prev.day === today && typeof prev.n === "number") ? prev.n : 0;
  if (n >= ROSTER_CAP) {
    return json({ ok: false, why: QUOTA_WHY, hint: REFUSAL_HINT }, 200);
  }

  if (intent.register) {
    try {
      await kv.put(keyName, JSON.stringify({ pub: sig.pub, keyId: sig.keyId, at: now }));
    } catch (e) {
      return refuse("roster would not take this publish: " + String((e && e.message) || e).slice(0, 140));
    }
    said.registered = true;
  }
  const rec = { owner: owner, t: now, day: today, n: n + 1, hash: hash, sections: sections };
  rec.intentVerified = verified;
  if (keyId) rec.keyId = keyId;
  if (pub) rec.pub = pub;
  if (verified && typeof body.signedAt === "number" && Number.isFinite(body.signedAt)) rec.signedAt = body.signedAt;
  try {
    await kv.put(key, JSON.stringify(rec), { expirationTtl: TTL_S });
  } catch (e) {
    return refuse("roster would not take this publish: " + String((e && e.message) || e).slice(0, 140));
  }
  return json(Object.assign({ ok: true, owner: owner, stored: ["roster"], key: key }, said), 200);
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
    // #95 - passed only when the record holds a boolean: a row stored before signing has none,
    // and a viewer must show it UNKNOWN, never verified and never unverified.
    if (typeof prev.intentVerified === "boolean") row.intentVerified = prev.intentVerified;
    if (typeof prev.keyId === "string" && /^[0-9a-f]{12}$/.test(prev.keyId)) row.keyId = prev.keyId;
    if (typeof prev.signedAt === "number" && Number.isFinite(prev.signedAt)) row.signedAt = prev.signedAt;
    if (Object.keys(sections).length) row.sections = sections;
    owners.push(row);
  }
  return json({ ok: true, owners: owners }, 200);
}
