# 🏗️ PER-ENGINE PERFECTION ROADMAP — polish each of the 4 engines individually (Konyo, 2026-07-21)

> "We need to perfect this individually — each — and polish the fuck out of it. A hundred versions between
> all of them at least. Serious Konyo-workflow time."

The 4 engines are separate beasts BY DESIGN so each can be perfected independently, then made to behave as
one (the Master Brain) and seen as one (the Engine Room). This is the ~100+ version commitment: a deep
polish arc PER engine, run Konyo-workflow style (agent army · Fable gates · Grok third-eye · version/round).

## THE 4 ENGINES + their perfection arcs

### 1. 📷 CAPTURE ENGINE (tv_diablo.py — film thread, capture_mac, pin)
Job: take every screenshot, ground truth. Perfect: 0 drops at any speed, pin robustness (no false "waiting"),
fps stability, white/blank-frame rejection, screen-recording grant resilience. Metric: film completeness =
100% real frames, 0 drops on fast runs.

### 2. 👁 READ ENGINE (tv_diablo.py — the 5-layer stack: live · second · closer · super-analyze)
Job: the AI brains that read. Perfect: KILL the 66s stall (fast, bounded reads), second-eye drains under
load, the 4th super-analyze deep-retro organ, OCR quality, text-eye trigger tuning. Metric: every captured
item ends verified-read or honest-miss; live+retro converge; no layer silently starves.

### 3. 🚦 ROUTE / GATE ENGINE (control_app.py — router, quorum, accuracy gate)
Job: accuracy — label, filter, route to the correct cell. Perfect: quorum tuning, cell-correctness, the
ping-pong verification mesh (§3.5), disagreement policy, dedupe. Metric: proven/held ratio honest; 0 wrong-
cell routes; every misread weeded BEFORE a cell.

### 4. 🩹 FUNNEL / INTAKE ENGINE (control_app.py closer + bible.html intakes + functions/api/intake.js)
Job: the hands — count/tier into cells. Perfect: never-zero on ALL cells, no-clobber (max-verified wins),
receipt integrity (no silent drops), the LOCKED intake accuracy (crops untouched), judge tiering. Metric:
no good tally ever demolished; every fire lands an honest receipt.

### + THE MASTER BRAIN (reconciler) and THE ENGINE ROOM (cockpit) — built ON TOP once the 4 are solid.

## COLLISION-SAFE SEQUENCING (the one-owner-per-file law, at scale)
- **Capture + Read** share `tv_diablo.py` → SEQUENTIAL rounds (one engine agent at a time on it), Fable gates between.
- **Route/Gate + Funnel** share `tv/control_app.py` → SEQUENTIAL rounds, Fable gates between.
- **Parallel lanes (different files, safe together):** `tv/stash_eye.py` (classifier), `functions/api/intake.js`
  (backend, NO crop-fraction changes), `bible.html` (intakes/legend, EDIT_LOCK), `control_ui.html` (polish-ui-2 / cockpit).
- **Read-only fleets** (critique/audit/forensic panels via Workflow) run anytime, no collision.
- Fable is the serializer: gate → commit → version → dispatch next. Each round is a version toward the 100+.

## CADENCE
Konyo-workflow: army spawns per-engine rounds · Fable gates every merge · Grok third-eyes via GitHub dossiers
(FORENSIC_CROSSREF pattern) · version-per-round · one final ping per arc. Guardrails: green floor every ship,
smoke on bible/spec, NEVER the full Playwright suite on the Mac, LOCKED intake crops untouched.

_Four beasts, each perfected. Then one Ninja. Then Level 2 at v2000._ 🥷
