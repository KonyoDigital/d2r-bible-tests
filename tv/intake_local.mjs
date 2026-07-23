#!/usr/bin/env node
// v874 — SUBSCRIPTION INTAKE LANE (Konyo: 'the console can use the subscription for claude
// instead of the api tokens?'). Runs the REAL functions/api/intake.js / ask.js — the locked
// pipeline stays byte-identical — but a fetch shim intercepts the api.anthropic.com call and
// rides it through the locally-authorized `claude -p` CLI (his Claude plan, zero API tokens).
// stdin:  {"path":"/api/intake"|"/api/ask","body":{...}}
// stdout: {"status":N,"body":"<response text>","lane":"subscription"}
//
// v1379 LEAK FIX (2026-07-23): each cold `claude -p` was launched from d2r_bible_tests,
// loading the monorepo CLAUDE.md + user settings (agent-teams, high effort — and if
// --model is omitted, the global default can be fable). That loop burned the subscription.
// Product model is SONNET (Konyo). Never inherit fable from ~/.claude/settings.json.
// Now: empty-cwd spawn, no project/local settings, no session persistence, low effort,
// hard hourly circuit breaker, explicit --model sonnet.
import { spawnSync } from 'node:child_process';
import { writeFileSync, unlinkSync, mkdtempSync, rmdirSync, readFileSync, mkdirSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const CLAUDE = process.env.TVD_CLAUDE_BIN || 'claude';
const BUDGET_PATH = join(HERE, '.subscription_budget.json');
// Hard caps — override with TV_INTAKE_HOURLY_MAX / TV_INTAKE_DAILY_MAX
const HOURLY_MAX = Math.max(0, parseInt(process.env.TV_INTAKE_HOURLY_MAX || '20', 10) || 20);
const DAILY_MAX = Math.max(0, parseInt(process.env.TV_INTAKE_DAILY_MAX || '80', 10) || 80);
// Product default: SONNET. Override only via TV_INTAKE_MODEL (e.g. haiku for experiments).
// Never leave this empty — empty would fall through to user settings (fable).
const INTAKE_MODEL = (process.env.TV_INTAKE_MODEL || 'sonnet').trim() || 'sonnet';

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
  try {
    writeFileSync(BUDGET_PATH, JSON.stringify(state));
  } catch (_) {}
}

function budgetCheck() {
  /** Returns null if allowed, or an Error message if the circuit is open. */
  if (HOURLY_MAX <= 0 || DAILY_MAX <= 0) {
    return 'subscription circuit open (TV_INTAKE_*_MAX=0)';
  }
  const now = Date.now();
  const state = _budgetLoad();
  const calls = (state.calls || []).filter((t) => now - t < 24 * 3600 * 1000);
  const hour = calls.filter((t) => now - t < 3600 * 1000);
  if (hour.length >= HOURLY_MAX) {
    return `subscription hourly cap hit (${hour.length}/${HOURLY_MAX}) — intake paused this hour`;
  }
  if (calls.length >= DAILY_MAX) {
    return `subscription daily cap hit (${calls.length}/${DAILY_MAX}) — intake paused today`;
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

function claudeCall(apiBody) {
  // translate one Anthropic /v1/messages body into a claude-CLI run on the subscription
  const blocked = budgetCheck();
  if (blocked) {
    throw new Error(blocked);
  }

  // Always pin model on the CLI so ~/.claude/settings.json "fable" never wins.
  // TV_INTAKE_MODEL=from-body → honor apiBody.model (still falls back to sonnet).
  let model = INTAKE_MODEL;
  if (process.env.TV_INTAKE_MODEL === 'from-body') {
    model = String(apiBody.model || 'sonnet').trim() || 'sonnet';
  }
  // Normalize aliases / block fable if something smuggled it in
  const lo = model.toLowerCase();
  if (!lo || lo.includes('fable') || lo.includes('opus')) {
    model = 'sonnet';
  }
  const sysText = (apiBody.system || []).map((b) => b.text || '').join('\n');
  const content = ((apiBody.messages || [])[0] || {}).content || [];
  const img = content.find((c) => c.type === 'image');
  const userText = content.filter((c) => c.type === 'text').map((c) => c.text).join('\n');
  const schema = apiBody.output_config && apiBody.output_config.format && apiBody.output_config.format.schema;

  let imgPath = null, work = null;
  // Always work in a throwaway dir so Claude Code never loads d2r_bible_tests project context
  work = mkdtempSync(join(tmpdir(), 'tvd-intake-'));
  if (img && img.source && img.source.data) {
    const ext = (img.source.media_type || 'image/png').includes('jpeg') ? 'jpg' : 'png';
    imgPath = join(work, 'shot.' + ext);
    writeFileSync(imgPath, Buffer.from(img.source.data, 'base64'));
  }

  let prompt = sysText + '\n\n' + userText;
  if (imgPath) prompt += '\n\nThe screenshot to read is the image file at: ' + imgPath + ' — open it with the Read tool first.';
  if (schema) prompt += '\n\nRespond with ONLY minified valid JSON matching this exact schema — no prose, no markdown fences:\n' + JSON.stringify(schema);

  const env = { ...process.env };
  delete env.ANTHROPIC_API_KEY;   // the whole point: subscription login, never API tokens
  delete env.ANTHROPIC_AUTH_TOKEN;
  // Do not inherit experimental agent-teams auto-spawn into vision calls
  delete env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS;

  // Lean CLI: skip project/local settings (monorepo CLAUDE.md + agent teams), do not
  // persist a 1.3MB session jsonl, low effort. Auth stays subscription OAuth (not --bare).
  const args = [
    '-p', prompt,
    '--model', model,
    '--allowedTools', 'Read',
    '--output-format', 'text',
    '--strict-mcp-config',
    '--no-session-persistence',
    '--setting-sources', 'user',
    '--effort', 'low',
  ];
  if (imgPath) args.push('--add-dir', work);

  const r = spawnSync(CLAUDE, args, {
    env,
    cwd: work,                         // NEVER d2r_bible_tests — that was the leak
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
    throw new Error('claude CLI gave no JSON (exit ' + r.status + '): ' + (r.stderr || out).slice(0, 200));
  }
  budgetRecord();
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
