// REG-2382 — ONE PER-PC SETTINGS FILE, READ THE SAME WAY ON EVERY PC (his Mac, the Windows boxes, Dean's).
//
// The intake reader's caps lived only in process.env (TV_INTAKE_HOURLY_MAX / TV_INTAKE_DAILY_MAX, read at
// tv/intake_local.mjs). His console is launched through Terminal (TVD_VIA_TERMINAL=1), so neither the LaunchAgent plist
// nor `launchctl setenv` ever reaches it: MEASURED 2026-10-21, the live console's environment carried no TV_INTAKE_*
// at all and the reader capped at the code default (20 an hour) while the caps were believed set. A Windows console
// started from its shortcut has the same blind spot, and nothing said which limit was enforced or why.
//
// tv/pc_settings.json is per PC and GITIGNORED - it never travels between machines. It holds env-style names:
//
//     {"TV_INTAKE_HOURLY_MAX": 50, "TV_INTAKE_DAILY_MAX": 300}
//
// One rule for every value: the process environment (an explicit override) beats this PC's file, which beats the code
// default. Every value says where it came from, so a refusal can name the source of the limit it enforced; a value a
// layer holds that is not usable is IGNORED AND SAID, never silently replaced. TV_PC_SETTINGS points the reader at
// another file (a law's fixture). Stdlib only, never throws.
import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
export const SETTINGS_FILE = 'pc_settings.json';

/** Where this PC's settings live. -> absolute path */
export function settingsPath(env = process.env) {
  return String(env.TV_PC_SETTINGS || '').trim() || join(HERE, SETTINGS_FILE);
}

/** This PC's settings. -> {label, values, error}; an absent file is {} with no error, an unreadable one says why.
 *  `label` names the file for a message without a home path in it. */
export function readSettings(env = process.env) {
  const path = settingsPath(env);
  const label = String(env.TV_PC_SETTINGS || '').trim() ? 'the TV_PC_SETTINGS file' : 'tv/' + SETTINGS_FILE;
  try {
    if (!existsSync(path)) return { label, values: {}, error: null };
    let text = readFileSync(path, 'utf8');
    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);   // Notepad saves UTF-8 with a BOM on Windows
    const v = JSON.parse(text);
    if (!v || typeof v !== 'object' || Array.isArray(v)) return { label, values: {}, error: 'not a JSON object' };
    return { label, values: v, error: null };
  } catch (e) {
    return { label, values: {}, error: String((e && e.message) || e).slice(0, 120) };
  }
}

/** A whole number >= 0 (0 is a real value: it switches a lane off), or null when `raw` is not one. */
export function wholeNumber(raw) {
  if (typeof raw === 'number') return Number.isInteger(raw) && raw >= 0 ? raw : null;
  const s = String(raw == null ? '' : raw).trim();
  return /^\d+$/.test(s) ? parseInt(s, 10) : null;
}

/** One whole-number setting. -> {value, source, notes}
 *  source: 'env NAME' | the settings file's label | 'the code default'. notes: every layer that held an unusable
 *  value, and why it was passed over. */
export function intSetting(name, fallback, env = process.env, settings = readSettings(env)) {
  const notes = [];
  const fromEnv = env[name];
  if (fromEnv !== undefined && String(fromEnv).trim() !== '') {
    const n = wholeNumber(fromEnv);
    if (n !== null) return { value: n, source: 'env ' + name, notes };
    notes.push('env ' + name + '=' + JSON.stringify(String(fromEnv).slice(0, 24)) + ' is not a whole number - ignored');
  }
  if (settings.error) {
    notes.push(settings.label + ' is unreadable (' + settings.error + ') - ignored');
  } else if (Object.prototype.hasOwnProperty.call(settings.values, name)) {
    const n = wholeNumber(settings.values[name]);
    if (n !== null) return { value: n, source: settings.label, notes };
    notes.push(settings.label + ' ' + name + '=' + JSON.stringify(settings.values[name]).slice(0, 24)
      + ' is not a whole number - ignored');
  }
  return { value: fallback, source: 'the code default', notes };
}
