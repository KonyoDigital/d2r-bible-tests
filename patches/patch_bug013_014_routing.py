#!/usr/bin/env python3
"""
BUG-013 — TZ-zone card click → openBossDetail (when zone maps to one of the 11 bosses)
BUG-014 — Calc source-chip Cmd/Ctrl+click → openBossDetail (in addition to existing jump-to-boss-card)

Mapping (zone name fragment → boss id):
  Catacombs L4         → andariel
  Tristram             → null  (Smith/Bone Ash/Rakanishu/Griswold — not 11 main)
  Burial Grounds       → null  (Blood Raven not in 11)
  Halls of Anguish     → nihl
  Worldstone Keep      → baal   (chain into throne)
  River of Flame       → diablo
  Pit                  → pit
  Mephisto             → mephisto
  Countess             → countess
  Travincal            → travincal
  Cows                 → cows
  Pindle               → pindle

Idempotent: sentinel "/* BUG-013 tz-routing */"
"""
import sys, shutil, time

BIBLE = "/Users/konyo/d2r_bible_tests/bible.html"
SENTINEL = "/* BUG-013 tz-routing */"

with open(BIBLE) as f: src = f.read()
if SENTINEL in src:
    print("BUG-013 already applied. Skipping.")
    sys.exit(0)

orig_len = len(src)

# === 1. Add zone → boss mapping function + click handler injection in renderTzZones ===
# Patch the renderTzZones function template: add data-boss-id + onclick on the .tz-zone-card div.
tz_anchor = "function renderTzZones() {"
tz_new = """/* BUG-013 tz-routing */
const TZ_BOSS_MAP = (function(){
  // Substring → boss id lookup
  return [
    {re:/catacombs/i, boss:'andariel'},
    {re:/halls of anguish|nihl/i, boss:'nihl'},
    {re:/worldstone keep|wsk/i, boss:'baal'},
    {re:/river of flame|chaos/i, boss:'diablo'},
    {re:/pit$|the pit/i, boss:'pit'},
    {re:/mephisto/i, boss:'mephisto'},
    {re:/countess|forgotten tower/i, boss:'countess'},
    {re:/travincal/i, boss:'travincal'},
    {re:/moo moo|cow level/i, boss:'cows'},
    {re:/pindle|nihlathak.s temple/i, boss:'pindle'},
    {re:/duriel|tomb/i, boss:'duriel'},
  ];
})();
function tzZoneBoss(zoneName){
  for(const m of TZ_BOSS_MAP){ if(m.re.test(zoneName)) return m.boss; }
  return null;
}
function renderTzZones() {"""
assert tz_anchor in src, "tz anchor missing"
src = src.replace(tz_anchor, tz_new, 1)

# === 2. Inject data-boss-id + onclick on .tz-zone-card div template ===
zone_card_anchor = '''return `<div class="tz-zone-card">
      <div class="tz-zone-header">'''
zone_card_new = '''const _bossId = tzZoneBoss(z.name);
    const _bossAttr = _bossId ? ` data-boss-id="${_bossId}" style="cursor:pointer" onclick="openBossDetail('${_bossId}')" title="click to open ${_bossId} detail"` : '';
    return `<div class="tz-zone-card${_bossId?' has-boss':''}"${_bossAttr}>
      <div class="tz-zone-header">'''
assert zone_card_anchor in src, "zone card anchor missing"
src = src.replace(zone_card_anchor, zone_card_new, 1)

# Add CSS for .tz-zone-card.has-boss
css_anchor = ".tz-zone-card{background:linear-gradient(180deg,var(--surface) 0%,var(--surface-2) 100%);border:1px solid var(--border);border-left:3px solid var(--terror);border-radius:8px;margin:10px 0;padding:14px 18px}"
css_new = css_anchor + "\n.tz-zone-card.has-boss{cursor:pointer;transition:all .15s}\n.tz-zone-card.has-boss:hover{border-left-color:var(--gold);transform:translateX(2px);box-shadow:0 4px 14px rgba(0,0,0,.4)}\n.tz-zone-card.has-boss::after{content:'↗ open boss detail';position:absolute;bottom:8px;right:14px;color:var(--gold);font-size:10px;letter-spacing:.4px;opacity:0;transition:opacity .15s;font-family:var(--mono,monospace)}\n.tz-zone-card.has-boss{position:relative}\n.tz-zone-card.has-boss:hover::after{opacity:1}\n"
assert css_anchor in src
src = src.replace(css_anchor, css_new, 1)

# === 3. BUG-014: Add Cmd/Ctrl+click on source chips → openBossDetail ===
# Current source-chip: onclick="setActiveItem(...);switchTab('bosses');..."
# Add a second handler — wrap onclick to detect modifier key.
# Simpler approach: add event listener at document level (delegation) that intercepts when meta/ctrl pressed on .source-chip
js_anchor = "/* BUG-010 boss-detail-fn */"
js_new_lines = """/* BUG-014 calc-chip-detail-route */
document.addEventListener('click', function(e){
  const chip = e.target.closest('.source-chip, .best-source-box');
  if(!chip) return;
  if(!(e.metaKey || e.ctrlKey)) return; // only on Cmd/Ctrl click
  // Try to find boss id from onclick attr (looks for setActiveItem(...,'<bossId>',...))
  const oh = chip.getAttribute('onclick') || '';
  const m = oh.match(/setActiveItem\\([^,]+,\\s*'([a-z]+)'/);
  if(m && typeof openBossDetail === 'function'){
    e.preventDefault();
    e.stopImmediatePropagation();
    openBossDetail(m[1]);
  }
}, true);
""" + "/* BUG-010 boss-detail-fn */"
assert js_anchor in src
src = src.replace(js_anchor, js_new_lines, 1)

# Save
bak = BIBLE + ".bak_bug013_014_" + time.strftime("%Y%m%d_%H%M%S")
shutil.copy(BIBLE, bak)
with open(BIBLE, "w") as f: f.write(src)
print(f"BUG-013/014 applied. {orig_len} → {len(src)} chars (+{len(src)-orig_len}). Backup: {bak}")
