# G5 Grok Eyes — removal guide + subscription contract

**EXTRA vision lane** (shadow / future primary). OFF by default. Claude path stays when OFF.

## POWER (non-negotiable)
| | |
|--|--|
| **Uses** | Local `grok -p` + SuperGrok **login** (OIDC / `grok login`) |
| **Does NOT use** | `XAI_API_KEY`, console API tokens, `api.x.ai` Bearer calls |
| **Same spirit as** | Claude lane: `claude -p` + subscription OAuth (API keys stripped) |

## Cousin contract
- No Grok / not logged in → leave **OFF** → console identical to today
- Toggle under **⚙ advanced** only; never blocks ON AIR when off
- No API key required of anyone

## Pieces
| Path | Role |
|------|------|
| `tv/g5_grok_eyes.py` | Subscription CLI vision + toggle |
| `tv/g5_sidecar/` | Isolated prove server (same CLI) |
| Fenced `# ══ GROK EYES (G5) ══` in `tv_diablo.py`, `control_app.py`, `control_ui.html` | Thin hooks |
| `tv/g5_grok_eyes.state` | Mode (gitignored) |
| `tv/g5_shadow.jsonl` | Shadow log (gitignored) |
| `tv/g5_subscription_budget.json` | Local hourly/daily caps (gitignored) |

## Modes
| Mode | Behavior |
|------|----------|
| **off** | No CLI calls |
| **shadow** | Claude drives; `grok -p` logs parallel |
| **primary** | `grok -p` drives vision; Claude if Grok fails |

## Install + authorize (v1381.2)
```bash
# IRM installers install the Grok CLI (like Claude Code) — optional, never blocks cousin
# Windows:  irm https://bull-4-u.com/d2r/install-tvd.ps1 | iex   # includes Git/Python/Claude/Grok
# Mac:      curl -fsSL https://bull-4-u.com/d2r/install-tvd.sh | bash
# Manual Grok only:
#   Windows:  irm https://x.ai/cli/install.ps1 | iex
#   Mac:      curl -fsSL https://x.ai/cli/install.sh | bash

# once per PC (browser SuperGrok OIDC — NO API keys):
# console: ⚙ advanced → ⚡ Authorize   (or: grok login)
# no-spam: if ~/.grok/auth.json already valid, button shows ⚡ Linked and does not re-open browser
```

## Toggle
```bash
# once:  grok login   OR console ⚡ Authorize
# console: ⚙ advanced → Grok Eyes  OFF | SHADOW | PRIMARY
# or HTTP:
# GET  /api/g5_status
# POST /api/g5_toggle  {"mode":"off"|"shadow"|"primary"}
# POST /api/g5_login   {"oauth":true,"setPrimary":true}   # v1381.2 authorize
```

## Remove
1. `rm tv/g5_grok_eyes.py tv/G5_*.md`
2. `rm -rf tv/g5_sidecar`
3. Delete every `GROK EYES (G5)` fence
4. Drop gitignore lines for g5_* if desired

## Prove (subscription, no API key)
```bash
# ensure logged in (SuperGrok) — do NOT export XAI_API_KEY
grok -p "ping" --output-format plain --always-approve

python3 tv/g5_sidecar/server.py
# POST /read with a real frame path
```
