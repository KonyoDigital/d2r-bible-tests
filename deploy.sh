#!/usr/bin/env bash
# deploy.sh — publish the D2R Bible live to Cloudflare Pages
# (project `d2r-bible` → bull-4-u.com). Ships bible.html as index.html plus the
# self-hosted item art (art/) and the AI-vision API (functions/api/intake.js).
#
# Run it by hand anytime:   bash deploy.sh
# It is ALSO invoked automatically by hooks/pre-push after the smoke gate passes
# on a push to main that touches bible.html / art / functions (see that hook).
#
# Auth: needs CLOUDFLARE_API_TOKEN in the env (set in ~/.zshenv, scope Pages:Edit).
# The non-interactive shell sources ~/.zshenv, so it's present on hook runs too.
# Exit codes: 0 = deployed, 2 = skipped (missing token/npx), 1 = deploy failed.
set -u

REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "deploy: not in a git repo."; exit 1; }
cd "$REPO" || exit 1

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "deploy: CLOUDFLARE_API_TOKEN not set — skipping (set it in ~/.zshenv, scope Pages:Edit)."
  exit 2
fi
if ! command -v npx >/dev/null 2>&1; then
  echo "deploy: npx not found on PATH — cannot deploy."
  exit 2
fi
for d in bible.html art functions; do
  if [ ! -e "$d" ]; then echo "deploy: missing '$d' — aborting."; exit 1; fi
done

DIST="$(mktemp -d -t d2r_dist.XXXXXX)" || { echo "deploy: mktemp failed."; exit 1; }
trap 'rm -rf "$DIST"' EXIT
mkdir -p "$DIST/d2r"
cp bible.html "$DIST/d2r/index.html"   # served at /d2r/
cp -R art "$DIST/d2r/art"              # MUST include — self-hosted item art
cp -R functions "$DIST/functions"      # MUST include — api/intake.js (AI vision)
# v657 — CACHE LOCKDOWN: Konyo's tabs kept serving WEEKS-old HTML from browser cache for URLs
# with stale ?v=/?cb= params (the recurring 'this bug is still there' ghost — routines widget,
# tooltip fixes, all of it). The HTML must always revalidate; the art can cache forever.
cat > "$DIST/_headers" <<'HDRS'
/d2r/
  Cache-Control: no-cache, must-revalidate
/d2r/index.html
  Cache-Control: no-cache, must-revalidate
/d2r/art/*
  Cache-Control: public, max-age=604800, immutable
HDRS

echo "deploy: publishing to Cloudflare Pages (d2r-bible → bull-4-u.com)…"
if npx wrangler pages deploy "$DIST" --project-name=d2r-bible --branch=main; then
  echo "deploy: ✨ live."
  exit 0
fi
echo "deploy: FAILED — site NOT updated. Re-run: bash deploy.sh"
exit 1
