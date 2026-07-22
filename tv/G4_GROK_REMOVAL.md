# G4 Grok add-on — removal guide + "lifts out clean" proof

The G4 Grok accuracy layer is a **self-contained, removable bolt-on** (Konyo's mandate:
"implement it to be taken out eventually"). It is OFF by default, cousin-safe, and needs
Konyo's own xAI key — so on any machine without the key + toggle it is already inert and
byte-identical to a build with no G4 at all.

## What it is (all the pieces)
- **`tv/g4_grok.py`** — the whole module: toggle (switch AND key), credit budget
  (hourly + daily), per-seam config, `g4_verify()`, `status()`, `_g4_collect_flags` reader.
- **`tv/control_app.py`** — fenced blocks only, each delimited by
  `# ══ GROK ADD-ON (G4) ══` … `# ══ END GROK ADD-ON (G4) ══`:
  the module shim + status/flags/toggle routes, and the 3 touchpoints
  (seal-time chronicle re-check; `/kai_verdict` keep/toss band; `/kai_verdict` grail promotion).
- **`bible.html`** — the `#g4-toggle-card` markup + the `// ══ GROK ADD-ON (G4) ══` script
  block (toggle + "🟣 Grok caught this" review surface), both fenced.
- **`.gitignore`** — `tv/g4_grok.state` (per-machine toggle state).

Every trace is found by: `grep -rn "GROK ADD-ON\|g4_grok\|_g4" .`

## Remove it (zero scars)
1. `rm tv/g4_grok.py`
2. Delete every fenced block — the marker lines are anchored (the marker sits right after
   the comment opener), so prose that *mentions* the marker is never a false match:
   ```
   python3 - <<'PY'
   import re
   START=re.compile(r'^\s*(#|//|<!--)\s*══ GROK ADD-ON \(G4\)')
   END  =re.compile(r'^\s*(#|//|<!--)\s*══ END GROK ADD-ON \(G4\)')
   for path in ("tv/control_app.py","bible.html"):
       out,skip=[],False
       for ln in open(path,encoding="utf-8"):
           if not skip and START.search(ln): skip=True; continue
           if skip and END.search(ln): skip=False; continue
           if not skip: out.append(ln)
       open(path,"w",encoding="utf-8").write("".join(out))
   PY
   ```
3. (optional) drop the `tv/g4_grok.state` line from `.gitignore`.

## Proof it lifts out clean (verified 2026-07-23, on scratch copies)
Ran the stripper above against copies of both files:
- **control_app.py** — `python3 -m py_compile` passes · **0 G4 traces** · `_g4_verify` gone · the
  G3 auto-route sweep returns identical results (sunders 4/6, runes 32, gems 33, 74 candidates).
- **bible.html** — all 16 inline scripts `new Function`-compile · **0 G4 traces**.
- Removal takes out ~190 lines from control_app.py and ~170 from bible.html, plus the module.

Because every touchpoint's `_g4_verify()` returns `None` the instant the add-on is OFF/un-keyed,
the running app is **already** byte-identical to the removed state until Konyo sets a key and
flips the toggle. Removal just deletes dormant code.
