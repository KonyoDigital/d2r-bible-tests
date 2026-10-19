# -*- coding: utf-8 -*-
"""v3768 — A GATE CARRIES WHEN GIT SAYS ITS INPUTS HAVE NOT MOVED SINCE THE PROOF.

A version was paying for about four full `run_gates` passes, each one re-proving gates whose inputs
had not changed. Hashing every input of every gate on the way back in cost as much as running them.
This ledger does not do that.

A PASS is stored with the commit it was proved at. The next `--changed` run asks git once:

    git diff --name-only <proven_sha>..HEAD
    git status --porcelain

and intersects that set with each gate's inputs. The input map is built once and reused while
`tv/run_gates.py` and `BLUEPRINT.md` are unchanged. A gate whose inputs are not in the set is
printed as `proven at <sha> (<age>)` and its files are not opened.

Fail closed. A missing or unreachable proven sha, a diff that fails, a gate whose inputs cannot
be named, a corrupt ledger, and a FAIL are all a run. Only a PASS is stored. `--full` does not
consult the ledger. GitHub CI does not either. The changed-law red-proof (v3292) is a different
stage and does not read this file.

The files are per checkout, gitignored, and never a verdict of record. CARRY is not a fresh pass
and it does not bank Wilson evidence.

    python3 tv/gate_ledger.py --carry NAME     exit 0 and "proven at <sha> (<age>)", or exit 1
    python3 tv/gate_ledger.py --record NAME    store a PASS for the registered gate
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

LEDGER_NAME = ".gate_ledger.json"
MAP_NAME = ".gate_inputs.json"
# written by the run that reads them — treating them as inputs would rerun every gate
_SELF = frozenset((LEDGER_NAME, LEDGER_NAME + ".tmp", MAP_NAME, MAP_NAME + ".tmp"))
_MAX = 4000
_SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
_SHA = re.compile(r"^[0-9a-f]{7,40}$")
_NODE_DYNAMIC = re.compile(r"\b(readdir|readdirSync|readDir|globSync)\b|\bglob\(")
_REL_IMPORT = re.compile(
    r"""(?:from\s+|import\s+|require\(\s*)['"](\.[^'"]+)['"]""")
_PY_PLAYWRIGHT = re.compile(r"(^|\n)\s*(import playwright\b|from playwright\b)")


def ledger_path():
    """This checkout's ledger, unless TV_GATE_LEDGER names another file. -> path"""
    return os.environ.get("TV_GATE_LEDGER") or os.path.join(HERE, LEDGER_NAME)


def ci_blocks():
    """GitHub is the full run. A ledger on the runner is not a verdict. -> bool"""
    return os.environ.get("GITHUB_ACTIONS") == "true"  # LEDGER-CI


def reuse_closed():
    """GATE_LEDGER=0 is the cold half of a measurement: nothing is carried or stored. -> bool"""
    return os.environ.get("GATE_LEDGER", "1") == "0"  # LEDGER-OFF


def load(path):
    """-> (entries, why). Missing is an empty ledger. Unreadable is why, and entries is None."""
    if not os.path.exists(path):
        return {}, None  # LEDGER-MISSING empty, so the gate runs
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return None, "unreadable (%s)" % type(exc).__name__  # LEDGER-CORRUPT
    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, dict):
        return None, "unreadable (no entries map)"
    return entries, None


def head_sha(root):
    """The commit this proof is labelled with. -> sha | None

    TV_GATE_LEDGER_SHA is the fixture seam. A label that is not a commit in this checkout
    cannot be diffed, so the next lookup runs the gate."""
    forced = os.environ.get("TV_GATE_LEDGER_SHA") or ""
    if _SHA.match(forced):
        return forced
    for cwd in (root, REPO):
        try:
            proc = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        except Exception:
            continue
        sha = (proc.stdout or "").strip()
        if proc.returncode == 0 and _SHA.match(sha):
            return sha
    return None


