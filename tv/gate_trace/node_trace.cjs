// v3772 (REG-2293) - what a node child of a gate read, in sitecustomize.py's trace format.
//
// gate_ledger.trace_env() puts `--require <this file>` in NODE_OPTIONS next to the python hook.
// It wraps the fs calls that read, list, stat or write a path, and every child_process call.
// Lines are `KIND<TAB>PID<TAB>TEXT`, repo-relative, appended to TV_GATE_TRACE. A child that is
// not node or python, and an ES module loaded from this checkout (its imports do not go through
// fs), are a U line: that run is never carried.
'use strict';
(function () {
  const out = process.env.TV_GATE_TRACE;
  const root = process.env.TV_GATE_TRACE_ROOT;
  if (!out || !root) return;
  const fs = require('fs');
  const path = require('path');
  const url = require('url');
  const roots = [path.normalize(root)];
  try { const r = fs.realpathSync(root); if (!roots.includes(r)) roots.push(r); } catch (e) { /* keep one */ }
  let fd;
  try { fd = fs.openSync(out, 'a'); } catch (e) { return; }
  const writeSync = fs.writeSync;
  const seen = new Set();
  let busy = false;
  function emit(kind, text, once) {
    const key = kind + '\t' + text;
    if (once !== false) { if (seen.has(key)) return; seen.add(key); }
    try { writeSync(fd, kind + '\t' + process.pid + '\t' + String(text).replace(/[\t\n]/g, ' ') + '\n'); } catch (e) { /* lost */ }
  }
  function rel(p) {
    try {
      if (p == null || typeof p === 'number') return null;
      if (p instanceof URL) p = url.fileURLToPath(p);
      if (Buffer.isBuffer(p)) p = p.toString();
      if (typeof p !== 'string') return null;
      p = path.resolve(p);
      for (const b of roots) {
        if (p === b) return '';
        if (p.startsWith(b + path.sep)) {
          const r = p.slice(b.length + 1).split(path.sep).join('/');
          if (r.startsWith('tv/gate_trace/') || r.split('/').includes('node_modules')) return null;
          return r;
        }
      }
    } catch (e) { /* not a path */ }
    return null;
  }
  function note(kind, p) { const r = rel(p); if (r !== null) emit(kind, r); }
  function writes(flags) {
    return typeof flags === 'string' ? /[wax+]/.test(flags)
      : (typeof flags === 'number' && (flags & (fs.constants.O_WRONLY | fs.constants.O_RDWR | fs.constants.O_CREAT)) !== 0);
  }
  function wrap(obj, name, before) {
    const real = obj && obj[name];
    if (typeof real !== 'function') return;
    obj[name] = function () {
      if (!busy) { busy = true; try { before.apply(null, arguments); } catch (e) { /* never break the call */ } finally { busy = false; } }
      return real.apply(this, arguments);
    };
  }
  const R = (p) => note('R', p);
  const W = (p) => note('W', p);
  const L = (p) => note('L', p);
  const realLstat = fs.lstatSync;
  const S = (p) => {
    const r = rel(p);
    if (r === null) return;
    let there = true;
    try { realLstat(p); } catch (e) { there = false; }
    emit(there ? 'S' : 'A', r);
  };
  const P = fs.promises;
  for (const n of ['readFileSync', 'readFile', 'createReadStream']) wrap(fs, n, R);
  for (const n of ['readFile']) wrap(P, n, R);
  for (const n of ['openSync', 'open']) wrap(fs, n, (p, flags) => (writes(flags) ? W(p) : R(p)));
  wrap(P, 'open', (p, flags) => (writes(flags) ? W(p) : R(p)));
  for (const n of ['readdirSync', 'readdir', 'opendirSync', 'opendir']) wrap(fs, n, L);
  for (const n of ['readdir', 'opendir']) wrap(P, n, L);
  for (const n of ['existsSync', 'statSync', 'lstatSync', 'stat', 'lstat', 'accessSync', 'access', 'exists', 'realpathSync']) wrap(fs, n, S);
  for (const n of ['stat', 'lstat', 'access']) wrap(P, n, S);
  for (const n of ['writeFileSync', 'writeFile', 'appendFileSync', 'appendFile', 'mkdirSync', 'mkdir', 'createWriteStream']) wrap(fs, n, W);
  for (const n of ['writeFile', 'appendFile', 'mkdir']) wrap(P, n, W);
  for (const n of ['renameSync', 'rename']) wrap(fs, n, (a, b) => W(b));
  wrap(P, 'rename', (a, b) => W(b));
  for (const n of ['copyFileSync', 'copyFile']) wrap(fs, n, (a, b) => { R(a); W(b); });
  let kids = 0;
  function child(file, env) {
    const head = path.basename(String(file || ''));
    const source = env || process.env;
    const traced = source.TV_GATE_TRACE === out;
    const isNode = head === 'node' || head === 'nodejs' || file === process.execPath;
    const isPy = head.startsWith('python');
    if (traced && (isPy || (isNode && String(source.NODE_OPTIONS || '').includes('node_trace.cjs')))) {
      kids += 1;
      emit('P', String(kids), false);
      return;
    }
    emit('U', 'started ' + (head || 'a process'));
  }
  const cp = require('child_process');
  for (const n of ['spawn', 'spawnSync', 'execFile', 'execFileSync']) {
    wrap(cp, n, (file, args, opts) => {
      if (args && !Array.isArray(args) && typeof args === 'object') opts = args;
      child(file, opts && opts.env);
    });
  }
  for (const n of ['exec', 'execSync']) wrap(cp, n, () => emit('U', 'started a shell'));
  wrap(cp, 'fork', (mod, args, opts) => {
    if (args && !Array.isArray(args) && typeof args === 'object') opts = args;
    child(process.execPath, opts && opts.env);
  });
  emit('B', String(process.ppid));
  const main = process.argv[1];
  const esm = process.execArgv.some((a) => a.startsWith('--input-type=module') || a.startsWith('--experimental-loader') || a.startsWith('--import'));
  if (esm || (main && rel(main) !== null && /\.mjs$/.test(main))) {
    emit('U', 'ran an ES module, whose imports do not go through fs');
  }
  if (main) R(main);
})();
