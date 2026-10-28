/**
 * #186 STEP 3 - THE CARRIER FOR PROOFS ONE PC EARNED, SO ANOTHER PC ON THE SAME COMMIT DOES NOT RE-PROVE THEM.
 *
 * His ruling, 2026-10-28: "identical bytes saved from the windows alt pc that has already been proved. he doesnt need to
 * reprove it all". Dean's PC and the ALT run the same commit on the same platform; the ALT's census banks a PROVEN for
 * every law it proves, and Dean's census used to prove each of them again from scratch.
 *
 * POST /api/proofs - one PC's `heart2 --export-proved` file, wrapped {owner, platform, head, export} and signed exactly
 *   as a roster publish is (X-Roster-Key / X-Roster-Sig over the EXACT bytes, roster.js signatureOf). Unlike a roster row
 *   it never registers a key and never stores an unsigned body: only the key ALREADY registered for that owner
 *   (rosterkey:<owner>) may carry proofs, because a proof is what lets another PC skip work. Stored whole under
 *   proofs:<owner> - one KV value, one write (a value holds 25 MiB) - for 7 days, replacing that owner's last export.
 *   The same head again inside 3 hours is answered without a write: the KV day is ~1,000 writes, 768 of them presence's
 *   and ~100 the roster's (roster.js).
 * GET /api/proofs?owner=<label> - that owner's last export: who, which head, which platform, when, how many; &body=1
 *   adds the export itself.
 *
 * Nothing here is trusted beyond WHO sent it. The importing PC runs `heart2 --import-proved`, which re-keys every entry
 * on ITS OWN bytes and banks only what matches (REG-2630): a file of another HEAD is refused whole, an entry keyed over
 * other bytes is dropped and named. No Proofs tab, no D1, no R2 - inside the $5 plan (his 10-07 ruling).
 */
import { OWNERS, signatureOf, intentOf } from "./roster.js";

const PROOFS_MAX_BODY = 6 * 1024 * 1024;
const TTL_S = 7 * 24 * 3600;
const SAME_HEAD_GAP_MS = 3 * 3600 * 1000;
const PREFIX = "proofs:";

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

// a refusal is HTTP 200 with ok:false and its own why - never a 500 that reads as the site being down
function refuse(why) {
  return json({ ok: false, why: "proofs would not take this export: " + why }, 200);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return refuse("storage unavailable");
  let bytes = new Uint8Array(0);
  try { bytes = new Uint8Array(await request.arrayBuffer()); } catch (e) { bytes = new Uint8Array(0); }
  if (bytes.byteLength > PROOFS_MAX_BODY) return refuse("the body is larger than 6 MB");
  // the signature is checked over the bytes as they arrived, before JSON.parse and before any write (roster.js #95)
  const sig = await signatureOf(request, bytes);
  let body;
  try { body = JSON.parse(new TextDecoder("utf-8").decode(bytes) || "{}"); } catch (e) { return refuse("the body was not JSON"); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return refuse("the body was not a record");
  const owner = body.owner;
  if (OWNERS.indexOf(owner) === -1) return refuse("the owner is not a roster label");
  const head = String(body.head || "");
  if (!/^[0-9a-f]{40}$/.test(head)) return refuse("the head is not a 40-hex commit");
  const platform = String(body.platform || "");
  if (!/^[a-z0-9]{2,16}$/.test(platform)) return refuse("the platform is not named");
  const ex = body.export;
  if (!ex || typeof ex !== "object" || !ex.entries || typeof ex.entries !== "object" || Array.isArray(ex.entries)
      || !ex.export || typeof ex.export !== "object" || ex.export.head !== head) {
    return refuse("the export does not carry its own manifest for this head");
  }
  let registered = null;
  try { registered = await kv.get("rosterkey:" + owner, { type: "json" }); } catch (e) { return refuse("the owner's key could not be read"); }
  if (registered === null) return refuse(owner + " has no registered key - proofs ride only a key the roster already trusts");
  const intent = intentOf(owner, registered, sig);
  if (!intent.verified) return refuse(intent.refused || "the signature did not verify");
  const now = Date.now();
  let prev = null;
  try { prev = await kv.get(PREFIX + owner, { type: "json" }); } catch (e) { prev = null; }
  if (prev && prev.head === head && typeof prev.at === "number" && now - prev.at < SAME_HEAD_GAP_MS) {
    return json({ ok: true, stored: false, why: "this head was carried less than 3 hours ago", head: head, at: prev.at }, 200);
  }
  const count = Object.keys(ex.entries).length;
  const rec = { owner: owner, head: head, platform: platform, at: now, keyId: intent.keyId, count: count, export: ex };
  try {
    await kv.put(PREFIX + owner, JSON.stringify(rec), { expirationTtl: TTL_S });
  } catch (e) {
    return refuse("storage refused the write (" + String((e && e.name) || e).slice(0, 60) + ")");
  }
  return json({ ok: true, stored: true, head: head, count: count, keyId: intent.keyId, at: now }, 200);
}

export async function onRequestGet(context) {
  const { request, env } = context;
  const kv = env && env.TZ_HISTORY;
  if (!kv) return json({ ok: false, why: "storage unavailable" }, 200);
  const url = new URL(request.url);
  const owner = url.searchParams.get("owner") || "";
  if (OWNERS.indexOf(owner) === -1) return json({ ok: false, why: "the owner is not a roster label" }, 200);
  let rec = null;
  try { rec = await kv.get(PREFIX + owner, { type: "json" }); } catch (e) { return json({ ok: false, why: "storage read failed" }, 200); }
  if (!rec || typeof rec !== "object") return json({ ok: true, owner: owner, have: false }, 200);
  const out = { ok: true, owner: owner, have: true, head: rec.head, platform: rec.platform, at: rec.at, keyId: rec.keyId,
                count: rec.count };
  if (url.searchParams.get("body") === "1") out.export = rec.export;
  return json(out, 200);
}
