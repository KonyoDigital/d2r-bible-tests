#!/usr/bin/env node
// ══ GROK EYES (G5) — INTAKE SUBSCRIPTION LANE (REMOVABLE) ══════════════════════
// Mirror of intake_local.mjs, but rides SuperGrok via local `grok -p` (OIDC login).
// NEVER uses XAI_API_KEY / api.x.ai / console API tokens.
//
// stdin:  {"path":"/api/intake"|"/api/ask","body":{...}}
// stdout: {"status":N,"body":"<response text>","lane":"grok-subscription"}
//
// Same real functions/api/intake.js pipeline — only the Anthropic fetch shim differs.
import { spawnSync } from 'node:child_process';
import { writeFileSync, unlinkSync, mkdtempSync, rmdirSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir, homedir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const GROK = process.env.G5_GROK_BIN || process.env.TV_GROK_BIN || 'grok';
const BUDGET_PATH = join(HERE, 'g5_subscription_budget.json');
const HOURLY_MAX = Math.max(0, parseInt(process.env.G5_GROK_HOURLY_MAX || '30', 10) || 30);
const DAILY_MAX = Math.max(0, parseInt(process.env.G5_GROK_DAILY_MAX || '200', 10) || 200);

function readStdin() {
  return new Promise((res) => {
    let d = '';
    process.stdin.on('data', (c) => (d += c));
    process.stdin.on('end', () => res(d));
  });
}

function _budgetLoad() {
  try {
    if (!existsSync(BUDGET_PATH)) return { calls: [] };
    return JSON.parse(readFileSync(BUDGET_PATH, 'utf8')) || { calls: [] };
  } catch (_) {
    return { calls: [] };
  }
}

function _budgetSave(state) {
  try { writeFileSync(BUDGET_PATH, JSON.stringify(state)); } catch (_) {}
}

function budgetCheck() {
  if (HOURLY_MAX <= 0 || DAILY_MAX <= 0) {
    return 'grok-subscription circuit open (G5_GROK_*_MAX=0)';
  }
  const now = Date.now();
  const state = _budgetLoad();
  const calls = (state.calls || []).filter((t) => now - t < 24 * 3600 * 1000);
  const hour = calls.filter((t) => now - t < 3600 * 1000);
  if (hour.length >= HOURLY_MAX) {
    return `grok-subscription hourly cap (${hour.length}/${HOURLY_MAX})`;
  }
  if (calls.length >= DAILY_MAX) {
    return `grok-subscription daily cap (${calls.length}/${DAILY_MAX})`;
  }
  return null;
}

function budgetRecord() {
  const now = Date.now();
  const state = _budgetLoad();
  const calls = (state.calls || []).filter((t) => now - t < 24 * 3600 * 1000);
  calls.push(now);
  _budgetSave({ calls, last: now });
}

function subscriptionLoggedIn() {
  try {
    const auth = join(homedir(), '.grok', 'auth.json');
    if (!existsSync(auth)) return false;
    const d = JSON.parse(readFileSync(auth, 'utf8'));
    return !!(d && typeof d === 'object' && Object.keys(d).length);
  } catch (_) {
    return false;
  }
}

function grokCall(apiBody) {
  const blocked = budgetCheck();
  if (blocked) throw new Error(blocked);
  if (!subscriptionLoggedIn()) {
    throw new Error('grok not logged in — run: grok login (SuperGrok subscription; NO API keys)');
  }

  const sysText = (apiBody.system || []).map((b) => b.text || '').join('\n');
  const content = ((apiBody.messages || [])[0] || {}).content || [];
  const img = content.find((c) => c.type === 'image');
  const userText = content.filter((c) => c.type === 'text').map((c) => c.text).join('\n');
  const schema = apiBody.output_config && apiBody.output_config.format && apiBody.output_config.format.schema;

  let imgPath = null;
  const work = mkdtempSync(join(tmpdir(), 'tvd-intake-g5-'));
  if (img && img.source && img.source.data) {
    const ext = (img.source.media_type || 'image/png').includes('jpeg') ? 'jpg' : 'png';
    imgPath = join(work, 'shot.' + ext);
    writeFileSync(imgPath, Buffer.from(img.source.data, 'base64'));
  }

  let prompt = sysText + '\n\n' + userText;
  if (imgPath) {
    prompt += '\n\nThe screenshot to read is the image file at: ' + imgPath
      + ' — open it with the read_file tool FIRST, then answer.';
  }
  if (schema) {
    prompt += '\n\nRespond with ONLY minified valid JSON matching this exact schema — no prose, no markdown fences:\n'
      + JSON.stringify(schema);
  }

  const env = { ...process.env };
  // FORCE subscription — never console API tokens
  delete env.XAI_API_KEY;
  delete env.G5_XAI_KEY;
  delete env.G4_XAI_KEY;
  delete env.OPENAI_API_KEY;
  delete env.ANTHROPIC_API_KEY;
  delete env.ANTHROPIC_AUTH_TOKEN;

  const args = [
    '-p', prompt,
    '--output-format', 'plain',
    '--always-approve',
    '--tools', 'read_file',
    '--cwd', work,
    '--disable-web-search',
  ];

  const r = spawnSync(GROK, args, {
    env,
    cwd: work,
    timeout: 140000,
    maxBuffer: 16 * 1024 * 1024,
    encoding: 'utf8',
  });

  try {
    if (imgPath) unlinkSync(imgPath);
    if (work) rmdirSync(work, { recursive: true });
  } catch (e) {}

  const out = (r.stdout || '').trim();
  const a = out.indexOf('{'), b = out.lastIndexOf('}');
  if (r.status !== 0 || a < 0 || b <= a) {
    throw new Error('grok -p gave no JSON (exit ' + r.status + '): ' + (r.stderr || out).slice(0, 200));
  }
  budgetRecord();
  const jsonText = out.slice(a, b + 1);
  // Anthropic-shaped so intake.js post-processing is untouched
  return {
    ok: true, status: 200,
    json: async () => ({
      content: [{ type: 'text', text: jsonText }],
      stop_reason: 'end_turn',
      usage: { input_tokens: 0, output_tokens: 0 },
    }),
    text: async () => jsonText,
  };
}

const realFetch = globalThis.fetch;
globalThis.fetch = async (url, init) => {
  if (String(url).startsWith('https://api.anthropic.com/')) {
    return grokCall(JSON.parse(init.body));
  }
  return realFetch(url, init);
};

const { path, body } = JSON.parse(await readStdin());
const modPath = path === '/api/ask' ? '../functions/api/ask.js' : '../functions/api/intake.js';
const mod = await import(pathToFileURL(join(HERE, modPath)).href);
const request = new Request('http://local' + path, {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify(body),
});
const resp = await mod.onRequestPost({ request, env: {} });
const text = await resp.text();
process.stdout.write(JSON.stringify({ status: resp.status, body: text, lane: 'grok-subscription' }));
