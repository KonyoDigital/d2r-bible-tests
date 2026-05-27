#!/usr/bin/env python3
"""
BUG-010 — Universal boss detail panel (Patch Trinity step 2)

Adds:
  - CSS for .boss-detail-overlay / .boss-detail-card / .boss-detail-close
  - HTML <div id="boss-detail-overlay" class="boss-detail-overlay hidden">…</div>
  - JS openBossDetail(bossId, focusDiff) / closeBossDetail()
  - Boss-header click -> openBossDetail (BUG-012)
  - Boss-nav chip click -> openBossDetail (BUG-011 / BUG-012)
  - Escape key closes overlay

Idempotent: looks for unique sentinel '/* BUG-010 boss-detail */' before injecting.
"""
import sys, shutil, os, re, time

BIBLE = "/Users/konyo/d2r_bible_tests/bible.html"
SENTINEL = "/* BUG-010 boss-detail */"

with open(BIBLE, "r", encoding="utf-8") as f:
    src = f.read()

if SENTINEL in src:
    print("BUG-010 already applied — sentinel found. Skipping.")
    sys.exit(0)

orig_len = len(src)

# === 1. CSS block (insert before existing .boss-nav rule) ===
css_anchor = ".boss-nav{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 16px;padding:8px 0;border-bottom:1px solid var(--border)}"
css_new = """/* BUG-010 boss-detail */
.boss-detail-overlay{position:fixed;inset:0;background:rgba(8,10,15,.86);backdrop-filter:blur(6px);z-index:9000;display:flex;align-items:flex-start;justify-content:center;padding:40px 20px;overflow-y:auto}
.boss-detail-overlay.hidden{display:none}
.boss-detail-card{background:linear-gradient(180deg,var(--surface) 0%,var(--surface-2) 100%);border:2px solid var(--gold);border-radius:14px;max-width:1120px;width:100%;box-shadow:0 24px 64px rgba(0,0,0,.7),0 0 0 1px rgba(255,208,64,.18);position:relative;overflow:hidden}
.boss-detail-header{background:linear-gradient(90deg,var(--surface-3),var(--surface-2));border-bottom:1px solid var(--gold);padding:22px 28px;display:flex;align-items:center;gap:18px;position:relative}
.boss-detail-header .boss-emoji{font-size:54px;line-height:1;text-shadow:0 0 18px rgba(255,208,64,.5)}
.boss-detail-header .bd-title{flex:1}
.boss-detail-header .bd-name{font-size:26px;font-weight:700;color:var(--gold);letter-spacing:.4px;margin:0;font-family:var(--mono,monospace);text-transform:uppercase}
.boss-detail-header .bd-sub{font-size:14px;color:var(--text-muted);margin:4px 0 0}
.boss-detail-header .bd-loc{font-size:12px;color:var(--text-muted);margin:6px 0 0;letter-spacing:.3px}
.boss-detail-close{position:absolute;top:14px;right:14px;background:rgba(0,0,0,.4);border:1px solid var(--border);color:var(--text);width:36px;height:36px;border-radius:50%;cursor:pointer;font-size:18px;line-height:1;display:flex;align-items:center;justify-content:center;transition:all .15s}
.boss-detail-close:hover{background:var(--terror);border-color:var(--terror);color:#fff;transform:rotate(90deg)}
.boss-detail-body{padding:22px 28px}
.boss-detail-body h3{color:var(--gold);text-transform:uppercase;letter-spacing:.6px;font-size:13px;margin:20px 0 10px;border-bottom:1px solid var(--border);padding-bottom:6px}
.boss-detail-body h3:first-child{margin-top:0}
.bd-diff-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:0 0 18px}
.bd-diff-cell{background:var(--surface-2);border:1px solid var(--border);border-radius:8px;padding:10px 12px;cursor:pointer;transition:all .15s}
.bd-diff-cell:hover{border-color:var(--gold);transform:translateY(-2px);box-shadow:0 6px 14px rgba(0,0,0,.4)}
.bd-diff-cell.terror{border-color:var(--terror);box-shadow:0 0 0 1px var(--terror) inset}
.bd-diff-cell.active{border-color:var(--gold);background:rgba(255,208,64,.08);box-shadow:0 0 0 2px var(--gold)}
.bd-diff-label{font-size:11px;color:var(--text-muted);letter-spacing:.5px;text-transform:uppercase;font-family:var(--mono,monospace)}
.bd-diff-stat{font-size:18px;font-weight:700;color:var(--gold);margin:4px 0 2px}
.bd-diff-tc{font-size:11px;color:var(--text-muted)}
.bd-meta-row{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}
.bd-meta-chip{background:var(--surface-3);border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:12px;color:var(--text)}
.bd-meta-chip strong{color:var(--gold);margin-right:6px}
.bd-actions{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 8px}
.bd-action-btn{background:var(--surface-3);border:1px solid var(--border);color:var(--text);padding:8px 14px;border-radius:6px;cursor:pointer;font-size:12px;letter-spacing:.3px;transition:all .15s}
.bd-action-btn:hover{border-color:var(--gold);color:var(--gold);background:rgba(255,208,64,.06)}
.bd-action-btn.primary{background:var(--gold);color:#1a1408;border-color:var(--gold);font-weight:600}
.bd-action-btn.primary:hover{background:#ffe28a}
.boss-header.clickable{cursor:pointer;transition:background .2s}
.boss-header.clickable:hover{background:linear-gradient(90deg,var(--surface-2),var(--surface-3))}
.boss-header.flash{animation:bossFlash 1.2s ease-out}
@keyframes bossFlash{0%{box-shadow:inset 0 0 0 3px var(--gold),0 0 24px var(--gold)}100%{box-shadow:inset 0 0 0 0 transparent,0 0 0 transparent}}
.boss-chip.flash{animation:chipFlash .8s ease-out}
@keyframes chipFlash{0%{background:var(--gold);color:#1a1408}100%{background:transparent;color:inherit}}
@media(max-width:680px){.boss-detail-overlay{padding:10px}.boss-detail-header{padding:14px 16px;flex-wrap:wrap}.boss-detail-header .boss-emoji{font-size:40px}.boss-detail-header .bd-name{font-size:20px}.boss-detail-body{padding:14px 16px}}
"""
assert css_anchor in src, "CSS anchor missing"
src = src.replace(css_anchor, css_new + css_anchor, 1)