def _git(root, args):
    """One git invocation. -> CompletedProcess | None"""
    try:
        return subprocess.run(["git", "-C", root] + list(args),
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    except Exception:
        return None


def _file_hash(path):
    """sha256 of one file, or None when it cannot be read. -> hex | None"""
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def map_key(root):
    """The input map is reused while these two files are the same bytes. -> hex"""
    rels = ("tv/run_gates.py", "BLUEPRINT.md")  # LEDGER-MAPKEY
    parts = []
    for rel in rels:
        parts.append(_file_hash(os.path.join(root, rel)) or "absent")
    return hashlib.sha256(b"\0".join(p.encode("ascii") for p in parts)).hexdigest()


def _porcelain(text):
    """Paths from `git status --porcelain`, including both sides of a rename. -> set"""
    out = set()
    for line in (text or "").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip()
        parts = path.split(" -> ") if " -> " in path else [path]
        for part in parts:
            part = part.strip().strip('"').replace("\\", "/")
            if part:
                out.add(part)
    return out


def _node_version():
    try:
        proc = subprocess.run(["node", "--version"], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=10)
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    line = ((proc.stdout or proc.stderr or "").strip().splitlines() or [""])[0]
    return line[:40] or None


def _playwright_version(root):
    for rel in ("node_modules/playwright/package.json",
                "node_modules/playwright-core/package.json"):
        path = os.path.join(root, rel)
        try:
            with open(path, encoding="utf-8") as fh:
                version = str(json.load(fh).get("version") or "")
        except Exception:
            continue
        if version:
            return version[:40]
    return None


def _rel(root, path):
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    if rel.startswith("../") or os.path.isabs(rel):
        return None
    return rel


class Ledger(object):
    def __init__(self, path=None, probes=None):
        self.path = path or ledger_path()
        self.probes = probes
        self._measured = None
        self.entries = None
        self.proven = None
        self.why = None
        self._loaded = False
        self.dropped = set()
        self.reads = 0
        self.map = None
        self.map_hit = False
        self._parsed = {}
        self._tracked_memo = None
        self._tracked_root = None
        self._change_memo = None
        self._change_root = None
        self._change_base = None

    def _ensure(self):
        if self._loaded:
            return
        entries, why = load(self.path)
        self.why = why
        self.entries = entries if isinstance(entries, dict) else {}
        self.proven = None
        if not why and os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as fh:
                    data = json.load(fh)
                sha = str((data or {}).get("proven_sha") or "")
                self.proven = sha if _SHA.match(sha) else None
            except Exception:
                self.proven = None
        self._loaded = True

    def _tools(self, root):
        if self._measured is None:
            if self.probes is not None:
                self._measured = dict(self.probes)
            else:
                self._measured = {
                    "python": "%d.%d.%d" % sys.version_info[:3],
                    "node": _node_version(),
                    "playwright": _playwright_version(root),
                }
        return self._measured

    def _subject(self, gate):
        """The file this gate runs, and which tools apply. -> (path|None, kinds, why|None)"""
        argv = [str(a) for a in (getattr(gate, "argv", None) or [])]
        py = node = None
        for arg in argv:
            if arg.endswith(".py") and os.path.isfile(arg):
                py = os.path.abspath(arg)
            if arg.endswith((".js", ".mjs", ".cjs")) and os.path.isfile(arg):
                node = os.path.abspath(arg)
        script = py or node
        if script is None:
            return None, set(), "the gate names no script file, so its inputs are UNKNOWN"
        parent = os.path.dirname(script)
        if os.path.basename(parent) != "tv":
            return None, set(), "the script is not in a tv/ directory, so its closure is UNKNOWN"
        kinds = set()
        bases = [os.path.basename(a) for a in argv]
        if py or any(os.path.basename(a) in ("python", "python3") or a == sys.executable for a in argv):
            kinds.add("python")
        if node or "node" in bases or "npx" in bases:
            kinds.add("node")
        try:
            with open(script, encoding="utf-8", errors="replace") as fh:
                text = fh.read(200000)
        except OSError:
            return None, set(), "the script cannot be read"
        if _PY_PLAYWRIGHT.search(text) or any("playwright" == b for b in bases):
            kinds.add("playwright")
        if "python" not in kinds and "node" not in kinds:
            kinds.add("python")
        return script, kinds, None

    def _definition(self, gate, root):
        argv = []
        for arg in (getattr(gate, "argv", None) or []):
            text = str(arg)
            if text == sys.executable or os.path.basename(text) in ("python", "python3"):
                argv.append("python")
                continue
            if os.path.isabs(text):
                rel = _rel(root, text)
                argv.append(rel if rel else os.path.basename(text))
            else:
                argv.append(text)
        try:
            cwd = os.path.abspath(getattr(gate, "cwd", None) or root)
            cwd_rel = _rel(root, cwd) or "."
        except Exception:
            cwd_rel = "."
        venue = {
            "needs_app": bool(getattr(gate, "needs_app", False)),
            "skip_ok": list(getattr(gate, "skip_ok", ()) or ()),
            "cwd": cwd_rel,
            "ci": ci_blocks(),
        }
        blob = json.dumps({"argv": argv, "timeout": int(getattr(gate, "timeout", 0) or 0),
                           "venue": venue}, sort_keys=True, default=str)  # LEDGER-DEF
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _tool_parts(self, kinds, root):
        probes = self._tools(root)
        py = probes.get("python")
        if not py:
            return None, "python version is UNKNOWN"
        parts = []
        parts.append("python:%s" % py)  # LEDGER-PY
        if "node" in kinds or "playwright" in kinds:
            node = probes.get("node")
            if not node:
                return None, "node version is UNKNOWN"
            parts.append("node:%s" % node)  # LEDGER-NODE
        if "playwright" in kinds:
            pw = probes.get("playwright")
            if not pw:
                return None, "playwright version is UNKNOWN"
            parts.append("playwright:%s" % pw)  # LEDGER-PW
        return parts, None

    def _tracked(self, root):
        if self._tracked_root != root:
            import heart2 as H
            try:
                self._tracked_memo = H._tracked_files(root)
            except Exception:
                self._tracked_memo = None
            self._tracked_root = root
        return self._tracked_memo

    def _py_inputs(self, script):
        import heart2 as H
        sandbox = os.path.dirname(script)
        root = os.path.dirname(sandbox)
        try:
            found, why = H.law_inputs(
                sandbox, os.path.basename(script), [],
                parsed=self._parsed, tracked=self._tracked(root))
        except Exception as exc:
            return [], "inputs could not be derived (%s)" % type(exc).__name__
        if why:
            return [], why
        paths = list(found)
        for extra in ("gate_ledger.py", "run_gates.py"):
            path = os.path.join(sandbox, extra)
            if os.path.isfile(path):
                paths.append(path)
        return paths, None

    def _node_inputs(self, script):
        try:
            with open(script, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            return [], "the script cannot be read"
        if _NODE_DYNAMIC.search(text):
            return [], "the script lists a directory, so no byte key can name its inputs"
        paths = [script]
        base = os.path.dirname(script)
        for match in _REL_IMPORT.finditer(text):
            spec = match.group(1)
            cand = os.path.normpath(os.path.join(base, spec))
            found = None
            for extra in ("", ".js", ".mjs", ".cjs"):
                path = cand + extra
                if os.path.isfile(path):
                    found = path
                    break
            if found is None:
                return [], "a relative import could not be resolved (%s)" % spec
            paths.append(found)
        return paths, None

    def _inputs(self, script, kinds):
        if script.endswith(".py"):
            return self._py_inputs(script)
        if "node" in kinds or script.endswith((".js", ".mjs", ".cjs")):
            return self._node_inputs(script)
        return [], "the script is not a python or node file"

    def _root_of(self, gates):
        for gate in gates or []:
            for arg in (getattr(gate, "argv", None) or []):
                text = str(arg)
                if not text.endswith((".py", ".js", ".mjs", ".cjs")) or not os.path.isabs(text):
                    continue
                parent = os.path.dirname(text)
                if os.path.basename(parent) == "tv":
                    return os.path.dirname(parent)
        return REPO

    def declare(self, gate):
        """Name the inputs. This is the only path that opens them. -> (decl|None, why)"""
        self.reads += 1
        script, kinds, why = self._subject(gate)
        if why:
            return None, why
        root = os.path.dirname(os.path.dirname(script))
        parts, pwhy = self._tool_parts(kinds, root)
        if pwhy:
            return None, pwhy
        found, iwhy = self._inputs(script, kinds)
        if iwhy:  # LEDGER-UNKEYABLE
            return None, iwhy
        rels = []
        for path in found:
            rel = _rel(root, path)
            if not rel or os.path.basename(rel) in _SELF:
                continue
            rels.append(rel)
        rels = list(rels)  # LEDGER-CLOSURE-ONLY
        return {
            "root": root,
            "def": self._definition(gate, root),
            "tools": list(parts),
            "inputs": sorted(set(rels)),
            "kinds": sorted(kinds),
        }, None

    def key_for(self, gate):
        """-> (key|None, decl, why). The key names the declaration, not the bytes on disk."""
        decl, why = self.declare(gate)
        if why or not decl:
            return None, {}, why or "unkeyable"
        blob = json.dumps({
            "name": str(getattr(gate, "name", "")),
            "def": decl["def"],
            "tools": list(decl["tools"]),
            "inputs": list(decl["inputs"]),
        }, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest(), decl, None

    def _map_file(self):
        return os.path.join(os.path.dirname(self.path) or ".", MAP_NAME)

    def _load_map(self, root):
        key = map_key(root)
        if self.map is not None and self.map.get("key") == key:
            return
        data = None
        path = self._map_file()
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                data = None
        if isinstance(data, dict) and data.get("key") == key and isinstance(data.get("gates"), dict):
            self.map = data
            self.map_hit = True
            return
        self.map = {"v": 1, "key": key, "gates": {}}
        self.map_hit = False

    def _write_map(self):
        path = self._map_file()
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.map, fh, sort_keys=True)
        os.replace(tmp, path)

    def prepare(self, gates):
        """Build the input map once, or load the one already cached for this runner and blueprint."""
        root = self._root_of(gates)
        self._load_map(root)
        names = [getattr(g, "name", None) for g in gates]
        if self.map_hit and all(name in self.map.get("gates", {}) for name in names):
            return
        rows = {}
        for gate in gates:
            try:
                decl, why = self.declare(gate)
            except Exception as exc:
                decl, why = None, "inputs could not be derived (%s)" % type(exc).__name__
            rows[gate.name] = {
                "inputs": None if (why or not decl) else list(decl["inputs"]),
                "why": why,
                "kinds": [] if (why or not decl) else list(decl["kinds"]),
                "def": None if (why or not decl) else decl["def"],
            }
        self.map = {"v": 1, "key": map_key(root), "gates": rows}
        self.map_hit = False
        self._write_map()

    def _map_row(self, gate, root):
        self._load_map(root)
        row = (self.map.get("gates") or {}).get(gate.name)
        if isinstance(row, dict):
            return row
        try:
            decl, why = self.declare(gate)
        except Exception as exc:
            decl, why = None, "inputs could not be derived (%s)" % type(exc).__name__
        row = {
            "inputs": None if (why or not decl) else list(decl["inputs"]),
            "why": why,
            "kinds": [] if (why or not decl) else list(decl["kinds"]),
            "def": None if (why or not decl) else decl["def"],
        }
        self.map.setdefault("gates", {})[gate.name] = row
        try:
            self._write_map()
        except Exception:
            pass
        return row

    def git_changed(self, root, proven):
        """Files that moved since the proven commit, plus the dirty worktree. -> (set|None, why)"""
        out = ""
        status_out = ""
        cat_rc = diff_rc = stat_rc = 1
        if proven and _SHA.match(proven):
            cat = _git(root, ["cat-file", "-e", "%s^{commit}" % proven])
            diff = _git(root, ["diff", "--name-only", "%s..HEAD" % proven])
            stat = _git(root, ["status", "--porcelain"])
            if cat is not None:
                cat_rc = cat.returncode
            if diff is not None:
                diff_rc = diff.returncode
                out = diff.stdout or ""
            if stat is not None:
                stat_rc = stat.returncode
                status_out = stat.stdout or ""
        if cat_rc != 0 or diff_rc != 0 or stat_rc != 0:  # LEDGER-SHA
            return None, "the proven sha cannot be diffed"
        changed = set(p.strip() for p in out.splitlines() if p.strip())  # LEDGER-DIFF
        changed |= _porcelain(status_out)  # LEDGER-STATUS
        changed = {p.replace("\\", "/") for p in changed}
        changed -= _SELF
        changed -= set("tv/" + name for name in _SELF)
        return changed, None

    def _changes(self, root):
        if (self._change_memo is not None and self._change_root == root
                and self._change_base == self.proven):
            return self._change_memo
        self._change_root = root
        self._change_base = self.proven
        self._change_memo = self.git_changed(root, self.proven)
        return self._change_memo

    def carry_line(self, entry):
        """'proven at <sha> (<age>)', or None when the row cannot be dated."""
        sha = str((entry or {}).get("sha") or "")
        if not _SHA.match(sha):
            return None
        try:
            import heart2 as H
            age = H._age_say(float(entry.get("at")))
        except Exception:
            return None
        if not age or age == "an UNKNOWN time":
            return None
        return "proven at %s (%s)" % (sha, age)

    def lookup(self, gate):
        """-> (entry|None, why). A hit did not open the gate's inputs."""
        if reuse_closed():
            return None, "GATE_LEDGER=0 — every gate runs"
        if ci_blocks():
            return None, "CI runs the full set — the ledger is not a verdict here"
        self._ensure()
        if self.why:
            return None, self.why
        name = getattr(gate, "name", None)
        entry = self.entries.get(name) if isinstance(self.entries, dict) else None
        if not isinstance(entry, dict) or entry.get("ok") is not True:  # LEDGER-ONLY-PASS
            return None, "no stored PASS for this gate"
        if entry.get("gate") != name:
            return None, "the stored row does not match this gate"
        root = self._root_of([gate])
        if entry.get("def") != self._definition(gate, root):
            return None, "the definition changed"
        if entry.get("sha") != self.proven:
            return None, "the stored PASS is not the proven sha"
        stored = [str(t) for t in (entry.get("tools") or [])]
        live, tw = self._tools_for(stored, root)
        if tw:
            return None, tw
        if live != stored:
            return None, "a tool version changed"
        try:
            row = self._map_row(gate, root)
        except Exception as exc:
            return None, "taking its inputs raised %s" % type(exc).__name__
        if not isinstance(row, dict) or row.get("why") or not isinstance(row.get("inputs"), list):
            return None, (row or {}).get("why") or "inputs are UNKNOWN"
        changed, cwhy = self._changes(root)
        if cwhy or changed is None:
            return None, cwhy or "the proven sha cannot be diffed"
        hit = [p for p in row["inputs"] if p in changed]
        if hit:
            return None, "inputs changed: %s" % hit[0]
        line = self.carry_line(entry)
        if not line:
            return None, "the stored PASS has no sha or no age"
        shown = dict(entry)
        shown["line"] = line
        return shown, None  # LEDGER-NO-BANK

    def _tools_for(self, stored, root):
        """Live versions for the tool names already stored. -> (list|None, why)"""
        probes = self._tools(root)
        live = []
        for item in stored:
            kind, _, _ver = item.partition(":")
            cur = probes.get(kind)
            if not cur:
                return None, "%s version is UNKNOWN" % (kind or "tool")
            live.append("%s:%s" % (kind, cur))
        return live, None

    def _write(self):
        if os.path.basename(self.path) != LEDGER_NAME:
            return False
        if len(self.entries) > _MAX:
            ranked = sorted(self.entries, key=lambda k: (self.entries[k] or {}).get("at") or 0)
            for old in ranked[:len(self.entries) - _MAX]:
                self.entries.pop(old, None)
        disk, why = load(self.path)
        if isinstance(disk, dict) and not why:
            for name, entry in disk.items():
                if name in self.dropped or name in self.entries:
                    continue
                if isinstance(entry, dict) and entry.get("ok") is True and entry.get("gate") == name:
                    self.entries[name] = entry
        folder = os.path.dirname(self.path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"v": 2, "proven_sha": self.proven, "entries": self.entries}, fh, sort_keys=True)
        os.replace(tmp, self.path)
        self.why = None
        return True

    def record(self, gate, ok):
        """Store a PASS. A FAIL deletes that gate and is never written. -> bool (stored)"""
        if reuse_closed() or ci_blocks():
            return False
        name = str(getattr(gate, "name", "") or "")
        root = self._root_of([gate])
        try:
            row = self._map_row(gate, root)
        except Exception:
            return False
        why = (row or {}).get("why")
        if ok is not True or why or not isinstance((row or {}).get("inputs"), list):  # LEDGER-NO-FAIL
            if name:
                self._drop(name)
            return False
        parts, pwhy = self._tool_parts(set(row.get("kinds") or []), root)
        if pwhy or not parts:
            if name:
                self._drop(name)
            return False
        sha = head_sha(root)
        if not sha:
            return False
        self._ensure()
        if self.entries is None:
            self.entries = {}
        self.dropped.discard(name)
        self.proven = sha
        self.entries[name] = {
            "ok": True,
            "gate": name,
            "sha": sha,
            "at": int(time.time() * 1000),
            "def": self._definition(gate, root),
            "tools": list(parts),
        }
        self._write()
        return True

    def _drop(self, name):
        self._ensure()
        if not isinstance(self.entries, dict):
            self.entries = {}
        self.entries.pop(name, None)  # LEDGER-DROP-FAIL
        self.dropped.add(name)
        if os.path.exists(self.path) or self.entries:
            try:
                self._write()
            except Exception:
                pass


def _gate(name):
    import run_gates
    for gate in run_gates.GATES:
        if gate.name == name:
            return gate
    return None


def main(argv):
    import argparse
    parser = argparse.ArgumentParser(description="carry or record one gate's PASS")
    parser.add_argument("--carry", metavar="GATE")
    parser.add_argument("--record", metavar="GATE")
    args = parser.parse_args(argv[1:])
    if bool(args.carry) == bool(args.record):
        print("ledger: name one of --carry or --record")
        return 2
    name = args.carry or args.record
    if not _SAFE.match(name or ""):
        print("ledger: %s is not a gate name" % name)
        return 1
    gate = _gate(name)
    if gate is None:
        print("ledger: %s is not a registered gate — it runs" % name)
        return 1
    led = Ledger()
    if args.carry:
        entry, why = led.lookup(gate)
        if entry is None:
            print("ledger: %s runs — %s" % (name, why))
            return 1
        print(entry["line"])
        return 0
    if led.record(gate, True):
        print("ledger: %s PASS recorded" % name)
        return 0
    print("ledger: %s was not recorded — the next run will execute it" % name)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
