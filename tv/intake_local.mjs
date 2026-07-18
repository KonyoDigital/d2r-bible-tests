#!/usr/bin/env node
// v874 — SUBSCRIPTION INTAKE LANE (Konyo: 'the console can use the subscription for claude
// instead of the api tokens?'). Runs the REAL functions/api/intake.js / ask.js — the locked
// pipeline stays byte-identical — but a fetch shim intercepts the api.anthropic.com call and
// rides it through the locally-authorized `claude -p` CLI (his Claude plan, zero API tokens).
// stdin:  {"path":"/api/intake"|"/api/ask","body":{...}}
// stdout: {"status":N,"body":"<response text>","lane":"subscription"}
import { spawnSync } from 'node:child_process';
import { writeFileSync, unlinkSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const CLAUDE = process.env.TVD_CLAUDE_BIN || 'claude';

function readStdin() {
  return new Promise((res) => {
    let d = '';
    process.stdin.on('data', (c) => (d += c));
    process.stdin.on('end', () => res(d));
  });
}

function claudeCall(apiBody) {
  // translate one Anthropic /v1/messages body into a claude-CLI run on the subscription
  const model = apiBody.model || 'claude-sonnet-4-6';
  const sysText = (apiBody.system || []).map((b) => b.text || '').join('\n');
  const content = ((apiBody.messages || [])[0] || {}).content || [];
  const img = content.find((c) => c.type === 'image');
  const userText = content.filter((c) => c.type === 'text').map((c) => c.text).join('\n');
  const schema = apiBody.output_config && apiBody.output_config.format && apiBody.output_config.format.schema;

  let imgPath = null, tmp = null;
  if (img && img.source && img.source.data) {
    tmp = mkdtempSync(join(tmpdir(), 'tvd-intake-'));
    const ext = (img.source.media_type || 'image/png').includes('jpeg') ? 'jpg' : 'png';
    imgPath = join(tmp, 'shot.' + ext);
    writeFileSync(imgPath, Buffer.from(img.source.data, 'base64'));
  }

  let prompt = sysText + '\n\n' + userText;
  if (imgPath) prompt += '\n\nThe screenshot to read is the image file at: ' + imgPath + ' — open it with the Read tool first.';
  if (schema) prompt += '\n\nRespond with ONLY minified valid JSON matching this exact schema — no prose, no markdown fences:\n' + JSON.stringify(schema);

  const env = { ...process.env };
  delete env.ANTHROPIC_API_KEY;   // the whole point: subscription login, never API tokens
  delete env.ANTHROPIC_AUTH_TOKEN;

  const r = spawnSync(CLAUDE, ['-p', prompt, '--model', model, '--allowedTools', 'Read',
    '--output-format', 'text', '--strict-mcp-config'],
    { env, timeout: 140000, maxBuffer: 16 * 1024 * 1024, encoding: 'utf8' });

  try { if (imgPath) unlinkSync(imgPath); } catch (e) {}

  const out = (r.stdout || '').trim();
  const a = out.indexOf('{'), b = out.lastIndexOf('}');
  if (r.status !== 0 || a < 0 || b <= a) {
    throw new Error('claude CLI gave no JSON (exit ' + r.status + '): ' + (r.stderr || out).slice(0, 200));
  }
  const jsonText = out.slice(a, b + 1);
  // Anthropic-shaped response so intake.js's post-processing runs untouched
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
    return claudeCall(JSON.parse(init.body));
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
process.stdout.write(JSON.stringify({ status: resp.status, body: text, lane: 'subscription' }));
