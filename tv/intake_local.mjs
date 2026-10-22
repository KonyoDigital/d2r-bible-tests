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
import { writeFileSync, unlinkSync, mkdtempSync, rmdirSync, readFileSync, mkdirSync, existsSync, renameSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readSettings, intSetting } from './pc_settings.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const CLAUDE = process.env.TVD_CLAUDE_BIN || 'claude';
// TV_SUB_BUDGET names the ledger explicitly - the same override tv_diablo._sub_budget_path() honours - so a law can
// point this lane at a fixture and never at his meter.
const BUDGET_PATH = String(process.env.TV_SUB_BUDGET || '').trim() || join(HERE, '.subscription_budget.json');
// Hard caps. REG-2382 - THEY WERE READ FROM process.env ONLY, and his console is launched through Terminal, where
// neither the LaunchAgent plist nor `launchctl setenv` reaches it: MEASURED 2026-10-21, the live console carried no
// TV_INTAKE_* at all and capped at 20 an hour. Now one rule on every PC (tv/pc_settings.mjs): env TV_INTAKE_*_MAX
// (the override) > this PC's gitignored tv/pc_settings.json > the code default 20 / 80. Each limit keeps its source so
// the refusal can say which limit it enforced and where that number came from. 0 opens the circuit.
const _SETTINGS = readSettings();
const HOURLY = intSetting('TV_INTAKE_HOURLY_MAX', 20, process.env, _SETTINGS);
const DAILY = intSetting('TV_INTAKE_DAILY_MAX', 80, process.env, _SETTINGS);
const HOURLY_MAX = HOURLY.value;
const DAILY_MAX = DAILY.value;
const HOUR_MS = 3600 * 1000;
const DAY_MS = 24 * HOUR_MS;
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
  // REG-2385 - ATOMIC, like tv_diablo's writer of the same file: a torn write reads as {} on both sides and restarts
  // BOTH lanes' caps from zero. A per-process tmp (two writers), and where a rename is refused - a reader holding the
  // file on Windows - the old in-place write rather than no write at all.
  const body = JSON.stringify(state);
  const tmp = BUDGET_PATH + '.' + process.pid + '.tmp';
  try {
    writeFileSync(tmp, body);
    renameSync(tmp, BUDGET_PATH);
    return;
  } catch (_) {
    try { unlinkSync(tmp); } catch (e) {}
  }
  try {
    writeFileSync(BUDGET_PATH, body);
  } catch (_) {}
}

function _said(limit) {
  /** REG-2382 - where a limit came from, plus every layer that held an unusable value. */
  return 'limit from ' + limit.source + (limit.notes.length ? '; ' + limit.notes.join('; ') : '');
}

function _retryS(window, used, max, now, span) {
  /** Seconds until enough of the window's calls age out for one more call - never a guess when it cannot be known. */
  const sorted = window.slice().sort((a, b) => a - b);
  const t = sorted[used - max];
  return Number.isFinite(t) ? Math.max(1, Math.ceil((t + span - now) / 1000)) : null;
}

function budgetCheck() {
  /** Returns null if allowed, else the refusal {window, used, limit, source, retryS, msg} (REG-2383). */
  if (HOURLY_MAX <= 0 || DAILY_MAX <= 0) {
    const off = HOURLY_MAX <= 0 ? HOURLY : DAILY;
    const name = HOURLY_MAX <= 0 ? 'TV_INTAKE_HOURLY_MAX' : 'TV_INTAKE_DAILY_MAX';
    return { window: 'circuit', used: null, limit: 0, source: off.source, retryS: null,
      msg: `subscription circuit open (${name}=0, ${_said(off)}) — intake is switched off on this PC` };
  }
  const now = Date.now();
  const state = _budgetLoad();
  const calls = (state.calls || []).filter((t) => now - t < DAY_MS);
  const hour = calls.filter((t) => now - t < HOUR_MS);
  if (hour.length >= HOURLY_MAX) {
    return { window: 'hour', used: hour.length, limit: HOURLY_MAX, source: HOURLY.source,
      retryS: _retryS(hour, hour.length, HOURLY_MAX, now, HOUR_MS),
      msg: `subscription hourly cap hit (${hour.length}/${HOURLY_MAX}, ${_said(HOURLY)}) — intake paused this hour` };
  }
  if (calls.length >= DAILY_MAX) {
    return { window: 'day', used: calls.length, limit: DAILY_MAX, source: DAILY.source,
      retryS: _retryS(calls, calls.length, DAILY_MAX, now, DAY_MS),
      msg: `subscription daily cap hit (${calls.length}/${DAILY_MAX}, ${_said(DAILY)}) — intake paused today` };
  }
  return null;
}

