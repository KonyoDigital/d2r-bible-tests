// v3772 (REG-2293) - what a node child of a gate read, in sitecustomize.py's trace format.
//
// gate_ledger.trace_env() puts `--require <this file>` in NODE_OPTIONS next to the python hook.
// It wraps the fs calls that read, list, stat or write a path, and every child_process call.
// Lines are `KIND<TAB>PID<TAB>TEXT`, repo-relative, appended to TV_GATE_TRACE. A child that is
// not node or python, and an ES module loaded from this checkout (its imports do not go through
// fs), are a U line: that run is never carried.
//
// REG-2442 (#147 R1) - the facts sitecustomize.py writes, written the same way here: Z (a stat's kind and size), E (a
// single-name read of process.env, `<sha256|-> <NAME>`, never for _PLUMBING, a name this process set, or - in a child -
// a value the run's root did not have), N (the root's environment, once), C (a child whose own env carries
// TV_GATE_TRACE_CDP=1 while this process's does not) and the U of TV_GATE_TRACE_DENY / _ALLOW. A bulk read of
// process.env (spread, Object.entries, a spawn with no env) reads each name right after enumerating it, and is not a
// fact. FLOOR, said: a name read directly in the same tick right after an enumeration that read no values (Object.keys)
// passes for a bulk read when it is exactly the last name enumerated; a C++ addon's getenv() is not seen.
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
  const realRealpath = fs.realpathSync;
  const realStat = fs.statSync;
  const realReadFile = fs.readFileSync;
  const realEnv = process.env;
  const crypto = require('crypto');
  // REG-2442 - the names a prover sets per run: the same set as sitecustomize.py's _PLUMBING  // TRACE-PLUMBING
  const PLUMBING = new Set(['TMPDIR', 'TEMP', 'TMP', 'TV_LANE_PORT_BASE', 'TV_PORT', 'TV_CONTROL_PORT', 'TV_LAW_PORT',
    'TV_RENDER_PORT', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX', 'NODE_OPTIONS']);
  const plumbing = (n) => { const u = String(n).toUpperCase(); return PLUMBING.has(u) || u.startsWith('HEART2_') || u.startsWith('TV_GATE_'); };
  const digestOf = (v) => crypto.createHash('sha256').update(Buffer.from(String(v), 'utf8')).digest('hex');
  const win = process.platform === 'win32';
  function formsOf(spec) {
    const found = [];
    for (let part of String(spec || '').split(path.delimiter)) {
      part = part.trim();
      if (!part) continue;
      if (part === '~' || part.startsWith('~/') || part.startsWith('~\\')) part = require('os').homedir() + part.slice(1);
      const p = path.resolve(part);
      const cands = [p];
      try { cands.push(realRealpath(p)); } catch (e) { /* the given form stands alone */ }
      for (let c of cands) { c = path.normalize(c); if (win) c = c.toLowerCase(); if (!found.includes(c)) found.push(c); }
    }
    return found;
  }
  const deny = formsOf(realEnv.TV_GATE_TRACE_DENY);
  const allow = formsOf(realEnv.TV_GATE_TRACE_ALLOW);
  // whose environment this process's E facts are held to: the nearest traced ancestor that wrote an N block
  let isRoot = true;
  let rootEnv = null;
  try {
    const parent = new Map();
    const block = new Map();
    for (const line of fs.readFileSync(out, 'utf8').split(/\r?\n/)) {
      if (!(line.startsWith('B\t') || line.startsWith('N\t'))) continue;
      const i = line.indexOf('\t', 2);
      if (i < 0) continue;
      const pid = line.slice(2, i);
      const text = line.slice(i + 1);
      if (line[0] === 'B') { parent.set(pid, text); continue; }
      const sp = text.indexOf(' ');
      if (!block.has(pid)) block.set(pid, new Map());
      block.get(pid).set(text.slice(sp + 1), text.slice(0, sp));
    }
    let p = String(process.ppid);
    if (parent.has(p)) {
      isRoot = false;
      const walked = new Set();
      while (parent.has(p) && !walked.has(p)) {
        if (block.has(p)) { rootEnv = block.get(p); break; }
        walked.add(p);
        p = parent.get(p);
      }
    }
  } catch (e) { /* unreadable: a root of its own subtree, every read a fact (over-wide, never under) */ }
  let fd;
  try { fd = fs.openSync(out, 'a'); } catch (e) { return; }
  const writeSync = fs.writeSync;
  const seen = new Set();
  let busy = false;
  const realdirs = new Map();
  function under(p, bases) {
    for (const b of bases) if (p === b || p.startsWith(b.endsWith(path.sep) ? b : b + path.sep)) return true;
    return false;
  }
  function denied(p) {
    const dir = path.dirname(p);
    let real = realdirs.get(dir);
    if (real === undefined) {
      try { real = realRealpath(dir); } catch (e) { real = dir; }
      if (realdirs.size < 8192) realdirs.set(dir, real);
    }
    const forms = [p, path.join(real, path.basename(p))].map((f) => (win ? f.toLowerCase() : f));
    if (allow.length && forms.some((f) => under(f, allow))) return false;
    return forms.some((f) => under(f, deny));
  }
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
      if (deny.length && denied(p)) emit('U', 'reached ' + p + ', under a root no key of this run can name');  // TRACE-DENY
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
  // REG-2442 - H: the bytes a read finds, measured as it opens (sitecustomize.py's bytes_fact): once per path
  function H(p) {
    const r = rel(p);
    if (r === null || seen.has('H:' + r)) return;
    seen.add('H:' + r);
    let d;
    try {
      const st = realStat(p);
      d = st.isDirectory() ? 'd' : (st.isFile() ? crypto.createHash('sha256').update(realReadFile(p)).digest('hex') : '?');
    } catch (e) { d = (e && e.code === 'ENOENT') ? '-' : '?'; }
    emit('H', d + ' ' + r);  // TRACE-BYTES-FACT
  }
  const RH = (p) => { R(p); H(p); };
  const W = (p) => note('W', p);
  const L = (p) => note('L', p);
  const realLstat = fs.lstatSync;
  const realReaddir = fs.readdirSync;
  const underRoot = (r) => (r === '' ? roots[0] : path.join(roots[0], ...r.split('/')));
  // REG-2449 - D: what a listed folder held as it was listed - sitecustomize.py's listing_fact, the same rule: each
  // name (never __pycache__) with its kind (l f d o, from lstat) and a file's or a link's size, rows sorted by code
  // point, one sha256; '-' absent, 'f' a file, '?' unreadable or a name that is not UTF-8. Once per folder. Before, a
  // node listing wrote L alone, so the ledger never held the ignored names it saw (its per-tree facts took D only).
  function D(p) {
    const r = rel(p);
    if (r === null || seen.has('D:' + r)) return;
    seen.add('D:' + r);
    const full = underRoot(r);
    let d;
    try {
      const rows = [];
      for (const name of realReaddir(full)) {
        if (name === '__pycache__') continue;
        let st = null;
        try { st = realLstat(path.join(full, name)); } catch (e) { st = null; }
        if (st === null || name.includes('\ufffd')) { d = '?'; break; }  // gone mid-listing, or not UTF-8
        const k = st.isSymbolicLink() ? 'l' : st.isFile() ? 'f' : st.isDirectory() ? 'd' : 'o';
        rows.push(name + '\t' + k + '\t' + ((k === 'f' || k === 'l') ? String(st.size) : '-'));
      }
      if (d === undefined) {
        rows.sort((a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8')));
        d = crypto.createHash('sha256').update(Buffer.from(rows.join('\n'), 'utf8')).digest('hex');
      }
    } catch (e) {
      d = (e && e.code === 'ENOENT') ? '-' : ((e && e.code === 'ENOTDIR') ? 'f' : '?');
    }
    emit('D', d + ' ' + r);  // TRACE-LISTING-FACT
  }
  // a listing: L and its D; a RECURSIVE one (node 20+) reads every folder under it, which no one D names - a U
  const LD = (p, opts) => {
    if (opts && typeof opts === 'object' && opts.recursive) {
      if (rel(p) !== null) emit('U', 'listed a folder recursively (no one D names what it read)');  // TRACE-RECURSIVE
      return;
    }
    L(p);
    D(p);
  };
  // the Z fact: an lstat names a non-link F, D or O (sitecustomize.py's size_of), a followed stat f, d or o
  const sizeOf = (st, follows) => {
    const k = st.isSymbolicLink() ? 'l' : st.isFile() ? 'f' : st.isDirectory() ? 'd' : 'o';
    return (follows || k === 'l' ? k : k.toUpperCase()) + ' ' + ((k === 'f' || k === 'l') ? String(st.size) : '-');
  };
  const S = (p) => {
    const r = rel(p);
    if (r === null) return;
    let there = true;
    let st = null;
    try { st = realLstat(p); } catch (e) { there = false; }
    emit(there ? 'S' : 'A', r);
    if (!st) return;
    emit('Z', sizeOf(st, false) + ' ' + r);  // TRACE-SIZE-FACT
    if (st.isSymbolicLink()) {
      let to = '- -';  // a followed stat finds nothing: the link dangles
      try { to = sizeOf(realStat(p), true); } catch (e) { /* kept as '- -' */ }
      emit('Z', to + ' ' + r);
    }
  };
  const P = fs.promises;
  for (const n of ['readFileSync', 'readFile', 'createReadStream']) wrap(fs, n, RH);
  for (const n of ['readFile']) wrap(P, n, RH);
  // a write that keeps the bytes it finds (append, r+, no truncate) measured them first, as a read does - and so does
  // (REG-2449) an exclusive create ('wx', O_EXCL): it fails on a path that is there, so it looked. Only a truncating
  // write makes a path without looking.
  const keeps = (flags) => (typeof flags === 'string' ? (/x/.test(flags) || !/w/.test(flags))
    : (typeof flags === 'number' && ((flags & fs.constants.O_EXCL) !== 0 || (flags & fs.constants.O_TRUNC) === 0)));
  const opened = (p, flags) => { if (!writes(flags)) { RH(p); return; } if (keeps(flags)) H(p); W(p); };
  for (const n of ['openSync', 'open']) wrap(fs, n, opened);
  wrap(P, 'open', opened);
  for (const n of ['readdirSync', 'readdir', 'opendirSync', 'opendir']) wrap(fs, n, LD);
  for (const n of ['readdir', 'opendir']) wrap(P, n, LD);
  for (const n of ['existsSync', 'statSync', 'lstatSync', 'stat', 'lstat', 'accessSync', 'access', 'exists', 'realpathSync']) wrap(fs, n, S);
  for (const n of ['stat', 'lstat', 'access']) wrap(P, n, S);
  // a writeFile or a write stream with a flag that keeps or refuses what it finds ('a', 'r+', 'wx') measures it first
  const flagOf = (opts, key, dflt) => (opts && typeof opts === 'object' && opts[key] !== undefined ? opts[key] : dflt);
  const wrote = (p, flags) => { if (keeps(flags)) H(p); W(p); };
  for (const n of ['writeFileSync', 'writeFile']) wrap(fs, n, (p, data, opts) => wrote(p, flagOf(opts, 'flag', 'w')));
  wrap(P, 'writeFile', (p, data, opts) => wrote(p, flagOf(opts, 'flag', 'w')));
  wrap(fs, 'createWriteStream', (p, opts) => wrote(p, flagOf(opts, 'flags', 'w')));
  // REG-2449 - mkdir, symlink and link fail on a path that is there: each LOOKED first (S or A, then W), so a run that
  // found the path absent and made it holds the absence
  const looked = (p) => { S(p); W(p); };  // TRACE-LOOKED-FIRST
  for (const n of ['mkdirSync', 'mkdir']) wrap(fs, n, looked);
  wrap(P, 'mkdir', looked);
  for (const n of ['symlinkSync', 'symlink', 'linkSync', 'link']) wrap(fs, n, (a, b) => looked(b));
  for (const n of ['symlink', 'link']) wrap(P, n, (a, b) => looked(b));
  // fs.cp copies a whole tree: its reads and writes go through no call this file wraps
  const copied = (a, b) => {
    if (rel(a) !== null || rel(b) !== null) emit('U', 'copied with fs.cp (its reads and writes reach no wrapped call)');
  };
  for (const n of ['cpSync', 'cp']) wrap(fs, n, copied);
  wrap(P, 'cp', copied);
  for (const n of ['appendFileSync', 'appendFile']) wrap(fs, n, (p) => { H(p); W(p); });
  wrap(P, 'appendFile', (p) => { H(p); W(p); });
  for (const n of ['renameSync', 'rename']) wrap(fs, n, (a, b) => W(b));
  wrap(P, 'rename', (a, b) => W(b));
  for (const n of ['copyFileSync', 'copyFile']) wrap(fs, n, (a, b) => { RH(a); W(b); });
  let kids = 0;
  function child(file, env) {
    const head = path.basename(String(file || ''));
    const source = env || realEnv;
    const traced = source.TV_GATE_TRACE === out;
    const isNode = head === 'node' || head === 'nodejs' || file === process.execPath;
    const isPy = head.startsWith('python');
    if (traced && (isPy || (isNode && String(source.NODE_OPTIONS || '').includes('node_trace.cjs')))) {
      kids += 1;
      emit('P', String(kids), false);
      return;
    }
    if (env && !isPy && !isNode && String(env.TV_GATE_TRACE_CDP || '') === '1' && String(realEnv.TV_GATE_TRACE_CDP || '') !== '1') {
      emit('C', 'started ' + (head || 'a process') + ', a Chrome this run started for its pages');  // TRACE-CDP-ATTESTED
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
  if (isRoot) {
    for (const k of Object.keys(realEnv)) if (!plumbing(k)) emit('N', digestOf(realEnv[k]) + ' ' + k);  // TRACE-ENV-ROOT-BLOCK
  }
  // REG-2442 - E facts: process.env behind a Proxy that tells a single-name read from a bulk one
  const envSeen = new Set();
  const envWritten = new Set();
  let pending = null;
  let enumerating = false;
  const envName = (k) => (win ? String(k).toUpperCase() : String(k));
  function envNote(k) {
    if (busy || typeof k !== 'string') return;
    const name = envName(k);
    if (plumbing(name) || envWritten.has(name) || envSeen.has(name)) return;
    envSeen.add(name);
    const v = Reflect.get(realEnv, k);
    const d = v === undefined ? '-' : (String(v).includes('\ufffd') ? '?' : digestOf(v));
    if (rootEnv !== null && /^[\x00-\x7f]*$/.test(name) && (rootEnv.get(name) || '-') !== d) return;  // TRACE-ENV-MADE
    emit('E', d + ' ' + name);  // TRACE-ENV-FACT
  }
  function settle() { enumerating = false; pending = null; }
  try {
    process.env = new Proxy(realEnv, {
      get(t, k) {
        if (typeof k === 'string') {
          if (pending === k) pending = null;  // a bulk copy reads the name it just enumerated
          else { settle(); envNote(k); }
        }
        return Reflect.get(t, k);
      },
      has(t, k) { settle(); envNote(k); return Reflect.has(t, k); },
      ownKeys(t) { enumerating = true; pending = null; process.nextTick(settle); return Reflect.ownKeys(t); },
      getOwnPropertyDescriptor(t, k) {
        if (enumerating) pending = k;
        else envNote(k);
        return Reflect.getOwnPropertyDescriptor(t, k);
      },
      set(t, k, v) { if (typeof k === 'string') envWritten.add(envName(k)); return Reflect.set(t, k, v); },
      deleteProperty(t, k) { if (typeof k === 'string') envWritten.add(envName(k)); return Reflect.deleteProperty(t, k); },
      defineProperty(t, k, d) { if (typeof k === 'string') envWritten.add(envName(k)); return Reflect.defineProperty(t, k, d); },
    });
  } catch (e) {
    emit('U', 'could not watch its environment');
  }
  const main = process.argv[1];
  const esm = process.execArgv.some((a) => a.startsWith('--input-type=module') || a.startsWith('--experimental-loader') || a.startsWith('--import'));
  if (esm || (main && rel(main) !== null && /\.mjs$/.test(main))) {
    emit('U', 'ran an ES module, whose imports do not go through fs');
  }
  if (main) R(main);
})();
