
// v635 — stamp the account cue class at boot (CSS above renders the golden ladder ribbon)
try { if (window.D2R_PROFILE==='ladder'){ document.body.classList.add('ladder-profile');
  var _lr=document.createElement('div'); _lr.id='ladder-ribbon'; _lr.textContent='🪜 LADDER ACCOUNT — separate economy · your main account is untouched'; document.body.appendChild(_lr);
} } catch(e){}
// v663 — cousin shell cue: blue ribbon + body class (hides the Main/Ladder pill, tints the masthead)
try { if (window.D2R_MACHINE==='windows'){ document.body.classList.add('cousin-shell');
  var _wr=document.createElement('div'); _wr.id='cousin-ribbon'; _wr.textContent='🪟 WINDOWS — cousin world · Mac untouched'; document.body.appendChild(_wr);
} } catch(e){}

// ── stash freshness (d2r_stashMeta: {runes|gems|materials|vault: epoch-ms}) ──
window._stashTouch = function(kind){
  try {
    var m = JSON.parse(window.LSR.getItem('d2r_stashMeta')||'{}')||{};
    m[kind] = Date.now();
    window.LSR.setItem('d2r_stashMeta', JSON.stringify(m));
    window._renderStashFresh();
  } catch(e){}
};
window._stashAgeH = function(kind){
  try { var m = JSON.parse(window.LSR.getItem('d2r_stashMeta')||'{}')||{}; if (!m[kind]) return Infinity;
    return (Date.now() - m[kind]) / 3600000; } catch(e){ return Infinity; }
};
function _scFreshLabel(h){ if (!isFinite(h)) return 'never scanned'; if (h < 1) return Math.max(1,Math.round(h*60))+'m ago'; if (h < 48) return Math.round(h)+'h ago'; return Math.round(h/24)+'d ago'; }
function _scFreshClass(h){ if (!isFinite(h) || h >= 36) return 'sc-bad'; if (h >= 12) return 'sc-warn'; return 'sc-ok'; }
var _SC_KINDS = [ {k:'runes',label:'Runes',cls:'tqu-rune'}, {k:'gems',label:'Gems',cls:'tqu-gem'}, {k:'materials',label:'Materials',cls:'tqu-mat'}, {k:'vault',label:'Vault',cls:'tqu-vault'} ];
window._renderStashFresh = function(){
  try {
    _SC_KINDS.forEach(function(x){
      var btn = document.querySelector('.tqu-btn.'+x.cls); if (!btn) return;
      var h = window._stashAgeH(x.k), cls = _scFreshClass(h);
      btn.classList.remove('sc-ok','sc-warn','sc-bad'); btn.classList.add(cls);
      var dot = btn.querySelector('.sc-dot');
      if (!dot){ dot = document.createElement('span'); dot.className='sc-dot'; btn.appendChild(dot); }
      btn.title = (btn.title||'').replace(/ · scanned .*$| · never scanned$/,'') + ' · ' + (isFinite(h)?('scanned '+_scFreshLabel(h)):'never scanned');
    });
    var host = document.getElementById('sc-fresh');
    if (host) host.innerHTML = _SC_KINDS.map(function(x){
      var h = window._stashAgeH(x.k);
      return '<button type="button" class="sc-chip '+_scFreshClass(h)+'" onclick="switchTab(\'tools\')" title="update in 🧰 tools"><span class="sc-dot"></span>'+x.label+' · '+_scFreshLabel(h)+'</button>';
    }).join('');
  } catch(e){}
};
// v687 — intake review: after AI tally, confirm / edit / undo before you trust Forge.
// Vault stays touch-only (item filing is multi-object; not a flat count map).
(function(){
  var KEY = { runes:'d2r_runeStash', gems:'d2r_gemStash', materials:'d2r_materialStash' };
  var MEM = { runes:'runeStash', gems:'gemStash', materials:'materialStash' };
  var REND = { runes:'renderRuneStash', gems:'renderGemStash', materials:'renderMaterialStash' };

  function _snap(kind){
    try {
      var mem = window[MEM[kind]];
      if (mem && typeof mem === 'object') return JSON.parse(JSON.stringify(mem));
    } catch(e){}
    try { return JSON.parse(window.LSR.getItem(KEY[kind])||'{}')||{}; } catch(e){ return {}; }
  }
  function _diff(before, after){
    var keys = {}, rows = [];
    Object.keys(before||{}).forEach(function(k){ keys[k]=1; });
    Object.keys(after||{}).forEach(function(k){ keys[k]=1; });
    Object.keys(keys).sort().forEach(function(k){
      var a = parseInt((before||{})[k],10)||0, b = parseInt((after||{})[k],10)||0;
      if (a !== b) rows.push({ k:k, before:a, after:b, delta:b-a });
    });
    return rows;
  }
  function _writeStash(kind, obj){
    try {
      var mem = window[MEM[kind]];
      if (mem && typeof mem === 'object'){
        Object.keys(mem).forEach(function(k){ delete mem[k]; });
        Object.keys(obj||{}).forEach(function(k){ var v=parseInt(obj[k],10); if(isFinite(v)&&v>0) mem[k]=v; });
      }
    } catch(e){}
    try { window.LSR.setItem(KEY[kind], JSON.stringify(obj||{})); } catch(e){}
    try {
      // also bare localStorage path if LSR mirrors
      if (window.LS && window.LS.setItem) window.LS.setItem(KEY[kind], JSON.stringify(obj||{}));
    } catch(e){}
    try { var rn = REND[kind]; if (typeof window[rn] === 'function') window[rn](); } catch(e){}
    try { if (typeof window.renderForge === 'function') window.renderForge(); } catch(e){}
    try { if (typeof window.renderSessionCockpit === 'function') window.renderSessionCockpit(); } catch(e){}
  }
  function _ensureModal(){
    var m = document.getElementById('v687-intake-modal');
    if (m) return m;
    m = document.createElement('div');
    m.id = 'v687-intake-modal';
    m.innerHTML = '<div class="v687-modal" role="dialog" aria-modal="true" aria-labelledby="v687-intake-title">'
      + '<h3 id="v687-intake-title">Review intake</h3>'
      + '<p class="v687-sub" id="v687-intake-sub"></p>'
      + '<div id="v687-intake-table"></div>'
      + '<div class="v687-actions">'
      + '<button type="button" class="v687-btn ghost" id="v687-intake-undo">↩ Undo</button>'
      + '<button type="button" class="v687-btn" id="v687-intake-edit">Apply edits</button>'
      + '<button type="button" class="v687-btn primary" id="v687-intake-keep">✓ Keep</button>'
      + '</div></div>';
    document.body.appendChild(m);
    m.addEventListener('click', function(e){ if (e.target === m) m.classList.remove('open'); });
    return m;
  }
  function _showReview(kind, before, after){
    var rows = _diff(before, after);
    if (!rows.length){ try { window._stashTouch(kind); } catch(e){} return; }
    var modal = _ensureModal();
    document.getElementById('v687-intake-title').textContent = 'Review ' + kind + ' intake';
    document.getElementById('v687-intake-sub').textContent = rows.length + ' change' + (rows.length===1?'':'s')
      + ' from vision — confirm, edit counts, or undo before Forge trusts this.';
    var wrap = document.getElementById('v687-intake-table');
    wrap.innerHTML = '<table class="v687-diff"><thead><tr><th>Item</th><th>Before</th><th>Δ</th><th>After</th></tr></thead><tbody>'
      + rows.map(function(r){
          var cls = r.delta>0?'up':'down';
          return '<tr><td>'+String(r.k).replace(/</g,'&lt;')+'</td><td class="same">'+r.before+'</td>'
            + '<td class="'+cls+'">'+(r.delta>0?'+':'')+r.delta+'</td>'
            + '<td><input type="number" min="0" step="1" data-key="'+String(r.k).replace(/"/g,'&quot;')+'" value="'+r.after+'"></td></tr>';
        }).join('')
      + '</tbody></table>';
    modal.classList.add('open');
    function close(){ modal.classList.remove('open'); }
    document.getElementById('v687-intake-keep').onclick = function(){
      try { window._stashTouch(kind); } catch(e){}
      close();
    };
    document.getElementById('v687-intake-undo').onclick = function(){
      _writeStash(kind, before);
      try { window._stashTouch(kind); } catch(e){}
      close();
    };
    document.getElementById('v687-intake-edit').onclick = function(){
      var next = JSON.parse(JSON.stringify(before||{}));
      wrap.querySelectorAll('input[data-key]').forEach(function(inp){
        var k = inp.getAttribute('data-key');
        var v = parseInt(inp.value, 10);
        if (isFinite(v) && v > 0) next[k] = v; else delete next[k];
      });
      _writeStash(kind, next);
      try { window._stashTouch(kind); } catch(e){}
      close();
    };
  }

  function _wrapIntake(name, kind, review){
    var orig = window[name];
    if (typeof orig !== 'function' || orig.__v687) return;
    // unwrap prior v686 wrapper if present by not stacking — only wrap once
    if (orig.__v686 && !orig.__v687) {
      // still wrap the v686 wrap; double-touch is ok
    }
    var w = async function(){
      var before = review ? _snap(kind) : null;
      var r = await orig.apply(this, arguments);
      try {
        if (review){
          var after = _snap(kind);
          _showReview(kind, before, after);
        } else {
          window._stashTouch(kind);
        }
      } catch(e){ try { window._stashTouch(kind); } catch(e2){} }
      return r;
    };
    w.__v687 = true; w.__v686 = true;
    window[name] = w;
  }
  _wrapIntake('runeIntake','runes', true);
  _wrapIntake('gemIntake','gems', true);
  _wrapIntake('materialIntake','materials', true);
  _wrapIntake('vaultIntake','vault', false);
})();

// ── session-target pin (d2r_chroniclePin: a runeword OR grail item name) ──
window._sessionPinGet = function(){ try { return window.LSR.getItem('d2r_chroniclePin') || ''; } catch(e){ return ''; } };
window._sessionPinSet = function(name){
  try { if (name) window.LSR.setItem('d2r_chroniclePin', String(name)); else window.LSR.removeItem('d2r_chroniclePin'); } catch(e){}
  window._renderDockPin();
  try { var t = document.getElementById('tab-session'); if (t && t.classList.contains('active')) window.renderSessionCockpit(); } catch(e){}
};
window._sessionPinClear = function(){ window._sessionPinSet(''); };
window._renderDockPin = function(){
  var el = document.getElementById('dock-pin'); if (!el) return;
  var pin = window._sessionPinGet();
  if (pin){ el.classList.remove('empty'); el.innerHTML = '🎯 <b>'+_scEsc(pin)+'</b>'; }
  else { el.classList.add('empty'); el.innerHTML = '🎯 <span class="dp-cta">set a session target</span>'; }   

};
function _scEsc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

// ── the cockpit ──
window._sessionLog = function(msg){
  try {
    var arr = JSON.parse(window.LSR.getItem('d2r_sessionLog')||'[]');
    if (!Array.isArray(arr)) arr = [];
    arr.unshift({ t: Date.now(), msg: String(msg||'') });
    if (arr.length > 40) arr = arr.slice(0, 40);
    window.LSR.setItem('d2r_sessionLog', JSON.stringify(arr));
  } catch(e){}
  try { window._renderSessionLog && window._renderSessionLog(); } catch(e){}
};
window._sessionLogClear = function(){
  try { window.LSR.setItem('d2r_sessionLog', '[]'); } catch(e){}
  try { window._renderSessionLog && window._renderSessionLog(); } catch(e){}
};
window._renderSessionLog = function(){
  var el = document.getElementById('sc-log-body'); if (!el) return;
  try {
    var arr = JSON.parse(window.LSR.getItem('d2r_sessionLog')||'[]');
    if (!arr.length){ el.innerHTML = '<div class="sc-empty">no events this shift — pin a mission or run an intake</div>'; return; }
    el.innerHTML = arr.slice(0,12).map(function(x){
      var d = new Date(x.t||Date.now());
      var hh = String(d.getHours()).padStart(2,'0')+':'+String(d.getMinutes()).padStart(2,'0');
      return '<div class="sc-log-line"><time>'+hh+'</time>'+_scEsc(x.msg)+'</div>';
    }).join('');
  } catch(e){ el.innerHTML = '<div class="sc-empty">log unavailable</div>'; }
};
window._sessionPrintPlan = function(){
  try { if (window.switchTab) window.switchTab('session'); } catch(e){}
  setTimeout(function(){ try { window.print(); } catch(e){} }, 200);
};
// Mark mission forged (chronicle) then refresh cockpit
window._sessionMarkForged = function(name){
  if (!name) return;
  try {
    var made = (typeof rwMade!=='undefined' && rwMade[name]);
    if (!made && typeof window.rwToggleMade === 'function') window.rwToggleMade(name);
  } catch(e){}
  try { window._sessionLog('✓ forged / toggled: '+name); } catch(e){}
  try { if (typeof window.renderForge==='function') window.renderForge(); } catch(e){}
  try { window.renderSessionCockpit(); } catch(e){}
};
window._sessionDoMission = function(){
  var m = window._scMission;
  if (!m){ if (window.switchTab) window.switchTab('forge'); return; }
  try { window._sessionLog('▶ do now: '+m.name+' ('+m.status+')'); } catch(e){}
  if (m.kind === 'rw'){
    if (window.switchTab) window.switchTab('forge');
    setTimeout(function(){
      try {
        if (m.status === 'now' && window.forgeSetFilter) window.forgeSetFilter('now');
        else if (m.status === 'step' && window.forgeSetFilter) window.forgeSetFilter('onestep');
        else if (m.status === 'pipe' && window.forgeSetFilter) window.forgeSetFilter('pipeline');
      } catch(e){}
    }, 80);
  } else if (m.kind === 'grail'){
    if (typeof window.openItemDetail === 'function') window.openItemDetail(m.name);
    else if (typeof window.openDrop === 'function') window.openDrop(m.name);
    else if (window.switchTab) window.switchTab('calc');
  } else {
    if (window.switchTab) window.switchTab('tools');
  }
};

window.renderSessionCockpit = function(){
  try {
    function esc(s){ return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
    function escJs(s){ return String(s==null?'':s).replace(/\\/g,'\\\\').replace(/'/g,"\\'"); }

    // ── KPIs ──
    var kh = [];
    var _scRwMade = function(){
      try { return Object.keys((typeof rwMade!=='undefined'&&rwMade)||{}).filter(function(n){
        return typeof RUNEWORD_TIP!=='undefined'&&RUNEWORD_TIP[n];
      }).length; } catch(e){ return 0; }
    };
    try {
      var rwT = (typeof RUNEWORD_TIP!=='undefined') ? Object.keys(RUNEWORD_TIP).length : 0;
      if (rwT) kh.push('<div class="sc-kpi"><b>'+_scRwMade()+'/'+rwT+'</b><span>Chronicle</span></div>');
    } catch(e){}
    var _scFuni = null; try { _scFuni = window.funiScan(); } catch(e){}
    if (_scFuni) kh.push('<div class="sc-kpi"><b>'+_scFuni.found+'/'+(_scFuni.chronTotal||_scFuni.total)+'</b><span>Grail</span></div>');
    try {
      if (typeof setPieces!=='undefined' && typeof SETS!=='undefined' && Array.isArray(SETS))
        kh.push('<div class="sc-kpi"><b>'+setPieces.size+'/'+SETS.reduce(function(a,s){return a+s.pieces.length;},0)+'</b><span>Sets</span></div>');
    } catch(e){}
    try { kh.push('<div class="sc-kpi"><b>'+((typeof mf!=='undefined')?mf:(window.LSR.getItem('d2r_mf')||'0'))+'%</b><span>MF</span></div>'); } catch(e){}
    try { kh.push('<div class="sc-kpi"><b>/p'+((typeof players!=='undefined')?players:(window.LSR.getItem('d2r_players')||'1'))+'</b><span>Players</span></div>'); } catch(e){}
    var kEl = document.getElementById('sc-kpis'); if (kEl) kEl.innerHTML = kh.join('');

    window._renderStashFresh();

    // ── Forge scan ──
    var scan = { now:[], onestep:[], pipeline:[], crafts:[], farm:[] };
    try { if (typeof window.forgeScan === 'function') scan = window.forgeScan() || scan; } catch(e){}
    var liveNow = (scan.now||[]).filter(function(t){ return !t.deferred; });

    // ── Resolve mission ──
    var pin = '';
    try { pin = window._sessionPinGet() || ''; } catch(e){}
    var mission = null; // {name, kind:'rw'|'grail'|'scan', status, detail, task}

    function findRwTask(name){
      var lists = [
        {arr:liveNow, status:'now', label:'Make now — runes + base ready'},
        {arr:scan.onestep||[], status:'step', label:'One step away'},
        {arr:scan.pipeline||[], status:'pipe', label:'Pipeline — socket / prepare base'},
        {arr:scan.farm||[], status:'farm', label:'Farm ingredients'}
      ];
      for (var i=0;i<lists.length;i++){
        for (var j=0;j<lists[i].arr.length;j++){
          if (lists[i].arr[j].rw === name){
            return { task: lists[i].arr[j], status: lists[i].status, label: lists[i].label };
          }
        }
      }
      // known runeword but not in queue
      if (typeof RUNEWORD_TIP!=='undefined' && RUNEWORD_TIP[name]){
        var made = typeof rwMade!=='undefined' && rwMade[name];
        return { task:null, status: made?'done':'hunt', label: made?'Already in Chronicle':'Not ready — farm runes/base' };
      }
      return null;
    }

    if (pin){
      var hit = findRwTask(pin);
      if (hit){
        mission = { name:pin, kind:'rw', status:hit.status, label:hit.label, task:hit.task };
      } else {
        mission = { name:pin, kind:'grail', status:'hunt', label:'Grail / item hunt', task:null };
      }
    } else if (liveNow[0]){
      mission = { name:liveNow[0].rw, kind:'rw', status:'now', label:'Make now — runes + base ready', task:liveNow[0], auto:true };
    } else if ((scan.onestep||[])[0]){
      var t = scan.onestep[0];
      mission = { name:t.rw, kind:'rw', status:'step', label:'One step away', task:t, auto:true };
    } else if ((scan.pipeline||[])[0]){
      var t2 = scan.pipeline[0];
      mission = { name:t2.rw, kind:'rw', status:'pipe', label:'Pipeline', task:t2, auto:true };
    } else {
      var wish = null;
      try { if (typeof wishlist!=='undefined' && wishlist.size) wish = [...wishlist][0]; } catch(e){}
      if (wish) mission = { name:wish, kind:'grail', status:'hunt', label:'Wishlist priority', task:null, auto:true };
      else if (_scFuni && _scFuni.missing && _scFuni.missing[0])
        mission = { name:_scFuni.missing[0].n, kind:'grail', status:'hunt', label:'Nearest dark corner of the wall', task:null, auto:true };
      else
        mission = { name:null, kind:'scan', status:'idle', label:'No live orders — update intel', task:null };
    }
    window._scMission = mission;

    // detail line
    var detail = '';
    if (mission.task){
      var t = mission.task;
      if (t.missing && t.missing.length) detail = 'Missing: <b>'+esc(t.missing.join(', '))+'</b>';
      else if (t.sub === 'base') detail = 'Need a socketed base'+(t.bestStr||t.baseReq ? ' — <b>'+esc(t.bestStr||t.baseReq)+'</b>' : '');
      else if (t.sub === 'cube') detail = 'Cube up runes, then forge';
      else if (mission.status === 'now') detail = 'Everything in hand — open Forge and socket in order';
      else if (t.base && t.base.base) detail = 'Base: <b>'+esc(t.base.base)+'</b>'+(t.need?(' · '+t.need+'os'):'');
    } else if (mission.kind === 'grail'){
      detail = 'Open its card for best boss + 1:X under your current MF / players.';
    } else if (mission.kind === 'scan'){
      detail = 'Scan runes · gems · vault in Tools so Forge can build a real queue.';
    }

    // Mission brief HTML
    var mB = document.getElementById('sc-mission-body');
    if (mB){
      if (!mission.name && mission.kind === 'scan'){
        mB.innerHTML = '<div class="sc-mission-name">Stand by</div>'
          + '<div class="sc-mission-status"><span class="sc-tag">idle</span></div>'
          + '<div class="sc-mission-detail">'+detail+'</div>'
          + '<div class="sc-mission-actions">'
          + '<button type="button" class="sc-cta" onclick="switchTab(\'tools\')">📸 Update intel</button>'
          + '<button type="button" class="sc-cta ghost" onclick="switchTab(\'forge\')">Open Forge</button>'
          + '</div>';
      } else {
        var art = '';
        try { if (typeof artOr==='function') art = artOr(mission.name,'🎯','sm'); } catch(e){}
        var statusCls = mission.status==='now'?'now':(mission.status==='step'||mission.status==='pipe'?'step':'want');
        mB.innerHTML = '<div class="sc-mission-name">'+(art||'🎯')+' '+esc(mission.name)
          + (mission.auto?' <span style="font-size:11px;font-weight:600;color:var(--text-dim);letter-spacing:.04em">AUTO</span>':'')
          + '</div>'
          + '<div class="sc-mission-status"><span class="sc-tag '+statusCls+'">'+esc(mission.status)+'</span>'
          + '<span style="font-size:12px;color:var(--text-muted)">'+esc(mission.label)+'</span></div>'
          + (detail?'<div class="sc-mission-detail">'+detail+'</div>':'')
          + '<div class="sc-mission-actions">'
          + '<button type="button" class="sc-cta" onclick="window._sessionDoMission()">▶ Do this now</button>'
          + (mission.kind==='rw' && mission.status!=='done'
              ? '<button type="button" class="sc-cta ghost" onclick="window._sessionMarkForged(\''+escJs(mission.name)+'\')">✓ Mark forged</button>' : '')
          + (!pin && mission.name
              ? '<button type="button" class="sc-cta ghost" onclick="window._sessionPinSet(\''+escJs(mission.name)+'\');window._sessionLog(\'🎯 pinned '+escJs(mission.name)+'\')">🎯 Pin mission</button>' : '')
          + (pin
              ? '<button type="button" class="sc-cta ghost" onclick="window._sessionPinClear();window._sessionLog(\'cleared mission pin\')">Clear pin</button>' : '')
          + '</div>';
      }
    }

    // ── Ops queue ──
    var ops = [];
    // blockers: stale stashes
    try {
      ['runes','gems','materials','vault'].forEach(function(k){
        var h = window._stashAgeH ? window._stashAgeH(k) : Infinity;
        if (!isFinite(h) || h >= 36){
          ops.push({
            blocker:true, tag:'intel', cls:'want',
            txt:'<b>'+esc(k)+'</b> stash '+(isFinite(h)?'stale ('+Math.round(h)+'h)':'never scanned')+' — orders may be wrong',
            act:'📸 Scan', go:function(){ if(window.switchTab) window.switchTab('tools'); }
          });
        } else if (h >= 12){
          ops.push({
            blocker:false, tag:'intel', cls:'step',
            txt:'Rescan <b>'+esc(k)+'</b> soon ('+Math.round(h)+'h old)',
            act:'Tools', goTab:'tools'
          });
        }
      });
    } catch(e){}
    // cap blockers shown
    var blockers = ops.filter(function(o){return o.blocker;}).slice(0,2);
    var rest = [];
    liveNow.slice(0,2).forEach(function(t){
      rest.push({ tag:'now', cls:'now', txt:'Forge <b>'+esc(t.rw)+'</b> — ready', pin:t.rw, act:'Forge', goTab:'forge', filter:'now' });
    });
    (scan.onestep||[]).slice(0,2).forEach(function(t){
      var miss = (t.missing&&t.missing.length)?t.missing.join(', '):(t.sub||'one step');
      rest.push({ tag:'step', cls:'step', txt:'<b>'+esc(t.rw)+'</b> — '+esc(miss), pin:t.rw, act:'Forge', goTab:'forge', filter:'onestep' });
    });
    (scan.pipeline||[]).slice(0,1).forEach(function(t){
      rest.push({ tag:'pipe', cls:'step', txt:'Pipeline <b>'+esc(t.rw)+'</b>', pin:t.rw, act:'Forge', goTab:'forge', filter:'pipeline' });
    });
    // grail side ops if room
    try {
      if (typeof wishlist!=='undefined'){
        [...wishlist].slice(0,2).forEach(function(n){
          if (mission && mission.name===n) return;
          rest.push({ tag:'grail', cls:'want', txt:'Wishlist <b>'+esc(n)+'</b>', pin:n, act:'Open', item:n });
        });
      }
    } catch(e){}
    ops = blockers.concat(rest).slice(0,6);

    var oB = document.getElementById('sc-ops-body');
    if (oB){
      if (!ops.length){
        oB.innerHTML = '<div class="sc-empty">queue clear — Chronicle sealed or intel empty. Hunt grail or enjoy the sun 🌞</div>';
      } else {
        oB.innerHTML = ops.map(function(op, idx){
          var btns = '';
          if (op.pin) btns += '<button type="button" class="sc-act" data-pin="'+esc(op.pin)+'">🎯</button>';
          if (op.act) btns += '<button type="button" class="sc-act sc-ops-go" data-i="'+idx+'">'+esc(op.act)+'</button>';
          return '<div class="sc-ops-row'+(op.blocker?' blocker':'')+'">'
            + '<span class="sc-ops-n">'+(idx+1)+'</span>'
            + '<span class="sc-tag '+op.cls+'">'+esc(op.tag)+'</span>'
            + '<div class="sc-row-txt">'+op.txt+'</div>'
            + '<div style="display:flex;gap:4px">'+btns+'</div></div>';
        }).join('');
        oB.querySelectorAll('[data-pin]').forEach(function(b){
          b.addEventListener('click', function(){
            var n = b.getAttribute('data-pin');
            window._sessionPinSet(n);
            window._sessionLog('🎯 pinned '+n);
          });
        });
        oB.querySelectorAll('.sc-ops-go').forEach(function(b){
          b.addEventListener('click', function(){
            var i = parseInt(b.getAttribute('data-i'),10);
            var op = ops[i]; if (!op) return;
            if (op.goTab){
              if (window.switchTab) window.switchTab(op.goTab);
              if (op.filter) setTimeout(function(){ try{ window.forgeSetFilter&&window.forgeSetFilter(op.filter);}catch(e){} }, 100);
            } else if (op.item){
              if (window.openItemDetail) window.openItemDetail(op.item);
              else if (window.openDrop) window.openDrop(op.item);
            } else if (typeof op.go === 'function') op.go();
          });
        });
      }
    }
    // keep legacy forge body filled lightly
    var fB = document.getElementById('sc-forge-body');
    if (fB) fB.innerHTML = '';

    // ── Battlefield TZ ──
    var tzB = document.getElementById('sc-tz-body');
    function tzVerdict(zoneLabel){
      var z = String(zoneLabel||'').toLowerCase();
      var mname = (mission && mission.name) ? String(mission.name) : '';
      var mstat = mission ? mission.status : '';
      // default
      var v = { cls:'weak', text:'Side content — only divert if the mission is blocked.' };
      if (!mname){ v = { cls:'weak', text:'No mission — farm densest loot or update intel.' }; }
      else if (mission.kind === 'rw'){
        if (mstat === 'now') v = { cls:'no', text:'Mission is Make-now — skip TZ and forge '+mname+' first.' };
        else if (mstat === 'step' || mstat === 'pipe' || mstat === 'farm' || mstat === 'hunt'){
          // rune-friendly zones
          if (/travincal|durance|chaos|worldstone|throne|pit|ancient tunnels|flayer|outer steppes|city of the damned|river of flame/.test(z))
            v = { cls:'yes', text:'Serves rune/base density for '+mname+' — good battlefield while you fill gaps.' };
          else if (/cows|mooland/.test(z))
            v = { cls:'yes', text:'Cows = base density king if you still need a host for '+mname+'.' };
          else
            v = { cls:'weak', text:'Weak for '+mname+' — optional clear or stay on targeted farms.' };
        } else if (mstat === 'done')
          v = { cls:'yes', text:'Mission forged — TZ is free real estate. Grail or next word.' };
      } else if (mission.kind === 'grail'){
        v = { cls:'yes', text:'Grail mission — open '+mname+' card; if this TZ holds its boss/superunique, dive in.' };
      }
      return v;
    }
    if (tzB){
      if (location.protocol === 'file:'){
        tzB.innerHTML = '<div class="sc-empty">📡 live rotation needs the online site</div>';
      } else {
        var _tzPaint = function(){
          var d = window._tzPeek && window._tzPeek();
          if (d && (d.current || d.next)){
            var curLabel = '';
            try {
              // tzZoneRowHtml returns HTML; also try plain fields
              if (d.current && d.current.zone) curLabel = d.current.zone;
              else if (typeof d.current === 'string') curLabel = d.current;
              else if (d.current && d.current.name) curLabel = d.current.name;
            } catch(e){}
            var ver = tzVerdict(curLabel || (tzB.textContent||''));
            // re-read label from rendered row if needed
            var rowHtml = '';
            try { rowHtml = window.tzZoneRowHtml ? window.tzZoneRowHtml(d.current) : esc(curLabel); } catch(e){ rowHtml = esc(curLabel); }
            var nextHtml = '';
            try { if (d.next) nextHtml = window.tzZoneRowHtml(d.next); } catch(e){}
            // refine verdict from full row text
            ver = tzVerdict((curLabel||'') + ' ' + (rowHtml||'').replace(/<[^>]+>/g,' '));
            tzB.innerHTML = '<div class="sc-row"><span class="sc-tag now">now</span><div class="sc-row-txt">'+rowHtml+'</div></div>'
              + (nextHtml ? '<div class="sc-row"><span class="sc-tag">next</span><div class="sc-row-txt">'+nextHtml+'</div></div>' : '')
              + '<div class="sc-tz-verdict '+ver.cls+'"><b>ROE · </b>'+esc(ver.text)+'</div>';
          } else tzB.innerHTML = '<div class="sc-empty">couldn’t reach live tracker — open 📡 TZ tracker</div>';
        };
        tzB.innerHTML = '<div class="sc-empty">fetching battlefield…</div>';
        Promise.resolve(window.refreshTzTracker && window.refreshTzTracker(false)).then(_tzPaint, _tzPaint);
      }
    }

    // ── Intel card ──
    var iB = document.getElementById('sc-intel-body');
    if (iB){
      var lines = [];
      lines.push('<div class="sc-row"><span class="sc-tag">chr</span><div class="sc-row-txt"><b>'+_scRwMade()+'</b> runewords forged'
        +(typeof RUNEWORD_TIP!=='undefined'?' / '+Object.keys(RUNEWORD_TIP).length:'')+'</div></div>');
      if (_scFuni) lines.push('<div class="sc-row"><span class="sc-tag">grail</span><div class="sc-row-txt"><b>'+_scFuni.found+'</b> / '+(_scFuni.chronTotal||_scFuni.total)+' uniques</div></div>');
      try {
        var mfV = (typeof mf!=='undefined')?mf:(window.LSR.getItem('d2r_mf')||'?');
        var pV = (typeof players!=='undefined')?players:(window.LSR.getItem('d2r_players')||'?');
        lines.push('<div class="sc-row"><span class="sc-tag">roe</span><div class="sc-row-txt">MF <b>'+esc(String(mfV))+'</b> · /p<b>'+esc(String(pV))+'</b> · use dock to adjust</div></div>');
      } catch(e){}
      try {
        var prof = window.D2R_PROFILE||'main';
        lines.push('<div class="sc-row"><span class="sc-tag">acct</span><div class="sc-row-txt">'+(prof==='ladder'?'🪜 Ladder':'Main')+' account · '+(window.D2R_MACHINE||'mac')+'</div></div>');
      } catch(e){}
      var staleN = 0;
      try {
        ['runes','gems','materials','vault'].forEach(function(k){
          var h = window._stashAgeH(k); if (!isFinite(h)||h>=12) staleN++;
        });
      } catch(e){}
      lines.push('<div class="sc-row"><span class="sc-tag '+(staleN?'want':'now')+'">intel</span><div class="sc-row-txt">'
        +(staleN? (staleN+' stash source'+(staleN>1?'s':'')+' need attention') : 'All stashes fresh enough to trust Forge')
        +'</div></div>');
      iB.innerHTML = lines.join('');
    }

    // legacy targets
    var tB = document.getElementById('sc-target-body');
    if (tB && mission && mission.name) tB.innerHTML = esc(mission.name);
    var gB = document.getElementById('sc-grail-body');
    if (gB) gB.innerHTML = '';

    window._renderDockPin();
    window._renderSessionLog();
  } catch(e){ try { console.warn('renderSessionCockpit', e); } catch(e2){} }
};

// log pin changes
(function(){
  var _pin = window._sessionPinSet;
  if (typeof _pin === 'function' && !_pin.__v688){
    window._sessionPinSet = function(name){
      var r = _pin.apply(this, arguments);
      try { if (name) window._sessionLog('🎯 mission → '+name); else window._sessionLog('mission cleared'); } catch(e){}
      return r;
    };
    window._sessionPinSet.__v688 = true;
  }
})();

// boot — the dock chip + freshness dots exist on every tab from the first paint
try { window._renderDockPin(); window._renderStashFresh(); } catch(e){}

// v687.1 — --dock-h becomes a MEASUREMENT, not a guess. The static 84px lied the moment the dock
// wrapped to a second row (v686's 🎯 chip at ≤1560w): the TZ pill lifted into card text and the
// body's safe-area under-padded, so the last card slid beneath the bar (Konyo saw both live).
// Every consumer (TZ pill, shortcut-hint, body padding) already reads the var — one observer
// fixes them all, at every width, forever. .dock-tall gates the pill's corner-docking off when
// the band has no free corner.
try {
  var _dockEl = document.querySelector('#control-dock .dock-inner');
  var _dockSync = function(){
    try {
      var h = _dockEl ? Math.ceil(_dockEl.getBoundingClientRect().height) + 14 : 84;   // +14 = the dock's bottom padding
      if (h < 60) h = 84;                                                              // collapsed/hidden dock → keep the floor sane
      document.documentElement.style.setProperty('--dock-h', h + 'px');
      document.documentElement.classList.toggle('dock-tall', h > 104);
    } catch(e){}
  };
  if (_dockEl && typeof ResizeObserver !== 'undefined'){ new ResizeObserver(_dockSync).observe(_dockEl); }
  window.addEventListener('resize', _dockSync);
  _dockSync();
  // v687.1 — the TZ countdown RIDES IN the dock band (first item) instead of floating above it:
  // one bottom collision system, zero card overlap at any width (the float was still biting the
  // 4th cockpit card at 1512w even with an exact lift). Fixed-position CSS stays as the fallback
  // for a missing dock.
  var _tzC = document.getElementById('v42-tz-countdown');
  if (_tzC && _dockEl){ _dockEl.insertBefore(_tzC, _dockEl.firstChild); _tzC.classList.add('in-dock'); }
} catch(e){}