// REG-2385 - TWO WRITERS, TWO CLOCKS, ONE LEDGER. This file is also tv_diablo's vision meter (_sub_budget_record writes
// time.time() SECONDS); this lane writes Date.now() MILLISECONDS. Recording a call kept only the rows younger than a day
// IN MILLISECONDS - which no seconds row ever is - so every intake read ERASED the vision lane's rows (reproduced on a
// fixture: three fresh vision rows in, one intake row out). The other lane's rows are kept now, aged in their own unit
// (tv_diablo._sub_budget_calls' window: a minute of skew, under a day). What this lane COUNTS is unchanged: budgetCheck
// windows in milliseconds, so it counts its own rows only - the G5 ledger records the same collision (v1698). That
// holds only while tv_diablo writes these rows back in milliseconds: it divided them by 1000, and one vision read
// reset this cap (REG-2387).
const MS_FLOOR = 1e11;   // 1e11 ms is 1973 and 1e11 s is the year 5138: nothing real lands between them

function budgetRecord() {
  const now = Date.now();
  const state = _budgetLoad();
  const calls = (Array.isArray(state.calls) ? state.calls : []).filter((t) => {
    const n = Number(t);
    if (!Number.isFinite(n)) return false;
    if (n >= MS_FLOOR) return now - n < DAY_MS;
    const age = now / 1000 - n;
    return age >= -60 && age < 86400;
  });
  calls.push(now);
  _budgetSave({ calls, last: now });
}

// REG-2383 - the refusal the shim raised. The locked pipeline catches the throw and answers 200 with an error body
// (intake.js) or rejects (ask.js); either way the answer this lane gives is the cap's 429, decided below.
let CAP_HIT = null;

function claudeCall(apiBody) {
  // translate one Anthropic /v1/messages body into a claude-CLI run on the subscription
  const blocked = budgetCheck();
  if (blocked) {
    CAP_HIT = blocked;
    throw new Error(blocked.msg);
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
// REG-2383 - A CAP HIT IS ANSWERED 429, NOT 200 WITH AN ERROR BODY. intake.js turned the shim's throw into
// `200 {error:'worker-exception'}`, so the console handed the board a success status for a read that never happened;
// ask.js let it reject, the runner exited 1, and the console fell through to the website proxy - the API key the cap
// exists to protect. A refusal is not a failure: it is said, with its limit, its source and when to retry.
let resp = null;
let text = '';
try {
  resp = await mod.onRequestPost({ request, env: {} });
  text = await resp.text();
} catch (e) {
  if (!CAP_HIT) throw e;   // not a cap: fail exactly as before, and the console tries its next lane
}
if (CAP_HIT) {
  process.stdout.write(JSON.stringify({
    status: 429,
    body: JSON.stringify({ error: 'subscription-cap', message: CAP_HIT.msg, window: CAP_HIT.window,
      used: CAP_HIT.used, limit: CAP_HIT.limit, source: CAP_HIT.source, retry_s: CAP_HIT.retryS,
      lane: 'subscription' }),
    lane: 'subscription',
  }));
} else {
  process.stdout.write(JSON.stringify({ status: resp.status, body: text, lane: 'subscription' }));
}