# === 2. HTML overlay container (insert after #boss-cards div) ===
html_anchor = '<div id="boss-cards"></div>'
html_new = html_anchor + '\n  <div id="boss-detail-overlay" class="boss-detail-overlay hidden" onclick="if(event.target===this)closeBossDetail()"><div class="boss-detail-card" id="boss-detail-card"></div></div>'
assert html_anchor in src
src = src.replace(html_anchor, html_new, 1)

# === 3. JS functions (insert after setBossSort) ===
js_anchor = "function setBossFilter(bossId, mode) { bossFilters[bossId] = mode; persist(); renderBossCards(); }"
js_new = js_anchor + """

/* BUG-010 boss-detail-fn */
function openBossDetail(bossId, focusDiff){
  const boss = BOSSES.find(b => b.id === bossId);
  if(!boss){ console.warn('openBossDetail: boss not found:', bossId); return; }
  const mf = (typeof currentMF === 'function') ? currentMF() : (window.mfValue || 300);
  const card = document.getElementById('boss-detail-card');
  // Build diff cells — show effective best-chance per difficulty using boss bestDropAt if available
  const fmtChance = (c) => c==null ? '<span style="color:var(--text-muted)">—</span>' : '1:'+c.toLocaleString();
  // Find best (lowest non-null) drop chance per difficulty across all dropTable rows
  function bestPerDiff(diffKey){
    let best = null, bestItem = null;
    (boss.dropTable||[]).forEach(it => {
      const v = it[diffKey];
      if(v != null && (best===null || v < best)){ best = v; bestItem = it.n; }
    });
    return {chance:best, item:bestItem};
  }
  const diffsHtml = (boss.diffs||[]).map(d => {
    const key = d.label.toLowerCase().replace(' ','');
    const keyMap = {'norm':'norm','normtz':'normTz','nm':'nm','nmtz':'nmTz','hell':'hell','helltz':'hellTz'};
    const k = keyMap[key] || key;
    const bp = bestPerDiff(k);
    const isFocus = focusDiff && (focusDiff === k);
    const cls = ['bd-diff-cell', d.terror?'terror':'', isFocus?'active':''].filter(Boolean).join(' ');
    return `<div class="${cls}" onclick="setBossDetailFocus('${boss.id}','${k}')">
      <div class="bd-diff-label">${d.label}</div>
      <div class="bd-diff-stat">${fmtChance(bp.chance)}</div>
      <div class="bd-diff-tc">mlvl ${d.mlvl} · TC≤${d.tcMax}${bp.item?' · '+bp.item:''}</div>
    </div>`;
  }).join('');
  // Drop table — abbreviated (top 12 by best non-null chance)
  const rows = (boss.dropTable||[]).slice().map(it => {
    const allVals = ['norm','normTz','nm','nmTz','hell','hellTz'].map(k => it[k]).filter(v => v!=null);
    const best = allVals.length ? Math.min(...allVals) : Infinity;
    return {...it, _best: best};
  }).sort((a,b) => a._best - b._best).slice(0, 12);
  const dropHtml = rows.map(it => {
    const escN = (it.n||'').replace(/'/g,"\\\\'");
    return `<tr style="cursor:pointer" onclick="closeBossDetail();selectedItem='${escN}';switchTab('calc');renderCalc();setTimeout(()=>{var d=document.getElementById('item-detail');if(d)d.scrollIntoView({behavior:'smooth'})},150)">
      <td><strong>${it.n}</strong> <span style="color:var(--text-muted);font-size:11px">TC${it.tc}/q${it.qlvl}</span></td>
      <td style="text-align:right">${fmtChance(it.norm)}</td>
      <td style="text-align:right">${fmtChance(it.nm)}</td>
      <td style="text-align:right">${fmtChance(it.hell)}</td>
    </tr>`;
  }).join('');
  card.innerHTML = `
    <button class="boss-detail-close" onclick="closeBossDetail()" aria-label="close">×</button>
    <div class="boss-detail-header">
      <span class="boss-emoji">${boss.emoji}</span>
      <div class="bd-title">
        <p class="bd-name">${boss.name}</p>
        <p class="bd-sub">${boss.subtitle||''}</p>
        <p class="bd-loc">${boss.loc||''} · <span style="color:var(--terror)">${boss.kph||'?'} kills/hr</span> · <span style="color:var(--gold)">${boss.tierLabel||''} ${boss.tierTag||''}</span></p>
      </div>
    </div>
    <div class="boss-detail-body">
      <h3>drop chances by difficulty (your MF: ${mf}%)</h3>
      <div class="bd-diff-grid">${diffsHtml}</div>
      <div class="bd-meta-row">
        <div class="bd-meta-chip"><strong>why:</strong>${boss.why||'—'}</div>
        <div class="bd-meta-chip"><strong>char:</strong>${boss.char||'—'}</div>
      </div>
      <h3>top drops (click to jump to calc detail)</h3>
      <div class="scroll-table"><table class="drops" style="width:100%">
        <thead><tr><th style="text-align:left">item</th><th style="text-align:right">NORM</th><th style="text-align:right">NM</th><th style="text-align:right">HELL</th></tr></thead>
        <tbody>${dropHtml||'<tr><td colspan="4" style="color:var(--text-muted);text-align:center;padding:20px">no drops in table</td></tr>'}</tbody>
      </table></div>
      <div class="bd-actions">
        <button class="bd-action-btn primary" onclick="closeBossDetail();setTimeout(()=>{var el=document.getElementById('${boss.id}');if(el){el.scrollIntoView({behavior:'smooth',block:'start'});el.querySelector('.boss-header')?.classList.add('flash');setTimeout(()=>el.querySelector('.boss-header')?.classList.remove('flash'),1300)}},120)">↗ open full boss card</button>
        <button class="bd-action-btn" onclick="closeBossDetail()">close (esc)</button>
      </div>
    </div>`;
  document.getElementById('boss-detail-overlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}
function closeBossDetail(){
  const o = document.getElementById('boss-detail-overlay');
  if(o) o.classList.add('hidden');
  document.body.style.overflow = '';
}
function setBossDetailFocus(bossId, diffKey){
  openBossDetail(bossId, diffKey);
}
// Esc-to-close
document.addEventListener('keydown', e => {
  if(e.key === 'Escape'){
    const o = document.getElementById('boss-detail-overlay');
    if(o && !o.classList.contains('hidden')) closeBossDetail();
  }
});
"""
assert js_anchor in src
src = src.replace(js_anchor, js_new, 1)

# === 4. Make boss-header clickable in renderBossCards template ===
hdr_anchor = '<div class="boss-header">\n        <span class="boss-emoji">${boss.emoji}</span>'
hdr_new = '<div class="boss-header clickable" onclick="openBossDetail(\'${boss.id}\')">\n        <span class="boss-emoji">${boss.emoji}</span>'
assert hdr_anchor in src
src = src.replace(hdr_anchor, hdr_new, 1)

# === 5. Patch boss-nav chip render to call openBossDetail on click too ===
# Original: `<a href="#${b.id}" class="boss-chip"><span class="emoji">${b.emoji}</span>${b.name}</a>`
nav_anchor = '$("boss-nav").innerHTML = BOSSES.map(b => `<a href="#${b.id}" class="boss-chip"><span class="emoji">${b.emoji}</span>${b.name}</a>`).join("");'
nav_new = '$("boss-nav").innerHTML = BOSSES.map(b => `<a href="#${b.id}" class="boss-chip" data-boss-id="${b.id}" onclick="event.preventDefault();(function(id){var el=document.getElementById(id);if(el){el.scrollIntoView({behavior:\'smooth\',block:\'start\'});var h=el.querySelector(\'.boss-header\');if(h){h.classList.add(\'flash\');setTimeout(()=>h.classList.remove(\'flash\'),1300)}}this.classList.add(\'flash\');setTimeout(()=>this.classList.remove(\'flash\'),900)}).call(this,\'${b.id}\')"><span class="emoji">${b.emoji}</span>${b.name}</a>`).join("");'
assert nav_anchor in src
src = src.replace(nav_anchor, nav_new, 1)

# Save
bak = BIBLE + ".bak_bug010_" + time.strftime("%Y%m%d_%H%M%S")
shutil.copy(BIBLE, bak)
with open(BIBLE, "w", encoding="utf-8") as f:
    f.write(src)

print(f"BUG-010 applied. {orig_len} → {len(src)} chars (+{len(src)-orig_len}). Backup: {bak}")
